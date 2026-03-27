# Claude Code Custom Commands - Greiner Portal DRIVE

## Uebersicht

| Command | Beschreibung | Wer |
|---------|-------------|-----|
| `/deploy` | Develop nach Produktion deployen | Florian |
| `/hotfix` | Bug in Produktion fixen + nach Develop mergen | Florian |
| `/sync` | Aktuellen Branch aktualisieren (git pull) | Alle |
| `/status` | Service-Status beider Umgebungen | Alle |
| `/logs` | Server-Logs anzeigen | Alle |
| `/db` | PostgreSQL-Abfragen (erkennt Prod/Dev) | Alle |
| `/test` | API-Endpoints testen | Alle |
| `/fix` | Bug analysieren und beheben | Alle |
| `/commit` | Git Commit erstellen | Alle |
| `/feature` | Neues Feature planen | Alle |
| `/session-start` | Arbeitssession starten | Alle |
| `/session-end` | Arbeitssession beenden | Alle |

## Workflows

### Feature entwickeln (Normalfall)
1. `/session-start` - Kontext laden
2. Entwickeln in `/opt/greiner-test/` (develop)
3. `/commit` - Aenderungen committen
4. `/deploy` - Nach Produktion deployen
5. `/session-end` - Session beenden

### Bug in Produktion fixen
1. In `/opt/greiner-portal/` wechseln
2. `/fix` - Bug finden und beheben
3. `/hotfix` - Fix committen + nach Develop mergen

### Aenderungen holen
1. `/sync` - Neueste Version vom Remote holen

## Umgebungen

| | Produktion | Develop |
|--|---|---|
| URL | http://drive | http://drive:5002 |
| Pfad | /opt/greiner-portal/ | /opt/greiner-test/ |
| Branch | main | develop |
| DB | drive_portal | drive_portal_dev |
| Port | 5000 | 5001 (extern 5002) |
