# TEK DRIVE vs. Reporting – Analyse der Abweichungen (ohne Code-Änderung)

**Stand:** 2026-02-17  
**Auftrag:** Nur Analyse, nichts ändern.

## Beobachtete Abweichungen (Screenshots Feb 2026)

| Kennzahl | DRIVE (Portal) | Reporting (E-Mail/PDF) |
|----------|----------------|------------------------|
| DB1 Monat | 261.156 € | 240.073 € (KPI) / 241.540 € (Tabelle) |
| Umsatz Monat | 1.404.078 € | 1.403.905 € |
| Prognose | 435.260 € | 400.122 € |
| Breakeven | 389.700 € | 395.836 € |
| Stück gesamt | 68 (GW 28) | 70 (GW 30) |
| Marge Monat | 18,6 % | 17,1 % / 17,2 % |
| Service/Werkstatt Umsatz Monat | 112.097 € | 111.924 € |

---

## 1. Zwei getrennte Datenpfade

- **Portal (DRIVE):** `routes/controlling_routes.py` → `api_tek()` baut Umsatz/Einsatz/DB1 **selbst** aus `loco_journal_accountings` (eigene SQL-Aggregation), inkl. 6-8932 und 9-Andere. `total_db1` und `gesamt` kommen aus dieser Route. Breakeven/Prognose: `berechne_breakeven_prognose(monat, jahr, total_db1, ...)` mit diesem **Portal-**`total_db1`.
- **Reporting (E-Mail/PDF):** `scripts/send_daily_tek.py` → `get_tek_data()` → `scripts/tek_api_helper.py` → `api.controlling_data.get_tek_data()` (get_tek_data_core). Alle Summen und die Prognose kommen **nur** aus `get_tek_data`; es wird **kein** Aufruf der Portal-Route gemacht.

Beide nutzen dieselbe Tabelle `loco_journal_accountings` über `db_session()` (Portal-DB). Unterschiede entstehen durch **unterschiedliche Aggregationslogik**, nicht durch unterschiedliche Datenbank oder Datenquelle.

---

## 2. Aggregationslogik: Clean Park (847301/747301) und 6-8932

### Portal (api_tek)

- **Umsatz:** CASE bildet Bereiche 1-NW, 2-GW, 3-Teile, **4-Lohn (84xxxx inkl. 847301)**, 5-Sonst, **6-8932** (893200–893299), sonst 9-Andere.
- **Einsatz:** CASE 74xxxx → 4-Lohn **inkl. 747301**, sonst 9-Andere (kein separates Clean-Park-Bucket).
- **Totals:** `totals['umsatz'] += umsatz_dict['6-8932'] + umsatz_dict['9-Andere']`, `totals['einsatz'] += einsatz_dict['9-Andere']`.
- Clean Park ist in der Anzeige **nicht** separat; 847301/747301 stecken in 4-Lohn bzw. 9-Andere.

### get_tek_data (controlling_data)

- **Umsatz:** CASE 4-Lohn = 84xxxx **ohne** 847301 (`nominal_account_number != 847301`); 8932 landet im **ELSE** → 9-Andere.
- **Einsatz:** CASE 4-Lohn = 74xxxx **ohne** 747301; 747301 → 9-Andere.
- **Zusätzlich:** Eigene Abfrage für Clean Park (847301 Umsatz, 747301 Einsatz); Ergebnis wird zu den Totals addiert:
  - `total_umsatz += umsatz_dict['9-Andere'] + cp_umsatz`
  - `total_einsatz += einsatz_dict['9-Andere'] + cp_einsatz`

**Folge:** In get_tek_data sind 847301 und 747301 **doppelt** enthalten: einmal in 9-Andere (weil aus 4-Lohn ausgeschlossen) und einmal als Clean-Park-Summe. Das erhöht Umsatz und Einsatz um je die CP-Beträge; der Effekt auf DB1 ist `(cp_umsatz - cp_einsatz)`. Ob das die ~21k DB1-Differenz erklärt, hängt von der Höhe von Clean Park ab (und ob cp_umsatz − cp_einsatz negativ ist). Unabhängig davon ist die Doppelzählung fachlich falsch und sollte in einer späteren Korrektur entfernt werden (z. B. 9-Andere ohne 847301/747301 oder Clean Park nicht zusätzlich addieren).

---

## 3. 4-Lohn-Einsatz: Rollierender Schnitt (vereinbart) – SSOT nur in get_tek_data

- **Vereinbarung:** Für 4-Lohn-Einsatz im laufenden Monat gilt der **rollierende 6-Monats-Schnitt**:  
  `Einsatz = Umsatz_aktuell × (Einsatz_6M / Umsatz_6M)`.  
  Siehe `docs/TEK_LOHNKOSTEN_LOCOSOFT_6_MONATE.md`; SSOT für alle TEK-KPIs: `api/controlling_data.py` (CLAUDE.md).
