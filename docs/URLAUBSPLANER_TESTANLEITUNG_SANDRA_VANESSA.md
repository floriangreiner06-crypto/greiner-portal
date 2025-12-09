# 🧪 URLAUBSPLANER TESTANLEITUNG

**Tester:** Sandra Brendel, Vanessa Groll  
**Testmonat:** Dezember 2025  
**Datum:** 09.12.2025  
**Version:** V19 TAG 107

---

## 📋 TEIL 1: OUTLOOK KALENDER EINRICHTEN

### Schritt-für-Schritt Anleitung (Outlook Desktop)

**1. Outlook öffnen**
- Outlook Desktop starten
- Zum Kalender wechseln (unten links auf Kalender-Symbol klicken)

**2. Freigegebenen Kalender hinzufügen**
- Im Menüband: **Start** → **Kalender öffnen** → **Aus Adressbuch...**
- ODER: Rechtsklick auf "Meine Kalender" → **Kalender hinzufügen** → **Aus Adressbuch**

**3. DRIVE-Kalender suchen**
- Im Suchfeld eingeben: `drive`
- Es erscheint: **Autohaus Greiner - DRIVE** (oder `drive@auto-greiner.de`)
- Doppelklick auf den Eintrag
- **OK** klicken

**4. Kalender erscheint**
- Links unter "Freigegebene Kalender" erscheint nun "Autohaus Greiner - DRIVE"
- ✅ Haken setzen um Kalender anzuzeigen
- Urlaubseinträge erscheinen im Format: `🏖️ [Verkauf] Max Mustermann`

---

## 📋 TEIL 2: DRIVE PORTAL AUFRUFEN

### Schritt 1: Anmelden
1. Browser öffnen (Chrome empfohlen)
2. URL eingeben: **https://drive.auto-greiner.de/urlaubsplaner/v2**
3. Mit Windows-Anmeldedaten einloggen (falls nicht automatisch)

### Schritt 2: Oberfläche prüfen
Nach dem Laden sollte erscheinen:
- Oben: **Urlaubsplaner** Header mit Statistik (Anspruch, Urlaub, ZA, Krank, Rest)
- Mitte: **Dezember 2025** Kalender mit allen Mitarbeitern
- Rechts: **"Meine Anträge"** Sidebar
- Eigene Zeile ist **blau hinterlegt**

---

## 🧪 TEIL 3: TESTFÄLLE FÜR SANDRA BRENDEL

> **Wichtig:** Nach jedem Test bitte Ergebnis dokumentieren!

---

### TEST 1: Urlaub beantragen (1 Tag)

**Aktion:**
1. Im Kalender auf die Zeile **Sandra Brendel** scrollen
2. Auf **Montag 16.12.** klicken (ein einzelner Tag)
3. Grünes Popup erscheint: "📅 16.12. buchen"
4. **🏖️ Urlaub** ist bereits ausgewählt
5. Auf **"✓ Einreichen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast-Meldung: "1 Tag(e) beantragt!"
- ✅ Tag 16.12. wird **gelb** (pending/beantragt)
- ✅ In "Meine Anträge" erscheint: 🏖️ 16.12. ⏳
- ✅ E-Mail an **Genehmiger** (wer ist das für Sandra?)

**Prüfen:**
- [ ] Tag ist gelb
- [ ] Eintrag in Sidebar
- [ ] E-Mail erhalten (Genehmiger prüft)

---

### TEST 2: Urlaub beantragen (mehrere Tage per Drag)

**Aktion:**
1. Auf **Dienstag 17.12.** klicken und **gedrückt halten**
2. Mit Maus bis **Freitag 19.12.** ziehen (Drag-Selection)
3. Maus loslassen
4. Grünes Popup erscheint: "📅 17.12. - 19.12. (3 Tage)"
5. **🏖️ Urlaub** lassen
6. **"✓ Einreichen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "3 Tag(e) beantragt!"
- ✅ Tage 17., 18., 19.12. werden **gelb**
- ✅ 3 neue Einträge in "Meine Anträge"
- ✅ Wochenende (Sa/So) wird **automatisch übersprungen**

**Prüfen:**
- [ ] 3 gelbe Tage
- [ ] Wochenende nicht gebucht
- [ ] E-Mails an Genehmiger

