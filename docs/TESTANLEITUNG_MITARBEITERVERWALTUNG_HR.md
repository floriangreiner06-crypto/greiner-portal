# Testanleitung: Mitarbeiterverwaltung (Digitale Personalakte)

**Zielgruppe:** HR / Vanessa  
**Stand:** TAG 213  
**URL:** Nach Login als Admin: **Admin** → **Mitarbeiterverwaltung**  
Direkt: `https://drive.auto-greiner.de/admin/mitarbeiterverwaltung` (bzw. Ihre Portal-URL + `/admin/mitarbeiterverwaltung`)

---

## 1. Voraussetzungen

- **Zugang:** Nur Nutzer mit Admin-Rechten sehen den Menüpunkt **Admin** → **Mitarbeiterverwaltung**.
- **Browser:** Am besten Chrome, Edge oder Firefox (aktuell). Nach Änderungen ggf. **Strg+F5** (hart neu laden).

---

## 2. Übersicht: Was wird getestet?

| Bereich | Funktionen |
|--------|------------|
| **Deckblatt** | Grunddaten anzeigen/ändern, Sync (LDAP/Locosoft), **Speichern** |
| **Adressdaten** | Private und Firmen-Kontaktdaten, **Speichern** |
| **Mitarbeiterdaten → Vertrag** | Vertragsdaten, **Speichern** |
| **Mitarbeiterdaten → Arbeitszeitmodell** | Einträge hinzufügen, bearbeiten, löschen |
| **Mitarbeiterdaten → Ausnahmen** | Ausnahmen hinzufügen, löschen |
| **Moduldaten → Urlaubsplaner** | Urlaubseinstellungen, **Urlaubseinstellungen speichern** |
| **Moduldaten → Zeiten ohne Urlaub** | Zeiträume hinzufügen, löschen |

---

## 3. Testablauf

### 3.1 Einstieg und Mitarbeiter auswählen

1. **Admin** → **Mitarbeiterverwaltung** öffnen.
2. **Erwartung:** Links Liste der Mitarbeiter (nach Abteilung gruppiert), rechts Hinweis „Kein Datensatz gewählt!“.
3. In der linken Liste **einen Mitarbeiter anklicken** (z. B. sich selbst oder einen Test-Mitarbeiter).
4. **Erwartung:**
   - Rechts erscheinen Tabs: **Deckblatt**, **Adressdaten**, **Mitarbeiterdaten**, **Moduldaten**.
   - Unten rechts erscheint der grüne Button **„Speichern“**.
   - Deckblatt zeigt Firma, Abteilung, Eintritt, Geburtstag etc. (soweit vorhanden).

**Hinweis:** Suche und Auf-/Zuklappen der Abteilungen in der linken Liste prüfen (optional).

---

### 3.2 Deckblatt: Änderung speichern

1. Tab **Deckblatt** ist aktiv.
2. Ein Feld ändern (z. B. **Abteilung** oder **Firma** – am besten ein Wert, den Sie später wieder zurücksetzen können).
3. Auf den grünen Button **„Speichern“** (unten rechts) klicken.
4. **Erwartung:** Meldung „Änderungen gespeichert!“, danach werden die Daten neu geladen.
5. **Prüfung:** Seite neu laden (F5) oder anderen Mitarbeiter wählen und zurück – die geänderte Abteilung/Firma muss weiterhin angezeigt werden.

**Falls die Änderung nicht ankommt:** Sicherstellen, dass beim Speichern der Tab **Deckblatt** aktiv war (nicht z. B. Adressdaten).

---

### 3.3 Sync (LDAP / Locosoft)

1. Weiterhin einen Mitarbeiter mit **LDAP-Zuordnung** und ggf. **Locosoft-ID** auswählen (z. B. Testperson).
2. Auf **„Sync-Vorschau“** klicken.
3. **Erwartung:** Ein Fenster (Modal) öffnet sich mit:
   - **LDAP:** angezeigte Änderungen (z. B. Firma, Abteilung, E-Mail) oder „Keine Änderungen“.
   - **Locosoft:** angezeigte Änderungen (z. B. Adresse, Kundennummer) oder „Keine Änderungen“.
4. Modal schließen.
5. Optional: **„LDAP“** oder **„Locosoft“** oder **„Vollständig“** klicken und Bestätigung bestätigen.
6. **Erwartung:** Erfolgsmeldung, danach werden die Mitarbeiterdaten neu geladen; geänderte Felder (z. B. E-Mail, Adresse) sind aktualisiert.

---

### 3.4 Adressdaten speichern

1. Tab **Adressdaten** öffnen.
2. Ein paar Felder ausfüllen oder ändern (z. B. Straße, PLZ, Ort, Telefon privat/Firma).
3. **„Speichern“** (unten rechts) klicken.
4. **Erwartung:** „Änderungen gespeichert!“, Daten werden neu geladen.
5. **Prüfung:** Nach Reload oder erneutem Auswählen des Mitarbeiters sind die Adressdaten noch vorhanden.

---

### 3.5 Vertrag (Mitarbeiterdaten) speichern

1. Tab **Mitarbeiterdaten** → Unter-Tab **Vertrag**.
2. Felder anpassen (z. B. „Eingest. als“, „Tätigkeit“, Kündigungsfristen, Eintritt/Austritt).
3. **„Speichern“** klicken.
4. **Erwartung:** „Änderungen gespeichert!“, Vertragsdaten bleiben nach Reload/Auswahl erhalten.

