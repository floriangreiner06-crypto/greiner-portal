# Vorschlag: QA & Bug-Reporting-Tool für DRIVE Portal

**TAG:** 192  
**Datum:** 2026-01-14  
**Status:** Vorschlag  
**Ziel:** Tägliche Feature-Prüfung & einfache Fehlermeldung durch Mitarbeiter

---

## 📋 ZUSAMMENFASSUNG

Ein integriertes QA-Tool, das Mitarbeitern ermöglicht:
1. ✅ **Täglich ihre Features zu prüfen** und Korrektheit zu bestätigen
2. ✅ **Fehler einfach zu melden** mit Screenshots, Kontext und Schritten
3. ✅ **Automatische Claude-Integration** für Bugfix-Vorschläge
4. ✅ **Tracking & Status-Verwaltung** für gemeldete Bugs
5. ✅ **Feature-Health-Dashboard** für Übersicht

---

## 🎯 ZIELSETZUNG

### Hauptziele
- **Proaktive Qualitätssicherung:** Mitarbeiter prüfen täglich ihre Features
- **Schnelle Fehlermeldung:** Einfacher Workflow ohne technische Hürden
- **Automatisierte Analyse:** Claude analysiert Bugs und schlägt Fixes vor
- **Transparenz:** Übersicht über Feature-Status und offene Bugs
- **Kontinuität:** Tägliche Routine für Qualitätssicherung

### Zielgruppen
- **Mitarbeiter:** Tägliche Feature-Prüfung & Fehlermeldung
- **Entwickler (Du):** Bugfix-Vorschläge von Claude, Priorisierung
- **Admin:** Übersicht über System-Gesundheit

---

## 🏗️ ARCHITEKTUR-ÜBERLEGUNGEN

### Option A: Integriertes Dashboard (EMPFOHLEN) ⭐

**Konzept:**
- Neues Feature `qa_dashboard` im DRIVE Portal
- Zugriff für alle Mitarbeiter (Feature: `qa_dashboard`)
- Integration in bestehende Navigation
- DB-basierte Speicherung aller QA-Daten

**Vorteile:**
- ✅ Nahtlose Integration ins bestehende System
- ✅ Nutzt bestehende Auth & Session-Management
- ✅ Einheitliche UI/UX
- ✅ Keine externe Abhängigkeiten

**Nachteile:**
- ⚠️ Erfordert Entwicklung im DRIVE Portal

### Option B: Externes Tool (z.B. Jira, GitHub Issues)

**Vorteile:**
- ✅ Bewährte Tools mit vielen Features
- ✅ Keine eigene Entwicklung nötig

**Nachteile:**
- ❌ Externe Abhängigkeit
- ❌ Zusätzliche Login-Prozesse
- ❌ Keine direkte Integration mit DRIVE
- ❌ Kosten (bei kommerziellen Tools)

**Empfehlung: Option A (Integriertes Dashboard)**

---

## 📊 DATENBANK-SCHEMA

### 1. `feature_qa_checks` (Tägliche Feature-Prüfungen)

```sql
CREATE TABLE feature_qa_checks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL,  -- 'passed', 'failed', 'warning', 'not_checked'
    notes TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, feature_name, check_date)
);

CREATE INDEX idx_qa_checks_user_date ON feature_qa_checks(user_id, check_date DESC);
CREATE INDEX idx_qa_checks_feature ON feature_qa_checks(feature_name);
CREATE INDEX idx_qa_checks_status ON feature_qa_checks(status);
```

**Zweck:** Speichert tägliche Feature-Prüfungen pro Mitarbeiter

### 2. `bug_reports` (Fehlermeldungen)

```sql
CREATE TABLE bug_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    feature_name VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    steps_to_reproduce TEXT,
    expected_behavior TEXT,
    actual_behavior TEXT,
    severity VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'analyzing', 'in_progress', 'fixed', 'closed', 'duplicate'
    priority INTEGER DEFAULT 3,  -- 1=highest, 5=lowest
    screenshot_urls TEXT[],  -- Array von URLs zu Screenshots
    browser_info TEXT,  -- JSON: {browser, version, os}
    url TEXT,  -- URL wo Bug auftrat
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

CREATE INDEX idx_bug_reports_status ON bug_reports(status);
CREATE INDEX idx_bug_reports_feature ON bug_reports(feature_name);
CREATE INDEX idx_bug_reports_reporter ON bug_reports(reporter_id);
CREATE INDEX idx_bug_reports_created ON bug_reports(created_at DESC);
```

