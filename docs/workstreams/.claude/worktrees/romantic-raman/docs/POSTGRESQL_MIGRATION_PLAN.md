# PostgreSQL Migration Plan - DRIVE Portal

**Erstellt:** TAG 135 (23.12.2024)
**Status:** Geplant

---

## 1. Ist-Analyse

### Aktuelle SQLite-Datenbank
| Kennzahl | Wert |
|----------|------|
| Dateigröße | 896 MB |
| Anzahl Tabellen | 183 |
| Anzahl Dateien mit sqlite3 | 125 |
| Haupttabelle (fibu_buchungen) | 549.224 Zeilen |

### Top-Tabellen nach Datenmenge
| Tabelle | Zeilen | Beschreibung |
|---------|--------|--------------|
| fibu_buchungen | 549.224 | FIBU-Buchungen (Controlling) |
| transaktionen | 16.614 | Bankenspiegel-Transaktionen |
| sales | 5.015 | Verkaufsaufträge |
| vacation_bookings | 1.369 | Urlaubsbuchungen |
| dealer_vehicles | 1.226 | Fahrzeugbestand |
| employees | 79 | Mitarbeiter |
| users | 18 | Portal-Benutzer |

### Datenstruktur-Analyse
- **Relationale Beziehungen:** Stark ausgeprägt (employees ↔ sales ↔ vehicles)
- **Transaktionen:** Kritisch für Finanzdaten (ACID erforderlich)
- **Aggregationen:** Häufig (SUM, GROUP BY für Reports)
- **JOINs:** 3-5 Tabellen typisch (TEK, BWA, Controlling)
- **Zeitreihen:** Monatliche Snapshots, tägliche Buchungen

---

## 2. Empfehlung: PostgreSQL (nicht MongoDB)

### Gründe für PostgreSQL

| Kriterium | PostgreSQL | MongoDB | Bewertung |
|-----------|------------|---------|-----------|
| Relationale Daten | Native Unterstützung | Erfordert Denormalisierung | PostgreSQL |
| ACID-Transaktionen | Vollständig | Nur auf Dokument-Ebene | PostgreSQL |
| JOINs | Optimiert | Manuell via $lookup | PostgreSQL |
| Aggregationen | SQL-Native | Aggregation Pipeline | PostgreSQL |
| Migration von SQLite | Trivial (gleiche SQL-Syntax) | Komplett-Umbau nötig | PostgreSQL |
| Finanz-Compliance | Branchenstandard | Nicht typisch | PostgreSQL |

### Gründe gegen MongoDB für DRIVE
1. **Alle Daten sind relational** - keine Document-Struktur erkennbar
2. **Finanz-Reporting braucht ACID** - MongoDB bietet das nur eingeschränkt
3. **Migration wäre massiver Umbau** - jede SQL-Query müsste neu geschrieben werden
4. **Keine Vorteile** - kein Schema-Flexibilität oder Horizontal-Scaling nötig

---

## 3. Migrations-Strategie

### Phase 1: Vorbereitung (1-2 Stunden)
```bash
# PostgreSQL auf Server installieren
sudo apt install postgresql postgresql-contrib

# Datenbank und User anlegen
sudo -u postgres psql
CREATE DATABASE drive_portal;
CREATE USER drive_user WITH ENCRYPTED PASSWORD 'xxx';
GRANT ALL PRIVILEGES ON DATABASE drive_portal TO drive_user;
```

### Phase 2: Schema-Migration
```bash
# SQLite-Schema exportieren
sqlite3 greiner_controlling.db .schema > schema.sql

# SQLite → PostgreSQL Schema-Konvertierung
# Änderungen:
# - INTEGER PRIMARY KEY → SERIAL PRIMARY KEY
# - AUTOINCREMENT → entfernen (SERIAL macht das)
# - TEXT → VARCHAR oder TEXT
# - DATETIME → TIMESTAMP
# - BOOLEAN → BOOLEAN (SQLite hat 0/1)
```

### Phase 3: Daten-Migration
```bash
# Für jede Tabelle:
sqlite3 -csv greiner_controlling.db "SELECT * FROM employees" > employees.csv
psql -d drive_portal -c "\COPY employees FROM 'employees.csv' CSV HEADER"

# Oder mit pgloader (automatisch):
pgloader sqlite:///opt/greiner-portal/data/greiner_controlling.db \
         postgresql://drive_user:xxx@localhost/drive_portal
```

