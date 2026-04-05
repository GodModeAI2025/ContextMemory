---
name: context-memory
description: Persistente, strukturierte Projekt-Memory für Claude mit Knowledge Graph. Gibt Claude ein Langzeitgedächtnis über Sessions hinweg, organisiert als hierarchischer Context Tree mit Agentic Search und typisierten Relationen. IMMER verwenden bei: Projektwissen speichern, Context Tree, Memory verwalten, Wissen kuratieren, Codebase-Kontext, Projektgedächtnis, brv, Kontext merken, Session-übergreifendes Wissen, Projektwissen abrufen, Knowledge Base aufbauen, Coding Memory, was wissen wir über dieses Projekt, zeig mir den Context Tree, Wissen synchronisieren, Memory durchsuchen, context engineering, Kontext-Management. Auch verwenden wenn der Benutzer sagt "merk dir das", "speicher das für später", "was weißt du über mein Projekt", "zeig mir alle gespeicherten Kontexte", "durchsuche mein Projektwissen", "vergiss das nicht", "Kontext kuratieren", "Memory aufbauen", "was haben wir bisher gelernt", oder wenn ein Projekt über mehrere Sessions hinweg bearbeitet wird und Wissen erhalten bleiben soll.
---

# Context Memory — Persistente Projekt-Memory für Claude

## Überblick

Context Memory gibt Claude ein strukturiertes Langzeitgedächtnis für Projekte. Statt dass Wissen nach jeder Session verloren geht, wird es in einem **Context Tree** organisiert — einer hierarchischen Wissensstruktur, die über Sessions hinweg persistiert.

### Kernkonzepte

1. **Context Tree**: Hierarchische Baumstruktur für Projektwissen (Architektur, Patterns, Entscheidungen, Lessons Learned)
2. **Memory Nodes**: Einzelne Wissenseinheiten mit Metadaten (Typ, Tags, Zeitstempel, Relevanz)
3. **Agentic Search**: Mehrstufige Suche — erst Fuzzy-Match auf Tags/Titel, dann semantische Tiefensuche
4. **Kuratierung**: Aktives Pflegen, Aktualisieren und Bereinigen des Wissensbaums
5. **Workspace**: Projektbezogener Speicherort unter `.context-memory/`

## Architektur

```
.context-memory/
├── tree.json              # Context Tree Struktur + Metadaten
├── nodes/                 # Einzelne Memory Nodes als Markdown
│   ├── arch-001.md        # z.B. Architekturentscheidung
│   ├── pattern-002.md     # z.B. Code-Pattern
│   └── lesson-003.md      # z.B. Lesson Learned
├── index.json             # Such-Index (Tags, Titel, Typen)
└── history.json           # Änderungshistorie
```

## Workflow

### Phase 1: Workspace initialisieren

Wenn der Benutzer ein Projekt hat und Memory nutzen will:

```bash
python3 /path/to/scripts/cm_init.py [--project-name "Mein Projekt"] [--path /pfad/zum/projekt]
```

Standardmäßig wird der Workspace in `/home/claude/.context-memory/` angelegt. Bei Angabe eines Projektnamens unter `/home/claude/.context-memory/<project-name>/`.

### Phase 2b: Dokumente aufnehmen (Ingest)

Wissen kann auch direkt aus Dateien extrahiert werden:

```bash
# Einzelnes Dokument als einen Node
python3 /path/to/scripts/cm_ingest.py --file spec.pdf --type architecture --tags "spec,api"

# Markdown/DOCX nach Abschnitten splitten
python3 /path/to/scripts/cm_ingest.py --file requirements.docx --split sections --type architecture

# Präsentation nach Slides splitten
python3 /path/to/scripts/cm_ingest.py --file slides.pptx --split slides --type architecture

# Excel nach Sheets splitten
python3 /path/to/scripts/cm_ingest.py --file data.xlsx --split sheets --type config

# PDF nach Seiten splitten
python3 /path/to/scripts/cm_ingest.py --file report.pdf --split pages --type architecture

# Dry-Run (zeigt was passieren würde)
python3 /path/to/scripts/cm_ingest.py --file report.pdf --dry-run
```

**Unterstützte Formate:**

