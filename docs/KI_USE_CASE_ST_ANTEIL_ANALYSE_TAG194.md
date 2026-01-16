# KI Use Case: St-Anteil Berechnungsanalyse - TAG 194

**Datum:** 2026-01-16  
**Status:** 💡 Vorschlag für Implementierung

---

## 🎯 Problem

St-Anteil Berechnung weicht bei bestimmten Mechanikern erheblich von Locosoft ab:
- **Tobias (5007):** DRIVE 3360 Min vs. Locosoft 4971 Min (Diff: 1611 Min, 32.4%) ❌
- **Litwin (5014):** DRIVE 2082 Min vs. Locosoft 2078 Min (Diff: 4 Min, 0.2%) ✅

---

## 💡 Wie kann LM Studio helfen?

### 1. SQL-Query-Analyse
- **Aufgabe:** Analysiere die SQL-Query auf Logik-Fehler
- **Input:** Aktuelle SQL-Query aus `api/werkstatt_data.py`
- **Output:** Identifizierte Probleme, Verbesserungsvorschläge

### 2. Datenstruktur-Analyse
- **Aufgabe:** Analysiere warum bei Tobias größere Abweichung als bei Litwin
- **Input:** Datenstruktur-Vergleich (Positionen, Stempelungen, AW)
- **Output:** Erkenntnisse über Unterschiede

### 3. Alternative Berechnungslogik
- **Aufgabe:** Vorschlage alternative SQL-Queries basierend auf Analyse
- **Input:** Problem-Beschreibung, getestete Varianten
- **Output:** Neue SQL-Query-Vorschläge

### 4. Pattern-Erkennung
- **Aufgabe:** Erkenne Muster in den Daten (z.B. Positionen OHNE AW)
- **Input:** Stempelungs-Daten, Positionen-Daten
- **Output:** Erkannte Muster, Korrelationen

### 5. Code-Review
- **Aufgabe:** Prüfe die Implementierung auf Fehler
- **Input:** Aktueller Code, Dokumentation
- **Output:** Identifizierte Probleme, Verbesserungen

---

## 🔧 Implementierung

### Option 1: API-Endpoint für St-Anteil-Analyse

**Endpoint:** `POST /api/ai/analysiere/st-anteil`

**Request:**
```json
{
  "mechaniker_nr": 5007,
  "von": "2026-01-01",
  "bis": "2026-01-16",
  "locosoft_wert": 4971,
  "drive_wert": 3360,
  "analyse_typ": "vollstaendig"  // oder "schnell", "tief"
}
```

**Response:**
```json
{
  "success": true,
  "analyse": {
    "differenz": 1611,
    "differenz_prozent": 32.4,
    "erkenntnisse": [
      "203 Positionen OHNE AW mit 12049 Min Stempelzeit",
      "43 von 57 Stempelungen gehen auf mehrere Positionen",
      "Zeit-Spanne (3691 Min) ist am nächsten an Locosoft"
    ],
    "hypothesen": [
      "Positionen OHNE AW werden teilweise berücksichtigt (10.6%)",
      "Locosoft verwendet Zeit-Spanne als Basis"
    ],
    "vorschlaege": [
      "Hybrid-Ansatz: Zeit-Spanne + 10.6% Positionen OHNE AW",
      "Bedingte Logik: Unterschiedliche Berechnung je nach Datenstruktur"
    ],
    "sql_vorschlag": "..."
  }
}
```

### Option 2: SQL-Query-Optimierung

**Endpoint:** `POST /api/ai/optimiere/sql-query`

**Request:**
```json
{
  "query": "SELECT ... FROM ...",
  "ziel": "St-Anteil Berechnung",
  "erwartetes_ergebnis": 4971,
  "aktuelles_ergebnis": 3360,
  "kontext": "Mechaniker 5007, 203 Positionen OHNE AW"
}
```

**Response:**
```json
{
  "success": true,
  "optimierung": {
    "probleme": [
      "Anteilige Verteilung reduziert Stempelzeit zu stark",
      "Positionen OHNE AW werden nicht berücksichtigt"
    ],
    "verbesserungen": [
      "Verwende Zeit-Spanne als Basis",
      "Füge Positionen OHNE AW hinzu (10.6%)"
    ],
    "neue_query": "WITH ... SELECT ..."
  }
}
```

### Option 3: Datenanalyse

**Endpoint:** `POST /api/ai/analysiere/daten`

**Request:**
```json
{
  "mechaniker_nr": 5007,
  "von": "2026-01-01",
  "bis": "2026-01-16",
  "analyse_typ": "stempelungen"  // oder "positionen", "auftraege"
}
```

**Response:**
```json
{
  "success": true,
  "analyse": {
    "statistiken": {
      "anzahl_stempelungen": 300,
      "anzahl_positionen": 206,
      "positionen_ohne_aw": 203,
      "stempelungen_mehrere_positionen": 43
    },
    "muster": [
      "75.4% der Stempelungen gehen auf mehrere Positionen",
      "98.5% der Positionen haben keine AW",
      "Stempelzeit auf mehrere Positionen: 2585 Min"
    ],
    "korrelationen": [
      "Mehr Positionen OHNE AW → Größere Abweichung",
      "Mehr Stempelungen auf mehrere Positionen → Größere Abweichung"
    ]
  }
}
```

---

## 📋 Prompt-Vorlagen

### Prompt 1: SQL-Query-Analyse

