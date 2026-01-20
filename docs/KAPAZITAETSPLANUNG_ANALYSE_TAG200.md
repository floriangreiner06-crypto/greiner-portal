# Kapazitätsplanung - Feature-Analyse und Status

**Erstellt:** 2026-01-XX (TAG 200)  
**Ziel:** Überblick über das Feature "Kapazitätsplanung", Identifikation von Problemen und unvollständigen Funktionen

---

## 📋 ÜBERBLICK

Das Feature **Kapazitätsplanung** wurde in **TAG 116** (2025-12-12) entwickelt und aus dem Dashboard ausgelagert. Es kombiniert mehrere Datenquellen:

1. **10-Tage Forecast** - Vorausschau auf geplante Kapazität vs. geplante Arbeit
2. **Gudat Team-Kapazität** - Live-Daten aus Gudat Werkstattplanung
3. **ML Auftrags-Analyse** - Maschinelles Lernen zur Erkennung unterbewerteter/überbewerteter Aufträge
4. **AVG-Verzögerungsgründe** - Abrechnungs-Verzögerungs-Statistik

**Route:** `/aftersales/kapazitaetsplanung`  
**Template:** `templates/aftersales/kapazitaetsplanung.html`  
**API-Endpunkt:** `/api/werkstatt/live/forecast`

---

## 🔍 KOMPONENTEN-ANALYSE

### 1. 10-Tage Forecast (Hauptkomponente)

**Status:** ⚠️ **NICHT VOLLSTÄNDIG FUNKTIONAL**

**Implementierung:**
- **Datei:** `api/werkstatt_live_api.py` (Zeile 1105-1658)
- **Endpoint:** `GET /api/werkstatt/live/forecast`
- **Features:**
  - Arbeitstage-Erkennung (ohne Wochenende, mit Feiertagen)
  - Tagesweise Kapazität (Mechaniker × Arbeitszeiten - Abwesenheiten)
  - Geplante Aufträge pro Tag (basierend auf `estimated_inbound_time`)
  - Auslastungsberechnung
  - Warnungen (unverplante, überfällige Aufträge, fehlende Teile)

**Berechnungslogik:**
```python
# Kapazität = Summe(Arbeitszeiten anwesender Mechaniker) × 6 AW/Stunde
kapazitaet_aw = kapazitaet_h * 6

# Geplant = Summe(Vorgabe-AW aller Aufträge mit Termin an diesem Tag)
geplant_aw = sum(auftrag['vorgabe_aw'] for auftrag in auftraege_tag)

# Auslastung = (Geplant / Kapazität) × 100
auslastung = (geplant_aw / kapazitaet_aw) * 100
```

**Probleme identifiziert:**

1. **Datenqualität:**
   - ⚠️ **0% Auslastung für HEUTE** - deutet auf fehlende oder falsche Termine hin
   - ⚠️ **Leere "Verzögerungsgründe"** - AVG-Daten scheinen nicht verfügbar zu sein
   - ⚠️ **Forecast zeigt "N/A"** - API-Fehler oder Datenproblem

2. **Datenquellen:**
   - **Locosoft DB:** `orders`, `labours`, `employees_history`, `employees_worktimes`, `absence_calendar`
   - **Portal DB:** `stellantis_bestellungen` (Servicebox)
   - **Problem:** Abhängigkeit von `estimated_inbound_time` - wenn nicht gepflegt, keine Forecast-Daten

3. **Abwesenheitslogik:**
   - Verwendet `absence_calendar` für Urlaub/Krankheit
   - **Potenzialproblem:** `day_contingent` (halbe Tage) wird möglicherweise nicht korrekt berücksichtigt

**Frontend-Hinweis:**
```javascript
// Zeile 621-624: Fallback bei API-Fehler
'Kapazitäts-Forecast wird noch entwickelt. Nutzen Sie vorerst die LIVE-Daten oben.'
```

---

### 2. Gudat Team-Kapazität

**Status:** ✅ **FUNKTIONAL, ABER DATENVALIDITÄT FRAGLICH**

**Implementierung:**
- **Datei:** `api/werkstatt_live_api.py` (Zeile 1005-1090)
- **Endpoint:** `GET /api/werkstatt/live/gudat/kapazitaet`
- **Proxy:** Ruft interne Gudat-API auf (`/api/gudat/workload`)

**Features:**
- Gesamtkapazität (nur interne Teams, TAG 122)
- Verplante AW
- Freie Kapazität
- Wochenübersicht (täglich)
- Teams nach Auslastung

**Probleme identifiziert:**

1. **Negative freie AW:**
   - ⚠️ **"Diagnosetechnik: -41 AW frei"** bei 67% Auslastung
   - **Ursache:** Berechnungsfehler oder Überbuchung in Gudat
   - **Formel:** `frei = kapazitaet - geplant` → kann negativ werden bei Überbuchung

