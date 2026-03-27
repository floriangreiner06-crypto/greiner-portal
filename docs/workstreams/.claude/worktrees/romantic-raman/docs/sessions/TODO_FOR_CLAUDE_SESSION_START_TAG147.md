# TODO FÜR CLAUDE - SESSION START TAG 147
**Erstellt:** 2025-12-30
**Basis:** Session TAG 146 (TEK Refactoring erfolgreich)

---

## 📋 OFFENE AUFGABEN

### 1. Git Commit erstellen (WICHTIG!)
**Status:** ⏳ Ausstehend
**Dateien:**
- `api/controlling_data.py` (NEU)
- `scripts/tek_api_helper.py` (NEU)
- `api/pdf_generator.py` (geändert - Redesign)
- `scripts/send_daily_tek.py` (geändert - nutzt Helper)
- `scripts/send_daily_auftragseingang.py` (geändert - PG Fix)
- `scripts/imports/import_santander_bestand.py` (geändert - PG Migration)
- `docs/sessions/SESSION_WRAP_UP_TAG146.md` (NEU)
- `docs/sessions/TODO_FOR_CLAUDE_SESSION_START_TAG147.md` (NEU)

**Commit Message:** Siehe SESSION_WRAP_UP_TAG146.md

**Commands:**
```bash
# 1. Lokal (Windows)
git add .
git commit -m "feat(TAG146): TEK Refactoring - Wiederverwendbares Datenmodul + Modernes PDF-Design

[Siehe vollständige Message in SESSION_WRAP_UP_TAG146.md]"

# 2. Server
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'chore: Sync TAG146 - TEK Refactoring'"
```

---

### 2. Andere Reports auf neues Design umstellen
**Status:** 🔄 Geplant
**Ziel:** Konsistentes Design für ALLE PDF-Reports

**Reports, die umgestellt werden sollten:**
1. **Auftragseingang PDF** (`generate_auftragseingang_komplett_pdf()`)
   - Greiner Logo
   - DRIVE CI Farben
   - Modernes Layout
   - Deutsches Zahlenformat

2. **TEK Filiale PDF** (`generate_tek_filiale_pdf()`)
   - Bereits TEK-Family, sollte aber geprüft werden
   - Gleicher Design-Standard wie TEK Daily

3. **TEK Bereich PDF** (`generate_tek_bereich_pdf()`)
   - Bereits TEK-Family, sollte aber geprüft werden
   - Gleicher Design-Standard wie TEK Daily

4. **Zukünftige Reports:**
   - Alle neuen Reports sollten das neue Design-Template nutzen

**Design-Standard:**
```python
# In pdf_generator.py
DRIVE_BLUE = colors.HexColor('#0066cc')
DRIVE_GREEN = colors.HexColor('#28a745')
DRIVE_RED = colors.HexColor('#dc3545')
DRIVE_YELLOW = colors.HexColor('#ffc107')

def format_currency_short(value):
    """Deutsches Format: 1.500 € statt 1,5k"""
    try:
        v = float(value)
        return f"{v:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0 €"
```

---

### 3. controlling_routes.py refactoren
**Status:** 🔄 Geplant
**Ziel:** Web-UI nutzt auch `api/controlling_data.py`

**Aktuell:**
- `routes/controlling_routes.py` hat eigene DB-Queries
- Duplicate Logik zu `api/controlling_data.py`

**Sollte:**
- Import: `from api.controlling_data import get_tek_data`
- Alle TEK-Routes nutzen `get_tek_data()` statt eigene Queries
- 100% Konsistenz zwischen Web-UI und Reports

**Affected Routes:**
- `/api/controlling/tek`
- `/api/controlling/tek/bereiche`
- `/api/controlling/tek/filiale`

---

### 4. Kalkulatorische Lohnkosten Parametrisierung
**Status:** 💡 Idee
**Aktuell:** Hardcoded 40% in `controlling_data.py`
**Sollte:** Konfigurierbar in DB oder Settings

**Vorschlag:**
```sql
CREATE TABLE controlling_settings (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255),
    beschreibung TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO controlling_settings VALUES
    ('werkstatt_kalk_lohn_prozent', '40', 'Kalkulatorische Lohnkosten in % vom Umsatz', NOW());
```

**Dann in controlling_data.py:**
```python
# Statt hardcoded 0.40
cursor.execute("SELECT value FROM controlling_settings WHERE key = 'werkstatt_kalk_lohn_prozent'")
prozent = float(cursor.fetchone()['value']) / 100.0
kalk_lohnkosten = werkstatt_umsatz * prozent
```

---

### 5. TEK Report Test-Versand an echte Empfänger
**Status:** ⏳ Ausstehend
**Was:** Test-Versand mit finalem Code an echte Empfänger-Liste

**Command:**
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && /opt/greiner-portal/venv/bin/python3 scripts/send_daily_tek.py --force"
```

**Prüfen:**
1. E-Mail kommt an (alle Empfänger)
2. PDF ist korrekt angehängt
3. Werkstatt-Werte sind realistisch (Einsatz ~104k €)
4. Design ist modern mit Logo
5. Zahlenformat ist deutsch

---

### 6. Celery Task für TEK-Reports
**Status:** ✅ Sollte bereits existieren
**Prüfen:** Ist Task korrekt konfiguriert?

```bash
# Celery Beat Schedule prüfen
ssh ag-admin@10.80.80.20 "grep -A 5 'email_tek' /opt/greiner-portal/celery_app/celery_config.py"

# Nächste Ausführung prüfen
# In DRIVE Admin → Celery Task Manager
```

---

### 7. Dokumentation aktualisieren
**Status:** ⏳ Ausstehend

**Dateien aktualisieren:**
1. **`docs/REPORTS_SYSTEM.md`** (falls existiert)
   - Neues controlling_data.py Modul dokumentieren
   - Wiederverwendbare Datenmodule erklären

2. **`docs/PDF_REPORTS.md`** (falls existiert)
   - Neues Design-Template dokumentieren
   - DRIVE CI Farben
   - format_currency_short() Funktion

3. **`README.md`** (falls existiert)
   - TAG 146 erwähnen

---

## 🎯 PRIORITÄT

1. **HIGH:** Git Commit erstellen (Änderungen sichern!)
2. **MEDIUM:** Test-Versand TEK-Report
3. **MEDIUM:** controlling_routes.py refactoren
4. **LOW:** Andere Reports auf neues Design umstellen
5. **LOW:** Kalkulatorische Lohnkosten parametrisieren

---

## 💡 IDEEN FÜR SPÄTER

### Performance-Dashboard für TEK
- Web-UI mit Chart.js
- Trend-Diagramme (DB1 über Zeit)
- Bereichs-Vergleiche
- Filial-Vergleiche

### Export-Funktionen
- TEK-Daten als Excel/CSV exportieren
- Für externe Analysen (z.B. Power BI)

### Alerts/Benachrichtigungen
- Wenn Breakeven unterschritten
- Wenn Marge unter Schwellwert
- Push-Benachrichtigungen oder Slack-Integration

---

**Erstellt von:** Claude Sonnet 4.5
**Basis:** TAG 146 erfolgreich abgeschlossen
