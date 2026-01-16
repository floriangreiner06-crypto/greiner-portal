# Modell-Training Anleitung - TAG 195

**Erstellt:** 2026-01-16  
**Ziel:** Fahrzeugbeschreibung-Modell für Greiner Autohaus optimieren  
**Status:** 📋 Planungsphase

---

## 🎯 ÜBERBLICK

Es gibt **3 Hauptansätze** für das Modell-Training:

1. **Fine-Tuning** - Modell auf eigenen Daten trainieren (aufwändig, aber bestes Ergebnis)
2. **RAG (Retrieval-Augmented Generation)** - Kontext aus Datenbanken nutzen (schnell, flexibel)
3. **Few-Shot Learning** - Beispiele im Prompt (einfach, sofort umsetzbar)

**Empfehlung:** Start mit **Few-Shot Learning**, dann **RAG**, später **Fine-Tuning**

---

## 🚀 OPTION 1: FEW-SHOT LEARNING (Sofort umsetzbar)

### Konzept
- Beispiele von guten Beschreibungen im Prompt mitgeben
- Modell lernt aus Beispielen, ohne Training
- Keine Modell-Änderungen nötig

### Umsetzung

**1. Beispiel-Datenbank erstellen:**
```sql
-- Tabelle für Beispiel-Beschreibungen
CREATE TABLE IF NOT EXISTS fahrzeug_beschreibung_beispiele (
    id SERIAL PRIMARY KEY,
    dealer_vehicle_number INTEGER,
    marke VARCHAR(50),
    modell VARCHAR(100),
    fahrzeugtyp VARCHAR(20),
    beschreibung_text TEXT,
    verkaufsargumente TEXT[],  -- Array
    seo_keywords TEXT[],        -- Array
    qualitaet_score INTEGER,    -- 1-10
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erstellt_von VARCHAR(50)
);
```

**2. Beispiele sammeln:**
- Manuell erstellte, gute Beschreibungen
- Von Verkaufsplattformen (AutoScout24, Mobile.de)
- Von erfolgreichen Verkäufen

**3. Prompt erweitern:**
```python
# Hole 2-3 ähnliche Beispiele
beispiele = hole_aehnliche_beispiele(marke, modell, fahrzeugtyp)

prompt = f"""
Hier sind Beispiele von guten Fahrzeugbeschreibungen:

BEISPIEL 1:
{beispiele[0]['beschreibung_text']}
Verkaufsargumente: {', '.join(beispiele[0]['verkaufsargumente'])}

BEISPIEL 2:
{beispiele[1]['beschreibung_text']}
Verkaufsargumente: {', '.join(beispiele[1]['verkaufsargumente'])}

Jetzt erstelle eine ähnliche Beschreibung für:
- Marke: {marke}
- Modell: {modell}
...
"""
```

**Vorteile:**
- ✅ Sofort umsetzbar
- ✅ Keine Modell-Änderungen
- ✅ Lernen aus echten Beispielen
- ✅ Stil-Konsistenz

**Nachteile:**
- ⚠️ Prompt wird länger (mehr Tokens)
- ⚠️ Beispiele müssen manuell gepflegt werden

---

## 🔍 OPTION 2: RAG (Retrieval-Augmented Generation)

### Konzept
- Ähnliche Fahrzeuge aus Datenbank finden
- Deren Beschreibungen als Kontext nutzen
- Modell bekommt relevanten Kontext automatisch

### Umsetzung

**1. Embeddings für Fahrzeuge erstellen:**
```python
# Nutze Embedding-Modell
embedding = lm_studio_client.create_embedding(
    text=f"{marke} {modell} {fahrzeugtyp} {erstzulassung_str}",
    model="text-embedding-nomic-embed-text-v1.5"
)

# Speichere Embedding in DB
# Tabelle: fahrzeug_embeddings
```

**2. Ähnliche Fahrzeuge finden:**
```python
# Vector-Similarity-Search
aehnliche_fahrzeuge = finde_aehnliche_fahrzeuge(
    embedding=embedding,
    limit=3
)

# Hole deren Beschreibungen
kontext = hole_beschreibungen_fuer_fahrzeuge(aehnliche_fahrzeuge)
```

