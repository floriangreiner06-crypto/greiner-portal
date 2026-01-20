# Urlaubsplaner Testanleitung - TAG 198

**Datum:** 2026-01-19  
**Zweck:** Test der behobenen Bugs und neuen Features

---

## 🧪 TEST-CHECKLISTE

### ✅ 1. Genehmigungsfunktion testen

**Test als Admin:**
1. Als Admin einloggen (z.B. Christian Aichinger)
2. Urlaubsplaner öffnen: `/urlaubsplaner`
3. In "Zu genehmigen" Box prüfen ob Anträge angezeigt werden
4. Auf "OK" Button klicken bei einem Antrag
5. Modal sollte erscheinen mit Mitarbeiter-Name und Datum
6. Auf "Genehmigen" klicken
7. ✅ **Erwartet:** Toast "Genehmigt!" erscheint, Antrag verschwindet aus Liste

**Test als normaler Genehmiger:**
1. Als Genehmiger einloggen (z.B. Vanessa Groll)
2. Prüfen ob eigene Team-Mitglieder in "Zu genehmigen" angezeigt werden
3. Antrag genehmigen
4. ✅ **Erwartet:** Genehmigung funktioniert

---

### ✅ 2. Resturlaubstage prüfen

**Test:**
1. Eigene Balance prüfen (rechts oben im Planer)
2. Urlaub beantragen (z.B. 5 Tage)
3. Nach Genehmigung Balance erneut prüfen
4. ✅ **Erwartet:** Resturlaub reduziert sich um beantragte Tage
5. Prüfen bei verschiedenen Mitarbeitern (z.B. Bianca Greindl, Herbert Huber)
6. ✅ **Erwartet:** Resturlaub zeigt korrekte Werte (nicht 41 Tage wenn falsch)

---

### ✅ 3. Jahreswechsel-Logik testen

**Test:**
1. Im Urlaubsplaner zu Januar 2027 wechseln
2. Prüfen ob Mitarbeiter Standard-Anspruch (27 Tage) haben
3. Prüfen ob vorherige Buchungen aus 2026 nicht mehr angezeigt werden
4. ✅ **Erwartet:** Neues Jahr startet mit 27 Tagen Anspruch

---

### ✅ 4. Falsche Darstellung prüfen

**Test:**
1. Als Christian Aichinger einloggen
2. Urlaubsplaner öffnen
3. Zu Juni 2026 navigieren
4. Prüfen ob nur Vanessa Grolls Buchungen bei Vanessa angezeigt werden
5. Prüfen ob keine Buchungen von Vanessa bei Christian angezeigt werden
6. ✅ **Erwartet:** Buchungen werden nur bei korrektem Mitarbeiter angezeigt

---

### ✅ 5. Urlaubssperren testen

**Test als Admin:**
1. Als Admin einloggen
2. Urlaubsplaner Admin öffnen: `/urlaubsplaner/admin`
3. "Urlaubssperren" Tab öffnen
4. Neue Sperre erstellen:
   - Datum wählen
   - Abteilung wählen (z.B. "Service")
   - Grund eingeben
5. Im Urlaubsplaner prüfen
6. ✅ **Erwartet:** Betroffene Zellen haben roten Rand

---

### ✅ 6. Masseneingaben testen

**Test als Admin:**
1. Als Admin einloggen
2. Urlaubsplaner Admin öffnen
3. "Masseneingaben" Button klicken
4. Modal öffnet sich
5. Abteilung oder Mitarbeiter auswählen
6. Zeitraum wählen (z.B. 01.06.2026 - 05.06.2026)
7. Urlaubstyp wählen
8. "Speichern" klicken
9. ✅ **Erwartet:** Urlaub wird für alle ausgewählten Mitarbeiter eingetragen

---

### ✅ 7. Jahresend-Report testen

