# Rechteverwaltung Redesign — Umsetzung

## Aufgabe

Umbau der Rechteverwaltung auf "Option B clean": Portal steuert Rollen komplett, LDAP liefert nur Identität. Das Mockup liegt als `rechteverwaltung_mockup.jsx` im Projekt.

## Problem (Ist-Zustand)

Die Portal-Rolle wird aktuell aus dem **LDAP-Titel** abgeleitet (`get_role_from_title()`). Wenn ein Admin in der Rechteverwaltung eine Rolle ändert, hat das **keine Auswirkung** auf Navigation und Feature-Zugriff — weil `portal_role` bei jedem Request aus `users.title` (LDAP) neu berechnet wird. Nur die Rolle `admin` in `user_roles` wirkt als Override.

Beispiel: Silvia Eiglmaier wurde in der Rechteverwaltung von "Buchhaltung" auf "Verkauf" geändert. Im AD steht aber weiterhin OU=Buchhaltung, Title="Mitarbeiterin Buchhaltung" → Portal zeigt weiterhin alle Buchhaltungs-Features.

## Ziel (Soll-Zustand)

Klare Kaskade für die wirksame Portal-Rolle:

1. **admin** in `user_roles` → voller Zugriff (bleibt wie bisher)
2. **`users.portal_role_override`** (vom Admin im Portal gesetzt) → diese Rolle + deren Features
3. **Fallback:** `mitarbeiter` (minimaler Zugriff: nur Urlaubsplaner, eigene Daten)

LDAP-Titel und OU werden **nur noch zur Anzeige** gespeichert, **nicht** mehr für Berechtigungen verwendet. `get_role_from_title()` und `TITLE_TO_ROLE` fallen weg.

## Umsetzungsschritte

### Schritt 1: DB-Migration

```sql
-- Neue Spalte für Portal-Rollen-Override
ALTER TABLE users ADD COLUMN portal_role_override TEXT DEFAULT NULL;
```

### Schritt 2: Migration bestehender Rollen

Script `scripts/migrations/migrate_to_portal_role_override.py`:
- Alle User durchgehen
- Aktuelles `get_role_from_title(user.title)` Ergebnis als `portal_role_override` schreiben
- Damit geht beim Umschalten nichts verloren

### Schritt 3: `auth/auth_manager.py` — Kern-Änderung

**`get_user_by_id()`** (Session-Reload bei jedem Request):

```python
def get_user_by_id(self, user_id):
    # ... User + Rollen aus DB laden wie bisher ...
    
    # NEU: Portal-Rolle Kaskade
    if 'admin' in roles:
        portal_role = 'admin'
        allowed_features = ALL_FEATURES  # alles
    elif user_row['portal_role_override']:
        portal_role = user_row['portal_role_override']
        allowed_features = get_features_for_role(portal_role)  # aus feature_access Tabelle
    else:
        portal_role = 'mitarbeiter'
        allowed_features = get_features_for_role('mitarbeiter')  # nur Urlaubsplaner etc.
    
    user = User(
        ...,
        portal_role=portal_role,
        allowed_features=allowed_features
    )
    return user
```

**`authenticate_user()`** (Login):
- LDAP-Auth bleibt
- `_cache_user()`: `title` und `ou` weiterhin aus LDAP schreiben (nur Info)
- **NICHT** mehr `portal_role` aus Title ableiten
- **NICHT** `portal_role_override` überschreiben beim Login
- `user_roles` weiterhin aus OU schreiben (nur für admin-Check relevant)

**Entfernen:**
- `get_role_from_title()` Aufrufe
- Jegliche Ableitung von Berechtigungen aus `users.title` oder `users.ou`

### Schritt 4: `config/roles_config.py` — Aufräumen

**Entfernen:**
- `TITLE_TO_ROLE` Dict
- `get_role_from_title()` Funktion

**Beibehalten/Erweitern:**
- `FEATURE_ACCESS` Dict (oder besser: nur noch aus DB lesen)
- `ROLES` Liste mit allen verfügbaren Rollen und deren Display-Info

```python
ROLES = {
    'admin':              {'label': 'Administrator',      'icon': '🛡️'},
    'geschaeftsfuehrung': {'label': 'Geschäftsführung',   'icon': '👔'},
    'buchhaltung':        {'label': 'Buchhaltung',        'icon': '📊'},
    'verkauf':            {'label': 'Verkauf',            'icon': '🚗'},
    'verkauf_leitung':    {'label': 'Verkaufsleitung',    'icon': '📈'},
    'werkstatt':          {'label': 'Werkstatt/Service',  'icon': '🔧'},
    'service_leitung':    {'label': 'Serviceleitung',     'icon': '⚙️'},
    'teile':              {'label': 'Teile & Zubehör',    'icon': '📦'},
    'mitarbeiter':        {'label': 'Mitarbeiter',        'icon': '👤'},
}
```

### Schritt 5: `api/admin_api.py` — Neue Endpoints

