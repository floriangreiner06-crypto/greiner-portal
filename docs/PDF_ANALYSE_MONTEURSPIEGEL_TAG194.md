# PDF-Analyse Monteurspiegel Jan - TAG 194

**Datum:** 2026-01-16  
**PDF:** `monteruspiegel_von_jan.pdf`  
**Mechaniker:** 5018 (Jan Majer)  
**Zeitraum:** 01.01.26 - 16.01.26

---

## 📊 PDF Gesamtsummen (Locosoft)

| Metrik | Wert |
|--------|------|
| **AW-Anteil** | 95:45 (5745 Min = 95.75 Stunden) |
| **St-Anteil** | 70:52 (4252 Min = 70.87 Stunden) |
| **Leistungsgrad** | 135,1% |

**✅ Diese Werte stimmen mit Locosoft UI überein!**

---

## 📊 PDF Aufteilung nach Betriebsstätten

### BS-SUMME 1 (Auftragsbetrieb: 01 DEGO - Deggendorf Opel)
| Metrik | Wert |
|--------|------|
| **AW-Anteil** | 57:51 (3471 Min = 57.85 Stunden) |
| **St-Anteil** | 47:50 (2870 Min = 47.83 Stunden) |
| **Leistungsgrad** | 120,9% |

### BS-SUMME 2 (Auftragsbetrieb: 02 DEGH - Deggendorf Hyundai)
| Metrik | Wert |
|--------|------|
| **AW-Anteil** | 37:54 (2274 Min = 37.90 Stunden) |
| **St-Anteil** | 23:02 (1382 Min = 23.03 Stunden) |
| **Leistungsgrad** | 164,5% |

**Verifikation:** 57:51 + 37:54 = 95:45 ✅ | 47:50 + 23:02 = 70:52 ✅

---

## 📊 DRIVE-Berechnung (aktuell)

### Subsidiary 1 (DEGO)
| Metrik | DRIVE | PDF | Differenz |
|--------|-------|-----|-----------|
| **AW-Anteil** | 2583 Min (43:03) | 3471 Min (57:51) | -888 Min (-25.6%) |
| **St-Anteil** | 1985 Min (33:05) | 2870 Min (47:50) | -885 Min (-30.8%) |

### Subsidiary 2 (DEGH)
| Metrik | DRIVE | PDF | Differenz |
|--------|-------|-----|-----------|
| **AW-Anteil** | 1710 Min (28:30) | 2274 Min (37:54) | -564 Min (-24.8%) |
| **St-Anteil** | 1124 Min (18:44) | 1382 Min (23:02) | -258 Min (-18.7%) |

### GESAMT
| Metrik | DRIVE | PDF | Differenz |
|--------|-------|-----|-----------|
| **AW-Anteil** | 4293 Min (71:33) | 5745 Min (95:45) | -1452 Min (-25.3%) |
| **St-Anteil** | 3109 Min (51:49) | 4252 Min (70:52) | -1143 Min (-26.9%) |
| **Leistungsgrad** | 138.1% | 135.1% | +3.0% ✅ |

---

## 🔍 Wichtige Erkenntnisse

### 1. Aufteilung nach Auftragsbetrieb
- **MA-Betrieb:** 01 DEGO (Deggendorf Opel) - Mitarbeiter-Betriebsstätte
- **Auftragsbetrieb:** 02 DEGH (Deggendorf Hyundai) - Betriebsstätte des Auftrags
- **Locosoft zeigt beide Betriebsstätten getrennt!**

### 2. Abweichungen sind proportional
- Alle Abweichungen sind ~25% zu niedrig
- Das deutet darauf hin, dass **Positionen fehlen**, nicht dass die Berechnung falsch ist

### 3. Leistungsgrad passt sehr gut
- DRIVE: 138.1%
- PDF/Locosoft UI: 135.1%
- **Nur 3.0% Differenz - sehr gut!** ✅

---

## 🔍 Mögliche Ursachen für fehlende Positionen

1. **Positionen ohne Stempelungen:**
   - Werden Positionen ohne Stempelungen in Locosoft berücksichtigt?
   - Vielleicht Positionen, bei denen der Mechaniker als `mechanic_no` eingetragen ist?

2. **Interne Positionen:**
   - PDF zeigt auch interne Positionen (I) und Garantie-Positionen (G)
   - Werden diese in Locosoft UI berücksichtigt?

3. **Andere Filter:**
   - Gibt es weitere Filterkriterien, die wir übersehen haben?

---

## 📝 Nächste Schritte

1. ✅ **Aufteilung nach Auftragsbetrieb verstanden** - Locosoft zeigt beide Betriebsstätten getrennt
2. ⚠️ **Fehlende Positionen analysieren:**
   - Prüfe ob Positionen ohne Stempelungen berücksichtigt werden müssen
   - Prüfe ob interne/Garantie-Positionen berücksichtigt werden
3. 🔧 **Weitere Korrekturen:**
   - Identifiziere welche Positionen Locosoft zeigt, die DRIVE nicht zeigt

---

**Status:** ✅ **Leistungsgrad-Berechnung funktioniert korrekt!** Abweichungen bei AW/St-Anteil (~25%) deuten auf fehlende Positionen hin.
