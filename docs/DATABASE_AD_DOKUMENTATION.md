# 📚 GREINER PORTAL - DATENBANK & AD DOKUMENTATION

**Version:** 2.0 - TAG 107  
**Datum:** 09.12.2025  
**Autor:** Claude AI

---

## 🏗️ ÜBERSICHT

Das Greiner Portal verwendet drei Datenquellen:

| Quelle | Typ | Verwendung |
|--------|-----|------------|
| **SQLite** | Lokal | Hauptdatenbank für Portal-Daten |
| **PostgreSQL** | Extern (Locosoft) | HR-Daten, Abwesenheiten, Buchungen |
| **Active Directory** | LDAP | Authentifizierung, Gruppen, Berechtigungen |

---

# 📊 TEIL 1: SQLITE DATENBANK

**Pfad:** `/opt/greiner-portal/data/greiner_controlling.db`

## 1.1 URLAUBSPLANER TABELLEN

### employees
Mitarbeiter-Stammdaten (aus LDAP + Locosoft synchronisiert)

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birthday DATE,
    entry_date DATE,
    exit_date DATE,
    department_id INTEGER,
    vacation_days_total INTEGER DEFAULT 30,
    role TEXT DEFAULT 'user',
    free_weekdays TEXT,
    locosoft_id INTEGER,              -- Verknüpfung zu Locosoft employee_number
    department_name TEXT,             -- z.B. "Verkauf", "Service", "Buchhaltung"
    location TEXT,                    -- "Deggendorf" oder "Landau"
    vacation_entitlement INTEGER DEFAULT 30,
    vacation_used_2025 REAL DEFAULT 0,
    supervisor_id INTEGER,
    active INTEGER DEFAULT 1,
    aktiv BOOLEAN DEFAULT 1,
    personal_nr TEXT,
    is_manager INTEGER DEFAULT 0,
    manager_role TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

### ldap_employee_mapping
Verknüpfung LDAP-Username ↔ Employee ↔ Locosoft

```sql
CREATE TABLE ldap_employee_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ldap_username TEXT UNIQUE NOT NULL,  -- z.B. "sandra.brendel"
    ldap_email TEXT,                      -- z.B. "sandra.brendel@auto-greiner.de"
    employee_id INTEGER NOT NULL,         -- FK zu employees.id
    locosoft_id INTEGER NOT NULL,         -- z.B. 1016 (employee_number in Locosoft)
    verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### users
Login-Daten (wird bei Login aus LDAP befüllt)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,    -- z.B. "florian.greiner@auto-greiner.de"
    display_name TEXT,                -- z.B. "Florian Greiner"
    email TEXT,
    ad_groups TEXT,                   -- JSON Array: ["GRP_Urlaub_Admin", "GRP_Urlaub_Genehmiger_GL"]
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Wichtig:** `ad_groups` enthält alle AD-Gruppen als JSON-Array!

### vacation_bookings
Urlaubs-/Abwesenheitsbuchungen

```sql
CREATE TABLE vacation_bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    date DATE NOT NULL,
    vacation_type_id INTEGER NOT NULL,  -- 1=Urlaub, 3=Krank, 5=Schulung, 6=ZA
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'rejected', 'cancelled'
    day_part TEXT DEFAULT 'full',        -- 'full', 'morning', 'afternoon'
    approved_by INTEGER,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (vacation_type_id) REFERENCES vacation_types(id)
);
```

### vacation_types
Abwesenheitsarten

```sql
CREATE TABLE vacation_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT,
    color TEXT,
    requires_approval BOOLEAN DEFAULT 1
);

-- Standard-Daten:
-- 1 = Urlaub (Url) - grün - requires_approval
-- 2 = Sonderurlaub - grün
-- 3 = Krank (Krn) - pink - NO approval needed (auto-approved)
-- 5 = Schulung - lila
-- 6 = Zeitausgleich (ZA.) - blau - requires_approval
```

### vacation_entitlements
Urlaubsanspruch pro Mitarbeiter und Jahr

```sql
CREATE TABLE vacation_entitlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_days REAL NOT NULL,          -- z.B. 27.0
    carried_over REAL DEFAULT 0,       -- Übertrag aus Vorjahr
    added_manually REAL DEFAULT 0,     -- Manuelle Korrekturen
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, year)
);
```

### vacation_adjustments
Manuelle Korrekturen (für HR-Admin)

```sql
CREATE TABLE vacation_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    adjustment_days REAL NOT NULL,
    reason TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### holidays
