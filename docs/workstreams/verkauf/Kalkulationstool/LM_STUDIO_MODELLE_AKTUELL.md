# LM Studio – aktuelle Modelle & Nutzung im Portal

**Abfrage:** 2026-03 (Server 46.229.10.1:4433)  
**Letzte Prüfung:** RZ hat neue Modelle geladen.  
**Anzahl Modelle auf dem Server:** 19

---

## Was ihr aktuell nutzt (Config)

**SSOT:** Alle LM-Studio-Einstellungen stehen zentral in **`config/credentials.json`** unter dem Schlüssel **`lm_studio`**:

- `api_url`, `default_model`, `vision_model`, `embedding_model`, `timeout`

Änderungen (z. B. anderes Modell) nur dort vornehmen; `api/ai_api.py` liest daraus und verwendet nirgends mehr hardcodierte Modellnamen.

| Zweck | Modell | Konfiguration |
|------|--------|----------------|
| **Chat / JSON (Hilfe, Kategorisierung, Verkaufsprogramm-Regelwerk, Unfall-Gutachten)** | `mistralai/devstral-small-2-2512` | `config/credentials.json` → `lm_studio.default_model` |
| **Vision (Fahrzeugschein-OCR)** | `qwen/qwen3-vl-4b` | `lm_studio.vision_model` |
| **Embeddings** | `text-embedding-nomic-embed-text-v1.5` | `lm_studio.embedding_model` |

Fallback in `api/ai_api.py` nur, wenn kein `lm_studio`-Block in `credentials.json` existiert (z. B. Testumgebung); optional Überschreibung per Umgebungsvariablen `LM_STUDIO_DEFAULT_MODEL`, `LM_STUDIO_API_URL` usw.

---

## Verfügbare Modelle auf dem Server (Stand RZ-Update)

**Chat/Text:**
- `mistralai/devstral-small-2-2512` ← **aktuell genutzt (Default, in config/credentials.json)**
- `glm-4.7-flash-claude-opus-4.5-high-reasoning-distill` ← **neu**
- `allenai/olmo-3-32b-think`
- `olmo-3.1-32b-instruct-mlx@4bit` / `@6bit`
- `olmo-3.1-32b-think-mlx@4bit` / `@6bit`
- `deepseek-r1-distill-qwen-7b` / `-14b` / `-32b-q`
- `deepseek/deepseek-r1-0528-qwen3-8b`
- `deepseek-coder-33b-instruct`
- `deepseek-prover-v2-7b`
- `openai/gpt-oss-20b`
- `qwen/qwen3-coder-30b`

**Vision (Bild + Text):**
- `qwen/qwen3-vl-4b` ← **aktuell genutzt (Fahrzeugschein)**
- `qwen/qwen3-vl-30b` (größer)

**Embedding:**
- `text-embedding-nomic-embed-text-v1.5` ← **aktuell genutzt**

---

## Neu auf dem Server (nach RZ-Update)

- **`mistralai/devstral-small-2-2512`** – neueres Mistral Small (Dez 2025), Nachfolger/Variante zu Magistral; für Chat/JSON einen Test wert.
- **`glm-4.7-flash-claude-opus-4.5-high-reasoning-distill`** – Reasoning-Distillat (Claude Opus); evtl. größerer Kontext / bessere Logik, prüfen ob Ausgabe direkt JSON oder mit Reasoning-Text.

Modellliste live abrufen (auf dem Server):

```bash
cd /opt/greiner-portal && .venv/bin/python -c "
from api.ai_api import lm_studio_client
models = lm_studio_client.list_models()
for m in sorted(models or []):
    print(m)
"
```

Oder im Portal (eingeloggt): API-Aufruf `GET /api/ai/models` (wenn Route registriert ist).

---

## Welches Modell passt für unsere bisherigen Zwecke am besten?

### Anforderungen im Portal

| Einsatz | Anforderung |
|--------|-------------|
| Hilfe „Mit KI erweitern“ | Deutsch, Markdown, längere Texte |
| Transaktions-Kategorisierung | Deutsch, kurze Antwort (Kategorie/Unterkategorie) |
| Verkaufsprogramm-Regelwerk | PDF-Text → **strikte JSON** (Programm, Konditionen, Boni mit Zahlen) |
| Unfall-Gutachten | Text → **strikte JSON** (Positionen, Beträge) |
| Fahrzeugbeschreibung / Arbeitskarten / TT-Zeit | strukturierte Ausgaben, teils JSON |
| Fahrzeugschein-OCR | **Vision**: Bild → JSON (VIN, EZ, etc.) |

Gemeinsam: **strukturierte Ausgabe (ideal JSON)**, **Deutsch**, **stabil und nicht zu langsam**. Think-Modelle (z. B. `olmo-3-32b-think`) sind ungeeignet – sie geben einen Denkprozess aus, kein direktes JSON.

### Empfehlung

| Zweck | Modell | Begründung |
|-------|--------|------------|
| **Chat/JSON (Standard)** | **`mistralai/devstral-small-2-2512`** | Neues Mistral Small (RZ-Update); gute JSON-Ausgaben, schnell, stabil. Passt für Hilfe, Kategorisierung, Regelwerk, Unfall, Fahrzeugbeschreibung. (Zuvor: magistral-small-2509.) |
| **Vision (Fahrzeugschein)** | **`qwen/qwen3-vl-4b`** | Gute Balance aus Genauigkeit und Latenz. Für höhere OCR-Qualität optional `qwen/qwen3-vl-30b` testen (mehr Ressourcen). |
| **Embeddings** | **`text-embedding-nomic-embed-text-v1.5`** | Standard für semantische Suche/Embeddings, beibehalten. |

**Falls ihr bei langen PDFs (Verkaufsprogramm) mehr Kontext braucht:**  
Ihr stoßt aktuell an ein Input-Limit (z. B. ~8k Zeichen). Ein Modell mit größerem Kontext könnte helfen – auf eurem Server z. B. **`deepseek-r1-distill-qwen-14b`** oder **`deepseek-r1-distill-qwen-7b`** (oft 32k Kontext). Dafür müsst ihr testen, ob die Antwort trotzdem **direktes JSON** ist (kein langer Reasoning-Text). Wenn ja, könnte man für den Regelwerk-Call gezielt dieses Modell übergeben; Standard für alle anderen Calls bleibt **magistral-small-2509**.

**Kurz:** Für eure bisherigen Zwecke: **`mistralai/devstral-small-2-2512`** (Text/JSON), **`qwen/qwen3-vl-4b`** (Vision). Nur bei Bedarf (längerer Kontext für ganze PDFs) optional ein DeepSeek-R1-Distill-Modell gezielt testen.

---

## Kurzfassung

- **Aktuell genutzt:** `mistralai/magistral-small-2509` (Text/JSON), `qwen/qwen3-vl-4b` (Vision).
- **Neuer/größer auf dem Server:** u. a. DeepSeek R1 (7B–32B), Qwen3-VL 30B, OLMO 3.1 – zum Testen in `credentials.json` unter `lm_studio.default_model` bzw. `vision_model` eintragen und ggf. Kontext-/Token-Limits prüfen.
