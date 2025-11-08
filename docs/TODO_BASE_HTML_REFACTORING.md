# TODO: BASE.HTML REFACTORING

**Priorität:** 🔴 HOCH  
**Status:** 📋 TODO  
**Blockiert:** Einkaufsfinanzierung Frontend  
**Aufwand:** 1-2 Stunden  
**Erstellt:** 08.11.2025

---

## 🎯 ZIEL

**Moderne, konsistente `base.html` nach Urlaubsplaner-V2-Standard**

Alle Seiten sollen:
- ✅ Einheitliches Layout
- ✅ Moderne Flask-Patterns (url_for)
- ✅ Vollständiges Block-System
- ✅ Konsistente Blueprint-Namen
- ✅ Wartbar und erweiterbar

---

## ❌ AKTUELLE PROBLEME

### 1. Fehlende Template-Blocks

```html
<!-- base.html (AKTUELL - PROTOTYP) -->
<!DOCTYPE html>
<html>
<head>
    <title>Greiner Portal</title>
    <!-- CSS -->
</head>
<body>
    <!-- Navigation -->
    <!-- Content -->
    
    <!-- ❌ {% block extra_js %} FEHLT! -->
    <!-- ❌ {% block extra_css %} FEHLT! -->
    <!-- ❌ {% block title %} FEHLT! -->
</body>
</html>
```

**Folge:**
- Einkaufsfinanzierung kann Chart.js nicht laden
- Keine seitenspezifischen Scripts
- Keine seitenspezifischen Styles

---

### 2. Hardcoded URLs

```html
<!-- AKTUELL (FALSCH) -->
<a href="/bankenspiegel/dashboard">Dashboard</a>
<a href="/urlaubsplaner/antrag">Urlaubsantrag</a>

<!-- SOLLTE SEIN -->
<a href="{{ url_for('bankenspiegel.dashboard') }}">Dashboard</a>
<a href="{{ url_for('urlaubsplaner.antrag') }}">Urlaubsantrag</a>
```

**Probleme:**
- Fehleranfällig (Tippfehler)
- Schwer wartbar
- Keine Auto-Completion
- Nicht Flask Best Practice

---

### 3. Inkonsistente Blueprint-Namen

```python
# routes/bankenspiegel_routes.py
bankenspiegel_bp = Blueprint('bankenspiegel', __name__)  # 'bankenspiegel'

# routes/urlaubsplaner_routes.py (V2)
urlaubsplaner_bp = Blueprint('urlaubsplaner_v2', __name__)  # 'urlaubsplaner_v2'?

# Inkonsistent!
```

---

### 4. Kein einheitlicher Standard

- Urlaubsplaner V2: Modern ✅
- Bankenspiegel: Prototyp ❌
- Andere Seiten: ???

---

## ✅ LÖSUNG: NEUE BASE.HTML

### Vorlage: Urlaubsplaner V2

**Datei:** `/opt/greiner-portal/templates/urlaubsplaner_v2.html`

**Warum?**
- ✅ Modern entwickelt
- ✅ Funktioniert perfekt
- ✅ Saubere Struktur
- ✅ Best Practices

**Analysieren:**
```bash
head -50 /opt/greiner-portal/templates/urlaubsplaner_v2.html
```

---

