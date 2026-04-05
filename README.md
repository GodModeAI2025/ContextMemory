# Context Memory 

Persistenter Knowledge Graph für Claude mit temporaler Dimension, Konfidenz-Tracking, 6 Export-Formaten und automatischer Qualitätsprüfung.

## Inhalt

```
├── context-memory/          ← Der Skill (als .skill installierbar)
│   ├── SKILL.md             # Skill-Definition für Claude
│   ├── README.md            # Ausführliche Dokumentation
│   └── scripts/             # 14 Python-Scripts
│       ├── cm_core.py       # Kernbibliothek
│       ├── cm_init.py       # Workspace anlegen
│       ├── cm_add.py        # Wissen speichern
│       ├── cm_ingest.py     # Dokumente aufnehmen (15+ Formate)
│       ├── cm_curate.py     # Codebase analysieren
│       ├── cm_search.py     # Mehrstufige Suche
│       ├── cm_tree.py       # Baumdarstellung
│       ├── cm_relate.py     # Knowledge Graph (22 Relationstypen)
│       ├── cm_update.py     # Nodes aktualisieren
│       ├── cm_delete.py     # Nodes entfernen
│       ├── cm_cleanup.py    # Veraltete Nodes finden
│       ├── cm_stats.py      # Statistiken
│       ├── cm_export.py     # Export (MD, JSON, JSON-LD, Mermaid, Chunks)
│       └── cm_import.py     # Import / Merge
│
└── kurs/                    ← Interaktiver Multi-Level-Kurs
    ├── index_de.html        # 👤 Anwender (DE)
    ├── index_en.html        # 👤 Anwender (EN)
    ├── index_dev_de.html    # 🔧 Entwickler (DE)
    ├── index_dev_en.html    # 🔧 Entwickler (EN)
    └── l1/                  # Vertiefungsseiten (Platzhalter)
```

## Skill installieren

Die `.skill`-Datei kann in Claude installiert werden. Alternativ den `context-memory/`-Ordner als Skill-Verzeichnis einbinden.

## Kurs öffnen

Die HTML-Dateien im `kurs/`-Ordner lokal öffnen — keine Dependencies, keine Server nötig. Standalone HTML mit eingebettetem CSS/JS.

## Lizenz

MIT
