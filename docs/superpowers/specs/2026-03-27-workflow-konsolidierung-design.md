# Design: Workflow-Konsolidierung & CLAUDE.md

**Datum:** 2026-03-27
**Status:** Genehmigt
**Scope:** Git-Workflow, Umgebungen, CLAUDE.md, Skills, Datenbank

---

## Hintergrund

Migration von Cursor Native AI zu Claude Code (VS Code Extension, Remote-SSH).
Der alte Workflow (Windows-Sync, ein Branch, eine DB) hat zu Chaos geführt:
- Dateien gingen "verloren" beim Branch-Wechsel
- Prod und Test teilen dieselbe Datenbank
- 3 Config-Dateien (CLAUDE.md, Windows-CLAUDE.md, .cursorrules) mit Widersprüchen
- Skills basieren auf SSH und Windows-Sync
- Sudo-Passwort im Klartext in Windows-CLAUDE.md

## Entscheidungen

- **Ansatz A gewählt:** Git-Branch-Workflow mit main/develop
- **Kein Windows-Sync** mehr (abgeschafft)
- **Kein Cursor** mehr (.cursorrules und .cursor/ werden entfernt)
- **Bootstrap 5.3.0** bestätigt (nicht 4)
- **Test-Umgebung** heißt ab jetzt "Develop"

---

## 1. Git-Branch-Strategie

```
main ─────●─────●─────●─────●──── (Produktion: drive, Port 5000)
           \         ↑         \
            \     git merge     \ hotfix
             \       |           ↘
develop ──────●─────●─────●──────●── (Develop: drive:5002)
               \
                feature/xyz (optional, fuer groessere Features)
```

### Regeln

| Regel | Details |
|-------|---------|
| `main` = Produktion | Nur getesteter Code, nur ueber Merge von `develop` oder Hotfix |
| `develop` = Entwicklung | Hier wird entwickelt und getestet (Florian + Vanessa) |
| Hotfixes auf `main` | Florian fixt direkt auf `main`, merged danach sofort nach `develop` |
| Kein direktes Editieren auf `main` | Ausser Hotfixes durch Florian |
| Feature-Branches | Optional, von `develop` abzweigen |
| Kein force-push | Nie, ohne Ruecksprache |

### Deploy-Workflow (develop -> Produktion)

1. Entwicklung in `develop` (auf `/opt/greiner-test/`)
2. Testen auf `drive:5002`
3. Wenn gut: In `/opt/greiner-portal/` wechseln
4. `git checkout main && git merge develop`
5. `sudo -n /usr/bin/systemctl restart greiner-portal`
6. Fertig

### Hotfix-Workflow (Fix in Produktion)

1. Florian fixt auf `main` (direkt in `/opt/greiner-portal/`)
2. Commit auf `main`
3. `cd /opt/greiner-test && git merge main`
4. Restart beider Services
5. Develop hat den Fix auch

---

## 2. Umgebungen

### Uebersicht

| | Produktion | Develop |
|--|---|---|
| URL | `http://drive` | `http://drive:5002` |
| Pfad | `/opt/greiner-portal/` | `/opt/greiner-test/` |
| Branch | `main` | `develop` |
| Datenbank | `drive_portal` | `drive_portal_dev` |
| Service | `greiner-portal.service` | `greiner-test.service` |
| Port (intern) | 5000 | 5001 (extern 5002) |
| Wer arbeitet | Florian (nur Hotfixes) | Florian + Vanessa |

### Weitere Services

| Service | Port | Beschreibung |
|---------|------|-------------|
| Metabase | 3001 | Business Intelligence |
| Flower | 5555 | Celery Monitoring |
| Redis | 6379 | Message Broker |

### VS Code Setup

- VS Code auf Windows, verbunden per SSH zu 10.80.80.20
- **Normalfall:** Workspace auf `/opt/greiner-test/` (Develop)
- **Hotfix:** Zweites VS Code Fenster auf `/opt/greiner-portal/` (Prod)
- Claude Code Extension laeuft auf dem Server (via Remote-SSH)

---

## 3. Datenbank-Trennung

### Aktuelle Situation (Problem)

Beide Umgebungen nutzen `drive_portal` — Test-Daten landen in Produktion.

### Neue Situation

| | Produktion | Develop |
|--|---|---|
| PostgreSQL DB | `drive_portal` | `drive_portal_dev` |
| Locosoft | `10.80.80.8` (read-only, geteilt) | `10.80.80.8` (read-only, geteilt) |
| Config | `/opt/greiner-portal/config/.env` | `/opt/greiner-test/config/.env` |

### Synchronisation

- Einmalig: `pg_dump drive_portal | pg_restore drive_portal_dev`
- Bei Bedarf: `/db refresh-dev` Skill fuer manuellen Refresh
- Migrationen (`migrations/*.sql`) muessen auf beiden DBs laufen

---

## 4. CLAUDE.md Konsolidierung

### Was rausfliegt

| Raus | Warum |
|------|-------|
| Sync-Architektur Abschnitt | Windows-Sync abgeschafft |
| Deployment-Befehle (cp/rsync) | Ersetzt durch Git-Workflow |
| `/mnt/greiner-portal-sync/` Referenzen | Obsolet |
| Sudo-PW im Klartext | Sicherheitsrisiko |
| SQLite-Referenzen in DB-Abschnitt | Seit TAG 135 PostgreSQL |
| SSH-Befehle in Beispielen | Claude laeuft direkt auf Server |
| Bootstrap 4 Referenz | Ist 5.3.0 |

