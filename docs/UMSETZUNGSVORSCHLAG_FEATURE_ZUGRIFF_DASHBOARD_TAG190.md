# Umsetzungsvorschlag: Feature-Zugriffsverwaltung & Individuelle Startseite

**TAG:** 190  
**Datum:** 2026-01-14  
**Status:** Vorschlag

---

## 📋 ZUSAMMENFASSUNG

Aktuell sind zwei wichtige Features nicht vollständig umgesetzt:

1. **Feature-Zugriff ist nicht bearbeitbar** - Die Feature-Zugriffs-Matrix wird nur angezeigt, kann aber nicht über die UI verwaltet werden
2. **Keine individuelle Startseite** - User können ihre persönliche Startseite nicht konfigurieren

---

## 🎯 ZIELSETZUNG

### 1. Feature-Zugriffsverwaltung
- ✅ Feature-Zugriff über UI bearbeitbar machen
- ✅ Rollen können Features zugewiesen/entfernt werden
- ✅ Änderungen werden in Datenbank gespeichert (nicht nur in Code)
- ✅ Rückwärtskompatibel zu bestehender `config/roles_config.py`

### 2. Individuelle Startseite
- ✅ User können ihre persönliche Startseite konfigurieren
- ✅ Auswahl aus verfügbaren Dashboards/Seiten
- ✅ Widgets/Kacheln für schnellen Zugriff
- ✅ Fallback auf rollenbasierte Weiterleitung wenn nicht konfiguriert

---

## 🏗️ ARCHITEKTUR-ÜBERLEGUNGEN

### Option A: Hybrid-Ansatz (EMPFOHLEN)
- **Feature-Zugriff:** DB-basiert mit Fallback auf `roles_config.py`
- **Vorteile:**
  - Bestehende Logik bleibt erhalten
  - Migration schrittweise möglich
  - Keine Breaking Changes
- **Nachteile:**
  - Zwei Quellen für Feature-Zugriff (DB + Config)
  - Synchronisation nötig

### Option B: Vollständig DB-basiert
- **Feature-Zugriff:** Komplett in DB
- **Vorteile:**
  - Single Source of Truth
  - Einfache Verwaltung
- **Nachteile:**
  - Migration aller bestehenden Daten nötig
  - Code-Änderungen in vielen Stellen

**Empfehlung: Option A (Hybrid)**

---

## 📊 DATENBANK-SCHEMA

### Neue Tabellen

#### 1. `feature_access` (Feature-Zugriff pro Rolle)

```sql
CREATE TABLE feature_access (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(feature_name, role_name)
);

CREATE INDEX idx_feature_access_feature ON feature_access(feature_name);
CREATE INDEX idx_feature_access_role ON feature_access(role_name);
```

**Zweck:** Speichert welche Rollen Zugriff auf welche Features haben (ersetzt/supplementiert `FEATURE_ACCESS` Dictionary)

#### 2. `user_dashboard_config` (Individuelle Startseite)

```sql
CREATE TABLE user_dashboard_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_type VARCHAR(50) NOT NULL,  -- 'redirect', 'custom', 'widgets'
    target_url VARCHAR(255),              -- URL für redirect
    widget_config JSONB,                 -- Widget-Konfiguration (für custom)
    layout_config JSONB,                 -- Layout-Einstellungen
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_dashboard_user ON user_dashboard_config(user_id);
```

**Zweck:** Speichert individuelle Startseiten-Konfiguration pro User

#### 3. `available_dashboards` (Verfügbare Dashboards)

```sql
CREATE TABLE available_dashboards (
    id SERIAL PRIMARY KEY,
    dashboard_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    url VARCHAR(255) NOT NULL,
    icon VARCHAR(50),                    -- Bootstrap Icon
    category VARCHAR(50),                -- 'verkauf', 'werkstatt', 'controlling', etc.
    requires_feature VARCHAR(100),       -- Optional: Feature-Zugriff erforderlich
    role_restriction VARCHAR(50),        -- Optional: Nur für bestimmte Rolle
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboards_category ON available_dashboards(category);
CREATE INDEX idx_dashboards_active ON available_dashboards(active);
```

