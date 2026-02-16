# PostgreSQL Datenbank-Schema - DRIVE Portal

**Stand:** 2025-12-29 (TAG 143)
**Migration abgeschlossen:** TAG 135-139

---

## Datenbank-Übersicht

| Datenbank | Host | Port | Beschreibung |
|-----------|------|------|--------------|
| **drive_portal** | 127.0.0.1 | 5432 | DRIVE Portal Hauptdatenbank |
| **loco_auswertung_db** | 10.80.80.8 | 5432 | Locosoft Auswertungs-DB (extern, read-only) |

### Zugangsdaten

```bash
# DRIVE Portal (lokal)
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal

# Locosoft (extern)
PGPASSWORD=loco psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db
```

### Konfiguration (.env)

```ini
DB_TYPE=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=drive_portal
DB_USER=drive_user
DB_PASSWORD=DrivePortal2024
```

---

## Tabellen-Statistik

| Metrik | Wert |
|--------|------|
| Anzahl Tabellen | 161 |
| Gesamtgröße | ~1 GB |
| Größte Tabelle | loco_parts_master (333 MB) |

### Top 10 Tabellen nach Größe

| Tabelle | Größe | Beschreibung |
|---------|-------|--------------|
| loco_parts_master | 333 MB | Teile-Stammdaten aus Locosoft |
| loco_journal_accountings | 246 MB | FIBU-Buchungen aus Locosoft |
| fibu_buchungen | 84 MB | FIBU-Buchungen (Controlling) |
| loco_labours | 35 MB | Arbeitsleistungen |
| loco_times | 20 MB | Zeiterfassung |
| loco_parts | 19 MB | Teile (aktuelle) |
| loco_vehicles | 18 MB | Fahrzeuge |
| loco_customers_suppliers | 11 MB | Kunden/Lieferanten |
| transaktionen | 5.6 MB | Bank-Transaktionen |
| werkstatt_auftraege_abgerechnet | 3.3 MB | Abgerechnete Aufträge |

---

## Tabellen nach Modul

### Finanzen & Controlling

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `banken` | Bankstammdaten | 7 |
| `konten` | Bankkonten | 12 |
| `transaktionen` | Bank-Transaktionen (MT940) | ~50.000 |
| `salden` | Tages-Salden | ~500 |
| `fibu_buchungen` | FIBU-Buchungen | ~550.000 |
| `bwa_monatswerte` | BWA-Monatswerte | ~100 |
| `fahrzeugfinanzierungen` | EK-Finanzierungen | ~200 |
| `afa_anlagevermoegen` | VFW/Mietwagen Anlagevermögen (AfA) | — |
| `afa_buchungen` | Monatliche AfA-Buchungen (Historie) | — |
| `tilgungen` | Tilgungsplan | ~1.000 |
| `ek_finanzierung_konditionen` | Zinskonditionen | 3 |
| `finanzierungsbanken` | Stellantis, Santander etc. | 3 |
| `santander_zins_staffel` | Santander Zinsstaffel | ~10 |

### Verkauf

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `dealer_vehicles` | Verkaufte Fahrzeuge (Cache) | ~1.200 |
| `loco_dealer_vehicles` | Locosoft Fahrzeugbestand | ~2.000 |
| `vehicles` | Fahrzeug-Stammdaten | ~500 |
| `sales` | Verkäufe (alt) | ~1.000 |
| `leasys_vehicle_cache` | Leasys Programm-Cache | ~170 |
| `budget_plan` | **NEU TAG 143** Verkaufs-Budget | ~72/Jahr |
| `stellantis_bestellungen` | Bestellungen | ~100 |
| `stellantis_positionen` | Bestellpositionen | ~500 |

