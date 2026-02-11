# TODO für Claude - Session Start TAG 205

**Erstellt:** 2026-01-21  
**Letzte Session:** TAG 204

---

## 📋 Offene Aufgaben

### 1. User-Feedback abwarten
- **Status:** ⏳ Pending
- **Beschreibung:** Warten auf User-Feedback, ob Alarm-E-Mails jetzt korrekte Werte zeigen
- **Erwartung:** Neue E-Mails sollten 116 Min statt 599 Min zeigen (mit korrekter Deduplizierung)

### 2. Stempeluhr LIVE Test
- **Status:** ⏳ Pending
- **Beschreibung:** Prüfen, ob Stempeluhr LIVE jetzt korrekte Werte anzeigt (ohne Pause abgezogen)
- **Erwartung:** Werte sollten mit Locosoft Realzeit übereinstimmen

### 3. Ungenutzte Funktion entfernen
- **Status:** ⏳ Pending
- **Beschreibung:** Funktion `berechne_netto_laufzeit_mit_pause()` in `api/werkstatt_data.py` (Zeile 1840-1880) wurde hinzugefügt, aber nicht verwendet
- **Optionen:**
  - Funktion entfernen (wenn nicht benötigt)
  - Funktion dokumentieren (wenn für zukünftige Verwendung)
- **Datei:** `api/werkstatt_data.py`

---

## 🔍 Qualitätsprobleme

### 1. Ungenutzte Funktion
- **Datei:** `api/werkstatt_data.py`
- **Zeile:** 1840-1880
- **Problem:** `berechne_netto_laufzeit_mit_pause()` wurde hinzugefügt, aber nicht verwendet
- **Empfehlung:** Entfernen oder dokumentieren

---

## 🎯 Nächste Schritte

1. **User-Feedback prüfen:** Werden Alarm-E-Mails jetzt korrekte Werte zeigen?
2. **Stempeluhr LIVE testen:** Werden die Werte jetzt korrekt angezeigt?
3. **Code-Cleanup:** Ungenutzte Funktion entfernen oder dokumentieren

---

## 💡 Wichtige Hinweise

1. **Locosoft Realzeit:** Brutto-Zeit (ohne Pause abzuziehen)
2. **Deduplizierung:** `DISTINCT ON (employee_number, order_number, start_time, end_time)`
3. **Alte E-Mails:** Wurden mit falscher Berechnung erstellt, neue sollten korrekt sein

---

## 🔗 Referenzen

- **TAG 204:** Alarm-E-Mail Bugfixes und Stempeluhr-Berechnungslogik
- **TAG 194:** Deduplizierungs-Logik korrigiert
- **TAG 193:** Laufzeit-Berechnung für aktive Aufträge
