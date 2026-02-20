# Testanleitung für Vanessa: Organigramm & Rechteverwaltung

**Zielgruppe:** Vanessa (HR)  
**Stand:** Februar 2026  
**Ziel:** Organigramm (Abteilungen, Hierarchie, Vertretungen, Genehmiger) und Rechteverwaltung prüfen.

---

## 1. Voraussetzungen

- **Login:** Als **Admin** (oder Nutzer mit Zugriff auf Admin → Organigramm / Rechteverwaltung).
- **Browser:** Chrome, Edge oder Firefox; nach Änderungen **Strg+F5** (hart neu laden).
- **Portal-URL:** z. B. `http://drive` oder `https://drive.auto-greiner.de`

---

## 2. Rechteverwaltung

### 2.1 Einstieg

1. **Admin** → **Rechteverwaltung** öffnen.
2. **Tabs:** „User & Rollen“, „Rollen-Features“, „Matrix“, „Architektur“ (und ggf. weitere).
3. **Status-Leiste** unten: Anzahl User, Rollen, Features.

### 2.2 User & Rollen

- Tabelle mit Nutzern, zugewiesenen Rollen (Badges), Quelle (Portal/Default).
- **Filter** nutzen (z. B. nach Rolle), **Suche** falls vorhanden.
- **Erwartung:** Keine Fehlermeldung, Daten laden; User ohne Rolle ggf. hervorgehoben.

### 2.3 Rollen-Features / Matrix

- **Rollen-Features:** Welche Rolle hat welches Feature (Häkchen).
- **Matrix:** Spalten = Rollen, Zeilen = Features (oder umgekehrt); konsistent zu „Rollen-Features“.
- **Erwartung:** Nur Rollen aus dem System (z. B. admin, …), keine leeren oder doppelten Spalten.

### 2.4 Architektur

- Übersicht zur Rechte-Architektur (Dokumentation).
- **Erwartung:** Seite lädt ohne Fehler.

---

## 3. Organigramm – Abteilungen

1. **Admin** (oder Navigation) → **Organigramm** öffnen.
2. Tab **Abteilungen** auswählen.
3. **Erwartung:** Liste/Karten der Abteilungen mit Namen, ggf. Standort, Mitarbeiteranzahl.
4. **Standortfilter** (falls vorhanden): z. B. „Deggendorf“ / „Landau“ / „Alle“ – Liste filtert sich.
5. Abteilung aufklappen/anklicken → **Mitarbeiter** der Abteilung sichtbar.

---

## 4. Organigramm – Hierarchie

1. Im Organigramm Tab **Hierarchie** wählen.
2. **Erwartung:** Baum/Struktur (z. B. Geschäftsführung oben, darunter Teams).
3. **„Team anzeigen“ / „Team ausblenden“** pro Knoten → Untere Ebene klappt auf/zu.
4. **„X offen“** (falls angezeigt): Klick führt zur Chef-Übersicht Urlaub (offene Anträge).
5. **Standortfilter** (falls vorhanden): Hierarchie filtert sich nach Standort.

---

## 5. Organigramm – Vertretungsregeln

1. Tab **Vertretungen** wählen.
2. **Tabelle:** Spalten z. B. Mitarbeiter, Abteilung, Vertreter, Prio, Aktion (Löschen).
3. **Neue Regel:**
   - Button **„Neue Regel“** klicken.
   - **Mitarbeiter (wird vertreten):** aus Dropdown wählen.
   - **Vertreter:** aus Dropdown wählen (nicht dieselbe Person).
   - **Priorität:** 1 (Hauptvertreter) oder 2 (Stellvertreter).
   - **Speichern** klicken.
4. **Erwartung:** Meldung Erfolg, neue Zeile erscheint in der Tabelle.
5. **Löschen:** Bei einer Regel auf **Löschen** (Papierkorb) klicken → Bestätigung → Zeile verschwindet.

---

## 6. Organigramm – Genehmigungsregeln

1. Tab **Genehmiger** wählen.
2. **Tabelle:** Gruppe, Standort, Genehmiger, Prio, Aktion (Löschen).
3. **Neue Regel:**
   - Button **„Neue Regel“** klicken.
   - **Gruppe (Abteilung):** Abteilungsname wählen (z. B. **Geschäftsführung**, Werkstatt, Service & Empfang) – **nicht** Kurzcode wie „GL“. Die Liste kommt aus Abteilungen und bestehenden Regeln.
   - **Standort:** Alle Standorte / Deggendorf / Landau a.d. Isar.
   - **Genehmiger (Mitarbeiter):** Person mit LDAP-Anbindung wählen.
   - **Priorität:** 1 (Haupt-Genehmiger) oder 2 (Stellvertreter).
   - **Speichern** klicken.