- **get_tek_data:** Setzt diese Logik um (im laufenden Monat: 4-Lohn-Einsatz = rollierender Schnitt).
- **Portal (api_tek):** Baut Umsatz/Einsatz **eigen** in der Route und nutzt für 4-Lohn den **gebuchten** FIBU-Einsatz (74xxxx) – **keine** Nutzung der SSOT, daher abweichender 4-Lohn-Einsatz und abweichender Gesamt-DB1.

**Konsequenz:**  
- Report nutzt SSOT (rollierender Schnitt) → total_einsatz/total_db1 aus get_tek_data.  
- Portal nutzt eigene Aggregation (FIBU-Stand) → anderes total_db1.  
- Die beobachtete DB1-Differenz (Report niedriger) entsteht, weil das Portal die vereinbarte SSOT (get_tek_data inkl. rollierender Schnitt) **nicht** verwendet.

**Zusammenfassung:** Die Abweichung ist ein **Verstoß gegen die SSOT-Regel**: Eine Quelle für alle KPIs/Berechnungen. Lösung: Portal muss TEK-KPIs aus get_tek_data beziehen, nicht selbst aggregieren.

---

## 4. Prognose und Breakeven

- Beide nutzen dieselbe Funktion `berechne_breakeven_prognose` (bzw. Standort-Variante), aber mit **unterschiedlichem** `aktueller_db1`:
  - **Portal:** übergibt `total_db1` aus der **Portal-**Aggregation (inkl. gebuchter 4-Lohn-Einsatz).
  - **Report:** Prognose/Breakeven kommen aus **get_tek_data**; dort wird `berechne_breakeven_prognose` intern mit dem **get_tek_data-**Gesamt-DB1 aufgerufen (inkl. kalkulatorischer 4-Lohn).

Weil der DB1-Eingabewert unterschiedlich ist (261k vs. 240k), sind **Prognose** (435k vs. 400k) und **Breakeven-Abstand** (389,7k vs. 395,8k Kosten) zwangsläufig unterschiedlich. Die Formel (Werktage-Divisor, „Noch X WT“) ist dieselbe; die Eingaben weichen ab.

---

## 5. Stückzahlen (68 vs. 70)

- **Portal:** Stückzahlen kommen aus der gleichen Route (z. B. `get_stueckzahlen_locosoft` im Kontext von api_tek).
- **Report:** `tek_api_helper.get_tek_data_from_api()` holt Bereiche aus `get_tek_data_core` und ruft **separat** `get_stueckzahlen_locosoft(von, bis, '1-NW'/'2-GW', ...)` auf.

Mögliche Ursachen für 68 vs. 70:
- **Zeitpunkt:** E-Mail/Report zu anderem Zeitpunkt generiert als der Portal-Abruf (z. B. andere Tagesstände in Locosoft).
- **Parameter:** Leichte Abweichung bei `von`/`bis`, `firma`, `standort` zwischen Route und Helper (z. B. wenn die Route einen anderen Standortfilter oder andere Grenzen verwendet).
- **Datenquelle Stück:** Beide nutzen Locosoft (dealer_vehicles / fakturierte Auslieferungen); Abweichung durch unterschiedliche Filter oder Stichtag denkbar.

Empfehlung: Einmal gleichen Aufruf (gleiches Datum, gleiche Parameter) für Portal und Helper prüfen und Stückzahlen-Abfrage (inkl. Filter) in Route und Helper vergleichen.

---

## 6. Service/Werkstatt-Umsatz (112.097 € vs. 111.924 €)

Kleine Differenz (173 €) im Bereich 4-Lohn/Service. Denkbar:
- Rundungsunterschiede in der Kette (Bereiche → Gesamt).
- Im Report: 4-Lohn wird aus get_tek_data übernommen (dort 84xxxx **ohne** 847301); 847301 steckt in 9-Andere + Clean Park. Im Portal: 847301 ist in 4-Lohn. Wenn 847301 in einem der Systeme anders zugeordnet oder doppelt/nicht gezählt wird, entstehen kleine Umsatzdifferenzen im Bereich „Werkstatt“.

---

## 7. Übersicht: Woher kommen die Werte?

