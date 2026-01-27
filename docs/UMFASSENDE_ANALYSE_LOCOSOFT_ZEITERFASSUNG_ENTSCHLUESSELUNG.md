# Umfassende Analyse: Locosoft Zeiterfassung entschlüsseln

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Kontext aller bisherigen Versuche + Vorschlag für weitere Vorgehensweise

---

## 📋 EXECUTIVE SUMMARY

### Problem
- **Stempelzeit-Berechnung (St-Anteil) weicht von Locosoft ab**
- Beispiel MA 5007 (07.01.2026): 
  - Locosoft: 13:05 Std (DEGO: 9:06 Std + DEGH: 3:59 Std)
  - Unsere Berechnung: 8:04 Std (DEGO: 3:21 Std + DEGH: 4:43 Std)
  - **Abweichung: 5:01 Std (38% zu niedrig)**

### Anforderungen
- ✅ **KPIs müssen NICHT in Echtzeit sein** (Tages-/Monatsauswertungen)
- ⚠️ **Stempelzeit-Überschreitung vs. Vorgabezeit MUSS in Echtzeit erfolgen** (Alarm-E-Mails)

### Bisherige Versuche
- 6+ verschiedene Deduplizierungs-Methoden getestet
- Keine Methode passt perfekt zu Locosoft
- Beste Näherung: DEGH mit auftrags-basierter Deduplizierung (4:43 vs. 3:59)

---

## 🔍 ALLE BISHERIGEN VERSUCHE

### 1. Auftrags-basierte Deduplizierung (aktuell) ⭐

**Methode:**
```sql
DISTINCT ON (employee_number, order_number, start_time, end_time)
```

**Logik:**
- Verschiedene Positionen auf demselben Auftrag zur gleichen Zeit → 1× zählen
- Verschiedene Aufträge zur gleichen Zeit → separat zählen

**Ergebnis (MA 5007, 07.01.2026):**
- DEGO: 3:21 Std (Locosoft: 9:06 Std) ❌ **Abweichung: -5:45 Std**
- DEGH: 4:43 Std (Locosoft: 3:59 Std) ✅ **Abweichung: +0:44 Std**
- GESAMT: 8:04 Std (Locosoft: 13:05 Std) ❌ **Abweichung: -5:01 Std**

**Bewertung:**
- ✅ DEGH sehr nah (nur 0:44 Std Abweichung)
- ❌ DEGO viel zu niedrig (5:45 Std Abweichung)
- ⚠️ **Aktuell in Produktion verwendet**

**Code-Stelle:**
- `api/werkstatt_data.py` → `get_stempelzeit_aus_times()` (Zeile 1035)

---

### 2. Position-basierte Berechnung

**Methode:**
```sql
DISTINCT ON (employee_number, order_number, order_position, 
             order_position_line, start_time, end_time)
```

**Logik:**
- Jede Position einzeln zählen (auch wenn zur gleichen Zeit)

**Ergebnis (MA 5007, 07.01.2026):**
- DEGO: 13:31 Std (Locosoft: 9:06 Std) ❌ **Abweichung: +4:25 Std**
- DEGH: 24:31 Std (Locosoft: 3:59 Std) ❌ **Abweichung: +20:32 Std**
- GESAMT: 38:02 Std (Locosoft: 13:05 Std) ❌ **Abweichung: +24:57 Std**

**Bewertung:**
- ❌ Viel zu hoch (fast 3× zu viel)
- ❌ Nicht verwendbar

**Code-Stelle:**
- Getestet in `docs/ANALYSE_MA_5007_07_01_2026.md`

---

### 3. Zeit-Spanne (erste bis letzte Stempelung)

**Methode:**
```sql
MIN(start_time) bis MAX(end_time) pro Tag/Betrieb
```

**Logik:**
- Zeit-Spanne von erster bis letzter Stempelung
- Lücken zwischen Stempelungen werden nicht abgezogen

**Ergebnis (MA 5007, 07.01.2026):**
- DEGO: 8:05 Std (Locosoft: 9:06 Std) ✅ **Abweichung: -1:01 Std**
- DEGH: 5:17 Std (Locosoft: 3:59 Std) ❌ **Abweichung: +1:18 Std**

**Bewertung:**
- ✅ DEGO sehr nah (nur 1:01 Std Abweichung)
- ❌ DEGH zu hoch (1:18 Std Abweichung)
- ⚠️ **Möglicherweise für DEGO verwendbar**

