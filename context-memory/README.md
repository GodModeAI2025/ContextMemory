# Context Memory — Dein persönlicher Knowledge Graph für Claude

**Persistentes, strukturiertes Projektgedächtnis mit Knowledge Graph, mehrstufiger Suche und Dokumenten-Ingest.**

---

## Was ist Context Memory?

Context Memory ist ein Claude Skill, der Claude ein Langzeitgedächtnis gibt. Du installierst den Skill, und ab dann kannst du Claude direkt ansprechen, um Wissen zu speichern, zu verknüpfen und wieder abzurufen.

Das Ergebnis ist ein **persönlicher Knowledge Graph**, der mit jedem Gespräch wächst.

---

## So sprichst du den Skill an

Der Skill heißt **Context Memory**. Nenne den Namen, damit Claude weiß, welchen Skill er verwenden soll. Hier sind die wichtigsten Aufrufe.

### Projekt anlegen

> „Context Memory: Erstelle mir eine Wissensbasis für mein Projekt ‚SaaS-Plattform'."
>
> „Context Memory: Leg ein neues Wissensprojekt an: Fachbuch KI Energie."
>
> „Starte Context Memory für mein aktuelles Projekt."

### Wissen speichern

> „Context Memory: Merk dir — wir nutzen PostgreSQL statt MongoDB wegen ACID-Transaktionen. Das ist eine kritische Entscheidung."
>
> „Context Memory: Speicher das als Lesson: Der N+1-Bug hat uns 2 Tage gekostet. Fix war ein JOIN statt Einzelabfragen."
>
> „Context Memory: Das ist ein Pattern: Alle Cache-Keys werden immer mit Tenant-ID prefixed."
>
> „Context Memory: Wichtig aber noch unsicher: Wir vermuten einen Memory-Leak im Order-Service."

### Dokumente aufnehmen

> „Context Memory: Nimm diese PDF in die Wissensbasis auf, splitte nach Seiten."
>
> „Context Memory: Hier ist unsere API-Spec als Markdown. Bitte nach Abschnitten aufteilen."
>
> „Context Memory: Verarbeite diese Excel-Datei — jedes Sheet als eigenen Eintrag."
>
> „Context Memory: Lies diese PowerPoint und speichere die Slides als Wissen."

### Wissen abrufen

> „Context Memory: Was wissen wir über die Authentifizierung?"
>
> „Context Memory: Durchsuche mein Projektwissen nach ‚Deployment'."
>
> „Context Memory: Zeig mir den Context Tree."
>
> „Context Memory: Zeig den Knowledge Graph — wie hängt alles zusammen?"

### Verknüpfungen und Zusammenhänge

> „Context Memory: Die API hängt von der Datenbank ab — verknüpfe das."
>
> „Context Memory: Der Bug wurde durch die Multi-Tenant-Entscheidung verursacht."
>
> „Context Memory: Die Stanford-Studie bestätigt die Interview-Aussagen."
>
> „Context Memory: Diese neue Erkenntnis widerspricht der alten Annahme."
>
> „Context Memory: Wie hängt der Cache-Bug mit der Architektur zusammen?"
>
> „Context Memory: Zeig mir alles was mit der Datenbankentscheidung verbunden ist."

### Zeitbezüge angeben

> „Context Memory: Das gilt seit Q3 2025."
>
> „Context Memory: Diese Studie ist von Juni 2025."
>
> „Context Memory: Die Info stammt aus dem McKinsey-Report März 2025 und gilt für Q1 2025."

### Konfidenz angeben

> „Context Memory: Das ist sicher — steht so in der Dokumentation."
>
> „Context Memory: Wir vermuten das, sind aber noch nicht sicher."
>
> „Context Memory: Hochrelevant, aber die Quelle ist unsicher."

### Codebase analysieren

> „Context Memory: Analysiere meine Codebase unter ./src."
>
> „Context Memory: Schau dir das Projekt an und speichere was du findest."

### Wissen pflegen

