# Hyundai Diagnose-Vergütung: Analyse & Workflow-Vorschlag

**Erstellt:** 2026-01-09 (TAG 173)  
**Basis:** Hyundai Garantie-Richtlinie 2025-09 + Rundschreiben RS 2023-016, RS 2024-001

---

## 🎯 PROBLEMSTELLUNG

**Aktuelle Situation:**
- Diagnose bei Garantie-Aufträgen ist sehr aufwendig (meist 1-3 Stunden)
- Garantie-AW-Preis: **8,43€** (vs. Standard-Werkstatt: 11,90€)
- Diagnosezeiten sind normalerweise **NICHT vergütet** (in Standardarbeitszeiten enthalten)
- **Ergebnis:** Bei jedem Garantie-Auftrag wird Geld verloren

**Ziel:** Mehr Zeit für Diagnose in Rechnung stellen, um Verluste zu minimieren

---

## 📋 WAS WIRD GRUNDSÄTZLICH VERGÜTET?

### 1. Standardarbeitszeiten (LTS)
- **Enthalten:** Vorbereitung, Reparatur, Prüfzeiten
- **Plus:** 20% Warte-/Rüst-/Pausenzeiten
- **Plus:** 5% äußere Einflüsse
- **Formel:** Ist-Arbeitszeit × 1,26 = Standardarbeitszeit
- **Problem:** Diagnose ist hier bereits "eingepreist", aber oft nicht ausreichend

### 2. GDS-Grundprüfung (RS 2024-001)
- **Arbeitscode:** `BASICA00`
- **Vergütung:** **1 AW** (ca. 8,43€)
- **Voraussetzung:** Keine störungsrelevanten Fehlercodes vorhanden
- **Einsatz:** Bei JEDEM Garantieauftrag möglich
- **Wichtig:** Nur einmal pro Werkstattauftrag, nicht mit RQ0 kombinierbar

### 3. Erweiterte Diagnose (RQ0)
- **Arbeitscode:** `RQ0`
- **Vergütung:** **3 AW** (ca. 25,29€)
- **Voraussetzung:** Fehlercodes wurden erfasst und Reparaturen durchgeführt
- **Einsatz:** Wenn GDS-Grundprüfung Fehlercodes findet

### 4. TT-Zeiten (Tatsächliche Zeit)
- **Bis 0,9 Stunden (9 AW):** **OHNE Freigabe** abrechenbar ⚠️ **WICHTIG: Stunden, nicht AW!**
- **Ab 1,0 Stunden (10 AW):** Freigabepflichtig über GWMS
- **Wichtig:** Nur tatsächlich aufgewendete Zeit, nicht generell 0,9h
- **Stempelzeiten:** Müssen immer mit angehängt werden
- **Umrechnung:** 0,9 Stunden = 54 Minuten = **9 AW** (bei 1 AW = 6 Minuten)

### 5. Such- und Diagnosezeiten (RS 2023-016)
- **Einreichung:** Über GWMS als Freigabe (Antragstyp: T, Freigabetyp: DK)
- **Voraussetzungen:**
  - Mindestens ein **Hyundai Technik Master** hat die Diagnose durchgeführt
  - Ggf. GSW Hotline-Ticket (nicht zwingend bei selbstständiger Fehlersuche)
- **Benötigt:**
  - Aufgeschlüsselte Zeiterfassung
  - Arbeitskarte
  - Bezug auf Garantieantragsnummer
  - Ggf. Hotline-Eintrag
- **Vergütung:** Wird in Einzelfällen/Härtefällen genehmigt

---

## 💰 VERGÜTUNGSVERGLEICH

| Maßnahme | AW | Vergütung (8,43€/AW) | Voraussetzung |
|----------|-----|---------------------|---------------|
| **GDS-Grundprüfung (BASICA00)** | 1 AW | **8,43€** | Keine Fehlercodes |
| **Erweiterte Diagnose (RQ0)** | 3 AW | **25,29€** | Fehlercodes gefunden |
| **TT-Zeit (bis 0,9h = 9 AW)** | **9 AW** | **75,87€** | Keine Freigabe nötig ⚠️ |
| **TT-Zeit (1,0h = 10 AW)** | 10 AW | **84,30€** | Freigabe erforderlich |
| **TT-Zeit (1,5h = 15 AW)** | 15 AW | **126,45€** | Freigabe erforderlich |
| **Such-/Diagnosezeit (Freigabe)** | Variabel | **Variabel** | Technik Master + Antrag |

**Aktueller Garantie-SVS:** 8,43€/AW (vs. Standard: 11,90€/AW)  
**Differenz:** -3,47€ pro AW = **-29% weniger Vergütung**

---

## 🔍 ANALYSE: WARUM VERLIEREN WIR GELD?

