# TEK E-Mail Report Verbesserungsvorschlag - TAG 204

**Datum:** 2026-01-20  
**Ziel:** E-Mail-Report stärker an Drive TEK Dashboard anlehnen - Alle Abteilungen detailiert

---

## 📋 Aktuelle Situation

### E-Mail-HTML (aktuell)
- Zeigt: DB1 aktuell, Marge, Prognose, Breakeven
- Bereiche: Umsatz, DB1, Marge
- **Fehlt:** Stückzahlen, Heute-Erlöse, detaillierte Abteilungsansicht

### PDF (aktuell)
- Zeigt: Vergleich VM/VJ, KPIs, Bereiche (Umsatz, Einsatz, DB1, Marge)
- **Fehlt:** Stückzahlen, Heute-Erlöse, detaillierte Abteilungsansicht

### Drive TEK Dashboard (Referenz)
- **Stückzahlen** für NW/GW prominent
- **Heute-Spalte** mit Umsatz und DB1
- **Monat-Spalte** mit Umsatz, Einsatz, DB1, Marge, DB1/Stk, Anteil
- Klare Struktur: Bereich → Stk → Heute → Monat
- **Alle Abteilungen** gleichwertig dargestellt

---

## 🎯 Vorschlag: Verbesserter E-Mail-Report

### Anforderungen
1. ✅ **Alle Abteilungen** gleichwertig darstellen (nicht nur Verkauf)
2. ✅ **Gruppiert nach KST** (Kostenstelle): NW, GW, Service, T&Z, etc.
3. ✅ **Heute-Erlöse** immer anzeigen (auch bei 0)
4. ✅ **Vorbereitung für Ziel/Erfüllung** (Spalten vorbereiten)

### 1. E-Mail-HTML Verbesserungen

#### A) Header-Bereich (unverändert)
```
┌─────────────────────────────────────────────────────────┐
│ TEK - Tägliche Erfolgskontrolle                          │
│ Dezember 2025 | Stand: 20.01.2026 19:30 Uhr             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📊 GESAMT                                                 │
│ DB1: 125.000 € | Marge: 12,5% | Prognose: 380.000 €     │
│ Breakeven: +50.000 € ✅                                  │
└─────────────────────────────────────────────────────────┘
```

#### B) Alle Abteilungen detailiert (NEU)
**Neue Haupttabelle - alle Bereiche gleichwertig:**
```html
<h3>📊 Abteilungen im Detail (nach KST)</h3>
<table>
  <tr>
    <th>KST</th>
    <th>Abteilung</th>
    <th>Stück</th>
    <th colspan="2">Heute</th>
    <th colspan="3">Monat kumuliert</th>
    <th colspan="2">Ziel/Erfüllung</th>
  </tr>
  <tr>
    <th></th>
    <th></th>
    <th></th>
    <th>Erlöse</th>
    <th>DB1</th>
    <th>Erlöse</th>
    <th>DB1</th>
    <th>DB1/Stk</th>
    <th>Ziel</th>
    <th>%</th>
  </tr>
  <tr>
    <td>1</td>
    <td>Neuwagen</td>
    <td>5</td>
    <td>25.000 €</td>
    <td>5.000 €</td>
    <td>800.000 €</td>
    <td>100.000 €</td>
    <td>20.000 €</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr>
    <td>2</td>
    <td>Gebrauchtwagen</td>
    <td>12</td>
    <td>20.000 €</td>
    <td>3.500 €</td>
    <td>450.000 €</td>
    <td>56.250 €</td>
    <td>4.688 €</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr>
    <td>3</td>
    <td>Service/Werkstatt</td>
    <td>-</td>
    <td>0 €</td>
    <td>0 €</td>
    <td>120.000 €</td>
    <td>60.000 €</td>
    <td>-</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr>
    <td>6</td>
    <td>Teile & Zubehör</td>
    <td>-</td>
    <td>0 €</td>
    <td>0 €</td>
    <td>80.000 €</td>
    <td>25.600 €</td>
    <td>-</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr>
    <td>7</td>
    <td>Sonstige</td>
    <td>-</td>
    <td>0 €</td>
    <td>0 €</td>
    <td>50.000 €</td>
    <td>5.000 €</td>
    <td>-</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr class="gesamt">
    <td colspan="2"><strong>GESAMT</strong></td>
    <td><strong>17</strong></td>
    <td><strong>45.000 €</strong></td>
    <td><strong>8.500 €</strong></td>
    <td><strong>1.500.000 €</strong></td>
    <td><strong>246.850 €</strong></td>
    <td><strong>14.521 €</strong></td>
    <td><strong>-</strong></td>
    <td><strong>-</strong></td>
  </tr>
</table>
```

