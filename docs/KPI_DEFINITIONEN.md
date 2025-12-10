# KPI DEFINITIONEN - Single Source of Truth

**Stand:** TAG 110 (2025-12-09)  
**Modul:** `utils/kpi_definitions.py`

---

## 🎯 Grundsatz

> **Wenn wir ein KPI anzeigen, muss ÜBERALL und IMMER die gleiche Berechnung erfolgen!**

Alle KPI-Berechnungen sind zentral in `utils/kpi_definitions.py` definiert.

---

## 📊 KPI-Übersicht (Branchenstandard Kfz-Gewerbe)

| # | KPI | Formel | Ziel | Bedeutung |
|---|-----|--------|------|-----------|
| 1 | **Anwesenheitsgrad** | Anwesend / Bezahlt × 100 | ~79% | Wie viel der bezahlten Zeit ist MA da? |
| 2 | **Auslastungsgrad** | Gestempelt / Anwesend × 100 | 90% | Wie viel wird produktiv gestempelt? |
| 3 | **Leistungsgrad** | Vorgabe / Gestempelt × 100 | 100% | Wie schnell vs. Kalkulation? |
| 4 | **Effizienz** | 1 × 2 × 3 (oder Verkauft/Bezahlt) | ~71% | Gesamtproduktivität |
| 5 | **Entgangener Umsatz** | (Gest. - Vorg.) × AW-Preis | 0 € | Bei Überzeiten |
| 6 | **Std/Durchgang** | Verkaufte Std / Aufträge | ~1,8h | Auftragswert |
| 7 | **SVS** | Lohnumsatz / Verkaufte Std | variiert | Stundenverrechnungssatz |

---

## 1️⃣ Anwesenheitsgrad

```
ANWESENHEITSGRAD = Anwesende Stunden / Bezahlte Stunden × 100
```

**Zielwert:** ~79% (wegen Urlaub, Krankheit, Schulung, Feiertage)

**Beispiel bei 40h/Woche:**
- 220 Arbeitstage × 8h = 1.760h bezahlt
- Abzüglich ~370h (Urlaub, Krank, etc.) = ~1.390h anwesend
- → 79% Anwesenheitsgrad

```python
from utils import berechne_anwesenheitsgrad
ag = berechne_anwesenheitsgrad(anwesend_h=6.5, bezahlt_h=8)  # 81.3%
```

---

## 2️⃣ Auslastungsgrad (= Produktivität)

```
AUSLASTUNGSGRAD = Gestempelte Auftragsstunden / Anwesende Stunden × 100
```

**Zielwert:** 90%

**Bedeutung:** 10% "Verlust" ist normal für:
- Arbeitsplatz aufräumen
- Werkzeug holen
- Leerlauf morgens (auf Aufträge warten)

```python
from utils import berechne_auslastungsgrad
au = berechne_auslastungsgrad(gestempelt_h=7.2, anwesend_h=8)  # 90%
```

---

## 3️⃣ Leistungsgrad

```
LEISTUNGSGRAD = Vorgabe-AW / Gestempelte-AW × 100
```

**Zielwert:** 100% (>100% möglich und gut!)

| Vorgabe | Gestempelt | Leistungsgrad | Bedeutung |
|---------|------------|---------------|-----------|
| 10 AW | 10 AW | 100% | Genau wie kalkuliert |
| 10 AW | 8 AW | **125%** | Schneller! 👍 |
| 10 AW | 12 AW | 83% | Langsamer 👎 |

```python
from utils import berechne_leistungsgrad
lg = berechne_leistungsgrad(vorgabe_aw=10, gestempelt_aw=8)  # 125%
```

---

## 4️⃣ Effizienz (Gesamtproduktivität)

```
EFFIZIENZ = Anwesenheitsgrad × Auslastungsgrad × Leistungsgrad / 10000
         = Verkaufte Stunden / Bezahlte Stunden × 100
```

**Zielwert:** ~71% (0.79 × 0.90 × 1.00)

**Das ist die "Wahrheit"** - was kommt am Ende wirklich raus?

```python
from utils import berechne_effizienz

# Variante A: Aus Einzelwerten
eff = berechne_effizienz(anwesenheitsgrad=79, auslastungsgrad=90, leistungsgrad=100)

# Variante B: Direkt
eff = berechne_effizienz(verkauft_h=5.7, bezahlt_h=8)  # 71.3%
```

---

## 5️⃣ Entgangener Umsatz

```
ENTGANGENER UMSATZ = (Gestempelte-AW - Vorgabe-AW) × AW-Preis
```

**Wichtig:** Nur bei Überzeiten! Schneller arbeiten = 0 € (kein "Gewinn")

```python
from utils import berechne_entgangener_umsatz

# Langsamer als Vorgabe:
verlust = berechne_entgangener_umsatz(10, 12, 11.90)  # 23.80 €

# Schneller als Vorgabe:
verlust = berechne_entgangener_umsatz(10, 8, 11.90)   # 0.00 €
```