**Zweck:** Katalog aller verfügbaren Dashboards/Seiten für Startseiten-Konfiguration

---

## 🔧 IMPLEMENTIERUNG

### Phase 1: Feature-Zugriffsverwaltung

#### 1.1 Datenbank-Migration

```sql
-- Migration Script
-- Datei: docs/migrations/migration_tag190_feature_access.sql

-- Tabelle erstellen
CREATE TABLE IF NOT EXISTS feature_access (
    id SERIAL PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(feature_name, role_name)
);

CREATE INDEX IF NOT EXISTS idx_feature_access_feature ON feature_access(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_access_role ON feature_access(role_name);

-- Initial-Daten aus roles_config.py migrieren
INSERT INTO feature_access (feature_name, role_name, created_by)
SELECT 
    feature,
    role,
    'system_migration'
FROM (
    VALUES
        ('bankenspiegel', 'admin'),
        ('bankenspiegel', 'buchhaltung'),
        ('controlling', 'admin'),
        ('controlling', 'buchhaltung'),
        -- ... alle Features aus FEATURE_ACCESS
    ) AS t(feature, role)
ON CONFLICT (feature_name, role_name) DO NOTHING;
```

#### 1.2 API-Erweiterung (`api/admin_api.py`)

```python
# Neue Endpoints:

@admin_api.route('/api/admin/feature-access', methods=['GET'])
def get_feature_access():
    """Feature-Zugriffs-Matrix laden (DB + Config-Fallback)"""
    # 1. Aus DB laden
    # 2. Falls leer, aus roles_config.py laden
    # 3. Zusammenführen
    pass

@admin_api.route('/api/admin/feature-access', methods=['POST'])
def update_feature_access():
    """Feature-Zugriff aktualisieren"""
    # Feature-Rolle-Zuordnung in DB speichern
    pass

@admin_api.route('/api/admin/feature-access/<feature>/role/<role>', methods=['POST'])
def add_feature_access(feature, role):
    """Rolle zu Feature hinzufügen"""
    pass

@admin_api.route('/api/admin/feature-access/<feature>/role/<role>', methods=['DELETE'])
def remove_feature_access(feature, role):
    """Rolle von Feature entfernen"""
    pass
```

#### 1.3 Utility-Funktion (`config/roles_config.py`)

```python
def get_feature_access_from_db():
    """Lädt Feature-Zugriff aus DB, Fallback auf FEATURE_ACCESS"""
    try:
        from api.db_connection import get_db
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT feature_name, role_name 
            FROM feature_access 
            ORDER BY feature_name, role_name
        ''')
        
        db_access = {}
        for row in cursor.fetchall():
            feature = row['feature_name']
            role = row['role_name']
            if feature not in db_access:
                db_access[feature] = []
            db_access[feature].append(role)
        
        conn.close()
        
        # Mit FEATURE_ACCESS zusammenführen (DB hat Priorität)
        merged = FEATURE_ACCESS.copy()
        merged.update(db_access)
        return merged
        
    except Exception as e:
        logger.warning(f"Fehler beim Laden aus DB, verwende Config: {e}")
        return FEATURE_ACCESS
```

#### 1.4 Frontend-Erweiterung (`templates/admin/rechte_verwaltung.html`)

**Änderungen:**
- Feature-Cards werden editierbar
- Klick auf Rolle → Toggle (hinzufügen/entfernen)
- Speichern-Button pro Feature
- Visual Feedback (grün = aktiv, grau = inaktiv)

**JavaScript-Funktionen:**
```javascript
async function toggleFeatureRole(feature, role, element) {
    // API-Call zum Hinzufügen/Entfernen
    // UI aktualisieren
}

async function saveFeatureAccess(feature) {
    // Alle Änderungen für Feature speichern
}
```

---

### Phase 2: Individuelle Startseite

#### 2.1 Datenbank-Migration

