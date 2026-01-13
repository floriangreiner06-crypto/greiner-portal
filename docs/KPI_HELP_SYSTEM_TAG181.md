# KPI Help System - Zentrale Hilfe für alle Features

**TAG:** 181  
**Datum:** 2026-01-12  
**Status:** ✅ Implementiert

---

## 📋 ÜBERBLICK

Das **KPI Help System** bietet eine einheitliche Hilfe-Funktionalität für alle KPIs im System. User können per Klick auf ein Info-Icon detaillierte Erklärungen zu Berechnung, Datengrundlage und Zielwerten erhalten.

---

## 🎯 ZWECK

**Problem:** User verstehen KPIs nicht immer - Formeln, Datengrundlagen und Zielwerte sind nicht klar.

**Lösung:** Zentrale Help-Komponente, die:
- ✅ Einheitlich für alle Features verwendet werden kann
- ✅ KPI-Definitionen zentral verwaltet
- ✅ Pro Feature erweiterbar ist
- ✅ Modal-basiert (nicht störend)
- ✅ Responsive und benutzerfreundlich

---

## 🚀 VERWENDUNG

### 1. Help-Icon anzeigen

**HTML:**
```html
<h6 class="text-muted mb-2">
    <i class="bi bi-speedometer"></i> Leistungsgrad
    <i class="bi bi-info-circle kpi-help-icon text-primary ms-1" 
       data-kpi="leistungsgrad" 
       style="cursor: pointer; font-size: 0.9rem;" 
       data-bs-toggle="tooltip" 
       title="Klicken für Hilfe"></i>
</h6>
```

**Wichtig:**
- Klasse: `kpi-help-icon` (muss vorhanden sein!)
- Attribut: `data-kpi="leistungsgrad"` (KPI-Name)
- Tooltip optional: `data-bs-toggle="tooltip"`

### 2. Help-System einbinden

**In Template:**
```html
{% block extra_js %}
<!-- KPI Help System -->
<script src="{{ url_for('static', filename='js/kpi_help.js') }}?v={{ STATIC_VERSION }}"></script>
{% endblock %}
```

**Auto-Init:** Das System initialisiert sich automatisch beim DOMContentLoaded.

### 3. Klick-Handler

**Automatisch:** Das System registriert automatisch Click-Handler für alle `.kpi-help-icon` Elemente.

**Manuell (optional):**
```javascript
// Help für einen KPI anzeigen
kpiHelp.showHelp('leistungsgrad');
```

---

## 📊 KPI-DEFINITIONEN

### Aktuell definierte KPIs

| KPI | Name | Datei |
|-----|------|-------|
| `leistungsgrad` | Leistungsgrad | `static/js/kpi_help.js` |
| `produktivitaet` | Produktivität | `static/js/kpi_help.js` |
| `effizienz` | Effizienz | `static/js/kpi_help.js` |
| `anwesenheitsgrad` | Anwesenheitsgrad | `static/js/kpi_help.js` |
| `entgangener_umsatz` | Entgangener Umsatz | `static/js/kpi_help.js` |

### KPI-Definition-Struktur

```javascript
{
    name: 'Leistungsgrad',
    formel: 'AW × 6 / Stempelzeit × 100',
    ziel: '≥ 100%',
    beschreibung: 'Wie schnell arbeitet der Mechaniker im Vergleich zur Kalkulation?',
    datengrundlage: 'Vorgabe-AW aus Rechnungen (labours) vs. gestempelte Zeit (times type=2)',
    beispiel: '10 AW Vorgabe, 8 AW gestempelt → 125% (schneller als kalkuliert)',
    schwellenwerte: {
        gut: '≥ 85%',
        warnung: '≥ 70%',
        kritisch: '< 70%'
    },
    berechnung: 'Die Vorgabe-AW werden mit 6 multipliziert (1 AW = 6 Min), dann durch die gestempelte Zeit geteilt.',
    hinweis: 'Optional: Zusätzliche Hinweise'
}
```

---

## 🔧 ERWEITERN FÜR NEUE FEATURES

### Neue KPI-Definition hinzufügen

**Option 1: In kpi_help.js erweitern**
```javascript
// In static/js/kpi_help.js
this.kpiDefinitions = {
    // ... bestehende KPIs ...
    'neuer_kpi': {
        name: 'Neuer KPI',
        formel: 'X / Y × 100',
        ziel: '≥ 80%',
        beschreibung: 'Beschreibung...',
        datengrundlage: 'Datenquelle...',
        beispiel: 'Beispiel...',
        schwellenwerte: {
            gut: '≥ 80%',
            warnung: '≥ 60%',
            kritisch: '< 60%'
        },
        berechnung: 'Berechnung...'
    }
};
```

**Option 2: Dynamisch hinzufügen**
```javascript
// In Feature-spezifischem JavaScript
kpiHelp.addKPI('neuer_kpi', {
    name: 'Neuer KPI',
    formel: 'X / Y × 100',
    // ... weitere Felder
});
```

### Help-Icon in Feature einfügen

```html
<!-- Beispiel: In einem Dashboard -->
<div class="kpi-card">
    <h5>
        Neuer KPI
        <i class="bi bi-info-circle kpi-help-icon text-primary ms-1" 
           data-kpi="neuer_kpi" 
           style="cursor: pointer; font-size: 0.9rem;"></i>
    </h5>
    <div class="kpi-value">85%</div>
</div>
```