2. **Interne Teams-Filter:**
   - TAG 122: Nur Teams mit IDs in `INTERNE_TEAMS` werden gezählt
   - **Problem:** Externe Teams (z.B. "Smart Repair Lack (Extern)") werden ausgeblendet, aber möglicherweise trotzdem angezeigt

3. **Datenaktualität:**
   - Zeitstempel im Frontend: "Stand: 08:02"
   - **Frage:** Wie oft wird aktualisiert? (scheint statisch zu sein)

**Gudat-API:**
- **Datei:** `api/gudat_api.py`
- **Client:** `tools/gudat_client.py`
- **Credentials:** `config/credentials.json` → `external_systems.gudat`

---

### 3. ML Auftrags-Analyse

**Status:** ✅ **FUNKTIONAL**

**Implementierung:**
- **Datei:** `api/werkstatt_live_api.py` (Zeile 2001-2600)
- **Endpoint:** `GET /api/werkstatt/live/auftraege-enriched`
- **ML-API:** `api/ml_prediction_api.py`

**Features:**
- **Unterbewertete Aufträge:** ML-Prognose > Vorgabe (mehr Zeit nötig)
- **Überbewertete Aufträge:** ML-Prognose < Vorgabe (geht schneller)
- **Potenzial-Berechnung:** Summe der zusätzlichen AW bei korrekter Planung
- **Umsatz-Potenzial:** Potenzial-AW × AW-Preis (107.460,00 € im Screenshot)

**ML-Logik:**
```python
# Zeile 2435-2450
if ml_potenzial > 1.0:
    ml_status = 'unterbewertet'  # Dauert deutlich länger
elif ml_potenzial > 0.3:
    ml_status = 'leicht_unterbewertet'
elif ml_potenzial < -0.5:
    ml_status = 'überbewertet'  # Geht schneller
```

**Datenqualität:**
- ✅ **Funktioniert** - zeigt 130 unterbewertete, 58 überbewertete Aufträge
- ✅ **Potenzial-Berechnung** plausibel (1075 AW mehr möglich)
- ⚠️ **Abhängig von ML-Modell-Qualität** - Modell muss regelmäßig neu trainiert werden

**ML-Modell:**
- **Technologie:** XGBoost (Gradient Boosting)
- **Genauigkeit:** R² = 0.749, MAE = 21.6 Minuten (laut `docs/ML_VS_OPENAI_VERGLEICH_TAG181.md`)
- **Training:** Statisches Modell auf historischen Daten

---

### 4. AVG-Verzögerungsgründe

**Status:** ⚠️ **KEINE DATEN**

**Implementierung:**
- **Datei:** `api/werkstatt_live_api.py` (Zeile 1556-1590)
- **SQL-Query:** `orders.clearing_delay_type` + `clearing_delay_types.description`

**Probleme:**
- ⚠️ **Frontend zeigt "Keine Daten"**
- **Mögliche Ursachen:**
  1. `clearing_delay_type` ist NULL oder leer in den meisten Aufträgen
  2. `clearing_delay_types`-Tabelle existiert nicht oder ist leer
  3. Query-Fehler (nicht sichtbar im Frontend)

**SQL-Query:**
```sql
SELECT
    o.clearing_delay_type as avg_code,
    cdt.description as avg_text,
    COUNT(*) as anzahl,
    COALESCE(SUM(l.time_units), 0) as summe_aw
FROM orders o
LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
WHERE o.has_open_positions = true
  AND o.clearing_delay_type IS NOT NULL
  AND o.clearing_delay_type != ''
GROUP BY o.clearing_delay_type, cdt.description
```

---

## 🐛 IDENTIFIZIERTE PROBLEME

### Kritisch

1. **Forecast zeigt "N/A" / 0% Auslastung**
   - **Symptom:** HEUTE zeigt 0% Auslastung, 0 AW gestempelt, 0,00 € Umsatz
   - **Ursache:** API-Fehler oder fehlende Termine in `orders.estimated_inbound_time`
   - **Impact:** Hauptfunktion nicht nutzbar

2. **Negative freie AW in Gudat**
   - **Symptom:** "Diagnosetechnik: -41 AW frei" bei 67% Auslastung
   - **Ursache:** Überbuchung oder Berechnungsfehler in Gudat
   - **Impact:** Daten nicht vertrauenswürdig

3. **AVG-Verzögerungsgründe leer**
   - **Symptom:** "Keine Daten" im Frontend
   - **Ursache:** `clearing_delay_type` nicht gepflegt oder Tabelle fehlt
   - **Impact:** Feature nicht nutzbar

### Mittel

4. **Wochenübersicht unvollständig**
   - **Symptom:** "von - AW" statt konkreter Werte
   - **Ursache:** Datenformat-Problem im Frontend oder API

5. **Teile-Status möglicherweise unvollständig**
   - **Symptom:** Leere Listen für "Warten auf Teile"
   - **Ursache:** Query filtert möglicherweise zu restriktiv

