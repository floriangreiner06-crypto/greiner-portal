# Standort-Filter Component - Zentrale Navigation

**TAG 177:** Wiederverwendbares Component für Standort-Filter-Navigation

---

## Übersicht

Zentrale Komponente für einheitliche Standort-Filter-Navigation mit Tabs statt Dropdowns.

### Vorteile:
- ✅ Einheitliche UI/UX über alle Features
- ✅ Keine Code-Duplikation
- ✅ Konsolidierte Ansicht standardmäßig verfügbar
- ✅ Einfache Integration

---

## Verwendung

### 1. In Templates

```jinja2
{% set current_standort = standort %}
{% set konsolidiert = konsolidiert | default(false) %}
{% include 'components/standort_filter_tabs.html' %}
```

**Mit zusätzlichen URL-Parametern:**
```jinja2
{% set additional_params = {
    'geschaeftsjahr': geschaeftsjahr,
    'monat': monat
} %}
{% include 'components/standort_filter_tabs.html' %}
```

**Ohne konsolidierte Ansicht:**
```jinja2
{% set show_konsolidiert = false %}
{% include 'components/standort_filter_tabs.html' %}
```

### 2. In Routes (Python)

```python
from utils.standort_filter_helpers import parse_standort_params, get_standorte_fuer_query

@route('/mein-feature')
def mein_feature():
    # Standort-Parameter parsen
    standort, konsolidiert = parse_standort_params(request)
    
    # Für Query: Liste von Standort-IDs
    standorte_fuer_query = get_standorte_fuer_query(standort, konsolidiert)
    
    # Query bauen
    if standorte_fuer_query:
        query = "WHERE standort = ANY(%s)"
        params = [standorte_fuer_query]
    else:
        query = ""  # Alle Standorte
        params = []
    
    # An Template weitergeben
    return render_template('mein_feature.html',
        standort=standort,
        konsolidiert=konsolidiert,
        # ...
    )
```

---

## Features, die das Component verwenden sollten

### Bereits umgesetzt:
- ✅ `planung/abteilungsleiter_uebersicht.html` (TAG 177)

### Sollten umgestellt werden:
- ⏳ `controlling/tek_dashboard_v2.html` - Aktuell Dropdowns
- ⏳ `verkauf_gw_dashboard.html` - Aktuell Dropdowns
- ⏳ `verkauf_budget_wizard.html` - Aktuell Dropdowns
- ⏳ `controlling/bwa.html` - Aktuell Dropdowns
- ⏳ `controlling/kst_ziele.html` - Aktuell Dropdowns
- ⏳ Alle anderen Features mit Standort-Filter

---

## Migration

### Vorher (Dropdown):
```html
<select name="standort">
    <option value="">Alle</option>
    <option value="1">Deggendorf</option>
    <option value="2">Hyundai DEG</option>
    <option value="3">Landau</option>
</select>
<button type="submit">Filtern</button>
```

### Nachher (Tabs):
```jinja2
{% include 'components/standort_filter_tabs.html' %}
```

**Vorteile:**
- Kein "Filtern"-Button nötig
- Direkte Navigation
- Konsolidierte Ansicht verfügbar
- Einheitliche UI

---

## Technische Details

### Component: `templates/components/standort_filter_tabs.html`
- Jinja2 Include
- Automatische URL-Parameter-Erhaltung
- Bootstrap 5 Tabs

### Helper: `utils/standort_filter_helpers.py`
- `parse_standort_params()` - Parst Request-Parameter
- `get_standorte_fuer_query()` - Gibt Standort-Liste für Query zurück

### SSOT: `api/standort_utils.py`
- `build_locosoft_filter_verkauf()` - SQL-Filter für Verkäufe
- `build_locosoft_filter_bestand()` - SQL-Filter für Bestand
- `build_locosoft_filter_orders()` - SQL-Filter für Orders
- `build_consolidated_filter()` - Konsolidierte Filter

---

## Beispiel: Vollständige Integration

### Route:
```python
from flask import Blueprint, render_template, request
from utils.standort_filter_helpers import parse_standort_params
from api.standort_utils import build_locosoft_filter_verkauf

bp = Blueprint('mein_feature', __name__)

@bp.route('/mein-feature')
def uebersicht():
    standort, konsolidiert = parse_standort_params(request)
    
    # Filter für Query
    if standort:
        filter_sql = build_locosoft_filter_verkauf(standort, nur_stellantis=False)
    else:
        filter_sql = ""
    
    # Daten laden
    # ...
    
    return render_template('mein_feature.html',
        standort=standort,
        konsolidiert=konsolidiert,
        # ...
    )
```

### Template:
```jinja2
{% extends "base.html" %}

{% block content %}
<h1>Mein Feature</h1>

{% set current_standort = standort %}
{% include 'components/standort_filter_tabs.html' %}

<!-- Content -->
{% endblock %}
```

---

**Status:** ✅ Component erstellt, ⏳ Migration der Features offen