Feiertage (Bayern)

```sql
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    name TEXT NOT NULL,
    year INTEGER
);
```

## 1.2 LOCOSOFT SYNC TABELLEN

### loco_employees
Mitarbeiter aus Locosoft PostgreSQL

```sql
CREATE TABLE loco_employees (
    employee_number INTEGER PRIMARY KEY,  -- z.B. 1016
    name TEXT,                            -- z.B. "Brendel,Sandra"
    subsidiary INTEGER,                   -- 1=Deggendorf, 3=Landau
    is_latest_record BOOLEAN,
    -- weitere Felder aus Locosoft...
);
```

### loco_employees_group_mapping
Abteilungs-Zuordnung aus Locosoft

```sql
CREATE TABLE loco_employees_group_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number INTEGER NOT NULL,     -- FK zu loco_employees
    grp_code TEXT NOT NULL,               -- z.B. "VKB", "SER", "MON", "LAG"
    UNIQUE(employee_number, grp_code)
);
```

**Locosoft Gruppen-Codes:**

| Code | Bedeutung | Genehmiger (AD-Gruppe) |
|------|-----------|------------------------|
| VKB | Verkaufsberatung | GRP_Urlaub_Genehmiger_Verkauf |
| SER | Service & Empfang | GRP_Urlaub_Genehmiger_Service_DEG |
| SB | Serviceberater | GRP_Urlaub_Genehmiger_Service_DEG |
| MON | Montage/Werkstatt | GRP_Urlaub_Genehmiger_Werkstatt_DEG/LAU |
| LAG | Lager & Teile | GRP_Urlaub_Genehmiger_Teile |
| CC | Call-Center/CRM | GRP_Urlaub_Genehmiger_CRM |
| MAR | Marketing | GRP_Urlaub_Genehmiger_CRM |
| VER | Verwaltung | GRP_Urlaub_Genehmiger_Buchhaltung |
| DIS | Disposition | GRP_Urlaub_Genehmiger_Disposition |
| GL | Geschäftsleitung | GRP_Urlaub_Genehmiger_GL |
| FL | Filialleitung | GRP_Urlaub_Genehmiger_GL |
| FZ | Fahrzeuge | GRP_Urlaub_Genehmiger_Buchhaltung |
| A-W | Azubi Werkstatt | GRP_Urlaub_Genehmiger_Werkstatt_* |
| A-L | Azubi Lager | GRP_Urlaub_Genehmiger_Teile |
| FA | Fahrzeugannahme | GRP_Urlaub_Genehmiger_Service_DEG |
| G | Garantie | GRP_Urlaub_Genehmiger_Service_DEG |
| HM | Hausmeister | GRP_Urlaub_Genehmiger_Werkstatt_DEG |

**Standorte (subsidiary):**
- 1 = Deggendorf
- 3 = Landau

---

# 🌐 TEIL 2: LOCOSOFT POSTGRESQL

**Host:** 10.80.80.8  
**Database:** loco_auswertung_db  
**User:** loco_auswertung_benutzer

## 2.1 WICHTIGE TABELLEN

### employees
```sql
SELECT employee_number, name, subsidiary, is_latest_record
FROM employees
WHERE is_latest_record = true;
```

### employees_groups_mapping
```sql
SELECT employee_number, grp_code
FROM employees_groups_mapping;
```

### absence_calendar
**Wichtigste Tabelle für Urlaubsdaten!**

```sql
SELECT 
    employee_number,
    date,
    reason,           -- 'Url', 'ZA.', 'Krn', 'BUr', etc.
    day_contingent    -- 1.0 = ganzer Tag, 0.5 = halber Tag
FROM absence_calendar
WHERE date >= '2025-01-01';
```

**Reason-Codes:**
| Code | Bedeutung |
|------|-----------|
| Url | Urlaub (bezahlt) |
| ZA. | Zeitausgleich (Überstunden-Abbau) |
| Krn | Krank |
| BUr | Betriebsurlaub |
| SUr | Sonderurlaub |
| Sch | Schulung |

### absence_reasons
```sql
SELECT id, short_text, long_text, is_annual_vacation
FROM absence_reasons;
```

## 2.2 SYNC-QUERIES

