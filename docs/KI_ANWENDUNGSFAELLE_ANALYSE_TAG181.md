# KI-Anwendungsfälle für DRIVE - Analyse TAG 181

**Erstellt:** 2026-01-12 (TAG 181)  
**Ziel:** Identifikation sinnvoller KI-Anwendungsfälle für lokale OpenAI-Integration

---

## 📋 ÜBERBLICK

Diese Analyse identifiziert konkrete Anwendungsfälle für eine lokale KI (OpenAI-Schnittstelle) im DRIVE-System. Fokus liegt auf:
- **Automatisierung** manueller Prüf- und Dokumentationsaufgaben
- **Qualitätssicherung** durch intelligente Validierung
- **Effizienzsteigerung** durch intelligente Klassifikation und Analyse

---

## 🎯 PRIORITÄT 1: WERKSTATT & GARANTIE

### 1.1 Werkstattauftrag-Dokumentationsprüfung ⭐⭐⭐

**Problem:**
- Arbeitskarten müssen vollständig dokumentiert sein (Hyundai-Richtlinie)
- Manuelle Prüfung auf Vollständigkeit ist zeitaufwendig
- Fehlende Dokumentation führt zu Garantie-Ablehnungen

**KI-Lösung:**
- **Automatische Vollständigkeitsprüfung** der Arbeitskarte:
  - Diagnose vorhanden?
  - Reparaturmaßnahme dokumentiert?
  - TT-Zeiten erfasst?
  - Teile-Nummern angegeben?
  - Kundenangabe (O-Ton) vorhanden?
- **Qualitätsbewertung:** KI bewertet Dokumentationsqualität (0-100%)
- **Automatische Warnungen:** Bei unvollständiger Dokumentation

**Datenquellen:**
- `orders` (Locosoft) - Auftragsdaten
- `labours` (Locosoft) - Arbeitspositionen
- `gudat` (GUDAT) - Mechaniker-Notizen
- `arbeitskarte` (DRIVE) - Arbeitskarten-Dokumentation

**Nutzen:**
- ⏱️ **Zeitersparnis:** 5-10 Min pro Auftrag → automatisch
- 💰 **Kostenersparnis:** Weniger Garantie-Ablehnungen
- ✅ **Qualität:** Konsistente Dokumentation

**Technische Umsetzung:**
```python
# Pseudo-Code
def pruefe_arbeitskarte_vollstaendigkeit(auftrag_id):
    auftrag_daten = hole_auftrag_daten(auftrag_id)
    dokumentation = hole_dokumentation(auftrag_id)
    
    prompt = f"""
    Prüfe die Vollständigkeit der Arbeitskarte für Auftrag {auftrag_id}:
    
    Auftragsdaten: {auftrag_daten}
    Dokumentation: {dokumentation}
    
    Prüfe:
    1. Diagnose vorhanden?
    2. Reparaturmaßnahme dokumentiert?
    3. TT-Zeiten erfasst?
    4. Teile-Nummern angegeben?
    5. Kundenangabe (O-Ton) vorhanden?
    
    Gib eine Bewertung (0-100%) und fehlende Elemente zurück.
    """
    
    ergebnis = openai_api.analyze(prompt)
    return ergebnis
```

---

### 1.2 Garantie-Dokumentationsprüfung ⭐⭐⭐

**Problem:**
- Garantieanträge müssen vollständig sein (21-Tage-Frist)
- Fehlende Dokumentation führt zu Ablehnungen
- Manuelle Prüfung vor Einreichung erforderlich

**KI-Lösung:**
- **Automatische Prüfung vor GWMS-Einreichung:**
  - Alle erforderlichen Felder vorhanden?
  - DTC-Codes dokumentiert?
  - Fotos vorhanden (wenn nötig)?
  - Arbeitskarte vollständig?
- **Risikobewertung:** KI bewertet Erfolgswahrscheinlichkeit
- **Automatische Empfehlungen:** Was fehlt noch?

