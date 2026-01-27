# Urlaubsplaner Testanleitung - TAG 209

**Datum:** 2026-01-26  
**Status:** Alle Fixes implementiert und Service neu gestartet

---

## 🧪 TESTANLEITUNG FÜR USER-TEST-TEAM

### Vorbereitung
1. **Browser-Cache leeren:** Strg+F5 (oder Strg+Shift+R)
2. **URL:** http://10.80.80.20:5000/urlaubsplaner
3. **Login:** Mit normalem AD-Account einloggen

---

## ✅ ZU TESTENDE PUNKTE

### 1. Masseneingabe (nur für Admins)
**Was testen:**
- Button "Masseneingabe" sollte sichtbar sein (nur für Admins)
- Button anklicken → Modal sollte sich öffnen
- Abteilung/Mitarbeiter auswählen
- Datum(e) eingeben (z.B. "2026-02-15" oder "2026-02-15 bis 2026-02-20")
- Typ auswählen (Urlaub, ZA, Krank, Schulung)
- "Erstellen" klicken → Buchungen sollten erstellt werden

**Erwartetes Ergebnis:**
- ✅ Modal öffnet sich
- ✅ Buchungen werden erstellt
- ✅ Erfolgsmeldung wird angezeigt
- ✅ Kalender aktualisiert sich automatisch

---

### 2. Genehmigung
**Was testen:**
- Als Genehmiger/Admin einloggen
- Urlaubsantrag eines Team-Mitglieds finden (in "Zu genehmigen" Box)
- "OK" Button klicken → Modal sollte sich öffnen
- "Genehmigen" Button klicken

**Erwartetes Ergebnis:**
- ✅ Modal öffnet sich mit korrekten Informationen
- ✅ Genehmigung funktioniert
- ✅ Erfolgsmeldung wird angezeigt
- ✅ Antrag verschwindet aus "Zu genehmigen" Liste
- ✅ Status ändert sich von "pending" zu "approved" im Kalender

---

### 3. Resturlaub-Anzeige
**Was testen:**
- Resturlaub in Klammern neben Mitarbeiternamen prüfen
- Beispiel: "Bianca Greindl (41)" → sollte korrekt sein (27 Tage + 14 Übertrag)
- Beispiel: "Herbert Huber (27)" → sollte korrekt sein

**Erwartetes Ergebnis:**
- ✅ Resturlaub wird korrekt angezeigt
- ✅ Nur Urlaubstage werden gezählt (nicht Krankheit, ZA, Schulung)
- ✅ Freie Tage werden vom Anspruch abgezogen (wenn `affects_vacation_entitlement = true`)

---

### 4. Jahreswechsel (2027)
**Was testen:**
- Kalender auf Januar 2027 wechseln
- Urlaubsanspruch prüfen → sollte 27 Tage sein (Standard)
- Resturlaub prüfen → sollte korrekt berechnet werden

**Erwartetes Ergebnis:**
- ✅ Januar 2027 zeigt korrekte Daten (nicht gleiche wie 2026)
- ✅ Standard-Anspruch: 27 Tage
- ✅ View für 2027 existiert und funktioniert

---

### 5. Frontend-Darstellung
**Was testen:**
- Kalender öffnen
- Urlaubstage verschiedener Mitarbeiter prüfen
- Eigene Urlaubstage prüfen
- Andere Mitarbeiter sollten gleiche Ansicht haben

**Erwartetes Ergebnis:**
- ✅ Alle sehen gleiche Buchungen
- ✅ Eigene Buchungen werden korrekt angezeigt
- ✅ Buchungen anderer Mitarbeiter werden korrekt angezeigt
- ✅ Keine Inkonsistenzen zwischen verschiedenen Benutzern

---

### 6. Halbe Tage - Farbe
**Was testen:**
- Halben Tag Schulung finden (z.B. Luca Kreulinger, 26.01.)
- Halben Tag Krankheit finden (z.B. Tobias Reitmeier, 22.01.)
- Farbe prüfen

**Erwartetes Ergebnis:**
- ✅ Halber Tag Schulung → **Lila** (nicht grün!)
- ✅ Halber Tag Krankheit → **Rosa** (nicht grün!)
- ✅ Symbol stimmt (📚 für Schulung, 🤒 für Krankheit)
- ✅ Farbe stimmt mit Typ überein

---

### 7. Freie Tage
**Was testen:**
- Freie Tage im Kalender finden (ausgegraut mit 🚫 Icon)
- Resturlaub prüfen → sollte um freie Tage reduziert sein (wenn `affects_vacation_entitlement = true`)

**Erwartetes Ergebnis:**
- ✅ Freie Tage werden ausgegraut angezeigt
- ✅ 🚫 Icon wird angezeigt
- ✅ Resturlaub berücksichtigt freie Tage korrekt

---

### 8. Falsche Tage-Markierung bei Genehmigung
**Was testen:**
- Urlaub von Edith Egner genehmigen
- Prüfen ob Tage bei Edith Egner markiert werden (nicht bei Christian Aichinger)

**Erwartetes Ergebnis:**
- ✅ Tage werden bei korrekter Person markiert
- ✅ Keine falsche Markierung bei anderen Personen

---

## 🐛 BEKANNTE PROBLEME / LIMITIERUNGEN

- **Herbert Huber:** Hat möglicherweise Buchungen in Locosoft, die nicht synchronisiert wurden
- **Bianca Greindl:** 41 Tage sind korrekt (27 Standard + 14 Übertrag aus Vorjahr)

---

## 📝 FEHLERMELDUNGEN

**Falls Probleme auftreten:**
1. Browser-Console öffnen (F12)
2. Fehlermeldungen notieren
3. Screenshot machen
4. An Entwickler weiterleiten

**Wichtige Fehlermeldungen:**
- "Keine Berechtigung" → Berechtigungen prüfen
- "Buchung nicht gefunden" → Datenbank-Sync prüfen
- "API Error" → Service-Status prüfen

---

## ✅ CHECKLISTE

- [ ] Masseneingabe funktioniert
- [ ] Genehmigung funktioniert
- [ ] Resturlaub wird korrekt angezeigt
- [ ] Jahreswechsel (2027) funktioniert
- [ ] Frontend-Darstellung konsistent
- [ ] Halbe Tage haben korrekte Farbe
- [ ] Freie Tage werden berücksichtigt
- [ ] Tage-Markierung bei Genehmigung korrekt

---

**Viel Erfolg beim Testen!** 🚀
