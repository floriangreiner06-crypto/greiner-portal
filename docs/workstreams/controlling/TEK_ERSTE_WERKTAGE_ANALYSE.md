# TEK – Analyse „Umschwenken“ zwischen 05.03. und 06.03. (erste Werktage)

**Korrektur (nach Klärung):** Die Prognose (DB1-Hochrechnung) wird **immer aus dem aktuellen Monat** berechnet: (DB1 / vergangene Werktage) × Werktage gesamt. Die frühere Sonderlogik „Prognose = 3-Monats-Durchschnitt (Vormonate), wenn &lt; 5 Tage mit Daten“ war ein Missverständnis und wurde entfernt. Breakeven bleibt der 4-Monats-Kostenschnitt.

---

## Ausgangslage (historisch)

- **Bis 05.03.2026:** TEK zeigte „-48.037 EUR UNTER Breakeven (Prognose)“ (Prognose 353.060 €, Breakeven 401.097 €).
- **Ab 06.03.2026:** TEK zeigte „+42.796 EUR ÜBER Breakeven (Prognose)“ (Prognose 445.819 €, Breakeven 403.023 €).

Es wirkt so, als würde die TEK „umgeschwenkt“ sein, obwohl sich die tatsächliche Performance (DB1 Monat 85.234 € → 101.323 €) nur moderat verbessert hat. Die **missverständliche Betrachtung** betrifft die **ersten ca. 4 Werktage bzw. die ersten Tage mit Locosoft-Daten**.

---

## Ursache 1: Prognose-Methode wechselt ab dem 5. Tag mit Daten

**SSOT:** `api/controlling_data.py`, Funktion `berechne_breakeven_prognose`, Zeilen 602–636.

### Logik

| Bedingung | Prognose-Berechnung | Methode |
|-----------|---------------------|---------|
| **tage_mit_daten < 5** | Prognose = **Durchschnitt DB1 der letzten 3 abgeschlossenen Monate** (vor dem aktuellen Monat) | `gleitend_3m` |
| **tage_mit_daten ≥ 5** | Prognose = **(aktueller_db1 / werktage_vergangen) × werktage_gesamt** (lineare Hochrechnung) | `hochrechnung` |

- **„Tage mit Daten“** = Anzahl verschiedener `accounting_date` im aktuellen Monat in Locosoft (FIBU). Locosoft wird typisch abends (ca. 18–19 Uhr) befüllt, daher sind am 05.03. abends oft erst 4 Tage (1.–4. März) mit Daten vorhanden.
- Sobald am **06.03.** der 5. Tag mit Daten in Locosoft ist, **springt** die Prognose von der 3-Monats-Durchschnitts-Prognose auf die **Hochrechnung aus dem laufenden Monat**.

### Konkret März 2026

- **Report 05.03. (19:30):**  
  - Vermutlich noch `tage_mit_daten = 4` (1.–4. März).  
  - Prognose = DB1-Schnitt aus z.B. Nov, Dez, Jan ≈ **353.060 €** (unabhängig vom aktuellen Monats-DB1).  
  - Breakeven (4M-Kosten, s. unten) = 401.097 € → **unter Breakeven**.

- **Report 06.03.:**  
  - `tage_mit_daten ≥ 5`.  
  - Prognose = (101.323 / 5) × 22 ≈ **445.819 €** (Hochrechnung aus Ist-DB1 und Werktagen).  
  - Breakeven ab 5. März mit neuem 4M-Fenster = 403.023 € → **über Breakeven**.

Die **Betrachtung ist missverständlich**, weil in den ersten 4 Tagen mit Daten die angezeigte „Prognose“ **nicht** eine Extrapolation des laufenden Monats ist, sondern ein fester Wert aus den Vormonaten. Für Nutzer wirkt es so, als ob sich die Lage am 6. März „auf einmal“ verbessert hat – tatsächlich hat sich die **Berechnungsmethode** geändert.

---

