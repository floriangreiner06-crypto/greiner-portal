# TODO für Claude - Session Start TAG 193

**Erstellt:** 2026-01-15  
**Letzte Session:** TAG 192

---

## 🔴 PRIORITÄT 1: Performance-Feedback

### 1. Performance testen
- [ ] **WICHTIG:** Bitte Performance nach QA-Feature-Entfernung testen
- [ ] Hard-Refresh (Strg+F5) durchführen
- [ ] Verschiedene Seiten testen (TEK, Werkstatt-Live, Controlling)
- [ ] Feedback geben: Besser oder immer noch langsam?

### 2. Entscheidung: QA-Dateien
- [ ] **Entscheidung nötig:** Sollen QA-Dateien gelöscht werden?
  - `api/qa_api.py`
  - `routes/qa_routes.py`
  - `templates/macros/qa_widget.html`
  - `templates/qa/bugs.html`
  - `templates/qa/bug_detail.html`
- [ ] Oder: Für spätere Reaktivierung aufbewahren?

---

## 🟡 PRIORITÄT 2: Performance-Optimierung (falls nötig)

### Falls Performance immer noch schlecht:
1. **Navigation-Caching implementieren**
   - Per-User-Cache (Session-basiert)
   - Erwartete Verbesserung: 5-10ms → 0.01ms

2. **Werkstatt-Queries analysieren**
   - EXPLAIN ANALYZE durchführen
   - Indizes prüfen/erstellen
   - Materialized Views prüfen

3. **API-Call-Optimierung**
   - Batch-Requests statt einzelne Calls
   - Lazy-Loading für nicht-kritische Daten

---

## 🟢 PRIORITÄT 3: QA-Feature (optional)

### Falls Performance OK ist:
1. **QA-Feature neu implementieren (optimiert)**
   - Lazy-Loading: Modals nur bei Bedarf laden
   - Conditional Loading: Nur auf bestimmten Seiten aktivieren
   - Kleinere JavaScript-Blöcke (nicht alles in base.html)

2. **Claude-Integration vorbereiten**
   - Bug-Reports an Claude senden
   - Bugfix-Vorschläge generieren

---

## 📋 Offene Aufgaben aus vorherigen Sessions

### Aus TAG 192
- [ ] Locosoft Support-Antwort abwarten (AW-Anteil-Frage)
- [ ] Performance-Feedback sammeln

---

## 🔍 Qualitätsprobleme die behoben werden sollten

### 1. QA-Dateien aufräumen
- [ ] Entscheidung: Löschen oder aufbewahren?
- [ ] Falls löschen: Alle QA-Dateien entfernen
- [ ] Falls aufbewahren: Dokumentieren wo/warum

### 2. Navigation-Optimierung
- [ ] Alternative Optimierung prüfen (statt SQL-Filterung)
- [ ] Navigation-Caching implementieren (falls Performance-Probleme)

---

## 📝 Wichtige Hinweise für nächste Session

### Performance
- QA-Feature wurde entfernt wegen Performance-Problemen
- Navigation-Optimierung wurde zurückgerollt
- Feature-Zugriff-Caching ist aktiv (5 Min TTL)

### Codebase
- QA-Blueprints sind in `app.py` auskommentiert
- QA-Dateien existieren noch, aber sind nicht aktiv
- STATIC_VERSION erhöht: `20260115104600`

### Testing
- **WICHTIG:** Performance nach QA-Entfernung testen
- Hard-Refresh erforderlich (Browser-Cache)

---

## 🚀 Nächste Schritte (je nach Performance-Feedback)

### Szenario 1: Performance ist gut
- QA-Feature neu implementieren (optimiert)
- Navigation-Caching optional

### Szenario 2: Performance ist immer noch schlecht
- Navigation-Caching implementieren
- Werkstatt-Queries analysieren
- Weitere Performance-Analyse

### Szenario 3: Performance ist katastrophal
- Rollback auf TAG 191 prüfen
- System-Ressourcen prüfen (CPU, Memory, DB)
- Server-Logs analysieren

---

**Status:** Warte auf Performance-Feedback
