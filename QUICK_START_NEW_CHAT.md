# 🚀 QUICK START - Neue Chat Session

**Für Claude: Diese Datei ZUERST lesen bei neuem Chat!**

---

## ⚡ SCHNELL-KONTEXT (30 Sekunden)

### Was ist das Projekt?
**Greiner Portal** - Internes Web-Portal für:
- 🏦 Bankenspiegel (Transaktionsübersicht mehrerer Banken)
- 📊 Grafana-Integration (Dashboards)
- 🏖️ Urlaubsplaner

### Aktueller Status?
⚠️ **UNKLAR** - Features teilweise verloren durch Refactoring  
📊 **ANALYSE ERFORDERLICH** - Systematischer Feature-Test nötig

### Tech-Stack
- Backend: Flask (Python)
- Frontend: Jinja2 Templates + Bootstrap/CSS
- DB: PostgreSQL (Greiner DB)
- Server: srvlinux01 (`/opt/greiner-portal`)

---

## 📋 START-ROUTINE FÜR NEUE CHATS

### 1️⃣ Erste Fragen an User (Kontext klären)
```
1. "Was ist das Ziel dieser Session?"
2. "Gibt es akute Probleme oder geht es um Weiterentwicklung?"
3. "Welches Feature soll ich mir anschauen?"
```

### 2️⃣ System-Check durchführen
```bash
# Git Status
cd /opt/greiner-portal
git status
git log --oneline -5

# Service Status
sudo systemctl status greiner-portal

# Letzte Sessions
ls -lt docs/sessions/*.md | head -5
```

### 3️⃣ Relevante Dokumente lesen
**WICHTIG:** Diese Dateien geben Überblick!

1. **`PROJECT_STATUS.md`** ← HAUPTDOKUMENT (Feature-Matrix!)
2. **Letzte 2-3 Session-Dateien** in `docs/sessions/`
3. **`FEATURE_TEST_CHECKLIST.md`** ← Wenn Testing nötig

### 4️⃣ Bei Unsicherheit: Analyze!
```bash
# System-Analyse durchführen
./analyze_system.sh > analyse_$(date +%Y%m%d).txt
cat analyse_*.txt
```

---

## 🎯 HÄUFIGE SZENARIEN

### Szenario A: "Feature X funktioniert nicht"
```
1. Feature in FEATURE_TEST_CHECKLIST.md finden
2. Test durchführen
3. Logs prüfen: journalctl -u greiner-portal -f
4. Code-Review: Relevante Dateien in app/
5. Fix implementieren
6. Testen
7. Git commit + PROJECT_STATUS.md aktualisieren
```

### Szenario B: "Wie war das nochmal?"
```
1. PROJECT_STATUS.md öffnen
2. Relevantes Feature in Matrix suchen
3. Session-Dateien durchsuchen: grep -r "keyword" docs/sessions/
4. Code anschauen: app/routes/* oder app/services/*
```

### Szenario C: "Neues Feature entwickeln"
```
1. ERST: Sicherstellen dass Basis stabil ist!
2. PROJECT_STATUS.md prüfen: Alle ✅?
3. DANN: Feature-Branch erstellen
4. Entwickeln
5. Testen mit FEATURE_TEST_CHECKLIST.md
6. Dokumentieren in SESSION_WRAP_UP
```

### Szenario D: "Ich hab den Überblick verloren"
```
1. STOP! Keine weiteren Änderungen!
2. analyze_system.sh ausführen
3. Alle Sessions der letzten Woche lesen
4. Feature-Matrix in PROJECT_STATUS.md ausfüllen
5. FEATURE_TEST_CHECKLIST.md durchgehen
6. DANN: Weiter mit klarem Plan
```

---

## 📁 WICHTIGE DATEIEN / PFADE

### Dokumentation
```
docs/sessions/              ← Session-Protokolle (Datum-basiert!)
PROJECT_STATUS.md           ← Master-Status-Dokument
FEATURE_TEST_CHECKLIST.md   ← Test-Checkliste
CREDENTIALS.md              ← DB/Server Zugänge
```

