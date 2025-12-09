# TODO FOR CLAUDE SESSION START TAG90

**Datum:** 2025-12-03  
**Vorgänger:** TAG89 (SKR51 Kontobezeichnungen)

---

## 🎯 KONTEXT

TAG89 hat **SKR51-Kontobezeichnungen** für TEK und BWA Drill-Down implementiert.
Konten zeigen jetzt aussagekräftige Namen wie "NW VE Gewerbekunde Leasing" statt "Konto 810831".

---

## 📋 OFFENE PUNKTE

### Prio 1: Monitoring & Stabilität

1. **ServiceBox Scraper beobachten**
   - Lock-File Mechanismus aus TAG88 testen
   - Sollte nur 1x pro Zeitplan laufen (nicht 4-10x)
   - Log prüfen: `journalctl -u greiner-portal | grep -i servicebox`

2. **Leasys Cache Timeout erhöhen**
   - Aktuell: 300s (5min)
   - Problem: Große Requests dauern länger
   - Fix: Timeout auf 600-900s erhöhen

### Prio 2: UI/UX

3. **Login-Seite deployen**
   - Mockup B wurde ausgewählt
   - Template: `templates/login_mockup_b.html` → `login.html`
   - CSS anpassen

4. **Admin-Bereich Navigation**
   - Nur für Admins sichtbar in `base.html`
   - URL: `/admin/system-status`

### Prio 3: Aufräumen

5. **Alte PDF-Parser entfernen** (optional)
   - Nicht mehr benötigt (MT940 ist Standard):
     - `parsers/sparkasse_parser.py`
     - `parsers/vrbank_landau_parser.py`
     - `parsers/genobank_universal_parser.py`
   - Behalten:
     - `parsers/hypovereinsbank_parser_v2.py` (einziger PDF-Import)
     - `parsers/mt940_parser.py` (Haupt-Import)

---

## 🗂️ RELEVANTE DATEIEN

```
# SKR51-Mapping (TAG89)
routes/controlling_routes.py    ← TEK mit SKR51
api/controlling_api.py          ← BWA mit SKR51

# Scheduler (TAG88)
app.py                          ← Lock-File Mechanismus
scheduler/job_definitions.py    ← Job-Übersicht

# Login
templates/login.html            ← Aktuell
templates/login_mockup_b.html   ← Neues Design
```

---

## 🔧 SCHNELLSTART

```bash
cd /opt/greiner-portal
source venv/bin/activate

# Server Status
sudo systemctl status greiner-portal

# Logs prüfen
journalctl -u greiner-portal -f

# Lock-File prüfen (Scheduler)
ls -la /tmp/greiner_scheduler.lock
```

---

## 📊 AKTUELLER STAND

| Modul | Status | Info |
|-------|--------|------|
| TEK Drill-Down | ✅ | SKR51-Bezeichnungen |
| BWA Drill-Down | ✅ | SKR51-Bezeichnungen |
| Job-Scheduler | ✅ | Lock-File aktiv |
| Bank-Import | ✅ | MT940 + 1x PDF (HVB) |
| Login-Seite | ⏳ | Mockup B ready |

---

**Erstellt:** 2025-12-03  
**Von:** Claude (TAG89)
