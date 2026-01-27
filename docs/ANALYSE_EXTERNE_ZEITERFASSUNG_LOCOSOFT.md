# Analyse: Externe Zeiterfassung an Locosoft anbinden

**Datum:** 2026-01-21  
**TAG:** 206  
**Zweck:** Prüfung, ob externe Zeiterfassung das KPI-Berechnungsproblem lösen kann

---

## 📋 Aktuelle Situation

### Problem
- **Stempelzeit-Berechnung (St-Anteil) weicht von Locosoft ab**
  - Beispiel MA 5007 (07.01.2026): 
    - Locosoft: 13:05 Std (DEGO: 9:06 Std + DEGH: 3:59 Std)
    - Unsere Berechnung: 8:04 Std (DEGO: 3:21 Std + DEGH: 4:43 Std)
    - **Abweichung: 5:01 Std (38% zu niedrig)**
- **Komplexe Deduplizierungs-Logik nicht nachvollziehbar**
  - Verschiedene Methoden (auftrags-basiert, position-basiert, zeit-spanne) ergeben unterschiedliche Werte
  - Keine Methode passt perfekt zu Locosoft

### Aktuelle Integration
- **Datenquelle:** PostgreSQL-Datenbank (read-only)
  - Host: 10.80.80.8:5432
  - Database: `loco_auswertung_db`
  - Tabelle: `times` (type=1 = Anwesenheit, type=2 = Stempelzeit)
- **Berechnung:** Direkt aus `times`-Tabelle
  - Deduplizierung: `DISTINCT ON (employee_number, order_number, start_time, end_time)`
  - Funktion: `api/werkstatt_data.py` → `get_stempelzeit_aus_times()`

### Locosoft Support-Antwort (Zusammenfassung)
1. **PostgreSQL-DB primär für eigene Produkte**
   - Optional bereitgestellt, primär für interne Nutzung
   - Verantwortung für korrekte Anbindung liegt beim Drittanbieter
2. **Weitergehende Beratung kostenpflichtig**
   - Analysen externer Anbindungen außerhalb des regulären Supports
   - Interpretation der PostgreSQL-Datenbank nicht im Leistungsumfang
3. **Hinweis: Komplexe Berechnung**
   - "Die Berechnung der Stempelzeiten ist recht komplex"
   - "Es müssen jegliche Logiken aus dem Loco-Soft auf die Datenbank angewandt werden"
   - "Arbeitszeiten/Pausen der Mitarbeiter müssen berücksichtigt werden"
4. **Eigene Lösung angeboten**
   - Locosoft bietet eigene Lösung zur Datenauswertung
   - Interesse an persönlichem Gespräch signalisiert

---

## 🔍 Recherche: Externe Zeiterfassung an Locosoft

### Verfügbare Schnittstellen

#### 1. PostgreSQL-Datenbank (aktuell genutzt)
- **Status:** ✅ Verfügbar (read-only)
- **Zugriff:** Direkt auf `times`-Tabelle
- **Problem:** Rohdaten ohne Berechnungslogik
- **Dokumentation:** Keine offizielle Dokumentation zur Berechnungslogik

#### 2. SOAP-API (vorhanden, aber nicht für Zeiterfassung)
- **Status:** ✅ Verfügbar (`tools/locosoft_soap_client.py`)
- **Endpoints:** 
  - `list_workshops()`
  - `list_appointments_by_date()`
  - `write_appointment()` (v2.2)
- **Zeiterfassung:** ❌ Keine SOAP-Methoden für Stempelzeiten gefunden
- **Dokumentation:** WSDL verfügbar, aber keine Zeiterfassungs-Endpoints

#### 3. REST-API (nicht gefunden)
- **Status:** ❌ Keine öffentlich dokumentierte REST-API
- **Zeiterfassung:** Keine Endpoints bekannt

#### 4. Import-Funktion für externe Zeiterfassung
- **Status:** ❓ Unbekannt
- **Frage an Locosoft:** Unterstützt Locosoft Import von Stempelzeiten aus externen Systemen?

---