### Werkstatt & Service

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `loco_orders` | Werkstattaufträge | ~10.000 |
| `loco_labours` | Arbeitsleistungen | ~100.000 |
| `loco_times` | Zeitbuchungen (Stempeluhr) | ~50.000 |
| `werkstatt_auftraege_abgerechnet` | Abgerechnete Aufträge | ~5.000 |
| `werkstatt_leistung_daily` | Tägliche Werkstatt-KPIs | ~1.000 |
| `unfall_checkliste_positionen` | Kürzungspositionen-Checkliste (M4) | 12 |
| `unfall_urteile` | Rechtsprechung Wissensdatenbank (M4) | ~10 |
| `unfall_urteile_checkliste` | n:n Urteil ↔ Checklistenposition | ~10 |
| `unfall_versicherungen` | Versicherungen Stammdaten | 0 |
| `unfall_versicherung_kunden` | Whitelist Versicherungskunden (M1) | ~125 |
| `unfall_gutachten` | Sachverständigengutachten pro Auftrag (PDF) | 0 |
| `unfall_gutachten_positionen` | AI-extrahiert aus Gutachten, Abgleich Rechnung | 0 |
| `unfall_textbausteine` | UE IWW Textbausteine (ue.iww.de) | ~700+ nach Scrape |
| `unfall_textbausteine_positionen` | TB ↔ Checklistenposition | ~30+ nach Seed |
| `unfall_rechnungen` | Unfallrechnungen (Kopf) | 0 |
| `unfall_positionen` | Positionen pro Rechnung | 0 |
| `unfall_kuerzungen` | Kürzungen pro Rechnung/Prüfbericht | 0 |

### Teile & Lager

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `loco_parts_master` | Teile-Stammdaten | ~500.000 |
| `loco_parts` | Aktuelle Teile | ~50.000 |
| `loco_parts_stock` | Lagerbestand | ~10.000 |
| `teile_lieferscheine` | ServiceBox-Lieferscheine | ~5.000 |
| `penner_marktpreise` | Marktpreise für Ladenhüter | ~1.000 |

### HR / Personal

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `employees` | Mitarbeiter-Stammdaten | 76 |
| `loco_employees` | Locosoft Mitarbeiter | ~80 |
| `vacation_bookings` | Urlaubsbuchungen | ~500 |
| `vacation_entitlements` | Urlaubsansprüche | ~80 |
| `vacation_approval_rules` | Genehmigungsregeln | ~20 |
| `holidays` | Feiertage | ~40 |
| `loco_absence_calendar` | Abwesenheitskalender | ~15.000 |
| `manager_assignments` | Vorgesetzten-Zuordnung | ~30 |

### Auth & Admin

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `users` | Benutzer | ~50 |
| `roles` | Rollen | ~10 |
| `user_roles` | Benutzer-Rollen-Zuordnung | ~100 |
| `ldap_employee_mapping` | LDAP-Mapping | 62 |
| `ad_group_role_mapping` | AD-Gruppen-Rollen | ~10 |
| `sessions` | User-Sessions | ~100 |
| `audit_log` | Audit-Log | ~1.000 |
| `report_subscriptions` | E-Mail-Report-Abos | ~20 |

### System & Sync

| Tabelle | Beschreibung | Zeilen (ca.) |
|---------|--------------|--------------|
| `sync_status` | Sync-Status pro Tabelle | ~50 |
| `sync_log` | Sync-Protokoll | ~1.000 |
| `system_jobs` | Celery Jobs | ~30 |
| `system_job_history` | Job-Historie | ~5.000 |
| `import_log` | Import-Protokoll | ~100 |

---

## Wichtige Tabellen-Schemas

### budget_plan (TAG 143)

```sql
CREATE TABLE budget_plan (
    id SERIAL PRIMARY KEY,
    jahr INTEGER NOT NULL,
    monat INTEGER NOT NULL,           -- 1-12
    standort INTEGER NOT NULL,         -- 1=DEG, 2=HYU, 3=LAN
    typ VARCHAR(2) NOT NULL,           -- 'NW' oder 'GW'
    stueck_plan INTEGER DEFAULT 0,
    umsatz_plan DECIMAL(15,2) DEFAULT 0,
    db1_plan DECIMAL(15,2) DEFAULT 0,
    marge_plan DECIMAL(5,2) DEFAULT 0,
    kommentar TEXT,
    erstellt_von VARCHAR(100),
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jahr, monat, standort, typ)
);

CREATE INDEX idx_budget_jahr ON budget_plan(jahr);
CREATE INDEX idx_budget_jahr_standort ON budget_plan(jahr, standort);
```

### employees

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    employee_number VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    department_id INTEGER,
    position VARCHAR(100),
    manager_id INTEGER,
    subsidiary INTEGER,              -- 1=DEG, 2=HYU, 3=LAN
    hire_date DATE,
    vacation_days_per_year INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT true,
    ldap_username VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### vacation_bookings

