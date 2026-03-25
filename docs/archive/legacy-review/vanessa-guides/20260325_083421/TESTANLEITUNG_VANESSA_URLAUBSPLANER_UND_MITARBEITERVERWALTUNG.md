# Testanleitung für Vanessa: Urlaubsplaner & Mitarbeiterverwaltung

**Zielgruppe:** Vanessa (HR)  
**Stand:** Februar 2026 (inkl. Usertest „Urlaubsplaner neu“)  
**Ziel:** Funktionen prüfen und die **Verbindung zwischen Mitarbeiterverwaltung und Urlaubsplaner** testen.

---

## 1. Voraussetzungen

- **Login:** Als **Admin** (oder mit Rechten für Admin → Mitarbeiterverwaltung).
- **Urlaubsanspruch speichern / Reporte / Urlaubsplaner-Admin:** Nutzer mit **Vacation-Admin**-Recht können Urlaubsanspruch speichern, Reporte nutzen und Urlaubssperren verwalten. Ohne Recht erscheinen ggf. Fehlermeldungen → an IT melden.
- **Browser:** Chrome, Edge oder Firefox; nach Änderungen **Strg+F5** (hart neu laden).
- **Portal-URL:** z. B. `http://drive` oder `https://drive.auto-greiner.de`

---

## 2. Übersicht: Was wird getestet?

| Bereich | Inhalt |
|--------|--------|
| **Mitarbeiterverwaltung** | Deckblatt, Adressdaten, Vertrag, Arbeitszeitmodell, Moduldaten (Urlaubsanspruch, Urlaubseinstellungen), **Reporte** (Urlaubsübersicht) |
| **Urlaubsplaner** | Kalender, Resturlaub-Anzeige, Monatspfeile, „Meine Anträge“ einklappbar, Masseneingabe (spezifische Mitarbeiter), Urlaubssperren, serielle Genehmigung/Ablehnung |
| **Verbindung** | Urlaubsanspruch und „Im Urlaubsplaner anzeigen“ aus der Mitarbeiterverwaltung müssen im Urlaubsplaner korrekt ankommen. |

---

## 3. Mitarbeiterverwaltung

### 3.1 Einstieg

1. **Admin** → **Mitarbeiterverwaltung** öffnen.
2. Links: Mitarbeiterliste (nach Abteilung), rechts: „Kein Datensatz gewählt!“.
3. Einen Mitarbeiter anklicken → Tabs **Deckblatt**, **Adressdaten**, **Mitarbeiterdaten**, **Moduldaten** und grüner Button **Speichern** sichtbar.

### 3.2 Urlaubsanspruch

1. Tab **Moduldaten** → **Urlaubsplaner**.
2. **Jahr** wählen (z. B. aktuelles Jahr).
3. **Urlaubsanspruch (Tage):** Dropdown nutzen – Werte wie im Personalplaner: **5,5 | 11 | 16 | 22 | 27 (Vollzeit) | 30** Tage (+ „Andere …“).
4. **„Urlaubsanspruch speichern“** klicken.
5. **Erwartung:** Meldung „Urlaubsanspruch gespeichert.“, Wert bleibt nach Reload sichtbar.

### 3.3 Reporte (Urlaubsübersicht)

1. Einen Mitarbeiter auswählen (damit die Kopfzeile sichtbar ist).
2. Button **„Reporte“** (oben rechts) klicken.
3. **Erwartung:** Modal **„Urlaubs-Report“** öffnet sich.
4. **Jahr** wählen und **Laden** klicken.
5. **Erwartung:** Tabelle mit allen Mitarbeitern und Spalten **Name**, **Abteilung**, **Anspruch**, **Genommen**, **Offen (Rest)**.
6. **Erwartung:** Daten wirken plausibel (z. B. Offen ≤ Anspruch).

**Hinweis:** Wichtig für Jahresabschluss / Rückstellung im August.

### 3.4 Urlaubseinstellungen & „Im Urlaubsplaner anzeigen“

