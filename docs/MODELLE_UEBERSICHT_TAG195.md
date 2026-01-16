# KI-Modelle Übersicht - TAG 195

**Erstellt:** 2026-01-16  
**Server:** LM Studio (http://46.229.10.1:4433)  
**Status:** ✅ 15 Modelle verfügbar

---

## 📊 VERFÜGBARE MODELLE

**Gesamt:** 15 Modelle auf LM Studio Server

### 📝 Chat/Completion Modelle (11)

| Modell | Größe | Verwendung | Status |
|--------|-------|------------|--------|
| `mistralai/magistral-small-2509` | Small | **Fahrzeugbeschreibungen** | ✅ Aktiv |
| `openai/gpt-oss-20b` | 20B | Alternative | ⏳ Verfügbar |
| `qwen/qwen3-vl-4b` | 4B | Vision/Language | ⏳ Verfügbar |
| `qwen/qwen3-coder-30b` | 30B | Code-Generierung | ⏳ Verfügbar |
| `qwen/qwen3-vl-30b` | 30B | Vision/Language | ⏳ Verfügbar |
| `deepseek-r1-distill-qwen-32b-q` | 32B | Reasoning | ⏳ Verfügbar |
| `deepseek-coder-33b-instruct` | 33B | Code-Generierung | ⏳ Verfügbar |
| `deepseek-prover-v2-7b` | 7B | Reasoning | ⏳ Verfügbar |
| `deepseek/deepseek-r1-0528-qwen3-8b` | 8B | Reasoning | ⏳ Verfügbar |
| `deepseek-r1-distill-qwen-14b` | 14B | Reasoning | ⏳ Verfügbar |
| `deepseek-r1-distill-qwen-7b` | 7B | Reasoning | ⏳ Verfügbar |

### 🧠 Think-Modelle (3)

| Modell | Größe | Verwendung | Status |
|--------|-------|------------|--------|
| `allenai/olmo-3-32b-think` | 32B | **Standard (Default)** | ⚠️ Think-Modell |
| `olmo-3.1-32b-think-mlx@6bit` | 32B (6bit) | Alternative | ⏳ Verfügbar |
| `olmo-3.1-32b-think-mlx@4bit` | 32B (4bit) | Alternative | ⏳ Verfügbar |

**⚠️ Hinweis:** Think-Modelle geben Denkprozess statt direkter Antwort aus (nicht ideal für JSON-Ausgaben)

### 🔢 Embedding-Modelle (1)

| Modell | Dimensionen | Verwendung | Status |
|--------|-------------|------------|--------|
| `text-embedding-nomic-embed-text-v1.5` | 768 | **Embeddings** | ✅ Aktiv |

---

## 🎯 AKTUELLE VERWENDUNG

### 1. Fahrzeugbeschreibung-Generierung

**Modell:** `mistralai/magistral-small-2509`

**Warum:**
- ✅ Gute JSON-Ausgabe (strukturiert)
- ✅ Kein "Think"-Prozess
- ✅ Schnell (Small-Modell)
- ✅ Zuverlässig

**Code:**
```python
# api/ai_api.py, Zeile 942
model = "mistralai/magistral-small-2509"  # Besseres Modell für strukturierte Ausgaben
response_content = lm_studio_client.chat_completion(
    messages=messages,
    model=model,
    max_tokens=800,
    temperature=0.7
)
```

---

### 2. TT-Zeit-Analyse

**Modell:** `default_model` (aktuell: `allenai/olmo-3-32b-think`)

**Problem:**
- ⚠️ Think-Modell gibt Denkprozess aus
- ⚠️ JSON-Parsing schwierig

**Empfehlung:** Wechsel zu `mistralai/magistral-small-2509`

**Code:**
```python
# api/ai_api.py, Zeile 676
response_content = lm_studio_client.chat_completion(
    messages=messages,
    max_tokens=500,
    temperature=0.3
)
# Verwendet default_model = 'allenai/olmo-3-32b-think'
```

---

### 3. Arbeitskarten-Prüfung

**Modell:** `default_model` (aktuell: `allenai/olmo-3-32b-think`)

**Problem:**
- ⚠️ Think-Modell gibt Denkprozess aus
- ⚠️ JSON-Parsing schwierig

**Empfehlung:** Wechsel zu `mistralai/magistral-small-2509`

---

### 4. Embeddings

**Modell:** `text-embedding-nomic-embed-text-v1.5`

**Verwendung:**
- Vector-Search (geplant)
- Ähnlichkeits-Suche
- RAG-Integration (geplant)

**Code:**
```python
# api/ai_api.py, Zeile 152
model = model or self.embedding_model  # text-embedding-nomic-embed-text-v1.5
```

---

## ⚙️ KONFIGURATION

### Aktuelle Konfiguration

**Datei:** `config/credentials.json` (oder Environment Variables)

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

### Empfohlene Konfiguration

**Für bessere JSON-Ausgaben:**

```json
{
  "lm_studio": {
    "api_url": "http://46.229.10.1:4433/v1",
    "default_model": "mistralai/magistral-small-2509",
    "embedding_model": "text-embedding-nomic-embed-text-v1.5",
    "timeout": 60
  }
}
```

**Grund:**
- `mistralai/magistral-small-2509` liefert bessere strukturierte Ausgaben
- Kein "Think"-Prozess
- Schneller als 32B-Modelle

---

## 🔄 MODELL-AUSWAHL

### Wann welches Modell?

**Für strukturierte Ausgaben (JSON):**
- ✅ `mistralai/magistral-small-2509` (empfohlen)
- ✅ `qwen/qwen3-coder-30b` (für Code/Struktur)
- ❌ `allenai/olmo-3-32b-think` (Think-Modell, nicht ideal)

**Für Reasoning/Analyse:**
- ✅ `deepseek-r1-distill-qwen-32b-q` (32B Reasoning)
- ✅ `deepseek-prover-v2-7b` (7B Reasoning)
- ⚠️ `allenai/olmo-3-32b-think` (Think-Modell, gibt Prozess aus)

**Für Code-Generierung:**
- ✅ `qwen/qwen3-coder-30b` (30B Code)
- ✅ `deepseek-coder-33b-instruct` (33B Code)

**Für Vision (falls nötig):**
- ✅ `qwen/qwen3-vl-4b` (4B Vision)
- ✅ `qwen/qwen3-vl-30b` (30B Vision)

**Für Embeddings:**
- ✅ `text-embedding-nomic-embed-text-v1.5` (einzige Option)

---

## 📊 VERGLEICH: THINK vs. NORMAL

### Think-Modell (`allenai/olmo-3-32b-think`)

**Ausgabe:**
```
Okay, I need to create a professional vehicle description...
Let me start by understanding the given details...
The make is Hyundai, model is also Hyundai...
Wait, maybe that's a typo?
...
```

**Problem:**
- ❌ Gibt Denkprozess aus
- ❌ JSON-Parsing schwierig
- ❌ Längere Antworten
- ❌ Nicht strukturiert

### Normal-Modell (`mistralai/magistral-small-2509`)

**Ausgabe:**
```json
{
  "beschreibung": "Professionelle Beschreibung...",
  "verkaufsargumente": ["Arg1", "Arg2"],
  "seo_keywords": ["KW1", "KW2"]
}
```

**Vorteil:**
- ✅ Direkte Antwort
- ✅ Strukturiert (JSON)
- ✅ Einfaches Parsing
- ✅ Konsistent

---

## 🔧 EMPFOHLENE ÄNDERUNGEN

### 1. Default-Modell wechseln

**Aktuell:**
```python
default_model = 'allenai/olmo-3-32b-think'
```

**Empfohlen:**
```python
default_model = 'mistralai/magistral-small-2509'
```

**Grund:** Bessere JSON-Ausgaben für alle Use Cases

### 2. TT-Zeit-Analyse Modell explizit setzen

**Aktuell:**
```python
response_content = lm_studio_client.chat_completion(
    messages=messages,
    max_tokens=500,
    temperature=0.3
)
```

**Empfohlen:**
```python
response_content = lm_studio_client.chat_completion(
    messages=messages,
    model="mistralai/magistral-small-2509",  # Explizit setzen
    max_tokens=500,
    temperature=0.3
)
```

### 3. Arbeitskarten-Prüfung Modell explizit setzen

**Gleiche Änderung wie bei TT-Zeit-Analyse**

---

## 📋 ZUSAMMENFASSUNG

**Verfügbar:** 15 Modelle

**Aktuell verwendet:**
- ✅ Fahrzeugbeschreibung: `mistralai/magistral-small-2509` (gut)
- ⚠️ TT-Zeit-Analyse: `allenai/olmo-3-32b-think` (Think-Modell)
- ⚠️ Arbeitskarten-Prüfung: `allenai/olmo-3-32b-think` (Think-Modell)
- ✅ Embeddings: `text-embedding-nomic-embed-text-v1.5` (gut)

**Empfehlung:**
- Default-Modell wechseln zu `mistralai/magistral-small-2509`
- Alle Use Cases auf strukturierte Ausgaben optimieren

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `api/ai_api.py` - Modell-Verwendung
- `config/credentials.json` - Konfiguration

**Dokumentation:**
- `docs/LM_STUDIO_INTEGRATION_DOKUMENTATION_TAG195.md` - Integration
- `docs/FAHRZEUGBESCHREIBUNG_KI_TAG195.md` - Use Case

---

**Erstellt:** TAG 195  
**Status:** Übersicht erstellt, Empfehlungen dokumentiert
