# DRIVE-Service-Account: Rechte + Umstellung (ohne Florian Greiner / Administrator)

**Stand:** 2026-02-27  
**Ziel:** Ein technischer AD-Benutzer (den du schon angelegt hast) wird für **LDAP** und **alle Mounts** genutzt. Florian Greiner und Administrator sollen dafür nicht mehr verwendet werden. Danach testen, ob LDAP und alle Mounts funktionieren.

---

## 1. Welche Rechte braucht der Service-Account?

Du nutzt **einen** Account für beides (z. B. `svc_drive` oder wie du ihn genannt hast). Er braucht:

### 1.1 Rechte im Active Directory (für LDAP)

- **Benutzer lesen** (unter der OU, in der eure User liegen, z. B. `OU=AUTO-GREINER,DC=auto-greiner,DC=de`):
  - Attribute: `sAMAccountName`, `displayName`, `mail`, `memberOf`, `department`, `company`, `title`, `manager`, `userPrincipalName`, `distinguishedName`
- **Gruppen lesen**, die für Genehmiger/Urlaub genutzt werden (z. B. Gruppen mit „Urlaub“ oder `GRP_*` im Namen).
- **Optional (für späteres Abteilungs-Tool):** Nur das Attribut **`department`** an Benutzerobjekten **ändern** dürfen (keine anderen Attribute, kein Passwort, keine Gruppen ändern).

**Praktisch im AD:**  
Delegation auf die User-OU: dem Service-Account „Benutzerobjekte lesen“ (bzw. „Read all user information“) zuweisen. Für department-Schreiben: erweiterte Rechte / „Write department“ oder Delegation „Properties“ nur für Attribut `department`. **Keine** Domain-Admin- oder Administrator-Rechte.

### 1.2 Rechte auf den Windows-Freigaben (für Mounts)

Der Account muss **Lese- und Schreibzugriff** auf folgende Freigaben haben (wie bisher Florian Greiner bzw. Administrator):

| Freigabe (Server) | Pfad / Verwendung | Mountpunkt auf 10.80.80.20 |
|-------------------|-------------------|-----------------------------|
| **Srvrdb01** | `Allgemein` (Buchhaltung) | `/mnt/buchhaltung` |
| **Srvrdb01** | `Allgemein\Greiner Portal\Greiner_Portal_NEU\Server` | `/mnt/greiner-portal-sync` |
| **Srvrdb01** | `Allgemein\DigitalesAutohaus\Hyundai_Garantie` | `/mnt/hyundai-garantie` |
| **Srvrdb01** | `Allgemein\DigitalesAutohaus\Stellantis_Garantie` | `/mnt/stellantis-garantie` |
| **Srvloco01** | `Loco\LOCOAUSTAUSCH\...\Teilelieferscheine - XQ0093` | `/mnt/loco-teilelieferscheine` |
| **Srvloco01** | `Loco\BILDER` | `/mnt/loco-bilder` |
| **Srvgc01** | `GlobalCube` | `/mnt/globalcube` |

**Praktisch:** Auf jedem Windows-Server (Srvrdb01, Srvloco01, Srvgc01) die Freigabe öffnen → Freigabeberechtigungen und/oder NTFS-Berechtigungen so setzen, dass der Service-Account (z. B. `AUTO-GREINER\svc_drive`) **Ändern** bzw. **Lesen & Schreiben** hat – analog zu dem, was bisher für Florian Greiner oder Administrator gilt.

---

## 2. Umstellung – Anweisung für dich

**Voraussetzung:** Der Service-Account existiert im AD, hat die Rechte aus Abschnitt 1, und du kennst das Passwort.

Ersetze in den folgenden Schritten `svc_drive` durch den **tatsächlichen** Kontonamen (z. B. `svc_portal` behalten oder deinen neuen Namen).

---

### Schritt A: LDAP umstellen (Portal)

1. Auf dem Server einloggen: `ssh ag-admin@10.80.80.20`
2. Datei bearbeiten:
   ```bash
   sudo nano /opt/greiner-portal/config/ldap_credentials.env
   ```
3. Anpassen:
   - `LDAP_BIND_DN=svc_drive@auto-greiner.de`  (oder dein Kontoname)
   - `LDAP_BIND_PASSWORD=<Passwort des Service-Accounts>`
4. Speichern (Strg+O, Enter, Strg+X).
5. Portal neu starten:
   ```bash
   sudo systemctl restart greiner-portal
   ```

---

### Schritt B: Mounts umstellen (Server)

Aktuell:
- **Florian Greiner** wird über `/root/.smbcredentials` genutzt (fstab für greiner-portal-sync, loco-*, globalcube, hyundai-garantie, stellantis-garantie).
- **Administrator** wird nur für `/mnt/buchhaltung` verwendet (Mount aktuell nicht in fstab).

**B1 – Credentials-Datei für alle Mounts (ein Account)**

1. Backup der aktuellen Credentials:
   ```bash
   sudo cp /root/.smbcredentials /root/.smbcredentials.bak.$(date +%Y%m%d)
   ```
2. Credentials-Datei bearbeiten:
   ```bash
   sudo nano /root/.smbcredentials
   ```
