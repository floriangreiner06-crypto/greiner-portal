# Kontext-Registry für KI „Mit KI erweitern“

**Letzte Prüfung:** 2026-02-28 (Session-End controlling: CONTEXT.md aktualisiert, tek-Inhalt unverändert).

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
- **Breakeven-Prognose:** Breakeven-Schwelle = 4-Monats-Schnitt der BWA-Kosten (unverändert). Die **Prognose (Hochrechnung)** wird **immer** aus dem aktuellen Monat berechnet: (aktueller DB1 / vergangene Werktage) × Werktage gesamt (wie GlobalCube); es gibt keinen Vormonats-Durchschnitt mehr. (1) **BWA-Kosten:** 4-Monats-Schnitt der Kosten (variable, direkte, indirekte) aus Locosoft – letzte 4 abgeschlossene Kalendermonate, ggf. anteilig nach Umsatz je Firma. (2) **Werktage:** Echte Werktage (Mo–Fr, ohne bayerische Feiertage). **Datenstichtag:** Locosoft liefert abends; vor 19:00 Uhr zählt „vergangen“ nur bis gestern. (3) **DB1 pro Werktag** = BWA-Kosten des Monats / Werktage gesamt. (4) **Hochrechnung DB1** = (aktueller DB1 / vergangene Werktage) × Werktage gesamt. (5) Ampel (grün/gelb/rot) und Gap aus aktueller DB1 und hochgerechneter DB1 vs. Breakeven-Schwelle.

Wenn du einen Hilfe-Artikel zu TEK oder Breakeven erweiterst, ergänze einen kurzen Abschnitt „So berechnet das DRIVE …“ mit diesen Punkten (rollierender Schnitt für Einsatz, BWA-Kosten 4-Monats-Schnitt, Prognose immer aus aktuellem Monat, Werktage mit Stichtag 19:00), ohne Code zu zitieren.

---

## Urlaub / Urlaubsplaner / Resturlaub / Genehmiger

**Schlüsselwörter (Tags oder Titel):** `urlaub`, `resturlaub`, `urlaubsplaner`, `genehmiger`, `urlaubsantrag`

**Kontext für KI:**

Urlaubsplaner im DRIVE: Anspruch und Resturlaub kommen aus der Mitarbeiterverwaltung (Portal). Resturlaub = min(Portal-View-Rest, Anspruch − Locosoft-Urlaub); Krankheit mindert den Resturlaub nicht. Genehmiger werden über AD-Gruppen (z. B. „Genehmiger für Urlaub Disposition“ oder GRP_Urlaub_Genehmiger_*) und Team (AD manager bzw. Abteilung) ermittelt. Bei Genehmigung: E-Mail an HR und Mitarbeiter, optional Eintrag in Outlook-Kalender (drive@ und Mitarbeiter-Kalender).
