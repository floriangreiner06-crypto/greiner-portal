# 🚀 INSTALLATION: EINKAUFSFINANZIERUNG FRONTEND

**Datum:** 08.11.2025  
**Version:** 1.0  
**Status:** Komplett neu entwickelt (kein Prototyp-Code)

---

## 📦 DATEIEN ÜBERSICHT

```
/opt/greiner-portal/
├── api/
│   └── bankenspiegel_api.py                    📝 ERWEITERN
├── routes/
│   └── bankenspiegel_routes.py                 📝 ERWEITERN
├── templates/
│   ├── base.html                               📝 ERWEITERN (Menü)
│   └── einkaufsfinanzierung.html               ✨ NEU
├── static/
│   ├── js/
│   │   └── einkaufsfinanzierung.js             ✨ NEU
│   └── css/
│       └── einkaufsfinanzierung.css            ✨ NEU
```

---

## 🔧 INSTALLATION SCHRITT-FÜR-SCHRITT

### SCHRITT 1: API-Endpoint hinzufügen

**Datei:** `/opt/greiner-portal/api/bankenspiegel_api.py`

**Aktion:** Am **ENDE der Datei** (vor `if __name__ == '__main__':`) einfügen:

```bash
cd /opt/greiner-portal/api

# Backup erstellen
cp bankenspiegel_api.py bankenspiegel_api.py.backup_before_einkaufsfinanzierung

# Inhalt von bankenspiegel_api_einkaufsfinanzierung.py ans Ende kopieren
# (Upload die Datei und füge den Inhalt manuell ein)
```

**Code zum Einfügen:** `bankenspiegel_api_einkaufsfinanzierung.py`

---

### SCHRITT 2: Route hinzufügen

**Datei:** `/opt/greiner-portal/routes/bankenspiegel_routes.py`

**Aktion:** Am **ENDE der Datei** einfügen:

```bash
cd /opt/greiner-portal/routes

# Backup erstellen
cp bankenspiegel_routes.py bankenspiegel_routes.py.backup

# Code einfügen
```

**Code zum Einfügen:** `bankenspiegel_routes_einkaufsfinanzierung.py`

---

### SCHRITT 3: Neue Dateien hochladen

```bash
cd /opt/greiner-portal

# Templates
cp einkaufsfinanzierung.html templates/

# JavaScript
cp einkaufsfinanzierung.js static/js/

# CSS
cp einkaufsfinanzierung.css static/css/

# Permissions setzen
chmod 644 templates/einkaufsfinanzierung.html
chmod 644 static/js/einkaufsfinanzierung.js
chmod 644 static/css/einkaufsfinanzierung.css
```

---

### SCHRITT 4: Menü-Link hinzufügen

**Datei:** `/opt/greiner-portal/templates/base.html`

**Aktion:** Im Bankenspiegel-Submenu einfügen (suche nach "Bankenspiegel Dashboard"):

```html
<!-- SUCHE NACH dieser Zeile: -->
<a class="nav-link" href="{{ url_for('bankenspiegel_routes.dashboard') }}">
    <i class="bi bi-speedometer2 me-2"></i>
    Bankenspiegel Dashboard
</a>

<!-- FÜGE DANACH EIN: -->
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('bankenspiegel_routes.einkaufsfinanzierung') }}">
        <i class="bi bi-car-front-fill me-2"></i>
        Einkaufsfinanzierung
    </a>
</li>
```

---

### SCHRITT 5: Flask neu starten

```bash
# Aktuellen Flask-Prozess finden
ps aux | grep "python.*app.py"

# Prozess beenden (PID ersetzen!)
kill 34726

# Neu starten
cd /opt/greiner-portal
source venv/bin/activate
nohup python app.py > logs/app.log 2>&1 &

# Prüfen
ps aux | grep "python.*app.py"
tail -f logs/app.log
```

---

## 🧪 TESTEN

### 1. API-Endpoint testen

```bash
curl http://localhost:5000/api/bankenspiegel/einkaufsfinanzierung | jq
```

**Erwartetes Ergebnis:**
```json
{
  "success": true,
  "gesamt": {
    "anzahl_fahrzeuge": 145,
    "finanzierung": 3800559.60,
    ...
  },
  "institute": [...],
  "top_fahrzeuge": [...],
  "warnungen": [...]
}
```

### 2. Frontend öffnen

**Browser:** http://10.80.80.20:5000/bankenspiegel/einkaufsfinanzierung

