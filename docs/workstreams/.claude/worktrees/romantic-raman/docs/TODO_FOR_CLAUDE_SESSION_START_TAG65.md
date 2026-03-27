# 📋 TODO FÜR CLAUDE SESSION START - TAG 65

**Datum:** 2025-11-20 (erwartet)  
**Fokus:** EINKAUFSFINANZIERUNG + FRONTEND-CHECK + CRON-JOBS

---

## ⚠️ KRITISCH - ZUERST AUSFÜHREN!

### 🔍 **SERVER-STATUS-CHECK:**
```bash
cd /opt/greiner-portal
bash scripts/maintenance/server_status_check.sh
```

**→ Ausgabe in Chat kopieren!**

**Prüft:**
- Disk Space
- Laufende Prozesse
- Cron-Jobs
- Log-Größen
- DB-Status

---

## 🎯 HAUPTZIELE TAG 65

### 1️⃣ **EINKAUFSFINANZIERUNG-BESTÄNDE IN DB HOLEN**

**Datenquellen:**
- ✅ **Stellantis:** ZIP mit Excel (PW-geschützt)
  - Passwort: in `config/credentials.json`
  - Bereits am Server vorhanden
  - Import-Routine existiert (funktionierte in alter DB)

- ✅ **Santander:** CSV-Dateien
  - Bereits am Server vorhanden
  - Import-Routine existiert

- ✅ **Hyundai:** CSV-Dateien
  - Bereits am Server vorhanden
  - Import-Routine existiert

**Aufgaben:**
1. Scripts auf Server finden
2. Testen ob sie noch funktionieren
3. An neues DB-Schema anpassen (falls nötig)
4. Importieren

---

### 2️⃣ **CRON-JOBS PRÜFEN**

⚠️ **WICHTIG:** Alter Import läuft evtl. noch!
```bash
# Cron-Jobs anzeigen:
crontab -l

# System-Crons prüfen:
sudo ls -la /etc/cron.d/
sudo ls -la /etc/cron.daily/
```

**Zu prüfen:**
- Laufen alte Import-Scripts noch?
- Kollidieren sie mit neuen Imports?
- Müssen sie deaktiviert werden?

---

### 3️⃣ **FRONTEND-CHECK**

**Problem:** Frontend funktioniert nicht mehr!

**Mögliche Ursachen:**
- API-Endpoints geändert?
- Routes fehlen?
- Templates nicht angepasst?
- JavaScript-Fehler?

**Checks:**
```bash
# Flask-Status:
systemctl status greiner-portal

# Logs:
journalctl -u greiner-portal -n 100

# API testen:
curl -I http://localhost:5000/
curl http://localhost:5000/api/bankenspiegel/dashboard
```

**Browser-Test:**
```
http://10.80.80.20:5000
```

**Fehler in Browser-Konsole prüfen!** (F12)

---

## 📁 WICHTIGE PFADE

### Einkaufsfinanzierung-Scripts:
```bash
# Suche nach Import-Scripts:
find /opt/greiner-portal/scripts -name "*stellantis*" -o -name "*santander*" -o -name "*hyundai*"

# Alte Imports prüfen:
ls -lh /opt/greiner-portal/scripts/imports/
```

### Datenquellen:
```bash
# Stellantis:
find /mnt/buchhaltung -name "*stellantis*" -type f
find /mnt/buchhaltung -name "*.zip" -type f

# Santander:
find /mnt/buchhaltung -name "*santander*" -type f

# Hyundai:
find /mnt/buchhaltung -name "*hyundai*" -type f
```

---

## 🎯 GROSSES ZIEL

**Siehe:** `KONSOLIDIERTES_72H_WRAP_UP_TAG37-49.md` im Project Knowledge

**Ziel:** Komplettes Finanz-Controlling mit:
- ✅ Bankkonten (FERTIG!)
- 🔄 Einkaufsfinanzierung (TODO!)
- 🔄 Zinsverfolgung (TODO!)
- 🔄 Fahrzeug-Tracking (TODO!)
- 🔄 Dashboard-Visualisierung (TODO!)

