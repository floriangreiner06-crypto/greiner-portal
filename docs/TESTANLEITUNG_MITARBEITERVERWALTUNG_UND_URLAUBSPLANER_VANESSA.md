# Testanleitung: Mitarbeiterverwaltung & Urlaubsplaner (für Vanessa)

**Zielgruppe:** Vanessa (HR)  
**Stand:** Februar 2026 (aktualisiert nach Feedback 3.2)  
**Wichtig:** Diese Anleitung prüft auch, ob die **Verbindung zwischen Mitarbeiterverwaltung und Urlaubsplaner** stimmig und funktional ist.

---

## 1. Voraussetzungen

- **Zugang:** Als **Admin** (oder Nutzer mit Rechten für Admin → Mitarbeiterverwaltung) einloggen.
- **Urlaubsanspruch speichern:** Nur Nutzer mit **Vacation-Admin**-Recht können den Urlaubsanspruch in der Mitarbeiterverwaltung speichern. Ohne dieses Recht erscheint eine Fehlermeldung beim Klick auf „Urlaubsanspruch speichern“ – dann bitte an IT/Entwicklung melden.
- **Browser:** Chrome, Edge oder Firefox (aktuell). Nach Änderungen ggf. **Strg+F5** (hart neu laden).
- **Portal-URL:** z. B. `http://drive` oder `https://drive.auto-greiner.de`

---

## 2. Was wird getestet?

| Bereich | Inhalt |
|--------|--------|
| **Mitarbeiterverwaltung** | Deckblatt, Adressdaten, Vertrag, Arbeitszeitmodell, Ausnahmen, Moduldaten (Urlaubseinstellungen, **Urlaubsanspruch**, Zeiten ohne Urlaub), Sync |
| **Urlaubsplaner** | Anzeige der Mitarbeiter, Anspruch/Resturlaub, Buchungen, Filter (Jahr, Abteilung) |
| **Verbindung beider** | Änderungen in der Mitarbeiterverwaltung (Urlaubsanspruch, „Im Urlaubsplaner anzeigen“) müssen im Urlaubsplaner **richtig und logisch** ankommen. |

---

## 3. Testablauf

### 3.1 Einstieg: Mitarbeiterverwaltung

1. **Admin** → **Mitarbeiterverwaltung** öffnen.
2. **Erwartung:** Links Mitarbeiterliste (nach Abteilung), rechts „Kein Datensatz gewählt!“.
3. **Sich selbst** (oder einen festen Test-Mitarbeiter) in der Liste anklicken.
4. **Erwartung:** Tabs **Deckblatt**, **Adressdaten**, **Mitarbeiterdaten**, **Moduldaten** sichtbar; unten rechts grüner Button **„Speichern“**.

---

### 3.2 Urlaubsanspruch in der Mitarbeiterverwaltung

1. Tab **Moduldaten** öffnen → Unter-Tab **Urlaubsplaner**.
2. **Jahr** auswählen (z. B. aktuelles Jahr).
3. **Urlaubsanspruch (Tage):** Im Dropdown einen Wert wählen. Die Optionen entsprechen dem **Personalplaner**: **5,5 | 11 | 16 | 22 | 27 (Vollzeit) | 30** Tage. Bei **„Andere …“** die gewünschte Zahl im Zusatzfeld eintragen (z. B. 14).
4. Auf **„Urlaubsanspruch speichern“** klicken.
5. **Erwartung:** Meldung „Urlaubsanspruch gespeichert.“, Daten werden neu geladen; das Dropdown zeigt weiterhin den gespeicherten Wert.
6. **Optional:** Jahr wechseln (z. B. nächstes Jahr), anderen Anspruch wählen, erneut speichern → Werte pro Jahr getrennt.

**Hinweis:** Wenn eine Fehlermeldung erscheint (z. B. „Keine Berechtigung“), fehlt das Vacation-Admin-Recht – bitte an IT melden.

---

### 3.3 Urlaubseinstellungen speichern