**Zweck:** Speichert alle Fehlermeldungen mit vollständigem Kontext

### 3. `bug_analysis` (Claude-Analysen)

```sql
CREATE TABLE bug_analysis (
    id SERIAL PRIMARY KEY,
    bug_report_id INTEGER NOT NULL REFERENCES bug_reports(id) ON DELETE CASCADE,
    analysis_text TEXT NOT NULL,  -- Claude's Analyse
    suggested_fix TEXT,  -- Vorschlag für Fix
    confidence_score INTEGER,  -- 1-100: Wie sicher ist Claude?
    code_suggestions JSONB,  -- Strukturierte Code-Vorschläge
    related_files TEXT[],  -- Dateien die betroffen sein könnten
    estimated_complexity VARCHAR(20),  -- 'trivial', 'easy', 'medium', 'hard', 'complex'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bug_analysis_bug ON bug_analysis(bug_report_id);
```

**Zweck:** Speichert Claude's Analyse und Bugfix-Vorschläge

### 4. `feature_health` (Feature-Gesundheits-Status)

```sql
CREATE TABLE feature_health (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    last_check_date DATE,
    pass_rate DECIMAL(5,2),  -- Prozent der erfolgreichen Checks (letzte 7 Tage)
    open_bugs_count INTEGER DEFAULT 0,
    critical_bugs_count INTEGER DEFAULT 0,
    last_bug_date DATE,
    health_status VARCHAR(20) DEFAULT 'unknown',  -- 'healthy', 'warning', 'critical', 'unknown'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feature_health_status ON feature_health(health_status);
```

**Zweck:** Aggregierte Feature-Gesundheits-Statistiken

---

## 🎨 UI/UX-KONZEPT

### 1. QA Dashboard (Hauptseite)

**Route:** `/qa/dashboard`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  QA Dashboard - Meine Features                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Heute: 3/5 Features geprüft                         │
│  ✅ 2 bestanden | ⚠️ 1 Warnung | ❌ 0 Fehler            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Feature: Bankenspiegel                          │   │
│  │ Status: ✅ Bestanden                             │   │
│  │ Letzte Prüfung: Heute 14:30                     │   │
│  │ [Prüfen] [Fehler melden]                        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Feature: BWA                                    │   │
│  │ Status: ⚠️ Warnung                               │   │
│  │ Letzte Prüfung: Heute 09:15                     │   │
│  │ Notiz: "Filter funktioniert, aber langsam"     │   │
│  │ [Prüfen] [Fehler melden]                        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Feature: Werkstatt Live                         │   │
│  │ Status: ⏳ Nicht geprüft                         │   │
│  │ [Jetzt prüfen]                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Liste aller Features, auf die User Zugriff hat
- Status-Anzeige (✅ Bestanden, ⚠️ Warnung, ❌ Fehler, ⏳ Nicht geprüft)
- Quick-Actions: "Prüfen", "Fehler melden"
- Filter: Nach Status, Feature-Name
- Statistiken: Heute geprüft, Pass-Rate (7 Tage)

### 2. Feature-Prüfung (Modal/Dialog)

