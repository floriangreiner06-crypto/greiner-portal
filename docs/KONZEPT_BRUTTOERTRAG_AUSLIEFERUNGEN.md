# 💰 KONZEPT: BRUTTOERTRAG & UMSATZ IN AUSLIEFERUNGEN
## Erweiterung der Verkaufs-Detail-Ansichten

**Datum:** 11.11.2025  
**Ziel:** Deckungsbeitrag & Umsatz pro Verkäufer anzeigen (kumuliert + einzeln)

---

## 📊 VERFÜGBARE DATEN (aus LocoSoft)

### Sales-Tabelle Spalten:
```sql
out_sale_price   -- Verkaufspreis (BRUTTO) - was Kunde zahlt
netto_price      -- Einkaufspreis (NETTO) - was wir bezahlt haben
```

### Berechnungen:
```sql
-- Bruttoertrag / Deckungsbeitrag pro Fahrzeug:
Deckungsbeitrag = out_sale_price - netto_price

-- Deckungsbeitrag in %:
DB% = (Deckungsbeitrag / netto_price) * 100

-- Umsatz:
Umsatz = out_sale_price
```

---

## 🎨 UI-KONZEPT: WO ANZEIGEN?

### Option 1: ERWEITERTE TABELLE (EMPFOHLEN) ⭐

**Seite:** Verkauf → Auslieferungen (Detail)

**Vorher (aktuell):**
```
┌─────────────────────────────────────────────────────────┐
│ Anton Süß                                    Gesamt: 2  │
├─────────────────────────────────────────────────────────┤
│ Neuwagen (0)                                            │
│                                                          │
│ Test/Vorführ (1)                                        │
│ • Corsa Edition, 1.2 ... (1x)                          │
│                                                          │
│ Gebraucht (1)                                           │
│ • IONIQ 6 Allradantrieb ... (1x)                       │
└─────────────────────────────────────────────────────────┘
```

**Nachher (mit Finanzdaten):**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Anton Süß                      Gesamt: 2  │  Umsatz: 56.890 €  │  DB: 8.450 € │
├──────────────────────────────────────────────────────────────────────────────┤
│ Neuwagen (0)                                     0 €        0 €      0 €     │
│                                                                                │
│ Test/Vorführ (1)                            20.390 €   20.390 €  2.150 € ✅  │
│ • Corsa Edition, 1.2 ... (1x)  │  20.390 €  │  DB: 2.150 € (10,5%) ✅       │
│                                                                                │
│ Gebraucht (1)                               36.500 €   36.500 €  6.300 € ✅  │
│ • IONIQ 6 Allradantrieb ... (1x) │  36.500 €  │  DB: 6.300 € (17,3%) ✅      │
└──────────────────────────────────────────────────────────────────────────────┘

Legende:
✅ = DB% > 10% (gut)
⚠️ = DB% 5-10% (mittel)
❌ = DB% < 5% (schlecht)
```

**Vorteile:**
- ✅ Alle Infos auf einen Blick
- ✅ Pro Verkäufer kumuliert
- ✅ Pro Fahrzeugtyp kumuliert
- ✅ Einzelfahrzeuge mit Details
- ✅ Farbcodierung für Performance

---

### Option 2: SEPARATE KPI-KACHELN (zusätzlich)

**Über der Verkäufer-Liste:**
```
┌────────────────┬────────────────┬────────────────┬────────────────┐
│ GESAMT UMSATZ  │ GESAMT DB      │ Ø DB%          │ ANZAHL         │
│ 670.129 €      │ 95.428 €       │ 14,2%          │ 31 Fzg.        │
└────────────────┴────────────────┴────────────────┴────────────────┘

