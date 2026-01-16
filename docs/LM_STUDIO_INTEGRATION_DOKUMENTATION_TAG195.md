# LM Studio Integration - Vollständige Dokumentation - TAG 195

**Erstellt:** 2026-01-16  
**Server:** Florian Füßl (RZ)  
**Status:** ✅ Implementiert und getestet

---

## 🎯 ÜBERBLICK

**LM Studio** ist ein lokaler LLM-Server, der auf dem Rechenzentrum (RZ) läuft und KI-Funktionen für das DRIVE Portal bereitstellt.

**Vorteile:**
- ✅ Lokal (keine Daten verlassen das Unternehmen)
- ✅ Kostenlos (keine API-Kosten)
- ✅ Schnell (lokale Verbindung)
- ✅ Datenschutz-konform

---

## 🔗 SERVER-INFORMATIONEN

### Server-URLs (von Florian Füßl bereitgestellt)

**Base URL:** `http://46.229.10.1:4433/v1`

**Verfügbare Endpoints:**
- `GET /v1/models` - Liste verfügbarer Modelle
- `POST /v1/chat/completions` - Chat-Completions (empfohlen)
- `POST /v1/completions` - Text-Completions
- `POST /v1/embeddings` - Text-Embeddings

**Server-Status:**
- ✅ Server erreichbar
- ✅ Alle Endpoints funktionsfähig
- ✅ Embedding-Modell verfügbar: `text-embedding-nomic-embed-text-v1.5`

---

## ⚙️ KONFIGURATION

### Konfigurationsdatei

**Datei:** `config/credentials.json`

**Struktur:**
```json
{
  "lm_studio": {
    "api_url": "http://46.229.10.1:4433/v1",
    "default_model": "allenai/olmo-3-32b-think",
    "embedding_model": "text-embedding-nomic-embed-text-v1.5",
    "timeout": 30
  }
}
```

### Konfigurationsfelder

| Feld | Beschreibung | Default |
|------|--------------|---------|
| `api_url` | Base URL des LM Studio Servers | `http://46.229.10.1:4433/v1` |
| `default_model` | Standard-Modell für Chat/Completions | `allenai/olmo-3-32b-think` |
| `embedding_model` | Modell für Embeddings | `text-embedding-nomic-embed-text-v1.5` |
| `timeout` | Timeout in Sekunden | `30` |

### Environment Variables (Alternative)

Falls `credentials.json` nicht verfügbar ist, werden Environment Variables verwendet:

```bash
export LM_STUDIO_API_URL="http://46.229.10.1:4433/v1"
export LM_STUDIO_DEFAULT_MODEL="allenai/olmo-3-32b-think"
export LM_STUDIO_EMBEDDING_MODEL="text-embedding-nomic-embed-text-v1.5"
export LM_STUDIO_TIMEOUT="30"
```

---

## 📋 API-ENDPOINTS

### 1. Models auflisten

**Endpoint:** `GET /api/ai/models`

**Beschreibung:** Listet alle verfügbaren Modelle auf dem LM Studio Server

**Request:**
```bash
curl http://localhost:5000/api/ai/models
```

**Response:**
```json
{
  "success": true,
  "models": [
    {
      "id": "allenai/olmo-3-32b-think",
      "object": "model",
      "created": 1234567890,
      "owned_by": "lm-studio"
    }
  ]
}
```

---

### 2. Chat Completions

**Endpoint:** `POST /api/ai/chat`

**Beschreibung:** Sendet eine Chat-Nachricht an das Modell