## 💡 Würde externe Zeiterfassung das Problem lösen?

### Szenario 1: Externe Zeiterfassung → Locosoft Import

**Ablauf:**
1. Mechaniker stempeln in externem System (z.B. Terminal, App)
2. Daten werden nach Locosoft importiert
3. Locosoft berechnet KPIs mit eigener Logik
4. DRIVE liest berechnete Werte aus Locosoft

**Vorteile:**
- ✅ Locosoft-Berechnungslogik wird verwendet (korrekte KPIs)
- ✅ Einheitliches System für alle Auswertungen
- ✅ Keine eigene Berechnungslogik nötig

**Nachteile:**
- ❌ Abhängigkeit von Locosoft-Import-Funktion (unbekannt ob verfügbar)
- ❌ Doppelte Erfassung (wenn Locosoft weiterhin genutzt wird)
- ❌ Mapping von Aufträgen/Positionen nötig
- ❌ Synchronisation zwischen Systemen

**Bewertung:** ⚠️ **Nur sinnvoll, wenn Locosoft Import unterstützt**

---

### Szenario 2: Externe Zeiterfassung → DRIVE direkt

**Ablauf:**
1. Mechaniker stempeln in externem System
2. Daten werden direkt in DRIVE gespeichert
3. DRIVE berechnet KPIs mit eigener Logik
4. Locosoft wird nur noch für Auftragsverwaltung genutzt

**Vorteile:**
- ✅ Volle Kontrolle über Berechnungslogik
- ✅ Transparente, nachvollziehbare KPIs
- ✅ Unabhängigkeit von Locosoft-Berechnungslogik

**Nachteile:**
- ❌ Eigene Berechnungslogik muss entwickelt werden
- ❌ Zwei Systeme für Zeiterfassung (Verwirrung)
- ❌ Synchronisation mit Locosoft-Aufträgen nötig
- ❌ Doppelte Pflege (Aufträge in Locosoft, Zeiten in DRIVE)

**Bewertung:** ⚠️ **Nur sinnvoll, wenn Locosoft komplett ersetzt werden soll**

---

### Szenario 3: Hybrid-Lösung (Externe Erfassung + Locosoft als Quelle)

**Ablauf:**
1. Mechaniker stempeln in externem System
2. Daten werden in DRIVE gespeichert
3. DRIVE berechnet KPIs aus eigenen Daten
4. Locosoft-Daten werden als Referenz/Validierung genutzt

**Vorteile:**
- ✅ Eigene Berechnungslogik (transparent)
- ✅ Vergleich mit Locosoft möglich (Validierung)
- ✅ Schrittweise Migration möglich

**Nachteile:**
- ❌ Doppelte Erfassung (zwei Systeme)
- ❌ Synchronisation nötig
- ❌ Höherer Wartungsaufwand

**Bewertung:** ⚠️ **Nur als Übergangslösung sinnvoll**

---

## 🎯 Kernproblem-Analyse

### Warum weichen die Werte ab?

**Mögliche Ursachen:**
1. **Deduplizierungs-Logik unbekannt**
   - Locosoft verwendet möglicherweise position-basierte Berechnung
   - Unsere auftrags-basierte Deduplizierung ist zu aggressiv
2. **Pausenzeiten-Berechnung**
   - Locosoft Support: "Arbeitszeiten/Pausen müssen berücksichtigt werden"
   - Aktuell: Pausenzeiten werden NICHT abgezogen
3. **Filterkriterien unbekannt**
   - Nur bestimmte Aufträge? (abgerechnet, extern, etc.)
   - Nur bestimmte Positionen?
4. **Zeit-Spanne vs. Summe**
   - DEGO: Zeit-Spanne (8:05) ist nah an Locosoft (9:06)
   - DEGH: Auftrags-basierte Summe (4:43) ist nah an Locosoft (3:59)
   - **Verschiedene Methoden für verschiedene Betriebe?**

### Würde externe Zeiterfassung helfen?

**Kurzantwort:** ❌ **Nein, nicht direkt**