### Problem 1: Diagnose nicht abgerechnet
- **Typische Diagnosezeit:** 1-3 Stunden (10-30 AW)
- **Vergütung:** 0€ (in Standardarbeitszeit "enthalten")
- **Verlust:** 84,30€ - 252,90€ pro Auftrag

### Problem 2: GDS-Grundprüfung nicht genutzt
- **Potenzial:** 1 AW pro Garantieauftrag
- **Aktuell:** Wird vermutlich nicht immer eingereicht
- **Verlust:** 8,43€ pro Auftrag

### Problem 3: TT-Zeiten nicht optimal genutzt
- **Bis 0,9 Stunden (9 AW):** Ohne Freigabe möglich ⚠️ **VIEL mehr als gedacht!**
- **Aktuell:** Wird vermutlich nicht immer genutzt
- **Verlust:** Bis zu **75,87€ pro Auftrag** (wenn anwendbar) - **Das ist enorm!**

### Problem 4: Erweiterte Diagnose (RQ0) nicht genutzt
- **Potenzial:** 3 AW wenn Fehlercodes gefunden
- **Aktuell:** Wird vermutlich nicht immer eingereicht
- **Verlust:** 25,29€ pro Auftrag (wenn anwendbar)

---

## 🚀 WORKFLOW-VORSCHLAG: OPTIMIERTE DIAGNOSE-ABRECHNUNG

### Phase 1: Vorbereitung (Serviceberater)

```
┌─────────────────────────────────────────────────────────┐
│ 1. KUNDENANGABE ERFASSEN                                │
│    - O-Ton Beanstandung (wörtlich!)                     │
│    - Symptom seit wann?                                 │
│    - Symptom wie oft?                                   │
│    - Kunde informieren: Diagnose kann Zeit kosten      │
└─────────────────────────────────────────────────────────┘
```

**Checkliste:**
- [ ] Kundenangabe wörtlich dokumentiert
- [ ] Kunde über mögliche Diagnosekosten informiert
- [ ] VIN geprüft (GWMS-Vorprüfung)
- [ ] Garantie-Status geprüft

---

### Phase 2: Diagnose (Techniker)

```
┌─────────────────────────────────────────────────────────┐
│ 2. DIAGNOSE DURCHFÜHREN                                  │
│                                                          │
│    A) GDS-GRUNDPRÜFUNG (IMMER!)                         │
│       → BASICA00 (1 AW) einreichen                       │
│                                                          │
│    B) FEHLERCODES GEFUNDEN?                             │
│       → RQ0 (3 AW) statt BASICA00                        │
│       → Fehlerleitfaden abarbeiten                       │
│                                                          │
│    C) ERWEITERTE DIAGNOSE NÖTIG?                        │
│       → Stempelzeiten erfassen                           │
│       → TT-Zeit prüfen (bis 0,9h = 9 AW ohne Freigabe!) │
│                                                          │
│    D) SEHR AUFWENDIGE DIAGNOSE?                          │
│       → Technik Master erforderlich?                    │
│       → Freigabe-Antrag vorbereiten (Typ T, DK)         │
└─────────────────────────────────────────────────────────┘
```

**Entscheidungsbaum:**

```
Diagnose starten
    │
    ├─→ GDS-Grundprüfung durchführen
    │       │
    │       ├─→ Keine Fehlercodes?
    │       │       └─→ BASICA00 (1 AW) einreichen ✅
    │       │
    │       └─→ Fehlercodes gefunden?
    │               └─→ RQ0 (3 AW) einreichen ✅
    │
    ├─→ Erweiterte Diagnose nötig?
    │       │
    │       ├─→ < 0,9 Stunden (9 AW)?
    │       │       └─→ TT-Zeit ohne Freigabe (bis 9 AW!) ✅
    │       │
    │       └─→ ≥ 1,0 Stunden (10 AW)?
    │               └─→ Freigabe-Antrag vorbereiten
    │                       └─→ Technik Master erforderlich?
    │                               └─→ GWMS Freigabe (Typ T, DK) ✅
    │
    └─→ Reparatur durchführen
            └─→ Standardarbeitszeit (LTS)
```

---

### Phase 3: Abrechnung (Serviceberater)