Filter: November 2025, Alle Standorte, Alle Verkäufer
```

**Vorteile:**
- ✅ Schneller Überblick
- ✅ Management-taugliche KPIs
- ✅ Benchmark: Durchschnitt sichtbar

---

### Option 3: DETAIL-MODAL (bei Klick auf Fahrzeug)

**Klick auf "Corsa Edition":**
```
╔═══════════════════════════════════════════════════╗
║ 🚗 FAHRZEUG-DETAILS                               ║
╠═══════════════════════════════════════════════════╣
║ Modell: Corsa Edition, 1.2 Direct Injection Turbo║
║ VIN: S4176742 (letzte 8 Stellen)                 ║
║ Typ: Test/Vorführwagen                            ║
║                                                    ║
║ 💰 FINANZEN:                                      ║
║ ├─ Verkaufspreis (Brutto): 20.390,00 €          ║
║ ├─ Einkaufspreis (Netto):  18.240,00 €          ║
║ ├─ Deckungsbeitrag:         2.150,00 € ✅        ║
║ └─ DB%:                        10,5% ✅           ║
║                                                    ║
║ 📅 TERMINE:                                       ║
║ ├─ Vertragsdatum: 06.11.2025                     ║
║ └─ Rechnungsdatum: ---                            ║
║                                                    ║
║ 👤 VERKÄUFER:                                     ║
║ └─ Anton Süß (VK-Nr: 2000)                       ║
╚═══════════════════════════════════════════════════╝
```

**Vorteile:**
- ✅ Detaillierte Infos ohne Überladung
- ✅ Bei Bedarf abrufbar
- ✅ Für Nachfragen/Controlling

---

## 🎯 EMPFOHLENES DESIGN (Kombination)

### LÖSUNG: Option 1 + Option 2

**Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│ 📊 AUSLIEFERUNGEN DETAIL                                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Filter: [November ▼] [2025 ▼] [Alle Standorte ▼] [Alle VK ▼] │
│                                                                 │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│ │ UMSATZ       │ DECKUNGSBEI. │ Ø DB%        │ FAHRZEUGE    │ │
│ │ 670.129 €    │ 95.428 €     │ 14,2% ✅     │ 31           │ │
│ └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 👤 Anton Süß               Fzg: 2 │ Umsatz: 56.890€ │ DB: 8.450€│
│ ├─────────────────────────────────────────────────────────────│
│ │ 🆕 Neuwagen (0)                  0€      0€     0€   ---     │
│ │                                                               │
│ │ 🧪 Test/Vorführ (1)         20.390€  20.390€ 2.150€  10,5%✅│
│ │   • Corsa Edition ... (1x)   20.390€  DB: 2.150€ (10,5%)   │
│ │                                                               │
│ │ ♻️ Gebraucht (1)              36.500€  36.500€ 6.300€  17,3%✅│
│ │   • IONIQ 6 Allrad... (1x)   36.500€  DB: 6.300€ (17,3%)   │
│ └─────────────────────────────────────────────────────────────│
│                                                                 │
│ 👤 Edeltraud Punzmann      Fzg: 5 │ Umsatz: 87.450€ │ DB: 12.300€│
│ ├─────────────────────────────────────────────────────────────│
│ │ 🆕 Neuwagen (4)              75.200€  75.200€ 9.800€  13,0%✅│
│ │   • Grandland X ... (2x)     42.800€  DB: 5.600€ (13,1%)   │
│ │   • Astra Sports ... (1x)    19.900€  DB: 2.500€ (12,6%)   │
│ │   • Mokka Edition (1x)       12.500€  DB: 1.700€ (13,6%)   │
│ │                                                               │
│ │ 🧪 Test/Vorführ (0)              0€      0€     0€   ---     │
│ │                                                               │
│ │ ♻️ Gebraucht (1)              12.250€  12.250€ 2.500€  20,4%✅│
│ │   • i20 1.2 ... (1x)         12.250€  DB: 2.500€ (20,4%)   │
│ └─────────────────────────────────────────────────────────────│
│                                                                 │
│ [Weitere Verkäufer...]                                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘

📊 [Excel Export] [PDF Export] [Drucken]
```

---