4. **Erwartung:** Meldung Erfolg, neue Zeile erscheint; **Gruppe** wird als Abteilungsname angezeigt (konsistent zu bestehenden Regeln).
5. **Löschen:** Bei einer Regel auf **Löschen** klicken → Bestätigung → Zeile verschwindet (Regel wird deaktiviert).

**Hinweis:** Wenn eine Regel mit Kurzcode „GL“ angelegt wurde, diese löschen und mit **Geschäftsführung** aus dem Dropdown neu anlegen, damit die Chef-Übersicht Urlaub korrekt zuordnet.

---

## 7. Vertretungsregel und Urlaubsplaner (Auswirkung prüfen)

Die hinterlegten **Vertretungsregeln** wirken im Urlaubsplaner: **Der Vertreter darf in dem Zeitraum keinen Urlaub buchen, in dem die von ihm vertretene Person abwesend ist** (Urlaub/Abwesenheit).

### 7.1 Testablauf

1. **Vertretungsregel vorbereiten** (Organigramm → Tab Vertretungen):  
   z. B. **Person A** (wird vertreten) → **Person B** (Vertreter), Priorität 1. Speichern.
2. **Urlaub für Person A** an einigen Tagen buchen (oder bereits gebucht haben), z. B. 15.03., 16.03., 17.03. (Status „beantragt“ oder „genehmigt“).
3. **Als Person B (Vertreter) einloggen** und im **Urlaubsplaner** an **denselben Tagen** (z. B. 15.–17.03.) Urlaub buchen wollen.
4. **Erwartung:**  
   - Buchung wird **abgelehnt**.  
   - Meldung erscheint (z. B. im Kalender oder als Fehlermeldung):  
     *„Sie vertreten in diesem Zeitraum [Name von A]. Urlaubsbuchung an den Tagen 2026-03-15, 2026-03-16, 2026-03-17 ist nicht möglich.“*
5. **Als Person B** an **anderen Tagen** (an denen A keinen Urlaub hat) Urlaub buchen.  
   **Erwartung:** Buchung ist möglich (keine Fehlermeldung).

### 7.2 Masseneingabe (Admin)

- Wenn ein Admin per **Masseneingabe** Urlaub für mehrere Mitarbeiter an denselben Tagen bucht: Für **Vertreter**, die an diesen Tagen jemanden vertreten (der abwesend ist), werden **diese Einzelbuchungen übersprungen** (kein Fehler, Rest wird gebucht).

---

## 8. Kurz-Checkliste

| Nr | Test | OK / Anmerkung |
|----|------|----------------|
| 1 | Rechteverwaltung: Tabs laden (User & Rollen, Rollen-Features, Matrix, Architektur) | |
| 2 | Organigramm – Abteilungen: Liste lädt, Standortfilter funktioniert | |
| 3 | Organigramm – Hierarchie: Baum sichtbar, Team auf-/zuklappen, „X offen“ optional prüfen | |
| 4 | Vertretungen: **Neue Regel** anlegen (MA + Vertreter + Prio) → Speichern → Zeile erscheint | |
| 5 | Vertretungen: **Löschen** einer Regel → Bestätigung → Zeile verschwindet | |
| 6 | Genehmiger: **Neue Regel** mit Abteilungsname (z. B. Geschäftsführung) → Speichern → Zeile erscheint | |
| 7 | Genehmiger: **Löschen** einer Regel → Bestätigung → Zeile verschwindet | |
| 8 | **Vertretungsregel & Urlaub:** Vertreter (B) kann an Tagen, an denen Vertretene (A) Urlaub hat, **keinen** Urlaub buchen → Fehlermeldung; an anderen Tagen Buchung möglich | |

---

## 9. Bei Fehlern

- **Strg+F5** (hart neu laden) probieren.
- **Browser-Konsole (F12 → Konsole)** prüfen; Screenshot oder Fehlertext an IT (Florian) senden.
- Checklisten-Nr. und kurze Beschreibung angeben.

---

**Stand:** Februar 2026 (ergänzt: Vertretungsregel-Auswirkung im Urlaubsplaner).  
**Sync:** Diese Datei liegt im Windows-Sync unter  
`docs\TESTANLEITUNG_VANESSA_ORGANIGRAMM_RECHTE.md`.