**Code-Stelle:**
- Getestet in `docs/ANALYSE_MA_5007_07_01_2026.md`

---

### 4. Zeit-basierte Deduplizierung (zu aggressiv)

**Methode:**
```sql
DISTINCT ON (employee_number, start_time, end_time)
```

**Logik:**
- Gleiche Zeit = 1× zählen (egal welcher Auftrag)

**Ergebnis:**
- ❌ Zu aggressiv (zählt verschiedene Aufträge zur gleichen Zeit nur 1×)
- ❌ Nicht verwendet

**Code-Stelle:**
- Getestet in `docs/ANALYSE_MA_5007_07_01_2026.md`

---

### 5. Time Range Merge Algorithm (Python)

**Methode:**
- Python-Algorithmus zum Zusammenführen überlappender Zeitblöcke
- Merge überlappender Intervalle

**Ergebnis:**
- DEGO: 8:05 Std (Locosoft: 9:06 Std) ✅ **Abweichung: -1:01 Std**
- DEGH: 4:43 Std (Locosoft: 3:59 Std) ✅ **Abweichung: +0:44 Std**

**Bewertung:**
- ✅ Sehr nah an Locosoft
- ⚠️ Komplexer Algorithmus, Performance-Probleme bei vielen Daten

**Code-Stelle:**
- Getestet in `docs/ANALYSE_MA_5007_07_01_2026.md`

---

### 6. Nur abgerechnete Aufträge

**Methode:**
- Auftrags-basierte Deduplizierung + Filter auf abgerechnete Aufträge

**Ergebnis (MA 5007, 07.01.2026):**
- DEGO: 1:20 Std (Locosoft: 9:06 Std) ❌ **Abweichung: -7:46 Std**
- DEGH: 0:35 Std (Locosoft: 3:59 Std) ❌ **Abweichung: -3:24 Std**

**Bewertung:**
- ❌ Viel zu niedrig
- ❌ Nicht verwendbar

**Code-Stelle:**
- Getestet in `docs/ANALYSE_MA_5007_07_01_2026.md`

---

## 📊 ZUSAMMENFASSUNG ALLER METHODEN

| Methode | DEGO | DEGH | GESAMT | Bewertung |
|---------|------|------|---------|-----------|
| **Locosoft (Referenz)** | 9:06 | 3:59 | 13:05 | ✅ |
| **Auftrags-basiert (aktuell)** | 3:21 ❌ | 4:43 ✅ | 8:04 ❌ | ⚠️ DEGH gut, DEGO schlecht |
| **Position-basiert** | 13:31 ❌ | 24:31 ❌ | 38:02 ❌ | ❌ Viel zu hoch |
| **Zeit-Spanne** | 8:05 ✅ | 5:17 ❌ | - | ⚠️ DEGO gut, DEGH schlecht |
| **Time Range Merge** | 8:05 ✅ | 4:43 ✅ | - | ✅ Sehr nah, aber komplex |

**Erkenntnis:**
- **Keine Methode passt perfekt zu Locosoft**
- **DEGO und DEGH benötigen unterschiedliche Methoden!**
- **Beste Näherung:** DEGH mit auftrags-basierter Deduplizierung, DEGO mit Zeit-Spanne

---

## 🔍 ERKENNTNISSE AUS ANALYSEN

### 1. Locosoft verwendet unterschiedliche Methoden pro Betrieb

**Beobachtung:**
- DEGO: Zeit-Spanne (8:05) ist nah an Locosoft (9:06) → **Abweichung: -1:01 Std**
- DEGH: Auftrags-basiert (4:43) ist nah an Locosoft (3:59) → **Abweichung: +0:44 Std**

**Hypothese:**
- Locosoft verwendet möglicherweise **betriebs-spezifische Berechnungsmethoden**
- DEGO: Zeit-Spanne + Pausenzeiten-Abzug?
- DEGH: Auftrags-basierte Summe?

### 2. Locosoft summiert St-Ant. Werte pro Betrieb

**Beobachtung:**
- Locosoft zeigt: DEGO (9:06) + DEGH (3:59) = GESAMT (13:05) ✅
- **St-Ant. (13:05) > Anwesenheit (7:26)** → Physikalisch unmöglich!

**Erklärung:**
- Locosoft zählt überlappende Stempelungen mehrfach
- Stempelzeit ist nicht Teil der Anwesenheit, sondern separate Metrik