1. Weiterhin Tab **Moduldaten** → **Urlaubsplaner**.
2. Einstellungen anpassen (z. B. „Im Urlaubsplaner anzeigen“, „Max. Übertrag“, „Max. Urlaubslänge“, „Eintragen von/bis“).
3. Auf den grünen Button **„Speichern“** (unten rechts) klicken.
4. **Erwartung:** „Änderungen gespeichert!“, beim erneuten Öffnen des Tabs sind die Werte unverändert.

---

### 3.4 Verbindung prüfen: Urlaubsanspruch → Urlaubsplaner

**Ziel:** Prüfen, ob der in der Mitarbeiterverwaltung gespeicherte Urlaubsanspruch im Urlaubsplaner **sichtbar und logisch** ist.

1. **Vor dem Test** in der Mitarbeiterverwaltung notieren:
   - Welcher Mitarbeiter (Name)?
   - Welches Jahr?
   - Welcher Urlaubsanspruch (Tage)? z. B. **11**, **16** oder **27**
2. **Urlaubsplaner** öffnen (Link in der Mitarbeiterverwaltung: **„Im Urlaubsplaner anzeigen“** oder Menü **Team Greiner** → **Urlaubsplaner**).
3. Im Urlaubsplaner **dasselbe Jahr** wählen (Dropdown „Jahr“).
4. Den **gleichen Mitarbeiter** in der Liste finden (links nach Abteilung, Name).
5. **Erwartung:**
   - Neben dem Namen steht eine Zahl in Klammern (z. B. **Vanessa Groll (11)** oder **(27)**). Diese Zahl ist der **Resturlaub** für dieses Jahr.
   - **Logik:** Resturlaub ≤ Urlaubsanspruch. Wenn Sie in der Mitarbeiterverwaltung **11 Tage** Anspruch gesetzt haben, darf die Zahl im Urlaubsplaner **nicht höher als 11** sein (sie kann niedriger sein, wenn bereits Urlaub gebucht ist). Wenn Sie **27 Tage** gesetzt haben, darf sie nicht höher als 27 sein.
6. **Falls die Zahl im Urlaubsplaner nicht zur Mitarbeiterverwaltung passt** (z. B. Sie haben 11 gesetzt, im Planer steht 27): Test als **nicht bestanden** vermerken und an IT/Entwicklung melden.

**Kurz:** Was in der Mitarbeiterverwaltung als Urlaubsanspruch (pro Jahr) gespeichert wird, muss im Urlaubsplaner als **Obergrenze** für die Anzeige (Resturlaub) wirken.

---

### 3.5 Verbindung prüfen: „Im Urlaubsplaner anzeigen“

**Ziel:** Prüfen, ob die Einstellung **„Im Urlaubsplaner anzeigen“** aus der Mitarbeiterverwaltung den Urlaubsplaner beeinflusst.

1. In der **Mitarbeiterverwaltung** einen Mitarbeiter wählen, der **im Urlaubsplaner sichtbar** ist (z. B. sich selbst oder einen Test-MA).
2. Tab **Moduldaten** → **Urlaubsplaner**.
3. **„Im Urlaubsplaner anzeigen“** **abwählen** (Häkchen entfernen).
4. **„Speichern“** (unten rechts) klicken.
5. **Urlaubsplaner** öffnen (neuer Tab oder gleicher Tab), **gleiches Jahr** und **gleiche Abteilung** wählen.
6. **Erwartung:** Der soeben ausgeblendete Mitarbeiter **erscheint nicht mehr** in der Mitarbeiterliste des Urlaubsplaners.
7. Zurück in die **Mitarbeiterverwaltung**, **„Im Urlaubsplaner anzeigen“** wieder **ankreuzen**, **Speichern**.
8. **Urlaubsplaner** neu laden (F5).
9. **Erwartung:** Der Mitarbeiter **erscheint wieder** in der Liste.

**Falls der Mitarbeiter trotz Abwählen weiterhin im Urlaubsplaner erscheint (oder nach Ankreuzen nicht wieder erscheint):** Test als **nicht bestanden** vermerken und an IT melden.

---

### 3.6 Weitere Tests in der Mitarbeiterverwaltung (Kurzfassung)

