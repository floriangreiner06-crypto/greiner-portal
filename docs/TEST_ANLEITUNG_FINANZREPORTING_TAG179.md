# Test-Anleitung: Finanzreporting Cube - TAG 179

**Datum:** 2026-01-10  
**Version:** 1.0

---

## 📋 ÜBERBLICK

Diese Anleitung beschreibt, wie Sie die neuen Features des Finanzreporting Cubes testen:

1. ✅ **Export-Funktion** (CSV/Excel)
2. ✅ **Metadaten-Endpunkt** (für Dropdowns)
3. ✅ **Automatischer Refresh** (Celery-Task)
4. ✅ **Frontend-Integration**

---

## 🚀 VORBEREITUNG

### 1. Service-Status prüfen

**Service sollte laufen:**
```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S systemctl status greiner-portal
```

**Falls nicht gestartet:**
```bash
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal
```

### 2. Browser öffnen

**URL:** `http://10.80.80.20:5000/controlling/finanzreporting`

**Login:** Mit Ihren AD-Credentials anmelden

---

## 🧪 TEST 1: Metadaten-Endpunkt

### Ziel
Prüfen, ob Metadaten korrekt geladen werden und Dropdowns befüllt werden.

### Schritte

1. **Seite öffnen:**
   - Navigieren Sie zu: `http://10.80.80.20:5000/controlling/finanzreporting`

2. **Browser-Console öffnen:**
   - F12 drücken
   - Tab "Console" öffnen

3. **Prüfen:**
   - ✅ Standorte-Dropdown sollte befüllt sein (DEG, HYU, LAN)
   - ✅ Konto-Ebenen-Dropdown sollte befüllt sein (400, 700, 800, etc.)
   - ✅ Keine Fehler in der Console

4. **Manueller API-Test (optional):**
   ```bash
   curl http://10.80.80.20:5000/api/finanzreporting/cube/metadata | python3 -m json.tool
   ```

**Erwartetes Ergebnis:**
- Dropdowns sind befüllt
- Keine Fehler in der Console
- Metadaten-Endpunkt gibt JSON zurück

---

## 🧪 TEST 2: Daten laden & Anzeige

### Ziel
Prüfen, ob Daten korrekt geladen und angezeigt werden.

### Schritte

1. **Filter setzen:**
   - **Zeitraum von:** `2024-09-01`
   - **Zeitraum bis:** `2024-10-31`
   - **Standort:** `Alle` (oder spezifisch: DEG, HYU, LAN)
   - **Konto-Ebene 3:** `800` (Umsatz)

2. **Dimensionen wählen:**
   - ✅ **Zeit** (aktiviert)
   - Optional: Standort, KST, Konto

3. **Measures wählen:**
   - ✅ **Betrag** (aktiviert)
   - Optional: Menge

4. **"Daten laden" klicken**

5. **Prüfen:**
   - ✅ Loading-Spinner erscheint kurz
   - ✅ KPI-Karten werden angezeigt:
     - Total Betrag
     - Total Menge
     - Anzahl Datensätze
     - Abfrage-Zeit
   - ✅ Chart wird angezeigt (Bar-Chart)
   - ✅ Tabelle wird angezeigt mit Daten

**Erwartetes Ergebnis:**
- Daten werden geladen
- KPI-Karten zeigen korrekte Werte
- Chart zeigt Visualisierung
- Tabelle zeigt Daten

---

## 🧪 TEST 3: Export-Funktion (CSV)

### Ziel
Prüfen, ob CSV-Export funktioniert.

### Schritte

1. **Daten laden:**
   - Filter setzen (siehe TEST 2)
   - "Daten laden" klicken
   - Warten bis Daten angezeigt werden

2. **CSV-Export:**
   - ✅ "CSV exportieren" Button sollte aktiviert sein (grün)
   - "CSV exportieren" klicken

3. **Prüfen:**
   - ✅ Download startet automatisch
   - ✅ Dateiname: `finanzreporting_cube_YYYYMMDD_HHMMSS.csv`
   - ✅ Datei öffnen (Excel/LibreOffice)
   - ✅ Spalten: Zeit, Standort (falls gewählt), Betrag, etc.
   - ✅ Daten korrekt (Dezimaltrennzeichen: Komma)

**Erwartetes Ergebnis:**
- Download startet
- CSV-Datei ist korrekt formatiert
- Daten stimmen mit Anzeige überein

---

## 🧪 TEST 4: Export-Funktion (Excel)

### Ziel
Prüfen, ob Excel-Export funktioniert.

### Schritte

1. **Daten laden:**
   - Filter setzen (siehe TEST 2)
   - "Daten laden" klicken

2. **Excel-Export:**
   - ✅ "Excel exportieren" Button sollte aktiviert sein (grün)
   - "Excel exportieren" klicken