**Wichtige Punkte:**
- ✅ **Stück** nur bei NW/GW (bei anderen "-" oder leer)
- ✅ **Heute-Erlöse/DB1** immer anzeigen (auch bei 0 €)
- ✅ **DB1/Stk** nur bei NW/GW (bei anderen "-" oder leer)
- ✅ **Ziel/Erfüllung** Spalten vorbereitet (später befüllen)
- ✅ **KST-Reihenfolge:** 1=NW, 2=GW, 3=Service, 6=T&Z, 7=Sonstige

---

### 2. PDF Verbesserungen

#### A) Erste Seite: Abteilungen im Detail (nach KST)
**Neue prominente Sektion am Anfang:**

```
┌─────────────────────────────────────────────────────────┐
│ TEK - Tägliche Erfolgskontrolle                          │
│ Dezember 2025 | Stand: 20.01.2026 19:30 Uhr             │
└─────────────────────────────────────────────────────────┘

📊 ABTEILUNGEN IM DETAIL (nach KST)
┌─────────────────────────────────────────────────────────────┐
│ KST │ Abteilung      │ Stk │ Heute      │ Monat kumuliert │ Ziel│
│     │                │     │ Erlöse DB1 │ Erlöse DB1 DB1/St│ %  │
├─────┼────────────────┼─────┼────────────┼─────────────────┼────┤
│  1  │ Neuwagen       │  5  │ 25k  5k    │ 800k  100k  20k │ -  │
│  2  │ Gebrauchtwagen │ 12  │ 20k  3,5k  │ 450k  56k   4,7k│ -  │
│  3  │ Service/Werkst.│  -  │  0k   0k   │ 120k  60k    -  │ -  │
│  6  │ Teile & Zubehör│  -  │  0k   0k   │  80k  25,6k  -  │ -  │
│  7  │ Sonstige       │  -  │  0k   0k   │  50k   5k    -  │ -  │
├─────┼────────────────┼─────┼────────────┼─────────────────┼────┤
│     │ GESAMT         │ 17  │ 45k  8,5k  │1.500k 246,9k 14,5│ -  │
└─────────────────────────────────────────────────────────────┘
```

**Wichtige Punkte:**
- ✅ Alle Abteilungen gleichwertig
- ✅ KST-Reihenfolge: 1, 2, 3, 6, 7
- ✅ Heute-Daten immer (auch 0 €)
- ✅ Stück nur bei NW/GW
- ✅ Ziel/Erfüllung vorbereitet

#### B) Zweite Seite: Gesamt-KPIs (wie bisher)
- Vergleich VM/VJ
- Gesamt-KPIs
- Breakeven-Status

#### C) Dritte Seite: Drill-Down - Verkauf (NW/GW)

**C.1) Neuwagen - Nach Absatzwegen:**
```
🚗 NEUWAGEN - DRILL-DOWN

📊 Nach Absatzwegen (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Absatzweg          │ Stück │ Erlöse   │ DB1      │ DB1/Stk│
├────────────────────┼───────┼──────────┼──────────┼────────┤
│ Privat Kauf        │   2   │ 320k €   │ 40k €    │ 20k €  │
│ Privat Leasing     │   1   │ 180k €   │ 22k €    │ 22k €  │
│ Gewerbe Kauf       │   1   │ 200k €   │ 25k €    │ 25k €  │
│ Gewerbe Leasing    │   1   │ 100k €   │ 13k €    │ 13k €  │
├────────────────────┼───────┼──────────┼──────────┼────────┤
│ GESAMT             │   5   │ 800k €   │ 100k €   │ 20k €  │
└─────────────────────────────────────────────────────────┘
```