```sql
CREATE TABLE vacation_bookings (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    vacation_type VARCHAR(50),        -- urlaub, krank, sonder, etc.
    status VARCHAR(20),               -- pending, approved, rejected
    days_used DECIMAL(4,1),
    comment TEXT,
    approved_by INTEGER,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### fahrzeugfinanzierungen

```sql
CREATE TABLE fahrzeugfinanzierungen (
    id SERIAL PRIMARY KEY,
    fahrzeug_id VARCHAR(50),
    vin VARCHAR(17),
    kennzeichen VARCHAR(20),
    marke VARCHAR(50),
    modell VARCHAR(100),
    bank VARCHAR(50),                 -- 'stellantis', 'santander'
    finanzierungsbetrag DECIMAL(12,2),
    zins_aktuell DECIMAL(5,2),
    zins_frei_bis DATE,
    eingang_datum DATE,
    status VARCHAR(20),               -- 'aktiv', 'abgeloest', 'verkauft'
    standort INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Locosoft-Tabellen (loco_*)

Alle Tabellen mit Prefix `loco_` werden von Locosoft gespiegelt.

**Sync-Intervall:** Stündlich via Celery Beat
**Quelle:** 10.80.80.8:5432/loco_auswertung_db

### Wichtigste Locosoft-Tabellen

| Tabelle | Locosoft-Quelle | Beschreibung |
|---------|-----------------|--------------|
| `loco_dealer_vehicles` | dealer_vehicles | Fahrzeugbestand |
| `loco_orders` | orders | Werkstattaufträge |
| `loco_times` | times | Zeitbuchungen |
| `loco_employees` | employees | Mitarbeiter |
| `loco_customers_suppliers` | customers_suppliers | Kunden |
| `loco_parts_master` | parts_master | Teile-Stamm |
| `loco_invoices` | invoices | Rechnungen |
| `loco_journal_accountings` | journal_accountings | FIBU |

---

## Standort-Mapping

```
Standort 1 = Deggendorf Opel (DEG)
Standort 2 = Deggendorf Hyundai (HYU)
Standort 3 = Landau (LAN)
```

In Locosoft: `out_subsidiary` / `subsidiary`

---

## Migration von SQLite

**Abgeschlossen:** TAG 135-139

### Was wurde migriert:

1. Alle 155 SQLite-Tabellen → 161 PostgreSQL-Tabellen
2. Datentypen konvertiert (TEXT → VARCHAR, REAL → DECIMAL)
3. SERIAL statt AUTOINCREMENT
4. Placeholder: `?` → `%s`
5. Datum-Funktionen: `date('now')` → `CURRENT_DATE`
6. Boolean: `= 1` → `= true`

### Alte SQLite-Datei (archiviert):

```
/opt/greiner-portal/data/greiner_controlling.db
→ Wird nicht mehr verwendet
→ Backup unter /opt/greiner-portal/data/backups/
```

---

## Backup & Wartung

### Backup erstellen

```bash
pg_dump -h 127.0.0.1 -U drive_user -d drive_portal -F c -f backup_$(date +%Y%m%d).dump
```

### Backup wiederherstellen

```bash
pg_restore -h 127.0.0.1 -U drive_user -d drive_portal -c backup_20251229.dump
```

### Tabellen-Statistiken aktualisieren

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "VACUUM ANALYZE"
```

---

## Verbindung in Python

```python
from api.db_connection import get_db, get_db_type

# Automatisch PostgreSQL (via DB_TYPE=postgresql)
conn = get_db()
cursor = conn.cursor()

# HybridRow: Unterstützt row[0] UND row['name']
cursor.execute("SELECT id, name FROM employees WHERE active = true")
for row in cursor.fetchall():
    print(row['name'], row[0])  # Beide Zugriffe funktionieren!

conn.close()
```

### Locosoft-Verbindung

```python
from api.db_utils import get_locosoft_connection
from psycopg2.extras import RealDictCursor

conn = get_locosoft_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT * FROM dealer_vehicles
    WHERE EXTRACT(YEAR FROM out_invoice_date) = 2025
""")
rows = cursor.fetchall()
conn.close()
```

---

*Erstellt: TAG 143 - 2025-12-29*
*Migration: TAG 135-139*