**Erwartetes Ergebnis:**
- ✅ 4 KPI-Karten oben
- ✅ 2 Institut-Cards (Stellantis + Santander)
- ✅ 2 Charts (Pie + Bar)
- ✅ Tabelle mit Top 10 Fahrzeugen
- ✅ Warnungen (falls vorhanden)

---

## ⚠️ TROUBLESHOOTING

### Problem: API-Endpoint nicht erreichbar

**Lösung:**
```bash
# Prüfe ob Endpoint registriert ist
grep -n "einkaufsfinanzierung" api/bankenspiegel_api.py

# Prüfe Flask-Logs
tail -50 logs/app.log
```

### Problem: "Template not found"

**Lösung:**
```bash
# Prüfe ob Template existiert
ls -la templates/einkaufsfinanzierung.html

# Prüfe Permissions
chmod 644 templates/einkaufsfinanzierung.html
```

### Problem: Charts werden nicht angezeigt

**Lösung:**
```bash
# Prüfe Chart.js im Browser:
# Öffne Developer Tools (F12)
# Console: Schaue nach Fehlern
# Network: Prüfe ob Chart.js geladen wurde
```

### Problem: "ModuleNotFoundError: No module named 'datetime'"

**Lösung:**
```python
# In bankenspiegel_api.py am Anfang prüfen:
from datetime import datetime

# Falls fehlt, hinzufügen!
```

---

## 📊 FEATURES ÜBERSICHT

### KPI-Karten:
- ✅ Gesamt Fahrzeuge (145)
- ✅ Finanzierungssaldo (3,8M EUR)
- ✅ Abbezahlt (mit Progress Bar)
- ✅ Zinsfreiheit-Warnungen

### Institut-Cards:
- ✅ Stellantis (104 Fzg., 2,97M EUR)
- ✅ Santander (41 Fzg., 0,82M EUR)
- ✅ Marken-Badges
- ✅ Durchschnitt & Alter

### Visualisierungen:
- ✅ Pie-Chart: Verteilung Stellantis vs Santander
- ✅ Bar-Chart: Marken-Verteilung

### Tabellen:
- ✅ Top 10 teuerste Fahrzeuge
- ✅ Zinsfreiheit-Warnungen (< 30 Tage)

### Interaktiv:
- ✅ Refresh-Button
- ✅ Responsive Design
- ✅ Hover-Effekte
- ✅ Smooth Animations

---

## 🎨 DESIGN-EIGENSCHAFTEN

- **Framework:** Bootstrap 5
- **Icons:** Bootstrap Icons
- **Charts:** Chart.js 4.4.0
- **Colors:** 
  - Stellantis: Lila (#9C27B0)
  - Santander: Blau (#03A9F4)
- **Responsive:** Mobile-optimiert
- **Modern:** Shadows, Transitions, Hover-Effects

---

## 🚀 NÄCHSTE SCHRITTE (Optional)

### Erweiterungen:
- [ ] Export-Funktion (Excel/PDF)
- [ ] Filter nach Bank/Marke
- [ ] Historische Entwicklung (Chart)
- [ ] Detail-Ansicht pro Fahrzeug
- [ ] Push-Benachrichtigungen bei Warnungen

### Integration:
- [ ] Link zu LocoSoft (VIN-Suche)
- [ ] Automatischer Abgleich mit Verkäufen
- [ ] Email-Benachrichtigung bei Zinsfreiheit

---

## 📝 DATEIEN-CHECKLISTE

Vor dem Hochladen prüfen:

- [ ] `einkaufsfinanzierung.html` (15 KB)
- [ ] `einkaufsfinanzierung.js` (12 KB)
- [ ] `einkaufsfinanzierung.css` (4 KB)
- [ ] API-Code für `bankenspiegel_api.py`
- [ ] Route-Code für `bankenspiegel_routes.py`
- [ ] Menü-Link für `base.html`

---

## 🎊 FERTIG!

Nach erfolgreicher Installation hast du ein **professionelles Einkaufsfinanzierung-Dashboard** mit:

- ✅ Live-Daten von Stellantis & Santander
- ✅ Moderne Visualisierungen
- ✅ Responsive Design
- ✅ Produktionsreif

**Viel Erfolg beim Deployment!** 🚀

---

*Erstellt am 08.11.2025 - Frontend V1.0*  
*Greiner Portal - Einkaufsfinanzierung Dashboard*
