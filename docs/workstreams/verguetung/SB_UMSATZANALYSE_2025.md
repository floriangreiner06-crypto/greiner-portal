# Serviceberater-Umsatzanalyse 2025

**Erstellt:** 2026-02-13  
**Quelle:** Locosoft PostgreSQL (loco_auswertung_db), Abfragezeitraum 01.01.2025–31.12.2025  
**Zweck:** Ist-Daten für Prämiensystem Service-Bereich (Vergütung Workstream)

---

## 1. Methodik

- **Serviceberater-Zuordnung:** `orders.order_taking_employee_no` = `employees.employee_number` (Auftragsannahme = SB).
- **Lohnumsatz:** Summe `labours.net_price_in_order` für fakturierte Positionen (`is_invoiced = true`), Join über `orders.number` und `orders.subsidiary`.
- **Teileumsatz:** Summe `parts.sum` für fakturierte Positionen, gleicher Auftrags-Join.
- **Beträge:** Locosoft speichert in Euro (kein Cent-Faktor).
- **Garantie/Kulanz:** Mitgezählt (Arbeit wurde geleistet).

Die vier ausgewerteten Serviceberater:

| Name (Locosoft)     | employee_number | Standort(e) |
|---------------------|-----------------|-------------|
| Huber, Herbert     | 4000            | 1, 2 (DEG)  |
| Salmansberger, Valentin | 5009     | 1, 2 (DEG)  |
| Kraus, Andreas      | 4005            | 1, 2 (DEG)  |
| Keidl, Leonhard (Leo) | 4002          | 2, 3 (HYU, LAN) |

**Subsidiary:** 1 = Deggendorf Stellantis (DEG), 2 = Deggendorf Hyundai (HYU), 3 = Landau (LAN).

---

## 2. Jahresübersicht 2025 (Lohn + Teile)

| Serviceberater        | Lohnumsatz (€) | Teileumsatz (€) | **Gesamtumsatz (€)** | Aufträge (Lohn) | Verkaufte Stunden |
|-----------------------|----------------|-----------------|----------------------|----------------|-------------------|
| Herbert Huber         | 594 341,94     | 621 407,16      | **1 215 749,10**     | 2 298           | 3 945,0           |
| Andreas Kraus         | 465 252,26     | 464 992,50      | **930 244,76**       | 1 842           | 2 946,1           |
| Valentin Salmansberger| 468 325,68     | 434 700,55      | **903 026,23**       | 1 553           | 3 028,1           |
| Leo Keidl             | 279 469,93     | 459 304,36      | **738 774,29**       | 1 673           | 2 683,8           |

- **Aufträge:** Anzahl distinct Aufträge mit mindestens einer fakturierten Lohnposition.
- **Verkaufte Stunden:** Summe `labours.time_units` / 10 (Locosoft-Einheit 0,1 h).

### 2.1 Kennzahlen pro SB

| Serviceberater        | Ø Stunden/Auftrag | Ø Aufträge/Arbeitstag (~220 Tage) | Branchenrichtwert 800–1 000 k€ |
|-----------------------|-------------------|------------------------------------|--------------------------------|
| Herbert Huber         | 1,72 h            | 10,4                               | **Erreicht** (≈1,22 Mio €)    |
| Andreas Kraus         | 1,60 h            | 8,4                                | **Nahe** (≈930 k€)            |
| Valentin Salmansberger| 1,95 h            | 7,1                                | **Nahe** (≈903 k€)            |
| Leo Keidl             | 1,60 h            | 7,6                                | **Unter** (≈739 k€)            |

Branchenrichtwert: 800 000–1 000 000 €/Jahr pro Serviceberater (Lohn + Teile). Quelle: Prompt/CONTEXT Vergütung.

---

## 3. Aufschlüsselung nach Betrieb (Subsidiary)

| Serviceberater        | Betrieb | Lohn (€)    | Teile (€)   |
|-----------------------|---------|-------------|-------------|
| Herbert Huber         | 1 DEG   | 304 021,37  | 386 878,96  |
| Herbert Huber         | 2 HYU   | 290 320,57  | 234 528,20  |
| Valentin Salmansberger| 1 DEG   | 227 476,89  | 264 797,28  |
| Valentin Salmansberger| 2 HYU   | 240 848,79  | 169 903,27  |
| Andreas Kraus         | 1 DEG   | 257 193,27  | 278 631,15  |
| Andreas Kraus         | 2 HYU   | 208 058,99  | 186 361,35  |
| Leo Keidl             | 2 HYU   | 21 016,17   | 35 810,68   |
| Leo Keidl             | 3 LAN   | 258 453,76  | 423 493,68  |

