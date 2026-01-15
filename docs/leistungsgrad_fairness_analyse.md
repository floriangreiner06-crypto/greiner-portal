# Leistungsgrad-Berechnung: Fairness & Validität Analyse

**Datum:** 2026-01-14  
**Basierend auf:** Internet-Recherche zu Best Practices

---

## Standard-Formel (Branchenüblich)

### Definition

Der **Leistungsgrad** ist eine zentrale Kennzahl in Kfz-Werkstätten, die das Verhältnis zwischen der **tatsächlich erbrachten Arbeitsleistung** und der **vorgegebenen Soll-Leistung** misst.

### Standard-Formel

```
Leistungsgrad = (Ist-Leistung / Soll-Leistung) × 100
```

**Dabei:**
- **Ist-Leistung:** Tatsächlich erbrachte Arbeitsleistung in AW (Arbeitswerten)
- **Soll-Leistung:** Vorgegebene Arbeitsleistung in AW (basierend auf Herstellervorgaben)

**Beispiel:**
- Mechaniker hat 9 AW erbracht
- Vorgabe war 10 AW
- Leistungsgrad = (9 / 10) × 100 = **90%**

**Interpretation:**
- **100%** = Vorgabezeit genau erreicht
- **> 100%** = Schneller als Vorgabe (gut!)
- **< 100%** = Langsamer als Vorgabe

---

## DRIVE-Formel (Aktuell)

### Aktuelle Berechnung

```
Leistungsgrad = (AW in Stunden / Stempelzeit_Leistungsgrad in Stunden) × 100
```

**Dabei:**
- **AW in Stunden:** Erfasste Arbeitswerte (AW-Anteil) in Stunden
- **Stempelzeit_Leistungsgrad:** Erste bis letzte Stempelung minus Lücken/Pausen

**Beispiel:**
- Mechaniker hat 10 AW erfasst (= 1.0 Stunde)
- Stempelzeit_Leistungsgrad = 0.75 Stunden (45 Min)
- Leistungsgrad = (1.0 / 0.75) × 100 = **133.3%**

---

## Vergleich: Standard vs. DRIVE

### Unterschiede

| Aspekt | Standard-Formel | DRIVE-Formel |
|--------|----------------|--------------|
| **Zähler** | Ist-Leistung (AW) | AW in Stunden |
| **Nenner** | Soll-Leistung (AW) | Stempelzeit_Leistungsgrad (Stunden) |
| **Vergleich** | AW vs. AW | AW vs. Zeit |
| **Interpretation** | Wie viel AW wurden erbracht vs. Vorgabe? | Wie viel AW pro Stunde? |

### Kritische Analyse

**1. Standard-Formel:**
- ✅ **Direkter Vergleich:** AW erbracht vs. AW vorgegeben
- ✅ **Einfach verständlich:** "Habe ich die Vorgabe erreicht?"
- ✅ **Branchenüblich:** Wird in vielen Werkstätten so verwendet
- ⚠️ **Problem:** Berücksichtigt nicht die tatsächliche Arbeitszeit

**2. DRIVE-Formel:**
- ✅ **Berücksichtigt Arbeitszeit:** Zeigt Effizienz pro Stunde
- ✅ **Fairer bei Pausen:** Stempelzeit_Leistungsgrad berücksichtigt Pausen/Lücken
- ✅ **Proportionale Verteilung:** AW werden fair bei mehreren Mechanikern verteilt
- ⚠️ **Problem:** Nicht direkt vergleichbar mit Standard-Formel
- ⚠️ **Problem:** Interpretation ist anders ("AW pro Stunde" vs. "Vorgabe erreicht")

---

## Ist die DRIVE-Formel fair und valide?

### ✅ FAIR - Ja, aus folgenden Gründen:

**1. Proportionale AW-Verteilung**
- Wenn mehrere Mechaniker an einem Auftrag arbeiten, werden AW **proportional zur Stempelzeit** verteilt
- **Beispiel:** Auftrag mit 10 AW, Mechaniker A: 60 Min, Mechaniker B: 40 Min
  - Mechaniker A: 6 AW (fair!)
  - Mechaniker B: 4 AW (fair!)
- **Nicht:** 5 AW / 5 AW (unfair, wenn einer mehr gearbeitet hat)

**2. Berücksichtigung von Pausen/Lücken**
- Stempelzeit_Leistungsgrad berücksichtigt:
  - Pausenzeiten (z.B. 12:00-12:44)
  - Lücken zwischen Stempelungen (10-60 Min)
- **Fairer Vergleich:** Nur tatsächliche Arbeitszeit wird berücksichtigt

**3. Nur fakturierte Positionen**
- Nur verrechnete Arbeit zählt
- Keine "Luftbuchungen"
- **Realistische Bewertung**