3. Inhalt (nur diese drei Zeilen, ohne Leerzeilen am Ende):
   ```
   username=svc_drive
   password=<Passwort des Service-Accounts>
   domain=auto-greiner.de
   ```
   Ersetze `svc_drive` und das Passwort durch deine Werte.
4. Speichern. Rechte prüfen:
   ```bash
   sudo chmod 600 /root/.smbcredentials
   ```

**B2 – Alle CIFS-Mounts neu mounten**

1. Alle bestehenden CIFS-Mounts aushängen:
   ```bash
   sudo umount /mnt/greiner-portal-sync
   sudo umount /mnt/loco-teilelieferscheine
   sudo umount /mnt/globalcube
   sudo umount /mnt/hyundai-garantie
   sudo umount /mnt/loco-bilder
   sudo umount /mnt/stellantis-garantie
   sudo umount /mnt/buchhaltung
   ```
   (Falls einer „busy“ ist: keine Anwendung/Skripte in dem Mount nutzen, ggf. kurz warten und wiederholen.)

2. Alle aus fstab wieder mounten (damit sie die neuen Credentials aus `/root/.smbcredentials` nutzen):
   ```bash
   sudo mount /mnt/greiner-portal-sync
   sudo mount /mnt/loco-teilelieferscheine
   sudo mount /mnt/hyundai-garantie
   sudo mount /mnt/loco-bilder
   sudo mount /mnt/stellantis-garantie
   ```
   (globalcube steht nicht in der gezeigten fstab – falls er in fstab ist, ebenfalls `sudo mount /mnt/globalcube`.)

3. **Buchhaltung:** Ist aktuell **nicht** in fstab. Entweder:
   - **Option 1 (empfohlen):** Einmal mit dem neuen Account mounten und testen:
     ```bash
     sudo mount -t cifs //srvrdb01/Allgemein /mnt/buchhaltung -o credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=0,gid=0
     ```
     Wenn das funktioniert, für Dauerbetrieb in fstab eintragen (siehe unten „B3“).
   - **Option 2:** Erst nur LDAP und die anderen Mounts testen; Buchhaltung später umstellen.

**B3 – Buchhaltung dauerhaft in fstab (optional)**

Wenn du Buchhaltung wie die anderen Mounts über die gleiche Credentials-Datei laufen lassen willst:

```bash
sudo nano /etc/fstab
```

Neue Zeile am Ende (eine Zeile, ohne Backslash):

```
//srvrdb01/Allgemein /mnt/buchhaltung cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=0,gid=0,nofail 0 0
```

Speichern. Beim nächsten Boot wird `/mnt/buchhaltung` automatisch mit dem Service-Account gemountet. Jetzt testweise:

```bash
sudo mount /mnt/buchhaltung
```

---

## 3. Testen – Checkliste

### 3.1 LDAP

1. **Login im Portal:** Mit einem normalen User (z. B. Florian Greiner) unter http://drive anmelden → Login muss funktionieren.
2. **Urlaubsplaner / Genehmiger:** Seite öffnen, Mitarbeiterliste und ggf. Genehmiger-Ansicht laden → keine Fehlermeldung, Daten sichtbar.
3. **Mitarbeiterverwaltung:** Admin → Mitarbeiterverwaltung → Sync (LDAP) einmal ausführen oder Liste laden → Sync/Anzeige funktioniert.
4. **Optional (wenn du das Script nutzt):**
   ```bash
   cd /opt/greiner-portal && python3 scripts/checks/check_ad_urlaub_gruppen.py
   ```
   → Verbindung und Ausgabe ohne Fehler.

### 3.2 Mounts

Auf dem Server (10.80.80.20):

```bash
# Prüfen, ob alle gemountet sind
mount | grep cifs

# Kurz Lese-/Schreibtest (z. B. Portal-Sync)
ls -la /mnt/greiner-portal-sync/
touch /mnt/greiner-portal-sync/test_svc_drive_$(date +%Y%m%d) && rm /mnt/greiner-portal-sync/test_svc_drive_*
echo "greiner-portal-sync OK"

# Buchhaltung (falls umgestellt)
ls /mnt/buchhaltung/
# Optional Schreibtest in einem Unterordner, den der Account beschreiben darf
```

Alle genutzten Mountpunkte sollten sichtbar sein und (wo nötig) Lesen/Schreiben möglich sein.

---

## 4. Kurzüberblick

| Was | Vorher | Nachher |
|-----|--------|---------|
| **LDAP (Portal)** | svc_portal (oder alter Account) | Dein Service-Account (z. B. svc_drive) in `config/ldap_credentials.env` |
| **Mounts (fstab + /root/.smbcredentials)** | florian.greiner | Derselbe Service-Account in `/root/.smbcredentials` |
| **Mount /mnt/buchhaltung** | Administrator (manuell) | Derselbe Service-Account (credentials=/root/.smbcredentials), ggf. in fstab |

**Rechte des Service-Accounts:**  
- AD: User (und Gruppen) lesen, optional nur `department` schreiben.  
- Freigaben: Lese-/Schreibzugriff auf die genannten Shares auf Srvrdb01, Srvloco01, Srvgc01.

Nach Umstellung und Tests werden Florian Greiner und Administrator für LDAP und Mounts nicht mehr verwendet.