### Neue base.html Struktur

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Dynamischer Titel -->
    <title>{% block title %}Greiner Portal{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
    
    <!-- Seitenspezifisches CSS -->
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <img src="{{ url_for('static', filename='images/greiner-logo.png') }}" alt="Greiner" height="30">
            </a>
            
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav">
                    
                    <!-- Bankenspiegel -->
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                            💰 Bankenspiegel
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a class="dropdown-item" href="{{ url_for('bankenspiegel.dashboard') }}">
                                    <i class="bi bi-speedometer2 me-2"></i>Dashboard
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item" href="{{ url_for('bankenspiegel.konten') }}">
                                    <i class="bi bi-credit-card me-2"></i>Konten
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item" href="{{ url_for('bankenspiegel.transaktionen') }}">
                                    <i class="bi bi-arrow-left-right me-2"></i>Transaktionen
                                </a>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <a class="dropdown-item" href="{{ url_for('bankenspiegel.einkaufsfinanzierung') }}">
                                    <i class="bi bi-car-front-fill me-2"></i>Einkaufsfinanzierung
                                </a>
                            </li>
                        </ul>
                    </li>
                    
                    <!-- Urlaubsplaner -->
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                            👥 Mitarbeiter
                        </a>
                        <ul class="dropdown-menu">
                            <li>
                                <a class="dropdown-item" href="{{ url_for('urlaubsplaner.overview') }}">
                                    <i class="bi bi-calendar-check me-2"></i>Urlaubsplaner
                                </a>
                            </li>
                            <!-- Weitere... -->
                        </ul>
                    </li>
                    
                    <!-- Weitere Menü-Punkte... -->
                    
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="container-fluid py-4">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-light text-center py-3 mt-5">
        <p class="text-muted mb-0">© 2025 Greiner Portal</p>
    </footer>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Seitenspezifisches JavaScript -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

## 📋 AUFGABEN-LISTE

### Phase 1: Vorbereitung

- [ ] **Urlaubsplaner V2 analysieren**
  ```bash
  cat /opt/greiner-portal/templates/urlaubsplaner_v2.html
  ```

- [ ] **Alle Blueprint-Namen erfassen**
  ```bash
  grep -r "Blueprint(" /opt/greiner-portal/routes/
  ```

- [ ] **Alle verwendeten URLs erfassen**
  ```bash
  grep -r "href=\"/" /opt/greiner-portal/templates/base.html
  ```

- [ ] **Backup erstellen**
  ```bash
  cp /opt/greiner-portal/templates/base.html \
     /opt/greiner-portal/templates/base.html.backup_before_refactoring
  ```

---

### Phase 2: Neue base.html erstellen

- [ ] **Grundstruktur schreiben**
  - HTML5 Doctype
  - Meta-Tags
  - Bootstrap 5 einbinden
  - Bootstrap Icons einbinden

- [ ] **Block-System implementieren**
  - `{% block title %}`
  - `{% block extra_css %}`
  - `{% block content %}`
  - `{% block extra_js %}`

- [ ] **Navigation modernisieren**
  - Bootstrap 5 Navbar
  - Dropdown-Menüs
  - Alle Links auf `url_for()` umstellen

- [ ] **Footer hinzufügen**
  - Copyright
  - Version
  - ggf. Links

---

### Phase 3: Blueprint-Namen vereinheitlichen

- [ ] **Konsistente Benennung festlegen**
  ```python
  # Standard-Format:
  modulname_bp = Blueprint('modulname', __name__)
  
  # Beispiele:
  bankenspiegel_bp = Blueprint('bankenspiegel', __name__)
  urlaubsplaner_bp = Blueprint('urlaubsplaner', __name__)
  verkauf_bp = Blueprint('verkauf', __name__)
  ```

- [ ] **Alle Routes prüfen & anpassen**
  ```bash
  # In allen route-Dateien:
  /opt/greiner-portal/routes/*.py
  ```

- [ ] **app.py prüfen & anpassen**
  ```python
  # Blueprint-Registrierung
  app.register_blueprint(bankenspiegel_bp, url_prefix='/bankenspiegel')
  app.register_blueprint(urlaubsplaner_bp, url_prefix='/urlaubsplaner')
  ```

---

### Phase 4: Alle Templates anpassen

- [ ] **Einkaufsfinanzierung** (bereits fertig!)
  ```html
  {% extends "base.html" %}
  {% block title %}Einkaufsfinanzierung{% endblock %}
  {% block extra_css %}...{% endblock %}
  {% block content %}...{% endblock %}
  {% block extra_js %}...{% endblock %}
  ```

- [ ] **Bankenspiegel Dashboard**
- [ ] **Bankenspiegel Konten**
- [ ] **Bankenspiegel Transaktionen**
- [ ] **Urlaubsplaner** (sollte schon passen)
- [ ] **Alle anderen Seiten**

---

### Phase 5: Testen

- [ ] **Jede Seite einzeln testen**
  - Lädt die Seite?
  - CSS geladen?
  - JavaScript geladen?
  - Navigation funktioniert?
  - Links funktionieren?

- [ ] **Browser-Console prüfen**
  - Keine Fehler?
  - Keine 404?
  - Keine fehlenden Ressourcen?

- [ ] **Responsive testen**
  - Desktop (1920px)
  - Tablet (768px)
  - Mobile (375px)

---

### Phase 6: Einkaufsfinanzierung aktivieren

- [ ] **Flask neu starten**
  ```bash
  pkill -f "python.*app.py"
  cd /opt/greiner-portal
  source venv/bin/activate
  nohup python app.py > logs/app.log 2>&1 &
  ```

- [ ] **Einkaufsfinanzierung öffnen**
  ```
  http://10.80.80.20:5000/bankenspiegel/einkaufsfinanzierung
  ```

- [ ] **Prüfen:**
  - ✅ KPI-Cards sichtbar?
  - ✅ Institut-Cards sichtbar?
  - ✅ Charts sichtbar?
  - ✅ Tabellen sichtbar?
  - ✅ Keine Console-Fehler?

---

## 🧪 TEST-CHECKLISTE

Nach dem Refactoring **ALLE** Seiten testen:

### Bankenspiegel:
- [ ] `/bankenspiegel/dashboard`
- [ ] `/bankenspiegel/konten`
- [ ] `/bankenspiegel/transaktionen`
- [ ] `/bankenspiegel/einkaufsfinanzierung` ⭐ NEU

### Urlaubsplaner:
- [ ] `/urlaubsplaner/overview`
- [ ] `/urlaubsplaner/antrag`
- [ ] `/urlaubsplaner/genehmigung`
- [ ] `/urlaubsplaner/kalender`

### Andere:
- [ ] `/` (Startseite)
- [ ] `/login`
- [ ] Alle weiteren Seiten

---

## 🎨 DESIGN-STANDARDS

### Bootstrap 5 Komponenten nutzen:

**Buttons:**
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-outline-secondary">Secondary</button>
```

**Cards:**
```html
<div class="card">
  <div class="card-header">Header</div>
  <div class="card-body">Content</div>
</div>
```

**Alerts:**
```html
<div class="alert alert-success">Success!</div>
<div class="alert alert-danger">Error!</div>
```

**Badges:**
```html
<span class="badge bg-primary">New</span>
<span class="badge bg-success">Active</span>
```

---

## 📝 CODING STANDARDS

### Flask Best Practices:

**1. Immer `url_for()` nutzen:**
```python
# ✅ RICHTIG
{{ url_for('bankenspiegel.dashboard') }}
{{ url_for('static', filename='css/style.css') }}

# ❌ FALSCH
/bankenspiegel/dashboard
/static/css/style.css
```

**2. Blueprint-Namen konsistent:**
```python
# Format: modulname_bp
bankenspiegel_bp = Blueprint('bankenspiegel', __name__)
```

**3. Template-Vererbung:**
```html
{% extends "base.html" %}
{% block title %}Meine Seite{% endblock %}
{% block content %}...{% endblock %}
```

---

## ⚠️ FALLSTRICKE

### 1. Blueprint-Namen in url_for()

```python
# Route-Datei:
bankenspiegel_bp = Blueprint('bankenspiegel', __name__)

@bankenspiegel_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Template:
{{ url_for('bankenspiegel.dashboard') }}
#           ^^^^^^^^^^^^  ^^^^^^^^^^
#           Blueprint     Funktionsname
```

### 2. Static Files

```html
<!-- ✅ RICHTIG -->
<link href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/app.js') }}"></script>

<!-- ❌ FALSCH -->
<link href="/static/css/style.css">
<script src="/static/js/app.js"></script>
```

### 3. Block-Namen müssen einzigartig sein

```html
<!-- base.html -->
{% block extra_js %}{% endblock %}

<!-- child.html -->
{% block extra_js %}
<script>...</script>
{% endblock %}
```

---

## 💾 GIT-WORKFLOW

### Nach erfolgreichem Refactoring:

```bash
cd /opt/greiner-portal

# Status prüfen
git status

# Änderungen ansehen
git diff templates/base.html

# Committen
git add templates/base.html
git add routes/*.py  # Falls Blueprint-Namen geändert
git add app.py       # Falls Blueprint-Registrierung geändert

git commit -m "refactor: base.html nach modernem Standard

PROBLEM:
- Prototyp-Code blockierte Einkaufsfinanzierung
- Fehlende Blocks (extra_js, extra_css)
- Hardcoded URLs statt url_for()
- Inkonsistente Blueprint-Namen

LÖSUNG:
- Neue base.html nach Urlaubsplaner-V2-Standard
- Vollständiges Block-System
- Alle URLs auf url_for() umgestellt
- Bootstrap 5 Navbar mit Dropdowns
- Konsistente Blueprint-Namen

FEATURES:
✅ {% block title %}
✅ {% block extra_css %}
✅ {% block content %}
✅ {% block extra_js %}
✅ Modern Navigation (Bootstrap 5)
✅ Responsive Design
✅ Wartbar & erweiterbar

BEHEBT:
- Einkaufsfinanzierung funktioniert jetzt! ⭐
- Alle Seiten einheitlicher Standard
- Bessere Wartbarkeit

TESTED:
✅ Bankenspiegel (alle Seiten)
✅ Urlaubsplaner (alle Seiten)
✅ Einkaufsfinanzierung ⭐
✅ Navigation funktioniert
✅ Responsive (Desktop, Tablet, Mobile)"

git push origin feature/bankenspiegel-komplett
```

---

## 🎯 ERFOLGS-KRITERIEN

Das Refactoring ist erfolgreich wenn:

- ✅ Einkaufsfinanzierung lädt vollständig
- ✅ Charts werden angezeigt
- ✅ Keine Console-Fehler
- ✅ Alle Seiten funktionieren
- ✅ Navigation ist einheitlich
- ✅ Responsive funktioniert
- ✅ Code ist wartbar

---

## 📚 RESSOURCEN

### Dokumentation:

- **Flask Templates:** https://flask.palletsprojects.com/en/3.0.x/templating/
- **Jinja2 Blocks:** https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance
- **Bootstrap 5:** https://getbootstrap.com/docs/5.3/
- **url_for():** https://flask.palletsprojects.com/en/3.0.x/api/#flask.url_for

### Projekt-Dateien als Referenz:

- `/opt/greiner-portal/templates/urlaubsplaner_v2.html` (Vorlage!)
- `/opt/greiner-portal/static/css/vacation_v2.css` (Style-Referenz)
- `/opt/greiner-portal/static/js/vacation_*.js` (JS-Referenz)

---

## 💡 TIPPS

1. **Schritt für Schritt:** Nicht alles auf einmal ändern
2. **Testen, testen, testen:** Nach jeder Änderung testen
3. **Backups:** Vor jeder größeren Änderung Backup erstellen
4. **Git:** Kleine, häufige Commits
5. **Vorlage nutzen:** Urlaubsplaner V2 kopieren & anpassen

---

**Erstellt:** 08.11.2025  
**Priorität:** 🔴 HOCH  
**Nächste Session:** BASE.HTML REFACTORING  
**Aufwand:** 1-2 Stunden

---

*TODO für Greiner Portal - base.html Refactoring*