> „Context Memory: Was ist veraltet in meiner Wissensbasis?"
>
> „Context Memory: Update den Node zur Datenbank — wir sind jetzt auf PostgreSQL 16."
>
> „Context Memory: Die alten Grafana-Alerts gelten nicht mehr. Ersetze sie durch die neuen."
>
> „Context Memory: Wie gut ist meine Wissensbasis?" *(löst Quality Check aus)*

### Exportieren

> „Context Memory: Exportiere alles als Markdown."
>
> „Context Memory: Mach ein JSON-Backup."
>
> „Context Memory: Exportiere als JSON-LD Knowledge Graph."
>
> „Context Memory: Zeig mir den Graphen als Mermaid-Diagramm."
>
> „Context Memory: Exportiere Chunks für meine RAG-Pipeline."
>
> „Context Memory: Exportiere alles in allen Formaten."

### Importieren / Übergeben

> „Context Memory: Hier ist mein Wissens-Backup. Importiere das." *(JSON-Datei hochladen)*
>
> „Context Memory: Merge dieses Wissen mit meinem bestehenden Projekt."

---

## Für wen ist das gemacht?

**Wissensprojekte** — Recherchen, Buchprojekte, Lernpfade. Du sammelst über Wochen Material aus PDFs, Artikeln, Notizen und baust daraus eine vernetzte Wissensbasis auf. Jede Quelle wird als Node gespeichert, Zusammenhänge als Relationen. Am Ende exportierst du alles als strukturiertes Markdown.

**Entwicklungsprojekte** — Codebases, Architekturentscheidungen, Bug-Fixes. Claude analysiert dein Projekt automatisch, speichert Abhängigkeiten, Patterns und Lessons Learned. Wenn du nächste Woche weitermachst, weiß Claude sofort, wie dein Projekt aufgebaut ist.

**Wissensablagen** — Persönliche Wissensdatenbanken zu beliebigen Themen. Fachexpertise, Projektdokumentation, Prozesse, Regelwerke. Alles durchsuchbar, verknüpft und exportierbar.

---

## Was Claude darauf antwortet — Beispiel-Dialoge

Hier siehst du, wie Claude auf die Aufrufe reagiert.

### Projekt starten

> **Du:** „Leg mir ein neues Wissensprojekt an, es heißt ‚Fachbuch KI Energie'."
>
> **Claude:** 🚀 Workspace erstellt: fachbuch-ki-energie. Bereit zum Wissen sammeln.

### Wissen aus Dokumenten aufnehmen

> **Du:** „Hier ist eine Stanford-Studie als PDF. Nimm die wichtigsten Erkenntnisse auf, splitte nach Seiten."
>
> **Claude:** ✅ 12 Wissenseinheiten aus der Studie extrahiert und gespeichert. Die Studie behandelt Predictive Maintenance, Demand Forecasting und Grid Optimization.

> **Du:** „Und hier sind meine Interview-Notizen als Word-Datei. Bitte nach Abschnitten aufteilen."
>
> **Claude:** ✅ 4 Abschnitte als eigene Nodes gespeichert: Netzbetrieb, Smart Metering, Kundenservice, Prognose.

**Unterstützte Formate:** PDF, Word, Excel, PowerPoint, CSV, JSON, Markdown, HTML, EPUB, YAML, Bilder, Code-Dateien — insgesamt über 15 Formate. Claude splittet automatisch nach Seiten, Abschnitten, Slides oder Sheets, je nachdem was sinnvoll ist.

### Eigenes Wissen festhalten

> **Du:** „Merk dir: Wir haben uns für eine Drei-Akt-Struktur entschieden — Status Quo, Disruption, Transformation. Das ist eine kritische Entscheidung."
>
> **Claude:** ✅ Gespeichert als `dec-001`: Drei-Akt-Struktur. Relevanz: critical.