**Begründung:**
1. **Das Problem liegt in der Berechnungslogik, nicht in der Erfassung**
   - Die Rohdaten aus `times`-Tabelle sind korrekt
   - Das Problem ist die Interpretation/Deduplizierung
2. **Externe Zeiterfassung würde das Problem verschieben**
   - Statt Locosoft-Berechnung zu verstehen, müsste eigene Logik entwickelt werden
   - Gleiche Komplexität, nur in anderem System
3. **Locosoft-Berechnungslogik ist nicht dokumentiert**
   - Auch mit externer Zeiterfassung müsste die Logik nachgebildet werden
   - Gleiche Herausforderung wie jetzt

---

## 🔧 Alternative Lösungsansätze

### Option 1: Reverse Engineering der Locosoft-Berechnung ⭐⭐⭐

**Ansatz:**
1. **Detaillierte Analyse der Rohdaten**
   - Alle Stempelungen für einen Mechaniker/Tag analysieren
   - Verschiedene Deduplizierungs-Methoden testen
   - Vergleich mit Locosoft-Werten
2. **Pattern-Recognition**
   - Welche Methode passt zu welchem Betrieb?
   - Gibt es Regeln, die wir übersehen haben?
3. **Iterative Annäherung**
   - Schrittweise die Berechnung verfeinern
   - Ziel: < 1% Abweichung zu Locosoft

**Vorteile:**
- ✅ Nutzt vorhandene Datenquelle
- ✅ Keine zusätzlichen Systeme nötig
- ✅ Transparente, nachvollziehbare Logik

**Nachteile:**
- ❌ Zeitaufwendig
- ❌ Möglicherweise nie 100% genau

**Status:** ⏳ **Bereits in Arbeit** (siehe `docs/ANALYSE_MA_5007_07_01_2026.md`)

---

### Option 2: Locosoft-Berechnungen als Referenz akzeptieren ⭐⭐

**Ansatz:**
1. **Locosoft-Werte als "Single Source of Truth"**
   - DRIVE zeigt Locosoft-Werte direkt an (keine eigene Berechnung)
   - Daten aus Locosoft-Reports/Exporten importieren
2. **Eigene Berechnung nur als Validierung**
   - Vergleich mit Locosoft-Werten
   - Abweichungen dokumentieren, aber nicht korrigieren

**Vorteile:**
- ✅ Keine Berechnungslogik nötig
- ✅ Konsistenz mit Locosoft garantiert
- ✅ Schnelle Implementierung

**Nachteile:**
- ❌ Abhängigkeit von Locosoft-Reports/Exporten
- ❌ Keine Echtzeit-Berechnung möglich
- ❌ Transparenz verloren

**Status:** ⏳ **Möglich, aber nicht ideal**

---

### Option 3: Locosoft-Support bezahlen ⭐

**Ansatz:**
1. **Kostenpflichtige Beratung bei Locosoft**
   - Exakte Berechnungsformel dokumentieren lassen
   - SQL-Query oder Pseudocode erhalten
   - Implementierung in DRIVE

**Vorteile:**
- ✅ Exakte, offizielle Dokumentation
- ✅ Garantiert korrekte Berechnung

**Nachteile:**
- ❌ Kosten (unbekannt)
- ❌ Möglicherweise nicht verfügbar
- ❌ Abhängigkeit von Locosoft-Support

**Status:** ⏳ **Zu prüfen: Kosten vs. Nutzen**

---

### Option 4: Eigene Berechnungslogik entwickeln (unabhängig von Locosoft) ⭐⭐

**Ansatz:**
1. **Geschäftslogik definieren**
   - Wie SOLL Stempelzeit berechnet werden?
   - Welche Deduplizierungs-Regeln sind sinnvoll?
   - Welche Pausenzeiten gelten?
2. **Implementierung in DRIVE**
   - Eigene, transparente Berechnungslogik
   - Dokumentation der Regeln
3. **Kommunikation**
   - Mitarbeiter informieren: "DRIVE verwendet eigene Berechnung"
   - Unterschiede zu Locosoft dokumentieren

