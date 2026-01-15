# Vorschlag: Zentrales Navigations-Management

**TAG:** 190  
**Datum:** 2026-01-14  
**Status:** Vorschlag

---

## 🎯 PROBLEM

Aktuell:
- Navigation ist hardcoded in `base.html`
- Viele Items haben keine Feature-Prüfung
- Mix aus `can_access_feature()` und `portal_role` Checks
- Keine zentrale Verwaltung
- Schwer zu überblicken, welche Items für welche Rollen sichtbar sind
- Entwicklungs-Features können nicht einfach ausgeblendet werden

---

## 💡 LÖSUNG: DB-basiertes Navigations-Management

### Konzept: Feature-basiert (keine Redundanz!)

**Prinzip:** Nutze bestehende Feature-Zugriffe - keine neue Berechtigungslogik!

1. **DB-Tabelle** für Navigation-Items
2. **Feature-Zuordnung** pro Item (optional)
3. **Admin-UI** zum Verwalten
4. **Template-Funktion** rendert Navigation aus DB
5. **Fallback** auf bestehende Navigation (keine Breaking Changes)

---

## 🏗️ ARCHITEKTUR

### Option A: Vollständig DB-basiert (EMPFOHLEN)

**Vorteile:**
- ✅ Zentrale Verwaltung
- ✅ Einfach Items ein/ausblenden
- ✅ Übersichtlich für Admins
- ✅ Keine Redundanz (nutzt Feature-Zugriffe)

**Nachteile:**
- ⚠️ Migration nötig (aber mit Fallback)

### Option B: Hybrid (Config + DB)

**Vorteile:**
- ✅ Schneller zu implementieren
- ✅ Fallback auf Config

**Nachteile:**
- ⚠️ Zwei Quellen (Redundanz)

**Empfehlung: Option A**

---

## 📊 DATENBANK-SCHEMA

### Tabelle: `navigation_items`

```sql
CREATE TABLE navigation_items (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES navigation_items(id) ON DELETE CASCADE,
    label VARCHAR(200) NOT NULL,
    url VARCHAR(255),
    icon VARCHAR(50),
    order_index INTEGER DEFAULT 0,
    requires_feature VARCHAR(100),  -- Optional: Feature-Zugriff erforderlich
    role_restriction VARCHAR(50),   -- Optional: Nur für bestimmte Rolle
    is_dropdown BOOLEAN DEFAULT false,
    is_header BOOLEAN DEFAULT false,  -- Für Dropdown-Header
    is_divider BOOLEAN DEFAULT false, -- Für Dropdown-Divider
    active BOOLEAN DEFAULT true,
    category VARCHAR(50),            -- 'main', 'dropdown', 'user_menu'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nav_parent ON navigation_items(parent_id);
CREATE INDEX idx_nav_active ON navigation_items(active);
CREATE INDEX idx_nav_category ON navigation_items(category);
```

**Struktur:**
- Top-Level Items: `parent_id = NULL`
- Dropdown-Items: `parent_id = ID des Dropdowns`
- Headers/Divider: `is_header = true` oder `is_divider = true`

---

## 🔧 IMPLEMENTIERUNG

### Phase 1: Datenbank & API

1. **Migration-Script** erstellen
2. **Initial-Daten** aus `base.html` migrieren
3. **API-Endpoints** für CRUD-Operationen
4. **Template-Funktion** zum Rendern

### Phase 2: Admin-UI

1. **Neuer Tab** in Rechteverwaltung: "Navigation"
2. **Drag & Drop** für Reihenfolge (optional)
3. **Toggle** für aktiv/inaktiv
4. **Feature-Zuordnung** pro Item

### Phase 3: Template-Integration

1. **Template-Funktion** `render_navigation()` erstellen
2. **Fallback** auf bestehende Navigation
3. **Schrittweise Migration**

---

## 📝 BEISPIEL-DATEN