1. Moduldaten → Urlaubsplaner: Einstellungen anpassen (z. B. „Im Urlaubsplaner anzeigen“, Max. Übertrag).
2. **Speichern** (unten rechts) klicken.
3. **Erwartung:** „Änderungen gespeichert!“, Werte bleiben erhalten.

---

## 4. Urlaubsplaner

### 4.1 Einstieg und Resturlaub

1. **Team Greiner** → **Urlaubsplaner** (oder Link „Im Urlaubsplaner anzeigen“ in der Mitarbeiterverwaltung).
2. **Jahr** und ggf. **Abteilung** wählen.
3. **Erwartung:** Mitarbeiterliste mit Zahl in Klammern (Resturlaub), Kalender mit Buchungen.
4. **Rest-Anzeige oben links:** Die Zahl **„Rest“** oben links und **„X Tage“** rechts müssen **dieselbe** Zahl zeigen wie die Klammerzahl neben Ihrem Namen in der Liste (z. B. überall 11).

### 4.2 Monatsauswahl mit Pfeilen

1. Neben den Dropdowns **Monat** und **Jahr** die Pfeile **‹** und **›** nutzen.
2. **Erwartung:** Ein Klick springt zum **vorherigen** bzw. **nächsten** Monat; Kalender aktualisiert sich.

### 4.3 „Meine Anträge“ (rechte Seite)

1. Rechts: Bereich **„Meine Anträge“**.
2. **Erwartung:** Bereich ist **standardmäßig eingeklappt** (nur Überschrift mit Pfeil nach rechts sichtbar).
3. Auf **„Meine Anträge“** klicken → Liste klappt auf (Pfeil nach unten).
4. Erneut klicken → Liste klappt wieder zu.

### 4.4 Masseneingabe (spezifische Mitarbeiter)

1. Als **Admin** im Urlaubsplaner: Button **„Masseneingabe“** (rechts oben) klicken.
2. **Erwartung:** Modal **Masseneingabe** öffnet sich.
3. **Ziel:** Sollte auf **„Spezifische Mitarbeiter“** stehen (oder Sie wählen es).
4. **Erwartung:** Darunter erscheint eine **mehrfach auswählbare Liste** aller Mitarbeiter (Strg/Cmd + Klick für mehrere).
5. Datum(e) und Buchungsart wählen, **Erstellen** klicken.
6. **Erwartung:** Buchungen werden nur für die ausgewählten Mitarbeiter angelegt.

### 4.5 Serielle Genehmigung / Ablehnung (mehrere Tage)

1. Als **Genehmiger/Admin** im Kalender **mehrere beantragte (gelbe) Tage** einer Person auswählen (Klick/Drag).
2. **Erwartung:** Ein **Modal** erscheint mit Aktionen.
3. **Erwartung:** Buttons **„Genehmigen“**, **„Ablehnen“** und **„Löschen“** sichtbar (bei offenen Anträgen).
4. **Genehmigen** oder **Ablehnen** wählen (bei Ablehnung optional Grund eintragen).
5. **Erwartung:** Alle ausgewählten offenen Anträge werden genehmigt bzw. abgelehnt; Kalender aktualisiert sich.

### 4.6 Urlaubssperren (Admin)

1. **Admin**-Button im Urlaubsplaner klicken → **Urlaubsplaner - Administration** öffnen.
2. Oben: Bereich **„Urlaubssperren“** mit Tabelle (Datum, Abteilung, Grund, Aktion).
3. **Erwartung:** Für das gewählte Jahr werden bestehende Sperren angezeigt.
4. Bei einer Test-Sperre: **„Löschen“** klicken und Bestätigung bestätigen.
5. **Erwartung:** Sperre verschwindet aus der Tabelle; **Aktualisieren** lädt die Liste neu.