### Phase 4: Code-Anpassung

#### Option A: Minimaler Umbau (empfohlen)
Erstelle `api/db_connection.py`:
```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'drive_portal'),
    'user': os.getenv('DB_USER', 'drive_user'),
    'password': os.getenv('DB_PASSWORD', 'xxx')
}

def get_db():
    """PostgreSQL-Verbindung mit Dict-Cursor (wie sqlite3.Row)"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = RealDictCursor
    return conn
```

#### Anpassungen in bestehenden Dateien:
```python
# ALT (in ~125 Dateien):
import sqlite3
conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
conn.row_factory = sqlite3.Row

# NEU:
from api.db_connection import get_db
conn = get_db()
```

#### SQL-Syntax-Änderungen:
| SQLite | PostgreSQL |
|--------|------------|
| `strftime('%Y', date)` | `EXTRACT(YEAR FROM date)` oder `TO_CHAR(date, 'YYYY')` |
| `date('now')` | `CURRENT_DATE` |
| `datetime('now')` | `NOW()` |
| `||` (String concat) | Bleibt gleich |
| `LIMIT x OFFSET y` | Bleibt gleich |

### Phase 5: Parallelbetrieb & Test
1. SQLite bleibt als Backup
2. PostgreSQL parallel laufen lassen
3. Read-Queries auf PostgreSQL umleiten
4. Write-Queries auf beide (Dual-Write)
5. Nach 1 Woche: Nur noch PostgreSQL

---

## 4. Aufwands-Schätzung

### Einmaliger Aufwand
| Aufgabe | Dateien/Queries |
|---------|-----------------|
| PostgreSQL Setup | 1 Stunde |
| Schema-Migration | 183 Tabellen (automatisierbar) |
| Daten-Migration | pgloader (< 1 Stunde für 900 MB) |
| db_connection.py erstellen | 1 Datei |
| Import-Statements ändern | ~40 aktive Dateien |
| SQL-Syntax-Fixes | ~20-30 Queries |

### Kritische Dateien (zuerst migrieren)
1. `api/db_utils.py` - Zentrale DB-Helfer
2. `api/controlling_api.py` - TEK, BWA
3. `api/vacation_api.py` - Urlaubsplaner
4. `api/verkauf_api.py` - Sales
5. `api/werkstatt_live_api.py` - Werkstatt
6. `scheduler/job_manager.py` - Jobs
7. `reports/registry.py` - Report-Subscriptions

---

## 5. Vorteile nach Migration

| Vorteil | Beschreibung |
|---------|--------------|
| **Performance** | Echte Parallelität, Connection Pooling |
| **Skalierbarkeit** | Multi-User ohne DB-Locks |
| **Backup** | pg_dump, Point-in-Time Recovery |
| **Monitoring** | pg_stat_statements, EXPLAIN ANALYZE |
| **Erweiterungen** | PostGIS (Geo), TimescaleDB (Zeitreihen) |
| **Professioneller Standard** | Audit, Compliance, Branchenstandard |

---

## 6. Empfohlene Reihenfolge

1. **Jetzt:** Report-Subscription-System fertig testen (SQLite)
2. **TAG 136-137:** PostgreSQL Setup + pgloader-Migration
3. **TAG 138-139:** Zentrale APIs umstellen (db_utils, controlling, verkauf)
4. **TAG 140+:** Restliche Dateien iterativ umstellen
5. **Nach 1 Woche Parallelbetrieb:** SQLite abschalten

---

## 7. Rollback-Plan

Falls Probleme auftreten:
1. `.env` auf SQLite zurücksetzen: `DB_TYPE=sqlite`
2. Alle Writes gehen wieder an SQLite
3. PostgreSQL-Daten bei Bedarf zurück-syncen

---

**Fazit:** PostgreSQL ist die richtige Wahl. Die Migration ist überschaubar (40 aktive Dateien, 1-2 Wochen mit Tests). MongoDB würde einen kompletten Umbau erfordern ohne erkennbaren Vorteil für das DRIVE-Portal.
