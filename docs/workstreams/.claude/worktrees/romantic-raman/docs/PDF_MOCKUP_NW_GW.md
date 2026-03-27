# PDF Mockup - TEK Neuwagen / Gebrauchtwagen

**TAG 140 - Konzept für Abteilungsleiter NW/GW**

---

## Layout-Übersicht

```
+----------------------------------------------------------+
|                    TEK NEUWAGEN                          |
|                   Dezember 2025                          |
|              Stand: 28.12.2025 08:00 Uhr                 |
+----------------------------------------------------------+

+---------+  +----------+  +---------+  +----------+
|   DB1   |  |  MARGE   |  |  STÜCK  |  | DB1/STK  |
|  25.4k  |  |   8,2%   |  |   12    |  |  2.117€  |
+---------+  +----------+  +---------+  +----------+
              ⚠ Warnung
              (Ziel: 12%)

+----------------------------------------------------------+
|                 DETAILS                                  |
+----------------------------------------------------------+
| Umsatz          |                           310.500 €    |
| Einsatz         |                          -285.100 €    |
| DB1 (Rohertrag) |                            25.400 €    |
| Marge           |                               8,2%     |
| Ziel-Marge      |                              12,0%     |
| Stück           |                                 12     |
| DB1/Stück       |                             2.117 €    |
+----------------------------------------------------------+

+----------------------------------------------------------+
|           MODELLE - TOP 5                                |
+----------------------------------------------------------+
| Modell              | Stück |    DB1    | DB1/Stk       |
|---------------------|-------|-----------|---------------|
| Peugeot 208         |     4 |   8.200 € |      2.050 €  |
| Peugeot 3008        |     3 |   9.600 € |      3.200 €  |
| Opel Corsa          |     2 |   3.400 € |      1.700 €  |
| Citroen C3          |     2 |   2.800 € |      1.400 €  |
| Fiat 500            |     1 |   1.400 € |      1.400 €  |
|---------------------|-------|-----------|---------------|
| GESAMT              |    12 |  25.400 € |      2.117 €  |
+----------------------------------------------------------+

+----------------------------------------------------------+
|           ABSATZWEGE                                     |
+----------------------------------------------------------+
| Absatzweg           | Stück |    DB1    | DB1/Stk       |
|---------------------|-------|-----------|---------------|
| Privat reg          |     7 |  15.400 € |      2.200 €  |
| Großkunde           |     3 |   6.000 € |      2.000 €  |
| Leasing             |     2 |   4.000 € |      2.000 €  |
|---------------------|-------|-----------|---------------|
| GESAMT              |    12 |  25.400 € |      2.117 €  |
+----------------------------------------------------------+

+----------------------------------------------------------+
|           VERGLEICH                                      |
+----------------------------------------------------------+
|               | DB1 Bereich |  DB1 Firma  | Differenz   |
|---------------|-------------|-------------|-------------|
| Aktuell       |   25.400 €  |  185.000 €  |      -      |
| Vormonat      |   31.200 €  |  210.400 €  |   -5.800 €  |
| Vorjahr       |   28.100 €  |  195.200 €   |  -2.700 €  |
+----------------------------------------------------------+

                    ───────────────────
                    TEK Neuwagen - DRIVE
                    ───────────────────
```

---

## Datenfelder

### Header-KPIs (groß dargestellt)
1. **DB1** - Deckungsbeitrag 1 (Rohertrag)
2. **Marge** - DB1/Umsatz in % (mit Ampel: grün ≥ Ziel, gelb ≥ Warnung, rot < Warnung)
3. **Stück** - Anzahl verkaufter Fahrzeuge
4. **DB1/Stk** - Durchschnittlicher DB1 pro Fahrzeug

### Details-Tabelle
- Umsatz (Erlöse)
- Einsatz (Wareneinsatz)
- DB1 (Rohertrag = Umsatz - Einsatz)
- Marge (DB1/Umsatz × 100)
- Ziel-Marge (NW: 12%, GW: 10%)
- Stück (Fahrzeuge)
- DB1/Stück

### Modelle (Top 5)
- Modell-Name (aus FIBU-Kontobezeichnung extrahiert)
- Stück
- DB1
- DB1/Stk

### Absatzwege
- Absatzweg (Privat reg, Großkunde, Leasing, etc.)
- Stück
- DB1
- DB1/Stk

### Vergleich
- Aktuell vs. Vormonat vs. Vorjahr
- Sowohl Bereichs-DB1 als auch Firmen-DB1

---

## Benchmark-Margen (Ampel-Logik)

| Bereich | Ziel (grün) | Warnung (gelb) | Unter Ziel (rot) |
|---------|-------------|----------------|------------------|
| NW      | ≥ 12%       | ≥ 8%           | < 8%             |
| GW      | ≥ 10%       | ≥ 7%           | < 7%             |

---

## Implementierungshinweise

1. **Datenquelle**: TEK v2 API (`/controlling/api/tek/detail`) + Modelle-API (`/controlling/api/tek/modelle`)
2. **PDF-Generator**: ReportLab erweitern
3. **Trigger**: `send_daily_tek.py` für Report-Typ `tek_nw` und `tek_gw`
4. **Empfänger**: Über `reports` Registry mit Bereich-Filter

---

## Offene Fragen

1. Sollen alle Modelle oder nur Top 5 angezeigt werden?
2. Absatzwege immer zeigen oder nur bei > 1 Absatzweg?
3. Vergleich auf Bereichs-Ebene (nur NW/GW) oder auch Firmen-Ebene?
