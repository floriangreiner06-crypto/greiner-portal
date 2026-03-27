# 📋 WORKFLOW.md - VERBINDLICHE REGELN FÜR CLAUDE + USER

**Erstellt:** 2025-12-04 (TAG 90)  
**Zweck:** Konsistente Arbeitsweise zwischen Sessions

---

## 🗂️ DATEI-STRUKTUR (VERBINDLICH)

```
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
│
├── WORKFLOW.md                          ← DIESE DATEI (immer aktuell!)
├── CLAUDE.md                            ← Projekt-Kontext (bei großen Änderungen updaten)
│
├── docs/
│   ├── SESSION_WRAP_UP_TAG[XX].md       ← Session-Zusammenfassungen
│   ├── TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md  ← Session-Startdokumente
│   └── [andere Dokumentation]
│
└── [Code-Verzeichnisse: api/, templates/, scripts/, etc.]
```

### Regeln:
1. **ALLE Session-Docs gehören nach `docs/`** - nicht ins Root!
2. **Dateinamen konsistent:** `SESSION_WRAP_UP_TAG[XX].md` und `TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md`
3. **Keine Duplikate** in verschiedenen Verzeichnissen

---

## 🚀 SESSION-START

### User macht (vor dem Chat oder am Anfang):

```bash
# Bei DB-Arbeit: Schema aktualisieren
cd /opt/greiner-portal
python3 scripts/utils/export_db_schema.py --all
```

### Wenn User sagt: "TAG XX: [Aufgabe]. Lies TODO..."

Claude führt **SOFORT** aus:

```
1. Filesystem:read_text_file → \\Srvrdb01\...\Server\docs\TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md
2. Filesystem:read_text_file → \\Srvrdb01\...\Server\CLAUDE.md (falls nötig)
3. Bei DB-Arbeit: docs/DB_SCHEMA_SQLITE.md und/oder DB_SCHEMA_LOCOSOFT.md lesen
4. Optional: SESSION_WRAP_UP_TAG[XX-1].md für mehr Kontext
```

### NIEMALS:
- ❌ In `/mnt/project/` suchen (ist read-only Kopie, oft veraltet)
- ❌ `project_knowledge_search` für Session-Docs nutzen
- ❌ Annehmen, dass Dateien im Claude Project Knowledge aktuell sind

### IMMER:
- ✅ Direkt im Sync-Verzeichnis lesen: `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\`
- ✅ Pfad `docs/` für Session-Dokumente nutzen

---

## 📝 SESSION-ENDE (CLAUDE ERSTELLT)

Am Ende jeder Session erstellt Claude:

### 1. SESSION_WRAP_UP_TAG[XX].md
```
Pfad: \\Srvrdb01\...\Server\docs\SESSION_WRAP_UP_TAG[XX].md

Inhalt:
- Was wurde gemacht
- Geänderte Dateien
- Git Commits
- Offene Punkte
```

### 2. TODO_FOR_CLAUDE_SESSION_START_TAG[XX+1].md
```
Pfad: \\Srvrdb01\...\Server\docs\TODO_FOR_CLAUDE_SESSION_START_TAG[XX+1].md

Inhalt:
- Kontext (was war TAG XX)
- Offene Punkte / Nächste Aufgaben
- Relevante Dateien
- Schnellstart-Befehle
```

### 3. CLAUDE.md updaten (nur bei großen Änderungen)
```
Pfad: \\Srvrdb01\...\Server\CLAUDE.md

Wann updaten:
- Neue Module/Features
- Geänderte Arbeitsweise
- Neue wichtige Pfade
```

---

## 🔧 GIT WORKFLOW

### Am Session-Ende:
```bash
cd /opt/greiner-portal

# Sync-Share Docs nach Server kopieren (falls nötig)
sudo cp /mnt/greiner-portal-sync/docs/SESSION_WRAP_UP_TAG[XX].md docs/
sudo cp /mnt/greiner-portal-sync/docs/TODO_FOR_CLAUDE_SESSION_START_TAG[XX+1].md docs/

# Git
git add -A
git commit -m "TAG [XX]: [Kurzbeschreibung]"
git push
```

---

## 🚨 RSYNC & GIT - KRITISCHE WARNUNG!

### ⚠️ TAG 91 LESSON LEARNED:

Ein `rsync` OHNE `--exclude '.git'` hat:
- Git-Historie komplett zerstört
- 200+ Dateien als "deleted" markiert
- Stunden Arbeit für Recovery gekostet

### REGELN FÜR RSYNC:

```bash
# ❌ NIEMALS SO:
rsync -av /mnt/greiner-portal-sync/ /opt/greiner-portal/

# ✅ IMMER SO (mit --exclude '.git'):
rsync -av --exclude '.git' /mnt/greiner-portal-sync/ /opt/greiner-portal/

