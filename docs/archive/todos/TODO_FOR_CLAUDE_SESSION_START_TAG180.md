# TODO FÜR CLAUDE - SESSION START TAG 180

**Erstellt:** 2026-01-10 (nach TAG 179)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

TAG 179 hat erfolgreich abgeschlossen:
- ✅ **BWA-Dashboard Compact-Design implementiert**
- ✅ **Automatischer Refresh** für Finanzreporting Cube
- ✅ **Redundanzen konsolidiert**
- ✅ **API-Erweiterungen** (Export, Metadaten)

**Nächste Schritte:** Detailverbesserungen am BWA-Dashboard

---

## 🎯 PRIORITÄT 1: BWA-Dashboard Detailverbesserungen

### Frontend-Verbesserungen

**Geplante Verbesserungen:**
1. [ ] Export-Funktion im Frontend integrieren
   - Button bereits im Header vorhanden
   - JavaScript-Funktion für CSV/Excel-Export
   - API-Endpunkt `/api/controlling/bwa/v2/export` erstellen

2. [ ] Druck-Funktion optimieren
   - Print-Stylesheet für bessere Druckausgabe
   - Seitenumbrüche optimieren
   - Header/Footer für Druck

3. [ ] Responsive Design verbessern
   - Mobile-Ansicht optimieren
   - Tabelle auf Mobile als Cards darstellen
   - Filter auf Mobile kompakter

4. [ ] Performance-Optimierungen
   - Lazy Loading für große Tabellen
   - Virtual Scrolling (falls nötig)
   - Debouncing für Filter-Änderungen

5. [ ] Accessibility-Verbesserungen
   - ARIA-Labels hinzufügen
   - Keyboard-Navigation verbessern
   - Screen-Reader-Unterstützung

---

## 🎯 PRIORITÄT 2: Finanzreporting Cube - Frontend-Integration

**Ziel:** Export-Button im Frontend hinzufügen

**Schritte:**
1. [ ] Export-Button in `templates/controlling/finanzreporting_cube.html` hinzufügen
2. [ ] JavaScript-Funktion für CSV/Excel-Export
3. [ ] Metadaten-Endpunkt für Dropdowns nutzen

**Vorteil:** Sofort nutzbar, hoher User-Wert

---

## 🎯 PRIORITÄT 3: Performance-Optimierungen

**Zu prüfen:**
1. [ ] Query-Performance messen
   - Vergleich mit alten Queries
   - Index-Optimierungen
   - Query-Plan-Analyse

2. [ ] Materialized View Refresh-Optimierung
   - Incremental Refresh (falls möglich)
   - Parallel Refresh
   - Refresh-Strategie optimieren

3. [ ] Caching-Strategie
   - API-Response-Caching
   - Frontend-Caching
   - Cache-Invalidation

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Aktueller Stand:**
   - Prüfe `docs/mockups/bwa_v2_compact_mockup.html` (Referenz)
   - Prüfe `templates/controlling/bwa_v2.html` (implementiert)
   - Teste Dashboard im Browser

2. **Bestehende Infrastruktur:**
   - Prüfe `api/controlling_api.py` (BWA API)
   - Prüfe `templates/controlling/bwa_v2.html` (Frontend)
   - Prüfe `celery_app/tasks.py` (Celery-Tasks)

3. **Performance:**
   - Query-Performance prüfen
   - Materialized View Refresh-Zeit messen
   - Frontend-Ladezeiten prüfen

---

## 📝 WICHTIGE HINWEISE

### BWA-Dashboard Design

**Aktuell:**
- Compact-Design implementiert
- Excel-ähnliches Layout
- Monospace-Schrift für Zahlen
- Kompakte KPI-Zeile

**Geplante Verbesserungen:**
- Export-Funktion
- Druck-Optimierung
- Responsive Design
- Performance-Optimierungen

### API-Design

**Aktuelle Endpunkte:**
- `GET /api/controlling/bwa/v2` - BWA-Daten
- `GET /api/controlling/bwa/v2/drilldown` - Drill-Down

**Geplante Erweiterungen:**
- `GET /api/controlling/bwa/v2/export` - Export (CSV/Excel)

### Frontend-Design

**Aktuell:**
- Compact-Design
- Excel-ähnliche Tabelle
- Inline-Filter
- Kompakte KPI-Zeile

**Geplante Verbesserungen:**
- Export-Button funktional
- Druck-Optimierung
- Mobile-Responsive
- Accessibility

---

## 🔗 RELEVANTE DATEIEN

### Code:
- `templates/controlling/bwa_v2.html` - BWA Dashboard (Compact-Design)
- `api/controlling_api.py` - BWA API
- `celery_app/tasks.py` - Celery-Tasks

### Mockups:
- `docs/mockups/bwa_v2_compact_mockup.html` - Referenz-Mockup
- `docs/mockups/bwa_v2_professional_mockup.html` - Alternative
- `docs/mockups/bwa_v2_modern_mockup.html` - Alternative
- `docs/mockups/BWA_V2_DESIGN_EMPFEHLUNGEN.md` - Design-Dokumentation

### Dokumentation:
- `docs/sessions/SESSION_WRAP_UP_TAG179.md` - Session-Zusammenfassung
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG180.md` - Diese Datei

---

## 🚀 NÄCHSTE SCHRITTE

1. **Detailverbesserungen** (Priorität 1)
   - Export-Funktion
   - Druck-Optimierung
   - Responsive Design
   - Performance

2. **Finanzreporting Frontend** (Priorität 2)
   - Export-Button
   - Metadaten-Integration

3. **Performance-Optimierungen** (Priorität 3)
   - Query-Performance
   - Refresh-Optimierung
   - Caching

**Bereit für nächste Session! 🚀**
