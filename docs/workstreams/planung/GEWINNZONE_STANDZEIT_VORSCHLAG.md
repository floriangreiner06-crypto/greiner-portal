# Gewinnzone: Was müssen wir planen? (Vorschlag)

**Stand:** Auswertung mit aktuellen Daten (Prognose Jahresende, Bereichspotenzial, Standzeit 300→150 Tage).

---

## 1. Wo stehen wir?

- **Prognose Jahresende** (ohne Standzeit-Effekt): Ergebnis negativ, Gap zu **Break-even (0 €)** und zum **1 %-Ziel (Gewinnzone)**.
- **Größtes Potenzial:** **Gebrauchtwagen (GW)** – Marge aktuell im Minus bzw. unter Ziel (Ziel 5 %). DB1-Potenzial bei Erreichen der Ziel-Marge am höchsten.
- **Standzeit:** Langsteher wurden abgebaut (hat einmalig Geld gekostet). Alle Fahrzeuge von **über 300 Standtagen auf 150 Tage** gebracht → **dauerhafte Zinskosten-Ersparnis** (Script berechnet sie aus den **gebuchten Zinskosten VJ** aus Locosoft/Portal, inkl. Zinsfreiheit; typ. Größenordnung siehe Script-Ausgabe, z. B. rund 25 % der VJ-Zinskosten).

---

## 2. Was müssen wir planen, um in die Gewinnzone zu kommen?

### 2.1 Break-even (0 €)

- Fehlbetrag zum Break-even = **Gap zu 0 €** (z. B. rund 570 k€, je nach Prognose).
- **Standzeit-Verbesserung** (300 → 150 Tage) reduziert den Fehlbetrag um die **Zinskosten-Ersparnis** (aus gebuchten Zinskosten VJ, inkl. Zinsfreiheit; siehe Script-Ausgabe).
- Rechnung: **Gap zu Break-even nach Standzeit = Gap zu 0 € minus Zinskosten-Ersparnis.**
- Wenn die Ersparnis den Gap übersteigt, reicht die Standzeit-Verbesserung rechnerisch bereits für **Break-even** (unter sonst gleichen Bedingungen).

### 2.2 1 %-Ziel (Gewinnzone)

- **Gap zum 1 %-Ziel** = Differenz zwischen prognostiziertem Ergebnis und 1 % vom (prognostizierten) Umsatz.
- **Nach Berücksichtigung der Standzeit-Ersparnis:**  
  **Gap zum 1 %-Ziel (reduziert) = Gap zum 1 %-Ziel minus Zinskosten-Ersparnis.**
- Den verbleibenden Gap müssen wir durch **DB1-Verbesserung und/oder Kostensenkung** schließen.

---

## 3. Welche Abteilung hat das größte Potenzial?

Die **Gap-Analyse** (Unternehmensplan) vergleicht IST-Marge mit **Ziel-Marge** pro Bereich und rechnet das in **DB1-Potenzial** um:

| Bereich    | typ. Ziel-Marge | Aussage |
|-----------|------------------|--------|
| **GW**    | 5 %              | Oft größtes Potenzial, wenn IST-Marge negativ oder sehr niedrig. |
| **NW**    | 8 %              | Bereits nahe Ziel → geringeres Potenzial als GW. |
| **Werkstatt** | 55 %         | Meist stabil; Potenzial über Stundensatz/Produktivität. |
| **Teile** | 28 %             | Lagerumschlag, Penner-Quote, Servicegrad. |
| **Sonstige** | 50 %           | Meist kleinerer Hebel. |

**Konkret:** In der aktuellen Auswertung liegt das **größte DB1-Potenzial bei GW**. Wenn die GW-Marge auf Zielniveau (z. B. 5 %) gebracht wird, bringt das die höchste DB1-Verbesserung. Zusätzlich: **Standzeit 300→150** ist bereits umgesetzt und liefert die Zinskosten-Ersparnis (kein weiterer Planungsschritt, aber in der Planung als „bereits wirksam“ berücksichtigen).

---

## 4. Standzeit-Verbesserung berücksichtigen / vergleichen

- **Vorher:** Langsteher, teils **über 300 Standtage** → hohe Zinskosten auf Lagerwert (5 % p.a. auf durchschnittlichen Bestand).
- **Nachher:** Ziel **150 Tage** für alle Fahrzeuge → Zinskosten halbieren sich (bei gleichem Lagerwert), bzw. Lagerwert sinkt mit kürzerer Standzeit zusätzlich.
- **Formel (Vereinfachung):**  
  Zinskosten ≈ Lagerwert × 5 % × (Standzeit / 365).  
  Ersparnis ≈ Zinskosten bei 300 Tagen − Zinskosten bei 150 Tagen.