### ⚠️ VALIDITÄT - Mit Einschränkungen:

**1. Abweichung zu Locosoft**
- DRIVE: 9.6 AW, Leistungsgrad 123.5%
- Locosoft: 10.0 AW, Leistungsgrad 133.0%
- **Differenz:** 0.4 AW, 9.5% Leistungsgrad
- **Ursache:** Locosoft berechnet AW-Ant. anders (noch nicht vollständig verstanden)
- **Status:** Support-Anfrage an Locosoft gestellt

**2. Unterschiedliche Interpretation**
- **Standard:** "Habe ich die Vorgabe erreicht?" (AW vs. AW)
- **DRIVE:** "Wie effizient war ich?" (AW pro Stunde)
- **Beide sind valide**, aber unterschiedliche Aussagen!

**3. Stempelzeit_Leistungsgrad vs. Stempelzeit**
- DRIVE verwendet **Stempelzeit_Leistungsgrad** (erste bis letzte minus Lücken/Pausen)
- **Vorteil:** Fairer, berücksichtigt Pausen
- **Nachteil:** Nicht direkt vergleichbar mit einfacher Stempelzeit

---

## Empfehlungen

### 1. Beide Formeln sind valide - unterschiedliche Aussagen

**Standard-Formel:**
- **Aussage:** "Habe ich die Vorgabe erreicht?"
- **Verwendung:** Vergleich mit Herstellervorgaben
- **Beispiel:** 9 AW erbracht, 10 AW vorgegeben = 90%

**DRIVE-Formel:**
- **Aussage:** "Wie effizient war ich pro Stunde?"
- **Verwendung:** Vergleich der tatsächlichen Effizienz
- **Beispiel:** 10 AW in 0.75 Stunden = 133.3%

### 2. DRIVE-Formel ist fairer für Team-Vergleiche

**Warum?**
- Berücksichtigt Pausen/Lücken (fairer Vergleich)
- Proportionale AW-Verteilung (fair bei mehreren Mechanikern)
- Nur fakturierte Arbeit (realistische Bewertung)

### 3. Verbesserungspotenzial

**Aktuell:**
- ⚠️ Abweichung zu Locosoft (0.4 AW, 9.5%)
- ⚠️ AW-Berechnung noch nicht exakt identisch

**Nächste Schritte:**
1. ✅ Support-Anfrage an Locosoft gestellt
2. ⏳ Auf Antwort von Locosoft warten
3. ⏳ AW-Berechnung anpassen, wenn Formel bekannt ist

---

## Fazit

### ✅ Die DRIVE-Formel ist FAIR

**Gründe:**
- Proportionale AW-Verteilung bei mehreren Mechanikern
- Berücksichtigung von Pausen/Lücken
- Nur fakturierte Positionen zählen
- Realistische Bewertung der tatsächlichen Effizienz

### ⚠️ Die DRIVE-Formel ist VALIDE - mit Einschränkungen

**Valide, weil:**
- Zeigt tatsächliche Effizienz (AW pro Stunde)
- Berücksichtigt alle relevanten Faktoren
- Fairer Vergleich zwischen Mechanikern

**Einschränkungen:**
- Abweichung zu Locosoft (wird geklärt)
- Unterschiedliche Interpretation als Standard-Formel
- Beide Formeln sind valide, aber unterschiedliche Aussagen!

### 📊 Vergleich

| Kriterium | Standard-Formel | DRIVE-Formel |
|-----------|----------------|--------------|
| **Fairness** | ✅ Fair | ✅✅ Fairer (berücksichtigt mehr Faktoren) |
| **Validität** | ✅ Valide | ✅ Valide (andere Aussage) |
| **Verständlichkeit** | ✅✅ Sehr einfach | ⚠️ Komplexer |
| **Team-Vergleich** | ⚠️ Schwierig | ✅✅ Sehr fair |
| **Pausen-Berücksichtigung** | ❌ Nein | ✅✅ Ja |

---

## Zusammenfassung für das Team

**Die DRIVE-Formel ist:**
- ✅ **FAIR:** Proportionale Verteilung, Pausen-Berücksichtigung
- ✅ **VALIDE:** Zeigt tatsächliche Effizienz
- ⚠️ **Unterschiedlich:** Andere Aussage als Standard-Formel
- ⚠️ **In Arbeit:** Abweichung zu Locosoft wird geklärt

**Beide Formeln sind korrekt - sie messen unterschiedliche Dinge:**
- **Standard:** "Vorgabe erreicht?" (AW vs. AW)
- **DRIVE:** "Effizienz pro Stunde?" (AW pro Stunde)

**DRIVE-Formel ist fairer für Team-Vergleiche!**
