# BANKENSPIEGEL FRONTEND - UPLOAD & INTEGRATION ANLEITUNG

**Datum:** 2025-11-07  
**Status:** Alle Dateien erstellt ✅  
**Nächster Schritt:** Upload zum Server & Flask-Integration

---

## 📦 ERSTELLTE DATEIEN

### Templates (HTML):
```
✅ bankenspiegel_dashboard.html      (Hauptdashboard mit KPIs + Charts)
✅ bankenspiegel_konten.html         (Kontenübersicht)
✅ bankenspiegel_transaktionen.html  (Transaktionsliste mit Filtern)
```

### JavaScript:
```
✅ bankenspiegel_dashboard.js        (Chart.js Integration)
✅ bankenspiegel_konten.js           (Konten-Filter)
✅ bankenspiegel_transaktionen.js    (Filter + Pagination)
```

### CSS:
```
✅ bankenspiegel.css                 (Custom Styling)
```

---

## 🚀 UPLOAD ZUM SERVER

### Option 1: SCP Upload (empfohlen)

```bash
# Von deinem lokalen Rechner (Downloads-Ordner)

# Templates hochladen
scp bankenspiegel_dashboard.html ag-admin@10.80.80.20:/opt/greiner-portal/templates/
scp bankenspiegel_konten.html ag-admin@10.80.80.20:/opt/greiner-portal/templates/
scp bankenspiegel_transaktionen.html ag-admin@10.80.80.20:/opt/greiner-portal/templates/

# JavaScript hochladen
scp bankenspiegel_dashboard.js ag-admin@10.80.80.20:/opt/greiner-portal/static/js/
scp bankenspiegel_konten.js ag-admin@10.80.80.20:/opt/greiner-portal/static/js/
scp bankenspiegel_transaktionen.js ag-admin@10.80.80.20:/opt/greiner-portal/static/js/

# CSS hochladen
scp bankenspiegel.css ag-admin@10.80.80.20:/opt/greiner-portal/static/css/
```

**Password:** `OHL.greiner2025`

---

### Option 2: WinSCP (Windows)

1. **Server verbinden:**
   - Host: `10.80.80.20`
   - Username: `ag-admin`
   - Password: `OHL.greiner2025`

2. **Dateien hochladen:**
   - Templates → `/opt/greiner-portal/templates/`
   - JavaScript → `/opt/greiner-portal/static/js/`
   - CSS → `/opt/greiner-portal/static/css/`

---

### Option 3: SSH + Vi/Nano (manuell)

```bash
# SSH verbinden
ssh ag-admin@10.80.80.20

# Zu Templates-Verzeichnis wechseln
cd /opt/greiner-portal/templates/

# Dateien erstellen und Inhalt einfügen
nano bankenspiegel_dashboard.html
# (Inhalt einfügen und mit Ctrl+X, Y, Enter speichern)

# Wiederholen für alle anderen Dateien...
```

---

## ⚙️ FLASK ROUTES REGISTRIEREN

Nach dem Upload müssen die Routes in Flask registriert werden.

### Schritt 1: SSH zum Server

```bash
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal
```

### Schritt 2: Routes-Datei erstellen

```bash
nano routes/bankenspiegel_routes.py
```

**Inhalt:**

```python
from flask import Blueprint, render_template

bankenspiegel_bp = Blueprint('bankenspiegel', __name__, url_prefix='/bankenspiegel')

@bankenspiegel_bp.route('/dashboard')
def dashboard():
    """Bankenspiegel Dashboard"""
    return render_template('bankenspiegel_dashboard.html')

@bankenspiegel_bp.route('/konten')
def konten():
    """Kontenübersicht"""
    return render_template('bankenspiegel_konten.html')

@bankenspiegel_bp.route('/transaktionen')
def transaktionen():
    """Transaktionsliste"""
    return render_template('bankenspiegel_transaktionen.html')
```

### Schritt 3: Blueprint in app.py registrieren

```bash
nano app.py
```

**Zeilen hinzufügen:**

```python
# Nach den anderen Blueprint-Imports
from routes.bankenspiegel_routes import bankenspiegel_bp

# Nach den anderen Blueprint-Registrierungen
app.register_blueprint(bankenspiegel_bp)
```

### Schritt 4: Flask neustarten

```bash
# Flask-Prozess finden
ps aux | grep "python.*app.py"

# Flask-Prozess beenden (PID ersetzen)
kill <PID>

# Neu starten
source venv/bin/activate
nohup python app.py > logs/flask.log 2>&1 &
```

**ODER mit Systemd (falls eingerichtet):**

```bash
sudo systemctl restart greiner-portal
```

---

## ✅ TESTEN

### 1. API-Endpoints prüfen

```bash
# Health Check
curl http://localhost:5000/api/bankenspiegel/health

# Dashboard-Daten
curl http://localhost:5000/api/bankenspiegel/dashboard
```

