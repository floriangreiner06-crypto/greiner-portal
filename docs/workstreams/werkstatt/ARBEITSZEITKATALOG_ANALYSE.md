# Greiner-Arbeitszeitenkatalog — Analyse & Konzept

**Stand:** 2026-02-12  
**Workstream:** Werkstatt  
**Zweck:** Datengrundlage und Konzept für einen betriebseigenen Arbeitszeitenkatalog auf Basis echter Werkstattzeiten (IST) statt nur Hersteller-Vorgabezeiten (AW).

---

## 1. Hintergrund und Ziele

Die **Hersteller-Vorgabezeiten (AW)** aus Stellantis ServiceBox und Hyundai-Arbeitszeitkatalogen sind für den Betrieb häufig nicht realistisch. Locosoft bietet eigene Reparaturpakete an, deren manuelle Pflege jedoch sehr aufwendig ist. Ziel ist ein **datengetriebener „Greiner-Arbeitszeitenkatalog“**, der auf echten Werkstattzeiten basiert und im DRIVE-Portal administrativ verwaltbar ist.

**Datenquellen (Locosoft-Portal-Spiegel / Locosoft PostgreSQL):**

| Quelle | Inhalt |
|--------|--------|
| **labours** (bzw. loco_labours) | Arbeitspositionen: labour_operation_id, time_units (Vorgabe-AW), charge_type, text_line, mechanic_no |
| **times** (bzw. loco_times) | Stempelzeiten: order_number, order_position, order_position_line, start_time, end_time, duration_minutes, employee_number |
| **orders** (bzw. loco_orders) | Aufträge: order_type, subsidiary, vehicle_id |
| **dealer_vehicles / vehicles** | Fahrzeugdaten, Marke/Modell |

*Hinweis: Stempelzeiten liegen in der Portal-DB als `loco_times` (Spiegel von Locosoft); die Verknüpfung labours ↔ times erfolgt über order_number + order_position (ggf. order_position_line).*

---

## 2. Bestandsaufnahme Locosoft (labours)

### 2.1 Übersicht

| Kennzahl | Wert |
|----------|------|
| **Gesamtanzahl labours** | 298.722 |
| **Unterschiedliche labour_operation_id** | 4.729 |
| **Positionen mit Arbeitsnummer** (labour_operation_id gesetzt) | 103.469 |
| **Positionen nur Freitext** (ohne Arbeitsnummer) | 195.253 |

Etwa **35 %** der Positionen haben eine Hersteller-Arbeitsnummer, **65 %** sind reine Freitext-Positionen.

### 2.2 Top-50 Arbeitsnummern (nach Häufigkeit)

Sortiert nach Anzahl Vorkommen, mit durchschnittlicher Vorgabe-AW und einem Freitext-Beispiel.

