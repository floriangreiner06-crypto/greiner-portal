# Workflow-Konsolidierung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from chaotic single-branch/single-DB setup to a clean main/develop Git workflow with separate databases, consolidated CLAUDE.md, and rewritten skills.

**Architecture:** Two server directories (`/opt/greiner-portal/` on `main`, `/opt/greiner-test/` on `develop`) each with their own PostgreSQL database. Git branches control what runs where. Skills enforce the workflow.

**Tech Stack:** Git, PostgreSQL, systemd, Bash, Claude Code skills (Markdown)

**Spec:** `docs/superpowers/specs/2026-03-27-workflow-konsolidierung-design.md`

---

## File Structure

### Files to Create
- `docs/WORKFLOW_ANLEITUNG.md` (user guide for Florian & Vanessa)
- `.claude/commands/hotfix.md` (new skill)
- `.claude/commands/sync.md` (new skill)

### Files to Rewrite
- `CLAUDE.md` (consolidated from 3 sources)
- `.claude/commands/deploy.md`
- `.claude/commands/db.md`
- `.claude/commands/status.md`
- `.claude/commands/logs.md`
- `.claude/commands/test.md`
- `.claude/commands/fix.md`
- `.claude/commands/commit.md`
- `.claude/commands/session-start.md`
- `.claude/commands/session-end.md`
- `.claude/commands/feature.md`
- `.claude/COMMANDS.md`

### Files to Delete
- `.cursorrules`
- `.cursor/` (entire directory)

### Files to Modify
- `/opt/greiner-test/config/.env` (DB_NAME change)
- `/mnt/greiner-portal-sync/CLAUDE.md` (remove password)
- `.claude/settings.local.json` (remove Windows permissions)

---

## Task 1: Commit All Untracked Files in Production

- [ ] **Step 1: Stage all docs and modified files**

```bash
cd /opt/greiner-portal
git add docs/ .gitignore
git add docs/workstreams/infrastruktur/DEALER_PORTABILITY_GIT_BASELINE.md
git add docs/workstreams/infrastruktur/DEV_ONBOARDING_CURSOR.md
git add docs/workstreams/infrastruktur/MERGE_ROLLOUT_PLAN_SANE_DRIVE_PRs.md
```

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
chore(infrastruktur): commit alle untracked docs vor workflow-migration

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify clean state**

```bash
git status --short | wc -l
```

Expected: 0 (or only config/.env)

---

## Task 2: Commit Changes in Test Environment

- [ ] **Step 1: Stage and commit**

```bash
cd /opt/greiner-test
git add api/verkauf_api.py api/verkauf_data.py templates/verkauf_auslieferung_detail.html
git commit -m "$(cat <<'EOF'
feat(verkauf): Auslieferung-Detail Anpassungen aus Develop

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 2: Push and sync**

```bash
cd /opt/greiner-test && git push origin feature/tag112-onwards
cd /opt/greiner-portal && git pull origin feature/tag112-onwards
```

---

## Task 3: Merge feature/tag112-onwards into main

- [ ] **Step 1: Verify fast-forward is possible**

```bash
cd /opt/greiner-portal
git log feature/tag112-onwards..main --oneline
```

Expected: empty (0 commits) = fast-forward moeglich

- [ ] **Step 2: Switch to main and merge**

```bash
cd /opt/greiner-portal
git checkout main
git merge feature/tag112-onwards
```

- [ ] **Step 3: Push main and restart**

```bash
git push origin main
sudo -n /usr/bin/systemctl restart greiner-portal
```

- [ ] **Step 4: Verify production**

```bash
sudo -n /usr/bin/systemctl status greiner-portal | head -5
curl -s http://localhost:5000/ | head -3
```

Expected: active (running), HTML response

---

## Task 4: Set Up develop Branch

- [ ] **Step 1: Create develop from main**

```bash
cd /opt/greiner-portal
git branch -D develop 2>/dev/null
git checkout -b develop
git push -u origin develop --force
git checkout main
```

- [ ] **Step 2: Switch test environment to develop**

```bash
cd /opt/greiner-test
git fetch origin
git checkout develop
git pull origin develop
```

- [ ] **Step 3: Verify branches**

```bash
echo "PROD:" && git -C /opt/greiner-portal rev-parse --abbrev-ref HEAD
echo "DEV:" && git -C /opt/greiner-test rev-parse --abbrev-ref HEAD
```

Expected: PROD: main, DEV: develop

- [ ] **Step 4: Restart test service**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
sudo -n /usr/bin/systemctl status greiner-test | head -5
```

---

## Task 5: Create Separate Develop Database

- [ ] **Step 1: Dump production database**

```bash
PGPASSWORD=DrivePortal2024 pg_dump -h 127.0.0.1 -U drive_user -d drive_portal -F c -f /tmp/drive_portal_backup.dump
```

