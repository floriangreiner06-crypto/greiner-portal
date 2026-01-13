# BWA-Prognose ML-Evaluation - Einschätzung

**Datum:** 2026-01-12  
**TAG:** 181  
**Ziel:** Einschätzung ob ML für BWA-Prognosen sinnvoll ist

---

## 📊 TEST-ERGEBNISSE

### Modell-Performance

| Modell | MAE | RMSE | R² | MAPE |
|--------|-----|------|----|----|
| **Random Forest** | **161,741 €** | 212,194 € | 0.282 | 80.1% |
| Gradient Boosting | 169,719 € | 224,971 € | 0.193 | 79.1% |
| **Statistische Baseline** | **231,342 €** | 294,490 € | -0.384 | 101.6% |

**Verbesserung durch ML:** +30.1% (MAE), +21.2% (MAPE)

### Feature Importance (Top 10)

1. **db2_rolling_3m** (82.1%) - Gleitender 3-Monats-Durchschnitt
2. **umsatz_lag1** (9.3%) - Vormonat-Umsatz
3. **db2_lag1** (4.0%) - Vormonat DB2
4. **db2_lag2** (2.4%) - Vorvorheriger Monat DB2
5. **monat** (0.8%) - Saisonalität
6. **wochentag_1** (0.4%) - Wochentag des 1. des Monats
7. **tage_im_monat** (0.3%) - Anzahl Tage
8. **offene_werkstatt_auftraege_lag1** (0.2%) - Offene Werkstatt-Aufträge (Vormonat)
9. **pipeline_nw_vk** (0.2%) - NW-Pipeline VK-Summe
10. **offene_werkstatt_aw** (0.2%) - Offene Werkstatt AW

### Offene Aufträge als Features

✅ **Relevant, aber nicht dominant:**
- Offene Werkstatt-Aufträge: Rang 8 & 10 (geringe Importance)
- NW-Pipeline: Rang 9 (geringe Importance)
- Offene Fahrzeug-Verträge: Rang 12-18 (sehr geringe Importance)

**Fazit:** Offene Aufträge tragen zur Prognose bei, aber der **gleitende Durchschnitt** ist bei weitem das wichtigste Feature.

---

## 💡 EINSCHÄTZUNG

### ✅ ML bringt signifikante Verbesserung

- **30% bessere Prognose** als statistische Baseline
- **Realistische Performance** (kein Overfitting nach Filterung)
- **Offene Aufträge helfen**, aber sind nicht entscheidend

### ⚠️ ABER: Wichtige Einschränkungen

1. **Datenbasis klein:** Nur 35 Monate → Modell könnte bei mehr Daten besser werden
2. **Feature-Dominanz:** 82% der Wichtigkeit kommt vom gleitenden Durchschnitt
3. **Komplexität vs. Nutzen:** ML ist komplexer, aber nur 30% besser
4. **Transparenz:** Statistische Methoden sind nachvollziehbarer

### 📋 Vergleich: ML vs. Verbesserte Statistik

| Aspekt | ML (Random Forest) | Verbesserte Statistik |
|--------|-------------------|----------------------|
| **Genauigkeit** | 30% besser | 10-15% besser (geschätzt) |
| **Transparenz** | Niedrig | Hoch |
| **Wartung** | Hoch (Re-Training) | Niedrig |
| **Erklärbarkeit** | Schwierig | Einfach |
| **Implementierung** | Komplex | Einfach |

---

## 🎯 EMPFEHLUNG

### Option 1: Verbesserte Statistik (EMPFOHLEN) ⭐

**Warum:**
- 30% Verbesserung rechtfertigt nicht die ML-Komplexität
- Statistische Methoden sind transparenter und wartungsfreundlicher
- Mit verbesserten Features (gewichteter Durchschnitt, Saisonalität) könnte man 15-20% erreichen

**Implementierung:**
```python
# Gewichteter 3-Monats-Durchschnitt (neueste Monate stärker)
db2_prognose = (db2_lag1 * 0.5 + db2_lag2 * 0.3 + db2_lag3 * 0.2)

# Saisonalitäts-Korrektur
saisonalitaet = db2_vorjahr / db2_rolling_12m
db2_prognose_korrigiert = db2_prognose * saisonalitaet

# Pipeline-Korrektur (offene Aufträge)
pipeline_boost = (offene_nw_vk * 0.1 + offene_werkstatt_aw * 0.05)
db2_final = db2_prognose_korrigiert + pipeline_boost
```

### Option 2: ML als Ergänzung (OPTIONAL)

**Nur wenn:**
- Mehr historische Daten verfügbar (> 60 Monate)
- Transparenz weniger wichtig
- Wartungsaufwand akzeptabel

**Implementierung:**
- ML-Prognose als "zweite Meinung" neben statistischer Prognose
- Beide Methoden anzeigen mit Confidence-Intervallen
- Nutzer kann wählen

---

## 🔍 FAZIT

**Ist ML "Blick in die Glaskugel"?**

**Teilweise JA:**
- Bei nur 35 Monaten Daten ist die Prognose unsicher
- 30% Verbesserung ist gut, aber nicht überwältigend
- Statistische Methoden sind transparenter

**ABER:**
- ML bringt messbare Verbesserung
- Mit mehr Daten könnte es besser werden
- Offene Aufträge als Features helfen (wenn auch gering)

**Finale Empfehlung:**
1. **Kurzfristig:** Verbesserte statistische Prognose implementieren
2. **Mittelfristig:** Mehr Daten sammeln (12-24 Monate)
3. **Langfristig:** ML erneut evaluieren mit größerer Datenbasis

---

## 📈 NÄCHSTE SCHRITTE

1. ✅ **Verbesserte Statistik implementieren**
   - Gewichteter Durchschnitt
   - Saisonalitäts-Korrektur
   - Pipeline-Korrektur (offene Aufträge)

2. ⏳ **Mehr Daten sammeln**
   - 12-24 Monate warten
   - ML erneut testen

3. 🔄 **ML optional später**
   - Nur wenn statistische Methoden nicht ausreichen
   - Als Ergänzung, nicht Ersatz