| # | labour_operation_id | Anzahl | Ø Vorgabe-AW | Freitext-Beispiel |
|---|---------------------|--------|--------------|-------------------|
| 1 | (leer/N) | 9.721 | 0,00 | Überprüfung auf Nacharbeiten / Kampagnen |
| 2 | RDKS | 4.922 | 0,00 | Reifenüberwachungssystem leuchtet |
| 3 | 93830000 | 2.636 | 9,98 | Systematische Wartungsarbeiten |
| 4 | INSP | 2.448 | 14,21 | Zwischeninspektion |
| 5 | 49450907 | 2.253 | 1,17 | Replace: Pollen Filter (Maintenance) |
| 6 | RWW | 2.169 | 0,01 | Winterräder neu montieren |
| 7 | SLM | 1.840 | 4,56 | Zwischenölwechsel durchführen |
| 8 | D | 1.725 | 3,15 | Zieht Update während der Fahrt |
| 9 | DES1 | 1.715 | 1,60 | Desinfektion Pollenfilterkasten airco |
| 10 | 0600933 | 1.552 | 1,63 | Motorölwechsel |
| 11 | 6 | 1.371 | 4,31 | Vorführung zur Abgas-Untersuchung o.B. |
| 12 | RWS | 1.363 | 0,01 | Sommerräder wechseln |
| 13 | 0600943011 | 1.345 | 3,10 | Bremsflüssigkeitswechsel Batterien |
| 14 | RW | 1.260 | 0,29 | Winterräder mont. |
| 15 | ABL | 1.256 | 0,00 | Ablieferungs-Check durchführen |
| 16 | 25022707 | 1.153 | 0,33 | ENTLEERT U BEFUELLT BREMSKREISLAUF |
| 17 | 0600933075 | 1.073 | 0,01 | Scheinwerfer, Prüfung und Einstellung |
| 18 | RWI | 965 | 0,01 | Winterräder von Altfahrzeug montieren |
| 19 | ZULNW | 961 | 0,00 | Zulassungsgebühren |
| 20 | 0600943 | 858 | 1,87 | Motorölwechsel |
| 21 | 0 | 847 | 4,83 | 107 Punkte Check Spoticar |
| 22 | LICHT | 841 | 2,00 | Nebelscheinwerfer eingestellt |
| 23 | BGV D 29 | 744 | 4,99 | UVV durchführen vom Kunden gewünscht |
| 24 | ARBEITSAUFWAND | 744 | 4,48 | Zusatzarbeit Zierleiste Stoßfänger |
| 25 | 0600953 | 743 | 2,11 | Ölwechsel durchführen |
| 26 | 99T1CA10 | 731 | 4,69 | Vorgang 1 (Software-Update) |
| 27 | ZI | 648 | 5,01 | Zwischenölwechsel durchführen |
| 28 | 99P1CA10 | 637 | 5,03 | Vordere Querlenkerbuchsen Austausch |
| 29 | 6430300 | 620 | 1,00 | Transmitter-Batterie - Austausch |
| 30 | W | 620 | 0,89 | Fahrzeug Oberwäsche ohne Berechnung |
| 31 | ZULGW | 614 | 0,14 | Zulassungsservice Vivaro |
| 32 | 6I | 598 | 0,01 | Vorführung zur Abgas-Untersuchung (AU)+ |
| 33 | 14030907 | 583 | 1,14 | Replace: Air Filter Element |
| 34 | 4062710 | 517 | 4,87 | Keilrippenriemen ersetzen |
| 35 | 202 | 527 | 4,01 | Vorführung zur Abgas-Untersuchung (AU) |
| 36 | 0600953052 | 523 | 2,44 | Zündkerzen ersetzen * Luftfilter |
| 37 | W1 | 565 | 0,98 | Innenreinigung |
| 38 | 05PH0507 | 431 | 0,66 | PH Kühlflüssigkeit geprüft Wartung |
| 39 | LEASING | 457 | 0,00 | Im Gesamtentgelt enthalten |
| 40 | SP2020 | 438 | -36,32 | 6er Spardepot |
| 41 | MONTI | 405 | 8,90 | Winterreifen montieren |
| 42 | L | 393 | 1,98 | Scheinwerfer Einstellung prüfen |
| 43 | ZAWEB | 342 | 7,42 | Wechsel eCall-Systembatterie Notruf |
| 44 | ZAWEB | 342 | 7,42 | Wechsel eCall-Systembatterie |
| 45 | BE | 329 | 3,07 | Zubehör Batterie ersetzen |
| 46 | NAVI | 296 | 0,14 | Navi Update |
| 47 | BP | 284 | 0,46 | Batterie und Ladesystem prüfen i.O. |
| … | … | … | … | … |

*(Auszug; vollständige Top-50 aus Abfrage vom 2026-02-12.)*

---

## 3. IST-Zeiten-Analyse (Vorgabe vs. Stempelzeit)

Verknüpfung: **loco_labours** mit **loco_times** über order_number + order_position (ggf. order_position_line). Nur Positionen mit mind. 10 Stempelzeiten; type=2 (Leistung), end_time und duration_minutes gesetzt.

### 3.1 Kennzahlen

- **Stempelzeiten mit Position:** ~171.655 (loco_times, type=2, order_position gesetzt)
- **Labour-Positionen:** ~298.583 (loco_labours im Portal-Spiegel)

### 3.2 Top-50 Arbeitsnummern: Hersteller-AW vs. Ø IST-Stempelzeit (Minuten) und Abweichung %

Negative Abweichung = IST kürzer als Vorgabe (Arbeit schneller erledigt), positive = länger.