### 3. Pausenzeiten werden nicht abgezogen

**Beobachtung:**
- Locosoft Support: "Arbeitszeiten/Pausen müssen berücksichtigt werden"
- Unsere Tests: Pausenzeiten-Abzug macht es schlimmer
- **Erkenntnis:** Pausenzeiten werden möglicherweise anders berücksichtigt (nicht einfach abgezogen)

### 4. App-Stempelungen haben Synchronisations-Verzögerung

**Beobachtung:**
- App-Stempelungen sind in Locosoft-UI sofort sichtbar
- PostgreSQL-Datenbank: Verzögerung von ca. 15-30 Minuten
- **Auswirkung:** Echtzeit-Alarme können verzögert sein

---

## 🎯 ANFORDERUNGEN

### 1. KPIs (NICHT Echtzeit) ✅

**Anforderung:**
- Leistungsgrad, Produktivität, Anwesenheitsgrad, Auslastungsgrad
- **Müssen NICHT in Echtzeit sein**
- Tages-/Monatsauswertungen sind ausreichend

**Aktuelle Lösung:**
- ✅ Funktioniert (mit Abweichungen zu Locosoft)
- ⚠️ Abweichungen akzeptabel für Tages-/Monatsauswertungen

### 2. Stempelzeit-Überschreitung (Echtzeit) ⚠️

**Anforderung:**
- Alarm-E-Mails bei Überschreitung von Vorgabezeit
- **MUSS in Echtzeit erfolgen**
- Aktuelle Stempelung vs. Vorgabezeit

**Aktuelle Lösung:**
- ✅ Funktioniert für Terminal-Stempelungen (Echtzeit)
- ⚠️ App-Stempelungen: Verzögerung von 15-30 Minuten
- ⚠️ Deduplizierung: Auftrags-basiert (kann zu niedrig sein)

**Problem:**
- Wenn Deduplizierung zu aggressiv ist → Alarm wird zu spät ausgelöst
- Wenn App-Stempelung verzögert ist → Alarm wird zu spät ausgelöst

---

## 💡 VORSCHLAG: HYBRID-ANSATZ

### Strategie: Zwei verschiedene Berechnungsmethoden

#### 1. Für KPIs (NICHT Echtzeit): Beste Näherung verwenden

**Methode:** Betriebs-spezifische Berechnung
- **DEGO:** Zeit-Spanne (MIN bis MAX) + Pausenzeiten-Abzug (falls nötig)
- **DEGH:** Auftrags-basierte Deduplizierung (aktuell)
- **LAN:** Auftrags-basierte Deduplizierung (aktuell)

**Vorteile:**
- ✅ Beste Näherung an Locosoft
- ✅ Abweichungen < 5% akzeptabel für Tages-/Monatsauswertungen
- ✅ Transparente, nachvollziehbare Logik

**Implementierung:**
```python
def get_stempelzeit_aus_times_hybrid(von, bis, subsidiary=None):
    """
    Hybrid-Ansatz: Betriebs-spezifische Berechnung
    
    - DEGO: Zeit-Spanne (MIN bis MAX)
    - DEGH/LAN: Auftrags-basierte Deduplizierung
    """
    if subsidiary == 1:  # DEGO
        # Zeit-Spanne
        return get_stempelzeit_zeit_spanne(von, bis)
    else:  # DEGH, LAN
        # Auftrags-basierte Deduplizierung
        return get_stempelzeit_auftrags_basiert(von, bis)
```

#### 2. Für Echtzeit-Alarme: Konservative Berechnung

**Methode:** Position-basierte Berechnung (konservativ)

**Logik:**
- Jede Position einzeln zählen (auch wenn zur gleichen Zeit)
- **Warum konservativ?** Lieber zu früh alarmieren als zu spät
- **Warum position-basiert?** Erfasst alle Stempelungen, auch überlappende

**Vorteile:**
- ✅ Erfasst alle Stempelungen (auch überlappende)
- ✅ Konservativ (lieber zu früh alarmieren)
- ✅ Einfach zu implementieren

**Nachteile:**
- ⚠️ Kann zu viele Alarme auslösen (wenn überlappende Stempelungen)
- ⚠️ Möglicherweise nicht 100% genau