3. **Prüfen:**
   - ✅ Download startet automatisch
   - ✅ Dateiname: `finanzreporting_cube_YYYYMMDD_HHMMSS.xlsx`
   - ✅ Datei öffnen (Excel/LibreOffice)
   - ✅ Spalten korrekt
   - ✅ Daten korrekt

**Erwartetes Ergebnis:**
- Download startet
- Excel-Datei ist korrekt formatiert
- Daten stimmen mit Anzeige überein

**Hinweis:** Falls Excel-Export nicht funktioniert, prüfen Sie ob `pandas` und `openpyxl` installiert sind.

---

## 🧪 TEST 5: Verschiedene Filter-Kombinationen

### Ziel
Prüfen, ob verschiedene Filter-Kombinationen funktionieren.

### Test-Kombinationen

#### Kombination 1: Zeit + Standort
- **Dimensionen:** Zeit, Standort
- **Measures:** Betrag
- **Filter:** Zeitraum 2024-09-01 bis 2024-10-31, Standort: DEG
- **Erwartung:** Daten nach Zeit und Standort gruppiert

#### Kombination 2: Zeit + KST
- **Dimensionen:** Zeit, KST
- **Measures:** Betrag
- **Filter:** Zeitraum 2024-09-01 bis 2024-10-31, Konto-Ebene: 700
- **Erwartung:** Daten nach Zeit und KST gruppiert

#### Kombination 3: Alle Dimensionen
- **Dimensionen:** Zeit, Standort, KST, Konto
- **Measures:** Betrag, Menge
- **Filter:** Zeitraum 2024-09-01 bis 2024-10-31
- **Erwartung:** Daten nach allen Dimensionen gruppiert

**Erwartetes Ergebnis:**
- Alle Kombinationen funktionieren
- Daten werden korrekt gruppiert
- Export funktioniert mit allen Kombinationen

---

## 🧪 TEST 6: Cube-Refresh (Manuell)

### Ziel
Prüfen, ob manueller Cube-Refresh funktioniert.

### Schritte

1. **"Cube aktualisieren" klicken**

2. **Bestätigung:**
   - ✅ Bestätigungs-Dialog erscheint
   - "OK" klicken

3. **Warten:**
   - ✅ Erfolgs-Meldung erscheint: "Cube erfolgreich aktualisiert!"
   - Dauer: ~10-30 Sekunden (abhängig von Datenmenge)

4. **Prüfen:**
   - ✅ Keine Fehler
   - ✅ Daten können danach geladen werden

**Erwartetes Ergebnis:**
- Refresh funktioniert
- Erfolgs-Meldung erscheint
- Daten können danach geladen werden

**Hinweis:** Automatischer Refresh läuft täglich um 19:20 Uhr (nach Locosoft Mirror).

---

## 🧪 TEST 7: Fehlerbehandlung

### Ziel
Prüfen, ob Fehler korrekt behandelt werden.

### Test-Szenarien

#### Szenario 1: Ungültige Dimension
- **URL:** `/api/finanzreporting/cube?dimensionen=invalid&measures=betrag`
- **Erwartung:** Fehler-Meldung: "Ungültige Dimension: invalid"

#### Szenario 2: Keine Daten
- **Filter:** Zeitraum in der Zukunft (z.B. 2030-01-01 bis 2030-12-31)
- **Erwartung:** 
  - Count: 0
  - Leere Tabelle
  - Keine Fehler

#### Szenario 3: Export ohne Daten
- **Schritte:**
  1. Filter setzen, die keine Daten liefern
  2. "Daten laden" klicken
  3. "CSV exportieren" klicken
- **Erwartung:** 
  - Export-Button deaktiviert oder
  - Fehler-Meldung: "Bitte laden Sie zuerst Daten!"

**Erwartetes Ergebnis:**
- Fehler werden korrekt behandelt
- Benutzerfreundliche Fehler-Meldungen
- Keine Crashes

---

## 🔍 API-TESTS (Manuell)

### Test 1: Metadaten-Endpunkt

```bash
curl http://10.80.80.20:5000/api/finanzreporting/cube/metadata | python3 -m json.tool
```

**Erwartetes Ergebnis:**
```json
{
    "dimensionen": [...],
    "measures": [...],
    "standorte": [...],
    "kostenstellen": [...],
    "konto_ebenen": [...]
}
```

---

### Test 2: Cube-Endpunkt

```bash
curl "http://10.80.80.20:5000/api/finanzreporting/cube?dimensionen=zeit&measures=betrag&von=2024-09-01&bis=2024-10-31&konto_ebene3=800" | python3 -m json.tool
```

**Erwartetes Ergebnis:**
```json
{
    "dimensionen": ["zeit"],
    "measures": ["betrag"],
    "data": [...],
    "total": {"betrag": ...},
    "count": ...
}
```