| labour_operation_id | N (Positionen) | Ø Vorgabe-AW | Ø IST (Min) | Abweichung % |
|---------------------|----------------|--------------|-------------|--------------|
| 93830000 | 2.513 | 10,00 | 92,6 | -84,6 % |
| INSP | 2.309 | 14,21 | 85,5 | -90,0 % |
| 49450907 | 2.140 | 1,18 | 93,3 | +31,8 % |
| DES1 | 1.507 | 1,68 | 97,8 | -3,0 % |
| 0600943011 | 1.291 | 3,10 | 117,1 | -37,0 % |
| 6 | 1.213 | 4,31 | 94,1 | -63,6 % |
| SLM | 1.196 | 5,80 | 109,1 | -68,6 % |
| 0 | 776 | 4,99 | 72,7 | -75,7 % |
| LICHT | 769 | 2,00 | 47,9 | -60,1 % |
| 99T1CA10 | 635 | 4,81 | 84,7 | -70,7 % |
| D | 630 | 7,67 | 146,3 | -68,2 % |
| ZI | 614 | 5,01 | 70,5 | -76,5 % |
| 6430300 | 590 | 1,00 | 116,6 | **+94,3 %** |
| 99P1CA10 | 552 | 5,22 | 82,3 | -73,7 % |
| 14030907 | 540 | 1,16 | 131,5 | **+88,9 %** |
| 4062710 | 499 | 4,88 | 150,5 | -48,6 % |
| 0600953052 | 491 | 2,45 | 114,1 | -22,4 % |
| BGV D 29 | 484 | 5,00 | 118,8 | -60,4 % |
| LS | 436 | 2,00 | 73,7 | -38,6 % |
| W1 | 398 | 1,00 | 81,4 | **+35,7 %** |
| 05PH0507 | 394 | 0,67 | 129,8 | **+222,9 %** |
| MONTI | 376 | 8,91 | 105,5 | -80,3 % |
| 06250907 | 352 | 1,24 | 109,9 | **+47,7 %** |
| ZAWEB | 325 | 7,59 | 109,2 | -76,0 % |
| 202 | 300 | 4,02 | 66,2 | -72,6 % |
| W | 297 | 1,00 | 87,5 | **+45,8 %** |
| 0B | 259 | 5,01 | 71,0 | -76,4 % |
| L | 252 | 2,01 | 64,0 | -46,9 % |
| SP | 251 | 5,05 | 46,7 | -84,6 % |
| 9141316 | 241 | 2,00 | 14,8 | -87,7 % |
| GW00000 | 238 | 5,00 | 75,7 | -74,8 % |
| 0600933 | 235 | 9,20 | 90,0 | -83,7 % |
| S | 232 | 4,99 | 70,4 | -76,5 % |
| 99P00510 | 218 | 1,95 | 94,6 | -19,1 % |
| 0602183011 | 213 | 3,00 | 136,4 | -24,2 % |
| MONT | 212 | 9,29 | 100,9 | -81,9 % |
| MDI | 210 | 6,17 | 152,2 | -58,9 % |
| BE | 197 | 3,09 | 53,4 | -71,2 % |
| 15500907 | 193 | 2,94 | 165,8 | -6,0 % |
| 520A0507 | 178 | 1,01 | 115,3 | **+90,3 %** |
| 996 | 177 | 8,22 | 141,5 | -71,3 % |
| 40DC18R0 | 173 | 3,00 | 29,0 | -83,9 % |
| BASICA00 | 167 | 1,01 | 133,8 | **+120,8 %** |
| 0800351 | 158 | 4,57 | 88,6 | -67,7 % |
| 2420150 | 157 | 6,59 | 141,7 | -64,2 % |
| 0600913 | 154 | 4,03 | 76,2 | -68,5 % |
| RAD2 | 154 | 7,37 | 81,3 | -81,6 % |
| 0600913003 | 152 | 4,01 | 76,3 | -68,3 % |
| 93840000 | 140 | 5,00 | 38,6 | -87,1 % |
| 40D240R0 | 138 | 7,00 | 64,1 | -84,7 % |

### 3.3 Interpretation

- **Systematisch kürzer als Vorgabe (realistisch schneller):** z. B. 93830000 (Systematische Wartung), INSP (Inspektion), SLM/ZI (Ölwechsel), MONTI/MONT (Reifenmontage), RAD2, 0, 202, SP, LICHT – Hersteller-AW oft deutlich höher als die gemessene Stempelzeit.
- **Systematisch länger als Vorgabe:** z. B. 6430300 (Transmitter-Batterie), 14030907 (Luftfilter), 05PH0507 (Kühlflüssigkeit), W1/W (Oberwäsche/Innenreinigung), 520A0507 (Scheinwerfer), BASICA00 (GDS-Grundprüfung) – hier wäre eine **höhere Greiner-AW** sinnvoll.

---

## 4. Freitext-Clustering (Positionen ohne labour_operation_id)

Für Positionen **ohne** labour_operation_id wurde text_line ausgewertet (Muster = linke 45 Zeichen), mind. 5 Vorkommen pro Muster. Top-30 nach Häufigkeit, mit Ø IST-Zeit (Minuten).

