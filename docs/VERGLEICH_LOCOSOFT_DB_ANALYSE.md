# 📊 VERGLEICH: LOCOSOFT EXCEL vs. DATENBANK
## Analyse Oktober 2025

**Datum:** 11.11.2025  
**Quelle:** LocoSoft Abrechnungsliste Oktober 2025

---

## 💰 IST-ZAHLEN (aus LocoSoft Excel)

### GESAMT-KPIs Oktober 2025:
```
Umsatz (Brutto):     2.303.135,53 EUR
Umsatz (Netto):      1.956.127,46 EUR
Deckungsbeitrag:        59.794,27 EUR
Ø DB%:                      10,18 %
Anzahl Fahrzeuge:              129
```

### TOP 3 Verkäufer (nach DB):
```
1. VK-2007 (11 Fzg):   219.532€ Umsatz │ 20.628€ DB │ 11,6% DB%
2. VK-2005 (13 Fzg):   270.791€ Umsatz │ 20.368€ DB │ 12,6% DB%
3. VK-2004 (22 Fzg):   388.728€ Umsatz │ 16.420€ DB │  7,0% DB%
```

### Nach Fahrzeugart:
```
Neuwagen (65):       1.162.489€ │  49.217€ DB │  5,2% DB%
Gebraucht (57):        977.556€ │   5.500€ DB │ 14,7% DB%
Vorführ/Test (7):      163.090€ │   5.077€ DB │  4,0% DB%
```

---

## 🔍 WICHTIGE ERKENNTNISSE

### 1. Excel-Spalten die wir haben:
```
✅ Rg.Brutto          → Verkaufspreis (was im System als out_sale_price)
✅ Rg.Netto           → Netto-Verkaufspreis
✅ Deckungsbeitrag    → Fertig berechnet! (Bruttoertrag)
✅ DB %               → Fertig berechnet! (Deckungsbeitrag in %)
✅ verk. VKB          → Verkäufer-Nummer
✅ Fz.-Art            → Fahrzeugart (N/D/G/T/V)
✅ Rg-Datum           → Rechnungsdatum
```

### 2. Berechnungslogik in LocoSoft:
```
Deckungsbeitrag = Rg.Netto - (Fahrzeuggrundpreis + Kosten)

NICHT einfach:
Deckungsbeitrag ≠ out_sale_price - netto_price

LocoSoft berücksichtigt:
- Fahrzeuggrundpreis
- Zubehör
- Fracht/Brief/Nebenkosten
- Einsatzer

höhungen
- Abschreibungen
- Verkaufsunterlagen
- Variable Kosten
- Kalkulationskosten
```

---

## ⚠️ PROBLEM: Unsere DB hat NICHT den Deckungsbeitrag!

### Was wir in der sales-Tabelle haben:
```sql
out_sale_price  -- Verkaufspreis (Brutto) ✅
netto_price     -- Einkaufspreis (Netto) ✅
```

### Was wir NICHT haben:
```
❌ Deckungsbeitrag (fertig berechnet)
❌ Alle Kostenkomponenten
❌ Abschreibungen
❌ Variable Kosten
❌ Kalkulationskosten
```

### Was wir berechnen können:
```
Rohertrag = out_sale_price - netto_price

ABER: Das ist NICHT der Deckungsbeitrag!
→ Rohertrag ist höher als Deckungsbeitrag
→ Deckungsbeitrag = Rohertrag - Kosten
```

---

## 💡 LÖSUNG: 2-Phasen-Ansatz

### Phase 1: ROHERTRAG anzeigen (SOFORT möglich)
```
Rohertrag = out_sale_price - netto_price

Anzeige im Frontend:
"Rohertrag: 2.150€ (10,5%)"
"⚠️ Hinweis: Ohne Berücksichtigung von Kosten/Abschreibungen"
```

**Vorteile:**
✅ Sofort umsetzbar (haben alle Daten)
✅ Gibt erste Einschätzung
✅ Besser als keine Kennzahl

**Nachteile:**
⚠️ Ungenau (höher als echter DB)
⚠️ Keine Kosten berücksichtigt

---

### Phase 2: ECHTER DECKUNGSBEITRAG (später, mit LocoSoft-Import)