---

### Test 3: Export-Endpunkt (CSV)

```bash
curl "http://10.80.80.20:5000/api/finanzreporting/cube/export?format=csv&dimensionen=zeit&measures=betrag&von=2024-09-01&bis=2024-10-31" -o test_export.csv
```

**Prüfen:**
- Datei wird erstellt
- Datei ist CSV-format
- Daten sind korrekt

---

### Test 4: Export-Endpunkt (Excel)

```bash
curl "http://10.80.80.20:5000/api/finanzreporting/cube/export?format=excel&dimensionen=zeit&measures=betrag&von=2024-09-01&bis=2024-10-31" -o test_export.xlsx
```

**Prüfen:**
- Datei wird erstellt
- Datei ist Excel-format (.xlsx)
- Daten sind korrekt

---

## ✅ CHECKLISTE

### Frontend
- [ ] Seite lädt ohne Fehler
- [ ] Metadaten-Dropdowns sind befüllt
- [ ] Filter funktionieren
- [ ] "Daten laden" funktioniert
- [ ] KPI-Karten werden angezeigt
- [ ] Chart wird angezeigt
- [ ] Tabelle wird angezeigt
- [ ] Export-Buttons werden aktiviert nach Datenladen
- [ ] CSV-Export funktioniert
- [ ] Excel-Export funktioniert
- [ ] "Cube aktualisieren" funktioniert

### API
- [ ] Metadaten-Endpunkt gibt korrekte Antwort
- [ ] Cube-Endpunkt gibt korrekte Antwort
- [ ] Export-Endpunkt (CSV) funktioniert
- [ ] Export-Endpunkt (Excel) funktioniert
- [ ] Refresh-Endpunkt funktioniert

### Daten
- [ ] Daten werden korrekt geladen
- [ ] Filter funktionieren korrekt
- [ ] Gruppierung funktioniert korrekt
- [ ] Export-Daten stimmen mit Anzeige überein

---

## 🐛 BEKANNTE PROBLEME

### Problem 1: Excel-Export funktioniert nicht

**Symptom:** Excel-Export gibt Fehler: "Excel-Export erfordert pandas und openpyxl"

**Lösung:**
```bash
# Sudo-Passwort: OHL.greiner2025
echo 'OHL.greiner2025' | sudo -S pip3 install pandas openpyxl
echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal
```

---

### Problem 2: Metadaten-Dropdowns sind leer

**Symptom:** Dropdowns sind nicht befüllt

**Prüfen:**
1. Browser-Console öffnen (F12)
2. Prüfen ob Fehler vorhanden
3. Prüfen ob Metadaten-Endpunkt erreichbar ist

**Lösung:**
- Service-Neustart: `echo 'OHL.greiner2025' | sudo -S systemctl restart greiner-portal`
- Prüfen ob Metadaten-Endpunkt funktioniert

---

### Problem 3: Export-Buttons sind deaktiviert

**Symptom:** Export-Buttons bleiben grau/deaktiviert

**Lösung:**
- Zuerst "Daten laden" klicken
- Buttons werden nach erfolgreichem Datenladen aktiviert

---

## 📊 ERFOLGS-KRITERIEN

### ✅ Alle Tests erfolgreich:
- Frontend lädt ohne Fehler
- Daten werden korrekt angezeigt
- Export funktioniert (CSV + Excel)
- Metadaten werden geladen
- Filter funktionieren
- Refresh funktioniert

### ⚠️ Teilweise erfolgreich:
- Frontend funktioniert, aber Export hat Probleme
- Daten werden angezeigt, aber Metadaten nicht

### ❌ Tests fehlgeschlagen:
- Frontend lädt nicht
- API-Endpunkte geben Fehler
- Export funktioniert nicht

---

## 📝 FEHLER-MELDUNG

Falls Probleme auftreten, bitte folgende Informationen sammeln:

1. **Browser-Console:**
   - F12 drücken
   - Tab "Console" öffnen
   - Screenshot oder Text kopieren

2. **API-Response:**
   - Network-Tab öffnen (F12)
   - Request/Response prüfen
   - Screenshot oder Text kopieren

3. **Server-Logs:**
   ```bash
   # Sudo-Passwort: OHL.greiner2025
   echo 'OHL.greiner2025' | sudo -S journalctl -u greiner-portal -n 50 --no-pager
   ```

4. **Beschreibung:**
   - Was wurde getestet?
   - Was war erwartet?
   - Was ist passiert?

---

## 🎯 NÄCHSTE SCHRITTE

Nach erfolgreichen Tests:

1. ✅ **User-Feedback sammeln**
2. ✅ **Performance messen** (Abfrage-Zeiten)
3. ✅ **Weitere Features planen** (Vergleichsfunktion, Drill-Down)

---

**Viel Erfolg beim Testen! 🚀**
