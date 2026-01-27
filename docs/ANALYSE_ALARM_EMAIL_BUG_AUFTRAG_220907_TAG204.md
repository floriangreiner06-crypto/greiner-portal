# Analyse: Alarm-E-Mail Bug - Auftrag 220907

**Datum:** 2026-01-21  
**TAG:** 204  
**Problem:** Alarm-E-Mail zeigt falsche "Gestempelt"-Zeit (557 Min statt 71 Min)

---

## 📊 E-Mail-Werte

- **Auftrag:** 220907
- **Gestempelt:** 557 Min (9.3 Std) ❌ **FALSCH**
- **Vorgabe:** 120 Min (2.0 Std)
- **Überschreitung:** +437 Min (464%)

---

## 🔍 Analyse der Stempelungen

### Stempelungen-Details
- **Anzahl Stempelungen:** 9
- **Mechaniker:** MA 5014 (Litwin, Jaroslaw)
- **Status:** **AKTIV** (seit 14:28, aktuell 71 Min)
- **Positionen:** 1/1, 1/2, 1/3, 1/4, 1/5, 1/6, 1/7, 2/1, 2/2
- **Alle zur gleichen Zeit:** 2026-01-21 14:28:12

### Zeitblöcke
- **Eindeutige Zeitblöcke:** 1 (alle 9 Stempelungen haben gleiche Start-/Endzeit)
- **Korrekte Berechnung (mit Deduplizierung):** **71 Min (1.2 Std)** ✅
- **Ohne Deduplizierung:** 643 Min (10.7 Std) ❌

---

## 🐛 Problem-Identifikation

### 1. Auftrag ist AKTIV, aber E-Mail verwendet falsche Berechnung

**Erwartetes Verhalten:**
- Auftrag ist aktiv → E-Mail sollte `heute_session_min` verwenden (71 Min)
- Query in `get_stempeluhr()` findet Auftrag korrekt: **73 Min** ✅

**Tatsächliches Verhalten:**
- E-Mail zeigt: **557 Min** ❌
- Das ist weder die korrekte deduplizierte Zeit (71 Min) noch die nicht-deduplizierte Zeit (643 Min)

### 2. Mögliche Ursachen

#### Option A: E-Mail verwendet Query für abgeschlossene Aufträge
- **Problem:** Obwohl Auftrag aktiv ist, wird die Query für abgeschlossene Aufträge verwendet
- **Query filtert:** Nur letzte 2 Tage (`DATE(start_time) >= CURRENT_DATE - INTERVAL '1 day'`)
- **Ergebnis:** Wenn der Auftrag vor mehr als 2 Tagen gestartet wurde, werden alte Stempelungen nicht erfasst

#### Option B: E-Mail verwendet nicht-deduplizierte Berechnung
- **Problem:** E-Mail summiert alle 9 Stempelungen ohne Deduplizierung
- **Berechnung:** 9 × 71 Min = 639 Min (nahe an 643 Min, aber E-Mail zeigt 557 Min)
- **Abweichung:** 557 Min ist nicht erklärbar durch einfache Summierung

#### Option C: E-Mail verwendet alte Berechnung (vor TAG 194 Fix)
- **Problem:** E-Mail wurde mit alter Logik erstellt (ohne Deduplizierung, nur heute)
- **Berechnung:** Summe aller Stempelungen von heute ohne Deduplizierung
- **Ergebnis:** 557 Min könnte eine Teilsumme sein (z.B. nur bestimmte Positionen)

---

## 🔬 Detaillierte Berechnungen

### Korrekte Berechnung (mit Deduplizierung)
```
1 Zeitblock: MA 5014, 14:28 - LAUFEND = 71 Min
Ergebnis: 71 Min ✅
```

### Falsche Berechnung (ohne Deduplizierung)
```
9 Stempelungen × 71 Min = 639 Min
Ergebnis: 639 Min ❌
```

### E-Mail zeigt
```
557 Min ❌
```

### Abweichungen
- **E-Mail zu korrekt:** 557 - 71 = **486 Min Differenz**
- **E-Mail zu ohne Dedup:** 557 - 639 = **-82 Min Differenz**

---

## 🎯 Root Cause Analysis

### Wahrscheinlichste Ursache: **Option C - Alte Berechnung**

**Indizien:**
1. E-Mail zeigt 557 Min, was zwischen korrekter (71 Min) und falscher (639 Min) Berechnung liegt
2. Auftrag ist aktiv, sollte aber in `get_stempeluhr()` erscheinen (wird auch gefunden: 73 Min)
3. E-Mail wurde möglicherweise mit alter Logik erstellt, bevor TAG 194 Fix aktiv war

**Mögliche Erklärung:**
- E-Mail verwendet eine Berechnung, die:
  - Nur bestimmte Positionen berücksichtigt (nicht alle 9)
  - Oder eine Teilsumme bildet
  - Oder eine andere Filterlogik verwendet

---

## 📋 Empfohlene Fixes

### 1. Prüfe E-Mail-Logik in `celery_app/tasks.py`
- **Zeile 276-289:** Prüfe, ob aktive Aufträge korrekt erkannt werden
- **Zeile 245-250:** Prüfe, ob `ueberschritten_map` korrekt befüllt wird
- **Problem:** Möglicherweise wird aktiver Auftrag nicht in `ueberschritten_map` aufgenommen

### 2. Prüfe `get_stempeluhr()` Rückgabe
- **Problem:** Auftrag erscheint in Query (73 Min), aber nicht in `get_stempeluhr()` Rückgabe
- **Mögliche Ursache:** Filter nach `subsidiaries` oder andere Bedingungen

### 3. Prüfe Deduplizierung in E-Mail-Berechnung
- **Problem:** E-Mail verwendet möglicherweise nicht-deduplizierte Berechnung
- **Fix:** Sicherstellen, dass `heute_session_min` aus `get_stempeluhr()` verwendet wird

---

## 🧪 Test-Szenario

### Erwartetes Verhalten
1. Auftrag 220907 ist aktiv (MA 5014, seit 14:28)
2. `get_stempeluhr()` findet Auftrag: **73 Min**
3. E-Mail sollte verwenden: `heute_session_min = 73 Min`
4. E-Mail sollte zeigen: **73 Min (1.2 Std)** statt 557 Min

### Tatsächliches Verhalten
1. ✅ Auftrag ist aktiv
2. ✅ `get_stempeluhr()` findet Auftrag: 73 Min
3. ❌ E-Mail zeigt: 557 Min (falsche Berechnung)

---

## 🔗 Referenzen

- **TAG 194:** Deduplizierungs-Logik korrigiert
- **TAG 204:** Pausenberechnung entfernt
- **celery_app/tasks.py:** Alarm-E-Mail Logik
- **api/werkstatt_data.py:** `get_stempeluhr()` Funktion

---

## 💡 Nächste Schritte

1. **Prüfe `celery_app/tasks.py` Zeile 245-250:**
   - Wird aktiver Auftrag korrekt in `ueberschritten_map` aufgenommen?
   - Wird `heute_session_min` korrekt verwendet?

2. **Prüfe `get_stempeluhr()` Rückgabe:**
   - Warum erscheint Auftrag nicht in Rückgabe, obwohl Query ihn findet?
   - Gibt es Filter, die den Auftrag ausschließen?

3. **Prüfe E-Mail-Berechnung:**
   - Welche Berechnung wird tatsächlich verwendet?
   - Wird `heute_session_min` oder `laufzeit_min` verwendet?
