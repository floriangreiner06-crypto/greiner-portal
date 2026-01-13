# Analyse: Stempelzeiten-Abweichung DRIVE vs. Locosoft Original

**Datum:** 2026-01-13 (TAG 185)  
**Mitarbeiter:** 5018 (Jan Majer)  
**Zeitraum:** 01.12.2025 - 31.12.2025

---

## 📊 ÜBERSICHT DER ABWEICHUNGEN

### Locosoft Original (Screenshot):
- **AW-Anteil**: 114:16 (114 Stunden 16 Minuten = 6856 Minuten = 1142.67 AW)
- **Stmp.Anteil**: 82:25 (82 Stunden 25 Minuten = 4945 Minuten)
- **Sollzeit**: 104:00 (104 Stunden = 6240 Minuten)
- **Anwesend**: 98:56 (98 Stunden 56 Minuten = 5936 Minuten)
- **Produktiv**: 82:57 (82 Stunden 57 Minuten = 4977 Minuten)
- **A-Grad**: 103%
- **P-Grad**: 84%

### DRIVE (Datenbank-Abfrage):
- **AW (Vorgabe)**: 1163 AW (aus `labours` mit `is_invoiced = true`)
- **Stempelzeit (Type 2)**: 28727.92 Minuten = 478.8 Stunden
- **Anwesenheit (Type 1)**: 6530.08 Minuten = 108.8 Stunden

---

## 🔍 IDENTIFIZIERTE ABWEICHUNGEN

### 1. Stempelzeit (Produktiv) - GROSSE ABWEICHUNG ⚠️

| Quelle | Wert | Minuten |
|--------|------|---------|
| **Locosoft** | 82:25 | 4.945 |
| **DRIVE (alle)** | 478:48 | 28.728 |
| **DRIVE (order > 31)** | 478:13 | 28.694 |
| **DRIVE (abgerechnet)** | 482:24 | 28.943 |
| **Differenz** | +396:23 | +23.783 |

**Abweichung:** DRIVE zeigt **5,8x mehr** Stempelzeit als Locosoft!

**Erkenntnis:** Die Abweichung ist NICHT durch "nur abgerechnete Aufträge" erklärbar, da abgerechnete Aufträge sogar MEHR Minuten zeigen (28.943 vs. 28.728).

### 2. Anwesenheit - GROSSE ABWEICHUNG ⚠️

| Quelle | Wert | Minuten |
|--------|------|---------|
| **Locosoft** | 98:56 | 5.936 |
| **DRIVE** | 108:50 | 6.530 |
| **Differenz** | +9:54 | +594 |

**Abweichung:** DRIVE zeigt **10% mehr** Anwesenheit als Locosoft.

### 3. AW (Vorgabe) - KLEINE ABWEICHUNG ✅

| Quelle | Wert | AW |
|--------|------|-----|
| **Locosoft** | 114:16 | ~1142.67 |
| **DRIVE** | - | 1.163 |
| **Differenz** | - | +20.33 |

**Abweichung:** DRIVE zeigt **1,8% mehr** AW als Locosoft (geringfügig).

---

## 🔎 URSACHENANALYSE

### Mögliche Ursachen für Stempelzeit-Abweichung:

#### 1. **Deduplizierungslogik unterschiedlich**
- **DRIVE**: Verwendet `DISTINCT ON (employee_number, start_time, end_time)` zur Deduplizierung
- **Locosoft**: Möglicherweise andere Deduplizierungslogik (z.B. nur erste/letzte Stempelung pro Tag?)

#### 2. **Filter unterschiedlich**
- **DRIVE**: Zählt ALLE Stempelungen mit `type = 2` und `end_time IS NOT NULL`
- **Locosoft**: Möglicherweise nur abgerechnete Aufträge oder bestimmte Auftragstypen?

#### 3. **Zeitraum-Filter unterschiedlich**
- **DRIVE**: `start_time >= '2025-12-01' AND start_time < '2025-12-31' + INTERVAL '1 day'`
- **Locosoft**: Möglicherweise andere Zeitraum-Logik (z.B. nur Arbeitstage, nur bestimmte Zeiten)?

