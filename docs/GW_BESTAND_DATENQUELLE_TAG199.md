# GW-Bestand Dashboard - Datenquelle und Validierung

**TAG:** 199  
**Datum:** 2026-01-19  
**Feature:** GW-Bestand & Standzeit Dashboard

---

## Datenquelle

**Hauptquelle:** Locosoft PostgreSQL-Datenbank (read-only)

### Tabellen

1. **`dealer_vehicles`** (Haupttabelle)
   - Enthält alle Händlerfahrzeuge (Bestand, Kalkulation, Standort)
   - Filter: `out_invoice_date IS NULL` (noch nicht verkauft)
   - Filter: `dealer_vehicle_type = 'G'` (Gebrauchtwagen)

2. **`vehicles`** (Stammdaten)
   - Enthält Fahrzeug-Stammdaten (VIN, Kennzeichen, Modell, EZ)
   - **WICHTIG:** JOIN erfolgt über:
     - `dealer_vehicle_number` + `dealer_vehicle_type` (NICHT über `vehicle_number`!)

### JOIN-Logik

**KORREKT:**
```sql
LEFT JOIN vehicles v 
    ON dv.dealer_vehicle_number = v.dealer_vehicle_number
    AND dv.dealer_vehicle_type = v.dealer_vehicle_type
```

**FALSCH (vorher):**
```sql
LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
```

**Grund:** Die `vehicles`-Tabelle hat sowohl `dealer_vehicle_number` als auch `dealer_vehicle_type` als Felder. Diese müssen beide für den JOIN verwendet werden, um die korrekten Modell-Daten zu erhalten.

---

## Modell-Feld

**Feld:** `v.free_form_model_text` (aus `vehicles`-Tabelle)

**Problem (TAG 199):**
- Modell-Spalte war überwiegend leer
- **Ursache:** Falscher JOIN führte dazu, dass keine Daten aus `vehicles` geholt wurden
- **Lösung:** JOIN korrigiert (siehe oben)

**Alternative Felder (falls `free_form_model_text` leer):**
- `v.model_code` + `models.description` (über `make_number` und `model_code`)
- `dv.out_model_code` + `models.description` (aus `dealer_vehicles`)

---

## Implementierung

**Datei:** `api/fahrzeug_data.py`

**Methoden:**
- `FahrzeugData.get_gw_bestand()` - Hauptmethode für GW-Bestand
- `FahrzeugData.get_standzeit_statistik()` - Aggregierte Statistik
- `FahrzeugData.get_standzeit_warnungen()` - Problemfälle (>90 Tage)

**API-Endpoints:**
- `GET /api/fahrzeug/gw` - GW-Bestand (Liste)
- `GET /api/fahrzeug/gw/dashboard` - Dashboard-Daten (Statistik + Top 10)
- `GET /api/fahrzeug/gw/statistik` - Standzeit-Statistik
- `GET /api/fahrzeug/gw/warnungen` - Warnungen

**Frontend:**
- Route: `/verkauf/gw-bestand`
- Template: `templates/verkauf_gw_dashboard.html`

---

## Korrigierte JOINs (TAG 199)

Alle folgenden Methoden in `api/fahrzeug_data.py` wurden korrigiert:

1. ✅ `get_gw_bestand()` - Zeile 231
2. ✅ `get_nw_pipeline()` - Zeile 321
3. ✅ `get_nw_pipeline_kategorisiert()` - Zeile 410
4. ✅ `get_vfw_bestand()` - Zeile 523
5. ✅ `get_standzeit_warnungen()` - Zeile 688

---

## Validierung

**Nach der Korrektur sollten:**
- ✅ Modell-Spalte in der Problemfälle-Tabelle gefüllt sein
- ✅ Modell-Spalte in der Fahrzeugliste gefüllt sein
- ✅ Alle anderen Felder (VIN, Kennzeichen, EZ) weiterhin funktionieren

**Test:**
1. Dashboard öffnen: `/verkauf/gw-bestand`
2. Prüfen ob Modell-Spalte in Problemfälle-Tabelle gefüllt ist
3. Prüfen ob Modell-Spalte in Fahrzeugliste gefüllt ist

---

## Weitere Informationen

**Datenbank-Schema:**
- `docs/DB_SCHEMA_LOCOSOFT.md` - Locosoft DB-Schema
- Tabelle `dealer_vehicles`: Zeile 530+
- Tabelle `vehicles`: Zeile 1633+

**Referenz-Implementierungen:**
- `api/verkauf_api.py` Zeile 530-532 (korrekter JOIN)
- `scripts/sync/sync_sales.py` Zeile 143-145 (korrekter JOIN)

---

## Deployment

**Nach Änderung:**
```bash
# Service neu starten (Python-Code geändert!)
sudo systemctl restart greiner-portal

# Logs prüfen
journalctl -u greiner-portal -f
```

**Hinweis:** Templates brauchen KEINEN Neustart, nur Browser-Refresh (Strg+F5).

---

**Status:** ✅ JOINs korrigiert, Modell-Daten sollten jetzt verfügbar sein
