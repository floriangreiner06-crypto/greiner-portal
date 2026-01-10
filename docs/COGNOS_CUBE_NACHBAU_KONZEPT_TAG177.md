# Cognos Cube Nachbau - Konzept & Kontext

**Datum:** 2025-01-09  
**TAG:** 177  
**Status:** Konzept-Phase

---

## 1. KONTEXT & GESCHICHTE

### Frühere Versuche

#### TAG 84 (2025-08-25)
- ✅ **GlobalCube Mapping entschlüsselt**
- ✅ **BWA Dashboard erstellt** (Ersatz für GlobalCube F.03)
- ✅ **Kontenrahmen analysiert** (`/tmp/kontenrahmen_utf8.csv`)
- ✅ **Mapping dokumentiert** (`BWA_KONTEN_MAPPING_FINAL.md`)

#### TAG 91 (TODO)
- ⚠️ **"BWA Global Cube Bericht nachbauen (mehrfach versucht)"**
- Status: Offen, mehrfach versucht

### Aktuelle Situation (TAG 177)
- ✅ **Globalcube Server erforscht** (`/mnt/globalcube/`)
- ✅ **Cognos Framework Manager Model analysiert** (`model.xml`)
- ✅ **LOC_Belege View verstanden** (SQL-Struktur)
- ✅ **MDC-Dateien identifiziert** (Stub-Dateien + echte Cubes in versionierten Ordnern)
- 🔄 **100k€ DB3-Abweichung** noch nicht vollständig geklärt

---

## 2. COGNOS TECHNOLOGIE-ÜBERSICHT

### IBM Cognos Analytics Architektur

#### Komponenten:
1. **Framework Manager** (Model-Designer)
   - Erstellt Datenmodelle (`model.xml`)
   - Definiert Query Subjects, Query Items
   - Verbindet Datenquellen (Views, Tabellen)
   - **Datei:** `/mnt/globalcube/System/LOCOSOFT/Package/model.xml`

2. **Transformer** (PowerCube-Erstellung)
   - Erstellt multidimensionale Cubes (MDC-Dateien)
   - Aggregiert Daten für schnelle Abfragen
   - **Dateien:** `/mnt/globalcube/Cubes/*.mdc`

3. **Report Studio / Workspace Advanced**
   - Erstellt Reports auf Basis von Cubes/Models
   - **Dateien:** `/mnt/globalcube/System/LOCOSOFT/Report/*.ppr`

### PowerCube (MDC) Struktur

#### Was ist ein PowerCube?
- **Multidimensionaler Datenwürfel** (OLAP)
- **Vorgeaggregierte Daten** für schnelle Abfragen
- **Dimensionen:** Zeit, Standort, Kostenstelle, Konto, etc.
- **Measures:** Betrag, Menge, etc.

#### MDC-Datei-Format:
- **Binäres Format** (proprietär IBM)
- **Stub-Dateien:** Nur 51 Bytes, Text "Dies ist eine PowerCube-Stubdatei. Nicht löschen!"
- **Echte Cubes:** Mehrere MB, enthalten aggregierte Daten

#### Aktuelle Situation:
```
/mnt/globalcube/Cubes/
├── dashboard_gesamt.mdc (51 Bytes - Stub, Platzhalter)
├── f_belege.mdc (51 Bytes - Stub, Platzhalter)
└── [Versionierte Cubes in Unterordnern]
    ├── dashboard_gesamt__20260110084319/
    │   └── dashboard_gesamt.mdc (17 MB - ECHTER CUBE!)
    ├── f_Belege__20260110083857/
    │   └── f_Belege.mdc (33 MB - ECHTER CUBE!)
    └── ...
```

**Erkenntnis:** 
- ✅ **Stub-Dateien** (51 Bytes) sind nur Platzhalter
- ✅ **Echte Cubes** (17-33 MB) werden in versionierten Unterordnern gespeichert
- ✅ **Naming-Pattern:** `{cube_name}__{YYYYMMDDHHMMSS}/`
- ✅ **Cubes werden regelmäßig neu gebaut** (täglich/bei Bedarf)
- ✅ **Format:** Binäres proprietäres Format (IBM Cognos Transformer)
- ✅ **Struktur:** Enthält "PDBCTRESOURCE" Strings, Dimensionen (CA, ME, TX, AL, DR, CI), verschlüsselte Bereiche

**Beispiele:**
- `dashboard_gesamt__20260110084319/dashboard_gesamt.mdc` (17 MB)
- `f_Belege__20260110083857/f_Belege.mdc` (36 MB)

---

## 3. COGNOS CUBE ERSTELLUNG (THEORIE)

### Workflow (Standard):

```
1. Datenquelle (PostgreSQL)
   ↓
2. Framework Manager Model (model.xml)
   - Query Subjects definieren
   - Dimensionen modellieren
   - Measures definieren
   ↓
3. Transformer
   - Dimensionen auswählen
   - Hierarchien definieren
   - Aggregationen konfigurieren
   - Cube bauen
   ↓
4. PowerCube (MDC)
   - Vorgeaggregierte Daten
   - Schnelle Abfragen
   ↓
5. Reports
   - BWA Reports
   - Dashboards
```