**Vorteile:**
- ✅ Volle Kontrolle
- ✅ Transparente, nachvollziehbare Logik
- ✅ Unabhängigkeit von Locosoft

**Nachteile:**
- ❌ Zwei verschiedene Berechnungen (Verwirrung)
- ❌ Möglicherweise nicht akzeptiert (Locosoft als Standard)

**Status:** ⏳ **Möglich, aber Kommunikation wichtig**

---

## 📊 Vergleich der Optionen

| Option | Aufwand | Kosten | Genauigkeit | Transparenz | Empfehlung |
|--------|---------|--------|-------------|-------------|------------|
| **1. Reverse Engineering** | Hoch | Niedrig | 95-99% | Sehr hoch | ⭐⭐⭐ |
| **2. Locosoft als Referenz** | Niedrig | Niedrig | 100% | Niedrig | ⭐⭐ |
| **3. Locosoft-Support bezahlen** | Mittel | Hoch | 100% | Mittel | ⭐ |
| **4. Eigene Logik** | Mittel | Niedrig | 100% | Sehr hoch | ⭐⭐ |
| **Externe Zeiterfassung** | Sehr hoch | Hoch | Unbekannt | Mittel | ❌ |

---

## 🎯 Empfehlung

### Kurzfristig (nächste 2-4 Wochen)
1. **Reverse Engineering fortsetzen** (Option 1)
   - Detaillierte Analyse für weitere Mechaniker/Tage
   - Pattern-Recognition: Welche Methode passt wann?
   - Ziel: < 5% Abweichung zu Locosoft
2. **Locosoft-Support anfragen: Kosten für Beratung**
   - Wie hoch wären die Kosten?
   - Was würde genau geliefert? (Dokumentation, Code, etc.)
   - Zeitrahmen?

### Mittelfristig (1-3 Monate)
1. **Entscheidung basierend auf Reverse Engineering-Ergebnissen**
   - Wenn < 5% Abweichung erreicht: Weiter mit Option 1
   - Wenn nicht: Option 3 (Locosoft-Support) oder Option 4 (eigene Logik) evaluieren

### Langfristig (6+ Monate)
1. **Eigene Berechnungslogik etablieren** (Option 4)
   - Geschäftslogik definieren
   - Transparente, dokumentierte Berechnung
   - Unabhängigkeit von Locosoft-Berechnungslogik

---

## ❌ Fazit: Externe Zeiterfassung

**Kurzantwort:** **Nein, externe Zeiterfassung würde das Problem nicht lösen.**

**Begründung:**
1. **Das Problem liegt in der Berechnungslogik, nicht in der Erfassung**
   - Rohdaten sind korrekt verfügbar
   - Problem ist die Interpretation/Deduplizierung
2. **Externe Zeiterfassung würde zusätzliche Komplexität schaffen**
   - Zwei Systeme zu synchronisieren
   - Gleiche Berechnungslogik müsste entwickelt werden
3. **Bessere Alternativen verfügbar**
   - Reverse Engineering (bereits in Arbeit)
   - Locosoft-Support (kostenpflichtig, aber möglich)
   - Eigene Berechnungslogik (langfristig)

**Empfehlung:** **Weiter mit Reverse Engineering + Optionen evaluieren**

---

## 📝 Nächste Schritte

1. **Reverse Engineering fortsetzen**
   - Weitere Mechaniker/Tage analysieren
   - Pattern-Recognition verfeinern
   - Ziel: < 5% Abweichung

2. **Locosoft-Support: Kosten anfragen**
   - Wie hoch wären die Kosten für Beratung?
   - Was würde genau geliefert?
   - Zeitrahmen?

3. **Geschäftslogik definieren** (für Option 4)
   - Wie SOLL Stempelzeit berechnet werden?
   - Welche Deduplizierungs-Regeln sind sinnvoll?
   - Welche Pausenzeiten gelten?

---

**Status:** ✅ Analyse abgeschlossen  
**Nächste Aktion:** Reverse Engineering fortsetzen + Locosoft-Support Kosten anfragen