---

## 6️⃣ Stunden pro Durchgang

```
STD/DURCHGANG = Verkaufte Stunden / Anzahl Aufträge
```

**Branchenschnitt:** ~1,8 Stunden pro Werkstattdurchgang

**Bedeutung:** Wie "werthaltig" ist ein Auftrag?

```python
from utils import berechne_stunden_pro_durchgang
spd = berechne_stunden_pro_durchgang(verkauft_h=54, anzahl_auftraege=30)  # 1.8h
```

---

## 7️⃣ Stundenverrechnungssatz (SVS)

```
SVS_erzielt = Lohnumsatz / Verkaufte Stunden
SVS_vorgabe = Lohnumsatz / Vorgabe Stunden
```

**Liefert:** Erzielter SVS, Vorgabe-SVS, Differenz

```python
from utils import berechne_stundenverrechnungssatz
svs = berechne_stundenverrechnungssatz(
    lohnumsatz_eur=5400, 
    verkauft_h=54, 
    vorgabe_h=60
)
# {'erzielt': 100.00, 'vorgabe': 90.00, 'differenz': 10.00}
```

---

## 🔧 Komplett-Berechnung für einen Mechaniker

```python
from utils import berechne_mechaniker_kpis

kpis = berechne_mechaniker_kpis(
    anwesend_min=390,      # 6.5h (aus Stempelung type=1)
    gestempelt_min=330,    # 5.5h (aus Stempelung type=2)
    vorgabe_aw=50,         # Summe Vorgabe-AW
    bezahlt_h=8,           # Soll (40h/5 Tage)
    lohnumsatz_eur=595,    # Optional
    anzahl_auftraege=5     # Optional
)

# Liefert:
# - anwesenheitsgrad, auslastungsgrad, leistungsgrad, effizienz
# - Alle Status-Bewertungen (gut/warnung/kritisch + Icon + Farbe)
# - stunden_pro_durchgang, svs (wenn Daten vorhanden)
```

---

## 🎨 Formatierung

```python
from utils import format_euro, format_prozent, format_aw, format_stunden

format_euro(1234.56)      # "1.234,56 €"
format_prozent(85.5)      # "85,5%"
format_aw(12.5)           # "12,5 AW"
format_stunden(8.5)       # "8,5 h"
format_zeit_hhmm(510)     # "8:30"
```

---

## 📏 Schwellenwerte

| KPI | Gut (✅) | Warnung (⚠️) | Kritisch (❌) |
|-----|----------|--------------|---------------|
| Anwesenheitsgrad | ≥ 75% | ≥ 65% | < 65% |
| Auslastungsgrad | ≥ 85% | ≥ 75% | < 75% |
| Leistungsgrad | ≥ 85% | ≥ 70% | < 70% |
| Effizienz | ≥ 65% | ≥ 55% | < 55% |

---

## 🔄 Konvertierungen

```python
from utils import (
    minuten_zu_aw, aw_zu_minuten,
    minuten_zu_stunden, stunden_zu_minuten,
    aw_zu_stunden, stunden_zu_aw
)

# 1 AW = 6 Minuten = 0.1 Stunden
minuten_zu_aw(60)       # 10.0 AW
aw_zu_minuten(10)       # 60 min
aw_zu_stunden(10)       # 1.0 h
stunden_zu_aw(1)        # 10.0 AW
```

---

## ⚠️ Konstanten

```python
from utils import (
    MINUTEN_PRO_AW,           # 6
    STUNDEN_PRO_WOCHE,        # 40
    STUNDEN_PRO_TAG,          # 8
    ZIEL_ANWESENHEITSGRAD,    # 79.0
    ZIEL_AUSLASTUNGSGRAD,     # 90.0
    ZIEL_LEISTUNGSGRAD,       # 100.0
    ZIEL_EFFIZIENZ,           # 71.0
    ZIEL_STUNDEN_PRO_DURCHGANG # 1.8
)
```

---

## 🚨 WICHTIG: Aggregation

Bei Gesamt-Berechnungen **NICHT mitteln**, sondern **summieren**:

```python
# ❌ FALSCH
gesamt_lg = sum(einzelne_leistungsgrade) / len(einzelne_leistungsgrade)

# ✅ RICHTIG
from utils import berechne_gesamt_leistungsgrad
gesamt_lg = berechne_gesamt_leistungsgrad(
    total_vorgabe_aw=sum(alle_vorgaben),
    total_gestempelt_aw=sum(alle_stempelungen)
)
```

---

## 📁 Dateien

| Datei | Zweck |
|-------|-------|
| `utils/__init__.py` | Package mit allen Exports |
| `utils/kpi_definitions.py` | Alle KPI-Funktionen |
| `docs/KPI_DEFINITIONEN.md` | Diese Dokumentation |

---

*Letzte Aktualisierung: TAG 110 (2025-12-09)*