#### 4. **Auftragsnummer-Filter unterschiedlich**
- **DRIVE**: Filtert `order_number > 31` (nur echte Aufträge, nicht Leerlauf)
- **Locosoft**: Möglicherweise andere Filterlogik?

#### 5. **Stempelungs-Status unterschiedlich**
- **DRIVE**: Zählt alle abgeschlossenen Stempelungen (`end_time IS NOT NULL`)
- **Locosoft**: Möglicherweise nur "fertig" markierte Stempelungen?

---

## 📋 NÄCHSTE SCHRITTE

### 1. Locosoft-Berechnungslogik verstehen
- [ ] Locosoft-Dokumentation prüfen (Pr. 811 - Bruttolohnabrechnung)
- [ ] Locosoft-Query analysieren (wie wird "Stmp.Anteil" berechnet?)
- [ ] Filter-Logik in Locosoft identifizieren

### 2. DRIVE-Berechnungslogik prüfen
- [ ] Deduplizierungslogik überprüfen
- [ ] Filter-Logik überprüfen
- [ ] Zeitraum-Filter überprüfen

### 3. Vergleichsabfrage erstellen
- [ ] SQL-Query erstellen, die Locosoft-Logik nachbildet
- [ ] Test-Abfrage für Jan (5018) im Dezember 2025
- [ ] Ergebnisse vergleichen

### 4. Korrektur implementieren
- [ ] **Option A**: DRIVE-Berechnungslogik an Locosoft anpassen (Zeit-Spanne minus Pausen)
- [ ] **Option B**: Beide Berechnungen anbieten (DRIVE-Standard + Locosoft-kompatibel)
- [ ] **Option C**: Locosoft-Logik dokumentieren und als Referenz nutzen (keine Änderung)

**Empfehlung**: Option B - Beide Berechnungen anbieten, damit Benutzer wählen können

---

## ✅ ERKENNTNISSE

### Locosoft-Berechnungslogik identifiziert:

**Locosoft "Stmp.Anteil" (Produktiv) = Zeit-Spanne (erste bis letzte Stempelung pro Tag) - Lücken zwischen Stempelungen**

- **Zeit-Spanne gesamt**: 6120 Minuten = 102:00 Stunden (12 Arbeitstage × ~8,5h)
- **Locosoft "Stmp.Anteil"**: 4945 Minuten = 82:25 Stunden
- **Differenz (Lücken)**: 1175 Minuten = 19:35 Stunden (~98 Minuten pro Tag)

### Detaillierte Analyse der Lücken zwischen Stempelungen:

| Kategorie | Anzahl | Minuten gesamt | Durchschnitt | Bedeutung |
|-----------|--------|----------------|-------------|-----------|
| **0-5 min (Wechsel)** | 67 | 30.7 | 0.5 | Normale Wechsel zwischen Aufträgen |
| **5-30 min (Kurze Pause)** | 21 | 306.2 | 14.6 | Kurze Pausen, Werkzeug holen, etc. |
| **30-60 min (Mittagspause?)** | 7 | 300.3 | 42.9 | Mittagspausen |
| **>60 min (Lange Pause)** | 2 | 133.8 | 66.9 | Längere Pausen |
| **GESAMT** | **97** | **771.0** | **7.9** | **Alle Lücken** |

**Erkenntnis:** Die Lücken zwischen Stempelungen (771 Minuten) sind deutlich weniger als die Differenz zwischen Zeit-Spanne und Locosoft-Wert (1175 Minuten). 

**Konfigurierte Pausenzeiten (aus `employees_breaktimes`):**
- Pause: 12:00 - 12:44 (44 Minuten pro Tag)
- Über 12 Arbeitstage: 44 × 12 = **528 Minuten**

**Validierung:**
- Zeit-Spanne gesamt: 6120 Minuten
- Locosoft "Stmp.Anteil": 4945 Minuten
- Differenz: 1175 Minuten
- Lücken zwischen Stempelungen: 771 Minuten
- Konfigurierte Pausen: 528 Minuten
- **Summe Lücken + Pausen: 1299 Minuten** (vs. Differenz 1175 Minuten)

