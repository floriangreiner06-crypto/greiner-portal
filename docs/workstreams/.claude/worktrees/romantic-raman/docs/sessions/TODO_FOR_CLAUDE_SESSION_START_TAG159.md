# TODO FOR CLAUDE - SESSION START TAG 159

**Letzte Session:** TAG 158 (2026-01-02)
**Ziel:** Gap-Tracker implementieren & GW-Standzeit Dashboard

---

## KONTEXT

TAG 158 hat die **Gap-Analyse** abgeschlossen:

### Kernzahlen:
- IST Unternehmensergebnis (Sep-Nov): -162.114 EUR
- Ziel (1% Rendite): +336.519 EUR
- **GAP: 984.974 EUR** (fehlen im GJ 2025/26)
- Pro Monat zusätzlich benötigt: +109.442 EUR

### Hauptproblem identifiziert:
- **GW mit -3.7% Marge** (Ziel: 6%)
- 37 GW mit Standzeit >120 Tage (DEG Opel kritisch)
- Swing-Potenzial: ~720.000 EUR/Jahr

### Dokumentation:
- `docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md` - Vollständiger Plan
- `docs/BWA_KONTEN_MAPPING_FINAL.md` - GlobalCube Referenz

---

## AUFGABEN TAG 159

### Option A: GW-Standzeit Dashboard (Priorität 1)

Neues Dashboard unter `/werkstatt/gw-standzeit` oder `/verkauf/gw-bestand`:

```python
# api/gw_bestand_data.py oder in fahrzeug_data.py
class GWBestandData:
    @staticmethod
    def get_bestand_nach_standzeit(standort=None):
        """
        Holt GW-Bestand direkt aus Locosoft dealer_vehicles
        Kategorien: Frisch, OK, Risiko, Penner, Leichen
        """

    @staticmethod
    def get_standzeitwarnungen():
        """Fahrzeuge die Aufmerksamkeit brauchen"""
```

SQL bereits validiert:
```sql
SELECT * FROM dealer_vehicles
WHERE out_invoice_date IS NULL AND dealer_vehicle_type = 'G'
```

### Option B: Gap-Tracker Endpoint

Neuer Endpoint für monatlichen SOLL-IST Vergleich:

```python
# In controlling_api.py oder unternehmensplan_data.py
@bp.route('/api/controlling/gap-tracker')
def get_gap_tracker():
    """
    Returns:
    - ist_ytd: Unternehmensergebnis YTD
    - soll_ytd: Lineares Ziel YTD
    - prognose_jahr: Hochrechnung auf GJ-Ende
    - gap: Differenz zum 1%-Ziel
    - massnahmen_status: Welche Maßnahmen umgesetzt
    """
```

### Option C: Abteilungsziele definieren

Endpoints für abteilungsspezifische Ziele:

```
GET /api/controlling/abteilungsziele
GET /api/controlling/abteilungsziele/gw
GET /api/controlling/abteilungsziele/werkstatt
```

Mit:
- Monatlichem DB1-Ziel
- Aktueller Performance
- Trend-Indikator

---

## WICHTIGE DATEIEN

```
docs/TAG158_GAP_ANALYSE_MASSNAHMENPLAN.md  - Massnahmenplan
api/unternehmensplan_data.py              - GlobalCube-BWA (SSOT)
api/werkstatt_data.py                     - Mechaniker-Daten
api/controlling_data.py                   - TEK-Daten
```

---

## LOCOSOFT QUERIES (VALIDIERT)

### GW-Bestand
```sql
SELECT
    dv.dealer_vehicle_number,
    v.license_plate,
    v.free_form_model_text,
    dv.in_arrival_date,
    CURRENT_DATE - dv.in_arrival_date as standzeit_tage,
    dv.in_subsidiary as standort
FROM dealer_vehicles dv
JOIN vehicles v ON dv.vehicle_number = v.internal_number
WHERE dv.out_invoice_date IS NULL
  AND dv.dealer_vehicle_type = 'G'
ORDER BY standzeit_tage DESC
```

### Mechaniker (bereits in DRIVE)
```python
WerkstattData.get_mechaniker_leistung(von, bis, betrieb)
```

---

## API ENDPOINTS (NEU ZU ERSTELLEN)

```
# GW-Standzeit:
GET /api/fahrzeug/gw-bestand
GET /api/fahrzeug/gw-bestand/warnungen
GET /api/fahrzeug/gw-bestand/export

# Gap-Tracker:
GET /api/controlling/gap-tracker?gj=2025/26
GET /api/controlling/abteilungsziele
```

---

## PORTAL URLs

- **Unternehmensplan:** https://drive.auto-greiner.de/controlling/unternehmensplan
- **TEK Dashboard:** https://drive.auto-greiner.de/controlling/tek