**Datenquellen:**
- `garantie_akte` (DRIVE) - Garantie-Dokumentation
- `orders` (Locosoft) - Auftragsdaten
- `gudat` (GUDAT) - Diagnose-Daten

**Nutzen:**
- ⏱️ **Zeitersparnis:** 10-15 Min pro Garantieantrag
- 💰 **Kostenersparnis:** Höhere Erfolgsquote bei Einreichungen
- ✅ **Qualität:** Weniger Nachforderungen

---

### 1.3 Automatische Fehlerklassifikation ⭐⭐

**Problem:**
- Mechaniker-Notizen sind unstrukturiert
- Fehler müssen manuell kategorisiert werden
- Keine automatische Priorisierung

**KI-Lösung:**
- **Automatische Klassifikation** von Fehlern:
  - Fehlertyp (Motor, Elektrik, Karosserie, etc.)
  - Dringlichkeit (kritisch, normal, niedrig)
  - Komplexität (einfach, mittel, komplex)
- **Vorschläge für Diagnose-Schritte**
- **Automatische Zuordnung** zu Spezialisten

**Datenquellen:**
- `gudat.description` - Mechaniker-Notizen
- `orders.order_text` - Kundenangabe
- `labours` - Arbeitspositionen

**Nutzen:**
- ⏱️ **Effizienz:** Schnellere Auftragsverteilung
- ✅ **Qualität:** Konsistente Klassifikation

---

## 🎯 PRIORITÄT 2: REKLAMATIONEN & KUNDENBEZIEHUNGEN

### 2.1 Reklamationsbewertung ⭐⭐⭐

**Problem:**
- Reklamationen müssen rechtlich bewertet werden
- Manuelle Bewertung ist zeitaufwendig (siehe `docs/reklamationen/`)
- Risikobewertung erforderlich

**KI-Lösung:**
- **Automatische rechtliche Bewertung:**
  - Gewährleistungsfrist prüfen
  - Beweislastumkehr prüfen (6 Monate)
  - Mangelbegriff prüfen
  - Risikobewertung (niedrig, mittel, hoch)
- **Automatische Empfehlungen:**
  - Gewährleistung annehmen/ablehnen?
  - Kulanzlösung empfehlen?
  - Versicherung empfehlen?

**Datenquellen:**
- Reklamationsdaten (DRIVE)
- Verkaufsdaten (Locosoft)
- Auftragshistorie (Locosoft)

**Nutzen:**
- ⏱️ **Zeitersparnis:** 20-30 Min pro Reklamation → automatisch
- ✅ **Konsistenz:** Einheitliche Bewertungskriterien
- 💰 **Risikominimierung:** Bessere Entscheidungsgrundlage

**Beispiel aus Dokumentation:**
- `docs/reklamationen/kunde_3008334_steinschlag_bewertung.md`
- KI könnte diese Bewertung automatisch durchführen

---

### 2.2 Kundenkommunikation-Analyse ⭐

**Problem:**
- Kundenanfragen müssen manuell kategorisiert werden
- Keine automatische Priorisierung

**KI-Lösung:**
- **Automatische Kategorisierung** von Kundenanfragen:
  - Thema (Rechnung, Termin, Reklamation, etc.)
  - Dringlichkeit
  - Zugehöriger Auftrag/Fahrzeug
- **Automatische Antwortvorschläge**

**Nutzen:**
- ⏱️ **Effizienz:** Schnellere Bearbeitung
- ✅ **Konsistenz:** Einheitliche Kategorisierung

---

## 🎯 PRIORITÄT 3: BANKENSPIEGEL & FINANZEN

### 3.1 Transaktions-Kategorisierung ⭐⭐

**Problem:**
- Transaktionen müssen manuell kategorisiert werden
- `kategorie`-Feld in `transaktionen`-Tabelle
- Zeitaufwendig bei vielen Transaktionen