**Trigger:** Button "Prüfen" oder "Jetzt prüfen"

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Feature prüfen: Bankenspiegel              │
├──────────────────────────────────────────────┤
│                                              │
│  Bitte prüfen Sie folgende Punkte:          │
│                                              │
│  ☑ Feature lädt ohne Fehler                 │
│  ☑ Daten werden korrekt angezeigt           │
│  ☑ Filter funktionieren                     │
│  ☑ Buttons/Actions funktionieren            │
│  ☑ Performance ist akzeptabel               │
│                                              │
│  Status:                                     │
│  ○ Bestanden                                │
│  ○ Warnung (kleine Probleme)                │
│  ○ Fehler gefunden                          │
│                                              │
│  Notizen (optional):                         │
│  [Textfeld für Notizen]                      │
│                                              │
│  [Abbrechen]  [Speichern]                   │
└──────────────────────────────────────────────┘
```

**Features:**
- Checkliste mit Standard-Punkten
- Status-Auswahl (Bestanden/Warnung/Fehler)
- Notizen-Feld
- Automatische Speicherung mit Timestamp

### 3. Fehler melden (Modal/Dialog)

**Trigger:** Button "Fehler melden"

**Layout:**
```
┌──────────────────────────────────────────────┐
│  Fehler melden: Bankenspiegel                │
├──────────────────────────────────────────────┤
│                                              │
│  Titel: *                                    │
│  [Filter zeigt falsche Daten]               │
│                                              │
│  Beschreibung: *                             │
│  [Textfeld - Was ist das Problem?]          │
│                                              │
│  Schritte zur Reproduktion:                 │
│  1. [Schritt 1]                              │
│  2. [Schritt 2]                              │
│  [+ Schritt hinzufügen]                     │
│                                              │
│  Erwartetes Verhalten:                       │
│  [Was sollte passieren?]                     │
│                                              │
│  Tatsächliches Verhalten:                    │
│  [Was passiert tatsächlich?]                 │
│                                              │
│  Schweregrad:                                │
│  ○ Niedrig (kosmetisch)                     │
│  ● Mittel (beeinträchtigt Nutzung)          │
│  ○ Hoch (Feature unbrauchbar)               │
│  ○ Kritisch (System-Crash)                  │
│                                              │
│  Screenshot:                                 │
│  [Datei auswählen] oder [Screenshot machen]  │
│                                              │
│  [Abbrechen]  [Fehler melden]               │
└──────────────────────────────────────────────┘
```

**Features:**
- Strukturiertes Formular
- Screenshot-Upload (automatisch in `/static/bug_screenshots/`)
- Browser-Info wird automatisch erfasst
- URL wird automatisch erfasst
- Schweregrad-Auswahl

### 4. Bug-Übersicht (Admin/Entwickler)

**Route:** `/qa/bugs`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Bug-Übersicht                                          │
├─────────────────────────────────────────────────────────┤
│  Filter: [Alle] [Offen] [In Bearbeitung] [Geschlossen]  │
│  Feature: [Alle] [Bankenspiegel ▼]                      │
│  Schweregrad: [Alle] [Kritisch ▼]                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ #42 | 🔴 Kritisch | Bankenspiegel                │   │
│  │ Filter zeigt falsche Daten                       │   │
│  │ Reporter: Max Mustermann | 14.01.2026 14:30     │   │
│  │ Status: Offen | Priorität: 1                     │   │
│  │ [Details] [Claude analysieren] [Zuweisen]        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ #41 | 🟡 Mittel | BWA                            │   │
│  │ Performance langsam bei großen Datenmengen        │   │
│  │ Reporter: Anna Schmidt | 14.01.2026 09:15       │   │
│  │ Status: Claude analysiert | Priorität: 2         │   │
│  │ [Details] [Analyse anzeigen]                     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Liste aller Bugs mit Filtern
- Status-Tracking
- Priorisierung
- Claude-Analyse-Button
- Zuweisung zu Entwicklern

### 5. Bug-Details mit Claude-Analyse

**Route:** `/qa/bugs/<id>`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Bug #42: Filter zeigt falsche Daten                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📋 Details                                             │
│  Feature: Bankenspiegel                                 │
│  Reporter: Max Mustermann                               │
│  Erstellt: 14.01.2026 14:30                            │
│  Status: Offen | Schweregrad: Kritisch                 │
│                                                          │
│  📝 Beschreibung                                        │
│  [Vollständige Beschreibung]                            │
│                                                          │
│  🔍 Claude-Analyse                                       │
│  [Button: Claude analysieren]                           │
│                                                          │
│  Nach Analyse:                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 🤖 Claude's Analyse:                            │   │
│  │                                                  │   │
│  │ Problem identifiziert in:                        │   │
│  │ - api/bankenspiegel_api.py (Zeile 145)          │   │
│  │ - routes/bankenspiegel_routes.py (Zeile 78)     │   │
│  │                                                  │   │
│  │ Vorgeschlagener Fix:                             │   │
│  │ [Code-Vorschlag]                                 │   │
│  │                                                  │   │
│  │ Konfidenz: 85%                                   │   │
│  │ Komplexität: Mittel                              │   │
│  │                                                  │   │
│  │ [Fix anwenden] [Manuell bearbeiten]              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  📸 Screenshots                                         │
│  [Screenshot 1] [Screenshot 2]                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Vollständige Bug-Details
- Claude-Analyse mit Code-Vorschlägen
- Screenshot-Anzeige
- Fix-Anwendung (mit Bestätigung)

### 6. Feature-Health-Dashboard (Admin)

**Route:** `/qa/health`

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Feature-Health-Übersicht                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Bankenspiegel                                    │   │
│  │ Status: 🟢 Gesund                                │   │
│  │ Pass-Rate (7 Tage): 95%                          │   │
│  │ Offene Bugs: 0 | Kritisch: 0                     │   │
│  │ Letzte Prüfung: Heute                            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ BWA                                              │   │
│  │ Status: 🟡 Warnung                               │   │
│  │ Pass-Rate (7 Tage): 78%                          │   │
│  │ Offene Bugs: 2 | Kritisch: 0                     │   │
│  │ Letzte Prüfung: Gestern                          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Werkstatt Live                                   │   │
│  │ Status: 🔴 Kritisch                              │   │
│  │ Pass-Rate (7 Tage): 45%                          │   │
│  │ Offene Bugs: 5 | Kritisch: 2                     │   │
│  │ Letzte Prüfung: Vor 3 Tagen                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Übersicht aller Features
- Health-Status (🟢 Gesund, 🟡 Warnung, 🔴 Kritisch)
- Pass-Rate (letzte 7 Tage)
- Bug-Statistiken
- Letzte Prüfung

---

## 🔧 TECHNISCHE IMPLEMENTIERUNG

### 1. Backend-Struktur

```
api/
  └── qa_api.py              # QA-Logik (Feature-Prüfungen, Bugs)
  └── bug_analysis_api.py    # Claude-Integration für Bug-Analyse