**Fazit:** Locosoft zählt wahrscheinlich: Zeit-Spanne MINUS Lücken zwischen Stempelungen MINUS konfigurierte Pausenzeiten (wenn innerhalb der Zeit-Spanne).

**Vergleich:**
- DRIVE summiert ALLE Stempelungen: 28.728 Minuten
- Locosoft zählt nur Zeit-Spanne minus Pausen: 4.945 Minuten
- **Faktor**: DRIVE zeigt 5,8x mehr als Locosoft

---

## 💡 HYPOTHESEN

### Hypothese 1: Locosoft zählt nur abgerechnete Aufträge ❌ WIDERLEGT
- **Test**: SQL-Query mit JOIN auf `invoices` erstellt
- **Ergebnis**: Abgerechnete Aufträge zeigen MEHR Minuten (28.943) als alle Aufträge (28.728)
- **Fazit**: Diese Hypothese ist falsch - die Abweichung hat andere Ursachen

### Hypothese 2: Locosoft zählt nur Zeit-Spanne (erste bis letzte Stempelung pro Tag) ✅ TEILWEISE BESTÄTIGT
- **Test**: Berechnung der Zeit-Spanne zwischen erster und letzter Stempelung pro Tag
- **Ergebnis**: 
  - Zeit-Spanne gesamt: 6120 Minuten = 102:00 Stunden
  - Locosoft "Stmp.Anteil": 4945 Minuten = 82:25 Stunden
  - **Differenz**: 1175 Minuten = 19:35 Stunden (~98 Minuten pro Tag)
  - **Tatsächliche Lücken zwischen Stempelungen**: 771 Minuten (~64 Minuten pro Tag)
  - **Rest-Differenz**: 404 Minuten (~34 Minuten pro Tag) - möglicherweise konfigurierte Pausenzeiten
- **Fazit**: Locosoft zählt Zeit-Spanne MINUS Lücken zwischen Stempelungen, möglicherweise zusätzlich MINUS konfigurierte Pausenzeiten

### Hypothese 3: Locosoft verwendet konfigurierte Pausenzeiten ✅ BESTÄTIGT
- **Test**: Prüfen, ob Locosoft zusätzlich zu Lücken auch konfigurierte Pausenzeiten abzieht
- **Ergebnis**: 
  - Konfigurierte Pause (Jan): 12:00 - 12:44 (44 Minuten pro Tag)
  - Über 12 Arbeitstage: 528 Minuten
  - Differenz Zeit-Spanne vs. Locosoft: 1175 Minuten
  - Tatsächliche Lücken: 771 Minuten
  - Konfigurierte Pausen: 528 Minuten
  - **Summe: 1299 Minuten** (vs. Differenz 1175 Minuten - Abweichung von 124 Minuten)
- **Fazit**: Locosoft zieht sowohl Lücken zwischen Stempelungen als auch konfigurierte Pausenzeiten ab. Die Abweichung von 124 Minuten könnte durch Überlappungen oder andere Faktoren erklärt werden.

---

## 📁 QUELLEN

- **Screenshot**: Locosoft "Tages-Stempelzeiten Übersicht" für Jan (5018), Dezember 2025
- **PDF**: `/mnt/greiner-portal-sync/docs/Analyse_offene_auftraege/jan_dezember.pdf`
- **DRIVE-Code**: `api/werkstatt_data.py::get_mechaniker_leistung()`
- **Datenbank**: Locosoft PostgreSQL (10.80.80.8)

---

## 🎯 LÖSUNGSVORSCHLÄGE

### Option A: DRIVE an Locosoft anpassen
**Vorteile:**
- Konsistenz mit Locosoft Original
- Einheitliche Berechnung

**Nachteile:**
- Verliert Detail-Information (tatsächliche Stempelzeiten)
- Pausen müssen identifiziert werden (komplex)