### Was reinkommt

| Neu | Inhalt |
|-----|--------|
| "Server ist Master" | Klare Ansage, kein Windows-Sync |
| Git-Branch-Workflow | main = Prod, develop = Dev, Regeln |
| Zwei Umgebungen | Prod + Develop mit Pfaden, Ports, Branches |
| Separate DBs | drive_portal + drive_portal_dev |
| Services & Ports | Alle Services mit Ports |
| Git-Regeln | Keine force-pushes, Commit-Format |
| Deploy/Hotfix Workflow | Kurzbeschreibung mit Verweis auf Skills |

### Dateien-Schicksal

| Datei | Aktion |
|-------|--------|
| `/opt/greiner-portal/CLAUDE.md` | Konsolidiert neu schreiben |
| `/opt/greiner-portal/.cursorrules` | Loeschen |
| `/opt/greiner-portal/.cursor/` | Loeschen |
| `/mnt/greiner-portal-sync/CLAUDE.md` | Passwort entfernen |
| `.claude/COMMANDS.md` | Aktualisieren |
| `settings.local.json` | Windows-Permissions aufraeumen |

---

## 5. Skills (Slash-Commands)

### Komplett neu geschrieben

| Skill | Was er tut |
|-------|-----------|
| `/deploy` | Merged `develop` nach `main`, restartet Produktion. Prueft: uncommitted changes, korrekter Branch |
| `/hotfix` | Committed Fix auf `main`, merged nach `develop`, restartet beide Services |
| `/db` | Direkt PostgreSQL (kein SSH, kein SQLite). Erkennt Prod/Dev anhand Arbeitsverzeichnis |
| `/status` | Branch, Services, DB-Status, uncommitted changes — direkte Befehle |
| `/logs` | Direkt journalctl, kein SSH |
| `/test` | Direkt curl gegen localhost, kein SSH |
| `/fix` | Direkt, erkennt ob main oder develop |
| `/sync` | `git pull` auf aktuellem Branch — fuer Vanessa wenn Florian gepusht hat |

### Ueberarbeitet

| Skill | Aenderung |
|-------|----------|
| `/commit` | Co-Author auf Opus 4.6, Workstream-Format statt TAG-Format |
| `/session-start` | Prueft Branch/Umgebung, entfernt Sync-Referenzen |
| `/session-end` | Entfernt Sync-Reminder, prueft ob merge noetig |
| `/feature` | Minimal angepasst, funktioniert schon gut |

### Sicherheitsmechanismen

- `/deploy` prueft: "Bin ich auf develop?" und "Gibt es uncommitted changes?"
- `/hotfix` prueft: "Bin ich auf main?"
- `/commit` zeigt an ob Prod oder Develop
- Kein Skill fuehrt force-push aus

---

## 6. Anleitung (Florian & Vanessa)

Wird als `docs/WORKFLOW_ANLEITUNG.md` erstellt.

### Inhalt

| Abschnitt | Beschreibung |
|-----------|-------------|
| Taegliche Arbeit | VS Code oeffnen, SSH, `/opt/greiner-test/`, entwickeln |
| Feature fertig | `/deploy` eintippen |
| Bug in Produktion | Florian wechselt auf `/opt/greiner-portal/`, fixt, `/hotfix` |
| Vanessa holt Updates | `/sync` |
| Dos & Don'ts | Nie direkt in Prod entwickeln, immer committen vor Branch-Wechsel |

---

## 7. Einmalige Umsetzungsschritte (Reihenfolge)

1. **Alles committen** — 181 untracked files in Prod + 3 geaenderte in Test
2. **`feature/tag112-onwards` nach `main` mergen** — Fast-forward, kein Risiko
3. **`develop` Branch von `main` neu aufsetzen**
4. **`drive_portal_dev` Datenbank erstellen** — pg_dump/pg_restore
5. **`/opt/greiner-test/config/.env`** auf `drive_portal_dev` umstellen
6. **`/opt/greiner-test/`** auf `develop` Branch setzen
7. **CLAUDE.md** konsolidiert neu schreiben
8. **Skills** alle neu schreiben
9. **`.cursorrules` und `.cursor/`** loeschen
10. **`settings.local.json`** bereinigen
11. **Windows-CLAUDE.md** Passwort entfernen
12. **`/data/greiner-test/`** aufraeuemen (alter toter Pfad)
13. **`docs/WORKFLOW_ANLEITUNG.md`** erstellen
14. **Beide Services restarten** und verifizieren
15. **Git push** beide Branches

---

## Risiken & Mitigationen

| Risiko | Mitigation |
|--------|-----------|
| Merge-Konflikte bei main-Merge | main ist Untermenge von feature/tag112-onwards, Fast-forward moeglich |
| Develop-DB divergiert von Prod | `/db refresh-dev` Skill fuer manuellen Reset |
| Vanessa arbeitet versehentlich in Prod | VS Code Workspace Default = `/opt/greiner-test/` |
| Hotfix vergessen nach develop zu mergen | `/hotfix` Skill macht es automatisch |
| Migrationen nur auf einer DB | Skills erinnern, auf beiden auszufuehren |