> **Du:** „Ich habe heute gelernt, dass die KI-Adoption in EVUs viel langsamer ist als gedacht. McKinsey sagt nur 12%. Das widerspricht der Stanford-Studie."
>
> **Claude:** ✅ Gespeichert als `les-001`: KI-Adoption langsamer als erwartet.
> 🕸️ Relation angelegt: les-001 **widerspricht** arch-003 (Stanford-Studie Seite 3).

### Wissen verknüpfen

> **Du:** „Die Stanford-Studie bestätigt die Aussagen aus dem Interview. Verknüpfe das."
>
> **Claude:** ✅ Relation: arch-003 (Stanford, Seite 3) **validiert** les-002 (Interview — Netzbetrieb).

> **Du:** „Zeig mir, wie alles mit der Buchstruktur zusammenhängt."
>
> **Claude:** 🌐 Kontext für die Drei-Akt-Struktur (2 Hops Entfernung):
> - Marktanalyse 2025 (dokumentiert die Struktur)
> - Zielgruppe: Entscheider (Entscheidung)
> - Stanford-Studie Seite 3 (2 Hops, über Interview verknüpft)
> - Interview CTO — Netzbetrieb (validiert durch Stanford)

### Wissen abrufen

> **Du:** „Was wissen wir über Use Cases in der Energiebranche?"
>
> **Claude:** 🔍 4 Treffer:
> 1. Interview CTO — Use Cases im Netzbetrieb (lesson, high)
>    🕸️ Validiert durch Stanford-Studie
> 2. Stanford-Studie — Predictive Maintenance (architecture, high)
> 3. Marktanalyse — Sheet: Prognosen (config, medium)
> 4. McKinsey-Report (lesson, high) ⚠️ Widerspricht Stanford bei Adoptionsrate

> **Du:** „Zeig mir den gesamten Wissensbaum."
>
> **Claude:** 🌳 Context Tree: fachbuch-ki-energie — 34 Nodes
> ├── 🏗️ arch-001: Stanford-Studie Seite 1 🟠
> ├── 🏗️ arch-002: Stanford-Studie Seite 2 🟠
> ├── ...
> ├── ⚖️ dec-001: Drei-Akt-Struktur 🔴
> ├── ⚖️ dec-002: Zielgruppe: Entscheider 🔴
> ├── 💡 les-001: KI-Adoption langsamer als erwartet 🟠
> └── ...

> **Du:** „Gibt es einen Zusammenhang zwischen dem McKinsey-Report und der Buchstruktur?"
>
> **Claude:** 🛤️ Pfad gefunden (3 Hops):
> McKinsey-Report → **widerspricht** → Stanford-Studie → **validiert** → Interview CTO → **dokumentiert durch** → Drei-Akt-Struktur

### Codebase analysieren (für Entwicklungsprojekte)

> **Du:** „Analysiere meine Codebase unter /home/user/saas-app."
>
> **Claude:** 🔍 847 Dateien gescannt, 3 Sprachen erkannt.
> ✅ 5 Wissenseinheiten automatisch erstellt:
> - Projektstruktur-Überblick
> - Node.js Dependencies (Express, Prisma, ...)
> - Konfigurationsdateien
> - Testing Setup (Jest)
> - Docker/Deployment Setup

### Wissen pflegen

> **Du:** „Was ist in meinem Projekt veraltet?"
>
> **Claude:** ⚠️ 5 Nodes wurden seit über 30 Tagen nicht aktualisiert:
> - dep-001: Node.js Dependencies (45 Tage)
> - cfg-002: Grafana Alerts (38 Tage)
> Soll ich sie als ‚veraltet' markieren?

> **Du:** „Die Dependencies sind inzwischen aktualisiert: Express 5.0, Node 22 LTS."
>
> **Claude:** ✅ Node dep-001 aktualisiert. Status zurück auf ‚active'.

> **Du:** „Die alten Grafana Alerts gelten nicht mehr. Ich hab neue Regeln."
>
> **Claude:** ✅ Neuer Node cfg-003: Grafana Alerts v2 angelegt.
> 🔄 Relation: cfg-003 **ersetzt** cfg-002. Alter Node als ‚superseded' markiert.

### Exportieren und Übergeben

