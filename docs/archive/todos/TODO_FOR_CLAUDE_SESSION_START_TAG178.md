# TODO FÜR CLAUDE - SESSION START TAG 178

**Erstellt:** 2026-01-10 (nach TAG 177)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

TAG 177 hat erfolgreich abgeschlossen:
- ✅ Direkte Kosten -100.381,57 € Differenz: **GELÖST**
- ✅ Indirekte Kosten -21.840,34 € Differenz: **GELÖST**
- ✅ Alle BWA-Positionen sind jetzt analog zu Globalcube
- ✅ Ergebnisse in DRIVE passen wie erwartet

**Nächste Aufgabe:** Finanzreporting entwickeln (wie vorgeschlagen)

---

## 🎯 PRIORITÄT 1: Finanzreporting entwickeln

**Kontext:** Siehe `docs/COGNOS_CUBE_NACHBAU_KONZEPT_TAG177.md`

**Ziel:** Finanzreporting-System mit Materialized Views und API entwickeln

### Phase 1: Dimensionstabellen erstellen

**Schritte:**
1. [ ] `dim_zeit` Materialized View erstellen
   - Jahr, Monat, Tag aus `accounting_date`
   - Index auf `accounting_date`

2. [ ] `dim_standort` Materialized View erstellen
   - Standort-ID, Standort-Name
   - Mapping: 1=DEG, 2=HYU, 3=LAN

3. [ ] `dim_kostenstelle` Materialized View erstellen
   - KST-ID (skr51_cost_center oder 5. Stelle)
   - KST-Name (aus `accounts_characteristics`)

4. [ ] `dim_konto` Materialized View erstellen
   - Konto, Konto-Name
   - Ebene1-6 (Kontenstruktur)

### Phase 2: Fact-Table erstellen

**Schritte:**
1. [ ] `fact_bwa` Materialized View erstellen
   - Zeit, Standort, KST, Konto
   - Betrag, Menge
   - Alle BWA-relevanten Buchungen

2. [ ] Refresh-Logik implementieren
   - Wann werden Views aktualisiert?
   - Automatisch nach Locosoft-Sync?
   - Manuell via API?

### Phase 3: Flask API erweitern

**Schritte:**
1. [ ] `/api/bwa/cube` Endpunkt erstellen
   - Dimensionen: zeit, standort, kst, konto
   - Measures: betrag, menge
   - Aggregiert dynamisch aus Fact-Table

2. [ ] Filter-Logik implementieren
   - Zeitraum-Filter
   - Standort-Filter
   - KST-Filter
   - Konto-Filter

3. [ ] Aggregations-Funktionen
   - SUM, AVG, COUNT
   - Gruppierung nach Dimensionen

### Phase 4: Frontend erweitern

**Schritte:**
1. [ ] BWA Dashboard erweitern
   - Cube-Funktionalität hinzufügen
   - Drill-Down nach Dimensionen
   - Filter-UI

2. [ ] Visualisierungen
   - Chart.js erweitern
   - Neue Diagramm-Typen
   - Interaktive Dashboards

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Aktueller Stand:**
   - Prüfe `docs/COGNOS_CUBE_NACHBAU_KONZEPT_TAG177.md`
   - Prüfe `docs/MATERIALIZED_VIEWS_BEWERTUNG_TAG177.md`
   - Prüfe `docs/GRAFANA_FUER_COGNOS_NACHBAU_TAG177.md`

2. **Bestehende Infrastruktur:**
   - Prüfe `api/controlling_api.py` (BWA-Logik)
   - Prüfe `templates/controlling/bwa_v2.html` (Frontend)
   - Prüfe Datenbank-Schema (`docs/DB_SCHEMA_POSTGRESQL.md`)

3. **Performance:**
   - Aktuelle Query-Performance prüfen
   - Datenvolumen prüfen
   - Index-Strategie planen

---

## 📝 WICHTIGE HINWEISE

### Materialized Views

**Vorteile:**
- ✅ Schnellere Abfragen (vorgeaggregierte Daten)
- ✅ Dimensionale Analyse möglich
- ✅ Zukunftssicherheit

**Nachteile:**
- ⚠️ Refresh-Logik nötig
- ⚠️ Mehr Wartungsaufwand
- ⚠️ Speicherplatz

**Empfehlung:** Jetzt implementieren, da Filter-Logik verstanden ist!

### API-Design

**Endpunkt-Struktur:**
```
GET /api/bwa/cube?dimensionen=zeit,standort&measures=betrag&filter=...
```

**Response:**
```json
{
  "dimensionen": ["zeit", "standort"],
  "measures": ["betrag"],
  "data": [
    {
      "zeit": "2024-09",
      "standort": "DEG",
      "betrag": 123456.78
    }
  ]
}
```

---

## 🔗 RELEVANTE DATEIEN

### Code:
- `api/controlling_api.py` - BWA-Logik
- `templates/controlling/bwa_v2.html` - Frontend
- `api/db_connection.py` - DB-Verbindung

### Dokumentation:
- `docs/COGNOS_CUBE_NACHBAU_KONZEPT_TAG177.md` - Konzept
- `docs/MATERIALIZED_VIEWS_BEWERTUNG_TAG177.md` - Bewertung
- `docs/DB_SCHEMA_POSTGRESQL.md` - Datenbank-Schema
- `docs/sessions/SESSION_WRAP_UP_TAG177.md` - Session-Zusammenfassung

---

## 🚀 NÄCHSTE SCHRITTE

1. **Dimensionstabellen erstellen** (Phase 1)
2. **Fact-Table erstellen** (Phase 2)
3. **API erweitern** (Phase 3)
4. **Frontend erweitern** (Phase 4)

**Bereit für nächste Session! 🚀**
