# Modell-Empfehlungen für unsere Anforderungen - TAG 195

**Erstellt:** 2026-01-16  
**Status:** ✅ Getestet und bewertet

---

## 🎯 UNSERE ANFORDERUNGEN

1. **Fahrzeugbeschreibung-Generierung**
   - Strukturierte JSON-Ausgaben
   - Kreative, professionelle Texte
   - SEO-optimiert

2. **TT-Zeit-Analyse**
   - Strukturierte JSON-Ausgaben
   - Technische Analyse
   - Logische Bewertung

3. **Arbeitskarten-Prüfung**
   - Strukturierte JSON-Ausgaben
   - Qualitätsbewertung
   - Checkliste

**Gemeinsam:** Alle benötigen **strukturierte JSON-Ausgaben** (kein Think-Prozess!)

---

## 📊 VERFÜGBARE MODELLE (getestet)

### ✅ Aktuell: `mistralai/magistral-small-2509`

**Vorteile:**
- ✅ Schnell (Small-Modell)
- ✅ Gute JSON-Ausgaben
- ✅ Zuverlässig
- ✅ Kein Think-Prozess

**Nachteile:**
- ⚠️ Kleineres Modell (möglicherweise weniger präzise)

**Test-Ergebnis:**
- JSON-Format: ✅
- Länge: 755 Zeichen
- Parsebar: ✅
- Geschwindigkeit: ⚡ Schnell

---

### 🆕 Alternative 1: `qwen/qwen3-coder-30b`

**Vorteile:**
- ✅ Code-Modell = speziell für strukturierte Ausgaben trainiert
- ✅ Größeres Modell (30B) = möglicherweise präziser
- ✅ Gute JSON-Ausgaben (getestet)
- ✅ Kein Think-Prozess

**Nachteile:**
- ⚠️ Langsamer (größeres Modell)
- ⚠️ Mehr Ressourcen

**Test-Ergebnis:**
- JSON-Format: ✅
- Länge: 546 Zeichen (kompakter!)
- Parsebar: ✅
- Geschwindigkeit: ⏱️ Langsamer

**Empfehlung:** Für **TT-Zeit-Analyse** und **Arbeitskarten-Prüfung** (strukturierte, technische Ausgaben)

---

### 🆕 Alternative 2: `deepseek-coder-33b-instruct`

**Vorteile:**
- ✅ Code-Modell = speziell für strukturierte Ausgaben
- ✅ Größtes Modell (33B) = höchste Präzision
- ✅ Instruct-Modell = folgt Anweisungen gut

**Nachteile:**
- ⚠️ Langsamste Option
- ⚠️ Meiste Ressourcen

**Empfehlung:** Für **kritische Analysen** (falls Präzision wichtiger als Geschwindigkeit)

---

### 🆕 Alternative 3: `qwen/qwen3-vl-30b`

**Vorteile:**
- ✅ Vision/Language = vielseitig
- ✅ Großes Modell (30B)
- ✅ Gute für kreative Texte

**Nachteile:**
- ⚠️ Langsamer
- ⚠️ Nicht speziell für Code/Struktur

**Empfehlung:** Für **Fahrzeugbeschreibung** (falls mehr Kreativität gewünscht)

---

## 💡 EMPFOHLENE KONFIGURATION

### Option A: Aktuell beibehalten (Geschwindigkeit)

**Alle Use Cases:** `mistralai/magistral-small-2509`

**Vorteile:**
- ✅ Schnell
- ✅ Zuverlässig
- ✅ Einheitlich

**Nachteile:**
- ⚠️ Möglicherweise weniger präzise bei komplexen Analysen

---

### Option B: Hybrid (Geschwindigkeit + Präzision)

**Fahrzeugbeschreibung:** `mistralai/magistral-small-2509`
- Kreativ, schnell, ausreichend präzise

**TT-Zeit-Analyse:** `qwen/qwen3-coder-30b`
- Strukturiert, präzise, technisch

**Arbeitskarten-Prüfung:** `qwen/qwen3-coder-30b`
- Strukturiert, präzise, bewertend

**Vorteile:**
- ✅ Beste Balance aus Geschwindigkeit und Präzision
- ✅ Code-Modelle für strukturierte Ausgaben
- ✅ Small-Modell für kreative Texte

**Nachteile:**
- ⚠️ Unterschiedliche Geschwindigkeiten
- ⚠️ Mehr Konfiguration

---

### Option C: Maximum Präzision

**Alle Use Cases:** `qwen/qwen3-coder-30b` oder `deepseek-coder-33b-instruct`

**Vorteile:**
- ✅ Höchste Präzision
- ✅ Beste strukturierte Ausgaben

