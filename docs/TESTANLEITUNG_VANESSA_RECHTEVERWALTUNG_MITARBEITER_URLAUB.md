# Testanleitung: Rechteverwaltung – Mitarbeiter, Urlaub, Personalakte

**Zielgruppe:** Vanessa und Test-Team  
**Stand:** Februar 2026  
**Thema:** Alle Änderungen an Rechteverwaltung, Mitarbeiter-Konfig-Modal, Urlaub, Digitale Personalakte und Organigramm-Link durchspielen und prüfen.

---

## 1. Was wurde geändert? (Kurzüberblick)

- **Ein zentrales Bearbeiten-Modal:** In der Rechteverwaltung unter **Mitarbeiter-Konfig** kann man pro Mitarbeiter mit einem Klick alles Wichtige bearbeiten: Abteilung, Standort, Vertretungen **und** Urlaubsanspruch/Urlaubseinstellungen – ohne in verschiedene Tabs wechseln zu müssen.
- **Keine doppelte Navigation mehr:** Die Tabs **Urlaubsverwaltung** und **Mitarbeiterverwaltung** öffnen im gleichen Bildschirm **ohne** zweite Menüleiste (keine „Verschachtelung“).
- **Hinweise zur doppelten Pflege:** Es gibt kurze Hinweise, wo Urlaub noch bearbeitet werden kann (Personalakte ↔ Urlaubsverwaltung).
- **Link zur Personalakte:** Aus dem Modal heraus öffnet „Alle Daten in der Digitalen Personalakte bearbeiten“ die Personalakte **direkt für den gewählten Mitarbeiter**.
- **Link zum Organigramm:** „Alle Vertretungsregeln im Organigramm“ öffnet das Organigramm **auf dem Tab Vertretungen** (nicht mehr Abteilungen).

---

## 2. Voraussetzungen

- **Login:** Als **Portal-Admin** (oder Nutzer mit Zugriff auf **Admin → Rechteverwaltung**).
- **Browser:** Chrome, Edge oder Firefox; nach Änderungen ggf. **Strg+F5** (Seite hart neu laden).
- **Portal-URL:** z. B. `http://drive` (intern).

---

## 3. Test 1: Rechteverwaltung – Tab „Mitarbeiter-Konfig“

**Ziel:** Prüfen, dass die Tabelle und das erweiterte Modal wie beschrieben funktionieren.

1. **Admin** → **Rechteverwaltung** öffnen.
2. Oben den Tab **„Mitarbeiter-Konfig“** wählen.
3. **Erwartung:** Tabelle mit Spalten z. B. Name, Abteilung, Standort, Genehmiger, Vertritt, Wird vertreten, und in der letzten Spalte ein **Stift-Symbol (Bearbeiten)**.
4. Einen Mitarbeiter auswählen (z. B. **Christian Aichinger**) und auf das **Stift-Symbol** klicken.
5. **Erwartung:** Es öffnet sich ein **großes Fenster (Modal)** mit der Überschrift **„Mitarbeiter bearbeiten“** und dem Namen des Mitarbeiters.

---

## 4. Test 2: Modal – Stammdaten und Vertretungen

**Ziel:** Abteilung, Standort und Vertretungen im Modal prüfen und speichern.

1. Im geöffneten Modal prüfen:
   - **Abteilung** (Dropdown) und **Standort** (Dropdown) sind sichtbar und befüllt.
   - **Vertritt (stellt sich für)** und **Wird vertreten von** sind sichtbar; bestehende Regeln werden angezeigt, mit **+** kann man hinzufügen, mit **X** entfernen.
2. Optional: Abteilung oder Standort ändern, eine Vertretung hinzufügen oder entfernen.
3. Unten auf **„Speichern“** klicken.
4. **Erwartung:** Modal schließt sich, die Tabelle aktualisiert sich (geänderte Abteilung/Standort/Vertretungen sind sichtbar). Keine Fehlermeldung.

---

## 5. Test 3: Modal – Urlaub (Jahr, Anspruch, Übertrag, Korrektur)

**Ziel:** Urlaubsanspruch und Urlaubseinstellungen im Modal laden und speichern.

1. Erneut einen Mitarbeiter in der **Mitarbeiter-Konfig** mit dem **Stift** öffnen.
2. Im Modal nach unten scrollen bis zum Bereich **„Urlaub“** (mit Regenschirm-Symbol).
3. **Prüfen:**
   - **Urlaubsanspruch (Jahr):** Dropdown (z. B. 2025, 2026, 2027) – Jahr wählbar.
   - **Anspruch (Tage), Übertrag, Korrektur (+/-):** Felder sind sichtbar und mit Werten befüllt (sofern bereits Daten vorhanden).
   - **Max. Urlaubslänge (am Stück)** und **Berechnung Urlaubswertung** sind sichtbar.
4. Optional: Jahr wechseln → **Erwartung:** Die Felder Anspruch/Übertrag/Korrektur passen sich dem gewählten Jahr an (sofern Daten da sind).
5. Optional: **Anspruch (Tage)** oder **Übertrag** ändern und auf **„Speichern“** klicken.
6. **Erwartung:** Modal schließt sich ohne Fehler. Im **Urlaubsplaner** oder in der **Urlaubsverwaltung** (Tab in der Rechteverwaltung) sollte der geänderte Wert für den Mitarbeiter sichtbar sein.

---

## 6. Test 4: Link „Alle Daten in der Digitalen Personalakte bearbeiten“

**Ziel:** Der Link öffnet die Digitale Personalakte **für genau diesen Mitarbeiter** (nicht „Kein Datensatz gewählt“).