> **Du:** „Exportiere alles als Markdown — ich brauche das für die Projektübergabe."
>
> **Claude:** ✅ 34 Nodes als Markdown exportiert → projekt-uebergabe.md

> **Du:** „Exportiere auch als JSON-Backup, damit mein Kollege es importieren kann."
>
> **Claude:** ✅ Vollständiger Export als JSON → saas-backup.json (5.5 KB)
> Dein Kollege kann die Datei importieren und hat sofort den gesamten Wissensstand.

---

## Was der Skill im Hintergrund tut

Du musst das nicht wissen, um den Skill zu nutzen — aber falls es dich interessiert:

### Context Tree

Jedes Projekt bekommt einen eigenen Workspace unter `~/.context-memory/`. Wissen wird als **Memory Nodes** gespeichert — Markdown-Dateien mit strukturierten Metadaten. Der Baum hat eine Hierarchie (Eltern-Kind-Beziehungen), und jeder Node hat einen Typ, Tags, eine Relevanz-Stufe und einen Status.

### 10 Node-Typen

| Typ | Wofür |
|-----|-------|
| architecture | Systemarchitektur, Strukturen, Überblicke |
| pattern | Wiederkehrende Muster, Best Practices |
| decision | Bewusste Entscheidungen mit Begründung |
| lesson | Gelerntes aus Fehlern und Erfahrung |
| config | Konfigurationen, Einstellungen |
| api | Schnittstellen, Endpunkte |
| dependency | Abhängigkeiten, Libraries |
| workflow | Prozesse, Abläufe |
| bug | Bekannte Fehler und Fixes |
| convention | Konventionen, Standards |

Claude wählt den passenden Typ automatisch anhand dessen, was du sagst. Du kannst ihn auch explizit angeben: „Speicher das als Entscheidung" oder „Das ist ein Pattern."

### 22 Relationstypen

Nodes können über typisierte Kanten verknüpft werden. Das macht aus der Ablage einen echten Knowledge Graph.

**Strukturell:** `depends_on` (hängt ab von), `part_of` (ist Teil von)
**Kausal:** `caused_by` (verursacht durch), `fixes` (behebt)
**Semantisch:** `implements` (implementiert), `supersedes` (ersetzt), `related_to` (verwandt)
**Wissen:** `documents` (dokumentiert), `validates` (bestätigt), `contradicts` (widerspricht), `extends` (erweitert)
**Workflow:** `precedes` (kommt vor), `blocks` (blockiert)

Jede Relation ist gerichtet und hat eine automatische Umkehrung (z.B. `depends_on` ↔ `required_by`).

### Dreistufige Suche

**Quick Search:** Schneller Abgleich auf Tags und Titel.
**Deep Search:** Volltextsuche in Node-Inhalten, wenn Quick Search nicht genug findet.
**Relationsanreicherung:** Zeigt zu jedem Treffer die verknüpften Nodes — nicht nur *was* relevant ist, sondern *warum* und *womit es zusammenhängt*.

### Dokumenten-Ingest

Der Skill extrahiert Wissen aus über 15 Dateiformaten:

| Format | Was extrahiert wird |
|--------|-------------------|
| PDF | Text mit Fallback auf OCR |
| Word (DOCX/DOC) | Fließtext, Abschnitts-Struktur |
| Excel (XLSX/XLS) | Spalten, Datentypen, Samples |
| PowerPoint (PPTX) | Slide-Text, Speaker Notes |
| CSV/TSV | Schema, Statistiken |
| JSON | Struktur, Keys, Typen |
| Markdown/TXT/HTML | Volltext mit Abschnittserkennung |
| EPUB/ODT/RTF | Fließtext |
| YAML/TOML/XML | Config-Blöcke |
| Bilder | Metadaten + Beschreibung |
| Code-Dateien | Volltext |

Dokumente können als Ganzes oder gesplittet aufgenommen werden — nach Abschnitten, Seiten, Slides oder Sheets. Claude erkennt Duplikate und warnt, bevor etwas doppelt gespeichert wird.

