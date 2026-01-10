# Grafana für Cognos Cube Nachbau - Analyse

**Datum:** 2025-01-09  
**TAG:** 177  
**Frage:** Kann Grafana beim Nachbau der Cognos Cubes helfen?

---

## 1. GRAFANA IM DRIVE-SYSTEM

### Aktueller Status:
- ✅ **Grafana installiert** (Port 3000)
- ✅ **URL:** http://10.80.80.20:3000/
- ⚠️ **Status:** Erwähnt in Dokumentation, aber nicht aktiv für BWA/Cubes genutzt
- 📊 **Verwendung:** Primär für Monitoring (geplant/erwähnt)

### Referenzen im Codebase:
- `docs/PHASE0_INFRASTRUKTUR_SETUP_ABGESCHLOSSEN.md` - Grafana installiert
- `docs/claude/QUICK_START_NEW_CHAT.md` - Grafana-Integration erwähnt
- Mehrere TODO-Items für Grafana-Dashboards

---

## 2. GRAFANA FÄHIGKEITEN

### ✅ Was Grafana KANN:

1. **Visualisierung:**
   - Interaktive Dashboards
   - Verschiedene Chart-Typen (Line, Bar, Pie, Table, etc.)
   - Zeitreihen-Visualisierung
   - Drill-Down-Funktionalität

2. **Datenquellen:**
   - PostgreSQL (✅ bereits vorhanden!)
   - MySQL, InfluxDB, Prometheus, etc.
   - CSV, JSON APIs

3. **Features:**
   - Variablen/Templates für dynamische Filter
   - Transformationen (Aggregationen, Berechnungen)
   - Alerting
   - Multi-User mit Rollen

### ❌ Was Grafana NICHT KANN:

1. **OLAP Cubes:**
   - ❌ Keine native OLAP-Funktionalität
   - ❌ Keine multidimensionalen Cubes
   - ❌ Keine automatische Aggregation über Dimensionen

2. **Cognos-ähnliche Features:**
   - ❌ Kein Framework Manager (Datenmodellierung)
   - ❌ Kein Transformer (Cube-Erstellung)
   - ❌ Keine PowerCubes (MDC-Dateien)

3. **Multidimensionale Analysen:**
   - ❌ Kein automatisches Drill-Down/Up über Hierarchien
   - ❌ Keine Pivot-Tabellen
   - ❌ Begrenzte Dimensionen-Handling

---

## 3. GRAFANA FÜR BWA - MÖGLICHKEITEN

### Option A: Grafana als Visualisierungs-Layer

#### Architektur:
```
PostgreSQL Materialized Views (Fact-Table)
    ↓
Grafana PostgreSQL Data Source
    ↓
Grafana Dashboards (BWA Visualisierung)
```

#### Vorteile:
- ✅ **Schnelle Visualisierung** ohne Frontend-Entwicklung
- ✅ **Interaktive Dashboards** (Filter, Zeiträume)
- ✅ **Verschiedene Chart-Typen** (BWA-Kaskade, Trends)
- ✅ **Multi-User** mit Rollen
- ✅ **Export-Funktionen** (PDF, CSV)

#### Nachteile:
- ⚠️ **Zusätzliche Infrastruktur** (Grafana Server)
- ⚠️ **Separates Tool** (nicht integriert in DRIVE)
- ⚠️ **Lernkurve** für User
- ⚠️ **Keine OLAP-Funktionalität** (muss in PostgreSQL gemacht werden)

### Option B: Hybrid (DRIVE API + Grafana)

#### Architektur:
```
PostgreSQL Materialized Views
    ↓
DRIVE Flask API (/api/bwa/cube)
    ↓
Grafana JSON Data Source
    ↓
Grafana Dashboards
```

#### Vorteile:
- ✅ **DRIVE API** für Business-Logik
- ✅ **Grafana** nur für Visualisierung
- ✅ **Flexibel** (kann auch direkt DRIVE Frontend nutzen)

#### Nachteile:
- ⚠️ **Zwei Systeme** (DRIVE + Grafana)
- ⚠️ **Doppelte Wartung**

---

## 4. VERGLEICH: GRAFANA vs. UNSER ANSATZ

| Feature | Grafana | DRIVE (PostgreSQL + Flask) |
|---------|---------|---------------------------|
| **Cube-Erstellung** | ❌ Nein | ✅ Materialized Views |
| **OLAP-Funktionalität** | ❌ Nein | ⚠️ Manuell (SQL) |
| **Visualisierung** | ✅ Sehr gut | ⚠️ Chart.js (einfacher) |
| **Dashboards** | ✅ Professionell | ✅ Custom (Bootstrap) |
| **Integration** | ⚠️ Separates Tool | ✅ Integriert in DRIVE |
| **Multi-User** | ✅ Ja | ✅ Flask-Login |
| **Export** | ✅ PDF, CSV | ⚠️ Muss implementiert werden |
| **Wartung** | ⚠️ Zusätzliches Tool | ✅ Alles in DRIVE |
| **Lernkurve** | ⚠️ Grafana-Syntax | ✅ Python/Flask |

---

## 5. EMPFEHLUNG

### ✅ **JA, Grafana kann helfen - aber nur für Visualisierung!**

### Konkrete Anwendung:

#### Szenario 1: Grafana als BWA-Dashboard-Ersatz
```
1. PostgreSQL Materialized Views erstellen (Fact-Table)
2. Grafana PostgreSQL Data Source konfigurieren
3. BWA-Dashboards in Grafana erstellen
4. User nutzen Grafana statt DRIVE BWA Dashboard
```