| Muster (Auszug) | Anzahl | Ø IST (Min) |
|-----------------|--------|-------------|
| vom Fahrzeughersteller | 10.043 | 260,8 |
| Berechnung | 4.912 | 281,0 |
| NACH 50 KM NACHZIEHEN LASSEN | 3.586 | 245,8 |
| Jahre(n) | 2.411 | 326,1 |
| Fahrzeugpreis ohne Mehrwertsteuer | 2.410 | 64,8 |
| NACH 50 BIS 100 KM NACHZIEHEN LASSEN | 2.123 | 280,3 |
| WARTUNGEN: SYSTEMATISCHE ARBEITEN | 1.983 | 246,5 |
| Org. Fzg. Grp.: Kleinwagen | 1.908 | 1.357,3 |
| AUSTAUSCH DES INNENRAUMFILTERS | 1.629 | 197,5 |
| Werkstattersatz - Inspektionstarif | 1.398 | 90,8 |
| Kilometer inklusive: 100 km | 1.320 | 111,4 |
| Bremsflüssigkeit, Wechseln | 1.295 | 220,7 |
| WARTUNG | 1.101 | 308,3 |
| (inkl. Zusatzscheinwerfer) | 1.027 | 276,5 |
| Diagnoseblatt erforderlich | 975 | 623,2 |
| einstellen | 902 | 285,0 |
| Scheinwerfereinstellung, Prüfen und | 894 | 284,4 |
| Berechnete Grp.: Kleinwagen | 837 | 2.926,7 |
| WECHSEL DER BREMSFLÜSSIGKEIT | 836 | 263,5 |
| Berechnete Grp.: Kleinwagen (3) | 774 | 208,0 |
| Org. Fzg. Grp.: Kompaktwagen | 730 | 87,0 |
| ./. Nachlass | 715 | – |
| Fahrzeugpreis | 645 | 318,5 |
| FAHRZEUG | 627 | 510,3 |
| intern | 614 | 275,5 |
| Batterien (Schlüsselgriff), Wechseln | 606 | 298,7 |
| Dokumentation auf | 574 | 590,5 |
| Verhalten) | 559 | 1.122,5 |
| Greiner - Kleinwagen (2) | 555 | 55,0 |
| AM FAHRZEUG | 548 | 287,3 |

**Wiederkehrende inhaltliche Muster:** Öl-/Filter-/Bremsflüssigkeit, Innenraumfilter, Scheinwerfer, Wartung/Inspektion, Nachziehen, Berechnungs-/Fahrzeuggruppen-Texte, Dokumentation/Diagnose. Ein Teil der Freitexte sind keine reinen Arbeitsbeschreibungen (z. B. Preise, Gruppen), für den Katalog sind vor allem Muster wie „Bremsflüssigkeit wechseln“, „Innenraumfilter austauschen“, „Scheinwerfereinstellung“ relevant.

---

## 5. Marken-/Standort-Unterschiede (Opel vs. Hyundai)

Vergleich **Opel (subsidiary 1+2)** vs. **Hyundai (subsidiary 3)** für Arbeitsnummern mit je mind. 20 Vorkommen pro Standort. Angezeigt: Arbeitsnummer, Ø IST Opel (Min), Ø IST Hyundai (Min), Differenz (Min), Differenz (%).

| labour_operation_id | Ø IST Opel (Min) | Ø IST Hyundai (Min) | Diff. (Min) | Diff. (%) |
|---------------------|------------------|---------------------|------------|-----------|
| 9D047210 | 1.129,9 | 417,3 | -712,6 | -63,1 % |
| 4032750 | 959,4 | 396,0 | -563,4 | -58,7 % |
| 2420170 | 677,5 | 217,3 | -460,2 | -67,9 % |
| 9141275 | 727,5 | 279,0 | -448,5 | -61,6 % |
| SLM | 522,1 | 121,7 | -400,4 | -76,7 % |
| BGV D 29 | 493,5 | 116,7 | -376,8 | -76,4 % |
| W | 496,9 | 135,8 | -361,1 | -72,7 % |
| 9141256 | 631,8 | 279,0 | -352,8 | -55,8 % |
| 9140962 | 615,1 | 279,0 | -336,1 | -54,6 % |
| RAD2 | 472,7 | 175,1 | -297,6 | -63,0 % |
| MONT | 641,1 | 372,3 | -268,8 | -41,9 % |
| BP | 459,5 | 196,6 | -262,9 | -57,2 % |
| 4025942 | 724,5 | 986,6 | **+262,1** | **+36,2 %** |
| 99P1CA10 | 159,9 | 416,8 | **+256,9** | **+160,7 %** |
| 99P2CA10 | 300,7 | 536,4 | **+235,7** | **+78,4 %** |
| 4064070 | 1.065,6 | 1.295,4 | **+229,8** | **+21,6 %** |
| 0800351 | 355,6 | 134,7 | -220,9 | -62,1 % |
| 25022707 | 318,1 | 509,5 | **+191,4** | **+60,2 %** |
| 99P00510 | 176,0 | 370,1 | **+194,1** | **+110,3 %** |

