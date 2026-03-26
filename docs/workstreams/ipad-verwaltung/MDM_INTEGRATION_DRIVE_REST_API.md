# MDM in DRIVE integrieren: REST-API, Optionen, „selber bauen“

**Stand:** 2026-03-18  
**Ziel:** Admins sollen iPad-Verwaltung in DRIVE nutzen können – **ein Login (DRIVE/LDAP)**, kein zweiter Account/Link für das MDM.

---

## Kurzantwort

- **Ja, Integration ist möglich** – wenn das MDM eine **REST-API** anbietet. Dann bauen wir in DRIVE eine Seite, die **über unser Backend** die MDM-API aufruft (Credentials einmal in `config/credentials.json`), und zeigen Geräteliste, Status, ggf. Aktionen (z. B. Remote Lock). Admin loggt nur in DRIVE ein.
- **„Selber bauen“** im Sinne eines **kompletten MDM** (Apple-Protokolle, DEP, Push) lohnt sich nicht und ist sehr aufwendig. **„Selber bauen“** im Sinne eines **DRIVE-Dashboards**, das ein bestehendes MDM per API anspricht, ist genau die richtige Integration.
- **Welche Tools haben REST-API?** Siehe Tabelle unten.

---

## 1. Zwei Wege: Link vs. echte Integration

| Weg | Beschreibung | Admin-Login | Aufwand |
|-----|--------------|-------------|--------|
| **Nur Link** | Navi-Punkt „iPad-Verwaltung“ verlinkt auf ABM bzw. MDM-Weboberfläche | Admin muss sich **nochmal** im MDM anmelden | Gering |
| **Echte Integration** | DRIVE-Backend ruft MDM-**REST-API** auf, Credentials in config; DRIVE-Seite zeigt Geräteliste, Status, evtl. Lock/Wipe | **Nur DRIVE-Login** (LDAP); MDM-Credentials liegen serverseitig | Mittel (API-Client + Route + Template) |

Für „keinen zweiten Link/Account merken“ braucht ihr die **echte Integration** mit einem MDM, das eine REST-API anbietet.

---

## 2. Welche MDM-Tools haben eine REST-API?