```
┌─────────────────────────────────────────────────────────┐
│ 3. GARANTIEANTRAG EINREICHEN                            │
│                                                          │
│    Checkliste:                                          │
│    □ BASICA00 oder RQ0 eingereicht?                    │
│    □ TT-Zeit (wenn nötig) eingereicht?                 │
│    □ Stempelzeiten dokumentiert?                       │
│    □ Freigabe-Antrag gestellt (wenn nötig)?            │
│    □ Alle AW vollständig abgerechnet?                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 ERGEBNIS: VERBESSERUNG DER VERGÜTUNG

### Szenario 1: Standard-Garantieauftrag (ohne Optimierung)
- **Diagnosezeit:** 1,5h (15 AW)
- **Vergütung:** 0€ (in LTS enthalten)
- **Reparatur:** 2 AW (Standardarbeitszeit)
- **Gesamt-Vergütung:** 2 AW × 8,43€ = **16,86€**
- **Tatsächliche Kosten:** 17 AW × 8,43€ = **143,31€**
- **Verlust:** **-126,45€** ❌

### Szenario 2: Optimiert (mit GDS + TT)
- **GDS-Grundprüfung:** 1 AW (BASICA00) = **8,43€**
- **TT-Zeit (0,9h = 9 AW):** 9 AW = **75,87€** ⚠️ **VIEL mehr!**
- **Reparatur:** 2 AW (Standardarbeitszeit) = **16,86€**
- **Gesamt-Vergütung:** 12 AW × 8,43€ = **101,16€**
- **Tatsächliche Kosten:** 17 AW × 8,43€ = **143,31€**
- **Verlust:** **-42,15€** ⚠️ (Verbesserung: +101,28€!) 🎉

### Szenario 3: Optimiert (mit RQ0 + TT)
- **Erweiterte Diagnose:** 3 AW (RQ0) = **25,29€**
- **TT-Zeit (0,9h = 9 AW):** 9 AW = **75,87€** ⚠️
- **Reparatur:** 2 AW (Standardarbeitszeit) = **16,86€**
- **Gesamt-Vergütung:** 14 AW × 8,43€ = **118,02€**
- **Tatsächliche Kosten:** 17 AW × 8,43€ = **143,31€**
- **Verlust:** **-25,29€** ⚠️ (Verbesserung: +121,15€!) 🎉

### Szenario 4: Optimiert (mit Freigabe-Antrag)
- **GDS-Grundprüfung:** 1 AW (BASICA00) = **8,43€**
- **Such-/Diagnosezeit (Freigabe):** 1,5 AW (angenommen) = **12,65€**
- **Reparatur:** 2 AW (Standardarbeitszeit) = **16,86€**
- **Gesamt-Vergütung:** 4,5 AW × 8,43€ = **37,94€**
- **Tatsächliche Kosten:** 17 AW × 8,43€ = **143,31€**
- **Verlust:** **-105,37€** ⚠️ (Verbesserung: +21,08€)

**Fazit:** Auch mit Optimierung bleibt ein Verlust, aber deutlich reduziert!

---

## 🛠️ UMSETZUNG IM GREINER PORTAL

### 1. Garantie-Checkliste erweitern

**Neue Felder in Diagnose-Sektion:**
- [ ] GDS-Grundprüfung durchgeführt?
- [ ] Fehlercodes gefunden? (Ja/Nein)
- [ ] BASICA00 eingereicht? (1 AW)
- [ ] RQ0 eingereicht? (3 AW, wenn Fehlercodes)
- [ ] TT-Zeit erforderlich? (Ja/Nein)
- [ ] TT-Zeit (AW): _____ (max. 0,9 AW ohne Freigabe)
- [ ] Freigabe-Antrag erforderlich? (Ja/Nein)
- [ ] Technik Master durchgeführt? (Ja/Nein)
- [ ] Stempelzeiten dokumentiert? (Ja/Nein)

### 2. Automatische Berechnung

**Workflow-Engine:**
```python
def berechne_diagnose_vergütung(diagnose_daten):
    vergütung = 0
    
    # GDS-Grundprüfung (immer)
    if diagnose_daten['gds_grundpruefung']:
        if diagnose_daten['fehlercodes_gefunden']:
            vergütung += 3  # RQ0 (3 AW)
        else:
            vergütung += 1  # BASICA00 (1 AW)
    
    # TT-Zeit (wenn nötig)
    # WICHTIG: 0,9 Stunden = 9 AW (nicht 0,9 AW!)
    if diagnose_daten['tt_zeit_erforderlich']:
        tt_aw = min(diagnose_daten['tt_zeit_aw'], 9)  # 9 AW = 0,9 Stunden
        vergütung += tt_aw
    
    # Freigabe-Antrag (wenn ≥ 1,0 Stunden = 10 AW)
    if diagnose_daten['tt_zeit_aw'] >= 10:
        # Wird separat beantragt
        pass
    
    return vergütung
