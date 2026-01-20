# Urlaubsplaner Code-Analyse (TAG 198)

**Datum:** 2026-01-18  
**Zweck:** Umfangreiche Analyse des Urlaubsplaner-Codes nach User-Test  
**Vermutung:** Bugs entstanden bei SQLite→PostgreSQL Migration und Refactoring

---

## 📋 INHALTSVERZEICHNIS

1. [Architektur-Übersicht](#architektur)
2. [Kritische Bugs gefunden](#kritische-bugs)
3. [SQLite→PostgreSQL Migrations-Probleme](#migrations-probleme)
4. [Refactoring-Probleme](#refactoring-probleme)
5. [Genehmigungsfunktion Analyse](#genehmigungsfunktion)
6. [Resturlaub-Berechnung Analyse](#resturlaub-berechnung)
7. [Frontend-JavaScript Analyse](#frontend)
8. [Empfohlene Fixes](#fixes)

---

## 🏗️ ARCHITEKTUR-ÜBERSICHT {#architektur}

### Dateien-Struktur

```
api/
├── vacation_api.py              # Haupt-API (2968 Zeilen)
├── vacation_approver_service.py # Genehmiger-Logik (AD-basiert)
├── vacation_admin_api.py        # Admin-Funktionen
├── vacation_chef_api.py        # Chef-Funktionen
├── vacation_locosoft_service.py # Locosoft-Integration
└── vacation_calendar_service.py # Kalender-Integration

templates/
├── urlaubsplaner.html          # Legacy
├── urlaubsplaner_v2.html       # Aktuelle Version
├── urlaubsplaner_chef.html     # Chef-View
└── urlaubsplaner_admin.html    # Admin-View
```

### API-Endpunkte

| Endpunkt | Methode | Funktion | Status |
|----------|---------|----------|--------|
| `/api/vacation/approve` | POST | Urlaub genehmigen | ❌ **BUG** |
| `/api/vacation/reject` | POST | Urlaub ablehnen | ✅ OK |
| `/api/vacation/book` | POST | Urlaub buchen | ⚠️ **Teilweise** |
| `/api/vacation/pending-approvals` | GET | Offene Anträge | ❌ **BUG** |
| `/api/vacation/my-team` | GET | Team-Übersicht | ❌ **BUG** |
| `/api/vacation/my-balance` | GET | Persönlicher Stand | ⚠️ **Teilweise** |

---

## 🚨 KRITISCHE BUGS GEFUNDEN {#kritische-bugs}

### 1. **SQLite-Syntax in PostgreSQL-Code** ❌ KRITISCH

**Problem:** SQLite-Placeholders (`?`) werden noch verwendet statt PostgreSQL (`%s`)

**Betroffene Dateien:**

#### `api/vacation_api.py`

**Zeile 1005:**
```python
placeholders = ','.join('?' * len(team_ids))  # ❌ SQLite-Syntax!
```

**Zeile 1144:**
```python
placeholders = ','.join('?' * len(team_ids))  # ❌ SQLite-Syntax!
```

**Zeile 2233:**
```python
cursor.execute("""
    SELECT ad_groups FROM users
    WHERE username LIKE ? OR username = %s  # ❌ Gemischte Syntax!
""", (f"%{ldap_username}%", ldap_username))
```

**Impact:**
- ❌ Queries schlagen fehl mit PostgreSQL
- ❌ `pending-approvals` funktioniert nicht
- ❌ `my-team` funktioniert nicht
- ❌ Genehmigungsfunktion kann Team nicht laden

**Fix:**
```python
# Statt:
placeholders = ','.join('?' * len(team_ids))

# Sollte sein:
placeholders = ','.join(['%s'] * len(team_ids))
```

---

#### `api/vacation_admin_api.py`

**Zeile 211:**
```python
cursor.execute("""
    INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)  # ❌ SQLite-Syntax!
    ON CONFLICT(employee_id, year) DO UPDATE SET
        total_days = excluded.total_days,
        carried_over = excluded.carried_over,
        added_manually = excluded.added_manually,
        updated_at = CURRENT_TIMESTAMP
""", (employee_id, year, anspruch, uebertrag, korrektur))
```

**Zeile 271:**
```python
cursor.execute("""
    INSERT INTO vacation_entitlements (employee_id, year, total_days, carried_over, added_manually, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)  # ❌ SQLite-Syntax!
    ON CONFLICT(employee_id, year) DO UPDATE SET
        total_days = excluded.total_days,
        carried_over = excluded.carried_over,
        added_manually = excluded.added_manually,
        updated_at = CURRENT_TIMESTAMP
""", (employee_id, year, anspruch, uebertrag, korrektur))
```

**Impact:**
- ❌ Admin kann Urlaubsansprüche nicht aktualisieren
- ❌ Bulk-Updates schlagen fehl

**Fix:**
```python
# Statt:
VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

# Sollte sein:
VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
```

---

### 2. **Genehmigungsfunktion - Team-Validierung fehlt** ❌ KRITISCH

**Datei:** `api/vacation_api.py`  
**Zeile:** 1202-1318

**Problem:**
```python
@vacation_api.route('/approve', methods=['POST'])
def approve_vacation():
    # ...
    team_members = get_team_for_approver(ldap_username)
    team_ids = [m['employee_id'] for m in team_members]  # ⚠️ Kann leer sein!
    
    # ...
    if booking[0] not in team_ids:  # ❌ Wenn team_ids leer, wird IMMER 403 zurückgegeben!
        return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
```

**Szenario:**
1. User ist Genehmiger (z.B. `christian.aichinger`)
2. `get_team_for_approver()` gibt leere Liste zurück (z.B. wegen AD-Problem)
3. `team_ids = []` (leer)
4. `if booking[0] not in []` → **IMMER True** → **403 Fehler**

**Impact:**
- ❌ Genehmigungen schlagen immer fehl wenn Team leer ist
- ❌ Admin kann nicht genehmigen wenn Team-Ermittlung fehlschlägt

**Fix:**
```python
team_members = get_team_for_approver(ldap_username)
team_ids = [m['employee_id'] for m in team_members]

# Admin-Bypass hinzufügen
is_admin = is_vacation_admin(ldap_username)

if not is_admin:
    if not team_ids:
        return jsonify({'success': False, 'error': 'Kein Team zugeordnet'}), 403
    
    if booking[0] not in team_ids:
        return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
```

---

### 3. **Falsche Tage-Markierung - Frontend-Bug** ❌ KRITISCH

**Datei:** `templates/urlaubsplaner_v2.html`  
**Zeile:** 1305-1317

**Problem:**
```javascript
async function doApprove() {
    const r = await api('/approve', 'POST', {booking_id: approveId});  // ⚠️ approveId könnte falsch sein!
    // ...
}
```

**Vermutung:**
- `approveId` wird in `showApprove()` gesetzt
- Wenn falscher Kontext (z.B. Edith Egner → Christian Aichinger), wird falsche ID verwendet
- Frontend zeigt falsche Person an, sendet aber korrekte `booking_id`

**Impact:**
- ❌ Falsche Tage werden markiert
- ❌ Genehmigung für falsche Person

**Zu prüfen:**
- Wie wird `approveId` gesetzt?
- Wird die richtige `employee_id` verwendet?

---

### 4. **Resturlaub-Berechnung - Wird nicht aktualisiert** ❌ KRITISCH

**Datei:** `api/vacation_api.py`  
**Zeile:** 1968-2050

**Problem:**
- Resturlaub wird bei Buchung **validiert** (Zeile 2044-2050)
- Aber nach Genehmigung wird Resturlaub **nicht neu berechnet**
- View `v_vacation_balance_{year}` wird nicht aktualisiert

**Aktueller Flow:**
1. User bucht Urlaub → Status: `pending`
2. Resturlaub wird validiert (OK)
3. Genehmiger genehmigt → Status: `approved`
4. **Resturlaub wird NICHT neu berechnet!**

**Impact:**
- ❌ Resturlaub zeigt falsche Werte nach Genehmigung
- ❌ Urlaubstage werden nicht vom Anspruch abgezogen
- ❌ View wird nicht aktualisiert

**Fix:**
- Nach Genehmigung: View neu berechnen oder Trigger erstellen
- Oder: Resturlaub dynamisch berechnen (nicht aus View)

---

### 5. **Jahreswechsel-Logik fehlt** ❌ KRITISCH

**Problem:**
- Keine automatische Reset-Logik für neues Jahr
- `vacation_entitlements` für neues Jahr wird nicht automatisch erstellt
- View `v_vacation_balance_{year}` wird nicht für neues Jahr erstellt

**Impact:**
- ❌ Januar 2027 zeigt noch 2026-Daten
- ❌ Urlaubsanspruch wird nicht zurückgesetzt

**Fix:**
- Celery-Task für Jahreswechsel erstellen
- Oder: Automatische Erstellung bei erstem Zugriff

---

## 🔄 SQLITE→POSTGRESQL MIGRATIONS-PROBLEME {#migrations-probleme}

### Gefundene SQLite-Syntax (sollte PostgreSQL sein):

| Datei | Zeile | Problem | Fix |
|-------|-------|---------|-----|
| `vacation_api.py` | 1005 | `placeholders = ','.join('?' * len(team_ids))` | `','.join(['%s'] * len(team_ids))` |
| `vacation_api.py` | 1144 | `placeholders = ','.join('?' * len(team_ids))` | `','.join(['%s'] * len(team_ids))` |
| `vacation_api.py` | 2233 | `WHERE username LIKE ?` | `WHERE username LIKE %s` |
| `vacation_admin_api.py` | 211 | `VALUES (?, ?, ?, ?, ?, ...)` | `VALUES (%s, %s, %s, %s, %s, ...)` |
| `vacation_admin_api.py` | 271 | `VALUES (?, ?, ?, ?, ?, ...)` | `VALUES (%s, %s, %s, %s, %s, ...)` |

### Bereits korrigiert (PostgreSQL-Syntax):

✅ `convert_placeholders()` wird verwendet (Zeile 1277, 2008, 2030, etc.)  
✅ `sql_placeholder()` wird verwendet (Zeile 1272, 1273, etc.)  
✅ `%s` wird in den meisten Queries verwendet

**Problem:** `convert_placeholders()` wird **nicht überall** verwendet!

---

## 🔧 REFACTORING-PROBLEME {#refactoring-probleme}

### 1. **Team-Ermittlung über AD**

**Datei:** `api/vacation_approver_service.py`

**Problem:**
- Team wird über AD `manager`-Attribut ermittelt
- Wenn AD nicht verfügbar → leeres Team
- Kein Fallback auf alte `vacation_approval_rules`

**Impact:**
- ❌ Genehmiger können kein Team sehen wenn AD-Problem
- ❌ Keine Genehmigungen möglich

**Fix:**
- Fallback auf `vacation_approval_rules` wenn AD fehlschlägt
- Oder: Besseres Error-Handling

---

### 2. **Berechtigungsprüfung inkonsistent**

**Problem:**
- `is_approver()` prüft AD-Gruppen
- `is_vacation_admin()` prüft Portal-Rolle + AD-Gruppen
- Inkonsistente Prüfungen an verschiedenen Stellen

**Impact:**
- ❌ Admin kann nicht genehmigen wenn Portal-Rolle nicht gesetzt
- ❌ Genehmiger-Rollen funktionieren nicht

---

### 3. **View-Abhängigkeit**

**Problem:**
- Code verwendet `v_vacation_balance_{year}` View
- View muss für jedes Jahr existieren
- View wird nicht automatisch erstellt

**Impact:**
- ❌ Neues Jahr → View fehlt → Fehler
- ❌ Resturlaub kann nicht berechnet werden

---

## 🔍 GENEHMIGUNGSFUNKTION ANALYSE {#genehmigungsfunktion}

### Code-Flow:

```python
@vacation_api.route('/approve', methods=['POST'])
def approve_vacation():
    1. get_employee_from_session()  # ✅ OK
    2. is_approver(ldap_username)    # ✅ OK (prüft AD-Gruppen)
    3. get_team_for_approver(ldap_username)  # ⚠️ Kann leer sein!
    4. team_ids = [m['employee_id'] for m in team_members]  # ⚠️ Leer wenn Team leer
    5. booking = cursor.fetchone()  # ✅ OK
    6. if booking[0] not in team_ids:  # ❌ IMMER True wenn team_ids leer!
         return 403
    7. UPDATE vacation_bookings SET status = 'approved'  # ✅ OK
```

### Probleme:

1. **Team-Validierung zu strikt:**
   - Wenn `team_ids` leer → IMMER 403
   - Admin sollte trotzdem genehmigen können

2. **Keine Admin-Bypass:**
   - Admin (`GRP_Urlaub_Admin`) sollte alle genehmigen können
   - Aktuell: Admin braucht auch Team

3. **Fehlerhafte Fehlermeldung:**
   - "Keine Berechtigung für diese Buchung" ist nicht hilfreich
   - Sollte sagen: "Team leer" oder "Nicht in Team"

### Fix-Vorschlag:

```python
@vacation_api.route('/approve', methods=['POST'])
def approve_vacation():
    # ...
    is_admin = is_vacation_admin(ldap_username)
    team_members = get_team_for_approver(ldap_username)
    team_ids = [m['employee_id'] for m in team_members]
    
    # Admin kann alle genehmigen
    if not is_admin:
        if not team_ids:
            return jsonify({
                'success': False, 
                'error': 'Kein Team zugeordnet. Bitte Admin kontaktieren.'
            }), 403
        
        if booking[0] not in team_ids:
            return jsonify({
                'success': False, 
                'error': f'Keine Berechtigung für diese Buchung. Team-Größe: {len(team_ids)}'
            }), 403
```

---

## 📊 RESTURLAUB-BERECHNUNG ANALYSE {#resturlaub-berechnung}

### Berechnungs-Logik:

**View:** `v_vacation_balance_{year}`

```sql
resturlaub = anspruch - verbraucht - geplant
```

**Problem:**
- `geplant` = Summe aller `pending` + `approved` Buchungen
- Nach Genehmigung wird View **nicht neu berechnet**
- View ist statisch, wird nicht aktualisiert

### Aktueller Flow:

1. **Buchung:** Status `pending` → `geplant` wird erhöht
2. **Genehmigung:** Status `approved` → `geplant` bleibt gleich (sollte zu `verbraucht`)
3. **Resturlaub:** Wird nicht neu berechnet

### Fix-Vorschlag:

**Option 1: View dynamisch machen (Materialized View)**
```sql
CREATE MATERIALIZED VIEW v_vacation_balance_2026 AS
SELECT
    employee_id,
    anspruch,
    verbraucht,
    geplant,
    anspruch - verbraucht - geplant as resturlaub
FROM ...
```

**Option 2: Trigger nach UPDATE**
```sql
CREATE TRIGGER update_vacation_balance
AFTER UPDATE ON vacation_bookings
FOR EACH ROW
WHEN NEW.status = 'approved' AND OLD.status = 'pending'
EXECUTE FUNCTION recalculate_balance();
```

**Option 3: Resturlaub dynamisch berechnen (aktuell in Code)**
```python
# Bereits implementiert in get_my_balance() (Zeile 908-910)
balance['resturlaub_korrigiert'] = round(
    balance['anspruch'] - locosoft_absences.get('urlaub', 0), 1
)
```

**Problem:** `resturlaub_korrigiert` wird nur in `my-balance` verwendet, nicht überall!

---

## 🎨 FRONTEND-JAVASCRIPT ANALYSE {#frontend}

### Genehmigungs-Funktion:

**Datei:** `templates/urlaubsplaner_v2.html`  
**Zeile:** 1295-1317

```javascript
function showApprove(id, name) {
    approveId = id;  // ⚠️ id = booking_id
    document.getElementById('approveInfo').textContent = `${name} - ${fmtD(date)}`;
    new bootstrap.Modal(document.getElementById('approveModal')).show();
}

async function doApprove() {
    const r = await api('/approve', 'POST', {booking_id: approveId});
    // ...
}
```

**Problem:**
- `approveId` wird aus Kontext gesetzt
- Wenn falscher Kontext (z.B. falsche Person angezeigt), wird falsche ID verwendet

**Zu prüfen:**
- Wie wird `showApprove()` aufgerufen?
- Wird die richtige `booking_id` übergeben?

---

## ✅ EMPFOHLENE FIXES {#fixes}

### Priorität 1 (KRITISCH - Sofort):

1. **SQLite-Syntax fixen:**
   - `vacation_api.py` Zeile 1005, 1144, 2233
   - `vacation_admin_api.py` Zeile 211, 271

2. **Genehmigungsfunktion - Admin-Bypass:**
   - Admin sollte alle genehmigen können
   - Team-Validierung nur für normale Genehmiger

3. **Team-Validierung verbessern:**
   - Bessere Fehlermeldungen
   - Fallback wenn Team leer

### Priorität 2 (HOCH - Diese Woche):

4. **Resturlaub-Berechnung:**
   - View nach Genehmigung neu berechnen
   - Oder: Dynamische Berechnung überall verwenden

5. **Jahreswechsel-Logik:**
   - Automatische Erstellung von `vacation_entitlements` für neues Jahr
   - View für neues Jahr automatisch erstellen

6. **Frontend-Bug - Falsche Tage:**
   - Prüfen wie `approveId` gesetzt wird
   - Sicherstellen dass richtige `booking_id` verwendet wird

### Priorität 3 (MITTEL - Nächste Woche):

7. **Berechtigungsprüfung konsolidieren:**
   - Zentrale Funktion für alle Berechtigungen
   - Konsistente Prüfungen

8. **Error-Handling verbessern:**
   - Bessere Fehlermeldungen
   - Logging für Debugging

---

## 📝 NÄCHSTE SCHRITTE

1. ✅ **Code-Analyse abgeschlossen**
2. ⏳ **Fixes implementieren** (Priorität 1)
3. ⏳ **Tests durchführen**
4. ⏳ **User-Test wiederholen**

---

**Status:** 🔴 **KRITISCH - Mehrere Bugs gefunden, die die Funktionalität blockieren**