**KI-Lösung:**
- **Automatische Kategorisierung** basierend auf:
  - `buchungstext`
  - `verwendungszweck`
  - Betrag
  - Konto
- **Vorschläge für Kategorien:**
  - Materialaufwand
  - Personalkosten
  - Miete
  - Versicherung
  - etc.

**Datenquellen:**
- `transaktionen` (DRIVE) - Banktransaktionen
- `konten` (DRIVE) - Kontoinformationen

**Nutzen:**
- ⏱️ **Zeitersparnis:** 2-5 Min pro Transaktion → automatisch
- ✅ **Konsistenz:** Einheitliche Kategorisierung
- 📊 **Buchhaltung:** Schnellere Buchhaltungsabschlüsse

**Technische Umsetzung:**
```python
def kategorisiere_transaktion(transaktion):
    prompt = f"""
    Kategorisiere diese Banktransaktion:
    
    Buchungstext: {transaktion['buchungstext']}
    Verwendungszweck: {transaktion['verwendungszweck']}
    Betrag: {transaktion['betrag']} €
    Konto: {transaktion['kontoname']}
    
    Mögliche Kategorien:
    - Materialaufwand
    - Personalkosten
    - Miete
    - Versicherung
    - Steuern
    - Sonstiges
    
    Gib die passende Kategorie zurück.
    """
    
    kategorie = openai_api.categorize(prompt)
    return kategorie
```

---

### 3.2 Anomalie-Erkennung bei Transaktionen ⭐⭐

**Problem:**
- Ungewöhnliche Transaktionen müssen manuell erkannt werden
- Fehlerhafte Buchungen werden spät entdeckt

**KI-Lösung:**
- **Automatische Anomalie-Erkennung:**
  - Ungewöhnliche Beträge
  - Ungewöhnliche Kategorien
  - Ungewöhnliche Zeitpunkte
  - Ungewöhnliche Verwendungszwecke
- **Automatische Warnungen** bei verdächtigen Transaktionen

**Nutzen:**
- ✅ **Sicherheit:** Früherkennung von Fehlern
- 💰 **Kostenersparnis:** Weniger fehlerhafte Buchungen

---

### 3.3 Verwendungszweck-Analyse ⭐

**Problem:**
- Verwendungszwecke sind oft unklar formuliert
- Manuelle Interpretation erforderlich

**KI-Lösung:**
- **Automatische Interpretation** von Verwendungszwecken:
  - Strukturierung unklarer Texte
  - Extraktion relevanter Informationen
  - Vorschläge für bessere Kategorisierung

**Nutzen:**
- ⏱️ **Effizienz:** Schnellere Bearbeitung
- ✅ **Qualität:** Bessere Datenqualität

---

## 🎯 PRIORITÄT 4: CONTROLLING & BWA

### 4.1 Automatische Kontenzuordnung ⭐

**Problem:**
- Buchungen müssen manuell Konten zugeordnet werden
- Fehlerhafte Zuordnungen führen zu falschen BWA-Werten

**KI-Lösung:**
- **Automatische Kontenzuordnung** basierend auf:
  - Buchungstext
  - Verwendungszweck
  - Betrag
  - Historie
- **Vorschläge für Konten** (SKR51-Kontenrahmen)

**Datenquellen:**
- `transaktionen` (DRIVE)
- `konten` (DRIVE)
- `SKR51_KONTOBEZEICHNUNGEN` (controlling_api.py)

**Nutzen:**
- ⏱️ **Zeitersparnis:** 3-5 Min pro Buchung
- ✅ **Konsistenz:** Einheitliche Zuordnung
- 📊 **BWA:** Korrektere BWA-Werte

---

### 4.2 BWA-Anomalie-Erkennung ⭐

**Problem:**
- Ungewöhnliche BWA-Werte müssen manuell erkannt werden
- Abweichungen werden spät entdeckt