**Hinweis:** Sperren können auch über **Masseneingabe** (Buchungsart „Urlaubssperre“) angelegt werden. Urlaub an gesperrten Tagen ist auch für Admins nicht buchbar (kein Umgehen über Masseneingabe).

### 4.7 Farben im Kalender

- **Urlaub:** Grün  
- **Beantragt:** Gelb  
- **Schulung:** Blau  
- **Krank:** Rosa/Pink  
- **ZA:** Blau (andere Nuance)  

**Erwartung:** Schulung und Krankheit sind gut unterscheidbar.

---

## 5. Verbindung Mitarbeiterverwaltung ↔ Urlaubsplaner

### 5.1 Urlaubsanspruch

1. In der **Mitarbeiterverwaltung** bei einem MA (z. B. sich selbst) für das aktuelle Jahr **11 Tage** (oder 16/27) setzen und **Urlaubsanspruch speichern**.
2. **Urlaubsplaner** öffnen, **dasselbe Jahr** wählen.
3. **Erwartung:** Neben dem MA steht eine Resturlaub-Zahl **≤ 11** (z. B. 11 oder weniger, wenn schon Urlaub gebucht).

### 5.2 „Im Urlaubsplaner anzeigen“

1. In der **Mitarbeiterverwaltung** bei einem sichtbaren MA **„Im Urlaubsplaner anzeigen“** **abwählen** → **Speichern**.
2. Im **Urlaubsplaner** (gleiches Jahr/Abteilung) prüfen: **Erwartung:** Dieser MA erscheint **nicht** in der Liste.
3. **„Im Urlaubsplaner anzeigen“** wieder **ankreuzen** → **Speichern**.
4. Urlaubsplaner neu laden (F5): **Erwartung:** MA erscheint **wieder**.

---

## 6. Checkliste zum Abhaken

### Mitarbeiterverwaltung

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 1 | Login, Admin → Mitarbeiterverwaltung erreichbar | |
| 2 | Mitarbeiter auswählen → Tabs + Speichern sichtbar | |
| 3 | Urlaubsanspruch (5,5 / 11 / 16 / 22 / 27 / 30) setzen und speichern | |
| 4 | **Reporte**-Button → Modal mit Tabelle (Name, Anspruch, Genommen, Offen) | |
| 5 | Urlaubseinstellungen + „Im Urlaubsplaner anzeigen“ speichern | |

### Urlaubsplaner

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 6 | Urlaubsplaner öffnen, Jahr wählen, Resturlaub-Zahlen sichtbar | |
| 7 | **Rest** oben links = Zahl neben eigenem Namen in der Liste | |
| 8 | **Monatspfeile** ‹ › funktionieren | |
| 9 | **Meine Anträge** ein- und ausklappbar, standardmäßig zu | |
| 10 | **Masseneingabe** → Ziel „Spezifische Mitarbeiter“, Liste mehrfach wählbar | |
| 11 | Mehrere Tage auswählen → Modal mit **Genehmigen** / **Ablehnen** / **Löschen** | |
| 12 | Admin → Urlaubssperren-Tabelle, **Löschen** einer Sperre funktioniert | |

### Verbindung

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 13 | Urlaubsanspruch in MV gesetzt → im Planer Resturlaub ≤ Anspruch | |
| 14 | „Im Urlaubsplaner anzeigen“ abwählen → MA im Planer weg; ankreuzen → wieder da | |

---

## 7. Bei Fehlern

- **Browser-Konsole (F12 → Konsole)** prüfen; Screenshot oder Fehlertext an IT senden.
- **Checklisten-Nr.** und kurze Beschreibung angeben.
- Diese Anleitung und ausgefüllte Checkliste (Foto/Scan) mitschicken.

---

**Referenz:** Detaillierte technische Beschreibungen in  
`docs/TESTANLEITUNG_MITARBEITERVERWALTUNG_UND_URLAUBSPLANER_VANESSA.md` und  
`docs/workstreams/urlaubsplaner/USERTEST_URLAUBSPLANER_NEU_VANESSA.md`.