### Dimensionen (aus model.xml analysiert):

1. **Zeit:** `Invoice Date` (Bookkeep Date)
2. **Standort:** `Betrieb_ID`, `Betrieb_Name`
3. **Kostenstelle:** `KST` (aus `skr51_cost_center`)
4. **Konto:** `Acct Nr`, `Konto`
5. **Marke:** `Marke`, `Fabrikat`
6. **Absatzkanal:** `Absatzkanal`
7. **Kostenträger:** `Kostenträger`

### Measures (Facts):

1. **Betrag:** `Ist` (aus `Betrag` in LOC_Belege)
2. **Menge:** `Menge` (aus `posted_count`)

---

## 4. NACHBAU-OPTIONEN

### Option 1: Python-basierter OLAP-Cube

#### Technologie-Stack:
- **Python:** pandas, numpy
- **OLAP-Library:** `pyolap` oder `cubes` (https://cubes.databrewery.org/)
- **Storage:** PostgreSQL (Materialized Views) oder Redis

#### Vorteile:
- ✅ Vollständige Kontrolle
- ✅ Open Source
- ✅ Anpassbar an DRIVE-Architektur
- ✅ Direkte Integration in Flask

#### Nachteile:
- ⚠️ Entwicklung nötig
- ⚠️ Performance-Optimierung erforderlich

### Option 2: PostgreSQL Materialized Views

#### Ansatz:
- **Materialized Views** für vorgeaggregierte Daten
- **Dimensionstabellen** für Hierarchien
- **Flask-API** für Abfragen

#### Vorteile:
- ✅ Nutzt bestehende PostgreSQL-Infrastruktur
- ✅ Schnelle Abfragen
- ✅ Einfache Wartung

#### Nachteile:
- ⚠️ Kein vollständiger OLAP-Support
- ⚠️ Manuelle Aggregationen

### Option 3: Apache Superset / Metabase / Grafana

#### Ansatz:
- **BI-Tool** installieren
- **Datenquellen** verbinden (PostgreSQL)
- **Dashboards** erstellen

#### Vergleich:

| Tool | Zielgruppe | OLAP | Einfachheit | Empfehlung |
|------|------------|------|-------------|------------|
| **Grafana** | DevOps/Monitoring | ❌ | ⚠️ Technisch | ⚠️ Für BWA weniger geeignet |
| **Metabase** | Business Users | ⚠️ Begrenzt | ✅ Business-freundlich | ✅ **Besser für BWA** |
| **Superset** | Data Engineers | ✅ Ja | ⚠️ Komplex | ⚠️ Overkill |

#### Vorteile:
- ✅ Fertige BI-Lösung
- ✅ Interaktive Dashboards
- ✅ Keine Frontend-Entwicklung nötig
- ✅ **Metabase:** Business-freundlich, Self-Service BI

#### Nachteile:
- ⚠️ Zusätzliche Infrastruktur
- ⚠️ Lernen der Tool-Syntax
- ⚠️ Separates Tool (nicht in DRIVE integriert)

**Siehe auch:** `docs/GRAFANA_FUER_COGNOS_NACHBAU_TAG177.md`

### Option 4: Cognos Transformer nachbauen

#### Ansatz:
- **Reverse Engineering** der MDC-Struktur
- **Python-Script** zum Cube-Bauen
- **Eigene Cube-Engine** entwickeln

#### Analyse der MDC-Struktur:
- **Header:** `f1 f3 0d 01` (Magic Number)
- **Ressourcen:** `PDBCTRESOURCE!CHARSET`, `PDBCTRESOURCE!ENCRYPTED_CUBE`
- **Dimensionen:** CA (Categories?), ME (Measures?), TX (Text?), AL (All?), DR (Drill?), CI (Categories Index?)
- **Format:** Binär, teilweise verschlüsselt

#### Vorteile:
- ✅ 100% Kompatibilität mit Globalcube
- ✅ Gleiche Struktur wie Original

#### Nachteile:
- ❌ Sehr aufwendig
- ❌ Proprietäres Format (IBM)
- ❌ Teilweise verschlüsselt
- ❌ Nicht empfohlen (zu komplex)

---

## 5. EMPFOHLENE LÖSUNG

### Hybrid-Ansatz: PostgreSQL + Python

#### Architektur:

```
1. Datenquelle: loco_journal_accountings (PostgreSQL)
   ↓
2. Materialized Views (Dimensionstabellen):
   - dim_zeit (Jahr, Monat, Tag)
   - dim_standort (Standort_ID, Standort_Name)
   - dim_kostenstelle (KST, KST_Name)
   - dim_konto (Konto, Konto_Name, Ebene1-6)
   ↓
3. Fact-Table (Materialized View):
   - fact_bwa (Zeit, Standort, KST, Konto, Betrag, Menge)
   ↓
4. Flask API:
   - /api/bwa/cube?dimensionen=zeit,standort&measures=betrag
   - Aggregiert dynamisch aus Fact-Table
   ↓
5. Frontend:
   - BWA Dashboard (bereits vorhanden)
   - Erweitern um Cube-Funktionalität
```

#### Vorteile:
- ✅ Nutzt bestehende Infrastruktur
- ✅ Schnelle Abfragen (Materialized Views)
- ✅ Flexibel erweiterbar
- ✅ Keine zusätzlichen Tools nötig

---

## 6. IMPLEMENTIERUNGS-PLAN

### Phase 1: Dimensionstabellen erstellen

```sql
-- dim_zeit
CREATE MATERIALIZED VIEW dim_zeit AS
SELECT DISTINCT
    accounting_date,
    EXTRACT(YEAR FROM accounting_date) as jahr,
    EXTRACT(MONTH FROM accounting_date) as monat,
    EXTRACT(DAY FROM accounting_date) as tag
FROM loco_journal_accountings;

-- dim_standort
CREATE MATERIALIZED VIEW dim_standort AS
SELECT DISTINCT
    subsidiary_to_company_ref as standort_id,
    -- Mapping zu Standort-Namen
FROM loco_journal_accountings;

-- dim_kostenstelle
CREATE MATERIALIZED VIEW dim_kostenstelle AS
SELECT DISTINCT
    skr51_cost_center as kst_id,
    -- Fallback: substr(nominal_account_number::TEXT, 5, 1)
    CASE 
        WHEN skr51_cost_center BETWEEN 1 AND 7 THEN skr51_cost_center
        ELSE CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER)
    END as kst_final
FROM loco_journal_accountings
WHERE nominal_account_number BETWEEN 400000 AND 499999;
```

### Phase 2: Fact-Table erstellen

```sql
CREATE MATERIALIZED VIEW fact_bwa AS
SELECT
    accounting_date as zeit_id,
    subsidiary_to_company_ref as standort_id,
    CASE 
        WHEN skr51_cost_center BETWEEN 1 AND 7 THEN skr51_cost_center
        ELSE CAST(substr(CAST(nominal_account_number AS TEXT), 5, 1) AS INTEGER)
    END as kst_id,
    nominal_account_number as konto_id,
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END / 100.0 as betrag,
    CASE WHEN debit_or_credit='S' THEN posted_count ELSE -posted_count END / 100.0 as menge
FROM loco_journal_accountings
WHERE accounting_date >= '2024-09-01';
```

### Phase 3: Cube-API erstellen

```python
# api/cube_api.py
def get_cube_data(dimensionen: list, measures: list, filters: dict):
    """
    Aggregiert Daten aus Fact-Table basierend auf Dimensionen
    """
    # Dynamische SQL-Generierung
    # GROUP BY dimensionen
    # SELECT measures
    # WHERE filters
    pass
```

### Phase 4: Frontend-Integration

- Erweitere BWA Dashboard um Cube-Funktionalität
- Drill-Down / Drill-Up
- Pivot-Tabellen

---

## 7. NÄCHSTE SCHRITTE

### Sofort:
1. ✅ **Dokumentation erstellt** (dieses Dokument)
2. ⏳ **Dimensionstabellen designen** (SQL-Skripte)
3. ⏳ **Fact-Table erstellen** (Materialized View)
4. ⏳ **Cube-API entwickeln** (Python)

### Später:
1. ⏳ **Frontend-Integration**
2. ⏳ **Performance-Tests**
3. ⏳ **Validierung gegen Globalcube**

---

## 8. REFERENZEN

### Cognos-Dokumentation:
- **Framework Manager Model:** `/mnt/globalcube/System/LOCOSOFT/Package/model.xml`
- **LOC_Belege View:** `/mnt/globalcube/System/LOCOSOFT/SQL/schema/LOCOSOFT/views/locosoft.LOC_Belege.sql`
- **Cubes-Verzeichnis:** `/mnt/globalcube/Cubes/`

### DRIVE-Dokumentation:
- **BWA Mapping:** `docs/BWA_KONTEN_MAPPING_FINAL.md`
- **Globalcube Analyse:** `docs/GLOBALCUBE_COGNOS_ANALYSE_TAG177.md`
- **DB3 Abweichung:** `docs/ANALYSE_DB3_ABWEICHUNG_TAG177.md`

### Web-Ressourcen:
- **Cognos Transformer:** IBM Cognos Analytics Dokumentation
- **OLAP Cubes:** https://cubes.databrewery.org/
- **PostgreSQL Materialized Views:** PostgreSQL Dokumentation

---

## 9. ENTSCHEIDUNG

**Empfehlung:** Option 2 (PostgreSQL Materialized Views) + Option 1 (Python API)

**Begründung:**
- Nutzt bestehende Infrastruktur
- Keine zusätzlichen Tools nötig
- Flexibel erweiterbar
- Schnelle Implementierung möglich
- Vollständige Kontrolle über Logik

**Alternative:** Option 3 (Apache Superset) für schnelle BI-Dashboards