---

### TEST 3: Zeitausgleich (ZA) beantragen

**Aktion:**
1. Auf **Montag 22.12.** klicken
2. Grünes Popup erscheint
3. Auf **⏰ Zeitausgleich** klicken (wird markiert)
4. **"✓ Einreichen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "1 Tag(e) beantragt!"
- ✅ Tag 22.12. wird **gelb** mit ⏰ Symbol
- ✅ In "Meine Anträge": ⏰ 22.12. ⏳

**Prüfen:**
- [ ] Gelb mit ⏰
- [ ] E-Mail an Genehmiger

---

### TEST 4: Krankheitstag eintragen

**Aktion:**
1. Auf **Dienstag 23.12.** klicken
2. Grünes Popup erscheint
3. Auf **🤒 Krank** klicken
4. **"✓ Einreichen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "1 Tag(e) beantragt!" (oder "Krankheitstag eingetragen")
- ✅ Tag 23.12. wird **SOFORT PINK** (nicht gelb!) = approved
- ✅ In "Meine Anträge": 🤒 23.12. ✓ (grüner Haken, nicht ⏳)
- ✅ **KEINE Genehmigung nötig** - direkt approved
- ✅ E-Mail an: **HR + Teamleitung + Florian Greiner**

**Prüfen:**
- [ ] Tag ist PINK (nicht gelb)
- [ ] Grüner Haken ✓ (nicht ⏳)
- [ ] E-Mail an HR erhalten
- [ ] E-Mail an Florian erhalten

---

### TEST 5: Buchung ändern (Typ wechseln)

**Aktion:**
1. Auf einen **bereits gebuchten gelben Tag** klicken (z.B. 16.12.)
2. **Lila Popup** erscheint mit Optionen
3. Auf **"⏰ Ändern zu ZA"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "Geändert zu Zeitausgleich!"
- ✅ Symbol im Kalender wechselt zu ⏰
- ✅ In "Meine Anträge" zeigt ⏰ statt 🏖️

**Prüfen:**
- [ ] Symbol geändert
- [ ] Typ in Sidebar geändert

---

### TEST 6: Buchung löschen

**Aktion:**
1. Auf einen **gebuchten Tag** klicken (z.B. 16.12.)
2. Lila Popup erscheint
3. Auf **"🗑️ Löschen"** klicken
4. Bestätigungsbereich erscheint: "🗑️ 16.12. wirklich löschen?"
5. Auf **"Löschen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "Gelöscht!"
- ✅ Tag wird wieder **leer/weiß**
- ✅ Eintrag verschwindet aus "Meine Anträge"
- ✅ Wenn vorher genehmigt: E-Mail an Genehmiger + HR

**Prüfen:**
- [ ] Tag wieder leer
- [ ] Aus Sidebar entfernt

---

### TEST 7: Aus Sidebar stornieren

**Aktion:**
1. In "Meine Anträge" auf den **roten Mülleimer-Button** klicken
2. Modal erscheint: "XX.12. wirklich stornieren?"
3. Auf **"Ja"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "Storniert!"
- ✅ Wie TEST 6

---

## 🧪 TEIL 4: GENEHMIGUNG TESTEN (Vanessa als Genehmiger)

> **Hinweis:** Vanessa muss als Genehmiger für Sandra konfiguriert sein!

---

### TEST 8: Antrag genehmigen

**Aktion (Vanessa):**
1. DRIVE Portal öffnen
2. Rechts erscheint **orange Box: "Zu genehmigen (X)"**
3. Bei "Sandra Brendel - 17.12." auf **grünen "OK" Button** klicken
4. Modal erscheint: "Sandra Brendel - 17.12. genehmigen?"
5. Auf **"Genehmigen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "Genehmigt!"
- ✅ Antrag verschwindet aus "Zu genehmigen" Liste
- ✅ Bei Sandra: Tag wechselt von **gelb → grün** (approved)
- ✅ **E-Mail an HR** mit Aufforderung: "Bitte in Locosoft eintragen"
- ✅ **E-Mail an Sandra** mit Bestätigung
- ✅ **Kalendereintrag** in DRIVE-Kalender: "🏖️ [Service] Sandra Brendel"

