# DRIVE-Features, die den AD-Account nutzen

**Stand:** 2026-02-27  
**AD-Account:** Konfiguration in `config/ldap_credentials.env` (`LDAP_BIND_DN`, `LDAP_BIND_PASSWORD`). Aktuell: **svc_portal@auto-greiner.de**.

Alle folgenden Features nutzen **diesen einen** Service-Account (kein Florian Greiner, kein Administrator im Code).

---

## 1. Zentrale Quelle

| Datei | Rolle |
|-------|--------|
| **auth/ldap_connector.py** | Liest `config/ldap_credentials.env`, stellt LDAP-Bind und alle AD-Abfragen bereit (Login, User-Details, Gruppen, Suche, Passwortänderung). |

---

## 2. Portal-Features (Laufzeit)

### Login & Session
| Feature | Datei | AD-Nutzung |
|---------|--------|------------|
| **Anmeldung** | auth/auth_manager.py | `ldap.authenticate_user()` (Bind mit User-Passwort), danach `ldap.get_user_details()` mit **Service-Account** für displayName, groups, title, department, company. |
| **Session-Refresh / Rollen** | auth/auth_manager.py | `get_user_details()` für Gruppen/Rollen-Aktualisierung. |
| **Passwort ändern (Profil)** | auth/auth_manager.py | User bindet sich selbst; Service-Account wird nur genutzt, um User-DN zu ermitteln (`get_user_details`), Passwort-Änderung macht der User mit eigenem Passwort. |

### Urlaubsplaner
| Feature | Datei | AD-Nutzung |
|---------|--------|------------|
| **Genehmiger-Erkennung** | api/vacation_approver_service.py | Eigene LDAP-Verbindung mit `ldap_credentials.env`; prüft ob User in Genehmiger-Gruppen ist (`is_approver`). |
| **Team des Genehmigers** | api/vacation_approver_service.py | `get_team_by_manager()`, `get_team_for_approver()` – liest AD: User, manager, department, company, memberOf. |
| **Balance / Chef-Übersicht / Genehmigen** | api/vacation_api.py, vacation_admin_api.py | Nutzen `is_approver()`, `get_team_for_approver()` → damit indirekt AD (Genehmiger-Gruppen, Team-Liste). |

### Mitarbeiterverwaltung & Sync
| Feature | Datei | AD-Nutzung |
|---------|--------|------------|
| **LDAP-Sync (einzelner MA)** | api/employee_sync_service.py | `get_ldap_connector().get_user_details()` → füllt department_name, email, title, company etc. aus AD. |
| **Sync-Vorschau / Voll-Sync** | api/employee_management_api.py | Ruft `sync_from_ldap`, `sync_preview`, `sync_full` aus employee_sync_service auf → nutzt LDAP get_user_details. |

### Organigramm / Abteilungen
| Feature | Datei | AD-Nutzung |
|---------|--------|------------|
| **Abteilungsliste** | api/organization_api.py | Liest `employees.department_name` aus der DB (kommt vorher aus AD per Sync). Kein direkter LDAP-Call in der Laufzeit – aber Datenherkunft ist AD. |

---

## 3. Scripts (manuell / Celery)

| Script | AD-Nutzung |
|--------|------------|
| **scripts/sync/sync_ldap_employees_pg.py** | Bind mit ldap_credentials.env; gleicht AD-User mit employees/ldap_employee_mapping ab. |
| **scripts/sync/sync_ldap_employees.py** | Wie oben (LDAP-Bind aus Config). |
| **scripts/sync/sync_ad_departments.py** | Nutzt `LDAPConnector()` (ldap_credentials.env); liest department aus AD, schreibt in employees.department_name. |
| **scripts/ldap_locosoft_matching_report.py** | Liest ldap_credentials.env; LDAP-Abfragen für Report (AD ↔ Locosoft). |
| **scripts/checks/check_ad_urlaub_gruppen.py** | Liest ldap_credentials.env; zeigt Urlaubs-Gruppen und GRP_* aus AD. |

---

## 4. Nicht im Einsatz (Archiv)

| Datei | Hinweis |
|-------|---------|
| scripts/archive/ldap_connector_root.py | Alte Version des Connectors; wird nicht von der App geladen. |

---

## 5. Mounts (Server, keine App)

Die CIFS-Mounts (z. B. `/mnt/greiner-portal-sync`, `/mnt/buchhaltung`) nutzen **dieselben** Zugangsdaten wie gewünscht aus **/root/.smbcredentials** (username=svc_portal, domain=auto-greiner.de). Das ist **kein** Zugriff aus dem Portal-Code, sondern aus dem Betriebssystem beim Mount. Einheitlich: **svc_portal** für LDAP und für alle genannten Mounts.

---

## 6. Kurz-Checkliste (ein Account für alles)

- **Login / Session / Passwort ändern** → auth_manager + ldap_connector (ldap_credentials.env).
- **Urlaubsplaner (Genehmiger, Team)** → vacation_approver_service (ldap_credentials.env), vacation_api.
- **Mitarbeiterverwaltung (Sync aus AD)** → employee_sync_service → ldap_connector.
- **Sync-Scripts (LDAP ↔ DB)** → sync_ldap_employees_pg, sync_ldap_employees, sync_ad_departments, ldap_locosoft_matching_report, check_ad_urlaub_gruppen.
- **Mounts** → /root/.smbcredentials (svc_portal).

Alle genannten Features hängen am **einen** AD-Account in `config/ldap_credentials.env` (und für Mounts an `/root/.smbcredentials`). Kein Feature verwendet im Code einen anderen AD-Benutzer (kein Florian Greiner, kein Administrator).