### Code
```
app/
├── __init__.py            ← Flask App Init
├── routes/                ← URL-Handler
├── models/                ← DB Models  
├── services/              ← Business Logic
└── templates/             ← HTML Templates

static/                    ← CSS, JS, Images
*_parser.py               ← Bank-Parser (Root)
requirements.txt          ← Python Dependencies
```

### System
```
/opt/greiner-portal/      ← Installations-Pfad
venv/                     ← Virtual Environment
logs/                     ← Log-Dateien (falls vorhanden)
```

---

## 🔍 DEBUGGING-TIPPS

### Logs ansehen
```bash
# Service Logs
sudo journalctl -u greiner-portal -f

# Letzte 100 Zeilen
sudo journalctl -u greiner-portal -n 100

# Fehler filtern
sudo journalctl -u greiner-portal | grep -i error
```

### Flask Debug-Mode
```bash
# In .env oder config setzen:
FLASK_DEBUG=True
FLASK_ENV=development

# Service neu starten
sudo systemctl restart greiner-portal
```

### DB-Verbindung testen
```bash
# Python Shell
cd /opt/greiner-portal
source venv/bin/activate
python3

>>> from app import db
>>> db.session.execute('SELECT 1')
```

---

## ⚠️ WICHTIGE REGELN

### DOs ✅
- **IMMER** PROJECT_STATUS.md nach Änderungen aktualisieren
- **IMMER** Session-Protokoll am Ende erstellen
- **IMMER** testen bevor committen
- **IMMER** Git-Commits mit sinnvollen Messages
- **VOR REFACTORING:** Backup-Branch erstellen!

### DON'Ts ❌
- **NIE** direkt auf `main` pushen ohne Test
- **NIE** großes Refactoring ohne vorherigen Feature-Test
- **NIE** DB-Schema ändern ohne Migration
- **NIE** Credentials in Git committen
- **NIE** "quick fixes" ohne Dokumentation

---

## 🆘 TROUBLESHOOTING

### "Service startet nicht"
```bash
sudo systemctl status greiner-portal
sudo journalctl -u greiner-portal -n 50
# Oft: Python-Fehler oder DB-Verbindung
```

### "Import-Fehler in Python"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "DB-Fehler"
```bash
# Credentials prüfen
cat CREDENTIALS.md
# Connection testen (siehe oben)
```

### "Static Files laden nicht"
```bash
# Cache-Busting prüfen
grep -r "cache_bust" app/
# Browser-Cache löschen
# Service neu starten
```

---

## 📊 PROJEKT-HISTORIE (Kurz)

**TAG 1-10:** Basis-Entwicklung  
**TAG 11-15:** Grafana-Integration  
**TAG 16-20:** PDF-Import & Parser  
**TAG 21-23:** Auth-Fixes, Cache-Busting, Refactoring  

**Problem:** Features gingen während Entwicklung verloren  
**Lösung:** Diese Dokumentations-Struktur! 🎯

---

## 🎯 ZIEL DIESER STRUKTUR

**Beim nächsten Chat soll Claude:**
1. In 2 Minuten vollen Kontext haben
2. Sofort produktiv arbeiten können
3. Keine Zeit mit "Was war nochmal...?" verschwenden
4. Systematisch Features prüfen können
5. Keine Features mehr verlieren!

---

## 💡 NEXT STEPS

**Aktuell (Tag 24):**
1. ✅ Neue Dokumentations-Struktur erstellt
2. ⏳ System-Analyse durchführen
3. ⏳ Feature-Matrix ausfüllen
4. ⏳ Kaputte Features identifizieren
5. ⏳ Fixes priorisieren

**Danach:**
- Stabilisierung
- Fehlende Features wiederherstellen
- Tests schreiben
- Weiterentwicklung

---

## 📞 KONTAKT / HILFE

**Bei Fragen zur Struktur:**
- Diese Datei wurde am 2025-11-10 erstellt
- Zweck: Besserer Chat-Einstieg + Überblick behalten
- Kann jederzeit angepasst werden!

**User:** ag-admin  
**Server:** srvlinux01  
**Projekt:** /opt/greiner-portal

---

**🚀 BEREIT? Los geht's!**
