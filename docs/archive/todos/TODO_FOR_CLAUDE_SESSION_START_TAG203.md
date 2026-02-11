# TODO für Claude Session Start TAG 203

**Erstellt:** 2026-01-20  
**Letzte Session:** TAG 202

---

## 📋 Offene Aufgaben

### 1. Code-Optimierung (Empfohlen)

**VIN-Suche-Logik dupliziert:**
- Problem: VIN-Suche-Logik ist in `get_fahrzeuge_by_marke` und `get_fahrzeug_details` dupliziert
- Lösung: Helper-Funktion `find_vehicle_by_vin(vin)` in `api/bankenspiegel_api.py` erstellen
- Datei: `api/bankenspiegel_api.py`
- **Priorität:** Hoch

**Genobank-Zinsberechnung:**
- Problem: Zinsen werden bei jedem API-Call neu berechnet (falls nicht vorhanden)
- Lösung: Zinsen beim Import berechnen und in `fahrzeugfinanzierungen` speichern
- Datei: `scripts/imports/import_genobank_finanzierungen.py`
- **Priorität:** Niedrig

**Locosoft-Bulk-Abfrage:**
- Problem: Bei Genobank-Marken-Statistik: N+1 Query Problem (jede VIN einzeln abfragen)
- Lösung: Bulk-Abfrage für alle VINs auf einmal
- Datei: `api/bankenspiegel_api.py` (get_einkaufsfinanzierung)
- **Priorität:** Mittel

**Fahrzeugtyp-Mapping inkonsistent:**
- Problem: `api/ai_api.py` verwendet noch "Tauschfahrzeug" statt "Tageszulassung" für Typ "T"
- Lösung: Mapping in `api/ai_api.py` korrigieren (Zeile 821)
- Datei: `api/ai_api.py`
- **Priorität:** Niedrig

---

### 2. Instituts-Historie vollständig tracken

**Import-Scripts anpassen:**
- Problem: Import-Scripts (z.B. `import_hyundai_finance.py`) löschen alte Einträge, bevor neue eingefügt werden
- Lösung: Alte Einträge auf `aktiv = false` setzen statt löschen
- Dateien:
  - `scripts/imports/import_hyundai_finance.py` - DELETE durch UPDATE ersetzen
  - `scripts/imports/import_stellantis.py` - Prüfen ob UPDATE korrekt ist
  - `scripts/imports/import_genobank_finanzierungen.py` - Prüfen ob UPDATE korrekt ist
- **Priorität:** Mittel

**Alternative: Historie-Tabelle:**
- Option: Separate Tabelle `fahrzeugfinanzierungen_historie` erstellen
- Vorteil: Vollständige Historie ohne Datenverlust
- Nachteil: Mehr Komplexität

---

### 3. Performance-Optimierung (Optional)

**Caching für Locosoft-Abfragen:**
- Falls Fahrzeugdetails häufig aufgerufen werden, könnte Caching helfen
- Redis oder Memory-Cache für VIN → Fahrzeugdetails

**Index auf fahrzeugfinanzierungen.vin:**
- Prüfen ob Index existiert: `CREATE INDEX IF NOT EXISTS idx_fahrzeugfinanzierungen_vin ON fahrzeugfinanzierungen(vin);`

---

### 4. Validierung & Testing

**Instituts-Historie testen:**
- Testen mit Fahrzeugen, die zwischen Instituten gewechselt haben
- Prüfen ob Zinsstartdatum-Text korrekt generiert wird

**Summen-Validierung:**
- Frontend-Validierung: Prüfe ob Summe der Marken-Badges = Gesamtanzahl
- Warnung in Console falls Diskrepanz

---

## 🔍 Qualitätsprobleme (aus TAG 202)

### ⚠️ Bekannte Issues

1. **VIN-Suche-Logik dupliziert**
   - In `get_fahrzeuge_by_marke` und `get_fahrzeug_details`
   - **Priorität:** Hoch
   - **Empfehlung:** Helper-Funktion erstellen

