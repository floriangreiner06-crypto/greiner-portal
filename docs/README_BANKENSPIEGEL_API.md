# 🏦 BANKENSPIEGEL REST API - DOKUMENTATION

**Version:** 1.0  
**Datum:** 2025-11-07  
**Projekt:** Greiner Portal - Bankenspiegel 3.0

---

## 📋 Übersicht

Die Bankenspiegel REST API bietet Zugriff auf:
- ✅ Dashboard-KPIs (Gesamtsaldo, Umsätze, Top-Kategorien)
- ✅ Kontenverwaltung (Liste mit Salden)
- ✅ Transaktionsdaten (mit umfangreichen Filtern)
- ✅ Automatische Aggregationen und Statistiken

**Basis-URL:** `http://10.80.80.20/api/bankenspiegel`

---

## 🚀 Installation

### 1. Dateien auf Server kopieren

```bash
cd /opt/greiner-portal
mkdir -p api

# Upload via WinSCP:
# - bankenspiegel_api.py → /opt/greiner-portal/api/
# - install_bankenspiegel_api.sh → /opt/greiner-portal/
```

### 2. Installation ausführen

```bash
cd /opt/greiner-portal
chmod +x install_bankenspiegel_api.sh
./install_bankenspiegel_api.sh
```

Das Script:
- ✅ Kopiert API-Dateien
- ✅ Erstellt Backup von app.py
- ✅ Registriert Blueprint in Flask
- ✅ Startet Flask neu
- ✅ Testet Health-Endpoint

---

## 📍 ENDPOINTS

### 1. 🏥 HEALTH CHECK

**Endpoint:** `GET /api/bankenspiegel/health`

**Beschreibung:** Prüft API-Status und Datenbank-Verbindung

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2025-11-07T10:30:00",
  "database": {
    "connected": true,
    "banken": 14,
    "konten": 24,
    "transaktionen": 49102
  }
}
```

**Beispiel:**
```bash
curl http://localhost:5000/api/bankenspiegel/health
```

---

### 2. 📊 DASHBOARD (KPIs)

**Endpoint:** `GET /api/bankenspiegel/dashboard`

**Beschreibung:** Liefert wichtigste Dashboard-KPIs:
- Gesamtsaldo aller Konten
- Anzahl aktiver Konten und Banken
- Transaktionen letzte 30 Tage
- Umsätze aktueller Monat
- Top 5 Ausgaben-Kategorien

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-11-07T10:30:00",
  "dashboard": {
    "gesamtsaldo": 125430.50,
    "anzahl_konten": 15,
    "anzahl_banken": 14,
    "neuester_stand": "2025-11-06",
    "letzte_30_tage": {
      "anzahl_transaktionen": 145,
      "einnahmen": 25000.00,
      "ausgaben": 18500.00,
      "saldo": 6500.00
    },
    "aktueller_monat": {
      "monat": "2025-11",
      "einnahmen": 12000.00,
      "ausgaben": 8500.00,
      "saldo": 3500.00,
      "anzahl_transaktionen": 67
    },
    "top_kategorien": [
      {
        "kategorie": "Miete",
        "anzahl": 5,
        "summe": 6000.00
      },
      {
        "kategorie": "Gehalt",
        "anzahl": 3,
        "summe": 4500.00
      }
    ]
  }
}
```

**Beispiel:**
```bash
curl http://localhost:5000/api/bankenspiegel/dashboard
```

---

### 3. 💰 KONTEN

**Endpoint:** `GET /api/bankenspiegel/konten`

**Beschreibung:** Liefert Liste aller Konten mit aktuellem Saldo

**Query-Parameter:**
| Parameter | Typ | Beschreibung | Default |
|-----------|-----|--------------|---------|
| `bank_id` | int | Filter nach Bank-ID | - |
| `aktiv` | int | 1 = aktiv, 0 = inaktiv | 1 |

**Response:**
```json
{
  "success": true,
  "konten": [
    {
      "konto_id": 1,
      "bank_name": "Sparkasse Oberland",
      "kontoname": "Hauptkonto",
      "iban": "DE89500500991234567890",
      "kontotyp": "Girokonto",
      "waehrung": "EUR",
      "saldo": 4656.20,
      "stand_datum": "2025-11-06",
      "aktiv": 1
    }
  ],
  "count": 15,
  "gesamtsaldo": 125430.50
}
```

**Beispiele:**
```bash
# Alle aktiven Konten
curl http://localhost:5000/api/bankenspiegel/konten

# Nur Konten von Bank ID 1
curl http://localhost:5000/api/bankenspiegel/konten?bank_id=1

# Auch inaktive Konten
curl http://localhost:5000/api/bankenspiegel/konten?aktiv=0
```

