#!/usr/bin/env python3
"""Tests for the time-aware ranking (stdlib only).

Run:
  python3 context-memory/tests/test_recency.py
"""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from cm_core import content_date, parse_partial_date, recency_factor, sort_key_recency  # noqa: E402
from cm_search import assemble_results, quick_search  # noqa: E402

NOW = datetime(2026, 9, 20, tzinfo=timezone.utc)


def node(title, tags, source_date="", created="2026-01-01T00:00:00+00:00", **extra):
    meta = {
        "title": title,
        "type": "lesson",
        "tags": tags,
        "relevance": "medium",
        "status": "active",
        "created": created,
        "updated": created,
        "temporal": {"source_date": source_date, "valid_from": "", "valid_until": "",
                     "temporal_confidence": "explicit" if source_date else "unknown"},
    }
    meta.update(extra)
    return meta


class ParseDateTest(unittest.TestCase):
    def test_partial_dates(self):
        self.assertEqual(parse_partial_date("2025"), datetime(2025, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(parse_partial_date("2025-03"), datetime(2025, 3, 1, tzinfo=timezone.utc))
        self.assertEqual(parse_partial_date("2025-03-17"), datetime(2025, 3, 17, tzinfo=timezone.utc))
        self.assertEqual(parse_partial_date("2025-03-17T10:00:00Z"),
                         datetime(2025, 3, 17, 10, tzinfo=timezone.utc))

    def test_unparsable_and_empty(self):
        self.assertIsNone(parse_partial_date("Q1 2025"))
        self.assertIsNone(parse_partial_date(""))
        self.assertIsNone(parse_partial_date(None))


class ContentDateTest(unittest.TestCase):
    def test_source_date_wins_over_file_dates(self):
        dated, field = content_date(node("t", [], source_date="2025-03", created="2026-09-01T00:00:00+00:00"))
        self.assertEqual(field, "temporal.source_date")
        self.assertEqual(dated.year, 2025)

    def test_valid_from_before_updated(self):
        meta = node("t", [], created="2026-09-01T00:00:00+00:00")
        meta["temporal"]["valid_from"] = "2024-06-01"
        dated, field = content_date(meta)
        self.assertEqual(field, "temporal.valid_from")
        self.assertEqual(dated.year, 2024)

    def test_falls_back_to_updated_then_created(self):
        meta = node("t", [], created="2026-05-05T00:00:00+00:00")
        dated, field = content_date(meta)
        self.assertEqual(field, "updated")
        self.assertEqual(dated.month, 5)
        del meta["updated"]
        dated, field = content_date(meta)
        self.assertEqual(field, "created")

    def test_node_without_any_date(self):
        meta = {"title": "legacy", "tags": [], "temporal": {}}
        self.assertEqual(content_date(meta), (None, ""))


class RecencyFactorTest(unittest.TestCase):
    def test_newer_weighs_more_than_older(self):
        new = recency_factor(node("n", [], source_date="2026-09-01"), NOW)
        old = recency_factor(node("o", [], source_date="2025-09-01"), NOW)
        ancient = recency_factor(node("a", [], source_date="2015-01-01"), NOW)
        self.assertGreater(new, old)
        self.assertGreater(old, ancient)

    def test_undated_node_is_neutral_not_dropped(self):
        self.assertEqual(recency_factor({"title": "legacy", "temporal": {}}, NOW), 1.0)

    def test_bounds_and_future_dates(self):
        self.assertLessEqual(recency_factor(node("n", [], source_date="2026-09-20"), NOW), 1.5)
        self.assertGreaterEqual(recency_factor(node("a", [], source_date="1999-01-01"), NOW), 1.0)
        # A date in the future must not buy extra weight.
        self.assertAlmostEqual(recency_factor(node("f", [], source_date="2030-01-01"), NOW),
                               recency_factor(node("t", [], source_date="2026-09-20"), NOW), places=3)


class RankingTest(unittest.TestCase):
    def test_2026_outranks_2025_for_equal_match(self):
        index = {"nodes": {
            "les-001": node("KI-Adoption EVU", ["ki", "adoption"], source_date="2025-03"),
            "les-002": node("KI-Adoption EVU", ["ki", "adoption"], source_date="2026-08"),
        }}
        results = quick_search(index, {"ki", "adoption"})
        self.assertEqual([r["id"] for r in results], ["les-002", "les-001"])
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_content_date_breaks_ties(self):
        older = {"id": "a", "score": 5.0, "content_timestamp": parse_partial_date("2025-01-01").timestamp()}
        newer = {"id": "b", "score": 5.0, "content_timestamp": parse_partial_date("2026-01-01").timestamp()}
        undated = {"id": "c", "score": 5.0, "content_timestamp": None}
        ordered = sorted([older, undated, newer], key=sort_key_recency)
        self.assertEqual([r["id"] for r in ordered], ["b", "a", "c"])

    def test_undated_node_still_appears(self):
        index = {"nodes": {
            "les-001": node("Backup Policy", ["backup"], source_date="2026-08"),
            "les-002": {"title": "Backup Policy legacy", "type": "lesson", "tags": ["backup"],
                        "relevance": "medium", "status": "active"},
        }}
        ids = [r["id"] for r in quick_search(index, {"backup"})]
        self.assertIn("les-002", ids)
        self.assertEqual(ids[0], "les-001")


class ContradictionTest(unittest.TestCase):
    """Old vs. new, contradictory: the newer wins, the older stays but ranks below."""

    def setUp(self):
        import tempfile
        from cm_core import ensure_workspace, save_index
        from cm_relate import add_relation
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "proj"
        ensure_workspace(self.ws)
        index = {"nodes": {
            "les-001": node("KI-Adoption 12 Prozent", ["ki"], source_date="2025-03"),
            "les-002": node("KI-Adoption 23 Prozent", ["ki"], source_date="2026-08"),
        }}
        save_index(self.ws, index)
        self.index = index
        self.add_relation = add_relation

    def tearDown(self):
        self.tmp.cleanup()

    def _search(self):
        quick = quick_search(self.index, {"ki"})
        return assemble_results(quick, [], 10, self.ws)

    def test_contradicts_demotes_the_older_statement(self):
        # The older node wins on text score, the relation still puts it second.
        self.index["nodes"]["les-001"]["title"] = "KI-Adoption KI Prozent"
        self.add_relation(self.ws, "les-001", "les-002", "contradicts")
        results = self._search()
        self.assertEqual([r["id"] for r in results], ["les-002", "les-001"])
        self.assertEqual(results[1]["outranked_by"], "les-002")
        # Nothing is deleted.
        self.assertEqual(len(results), 2)

    def test_supersedes_demotes_the_replaced_node(self):
        self.index["nodes"]["les-001"]["title"] = "KI-Adoption KI Prozent"
        self.add_relation(self.ws, "les-002", "les-001", "supersedes")
        results = self._search()
        self.assertEqual([r["id"] for r in results], ["les-002", "les-001"])
        self.assertEqual(results[1]["outranked_by"], "les-002")

    def test_unrelated_relation_changes_nothing(self):
        self.add_relation(self.ws, "les-001", "les-002", "related_to")
        results = self._search()
        self.assertEqual([r["id"] for r in results], ["les-002", "les-001"])
        self.assertNotIn("outranked_by", results[0])
        self.assertNotIn("outranked_by", results[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
