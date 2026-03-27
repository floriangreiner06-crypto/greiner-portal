# PDF Mockup - TEK Werkstatt

**TAG 140 - Konzept für Werkstattleiter**

---

## Layout-Übersicht

```
+----------------------------------------------------------+
|                   TEK WERKSTATT                          |
|                   Dezember 2025                          |
|              Stand: 28.12.2025 08:00 Uhr                 |
+----------------------------------------------------------+

+---------+  +----------+  +---------+  +----------+
|   DB1   |  |  MARGE   |  |   EW    |  |   LG    |
|  95.2k  |  |  56,0%   |  |  78,5%  |  |  92,3%  |
+---------+  +----------+  +---------+  +----------+
              ✓ Ziel        Produkti-   Leistungs-
              erreicht      vität       grad

+----------------------------------------------------------+
|                 DETAILS                                  |
+----------------------------------------------------------+
| Umsatz (Lohn)   |                           170.163 €    |
| Einsatz FIBU    |                           -32.521 €    |
|   davon Teile   |                           -22.100 €    |
|   davon Fremdl. |                           -10.421 €    |
| Lohn kalk. (21%)|                           -35.734 € *  |
|-----------------|----------------------------------------|
| Einsatz Gesamt  |                           -68.255 €    |
| DB1 (Rohertrag) |                           101.908 €    |
| Marge           |                              59,9%     |
| Ziel-Marge      |                              50,0%     |
+----------------------------------------------------------+
 * Rollierender 3-Vormonate-Durchschnitt (Sep-Nov 2025: 21%)

+----------------------------------------------------------+
|           UMSATZ NACH GRUPPEN                            |
+----------------------------------------------------------+
| Erlösgruppe         | Einsatz    | Erlös      | DB1      |
|---------------------|------------|------------|----------|
| Werkstattlohn (84)  |   -32.521€ |  170.163€  | 137.642€ |
|   Kundendienst      |   -18.200€ |   92.400€  |  74.200€ |
|   Karosserie        |    -8.100€ |   45.300€  |  37.200€ |
|   Garantie          |    -6.221€ |   32.463€  |  26.242€ |
|---------------------|------------|------------|----------|
| GESAMT              |   -32.521€ |  170.163€  | 137.642€ |
+----------------------------------------------------------+

+----------------------------------------------------------+
|           PRODUKTIVITÄT (Stempeluhr)                     |
+----------------------------------------------------------+
| Kennzahl            | Wert       | Ziel       | Status   |
|---------------------|------------|------------|----------|
| Produktivität (EW)  |     78,5%  |     75%    |    ✓     |
| Leistungsgrad (LG)  |     92,3%  |     90%    |    ✓     |
| Anwesenheitsstunden |    1.240h  |      -     |          |
| Produktivstunden    |      973h  |      -     |          |
| Verkaufte AW        |    1.147h  |      -     |          |
+----------------------------------------------------------+

+----------------------------------------------------------+
|           VERGLEICH                                      |
+----------------------------------------------------------+
|               | DB1 Werkst. |  DB1 Firma  | Differenz   |
|---------------|-------------|-------------|-------------|
| Aktuell       |  101.908 €  |  185.000 €  |      -      |
| Vormonat      |   98.400 €  |  210.400 €  |   +3.508 €  |
| Vorjahr       |   89.200 €  |  195.200 €  |  +12.708 €  |
+----------------------------------------------------------+

                    ───────────────────
                    TEK Werkstatt - DRIVE
                    ───────────────────
```

---

## Datenfelder

### Header-KPIs (groß dargestellt)
1. **DB1** - Deckungsbeitrag 1 (Rohertrag)
2. **Marge** - DB1/Umsatz in % (mit Ampel: grün ≥ 50%, gelb ≥ 45%, rot < 45%)
3. **EW** - Eigenleistungs-Wirkungsgrad (Produktivität)
4. **LG** - Leistungsgrad

### Details-Tabelle
- Umsatz (Lohn-Erlöse)
- Einsatz FIBU (was bereits gebucht ist)
  - davon Teile (Konten 743xxx)
  - davon Fremdleistungen (Konten 747xxx)
- Lohn kalkulatorisch (nur im lfd. Monat, rollierender %-Satz)
- Einsatz Gesamt (FIBU + kalk. Lohn)
- DB1 (Umsatz - Einsatz Gesamt)
- Marge
- Ziel-Marge (50%)

### Umsatz nach Gruppen
- Kundendienst
- Karosserie
- Garantie
- Sonstige
- Jeweils mit Einsatz | Erlös | DB1

### Produktivität (aus Stempeluhr)
- Produktivität (EW) - produktive Zeit / Anwesenheit
- Leistungsgrad (LG) - verkaufte AW / produktive Zeit
- Anwesenheitsstunden
- Produktivstunden
- Verkaufte Arbeitswerte (AW)

### Vergleich
- Aktuell vs. Vormonat vs. Vorjahr

---

## Benchmark-Margen (Ampel-Logik)

| Kennzahl     | Ziel (grün) | Warnung (gelb) | Unter Ziel (rot) |
|--------------|-------------|----------------|------------------|
| Marge        | ≥ 50%       | ≥ 45%          | < 45%            |
| EW           | ≥ 75%       | ≥ 70%          | < 70%            |
| LG           | ≥ 90%       | ≥ 85%          | < 85%            |

---

## Kalkulatorischer Lohn-Einsatz (TAG 140)

### Problem
Im laufenden Monat sind die Lohnkosten (Konten 740xxx) noch nicht in der FIBU gebucht.
Diese werden erst nach Monatsabschluss verbucht.

**WICHTIG:** Fremdleistungen (747xxx wie Autoglas, Waschanlage) werden NICHT kalkulatorisch
zugeschlagen - diese haben eine verhandelte Marge und werden laufend gebucht!

### Lösung
Rollierender 3-Vormonate-Durchschnitt (NUR Lohnkosten):
1. Summe Lohnkosten (NUR 740xxx) der letzten 3 abgeschlossenen Monate
2. Geteilt durch Summe Umsatz (840xxx) der gleichen 3 Monate
3. Ergibt Quote (z.B. 15%)
4. Diese Quote wird auf aktuellen Umsatz angewendet

### Beispiel Dezember 2025
- Zeitraum für Durchschnitt: Aug-Okt 2025
- Lohnkosten Aug-Okt: 117.338 €
- Umsatz Aug-Okt: 799.517 €
- Quote: 14,7%
- Aktueller Umsatz Dez: 170.163 €
- Kalk. Lohn: 170.163 × 0.147 = 25.014 €

### Im PDF
- Bei laufendem Monat: "Lohn kalk. (15%): 25.014 € *"
- Fußnote: "* Rollierender 3-Vormonate-Durchschnitt (nur 740xxx)"
- Bei abgeschlossenem Monat: Nur FIBU-Werte (ohne kalk. Zuschlag)

---

## Implementierungshinweise

1. **Datenquelle**: TEK v2 API + Produktivitäts-API (`/api/werkstatt/produktivitaet`)
2. **PDF-Generator**: ReportLab erweitern
3. **Trigger**: `send_daily_tek.py` für Report-Typ `tek_werkstatt`
4. **Empfänger**: Werkstattleiter über `reports` Registry