---

### 4. 💸 TRANSAKTIONEN

**Endpoint:** `GET /api/bankenspiegel/transaktionen`

**Beschreibung:** Liefert filterbare Transaktionsliste mit Statistiken

**Query-Parameter:**
| Parameter | Typ | Beschreibung | Default |
|-----------|-----|--------------|---------|
| `konto_id` | int | Filter nach Konto-ID | - |
| `bank_id` | int | Filter nach Bank-ID | - |
| `von` | date | Start-Datum (YYYY-MM-DD) | - |
| `bis` | date | End-Datum (YYYY-MM-DD) | - |
| `kategorie` | string | Filter nach Kategorie | - |
| `betrag_min` | float | Mindestbetrag | - |
| `betrag_max` | float | Maximalbetrag | - |
| `suche` | string | Volltext-Suche | - |
| `limit` | int | Max. Anzahl (max 1000) | 100 |
| `offset` | int | Offset für Pagination | 0 |
| `order` | string | 'asc' oder 'desc' | desc |

**Response:**
```json
{
  "success": true,
  "transaktionen": [
    {
      "id": 49102,
      "bank_name": "Sparkasse Oberland",
      "konto_id": 1,
      "kontoname": "Hauptkonto",
      "iban": "DE89500500991234567890",
      "buchungsdatum": "2025-11-06",
      "valutadatum": "2025-11-06",
      "buchungstext": "Gehalt November",
      "verwendungszweck": "Lohn/Gehalt 11/2025",
      "betrag": 4500.00,
      "waehrung": "EUR",
      "kategorie": "Gehalt",
      "steuerrelevant": 1,
      "pdf_quelle": "kontoauszug_11_2025.pdf",
      "saldo_nach_buchung": 4656.20
    }
  ],
  "pagination": {
    "count": 100,
    "total": 49102,
    "limit": 100,
    "offset": 0,
    "has_more": true
  },
  "statistik": {
    "einnahmen": 12000.00,
    "ausgaben": 8500.00,
    "saldo": 3500.00
  }
}
```

**Beispiele:**

```bash
# Letzte 10 Transaktionen
curl http://localhost:5000/api/bankenspiegel/transaktionen?limit=10

# Transaktionen von Konto 1
curl http://localhost:5000/api/bankenspiegel/transaktionen?konto_id=1&limit=20

# Transaktionen letzte 30 Tage
HEUTE=$(date +%Y-%m-%d)
VOR_30=$(date -d "30 days ago" +%Y-%m-%d)
curl "http://localhost:5000/api/bankenspiegel/transaktionen?von=$VOR_30&bis=$HEUTE"

# Oktober 2025
curl http://localhost:5000/api/bankenspiegel/transaktionen?von=2025-10-01&bis=2025-10-31

# Nur Ausgaben (negative Beträge)
curl http://localhost:5000/api/bankenspiegel/transaktionen?betrag_max=-0.01&limit=20

# Nur Einnahmen (positive Beträge)
curl http://localhost:5000/api/bankenspiegel/transaktionen?betrag_min=0.01&limit=20

# Große Beträge (> 1000 EUR)
curl http://localhost:5000/api/bankenspiegel/transaktionen?betrag_min=1000&limit=10

# Kategorie "Gehalt"
curl http://localhost:5000/api/bankenspiegel/transaktionen?kategorie=Gehalt&limit=10

# Volltext-Suche "Miete"
curl http://localhost:5000/api/bankenspiegel/transaktionen?suche=Miete&limit=10

# Pagination (zweite Seite, je 50 Einträge)
curl http://localhost:5000/api/bankenspiegel/transaktionen?limit=50&offset=50

# Kombination mehrerer Filter
curl "http://localhost:5000/api/bankenspiegel/transaktionen?konto_id=1&von=2025-10-01&bis=2025-10-31&kategorie=Gehalt&limit=20"
```

---

## 🧪 TESTING

### Automatisiertes Test-Script

```bash
cd /opt/greiner-portal
chmod +x test_bankenspiegel_api.sh
./test_bankenspiegel_api.sh
```

Das Script testet:
- ✅ Health Check
- ✅ Dashboard
- ✅ Konten (alle & gefiltert)
- ✅ Transaktionen mit verschiedenen Filtern
- ✅ Suche und Kategorien

### Manuelles Testen

```bash
# Mit curl
curl http://localhost:5000/api/bankenspiegel/health | python3 -m json.tool

# Im Browser
http://10.80.80.20/api/bankenspiegel/dashboard

# Mit wget
wget -qO- http://localhost:5000/api/bankenspiegel/konten | python3 -m json.tool
```