```sql
-- Migration Script
-- Datei: docs/migrations/migration_tag190_user_dashboard.sql

-- Tabellen erstellen
CREATE TABLE IF NOT EXISTS available_dashboards (
    id SERIAL PRIMARY KEY,
    dashboard_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    url VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    category VARCHAR(50),
    requires_feature VARCHAR(100),
    role_restriction VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_dashboard_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_type VARCHAR(50) NOT NULL,
    target_url VARCHAR(255),
    widget_config JSONB,
    layout_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Initial-Dashboards einfügen
INSERT INTO available_dashboards (dashboard_key, name, description, url, icon, category, display_order) VALUES
    ('dashboard', 'Allgemeines Dashboard', 'Übersicht über alle Bereiche', '/dashboard', 'bi-speedometer2', 'general', 1),
    ('verkauf_auftragseingang', 'Auftragseingang', 'Verkaufsaufträge verwalten', '/verkauf/auftragseingang', 'bi-cart', 'verkauf', 2),
    ('werkstatt_dashboard', 'Werkstatt Dashboard', 'Werkstatt-Übersicht', '/werkstatt/dashboard', 'bi-tools', 'werkstatt', 3),
    ('controlling', 'Controlling', 'Finanz-Controlling', '/controlling', 'bi-graph-up', 'controlling', 4),
    ('bankenspiegel', 'Bankenspiegel', 'Bankkonten-Übersicht', '/bankenspiegel', 'bi-bank', 'finanzen', 5),
    ('mein_bereich', 'Mein Bereich', 'Persönlicher Bereich', '/mein-bereich', 'bi-person', 'personal', 6)
ON CONFLICT (dashboard_key) DO NOTHING;
```

#### 2.2 API-Erweiterung (`api/admin_api.py`)

```python
@admin_api.route('/api/admin/dashboards', methods=['GET'])
def get_available_dashboards():
    """Verfügbare Dashboards für aktuellen User"""
    # Nur Dashboards zurückgeben, auf die User Zugriff hat
    pass

@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['GET'])
def get_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration laden"""
    pass

@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['POST'])
def set_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration speichern"""
    pass

@admin_api.route('/api/admin/user/<int:user_id>/dashboard', methods=['DELETE'])
def reset_user_dashboard_config(user_id):
    """User-Dashboard-Konfiguration zurücksetzen"""
    pass
```

#### 2.3 Route-Anpassung (`app.py`)

```python
@app.route('/')
@app.route('/start')
@login_required
def start():
    """Dynamische Startseite nach Login"""
    
    # 1. Prüfe individuelle Konfiguration
    user_config = get_user_dashboard_config(current_user.id)
    if user_config and user_config.get('target_url'):
        return redirect(user_config['target_url'])
    
    # 2. Fallback auf rollenbasierte Weiterleitung (bestehende Logik)
    role = getattr(current_user, 'portal_role', 'mitarbeiter')
    # ... bestehende Logik ...
```

#### 2.4 Frontend: Dashboard-Konfiguration

**Neue Seite:** `templates/admin/user_dashboard_config.html`

**Features:**
- Liste verfügbarer Dashboards
- Auswahl per Radio-Button oder Dropdown
- Vorschau der Ziel-URL
- Speichern-Button
- "Zurücksetzen"-Button (zurück zu rollenbasiert)

**Integration:**
- Link im User-Profil-Dropdown: "Startseite konfigurieren"
- Oder: Neuer Tab in Administration

---

## 📝 MIGRATION-STRATEGIE

### Schritt 1: Datenbank-Schema erstellen
```bash
# Migration-Script ausführen
psql -h 127.0.0.1 -U drive_user -d drive_portal -f docs/migrations/migration_tag190_feature_access.sql
psql -h 127.0.0.1 -U drive_user -d drive_portal -f docs/migrations/migration_tag190_user_dashboard.sql
```

### Schritt 2: Code-Implementierung
1. API-Endpoints hinzufügen
2. Utility-Funktionen erweitern
3. Frontend erweitern
4. Route-Anpassung

### Schritt 3: Testing
1. Feature-Zugriff bearbeiten testen
2. Individuelle Startseite konfigurieren testen
3. Fallback-Verhalten testen
4. Rückwärtskompatibilität testen