**KI-Lösung:**
- **Automatische Anomalie-Erkennung** in BWA:
  - Ungewöhnliche Abweichungen zum Vorjahr
  - Ungewöhnliche Abweichungen zum Plan
  - Ungewöhnliche Kontenwerte
- **Automatische Warnungen** bei verdächtigen Werten

**Nutzen:**
- ✅ **Früherkennung:** Probleme werden früher erkannt
- 📊 **BWA:** Korrektere BWA-Werte

---

## 🎯 PRIORITÄT 5: VERKAUF & FAHRZEUGVERWALTUNG

### 5.1 Fahrzeugbeschreibung-Generierung ⭐

**Problem:**
- Fahrzeugbeschreibungen müssen manuell geschrieben werden
- Zeitaufwendig für Verkaufsplattformen

**KI-Lösung:**
- **Automatische Generierung** von Fahrzeugbeschreibungen:
  - Basierend auf Fahrzeugdaten
  - Marktgerechte Formulierung
  - SEO-optimiert
- **Vorschläge für Verkaufsargumente**

**Datenquellen:**
- `fahrzeuge` (Locosoft) - Fahrzeugdaten
- Verkaufsdaten (Locosoft)

**Nutzen:**
- ⏱️ **Zeitersparnis:** 10-15 Min pro Fahrzeug
- ✅ **Qualität:** Konsistente Beschreibungen

---

### 5.2 Standzeit-Analyse & Empfehlungen ⭐

**Problem:**
- Fahrzeuge mit langer Standzeit müssen identifiziert werden
- Manuelle Analyse erforderlich

**KI-Lösung:**
- **Automatische Analyse** der Standzeit:
  - Gründe für lange Standzeit identifizieren
  - Empfehlungen für Preisreduktion
  - Empfehlungen für Marketing-Maßnahmen

**Datenquellen:**
- `fahrzeuge` (Locosoft) - Fahrzeugdaten
- Verkaufsdaten (Locosoft)

**Nutzen:**
- 💰 **Umsatz:** Schnellere Fahrzeugverkäufe
- 📊 **Lagerumschlag:** Bessere Lagerumschlag-Zahlen

---

## 📊 ZUSAMMENFASSUNG: TOP 5 USE CASES

| Priorität | Use Case | Zeitersparnis | Nutzen | Komplexität |
|-----------|----------|---------------|--------|-------------|
| 1 | **Werkstattauftrag-Dokumentationsprüfung** | 5-10 Min/Auftrag | ⭐⭐⭐ | Mittel |
| 2 | **Garantie-Dokumentationsprüfung** | 10-15 Min/Antrag | ⭐⭐⭐ | Mittel |
| 3 | **Reklamationsbewertung** | 20-30 Min/Reklamation | ⭐⭐⭐ | Hoch |
| 4 | **Transaktions-Kategorisierung** | 2-5 Min/Transaktion | ⭐⭐ | Niedrig |
| 5 | **Automatische Fehlerklassifikation** | 3-5 Min/Auftrag | ⭐⭐ | Mittel |

---

## 🛠️ TECHNISCHE UMSETZUNG

### API-Struktur

**Externe OpenAI-Schnittstelle:**
- API-Key wird über `config/credentials.json` bereitgestellt
- API-URL konfigurierbar (z.B. OpenAI API oder lokale Instanz)
- Fehlerbehandlung und Retry-Logik implementiert