| Format | Extraktion | Split-Optionen |
|--------|-----------|----------------|
| PDF | Text (pypdf + pdftotext fallback) | `pages`, `single` |
| DOCX/DOC | Markdown via pandoc, Abschnitte via Headings | `sections`, `single` |
| XLSX/XLS/ODS | Spalten, Typen, Sample-Daten via pandas | `sheets`, `single` |
| PPTX | Slide-Text + Speaker Notes | `slides`, `single` |
| CSV/TSV | Schema, Statistiken, Sample via pandas | `single` |
| JSON/JSONL | Strukturanalyse, Keys, Types | `single` |
| Markdown/TXT | Direkt, mit Abschnittserkennung | `sections`, `single` |
| HTML | Via pandoc nach Markdown | `sections`, `single` |
| EPUB/ODT/RTF | Via pandoc nach Text | `single` |
| YAML/TOML/XML | Als Config-Block | `single` |
| Bilder | Metadata (Größe, Format) + optionale Beschreibung | `single` |
| Code (.py/.js/...) | Als Text mit Syntax-Erkennung | `single` |

### Phase 3: Wissen kuratieren

Wissen wird als **Memory Nodes** gespeichert. Jeder Node hat:

- **ID**: Automatisch generiert (`<typ>-<nummer>`)
- **Typ**: `architecture`, `pattern`, `decision`, `lesson`, `config`, `api`, `dependency`, `workflow`, `bug`, `convention`
- **Titel**: Kurze Beschreibung
- **Tags**: Suchbare Schlagwörter
- **Inhalt**: Detailliertes Wissen in Markdown
- **Relevanz**: `critical`, `high`, `medium`, `low`
- **Status**: `active`, `outdated`, `superseded`
- **Erstellt/Aktualisiert**: Zeitstempel

**Wissen hinzufügen:**
```bash
python3 /path/to/scripts/cm_add.py \
  --type "architecture" \
  --title "Backend API Struktur" \
  --tags "api,rest,express,nodejs" \
  --relevance "high" \
  --content "Das Backend nutzt Express.js mit einer 3-Schicht-Architektur..."
```

**Wissen aus Codebase extrahieren (Agentic Curate):**
```bash
python3 /path/to/scripts/cm_curate.py --path /pfad/zum/projekt [--focus "testing"] [--depth 3]
```

Dieses Script analysiert die Codebase und erzeugt automatisch Memory Nodes für:
- Erkannte Architektur-Patterns
- Abhängigkeiten und deren Versionen
- Konfigurationsdetails
- Code-Konventionen
- Test-Strategien

### Phase 3: Wissen abrufen (Agentic Search)

Die Suche arbeitet mehrstufig:

1. **Quick Search**: Exakte und Fuzzy-Matches auf Tags, Titel, Typ
2. **Deep Search**: Durchsucht Inhalte aller Nodes bei unzureichenden Quick-Results
3. **Context Assembly**: Stellt relevante Nodes zu einem kohärenten Kontext zusammen

```bash
python3 /path/to/scripts/cm_search.py --query "wie funktioniert die Authentifizierung" [--type "architecture"] [--limit 5]
```

**Gesamten Context Tree anzeigen:**
```bash
python3 /path/to/scripts/cm_tree.py [--format "detailed"|"compact"|"visual"]
```

### Phase 4: Wissen pflegen

```bash
# Node aktualisieren
python3 /path/to/scripts/cm_update.py --id "arch-001" --content "Neuer Inhalt..." [--status "outdated"]

# Node entfernen
python3 /path/to/scripts/cm_delete.py --id "arch-001"

# Veraltete Nodes finden
python3 /path/to/scripts/cm_cleanup.py [--older-than 30] [--status "outdated"]

# Statistiken anzeigen
python3 /path/to/scripts/cm_stats.py
```

### Phase 5: Export & Sharing

```bash
# Als Markdown exportieren
python3 /path/to/scripts/cm_export.py --format "markdown" --output "project-knowledge.md"

# Als JSON exportieren (für Backup/Transfer)
python3 /path/to/scripts/cm_export.py --format "json" --output "project-knowledge.json"

# Importieren
python3 /path/to/scripts/cm_import.py --input "project-knowledge.json"
```

## Verhaltensregeln für Claude

### Wann automatisch kuratieren:
- Wenn der Benutzer eine wichtige Architekturentscheidung trifft → als `decision` Node speichern
- Wenn ein schwieriger Bug gelöst wird → als `lesson` Node speichern
- Wenn ein neues Pattern eingeführt wird → als `pattern` Node speichern
- Wenn Konfigurationen geändert werden → als `config` Node speichern

