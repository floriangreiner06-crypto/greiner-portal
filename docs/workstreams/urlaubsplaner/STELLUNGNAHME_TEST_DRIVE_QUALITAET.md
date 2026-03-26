# Stellungnahme: Qualität unzureichend – Test nach 5 Minuten abgebrochen

**Quelle:** `Test DRIVE.docx` (Windows-Sync: `F:\Greiner Portal\Greiner_Portal_NEU\Server\docs\workstreams\urlaubsplaner\`)  
**Stand:** 2026-02-24

---

## Einschätzung

Die Qualität ist **nicht akzeptabel**. Bereits nach kurzem Test (ca. 5 Minuten) wurden **vier konkrete Fehler** festgestellt. Das ist ein klares Zeichen dafür, dass vor dem Rollout für weitere Abteilungen (z. B. Disposition) **systematische Tests und Bugfixes** nötig sind – und dass die bisherige Entwicklung zu wenig mit echten Nutzerszenarien und Rollen (nicht-Admin, Genehmiger, etc.) abgeglichen wurde.

---

## Die vier im Test-Dokument genannten Punkte

### 1. Falsche Berechnung Resturlaub (Susanne Kerscher)

- **Soll:** Vor Antrag 16 Tage Rest, 3 Tage im Juni verplant → **13 Tage Rest**.
- **Ist:** Im DRIVE werden **14 Tage Rest** angezeigt.
- **Bewertung:** Abweichung um 1 Tag – wieder eine **Resturlaub-Inkonsistenz**. Mögliche Ursachen (ohne hier geprüft zu haben): Locosoft vs. Portal (3 Tage „verplant“ nur in einem System?), Rundung, oder die Formel `Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub)` liefert für Susanne einen anderen Wert als erwartet. **Nötig:** Fall Susanne Kerscher (Mitarbeiterin, Jahr, Anspruch, Buchungen in Portal + Locosoft) nachvollziehen und Formel/Anzeige in Übereinstimmung bringen.

### 2. Krankheitstage: Susanne Kerscher kann Krankheit eintragen (sollte nur Admin)

- **Soll:** Krankheit eintragen nur für **Admin** (bzw. definierte Rolle) freigeschaltet.
- **Ist:** Susanne Kerscher (offenbar keine Admin-Rolle) kann Krankheitstage eintragen.
- **Bewertung:** **Berechtigungsfehler.** Die Prüfung „nur Admin (bzw. GRP_Urlaub_Admin) darf Krankheit buchen“ greift für diese Nutzerin nicht – entweder falsche Rolle, oder die Prüfung fehlt an der richtigen Stelle (Einzelbuchung, Masseneingabe, Kalender-UI). **Nötig:** Rechteprüfung für Urlaubstyp „Krankheit“ an allen Buchungswegen prüfen und sicherstellen, dass nur berechtigte Rollen den Typ wählen/buchen können.

### 3. Bei Zeitausgleich werden auch Urlaubstage abgezogen

- **Soll:** Zeitausgleich (ZA) mindert **nicht** den Urlaubsanspruch / Resturlaub.
- **Ist:** Wenn Zeitausgleich gebucht wird, werden offenbar auch Urlaubstage (Rest) abgezogen.
- **Bewertung:** Entweder wird **ZA in der Rest-Formel mitgezählt** (z. B. Locosoft liefert „Urlaub“ inkl. ZA und wir ziehen das ab), oder die **Anzeige/Validierung** behandelt ZA wie Urlaub. Die View `v_vacation_balance_*` zählt nur `vacation_type_id = 1` (Urlaub) – wenn trotzdem Rest sinkt, kommt der Fehler eher von **Locosoft-Aggregation** (Url/BUr/ZA vermischt?) oder von einer anderen Stelle, die ZA auf den Rest anrechnet. **Nötig:** Klarstellen, ob Rest nur aus Portal kommt oder min(Portal, Anspruch − Locosoft); wenn Locosoft: prüfen, ob Locosoft-„Urlaub“ für die Rest-Berechnung **nur** Url/BUr enthält und **kein** ZA. Ggf. Locosoft-Abfrage oder Anzeige anpassen.

### 4. Vertretungsregel nicht mehr aktiv

- **Soll:** Vertretungsregel gilt (Vertreter darf in Zeiträumen, in denen die vertretene Person Urlaub hat, keinen Urlaub buchen).
- **Ist:** Regel scheint nicht mehr zu greifen („nicht mehr aktiv“).
- **Bewertung:** Mögliche Ursachen: **substitution_rules** nicht befüllt/gepflegt, Prüfung in Buchung/API deaktiviert oder umgangen, oder Daten (Vertreter ↔ Vertretene) passen nicht. **Nötig:** Prüfen, ob `_check_substitute_vacation_conflict` in allen Buchungswegen aufgerufen wird (Einzelbuchung, Batch, Masseneingabe) und ob die Tabelle `substitution_rules` bzw. die Organigramm-Daten für die getesteten Personen stimmen.

---

## Konsequenzen

1. **Kein weiterer Rollout** (z. B. Disposition) ohne Behebung oder zumindest klare Einordnung dieser vier Punkte (und Regressionstests).
2. **Priorisierung:** Zuerst die Punkte 2 (Rechte Krankheit) und 4 (Vertretungsregel) prüfen – das sind klare Funktionsfehler. Danach 1 (Resturlaub Susanne Kerscher) und 3 (Zeitausgleich zieht Urlaub ab) analysieren und beheben.
3. **Testprozess:** Tests nicht nur „kurz anklopfen“, sondern mit **konkreten Testfällen und Rollen** (z. B. Susanne Kerscher als Nicht-Admin, mit Anträgen und mit Vertretung) durchspielen; Ergebnisse in derselben Form wie im „Test DRIVE“-Dokument festhalten.
4. **Dokumentation:** Diese Stellungnahme und das Test-Dokument (`Test DRIVE.docx`) in den Urlaubsplaner-Kontext (CONTEXT.md) aufnehmen, damit die nächste Session die vier Punkte gezielt abarbeitet.

---

## Nächste Schritte (für Entwicklung)

- **Punkt 2:** In `api/vacation_api.py` und ggf. Frontend prüfen, wo der Urlaubstyp „Krankheit“ gewählt werden kann und ob dort `can_book_krankheit` (bzw. Admin/GRP_Urlaub_Admin) geprüft wird.
- **Punkt 4:** Sicherstellen, dass `_check_substitute_vacation_conflict` bei jeder Buchung (book, book-batch, mass_booking) aufgerufen wird; Organigramm/`substitution_rules` für getestete MA prüfen.
- **Punkt 1:** Susanne Kerscher (employee_id, Anspruch, Buchungen Portal/Locosoft) analysieren wie zuvor bei Vanessa/Margit.
- **Punkt 3:** Locosoft-Abfrage und Rest-Formel prüfen – ob ZA in „Urlaub“ für Rest einfließt; ggf. Locosoft-Aggregation auf Url/BUr beschränken.

Diese Stellungnahme ersetzt keine Fehlerbehebung, soll aber die Probleme klar benennen und die Reihenfolge der Abarbeitung vorgeben.