---

## 📊 DATENFLUSS

```
┌─────────────────┐
│  Locosoft DB    │
│  - orders       │
│  - labours      │
│  - employees_*  │
│  - absence_*    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Forecast API   │
│  /forecast      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │
│  kapazitaets-   │
│  planung.html   │
└─────────────────┘

┌─────────────────┐
│  Gudat Portal   │
│  (Selenium)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gudat Client   │
│  gudat_client   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gudat API      │
│  /gudat/workload│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Werkstatt API  │
│  /gudat/kapazit │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │
└─────────────────┘
```

---

## 🔧 EMPFOHLENE MASSNAHMEN

### Sofort (Kritisch)

1. **Forecast-API debuggen:**
   ```bash
   # API direkt testen
   curl http://localhost:5000/api/werkstatt/live/forecast?subsidiary=1
   
   # Logs prüfen
   journalctl -u greiner-portal -f | grep forecast
   ```

2. **Datenqualität prüfen:**
   ```sql
   -- Prüfe: Wie viele Aufträge haben Termine?
   SELECT 
       COUNT(*) as gesamt,
       COUNT(estimated_inbound_time) as mit_termin,
       COUNT(*) FILTER (WHERE DATE(estimated_inbound_time) = CURRENT_DATE) as heute
   FROM orders
   WHERE has_open_positions = true;
   
   -- Prüfe: AVG-Daten
   SELECT COUNT(*), COUNT(clearing_delay_type)
   FROM orders
   WHERE has_open_positions = true;
   ```

3. **Gudat negative Werte analysieren:**
   - Prüfe Gudat-Client-Logik in `tools/gudat_client.py`
   - Validiere Berechnung: `frei = kapazitaet - geplant`

### Kurzfristig (1-2 Tage)

4. **Fehlerbehandlung verbessern:**
   - API sollte detaillierte Fehlermeldungen zurückgeben
   - Frontend sollte Fehler anzeigen statt "N/A"

5. **Datenvalidierung:**
   - Prüfe `employees_worktimes` - sind Arbeitszeiten korrekt?
   - Prüfe `absence_calendar` - werden Abwesenheiten korrekt erfasst?

6. **AVG-Feature reparieren oder deaktivieren:**
   - Wenn Daten nicht verfügbar: Feature ausblenden
   - Wenn Daten verfügbar: Query debuggen

### Mittelfristig (1 Woche)

7. **Forecast-Logik überarbeiten:**
   - Fallback wenn `estimated_inbound_time` fehlt (z.B. `order_date`)
   - Bessere Validierung der Eingabedaten

8. **Dokumentation:**
   - Erstelle Anleitung: "Wie pflege ich Termine für Kapazitätsplanung?"
   - Dokumentiere Datenquellen und Berechnungslogik

9. **Monitoring:**
   - Health-Check für Forecast-API
   - Alerts bei 0% Auslastung über mehrere Tage

---

## 📝 CODE-REFERENZEN

### Wichtige Dateien

- **API:** `api/werkstatt_live_api.py`
  - Forecast: Zeile 1105-1658
  - Gudat: Zeile 1005-1090
  - ML-Analyse: Zeile 2001-2600
  - AVG: Zeile 1556-1590

- **Routes:** `routes/werkstatt_routes.py`
  - Route: Zeile 140-145

- **Templates:** `templates/aftersales/kapazitaetsplanung.html`
  - Forecast-Loading: Zeile 601-626
  - Gudat-Loading: Zeile 810-826
  - ML-Rendering: Zeile 952-990

- **Gudat-Integration:**
  - API: `api/gudat_api.py`
  - Client: `tools/gudat_client.py`

- **ML-Integration:**
  - API: `api/ml_prediction_api.py`
  - Model: `scripts/ml/train_auftragsdauer_model_v2.py`

### Analyse-Scripte

- **Datenanalyse:** `scripts/analysis/analyse_kapazitaet_daten.py`
  - Prüft Datenquellen und Berechnungslogik
  - Kann zur Diagnose verwendet werden

---

## 🎯 ZUSAMMENFASSUNG

**Status:** ⚠️ **TEILWEISE FUNKTIONAL**

**Funktioniert:**
- ✅ Gudat Team-Kapazität (mit Datenvaliditätsproblemen)
- ✅ ML Auftrags-Analyse
- ✅ Frontend-Struktur und UI

**Probleme:**
- ❌ Forecast zeigt "N/A" / 0% Auslastung
- ❌ AVG-Verzögerungsgründe leer
- ⚠️ Negative freie AW in Gudat
- ⚠️ Datenqualität fraglich

**Nächste Schritte:**
1. API-Fehler debuggen (Forecast)
2. Datenqualität prüfen (Termine, AVG)
3. Gudat-Berechnung validieren
4. Fehlerbehandlung verbessern

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-XX  
**TAG:** 200