### Schritt 4: Deployment
1. Service-Neustart: `sudo systemctl restart greiner-portal`
2. Logs prüfen
3. User testen lassen

---

## 🔄 RÜCKWÄRTSKOMPATIBILITÄT

### Feature-Zugriff
- ✅ Bestehende `FEATURE_ACCESS` in `roles_config.py` bleibt erhalten
- ✅ DB-Werte haben Priorität, Config als Fallback
- ✅ Keine Breaking Changes für bestehende Code-Stellen

### Startseite
- ✅ Bestehende rollenbasierte Weiterleitung bleibt als Fallback
- ✅ User ohne Konfiguration → wie bisher
- ✅ Keine Änderung an bestehenden Routes nötig

---

## 🎨 UI/UX-ENTWURF

### Feature-Zugriff (Bearbeitung)

**Aktuell:**
- Feature-Cards zeigen Rollen als statische Tags

**Neu:**
- Feature-Cards mit "Bearbeiten"-Button
- Modal öffnet sich mit:
  - Liste aller verfügbaren Rollen
  - Checkboxen für jede Rolle
  - "Speichern"-Button
- Visual Feedback: Grün = aktiv, Grau = inaktiv

### Individuelle Startseite

**Neue Seite:** `/admin/meine-startseite` oder `/settings/dashboard`

**Layout:**
- Überschrift: "Meine Startseite konfigurieren"
- Radio-Buttons oder Dropdown mit verfügbaren Dashboards
- Vorschau: "Nach Login werde ich weitergeleitet zu: [URL]"
- Buttons: "Speichern", "Zurücksetzen"

**Integration:**
- Link im User-Dropdown (oben rechts): "⚙️ Startseite"
- Oder: Neuer Tab in Administration (nur für eigenen User)

---

## 📊 PRIORISIERUNG

### Phase 1 (HOCH): Feature-Zugriffsverwaltung
- **Aufwand:** Mittel (2-3 Stunden)
- **Nutzen:** Hoch (Admin kann Features ohne Code-Änderung verwalten)
- **Risiko:** Niedrig (Fallback auf Config)

### Phase 2 (MITTEL): Individuelle Startseite
- **Aufwand:** Mittel (2-3 Stunden)
- **Nutzen:** Mittel (User-Komfort)
- **Risiko:** Niedrig (Fallback auf rollenbasiert)

---

## ✅ CHECKLISTE

### Feature-Zugriff
- [ ] DB-Schema erstellen (`feature_access`)
- [ ] Migration-Script erstellen
- [ ] API-Endpoints implementieren
- [ ] Utility-Funktion `get_feature_access_from_db()` erstellen
- [ ] Frontend editierbar machen
- [ ] Testing: Feature-Rolle hinzufügen/entfernen
- [ ] Testing: Fallback auf Config

### Individuelle Startseite
- [ ] DB-Schema erstellen (`user_dashboard_config`, `available_dashboards`)
- [ ] Migration-Script erstellen
- [ ] Initial-Dashboards einfügen
- [ ] API-Endpoints implementieren
- [ ] Route `start()` anpassen
- [ ] Frontend-Seite erstellen
- [ ] Testing: Dashboard konfigurieren
- [ ] Testing: Fallback auf rollenbasiert

---

## 🚀 NÄCHSTE SCHRITTE

1. **Vorschlag besprechen** mit User
2. **Priorisierung** festlegen
3. **Implementierung starten** (Phase 1 oder Phase 2)
4. **Testing** durchführen
5. **Deployment** auf Server

---

## 📝 ANMERKUNGEN

- **SSOT-Prinzip:** Feature-Zugriff wird hybrid (DB + Config), aber DB hat Priorität
- **Keine Breaking Changes:** Bestehende Logik bleibt als Fallback
- **Migration:** Schrittweise möglich, keine Big Bang
- **User-Experience:** Beide Features verbessern Admin- und User-Erfahrung

---

*Erstellt: TAG 190 | Autor: Claude AI*