| Kennzahl | DRIVE (Portal) | Reporting (E-Mail/PDF) |
|----------|----------------|------------------------|
| Umsatz/Einsatz/DB1 Gesamt | Eigene SQL-Aggregation in `api_tek()` (controlling_routes), dann totals + 6-8932 + 9-Andere | `get_tek_data()` (controlling_data): 5 Bereiche + 9-Andere + Clean Park (mit Doppelzählung 847301/747301) |
| 4-Lohn Einsatz | FIBU (74xxxx) inkl. 747301 | Laufender Monat: kalkulatorisch (6-M-Quote); sonst FIBU ohne 747301 + CP separat |
| Prognose / Breakeven | `berechne_breakeven_prognose(..., total_db1, ...)` mit Portal-total_db1 | Aus get_tek_data (intern gleiche Funktion, aber mit get_tek_data-total_db1) |
| Stückzahlen | Aus Route (get_stueckzahlen_locosoft im Kontext api_tek) | tek_api_helper: get_tek_data_core + get_stueckzahlen_locosoft separat |
| Werktage / „Noch X WT“ | Wie Report (get_werktage_monat mit Stichtag) | Aus get_tek_data / gleiche SSOT |

---

## 8. Empfohlene nächste Schritte (für spätere Umsetzung)

1. **Eine SSOT für Gesamt-Umsatz/Einsatz/DB1:** Entweder  
   - die Portal-Route stellt ihre Aggregation um auf einen gemeinsamen Datenlayer (z. B. get_tek_data), oder  
   - get_tek_data wird so angepasst, dass es **dieselbe** Logik wie die Route verwendet (4-Lohn inkl. 847301/747301, 6-8932 separat, **keine** Doppelzählung Clean Park).
2. **Clean Park in get_tek_data:** Doppelzählung entfernen (9-Andere entweder ohne 847301/747301 definieren oder Clean-Park-Beträge nicht zusätzlich zu 9-Andere addieren).
3. **4-Lohn = rollierender Schnitt (bereits vereinbart):** SSOT ist get_tek_data. Portal darf nicht abweichen – muss get_tek_data für alle TEK-KPIs nutzen statt eigener Aggregation.
4. **Stückzahlen:** Einmal abgleichen mit gleichen Parametern (von, bis, firma, standort) und gleichem Stichtag; ggf. Stückzahlen nur aus einer Quelle (get_tek_data oder Route) beziehen.

Keine Code-Änderung im Rahmen dieser Analyse – nur Bestandsaufnahme und Ursachenanalyse.

---

## 9. Abweichungen TEK E-Mail vs. Portal – Stand nach SSOT (2026-02-19)

**Nach der SSOT-Umsetzung** (Portal bezieht alle TEK-KPIs aus `get_tek_data`) gelten folgende **verbleibenden Ursachen** für Abweichungen zwischen E-Mail-Report und Portal:

| Ursache | Erklärung | Maßnahme |
|--------|------------|----------|
| **GESAMT-Zeile in der E-Mail-Tabelle** | Die E-Mail-Tabelle bildete die GESAMT-Zeile als **Summe der 5 Bereiche**. Das Gesamt aus `get_tek_data` enthält zusätzlich **9-Andere** und **Clean Park** (847301/747301). Dadurch wich DB1/Umsatz/Marge in der E-Mail-GESAMT-Zeile vom Portal ab. | **Behoben (2026-02-19):** E-Mail verwendet für die Monatsspalten der GESAMT-Zeile nun `data.gesamt` (Umsatz, DB1, Marge) – identisch mit Portal. |
| **Stückzahlen (z. B. 70 vs. 73)** | E-Mail wird um **19:30 Uhr** (nach Locosoft-Mirror) versendet; das Portal wird zu einem **anderen Zeitpunkt** aufgerufen. Locosoft-Stückzahlen (dealer_vehicles, fakturierte Auslieferungen) können sich je nach Stichtag/Spätbuchungen unterscheiden. | Keine technische Abweichung – reiner **Zeitpunktunterschied**. |
| **„Heute“-Daten (Tageswerte)** | Der E-Mail-Helper (`tek_api_helper`) holt Heute-Umsatz/Einsatz aus **Locosoft** (`journal_accountings`) mit eigenem Filter (ohne G&V-Filter, Konten 800000–899999). Das Portal nutzt `loco_journal_accountings` mit G&V-Filter und 8932. | Kleine Abweichungen bei den **Tageswerten** (Heute-Spalte) möglich; Monats- und Gesamtwerte sind über get_tek_data identisch. |
| **Prognose / Breakeven** | Beide nutzen dieselbe SSOT (`berechne_breakeven_prognose` in get_tek_data). Abweichungen entstehen nur noch, wenn **unterschiedlicher Aufrufzeitpunkt** (z. B. anderer Werktage-Stichtag vor/nach 19:00) oder anderer Monats-DB1 (z. B. durch Stückzahl-/Zeitdifferenz) vorliegt. | Konsistent, sofern gleicher Datenstand. |
