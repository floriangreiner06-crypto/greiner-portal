# SESSION WRAP-UP TAG 96
**Datum:** 2025-12-06 (Samstag)  
**Dauer:** ~4 Stunden  
**Fokus:** ML Werkstatt Intelligence

---

## ✅ ERLEDIGT

### 1. Bug-Analyse: Samstag 152h Kapazität
- **Problem:** HEUTE LIVE zeigt 152h Soll am Samstag (sollte 0 sein)
- **Ursache:** In Locosoft `employees_worktimes` haben 98 Mitarbeiter Samstags-Arbeitszeiten gepflegt
- **Lösung:** HR muss in Locosoft korrigieren (nicht im Portal-Code)
- **Doku:** `docs/HR_LOCOSOFT_ARBEITSZEITEN_PFLEGE.md`

### 2. ML Werkstatt Intelligence - KOMPLETT NEU
- **Datenbasis erstellt:**
  - `auftraege_mit_zeiten.csv` - 243.667 Aufträge (roh)
  - `auftraege_mit_zeiten_v2.csv` - 143.510 Aufträge (gefiltert, sauber)
  - `teile_auf_auftraegen.csv` - 114.556 Teile-Positionen
  - `mechaniker_qualitaet.csv` - Qualitäts-Report für HR

- **Datenqualitäts-Filter implementiert:**
  - Azubis rausgefiltert (stempeln nur Anwesenheit)
  - Unplausible Stempelungen entfernt (€/h < 150 oder > 1200)
  - Ergebnis: 41% Müll-Daten entfernt

- **ML-Modell trainiert:**
  - Algorithmus: RandomForest
  - R² Score: 0.749 (75% Erklärungskraft)
  - MAE: 21.6 min (Ø Fehler)
  - Verbesserung vs. Hersteller-Vorgabe: 61%

- **Feature Importance:**
  - Vorgabe-AW: 41.1%
  - km-Stand: 17.2%
  - Startuhrzeit: 14.1%
  - Mechaniker: 7.5%

- **ML-API implementiert:**
  - `POST /api/ml/auftragsdauer` - Dauer vorhersagen
  - `GET /api/ml/mechaniker-ranking` - Effizienz-Ranking
  - `GET /api/ml/statistik` - Modell-Statistiken
  - `GET /api/ml/health` - Health-Check

- **Frontend Dashboard:**
  - Route: `/werkstatt/intelligence`
  - Vorhersage-Tool mit Formular
  - Mechaniker-Ranking mit Effizienz-Balken
  - Feature-Importance Visualisierung
  - KPI-Karten (Genauigkeit, Fehler, Mechaniker)

### 3. Rechnungs-Analyse
- Verknüpfung `invoices` ↔ `times` ↔ `orders` gefunden
- €/h pro Mechaniker berechnet
- Erkannt: Große Unterschiede (57% - 2.357€/h)
- Basis für Datenqualitäts-Filter

---

## 📁 NEUE DATEIEN

```
api/
  ml_api.py                          # ML REST-API (4 Endpoints)

scripts/ml/
  prepare_werkstatt_ml_data.py       # Daten-Export V1 (ungefiltert)
  prepare_werkstatt_ml_data_v2.py    # Daten-Export V2 (gefiltert)
  train_auftragsdauer_model.py       # ML-Modell Training

templates/
  werkstatt_intelligence.html        # ML Dashboard Frontend

data/ml/                             # (lokal auf Server, nicht in Git)
  auftraege_mit_zeiten.csv
  auftraege_mit_zeiten_v2.csv
  teile_auf_auftraegen.csv
  mechaniker_qualitaet.csv
  models/
    auftragsdauer_model.pkl
    label_encoders.pkl
```

---

## 🔧 TECHNISCHE DETAILS

### Installierte Pakete (venv)
```bash
/opt/greiner-portal/venv/bin/pip install scikit-learn
# → scikit-learn, scipy, joblib, threadpoolctl
```

### Installierte Pakete (System - für Scripts)
```bash
pip3 install pandas --break-system-packages
pip3 install scikit-learn --break-system-packages
```

---

## ⚠️ BEKANNTE ISSUES

1. **Mechaniker-Namen fehlen** - Dashboard zeigt nur Nummern
2. **5027/1014 noch im Ranking** - API nutzt alte Daten, Ranking-Filter prüfen
3. **Samstag-Stunden in Locosoft** - HR muss korrigieren
4. **Warnings bei Vorhersage** - sklearn UserWarning (kosmetisch)

---

## 📊 ERKENNTNISSE FÜR GESCHÄFTSFÜHRUNG

1. **Hersteller-Vorgaben sind unzuverlässig:**
   - Erklären nur 41% der tatsächlichen Arbeitszeit
   - IST-Dauer im Schnitt 51% über Vorgabe

2. **Mechaniker-Effizienz variiert stark:**
   - Beste: 122% (schneller als Vorgabe)
   - Schlechteste: 58% (fast doppelt so langsam)
   - 8 Mitarbeiter mit unplausiblen Stempelungen

3. **Datenqualität in Locosoft:**
   - 41% der Stempelungen unbrauchbar für Analyse
   - Azubis stempeln oft nur "anwesend", nicht pro Auftrag
   - Samstags-Arbeitszeiten fälschlich gepflegt

---

## GIT

```
Commit: 62c2f48
Branch: feature/tag82-onwards
Message: TAG 96: ML Werkstatt Intelligence - Auftragsdauer-Vorhersage
Files: 6 changed, 1374 insertions
```