**Option A: Erweitere LocoSoft-Sync**
```python
# In master_sync.py oder neuem Script:
# Importiere auch Deckungsbeitrag aus LocoSoft

ALTER TABLE sales ADD COLUMN deckungsbeitrag REAL;
ALTER TABLE sales ADD COLUMN db_prozent REAL;
ALTER TABLE sales ADD COLUMN fahrzeuggrundpreis REAL;
ALTER TABLE sales ADD COLUMN kosten_gesamt REAL;

# Dann bei jedem Sync:
UPDATE sales SET
    deckungsbeitrag = [aus LocoSoft],
    db_prozent = [aus LocoSoft],
    ...
```

**Option B: Importiere Excel-Daten direkt**
```python
# Script: import_locosoft_verkaufsstatistik.py
# Liest monatliche Excel-Dateien
# Updated bestehende Verkäufe mit Finanz-Daten
```

---

## 🎯 EMPFOHLENER UMSETZUNGSPLAN

### JETZT (Tag 30/31): Phase 1 - Rohertrag
**Zeit: 3-4 Stunden**

1. **API erweitern** (1h)
   ```python
   # Berechne Rohertrag in SQL:
   SELECT
       out_sale_price,
       netto_price,
       (out_sale_price - netto_price) as rohertrag,
       CASE 
           WHEN netto_price > 0 
           THEN ((out_sale_price - netto_price) / netto_price * 100)
           ELSE 0 
       END as rohertrag_prozent
   ```

2. **Frontend anpassen** (2h)
   - KPI-Kacheln mit Rohertrag
   - Tabelle mit Rohertrag-Spalten
   - Hinweis: "Rohertrag (vor Kosten)"
   - Farb-Codierung

3. **Testing** (1h)
   - Vergleich mit Excel-Werten
   - Dokumentation der Abweichung

**Ergebnis:**
```
✅ Verkaufsleitung kann Rohertrag sehen
✅ Erste Einschätzung möglich
⚠️ Mit Hinweis dass Kosten fehlen
```

---

### SPÄTER (Tag 35+): Phase 2 - Echter Deckungsbeitrag
**Zeit: 1-2 Tage**

1. **LocoSoft-Sync erweitern** (4h)
   - Schema-Migration (neue Spalten)
   - Sync-Script anpassen
   - Import aus Excel oder direkt aus LocoSoft-DB

2. **API umstellen** (2h)
   - Verwende `deckungsbeitrag` statt Rohertrag
   - Entferne Hinweis

3. **Testing & Rollout** (2h)

**Ergebnis:**
```
✅ Exakte Werte wie in LocoSoft
✅ Deckungsbeitrag = Rohertrag - Kosten
✅ Volle Transparenz
```

---

## 📊 VERGLEICH: Rohertrag vs. Deckungsbeitrag

### Beispiel: Opel Frontera (aus Excel)
```
Verkaufspreis (Brutto):    20.390,20 EUR
Verkaufspreis (Netto):     17.134,62 EUR
Fahrzeuggrundpreis:        18.678,17 EUR
Kosten (Summe):            21.522,70 EUR
Deckungsbeitrag (echt):       940,09 EUR  ← LocoSoft
DB%:                            5,20 %    ← LocoSoft

---

Was wir berechnen könnten (Rohertrag):
out_sale_price:            20.390,20 EUR
netto_price:               ~18.240,00 EUR (geschätzt)
Rohertrag:                 ~2.150,00 EUR  ← Unsere Berechnung
Rohertrag%:                   ~10,5 %     ← Unsere Berechnung

DIFFERENZ: ~1.210 EUR (Kosten!)
```

### Interpretation:
```
Rohertrag:       2.150€  (was wir zeigen können)
- Kosten:       -1.210€  (was wir NICHT haben)
= Deckungsbeitrag: 940€  (LocoSoft-Realität)

→ Unser Rohertrag ist ca. 2x höher als echter DB!
```

---

## 🎨 UI-MOCKUP (Phase 1 - mit Rohertrag)

