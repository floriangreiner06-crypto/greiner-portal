# SESSION WRAP-UP TAG 121

**Datum:** 2025-12-16
**Schwerpunkt:** SB-Controlling Werktage-Berechnung, Hochrechnung, Detail-Modal Fix

---

## 1. Erledigte Aufgaben

### 1.1 SB-Ranking Komplett-Überarbeitung (aus TAG120)
- **Problem:** Falsche Serviceberater (Fakturisten 1xxx statt echte SB 4xxx)
- **Lösung:**
  - `creating_employee` → `order_taking_employee_no` via JOIN mit orders
  - SERVICEBERATER_IDS korrigiert: [4000, 4005, 5009, 4002, 4003]
  - MA-Namen aus Locosoft statt SQLite

### 1.2 Werktage-Berechnung (Hauptaufgabe TAG121)
- **Problem:** Alle Berechnungen nutzten Kalendertage (31 für Dezember)
- **Lösung:** Echte Werktage ohne Wochenenden und bayerische Feiertage
  - Dezember 2025: 23 Werktage (nicht 31)
  - 16.12.2025: 11 Werktage vergangen = 47,8% (nicht 51,6%)

**Neue Funktionen:**
```python
FEIERTAGE_2025 = [...]  # 13 bayerische Feiertage

def get_werktage(start_date, end_date, include_end=False):
    """Berechnet Werktage zwischen zwei Daten (Mo-Fr, ohne Feiertage)"""

def get_werktage_monat(jahr, monat):
    """Returns: {gesamt, vergangen, verbleibend, fortschritt_prozent, ist_aktueller_monat}"""
```

### 1.3 Hochrechnung/Prognose für SB
- DB-Prognose für Monatsende: `db1 / vergangene_tage * gesamt_tage`
- Delta vs. Soll: Vergleich aktuelle Erreichung mit Werktage-Fortschritt
- Trend-Badges: "Auf Kurs", "+X% voraus", "X% zurück"

### 1.4 TEK-Dashboard Werktage-Umstellung
- `tage_im_monat` jetzt Werktage statt Kalendertage
- Neue Response-Felder: `werktage`, `db1_soll_bis_heute`, `db1_pro_werktag`
- Template zeigt "11/23 Werktage (47,8%)"

### 1.5 Detail-Modal Fix
- **Problem:** Modal blieb bei "Lade Details..." hängen
- **Ursachen:**
  1. Query nutzte `creating_employee` statt `order_taking_employee_no`
  2. Referenz auf nicht-existierendes `TEK_CONFIG['vollkosten_monat']`
- **Lösung:**
  - JOIN mit orders-Tabelle
  - Dynamische Zielberechnung via `get_breakeven_schwelle()`
  - DB1 statt Umsatz für Zielerreichung

### 1.6 Standort-Filter
- Neue Filter: Gesamt, Deggendorf (Opel+Hyundai), Landau
- API-Parameter: `?standort=alle|deggendorf|landau`

---

## 2. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `api/serviceberater_api.py` | Werktage, Hochrechnung, Detail-Fix, Standort-Filter |
| `routes/controlling_routes.py` | Werktage-Funktionen, Breakeven auf Werktage |
| `templates/aftersales/serviceberater.html` | Werktage-Fortschritt, Prognose, Trend-Badges |
| `templates/controlling/tek_dashboard.html` | Werktage-Anzeige |

---

## 3. API-Änderungen (TAG121)

### /api/serviceberater/uebersicht
Neue Response-Felder:
```json
{
  "werktage": {
    "gesamt": 23,
    "vergangen": 11,
    "verbleibend": 12,
    "fortschritt_prozent": 47.8,
    "ist_aktueller_monat": true
  },
  "serviceberater": [{
    "hochrechnung": {
      "db_prognose": 78000,
      "erreichung_prognose": 139.4,
      "erreichung_soll": 47.8,
      "delta_vs_soll": 18.7,
      "auf_kurs": true
    }
  }]
}
```

### /api/serviceberater/detail/{ma_id}
- Korrigiert: JOIN mit orders für `order_taking_employee_no`
- Neu: `db1`, `db_ziel`, `werktage` in Response

### TEK Breakeven-Prognose
Neue Response-Felder:
```json
{
  "werktage": {
    "gesamt": 23,
    "vergangen": 11,
    "verbleibend": 12,
    "fortschritt_prozent": 47.8
  },
  "db1_soll_bis_heute": 205723.45,
  "db1_pro_werktag": 18702.13
}
```

---

## 4. Konfiguration

### Bayerische Feiertage 2025
```python
FEIERTAGE_2025 = [
    datetime(2025, 1, 1),    # Neujahr
    datetime(2025, 1, 6),    # Heilige Drei Könige
    datetime(2025, 4, 18),   # Karfreitag
    datetime(2025, 4, 21),   # Ostermontag
    datetime(2025, 5, 1),    # Tag der Arbeit
    datetime(2025, 5, 29),   # Christi Himmelfahrt
    datetime(2025, 6, 9),    # Pfingstmontag
    datetime(2025, 6, 19),   # Fronleichnam
    datetime(2025, 8, 15),   # Mariä Himmelfahrt
    datetime(2025, 10, 3),   # Tag der Deutschen Einheit
    datetime(2025, 11, 1),   # Allerheiligen
    datetime(2025, 12, 25),  # 1. Weihnachtstag
    datetime(2025, 12, 26),  # 2. Weihnachtstag
]
```

### TEK-Konfiguration
```python
TEK_CONFIG = {
    'aftersales_deckung_ziel': 0.65,  # 65% der Hauskosten
    'marge_arbeit': 0.554,   # 55,4% (BWA)
    'marge_teile': 0.347,    # 34,7% (BWA)
    'marge_gewichtet': 0.424,  # 42,4%
}
```

---

## 5. Offene Punkte

### 5.1 Locosoft Anwesenheits-Problem (EXTERN)
- Type 1 (Anwesenheit) für Werkstatt-MA fehlt in PostgreSQL
- Wartet auf Locosoft

### 5.2 Werkstatt Tagesbericht Email
- Script lokal erstellt, noch nicht deployed
- TODO: In Celery integrieren

---

## 6. Deployment-Status

**Synced:**
- `api/serviceberater_api.py` ✓
- `routes/controlling_routes.py` ✓
- `templates/aftersales/serviceberater.html` ✓
- `templates/controlling/tek_dashboard.html` ✓

**Neustart erforderlich:** `sudo systemctl restart greiner-portal`

---

*Erstellt: 2025-12-16*
