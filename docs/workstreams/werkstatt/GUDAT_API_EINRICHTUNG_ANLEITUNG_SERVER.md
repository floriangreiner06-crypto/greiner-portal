# Gudat API – Anleitung Einrichtung (Center + DRIVE-Server)

**Workstream:** werkstatt  
**Stand:** 2026-03-12

Diese Anleitung beschreibt die Schritte zur Einrichtung der Gudat-API: **API-Benutzer im Gudat Center** anlegen und **Credentials am DRIVE-Server** eintragen.

---

## Teil 1: API-Benutzer im Gudat/DA Center anlegen

Der Gudat-Support verlangt: *„In ihrem Center müssen Sie noch einen Benutzer für die API-Nutzung erstellen.“* Dieser Benutzer wird für den **OAuth Password Grant** (E-Mail + Passwort) benötigt; DRIVE nutzt ihn ausschließlich für API-Aufrufe, nicht für manuelles Login im Browser.

### 1.1 Wo anlegen?

- **Deggendorf:** Verwaltung in der Regel unter  
  `https://werkstattplanung.net/greiner/deggendorf/`  
  (Bereich **lic** oder **Verwaltung** / Benutzerverwaltung – je nach Menüführung von Gudat.)
- **Landau:** Entsprechend  
  `https://werkstattplanung.net/greiner/landau/`  
  (falls Landau eine eigene Verwaltungsoberfläche hat).

Falls ihr nur **einen** API-Benutzer für beide Center anlegen könnt, reicht einer; ob ein User für beide Center (group=greiner, center=deggendorf bzw. landau) ausreicht, steht in der Gudat-Doku oder kann beim Support erfragt werden.

### 1.2 Was anlegen?

| Feld | Empfehlung |
|------|------------|
| **E-Mail / Benutzername** | z. B. `api-drive@auto-greiner.de` oder ein anderer technischer Account (kein persönliches Postfach). |
| **Passwort** | Falls die Oberfläche ein Passwort abfragt: starkes Passwort; in DRIVE unter `config/credentials.json` eintragen. **Bei Greiner:** In der Gudat-UI wurde **kein Passwort** abgefragt (Stand 12.03.2026). |
| **Rolle / Rechte** | So setzen, dass der Benutzer für die **API-Nutzung** berechtigt ist – **bei Greiner** war **keine gesonderte Rechtevergabe** in der Oberfläche nötig (Rolle „Greiner Admin“ wurde zugewiesen). |

### 1.3 Bei Greiner umgesetzt (12.03.2026)

| Center     | Name/ID (in Gudat)   | E-Mail                 | Rolle        | Angelegt   |
|------------|---------------------|------------------------|--------------|------------|
| **Landau** | api_drive_landau / drive_api_landau | admin@auto-greiner.de   | Greiner Admin | 12.03.2026 15:54 |
| **Deggendorf** | drive_api_deggendorf | **admin@opel-greiner.de** | Greiner Admin | 12.03.2026 15:55 |

Hinweis: E-Mail pro Center muss **eindeutig** sein (Gudat: nur einmalig verwendbar). Deggendorf wurde daher auf **admin@opel-greiner.de** geändert. **Passwörter** wurden per E-Mail von Gudat zugestellt und sind in `config/credentials.json` pro Center einzutragen. Es wurde keine gesonderte Rechtevergabe in der Oberfläche gefordert.

### 1.4 Notieren

- **E-Mail** (und ggf. Passwort, falls später gesetzt) pro Center für Teil 2 (DRIVE-Server) notieren.

---

## Teil 2: Credentials am DRIVE-Server eintragen

Alle Zugangsdaten liegen **nur auf dem Server** in `config/credentials.json`. Diese Datei ist in der `.gitignore` und wird **nicht** ins Git eingecheckt.

### 2.1 Pfad und Rechte

- **Pfad:** `/opt/greiner-portal/config/credentials.json`
- **Bearbeiten:** z. B. per SSH auf dem Server (`ag-admin@10.80.80.20`) mit einem Editor (nano, vim) oder von eurem Sync/Backup aus, sofern die Datei dorthin kopiert wird.
- **Sicherheit:** Nur berechtigte Personen; Datei nicht per E-Mail oder in Chats teilen.

### 2.2 Struktur für Gudat (bestehend + OAuth)

Unter `external_systems.gudat` soll Folgendes stehen:

1. **Bereits vorhanden (KIC/Session – weiter nutzen):**  
   `username`, `password` – können vorerst die bisherigen Werte bleiben (z. B. für Werkstatt Live, Kapazität, GraphQL).  
   Optional: Nach dem Anlegen des API-Benutzers hier auf den **neuen** API-User umstellen (dann ein Account für KIC und OAuth).

2. **Neu (OAuth DA REST API):**  
   - `api_base_url`: `https://api.werkstattplanung.net/da/v1`  
   - `group`: `greiner`  
   - `centers`: je Center `client_id` und `client_secret` (aus der entschlüsselten Gudat-Datei).  
   - Für OAuth Password Grant: `username` und `password` = der **im Center angelegte API-Benutzer** (E-Mail + Passwort).