**3. Kontext in Prompt einbauen:**
```python
prompt = f"""
Ähnliche Fahrzeuge und deren Beschreibungen:

{kontext}

Erstelle jetzt eine Beschreibung für:
- Marke: {marke}
- Modell: {modell}
...
"""
```

**Vorteile:**
- ✅ Automatisch relevanter Kontext
- ✅ Lernen aus ähnlichen Fahrzeugen
- ✅ Skalierbar (viele Beispiele)

**Nachteile:**
- ⚠️ Embeddings müssen berechnet werden
- ⚠️ Vector-Search nötig (PostgreSQL pgvector oder ähnlich)

---

## 🎓 OPTION 3: FINE-TUNING (Langfristig)

### Konzept
- Modell auf eigenen Daten trainieren
- Spezialisiertes Modell nur für Fahrzeugbeschreibungen
- Bestes Ergebnis, aber aufwändig

### Voraussetzungen

**1. Trainingsdaten sammeln:**
- **Menge:** Mindestens 100-500 Beispiele (ideal: 1000+)
- **Qualität:** Professionelle, manuell erstellte Beschreibungen
- **Vielfalt:** Verschiedene Marken, Modelle, Typen, Preise

**2. Datenformat (JSONL):**
```json
{"messages": [{"role": "system", "content": "Du schreibst Fahrzeugbeschreibungen."}, {"role": "user", "content": "Marke: Hyundai, Modell: Ioniq 5, Typ: Vorführwagen, EZ: 09/2024, KM: 6.700, Preis: 34.980€"}, {"role": "assistant", "content": "{\"beschreibung\": \"...\", \"verkaufsargumente\": [...], \"seo_keywords\": [...]}"}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**3. Training durchführen:**
```bash
# Mit LM Studio (falls unterstützt)
# Oder mit Hugging Face Transformers
python train_fahrzeug_model.py \
  --model_name "mistralai/magistral-small-2509" \
  --train_data "train_data.jsonl" \
  --output_dir "models/fahrzeug_beschreibung"