```

### 3. Dashboard-Integration

**Neue KPIs:**
- Diagnose-Vergütung pro Auftrag
- BASICA00/RQ0 Quote
- TT-Zeit-Nutzung
- Freigabe-Anträge (offen/genehmigt/abgelehnt)
- Verlust-Reduktion durch Optimierung

### 4. Warnungen

**Automatische Hinweise:**
- ⚠️ "GDS-Grundprüfung noch nicht eingereicht!"
- ⚠️ "TT-Zeit möglich (bis 0,9 AW ohne Freigabe)"
- ⚠️ "Freigabe-Antrag erforderlich (> 0,9 AW)"
- ⚠️ "Technik Master erforderlich für Freigabe"

---

## 📋 CHECKLISTE FÜR SERVICEBERATER

### Bei jedem Garantieauftrag:

- [ ] **GDS-Grundprüfung durchführen lassen**
  - [ ] BASICA00 (1 AW) einreichen, wenn keine Fehlercodes
  - [ ] RQ0 (3 AW) einreichen, wenn Fehlercodes gefunden

- [ ] **TT-Zeit prüfen** ⚠️ **WICHTIG: 0,9 Stunden = 9 AW!**
  - [ ] Wenn Diagnose > Standardarbeitszeit: TT-Zeit erfassen
  - [ ] Bis 0,9 Stunden (9 AW): Ohne Freigabe einreichen ✅
  - [ ] Ab 1,0 Stunden (10 AW): Freigabe-Antrag vorbereiten

- [ ] **Freigabe-Antrag (wenn nötig)**
  - [ ] Technik Master hat Diagnose durchgeführt?
  - [ ] Aufgeschlüsselte Zeiterfassung vorhanden?
  - [ ] Arbeitskarte vorhanden?
  - [ ] GWMS-Antrag (Typ T, Freigabetyp DK) stellen

- [ ] **Dokumentation**
  - [ ] Stempelzeiten dokumentiert
  - [ ] Alle AW vollständig abgerechnet
  - [ ] Garantieantrag innerhalb 21 Tage eingereicht

---

## 💡 BEST PRACTICES

### 1. GDS-Grundprüfung IMMER durchführen
- **Kosten:** Minimal (1 AW = 8,43€)
- **Nutzen:** Zusätzliche Vergütung + frühzeitige Fehlererkennung
- **Empfehlung:** Bei JEDEM Garantieauftrag

### 2. TT-Zeit konsequent nutzen ⚠️ **KRITISCH!**
- **Bis 0,9 Stunden (9 AW):** Immer einreichen (keine Freigabe nötig) - **Das ist enorm viel!**
- **Ab 1,0 Stunden (10 AW):** Freigabe-Antrag stellen (lohnt sich meist)
- **Potenzial:** Bis zu **75,87€ zusätzliche Vergütung pro Auftrag**

### 3. Technik Master einsetzen
- **Bei aufwendigen Diagnosen:** Immer Technik Master einsetzen
- **Vorteil:** Freigabe-Anträge haben höhere Erfolgsquote

### 4. Dokumentation ist entscheidend
- **Stempelzeiten:** Immer dokumentieren
- **Arbeitskarte:** Vollständig ausfüllen
- **Kundenangabe:** Wörtlich erfassen

---

## 🎯 ZIELSETZUNG

**Kurzfristig (1-3 Monate):**
- GDS-Grundprüfung bei 100% der Garantieaufträge
- TT-Zeit-Nutzung: 50% der relevanten Fälle
- Verlust-Reduktion: **+80-100€ pro Auftrag** ⚠️ **VIEL mehr als gedacht!**

**Mittelfristig (3-6 Monate):**
- Freigabe-Anträge: 80% Erfolgsquote
- Verlust-Reduktion: **+100-120€ pro Auftrag**
- Automatisierung im Portal

**Langfristig (6-12 Monate):**
- Vollständige Integration in Garantie-Checkliste
- Dashboard mit Echtzeit-KPIs
- Verlust-Reduktion: **+120-150€ pro Auftrag** (durch optimale Nutzung aller Möglichkeiten)

---

## 📞 ANSPRECHPARTNER

**Hyundai Garantie:**
- Fernando Scarico
- Teamleiter Garantie
- Tel: 069 380 767-220
- E-Mail: fernando.scarico@hyundai.de

**Bei Fragen zu:**
- Such- und Diagnosezeiten (RS 2023-016)
- GDS-Grundprüfung (RS 2024-001)
- TT-Zeiten
- Freigabe-Anträgen

---

## 📚 QUELLEN

1. **Garantie-Richtlinie 2025-09** (112 Seiten)
   - Grundlagen der Garantieabwicklung
   - Standardarbeitszeiten
   - TT-Zeiten

2. **Rundschreiben RS 2023-016** (Such- und Diagnosezeiten)
   - Prozessänderung zu Diagnosezeiten
   - Freigabe-Antrag über GWMS

3. **Rundschreiben RS 2024-001** (GDS-Grundprüfung)
   - Standardisierte Nutzung des GDS-Testers
   - BASICA00 (1 AW) Vergütung

4. **Verwendung von TT-Zeiten**
   - RTT/HTT Arbeitsnummern
   - Freigabepflicht ab 0,9h

---

*Analyse erstellt: 2026-01-09 (TAG 173)*