```python
# api/ai_api.py
from flask import Blueprint, jsonify, request
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

ai_api = Blueprint('ai_api', __name__, url_prefix='/api/ai')

# OpenAI Client
class OpenAIClient:
    """Client für externe OpenAI-Schnittstelle"""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.api_url = self._load_api_url()
    
    def _load_api_key(self):
        """Lädt API-Key aus credentials.json"""
        creds_file = 'config/credentials.json'
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                    if 'openai' in creds:
                        return creds['openai'].get('api_key')
            except Exception as e:
                logger.error(f"Fehler beim Laden der OpenAI-Credentials: {e}")
        
        # Fallback: Environment Variable
        return os.getenv('OPENAI_API_KEY')
    
    def _load_api_url(self):
        """Lädt API-URL aus credentials.json"""
        creds_file = 'config/credentials.json'
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                    if 'openai' in creds:
                        return creds['openai'].get('api_url', 'https://api.openai.com/v1')
            except Exception as e:
                logger.error(f"Fehler beim Laden der OpenAI-URL: {e}")
        
        # Fallback: Environment Variable oder Default
        return os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1')
    
    def analyze(self, prompt: str, model: str = 'gpt-4', max_tokens: int = 500):
        """Sendet Prompt an OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'Du bist ein hilfreicher Assistent für ein Autohaus-Management-System.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': 0.3  # Niedrigere Temperatur für konsistentere Ergebnisse
        }
        
        try:
            response = requests.post(
                f'{self.api_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Fehler bei OpenAI API-Call: {e}")
            raise

# Globale Client-Instanz
openai_client = OpenAIClient()

@ai_api.route('/pruefe/arbeitskarte/<int:auftrag_id>', methods=['POST'])
def pruefe_arbeitskarte(auftrag_id):
    """Prüft Vollständigkeit der Arbeitskarte"""
    # ... Implementierung

@ai_api.route('/kategorisiere/transaktion', methods=['POST'])
def kategorisiere_transaktion():
    """Kategorisiert eine Transaktion"""
    # ... Implementierung

@ai_api.route('/bewerte/reklamation', methods=['POST'])
def bewerte_reklamation():
    """Bewertet eine Reklamation rechtlich"""
    # ... Implementierung
```

### Konfiguration

**`config/credentials.json`:**
```json
{
  "openai": {
    "api_key": "sk-...",
    "api_url": "https://api.openai.com/v1"
  }
}
```