2. **Instituts-Historie nicht vollständig**
   - Import-Scripts löschen alte Einträge
   - **Priorität:** Mittel
   - **Empfehlung:** Alte Einträge auf `aktiv = false` setzen

3. **Genobank-Zinsberechnung**
   - Wird bei jedem API-Call neu berechnet (falls nicht vorhanden)
   - **Priorität:** Niedrig
   - **Empfehlung:** Beim Import berechnen

4. **Fahrzeugtyp-Mapping inkonsistent**
   - `api/ai_api.py` verwendet noch "Tauschfahrzeug"
   - **Priorität:** Niedrig
   - **Empfehlung:** Mapping korrigieren

---

## 📝 Wichtige Hinweise für nächste Session

### Aktuelle Features (TAG 202):
- ✅ Alle VINs klickbar (Top Fahrzeuge, Zinsen-Tabelle, Warnungen-Tabelle, Marken-Modal)
- ✅ Zinsstartdatum im Modal angezeigt
- ✅ Zinsberechnung basiert auf `zins_startdatum` (nicht Standzeit)
- ✅ Zinsberechnung für Genobank im Marken-Modal
- ✅ Fahrzeugtyp "T" → "Tageszulassung" korrigiert
- ✅ Instituts-Historie für Zinsstartdatum (dynamischer Text)

### Datenquellen:
- **fahrzeugfinanzierungen**: Haupttabelle für Finanzierungsdaten
- **Locosoft**: Fahrzeugdetails (VIN, Modell, Marke, EZ, KM)
- **konten & salden**: Genobank-Konto 4700057908 (sollzins)

### API-Endpunkte:
- `GET /api/bankenspiegel/einkaufsfinanzierung` - Hauptübersicht
- `GET /api/bankenspiegel/einkaufsfinanzierung/fahrzeuge?institut=X&marke=Y` - Fahrzeugliste
- `GET /api/bankenspiegel/fahrzeug-details?vin=XXX` - Einzelfahrzeug-Details

### Wichtige Dateien:
- `api/bankenspiegel_api.py` - Haupt-API (3 Endpunkte)
- `templates/einkaufsfinanzierung.html` - Template mit 2 Modalen
- `static/js/einkaufsfinanzierung.js` - Frontend-Logik
- `static/css/einkaufsfinanzierung.css` - CSS-Styling
- `scripts/imports/import_genobank_finanzierungen.py` - Genobank-Import

---

## 🐛 Bekannte Bugs

**Keine kritischen Bugs bekannt.**

**Kleinere Issues:**
- Browser-Cache kann alte Daten zeigen (Strg+F5 löst)
- VIN-Suche kann bei sehr kurzen VINs mehrere Treffer finden (LIMIT 1 verhindert)
- Instituts-Historie nicht vollständig für Fahrzeuge, die vor TAG 202 zwischen Instituten gewechselt haben

---

## 📚 Dokumentation

**Erstellt in TAG 201:**
- `docs/TESTANLEITUNG_FAHRZEUGFINANZIERUNGEN.md` - Testanleitung für Verkaufsleitung & Buchhaltung
- Kopiert nach: `/mnt/greiner-portal-sync/docs/` (Windows-Sync)

**Zu aktualisieren:**
- API-Dokumentation (falls vorhanden)
- Code-Kommentare erweitern

---

## 🔄 Nächste Schritte (Priorität)

1. **Hoch:** VIN-Suche Helper-Funktion erstellen (Code-Duplikat entfernen)
2. **Mittel:** Instituts-Historie vollständig tracken (Import-Scripts anpassen)
3. **Mittel:** Locosoft-Bulk-Abfrage für Genobank-Marken-Statistik
4. **Niedrig:** Genobank-Zinsen beim Import berechnen
5. **Niedrig:** Fahrzeugtyp-Mapping in `api/ai_api.py` korrigieren

---

**Ende TODO_FOR_CLAUDE_SESSION_START_TAG203**
