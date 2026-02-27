# AD: Administrator raus – dedizierter DRIVE-Account mit minimalen Rechten

**Stand:** 2026-02-27  
**Ziel:** Den AD-Administrator (bzw. den aktuell verwendeten Account mit zu vielen Rechten) aus dem Portal-Betrieb und aus den gemounteten Laufwerken entfernen. Stattdessen einen **DRIVE-Benutzer** im AD anlegen, der nur die nötigen Rechte hat.

---

## 1. Wo wird heute ein AD-Account verwendet?

### 1.1 LDAP-Bind (Portal ↔ Active Directory)

**Konfiguration:** Eine zentrale Datei – `config/ldap_credentials.env`:

- `LDAP_BIND_DN` = Benutzer für die Verbindung zum AD (z. B. `svc_portal@auto-greiner.de`)
- `LDAP_BIND_PASSWORD` = Passwort

**Aktuell eingetragen:** `svc_portal@auto-greiner.de` (laut Config). Wenn dieser Account mit Administrator-Rechten oder sehr weitreichenden Rechten angelegt wurde, soll er durch einen eingeschränkten DRIVE-Account ersetzt werden.

**Alle Stellen im Code, die diesen Account nutzen** (sie lesen alle aus `ldap_credentials.env`, außer ein Script):

| Stelle | Verwendung |
|--------|------------|
| **auth/ldap_connector.py** | Bind mit `LDAP_BIND_DN` / `LDAP_BIND_PASSWORD` für: Login-Prüfung, `get_user_details` (u. a. department, groups), `search_users`, Passwortänderung (Self-Service, mit User-Passwort), `test_connection` |
| **api/vacation_approver_service.py** | Eigenes Einlesen von `ldap_credentials.env`; direkte LDAP-Verbindung für: Team/Genehmiger-Abfragen (User + manager, department, company) |
| **api/employee_sync_service.py** | Nutzt `get_ldap_connector()` → liest Config über ldap_connector; Sync LDAP → Portal (u. a. department_name) |
| **scripts/sync/sync_ldap_employees_pg.py** | Liest `ldap_credentials.env`; LDAP-Bind für Abgleich AD ↔ employees / ldap_employee_mapping |
| **scripts/sync/sync_ldap_employees.py** | Wie oben (LDAP-Bind aus Config) |
| **scripts/ldap_locosoft_matching_report.py** | Liest `ldap_credentials.env`; LDAP für Report |
| **scripts/checks/check_ad_urlaub_gruppen.py** | **Ausnahme:** Liest **nicht** die Config, sondern hat **LDAP_BIND_DN** und **LDAP_BIND_PASSWORD fest im Code** (svc_portal@..., Vollgas2026!). Sollte auf die Config umgestellt werden. |
| **scripts/archive/ldap_connector_root.py** | Archiv; liest Config (nur Referenz) |

**Fazit:** Ein einziger Account (LDAP_BIND_DN/ LDAP_BIND_PASSWORD) wird für alle LDAP-Funktionen des Portals genutzt. Wenn ihr diesen Account wechselt, reicht die Anpassung in **einer** Datei (`config/ldap_credentials.env`) – plus die **eine** Code-Anpassung im Script `check_ad_urlaub_gruppen.py`, damit es die Config nutzt statt Hardcoding.

---

### 1.2 Gemountete Laufwerke (Linux-Server ↔ Windows-Freigaben)

**Hintergrund:** Der Linux-Server mountet Windows-Freigaben (z. B. `\\Srvrdb01\...`) – z. B. für Sync `\\Srvrdb01\Allgemein\Greiner Portal\...` → `/mnt/greiner-portal-sync/`. Dafür wird ein **AD-Benutzer** für die SMB/CIFS-Anmeldung verwendet.

**Wo konfiguriert:** **Nicht im Portal-Repo.** Die Mount-Konfiguration liegt auf dem Server, z. B.:

- **/etc/fstab** (Eintrag mit `credentials=...` oder `username=...,password=...`), oder
- **systemd-Mount-Unit** (z. B. `/etc/systemd/system/mnt-greiner_portal_sync.mount`), oder
- Manuell: `sudo mount -t cifs ... -o username=...,domain=auto-greiner.de,...`

**Bekannt aus Doku (Session TAG6):** Für einen CIFS-Mount wurde früher explizit **`username=Administrator,domain=auto-greiner.de`** verwendet. Wenn das heute noch so ist (oder ein anderer „starker“ Account), soll auch hier ein eigener DRIVE-Account verwendet werden.