```python
# Portal-Rolle eines Users setzen
@admin_bp.route('/admin/user/<int:user_id>/portal-role', methods=['POST'])
@require_role('admin')
def set_user_portal_role(user_id):
    """Setzt portal_role_override für einen User"""
    role = request.json.get('role')  # z.B. "verkauf" oder null zum Zurücksetzen
    
    if role and role not in ROLES:
        return jsonify({'error': 'Ungültige Rolle'}), 400
    
    # In DB schreiben
    db.execute('UPDATE users SET portal_role_override = ? WHERE id = ?', (role, user_id))
    
    # Audit-Log
    log_event(f'portal_role_override für User {user_id} auf "{role}" gesetzt')
    
    return jsonify({'success': True, 'portal_role': role or 'mitarbeiter'})


# Feature-Zugriff einer Rolle lesen/schreiben
@admin_bp.route('/admin/role/<role_name>/features', methods=['GET'])
@require_role('admin')
def get_role_features(role_name):
    """Liest Features einer Rolle aus feature_access"""
    features = db.execute(
        'SELECT feature_name FROM feature_access WHERE role_name = ?', (role_name,)
    )
    return jsonify({'role': role_name, 'features': [f['feature_name'] for f in features]})


@admin_bp.route('/admin/role/<role_name>/features', methods=['PUT'])
@require_role('admin')
def set_role_features(role_name):
    """Setzt Features einer Rolle (komplett ersetzen)"""
    features = request.json.get('features', [])
    
    db.execute('DELETE FROM feature_access WHERE role_name = ?', (role_name,))
    for feature in features:
        db.execute('INSERT INTO feature_access (role_name, feature_name) VALUES (?, ?)', 
                   (role_name, feature))
    
    return jsonify({'success': True, 'role': role_name, 'features': features})
```

### Schritt 6: `api/navigation_utils.py` — Prüfung

`get_navigation_for_user()` verwendet schon `current_user.portal_role` und `can_access_feature` — das sollte mit dem neuen System direkt funktionieren, weil `portal_role` und `allowed_features` jetzt korrekt aus der Kaskade kommen. Trotzdem prüfen:

- `can_access_feature(user, feature)` muss `feature in user.allowed_features` prüfen
- Kein Fallback auf `get_role_from_title()` mehr

### Schritt 7: Template `templates/admin/rechte_verwaltung.html` — UI Redesign

Orientiere dich am Mockup (`rechteverwaltung_mockup.jsx`). Die Seite hat 4 Tabs:

**Tab 1 "User & Rollen":**
- User-Tabelle mit Suche, Standort-Filter, Status-Filter
- Spalten: Name, LDAP-Info (nur Anzeige!), Portal-Rolle (Dropdown), Quelle (Portal/Default), Aktion
- "⚠ Ohne Rolle" als Warnung für User ohne portal_role_override
- Beim Speichern: AJAX POST an `/admin/user/<id>/portal-role`

**Tab 2 "Rollen-Features":**
- Rolle auswählen (Buttons), dann Feature-Checkboxen gruppiert nach Bereich
- Beim Speichern: AJAX PUT an `/admin/role/<name>/features`

**Tab 3 "Matrix":**
- Read-only Tabelle: Features (Zeilen) × Rollen (Spalten), ✓/— pro Zelle

**Tab 4 ist nur im Mockup** (Architektur-Doku, muss nicht im Portal sein).

### Schritt 8: Diagnose-Script aktualisieren

`scripts/checks/check_user_portal_role.py` anpassen:
- Zeigt jetzt: username, ou (AD), title (AD), portal_role_override, **wirksame Rolle** (aus Kaskade), Features
- Statt `get_role_from_title()` die neue Kaskade prüfen

## Betroffene Dateien

| Datei | Aktion |
|---|---|
| `auth/auth_manager.py` | **Kern-Änderung:** Kaskade in `get_user_by_id()` und `authenticate_user()` |
| `config/roles_config.py` | Aufräumen: `TITLE_TO_ROLE` + `get_role_from_title()` entfernen, `ROLES` dict hinzufügen |
| `api/admin_api.py` | Neue Endpoints für portal-role und role-features |
| `api/navigation_utils.py` | Prüfen, ggf. anpassen |
| `templates/admin/rechte_verwaltung.html` | UI-Redesign nach Mockup |
| `scripts/migrations/migrate_to_portal_role_override.py` | Neu: Einmal-Migration |
| `scripts/checks/check_user_portal_role.py` | Anpassen an neue Kaskade |
| `docs/workstreams/auth-ldap/CONTEXT.md` | Doku aktualisieren |

## Reihenfolge

1. **Backup** aller betroffenen Dateien (`*.bak_rechteverwaltung`)
2. DB-Migration (ALTER TABLE)
3. Migrations-Script laufen lassen (bestehende Title-Rollen → portal_role_override)
4. `auth_manager.py` umbauen (Kaskade)
5. `roles_config.py` aufräumen
6. `admin_api.py` neue Endpoints
7. Template redesignen
8. `navigation_utils.py` prüfen
9. Diagnose-Script anpassen
10. Testen: Silvia Eiglmaier als Testcase — Rolle auf "verkauf" setzen, prüfen dass Navi stimmt
11. Git commit

## Wichtige Regeln

- **LDAP/AD nicht anfassen** — wir ändern nichts im Active Directory
- **Bestehende Sessions:** Nach Deployment muss jeder User sich einmal neu anmelden oder die Session wird beim nächsten Request automatisch die neue Kaskade durchlaufen (da `get_user_by_id()` bei jedem Request aufgerufen wird)
- **feature_access Tabelle** wird zur Single Source of Truth — kein Fallback auf Python-Config mehr
- **Audit-Log:** Jede Rollenänderung loggen (wer, wann, welcher User, alte Rolle → neue Rolle)
- Bootstrap 4 + jQuery für das Template (wie im restlichen Portal)
- Kein neues Framework einführen

## Testfälle

1. Silvia Eiglmaier: portal_role_override = "verkauf" → sieht nur Verkaufs-Features in der Navi
2. Florian Greiner: admin in user_roles → sieht alles (Override irrelevant)
3. Neuer User ohne portal_role_override → sieht nur Urlaubsplaner (Default mitarbeiter)
4. Lisa Bauer: portal_role_override = null → Default mitarbeiter → nur Urlaubsplaner
5. Rolle ändern in Rechteverwaltung → sofort wirksam beim nächsten Seitenaufruf (kein Re-Login nötig)