**Beispielstruktur** (Platzhalter ersetzen, keine echten Geheimnisse hier eintragen). Pro Center: **username** = E-Mail des API-Benutzers, **password** = von Gudat per E-Mail zugestellt:

```json
"external_systems": {
  "gudat": {
    "username": "admin@auto-greiner.de",
    "password": "<Passwort KIC – z. B. bisheriger Wert oder Landau-Passwort>",
    "portal_url": "https://werkstattplanung.net/greiner/deggendorf/kic",
    "api_base_url": "https://api.werkstattplanung.net/da/v1",
    "group": "greiner",
    "centers": {
      "deggendorf": {
        "client_id": "<Client ID Deggendorf aus Gudat-Datei>",
        "client_secret": "<Client Secret Deggendorf>",
        "username": "admin@opel-greiner.de",
        "password": "<Passwort von Gudat per E-Mail für Deggendorf>"
      },
      "landau": {
        "client_id": "<Client ID Landau aus Gudat-Datei>",
        "client_secret": "<Client Secret Landau>",
        "username": "admin@auto-greiner.de",
        "password": "<Passwort von Gudat per E-Mail für Landau>"
      }
    }
  }
}
```

Hinweis: Das obere `username`/`password` wird weiterhin für **KIC** (Werkstatt Live, Kapazität, GraphQL) genutzt. Pro Center: **username** = E-Mail (Deggendorf: admin@opel-greiner.de, Landau: admin@auto-greiner.de), **password** = von Gudat per E-Mail erhalten.

### 2.3 Konkret am Server (PuTTY Schritt für Schritt)

**Ausführliche Anleitung mit allen Befehlen für PuTTY:** siehe **`GUDAT_CREDENTIALS_PUTTY_SCHRITT_FÜR_SCHRITT.md`** (in diesem Ordner).

Kurz:
1. Auf dem DRIVE-Server einloggen (PuTTY/SSH).
2. Datei öffnen:  
   `nano /opt/greiner-portal/config/credentials.json`  
   (oder `vim` / anderer Editor.)
3. Den Block `external_systems.gudat` wie oben erweitern bzw. anpassen:
   - **username** / **password** (obere Ebene): weiterhin für KIC (Werkstatt Live etc.); ggf. bestehende Werte lassen.
   - **centers.deggendorf**: `client_id`, `client_secret` aus der Gudat-Datei; `username`: **admin@opel-greiner.de**; `password`: von Gudat per E-Mail.
   - **centers.landau**: `client_id`, `client_secret` aus der Gudat-Datei; `username`: **admin@auto-greiner.de**; `password`: von Gudat per E-Mail.
4. Datei speichern und schließen.
5. **Kein** Commit der Datei ins Git – sie ist ignoriert.
6. Optional: Berechtigungen prüfen, z. B. nur App-User lesbar:  
   `chmod 600 /opt/greiner-portal/config/credentials.json`

### 2.4 Nach dem Eintragen

- **Bisherige Gudat-Funktionen (KIC):** Werkstatt Live, Kapazität, Arbeitskarte nutzen weiter `username`/`password` aus derselben Datei. Wenn ihr dort den neuen API-User eingetragen habt, testet z. B. das Werkstatt-Live-Board im Browser.
- **OAuth (DA REST API):** Die Nutzung der neuen Client-ID/Secret erfordert noch Code (Token-Handling, Aufrufe gegen api.werkstattplanung.net). Die Konfiguration ist damit vorbereitet; die technische Integration folgt laut Plan (`GUDAT_API_EINRICHTUNG_PLAN.md`).

---

## Kurz-Checkliste

| Schritt | Erledigt |
|--------|----------|
| 1. Im Gudat Center API-Benutzer angelegt (Landau: admin@auto-greiner.de, Deggendorf: admin@opel-greiner.de); Passwörter per E-Mail von Gudat erhalten | ☐ |
| 2. Auf DRIVE-Server: `config/credentials.json` geöffnet | ☐ |
| 3. `external_systems.gudat` um `api_base_url`, `group`, `centers` ergänzt | ☐ |
| 4. Pro Center: `client_id`, `client_secret`, `username` (E-Mail), `password` (von Gudat per E-Mail) eingetragen | ☐ |
| 5. Datei gespeichert, **nicht** ins Git committet | ☐ |
| 6. Optional: Werkstatt Live / Kapazität im Portal testen (KIC nutzt weiter oberes username/password) | ☐ |

---

**Referenzen:**  
- Plan & Funktionsumfang: `GUDAT_API_EINRICHTUNG_PLAN.md`  
- Credentials allgemein: `docs/CREDENTIALS_AM_SERVER.md`  
- Werkstatt-CONTEXT: `docs/workstreams/werkstatt/CONTEXT.md` (Gudat-Credentials SSOT)