- [ ] **Step 2: Create and restore develop database**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d postgres -c "CREATE DATABASE drive_portal_dev OWNER drive_user;"
PGPASSWORD=DrivePortal2024 pg_restore -h 127.0.0.1 -U drive_user -d drive_portal_dev /tmp/drive_portal_backup.dump
```

- [ ] **Step 3: Verify table count**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

Expected: ~161 tables

- [ ] **Step 4: Update test config**

Edit `/opt/greiner-test/config/.env` line 49 — change `DB_NAME=drive_portal` to `DB_NAME=drive_portal_dev`

- [ ] **Step 5: Restart and verify**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
curl -s http://localhost:5001/ | head -3
rm /tmp/drive_portal_backup.dump
```

- [ ] **Step 6: Commit config change**

```bash
cd /opt/greiner-test
git add config/.env
git commit -m "$(cat <<'EOF'
feat(infrastruktur): separate Develop-Datenbank drive_portal_dev

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin develop
```

---

## Task 6: Write Consolidated CLAUDE.md

**File:** Rewrite `/opt/greiner-portal/CLAUDE.md`

Die neue CLAUDE.md ist das Kernstueck. Inhalt aus alter CLAUDE.md + .cursorrules konsolidiert, Sync entfernt, Git-Workflow rein.

- [ ] **Step 1: Write new CLAUDE.md**

Kompletter Inhalt — siehe Spec Abschnitt 4 fuer die Regeln was rein/raus kommt.
Wichtigste Aenderungen:
- Arbeitsumgebung: Tabelle mit Prod/Develop statt Sync-Architektur
- "Server ist Master" Abschnitt (aus .cursorrules)
- Git-Workflow Abschnitt (main/develop, Deploy, Hotfix)
- Services & Ports Tabelle (aus .cursorrules: Metabase, Flower, Redis)
- Zwei Datenbanken (drive_portal + drive_portal_dev)
- Diagnose-Befehle mit sudo -n und vollem Pfad
- Entfernt: Sync-Architektur, Deployment-Befehle (cp/rsync), SSH-Beispiele, Bootstrap 4
- SQL-Syntax Tabelle behalten (PostgreSQL)
- SSOT, Kein SQLite, Navigation, Workstreams — bleiben wie sie sind

- [ ] **Step 2: Commit**

```bash
cd /opt/greiner-portal
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(infrastruktur): konsolidierte CLAUDE.md fuer Claude Code Workflow

- Sync-Architektur entfernt (Windows-Sync abgeschafft)
- Git-Branch-Workflow dokumentiert (main/develop)
- Zwei Umgebungen mit separaten DBs
- Services & Ports Uebersicht
- Bootstrap auf 5.3 korrigiert

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Write All Skills

**Neue Skills erstellen:**
- `.claude/commands/hotfix.md`
- `.claude/commands/sync.md`

**Bestehende Skills umschreiben:**
- `.claude/commands/deploy.md`
- `.claude/commands/db.md`
- `.claude/commands/status.md`
- `.claude/commands/logs.md`
- `.claude/commands/test.md`
- `.claude/commands/fix.md`
- `.claude/commands/commit.md`
- `.claude/commands/session-start.md`
- `.claude/commands/session-end.md`
- `.claude/commands/feature.md`

- [ ] **Step 1: /deploy — Develop nach Produktion**

```markdown
# /deploy - Develop nach Produktion deployen

## Anweisungen

1. **Sicherheitschecks:**
   - Muss im Verzeichnis `/opt/greiner-test/` sein (develop)
   - `git status --short` — wenn uncommitted changes: STOPP

2. **Develop pushen:**
   ```bash
   cd /opt/greiner-test && git push origin develop
   ```

3. **In Produktion mergen:**
   ```bash
   cd /opt/greiner-portal && git checkout main && git pull origin main && git merge develop
   ```

4. **Restart + Push:**
   ```bash
   sudo -n /usr/bin/systemctl restart greiner-portal
   cd /opt/greiner-portal && git push origin main
   ```

5. **Verifizieren + Ergebnis anzeigen**

Bei Merge-Konflikten: STOPP und Florian fragen.
```

- [ ] **Step 2: /hotfix — Fix in Produktion + merge nach Develop**

```markdown
# /hotfix - Bug in Produktion fixen

## Anweisungen

1. **Check:** Muss auf `main` sein (`/opt/greiner-portal/`)
2. **Fix committen** auf main
3. **Restart:** `sudo -n /usr/bin/systemctl restart greiner-portal`
4. **Fix nach develop mergen:**
   ```bash
   cd /opt/greiner-test && git checkout develop && git merge main
   sudo -n /usr/bin/systemctl restart greiner-test
   ```