---

## Ausführliches Arbeitsbeispiel: Von der leeren Wissensbasis zum vernetzten Knowledge Graph

Hier ein durchgängiges Beispiel, wie ein Entwicklungsprojekt über mehrere Sessions wächst.

### Session 1 — Projektstart

> **Du:** „Ich starte ein neues Projekt: eine SaaS-Plattform mit Multi-Tenant-Architektur. Leg mir eine Wissensbasis an."
>
> **Claude:** 🚀 Workspace ‚saas-plattform' erstellt.

> **Du:** „Analysiere meine Codebase unter ./saas-app."
>
> **Claude:** ✅ 5 Nodes automatisch erstellt: Projektstruktur, Dependencies, Config, Tests, Docker-Setup.

> **Du:** „Wichtige Entscheidung: Wir nutzen Schema-pro-Tenant in PostgreSQL statt eigener Datenbanken. Jeder Tenant bekommt sein eigenes Schema. Vorteil: einfachere Migrations. Nachteil: keine vollständige DB-Isolation."
>
> **Claude:** ✅ Gespeichert als `dec-001`: Multi-Tenant mit Schema-pro-Tenant. Relevanz: critical.
> 🔗 Relation: dec-001 **required_by** arch-001 (Projektstruktur).

> **Du:** „Hier ist unsere API-Spezifikation. [lädt api-spec.md hoch] Bitte nach Abschnitten aufteilen."
>
> **Claude:** ✅ 4 API-Nodes gespeichert: Authentication, Tenant Management, Orders, Webhooks.

### Session 2 — Eine Woche später, Bug taucht auf

> **Du:** „Was wissen wir nochmal über die Tenant-Architektur?"
>
> **Claude:** 🔍 Hier ist was wir gespeichert haben:
> 1. **dec-001:** Multi-Tenant mit Schema-pro-Tenant (critical)
>    - Jeder Tenant = eigenes PostgreSQL-Schema
>    - Vorteile: Einfachere Migrations, shared connection pool
>    - Nachteile: Keine vollständige DB-Isolation
>    🕸️ Required by: Projektstruktur
>
> 2. **api-002:** API Spec — Tenant Management (high)
>    - POST /tenants, DELETE /tenants/{id}, ...

> **Du:** „Wir haben einen kritischen Bug gefunden: Redis-Cache-Keys haben keinen Tenant-Prefix. Unter bestimmten Bedingungen werden Daten fremder Tenants zurückgegeben."
>
> **Claude:** ✅ Gespeichert als `bug-001`: Tenant-Daten-Leak über shared Cache-Key. Relevanz: critical.
> ⚡ Relation: bug-001 **caused_by** dec-001 — der Bug hängt direkt mit der Multi-Tenant-Entscheidung zusammen.

> **Du:** „Fix: Alle Cache-Keys müssen mit tenant:{id}: prefixed werden. Wir haben eine Middleware gebaut die das automatisch macht."
>
> **Claude:** ✅ Gespeichert als `les-001`: Cache-Keys immer mit Tenant-ID prefixen. Relevanz: critical.
> 🔧 Relation: les-001 **fixes** bug-001.
> ➕ Relation: les-001 **extends** dec-001 — ergänzt die Multi-Tenant-Architektur um Cache-Isolation.

### Session 3 — Neuer Entwickler steigt ein

> **Du:** „Zeig mir den kompletten Wissensstand für das Onboarding."
>
> **Claude:** 🌳 Context Tree: saas-plattform — 14 Nodes
>
> ├── 🏗️ arch-001: Projektstruktur 🟠
> ├── 📦 dep-001: Node.js Dependencies 🟠
> ├── ⚖️ dec-001: Multi-Tenant Schema-pro-Tenant 🔴
> ├── 🔌 api-001: Authentication 🟠
> ├── 🔌 api-002: Tenant Management 🟠
> ├── 🔌 api-003: Orders 🟠
> ├── 🔌 api-004: Webhooks 🟠
> ├── 🐛 bug-001: Tenant-Daten-Leak (Cache) 🔴
> ├── 💡 les-001: Cache-Keys mit Tenant-ID 🔴
> └── ...