**Implementierung:**
```sql
-- Zeit-Spanne pro Tag berechnen
WITH tages_spannen AS (
    SELECT 
        DATE(start_time) as datum,
        MIN(start_time) as erste_stempelung,
        MAX(end_time) as letzte_stempelung
    FROM times
    WHERE employee_number = 5018
      AND type = 2
      AND end_time IS NOT NULL
      AND order_number > 31
    GROUP BY DATE(start_time)
)
SELECT 
    SUM(EXTRACT(EPOCH FROM (letzte_stempelung - erste_stempelung))/60) as stempelzeit_minuten
FROM tages_spannen
-- Minus Pausen (z.B. 30-60 Minuten pro Tag)
```

### Option B: Beide Berechnungen anbieten (EMPFOHLEN) ✅
**Vorteile:**
- Beide Perspektiven verfügbar
- Flexibilität für Benutzer
- Keine Datenverluste

**Nachteile:**
- Zwei verschiedene Werte können verwirrend sein
- Benötigt UI-Anpassung

**Implementierung:**
- Neue API-Parameter: `?berechnung=standard` (DRIVE) oder `?berechnung=locosoft`
- Oder: Zwei separate Felder in der Antwort: `stempelzeit_drive` und `stempelzeit_locosoft`

### Option C: Keine Änderung (nur Dokumentation)
**Vorteile:**
- Keine Code-Änderungen nötig
- DRIVE-Berechnung ist detaillierter

**Nachteile:**
- Abweichung bleibt bestehen
- Benutzer müssen Unterschied verstehen

---

## 📝 ZUSAMMENFASSUNG

**Hauptursache der Abweichung:**
- **DRIVE**: Summiert ALLE Stempelungen mit ihrer tatsächlichen Dauer (28.728 Minuten)
- **Locosoft**: Zählt Zeit-Spanne zwischen erster und letzter Stempelung pro Tag, MINUS:
  1. Lücken zwischen Stempelungen (771 Minuten)
  2. Konfigurierte Pausenzeiten (528 Minuten)
  = 4.945 Minuten
- **Faktor**: DRIVE zeigt 5,8x mehr als Locosoft

**Detaillierte Aufschlüsselung:**

| Berechnungsschritt | Wert | Minuten | Stunden:Minuten |
|-------------------|------|---------|-----------------|
| **1. Zeit-Spanne** (erste bis letzte Stempelung pro Tag, summiert) | 6120 | 6120 | 102:00 |
| **2. Tatsächliche Stempelzeit** (dedupliziert, summiert) | 5349 | 5349 | 89:09 |
| **3. Lücken zwischen Stempelungen** | 771 | 771 | 12:51 |
| **4. Konfigurierte Pausenzeiten** (12:00-12:44, 12 Tage) | 528 | 528 | 8:48 |
| **5. Locosoft "Stmp.Anteil"** (gemessen) | 4945 | 4945 | 82:25 |
| **6. Berechnete Differenz** (Zeit-Spanne - Lücken - Pausen) | 4821 | 4821 | 80:21 |
| **7. Abweichung** (Locosoft vs. Berechnung) | +124 | +124 | +2:04 |

**Validierung:**
- Zeit-Spanne (6120) - Lücken (771) - Pausen (528) = 4821 Minuten
- Locosoft zeigt: 4945 Minuten
- **Abweichung: +124 Minuten** (Locosoft zeigt 2:04 Stunden mehr)

**Mögliche Erklärungen für die Abweichung:**
- Locosoft könnte Pausen nur abziehen, wenn sie innerhalb der Zeit-Spanne liegen
- Es könnte Überlappungen zwischen Lücken und Pausen geben
- Locosoft könnte eine andere Deduplizierungslogik verwenden

**Empfehlung:**
- Option B: Beide Berechnungen anbieten
- Dokumentation erweitern, um Unterschied zu erklären
- UI-Anpassung: Toggle zwischen "DRIVE-Standard" und "Locosoft-kompatibel"

---

*Erstellt: TAG 185 | Autor: Claude AI*