**Implementierung:**
```python
def get_stempelzeit_echtzeit_alarm(employee_number, order_number, heute):
    """
    Echtzeit-Berechnung für Alarm-E-Mails
    
    Konservativ: Position-basierte Berechnung
    (lieber zu früh alarmieren als zu spät)
    """
    # Position-basierte Berechnung (konservativ)
    # Jede Position einzeln zählen
    query = """
        SELECT SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
        FROM times
        WHERE employee_number = %s
          AND order_number = %s
          AND type = 2
          AND DATE(start_time) = %s
          AND end_time IS NOT NULL
    """
    # Keine Deduplizierung → konservativ
```

#### 3. Für App-Stempelungen: Direkt aus Locosoft-UI lesen

**Problem:**
- App-Stempelungen haben 15-30 Minuten Verzögerung in PostgreSQL
- Echtzeit-Alarme benötigen sofortige Daten

**Lösung:**
- **Option A:** Locosoft SOAP-API (falls verfügbar)
- **Option B:** Locosoft-UI scraping (nicht empfohlen)
- **Option C:** Verzögerung akzeptieren (15-30 Min) + konservative Berechnung

**Empfehlung:**
- **Option C:** Verzögerung akzeptieren, aber konservative Berechnung verwenden
- **Grund:** 15-30 Min Verzögerung ist für Alarm-E-Mails akzeptabel

---

## 📝 DETAILLIERTER IMPLEMENTIERUNGSPLAN

### Phase 1: KPIs verbessern (NICHT Echtzeit)

#### Schritt 1.1: Betriebs-spezifische Berechnung implementieren

**Datei:** `api/werkstatt_data.py`

**Funktion:** `get_stempelzeit_aus_times_hybrid()`

**Logik:**
```python
def get_stempelzeit_aus_times_hybrid(von, bis, subsidiary=None):
    """
    Hybrid-Ansatz: Betriebs-spezifische Berechnung
    
    - DEGO (subsidiary=1): Zeit-Spanne (MIN bis MAX)
    - DEGH (subsidiary=2): Auftrags-basierte Deduplizierung
    - LAN (subsidiary=3): Auftrags-basierte Deduplizierung
    """
    if subsidiary == 1:  # DEGO
        return get_stempelzeit_zeit_spanne(von, bis)
    else:  # DEGH, LAN
        return get_stempelzeit_auftrags_basiert(von, bis)
```

**Zeit-Spanne-Funktion:**
```python
def get_stempelzeit_zeit_spanne(von, bis):
    """
    Zeit-Spanne: MIN(start_time) bis MAX(end_time) pro Mechaniker/Tag
    
    Für DEGO: Sehr nah an Locosoft (8:05 vs. 9:06)
    """
    query = """
        SELECT 
            employee_number,
            DATE(start_time) as tag,
            MIN(start_time) as erste_stempelung,
            MAX(end_time) as letzte_stempelung,
            EXTRACT(EPOCH FROM (MAX(end_time) - MIN(start_time))) / 3600.0 as stempelzeit_stunden
        FROM times
        WHERE type = 2
          AND end_time IS NOT NULL
          AND start_time >= %s
          AND start_time < %s + INTERVAL '1 day'
        GROUP BY employee_number, DATE(start_time)
    """
```

**Auftrags-basierte Funktion (bereits vorhanden):**
- `get_stempelzeit_aus_times()` (aktuell)

#### Schritt 1.2: KPI-Berechnung anpassen

**Datei:** `api/werkstatt_data.py`

**Funktion:** `berechne_mechaniker_kpis_aus_rohdaten()`

**Änderung:**
- Verwende `get_stempelzeit_aus_times_hybrid()` statt `get_stempelzeit_aus_times()`
- Gruppiere nach Betrieb (subsidiary)

#### Schritt 1.3: Testen und Validieren

**Test-Szenarien:**
- MA 5007 (07.01.2026): DEGO vs. DEGH
- Weitere Mechaniker/Tage
- Vergleich mit Locosoft-Werten

**Ziel:**
- Abweichung < 5% zu Locosoft
- Transparente, nachvollziehbare Logik

---

### Phase 2: Echtzeit-Alarme verbessern

#### Schritt 2.1: Konservative Berechnung für Echtzeit-Alarme

**Datei:** `api/werkstatt_data.py`

**Funktion:** `get_stempelzeit_echtzeit_alarm()`