**Urlaubsverbrauch pro Mitarbeiter 2025:**
```sql
SELECT 
    e.employee_number,
    e.name,
    SUM(CASE WHEN a.reason = 'Url' THEN a.day_contingent ELSE 0 END) as urlaub,
    SUM(CASE WHEN a.reason = 'ZA.' THEN a.day_contingent ELSE 0 END) as zeitausgleich,
    SUM(CASE WHEN a.reason = 'Krn' THEN a.day_contingent ELSE 0 END) as krank
FROM employees e
LEFT JOIN absence_calendar a ON e.employee_number = a.employee_number
    AND a.date >= '2025-01-01' AND a.date <= '2025-12-31'
WHERE e.is_latest_record = true
GROUP BY e.employee_number, e.name
ORDER BY e.name;
```

---

# 🔐 TEIL 3: ACTIVE DIRECTORY

**Domain:** auto-greiner.de  
**Server:** ldap://[DC-IP]

## 3.1 OU STRUKTUR

```
DC=auto-greiner,DC=de
└── OU=AUTO-GREINER
    ├── OU=Abteilungen
    │   ├── OU=Buchhaltung
    │   │   └── OU=Benutzer → Vanessa Groll, Christian Aichinger
    │   ├── OU=CRM & Marketing
    │   │   └── OU=Benutzer → Brigitte Lackerbeck
    │   ├── OU=Disposition
    │   │   └── OU=Benutzer → Margit Loibl, Jennifer Bielmeier
    │   ├── OU=Geschäftsleitung
    │   │   └── OU=Benutzer → Florian Greiner, Franz Loibl
    │   ├── OU=Kundenzentrale
    │   │   └── OU=Benutzer → Sandra Brendel, ...
    │   ├── OU=Service
    │   │   └── OU=Benutzer → Matthias König, ...
    │   ├── OU=Teile und Zubehör
    │   │   └── OU=Benutzer → Bruno Wieland, ...
    │   └── OU=Verkauf
    │       └── OU=Benutzer → Anton Süß, ...
    │
    └── OU=Urlaub                        ← Genehmiger-Gruppen
        ├── GRP_Urlaub_Admin
        ├── GRP_Urlaub_Genehmiger_Buchhaltung
        ├── GRP_Urlaub_Genehmiger_CRM
        ├── GRP_Urlaub_Genehmiger_Disposition
        ├── GRP_Urlaub_Genehmiger_GL
        ├── GRP_Urlaub_Genehmiger_Service_DEG
        ├── GRP_Urlaub_Genehmiger_Teile
        ├── GRP_Urlaub_Genehmiger_Verkauf
        ├── GRP_Urlaub_Genehmiger_Werkstatt_DEG
        └── GRP_Urlaub_Genehmiger_Werkstatt_LAU
```

## 3.2 URLAUBS-GRUPPEN

### GRP_Urlaub_Admin
**Vollzugriff auf Urlaubsplaner-Administration**

| Mitglied | Funktion |
|----------|----------|
| Christian Aichinger | Buchhaltung |
| Vanessa Groll | Buchhaltung/HR |
| Sandra Brendel | Kundenzentrale |
| Florian Greiner | Geschäftsführung |

### GRP_Urlaub_Genehmiger_*
**Genehmigt Urlaub für bestimmte Abteilungen**

| Gruppe | Mitglieder | Genehmigt für |
|--------|------------|---------------|
| GRP_Urlaub_Genehmiger_Buchhaltung | Christian Aichinger, Vanessa Groll | VER |
| GRP_Urlaub_Genehmiger_CRM | Brigitte Lackerbeck | CC, MAR |
| GRP_Urlaub_Genehmiger_Disposition | Margit Loibl, Jennifer Bielmeier | DIS |
| GRP_Urlaub_Genehmiger_GL | Florian Greiner | GL, FL |
| GRP_Urlaub_Genehmiger_Service_DEG | Matthias König, Sandra Brendel | SER, SB (Standort 1) |
| GRP_Urlaub_Genehmiger_Teile | Bruno Wieland | LAG, A-L |
| GRP_Urlaub_Genehmiger_Verkauf | Anton Süß | VKB (alle Standorte) |
| GRP_Urlaub_Genehmiger_Werkstatt_DEG | Wolfgang Scheingraber | MON, A-W (Standort 1) |
| GRP_Urlaub_Genehmiger_Werkstatt_LAU | Rolf Sterr, Leonhard Keidl | MON, A-W, SER (Standort 3) |

