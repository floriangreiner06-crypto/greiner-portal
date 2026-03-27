# /session-start - Neue Arbeitssession starten

Laedt den Kontext der letzten Session und bereitet die Arbeit vor.

## Schritt 1: Umgebung pruefen

```bash
pwd && git branch --show-current
```

Warnung ausgeben wenn aktuelles Verzeichnis `/opt/greiner-portal/` ist (Production):
"Achtung: Du arbeitest gerade in der Production-Umgebung (main). Fuer neue Features und normale Entwicklung besser in /opt/greiner-test/ (develop) arbeiten."

## Schritt 2: CLAUDE.md lesen

`/opt/greiner-portal/CLAUDE.md` lesen -- dort stehen alle Architektur-Regeln, DB-Zugaenge und Standards.

## Schritt 3: Workstream-Kontext laden

Den User fragen: "An welchem Workstream arbeitest du heute?"

Verfuegbare Workstreams: `controlling`, `verkauf`, `werkstatt`, `urlaubsplaner`, `hr`, `teile-lager`, `planung`, `finanzierungen`, `infrastruktur`, `auth-ldap`, `integrations`, `marketing`, `verguetung`

Passende CONTEXT.md lesen:

```
/opt/greiner-portal/docs/workstreams/[workstream]/CONTEXT.md
```

Falls kein Workstream angegeben: die juengste git-Aktivitaet pruefen:

```bash
cd /opt/greiner-portal && git log --oneline -5
```

## Schritt 4: Letzten Stand zusammenfassen

Aus der CONTEXT.md ausgeben:
- Was wurde zuletzt implementiert
- Welche Aufgaben sind offen
- Bekannte Probleme oder Blocker
- Aktuelle Architektur-Entscheidungen

## Schritt 5: Service-Status kurz pruefen

```bash
sudo -n /usr/bin/systemctl is-active greiner-portal greiner-test celery-worker 2>/dev/null
```

Wenn ein Service nicht laeuft: sofort melden.

## Schritt 6: Fragen

Den User fragen:
- Womit sollen wir heute starten?
- Gibt es neue Anforderungen oder Prioritaeten?
- Gibt es Fehler oder Probleme die zuerst behoben werden muessen?

## SSOT-Erinnerung

Vor der Implementierung immer pruefen:

- DB-Verbindungen: `api/db_connection.py` -> `get_db()` (DRIVE), `api/db_utils.py` -> `get_locosoft_connection()` (Locosoft)
- Standort-Logik: `api/standort_utils.py`
- TEK-Berechnungen: `api/controlling_data.py` -> `get_tek_data()`
- Kein SQLite, kein `sqlite3`, keine parallele DB-Logik
- PostgreSQL-Syntax: `%s`, `true`, `CURRENT_DATE`, `EXTRACT(YEAR FROM ...)`

## Nicht tun

- Keine SESSION_WRAP_UP-Dateien lesen (veraltet, ersetzt durch CONTEXT.md)
- Keine TODO_FOR_CLAUDE-Dateien anlegen
- Nicht automatisch Code aendern -- erst verstehen, dann fragen