**Fazit:** Bei vielen Nummern ist die IST-Zeit bei **Opel (DEG)** deutlich höher als bei **Hyundai (LAN)** (z. B. Diagnose/Fehlersuche 9D047210, Wasserpumpe 4032750, Bremsen 2420170, SLM, BGV D 29, W, RAD2, MONT, BP). Umgekehrt sind bei einigen Arbeiten (4025942, 99P1CA10, 99P2CA10, 4064070, 25022707, 99P00510) die Zeiten in Landau höher. Ein **Greiner-Katalog** kann optional **standortabhängige AW** vorsehen (z. B. DEG vs. LAN).

---

## 6. Reparaturpakete-Struktur in Locosoft

In der Locosoft-Datenbank (loco_auswertung_db) gibt es **keine** eigenen Tabellen mit Namen wie „package“, „standard“, „template“, „catalogue“ oder „catalog“ für Reparaturpakete oder Standardarbeiten.

**Relevante Strukturen:**

| Tabelle | Zweck |
|---------|--------|
| **labours** | Einzelne Arbeitspositionen je Auftrag (order_number, order_position, labour_operation_id, time_units, text_line). |
| **labours_master** | Stammdaten zu Arbeitsnummern: source_number, labour_number, mapping_code, text, source. Verknüpfung Hersteller-/Hyundai-Codes mit Beschreibungstext. |
| **labours_groups** | Gruppierung von Arbeitsnummern: source_number, labour_number_range, description, source. Keine Paket-Logik im Sinne vordefinierter Reparaturpakete. |

**Fazit:** Eigene „Reparaturpakete“ oder ein betrieblicher Standardarbeitskatalog sind in Locosoft nicht als eigene Entität abgebildet. Sie müssten **außerhalb** (z. B. im DRIVE-Portal) geführt und mit labour_operation_id bzw. text_line gemappt werden.

---

## 7. Greiner-Standardarbeiten – Top-100 Vorschlag

Empfohlene Standardarbeiten mit **realistischer Greiner-AW** aus IST-Daten (Stempelzeiten), Hersteller-AW, Abweichung und Häufigkeit. Standort-Differenzen siehe Abschnitt 5.

### 7.1 Feedback Serviceleiter (erster Eindruck)

**Hinweis:** Die Spalte „Greiner-AW (Std)“ in der folgenden Tabelle ist ein **datengetriebener Vorschlag** (Mittelwert aus Stempelzeiten), kein verbindlicher Katalogwert. Die Werkstattleitung prüft und entscheidet.

- **Beobachtung:** Überwiegend liegen die vorgeschlagenen Zeiten **unter** der Hersteller-Vorgabe.
- **Vermutung:** Die Berechnung kann verzerrt sein, weil Mechaniker **nicht bei jedem Wechsel umstempeln** – insbesondere bei **Inspektionen** (eine Stempelung für mehrere Positionen bzw. Inspektion + Zusatzarbeiten).
- **Folge:** IST-Zeiten pro Position können **zu niedrig** ausgewertet werden; die „Greiner-AW“ aus reiner IST-Mittelwertbildung wäre dann zu knapp.

**Vorgeschlagene Anpassungsregeln (Serviceleiter):**

| Konstellation | Regel |
|---------------|--------|
| **Ungerade Inspektionen** (1., 3., 5. … Jahr) oder **Zwischeninspektion** | **+1 AW** zur Hersteller-Vorgabezeit |
| **Gerade Inspektionen** (2., 4., 6. … Jahr) | **+2 AW** zur Hersteller-Vorgabezeit |
| **Zusatzarbeiten** (z. B. Zündkerzen 06250907, Luftfilter, Bremsflüssigkeit etc.) | **+1 AW** pro Zusatzarbeit; prüfen, ob hohe Abweichung (z. B. +285 %) mit **Fehl- oder Nicht-Umstempelung** zusammenhängt |

