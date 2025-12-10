# LOCOSOFT HELPERS - Dokumentation

**Stand:** TAG 110 (2025-12-09)  
**Modul:** `utils/locosoft_helpers.py`

---

## 🎯 Übersicht

Zentrale Funktionen für Auftragsarten, SVS und Klassifizierung.

**Architektur:**
```
┌─────────────────┐      Sync-Job       ┌─────────────────┐
│    Locosoft     │  ──────────────────▶│     SQLite      │
│   (PostgreSQL)  │   sync_charge_      │  (charge_types  │
│  charge_types   │      types.py       │     _sync)      │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ locosoft_helpers│
                                        │   hole_svs()    │
                                        └─────────────────┘
```

**Prinzip:** 
- Stammdaten (SVS, charge_types) → SQLite (gesynct)
- Live-Daten (Auftragsdetails) → Locosoft direkt

---

## 🔄 Sync-Job

**Script:** `scripts/imports/sync_charge_types.py`

```bash
# Normaler Sync
python scripts/imports/sync_charge_types.py

# Tabellen neu erstellen
python scripts/imports/sync_charge_types.py --force

# Nur anzeigen
python scripts/imports/sync_charge_types.py --show
```

**Empfehlung:** Täglich per Cron oder bei App-Start

```bash
# Crontab (täglich 6:00)
0 6 * * * cd /opt/greiner-portal && venv/bin/python scripts/imports/sync_charge_types.py >> logs/sync_charge_types.log 2>&1
```

---

## 📊 SVS (Stundenverrechnungssätze)

### Alle SVS holen

```python
from utils import hole_svs

svs = hole_svs(betrieb=1)

# Ergebnis:
{
    'standard': 11.90,        # Type 10 (Mechanik)
    'wartung': 11.90,         # Type 11
    'elektrik': 12.90,        # Type 15
    'elektrofahrzeug': 17.90, # Type 16 (!)
    'karosserie': 21.00,      # Type 20
    'garantie': 8.43,         # Type 60
    'intern': 6.50,           # Type 40
    'fremdleistung': 15.50,   # Type 90
    'alle': {...},            # Alle charge_types
    'quelle': 'sqlite',       # Datenquelle
    'last_sync': '2025-12-09 10:00:00'
}
```

### Einzelner AW-Preis

```python
from utils import hole_aw_preis

# AW-Preis für Elektrofahrzeug (charge_type 16)
preis = hole_aw_preis(betrieb=1, charge_type=16)  # 17.90
```

### Charge-Type Details

```python
from utils import hole_charge_type_info

info = hole_charge_type_info(charge_type=16, betrieb=1)

# Ergebnis:
{
    'type': 16,
    'beschreibung': 'Ber.Art 16 Elektrofahrzeuge',
    'aw_preis': 17.90,
    'stundensatz': 179.00,
    'abteilung': 1,
    'abteilung_name': 'Werkstatt',
    'kategorie': 'elektrofahrzeug'
}
```

---

## 🏷️ Auftragsart-Klassifizierung

### Klassifizierung nach Kriterien

```python
from utils import klassifiziere_auftragsart

# Werkstatt Kunde
k = klassifiziere_auftragsart(charge_type=10, labour_type='W')
# {'kategorie': 'werkstatt_kunde', 'ist_garantie': False, ...}

# Garantie Opel
k = klassifiziere_auftragsart(charge_type=60, labour_type='G', marke='Opel')
# {'kategorie': 'garantie', 'hersteller': 'Stellantis', ...}

# Elektrofahrzeug
k = klassifiziere_auftragsart(charge_type=16)
# {'kategorie': 'elektrofahrzeug', 'ist_elektro': True, ...}

# Leasing Alphabet
k = klassifiziere_auftragsart(charge_type=12)
# {'kategorie': 'leasing_alphabet', 'ist_leasing': True, ...}
```

### Komplette Auftragsdetails (LIVE aus Locosoft!)

