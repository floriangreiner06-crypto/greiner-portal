# Anwesenheitsgrad - Recherche und Analyse TAG 181

**Datum:** 2026-01-12  
**Status:** ✅ Recherche abgeschlossen

---

## 📋 ZUSAMMENFASSUNG

Der **Anwesenheitsgrad** ist bereits im System definiert, wird aber **aktuell NICHT im Werkstatt-Dashboard angezeigt**. Die Berechnung ist möglich, benötigt aber die "bezahlte Zeit" (Soll-Zeit) als Basis.

---

## 🔍 INTERNET-RECHERCHE

### Definition

**Anwesenheitsgrad** = Anteil der tatsächlich geleisteten Anwesenheit im Verhältnis zur geplanten/bezahlten Anwesenheit.

**Formel:**
```
Anwesenheitsgrad (%) = (Anwesende Stunden / Bezahlte Stunden) × 100
```

### Bedeutung

- **Hoher Anwesenheitsgrad:** Hohe Präsenz, starkes Engagement
- **Niedriger Anwesenheitsgrad:** Mögliche Probleme (Motivation, Gesundheit, etc.)

### Benchmarks (branchenabhängig)

| Branche | Anwesenheitsgrad | Abwesenheitsquote |
|---------|------------------|-------------------|
| **Kfz-Gewerbe** | **~79%** | ~21% |
| Bildung | ≥80% | ≤20% |
| Gesundheitswesen | 88-93% | 7-12% |
| Allgemein | 85-90% | 10-15% |

**Für unser Feature (Kfz-Werkstatt):** Zielwert **~79%** ist korrekt!

**Begründung bei 40h/Woche:**
- 220 Arbeitstage × 8h = **1.760h bezahlt** (Jahr)
- Abzüglich ~370h (Urlaub, Krankheit, Schulung, Feiertage) = **~1.390h anwesend**
- → **79% Anwesenheitsgrad**

---

## ✅ AKTUELLER STAND IM SYSTEM

### 1. KPI-Definition vorhanden

**Datei:** `utils/kpi_definitions.py`

```python
def berechne_anwesenheitsgrad(anwesend_h: float, bezahlt_h: float) -> Optional[float]:
    """
    Berechnet den Anwesenheitsgrad.
    
    Formel: Anwesende Stunden / Bezahlte Stunden × 100
    
    Args:
        anwesend_h: Tatsächlich anwesende Stunden
        bezahlt_h: Bezahlte Stunden (Soll lt. Arbeitsvertrag)
        
    Returns:
        Anwesenheitsgrad in % (Ziel: ~79%)
    """
    if bezahlt_h is None or bezahlt_h <= 0:
        return None
    if anwesend_h is None or anwesend_h < 0:
        return None
    
    return round((anwesend_h / bezahlt_h) * 100, 1)
```

**Zielwert:** `ZIEL_ANWESENHEITSGRAD = 79.0` ✅

**Schwellenwerte:**
- Gut (✅): ≥ 75%
- Warnung (⚠️): ≥ 65%
- Kritisch (❌): < 65%

### 2. Datenverfügbarkeit

**Anwesenheit (Ist):** ✅ **Verfügbar**
- Wird bereits aus Locosoft geholt: `times` WHERE `type=1` (Anwesenheit)
- In `WerkstattData.get_mechaniker_leistung()` bereits enthalten:
  - `anwesenheit` (Minuten) pro Mechaniker
  - `gesamt_anwesenheit` (Minuten) gesamt

**Bezahlte Zeit (Soll):** ⚠️ **Muss berechnet werden**
- Nicht direkt in Locosoft verfügbar
- Muss berechnet werden: `Anzahl Arbeitstage × 8 Stunden × Anzahl Mechaniker`

### 3. Dashboard-Status

**Aktuell angezeigt:**
- ✅ Leistungsgrad (60.7% im Screenshot)
- ✅ Produktivität (86.8% im Screenshot)
- ✅ Effizienz (52.4% im Screenshot)
- ✅ Entgangener Umsatz

**NICHT angezeigt:**
- ❌ **Anwesenheitsgrad** (fehlt!)

**Erwähnung in Templates:**
- `templates/aftersales/werkstatt_finanz_kpis.html` - Zeile 576: `<span>Anwesenheitsgrad</span>`
- Aber: Wird nicht mit echten Daten befüllt (nur Platzhalter)

---

## 🎯 PASST DER ANWESENHEITSGRAD IN UNSER FEATURE?

### ✅ JA - Perfekt passend!

**Gründe:**
1. **Bereits definiert** in `utils/kpi_definitions.py` (SSOT)
2. **Daten verfügbar** (Anwesenheit aus Locosoft)
3. **Logische Ergänzung** zu den bestehenden KPIs:
   - **Anwesenheitsgrad:** Wie viel der bezahlten Zeit ist MA da? (79%)
   - **Produktivität:** Wie viel der Anwesenheit wird gestempelt? (90%)
   - **Leistungsgrad:** Wie schnell vs. Kalkulation? (100%)
   - **Effizienz:** Gesamtproduktivität (71%)

4. **Branchenstandard** für Kfz-Werkstätten
5. **Wertvoll für Management:** Zeigt Auslastung der Personalressourcen

---

## 💻 KÖNNEN WIR IHN BERECHNEN?

### ✅ JA - Mit Einschränkungen

**Was wir haben:**
- ✅ Anwesenheit (Ist) aus Locosoft: `times` WHERE `type=1`
- ✅ Anzahl Mechaniker
- ✅ Anzahl Arbeitstage (bereits berechnet in `get_mechaniker_leistung()`)

