# TODO FÜR TAG 102 - URLAUBSPLANER REVIVAL + LOCOSOFT HR-ANALYSE

**Datum:** 2025-12-08  
**Letzter Stand:** TAG 101 - Stempeluhr Dual-Filter deployed

---

## 🎯 HAUPTZIELE TAG 102

### 1. LOCOSOFT HR-DATEN ANALYSE

**Frage:** Wie sind die Mitarbeiter in Locosoft gepflegt? Gibt es einen Schichtplan?

**Zu prüfende Tabellen:**
- `employees_history` - Mitarbeiter-Stammdaten
- `employees_worktimes` - Arbeitszeiten pro Wochentag
- `absence_calendar` - Abwesenheiten (Urlaub, Krank)
- `year_calendar` - Feiertage
- Gibt es `shifts` oder `shift_plans` Tabellen?

**Analyse-Fragen:**
1. Welche Felder sind für Schichtplanung vorhanden?
2. Gibt es feste Schichten (Früh/Spät) oder nur Tagesarbeitszeit?
3. Wie werden Pausenzeiten gepflegt?
4. Ist `productivity_factor` gepflegt? (derzeit meist 0.0!)

**Bekannte Probleme (aus TAG 94):**
- `is_latest_record` ist IMMER NULL (nicht gepflegt)
- `productivity_factor` bei Mechanikern meist 0.0 statt 1.0

---

### 2. URLAUBSPLANER REVIVAL

**Historie:**
- TAG 1 (06.11.2025): Urlaubsplaner V2 gestartet
- Mitarbeiter-Sync aus Locosoft erfolgreich (71 MA)
- Seitdem RUHT das Projekt

**Relevante Dokumente:**
- `docs/sessions/SESSION_WRAP_UP-Tag1_urlaubslplaner.md` - Ursprüngliches Setup
- `api/vacation_api.py` - Bestehende API
- `api/graph_mail_connector.py` - Microsoft Graph für E-Mails (existiert!)

**Offene Fragen für TAG 102:**
1. Was ist der aktuelle Stand? (employees-Tabelle prüfen)
2. Feiertage 2025/2026 aktuell?
3. GraphAPI: Was war das Ziel? (Outlook-Kalender-Sync?)
4. VacationCalculator fertig?

---

### 3. GRAPH API - STATUS PRÜFEN

**Existiert bereits:** `api/graph_mail_connector.py`
- Kann E-Mails über Office 365 senden
- Benötigt: GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET

**Mögliche Erweiterungen:**
- Outlook-Kalender-Integration (Urlaub als Termin eintragen)
- Teams-Benachrichtigungen bei Urlaubsanträgen
- Abwesenheits-Auto-Reply setzen?

---

## 📁 RELEVANTE DATEIEN

### Urlaubsplaner:
- `api/vacation_api.py`
- `templates/urlaubsplaner_v2.html`
- `data/greiner_controlling.db` → Tabellen: employees, vacation_*, holidays

### Graph API:
- `api/graph_mail_connector.py`
- `config/.env` → GRAPH_* Credentials

### HR/Locosoft:
- `docs/HR_LOCOSOFT_ARBEITSZEITEN_PFLEGE.md`
- `docs/DB_SCHEMA_LOCOSOFT.md`

---

## 🔧 SCHNELLSTART-BEFEHLE

```bash
# SSH
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal
source venv/bin/activate

# Locosoft-Tabellen erkunden
python3 << 'EOF'
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('config/.env')
conn = psycopg2.connect(
    host=os.getenv('LOCOSOFT_HOST'),
    database=os.getenv('LOCOSOFT_DATABASE'),
    user=os.getenv('LOCOSOFT_USER'),
    password=os.getenv('LOCOSOFT_PASSWORD')
)
cur = conn.cursor()

# Schicht-Tabellen suchen
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%shift%' OR table_name LIKE '%schicht%')
""")
print("Schicht-Tabellen:", cur.fetchall())

# Employees_worktimes Struktur
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'employees_worktimes'
    ORDER BY ordinal_position
""")
print("\nemployees_worktimes Spalten:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
EOF

# SQLite Urlaubsplaner-Status
sqlite3 data/greiner_controlling.db << 'SQL'
SELECT COUNT(*) as anzahl, 'employees' as tabelle FROM employees
UNION ALL
SELECT COUNT(*), 'vacation_bookings' FROM vacation_bookings
UNION ALL
SELECT COUNT(*), 'holidays' FROM holidays WHERE year >= 2025;
SQL
```

---

## 📊 ARCHITEKTUR-ZIEL URLAUBSPLANER

```
┌─────────────────────────────────────────────────────────────┐
│                     URLAUBSPLANER V2                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Frontend   │    │   REST API  │    │   Graph API │    │
│  │  (Jinja2)   │───▶│ vacation_api│───▶│  (E-Mail)   │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                  │                   │           │
│         └──────────────────┴───────────────────┘           │
│                            │                               │
│         ┌──────────────────┴───────────────────┐          │
│         ▼                                       ▼          │
│  ┌─────────────────┐              ┌─────────────────┐     │
│  │     SQLite      │              │    Locosoft     │     │
│  │ greiner_ctrl.db │◀────sync─────│   PostgreSQL    │     │
│  │ - employees     │              │ - employees_    │     │
│  │ - vacation_*    │              │   history       │     │
│  │ - holidays      │              │ - absence_cal   │     │
│  └─────────────────┘              └─────────────────┘     │
│                                                             │
│  Optionale Erweiterung:                                    │
│  ┌─────────────────┐                                       │
│  │  Outlook/Teams  │◀──── Graph API ────                   │
│  │  - Kalender     │                                       │
│  │  - Auto-Reply   │                                       │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏳ NOCH OFFEN VON FRÜHER

### TAG 100 TODOs:
- [ ] Mit Serviceleiter: Kritische Aufträge (>500 Tage)
- [ ] ML für Lieferzeit-Prognose

### Urlaubsplaner (TAG 1):
- [ ] VacationCalculator fertigstellen
- [ ] Feiertage 2025-2026 prüfen
- [ ] Views erstellen (v_vacation_balance_2025)
- [ ] Genehmigungsprozess

---

## 💡 ARBEITSWEISE

```
User: TAG 102 Urlaubsplaner Revival. Lies TODO.
Claude: 
1. Liest dieses TODO
2. Analysiert Locosoft HR-Daten
3. Prüft aktuellen Urlaubsplaner-Stand
4. Erstellt Plan für Weiterentwicklung
```

---

**Erstellt:** 2025-12-08  
**Projekt:** GREINER DRIVE