```

**4. Modell deployen:**
- Fine-tuned Modell auf LM Studio Server laden
- In `config/credentials.json` konfigurieren

**Vorteile:**
- ✅ Bestes Ergebnis
- ✅ Spezialisiert auf unsere Anwendung
- ✅ Konsistenter Stil

**Nachteile:**
- ❌ Aufwändig (Daten sammeln, Training, Deployment)
- ❌ Rechenressourcen nötig
- ❌ Regelmäßige Updates nötig

---

## 📊 PRAKTISCHER START-PLAN

### Phase 1: Few-Shot Learning (TAG 196-197)

**Schritt 1: Beispiel-Datenbank erstellen**
```sql
-- Siehe SQL oben
```

**Schritt 2: 10-20 Beispiele sammeln**
- Bestehende Beschreibungen von Verkaufsplattformen
- Manuell erstellte, gute Beschreibungen
- Verschiedene Fahrzeugtypen (G/N/D/V/L)

**Schritt 3: API erweitern**
- Funktion: `hole_aehnliche_beispiele()`
- Prompt erweitern mit Beispielen
- Testen

**Zeitaufwand:** 1-2 Tage

---

### Phase 2: RAG-Integration (TAG 198-199)

**Schritt 1: Embeddings-Tabelle erstellen**
```sql
CREATE TABLE fahrzeug_embeddings (
    dealer_vehicle_number INTEGER PRIMARY KEY,
    embedding VECTOR(768),  -- pgvector
    marke VARCHAR(50),
    modell VARCHAR(100),
    fahrzeugtyp VARCHAR(20)
);
```

**Schritt 2: Embeddings berechnen**
- Script: `scripts/berechnen_fahrzeug_embeddings.py`
- Für alle Fahrzeuge im Bestand
- Regelmäßig aktualisieren

**Schritt 3: Vector-Search implementieren**
- Funktion: `finde_aehnliche_fahrzeuge()`
- Nutze pgvector oder ähnlich

**Zeitaufwand:** 2-3 Tage

---

### Phase 3: Fine-Tuning (TAG 200+)

**Schritt 1: Trainingsdaten sammeln**
- Ziel: 500+ Beispiele
- Qualität: Professionell, manuell geprüft
- Vielfalt: Alle Fahrzeugtypen, Marken, Preisklassen

**Schritt 2: Daten aufbereiten**
- JSONL-Format
- Train/Val/Test Split (70/15/15)

**Schritt 3: Training**
- Mit Florian Füßl (RZ) koordinieren
- GPU-Ressourcen prüfen
- Training durchführen

**Schritt 4: Evaluation**
- Test-Set prüfen
- Qualität bewerten
- Iteration

**Zeitaufwand:** 1-2 Wochen

---

## 📋 DATEN-SAMMLUNG

### Was sammeln?

**1. Fahrzeugbeschreibungen:**
- Vollständiger Text (150-250 Wörter)
- Verkaufsargumente (3-5 Punkte)
- SEO-Keywords (5-10 Begriffe)

**2. Metadaten:**
- Marke, Modell, Typ
- EZ, KM, Preis
- Standzeit
- Erfolgreich verkauft? (optional)

**3. Qualitätsbewertung:**
- Score 1-10
- Bewertet von Verkäufern
- Feedback sammeln

### Wo sammeln?

**1. Verkaufsplattformen:**
- AutoScout24
- Mobile.de
- eBay Kleinanzeigen
- Eigene erfolgreiche Inserate

**2. Interne Quellen:**
- Manuell erstellte Beschreibungen
- Von Verkäufern
- Historische Verkäufe

**3. KI-generierte (mit Feedback):**
- Aktuelle API-Ausgaben
- Nach manueller Korrektur
- Als Trainingsdaten nutzen

---

## 🛠️ IMPLEMENTIERUNG: FEW-SHOT LEARNING

### 1. Datenbank-Schema

```sql
-- Beispiel-Beschreibungen
CREATE TABLE IF NOT EXISTS fahrzeug_beschreibung_beispiele (
    id SERIAL PRIMARY KEY,
    dealer_vehicle_number INTEGER,
    marke VARCHAR(50) NOT NULL,
    modell VARCHAR(100) NOT NULL,
    fahrzeugtyp VARCHAR(20) NOT NULL,
    beschreibung_text TEXT NOT NULL,
    verkaufsargumente TEXT[] NOT NULL,
    seo_keywords TEXT[] NOT NULL,
    zusammenfassung TEXT,
    qualitaet_score INTEGER CHECK (qualitaet_score BETWEEN 1 AND 10),
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erstellt_von VARCHAR(50),
    erfolgreich_verkauft BOOLEAN DEFAULT false,
    
    -- Index für schnelle Suche
    INDEX idx_marke_modell_typ (marke, modell, fahrzeugtyp)
);
```

### 2. API-Funktion

```python
def hole_aehnliche_beispiele(marke: str, modell: str, fahrzeugtyp: str, limit: int = 3) -> List[Dict]:
    """Holt ähnliche Beispiel-Beschreibungen aus DB"""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            beschreibung_text,
            verkaufsargumente,
            seo_keywords,
            zusammenfassung
        FROM fahrzeug_beschreibung_beispiele
        WHERE marke = %s
          AND fahrzeugtyp = %s
          AND qualitaet_score >= 7
        ORDER BY qualitaet_score DESC, erstellt_am DESC
        LIMIT %s
    """, [marke, fahrzeugtyp, limit])
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'beschreibung_text': row[0],
            'verkaufsargumente': row[1],
            'seo_keywords': row[2],
            'zusammenfassung': row[3]
        }
        for row in rows
    ]
```

### 3. Prompt erweitern

```python
# Hole Beispiele
beispiele = hole_aehnliche_beispiele(marke, modell_name, fahrzeugtyp, limit=2)

# Baue Beispiel-Text
beispiel_text = ""
if beispiele:
    for i, beispiel in enumerate(beispiele, 1):
        beispiel_text += f"""
BEISPIEL {i}:
Beschreibung: {beispiel['beschreibung_text']}
Verkaufsargumente: {', '.join(beispiel['verkaufsargumente'])}
SEO-Keywords: {', '.join(beispiel['seo_keywords'])}

"""

prompt = f"""
Hier sind Beispiele von professionellen Fahrzeugbeschreibungen:

{beispiel_text}

Erstelle jetzt eine ähnliche, professionelle Beschreibung für:

FAHRZEUGDATEN:
- Marke: {marke}
- Modell: {modell_name}
...
"""
```

---

## 📈 EVALUATION & METRIKEN

### Qualitätsmetriken

**1. Quantitative Metriken:**
- Länge (150-250 Wörter) ✅
- Vollständigkeit (alle Felder erwähnt) ✅
- JSON-Format korrekt ✅

**2. Qualitative Metriken:**
- Lesbarkeit (1-10)
- Relevanz der Argumente (1-10)
- SEO-Optimierung (1-10)
- Stil-Konsistenz (1-10)

**3. Business-Metriken:**
- Verkaufsrate (optional)
- Klickrate auf Inserate (optional)
- Feedback von Verkäufern

### Evaluation-Script

```python
def evaluiere_beschreibung(beschreibung: Dict, fahrzeug: Dict) -> Dict:
    """Bewertet Qualität einer generierten Beschreibung"""
    score = 0
    feedback = []
    
    # Länge prüfen
    text_len = len(beschreibung.get('haupttext', '').split())
    if 150 <= text_len <= 250:
        score += 2
    else:
        feedback.append(f"Länge: {text_len} Wörter (sollte 150-250 sein)")
    
    # Vollständigkeit prüfen
    if fahrzeug['marke'] in beschreibung.get('haupttext', ''):
        score += 1
    if fahrzeug['modell'] in beschreibung.get('haupttext', ''):
        score += 1
    if fahrzeug['erstzulassung'] in beschreibung.get('haupttext', ''):
        score += 1
    
    # Verkaufsargumente prüfen
    if len(beschreibung.get('verkaufsargumente', [])) >= 3:
        score += 1
    
    # SEO-Keywords prüfen
    if len(beschreibung.get('seo_keywords', [])) >= 5:
        score += 1
    
    return {
        'score': score,
        'max_score': 7,
        'feedback': feedback
    }
```

---

## 🔄 ITERATION & VERBESSERUNG

### Feedback-Loop

**1. Nutzung:**
- API wird verwendet
- Beschreibungen werden generiert

**2. Feedback sammeln:**
- Verkäufer bewerten Beschreibungen
- Erfolgreiche Verkäufe tracken
- Probleme dokumentieren

**3. Daten aktualisieren:**
- Gute Beschreibungen in Beispiel-DB
- Schlechte als "was nicht tun"
- Prompt anpassen

**4. Modell verbessern:**
- Few-Shot: Neue Beispiele hinzufügen
- RAG: Embeddings aktualisieren
- Fine-Tuning: Nachtrainieren

---

## 📝 NÄCHSTE SCHRITTE

### Sofort (TAG 196)
1. [ ] Beispiel-Datenbank erstellen
2. [ ] 10-20 Beispiele sammeln
3. [ ] API erweitern mit Few-Shot Learning
4. [ ] Testen

### Kurzfristig (TAG 197-198)
5. [ ] Feedback-Mechanismus implementieren
6. [ ] Evaluation-Script erstellen
7. [ ] Weitere Beispiele sammeln (50+)

### Mittelfristig (TAG 199-200)
8. [ ] RAG-Integration (Embeddings)
9. [ ] Vector-Search implementieren
10. [ ] Automatische Beispiel-Auswahl

### Langfristig (TAG 201+)
11. [ ] Fine-Tuning vorbereiten (500+ Beispiele)
12. [ ] Training durchführen
13. [ ] Fine-tuned Modell deployen

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `api/ai_api.py` - Aktuelle Implementierung
- `api/db_connection.py` - DB-Verbindung

**Dokumentation:**
- `docs/FAHRZEUGBESCHREIBUNG_KI_TAG195.md` - Use Case Dokumentation
- `docs/LM_STUDIO_INTEGRATION_DOKUMENTATION_TAG195.md` - LM Studio Integration

**Geplant:**
- `scripts/berechnen_fahrzeug_embeddings.py` - Embeddings berechnen
- `scripts/sammle_beschreibung_beispiele.py` - Beispiele sammeln
- `api/fahrzeug_beschreibung_beispiele.py` - Beispiel-Management

---

## ✅ STATUS

**TAG 195:**
- ✅ Dokumentation erstellt
- ✅ 3 Ansätze definiert
- ⏳ Few-Shot Learning: Geplant
- ⏳ RAG: Geplant
- ⏳ Fine-Tuning: Langfristig

**Empfehlung:** Start mit Few-Shot Learning (einfach, schnell, effektiv)

---

**Erstellt:** TAG 195  
**Status:** Planungsphase - Bereit für Implementierung