- **In der Planung:**  
  - Die **Zinskosten-Ersparnis** (z. B. Script-Ausgabe in €/Jahr) als **dauerhafte Verbesserung** in der Ergebnisplanung abbilden (z. B. höheres DB2/Ergebnis oder geringere „Kosten“ Zinsen).  
  - **Vergleich:** Plan „ohne Standzeit-Effekt“ vs. Plan „mit Standzeit-Effekt“ (Break-even und 1 %-Ziel) – siehe Script-Ausgabe.
- **Standzeiten aus Locosoft:** Für Planung/Zinsen relevant sind die **Standzeiten des Bestands** (noch nicht verkaufte Fz, Stichtag): aus `dealer_vehicles` mit `out_invoice_date IS NULL`, Standzeit = Stichtag − Ankunft. Zusätzlich zeigt das Script **zum Vergleich** die Standzeiten der **verkauften** Fahrzeuge (VJ/Vor-VJ) – wie lange sie vor Verkauf lagen. Die Script-Ersparnis ist der **Vergleich 300 Tage vs. 150 Tage** (Szenario vorher/nachher), berechnet als Anteil der **gebuchten Zinskosten VJ** (Locosoft 895xxx/4982x oder Fallback: Fahrzeugfinanzierungen Portal, inkl. Zinsfreiheit).

---

## 5. Konkreter Vorschlag (Kurzfassung)

1. **Standzeit 150 Tage** als Standard in der Planung festhalten und die **Zinskosten-Ersparnis** (z. B. aus dem Script) in der Ergebnisprognose nutzen.
2. **Priorität Abteilung:** **GW** – Marge auf Ziel (z. B. 5 %) bringen; größtes DB1-Potenzial.
3. **Break-even:** Mit Standzeit-Ersparnis kann der Fehlbetrag zum Break-even bereits stark sinken oder (je nach Zahl) geschlossen werden; verbleibenden Rest über GW + ggf. Kosten/NW/Werkstatt abdecken.
4. **1 %-Ziel:** Verbleibenden **Gap zum 1 %-Ziel** nach Standzeit mit **DB1 (v. a. GW)** und ggf. **Kostensenkung** planerisch schließen.
5. **Langsteher-Abbau:** Einmalige Kosten abgeschlossen; laufende **Zinsersparnis** in allen künftigen Planungen und Forecasts berücksichtigen.

---

## 6. Zinskosten-Quelle (Locosoft / Portal)

- **Primär:** `loco_journal_accountings` – Konten **895xxx**, **4982x**; plus **in Locosoft belegte Konten** (Belastungen Stellantis Bank, Santander, Genobank): **890501, 891001, 891711, 891712, 896711, 896712**. Es zählt die SOLL-Seite (Aufwand). Gefunden mit Script `scripts/planung_finde_zinskosten_konten.py` (Suchbegriffe: santander, stellantis, genobank, genossenschaft, zins).
- **Fallback:** Wenn die Summe aus 895/4982/89x **0 €** ist, nutzt das Script **fahrzeugfinanzierungen**: `zinsen_letzte_periode` × 12 (inkl. Zinsfreiheit).
- **Hinweis:** 895xxx/4982x sind im Portal oft 0; bei euch liefert vor allem **890501** SOLL-Buchungen (Zinskosten). Die 820 k€ waren eine alte Schätzung (5 % Lagerwert); gebuchte Zinsen liegen typ. in einer anderen Größenordnung (z. B. 22 k€ aus 890501 oder 100–120 k€ aus Fahrzeugfinanzierungen-Hochrechnung).

---

## 7. Plan-Zinskosten (Annahme: 90 Tage unter Zins, 5 %, Wert ohne MwSt.)

Für die Planung wird eine **vereinheitlichte Annahme** genutzt:

- **Nach Zinsfreiheit** rechnen wir den **Gesamtbestand** mit **90 Tagen unter Zinsen** (pauschale Annahme).
- **Durchschnittlicher Zins** über alle Linien (Stellantis Bank, Santander, Genobank): **5 %** p.a.
- **Durchschnittlicher Fahrzeugwert** aus **Locosoft** (`dealer_vehicles`), **ohne MwSt.** (MwSt. wird nicht finanziert):  
  `COALESCE(in_acntg_cost_unit_new_vehicle, in_buy_list_price)` – i.d.R. bereits netto/Buchwert.