**Prüfen:**
- [ ] Tag bei Sandra ist GRÜN
- [ ] E-Mail an HR
- [ ] E-Mail an Sandra
- [ ] Eintrag im Outlook DRIVE-Kalender sichtbar

---

### TEST 9: Antrag ablehnen

**Aktion (Vanessa):**
1. Bei "Sandra Brendel - 18.12." auf **roten "X" Button** klicken
2. Modal erscheint mit Textfeld
3. **Optional:** Grund eingeben (z.B. "Zu viele Kollegen fehlen")
4. Auf **"Ablehnen"** klicken

**Erwartetes Ergebnis:**
- ✅ Toast: "Abgelehnt"
- ✅ Antrag verschwindet aus Liste
- ✅ Bei Sandra: Tag verschwindet (wird gelöscht/rejected)
- ✅ **E-Mail an Sandra** mit Ablehnungsgrund

**Prüfen:**
- [ ] Tag bei Sandra nicht mehr sichtbar
- [ ] E-Mail an Sandra erhalten

---

## 📋 TEIL 5: LOCOSOFT PRÜFUNG

### Wichtige Information zur Synchronisation:

| Richtung | Wann? | Was passiert? |
|----------|-------|---------------|
| **Locosoft → DRIVE** | Nächtlich (ca. 23:00) | PostgreSQL-Sync lädt Abwesenheiten aus Locosoft |
| **DRIVE → Locosoft** | **MANUELL durch HR** | HR muss genehmigte Urlaube in Locosoft eintragen |

### ⚠️ WICHTIG:
- **DRIVE schreibt NICHT automatisch in Locosoft!**
- HR erhält E-Mail und muss manuell in Locosoft eintragen
- Die Anzeige "in Locosoft" im DRIVE zeigt erst am nächsten Tag den Eintrag

---

### TEST 10: Locosoft-Eintrag prüfen (am nächsten Tag)

**Aktion (HR oder Admin):**
1. In **Locosoft** die genehmigten Urlaube eintragen
2. Warten bis nächster Tag (Sync läuft nachts)
3. In DRIVE Portal prüfen

**Erwartetes Ergebnis:**
- ✅ In der oberen Statistik aktualisieren sich die Zahlen
- ✅ "Urlaub" Zähler erhöht sich
- ✅ "Rest" Zähler verringert sich

---

## 📋 TEIL 6: KALENDER-CHECK

### Im Outlook DRIVE-Kalender prüfen:

Nach Genehmigung sollte erscheinen:
- `🏖️ [Service] Sandra Brendel` am genehmigten Tag
- Ganztägiger Termin
- Kategorie entspricht Abteilung

### Bei Stornierung:
- Kalendereintrag wird automatisch gelöscht

---

## 📝 CHECKLISTE ZUM ABSCHLUSS

### Funktionen getestet:
- [ ] Einzelnen Tag buchen
- [ ] Mehrere Tage per Drag buchen
- [ ] Verschiedene Typen (Urlaub, ZA, Krank, Schulung)
- [ ] Buchung ändern
- [ ] Buchung löschen (Popup)
- [ ] Buchung stornieren (Sidebar)
- [ ] Genehmigung erteilen
- [ ] Genehmigung ablehnen
- [ ] Outlook Kalender eingerichtet
- [ ] Kalendereinträge sichtbar

### E-Mails erhalten:
- [ ] Neuer Antrag → an Genehmiger
- [ ] Genehmigung → an HR + Mitarbeiter
- [ ] Ablehnung → an Mitarbeiter
- [ ] Krankheit → an HR + Teamleitung + GL
- [ ] Stornierung → an Genehmiger (+ HR wenn approved)

---

## 🐛 FEHLER DOKUMENTIEREN

Falls etwas nicht funktioniert:

1. **Screenshot machen** (Windows: Win + Shift + S)
2. **Browser-Konsole öffnen** (F12 → Console Tab)
3. **Fehlermeldung kopieren**
4. An Florian senden mit:
   - Was wurde versucht?
   - Was ist passiert?
   - Was wurde erwartet?

---

## 📞 KONTAKT BEI PROBLEMEN

**Florian Greiner**  
florian.greiner@auto-greiner.de

---

*Erstellt: 09.12.2025 - TAG 107*