**Alternative: Environment Variables:**
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_API_URL="https://api.openai.com/v1"
```

### Integration in bestehende Module

**Werkstatt:**
- `api/werkstatt_api.py` → KI-Prüfung bei Auftragserstellung
- `api/arbeitskarte_api.py` → KI-Prüfung bei Arbeitskarte-Erstellung

**Garantie:**
- `api/garantie_soap_api.py` → KI-Prüfung vor GWMS-Einreichung

**Bankenspiegel:**
- `api/bankenspiegel_api.py` → KI-Kategorisierung bei Import

**Controlling:**
- `api/controlling_api.py` → KI-Kontenzuordnung bei Buchungen

---

## 💰 ROI-ABSCHÄTZUNG

### Werkstattauftrag-Dokumentationsprüfung

**Annahmen:**
- 50 Aufträge/Tag
- 5 Min manuelle Prüfung pro Auftrag
- 250 Min/Tag = 4,2 Stunden/Tag
- 20 Arbeitstage/Monat = 84 Stunden/Monat

**Ersparnis:**
- 84 Stunden/Monat = **~2.000€/Monat** (bei 25€/Stunde)
- **~24.000€/Jahr**

### Reklamationsbewertung

**Annahmen:**
- 10 Reklamationen/Monat
- 25 Min manuelle Bewertung pro Reklamation
- 250 Min/Monat = 4,2 Stunden/Monat

**Ersparnis:**
- 4,2 Stunden/Monat = **~100€/Monat**
- **~1.200€/Jahr**

### Transaktions-Kategorisierung

**Annahmen:**
- 500 Transaktionen/Monat
- 3 Min manuelle Kategorisierung pro Transaktion
- 1.500 Min/Monat = 25 Stunden/Monat

**Ersparnis:**
- 25 Stunden/Monat = **~625€/Monat**
- **~7.500€/Jahr**

**Gesamt-ROI:**
- **~32.700€/Jahr** Zeitersparnis
- **+ Qualitätsverbesserung** (weniger Fehler, höhere Erfolgsquote)

---

## 🚀 NÄCHSTE SCHRITTE

### Phase 1: Proof of Concept (2-4 Wochen)

1. **Externe OpenAI-Schnittstelle konfigurieren**
   - API-Key in `config/credentials.json` hinterlegen
   - API-URL konfigurieren (falls abweichend)
   - API-Client implementieren (`api/ai_api.py`)

2. **Ersten Use Case implementieren:**
   - **Werkstattauftrag-Dokumentationsprüfung** (höchste Priorität)
   - Integration in `api/werkstatt_api.py`
   - Test mit echten Daten

3. **Evaluation:**
   - Genauigkeit prüfen
   - Zeitersparnis messen
   - Feedback sammeln

### Phase 2: Erweiterung (4-8 Wochen)

1. **Weitere Use Cases implementieren:**
   - Garantie-Dokumentationsprüfung
   - Transaktions-Kategorisierung
   - Reklamationsbewertung

2. **Integration in bestehende Workflows:**
   - Automatische Prüfung bei Auftragserstellung
   - Automatische Warnungen bei unvollständiger Dokumentation

### Phase 3: Optimierung (laufend)

1. **Model-Fine-Tuning:**
   - Auf DRIVE-spezifische Daten trainieren
   - Genauigkeit verbessern

2. **Weitere Use Cases:**
   - Basierend auf Feedback
   - Neue Anforderungen

---

## ⚠️ HERAUSFORDERUNGEN

### Technisch

1. **API-Verfügbarkeit:**
   - Externe API muss erreichbar sein
   - Timeout-Handling implementieren
   - Retry-Logik bei Fehlern

2. **Performance:**
   - Antwortzeiten akzeptabel? (< 5 Sekunden)
   - Parallelisierung möglich?

3. **Integration:**
   - Bestehende APIs erweitern
   - Keine Breaking Changes

### Organisatorisch

1. **Akzeptanz:**
   - Mitarbeiter vertrauen KI-Ergebnissen?
   - Feedback-Mechanismus etablieren

2. **Qualitätssicherung:**
   - KI-Ergebnisse müssen überprüfbar sein
   - Manuelle Korrektur möglich

3. **API-Kosten:**
   - Kosten pro Request überwachen
   - Rate-Limiting implementieren
   - Caching für wiederkehrende Anfragen

4. **Dokumentation:**
   - KI-Entscheidungen nachvollziehbar
   - Logging und Audit-Trail

---

## 📝 FAZIT

**KI-Integration (externe OpenAI-Schnittstelle) macht Sinn für:**

✅ **Werkstatt & Garantie:**
- Dokumentationsprüfung (höchste Priorität)
- Automatische Qualitätssicherung
- **ROI: ~24.000€/Jahr**

✅ **Reklamationen:**
- Rechtliche Bewertung
- Risikobewertung
- **ROI: ~1.200€/Jahr**

✅ **Bankenspiegel:**
- Transaktions-Kategorisierung
- Anomalie-Erkennung
- **ROI: ~7.500€/Jahr**

**Gesamt-ROI: ~32.700€/Jahr + Qualitätsverbesserung**

**Empfehlung:**
1. **Start mit Werkstattauftrag-Dokumentationsprüfung** (höchster ROI)
2. **Proof of Concept** mit externer OpenAI-Schnittstelle
3. **Schrittweise Erweiterung** auf weitere Use Cases

**Technische Voraussetzungen:**
- API-Key in `config/credentials.json` hinterlegen
- API-Client implementieren (`api/ai_api.py`)
- Integration in bestehende Module

---

**Erstellt von:** Claude AI  
**Datum:** 2026-01-12  
**Status:** Analyse abgeschlossen, bereit für Implementierung
