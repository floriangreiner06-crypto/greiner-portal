# TODO FÜR CLAUDE - SESSION START TAG 181

**Erstellt:** 2026-01-12 (nach TAG 180)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

TAG 180 hat erfolgreich abgeschlossen:
- ✅ **Bankenspiegel-Erweiterung** (Kreditlinie, Verfügbar, Zeitverlauf)
- ✅ **Automatische Snapshot-Erstellung** bei MT940/HVB Import
- ✅ **Sortierung nach Kontoinhaber** implementiert
- ✅ **SSOT und PostgreSQL-Kompatibilität** geprüft und bestätigt

**Nächste Schritte:** Testing durch Buchhaltung, dann ggf. Verbesserungen

---

## 🎯 PRIORITÄT 1: Testing durch Buchhaltung

**Status:** ⏳ In Arbeit (User gibt es zum Test)

**Zu prüfen:**
1. [ ] Kontenübersicht zeigt Kreditlinie und Verfügbar korrekt
2. [ ] Zeitverlauf-Ansicht funktioniert
3. [ ] Automatische Snapshots werden erstellt (nach nächstem MT940/HVB Import)
4. [ ] Sortierung nach Kontoinhaber korrekt
5. [ ] Daten entsprechen Excel-Kontoaufstellung (Kontrolle)

**Nach Testing:**
- Feedback sammeln
- Ggf. Anpassungen vornehmen
- Dokumentation aktualisieren

---

## 🎯 PRIORITÄT 2: Weitere Verbesserungen (optional)

### Zeitverlauf-Erweiterungen

**Mögliche Verbesserungen:**
1. [ ] Export-Funktion (Excel/CSV)
2. [ ] Mehr Filter-Optionen (Bank, Kontotyp)
3. [ ] Chart-Visualisierung (Trend-Grafik)
4. [ ] Vergleichsfunktion (Vorwoche, Vormonat)

### Kontenübersicht-Erweiterungen

**Mögliche Verbesserungen:**
1. [ ] Kreditlinien-Verwaltung (manuell bearbeiten)
2. [ ] Zinssatz-Anzeige
3. [ ] Ausnutzungs-Prozent (Kreditlinie ausgenutzt)
4. [ ] Alerts bei niedriger verfügbarer Kreditlinie

### Automatisierung

**Mögliche Verbesserungen:**
1. [ ] Celery-Task für tägliche Snapshot-Erstellung (falls nötig)
2. [ ] Automatische Kreditlinien-Update (falls möglich)
3. [ ] E-Mail-Benachrichtigungen bei kritischen Werten

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Aktueller Stand:**
   - Prüfe Feedback von Buchhaltung
   - Prüfe ob Snapshots automatisch erstellt werden
   - Prüfe ob Zeitverlauf-Ansicht genutzt wird

2. **Bestehende Infrastruktur:**
   - Prüfe `api/bankenspiegel_utils.py` (Snapshot-Funktion)
   - Prüfe `api/bankenspiegel_api.py` (API-Endpunkte)
   - Prüfe `templates/bankenspiegel_zeitverlauf.html` (Frontend)

3. **Datenqualität:**
   - Prüfe ob Kreditlinien in `konten`-Tabelle gepflegt sind
   - Prüfe ob Snapshots erstellt werden (nach Import)
   - Prüfe Datenstand der Konten

---

## 📝 WICHTIGE HINWEISE

### Automatische Snapshot-Erstellung

**Funktionsweise:**
- Bei jedem MT940 Import (3x täglich: 08:00, 12:00, 17:00)
- Bei jedem HVB PDF Import (täglich: 08:30)
- Snapshots werden automatisch in `konto_snapshots` erstellt

**Kreditlinien:**
- Werden aus `konten`-Tabelle übernommen
- Müssen manuell in DB gepflegt werden (falls noch nicht geschehen)

### Excel-Import (optional)

**Datei:** `scripts/imports/import_kontoaufstellung.py`

**Verwendung:**
- Nur für manuelle Kontrolle
- Wird von Buchhaltung verwendet, bis alles in DRIVE korrekt ist
- Nicht für regulären Betrieb nötig

### SSOT-Konformität

**Alle Module sind SSOT-konform:**
- ✅ Verwenden zentrale Funktionen (`db_session()`, `row_to_dict()`, etc.)
- ✅ Keine eigenen `get_db()` Funktionen
- ✅ Zentrale Snapshot-Funktion in `api/bankenspiegel_utils.py`

### PostgreSQL-Kompatibilität

**Alle Queries sind PostgreSQL-kompatibel:**
- ✅ Verwenden `%s` Placeholder
- ✅ `?` Placeholder werden durch `convert_placeholders()` konvertiert
- ✅ Keine SQLite-Syntax

---

## 🔗 RELEVANTE DATEIEN

### Code:
- `api/bankenspiegel_utils.py` - Zentrale Snapshot-Funktion (SSOT)
- `api/bankenspiegel_api.py` - Erweiterte API
- `routes/bankenspiegel_routes.py` - Neue Route
- `templates/bankenspiegel_zeitverlauf.html` - Zeitverlauf-Template
- `static/js/bankenspiegel_zeitverlauf.js` - Zeitverlauf-JavaScript
- `scripts/imports/import_mt940.py` - Snapshot-Erstellung integriert
- `scripts/imports/import_all_bank_pdfs.py` - Snapshot-Erstellung integriert

### Dokumentation:
- `docs/sessions/SESSION_WRAP_UP_TAG180.md` - Session-Zusammenfassung
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG181.md` - Diese Datei

---

## 🚀 NÄCHSTE SCHRITTE

1. **Testing durch Buchhaltung** (Priorität 1)
   - Feedback sammeln
   - Ggf. Anpassungen vornehmen

2. **Weitere Verbesserungen** (Priorität 2, optional)
   - Export-Funktion
   - Filter-Optionen
   - Chart-Visualisierung

3. **Automatisierung** (Priorität 3, optional)
   - Celery-Tasks
   - E-Mail-Benachrichtigungen

**Bereit für nächste Session! 🚀**