```python
from utils import hole_auftragsdetails

details = hole_auftragsdetails(order_number=219379)

# Ergebnis:
{
    'order_number': 219379,
    'betrieb': 1,
    'kennzeichen': 'DEG-X 212',
    'marke': 'Opel',
    'kunde': 'Mustermann, Max',
    'serviceberater': 'Sandra Müller',
    'klassifizierung': {
        'kategorie': 'werkstatt_kunde',
        'ist_garantie': False,
        'ist_elektro': False,
        ...
    },
    'positionen': [...],
    'summen': {...}
}
```

---

## 🔧 Auftragsarten-Tabelle

### charge_types (Berechnungsarten)

| Type | Beschreibung | AW-Preis | Kategorie |
|------|--------------|----------|-----------|
| **10** | Lohn Mechanik | 11,90 € | werkstatt_mechanik |
| **11** | Lohn Wartung | 11,90 € | werkstatt_wartung |
| **15** | Lohn Elektrik | 12,90 € | werkstatt_elektrik |
| **16** | Elektrofahrzeuge | **17,90 €** | elektrofahrzeug |
| **18** | Elektrofahrzeuge BW | 15,10 € | elektrofahrzeug_karosserie |
| **12** | Alphabet Leasing | 12,50 € | leasing_alphabet |
| **13** | Stellantis Bank | 14,00 € | leasing_stellantis_bank |
| **14** | Allg. Leasing | 14,00 € | leasing_allgemein |
| **17** | OFL/ALD Leasing | 12,70 € | leasing_ofl_ald |
| **20** | Lohn Karosserie | 21,00 € | karosserie |
| **30** | Lohn Eigenlackierung | – | lackierung |
| **40** | Lohn intern | 6,50 € | intern |
| **60** | Lohn Garantie | 8,43 € | garantie |
| **68** | Kulanz GW | – | kulanz_gw |
| **69** | Kulanz NW | – | kulanz_nw |
| **90** | Fremdleistung | 15,50 € | fremdleistung |

---

## 💰 Fremdleistungs-Margen

### Einzelne Marge berechnen

```python
from utils import berechne_fremdleistung_marge

# Lackierer-Rechnung
marge = berechne_fremdleistung_marge(
    netto_vk=270.80,    # Was der Kunde zahlt
    einsatzwert=163.20  # Was es uns kostet
)

# Ergebnis:
{
    'marge_eur': 107.60,
    'marge_prozent': 39.7,
    'aufschlag_prozent': 65.9
}
```

---

## 🗄️ SQLite-Tabellen

### charge_types_sync

```sql
CREATE TABLE charge_types_sync (
    id INTEGER PRIMARY KEY,
    type INTEGER NOT NULL,
    subsidiary INTEGER NOT NULL,
    timeunit_rate REAL,        -- AW-Preis
    department INTEGER,
    stundensatz REAL,          -- AW-Preis × 10
    kategorie TEXT,            -- z.B. 'werkstatt_mechanik'
    abteilung_name TEXT,       -- z.B. 'Werkstatt'
    synced_at TEXT,
    UNIQUE(type, subsidiary)
);
```

### charge_type_descriptions_sync

```sql
CREATE TABLE charge_type_descriptions_sync (
    type INTEGER PRIMARY KEY,
    description TEXT,
    synced_at TEXT
);
```

---

## 📁 Dateien

| Datei | Zweck |
|-------|-------|
| `utils/__init__.py` | Package mit allen Exports |
| `utils/kpi_definitions.py` | KPI-Berechnungen |
| `utils/locosoft_helpers.py` | SVS, Klassifizierung (SQLite) |
| `scripts/imports/sync_charge_types.py` | Sync-Job |
| `docs/LOCOSOFT_HELPERS.md` | Diese Dokumentation |

---

## ⚠️ Wichtige Hinweise

1. **Sync-Job muss laufen!** Sonst werden Fallback-Werte verwendet.
2. **Preisänderungen:** Nach Änderung in Locosoft → Sync ausführen
3. **Live-Daten:** `hole_auftragsdetails()` greift direkt auf Locosoft zu
4. **Fallback:** Bei fehlender Sync-Tabelle werden Standard-Werte genutzt

---

*Letzte Aktualisierung: TAG 110 (2025-12-09)*
