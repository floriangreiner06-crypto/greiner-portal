# Kontext-Registry für KI „Mit KI erweitern“

**Letzte Prüfung:** 2026-03-20 (Session controlling: Konten-Verwaltung Persistenz/Sortierung geprüft; Registry-Einträge TEK/Urlaub gegengeprüft).

**Zweck:** Pro Thema ein kurzer, fachlicher SSOT-Text für die KI. Wird beim „Mit KI erweitern“ an den Prompt angehängt, damit die KI Berechnungsdetails korrekt ergänzen kann.

**Matching:** Über **Tags** oder **Titel** des Artikels (z. B. Tag `tek` oder Titel enthält „Breakeven“ → Kontext „TEK/Breakeven“).

---

## TEK / Breakeven / Einsatz / DB1

**Schlüsselwörter (Tags oder Titel):** `tek`, `breakeven`, `erfolgskontrolle`, `kennzahlen`, `einsatz`, `db1`, `deckungsbeitrag`

**Kontext für KI:**

Die TEK (Tägliche Erfolgskontrolle) im DRIVE zeigt tägliche Kennzahlen für Umsatz, Einsatz, DB1 (Deckungsbeitrag 1), Marge und eine Breakeven-Prognose. Alle Berechnungen kommen aus einer zentralen Quelle (api/controlling_data.py).

- **Umsatz:** Tagesumsatz aus Locosoft (Fahrzeugverkauf, Werkstatt, Teile etc.), Konten 800000–889999.
- **Einsatz (4-Lohn im laufenden Monat):** Im laufenden Monat wird der **rollierende 6-Monats-Schnitt** verwendet: Einsatz_aktuell = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M). Grund: Die FIBU (74xxxx) ist im laufenden Monat oft noch nicht voll gebucht; so bleibt die Marge aussagekräftig. In abgeschlossenen Monaten kommt der Einsatz direkt aus den Buchungen.
- **DB1:** Deckungsbeitrag 1 = Umsatz minus variable Kosten (Einsatz).
- **Stückzahlen NW/GW:** Aus FIBU (loco_journal_accountings), Summe der pro Konto distinct vehicle_reference für 81xxxx/82xxxx – gleiche Quelle wie die Detail-Ansicht (Übersicht = Detail); Portal und E-Mail-Report konsistent.
- **Breakeven-Prognose:** Breakeven-Schwelle = 4-Monats-Schnitt der BWA-Kosten (unverändert). Die **Prognose (Hochrechnung)** wird **immer** aus dem aktuellen Monat berechnet: (aktueller DB1 / vergangene Werktage) × Werktage gesamt (wie GlobalCube); es gibt keinen Vormonats-Durchschnitt mehr. (1) **BWA-Kosten:** 4-Monats-Schnitt der Kosten (variable, direkte, indirekte) aus Locosoft – letzte 4 abgeschlossene Kalendermonate, ggf. anteilig nach Umsatz je Firma. (2) **Werktage:** Echte Werktage (Mo–Fr, ohne bayerische Feiertage). **Datenstichtag:** Locosoft liefert abends; vor 19:00 Uhr zählt „vergangen“ nur bis gestern. (3) **DB1 pro Werktag** = BWA-Kosten des Monats / Werktage gesamt. (4) **Hochrechnung DB1** = (aktueller DB1 / vergangene Werktage) × Werktage gesamt. (5) Ampel (grün/gelb/rot) und Gap aus aktueller DB1 und hochgerechneter DB1 vs. Breakeven-Schwelle.

Wenn du einen Hilfe-Artikel zu TEK oder Breakeven erweiterst, ergänze einen kurzen Abschnitt „So berechnet das DRIVE …“ mit diesen Punkten (rollierender Schnitt für Einsatz, BWA-Kosten 4-Monats-Schnitt, Prognose immer aus aktuellem Monat, Werktage mit Stichtag 19:00), ohne Code zu zitieren.

---

## Urlaub / Urlaubsplaner / Resturlaub / Genehmiger

**Schlüsselwörter (Tags oder Titel):** `urlaub`, `resturlaub`, `urlaubsplaner`, `genehmiger`, `urlaubsantrag`

**Kontext für KI:**

Urlaubsplaner im DRIVE: Anspruch und Resturlaub kommen ausschließlich aus der Mitarbeiterverwaltung (Portal-View); Locosoft fließt nicht mehr in die Resturlaubsberechnung ein. Krankheit mindert den Resturlaub nicht. Teilzeit: Nicht-Arbeitstage (Arbeitszeitmodell work_weekdays) werden im Planer grau dargestellt und bei Urlaubsantrag nicht vom Kontingent abgezogen (contingent_days). Genehmiger (AD-Gruppen, z. B. GRP_Urlaub_Genehmiger_*) dürfen für ihr Team auch Urlaub eintragen und stornieren. Kategorie „kein Samstagsdienst (Info)“: reine Info, kein Urlaubstag-Abzug. Bei Genehmigung: E-Mail an HR und Mitarbeiter, optional Outlook-Kalender (drive@ und Mitarbeiter-Kalender).