**Wichtig:**  
- Der Account für den **Mount** kann derselbe sein wie der für **LDAP** (z. B. ein gemeinsamer `svc_drive@auto-greiner.de`), sofern er sowohl LDAP-Rechte als auch Lese-/Schreibrechte auf die jeweiligen Freigaben hat.  
- Oder ihr legt **zwei** Accounts an: einen nur für LDAP (`svc_drive`), einen nur für Freigaben (`svc_drive_sync` o. ä.) – dann hat jeder nur die minimal nötigen Rechte.

---

## 2. Vorschlag: DRIVE-Account(s) im AD anlegen

### 2.1 Ein Account für alles (einfacher)

- **Name (Beispiel):** `svc_drive@auto-greiner.de` (Anzeigename z. B. „DRIVE Service“).
- **Rechte im AD:**
  - **LDAP (Portal):**
    - Benutzer lesen (sAMAccountName, displayName, mail, memberOf, department, company, title, manager, …)
    - Optional für künftiges Abteilungs-Tool: **Schreiben** des Attributs **`department`** auf Benutzerobjekte (nur dieses Attribut, keine anderen).
  - **Passwortänderung:** Das Portal ändert User-Passwörter, indem sich der **User selbst** mit altem Passwort bindet und `unicodePwd` setzt – dafür braucht der **Service-Account** keine Passwort-Admin-Rechte.
  - **Freigaben (Mount):** Lese- und Schreibrecht auf die genutzten Freigaben (z. B. `\\Srvrdb01\...\Server\` bzw. die konkrete Freigabe, die nach `/mnt/greiner-portal-sync` gemountet wird).

Dann:

- **LDAP:** In `config/ldap_credentials.env` nur `LDAP_BIND_DN` und `LDAP_BIND_PASSWORD` auf `svc_drive@...` und das neue Passwort umstellen.
- **Mount:** In der Mount-Konfiguration auf dem Server (fstab bzw. systemd) `username=` (und ggf. Passwort-Datei) auf `svc_drive` umstellen; **Administrator** entfernen.

### 2.2 Zwei Accounts (strikte Trennung)

- **svc_drive@auto-greiner.de**  
  - Nur für **LDAP**: Lesen wie oben, optional Schreiben nur `department`.  
  - Wird nur in `config/ldap_credentials.env` eingetragen.  
  - Keine Freigaben-Rechte nötig.

- **svc_drive_sync@auto-greiner.de** (oder anderer Name)  
  - Nur für **SMB/CIFS-Mount**: Lese-/Schreibrecht auf die Sync-Freigabe(n).  
  - Wird nur in der Mount-Konfiguration auf dem Server eingetragen (fstab/systemd/credentials-Datei).  
  - Keine LDAP-Rechte nötig.

Vorteil: Minimale Rechte pro Zweck. Nachteil: Zwei Accounts und zwei Passwörter zu pflegen.

---

## 3. Konkrete Schritte (Administrator raus, DRIVE-Account rein)

### Schritt 1: AD – DRIVE-Account(s) anlegen und Rechte setzen

1. Im AD einen (oder zwei) Benutzer anlegen, z. B. `svc_drive` (und ggf. `svc_drive_sync`).
2. **LDAP-Account (`svc_drive`):**
   - Delegation/Rechte so setzen, dass dieser Account:
     - unter der gewünschten Base/OU **Benutzer lesen** kann (alle für Portal/Genehmiger/Sync genutzten Attribute);
     - optional: nur das Attribut **`department`** an Benutzerobjekten **ändern** darf (für Abteilungs-Tool).
   - Keine Domain-Admin- oder Administrator-Rechte.
3. **Mount-Account** (falls getrennt): Nur Zugriff auf die jeweilige Freigabe; kein LDAP-Zugriff nötig.

### Schritt 2: Portal – nur LDAP-Bind umstellen

1. **config/ldap_credentials.env** (auf dem Server, nicht im Git):
   - `LDAP_BIND_DN=svc_drive@auto-greiner.de` (bzw. der gewählte Kontoname)
   - `LDAP_BIND_PASSWORD=<neues sicheres Passwort>`
2. **Kein anderer Code** muss geändert werden, weil alle anderen Stellen die Config lesen – **außer**:
3. **scripts/checks/check_ad_urlaub_gruppen.py:**  
   Derzeit sind `LDAP_BIND_DN` und `LDAP_BIND_PASSWORD` **fest im Script** eingetragen. Vorschlag: Script so umbauen, dass es dieselbe Config wie der Rest lädt (`config/ldap_credentials.env` oder über den ldap_connector), dann reicht die Umstellung in Schritt 2.1.

### Schritt 3: Mount – Administrator aus der Mount-Konfiguration entfernen

1. **Auf dem Linux-Server** die aktuelle Mount-Konfiguration prüfen:
   - `mount | grep -E 'srvrdb01|cifs|greiner'`
   - `cat /etc/fstab` (nach Einträgen für srvrdb01/greiner-portal-sync suchen)
   - `systemctl list-units --type=mount` und ggf. Unit-Dateien unter `/etc/systemd/system/*.mount`
2. **Credentials für den Mount:**  
   Wo steht aktuell `username=Administrator` (oder der alte Account)? Meist:
   - in **fstab** in der Option `credentials=/path/to/file` (dann in dieser Datei `username=...` und `password=...` anpassen), oder
   - direkt in der Unit-Datei als `Options=... username=...,password=...` (dann dort anpassen).
3. **Umstellen** auf den neuen Account (z. B. `svc_drive` oder `svc_drive_sync`):
   - Username auf den neuen AD-Benutzer setzen (z. B. `svc_drive` oder `svc_drive_sync`), Domain weiter `auto-greiner.de`.
   - Passwort in der Credentials-Datei bzw. in der Unit aktualisieren.
4. Mount testen:
   - `sudo umount /mnt/greiner-portal-sync` (oder der konkrete Mountpunkt)
   - `sudo mount /mnt/greiner-portal-sync` (bzw. den Eintrag aus fstab/systemd auslösen)
   - Prüfen, ob Lese-/Schreibzugriff auf die Sync-Pfade funktioniert.

Danach wird **Administrator** (bzw. der alte Account) in der Mount-Konfiguration nicht mehr verwendet.

### Schritt 4: Alten Account im AD einschränken oder stilllegen

- **svc_portal** (falls das der bisherige LDAP-Bind-Account war): Passwort ändern oder Account deaktivieren, sobald alles mit dem neuen Account läuft.
- **Administrator:** Wird nur noch für echte Admin-Aufgaben genutzt, nicht mehr für Portal-LDAP oder für den Sync-Mount.

---

## 4. Kurzüberblick

| Verwendung | Konfigurationsort | Aktuell (laut Doku/Config) | Ziel |
|------------|-------------------|-----------------------------|------|
| **LDAP-Bind (Portal)** | `config/ldap_credentials.env` | svc_portal@auto-greiner.de | svc_drive@auto-greiner.de (nur Lesen + optional Schreiben `department`) |
| **LDAP-Script (Check)** | scripts/checks/check_ad_urlaub_gruppen.py (hardcoded) | svc_portal + Passwort im Code | Umstellung auf Config-Datei, dann gleicher Account wie oben |
| **CIFS-Mount (Sync)** | Server: fstab oder systemd Mount-Unit + ggf. credentials-Datei | username=Administrator (laut alter Doku) | username=svc_drive (oder svc_drive_sync), Administrator entfernen |

---

## 5. Code-Anpassung (nur eine Stelle)

**Datei:** `scripts/checks/check_ad_urlaub_gruppen.py`

**Problem:** LDAP_BIND_DN und LDAP_BIND_PASSWORD sind fest im Script gesetzt; bei Account-Wechsel müsste man sie hier nochmal ändern und Passwörter im Code haben.

**Lösung:** Config aus `config/ldap_credentials.env` laden (analog zu `sync_ldap_employees_pg.py` oder `vacation_approver_service.py`) und damit verbinden. Dann reicht die Pflege in `ldap_credentials.env`; das Script nutzt automatisch den gleichen Account wie das Portal.

---

## 6. Laufwerke / Mounts – was ihr prüfen solltet

- **Welche Mounts** gibt es für Greiner/Portal? (z. B. `/mnt/greiner-portal-sync`, `/mnt/buchhaltung`?)
- **Wo** sind sie konfiguriert? (fstab, systemd, Cron-Skript?)
- **Welcher AD-Benutzer** steht dort aktuell? Wenn dort noch **Administrator** (oder ein anderer zu mächtiger Account) steht: durch den neuen DRIVE-Account (oder den separaten Sync-Account) ersetzen und Administrator aus der Konfiguration entfernen.

Die konkreten Pfade und Unit-Namen sind serverabhängig und stehen nicht im Portal-Repo; sie sollten einmal auf dem Server dokumentiert werden (z. B. in einer internen Betriebsdoku oder in `docs/` unter einem Stichwort „Mounts / Sync-Freigaben“).

---

**Zusammenfassung:**  
- **Portal:** Ein Account (`svc_drive`) mit minimalen LDAP-Rechten (Lesen + optional Schreiben `department`), eingetragen nur in `config/ldap_credentials.env`.  
- **Mount:** Dieselben Credentials oder ein zweiter Account nur für Freigaben; Konfiguration auf dem Server anpassen, Administrator entfernen.  
- **Code:** Nur `check_ad_urlaub_gruppen.py` auf Config-Umstellung anpassen, dann ist der Administrator aus dem Portal-Umfeld heraus und durch den DRIVE-Account ersetzt.