### Wann automatisch suchen:
- Wenn der Benutzer nach Projektdetails fragt → im Context Tree suchen
- Wenn Code geschrieben wird, der zu existierendem Kontext passt → relevante Nodes laden
- Wenn eine neue Session beginnt und der Benutzer am gleichen Projekt arbeitet → Tree-Übersicht laden

### Kommunikation:
- Bestätige immer, wenn Wissen gespeichert wurde: "Gespeichert als `arch-003`: Backend API Routing"
- Bei Suchen, zeige was gefunden wurde und die Relevanz
- Biete proaktiv an, Wissen zu kuratieren wenn du merkst, dass wichtige Erkenntnisse entstehen
- Frage nach, bevor du existierende Nodes überschreibst

### Phase 6: Knowledge Graph — Relationen zwischen Nodes

Nodes können über typisierte, gerichtete Kanten verknüpft werden — das macht aus der Ablage einen echten Knowledge Graph.

```bash
# Relation erstellen
python3 /path/to/scripts/cm_relate.py --from arch-001 --to dec-001 --relation depends_on --note "API braucht DB"

# Alle Relationen eines Nodes anzeigen
python3 /path/to/scripts/cm_relate.py --show dec-001

# Ganzen Knowledge Graph visualisieren
python3 /path/to/scripts/cm_relate.py --graph

# Kürzesten Pfad zwischen zwei Nodes finden
python3 /path/to/scripts/cm_relate.py --path cfg-001 bug-001

# Verwandten Kontext abrufen (alle Nodes in N Hops Entfernung)
python3 /path/to/scripts/cm_relate.py --context dec-001 --context-depth 2

# Relation entfernen
python3 /path/to/scripts/cm_relate.py --from arch-001 --to dec-001 --remove

# Alle Relationstypen anzeigen
python3 /path/to/scripts/cm_relate.py --types
```

**Verfügbare Relationstypen:**

| Kategorie | Typen |
|-----------|-------|
| Strukturell | `depends_on` ↔ `required_by`, `part_of` ↔ `contains` |
| Kausal | `caused_by` ↔ `causes`, `fixed_by` ↔ `fixes` |
| Semantisch | `implements` ↔ `implemented_by`, `supersedes` ↔ `superseded_by`, `related_to` |
| Wissen | `documents` ↔ `documented_by`, `validates` ↔ `validated_by`, `contradicts`, `extends` ↔ `extended_by` |
| Workflow | `precedes` ↔ `follows`, `blocks` ↔ `blocked_by` |

**Suche mit Relationen:** `cm_search.py --query "database" --with-relations` zeigt zu jedem Treffer die verknüpften Nodes.

## Schnellreferenz

| Aktion | Befehl |
|--------|--------|
| Workspace anlegen | `cm_init.py` |
| Wissen hinzufügen | `cm_add.py` |
| Dokument aufnehmen | `cm_ingest.py` |
| Codebase analysieren | `cm_curate.py` |
| Suchen | `cm_search.py` |
| Suche + Relationen | `cm_search.py --with-relations` |
| Tree anzeigen | `cm_tree.py` |
| Relationen verwalten | `cm_relate.py` |
| Knowledge Graph | `cm_relate.py --graph` |
| Pfad finden | `cm_relate.py --path A B` |
| Kontext abrufen | `cm_relate.py --context ID` |
| Aktualisieren | `cm_update.py` |
| Löschen | `cm_delete.py` |
| Aufräumen | `cm_cleanup.py` |
| Statistiken | `cm_stats.py` |
| Exportieren | `cm_export.py` |
| Importieren | `cm_import.py` |

## Edge Cases

- **Leerer Workspace**: Bei Suche in leerem Tree → freundlicher Hinweis, dass noch kein Wissen gespeichert ist
- **Duplikate**: Vor dem Speichern prüfen, ob ähnlicher Node existiert → Merge anbieten
- **Veraltetes Wissen**: Bei jedem Zugriff auf einen Node älter als 30 Tage → Status-Check anbieten
- **Große Codebases**: `cm_curate.py` limitiert auf konfigurierbare Tiefe und ignoriert node_modules, .git, etc.
- **Konfligierende Nodes**: Wenn zwei Nodes sich widersprechen → Benutzer auf Konflikt hinweisen
- **Encoding**: Alle Dateien UTF-8, Sonderzeichen in Tags werden normalisiert
- **Fehlende Dateien**: Robuste Fehlerbehandlung wenn Nodes referenziert aber nicht gefunden werden
- **Concurrent Access**: Last-write-wins mit Warnung im History-Log