Leo Keidl ist überwiegend in Landau (3) tätig, mit geringem Anteil Hyundai (2). Die übrigen drei SBs sind in Deggendorf (1 + 2) unterwegs.

---

## 4. Monatsweise Aufschlüsselung

### 4.1 Lohnumsatz (€) pro Monat

| SB / Monat | 2025-01 | 2025-02 | 2025-03 | 2025-04 | 2025-05 | 2025-06 | 2025-07 | 2025-08 | 2025-09 | 2025-10 | 2025-11 | 2025-12 |
|------------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
| Huber, Herbert | 57 021 | 43 730 | 33 354 | 100 627 | 49 817 | 40 348 | 46 237 | 27 888 | 68 363 | 51 919 | 48 508 | 26 529 |
| Keidl, Leonhard | 29 951 | 18 058 | 37 243 | 22 951 | 29 023 | 18 662 | 21 397 | 14 950 | 24 504 | 32 465 | 20 918 | 9 348 |
| Kraus, Andreas | 41 457 | 36 062 | 30 665 | 28 937 | 29 062 | 27 364 | 28 360 | 25 934 | 85 809 | 62 435 | 37 128 | 32 038 |
| Salmansberger, Valentin | 31 981 | 59 880 | 17 977 | 41 713 | 30 405 | 29 545 | 17 967 | 78 217 | 56 382 | 40 865 | 36 121 | 27 272 |

### 4.2 Teileumsatz (€) pro Monat

| SB / Monat | 2025-01 | 2025-02 | 2025-03 | 2025-04 | 2025-05 | 2025-06 | 2025-07 | 2025-08 | 2025-09 | 2025-10 | 2025-11 | 2025-12 |
|------------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
| Huber, Herbert | 58 289 | 57 552 | 44 261 | 37 238 | 59 633 | 39 342 | 46 125 | 61 612 | 75 020 | 57 474 | 55 228 | 29 633 |
| Keidl, Leonhard | 47 257 | 27 251 | 64 248 | 35 558 | 36 801 | 47 114 | 27 910 | 22 395 | 33 565 | 58 454 | 39 255 | 19 496 |
| Kraus, Andreas | 42 830 | 47 926 | 50 110 | 39 974 | 35 196 | 36 379 | 26 028 | 22 786 | 51 548 | 42 705 | 42 506 | 27 005 |
| Salmansberger, Valentin | 34 241 | 13 517 | 22 493 | 49 428 | 33 137 | 34 743 | 18 532 | 49 366 | 38 610 | 74 599 | 35 031 | 31 004 |

### 4.3 Aufträge (Lohn) pro Monat

| SB / Monat | 2025-01 | 2025-02 | 2025-03 | 2025-04 | 2025-05 | 2025-06 | 2025-07 | 2025-08 | 2025-09 | 2025-10 | 2025-11 | 2025-12 |
|------------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
| Huber, Herbert | 199 | 199 | 273 | 178 | 203 | 160 | 181 | 122 | 247 | 227 | 177 | 132 |
| Keidl, Leonhard | 164 | 113 | 188 | 159 | 162 | 125 | 117 | 73 | 145 | 219 | 147 | 61 |
| Kraus, Andreas | 165 | 158 | 183 | 161 | 130 | 111 | 113 | 152 | 194 | 205 | 162 | 108 |
| Salmansberger, Valentin | 111 | 55 | 118 | 157 | 134 | 112 | 98 | 192 | 171 | 186 | 149 | 70 |

---

## 5. Technische Hinweise

- **Doppelzählung vermieden:** Aufträge über `COUNT(DISTINCT order_number)` bzw. distinct `orders.number` mit Join auf `orders.subsidiary` für Lohn/Teile.
- **Tabellen:** `orders`, `labours`, `parts`, `employees` (Locosoft); nur `employees.is_latest_record = true` für aktuelle Namen.
- **Kein Code deployt** — reine Analyse; Ergebnis liegt unter `docs/workstreams/verguetung/SB_UMSATZANALYSE_2025.md`.
