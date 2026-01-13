# Referenz: Hardcodierte Werte im Code

**Zweck:** Schnelle Übersicht aller Dateien mit Greiner-spezifischen Werten

---

## 🔴 KRITISCHE DATEIEN (MUSS ANGEPASST WERDEN)

### 1. Datenbank & Locosoft

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `api/db_utils.py` | 100-105 | `10.80.80.8`, `loco_auswertung_benutzer`, `loco` | Deine Locosoft-DB |
| `utils/locosoft_helpers.py` | 49-54 | Locosoft-Env-Vars | Deine Locosoft-DB |
| `scripts/sync/bwa_berechnung.py` | 44-50 | `DrivePortal2024` | Dein DB-Passwort |

---

### 2. LDAP/Active Directory

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `auth/auth_manager.py` | 212 | `@auto-greiner.de` | Deine Domain |
| `auth/ldap_connector.py` | 139 | Domain-Extraktion | Deine Domain |

**Konfiguration:**
- `config/ldap_credentials.env` → Siehe `ldap_credentials.env.example`

---

### 3. Standort-Konfiguration

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `api/standort_utils.py` | 51-55 | `STANDORT_NAMEN` | Deine Standorte |
| `api/standort_utils.py` | 60-64 | `BETRIEB_NAMEN` | Deine Betriebe |
| `api/standort_utils.py` | 67-71 | `STANDORT_KUERZEL` | Deine Kürzel |
| `api/standort_utils.py` | 22-48 | `STANDORTE` Dict | Deine Struktur |

---

### 4. App-Namen & Domain

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `app.py` | 100 | `'Greiner Portal'` | Dein Portal-Name |

---

### 5. E-Mail-Konfiguration

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `celery_app/tasks.py` | 332 | `drive@auto-greiner.de` | Deine E-Mail |
| `celery_app/tasks.py` | 320 | `http://drive.auto-greiner.de/...` | Deine Portal-URL |
| `celery_app/tasks.py` | 324 | `Greiner DRIVE Portal` | Dein Portal-Name |
| `scripts/send_daily_tek.py` | - | E-Mail-Konfiguration | Deine E-Mail |

---

### 6. Serviceberater

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `api/serviceberater_api.py` | 136-146 | `SERVICEBERATER_CONFIG` | Deine Serviceberater |
| `celery_app/tasks.py` | 125-127 | Manager-IDs | Deine Manager-IDs |

---

### 7. Cognos (falls verwendet)

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `scripts/cognos_soap_client.py` | 20 | `http://10.80.80.10:9300` | Dein Cognos-Server |
| `scripts/cognos_soap_client.py` | 23 | `Greiner` | Dein Cognos-User |
| `scripts/cognos_soap_client.py` | 24 | `Hawaii#22` | Dein Cognos-Passwort |
| `scripts/cognos_soap_client.py` | 27 | Report-ID | Deine Report-ID |

---

### 8. Pfade

| Datei | Zeile | Wert | Zu ändern zu |
|-------|-------|------|--------------|
| `api/db_connection.py` | 185 | `/opt/greiner-portal/` | Dein Installationspfad |
| `celery_app/tasks.py` | 373, 376, etc. | `/opt/greiner-portal/` | Dein Installationspfad |

**Hinweis:** Falls Installationspfad gleich bleibt, kann dies ignoriert werden.

---

## 🟡 OPTIONAL - DOKUMENTATION

Die folgenden Dateien enthalten nur Dokumentation/Beispiele und müssen nicht angepasst werden:

- `docs/*.md` - Dokumentationsdateien
- `CLAUDE.md` - Entwickler-Dokumentation

---

## 🔍 SUCHBEFEHLE

### Alle Greiner-spezifischen Werte finden:

```bash
cd /opt/greiner-portal

# Domain
grep -r "auto-greiner" --include="*.py" --include="*.html"

# IP-Adressen
grep -r "10\.80\.80\." --include="*.py"

# Standorte
grep -r "Deggendorf\|Landau" --include="*.py" -i

# E-Mails
grep -r "drive@auto-greiner" --include="*.py"
```

---

## ✅ PRIORITÄTEN

**Höchste Priorität (System funktioniert nicht ohne):**
1. Datenbank-Credentials (`.env`, `bwa_berechnung.py`)
2. Locosoft-Verbindung (`credentials.json`, `db_utils.py`)
3. Standort-Konfiguration (`standort_utils.py`)

**Hohe Priorität (Features funktionieren nicht):**
4. LDAP-Konfiguration (`ldap_credentials.env`, `auth_manager.py`)
5. App-Namen (`app.py`)

**Mittlere Priorität (Cosmetik/Info):**
6. E-Mail-Konfiguration (`celery_app/tasks.py`)
7. Serviceberater (`serviceberater_api.py`)

**Niedrige Priorität (Optional):**
8. Cognos-Konfiguration (nur falls verwendet)
9. Pfade (nur falls anderer Installationspfad)

---

**Stand:** 2026-01-09  
**Version:** 1.0