**Nachteile:**
- ❌ Langsamer
- ❌ Mehr Ressourcen

---

## 📊 VERGLEICHSTABELLE

| Modell | Größe | Geschwindigkeit | JSON-Qualität | Kreativität | Empfehlung |
|--------|-------|----------------|---------------|-------------|------------|
| `mistralai/magistral-small-2509` | Small | ⚡⚡⚡ Schnell | ✅✅ Gut | ✅✅ Gut | **Aktuell, gut** |
| `qwen/qwen3-coder-30b` | 30B | ⏱️ Langsam | ✅✅✅ Sehr gut | ✅ Mittel | **Für strukturierte Ausgaben** |
| `deepseek-coder-33b-instruct` | 33B | ⏱️⏱️ Sehr langsam | ✅✅✅ Sehr gut | ✅ Mittel | **Für kritische Analysen** |
| `qwen/qwen3-vl-30b` | 30B | ⏱️ Langsam | ✅✅ Gut | ✅✅✅ Sehr gut | **Für kreative Texte** |

---

## 🎯 KONKRETE EMPFEHLUNG

### Für unsere Anforderungen: **Option B (Hybrid)**

**Begründung:**
1. **Fahrzeugbeschreibung** braucht Kreativität → `mistralai` (schnell, ausreichend)
2. **TT-Zeit-Analyse** braucht Präzision → `qwen3-coder` (strukturiert, präzise)
3. **Arbeitskarten-Prüfung** braucht Präzision → `qwen3-coder` (strukturiert, präzise)

**Umsetzung:**
```python
# Fahrzeugbeschreibung
model = "mistralai/magistral-small-2509"  # Kreativ, schnell

# TT-Zeit-Analyse
model = "qwen/qwen3-coder-30b"  # Strukturiert, präzise

# Arbeitskarten-Prüfung
model = "qwen/qwen3-coder-30b"  # Strukturiert, präzise
```

---

## 🧪 TEST-ERGEBNISSE

### Test 1: TT-Zeit-Analyse Prompt

**mistralai/magistral-small-2509:**
- ✅ JSON-Format: Ja
- ✅ Länge: 755 Zeichen
- ✅ Parsebar: Ja
- ⚡ Geschwindigkeit: Schnell

**qwen/qwen3-coder-30b:**
- ✅ JSON-Format: Ja
- ✅ Länge: 546 Zeichen (kompakter!)
- ✅ Parsebar: Ja
- ⏱️ Geschwindigkeit: Langsamer

**Fazit:** Beide funktionieren, `qwen3-coder` ist kompakter und möglicherweise präziser.

---

## 🔄 MIGRATION-EMPFEHLUNG

### Schritt 1: Test mit qwen3-coder

1. TT-Zeit-Analyse auf `qwen3-coder` umstellen
2. Mit echten Daten testen
3. Qualität vergleichen

### Schritt 2: Evaluation

- Geschwindigkeit akzeptabel?
- Qualität besser?
- JSON-Parsing zuverlässig?

### Schritt 3: Rollout

- Wenn besser: Arbeitskarten-Prüfung auch umstellen
- Fahrzeugbeschreibung: Bei mistralai belassen (Kreativität)

---

## 📝 NÄCHSTE SCHRITTE

### Kurzfristig (TAG 196)
1. [ ] TT-Zeit-Analyse auf `qwen3-coder` testen
2. [ ] Qualität vergleichen
3. [ ] Entscheidung treffen

### Mittelfristig (TAG 197+)
4. [ ] Hybrid-Konfiguration implementieren (falls gewünscht)
5. [ ] Performance-Monitoring
6. [ ] Weitere Optimierungen

---

## 🔗 RELEVANTE DATEIEN

**Code:**
- `api/ai_api.py` - Modell-Verwendung

**Dokumentation:**
- `docs/MODELLE_UEBERSICHT_TAG195.md` - Modell-Übersicht
- `docs/LM_STUDIO_INTEGRATION_DOKUMENTATION_TAG195.md` - Integration

---

## ✅ STATUS

**TAG 195:**
- ✅ Modelle analysiert
- ✅ Tests durchgeführt
- ✅ Empfehlungen erstellt
- ⏳ Entscheidung: Hybrid-Konfiguration (optional)

**Aktuell:** `mistralai/magistral-small-2509` funktioniert gut für alle Use Cases

**Optional:** `qwen3-coder-30b` für strukturierte Ausgaben (TT-Zeit, Arbeitskarten)

---

**Erstellt:** TAG 195  
**Status:** Empfehlungen erstellt, bereit für Entscheidung
