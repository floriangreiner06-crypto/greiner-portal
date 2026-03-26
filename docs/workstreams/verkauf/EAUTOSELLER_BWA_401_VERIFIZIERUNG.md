# eAutoSeller BWA / mobile.de Platz – Verifizierung & Umstellung

## Umstellung auf Price-Suggestions (nach User-Hinweis)

**Neue Quelle:** `GET /dms/vehicles/prices/suggestions` (offizielle API).

- Liefert pro Fahrzeug: **current.mobilePosition**, **target.mobilePosition**, **current.priceGross**, **target.priceGross**.
- **Ein** GET für alle Fahrzeuge, gleiche DMS-Auth wie `/dms/vehicles` – **kein separater BWA-Call** mehr nötig.
- DRIVE nutzt diese Quelle in `get_market_placements_for_vins()` und im Celery-Task `sync_eautoseller_data`.
- Optional: Bei 403 den Endpoint bei eAutoSeller für euren Zugang freischalten lassen.

## Früherer Test (19.03.2026) – BWA 401

- **GET /dms/vehicles?vin=...** → **200** (API-Key wird akzeptiert)
- **GET /dms/vehicle/{id}/details** → **200**
- **POST /bwa/evaluation** → **401** (BWA-Berechtigung fehlte)

**Fazit:** Mit der Umstellung auf **prices/suggestions** wird die BWA-Berechtigung nicht mehr benötigt. Bei **403** auf `/dms/vehicles/prices/suggestions`: Zugang für „Price Suggestions“ beim Anbieter erfragen.

## Credentials

- Unterstützt werden **beides**: `config/credentials.json` (Block `eautoseller` mit `api_key`, `client_secret`) und **Umgebungsvariablen** `EAUTOSELLER_API_KEY`, `EAUTOSELLER_CLIENT_SECRET`.
- **Reihenfolge:** Zuerst .env/Umgebung, falls nicht gesetzt dann `credentials.json`.
- Celery lädt beim Start `config/.env` (dotenv), damit Werte aus .env auch im Worker ankommen.

## Was du tun kannst

1. **eAutoSeller kontaktieren:** BWA-/Bewerter-Zugang für euren API-Key freischalten lassen (DMS funktioniert bereits).
2. **Optional Credentials in .env:** In `config/.env` eintragen: `EAUTOSELLER_API_KEY=...`, `EAUTOSELLER_CLIENT_SECRET=...`. Danach Celery neu starten: `sudo systemctl restart celery-worker celery-beat`.