## Ursache 2: Breakeven (4M-Kostenschnitt) wechselt am 5. Kalendertag

**SSOT:** `api/controlling_data.py`, `STICHTAG_VORMONAT_4M = 5`, `_letzte_4_abgeschlossene_monate()`.

- **Bis 4. März (Tag 1–4):** Die „letzten 4 abgeschlossenen Monate“ für den Kostenschnitt sind **Okt, Nov, Dez, Jan** (Vormonat Februar wird bewusst ausgeschlossen, da Lohn/Gehalt zu Monatsbeginn gebucht wird und der Vormonat in Locosoft noch unvollständig wäre).
- **Ab 5. März:** Die 4 Monate sind **Nov, Dez, Jan, Feb**.

Damit ändert sich **kosten_pro_monat** und damit die **Breakeven-Schwelle** am 5. Kalendertag (401.097 € → 403.023 € im Beispiel). Das ist ein zweiter, kleinerer „Sprung“ neben dem Prognose-Wechsel.

---

## Zusammenfassung: Warum die ersten ~4 Werktage missverständlich sind

1. **Prognose:**  
   In den ersten **weniger als 5 Tagen mit Locosoft-Daten** zeigt die TEK eine Prognose auf Basis der **letzten 3 Monate** (gleitend_3m), **nicht** eine Hochrechnung aus dem aktuellen Monat. Sobald der 5. Tag mit Daten da ist, wird auf die übliche Hochrechnung (Prognose = DB1/vergangene WT × WT gesamt) umgestellt → gefühlter „Umschwung“.

2. **Breakeven:**  
   Am **5. Kalendertag** wechselt die 4M-Basis (ohne/mit Vormonat), die Breakeven-Schwelle ändert sich einmalig.

3. **Transparenz:**  
   Im Report/Portal ist für Nutzer nicht erkennbar, dass in der ersten Woche eine **andere** Prognosemethode (3-Monats-Schnitt) verwendet wird. Ein Hinweis wie „Prognose: Ø letzte 3 Monate (noch < 5 Tage mit Daten)“ existiert nur indirekt über `prognose_methode` / `hinweis_umlage` / `kosten_ohne_vormonat`.

---

## Empfehlungen (ohne Code-Änderung)

1. **Kommunikation:**  
   In GF/Controlling kurz festhalten: In den **ersten bis zu 4 Tagen mit FIBU-Daten** ist die TEK-Prognose bewusst der **3-Monats-Durchschnitt** (keine Hochrechnung aus dem laufenden Monat). Der „Sprung“ ab dem 5. Tag mit Daten ist methodenbedingt.

2. **Optional – Transparenz im Report/Portal:**  
   Wenn `prognose_methode == 'gleitend_3m'` (bzw. `tage_mit_daten < 5`): in TEK-E-Mail und TEK-Dashboard einen kurzen Hinweis anzeigen, z. B.  
   „Prognose bis zum 5. Tag mit Daten: Durchschnitt der letzten 3 Monate; ab dann: Hochrechnung aus aktuellem Monat.“

3. **Optional – Schwellenwert prüfen:**  
   Die Grenze „5 Tage mit Daten“ ist fachlich sinnvoll (wenig Daten → keine stabile Hochrechnung). Wenn gewünscht, kann man diskutieren, ob z. B. „5 Werktage vergangen“ statt „5 Tage mit Daten“ die Darstellung am Monatsanfang noch klarer macht (dann gleiche Logik unabhängig von Locosoft-Befüllung).

---

## Referenzen

- CONTEXT.md (Controlling): TEK Monatsanfang 4M ohne Vormonat, TEK Prognose wie GlobalCube, Werktage-Datenstichtag.
- `api/controlling_data.py`: `berechne_breakeven_prognose`, `_letzte_4_abgeschlossene_monate`, `STICHTAG_VORMONAT_4M`.
- `utils/werktage.py`: `get_werktage_monat` (Stichtag vor/nach 19:00).