1. In der **Mitarbeiter-Konfig** einen Mitarbeiter mit dem **Stift** öffnen (z. B. Christian Aichinger).
2. Im Modal ganz nach unten scrollen.
3. Auf den blauen Link **„Alle Daten in der Digitalen Personalakte bearbeiten“** klicken (öffnet in neuem Tab).
4. **Erwartung:**
   - Ein neuer Tab öffnet sich mit der **Digitalen Personalakte** (Mitarbeiterverwaltung).
   - **Nicht** die Meldung „Kein Datensatz gewählt!“, sondern **der gewählte Mitarbeiter** (z. B. Christian Aichinger) ist **automatisch ausgewählt** – links in der Liste markiert, rechts die Details (Deckblatt, Adressdaten, …) sichtbar.

**Falls „Kein Datensatz gewählt“ erscheint:** Bitte melden (Browser, genauer Mitarbeiter, ob in neuem Tab oder im gleichen Fenster geöffnet).

---

## 7. Test 5: Link „Alle Vertretungsregeln im Organigramm“

**Ziel:** Der Link öffnet das Organigramm **auf dem Tab Vertretungen** (nicht Abteilungen).

1. In der **Mitarbeiter-Konfig** einen Mitarbeiter mit dem **Stift** öffnen.
2. Unter den Vertretungsfeldern auf den Link **„Alle Vertretungsregeln im Organigramm“** klicken (öffnet in neuem Tab).
3. **Erwartung:**
   - Ein neuer Tab öffnet sich mit der **Organigramm**-Seite.
   - **Nicht** der Tab „Abteilungen“, sondern der Tab **„Vertretungen“** ist aktiv (lila/hervorgehoben).
   - Die Tabelle/Liste der **Vertretungsregeln** ist sichtbar.

**Falls stattdessen „Abteilungen“ angezeigt wird:** Bitte melden.

---

## 8. Test 6: Tabs „Urlaubsverwaltung“ und „Mitarbeiterverwaltung“ (keine doppelte Nav)

**Ziel:** In der Rechteverwaltung erscheint pro Tab nur **eine** Menüleiste (keine verschachtelte Navigation).

1. **Admin** → **Rechteverwaltung** öffnen.
2. Tab **„Urlaubsverwaltung“** wählen.
3. **Erwartung:** Im Bereich unter den Tabs wird die **Urlaubsplaner-Administration** angezeigt (Jahr, Mitarbeiter, Urlaubsansprüche usw.). Es gibt **keine zweite** komplette Menüleiste („Greiner DRIVE“, Dashboard, Service, …) innerhalb dieses Bereichs – also **keine Verschachtelung**.
4. Tab **„Mitarbeiterverwaltung“** wählen.
5. **Erwartung:** Im Bereich wird die **Digitale Personalakte** (Mitarbeiterliste links, Inhalte rechts) angezeigt. Auch hier **keine zweite** Menüleiste im eingebetteten Bereich.

**Falls doch eine doppelte Menüleiste sichtbar ist:** Bitte kurz beschreiben (welcher Tab, Screenshot hilfreich).

---

## 9. Test 7: Hinweise zu Urlaub (Redundanz)

**Ziel:** Die Hinweise sind sichtbar, dass Urlaub an zwei Stellen bearbeitet werden kann.

1. **In der Digitalen Personalakte:** Einen Mitarbeiter wählen → Tab **Moduldaten** → Bereich **Urlaubseinstellungen / Urlaubsanspruch**.  
   **Erwartung:** Ein kurzer Hinweis in der Art: *„Urlaubsansprüche pro Jahr können auch in der Rechteverwaltung (Tab Urlaubsverwaltung) bearbeitet werden.“*

2. **In der Urlaubsverwaltung** (Rechteverwaltung → Tab Urlaubsverwaltung): Oben im Kopfbereich.  
   **Erwartung:** Ein kurzer Hinweis in der Art: *„Stammdaten und Urlaubseinstellungen können auch in der Digitalen Personalakte (Rechteverwaltung → Mitarbeiterverwaltung) gepflegt werden.“*

---

## 10. Checkliste für das Test-Team

| Nr | Test | Erwartung | OK / Fehler (kurz notieren) |
|----|------|-----------|-----------------------------|
| 1 | Mitarbeiter-Konfig-Tabelle + Modal öffnet | Tabelle sichtbar, Stift öffnet großes Modal | |
| 2 | Stammdaten + Vertretungen speichern | Speichern schließt Modal, Tabelle aktualisiert | |
| 3 | Urlaub im Modal (Jahr, Anspruch, Speichern) | Werte laden, Speichern ohne Fehler | |
| 4 | Link „Digitale Personalakte bearbeiten“ | Neuer Tab, Mitarbeiter ist vorausgewählt | |
| 5 | Link „Vertretungsregeln im Organigramm“ | Neuer Tab, Tab „Vertretungen“ ist aktiv | |
| 6 | Tabs Urlaubsverwaltung / Mitarbeiterverwaltung | Keine doppelte Menüleiste (keine Verschachtelung) | |
| 7 | Hinweise Urlaub (Personalakte + Urlaubsverwaltung) | Beide Hinweise sichtbar | |

---

## 11. Bei Fehlern melden

- **Was** wurde gemacht (Schritt für Schritt)?
- **Was** wurde erwartet?
- **Was** ist stattdessen passiert? (Fehlermeldung, falscher Tab, leerer Datensatz, …)
- **Browser** und ob **neu geladen** (Strg+F5) wurde.
- Optional: **Screenshot** oder kurze Beschreibung des Bildschirms.

Damit können Vanessa und das Test-Team alle Änderungen systematisch durchspielen und Rückmeldung geben.