Diese Regeln sind als **betriebliche Vorgabe** zu verstehen und sollten bei der Definition des Greiner-Katalogs (und ggf. im DRIVE-Modul) berücksichtigt werden. Zusatzarbeiten mit sehr hoher IST-Abweichung (z. B. 06250907 Zündkerzen) sollten vor Übernahme in den Katalog auf Stempelverhalten geprüft werden.

### 7.2 Alternative: Katalog mit Referenz statt nur Pauschale

Die Pauschalen (+1/+2 AW) sind einfach umsetzbar, aber **statisch** und ohne Bezug zu echten Auftragskombinationen. Ein Katalog mit **mehr Referenz** und **mehr als nur pauschaler Aufschlag** könnte so aussehen:

**1. Referenz pro Position (Transparenz)**  
Jede Katalogzeile führt nicht nur „Greiner-AW“, sondern **Referenzdaten** mit:
- **N** = Anzahl Aufträge/Positionen, auf denen die AW basiert
- **Streuung** (z. B. Standardabweichung oder Perzentile 25/75) der IST-Zeiten
- **Kontext-Anteil:** z. B. „80 % der Fälle im gleichen Auftrag wie INSP/93830000“ (Inspektionskontext)

Damit sieht der Werkstattleiter sofort: „Diese AW stammt aus 353 Fällen, Streuung hoch, oft zusammen mit Inspektion → ggf. manuell prüfen.“ Statt blind +1 AW liefert der Katalog **nachvollziehbare Referenz**.

**2. Kontextabhängige AW (nicht nur eine Zahl)**  
Statt **einer** Greiner-AW pro Arbeitsnummer zwei (oder mehr) Werte:
- **AW „allein“:** nur Aufträge, in denen diese Position die einzige bzw. dominante Arbeit ist (wenige Positionen pro Auftrag)
- **AW „im Inspektionskontext“:** Aufträge, in denen gleichzeitig Inspektion (INSP, 93830000, ZI …) vorkommt

Beispiel: Zündkerzen 06250907 → 1,2 AW „allein“, 0,8 AW „zusätzlich bei Inspektion“ (weil Rüstzeit schon abgegolten). So wird der Aufschlag **datengetrieben** aus echten Kombinationen berechnet, nicht pauschal +1 AW.

**3. Kombinations- / Paket-AW aus echten Aufträgen**  
Häufige **Kombinationen** (z. B. INSP + Zündkerzen + Bremsflüssigkeit) pro Auftrag auswerten:
- Gesamt-IST des Auftrags erfassen
- Pro Kombination einen **Paket-AW** berechnen (z. B. „Inspektion gerade + Zündkerzen = 8,5 AW“ aus Mittelwert aller solcher Aufträge)
- Im Katalog: neben Einzelpositionen auch **Referenzpakete** mit eigener AW und N

Damit entstehen **mehrere Referenzebenen**: Einzelarbeit, Kontext „mit Inspektion“, und konkrete Pakete. Angebote können wahlweise Einzel-AW oder Paket-AW nutzen.

**4. Pauschale nur als Fallback**  
- Wenn **N ≥ Schwellwert** (z. B. 30) und Streuung vertretbar: **Greiner-AW aus IST** (ggf. kontextabhängig) nutzen.
- Wenn **N zu klein** oder Streuung sehr hoch: **Fallback** auf Hersteller + Pauschale (+1/+2 AW wie Serviceleiter-Vorschlag) oder manuelle Festlegung.

**Umsetzung (stufig denkbar):**  
- **Phase 1:** Katalog wie bisher, aber mit Spalten N, Streuung, „Anteil im Inspektionskontext“ (nur Anzeige, mehr Referenz).  
- **Phase 2:** Kontext „allein“ vs. „mit Inspektion“ auswerten, zwei AW pro Position speichern und in Angebot/Planung nutzbar machen.  
- **Phase 3:** Häufige Kombinationen identifizieren, Paket-AW berechnen und als zusätzliche Katalogreferenz anbieten.

*(Auszug Top-50; vollständige Top-100 aus Analyse 2026-02-12.)*

