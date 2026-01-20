# Urlaubsplaner Genehmigungsfunktion - Refactoring-Analyse TAG 198

**Datum:** 2026-01-19  
**Problem:** Genehmigungsfunktion war vorhanden, wurde aber bei Refactoring zerstört  
**Status:** Analyse und Prüfung

---

## 🔍 CODE-ANALYSE

### ✅ Backend-Funktionen vorhanden

1. **API-Endpoint:** `/api/vacation/approve` (POST)
   - Datei: `api/vacation_api.py` (Zeilen 1245-1382)
   - Funktion: `approve_vacation()`
   - Status: ✅ Vorhanden

2. **Berechtigungsprüfung:**
   - `is_approver()` aus `api/vacation_approver_service.py` (Zeile 419)
   - `is_vacation_admin()` für Admin-Bypass
   - Status: ✅ Vorhanden

3. **Team-Validierung:**
   - `get_team_for_approver()` aus `api/vacation_approver_service.py`
   - Admin-Bypass implementiert (TAG 198)
   - Status: ✅ Vorhanden

### ✅ Frontend-Funktionen vorhanden

1. **JavaScript-Funktionen:**
   - `showApprove(id, name, date)` - Zeigt Modal (Zeile 1363)
   - `doApprove()` - Ruft API auf (Zeile 1369)
   - Event-Listener registriert (Zeile 1455)
   - Status: ✅ Vorhanden

2. **UI-Elemente:**
   - Approve Modal vorhanden (Zeilen 535-553)
   - Button "Genehmigen" vorhanden (Zeile 549)
   - Status: ✅ Vorhanden

---

## 🐛 MÖGLICHE PROBLEME

### 1. Team-Validierung zu strikt

**Problem:** Die Team-Validierung könnte zu strikt sein und verhindert Genehmigungen.

**Code-Stelle:** `api/vacation_api.py` Zeilen 1307-1326

```python
# TAG 198: Team-Validierung nur für normale Genehmiger (nicht Admin)
if not is_admin:
    if not team_ids:
        return jsonify({
            'success': False, 
            'error': 'Kein Team zugeordnet. Bitte Admin kontaktieren.',
            ...
        }), 403
    
    if booking[0] not in team_ids:
        return jsonify({
            'success': False, 
            'error': f'Keine Berechtigung für diese Buchung. Team-Größe: {len(team_ids)}',
            ...
        }), 403
```

**Mögliche Ursachen:**
- `get_team_for_approver()` gibt leere Liste zurück
- Team-Mapping in AD nicht korrekt
- Manager-Attribut fehlt in AD

**Lösung:** Prüfen ob `get_team_for_approver()` korrekt funktioniert

---

### 2. `is_approver()` gibt False zurück

**Problem:** Die `is_approver()` Funktion könnte False zurückgeben, obwohl der User Genehmiger ist.

**Code-Stelle:** `api/vacation_approver_service.py` Zeilen 419-444

**Mögliche Ursachen:**
- AD-Gruppen nicht in `users.ad_groups` gespeichert
- Username-Mapping falsch
- LDAP-Abfrage schlägt fehl

**Lösung:** Prüfen ob AD-Gruppen korrekt geladen werden

---

### 3. Frontend-Event-Bindung

**Problem:** Event-Listener könnte nicht korrekt gebunden sein.

**Code-Stelle:** `templates/urlaubsplaner_v2.html` Zeile 1455

**Status:** ✅ Event-Listener ist registriert

---

### 4. API-Route nicht registriert

**Problem:** Blueprint könnte nicht korrekt registriert sein.

**Prüfung:**
- Blueprint: `vacation_api = Blueprint('vacation_api', __name__, url_prefix='/api/vacation')`
- Route: `@vacation_api.route('/approve', methods=['POST'])`
- Status: ✅ Korrekt definiert

---

## 🔧 DEBUGGING-SCHRITTE

### 1. Backend-Logs prüfen

```bash
journalctl -u greiner-portal -f | grep -i "approve\|genehmig"
```

### 2. Browser-Console prüfen

- Network-Tab: Prüfen ob `/api/vacation/approve` aufgerufen wird
- Console: Prüfen ob JavaScript-Fehler vorhanden sind
- Response: Prüfen ob API-Fehler zurückgegeben wird

### 3. Berechtigungen prüfen

```python
# In Python-Shell testen:
from api.vacation_approver_service import is_approver, get_team_for_approver

# Test für einen Genehmiger:
ldap_username = "christian.aichinger"  # Beispiel
print(f"is_approver: {is_approver(ldap_username)}")
print(f"team: {get_team_for_approver(ldap_username)}")
```

### 4. API direkt testen

```bash
curl -X POST http://localhost:5000/api/vacation/approve \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"booking_id": 123}'
```

---

## 🎯 NÄCHSTE SCHRITTE

1. **Browser-Console prüfen:**
   - Öffne Browser-Entwicklertools
   - Prüfe Network-Tab beim Klick auf "Genehmigen"
   - Prüfe Console auf Fehler

2. **Backend-Logs prüfen:**
   - Prüfe ob API-Endpoint aufgerufen wird
   - Prüfe ob Fehler in Logs erscheinen

3. **Berechtigungen testen:**
   - Prüfe ob `is_approver()` für betroffene User True zurückgibt
   - Prüfe ob `get_team_for_approver()` korrekte Teams zurückgibt

4. **Team-Validierung lockern (falls nötig):**
   - Admin-Bypass sollte bereits funktionieren
   - Für normale Genehmiger: Prüfen ob Team-Mapping korrekt ist

---

## 📝 HINWEISE

- **Admin-Bypass:** Admins können alle Buchungen genehmigen (TAG 198)
- **Team-Validierung:** Nur für normale Genehmiger (nicht Admin)
- **Event-Listener:** Ist korrekt registriert
- **API-Route:** Ist korrekt definiert

**Vermutung:** Das Problem liegt wahrscheinlich in der Team-Validierung oder in der `is_approver()` Prüfung, nicht in der grundlegenden Funktionalität.
