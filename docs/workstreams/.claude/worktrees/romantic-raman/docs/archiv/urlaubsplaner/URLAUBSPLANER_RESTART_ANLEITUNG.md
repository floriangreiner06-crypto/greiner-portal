# Urlaubsplaner Restart-Anleitung

**Datum:** 2025-12-29  
**Problem:** Code-Änderungen werden nicht wirksam

---

## ✅ RESTART ERFORDERLICH!

Ja, nach Code-Änderungen in Python-Dateien ist **immer ein Service-Restart notwendig**, damit Gunicorn die neuen Code-Änderungen lädt.

---

## Restart-Befehle

### Standard-Restart (empfohlen):
```bash
sudo systemctl restart greiner-portal
```

### Status prüfen:
```bash
sudo systemctl status greiner-portal
```

### Logs live ansehen (nach Restart):
```bash
sudo journalctl -u greiner-portal -f
```

### Hard-Restart (falls Standard-Restart nicht hilft):
```bash
# Service stoppen
sudo systemctl stop greiner-portal

# Alle Gunicorn-Prozesse killen (falls hängend)
sudo pkill -9 -f gunicorn

# 3 Sekunden warten
sleep 3

# Service starten
sudo systemctl start greiner-portal

# Status prüfen
sudo systemctl status greiner-portal
```

---

## Nach dem Restart testen

1. **Browser-Cache leeren:**
   - Strg + Shift + R (Windows/Linux)
   - Cmd + Shift + R (Mac)

2. **Urlaubsplaner öffnen:**
   - `/urlaubsplaner/v2`

3. **Urlaub beantragen testen:**
   - Tage im Kalender anklicken/ziehen
   - "Urlaub beantragen" klicken
   - Prüfen ob keine SQL-Fehler mehr auftreten

---

## Warum ist ein Restart nötig?

- **Gunicorn lädt Python-Code beim Start**
- **Worker-Prozesse halten Code im Speicher**
- **Code-Änderungen werden erst nach Restart wirksam**
- **Templates brauchen KEINEN Restart** (nur Browser-Refresh)

---

## Troubleshooting

### Service startet nicht:
```bash
# Logs prüfen
sudo journalctl -u greiner-portal -n 50

# Syntax-Fehler prüfen
cd /opt/greiner-portal
source venv/bin/activate
python -m py_compile api/vacation_api.py
```

### Service läuft, aber Fehler bleibt:
1. **Browser-Cache leeren** (Strg+Shift+R)
2. **Hard-Restart** durchführen (siehe oben)
3. **Logs prüfen** für weitere Fehler

### Gunicorn-Prozesse hängen:
```bash
# Alle Gunicorn-Prozesse finden
ps aux | grep gunicorn

# Alle killen
sudo pkill -9 -f gunicorn

# Service neu starten
sudo systemctl start greiner-portal
```

---

## Service-Konfiguration

Der Service läuft als:
- **Service-Name:** `greiner-portal`
- **User:** `ag-admin` (vermutlich)
- **Working Directory:** `/opt/greiner-portal`
- **Gunicorn Config:** `/opt/greiner-portal/config/gunicorn.conf.py`
- **Port:** 8000 (laut Config)

---

## Wichtige Hinweise

⚠️ **Bei Code-Änderungen IMMER Restart!**
- Python-Dateien: ✅ Restart erforderlich
- Templates: ❌ Kein Restart (nur Browser-Refresh)
- Static Files: ❌ Kein Restart (nur Browser-Refresh)
- Config-Dateien (.env): ✅ Restart erforderlich