| Arbeitsnr. | Beschreibung | Hersteller-AW | Greiner-AW (Std) | Abweichung % | Häufigkeit/Jahr (N) |
|------------|--------------|---------------|-------------------|--------------|----------------------|
| 93830000 | Systematische Wartungsarbeiten | 10,00 | 3,79 | -62,1 % | 2.519 |
| INSP | Wartung 36 Monate / 45.000 km | 14,21 | 4,37 | -69,3 % | 2.312 |
| 49450907 | Replace: Pollen Filter (Maintenance) | 1,18 | 3,72 | +216,3 % | 2.153 |
| DES1 | Desinfektion Pollenfilterkasten | 1,69 | 5,39 | +218,8 % | 1.530 |
| SLM | Zwischenölwechsel durchführen | 5,88 | 5,59 | -5,0 % | 1.329 |
| 0600943011 | Bremsflüssigkeitswechsel Batterien | 3,10 | 3,63 | +17,2 % | 1.293 |
| 6 | Vorführung zur Abgas-Untersuchung o.B. | 4,31 | 3,49 | -19,0 % | 1.222 |
| LICHT | Nebelscheinwerfer eingestellt | 2,00 | 3,41 | +70,4 % | 820 |
| 0 | 107 Punkte Check Spoticar | 4,99 | 2,48 | -50,3 % | 783 |
| D | Zieht Update während der Fahrt | 7,59 | 8,57 | +12,8 % | 653 |
| 99T1CA10 | Vorgang 1 (Software-Update) | 4,80 | 3,56 | -25,8 % | 648 |
| ZI | Zwischenölwechsel durchführen | 5,01 | 3,79 | -24,4 % | 615 |
| 6430300 | Transmitter-Batterie - Austausch | 1,00 | 5,02 | +401,4 % | 593 |
| 99P1CA10 | Vordere Querlenkerbuchsen Austausch | 5,17 | 4,08 | -21,0 % | 568 |
| 14030907 | Luftfilter ersetzen | 1,16 | 5,26 | +354,4 % | 541 |
| BGV D 29 | UVV durchführen vom Kunden gewünscht | 5,00 | 7,29 | +45,8 % | 512 |
| 4062710 | Keilrippenriemen ersetzen | 4,88 | 5,09 | +4,4 % | 502 |
| 0600953052 | Zündkerzen ersetzen * Luftfilter | 2,45 | 7,64 | +212,2 % | 495 |
| W1 | Innenreinigung / Oberwäsche | 1,00 | 4,78 | +377,7 % | 461 |
| LS | Lackschichtmessung | 2,00 | 2,98 | +48,9 % | 440 |
| 05PH0507 | PH Kühlflüssigkeit geprüft Wartung | 0,67 | 5,20 | +675,4 % | 397 |
| MONTI | Winterreifen montieren | 8,89 | 8,08 | -9,2 % | 396 |
| 06250907 | Zündkerzen ersetzen | 1,24 | 4,77 | +285,6 % | 353 |
| W | Fahrzeug Oberwäsche ohne Berechnung | 1,00 | 4,31 | +331,0 % | 336 |
| L | Scheinwerfer Einstellung prüfen | 2,01 | 2,61 | +30,2 % | 330 |
| ZAWEB | Wechsel eCall-Systembatterie | 7,59 | 6,33 | -16,6 % | 328 |
| 202 | Vorführung zur Abgas-Untersuchung (AU) | 4,02 | 1,46 | -63,6 % | 305 |
| 0B | 107 Punkte Check Verbrenner/PHEV | 5,01 | 1,84 | -63,3 % | 259 |
| BE | Zubehör Batterie ersetzen | 3,10 | 3,62 | +17,0 % | 257 |
| SP | Sender programmieren | 5,05 | 1,33 | -73,6 % | 252 |
| … | … | … | … | … | … |

**Spalte „Standort-Differenz“:** Siehe Abschnitt 5; für ausgewählte Nummern kann eine separate DEG/LAN-AW hinterlegt werden.

---

## 8. DRIVE-Modul-Konzept: „Arbeitszeitenkatalog-Manager“

**Nur Skizze, kein Code.**

### 8.1 Ziele

- Zentrale Pflege des **Greiner-Arbeitszeitenkatalogs** (Arbeitsnummer, Beschreibung, Greiner-AW, optional Hersteller-AW, Standort).
- Nutzung in Angebots-/Auftragswesen (Locosoft/DRIVE) und für Kennzahlen (Vorgabe vs. IST).
- Workflow für Werkstattleiter: Vorschläge aus IST-Daten prüfen, freigeben, anpassen.

### 8.2 DB-Tabellen (Vorschlag, im Portal)

| Tabelle | Zweck |
|---------|--------|
| **arbeitszeitenkatalog** | Stammdaten: id, arbeitsnummer (PK/UK), beschreibung, hersteller_aw, greiner_aw, standort (NULL = alle, 1/2/3), quelle (hersteller/greiner), aktiv, created_at, updated_at. |
| **arbeitszeitenkatalog_historie** | Versionen: id, arbeitszeitenkatalog_id, greiner_aw_alt, greiner_aw_neu, geaendert_von, geaendert_am. |
| **arbeitszeitenkatalog_mapping** | Optional: Zuordnung labour_operation_id ↔ interne Katalog-ID, falls mehrere Hersteller-Codes auf eine Greiner-Standardarbeit abgebildet werden. |