# ✅ ODER: Nur spezifische Dateien kopieren:
cp /mnt/greiner-portal-sync/scheduler/job_definitions.py /opt/greiner-portal/scheduler/
```

### BEI GIT-CHAOS - RECOVERY:

```bash
# GitHub ist unser Backup! Reset auf sauberen Stand:
cd /opt/greiner-portal
git fetch origin
git reset --hard origin/feature/tag82-onwards

# Danach untracked files prüfen (echte neue Dateien behalten):
git status
```

### CLAUDE MUSS BEI RSYNC-BEFEHLEN:
1. **IMMER** `--exclude '.git'` hinzufügen
2. **IMMER** den User warnen wenn rsync ohne exclude gegeben wird
3. **VOR** rsync: `git status` empfehlen
4. **NACH** rsync: `git status` empfehlen

---

## ❓ CLAUDE PROJECT KNOWLEDGE

**Status:** Wird NICHT mehr als primäre Quelle genutzt!

**Warum:** 
- Muss manuell hochgeladen werden
- Ist oft veraltet
- Sync-Verzeichnis ist immer aktuell

**Regel:** Claude liest Session-Docs **direkt aus dem Sync-Verzeichnis**, nicht aus Project Knowledge.

---

## 📞 BEFEHLE FÜR USER

### Neuen Chat starten:
```
TAG [XX]: [Aufgabe]. Lies TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md
```

### Beispiel:
```
TAG 90: Script-Umbenennung. Lies TODO_FOR_CLAUDE_SESSION_START_TAG90.md
```

Das ist alles! Claude weiß dann:
1. Wo die Datei liegt (docs/)
2. Welches Sync-Verzeichnis
3. Was zu tun ist

---

## ✅ CHECKLISTE

### Session-Start (USER):
- [ ] Bei DB-Arbeit: `python3 scripts/utils/export_db_schema.py --all`
- [ ] Prompt: `TAG XX: [Aufgabe]. Lies docs/TODO_FOR_CLAUDE_SESSION_START_TAG[XX].md`

### Session-Start (CLAUDE):
- [ ] TODO aus `docs/` lesen (Sync-Verzeichnis!)
- [ ] CLAUDE.md prüfen falls nötig
- [ ] Bei DB-Arbeit: `docs/DB_SCHEMA_*.md` lesen
- [ ] Kontext zusammenfassen
- [ ] Loslegen

### Session-Ende (CLAUDE):
- [ ] `docs/SESSION_WRAP_UP_TAG[XX].md` schreiben
- [ ] `docs/TODO_FOR_CLAUDE_SESSION_START_TAG[XX+1].md` schreiben
- [ ] Git-Befehle für User bereitstellen

### Nach DB-Migrationen (USER):
- [ ] `python3 scripts/utils/export_db_schema.py --all`
- [ ] Ergebnis prüfen (neue Tabellen/Spalten sichtbar?)

---

---

## 🗄️ DATENBANK-DOKUMENTATION

### Problem: Veraltete Schema-Docs
Die manuelle `docs/DATABASE_SCHEMA.md` ist oft veraltet. Neue Tabellen/Spalten fehlen.

### Lösung: Auto-generiertes Schema

**Script:** `scripts/utils/export_db_schema.py`

```bash
# SQLite Schema exportieren
cd /opt/greiner-portal
python3 scripts/utils/export_db_schema.py > docs/DB_SCHEMA_SQLITE.md

# Locosoft Schema exportieren
python3 scripts/utils/export_db_schema.py --locosoft > docs/DB_SCHEMA_LOCOSOFT.md

# Beide auf einmal
python3 scripts/utils/export_db_schema.py --all
```

### Wann Schema aktualisieren?
- Nach DB-Migrationen
- Wenn Claude nach Spalten fragt die nicht existieren
- Bei Session-Start wenn DB-Arbeit geplant ist

### Dateien (Single Source of Truth):

| Datei | Inhalt | Generiert |
|-------|--------|----------|
| `docs/DB_SCHEMA_SQLITE.md` | SQLite Tabellen + Spalten + Indizes | Auto ✅ |
| `docs/DB_SCHEMA_LOCOSOFT.md` | PostgreSQL Tabellen + Spalten | Auto ✅ |
| `docs/DATABASE_SCHEMA.md` | **VERALTET** - nicht mehr verwenden! | Manuell ❌ |

### Für Claude bei DB-Queries:

1. **IMMER** zuerst `docs/DB_SCHEMA_SQLITE.md` oder `DB_SCHEMA_LOCOSOFT.md` lesen
2. **NIEMALS** Spalten annehmen - Schema prüfen!
3. Bei Zweifeln: User bitten `PRAGMA table_info(tabelle);` auszuführen

---

*Diese Datei ist die verbindliche Referenz für alle Sessions.*