**C.2) Neuwagen - Nach Modellen:**
```
📊 Nach Modellen (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Modell      │ Stück │ Erlöse   │ DB1      │ DB1/Stk│
├─────────────┼───────┼──────────┼──────────┼────────┤
│ Corsa       │   2   │ 200k €   │ 25k €    │ 12,5k €│
│ Astra       │   2   │ 400k €   │ 50k €    │ 25k €  │
│ Combo       │   1   │ 200k €   │ 25k €    │ 25k €  │
├─────────────┼───────┼──────────┼──────────┼────────┤
│ GESAMT      │   5   │ 800k €   │ 100k €   │ 20k €  │
└─────────────────────────────────────────────────────────┘
```

**C.3) Gebrauchtwagen - Nach Absatzwegen:**
```
🚗 GEBRAUCHTWAGEN - DRILL-DOWN

📊 Nach Absatzwegen (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Absatzweg          │ Stück │ Erlöse   │ DB1      │ DB1/Stk│
├────────────────────┼───────┼──────────┼──────────┼────────┤
│ Privat reg         │   8   │ 280k €   │ 35k €    │ 4,4k € │
│ Privat Kauf        │   2   │  80k €   │ 10k €    │ 5k €   │
│ Gewerbe reg        │   2   │  90k €   │ 11,25k €│ 5,6k € │
├────────────────────┼───────┼──────────┼──────────┼────────┤
│ GESAMT             │  12   │ 450k €   │ 56,25k € │ 4,7k € │
└─────────────────────────────────────────────────────────┘
```

**C.4) Gebrauchtwagen - Nach Modellen:**
```
📊 Nach Modellen (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Modell      │ Stück │ Erlöse   │ DB1      │ DB1/Stk│
├─────────────┼───────┼──────────┼──────────┼────────┤
│ Golf        │   4   │ 150k €   │ 18,75k €│ 4,7k € │
│ Passat      │   3   │ 120k €   │ 15k €   │ 5k €   │
│ BMW 3er     │   2   │  90k €   │ 11,25k €│ 5,6k € │
│ Sonstige    │   3   │  90k €   │ 11,25k €│ 3,75k €│
├─────────────┼───────┼──────────┼──────────┼────────┤
│ GESAMT      │  12   │ 450k €   │ 56,25k € │ 4,7k € │
└─────────────────────────────────────────────────────────┘
```

#### D) Vierte Seite: Drill-Down - Service/Werkstatt (optional)
```
🔧 SERVICE/WERKSTATT - DRILL-DOWN

📊 Nach Bereichen (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Bereich        │ Erlöse   │ Einsatz  │ DB1      │ Marge │
├────────────────┼──────────┼──────────┼──────────┼───────┤
│ Mechanik       │  80k €   │  40k €   │ 40k €    │ 50%   │
│ Karosserie     │  30k €   │  15k €   │ 15k €    │ 50%   │
│ Sonstige       │  10k €   │   5k €   │  5k €    │ 50%   │
├────────────────┼──────────┼──────────┼──────────┼───────┤
│ GESAMT         │ 120k €   │  60k €   │ 60k €    │ 50%   │
└─────────────────────────────────────────────────────────┘
```