---

### 3.6 Arbeitszeitmodell: Hinzufügen, Bearbeiten, Löschen

1. Tab **Mitarbeiterdaten** → **Vertrag** – nach unten scrollen bis **„Arbeitszeitmodell“**.
2. **Hinzufügen:**
   - Auf **„Neuen Datensatz hinzufügen“** klicken.
   - Modal: **Startdatum** (Pflicht), **Stunden/Woche** (Pflicht), optional Enddatum, Arbeitstage/Woche, Beschreibung (z. B. „Teilzeit 80 %“).
   - **„Speichern“** im Modal.
   - **Erwartung:** Modal schließt sich, Tabelle zeigt den neuen Eintrag.
3. **Bearbeiten:**
   - Beim neuen Eintrag auf das **Stift-Symbol** klicken.
   - Modal mit vorausgefüllten Daten: z. B. Stunden oder Beschreibung ändern → **„Speichern“**.
   - **Erwartung:** Tabelle zeigt die aktualisierten Werte.
4. **Löschen:**
   - Beim Eintrag auf das **Papierkorb-Symbol** klicken.
   - Bestätigung **„Dieses Arbeitszeitmodell wirklich löschen?“** mit OK.
   - **Erwartung:** Zeile verschwindet.

---

### 3.7 Ausnahmen: Hinzufügen und Löschen

1. Tab **Mitarbeiterdaten** → **Vertrag** – Bereich **„Ausnahmen der Arbeitszeitmodelle“**.
2. **Hinzufügen:**
   - **„Neue Ausnahme hinzufügen“** klicken.
   - Modal: **Von-** und **Bis-Datum**, **Typ** (z. B. Sonderurlaub, Elternzeit), optional Bemerkung, optional „Beeinflusst Urlaubsanspruch“.
   - **„Speichern“** im Modal.
   - **Erwartung:** Neue Zeile in der Ausnahmen-Tabelle.
3. **Löschen:**
   - Bei einer Ausnahme Papierkorb-Symbol → Bestätigung → **Erwartung:** Zeile wird entfernt.

---

### 3.8 Urlaubseinstellungen (Moduldaten)

1. Tab **Moduldaten** → **Urlaubsplaner**.
2. Einstellungen anpassen (z. B. „Im Urlaubsplaner anzeigen“, „Max. Übertrag“, „Max. Urlaubslänge“, „Eintragen von/bis“).
3. Auf den grünen Button **„Speichern“** (unten rechts) klicken – derselbe Button speichert Stammdaten und Urlaubseinstellungen.
4. **Erwartung:** Meldung „Änderungen gespeichert!“, Daten werden neu geladen.
5. **Prüfung:** Tab erneut öffnen – Werte sind weiterhin gesetzt.

---

### 3.9 Zeiten ohne Urlaubsanspruch: Hinzufügen und Löschen

1. Tab **Moduldaten** → **Urlaubsplaner** – nach unten zu **„Zeiten ohne Urlaubsanspruch“**.
2. **Hinzufügen:**
   - **„Neuen Zeitraum hinzufügen“** klicken.
   - Modal: **Von-** und **Bis-Datum**, **Typ** (z. B. Elternzeit, Unbezahlt), optional Bezeichnung → **„Speichern“**.
   - **Erwartung:** Neuer Eintrag in der Tabelle.
3. **Löschen:**
   - Papierkorb bei einem Eintrag → Bestätigung → **Erwartung:** Eintrag wird gelöscht.

---

## 4. Kurz-Checkliste für Vanessa

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 1 | Login als Admin, Menüpunkt „Mitarbeiterverwaltung“ sichtbar | |
| 2 | Mitarbeiter auswählen → Tabs + Speichern-Button sichtbar | |
| 3 | Deckblatt ändern → Speichern → Wert bleibt nach Reload | |
| 4 | Sync-Vorschau öffnet sich, LDAP/Locosoft angezeigt | |
| 5 | Adressdaten ändern → Speichern → Werte bleiben | |
| 6 | Vertragsdaten ändern → Speichern → Werte bleiben | |
| 7 | Arbeitszeitmodell: Add → Edit → Delete funktioniert | |
| 8 | Ausnahme: Add + Delete funktioniert | |
| 9 | Urlaubseinstellungen speichern → Werte bleiben | |
| 10 | Zeit ohne Urlaub: Add + Delete funktioniert | |

---

## 5. Bekannte Hinweise

- **Speichern-Button:** Er erscheint unten rechts, sobald ein Mitarbeiter ausgewählt ist (nicht erst nach einer Änderung).
- **Deckblatt vs. Vertrag:** Firma/Abteilung/Eintritt werden aus dem **gerade aktiven Tab** übernommen. Wer nur im Deckblatt etwas ändert, sollte vor dem Speichern **Deckblatt** ausgewählt lassen.
- **Urlaubseinstellungen:** Der Button **„Speichern“** (unten rechts) speichert sowohl Stammdaten (Deckblatt, Adresse, Vertrag) als auch die Urlaubseinstellungen aus dem Tab Moduldaten in einem Schritt.
- Bei Fehlermeldungen oder unerwartetem Verhalten: **Browser-Konsole (F12 → Konsole)** prüfen und Screenshot/Text der Meldung an IT/Entwicklung senden.

---

**Fragen/Probleme:** An Entwicklung/IT wenden (z. B. mit Link zu dieser Anleitung und ausgefüllter Checkliste).
/sess