- **Deckblatt:** Feld ändern (z. B. Abteilung) → **Speichern** → nach Reload oder erneutem Auswählen muss der Wert noch da sein.
- **Adressdaten:** Felder anpassen → **Speichern** → Werte bleiben erhalten.
- **Vertrag:** Vertragsdaten anpassen → **Speichern** → Werte bleiben erhalten.
- **Arbeitszeitmodell:** Neuen Datensatz hinzufügen (Startdatum, Stunden/Woche) → Speichern im Modal → Zeile erscheint. Bearbeiten (Stift) → Speichern → Werte aktualisiert. Löschen (Papierkorb) → Bestätigung → Zeile weg.
- **Ausnahmen:** Neue Ausnahme hinzufügen (Von/Bis, Typ) → Speichern → Zeile erscheint. Löschen → Zeile weg.
- **Zeiten ohne Urlaub:** Neuen Zeitraum hinzufügen → Speichern → Zeile erscheint. Löschen → Zeile weg.
- **Sync:** „Sync-Vorschau“ öffnet Fenster mit LDAP/Locosoft-Änderungen; optional LDAP/Locosoft/Vollständig ausführen → Erfolgsmeldung, Daten aktualisiert.

---

### 3.7 Urlaubsplaner: Anzeige und Logik

1. **Urlaubsplaner** öffnen, **Jahr** und ggf. **Abteilung** wählen.
2. **Erwartung:** Liste der Mitarbeiter mit Zahl in Klammern (Resturlaub); Kalender mit Buchungen (Urlaub, Krank, ZA etc.); blaue Punkte bei genehmigten Buchungen.
3. **Logik:** Die Zahl neben dem Namen (Resturlaub) soll **nie höher** sein als der in der Mitarbeiterverwaltung für diesen Mitarbeiter und dieses Jahr gesetzte **Urlaubsanspruch**. Wenn jemand z. B. 11 Tage Anspruch hat und bereits Urlaub gebucht ist, sollte die angezeigte Zahl entsprechend niedriger sein – nicht 27 oder 16.

### 3.8 Rest-Anzeige oben links = Zahl in der Liste (Feedback 3.2)

**Ziel:** Die Anzeige **„Rest“** oben links in der Leiste (und die **„X Tage“** neben dem eigenen Namen) muss **dieselbe Zahl** zeigen wie die Zahl in Klammern neben Ihrem Namen in der Mitarbeiterliste.

1. **Urlaubsplaner** öffnen, **eigenen** Namen in der Liste suchen und die **Zahl in Klammern** notieren (z. B. **11**).
2. **Oben links** in der Leiste die Statistik **„✅ Rest“** prüfen sowie rechts **„X Tage“** neben Ihrem Namen.
3. **Erwartung:** Alle drei Werte sind **identisch** (z. B. überall **11**). Es darf nicht vorkommen, dass in der Liste 11 steht, oben links oder bei „X Tage“ aber z. B. 16 angezeigt wird.
4. **Falls die Werte abweichen:** Test als **nicht bestanden** vermerken und an IT melden (inkl. welche Zahl wo angezeigt wird).

---

## 4. Checkliste für Vanessa

### 4.1 Mitarbeiterverwaltung

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 1 | Login als Admin, **Admin** → **Mitarbeiterverwaltung** sichtbar und erreichbar | |
| 2 | Mitarbeiter auswählen → Tabs (Deckblatt, Adressdaten, Mitarbeiterdaten, Moduldaten) + Speichern-Button sichtbar | |
| 3 | Deckblatt: Änderung speichern → Wert bleibt nach Reload | |
| 4 | Adressdaten: Änderung speichern → Werte bleiben | |
| 5 | Vertrag: Änderung speichern → Werte bleiben | |
| 6 | Moduldaten → Urlaubsplaner: **Urlaubsanspruch** (Jahr + Tage) wählen → **„Urlaubsanspruch speichern“** → Meldung „Urlaubsanspruch gespeichert.“, Wert bleibt | |
| 7 | Urlaubseinstellungen (z. B. Max. Übertrag, Im Planer anzeigen) ändern → **Speichern** → Werte bleiben | |
| 8 | Arbeitszeitmodell: Hinzufügen, Bearbeiten, Löschen funktioniert | |
| 9 | Ausnahme: Hinzufügen, Löschen funktioniert | |
| 10 | Zeiten ohne Urlaub: Hinzufügen, Löschen funktioniert | |
| 11 | Sync-Vorschau öffnet sich; optional Sync ausführen → Erfolg | |