#### E) Fünfte Seite: Drill-Down - Teile & Zubehör (optional)
```
📦 TEILE & ZUBEHÖR - DRILL-DOWN

📊 Nach Kategorien (Monat kumuliert)
┌─────────────────────────────────────────────────────────┐
│ Kategorie      │ Erlöse   │ Einsatz  │ DB1      │ Marge │
├────────────────┼──────────┼──────────┼──────────┼───────┤
│ Ersatzteile    │  50k €   │  30k €   │ 20k €    │ 40%   │
│ Zubehör        │  20k €   │  12k €   │  8k €    │ 40%   │
│ Sonstige       │  10k €   │   6k €   │  4k €    │ 40%   │
├────────────────┼──────────┼──────────┼──────────┼───────┤
│ GESAMT         │  80k €   │  48k €   │ 32k €    │ 40%   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technische Umsetzung

### Daten aus API verfügbar
Die TEK-API (`/api/tek`) liefert bereits:
- ✅ `bereiche['1-NW']['stueck']` - Stückzahlen Neuwagen
- ✅ `bereiche['2-GW']['stueck']` - Stückzahlen Gebrauchtwagen
- ✅ `heute.bereiche['1-NW']['umsatz']` - Heute-Erlöse NW
- ✅ `heute.bereiche['1-NW']['db1']` - Heute-DB1 NW
- ✅ `bereiche['1-NW']['umsatz']` - Monat-Erlöse NW
- ✅ `bereiche['1-NW']['db1']` - Monat-DB1 NW
- ✅ `bereiche['1-NW']['db1_pro_stueck']` - DB1/Stk NW
- ✅ `heute.bereiche['3-Teile']['umsatz']` - Heute-Erlöse Teile (kann 0 sein)
- ✅ `heute.bereiche['4-Lohn']['umsatz']` - Heute-Erlöse Werkstatt (kann 0 sein)

### KST-Mapping
```python
KST_MAPPING = {
    '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1},
    '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2},
    '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3},
    '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4},
    '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5}
}
```

### Änderungen in `send_daily_tek.py`

#### 1. `build_gesamt_email_html()` komplett überarbeiten
```python
def build_gesamt_email_html(data):
    """Erstellt HTML-Body für Gesamt-Report - ALLE ABTEILUNGEN DETAILIERT"""
    
    # ... bestehender Header-Code ...
    
    # KST-Mapping
    KST_MAPPING = {
        '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1, 'show_stueck': True},
        '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2, 'show_stueck': True},
        '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3, 'show_stueck': False},
        '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4, 'show_stueck': False},
        '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5, 'show_stueck': False}
    }
    
    # Bereiche nach KST-Reihenfolge sortieren
    bereiche_sorted = sorted(
        data['bereiche'],
        key=lambda b: KST_MAPPING.get(b['bereich'], {}).get('order', 99)
    )
    
    # Abteilungen-Tabelle generieren
    abteilungen_rows = ""
    gesamt_stueck = 0
    gesamt_heute_umsatz = 0
    gesamt_heute_db1 = 0
    gesamt_monat_umsatz = 0
    gesamt_monat_db1 = 0
    
    for b in bereiche_sorted:
        bkey = b['bereich']
        cfg = KST_MAPPING.get(bkey, {'kst': '-', 'name': bkey, 'show_stueck': False})
        
        # Heute-Daten (immer anzeigen, auch wenn 0)
        heute_umsatz = b.get('heute_umsatz', 0)
        heute_db1 = b.get('heute_db1', 0)
        
        # Monat-Daten
        monat_umsatz = b.get('umsatz', 0)
        monat_db1 = b.get('db1', 0)
        monat_db1_pro_stueck = b.get('db1_pro_stueck', 0) if cfg['show_stueck'] else None
        
        # Stück (nur bei NW/GW)
        stueck = b.get('stueck', 0) if cfg['show_stueck'] else None
        stueck_display = str(stueck) if stueck is not None else "-"
        
        # DB1/Stk (nur bei NW/GW)
        db1_stk_display = format_euro(monat_db1_pro_stueck) if monat_db1_pro_stueck else "-"
        
        # Summen für Gesamt
        if stueck:
            gesamt_stueck += stueck
        gesamt_heute_umsatz += heute_umsatz
        gesamt_heute_db1 += heute_db1
        gesamt_monat_umsatz += monat_umsatz
        gesamt_monat_db1 += monat_db1
        
        abteilungen_rows += f"""
        <tr>
            <td style="padding: 8px; text-align: center;">{cfg['kst']}</td>
            <td style="padding: 8px;">{cfg['name']}</td>
            <td style="padding: 8px; text-align: center;">{stueck_display}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(heute_umsatz)}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(heute_db1)}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(monat_umsatz)}</td>
            <td style="padding: 8px; text-align: right;">{format_euro(monat_db1)}</td>
            <td style="padding: 8px; text-align: right;">{db1_stk_display}</td>
            <td style="padding: 8px; text-align: center;">-</td>
            <td style="padding: 8px; text-align: center;">-</td>
        </tr>"""
    
    # Gesamt-DB1/Stk berechnen (nur NW+GW)
    nw = next((b for b in bereiche_sorted if b['bereich'] == '1-NW'), None)
    gw = next((b for b in bereiche_sorted if b['bereich'] == '2-GW'), None)
    db1_nw_gw = (nw.get('db1', 0) if nw else 0) + (gw.get('db1', 0) if gw else 0)
    gesamt_db1_stk = round(db1_nw_gw / gesamt_stueck, 2) if gesamt_stueck > 0 else 0
    
    abteilungen_html = f"""
    <h3 style="color: #333; margin-top: 25px;">📊 Abteilungen im Detail (nach KST)</h3>
    <table style="border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.9rem;">
        <tr style="background: #0066cc; color: white;">
            <th style="padding: 10px; text-align: center;">KST</th>
            <th style="padding: 10px; text-align: left;">Abteilung</th>
            <th style="padding: 10px; text-align: center;">Stück</th>
            <th colspan="2" style="padding: 10px; text-align: center; background: #17a2b8;">Heute</th>
            <th colspan="3" style="padding: 10px; text-align: center; background: #6c757d;">Monat kumuliert</th>
            <th colspan="2" style="padding: 10px; text-align: center; background: #ffc107;">Ziel/Erfüllung</th>
        </tr>
        <tr style="background: #e9ecef;">
            <th></th>
            <th></th>
            <th></th>
            <th style="padding: 8px; text-align: right;">Erlöse</th>
            <th style="padding: 8px; text-align: right;">DB1</th>
            <th style="padding: 8px; text-align: right;">Erlöse</th>
            <th style="padding: 8px; text-align: right;">DB1</th>
            <th style="padding: 8px; text-align: right;">DB1/Stk</th>
            <th style="padding: 8px; text-align: center;">Ziel</th>
            <th style="padding: 8px; text-align: center;">%</th>
        </tr>
        {abteilungen_rows}
        <tr style="background: #e9ecef; font-weight: bold; border-top: 2px solid #333;">
            <td colspan="2" style="padding: 8px;"><strong>GESAMT</strong></td>
            <td style="padding: 8px; text-align: center;"><strong>{gesamt_stueck}</strong></td>
            <td style="padding: 8px; text-align: right;"><strong>{format_euro(gesamt_heute_umsatz)}</strong></td>
            <td style="padding: 8px; text-align: right;"><strong>{format_euro(gesamt_heute_db1)}</strong></td>
            <td style="padding: 8px; text-align: right;"><strong>{format_euro(gesamt_monat_umsatz)}</strong></td>
            <td style="padding: 8px; text-align: right;"><strong>{format_euro(gesamt_monat_db1)}</strong></td>
            <td style="padding: 8px; text-align: right;"><strong>{format_euro(gesamt_db1_stk)}</strong></td>
            <td style="padding: 8px; text-align: center;"><strong>-</strong></td>
            <td style="padding: 8px; text-align: center;"><strong>-</strong></td>
        </tr>
    </table>
    """
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 900px;">
        <!-- ... bestehender Header ... -->
        
        <!-- NEU: Abteilungen im Detail -->
        {abteilungen_html}
        
        <!-- Bestehende Bereiche-Tabelle (optional, kompakt) -->
        <!-- ... -->
    </body>
    </html>
    """
```

#### 2. `generate_tek_daily_pdf()` erweitern
```python
def generate_tek_daily_pdf(data: dict) -> bytes:
    """Generiert PDF für TEK - ALLE ABTEILUNGEN DETAILIERT + DRILL-DOWNS"""
    
    # ... bestehender Code ...
    
    # KST-Mapping
    KST_MAPPING = {
        '1-NW': {'kst': '1', 'name': 'Neuwagen', 'order': 1, 'show_stueck': True},
        '2-GW': {'kst': '2', 'name': 'Gebrauchtwagen', 'order': 2, 'show_stueck': True},
        '4-Lohn': {'kst': '3', 'name': 'Service/Werkstatt', 'order': 3, 'show_stueck': False},
        '3-Teile': {'kst': '6', 'name': 'Teile & Zubehör', 'order': 4, 'show_stueck': False},
        '5-Sonst': {'kst': '7', 'name': 'Sonstige', 'order': 5, 'show_stueck': False}
    }
    
    # NEU: Abteilungen im Detail als erste Sektion
    elements.append(Paragraph("📊 Abteilungen im Detail (nach KST)", section_style))
    
    # ... Abteilungen-Tabelle (wie oben) ...
    
    # NEU: DRILL-DOWNS für Verkauf (NW/GW)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("🚗 Verkauf - Drill-Down", section_style))
    
    # NEU: Neuwagen Drill-Down
    nw = next((b for b in data['bereiche'] if b['bereich'] == '1-NW'), None)
    if nw:
        # Absatzwege holen (via API)
        absatzwege_nw = get_absatzwege_drill_down(
            bereich='1-NW',
            firma=data.get('firma', '0'),
            standort=data.get('standort', '0'),
            monat=data.get('monat'),
            jahr=data.get('jahr')
        )
        
        # Modelle holen (via API)
        modelle_nw = get_modelle_drill_down(
            bereich='1-NW',
            firma=data.get('firma', '0'),
            standort=data.get('standort', '0'),
            monat=data.get('monat'),
            jahr=data.get('jahr')
        )
        
        # Absatzwege-Tabelle
        if absatzwege_nw:
            elements.append(Paragraph("📊 Neuwagen - Nach Absatzwegen (Monat kumuliert)", styles['Heading3']))
            absatzwege_data = [['Absatzweg', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for aw in absatzwege_nw:
                absatzwege_data.append([
                    aw['absatzweg'],
                    str(aw['stueck']),
                    format_currency_short(aw['umsatz']),
                    format_currency_short(aw['db1']),
                    format_currency_short(aw.get('db1_pro_stueck', 0))
                ])
            # Gesamt-Zeile
            absatzwege_data.append([
                'GESAMT',
                str(nw.get('stueck', 0)),
                format_currency_short(nw.get('umsatz', 0)),
                format_currency_short(nw.get('db1', 0)),
                format_currency_short(nw.get('db1_pro_stueck', 0))
            ])
            absatzwege_table = Table(absatzwege_data, colWidths=[...])
            # ... Styling ...
            elements.append(absatzwege_table)
            elements.append(Spacer(1, 15))
        
        # Modelle-Tabelle
        if modelle_nw:
            elements.append(Paragraph("📊 Neuwagen - Nach Modellen (Monat kumuliert)", styles['Heading3']))
            modelle_data = [['Modell', 'Stück', 'Erlöse', 'DB1', 'DB1/Stk']]
            for m in sorted(modelle_nw, key=lambda x: x.get('umsatz', 0), reverse=True)[:10]:  # Top 10
                modelle_data.append([
                    m['modell'],
                    str(m.get('stueck', 0)),
                    format_currency_short(m['umsatz']),
                    format_currency_short(m['db1']),
                    format_currency_short(m.get('db1_pro_stueck', 0))
                ])
            modelle_table = Table(modelle_data, colWidths=[...])
            # ... Styling ...
            elements.append(modelle_table)
            elements.append(Spacer(1, 20))
    
    # NEU: Gebrauchtwagen Drill-Down
    gw = next((b for b in data['bereiche'] if b['bereich'] == '2-GW'), None)
    if gw:
        # Absatzwege holen
        absatzwege_gw = get_absatzwege_drill_down(
            bereich='2-GW',
            firma=data.get('firma', '0'),
            standort=data.get('standort', '0'),
            monat=data.get('monat'),
            jahr=data.get('jahr')
        )
        
        # Modelle holen
        modelle_gw = get_modelle_drill_down(
            bereich='2-GW',
            firma=data.get('firma', '0'),
            standort=data.get('standort', '0'),
            monat=data.get('monat'),
            jahr=data.get('jahr')
        )
        
        # Absatzwege-Tabelle
        if absatzwege_gw:
            elements.append(Paragraph("📊 Gebrauchtwagen - Nach Absatzwegen (Monat kumuliert)", styles['Heading3']))
            # ... wie bei NW ...
        
        # Modelle-Tabelle
        if modelle_gw:
            elements.append(Paragraph("📊 Gebrauchtwagen - Nach Modellen (Monat kumuliert)", styles['Heading3']))
            # ... wie bei NW ...
    
    # NEU: Service/Werkstatt Drill-Down (optional)
    service = next((b for b in data['bereiche'] if b['bereich'] == '4-Lohn'), None)
    if service and service.get('umsatz', 0) > 0:
        # Nach Bereichen/Kategorien aufdrillen
        # (kann später erweitert werden)
        pass
    
    # NEU: Teile & Zubehör Drill-Down (optional)
    teile = next((b for b in data['bereiche'] if b['bereich'] == '3-Teile'), None)
    if teile and teile.get('umsatz', 0) > 0:
        # Nach Kategorien aufdrillen
        # (kann später erweitert werden)
        pass
    
    # ... bestehender Code (Vergleich, KPIs) ...


def get_absatzwege_drill_down(bereich, firma, standort, monat, jahr):
    """Holt Absatzwege-Daten via API /api/tek/detail"""
    import requests
    try:
        params = {
            'bereich': bereich,
            'firma': firma,
            'standort': standort,
            'monat': monat,
            'jahr': jahr,
            'ebene': 'gruppen'
        }
        response = requests.get('http://127.0.0.1:5000/api/tek/detail', params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('absatzwege', [])
    except:
        pass
    return []


def get_modelle_drill_down(bereich, firma, standort, monat, jahr):
    """Holt Modell-Daten via API /api/tek/modelle"""
    import requests
    try:
        params = {
            'bereich': bereich,
            'firma': firma,
            'standort': standort,
            'monat': monat,
            'jahr': jahr,
            'gruppierung': 'modell'  # oder 'modell_kundentyp' für detaillierter
        }
        response = requests.get('http://127.0.0.1:5000/api/tek/modelle', params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('modelle', [])
    except:
        pass
    return []
```

---

## 📊 Datenstruktur-Erweiterung

### `get_tek_data()` erweitern
Die Funktion muss die "Heute"-Daten aus der API-Response extrahieren:

```python
def get_tek_data(monat=None, jahr=None, standort=None):
    """Holt TEK-Daten über die DRIVE-API - ERWEITERT mit Heute-Daten"""
    
    # ... bestehender API-Call ...
    
    # NEU: Heute-Daten extrahieren
    heute_data = api_data.get('heute', {})
    heute_bereiche = heute_data.get('bereiche', {})
    
    # Heute-Daten zu Bereichen hinzufügen
    for b in bereiche:
        bkey = b['bereich']
        if bkey in heute_bereiche:
            hb = heute_bereiche[bkey]
            b['heute_umsatz'] = round(hb.get('umsatz', 0), 2)
            b['heute_db1'] = round(hb.get('db1', 0), 2)
        else:
            b['heute_umsatz'] = 0
            b['heute_db1'] = 0
    
    return {
        # ... bestehende Daten ...
        'bereiche': bereiche  # Jetzt mit heute_umsatz und heute_db1
    }
```

---

## ✅ Vorteile des Vorschlags

1. **Konsistenz:** E-Mail-Report ähnelt dem Drive TEK Dashboard
2. **Relevanz:** Verkaufs-Daten (Stückzahlen, Erlöse) prominent
3. **Aktualität:** Heute-Erlöse sofort sichtbar
4. **Übersicht:** Monat kumuliert klar dargestellt
5. **Vollständigkeit:** Alle Bereiche weiterhin vorhanden

---

## 🔄 Nächste Schritte

1. **Diskussion:** Vorschlag mit Team besprechen
2. **Anpassungen:** Basierend auf Feedback
3. **Implementierung:** 
   - `send_daily_tek.py` erweitern
   - `api/pdf_generator.py` erweitern
   - `get_tek_data()` erweitern
4. **Testing:** Test-E-Mail versenden
5. **Deployment:** Nach Freigabe

---

## ✅ Vorteile des überarbeiteten Vorschlags

1. **Gleichwertigkeit:** Alle Abteilungen gleichwertig dargestellt
2. **KST-Struktur:** Klare Gruppierung nach Kostenstellen
3. **Vollständigkeit:** Heute-Daten immer angezeigt (auch bei 0)
4. **Erweiterbarkeit:** Ziel/Erfüllung vorbereitet
5. **Konsistenz:** Ähnelt Drive TEK Dashboard
6. **Übersichtlichkeit:** Klare Struktur, alle wichtigen Kennzahlen

---

## 🔄 Nächste Schritte

1. **Implementierung:**
   - `send_daily_tek.py` → `build_gesamt_email_html()` überarbeiten
   - `api/pdf_generator.py` → `generate_tek_daily_pdf()` erweitern
   - `get_tek_data()` → Heute-Daten aus API-Response extrahieren
2. **Testing:** Test-E-Mail versenden
3. **Ziel/Erfüllung:** Später implementieren (Daten aus Planung)

---

## 📝 Technische Details

### KST-Reihenfolge
1. **KST 1:** Neuwagen (NW)
2. **KST 2:** Gebrauchtwagen (GW)
3. **KST 3:** Service/Werkstatt
4. **KST 6:** Teile & Zubehör
5. **KST 7:** Sonstige

### Stückzahlen
- Nur bei **NW** und **GW** angezeigt
- Bei anderen Abteilungen: **"-"** oder leer

### Heute-Daten
- **Immer anzeigen**, auch wenn 0 €
- Format: `0 €` (nicht verstecken)

### Ziel/Erfüllung (vorbereitet)
- Spalten vorhanden, aber noch nicht befüllt
- Später: Daten aus Planung/Unternehmensplan

### Drill-Down Datenquellen

#### Verkauf (NW/GW)
- **Absatzwege:** `/api/tek/detail?bereich=1-NW&ebene=gruppen`
  - Liefert: `absatzwege[]` mit Stück, Umsatz, DB1, DB1/Stk
  - Gruppiert nach: Kundentyp + Verkaufsart (z.B. "Privat Kauf", "Gewerbe Leasing")
  
- **Modelle:** `/api/tek/modelle?bereich=1-NW&gruppierung=modell`
  - Liefert: `modelle[]` mit Modell, Stück, Umsatz, DB1, DB1/Stk
  - Gruppiert nach: Fahrzeugmodell (z.B. "Corsa", "Astra")
  - Optionen: `modell`, `modell_kundentyp`, `modell_verkaufsart`, `detail`

#### Service/Werkstatt (optional)
- **Nach Bereichen:** `/api/tek/detail?bereich=4-Lohn&ebene=gruppen`
  - Kann nach Konten-Gruppen aufdrillen
  - Später erweiterbar

#### Teile & Zubehör (optional)
- **Nach Kategorien:** `/api/tek/detail?bereich=3-Teile&ebene=gruppen`
  - Kann nach Konten-Gruppen aufdrillen
  - Später erweiterbar

### PDF-Struktur
1. **Seite 1:** Abteilungen im Detail (nach KST)
2. **Seite 2:** Gesamt-KPIs (Vergleich VM/VJ, Breakeven)
3. **Seite 3:** Drill-Down Verkauf (NW/GW - Absatzwege + Modelle)
4. **Seite 4+:** Optional weitere Drill-Downs (Service, Teile)

---

## ✅ Vorteile der Drill-Downs

1. **Detaillierte Analyse:** Verkauf nach Absatzwegen und Modellen
2. **Bereits verfügbar:** APIs existieren bereits (`/api/tek/detail`, `/api/tek/modelle`)
3. **Flexibel:** Kann später erweitert werden (Service, Teile)
4. **Übersichtlich:** Separate Seiten für jeden Drill-Down

---

**Ende Vorschlag**