> **Du:** „Zeig den Knowledge Graph — wie hängt alles zusammen?"
>
> **Claude:**
> 🕸️ Knowledge Graph (14 Nodes, 8 Relationen)
>
> 📌 dec-001: Multi-Tenant Architektur
>    ⚡ verursacht → bug-001: Tenant-Daten-Leak
>    ➕ erweitert durch ← les-001: Cache-Keys mit Tenant-ID
>    🔗 benötigt von ← arch-001: Projektstruktur
>
> 📌 les-001: Cache-Keys mit Tenant-ID
>    🔧 behebt → bug-001: Tenant-Daten-Leak
>    ➕ erweitert → dec-001: Multi-Tenant Architektur

> **Du:** „Exportiere alles als Markdown für den neuen Kollegen."
>
> **Claude:** ✅ 14 Nodes exportiert → onboarding-saas.md

---

## Zeitdimension — Wissen veraltet, und der Skill weiß das

Wissen ohne Zeitbezug erzeugt Widersprüche. „Umsatz 28 Mrd." und „Umsatz 34 Mrd." sind kein Konflikt — sondern eine Zeitreihe. Context Memory speichert deshalb drei Zeitebenen pro Node:

| Ebene | Bedeutung | Beispiel |
|-------|-----------|---------|
| **Quelldatum** | Wann wurde das Wissen publiziert? | „Diese Studie ist von Juni 2025" |
| **Gültigkeit** | Ab wann / bis wann gilt es? | „Gültig seit Q3 2025" oder „Gilt bis Jahresende" |
| **Zeitkonfidenz** | Wie sicher ist die Zeitangabe? | explicit (steht im Dokument), inferred (abgeleitet), unknown |

> **Du:** „Merk dir: Laut McKinsey-Report von März 2025 haben nur 12% der EVUs KI produktiv im Einsatz. Das gilt für Q1 2025."
>
> **Claude:** ✅ Gespeichert als `les-003`: KI-Adoption bei EVUs.
> 🕐 Quelldatum: 2025-03 | Gültig: Q1 2025 | Zeitkonfidenz: explicit

> **Du:** „Und in einem neueren Report von November 2025 sind es schon 23%."
>
> **Claude:** ✅ Gespeichert als `les-004`: KI-Adoption aktualisiert.
> 🕐 Quelldatum: 2025-11 | Gültig: Q4 2025 | Zeitkonfidenz: explicit
> 🔄 Relation: les-004 **ersetzt** les-003 — die 12% sind jetzt superseded, nicht widersprüchlich.

Das verhindert, dass Claude alte und neue Zahlen durcheinanderbringt. Bei der Suche werden Treffer mit explizitem Zeitbezug bevorzugt, und bei Widersprüchen sieht man sofort, welcher Wert neuer ist.

---

## Konfidenz — Nicht alles Wissen ist gleich sicher

Relevanz und Konfidenz sind zwei verschiedene Dinge. Ein Node kann hochrelevant sein, aber die Information unsicher:

| | Hohe Konfidenz | Niedrige Konfidenz |
|---|---|---|
| **Hohe Relevanz** | Kernwissen, bestätigt | Wichtig, aber noch zu validieren |
| **Niedrige Relevanz** | Randdetail, gesichert | Gerücht, Randnotiz |

> **Du:** „Wir vermuten, dass der Memory-Leak im Order-Service liegt, aber sicher sind wir noch nicht. Das ist aber kritisch."
>
> **Claude:** ✅ Gespeichert als `bug-002`: Vermuteter Memory-Leak im Order-Service.
> Relevanz: critical | Konfidenz: low
>
> So weiß jeder: Wichtig, aber noch nicht bestätigt.

