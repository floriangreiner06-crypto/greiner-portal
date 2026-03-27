# Testanleitung für Vanessa: Urlaubsplaner & Mitarbeiterverwaltung

**Zielgruppe:** Vanessa (HR)  
**Stand:** Februar 2026 (aktualisiert inkl. Resturlaub-Anzeige, Report Export, Urlaubssperren, Rollen)  
**Ziel:** Alle relevanten Funktionen prüfen – Mitarbeiterverwaltung, Urlaubsplaner, Reporte, Urlaubssperren, Buchungsrollen.

---

## 1. Voraussetzungen

- **Login:** Als **Admin** (oder mit Rechten für Admin → Mitarbeiterverwaltung).
- **Urlaubsanspruch / Reporte / Urlaubssperren:** Nutzer mit **Urlaub-Admin** oder **Portal-Admin**.
- **Schulung/Krankheit testen:** Optional als **Genehmiger** einloggen (ohne Admin).
- **Browser:** Chrome, Edge oder Firefox; nach Änderungen **Strg+F5** (hart neu laden).
- **Portal-URL:** z. B. `http://drive` oder `https://drive.auto-greiner.de`

---

## 2. Mitarbeiterverwaltung

### 2.1 Einstieg

1. **Admin** → **Mitarbeiterverwaltung** öffnen.
2. Links: Mitarbeiterliste, rechts nach Klick auf einen MA: Tabs **Deckblatt**, **Adressdaten**, **Mitarbeiterdaten**, **Moduldaten** und **Speichern**.

### 2.2 Urlaubsanspruch

1. Tab **Moduldaten** → **Urlaubsplaner**, **Jahr** wählen.
2. **Urlaubsanspruch (Tage):** z. B. **5,5 | 11 | 16 | 22 | 27 | 30** (+ „Andere …“).
3. **„Urlaubsanspruch speichern“** klicken → Meldung „Urlaubsanspruch gespeichert.“.

### 2.3 Reporte (Urlaubs-Report mit Monaten + Export)

1. Button **„Reporte“** (oben rechts) klicken → Modal **„Urlaubs-Report“**.
2. **Jahr** wählen, **Laden** klicken.
3. **Erwartung:** Tabelle mit **Name, Abteilung, Anspruch, Übertrag, Gesamt, Genommen, Rest** und **Monatsspalten (Jan–Dez)** (Jahresrückstellung wie Altsystem).
4. **„Als CSV exportieren“** klicken → Datei wird heruntergeladen (z. B. `Jahresrueckstellung_Urlaub_2026.csv`), in Excel öffnen und prüfen.

### 2.4 Urlaubseinstellungen

1. Moduldaten → Urlaubsplaner: **„Im Urlaubsplaner anzeigen“**, Max. Übertrag usw. anpassen → **Speichern**.

---

## 3. Urlaubsplaner (Kalender)

### 3.1 Resturlaub-Anzeige (wichtig nach Usertest)

1. **Urlaubsplaner** öffnen, Jahr wählen.
2. **Resturlaub** erscheint: oben links („Rest“), in der Sidebar und **in Klammern neben jedem Namen** in der Tabelle.
3. **Test:** Einen Urlaubstag **beantragen** (gelb) oder **buchen**.
4. **Erwartung:** Die Zahl **Rest** und die Klammerzahl neben dem Namen **aktualisieren sich sofort** (z. B. 28 → 27), **ohne** Seite neu zu laden. Bei anderen MA ebenfalls: Nach Genehmigung/Storno/Ablehnung aktualisieren sich die angezeigten Resttage.

### 3.2 Monatspfeile, „Meine Anträge“

- **Pfeile** ‹ › neben Monat/Jahr: Ein Klick = vorheriger/nächster Monat.
- **„Meine Anträge“** rechts: standardmäßig **eingeklappt**, per Klick auf- und zuklappbar.

### 3.3 Masseneingabe

1. Button **Masseneingabe** → **Ziel:** **„Spezifische Mitarbeiter“** (oder Abteilung / Alle).
2. **Buchungsart:** z. B. Urlaub, Schulung, Krank, **oder 🚫 Urlaubssperre**.
3. Datum(e) wählen, ggf. Mitarbeiter auswählen → **Erstellen**.