```
Du bist ein SQL-Experte für PostgreSQL. Analysiere diese SQL-Query für St-Anteil Berechnung:

[SQL-Query einfügen]

Problem:
- Erwartetes Ergebnis: 4971 Min
- Aktuelles Ergebnis: 3360 Min
- Differenz: 1611 Min (32.4%)

Kontext:
- Mechaniker hat 300 Stempelungen auf 206 Positionen
- 203 Positionen OHNE AW (time_units = 0) mit 12049 Min Stempelzeit
- 43 von 57 Stempelungen gehen auf mehrere Positionen

Aufgaben:
1. Identifiziere mögliche Logik-Fehler
2. Erkläre warum die Abweichung so groß ist
3. Schlage Verbesserungen vor
4. Erstelle optimierte SQL-Query
```

### Prompt 2: Datenstruktur-Analyse

```
Du bist ein Datenanalyst. Analysiere diese Datenstruktur:

Mechaniker 5007 (Tobias):
- 300 Stempelungen, 206 Positionen
- 203 Positionen OHNE AW (12049 Min)
- 43 Stempelungen auf mehrere Positionen
- Abweichung: 32.4%

Mechaniker 5014 (Litwin):
- 176 Stempelungen, 148 Positionen
- Weniger Positionen OHNE AW
- 19 Stempelungen auf mehrere Positionen
- Abweichung: 0.2%

Aufgaben:
1. Erkläre warum die Abweichung bei Tobias größer ist
2. Identifiziere kritische Faktoren
3. Schlage Lösungsansätze vor
```

### Prompt 3: Alternative Berechnungslogik

```
Du bist ein SQL-Experte. Basierend auf dieser Analyse:

Getestete Varianten:
- Position-basiert (anteilig): 3360 Min (Diff: 1611 Min)
- OHNE anteilige Verteilung: 3602 Min (Diff: 1369 Min)
- Zeit-Spanne: 3691 Min (Diff: 1280 Min) ← AM NÄCHSTEN!

Erkenntnisse:
- Zeit-Spanne ist am nächsten
- 1280 Min Differenz = 10.6% der Positionen OHNE AW (12049 Min)

Aufgaben:
1. Entwickle Hybrid-Ansatz: Zeit-Spanne + Positionen OHNE AW
2. Erstelle SQL-Query für diesen Ansatz
3. Erkläre die Logik
```

---

## 🚀 Schnellstart

### 1. Test mit LM Studio API

```python
from api.ai_api import lm_studio_client

# SQL-Query-Analyse
messages = [
    {
        "role": "system",
        "content": "Du bist ein SQL-Experte für PostgreSQL und KPI-Berechnungen."
    },
    {
        "role": "user",
        "content": """
        Analysiere diese SQL-Query für St-Anteil Berechnung:
        
        [SQL-Query aus werkstatt_data.py einfügen]
        
        Problem:
        - Erwartet: 4971 Min
        - Aktuell: 3360 Min
        - Differenz: 1611 Min (32.4%)
        
        Kontext:
        - 203 Positionen OHNE AW (12049 Min)
        - 43 Stempelungen auf mehrere Positionen
        
        Aufgaben:
        1. Identifiziere Probleme
        2. Schlage Verbesserungen vor
        3. Erstelle optimierte Query
        """
    }
]

response = lm_studio_client.chat_completion(
    messages=messages,
    max_tokens=2000,
    temperature=0.3
)

print(response['response'])
```

### 2. Direkter API-Call

```bash
curl -X POST http://localhost:5000/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "Du bist ein SQL-Experte."
      },
      {
        "role": "user",
        "content": "Analysiere diese SQL-Query: [Query einfügen]"
      }
    ],
    "max_tokens": 2000,
    "temperature": 0.3
  }'
```

---

## 📊 Erwartete Vorteile

1. **Schnellere Problemanalyse:**
   - KI analysiert SQL-Query automatisch
   - Identifiziert Probleme schneller

2. **Alternative Ansätze:**
   - KI schlägt neue Berechnungslogiken vor
   - Testet verschiedene Varianten

3. **Pattern-Erkennung:**
   - KI erkennt Muster in Daten
   - Findet Korrelationen

4. **Code-Optimierung:**
   - KI optimiert SQL-Queries
   - Verbessert Performance

---

## ⚠️ Wichtige Hinweise

1. **Datenqualität:**
   - KI benötigt korrekte Input-Daten
   - Kontext muss vollständig sein

2. **Validierung:**
   - KI-Vorschläge müssen getestet werden
   - Nicht blind übernehmen

3. **Kombination:**
   - KI + manuelle Analyse = beste Ergebnisse
   - KI als Unterstützung, nicht Ersatz

---

## 🔗 Relevante Dateien

**Dokumentation:**
- `docs/KONTEXT_ST_ANTEIL_PROBLEM_FUER_KI.md` - Kontext für KI
- `docs/VERBESSERUNGSANSATZE_ST_ANTEIL_TAG194.md` - Verbesserungsansätze
- `docs/SUCHE_1369_MIN_DIFFERENZ_TAG194.md` - Systematische Suche

**Code:**
- `api/werkstatt_data.py` - Aktuelle SQL-Query (Zeile 446-588)
- `api/ai_api.py` - LM Studio API Client

**Konfiguration:**
- `config/credentials.json` - LM Studio Config

---

## ✅ Nächste Schritte

1. **Test mit Prompt 1 (SQL-Query-Analyse):**
   - SQL-Query an KI senden
   - Analyse-Ergebnisse prüfen

2. **Test mit Prompt 2 (Datenstruktur-Analyse):**
   - Datenstruktur-Vergleich an KI senden
   - Erkenntnisse sammeln

3. **Test mit Prompt 3 (Alternative Logik):**
   - Hybrid-Ansatz von KI entwickeln lassen
   - SQL-Query generieren lassen

4. **Implementierung:**
   - Beste Vorschläge testen
   - In Code integrieren

---

**Status:** 💡 **Vorschlag - kann sofort getestet werden!**
