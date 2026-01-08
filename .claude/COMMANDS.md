# Claude Code Custom Commands - Greiner Portal

Diese Slash-Commands sind im Ordner `.claude/commands/` definiert und funktionieren in Claude Code (Terminal & Cursor).

---

## Übersicht

| Command | Beschreibung |
|---------|--------------|
| `/deploy` | Dateien auf Server syncen |
| `/status` | Server & Service Status prüfen |
| `/logs` | Server-Logs anzeigen |
| `/db` | Datenbank-Abfragen ausführen |
| `/test` | API-Endpoints testen |
| `/commit` | Git Commit erstellen |
| `/fix` | Bug analysieren & beheben |
| `/feature` | Neues Feature planen |
| `/session-start` | Arbeitssession starten |
| `/session-end` | Arbeitssession beenden |

---

## Command Details

### `/deploy` - Server Sync
Synchronisiert geänderte Dateien auf den Linux-Server.
- Prüft git status
- Fragt welche Dateien/Ordner
- Führt sync via SSH aus
- Erinnert an Neustart bei Python-Änderungen

### `/status` - Server Status
Zeigt den aktuellen Status:
- Service Health Check
- Celery Worker Status
- Redis Status
- Disk Space
- Letzte Log-Einträge

### `/logs` - Logs anzeigen
Optionen:
- Portal-Logs (Standard)
- Celery Worker Logs
- Nur Errors
- Live-Logs (Follow)

### `/db` - Datenbank
Datenbank-Abfragen auf:
- **SQLite** (greiner_controlling.db)
- **PostgreSQL** (Locosoft)

Häufige Abfragen:
- User mit Rollen
- Letzte Logins
- Tabellen-Liste

### `/test` - API testen
Testet API-Endpoints:
- Health-Checks
- Custom Endpoints
- POST-Requests mit JSON

### `/commit` - Git Commit
Erstellt strukturierte Commits:
- Prüft Status & Diff
- Analysiert Änderungen
- Format: `<type>(TAG[X]): <Beschreibung>`
- Types: feat, fix, docs, refactor, style, chore

### `/fix` - Bug beheben
Workflow:
1. Bug-Beschreibung sammeln
2. Logs prüfen
3. Code-Analyse
4. Fix implementieren
5. Testen
6. Dokumentieren

### `/feature` - Feature planen
Workflow:
1. Anforderungen sammeln
2. Technische Analyse
3. Architektur-Check
4. Todo-Liste erstellen
5. Komplexitäts-Einschätzung

### `/session-start` - Session starten
- Liest CLAUDE.md
- Findet letzte Session-Docs
- Fasst offene Aufgaben zusammen
- Bestimmt aktuelle TAG-Nummer

### `/session-end` - Session beenden
- Erstellt SESSION_WRAP_UP_TAG[X].md
- Erstellt TODO_FOR_CLAUDE_SESSION_START_TAG[X+1].md
- Prüft git status
- Erinnert an Server-Sync

---

## Server-Details

| Info | Wert |
|------|------|
| Host | 10.80.80.20 |
| User | ag-admin |
| Sync-Quelle | /mnt/greiner-portal-sync/ |
| Ziel | /opt/greiner-portal/ |
| SQLite | /opt/greiner-portal/data/greiner_controlling.db |
| PostgreSQL | 10.80.80.8:5432 (loco_auswertung_db) |

---

## Verwendung

Einfach im Claude Code Chat eingeben:
```
/status
```

Oder mit Parametern:
```
/logs letzte stunde
/db SELECT * FROM users LIMIT 5
```

---

*Erstellt: TAG 134 (23.12.2025)*
