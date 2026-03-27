# 🚀 QUICK-START - TAG 23

**Datum:** Nach 10. November 2025  
**Status:** Portal läuft, aber Verkaufs-Dashboard lädt nicht

---

## ⚡ PROBLEM

**Symptom:** Auftragseingang-Dashboard zeigt endlos Lade-Spinner

**URL:** http://10.80.80.20/verkauf/auftragseingang

**Was nicht funktioniert:**
- 🔴 Daten laden nicht
- 🔴 Spinner drehen endlos
- 🔴 Keine Fehler-Meldung sichtbar

---

## 🔍 DEBUGGING-SCHRITTE

### 1️⃣ **Browser Console checken**
```
F12 → Console Tab
Suche nach: Fehler (rot)
```

**Häufige Fehler:**
- API 404 Not Found
- API 500 Server Error
- CORS-Fehler
- JSON Parse Error

### 2️⃣ **Network Tab checken**
```
F12 → Network Tab → Seite neu laden
Suche nach: /api/verkauf/auftragseingang
```

**Prüfen:**
- Status Code (sollte 200 sein)
- Response (JSON-Daten vorhanden?)
- Timing (wie lange dauert es?)

### 3️⃣ **Backend Logs checken**
```bash
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal

# Service Status
sudo systemctl status greiner-portal

# Letzte 100 Log-Zeilen
sudo journalctl -u greiner-portal -n 100 --no-pager

# Live Logs (während du die Seite lädst)
sudo journalctl -u greiner-portal -f
```

### 4️⃣ **API direkt testen**
```bash
# Im Browser oder curl
curl http://10.80.80.20/api/verkauf/auftragseingang
```

**Erwartetes Ergebnis:**
```json
{
  "status": "success",
  "data": [ ... ]
}
```

### 5️⃣ **Datenbank prüfen**
```bash
cd /opt/greiner-portal
source venv/bin/activate

sqlite3 data/greiner_controlling.db

# Verkäufe zählen
SELECT COUNT(*) FROM sales;
-- Sollte: 4846 sein

# Letzte Verkäufe
SELECT * FROM sales ORDER BY out_sales_contract_date DESC LIMIT 5;

.quit
```

---

## 📊 BEKANNTE DATEN

### **Datenbank:**
```
Verkäufe:       4.846 (16 im November 2025)
Transaktionen:  49.831
Fahrzeuge:      107
Users:          1
```

### **Cron-Jobs:**
```bash
crontab -l

# Sollte zeigen:
# Verkauf:    0 7-18 * * * ... sync_sales.py
# Stellantis: 0 7-18 * * * ... import_stellantis.py
# Bank-PDFs:  0 7-18 * * * ... import_november_all_accounts_v2.py
```

### **Letzte Sync:**
```bash
tail -30 logs/sync_sales.log

# Sollte zeigen: Letzter erfolgreicher Sync heute
```

---

## 🔧 MÖGLICHE URSACHEN

### **1. API-Route fehlt/falsch**
```bash
# Prüfe ob Route existiert
cd /opt/greiner-portal
grep -r "auftragseingang" api/verkauf_api.py routes/verkauf_routes.py
```

### **2. Blueprint nicht registriert**
```bash
grep "register_blueprint.*verkauf" app.py
# Sollte zeigen: app.register_blueprint(verkauf_api)
```

### **3. Datenbank leer**
```bash
sqlite3 data/greiner_controlling.db "SELECT COUNT(*) FROM sales;"
# Sollte: 4846 sein
```

### **4. JavaScript-Fehler**
```
F12 → Console
Suche nach: verkauf, auftragseingang
```

### **5. Permission-Problem**
```bash
ls -la data/greiner_controlling.db
# Sollte: ag-admin ag-admin sein
```

---

## 📁 WICHTIGE DATEIEN
```
/opt/greiner-portal/
├── api/verkauf_api.py              ← API-Endpoints
├── routes/verkauf_routes.py        ← Frontend-Routes
├── templates/
│   ├── verkauf_auftragseingang.html
│   ├── verkauf_auftragseingang_detail.html
│   └── verkauf_auslieferung_detail.html
├── static/js/
│   └── verkauf_*.js                ← JavaScript (lädt Daten)
├── logs/
│   └── sync_sales.log              ← Sync-Log
└── data/
    └── greiner_controlling.db      ← Datenbank
```

