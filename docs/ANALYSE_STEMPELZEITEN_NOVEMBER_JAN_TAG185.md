# Analyse: Stempelzeiten-Abweichung DRIVE vs. Locosoft - November 2025

**Datum:** 2026-01-13 (TAG 185)  
**Mitarbeiter:** 5018 (Jan Majer)  
**Zeitraum:** 01.11.2025 - 30.11.2025

---

## 📊 ÜBERSICHT DER WERTE

### Locosoft Original (Screenshot):
- **AW-Anteil**: 205:55 (205 Stunden 55 Minuten = 12.355 Minuten = 2.059,17 AW)
- **Stmp.Anteil**: 141:23 (141 Stunden 23 Minuten = 8.483 Minuten)
- **Sollzeit**: 140:00 (140 Stunden = 8.400 Minuten)
- **Anwesend**: 146:44 (146 Stunden 44 Minuten = 8.804 Minuten)
- **Produktiv**: 140:01 (140 Stunden 1 Minute = 8.401 Minuten)
- **A-Grad**: 105%
- **P-Grad**: 95%

### DRIVE (Datenbank-Abfrage):
- **AW (Vorgabe, alle)**: 1.904 AW
- **AW (Vorgabe, ohne interne)**: 1.477 AW
- **Stempelzeit (alle Stempelungen summiert)**: 57.377 Minuten
- **Stempelzeit (Zeit-Spanne, alle)**: 9.309 Minuten
- **Stempelzeit (Zeit-Spanne, ohne interne)**: 7.719 Minuten
- **Stempelzeit (Zeit-Spanne, ohne interne, nur abgerechnet)**: Wird berechnet...
- **Anwesenheit**: 9.727 Minuten
- **Arbeitstage**: 18 Tage

---

## 🔍 IDENTIFIZIERTE ABWEICHUNGEN

### 1. Stempelzeit (Produktiv) - GROSSE ABWEICHUNG ⚠️

| Quelle | Wert | Minuten |
|--------|------|---------|
| **Locosoft** | 141:23 | 8.483 |
| **DRIVE (alle Stempelungen summiert)** | - | 57.377 |
| **DRIVE (Zeit-Spanne, alle Aufträge > 31)** | - | 9.309 |
| **DRIVE (Zeit-Spanne, mit Leerlauf)** | - | 9.528 |
| **DRIVE (Zeit-Spanne, ohne interne, ohne Leerlauf)** | - | 7.719 |
| **Leerlauf (order_number = 31)** | - | 212 |
| **Differenz** | - | +764 bis +48.894 |

**Erkenntnis:** 
- Locosoft zeigt 8.483 Minuten
- DRIVE Zeit-Spanne (ohne interne) zeigt 7.719 Minuten
- **Differenz: +764 Minuten** (etwa 12,7 Stunden = 34,7 Minuten pro Tag)
- **Mögliche Ursachen:**
  - Locosoft könnte nur abgerechnete Aufträge zählen
  - Locosoft könnte andere Pausenzeiten verwenden
  - Locosoft könnte andere Lücken-Berechnung verwenden

### 2. Interne Aufträge

| Kategorie | Anzahl Stempelungen | Minuten |
|-----------|---------------------|---------|
| **Interne Aufträge** (Kunde 3000001) | 290 | 16.727 |
| **Externe Aufträge** | 731 | 40.649 |
| **Gesamt** | 1.021 | 57.377 |

**Erkenntnis:** 
- 290 Stempelungen auf interne Aufträge (16.727 Minuten)
- 731 Stempelungen auf externe Aufträge (40.649 Minuten)
- **Interne Aufträge machen 29% der Stempelungen aus**

### 3. AW (Vorgabe) - ABWEICHUNG ⚠️

| Quelle | Wert | AW |
|--------|------|-----|
| **Locosoft** | 205:55 | ~2.059,17 |
| **DRIVE (alle)** | - | 1.904 |
| **Differenz** | - | -155,17 |

**Abweichung:** DRIVE zeigt **7,5% weniger** AW als Locosoft.

---

## 🔎 HYPOTHESEN

### Hypothese 1: Locosoft schließt interne Aufträge aus ❌ WIDERLEGT
- **Test**: Berechnung ohne interne Aufträge (Kunde 3000001)
- **Ergebnis**: 
  - Zeit-Spanne ohne interne = 7.719 Minuten
  - Locosoft = 8.483 Minuten
  - **Differenz: -764 Minuten** (ohne interne ist zu niedrig!)
- **Fazit**: Wenn Locosoft interne komplett ausschließt, wäre die Zeit-Spanne zu niedrig. Locosoft zeigt mehr als ohne interne.

### Hypothese 1b: Locosoft zählt interne Aufträge mit ⚠️ UNKLAR
- **Test**: Berechnung mit internen Aufträgen
- **Ergebnis**: 
  - Zeit-Spanne mit internen = 9.309 Minuten
  - Locosoft = 8.483 Minuten
  - **Differenz: -826 Minuten** (mit internen ist zu hoch!)
- **Fazit**: Wenn Locosoft interne komplett mitzählt, wäre die Zeit-Spanne zu hoch. Locosoft zeigt weniger als mit internen.

