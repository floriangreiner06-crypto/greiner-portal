# Stellungnahme: Gebuchter Urlaub wird nicht vom Anspruch abgezogen (Vanessa-Feedback)

**Datum:** Februar 2026  
**Betrifft:** Urlaubsplaner – Resturlaub-Anzeige (Zahl in Klammern neben dem Namen)  
**Feedback:** „Gebuchter Urlaub wird nicht vom Anspruch abgezogen“; bei manchen MA steht z. B. weiterhin 28 Tage Rest, obwohl bereits Tage verplant sind. Bei Vanessa und Christian Aichinger stimmt der Saldo.

---

## Kurzfassung

- Die **Resturlaub-Berechnung** nutzt **zwei Quellen**: (1) **Portal** (`vacation_bookings`), (2) **Locosoft** (`absence_calendar`). Im Kalender werden beide angezeigt (Portal + Locosoft-Tage).
- Wenn Urlaub **nur in Locosoft** gebucht ist (z. B. 24. und 27.12.), die **Locosoft-Aggregat-Abfrage** für diese MA aber **0 Urlaubstage** liefert, bleibt die angezeigte Restzahl unverändert (z. B. 28).
- **Warum es bei Vanessa und Christian passt:** Entweder buchen sie im **Portal** (dann zieht die View den Urlaub ab) oder ihre **Locosoft-Daten** kommen korrekt an. MA ohne Locosoft-Verbindung werden nur aus dem Portal berechnet – dann stimmt die Anzeige, wenn alle Buchungen im Portal sind.

---

## Technischer Hintergrund

1. **View `v_vacation_balance_{Jahr}`**  
   Zieht nur **Portal-Buchungen** (Urlaub, type_id=1, approved/pending) vom Anspruch ab. Locosoft-Einträge stehen dort nicht drin.

2. **API `/balance`**  
   - Liest für jede Person: Anspruch, verbraucht, geplant, Rest aus der View.  
   - Für MA **mit** Locosoft-Verbindung: Es wird zusätzlich Locosoft-Urlaub geholt (`get_absences_for_employees`).  
   - Anzeige: **Rest = Anspruch − max(Portal-Urlaub, Locosoft-Urlaub)** (es wird immer der höhere Verbrauch berücksichtigt).

3. **Kalender**  
   Zeigt **Portal- und Locosoft-Tage** gemeinsam (API `/all-bookings`). Daher kann im Kalender „Urlaub“ stehen (z. B. aus Locosoft), obwohl die Balance bisher nur Portal oder nur das (ggf. fehlerhafte) Locosoft-Aggregat kannte.

4. **Mögliche Ursache für „28 bleibt 28“**  
   - Urlaub nur in **Locosoft** gebucht **und**  
   - Die Locosoft-Abfrage (Summe Urlaub pro MA) liefert für diese MA **0** (Fehler, falsches Mapping, andere Gründe in Locosoft/DB).  
   Dann wird nichts abgezogen → Rest bleibt z. B. 28.

---

## Umgesetzte Maßnahmen

1. **Fallback in der Balance-API**  
   Wenn die **Aggregat-Abfrage** (Locosoft) für einen MA **0 Urlaub** liefert, wird ein **zweiter Weg** genutzt: dieselbe Quelle wie für den Kalender (`get_absence_days_for_employees`). Daraus werden die Urlaubstage (Gründe „Url“, „BUr“) summiert. Wenn diese Summe > 0 ist, wird sie für die Resturlaub-Anzeige verwendet. So sollen Fälle abgefangen werden, in denen das Aggregat fehlt oder falsch ist, die Tagesdaten aber stimmen.

2. **Bereits zuvor umgesetzt**  
   Nach Buchung/Genehmigung/Storno/Ablehnung/Jahreswechsel wird die **Mitarbeiterliste inkl. Resturlaub** neu geladen (`loadAllEmployees`), damit sich die Zahl neben dem Namen sofort aktualisiert (ohne F5).

---

## Was wir von euch brauchen (optional)

- **Betroffene MA** (z. B. Stefanie Bittner, Thomas Stangl, Zuzana Scheppach), **Jahr** und **Beispieltage** (z. B. 24. und 27.12.).  
- Dann können wir prüfen:  
  - Ob die Buchungen **im Portal** (`vacation_bookings`) oder **nur in Locosoft** liegen.  
  - Ob die **Locosoft-Anbindung** (employee_number / locosoft_id) für diese MA stimmt und die Abfrage Urlaubstage liefert.

---

## Zusammenfassung für Vanessa

- **Problem:** Bei einigen MA wird gebuchter Urlaub (v. a. aus Locosoft) nicht vom angezeigten Rest abgezogen; bei dir und Christian Aichinger passt der Saldo.  
- **Ursache:** Resturlaub kommt aus Portal + Locosoft; wenn Locosoft für diese MA „0 Urlaub“ meldet, bleibt die Anzeige unverändert.  
- **Erledigt:** (1) Fallback: Wenn die Locosoft-Summe 0 ist, werden die gleichen Tagesdaten wie im Kalender für die Rest-Berechnung genutzt. (2) Die Anzeige wird nach jeder Buchung/Genehmigung/Storno sofort aktualisiert.  
- **Nächster Schritt:** Nach Deployment **Strg+F5** im Urlaubsplaner; wenn es bei einzelnen MA weiterhin falsch ist, bitte Namen + Jahr + Beispieltage nennen, dann prüfen wir die Locosoft-Daten für diese MA.