## 3.3 GENEHMIGER-LOGIK

Die Zuordnung Mitarbeiter → Genehmiger basiert auf:

1. **Locosoft grp_code** des Mitarbeiters (aus `loco_employees_group_mapping`)
2. **Locosoft subsidiary** (Standort 1=DEG, 3=LAU)
3. **AD-Gruppe** des Genehmigers (aus `users.ad_groups`)

**Mapping-Tabelle in Code:**
```python
APPROVER_GROUP_MAPPING = {
    ('VKB', None): 'GRP_Urlaub_Genehmiger_Verkauf',
    ('SER', 1): 'GRP_Urlaub_Genehmiger_Service_DEG',
    ('SER', 3): 'GRP_Urlaub_Genehmiger_Werkstatt_LAU',  # Landau
    ('MON', 1): 'GRP_Urlaub_Genehmiger_Werkstatt_DEG',
    ('MON', 3): 'GRP_Urlaub_Genehmiger_Werkstatt_LAU',
    ('LAG', None): 'GRP_Urlaub_Genehmiger_Teile',
    ('VER', None): 'GRP_Urlaub_Genehmiger_Buchhaltung',
    ('CC', None): 'GRP_Urlaub_Genehmiger_CRM',
    ('GL', None): 'GRP_Urlaub_Genehmiger_GL',
    # ... etc.
}
```

---

# 🔄 TEIL 4: SYNC-PROZESSE

## 4.1 Locosoft → SQLite (Nächtlich)

**Script:** `/opt/greiner-portal/scripts/sync_locosoft.py`

Synchronisiert:
- `loco_employees`
- `loco_employees_group_mapping`
- Abwesenheiten aus `absence_calendar`

**Zeitplan:** Täglich ca. 23:00 Uhr

## 4.2 AD → SQLite (Bei Login)

Bei jedem Login wird:
1. User in `users` Tabelle aktualisiert/erstellt
2. `ad_groups` aus LDAP gelesen und als JSON gespeichert

**Wichtig:** User die sich nie einloggen haben keine `ad_groups` in der DB!

---

# 📋 TEIL 5: API ÜBERSICHT

## Vacation API (`/api/vacation/...`)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/my-balance` | GET | Eigenes Guthaben + Statistik |
| `/my-bookings` | GET | Eigene Buchungen |
| `/book` | POST | Neue Buchung erstellen |
| `/cancel` | POST | Buchung stornieren |
| `/pending-approvals` | GET | Offene Genehmigungen (für Genehmiger) |
| `/approve` | POST | Antrag genehmigen |
| `/reject` | POST | Antrag ablehnen |
| `/balance` | GET | Balance aller MA (mit ?year=2025) |

---

# 🔍 TEIL 6: WICHTIGE QUERIES

## Genehmiger für Mitarbeiter finden
```python
from api.vacation_approver_service import get_approvers_for_employee
approvers = get_approvers_for_employee(employee_id=6)  # Sandra Brendel
# Returns: [{'approver_name': 'Matthias König', 'ad_group': 'GRP_Urlaub_Genehmiger_Service_DEG', ...}]
```

## Team für Genehmiger finden
```python
from api.vacation_approver_service import get_team_for_approver
team = get_team_for_approver('matthias.koenig')
# Returns: [{'employee_id': 6, 'name': 'Sandra Brendel', 'grp_code': 'SER', 'standort': 'Deggendorf'}, ...]
```

## Ist User Genehmiger?
```python
from api.vacation_approver_service import is_approver
is_appr = is_approver('sandra.brendel')
# Returns: True (wenn in GRP_Urlaub_Genehmiger_* Gruppe)
```

---

# ⚠️ BEKANNTE PROBLEME

1. **User ohne Login:** Haben keine `ad_groups` in `users` Tabelle
   - Lösung: LDAP-Bulk-Sync oder erst bei Bedarf abfragen

2. **ZA-Anzeige "SO.31":** Formatierungsproblem in Header-Statistik
   - Quelle: API `/my-balance` Response

3. **Locosoft-Sync Timing:** Änderungen in Locosoft erscheinen erst am nächsten Tag
   - Sync läuft nachts

---

*Dokumentation erstellt: 09.12.2025 - TAG 107*