5. **Push beide:** main + develop
```

- [ ] **Step 3: /sync — Branch aktualisieren**

```markdown
# /sync - Aktuellen Branch aktualisieren

## Anweisungen
1. Branch + Verzeichnis anzeigen
2. Uncommitted changes pruefen (erst committen wenn noetig)
3. `git pull origin $(git rev-parse --abbrev-ref HEAD)`
4. Service neustarten falls Python-Dateien geaendert
```

- [ ] **Step 4: /status — Beide Umgebungen**

```markdown
# /status - Server & Service Status

## Anweisungen
1. Git: Branch + uncommitted changes fuer PROD und DEV
2. Services: greiner-portal, greiner-test, celery-worker, celery-beat, redis
3. DBs: drive_portal + drive_portal_dev erreichbar?
4. Letzte Fehler aus journalctl
5. Disk Space
```

- [ ] **Step 5: /logs — Direkt journalctl**

```markdown
# /logs - Server-Logs

## Anweisungen
Optionen:
1. Produktion: `sudo -n /usr/bin/journalctl -u greiner-portal --since "30 min ago" --no-pager | tail -50`
2. Develop: `sudo -n /usr/bin/journalctl -u greiner-test --since "30 min ago" --no-pager | tail -50`
3. Celery: `sudo -n /usr/bin/journalctl -u celery-worker ...`
4. Nur Fehler: `grep -i "error\|exception"`
5. Live: `sudo -n /usr/bin/journalctl -u greiner-portal -f`
```

- [ ] **Step 6: /db — PostgreSQL direkt**

```markdown
# /db - Datenbank-Abfragen

## Anweisungen
Erkennung anhand Arbeitsverzeichnis:
- `/opt/greiner-portal/` → drive_portal
- `/opt/greiner-test/` → drive_portal_dev

Befehle direkt (kein SSH):
- `PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d <DB> -c "[QUERY]"`
- Locosoft: `PGPASSWORD=loco psql -h 10.80.80.8 ...`

Sonderbefehl `/db refresh-dev`: Prod-DB nach Dev kopieren (pg_dump/pg_restore)

SELECT ohne Bestaetigung, INSERT/UPDATE/DELETE nur nach Rueckfrage.
```

- [ ] **Step 7: /test — Direkt curl**

```markdown
# /test - API-Endpoints testen

## Anweisungen
Erkennung:
- `/opt/greiner-portal/` → Port 5000
- `/opt/greiner-test/` → Port 5001

Health-Checks: `curl -s http://localhost:<PORT>/api/admin/health`
Custom: `curl -s http://localhost:<PORT>/[endpoint]`
JSON formatieren mit `python3 -m json.tool`
```

- [ ] **Step 8: /fix — Bug beheben**

```markdown
# /fix - Bug analysieren und beheben

## Anweisungen
1. Umgebung erkennen (main = Hotfix-Workflow, develop = normal)
2. Logs pruefen: `sudo -n /usr/bin/journalctl -u greiner-portal --since "1 hour ago" ...`
3. Code analysieren und fixen
4. Auf main: `/hotfix` vorschlagen
5. Auf develop: normaler `/commit`
```

- [ ] **Step 9: /commit — Git Commit**

```markdown
# /commit - Git Commit erstellen

## Anweisungen
1. Branch + Verzeichnis anzeigen (Prod oder Develop)
2. `git status --short` + `git diff --stat`
3. Format: `<type>(<workstream>): <Kurzbeschreibung>`
4. Types: feat, fix, docs, refactor, chore
5. Co-Author: `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`
6. Nach Commit: Push anbieten
```

- [ ] **Step 10: /session-start — Session starten**

```markdown
# /session-start - Neue Arbeitssession starten

## Anweisungen
1. Umgebung pruefen (Branch, Verzeichnis)
   - Warnung wenn in /opt/greiner-portal/ (sollte /opt/greiner-test/ sein)
2. CLAUDE.md lesen
3. Workstream-CONTEXT.md finden und lesen
4. Zusammenfassen: letzter Stand, offene Aufgaben
5. Fragen: Womit starten wir heute?
```

- [ ] **Step 11: /session-end — Session beenden**

```markdown
# /session-end - Arbeitssession beenden

## Anweisungen
1. CONTEXT.md des Workstreams aktualisieren
2. Git status pruefen, commit vorschlagen
3. Push auf aktuellen Branch
4. Merge-Status: Deploy noetig? Hotfix gemerged?
5. Keine SESSION_WRAP_UP oder TODO-Dateien erstellen
```

- [ ] **Step 12: /feature — Feature planen**

```markdown
# /feature - Neues Feature planen