```
┌────────────────────────────────────────────────────────────────┐
│ 📊 AUSLIEFERUNGEN DETAIL - OKTOBER 2025                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ⚠️ HINWEIS: Rohertrag (vor Abzug von Kosten/Abschreibungen)   │
│            Für exakte Werte siehe LocoSoft-Abrechnungsliste   │
│                                                                 │
│ ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│ │ UMSATZ       │ ROHERTRAG    │ Ø RE%        │ FAHRZEUGE    │ │
│ │ 2.303.136 €  │ ~95.000 € (?) │ ~4% (?)     │ 129          │ │
│ └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│ 👤 VK-2007          Fzg: 11 │ Umsatz: 219.532€ │ RE: ~35.000€│
│ ├────────────────────────────────────────────────────────────│
│ │ 🆕 Neuwagen (8)      180.450€   RE: ~28.000€  (~15%)  ⚠️  │
│ │ ♻️ Gebraucht (3)       39.082€   RE: ~7.000€   (~18%)  ⚠️  │
│ └────────────────────────────────────────────────────────────│
│                                                                 │
│ ℹ️ RE = Rohertrag (Verkaufspreis - Einkaufspreis)             │
│    Echter Deckungsbeitrag ist niedriger (ca. 50% vom RE)      │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 ENTSCHEIDUNG ERFORDERLICH

### Option 1: Zeige Rohertrag (JETZT)
**Pro:**
- ✅ Schnell umsetzbar (3-4h)
- ✅ Besser als nichts
- ✅ Erste Einschätzung möglich

**Contra:**
- ⚠️ Ungenau (2x zu hoch)
- ⚠️ Verwirrt evt. Nutzer
- ⚠️ Muss mit Disclaimer

**Empfehlung:** ⚠️ NUR wenn Verkaufsleitung das explizit will!

---

### Option 2: Warte auf echten DB (Phase 2)
**Pro:**
- ✅ Exakte Werte
- ✅ Keine Verwirrung
- ✅ Professionell

**Contra:**
- ⏳ Dauert länger (1-2 Tage)
- ⏳ Mehr Aufwand

**Empfehlung:** ✅ BESSER! Lieber richtig als schnell.

---

### Option 3: Hybrid-Ansatz (EMPFOHLEN)
1. **Sofort:** Zeige nur Umsatz (ohne Ertrag)
   ```
   ✅ Umsatz pro Verkäufer
   ✅ Anzahl Fahrzeuge
   ❌ Kein Deckungsbeitrag (noch nicht)
   ```

2. **Nächste Woche:** Importiere echte DB-Werte
   ```
   ✅ LocoSoft-Sync erweitern
   ✅ Echte Deckungsbeiträge
   ✅ Exakte Kennzahlen
   ```

**Vorteile:**
- ✅ Kein falscher Eindruck
- ✅ Professionell
- ✅ Später: Vollständig

---

## 📝 NÄCHSTE SCHRITTE

### JETZT - Feedback einholen:
```
Frage an Verkaufsleitung/Geschäftsführung:

"Wir können entweder:

A) Rohertrag anzeigen (schnell, aber ungenau - ca. 2x zu hoch)
B) Nur Umsatz anzeigen, Deckungsbeitrag kommt nächste Woche
C) 1-2 Tage warten und direkt echte DB-Werte importieren

Was ist euch lieber?"
```

### Option A gewählt → Umsetzen:
1. API mit Rohertrag-Berechnung
2. Frontend mit Disclaimer
3. Testing mit Oktober-Daten
4. Deployment

### Option B/C gewählt → LocoSoft-Import:
1. Schema-Migration (neue Spalten)
2. Import-Script (aus Excel oder LocoSoft-DB)
3. API mit echten DB-Werten
4. Frontend ohne Disclaimer
5. Testing & Deployment

---

## 📊 DATENQUALITÄT (aus Excel-Analyse)

### Was funktioniert:
✅ Alle 129 Verkäufe haben Finanz-Daten
✅ Deckungsbeitrag ist berechnet
✅ DB% ist berechnet
✅ Verkäufer-Zuordnung stimmt

### Was auffällt:
⚠️ VK-2000: Negativer DB (-4.835€)
⚠️ VK-2002: Negativer DB (-20.941€)
⚠️ Einige Verkäufe mit DB% < 1% (Problemfälle)

### Empfehlung:
→ Bei negativem DB: Rot markieren im Frontend
→ Bei DB% < 5%: Orange markieren (Warnung)
→ Klick auf Fahrzeug → Details/Erklärung

---

**Version:** 1.0  
**Erstellt:** 11.11.2025  
**Status:** Analyse abgeschlossen - Entscheidung erforderlich