### 4.2 Verbindung Mitarbeiterverwaltung ↔ Urlaubsplaner

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 12 | **Urlaubsanspruch:** In Mitarbeiterverwaltung für einen MA (z. B. sich selbst) **11 Tage** (oder 16/27) für aktuelles Jahr setzen und speichern → Im **Urlaubsplaner** (gleiches Jahr) bei diesem MA erscheint eine Zahl ≤ gewählter Anspruch (Resturlaub) | |
| 13 | **Urlaubsanspruch:** Dropdown zeigt Personalplaner-Werte: **5,5 | 11 | 16 | 22 | 27 | 30** Tage (+ „Andere …“) | |
| 14 | **Im Urlaubsplaner anzeigen:** Bei einem MA **abwählen** → Speichern → Im Urlaubsplaner erscheint dieser MA **nicht** in der Liste | |
| 15 | **Im Urlaubsplaner anzeigen:** Wieder **ankreuzen** → Speichern → Im Urlaubsplaner erscheint der MA **wieder** | |
| 15a | **Rest-Anzeige:** Zahl „Rest“ oben links + „X Tage“ rechts = **gleich** der Zahl in Klammern neben dem eigenen Namen in der Liste (z. B. überall 11) | |

### 4.3 Urlaubsplaner

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 16 | Urlaubsplaner öffnen → Jahr wählen → Mitarbeiterliste mit Zahlen (Resturlaub) sichtbar | |
| 17 | Resturlaub-Anzeige wirkt logisch (nicht höher als erwarteter Anspruch; berücksichtigt bereits gebuchte Tage) | |
| 18 | „Rest“ oben links und „X Tage“ stimmen mit der Resturlaub-Zahl in der Mitarbeiterliste überein (Feedback 3.2) | |

---

## 5. Wann ist die Verbindung „valide und logisch und funktional“?

- **Valide:** Die in der Mitarbeiterverwaltung gespeicherten Werte (Urlaubsanspruch pro Jahr, „Im Urlaubsplaner anzeigen“) werden in der Datenbank korrekt abgelegt und vom Urlaubsplaner aus derselben Quelle gelesen (keine getrennten Systeme).
- **Logisch:** Im Urlaubsplaner ist die angezeigte Zahl (Resturlaub) nie höher als der in der Mitarbeiterverwaltung gesetzte Urlaubsanspruch für dieses Jahr; ausgeblendete MA erscheinen nicht im Planer.
- **Funktional:** Nach Speichern in der Mitarbeiterverwaltung reicht ein Reload (oder erneutes Öffnen) des Urlaubsplaners, um die Änderung zu sehen – ohne Neustart oder manuellen Datenimport.

Wenn die Punkte 12–15, 15a, 17 und 18 in der Checkliste mit **OK** bestätigt werden können, gilt die Verbindung zwischen Mitarbeiterverwaltung und Urlaubsplaner als getestet und funktional.

---

## 6. Bei Fehlern oder Fragen

- **Browser-Konsole (F12 → Konsole)** prüfen, ob Fehlermeldungen erscheinen; Screenshot oder Text an IT/Entwicklung senden.
- **Welcher Schritt** ist fehlgeschlagen? (Nr. der Checkliste + kurze Beschreibung.)
- **Link zu dieser Anleitung** und ausgefüllte Checkliste (z. B. als Foto oder Scan) erleichtern die Nachverfolgung.

---

**Referenz:** Detailliertere Schritte nur für die Mitarbeiterverwaltung (ohne Urlaubsplaner-Verbindung) stehen in  
`docs/TESTANLEITUNG_MITARBEITERVERWALTUNG_HR.md`.