## 🔢 BERECHNUNGSLOGIK

### SQL-Query für Auslieferungen mit Finanzdaten:

```sql
SELECT
    s.salesman_number,
    COALESCE(e.first_name || ' ' || e.last_name, 'Verkäufer #' || s.salesman_number) as verkaufer_name,
    
    -- Fahrzeugtyp
    s.dealer_vehicle_type,
    s.model_description,
    
    -- Anzahl
    COUNT(*) as anzahl,
    
    -- Finanzen pro Gruppe
    SUM(s.out_sale_price) as umsatz_gesamt,
    SUM(s.netto_price) as einkauf_gesamt,
    SUM(s.out_sale_price - s.netto_price) as deckungsbeitrag_gesamt,
    
    -- Durchschnittliche DB%
    ROUND(
        AVG(
            CASE 
                WHEN s.netto_price > 0 
                THEN ((s.out_sale_price - s.netto_price) / s.netto_price * 100)
                ELSE 0 
            END
        ), 
        1
    ) as db_prozent_durchschnitt

FROM sales s
LEFT JOIN employees e ON s.salesman_number = e.locosoft_id

WHERE strftime('%Y', s.out_invoice_date) = '2025'
  AND strftime('%m', s.out_invoice_date) = '11'
  AND s.out_invoice_date IS NOT NULL
  AND s.salesman_number IS NOT NULL
  
  -- Dedup-Filter (wichtig!)
  AND NOT EXISTS (
      SELECT 1 
      FROM sales s2 
      WHERE s2.vin = s.vin 
          AND s2.out_sales_contract_date = s.out_sales_contract_date
          AND s2.dealer_vehicle_type IN ('T', 'V')
          AND s.dealer_vehicle_type = 'N'
  )

GROUP BY 
    s.salesman_number, 
    verkaufer_name, 
    s.dealer_vehicle_type, 
    s.model_description

ORDER BY 
    verkaufer_name, 
    s.dealer_vehicle_type, 
    s.model_description;
```

### KPI-Query (für die Kacheln oben):

```sql
SELECT
    COUNT(*) as anzahl_fahrzeuge,
    SUM(s.out_sale_price) as umsatz_gesamt,
    SUM(s.netto_price) as einkauf_gesamt,
    SUM(s.out_sale_price - s.netto_price) as db_gesamt,
    
    ROUND(
        AVG(
            CASE 
                WHEN s.netto_price > 0 
                THEN ((s.out_sale_price - s.netto_price) / s.netto_price * 100)
                ELSE 0 
            END
        ), 
        1
    ) as db_prozent_durchschnitt

FROM sales s

WHERE strftime('%Y', s.out_invoice_date) = '2025'
  AND strftime('%m', s.out_invoice_date) = '11'
  AND s.out_invoice_date IS NOT NULL
  AND s.salesman_number IS NOT NULL
  
  -- Dedup-Filter
  AND NOT EXISTS (
      SELECT 1 
      FROM sales s2 
      WHERE s2.vin = s.vin 
          AND s2.out_sales_contract_date = s.out_sales_contract_date
          AND s2.dealer_vehicle_type IN ('T', 'V')
          AND s.dealer_vehicle_type = 'N'
  );
```

---

## 🎨 FARB-CODIERUNG (für DB%)

```javascript
// JavaScript Funktion für Farben
function getDBColor(dbPercent) {
    if (dbPercent >= 15) return 'success';  // Grün (sehr gut)
    if (dbPercent >= 10) return 'info';     // Blau (gut)
    if (dbPercent >= 5) return 'warning';   // Orange (mittel)
    return 'danger';                         // Rot (schlecht)
}

// Emoji-Variante
function getDBEmoji(dbPercent) {
    if (dbPercent >= 15) return '✅';  // Sehr gut
    if (dbPercent >= 10) return '✅';  // Gut
    if (dbPercent >= 5) return '⚠️';   // Mittel
    return '❌';                        // Schlecht
}
```