> **Du:** „Update: Wir haben den Leak bestätigt. Es ist ein unbegrenzter In-Memory-Cache."
>
> **Claude:** ✅ Node `bug-002` aktualisiert. Konfidenz: high.
> Inhalt ergänzt: Ursache identifiziert — unbegrenzter Cache ohne TTL.

Die Suche zeigt die Konfidenz bei jedem Treffer an. So siehst du auf einen Blick, was gesichert ist und was noch überprüft werden muss.

---

## Export-Formate — Vom Markdown bis zum Knowledge Graph für RAG

Context Memory exportiert in sechs Formaten. Du sagst Claude einfach, was du brauchst.

### Markdown — Für Menschen

> **Du:** „Exportiere mein Projekt als Markdown."
>
> **Claude:** ✅ 34 Nodes exportiert als lesbares Markdown mit Quality Score 95/100.

Strukturiertes Dokument mit allen Nodes nach Typ gruppiert, inklusive Zeitbezüge, Konfidenz und Relationen. Sofort lesbar, verschickbar, druckbar.

### JSON — Für Backup und Transfer

> **Du:** „Mach ein Backup als JSON."
>
> **Claude:** ✅ Vollständiger Export mit allen Nodes, Relationen und History.

Enthält alles. Kann in einer neuen Session oder auf einem anderen System importiert werden. Auch Merge mit bestehendem Wissen möglich.

### JSON-LD — Für Wissensgraph-Tools

> **Du:** „Exportiere als JSON-LD Knowledge Graph."
>
> **Claude:** ✅ JSON-LD mit schema.org-Kontext exportiert.
> 34 Nodes, 22 Edges, 34 Chunks, 8 Cluster.

Standardkonformer Knowledge Graph mit schema.org-Vokabular. Importierbar in Neo4j, Gephi oder jedes andere Graph-Tool. Jeder Knoten hat Definition, Statements, Cluster-Zuordnung und temporale Metadaten.

### Mermaid — Für visuelle Darstellung

> **Du:** „Zeig mir den Graphen als Mermaid-Diagramm."
>
> **Claude:** ✅ Mermaid-Diagramm exportiert. Öffne es in Obsidian, GitHub oder mermaid.live.

Farbcodierte Diagramme: Architektur in Blau, Entscheidungen in Rot, Lessons in Orange, Patterns in Grün. Verschiedene Pfeiltypen je Relationstyp — durchgezogene Linien für Abhängigkeiten, gestrichelte für Kausalität, doppelte für Fixes.

### Embedding-Chunks — Für RAG-Pipelines und semantische Suche

> **Du:** „Exportiere Chunks für meine RAG-Pipeline."
>
> **Claude:** ✅ 34 Embedding-Chunks als JSONL exportiert.
> Geschätzte Tokens: ~4.200.
> Bereit für LangChain, LlamaIndex, OpenAI Embeddings, Cohere.

Saubere Textblöcke ohne Markdown-Formatierung, Emojis oder Sonderzeichen. Jeder Chunk beginnt mit einem natürlichsprachlichen Zeitbezug wie „As of Q3 2025:" und enthält Typ, Konfidenz und Token-Schätzung. Ein Chunk pro Node — optimiert für Embedding-Modelle.

### Alles auf einmal

> **Du:** „Exportiere alles in allen Formaten."
>
> **Claude:** ✅ 5 Dateien exportiert:
> - projekt.knowledge.md (Markdown)
> - projekt.knowledge.json (Backup)
> - projekt.knowledge.jsonld.json (Knowledge Graph)
> - projekt.knowledge.mermaid (Diagramm)
> - projekt.knowledge.chunks.jsonl (RAG-Chunks)
>
> 📊 Quality Score: 95/100

---

## Qualitätsprüfung — Wie gut ist meine Wissensbasis?

Der Skill prüft automatisch 8 Qualitätskriterien und gibt einen Score von 0 bis 100:

