# Urlaubsplaner Genehmigungsprozess - Debug Analyse TAG 167

**Datum:** 2026-01-05  
**Problem:** Matthias K darf Urlaub von Edith nicht genehmigen  
**Status:** 🔍 Analyse in Arbeit

---

## Problembeschreibung

**User-Bericht:**
- Matthias K versucht Urlaub von Edith zu genehmigen
- Genehmigung schlägt fehl
- UI zeigt möglicherweise Genehmigungs-Button an, obwohl keine Berechtigung besteht

---

## System-Architektur

### Genehmigungslogik (AD-Manager-basiert)

**Version:** 3.0 - TAG 107  
**Basis:** AD `manager`-Attribut

**Flow:**
1. **Team-Ermittlung:** `get_team_for_approver(ldap_username)`
   - Normaler Genehmiger: Team = alle MA wo `AD manager = dieser User`
   - Admin: Team = ALLE aktiven MA
   
2. **Pending Approvals:** `/api/vacation/pending-approvals`
   - Filtert nur Anträge von Team-Mitgliedern
   - Zeigt nur `status = 'pending'` Buchungen
   
3. **Genehmigung:** `/api/vacation/approve`
   - Prüft: `is_approver(ldap_username)` ✅
   - Prüft: `booking.employee_id IN team_ids` ✅
   - Fehler: "Keine Berechtigung für diese Buchung" wenn nicht im Team

---

## Mögliche Ursachen

### 1. AD-Manager-Struktur falsch
**Problem:** Edith's Manager in AD ist nicht Matthias K

**Prüfung:**
- Edith Egner: employee_id 4003, Landau, Abteilung "Kundenzentrale"
- Matthias König: Serviceleiter, Deggendorf
- **Vermutung:** Edith's Manager ist wahrscheinlich jemand anderes (z.B. Filialleitung Landau)

**Lösung:**
- AD-Struktur prüfen
- Manager-Attribut korrigieren falls nötig

### 2. UI zeigt falsche Anträge
**Problem:** UI zeigt Genehmigungs-Buttons für Anträge, die nicht genehmigt werden können

**Prüfung:**
- `loadAppr()` lädt `/pending-approvals`
- Zeigt alle zurückgegebenen Anträge an
- **Vermutung:** Wenn Backend fälschlicherweise Edith's Antrag zurückgibt, wird Button angezeigt

**Lösung:**
- Backend-Filter prüfen
- UI-Validierung hinzufügen (zusätzliche Sicherheit)

### 3. Backend-Validierung korrekt, aber UI-Filter fehlerhaft
**Problem:** Backend filtert korrekt, aber UI zeigt trotzdem falsche Anträge

**Prüfung:**
- `/pending-approvals` filtert korrekt
- `/approve` validiert korrekt
- **Vermutung:** UI zeigt Anträge aus anderer Quelle (z.B. `/all-bookings`)

**Lösung:**
- UI-Logik prüfen
- Sicherstellen dass nur `/pending-approvals` für Genehmigungen verwendet wird

---

## Code-Analyse

### Backend: `/api/vacation/pending-approvals`

```python
# Zeile 1134: Team-Ermittlung
team_members = get_team_for_approver(ldap_username)

# Zeile 1143: Team-IDs extrahieren
team_ids = [m['employee_id'] for m in team_members]

# Zeile 1163: Nur Anträge von Team-Mitgliedern
WHERE vb.employee_id IN ({placeholders})
```

**✅ Korrekt:** Filtert nur Team-Mitglieder

### Backend: `/api/vacation/approve`

```python
# Zeile 1232: Team-Ermittlung
team_members = get_team_for_approver(ldap_username)
team_ids = [m['employee_id'] for m in team_members]

# Zeile 1261: Validierung
if booking[0] not in team_ids:
    return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
```

**✅ Korrekt:** Validiert Team-Mitgliedschaft

### Frontend: `loadAppr()`

```javascript
// Zeile 663: Lade pending approvals
const r = await api('/pending-approvals');

// Zeile 668: Zeige alle zurückgegebenen Anträge
r.pending.forEach(p => {
    // Zeile 672: Genehmigungs-Button
    <button onclick="showApprove(${p.booking_id},...)">OK</button>
});
```

**⚠️ Potentielles Problem:** Zeigt alle Anträge an, die Backend zurückgibt

---

## Debug-Schritte

### 1. AD-Manager-Struktur prüfen

**Test-Script:**
```python
# In vacation_approver_service.py ausführen
ad_users = get_ad_users_with_manager()
edith_ad = ad_users.get('edith.egner')
matthias_team = get_team_for_approver('matthias.koenig')

print(f"Edith's Manager: {edith_ad.get('manager_username')}")
print(f"Matthias Team: {[m['name'] for m in matthias_team]}")
```