**Bootstrap CSS:**
```html
<span class="badge bg-success">15,2% ✅</span>  <!-- Grün -->
<span class="badge bg-info">12,8% ✅</span>     <!-- Blau -->
<span class="badge bg-warning">7,5% ⚠️</span>   <!-- Orange -->
<span class="badge bg-danger">3,2% ❌</span>    <!-- Rot -->
```

---

## 📱 RESPONSIVE DESIGN

### Desktop (> 1200px):
- Alle Spalten sichtbar (Anzahl, Umsatz, DB, DB%)

### Tablet (768px - 1200px):
- Wichtigste Spalten (Anzahl, Umsatz, DB%)
- Einkauf ausgeblendet (berechenbar)

### Mobile (< 768px):
- Nur Anzahl und DB%
- Klick für Details

---

## 🔒 BERECHTIGUNGEN & DATENSCHUTZ

**⚠️ WICHTIG:**
```
Deckungsbeiträge = VERTRAULICHE GESCHÄFTSDATEN!

Nur sichtbar für:
✅ Geschäftsführung
✅ Verkaufsleitung
✅ Controlling
❌ NICHT für normale Verkäufer!

→ Berechtigungs-Check in API implementieren
→ Separate Route: /verkauf/auslieferung/detail/finanz
```

**Implementierung:**
```python
@verkauf_api.route('/auslieferung/detail/finanz', methods=['GET'])
@requires_role(['geschaeftsfuehrung', 'verkaufsleitung', 'controlling'])
def get_auslieferung_detail_finanz():
    # Nur für berechtigte Benutzer
    # Zeigt Deckungsbeiträge
    pass
```

---

## ⚠️ EDGE CASES

### Fall 1: netto_price ist NULL
```sql
COALESCE(s.netto_price, 0) 

→ DB wird 0
→ Anzeige: "Keine EK-Daten" statt 0%
```

### Fall 2: out_sale_price ist NULL
```sql
WHERE s.out_sale_price IS NOT NULL
  AND s.netto_price IS NOT NULL

→ Fahrzeuge ohne Preise ausschließen
```

### Fall 3: Negativer Deckungsbeitrag
```sql
-- Kann vorkommen bei:
- Garantie-Kulanz
- Inzahlungnahme über Wert
- Rabatt-Aktionen

→ Trotzdem anzeigen (mit roter Farbe)
→ Emoji: ❌
```

### Fall 4: DB% > 50%
```sql
-- Kann sein bei Gebrauchtwagen
-- Aber: Prüfen ob Datenfehler!

→ Wenn > 50%: Warnung anzeigen
→ "Bitte Einkaufspreis prüfen!"
```

---

## 🚀 UMSETZUNGSPLAN

### Phase 1: Backend (API-Erweiterung)
**Zeit: 2-3 Stunden**

1. ✅ API-Endpoint erweitern: `/api/verkauf/auslieferung/detail/finanz`
2. ✅ KPI-Endpoint: `/api/verkauf/auslieferung/kpis`
3. ✅ SQL-Queries mit Finanz-Berechnungen
4. ✅ Dedup-Filter integrieren (wichtig!)
5. ✅ NULL-Handling
6. ✅ Testing

### Phase 2: Frontend (UI)
**Zeit: 3-4 Stunden**

1. ✅ KPI-Kacheln oben hinzufügen
2. ✅ Tabelle erweitern (Umsatz, DB, DB% Spalten)
3. ✅ Farb-Codierung implementieren
4. ✅ Responsive Design
5. ✅ Detail-Modal (optional)
6. ✅ Export-Funktionen (Excel, PDF)

### Phase 3: Berechtigungen
**Zeit: 1-2 Stunden**

1. ✅ Rollen-Check implementieren
2. ✅ Separate Route für Finanz-Daten
3. ✅ UI: Nur berechtigten Usern anzeigen
4. ✅ Testing mit verschiedenen Rollen