---

## 📁 DATEIEN

| Datei | Zweck |
|-------|-------|
| `static/js/kpi_help.js` | Zentrale Help-System-Implementierung |
| `docs/KPI_HELP_SYSTEM_TAG181.md` | Diese Dokumentation |
| `templates/aftersales/werkstatt_uebersicht.html` | Beispiel-Integration |

---

## 🎨 MODAL-DESIGN

Das Help-Modal zeigt:
- **Header:** KPI-Name mit Icon
- **Berechnung:** Formel und Erklärung
- **Zielwert:** Grün hervorgehoben
- **Schwellenwerte:** Gut/Warnung/Kritisch mit Badges
- **Datengrundlage:** Datenquelle (z.B. Locosoft-Tabellen)
- **Beispiel:** Konkrete Berechnung
- **Hinweis:** Optional zusätzliche Informationen

**Styling:** Bootstrap 5 Modal mit farbigen Cards für bessere Lesbarkeit.

---

## ✅ BEST PRACTICES

### 1. Konsistente KPI-Namen

**✅ GUT:**
- `leistungsgrad`, `produktivitaet`, `anwesenheitsgrad`
- Kleinschreibung, einheitliche Namenskonvention

**❌ SCHLECHT:**
- `Leistungsgrad`, `Produktivität`, `anwesenheits_grad`
- Inkonsistente Schreibweise

### 2. Help-Icons platzieren

**✅ GUT:**
- Direkt neben KPI-Name
- Kleine Größe (0.9rem)
- Primärfarbe für Sichtbarkeit

**❌ SCHLECHT:**
- Zu groß oder zu klein
- Zu weit vom KPI-Name entfernt
- Unauffällige Farbe

### 3. KPI-Definitionen pflegen

**✅ GUT:**
- Alle Felder ausfüllen (name, formel, ziel, beschreibung, datengrundlage, beispiel, schwellenwerte)
- Klare, verständliche Sprache
- Konkrete Beispiele

**❌ SCHLECHT:**
- Unvollständige Definitionen
- Technischer Jargon ohne Erklärung
- Keine Beispiele

---

## 🔄 MIGRATION FÜR BESTEHENDE FEATURES

### Schritt 1: Help-System einbinden

```html
{% block extra_js %}
<script src="{{ url_for('static', filename='js/kpi_help.js') }}?v={{ STATIC_VERSION }}"></script>
{% endblock %}
```

### Schritt 2: KPI-Definitionen hinzufügen

In `static/js/kpi_help.js` oder per `kpiHelp.addKPI()`.

### Schritt 3: Help-Icons einfügen

Bei jedem KPI ein Help-Icon hinzufügen:
```html
<i class="bi bi-info-circle kpi-help-icon text-primary ms-1" 
   data-kpi="kpi_name" 
   style="cursor: pointer; font-size: 0.9rem;"></i>
```

### Schritt 4: Testen

- Help-Icon klicken
- Modal öffnet sich
- Alle Informationen werden korrekt angezeigt

---

## 📝 BEISPIEL: WERKSTATT-DASHBOARD

**Implementiert in:** `templates/aftersales/werkstatt_uebersicht.html`

**KPIs mit Help:**
- ✅ Leistungsgrad
- ✅ Produktivität
- ✅ Anwesenheitsgrad (TAG 181)
- ✅ Effizienz
- ✅ Entgangener Umsatz

**Code-Beispiel:**
```html
<h6 class="text-muted mb-2">
    <i class="bi bi-speedometer"></i> Leistungsgrad
    <i class="bi bi-info-circle kpi-help-icon text-primary ms-1" 
       data-kpi="leistungsgrad" 
       style="cursor: pointer; font-size: 0.9rem;" 
       data-bs-toggle="tooltip" 
       title="Klicken für Hilfe"></i>
</h6>
```

---

## 🚀 NÄCHSTE SCHRITTE

### Für alle Features

1. **Help-System einbinden** (siehe Verwendung)
2. **KPI-Definitionen hinzufügen** (siehe Erweitern)
3. **Help-Icons einfügen** (siehe Verwendung)
4. **Testen** (Modal öffnet, Informationen korrekt)

### Empfohlene Features

- ✅ **Werkstatt-Dashboard** (bereits implementiert)
- ⏳ **Controlling/BWA** (KPIs: Umsatz, Kosten, DB, etc.)
- ⏳ **Verkauf** (KPIs: Verkäufe, Marge, etc.)
- ⏳ **Urlaubsplaner** (KPIs: Auslastung, etc.)

---

## 🔗 RELEVANTE DATEIEN

- `static/js/kpi_help.js` - Help-System-Implementierung
- `docs/KPI_HELP_SYSTEM_TAG181.md` - Diese Dokumentation
- `docs/KPI_DEFINITIONEN.md` - KPI-Definitionen (Backend)
- `utils/kpi_definitions.py` - KPI-Berechnungen (Backend)

---

**Erstellt:** TAG 181 (2026-01-12)  
**Autor:** Claude  
**Status:** ✅ Produktiv