---

## 📋 SCHRITT-FÜR-SCHRITT TAG 65

### **Phase 1: Server-Check** (15 Min)
```bash
1. server_status_check.sh ausführen
2. Cron-Jobs prüfen
3. Disk-Space prüfen
4. Log-Dateien prüfen
```

### **Phase 2: Einkaufsfinanzierung lokalisieren** (30 Min)
```bash
1. Stellantis-Daten finden
2. Santander-Daten finden
3. Hyundai-Daten finden
4. Import-Scripts finden
5. Credentials prüfen
```

### **Phase 3: Import-Scripts testen** (1 Std)
```bash
1. Stellantis-Import Dry-Run
2. Santander-Import Dry-Run
3. Hyundai-Import Dry-Run
4. DB-Schema prüfen (Tabellen vorhanden?)
5. Scripts anpassen falls nötig
```

### **Phase 4: Echter Import** (1 Std)
```bash
1. Stellantis importieren
2. Santander importieren
3. Hyundai importieren
4. Validierung
```

### **Phase 5: Frontend-Check** (1 Std)
```bash
1. Dashboard aufrufen
2. API-Endpoints testen
3. JavaScript-Konsole prüfen
4. Fehler beheben
```

---

## 🔍 DIAGNOSE-BEFEHLE

### Server-Status:
```bash
df -h                                    # Disk-Space
systemctl status greiner-portal          # Flask-Status
journalctl -u greiner-portal -n 50       # Logs
ps aux | grep python                     # Laufende Python-Prozesse
```

### Cron-Jobs:
```bash
crontab -l                               # User-Crons
sudo crontab -l                          # Root-Crons
sudo ls -la /etc/cron.d/                # System-Crons
```

### Datenbank:
```bash
cd /opt/greiner-portal
sqlite3 data/greiner_controlling.db ".tables"
sqlite3 data/greiner_controlling.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%finanz%';"
```

### Einkaufsfinanzierung-Tabellen:
```bash
sqlite3 data/greiner_controlling.db << 'EOF'
.tables
SELECT name FROM sqlite_master 
WHERE type='table' 
AND (name LIKE '%finanz%' OR name LIKE '%fahrzeug%' OR name LIKE '%stellantis%');
EOF
```

---

## ⚠️ WICHTIGE HINWEISE FÜR CLAUDE

1. **IMMER erst `server_status_check.sh` ausführen!**
2. **Cron-Jobs können Konflikte verursachen!**
3. **Alte Import-Scripts könnten noch laufen!**
4. **DB-Schema könnte sich geändert haben!**
5. **Credentials in `config/credentials.json` prüfen!**

---

## 📚 RELEVANTE DOKUMENTATION

**Im Project Knowledge:**
- `KONSOLIDIERTES_72H_WRAP_UP_TAG37-49.md` → Großes Ziel
- `LOCOSOFT_POSTGRESQL_DOKUMENTATION.md` → FIBU-Buchungen
- `DATABASE_SCHEMA.md` → DB-Struktur
- `API_INTEGRATION.md` → API-Endpunkte

**Session Wrap-Ups:**
- `SESSION_WRAP_UP_TAG50_MEGA.md` → Einkaufsfinanzierung
- `SESSION_WRAP_UP_TAG64.md` → Diese Session

---

## ✅ ERFOLGSKRITERIEN TAG 65

**Must-Have:**
- [ ] Server-Status geprüft
- [ ] Cron-Jobs identifiziert
- [ ] Einkaufsfinanzierung-Daten gefunden
- [ ] Import-Scripts lokalisiert

**Should-Have:**
- [ ] Stellantis importiert
- [ ] Santander importiert
- [ ] Hyundai importiert
- [ ] Frontend funktioniert

**Nice-to-Have:**
- [ ] Dashboard zeigt Einkaufsfinanzierung an
- [ ] Täglicher Import eingerichtet
- [ ] Dokumentation aktualisiert

