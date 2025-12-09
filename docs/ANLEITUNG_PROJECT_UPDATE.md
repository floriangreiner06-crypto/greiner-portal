# ANLEITUNG: Claude Project aktualisieren

## Schritt 1: Project Instructions aktualisieren

Gehe zu deinem Claude Project "Greiner Portal" → Settings → "Custom Instructions" (oder "Project Instructions")

**Kopiere diesen Text komplett hinein:**

---

Bei Session-Start mit "TAG XX: ... Lies TODO..." oder ähnlichem:

1. SOFORT Filesystem:read_text_file auf das Sync-Verzeichnis ausführen:
   Pfad: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md

2. NIEMALS project_knowledge_search für Session-Docs nutzen - Project Knowledge ist oft veraltet!

3. Bei Bedarf auch lesen:
   - \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\CLAUDE.md
   - \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\WORKFLOW.md
   - \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\docs\DB_SCHEMA_SQLITE.md

Projekt: Greiner Portal DRIVE - Flask ERP-System für Autohaus
Server: 10.80.80.20, Pfad: /opt/greiner-portal/
Sync-Verzeichnis: \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\

---

## Schritt 2: Project Knowledge aufräumen

**LÖSCHEN** (veraltet):
- Alle SESSION_WRAP_UP_*.md
- Alle TODO_FOR_CLAUDE_SESSION_START_*.md  
- Alte CLAUDE.md Versionen
- Alles was älter als heute ist

**BEHALTEN/HOCHLADEN** (optional, aber hilfreich):
- PROJECT_OVERVIEW.md (falls allgemeine Infos gewünscht)

**NICHT HOCHLADEN:**
- Session-Docs → werden aus Sync-Verzeichnis gelesen!
- WORKFLOW.md → steht in Project Instructions
- CLAUDE.md → wird aus Sync-Verzeichnis gelesen

## Schritt 3: Testen

Neuen Chat starten mit:
```
TAG 91: Test. Lies docs/TODO_FOR_CLAUDE_SESSION_START_TAG91.md
```

Claude sollte SOFORT `Filesystem:read_text_file` auf das Sync-Verzeichnis ausführen, NICHT `project_knowledge_search`!