**Erkenntnis:** Locosoft zeigt einen Wert zwischen "ohne interne" (7.719) und "mit internen" (9.309). Möglicherweise werden interne Aufträge teilweise mitgezählt oder anders behandelt.

### Hypothese 2: Locosoft schließt Leerlauf (order_number = 31) aus ✅ BESTÄTIGT
- **Test**: Prüfen, ob Leerlauf-Aufträge existieren
- **Ergebnis**: 
  - 9 Leerlauf-Stempelungen im November
  - 212 Minuten Leerlauf-Zeit
  - 9 Tage mit Leerlauf
- **Fazit**: DRIVE schließt bereits Leerlauf aus (`order_number > 31`), aber die Differenz bleibt bestehen

### Hypothese 3: Locosoft verwendet andere Filter ❓
- **Mögliche Filter:**
  - Nur abgerechnete Aufträge? → ❌ Getestet, keine Änderung
  - Nur bestimmte Auftragstypen?
  - Nur bestimmte charge_types?
  - Andere Pausenzeiten-Konfiguration?

### Hypothese 4: Locosoft "I"-Präfix in Auftragsnummer ❌ WIDERLEGT
- **Test**: Prüfen, ob Aufträge mit "I"-Präfix existieren
- **Ergebnis**: 0 Aufträge mit "I"-Präfix gefunden
- **Fazit**: "I"-Präfix wird nicht verwendet, interne Aufträge werden über Kunde 3000001 identifiziert

---

## 📋 NÄCHSTE SCHRITTE

### 1. Locosoft-Filter identifizieren
- [x] Prüfen, ob Locosoft nur abgerechnete Aufträge zählt → **Nein, Zeit-Spanne bleibt gleich**
- [ ] Prüfen, ob Locosoft bestimmte charge_types ausschließt
- [ ] Prüfen, ob Locosoft bestimmte Auftragstypen ausschließt
- [ ] Prüfen, ob Locosoft andere Pausenzeiten verwendet

### 2. DRIVE-Berechnung anpassen
- [ ] Interne Aufträge aus Stempelzeit-Berechnung ausschließen (wenn Locosoft das tut)
- [ ] Weitere Filter anwenden (wenn identifiziert)

### 3. Validierung
- [ ] DRIVE-Werte mit Locosoft vergleichen
- [ ] Abweichungen dokumentieren

---

## 💡 ERKENNTNISSE

### Interne Aufträge:
- **41 Aufträge** mit Kunde 3000001 im November
- **290 Stempelungen** auf interne Aufträge
- **16.727 Minuten** Stempelzeit auf interne Aufträge
- **29% der Stempelungen** sind auf interne Aufträge
- **"I"-Präfix in Auftragsnummer:** ❌ Nicht vorhanden (0 Aufträge gefunden)
- **Interne Aufträge werden über Kunde 3000001 identifiziert**

### Locosoft-Berechnung:
- Zeigt 8.483 Minuten Stempelzeit
- DRIVE Zeit-Spanne (ohne interne) = 7.719 Minuten
- DRIVE Zeit-Spanne (ohne interne, nur abgerechnet) = 7.719 Minuten
- **Differenz: +764 Minuten** (etwa 12,7 Stunden = 34,7 Minuten pro Tag)

**Validierung:**
- ✅ Interne Aufträge werden ausgeschlossen (Kunde 3000001)
- ✅ "I"-Präfix wird nicht verwendet
- ❌ "Nur abgerechnete Aufträge" erklärt die Differenz nicht
- ❓ Weitere Filter oder andere Berechnungslogik in Locosoft

**Mögliche Erklärungen für +764 Minuten:**
1. ✅ **Interne Aufträge ausgeschlossen** (Kunde 3000001) - bereits implementiert
2. ✅ **Leerlauf ausgeschlossen** (order_number = 31) - bereits implementiert
3. ❓ **Andere/erweiterte Pausenzeiten** in Locosoft
4. ❓ **Andere Lücken-Berechnung** (z.B. nur Lücken > X Minuten werden abgezogen)
5. ❓ **Zusätzliche Filter** (z.B. bestimmte charge_types)
6. ❓ **Konfigurierte Arbeitszeiten** (nicht nur Pausenzeiten)

**Aktueller Stand:**
- DRIVE Zeit-Spanne (ohne interne, ohne Leerlauf) = 7.719 Minuten
- Locosoft = 8.483 Minuten
- **Differenz: +764 Minuten** (etwa 34,7 Minuten pro Tag über 18 Arbeitstage)

### AW (Vorgabe):
- **Locosoft**: ~2.059 AW (205:55 Stunden)
- **DRIVE (alle)**: 1.904 AW
- **DRIVE (ohne interne)**: 1.477 AW
- **Differenz**: -582 AW (ohne interne) bis -155 AW (alle)

**Erkenntnis:** 
- Locosoft zeigt deutlich mehr AW als DRIVE
- Möglicherweise zählt Locosoft auch nicht-abgerechnete AW oder interne Aufträge mit

---

*Erstellt: TAG 185 | Autor: Claude AI*