**Formel:**  
`Zinskosten_Plan = Lagerwert_netto_gesamt × (90 / 365) × 5 %`

- **Bestand:** Stichtag Locosoft, nur Fahrzeuge mit Wert > 0 (`out_invoice_date IS NULL`).
- Das Script gibt aus: Bestand NW/GW/gesamt, Ø Wert netto, Lagerwert netto gesamt, Zinskosten Plan/Jahr.

**Hinweis Datenqualität:** Wenn für Neuwagen in Locosoft `in_acntg_cost_unit_new_vehicle` / `in_buy_list_price` oft fehlen, liegt der NW-Ø-Wert unrealistisch niedrig; dann trägt vor allem der GW-Bestand zum Lagerwert bei. Bei Bedarf Pauschalwert für NW ergänzen oder Locosoft-Pflege prüfen.

---

## 8. Kritik am Ansatz und Gegenvorschläge

**Vorteile der Annahme (90 Tage, 5 %, Wert ohne MwSt.):**

- Einfach und nachvollziehbar; eine Zahl für die Planung.
- Wert ohne MwSt. passt zur Realität (Bank finanziert keine MwSt.).
- Ø-Zins 5 % ist ein runder, plausibler Mix aus verschiedenen Finanzierungslinien.

**Kritik / Schwächen:**

1. **90 Tage pauschal:** Unabhängig von tatsächlicher Standzeit des Bestands (Locosoft Stichtag: z. B. NW Ø 153, GW Ø 85 Tage) wird immer 90 Tage angenommen. Bei kürzerer Standzeit überschätzt man die Zinskosten, bei längerer unterschätzt man sie.
2. **Ein Zinssatz für alle:** Stellantis/Santander/Genobank haben unterschiedliche Konditionen; 5 % ist nur ein Durchschnitt.
3. **Stichtagsbestand:** Der Bestand schwankt; ein einzelner Stichtag kann verzerren (z. B. kurz nach Auslieferungswelle).
4. **NW-Werte in Locosoft:** Wenn Buchwerte für NW oft fehlen, ist der ermittelte Ø-Wert bzw. Lagerwert für NW unscharf.

**Gegenvorschläge (optional):**

- **Variante A (datengetriebener):** Statt 90 Tagen die **durchschnittliche Standzeit** des Bestands aus Locosoft nutzen (z. B. `AVG(CURRENT_DATE - in_arrival_date)` für Bestand) und davon z. B. **Zinsfreiheit 90 Tage abziehen** → „Tage unter Zins“ = max(0, Ø-Standzeit − 90). Dann: `Lagerwert × (Tage_unter_Zins / 365) × 5 %`.
- **Variante B (gebucht als Anker):** Plan-Zinskosten an die **gebuchten Zinskosten VJ** (oder Fahrzeugfinanzierungen-Hochrechnung) anbinden und die 90-Tage-Formel nur als **Plausi** oder für Szenarien („wenn Bestand/Standzeit so bleibt“) nutzen.
- **Variante C:** NW und GW getrennt planen (eigene Ø-Werte, ggf. eigene Zinsfreiheit/Tage unter Zins), wenn die Daten in Locosoft dafür ausreichend sind.

Aktuell bleibt die **einfache Annahme (90 Tage, 5 %, Wert ohne MwSt.)** im Script; die Varianten können bei Bedarf ergänzt werden.

---

## 9. Script (Ausführung)

```bash
cd /opt/greiner-portal
python3 scripts/planung_gewinnzone_standzeit_vorschlag.py
```

- Zeigt: Prognose Jahresende, Gap zu Break-even und 1 %-Ziel, Potenzial pro Abteilung, **Zinskosten VJ**, **Plan-Zinskosten** (90 Tage, 5 %, Ø-Wert ohne MwSt.), **Standzeiten belegt aus Locosoft** (historisch: verkaufte Fz VJ + Vor-VJ; aktueller Bestand: Stück + Ø Tage NW/GW), Ersparnis-Schätzung, Gap nach Standzeit-Effekt.
- Standzeiten: Quelle `dealer_vehicles` (Verkauf = out_invoice_date − Ankunft; Bestand = Stichtag − Ankunft). Zinskosten VJ: gebuchte Werte; Ersparnis = grob 25 % der VJ-Zinskosten bei Halbierung Standzeit.