**Test als Admin:**
1. Als Admin einloggen
2. Urlaubsplaner Admin öffnen
3. "Jahresend-Report" Button klicken
4. Jahr wählen (z.B. 2025)
5. CSV-Datei wird heruntergeladen
6. CSV in Excel öffnen
7. ✅ **Erwartet:** 
   - Daten sind korrekt (nicht verschoben)
   - Umlaute werden korrekt angezeigt
   - Spalten: Name, Standort, Gruppe, Anspruch, Übertrag, Urlaub, ZA, Krank, Sonstige, Verfügbar

---

### ✅ 8. Freie Tage testen

**Test als Admin:**
1. Als Admin einloggen
2. Urlaubsplaner Admin öffnen
3. "Freie Tage" Tab öffnen
4. Neuen freien Tag erstellen:
   - Datum wählen (z.B. jeden Mittwoch)
   - Beschreibung eingeben
   - "Betrifft Urlaubsanspruch" aktivieren/deaktivieren
5. Im Urlaubsplaner prüfen
6. ✅ **Erwartet:** 
   - Betroffene Zellen sind grau mit 🚫 Icon
   - Urlaubsanspruch wird angepasst (wenn aktiviert)

---

### ✅ 9. Krankheit-Darstellung prüfen

**Test:**
1. Prüfen ob Krankheitstage korrekt als "Krank" angezeigt werden
2. Prüfen ob sie nicht als "Schulung" angezeigt werden
3. ✅ **Erwartet:** Krankheit = 🏥 Icon, Klasse "krank" (nicht "schulung")

---

### ✅ 10. E-Mail-Funktion testen

**Test:**
1. Urlaub genehmigen (siehe Punkt 1)
2. Prüfen ob E-Mail an HR gesendet wurde
3. Prüfen ob E-Mail an Mitarbeiter gesendet wurde
4. Logs prüfen:
   ```bash
   journalctl -u greiner-portal -f | grep -i "email\|mail"
   ```
5. ✅ **Erwartet:** 
   - E-Mail an HR: `hr@auto-greiner.de`
   - E-Mail an Mitarbeiter: Mitarbeiter-E-Mail-Adresse
   - Log zeigt "✅ HR-E-Mail gesendet"

---

## 🐛 BEKANNTE PROBLEME (falls auftreten)

### Problem: Genehmigung funktioniert nicht
**Lösung:** 
- Prüfen ob User Admin oder Genehmiger ist
- Browser-Console prüfen (F12) auf Fehler
- Backend-Logs prüfen: `journalctl -u greiner-portal -f`

### Problem: Resturlaub zeigt falsche Werte
**Lösung:**
- View neu erstellen: `scripts/migrations/fix_vacation_balance_views_all_years_tag198.sql`
- Prüfen ob nur `vacation_type_id = 1` (Urlaub) gezählt wird

### Problem: Buchungen werden bei falschem Mitarbeiter angezeigt
**Lösung:**
- Browser-Cache leeren (Strg+F5)
- Prüfen ob `employee_id` korrekt ist in Browser-Console

---

## 📋 SCHNELLTEST (5 Minuten)

1. ✅ Als Admin einloggen
2. ✅ Urlaub genehmigen (sollte funktionieren)
3. ✅ Resturlaub prüfen (sollte korrekt sein)
4. ✅ Jahresend-Report exportieren (sollte korrekt sein)
5. ✅ Urlaubssperre erstellen (sollte roten Rand zeigen)

---

## ✅ ERFOLGSKRITERIEN

- ✅ Genehmigung funktioniert für Admins und Genehmiger
- ✅ Resturlaub wird korrekt berechnet
- ✅ Buchungen werden nur bei korrektem Mitarbeiter angezeigt
- ✅ Jahreswechsel funktioniert (27 Tage Standard)
- ✅ Urlaubssperren werden angezeigt (roter Rand)
- ✅ Masseneingaben funktionieren
- ✅ Jahresend-Report ist korrekt (CSV nicht verschoben)
- ✅ Freie Tage werden angezeigt (grau mit 🚫)
- ✅ Krankheit wird korrekt angezeigt (nicht als Schulung)

---

**Status:** ✅ **Bereit zum Testen**
