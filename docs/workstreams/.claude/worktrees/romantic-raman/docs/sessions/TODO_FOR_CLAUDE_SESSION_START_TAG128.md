# TODO FOR CLAUDE - SESSION START TAG 128

**Erstellt:** 2025-12-19
**Vorherige Session:** TAG 127

---

## Kontext aus TAG 127

### Abgeschlossen:
1. **Admin-Direktbuchung Urlaubsplaner** - Admins können in fremden Zeilen klicken, Buchung ist sofort genehmigt
2. **AD-Department-Sync Fix** - Nutzt jetzt `ldap_username` aus Mapping-Tabelle
3. **Locosoft-Sync schützt LDAP-Abteilungen** - Überschreibt nicht mehr AD-Departments

### Sync-Architektur:
- `sync_employees` (06:00): Locosoft → SQLite (Department NUR ohne LDAP-Mapping)
- `sync_ad_departments` (06:20): AD → SQLite (überschreibt mit AD-Department)
- **AD ist Master für Abteilungen!**

---

## Offene Punkte

### 1. Daniel Thammer - AD-Department fehlt
- Hat im Active Directory kein `department`-Attribut
- Muss von IT/Admin in AD gepflegt werden
- Danach greift automatischer Sync

### 2. Produktivtest Admin-Buchung
- Florian Greiner soll Admin-Direktbuchung testen
- Prüfen: Sofortige Genehmigung, HR-Info-Mail

### 3. Portal-Abwesenheiten in Werkstatt
- TAG 127 hat `get_portal_absences()` in `db_utils.py` implementiert
- Werkstatt-Liveboard sollte Portal-ZA/Krank anzeigen
- Testen ob Integration funktioniert

---

## Wichtige Dateien (TAG 127)

| Datei | Zweck |
|-------|-------|
| `api/vacation_api.py` | Admin-Direktbuchung mit `for_employee_id` |
| `api/db_utils.py` | `get_portal_absences()` für Werkstatt |
| `scripts/sync/sync_ad_departments.py` | AD-Sync mit LDAP-Username-Matching |
| `scripts/sync/sync_employees.py` | Locosoft-Sync schützt LDAP-Departments |

---

## Git-Status

Letzter Commit: `feat(TAG127): Admin-Direktbuchung, AD-Sync-Fix, LDAP-Abteilungsschutz`