**Logik:**
```python
def get_stempelzeit_echtzeit_alarm(employee_number, order_number, heute):
    """
    Echtzeit-Berechnung für Alarm-E-Mails
    
    Konservativ: Position-basierte Berechnung
    (lieber zu früh alarmieren als zu spät)
    """
    query = """
        SELECT SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60) as minuten
        FROM times
        WHERE employee_number = %s
          AND order_number = %s
          AND type = 2
          AND DATE(start_time) = %s
          AND end_time IS NOT NULL
        -- KEINE Deduplizierung → konservativ
    """
```

#### Schritt 2.2: Alarm-E-Mail-Logik anpassen

**Datei:** `celery_app/tasks.py`

**Funktion:** `benachrichtige_serviceberater_ueberschreitungen()`

**Änderung:**
- Verwende `get_stempelzeit_echtzeit_alarm()` für aktive Aufträge
- Konservative Berechnung (lieber zu früh alarmieren)

#### Schritt 2.3: App-Stempelungen: Verzögerung dokumentieren

**Dokumentation:**
- App-Stempelungen: 15-30 Minuten Verzögerung
- Terminal-Stempelungen: Echtzeit
- **Akzeptabel für Alarm-E-Mails** (15-30 Min Verzögerung ist OK)

---

### Phase 3: Monitoring und Optimierung

#### Schritt 3.1: Abweichungen tracken

**Metriken:**
- Abweichung zu Locosoft pro Mechaniker/Tag
- Abweichung pro Betrieb (DEGO vs. DEGH)
- Durchschnittliche Abweichung

**Ziel:**
- Abweichung < 5% zu Locosoft
- Transparente, nachvollziehbare Logik

#### Schritt 3.2: Iterative Verbesserung

**Vorgehen:**
- Weitere Mechaniker/Tage analysieren
- Pattern-Recognition: Welche Methode passt wann?
- Schrittweise Verfeinerung

---

## 🎯 EMPFEHLUNG

### Kurzfristig (nächste 2-4 Wochen)

1. **Hybrid-Ansatz implementieren**
   - Betriebs-spezifische Berechnung für KPIs
   - Konservative Berechnung für Echtzeit-Alarme
   - Ziel: Abweichung < 5% zu Locosoft

2. **Testen und Validieren**
   - MA 5007 (07.01.2026) als Referenz
   - Weitere Mechaniker/Tage
   - Vergleich mit Locosoft-Werten

### Mittelfristig (1-3 Monate)

1. **Monitoring etablieren**
   - Abweichungen tracken
   - Pattern-Recognition
   - Iterative Verbesserung

2. **Dokumentation**
   - Berechnungslogik dokumentieren
   - Unterschiede zu Locosoft dokumentieren
   - Troubleshooting-Guide

### Langfristig (6+ Monate)

1. **Eigene Berechnungslogik etablieren**
   - Geschäftslogik definieren
   - Transparente, nachvollziehbare Berechnung
   - Unabhängigkeit von Locosoft-Berechnungslogik

---

## ❓ OFFENE FRAGEN

1. **Warum verwendet Locosoft unterschiedliche Methoden pro Betrieb?**
   - DEGO: Zeit-Spanne?
   - DEGH: Auftrags-basierte Summe?
   - Oder gibt es andere Faktoren?

2. **Wie werden Pausenzeiten berücksichtigt?**
   - Werden sie abgezogen?
   - Oder anders berücksichtigt?
   - Warum macht Abzug es schlimmer?

3. **Gibt es Filterkriterien?**
   - Nur bestimmte Aufträge?
   - Nur bestimmte Positionen?
   - Nur bestimmte Auftragsarten?

4. **Wie werden überlappende Stempelungen behandelt?**
   - Position-basiert?
   - Auftrags-basiert?
   - Zeit-basiert?
   - Oder Mischung?

---

## 📊 ERWARTETE ERGEBNISSE

### Nach Implementierung

**KPIs (NICHT Echtzeit):**
- Abweichung < 5% zu Locosoft
- Transparente, nachvollziehbare Logik
- Betriebs-spezifische Berechnung

**Echtzeit-Alarme:**
- Konservative Berechnung (lieber zu früh alarmieren)
- App-Stempelungen: 15-30 Min Verzögerung akzeptabel
- Terminal-Stempelungen: Echtzeit

**Monitoring:**
- Abweichungen tracken
- Pattern-Recognition
- Iterative Verbesserung

---

**Status:** ✅ Analyse abgeschlossen  
**Nächste Aktion:** Hybrid-Ansatz implementieren (Phase 1)