```sql
-- Top-Level: Controlling
INSERT INTO navigation_items (label, url, icon, order_index, requires_feature, is_dropdown, category) VALUES
('Controlling', NULL, 'bi-graph-up-arrow', 2, NULL, true, 'main');

-- Dropdown-Items: Controlling
INSERT INTO navigation_items (parent_id, label, url, icon, order_index, is_header) VALUES
((SELECT id FROM navigation_items WHERE label = 'Controlling'), 'Übersichten', NULL, NULL, 1, true),
((SELECT id FROM navigation_items WHERE label = 'Controlling'), 'Dashboard', '/controlling/dashboard', 'bi-speedometer2', 2, false),
((SELECT id FROM navigation_items WHERE label = 'Controlling'), 'BWA', '/controlling/bwa', 'bi-graph-up', 3, false),
((SELECT id FROM navigation_items WHERE label = 'Controlling'), 'TEK', '/controlling/tek', 'bi-bar-chart-line', 4, false);

-- Divider
INSERT INTO navigation_items (parent_id, label, is_divider, order_index) VALUES
((SELECT id FROM navigation_items WHERE label = 'Controlling'), '', true, 5);
```

---

## 🎨 ADMIN-UI KONZEPT

### Tab "Navigation" in Rechteverwaltung

**Layout:**
- Baumstruktur (Top-Level → Dropdown-Items)
- Checkboxen für aktiv/inaktiv
- Dropdown für Feature-Zuordnung
- Drag & Drop für Reihenfolge (optional)
- "Neu hinzufügen" Button

**Features:**
- ✅ Item aktivieren/deaktivieren
- ✅ Feature zuordnen/entfernen
- ✅ Reihenfolge ändern
- ✅ Item hinzufügen/löschen
- ✅ Vorschau der Navigation

---

## 🔄 MIGRATION-STRATEGIE

### Schritt 1: DB-Schema + Initial-Daten
- Tabelle erstellen
- Alle Items aus `base.html` migrieren
- Feature-Zuordnungen setzen

### Schritt 2: Template-Funktion
- `render_navigation()` erstellen
- Fallback auf bestehende Navigation
- Testen

### Schritt 3: Admin-UI
- Tab hinzufügen
- CRUD-Funktionalität
- Testen

### Schritt 4: Aktivierung
- Template auf DB-basierte Navigation umstellen
- Fallback behalten für Sicherheit

---

## ✅ VORTEILE

1. **Zentrale Verwaltung:**
   - Alle Nav-Items an einem Ort
   - Einfach ein/ausblenden
   - Übersichtlich für Admins

2. **Keine Redundanz:**
   - Nutzt bestehende Feature-Zugriffe
   - Keine neue Berechtigungslogik
   - SSOT-Prinzip

3. **Flexibilität:**
   - Entwicklungs-Features einfach ausblenden
   - Neue Items schnell hinzufügen
   - Reihenfolge anpassbar

4. **Übersicht:**
   - Admin sieht alle Items
   - Welche Features benötigt werden
   - Welche Rollen Zugriff haben

---

## ⚠️ ALTERNATIVE: Einfacherer Ansatz

### Option: Feature-Flags in Config

**Vorteile:**
- Schneller zu implementieren
- Keine DB-Änderungen
- Einfach zu verwalten

**Nachteile:**
- Code-Änderung nötig für neue Items
- Nicht so flexibel

**Beispiel:**
```python
# config/navigation_config.py
NAVIGATION_ITEMS = {
    'controlling': {
        'label': 'Controlling',
        'requires_feature': None,  # Oder ['bankenspiegel', 'zinsen']
        'items': [
            {'label': 'Dashboard', 'url': '/controlling/dashboard', 'requires_feature': 'controlling'},
            # ...
        ]
    }
}
```

---

## 🎯 EMPFEHLUNG

**Option A (DB-basiert)** für:
- ✅ Langfristige Wartbarkeit
- ✅ Zentrale Verwaltung
- ✅ Keine Code-Änderungen für Nav-Updates

**Option B (Config-basiert)** für:
- ✅ Schnelle Implementierung
- ✅ Weniger Komplexität
- ✅ Code-Review für Nav-Änderungen (kann Vorteil sein!)

---

## 📊 VERGLEICH

| Aspekt | DB-basiert | Config-basiert |
|--------|------------|----------------|
| Implementierung | Mittel (2-3h) | Schnell (1h) |
| Wartbarkeit | Hoch | Mittel |
| Flexibilität | Sehr hoch | Mittel |
| Code-Änderungen | Nein | Ja |
| Admin-Aufwand | Niedrig | Mittel |
| Übersicht | Sehr gut | Gut |

---

## 🚀 NÄCHSTE SCHRITTE

1. **Entscheidung:** Option A oder B?
2. **Implementierung** starten
3. **Migration** durchführen
4. **Testing**

---

*Erstellt: TAG 190 | Autor: Claude AI*