### Phase 4: Testing & Rollout
**Zeit: 2 Stunden**

1. ✅ Plausibilitäts-Check (Summen stimmen?)
2. ✅ Edge Cases testen
3. ✅ Mit echten Daten testen (November 2025)
4. ✅ Feedback einholen (Verkaufsleitung)
5. ✅ Anpassungen
6. ✅ Deployment

**GESAMT: 1-2 Tage**

---

## 📊 BEISPIEL-AUSGABE (Mockup)

```
╔══════════════════════════════════════════════════════════════════════╗
║ 📊 AUSLIEFERUNGEN DETAIL - NOVEMBER 2025                             ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║ ┌────────────┬───────────────┬───────────────┬──────────────────┐   ║
║ │ UMSATZ     │ DECKUNGSBEI.  │ Ø DB%         │ FAHRZEUGE        │   ║
║ │ 670.129 €  │ 95.428 €      │ 14,2% ✅      │ 31               │   ║
║ └────────────┴───────────────┴───────────────┴──────────────────┘   ║
║                                                                       ║
║ ┌─────────────────────────────────────────────────────────────────┐ ║
║ │ 👤 Anton Süß          Fzg: 2 │ 56.890€ │ 8.450€ │ 14,8% ✅    │ ║
║ ├─────────────────────────────────────────────────────────────────┤ ║
║ │ 🆕 Neuwagen (0)            0€      0€     0€    ---             │ ║
║ │ 🧪 Test/Vorführ (1)   20.390€  20.390€ 2.150€  10,5% ✅        │ ║
║ │   • Corsa Edition          20.390€    DB: 2.150€ (10,5%)      │ ║
║ │ ♻️ Gebraucht (1)       36.500€  36.500€ 6.300€  17,3% ✅        │ ║
║ │   • IONIQ 6 Allrad...      36.500€    DB: 6.300€ (17,3%)      │ ║
║ └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║ ┌─────────────────────────────────────────────────────────────────┐ ║
║ │ 👤 Edeltraud Punzmann Fzg: 5 │ 87.450€ │ 12.300€ │ 14,1% ✅   │ ║
║ ├─────────────────────────────────────────────────────────────────┤ ║
║ │ 🆕 Neuwagen (4)       75.200€  75.200€ 9.800€  13,0% ✅        │ ║
║ │   • Grandland X (2x)       42.800€    DB: 5.600€ (13,1%)      │ ║
║ │   • Astra Sports (1x)      19.900€    DB: 2.500€ (12,6%)      │ ║
║ │   • Mokka Edition (1x)     12.500€    DB: 1.700€ (13,6%)      │ ║
║ │ 🧪 Test/Vorführ (0)        0€      0€     0€    ---             │ ║
║ │ ♻️ Gebraucht (1)       12.250€  12.250€ 2.500€  20,4% ✅        │ ║
║ │   • i20 1.2 (1x)           12.250€    DB: 2.500€ (20,4%)      │ ║
║ └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║ [Weitere 8 Verkäufer...]                                             ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════╝

📊 [Excel Export] [PDF Export] [Drucken]
```

---

## ✅ ERFOLGS-KRITERIEN

- [ ] KPIs werden korrekt berechnet (Umsatz, DB, DB%)
- [ ] Pro Verkäufer kumuliert sichtbar
- [ ] Pro Fahrzeugtyp kumuliert sichtbar
- [ ] Einzelfahrzeuge mit Details
- [ ] Farb-Codierung funktioniert
- [ ] Dedup-Filter aktiv (keine Doppelzählungen)
- [ ] Nur berechtigte User sehen Finanzdaten
- [ ] Responsive Design funktioniert
- [ ] Export-Funktionen vorhanden
- [ ] Performance OK (< 2 Sek. Ladezeit)

---

**Version:** 1.0  
**Erstellt:** 11.11.2025  
**Status:** Konzept-Phase  
**Nächster Schritt:** Feedback einholen → Umsetzung