routes/
  └── qa_routes.py           # QA-Routes (Dashboard, Bugs, Health)

templates/
  └── qa/
      ├── dashboard.html     # QA Dashboard
      ├── feature_check.html # Feature-Prüfung Modal
      ├── bug_report.html    # Fehler melden Modal
      ├── bugs.html          # Bug-Übersicht
      ├── bug_detail.html    # Bug-Details mit Claude-Analyse
      └── health.html        # Feature-Health-Dashboard
```

### 2. Claude-Integration

**Konzept:**
- API-Endpoint: `/qa/bugs/<id>/analyze`
- Claude bekommt:
  - Bug-Beschreibung
  - Schritte zur Reproduktion
  - Feature-Name
  - Relevante Code-Dateien (via Codebase-Search)
  - Screenshots (falls vorhanden)

**Claude-Analyse:**
1. Codebase durchsuchen nach relevanten Dateien
2. Code analysieren
3. Bug-Ursache identifizieren
4. Fix-Vorschlag generieren
5. Code-Patch erstellen
6. Konfidenz-Score berechnen

**Speicherung:**
- Analyse in `bug_analysis` Tabelle
- Code-Vorschläge als JSONB
- Betroffene Dateien als Array

### 3. Feature-Erkennung

**Automatisch:**
- Aus `config/roles_config.py` → `FEATURE_ACCESS`
- Aus DB → `feature_access` Tabelle
- Kombiniert: Alle Features die User sehen kann

**Manuell:**
- Admin kann Features hinzufügen/entfernen
- Features können deaktiviert werden (nicht mehr prüfbar)

### 4. Screenshot-Upload

**Implementierung:**
- Upload in `/static/bug_screenshots/<bug_id>/`
- Dateinamen: `screenshot_<timestamp>_<index>.png`
- URLs in `bug_reports.screenshot_urls` Array
- Max. 5 Screenshots pro Bug

### 5. Browser-Info-Erfassung

**JavaScript:**
```javascript
// Automatisch beim Öffnen des Bug-Report-Dialogs
const browserInfo = {
    browser: navigator.userAgent,
    version: navigator.appVersion,
    os: navigator.platform,
    screen: {
        width: window.screen.width,
        height: window.screen.height
    },
    url: window.location.href
};
```

---

## 📅 WORKFLOW

### Täglicher Workflow (Mitarbeiter)

1. **Login ins DRIVE Portal**
2. **QA Dashboard öffnen** (`/qa/dashboard`)
3. **Features prüfen:**
   - Für jedes Feature: Button "Prüfen"
   - Checkliste durchgehen
   - Status setzen (Bestanden/Warnung/Fehler)
   - Notizen hinzufügen (optional)
   - Speichern
4. **Bei Fehlern:**
   - Button "Fehler melden"
   - Formular ausfüllen
   - Screenshot hinzufügen (optional)
   - Absenden

### Workflow (Entwickler/Du)

1. **Bug-Übersicht öffnen** (`/qa/bugs`)
2. **Bugs durchgehen:**
   - Priorität setzen
   - Status ändern
   - Claude-Analyse starten (Button)
3. **Claude-Analyse:**
   - Claude analysiert Bug
   - Generiert Fix-Vorschlag
   - Zeigt betroffene Dateien
4. **Fix anwenden:**
   - Claude's Vorschlag prüfen
   - Fix anwenden (Button) oder manuell bearbeiten
   - Status auf "Fixed" setzen
   - Resolution-Notes hinzufügen

### Automatisierter Workflow

1. **Täglich 08:00:** E-Mail an Mitarbeiter mit Features die noch nicht geprüft wurden
2. **Bei neuem Bug:** E-Mail an Entwickler (wenn kritisch)
3. **Feature-Health:** Automatische Berechnung (Pass-Rate, Status)
4. **Claude-Analyse:** Optional automatisch bei neuem Bug (wenn Schweregrad = kritisch)

---

## 🚀 IMPLEMENTIERUNGS-PHASEN

### Phase 1: Grundfunktionen (MVP) ⭐

**Ziel:** Basis-Funktionalität für tägliche Feature-Prüfung

**Umfang:**
- ✅ DB-Schema erstellen
- ✅ QA Dashboard (Feature-Liste)
- ✅ Feature-Prüfung (Modal)
- ✅ Fehler melden (Modal)
- ✅ Bug-Übersicht (Basis)

**Dauer:** ~2-3 Tage

### Phase 2: Claude-Integration

**Ziel:** Automatische Bug-Analyse durch Claude

**Umfang:**
- ✅ Claude-API-Integration
- ✅ Codebase-Search für relevante Dateien
- ✅ Bug-Analyse-Generierung
- ✅ Fix-Vorschläge
- ✅ Bug-Details-Seite mit Analyse

**Dauer:** ~2-3 Tage

### Phase 3: Feature-Health & Statistiken

**Ziel:** Übersicht über System-Gesundheit

**Umfang:**
- ✅ Feature-Health-Dashboard
- ✅ Pass-Rate-Berechnung
- ✅ Automatische Health-Status-Berechnung
- ✅ Statistiken & Charts

**Dauer:** ~1-2 Tage

### Phase 4: Erweiterte Features

**Ziel:** Workflow-Optimierung

**Umfang:**
- ✅ E-Mail-Benachrichtigungen
- ✅ Automatische Claude-Analyse (bei kritischen Bugs)
- ✅ Bug-Zuweisung
- ✅ Kommentare zu Bugs
- ✅ Bug-Historie

**Dauer:** ~2-3 Tage

---

## 📊 MIGRATION & ROLLOUT

### Migration

1. **DB-Schema erstellen:**
   ```sql
   -- Migration-Script in migrations/
   -- migration_tag192_qa_system.sql
   ```

2. **Feature-Zugriff:**
   - Neues Feature `qa_dashboard` in `config/roles_config.py`
   - Zugriff für alle Rollen: `['*']`

3. **Navigation:**
   - Neuer Menüpunkt "QA Dashboard" in Navigation
   - Nur sichtbar wenn User Zugriff hat

### Rollout

1. **Phase 1 (MVP):** Intern testen
2. **Phase 2:** Kleine Gruppe (2-3 Mitarbeiter)
3. **Phase 3:** Alle Mitarbeiter
4. **Schulung:** Kurze Einführung (5-10 Min)

---

## 💡 ERWEITERUNGS-MÖGLICHKEITEN

### Kurzfristig
- **Mobile-Ansicht:** Responsive Design für Smartphones
- **Browser-Extension:** Screenshot-Tool direkt im Browser
- **Slack-Integration:** Bugs als Slack-Nachrichten

### Mittelfristig
- **Automatische Tests:** Integration mit Test-Framework
- **Performance-Monitoring:** Automatische Performance-Checks
- **Regression-Tests:** Automatische Tests bei Fixes

### Langfristig
- **KI-gestützte QA:** Claude prüft Features automatisch
- **Predictive Analytics:** Vorhersage von Bugs
- **A/B-Testing:** Feature-Varianten testen

---

## 🎯 ERFOLGS-KRITERIEN

### Quantitativ
- **Feature-Prüfungen:** >80% der Features täglich geprüft
- **Bug-Response-Zeit:** <24h für kritische Bugs
- **Pass-Rate:** >90% für alle Features
- **Claude-Konfidenz:** >70% für Fix-Vorschläge

### Qualitativ
- **Einfachheit:** Mitarbeiter können ohne Schulung nutzen
- **Geschwindigkeit:** Feature-Prüfung <2 Min
- **Nützlichkeit:** Claude-Vorschläge sind hilfreich
- **Akzeptanz:** Mitarbeiter nutzen Tool regelmäßig

---

## ❓ OFFENE FRAGEN

1. **Claude-API:**
   - Wie wird Claude integriert? (Cursor API, eigene API?)
   - Rate-Limits?
   - Kosten?

2. **Screenshot-Upload:**
   - Max. Dateigröße?
   - Speicherort? (Lokal vs. Cloud)

3. **E-Mail-Benachrichtigungen:**
   - SMTP-Server vorhanden?
   - E-Mail-Templates?

4. **Feature-Liste:**
   - Sollen alle Features prüfbar sein?
   - Oder nur ausgewählte Features?

---

## 📝 NÄCHSTE SCHRITTE

1. **Vorschlag diskutieren** (mit Dir)
2. **Offene Fragen klären**
3. **Prioritäten setzen** (MVP vs. Vollversion)
4. **Implementierung starten** (Phase 1)
5. **Testen & Feedback einholen**

---

## 📚 ANHANG

### Beispiel: Bug-Report

```json
{
  "id": 42,
  "reporter": "Max Mustermann",
  "feature": "bankenspiegel",
  "title": "Filter zeigt falsche Daten",
  "description": "Wenn ich den Filter 'Letzte 30 Tage' wähle, werden Daten von vor 2 Monaten angezeigt.",
  "steps_to_reproduce": [
    "1. Bankenspiegel öffnen",
    "2. Filter 'Letzte 30 Tage' wählen",
    "3. Daten werden angezeigt"
  ],
  "expected_behavior": "Nur Transaktionen der letzten 30 Tage",
  "actual_behavior": "Transaktionen von vor 2 Monaten werden angezeigt",
  "severity": "critical",
  "status": "open",
  "url": "http://10.80.80.20:5000/bankenspiegel/dashboard?filter=30days",
  "browser_info": {
    "browser": "Chrome",
    "version": "120.0",
    "os": "Windows 10"
  }
}
```

### Beispiel: Claude-Analyse

```json
{
  "bug_report_id": 42,
  "analysis_text": "Das Problem liegt in der Filter-Logik in api/bankenspiegel_api.py. Die Funktion get_filtered_transactions() verwendet CURRENT_DATE - 30, aber berücksichtigt nicht, dass die Datenbank-Zeitzone anders ist als die Browser-Zeitzone.",
  "suggested_fix": "Zeitzone-Problem beheben: Verwende timezone-aware Datums-Vergleiche.",
  "confidence_score": 85,
  "code_suggestions": {
    "file": "api/bankenspiegel_api.py",
    "line": 145,
    "old_code": "WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'",
    "new_code": "WHERE transaction_date >= (CURRENT_DATE AT TIME ZONE 'Europe/Berlin') - INTERVAL '30 days'"
  },
  "related_files": [
    "api/bankenspiegel_api.py",
    "routes/bankenspiegel_routes.py"
  ],
  "estimated_complexity": "medium"
}
```

---

**Ende des Vorschlags**