**Erwartung:**
- Wenn Edith's Manager != Matthias K → Problem erklärt
- Wenn Edith nicht in Matthias Team → Problem erklärt

### 2. Backend-Logging aktivieren

**Hinzufügen:**
```python
# In get_team_for_approver()
logger.info(f"Team für {approver_ldap_username}: {[m['name'] for m in team]}")

# In approve_vacation()
logger.info(f"Genehmigung: {ldap_username} versucht {booking_id} zu genehmigen")
logger.info(f"Team-IDs: {team_ids}, Booking-Employee-ID: {booking[0]}")
```

### 3. UI-Debug-Info hinzufügen

**Hinzufügen:**
```javascript
// In loadAppr()
console.log('Pending Approvals:', r.pending);
console.log('Team-Mitglieder:', r.approver?.team);
```

---

## Empfohlene Fixes

### Fix 1: UI-Validierung hinzufügen (Defensive Programming)

**Datei:** `templates/urlaubsplaner_v2.html`

**Änderung:**
```javascript
async function loadAppr() {
    const r = await api('/pending-approvals');
    if (r.success && r.pending?.length) {
        // Zusätzliche Validierung: Nur Anträge anzeigen die genehmigt werden können
        const validPending = r.pending.filter(p => {
            // Prüfe ob employee_id im Team ist
            return r.approver?.team_ids?.includes(p.employee_id) ?? true;
        });
        
        if (validPending.length !== r.pending.length) {
            console.warn('⚠️ Einige Anträge wurden gefiltert (keine Berechtigung)');
        }
        
        // Zeige nur validPending
        document.getElementById('apprCnt').textContent = validPending.length;
        // ... rest
    }
}
```

### Fix 2: Backend-Logging verbessern

**Datei:** `api/vacation_api.py`

**Änderung:**
```python
@vacation_api.route('/approve', methods=['POST'])
def approve_vacation():
    # ... existing code ...
    
    team_members = get_team_for_approver(ldap_username)
    team_ids = [m['employee_id'] for m in team_members]
    
    # DEBUG: Logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Genehmigung: {ldap_username} versucht booking_id={booking_id} zu genehmigen")
    logger.info(f"Team-IDs: {team_ids}, Booking-Employee-ID: {booking[0]}")
    
    if booking[0] not in team_ids:
        logger.warning(f"❌ Genehmigung verweigert: {ldap_username} darf {booking[0]} nicht genehmigen")
        return jsonify({'success': False, 'error': 'Keine Berechtigung für diese Buchung'}), 403
```

### Fix 3: Bessere Fehlermeldung

**Datei:** `api/vacation_api.py`

**Änderung:**
```python
if booking[0] not in team_ids:
    # Hole Employee-Name für bessere Fehlermeldung
    cursor.execute("SELECT first_name || ' ' || last_name FROM employees WHERE id = %s", (booking[0],))
    employee_name = cursor.fetchone()[0] if cursor.fetchone() else "Unbekannt"
    
    return jsonify({
        'success': False, 
        'error': f'Keine Berechtigung: Sie können Urlaub von {employee_name} nicht genehmigen. Bitte prüfen Sie die AD-Manager-Struktur.'
    }), 403
```

---

## Nächste Schritte

1. ✅ **AD-Struktur prüfen:** Wer ist Edith's Manager?
2. ✅ **Backend-Logging aktivieren:** Detaillierte Logs für Genehmigungen
3. ✅ **UI-Validierung hinzufügen:** Defensive Programming
4. ✅ **Fehlermeldungen verbessern:** Klarere Fehlermeldungen für User
5. ⏳ **Test:** Genehmigung mit Matthias K und Edith testen

---

## Status

- [x] Problem analysiert
- [ ] AD-Struktur geprüft
- [ ] Backend-Logging aktiviert
- [ ] UI-Validierung hinzugefügt
- [ ] Fix getestet

---

**Nächste Aktion:** AD-Struktur prüfen und Fixes implementieren

---

## ZUSÄTZLICHES PROBLEM: Urlaubsansprüche fehlen (TAG 167)

**Problem:** Alle Mitarbeiter zeigen "0" Tage Urlaubsanspruch

**Ursache:** View `v_vacation_balance_2025` verwendet SQLite-Syntax (`strftime('%Y', ...)`) statt PostgreSQL (`EXTRACT(YEAR FROM ...)`)

**Lösung:**
1. ✅ PostgreSQL-kompatible View erstellt: `scripts/migrations/fix_vacation_balance_view_postgresql.sql`
2. ⏳ View auf Server ausführen
3. ⏳ Prüfen ob `vacation_entitlements` Daten vorhanden sind

**Dateien:**
- `scripts/migrations/fix_vacation_balance_view_postgresql.sql` - View-Fix
- `scripts/checks/check_vacation_entitlements.py` - Diagnose-Script