**Request:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Du bist ein Experte für Autohaus-Dokumentation."
    },
    {
      "role": "user",
      "content": "Prüfe diese Arbeitskarte auf Vollständigkeit..."
    }
  ],
  "model": "allenai/olmo-3-32b-think",
  "max_tokens": 500,
  "temperature": 0.3
}
```

**Response:**
```json
{
  "success": true,
  "response": "Die Arbeitskarte ist vollständig...",
  "model": "allenai/olmo-3-32b-think",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

**Parameter:**
- `messages` (required): Array von Nachrichten (system, user, assistant)
- `model` (optional): Modell-Name (default: aus Config)
- `max_tokens` (optional): Maximale Token-Anzahl (default: 500)
- `temperature` (optional): Kreativität (0.0-1.0, default: 0.3)

---

### 3. Text Completions

**Endpoint:** `POST /api/ai/completion`

**Beschreibung:** Generiert Text-Completion (einfacher als Chat)

**Request:**
```json
{
  "prompt": "Prüfe diese Arbeitskarte:",
  "model": "allenai/olmo-3-32b-think",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "response": "Die Arbeitskarte ist vollständig...",
  "model": "allenai/olmo-3-32b-think"
}
```

---

### 4. Embeddings

**Endpoint:** `POST /api/ai/embedding`

**Beschreibung:** Erstellt Text-Embeddings (Vektoren) für semantische Suche

**Request:**
```json
{
  "text": "Dieser Text soll in einen Vektor umgewandelt werden.",
  "model": "text-embedding-nomic-embed-text-v1.5"
}
```

**Response:**
```json
{
  "success": true,
  "embedding": [0.123, -0.456, 0.789, ...],
  "model": "text-embedding-nomic-embed-text-v1.5",
  "dimensions": 768
}
```

---

## 🔧 IMPLEMENTIERUNG

### Code-Struktur

**Datei:** `api/ai_api.py`

**Klasse:** `LMStudioClient`
- `__init__()` - Lädt Konfiguration
- `chat_completion()` - Chat-Completions
- `completion()` - Text-Completions
- `create_embedding()` - Embeddings

**Blueprint:** `ai_api`
- URL-Prefix: `/api/ai`
- Alle Endpoints sind mit `@login_required` geschützt

---

## 📊 USE CASES

### 1. TT-Zeit-Optimierung ✅

**Endpoint:** `POST /api/ai/analysiere/tt-zeit/<auftrag_id>`

**Beschreibung:** Analysiert ob TT-Zeit für einen Garantieauftrag abgerechnet werden kann

**Features:**
- Technische Prüfung (automatisch)
- KI-Analyse (Begründung, Empfehlung)
- Warnung für manuelle GSW Portal-Prüfung

**ROI:** ~9.000€/Jahr (bis zu 75,87€ pro Auftrag)

**Dokumentation:** `docs/TT_ZEIT_OPTIMIERUNG_IMPLEMENTIERUNG_TAG195.md`

---

### 2. Arbeitskarten-Dokumentationsprüfung ✅

**Endpoint:** `POST /api/ai/pruefe/arbeitskarte/<auftrag_id>`

**Beschreibung:** Prüft Vollständigkeit der Arbeitskarte

**Features:**
- Prüft Diagnose, Reparaturmaßnahme, TT-Zeiten, Teile-Nummern
- Bewertung (0-100%)
- Fehlende Elemente
- Empfehlungen

**ROI:** ~24.000€/Jahr

**Dokumentation:** `docs/KI_ANWENDUNGSFAELLE_ANALYSE_TAG181.md`

---

### 3. Weitere Use Cases (geplant)

**Siehe:** `docs/KI_USE_CASES_GREINER_AUTOHAUS_TAG195.md`

- Garantie-Dokumentationsprüfung
- Automatische Fehlerklassifikation
- Reklamationsbewertung
- Transaktions-Kategorisierung
- Automatische Kontenzuordnung
- Anomalie-Erkennung bei Transaktionen
- Fahrzeugbeschreibung-Generierung
- Standzeit-Analyse & Empfehlungen

---

## 🧪 TESTING

### Verbindung testen

**Script:** `scripts/test_lm_studio_connection.py`

**Ausführung:**
```bash
cd /opt/greiner-portal
source venv/bin/activate
python3 scripts/test_lm_studio_connection.py
```

**Erwartete Ausgabe:**
```
✅ GET /v1/models - OK
✅ POST /v1/chat/completions - OK
✅ POST /v1/completions - OK
✅ POST /v1/embeddings - OK
```

### API-Endpoints testen

**1. Models auflisten:**
```bash
curl http://localhost:5000/api/ai/models
```

**2. Chat-Completion:**
```bash
curl -X POST http://localhost:5000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hallo!"}
    ]
  }'
```

**3. Embedding:**
```bash
curl -X POST http://localhost:5000/api/ai/embedding \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test-Text"
  }'
```

---

## 🔍 TROUBLESHOOTING

### Problem 1: Connection Timeout

**Symptom:** `ConnectionTimeoutError` oder `Timeout`

**Lösung:**
1. Prüfe ob Server erreichbar ist:
   ```bash
   ping 46.229.10.1
   curl http://46.229.10.1:4433/v1/models
   ```
2. Prüfe Firewall-Regeln
3. Prüfe ob Server läuft (Kontakt: Florian Füßl)

---

### Problem 2: 404 Not Found

**Symptom:** `404 Not Found` bei API-Calls

**Lösung:**
1. Prüfe URL-Pfad: `/v1/models` (nicht `/models`)
2. Prüfe ob Server läuft
3. Prüfe Konfiguration in `config/credentials.json`

---

### Problem 3: Model nicht verfügbar

**Symptom:** `Model not found` oder ähnliche Fehler

**Lösung:**
1. Prüfe verfügbare Modelle:
   ```bash
   curl http://46.229.10.1:4433/v1/models
   ```
2. Passe Konfiguration an:
   ```json
   {
     "lm_studio": {
       "default_model": "verfügbares-modell"
     }
   }
   ```

---

### Problem 4: Embedding-Modell nicht verfügbar

**Symptom:** `Embedding model not found`

**Lösung:**
1. Prüfe ob Embedding-Modell geladen ist (Kontakt: Florian Füßl)
2. Passe Konfiguration an:
   ```json
   {
     "lm_studio": {
       "embedding_model": "text-embedding-nomic-embed-text-v1.5"
     }
   }
   ```

---

## 📝 BEISPIELE

### Beispiel 1: TT-Zeit-Analyse

```python
from api.ai_api import lm_studio_client

# TT-Zeit-Analyse für Auftrag 22073
response = requests.post(
    'http://localhost:5000/api/ai/analysiere/tt-zeit/22073',
    headers={'Content-Type': 'application/json'}
)

data = response.json()
print(f"Begründung: {data['ki_analyse']['begruendung']}")
print(f"Empfehlung: {data['ki_analyse']['empfehlung']}")
```

### Beispiel 2: Arbeitskarten-Prüfung

```python
# Arbeitskarte prüfen
response = requests.post(
    'http://localhost:5000/api/ai/pruefe/arbeitskarte/22073',
    headers={'Content-Type': 'application/json'}
)

data = response.json()
print(f"Vollständigkeit: {data['pruefung']['vollstaendigkeit']}%")
print(f"Fehlende Elemente: {data['pruefung']['fehlende_elemente']}")
```

### Beispiel 3: Direkter LM Studio Client

```python
from api.ai_api import lm_studio_client

# Chat-Completion
messages = [
    {"role": "system", "content": "Du bist ein Experte."},
    {"role": "user", "content": "Analysiere diese Daten..."}
]

response = lm_studio_client.chat_completion(
    messages=messages,
    max_tokens=500,
    temperature=0.3
)

print(response)
```

---

## 🔐 SICHERHEIT

### Authentifizierung

**Status:** ⚠️ **Keine Authentifizierung erforderlich** (lokaler Server)

**Hinweis:** 
- Server läuft im internen Netzwerk
- Keine API-Keys erforderlich
- Zugriff nur aus internem Netzwerk möglich

### Datenschutz

**Vorteile:**
- ✅ Daten verlassen nicht das Unternehmen
- ✅ Keine Cloud-Integration
- ✅ Lokale Verarbeitung
- ✅ DSGVO-konform

---

## 📊 PERFORMANCE

### Timeouts

**Standard:** 30 Sekunden

**Anpassung:**
```json
{
  "lm_studio": {
    "timeout": 60
  }
}
```

### Token-Limits

**Standard:** 500 Tokens pro Request

**Anpassung:**
```python
response = lm_studio_client.chat_completion(
    messages=messages,
    max_tokens=1000  # Erhöht
)
```

---

## 🔄 UPDATES & WARTUNG

### Server-Updates

**Kontakt:** Florian Füßl (RZ)

**Bei Problemen:**
1. Server-Status prüfen
2. Florian kontaktieren
3. Logs prüfen: `journalctl -u greiner-portal -f`

### Modell-Updates

**Neue Modelle:**
1. Florian lädt neues Modell auf Server
2. Konfiguration anpassen (falls nötig)
3. Testen

---

## 📋 CHECKLISTE FÜR NEUE USE CASES

### 1. Use Case definieren
- [ ] Problem identifizieren
- [ ] ROI berechnen
- [ ] Datenquellen identifizieren

### 2. API-Endpoint erstellen
- [ ] Endpoint in `api/ai_api.py` hinzufügen
- [ ] Hilfsfunktionen erstellen
- [ ] Prompt-Engineering

### 3. Frontend-Integration
- [ ] Button/Trigger hinzufügen
- [ ] Modal/Ansicht erstellen
- [ ] Ergebnisse anzeigen

### 4. Testing
- [ ] Mit echten Daten testen
- [ ] Feedback sammeln
- [ ] Verbesserungen

### 5. Dokumentation
- [ ] Use Case dokumentieren
- [ ] API-Endpoint dokumentieren
- [ ] Frontend-Integration dokumentieren

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `api/ai_api.py` - AI API Implementation
- `app.py` - Blueprint-Registrierung

**Konfiguration:**
- `config/credentials.json` - LM Studio Konfiguration

**Dokumentation:**
- `docs/LM_STUDIO_INTEGRATION_TAG195.md` - Integration-Übersicht
- `docs/LM_STUDIO_CONNECTION_TEST_TAG195.md` - Connection-Tests
- `docs/KI_USE_CASES_GREINER_AUTOHAUS_TAG195.md` - Use Cases
- `docs/TT_ZEIT_OPTIMIERUNG_IMPLEMENTIERUNG_TAG195.md` - TT-Zeit Use Case

**Scripts:**
- `scripts/test_lm_studio_connection.py` - Connection-Test

---

## 📞 KONTAKT

**Server-Verwaltung:**
- **Kontakt:** Florian Füßl (RZ)
- **Server:** 46.229.10.1:4433
- **Status:** ✅ Aktiv

**Entwicklung:**
- **Implementiert:** TAG 195
- **Dokumentation:** Diese Datei
- **Support:** Siehe Troubleshooting

---

## ✅ STATUS

**Integration:** ✅ Implementiert  
**Testing:** ✅ Getestet  
**Dokumentation:** ✅ Vollständig  
**Production:** ✅ Aktiv

---

**Erstellt:** TAG 195  
**Letzte Aktualisierung:** 2026-01-16  
**Status:** ✅ Vollständig dokumentiert