## Anweisungen
1. Sollte auf develop sein
2. Anforderungen sammeln
3. Technische Analyse (Module, APIs, DB)
4. SSOT pruefen
5. In CONTEXT.md eintragen
6. Auf OK warten
```

- [ ] **Step 13: Commit all skills**

```bash
cd /opt/greiner-portal
git add .claude/commands/
git commit -m "$(cat <<'EOF'
feat(infrastruktur): alle Skills fuer neuen Git-Workflow

Neue: /hotfix, /sync
Umgeschrieben: /deploy, /db, /status, /logs, /test, /fix,
               /commit, /session-start, /session-end, /feature
- Kein SSH, kein Windows-Sync
- Erkennung Prod/Develop anhand Arbeitsverzeichnis

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update COMMANDS.md

- [ ] **Step 1: Rewrite `.claude/COMMANDS.md`**

Neue Uebersicht mit allen 12 Skills, Workflows (Feature, Hotfix, Sync), Umgebungstabelle.

- [ ] **Step 2: Commit**

```bash
cd /opt/greiner-portal
git add .claude/COMMANDS.md
git commit -m "$(cat <<'EOF'
docs(infrastruktur): COMMANDS.md fuer neuen Workflow

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Delete Cursor Files

- [ ] **Step 1: Remove .cursorrules and .cursor/**

```bash
cd /opt/greiner-portal
git rm .cursorrules
git rm -r .cursor/
```

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
chore(infrastruktur): entferne Cursor-Dateien (Migration zu Claude Code)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Clean Up settings.local.json

- [ ] **Step 1: Replace with minimal server-only permissions**

Entferne alle Windows-Pfade (`f:/Greiner Portal/...`), `powershell`, `dir`, `wmic`,
alte git-Befehle mit Windows-Pfaden. Behalte nur server-relevante Permissions:
git, python3, curl, ls, mkdir, wc, node, npx, WebSearch.

- [ ] **Step 2: Commit**

```bash
cd /opt/greiner-portal
git add .claude/settings.local.json
git commit -m "$(cat <<'EOF'
chore(infrastruktur): bereinige settings.local.json (Windows-Reste entfernt)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Remove Password from Windows CLAUDE.md

- [ ] **Step 1: Replace password line**

Edit `/mnt/greiner-portal-sync/CLAUDE.md` line 12.
Ersetze `**Sudo PW:** OHL.greiner2025` mit `**Sudo:** NOPASSWD via /etc/sudoers.d/greiner-portal`

- [ ] **Step 2: Verify**

```bash
grep -i "OHL\|greiner2025" /mnt/greiner-portal-sync/CLAUDE.md
```

Expected: keine Ausgabe

---

## Task 12: Write Workflow Guide

- [ ] **Step 1: Create `docs/WORKFLOW_ANLEITUNG.md`**

Inhalt:
- **Taeglich:** VS Code → SSH → /opt/greiner-test/ → /session-start → arbeiten → /commit → /session-end
- **Deploy:** /deploy (merged develop→main)
- **Hotfix:** Zweites Fenster → /opt/greiner-portal/ → fixen → /hotfix
- **Sync:** /sync (Vanessa holt Updates)
- **Dos & Don'ts Tabelle**
- **Befehlsuebersicht Tabelle**
- **Welcher Ordner wofuer** (ASCII-Diagramm)

- [ ] **Step 2: Commit**

```bash
cd /opt/greiner-portal
git add docs/WORKFLOW_ANLEITUNG.md
git commit -m "$(cat <<'EOF'
docs(infrastruktur): Workflow-Anleitung fuer Florian und Vanessa

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Push Everything and Sync Develop

- [ ] **Step 1: Push main**

```bash
cd /opt/greiner-portal && git push origin main
```

- [ ] **Step 2: Merge main into develop**

```bash
cd /opt/greiner-test && git checkout develop && git pull origin develop && git merge main
```

- [ ] **Step 3: Push develop**

```bash
cd /opt/greiner-test && git push origin develop
```

- [ ] **Step 4: Restart both services**

```bash
sudo -n /usr/bin/systemctl restart greiner-portal
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 5: Final verification**

```bash
echo "=== PROD ===" && git -C /opt/greiner-portal rev-parse --abbrev-ref HEAD && sudo -n /usr/bin/systemctl is-active greiner-portal
echo "=== DEV ===" && git -C /opt/greiner-test rev-parse --abbrev-ref HEAD && sudo -n /usr/bin/systemctl is-active greiner-test
echo "=== DBs ===" && PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT 'prod OK'" && PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "SELECT 'dev OK'"
```

Expected: main/active, develop/active, prod OK, dev OK

---

## Task 14: Clean Up Old Test Directory

- [ ] **Step 1: Archive (don't delete)**

```bash
sudo mv /data/greiner-test/ /data/greiner-test-archived-$(date +%Y%m%d)/
```

- [ ] **Step 2: Verify**

```bash
ls /data/greiner-test/ 2>&1
```

Expected: "No such file or directory"
