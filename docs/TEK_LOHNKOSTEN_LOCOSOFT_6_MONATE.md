# TEK 4-Lohn: Echte Lohnkosten aus Locosoft, rollierender 6-Monats-Schnitt

## Haben wir die Lohnkosten aus Locosoft in der PostgreSQL?

**Ja.** Die in Locosoft verbuchten Lohnkosten (für Mechaniker/Werkstatt) liegen in der Portal-Datenbank in der Tabelle **`loco_journal_accountings`**.

- **Tabelle:** `loco_journal_accountings` (FIBU-Buchungen aus Locosoft, gespiegelt in die Portal-DB)
- **Lohnkonten:** **740000–742999** („Lohn“; 743xxx = Teile, 747xxx = Fremdleistungen)
- **Verwendung:** Bereits heute wird in der Online-TEK für den Bereich „4-Lohn“ im **laufenden Monat** ein Anteil Lohn zugeschlagen, berechnet aus den **echten verbuchten** Lohnkosten (740xxx) und dem Umsatz (84xxxx) der letzten Monate – bisher **3 abgeschlossene Vormonate**.

Es handelt sich also bereits um **echte Locosoft-Lohnkosten**, nicht um kalkulatorische Pauschalwerte. Die Anpassung betrifft nur:
- **Zeitraum:** von 3 auf **6 abgeschlossene Vormonate** (rollierender 6-Monats-Schnitt)
- **Formulierung:** in Kommentaren klarstellen, dass „echte verbuchte Lohnkosten aus Locosoft“ verwendet werden

## Technische Details

- **Datenquelle:** `loco_journal_accountings` (PostgreSQL/SQLite je nach `DB_TYPE`)
- **Lohn-Einsatz:** `nominal_account_number BETWEEN 740000 AND 742999`, Saldo über `debit_or_credit` / `posted_value`
- **Umsatz Werkstatt:** `nominal_account_number BETWEEN 840000 AND 849999`
- **Zeitraum für Durchschnitt:** 6 abgeschlossene Kalendermonate vor dem aktuellen Monat

## Alternative: Einsatz 6 Monate im Verhältnis zum aktuellen Umsatz (einfacher)

Statt nur Lohn 740xxx anzusetzen, kann man den **gesamten Einsatz 74xxxx** der letzten 6 Monate nehmen und eine Quote bilden:

- **Quote = Summe(Einsatz 74xxxx) / Summe(Umsatz 84xxxx)** über 6 abgeschlossene Monate
- **Einsatz kalk (laufender Monat) = Umsatz_aktuell × Quote**

Vorteil: eine Kennzahl, kein Aufteilen in Lohn/Teile/Fremdleistungen. Nachteil: reagiert auf Verschiebungen zwischen Lohn/Teile/FL nur über die 6-Monats-Quote.

**Wertevergleich:** Das Skript `scripts/vergleiche_tek_4lohn_methoden.py` berechnet beide Methoden und vergleicht sie (inkl. Abweichung Method B zum Ist im letzten abgeschlossenen Monat). Ausführen mit:  
`python3 scripts/vergleiche_tek_4lohn_methoden.py` (aus Projektroot, mit aktivierter venv).

- **Method A:** FIBU-Einsatz (aktuell) + (Umsatz × Lohnquote_6M) — wie bisher, nur 6 Monate
- **Method B:** Umsatz_aktuell × (Einsatz_6M / Umsatz_6M)

## Umsetzung im Code (Method B aktiv)

- **Datei:** `routes/controlling_routes.py`, Block „WERKSTATT-EINSATZ (TAG 140)“
- **Aktuell umgesetzt: Method B (Einsatz 6M-Quote)**  
  - `einsatz_quote_6m = Summe(Einsatz 74xxxx) / Summe(Umsatz 84xxxx)` über die letzten 6 abgeschlossenen Monate (loco_journal_accountings, mit firma_filter_umsatz / firma_filter_einsatz).  
  - Im laufenden Monat: `einsatz_kalk = werkstatt_umsatz * einsatz_quote_6m`; DB1/Marge daraus.  
  - Hinweis z. B.: „Einsatz kalk. (6M-Quote 36%): 120k“
- **Variante 1 (nur Lohn)** war: Lohn 740xxx / Umsatz 6M, dann FIBU + kalk. Lohn – nicht mehr aktiv.