---

## 🩺 DIAGNOSE-CHECKLISTE
```bash
# 1. Service läuft?
sudo systemctl is-active greiner-portal
# → Sollte: active

# 2. Port 80 erreichbar?
curl -I http://10.80.80.20/
# → Sollte: HTTP/1.1 200 OK

# 3. API antwortet?
curl http://10.80.80.20/api/verkauf/auftragseingang
# → Sollte: JSON zurückgeben

# 4. Daten vorhanden?
sqlite3 data/greiner_controlling.db "SELECT COUNT(*) FROM sales;"
# → Sollte: 4846

# 5. JavaScript lädt?
curl http://10.80.80.20/static/js/verkauf_auftragseingang.js
# → Sollte: JavaScript-Code

# 6. Logs zeigen Fehler?
sudo journalctl -u greiner-portal -n 50 | grep -i error
# → Sollte: keine kritischen Fehler
```

---

## 🔨 QUICK-FIXES

### **Fix 1: Service neu starten**
```bash
sudo systemctl restart greiner-portal
sleep 3
sudo systemctl status greiner-portal
```

### **Fix 2: Browser-Cache leeren**
```
Strg + Shift + R (Hard Reload)
oder
F12 → Network Tab → "Disable cache" aktivieren
```

### **Fix 3: Permissions prüfen**
```bash
cd /opt/greiner-portal
sudo chown -R ag-admin:ag-admin data/
sudo chmod 664 data/greiner_controlling.db
```

### **Fix 4: API manuell testen**
```bash
cd /opt/greiner-portal
source venv/bin/activate

python3 -c "
from api.verkauf_api import verkauf_api
print('API Blueprint:', verkauf_api)
"
```

---

## 📝 FÜR CLAUDE IN NEUER SESSION

**Kontext laden:**
```
"Lies bitte:
- docs/sessions/SESSION_WRAP_UP_TAG22.md (Was gestern passiert ist)
- docs/QUICK_START_TAG23.md (Aktuelles Problem)

Das Verkaufs-Dashboard lädt nicht. Ich habe:
- Browser Console Errors
- Backend Logs
- Network Tab Screenshots

Portal läuft auf http://10.80.80.20/verkauf/auftragseingang
```

---

## 🎯 ERWARTETES VERHALTEN

**Sollte zeigen:**

1. **Auftragseingang Heute:**
   - Tabelle mit Verkäufern
   - NW/GW/Gesamt Spalten
   - Summen-Zeile

2. **Kumulierter Auftragseingang:**
   - Gleiche Struktur
   - Jahres-Summen

3. **Filter:**
   - Monat-Auswahl
   - Jahr-Auswahl
   - "Anzeigen" Button

---

## 📚 RELEVANTE DOKUMENTATION
```
docs/sessions/SESSION_WRAP_UP_TAG22.md  ← Gestern
docs/sessions/SESSION_WRAP_UP_TAG16.md  ← Verkauf erstellt
docs/INDEX.md                            ← Übersicht
```

---

## 🔗 NÜTZLICHE LINKS

- **Dashboard:** http://10.80.80.20/
- **Bankenspiegel:** http://10.80.80.20/bankenspiegel/dashboard
- **Verkauf:** http://10.80.80.20/verkauf/auftragseingang
- **Login:** http://10.80.80.20/login

---

## 💡 TIPPS

1. **Immer zuerst Browser Console checken!**
2. **Network Tab zeigt welche API-Calls fehlschlagen**
3. **Backend Logs zeigen Python-Fehler**
4. **Bei Zweifeln: Service neu starten**
5. **Browser-Cache kann alte JS-Dateien cachen**

---

**Version:** 1.0  
**Für:** Tag 23  
**Problem:** Verkaufs-Dashboard Lade-Fehler  
**Status:** Debugging needed

**VIEL ERFOLG! 🔧**
