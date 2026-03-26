# ecoDMS – Swagger/OpenAPI ordentlich einbinden

**Workstream:** Controlling (Bankenspiegel / ecoDMS Belegsuche)

**Zweck:** Die ecoDMS-API wird über die OpenAPI/Swagger-Spec als zentrale Quelle eingebunden. So bleiben Endpunkte und Felder konsistent, und bei Versionswechseln der ecoDMS-API müssen wir nicht dauernd raten.

---

## Was ist die „Spec-URL“ / Swagger-URL?

Die **Spec-URL** (auch Swagger-URL oder OpenAPI-URL) ist **die genaue Webadresse**, unter der ecoDMS die **API-Beschreibung** (eine JSON-Datei mit allen Endpunkten und Parametern) ausliefert. Beispiele:

- `http://10.80.80.3:8180/v3/api-docs`
- oder nur der Pfad: `/v3/api-docs` (wird mit der ecoDMS-Basis-URL ergänzt)

**Bei eurer ecoDMS-Instanz** liefert der Standardpfad `/v3/api-docs` **404** (laut früherem Test). Es ist **keine funktionierende Swagger-URL im Projekt gespeichert**. Das Portal kommt trotzdem zurecht: Es nutzt die bekannten API-Pfade direkt (z. B. `/api/folders`). Sobald ihr eine funktionierende Spec-URL habt, könnt ihr sie setzen (siehe unten).

**Swagger-URL herausfinden:** Skript ausführen (probiert alle üblichen Pfade und gibt die erste funktionierende URL aus):

```bash
cd /opt/greiner-portal && python3 scripts/ecodms_find_swagger_url.py
```

Falls eine URL gefunden wird, steht in der Ausgabe, was ihr in `config/.env` eintragen sollt.

---

## 1. Konfiguration

### Spec-URL setzen (empfohlen, sobald bekannt)

In **`config/.env`** (nicht versioniert):

```bash
# Vollständige URL zur OpenAPI-Spec (wenn Swagger unter anderem Pfad läuft)
ECODMS_OPENAPI_SPEC_URL=http://10.80.80.3:8180/ihr-pfad/v3/api-docs

# Oder nur Pfad relativ zur ecoDMS-Basis-URL (ECODMS_BASE_URL):
ECODMS_OPENAPI_SPEC_URL=/ihr-pfad/v3/api-docs
```

- Wenn **nicht** gesetzt: Das Portal versucht automatisch mehrere Standard-Pfade (Discovery, siehe unten).
- Wenn **gesetzt**: Es wird ausschließlich diese URL verwendet. So vermeiden Sie 404 und nutzen die bei euch gültige Spec.

### Swagger-URL in ecoDMS herausfinden

1. **Swagger-UI in ecoDMS:**  
   In der ecoDMS-Installation prüfen, ob es eine Swagger- oder API-Dokumentations-Weboberfläche gibt (z. B. unter `http://<ecoDMS-Server>:8180/swagger-ui.html` oder `/swagger-ui/index.html`). In der Seite steht oft die URL zur JSON-Spec (z. B. „OpenAPI spec“ / „api-docs“).

2. **Typische Pfade ausprobieren** (im Browser oder mit `curl`):
   - `/v3/api-docs`
   - `/v2/api-docs`
   - `/api-docs`
   - `/api/v3/api-docs`
   - `/swagger-resources` (liefert oft eine Liste mit `location` zur eigentlichen Spec)

3. **Portal-Diagnose:**  
   `GET /api/bankenspiegel/transaktionen/ecodms/openapi-status` (eingeloggt) liefert, ob eine Spec geladen wurde und welche Pfade darin vorkommen (siehe Abschnitt 3).

---

## 2. Ablauf im Code

- **Laden:**  
  `api/ecodms_api.py` → **`get_openapi_spec()`** lädt die Spec:
  - zuerst **ECODMS_OPENAPI_SPEC_URL** (wenn gesetzt),
  - sonst **Discovery** über feste Pfade und ggf. `/swagger-resources`.
- **Cache:**  
  Spec wird **10 Minuten** gecacht, damit nicht bei jedem Aufruf neu geladen wird.
- **Nutzung:**  
  Sobald eine Spec vorhanden ist, werden daraus z. B. Ordner-Endpunkte und (geplant) Request/Response-Strukturen abgeleitet. Ohne Spec greifen Fallbacks (z. B. bekannter Pfad `/api/folders`).

---

## 3. API-Endpunkt für Diagnose

| Methode | URL | Beschreibung |
|--------|-----|----------------|
| GET | `/api/bankenspiegel/transaktionen/ecodms/openapi-status` | Ob Spec geladen wurde, Quelle (URL/Pfad), Anzahl Pfade; nur eingeloggt. |

So sehen Sie, ob Swagger ordentlich angebunden ist und können die richtige **ECODMS_OPENAPI_SPEC_URL** ermitteln, falls bisher 404 auftritt.