| Tool | Zielgruppe | REST-API? | Anmerkung |
|------|------------|------------|-----------|
| **Jamf Pro** | Größere Umgebungen | **Ja** (umfangreich) | Bearer Token (Basic Auth → `/api/v1/auth/token`), dann z. B. `GET /api/v2/mobile-devices`, Lock, Wipe, etc. Gut dokumentiert unter [developer.jamf.com](https://developer.jamf.com/jamf-pro/reference/get_v2-mobile-devices). |
| **Jamf Now** | Kleine Teams (&lt; 25 Geräte) | **Nein** (keine öffentliche API für Drittanbieter) | Nur Weblink möglich, keine Integration der Geräteliste in DRIVE. |
| **Mosyle Business** | Schulen / KMU | **Ja** (REST, JWT) | `businessapi.mosyle.com` – Geräteliste, Gruppen, Wipe etc. Gut für DRIVE-Integration; Mosyle Business FREE bis 30 Geräte kostenlos. |
| **Microsoft Intune** | M365-Kunden | **Ja** (Microsoft Graph API) | `GET /deviceManagement/managedDevices` etc. Sinnvoll, wenn ihr ohnehin Microsoft 365 stark nutzt; dann Integration in DRIVE über Graph API möglich. |
| **MicroMDM / NanoMDM** | Self-Hosted, technisch versiert | **Ja** (REST-API) | Open Source, API für Geräteliste, Befehle (Lock, Wipe). Wenn ihr Self-Hosted MDM betreibt, ist eine DRIVE-Integration gut machbar. |

**Fazit für euch (15 iPads):**

- **Wenn ihr ein Cloud-MDM mit API wollt:** **Jamf Pro** (kostet mehr, hat volle API) oder **Microsoft Intune** (falls M365 vorhanden). Dann können wir die **Integration in DRIVE** bauen: eine Seite „iPad-Verwaltung“ mit Geräteliste aus der API, optional Buttons für Lock/Wipe.
- **Wenn ihr bei Jamf Now oder Mosyle ohne nutzbare API bleibt:** In DRIVE nur **Link** auf das MDM + optional eine **manuell gepflegte** Geräteliste (Tabelle in PostgreSQL), damit ihr wenigstens „Wer hat welches iPad“ in DRIVE seht.

---

## 3. Wie die Integration in DRIVE aussehen würde (mit REST-API)

**Architektur (wie bei Gudat, Leasys, etc.):**

1. **Credentials** einmalig in `config/credentials.json`, z. B. unter `external_systems.jamf` (oder `intune`, `micromdm`):
   - Jamf Pro: Basis-URL (z. B. `https://eure-instanz.jamfcloud.com`), Benutzer + Passwort (oder Client Credentials) für Token.
   - Intune: Tenant-ID, Client-ID, Client-Secret für Microsoft Graph.
   - MicroMDM: Basis-URL + API-Key.
2. **Backend (API-Route):** z. B. `api/ipad_verwaltung_api.py` (oder Erweiterung in `admin_api.py`):
   - Holt Token (Jamf: POST `/api/v1/auth/token`, Intune: OAuth2, MicroMDM: Header).
   - Ruft z. B. `GET /api/v2/mobile-devices` (Jamf) bzw. äquivalent bei anderem MDM auf.
   - Gibt gefilterte Daten (Geräteliste, Status) als JSON an die DRIVE-Frontend-Route zurück.
3. **Route:** z. B. `/admin/ipad-verwaltung` oder `/werkstatt/ipad-verwaltung` (nur für berechtigte Rollen).
4. **Template:** Eine Seite zeigt die Geräteliste (Name, Seriennummer, Modell, zugewiesener User, Status, letzte Meldung, optional Buttons „Sperren“ / „Ort anzeigen“ wenn die MDM-API das unterstützt).

**Rechte:** Nur Nutzer mit entsprechender Berechtigung (z. B. Feature `ipad_verwaltung` oder Admin-Rolle) sehen die Seite. **Ein Login:** DRIVE (LDAP). Das MDM wird nur serverseitig mit den gespeicherten Credentials angesprochen.

**Kein iframe nötig:** Wir bauen keine fremde MDM-Weboberfläche ein (iframe), sondern nutzen nur die **Daten** der MDM-API und zeigen sie in unserem eigenen Layout. Das vermeidet Login-Probleme und sieht einheitlich aus.

---

## 4. „Selber bauen“ – was geht, was nicht

- **Nicht sinnvoll:** Ein **vollständiges MDM** selber bauen (Apple DEP, APNS, Konfigurations-Profile, Zertifikate, Geräteregistrierung). Das ist Apple-spezifisch, aufwendig und wird von fertigen Produkten abgedeckt.
- **Sinnvoll:** Das **DRIVE-Dashboard** „selber bauen“, das ein **bestehendes MDM** per REST-API anspricht. Das ist eine normale Backend-Integration wie bei Gudat/Leasys: API-Client, Route, Template. Kein zweiter Account für Admins.

---

## 5. Konkrete Empfehlung

1. **MDM-Entscheidung:**  
   - Wenn **Jamf Pro** oder **Intune** (bei M365) im Einsatz ist oder geplant ist → **REST-API nutzen** und **Integration in DRIVE** umsetzen (Geräteliste + optionale Aktionen).  
   - Wenn ihr bei **Jamf Now** oder einem Anbieter **ohne API** bleibt → in DRIVE nur **Link** + ggf. **manuelle Geräteliste** (iPad ↔ Mechaniker in PostgreSQL).
2. **Umsetzung in DRIVE:**  
   - Kleines Modul: `api/ipad_verwaltung_api.py` (oder in admin_api), Credentials unter `external_systems.<mdm>`, Route `/admin/ipad-verwaltung` (oder unter Werkstatt), Template mit Tabelle aus API-Daten, Rechte wie andere Admin-Seiten.
3. **Tiefe der Integration:**  
   - **Phase 1:** Nur Geräteliste (Name, Seriennummer, Modell, User, Status).  
   - **Phase 2 (optional):** Buttons für Remote Lock / Wipe, wenn die gewählte MDM-API das anbietet und ihr es wollt.

Wenn ihr euch für ein MDM mit API entscheidet (Jamf Pro, Intune oder MicroMDM), kann im Anschluss die konkrete Implementierung (Endpoints, Credential-Struktur, Beispiel-Request) beschrieben bzw. im Code angelegt werden.