---

## 🔒 SICHERHEIT

### Zugriffskontrolle

**Aktuell:** Keine Authentifizierung (nur internes Netzwerk)

**Für Produktion empfohlen:**
```python
# In bankenspiegel_api.py vor jedem Endpoint:
from functools import wraps
from flask import session, jsonify

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Nicht angemeldet'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bankenspiegel_api.route('/dashboard', methods=['GET'])
@require_login
def get_dashboard():
    # ...
```

---

## 📊 DATENBANK-VIEWS

Die API nutzt folgende optimierte Views:

### v_aktuelle_kontostaende
```sql
SELECT 
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    k.iban,
    k.kontotyp,
    k.waehrung,
    COALESCE(kh.saldo, 0.0) as saldo,
    kh.datum as stand_datum,
    k.aktiv
FROM konten k
JOIN banken b ON k.bank_id = b.id
LEFT JOIN kontostand_historie kh ON k.id = kh.konto_id
-- Nur neuester Stand pro Konto
```

### v_monatliche_umsaetze
```sql
SELECT 
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    strftime('%Y-%m', t.buchungsdatum) as monat,
    SUM(CASE WHEN t.betrag > 0 THEN t.betrag ELSE 0 END) as einnahmen,
    SUM(CASE WHEN t.betrag < 0 THEN ABS(t.betrag) ELSE 0 END) as ausgaben,
    SUM(t.betrag) as saldo,
    COUNT(*) as anzahl_transaktionen
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id
GROUP BY b.bank_name, k.id, k.kontoname, monat
```

### v_transaktionen_uebersicht
```sql
SELECT 
    t.id,
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    k.iban,
    t.buchungsdatum,
    t.valutadatum,
    t.buchungstext,
    t.verwendungszweck,
    t.betrag,
    t.waehrung,
    t.kategorie,
    t.steuerrelevant,
    t.pdf_quelle,
    t.saldo_nach_buchung
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id
```

---

## 🛠️ TROUBLESHOOTING

### Problem: API antwortet nicht

```bash
# Prüfe ob Flask läuft
ps aux | grep "python.*app.py"

# Flask-Logs prüfen
tail -f /opt/greiner-portal/logs/flask.log

# Flask neu starten
cd /opt/greiner-portal
source venv/bin/activate
pkill -f "python.*app.py"
nohup python3 app.py > logs/flask.log 2>&1 &
```

### Problem: 500 Internal Server Error

```bash
# Prüfe Datenbank-Zugriff
sqlite3 /opt/greiner-portal/data/greiner_controlling.db "SELECT COUNT(*) FROM transaktionen;"

# Prüfe Views
sqlite3 /opt/greiner-portal/data/greiner_controlling.db "SELECT * FROM v_aktuelle_kontostaende LIMIT 1;"

# Flask-Logs für Fehlerdetails
tail -100 /opt/greiner-portal/logs/flask.log
```

### Problem: Langsame Abfragen

```bash
# Prüfe Indizes
sqlite3 /opt/greiner-portal/data/greiner_controlling.db << EOF
.indices transaktionen
.indices konten
.indices kontostand_historie
EOF

# Falls Indizes fehlen - siehe migrations/phase1/001-005
```

---

## 🚀 NÄCHSTE SCHRITTE

Nach erfolgreicher API-Installation:

### Phase 2 - Frontend (1-2 Tage)
- ✅ Dashboard-UI mit KPI-Kacheln
- ✅ Konten-Übersicht (Tabelle)
- ✅ Transaktionsliste (mit Filtern)
- ✅ Charts (Chart.js)

### Phase 3 - Erweiterte Features (2-3 Tage)
- ✅ Stellantis-Integration (Fahrzeugfinanzierungen)
- ✅ LocoSoft-Anbindung
- ✅ PDF-Upload & Import
- ✅ Kategorien-Management
- ✅ Export-Funktionen (Excel, PDF)

---

## 📞 SUPPORT

**Projekt:** Greiner Portal - Bankenspiegel 3.0  
**Version:** 1.0  
**Datum:** 2025-11-07

**Wichtige Dateien:**
- API: `/opt/greiner-portal/api/bankenspiegel_api.py`
- App: `/opt/greiner-portal/app.py`
- DB: `/opt/greiner-portal/data/greiner_controlling.db`
- Logs: `/opt/greiner-portal/logs/flask.log`

**Referenz-Dokumentation:**
- SESSION_WRAP_UP_TAG8.md
- PHASE1_HYBRID_*.md
- README_PHASE1_MIGRATION.md

---

**🎉 Viel Erfolg mit der Bankenspiegel API!**