> **Du:** „Wie gut ist meine Wissensbasis?"
>
> **Claude:** 🔍 Quality Score: 88/100
>
> ✅ 7 von 8 Checks bestanden:
> - Alle Nodes haben Inhalt
> - Keine verwaisten Relationen
> - Keine doppelten Titel
> - Alle Nodes haben Tags
> - Alle Nodes haben Konfidenz-Angaben
> - 28 von 34 Nodes haben Zeitdaten
> - Aktive Nodes vorhanden
>
> ⚠️ 1 Issue:
> - 6 Nodes ohne Zeitdaten. Überlege, Quelldaten zu ergänzen.

**Was geprüft wird:**

| Check | Was es bedeutet |
|-------|----------------|
| Content vorhanden | Kein Node ist leer oder zu kurz |
| Keine verwaisten Relationen | Jede Kante zeigt auf existierende Nodes |
| Keine Duplikat-Titel | Jeder Titel ist eindeutig |
| Tags vorhanden | Jeder Node ist durchsuchbar |
| Konfidenz vorhanden | Jeder Node hat eine Sicherheitseinschätzung |
| Zeitdaten vorhanden | Mindestens einige Nodes haben temporale Metadaten |
| Aktive Nodes vorhanden | Nicht alles ist veraltet oder ersetzt |
| Relationen vorhanden | Bei mehr als 3 Nodes sollten Verknüpfungen existieren |

Der Score wird bei jedem Export automatisch mitberechnet und im Dokument angezeigt.

---

## Daten-Persistenz

Der Skill speichert alles als einfache JSON- und Markdown-Dateien unter `~/.context-memory/`. Kein Datenbankserver, kein Cloud-Konto.

| Umgebung | Persistenz |
|----------|-----------|
| **Claude Code** | Volle Persistenz — ideale Umgebung |
| **Cowork** | Volle Persistenz innerhalb des Projekts |
| **Eigener Server** | Volle Persistenz |
| **Claude.ai** | Dateisystem wird zwischen Sessions zurückgesetzt — am Ende der Session exportieren und nächstes Mal importieren |

**Für Claude.ai-Nutzer:** Sag am Ende der Session „Exportiere mein Wissen als JSON" und lade die Datei herunter. In der nächsten Session lädst du sie hoch und sagst „Importiere mein Wissen." Fertig.

---

## Was der Skill NICHT kann

- **Kein Cloud-Sync** — Daten liegen lokal. Transfer zwischen Geräten per Export/Import.
- **Kein Team-Sharing in Echtzeit** — Export/Import als Workaround.
- **Keine semantische KI-Suche** — die Suche basiert auf Tags, Titeln und Volltext, nicht auf Embeddings. Dafür ist sie schnell, transparent und braucht keinen Vektor-Datenbankserver.
- **In Claude.ai keine automatische Persistenz** — Export/Import-Workflow nötig (in Claude Code und Cowork funktioniert es automatisch).

---

## Skill-Inhalt

```
context-memory/
├── SKILL.md          # Anweisungen für Claude
├── README.md         # Diese Dokumentation
└── scripts/          # 14 Python-Scripts (werden von Claude ausgeführt, nicht vom Nutzer)
    ├── cm_core.py    # Kernbibliothek
    ├── cm_init.py    # Workspace anlegen
    ├── cm_add.py     # Wissen speichern
    ├── cm_ingest.py  # Dokumente aufnehmen
    ├── cm_curate.py  # Codebase analysieren
    ├── cm_search.py  # Suche
    ├── cm_tree.py    # Baumdarstellung
    ├── cm_relate.py  # Knowledge Graph
    ├── cm_update.py  # Aktualisieren
    ├── cm_delete.py  # Löschen
    ├── cm_cleanup.py # Aufräumen
    ├── cm_stats.py   # Statistiken
    ├── cm_export.py  # Export
    └── cm_import.py  # Import
```

Die Scripts werden von Claude im Hintergrund ausgeführt. Du interagierst ausschließlich über natürliche Sprache.

---

*Context Memory Skill — v2.0*
*Ein Claude-nativer Knowledge Graph mit temporaler Dimension, Konfidenz-Tracking, 6 Export-Formaten und automatischer Qualitätsprüfung.*