**Erwartete Response:**
```json
{
  "anzahl_banken": 14,
  "anzahl_konten_aktiv": 15,
  "anzahl_konten_gesamt": 24,
  "gesamtsaldo": 49948.0,
  "letzte_30_tage": {
    "anzahl_transaktionen": 1660,
    "einnahmen": 5361166.43,
    "ausgaben": 5075236.57,
    "saldo": 285929.86
  },
  "interne_transfers_30_tage": {
    "anzahl_transaktionen": 343,
    "volumen": 3909488.39
  }
}
```

### 2. Frontend-Seiten aufrufen

Im Browser:
- Dashboard: `http://10.80.80.20:5000/bankenspiegel/dashboard`
- Konten: `http://10.80.80.20:5000/bankenspiegel/konten`
- Transaktionen: `http://10.80.80.20:5000/bankenspiegel/transaktionen`

---

## 🎨 WICHTIG: BASE.HTML VORAUSSETZUNG

Die Templates erweitern `base.html`. Diese Datei muss existieren mit:

### Mindest-Anforderungen für base.html:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Greiner Portal{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/bankenspiegel.css') }}" rel="stylesheet">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation (optional) -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">Greiner Portal</a>
            <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link" href="/bankenspiegel/dashboard">Bankenspiegel</a>
                </li>
            </ul>
        </div>
    </nav>
    
    <!-- Content -->
    {% block content %}{% endblock %}
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom Scripts -->
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Falls base.html nicht existiert:** Templates funktionieren NICHT!

---

## 🔧 TROUBLESHOOTING

### Problem 1: "Template not found"
```bash
# Prüfen ob Dateien existieren
ls -la /opt/greiner-portal/templates/bankenspiegel_*

# Permissions prüfen
chmod 644 /opt/greiner-portal/templates/bankenspiegel_*
```

### Problem 2: "404 Not Found"
```bash
# Routes prüfen
grep -r "bankenspiegel" /opt/greiner-portal/routes/
grep -r "register_blueprint.*bankenspiegel" /opt/greiner-portal/app.py
```

### Problem 3: JavaScript lädt nicht
```bash
# Static-Dateien prüfen
ls -la /opt/greiner-portal/static/js/bankenspiegel_*
ls -la /opt/greiner-portal/static/css/bankenspiegel.css

# Permissions prüfen
chmod 644 /opt/greiner-portal/static/js/bankenspiegel_*
chmod 644 /opt/greiner-portal/static/css/bankenspiegel.css
```

### Problem 4: API gibt keine Daten zurück
```bash
# API direkt testen
curl http://localhost:5000/api/bankenspiegel/dashboard | jq

# Flask-Logs prüfen
tail -f /opt/greiner-portal/logs/flask.log
```

---

## 📊 FEATURES IM ÜBERBLICK

### Dashboard:
✅ KPI-Kacheln (Gesamtsaldo, Banken, Konten, Transaktionen)
✅ Monatliche Umsätze (Chart.js Bar-Chart)
✅ Einnahmen/Ausgaben/Saldo (30 Tage)
✅ Interne Transfers (Info-Box mit Hinweis)
✅ Letzte 10 Transaktionen (Tabelle)
✅ Auto-Refresh (alle 5 Minuten)

### Konten:
✅ Alle Konten in Tabelle
✅ Filter nach Bank
✅ Filter nach Status (aktiv/inaktiv)
✅ Suche (IBAN, Kontoname)
✅ Farbkodierung (Saldo positiv/negativ)
✅ Link zu Transaktionen pro Konto

### Transaktionen:
✅ Filterbare Tabelle (Datum, Konto, Typ)
✅ Suche in Verwendungszweck
✅ Statistik (Einnahmen/Ausgaben/Saldo gefiltert)
✅ Pagination (50 Einträge pro Seite)
✅ Datum-Range-Picker
✅ URL-Parameter Support (konto_id)

---

## 🎯 NÄCHSTE SCHRITTE (OPTIONAL)

Nach erfolgreichem Upload und Test:

### Phase 3 (Erweiterte Features):
1. **Kategorien-Zuweisung**
   - UI zum Zuweisen von Kategorien
   - Bulk-Update-Funktion
   - Regelbasierte Auto-Kategorisierung

2. **Export-Funktionen**
   - Excel-Export (gefilterte Transaktionen)
   - CSV-Export
   - PDF-Report (monatliche Übersicht)

3. **Duplikat-Prevention**
   - UNIQUE Constraint auf Transaktionen
   - Import-Validierung
   - Warnung bei möglichen Duplikaten

4. **Dashboard-Erweiterungen**
   - Monats-Vergleich (Charts)
   - Top-Kategorien (Pie-Chart)
   - Saldo-Entwicklung (Liniendiagramm)

---

## 📝 ZUSAMMENFASSUNG

**Erstellt:**
- 3 Templates (HTML)
- 3 JavaScript-Dateien
- 1 CSS-Datei

**Upload:**
- SCP / WinSCP / SSH+Nano

**Integration:**
- Routes-Datei erstellen
- Blueprint registrieren
- Flask neustarten

**Testen:**
- API-Endpoints prüfen
- Frontend-Seiten aufrufen

---

**Status:** ✅ FRONTEND KOMPLETT  
**Bereit für:** Upload & Test  
**Rollback möglich:** Ja, einfach Dateien löschen

---

**Viel Erfolg beim Upload! 🚀**