### 8.3 Views / Oberflächen

1. **Katalog-Übersicht (Liste)**  
   Filter: Arbeitsnummer, Beschreibung, Standort, aktiv. Spalten: Arbeitsnummer, Beschreibung, Hersteller-AW, Greiner-AW, Standort, Letzte Aktualisierung. Aktionen: Bearbeiten, Deaktivieren.

2. **Detail/ Bearbeitung**  
   Eine Zeile: Arbeitsnummer, Beschreibung, Hersteller-AW, Greiner-AW, Standort, Quelle, Aktiv. Optional: Link zu „IST-Statistik“ (aus loco_labours/loco_times aggregiert).

3. **IST-Vorschläge („Auswertung“)**  
   Tabelle/Report aus Analyse wie in Abschnitt 3 und 7: Top-N nach Häufigkeit, Ø IST (Stunden), Abweichung zu Hersteller-AW. Aktion: „Als Greiner-AW übernehmen“ (fügt/aktualisiert arbeitszeitenkatalog).

4. **Freitext-Muster (optional)**  
   Auswertung wie Abschnitt 4: häufigste Freitexte ohne labour_operation_id. Aktion: „Neue Standardarbeit anlegen“ (Arbeitsnummer vergeben, Greiner-AW aus Ø IST).

### 8.4 Workflow Werkstattleiter

1. **Regelmäßig (z. B. monatlich):** Report „IST vs. Vorgabe“ ansehen, Abweichungen prüfen.
2. **Vorschläge:** System schlägt Greiner-AW aus Ø IST vor; Werkstattleiter bestätigt oder passt an.
3. **Freigabe:** Änderungen werden in **arbeitszeitenkatalog** übernommen, Historie wird geschrieben.
4. **Nutzung:** Andere Module (Angebot, Locosoft-Export, KPIs) lesen Greiner-AW aus dem Katalog (bei Fehlen Fallback auf Hersteller-AW).

### 8.5 Rechte und Navigation

- **Berechtigung:** z. B. Feature „arbeitszeitenkatalog“ für Rolle Werkstattleiter/Admin.
- **Navigation:** Unter **Service → Werkstatt → Arbeitszeitenkatalog** (oder „Werkstatt → Einstellungen → Arbeitszeitenkatalog“).

### 8.6 Technische Anbindung

- **Lesen:** API liefert Greiner-AW zu labour_operation_id (und optional standort).
- **Schreiben:** Nur über DRIVE-UI (Werkstattleiter); keine automatische Überschreibung durch Batch ohne Freigabe.
- **Sync Locosoft:** labours/labours_master bleiben unverändert; DRIVE-Katalog ist Zusatzschicht „Greiner-AW“.

---

## 9. Nächste Schritte (Empfehlung)

1. **Entscheidung Katalog-Ansatz:** Statische Pauschale (7.1) vs. referenzbasierter Katalog (7.2). Empfehlung: Katalog mit Referenz (N, Streuung, Kontext) und optional kontextabhängiger AW / Paket-AW; Pauschale nur als Fallback bei wenig Daten.
2. **Vorgaben Werkstattleitung:** Inspektions- und Zusatzarbeits-Regeln aus Abschnitt 7.1 im Katalog abbilden (als Mindestvorgabe oder Fallback).
3. **Priorisierung:** Top-20 bis Top-50 Standardarbeiten mit größter Abweichung und hoher Häufigkeit zuerst im Katalog abbilden.
4. **DB-Migration:** Tabellen arbeitszeitenkatalog (+ Historie, optional Mapping); bei referenzbasiertem Ansatz zusätzlich Felder N, Streuung, Kontext, ggf. Paket-Kombinationen.
5. **API + UI:** Minimales CRUD für Katalog, dann View „IST-Vorschläge“ und Workflow „Übernehmen“; bei 7.2 Anzeige Referenzdaten und kontextabhängige AW.
6. **Integration:** Anbindung an Angebots-/Auftragsprozess und an Kennzahlen (Vorgabe vs. IST) festlegen.
7. **Freitext:** Optionale Erweiterung um „Freitext-Muster → neue Standardarbeit“ und Mapping text_line → arbeitsnummer.

---

*Dokument Ende. Analyse basiert auf Locosoft labours (bzw. loco_labours) und Portal loco_times/loco_orders; Stand Daten 2026-02-12.*