### 3.4 Urlaubssperre für spezifische Mitarbeiter

1. Masseneingabe → **Ziel: „Spezifische Mitarbeiter“**, **Buchungsart: 🚫 Urlaubssperre**.
2. **Abteilung** muss **nicht** ausgefüllt werden (nur bei Ziel „Abteilung“).
3. Mindestens ein **Datum** und mindestens einen **Mitarbeiter** auswählen → **Erstellen**.
4. **Erwartung:** Keine Meldung „Bitte Abteilung wählen“. Erfolg: „X Urlaubssperre(n) erstellt!“. Im Kalender haben **nur die ausgewählten** MA an dem Tag den roten Sperren-Strich.

### 3.5 Urlaubssperren löschen (Admin)

1. **Urlaubsplaner Admin** (oder Admin-Button → Administration) → Bereich **„Urlaubssperren“**.
2. Jahr wählen → Tabelle mit Datum, Abteilung, Grund, **Löschen**-Button.
3. **Löschen** klicken → Bestätigung → **Erwartung:** Meldung „Sperre gelöscht“, Zeile verschwindet.

**Falls „Keine Berechtigung“:** Mit Portal-Admin oder GRP_Urlaub_Admin testen.

### 3.6 Schulung & Krankheit nur Genehmiger/Admin

- Als **Genehmiger** oder **Admin:** Buchungsart **📚 Schulung** oder **🤒 Krank** (einzeln oder Masseneingabe) → **sollte funktionieren**.
- Als **normaler Mitarbeiter** (ohne Genehmiger/Admin): Schulung oder Krank buchen → **Erwartung:** Meldung „Schulung und Krankheit können nur von Genehmiger oder Admin eingetragen werden.“

**Hinweis:** Zeitausgleich (ZA) bleibt nur für **Admins** buchbar.

### 3.7 Serielle Genehmigung / Ablehnung

- Mehrere **beantragte (gelbe)** Tage einer Person auswählen → Modal mit **Genehmigen**, **Ablehnen**, **Löschen** → Aktion ausführen; Kalender und Resturlaub aktualisieren sich.

### 3.8 Farben

- Urlaub: Grün | Beantragt: Gelb | Schulung: Blau | Krank: Rosa | ZA: blau.

---

## 4. Verbindung Mitarbeiterverwaltung ↔ Urlaubsplaner

1. In **Mitarbeiterverwaltung** bei einem MA **Urlaubsanspruch** (z. B. 11 Tage) setzen und speichern.
2. Im **Urlaubsplaner** (gleiches Jahr): **Resturlaub** neben diesem MA ≤ 11.
3. **„Im Urlaubsplaner anzeigen“** abwählen → Speichern → im Planer erscheint der MA **nicht**. Wieder ankreuzen → nach Reload **wieder sichtbar**.

---

## 5. Kurz-Checkliste

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 1 | MV: Urlaubsanspruch setzen und speichern | |
| 2 | **Reporte:** Tabelle mit Monaten (Jan–Dez), **Als CSV exportieren** funktioniert | |
| 3 | Urlaubsplaner: **Resturlaub** aktualisiert sich nach Buchung/Genehmigung sofort (ohne F5) | |
| 4 | Masseneingabe: **Spezifische Mitarbeiter** + **Urlaubssperre** ohne Abteilung möglich | |
| 5 | Urlaubssperre **löschen** (Admin-Seite) funktioniert | |
| 6 | Schulung/Krankheit nur als Genehmiger/Admin buchbar; normaler MA erhält Fehlermeldung | |
| 7 | Urlaubsanspruch aus MV erscheint im Planer; „Im Urlaubsplaner anzeigen“ schaltet Sichtbarkeit | |

---

## 6. Bei Fehlern

- **Strg+F5** (hart neu laden) probieren.
- **Browser-Konsole (F12 → Konsole)** prüfen; Screenshot oder Fehlertext an IT (Florian) senden.
- Checklisten-Nr. und kurze Beschreibung angeben.

---

**Stand:** Februar 2026.  
**Sync:** Diese Datei liegt im Windows-Sync unter  
`docs\workstreams\urlaubsplaner\TESTANLEITUNG_VANESSA.md`.