**Was wir berechnen müssen:**
- ⚠️ **Bezahlte Zeit (Soll):**
  - Option 1: `Anzahl Arbeitstage × 8h × Anzahl Mechaniker`
  - Option 2: `Anzahl Arbeitstage × 8h` (pro Mechaniker individuell)
  - Option 3: Aus `employees`-Tabelle: Individuelle Arbeitszeiten (falls vorhanden)

**Empfehlung:**
- **Option 1** für Gesamt-Übersicht (einfach, Standard 8h/Tag)
- **Option 2** für Mechaniker-Individualansicht (genauer)

**Beispiel-Berechnung:**
```python
# Gesamt-Anwesenheitsgrad
anzahl_tage = 8  # Arbeitstage im Zeitraum
anzahl_mechaniker = 10
bezahlt_h_gesamt = anzahl_tage * 8 * anzahl_mechaniker  # 640h
anwesend_h_gesamt = gesamt_anwesenheit / 60  # Minuten → Stunden
anwesenheitsgrad_gesamt = (anwesend_h_gesamt / bezahlt_h_gesamt) * 100

# Pro Mechaniker
bezahlt_h_pro_ma = anzahl_tage * 8  # 64h
anwesend_h_pro_ma = mechaniker['anwesenheit'] / 60
anwesenheitsgrad_pro_ma = (anwesend_h_pro_ma / bezahlt_h_pro_ma) * 100
```

---

## 📊 WIE IST DER MOMENTAN?

### Aktueller Status: **NICHT BERECHNET**

**Grund:** Bezahlte Zeit (Soll) wird nicht berechnet/angezeigt.

**Um den aktuellen Wert zu ermitteln:**
1. Daten aus `WerkstattData.get_mechaniker_leistung()` holen
2. Bezahlte Zeit berechnen (siehe oben)
3. Anwesenheitsgrad mit `berechne_anwesenheitsgrad()` berechnen

**Beispiel-Query (für aktuellen Monat):**
```python
from api.werkstatt_data import WerkstattData
from utils import berechne_anwesenheitsgrad

data = WerkstattData.get_mechaniker_leistung()
gesamt = data['gesamt']

# Bezahlte Zeit berechnen
anzahl_tage = data['anzahl_tage']  # z.B. 8
anzahl_mechaniker = data['anzahl_mechaniker']  # z.B. 10
bezahlt_h = anzahl_tage * 8 * anzahl_mechaniker  # 640h

# Anwesend (aus Daten)
anwesend_h = gesamt['anwesenheit'] / 60  # Minuten → Stunden

# Anwesenheitsgrad berechnen
anwesenheitsgrad = berechne_anwesenheitsgrad(anwesend_h, bezahlt_h)
```

---

## 🚀 EMPFEHLUNG: IMPLEMENTIERUNG

### Schritt 1: API erweitern

**Datei:** `api/werkstatt_data.py` → `get_mechaniker_leistung()`

**Ergänzung:**
```python
# Gesamt-Anwesenheitsgrad berechnen
gesamt_bezahlt_h = anzahl_tage * 8 * len(mechaniker_liste)
gesamt_anwesend_h = gesamt_anwesenheit / 60
gesamt_anwesenheitsgrad = berechne_anwesenheitsgrad(gesamt_anwesend_h, gesamt_bezahlt_h)

# Pro Mechaniker
for m in mechaniker_liste:
    bezahlt_h = m['tage'] * 8
    anwesend_h = m['anwesenheit'] / 60
    m['anwesenheitsgrad'] = berechne_anwesenheitsgrad(anwesend_h, bezahlt_h)
```

### Schritt 2: Dashboard erweitern

**Datei:** `templates/aftersales/werkstatt_uebersicht.html`

**Neue KPI-Card hinzufügen:**
- 4. Gauge: "Anwesenheitsgrad" (neben Leistungsgrad, Produktivität, Effizienz)
- Ziel: ≥ 79%
- Schwellenwerte: 75% (gut), 65% (Warnung), <65% (kritisch)

### Schritt 3: Mechaniker-Karten erweitern

**Anzeige pro Mechaniker:**
- Anwesenheitsgrad als zusätzliche Info
- Farbcodierung (grün/gelb/rot)

---

## 📝 ZUSAMMENFASSUNG

| Frage | Antwort |
|-------|---------|
| **Was ist Anwesenheitsgrad?** | Anteil Anwesenheit / Bezahlte Zeit × 100 |
| **Was sagt er aus?** | Wie viel der bezahlten Zeit ist MA tatsächlich da? |
| **Benchmark (Kfz)?** | **~79%** (wegen Urlaub, Krankheit, etc.) |
| **Passt in unser Feature?** | ✅ **JA** - Perfekt passend! |
| **Können wir ihn berechnen?** | ✅ **JA** - Mit berechneter "bezahlter Zeit" |
| **Wie ist er momentan?** | ❌ **NICHT BERECHNET** - Fehlt im Dashboard |

---

## 🔗 RELEVANTE DATEIEN

- `utils/kpi_definitions.py` - KPI-Definition (SSOT)
- `docs/KPI_DEFINITIONEN.md` - Dokumentation
- `api/werkstatt_data.py` - Datenquelle (Anwesenheit bereits vorhanden)
- `templates/aftersales/werkstatt_uebersicht.html` - Dashboard (Anzeige fehlt)

---

**Nächste Schritte:** Implementierung in API und Dashboard (siehe Empfehlung oben)