**Vorteil:** Professionelle Visualisierung, weniger Frontend-Entwicklung  
**Nachteil:** Zwei Systeme, User müssen Grafana lernen

#### Szenario 2: Grafana als zusätzliches Tool
```
1. DRIVE BWA Dashboard bleibt (für normale User)
2. Grafana für erweiterte Analysen (für Power-User)
3. Beide nutzen gleiche Materialized Views
```

**Vorteil:** Beste aus beiden Welten  
**Nachteil:** Doppelte Wartung

#### Szenario 3: Nur DRIVE (ohne Grafana)
```
1. PostgreSQL Materialized Views
2. DRIVE Flask API
3. DRIVE Frontend (Chart.js erweitern)
```

**Vorteil:** Alles in einem System  
**Nachteil:** Mehr Frontend-Entwicklung

---

## 6. PRAKTISCHE IMPLEMENTIERUNG

### Wenn wir Grafana nutzen wollen:

#### Schritt 1: Materialized Views erstellen
```sql
-- Fact-Table (wie in COGNOS_CUBE_NACHBAU_KONZEPT_TAG177.md)
CREATE MATERIALIZED VIEW fact_bwa AS
SELECT
    accounting_date,
    subsidiary_to_company_ref as standort_id,
    CASE 
        WHEN skr51_cost_center BETWEEN 1 AND 7 THEN skr51_cost_center
        ELSE CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER)
    END as kst_id,
    nominal_account_number as konto_id,
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END / 100.0 as betrag
FROM loco_journal_accountings
WHERE accounting_date >= '2024-09-01';
```

#### Schritt 2: Grafana konfigurieren
```yaml
# Grafana Data Source (PostgreSQL)
Host: 127.0.0.1:5432
Database: drive_portal
User: drive_user
Password: DrivePortal2024
```

#### Schritt 3: Dashboard erstellen
- **Panel 1:** BWA-Kaskade (Umsatz → DB1 → DB2 → DB3 → BE)
- **Panel 2:** Monatlicher Trend
- **Panel 3:** Kostenstellen-Breakdown
- **Panel 4:** Konten-Details

---

## 7. ALTERNATIVE: METABASE

### Warum Metabase statt Grafana?

**Metabase** ist speziell für Business Intelligence entwickelt:

| Feature | Grafana | Metabase |
|---------|---------|----------|
| **Zielgruppe** | DevOps/Monitoring | Business Users |
| **OLAP** | ❌ | ⚠️ Begrenzt |
| **Einfachheit** | ⚠️ Technisch | ✅ Business-freundlich |
| **SQL-Editor** | ✅ | ✅ |
| **Visualisierung** | ✅ | ✅ |
| **Self-Service BI** | ⚠️ | ✅ |

**Empfehlung:** Metabase könnte besser für BWA sein als Grafana!

---

## 8. FINALE EMPFEHLUNG

### ✅ **JA, aber mit Einschränkungen:**

1. **Grafana für Visualisierung:** ✅ Gut geeignet
2. **Grafana für Cube-Erstellung:** ❌ Nicht geeignet
3. **Grafana als Ersatz für Cognos:** ❌ Nicht möglich

### Beste Lösung:

**Hybrid-Ansatz:**
```
PostgreSQL Materialized Views (Cube-Ersatz)
    ↓
DRIVE Flask API (Business-Logik)
    ↓
┌─────────────────┬─────────────────┐
│  DRIVE Frontend │  Grafana (opt.)  │
│  (Chart.js)     │  (Power-User)    │
└─────────────────┴─────────────────┘
```

**Vorteile:**
- ✅ Materialized Views = Cube-Ersatz
- ✅ DRIVE API = Business-Logik
- ✅ DRIVE Frontend = Standard-User
- ✅ Grafana = Optionale erweiterte Analysen

---

## 9. NÄCHSTE SCHRITTE

### Option 1: Mit Grafana
1. ⏳ Materialized Views erstellen
2. ⏳ Grafana PostgreSQL Data Source konfigurieren
3. ⏳ BWA-Dashboard in Grafana erstellen
4. ⏳ Testen und validieren

### Option 2: Ohne Grafana (nur DRIVE)
1. ⏳ Materialized Views erstellen
2. ⏳ DRIVE API erweitern
3. ⏳ DRIVE Frontend verbessern (Chart.js)
4. ⏳ Alles in einem System

### Option 3: Metabase statt Grafana
1. ⏳ Metabase installieren
2. ⏳ Materialized Views erstellen
3. ⏳ Metabase Dashboards erstellen
4. ⏳ Business-freundlichere Alternative

---

## 10. ENTSCHEIDUNG

**Empfehlung:** **Option 2 (ohne Grafana)** + **Option 3 (Metabase als Alternative)**

**Begründung:**
- ✅ Alles in DRIVE = Einheitliches System
- ✅ Keine zusätzliche Infrastruktur nötig
- ✅ User müssen nur DRIVE lernen
- ✅ Metabase als Option für Power-User (später)

**Grafana:** Nur wenn bereits vorhanden und User damit vertraut sind.

---

## REFERENZEN

- **Grafana Docs:** https://grafana.com/docs/
- **Metabase:** https://www.metabase.com/
- **Cognos Nachbau:** `docs/COGNOS_CUBE_NACHBAU_KONZEPT_TAG177.md`
- **Grafana im Projekt:** `docs/PHASE0_INFRASTRUKTUR_SETUP_ABGESCHLOSSEN.md`
