# Testanleitung für Vanessa: Urlaubssperren & Buchungsrollen

**Zielgruppe:** Vanessa (HR)  
**Stand:** Februar 2026  
**Inhalt:** Prüfung der Anpassungen zu Urlaubssperren (Löschen, spezifische Mitarbeiter) sowie Schulung/Krankheit nur für Genehmiger & Admin.

---

## 1. Voraussetzungen

- **Login:** Als Nutzer mit **Admin-** oder **Urlaub-Admin-Rechten** (z. B. für Urlaubssperren löschen und Masseneingabe).
- **Genehmiger-Login:** Ein zweiter Test optional als **Genehmiger** (ohne Admin), um zu prüfen, dass nur Genehmiger/Admin Schulung und Krankheit buchen können.
- **Portal-URL:** z. B. `http://drive`
- **Browser:** Nach Änderungen **Strg+F5** (hart neu laden).

---

## 2. Urlaubssperre löschen (Admin)

**Ziel:** Sicherstellen, dass Admins Urlaubssperren wieder löschen können.

### Schritte

1. **Urlaubsplaner Admin** öffnen (z. B. über Menü **Urlaub** → **Urlaubsplaner Admin** oder direkte URL, sofern vorhanden).
2. Bereich **„Urlaubssperren“** finden.
3. **Jahr** wählen (z. B. 2026).
4. **Erwartung:** Tabelle mit bestehenden Sperren (Datum, Abteilung, Grund) und pro Zeile ein Button **„Löschen“**.
5. Eine **Test-Sperre** löschen (z. B. eine, die du zuvor angelegt hast):
   - Auf **„Löschen“** klicken.
   - Bestätigungsdialog: **„Urlaubssperre vom … wirklich löschen?“** → **OK**.
6. **Erwartung:** Meldung wie „Sperre gelöscht“, die Zeile verschwindet aus der Tabelle.

**Falls „Keine Berechtigung“ erscheint:** Mit einem Nutzer testen, der **Portal-Admin** oder in der Gruppe **GRP_Urlaub_Admin** ist.

---

## 3. Urlaubssperre für spezifische Mitarbeiter (Masseneingabe)

**Ziel:** Urlaubssperre nur für ausgewählte Mitarbeiter anlegen (nicht nur für eine ganze Abteilung).

### Schritte

1. **Urlaubsplaner (V2)** öffnen (moderne Kalenderansicht).
2. Button **„Masseneingabe“** öffnen.
3. **Ziel:** **„Spezifische Mitarbeiter“** wählen (nicht „Abteilung“).
4. **Abteilung** bleibt leer bzw. „Abteilung wählen…“ – das ist bei dieser Option **richtig so**.
5. **Buchungsart:** **„🚫 Urlaubssperre“** wählen.
6. **Datum(e):** Mindestens ein Datum hinzufügen (z. B. ein zukünftiger Tag).
7. Im Feld **„Mitarbeiter (mehrfach auswählbar)“** einen oder mehrere Mitarbeiter auswählen (Strg/Cmd + Klick für Mehrfachauswahl).
8. Auf **„Erstellen“** klicken.
9. **Erwartung:** Keine Meldung „Bitte Abteilung wählen für Urlaubssperre“. Stattdessen: Erfolgsmeldung, z. B. „X Urlaubssperre(n) erstellt!“.

### Kontrolle im Kalender

- An dem gesperrten Datum sollten **nur die ausgewählten Mitarbeiter** den roten Sperren-Strich sehen.
- Andere Mitarbeiter (andere Abteilungen / nicht ausgewählt) an diesem Tag **nicht** gesperrt.

**Kurz:** Abteilungssperre = alle in der Abteilung gesperrt. Spezifische Mitarbeiter = nur diese MA gesperrt.

---

## 4. Schulung & Krankheit nur Genehmiger & Admin

**Ziel:** Nur Genehmiger und Admins dürfen **Schulung** und **Krankheit** buchen (Einzelbuchung und Masseneingabe).

### 4.1 Einzelbuchung (ein Tag, ein Mitarbeiter)

1. Als **Genehmiger** oder **Admin** im Urlaubsplaner (V2) einloggen.
2. Einen Tag anklicken (eigener oder ein Mitarbeiter, falls Admin).
3. Buchungsart **„📚 Schulung“** oder **„🤒 Krank“** wählen und speichern.
4. **Erwartung:** Buchung wird angelegt (keine Fehlermeldung).

5. Optional: Als **normaler Mitarbeiter** (weder Genehmiger noch Admin) einloggen und denselben Versuch machen.
6. **Erwartung:** Meldung in der Art: **„Schulung und Krankheit können nur von Genehmiger oder Admin eingetragen werden.“**

### 4.2 Masseneingabe (Schulung/Krankheit)

1. Als **Genehmiger** oder **Admin** einloggen.
2. **Masseneingabe** öffnen.
3. **Ziel:** z. B. Abteilung oder spezifische Mitarbeiter.
4. **Buchungsart:** **„📚 Schulung“** oder **„🤒 Krank“**.
5. Datum(e) wählen und **„Erstellen“** klicken.
6. **Erwartung:** Buchungen werden erstellt (keine Berechtigungsfehler).

7. Optional: Als **normaler Mitarbeiter** (ohne Genehmiger/Admin) Masseneingabe mit Schulung/Krankheit versuchen.
8. **Erwartung:** Fehlermeldung **„Keine Berechtigung“** (Masseneingabe für diese Buchungsarten nur für Genehmiger & Admin).

**Hinweis:** **Zeitausgleich** bleibt weiterhin nur für **Admins** buchbar (nicht für Genehmiger).

---

## 5. Kurz-Checkliste

| Test | Erwartung |
|------|-----------|
| Urlaubssperre löschen (Admin-Seite) | Button „Löschen“ funktioniert, Sperre verschwindet. |
| Urlaubssperre – Ziel „Spezifische Mitarbeiter“ | Kein Zwang zur Abteilung; Sperre nur für ausgewählte MA. |
| Schulung/Krankheit als Genehmiger oder Admin | Buchung (einzeln + Massen) möglich. |
| Schulung/Krankheit als normaler MA | Fehlermeldung: nur Genehmiger/Admin. |

---

## 6. Bei Problemen

- **„Keine Berechtigung“ beim Löschen:** Mit Nutzer testen, der **Portal-Admin** oder **GRP_Urlaub_Admin** ist.
- **„Bitte Abteilung wählen“ bei spezifischen MA:** Sicherstellen, dass **Ziel = „Spezifische Mitarbeiter“** und mindestens **ein Mitarbeiter** ausgewählt ist.
- **Schulung/Krankheit geht nicht:** Prüfen, ob der Nutzer in einer **Genehmiger-Gruppe** (z. B. `GRP_Urlaub_Genehmiger_…`) oder **GRP_Urlaub_Admin** ist.

Bei Fragen oder Fehlern bitte an die IT (Florian) wenden und ggf. Browser, Nutzer und genaue Schritte angeben.
