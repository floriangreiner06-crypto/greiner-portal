# TT-Zeit-Implementierung: Empfehlung - TAG 195

**Datum:** 2026-01-16  
**Ziel:** Empfehlung für TT-Zeit-Optimierung basierend auf Tests

---

## 📊 TEST-ERGEBNISSE

### SOAP-Tests:
- ✅ SOAP-Verbindung funktioniert
- ❌ Keine Hyundai-spezifischen Methoden für GSW Portal-Daten
- ✅ `labour_operation_id` existiert in Datenbank

### REST API-Tests:
- ✅ Server sind erreichbar
- ✅ Credentials vorhanden (MK / Hyundai_2025)
- ❌ **Web-Firewall blockiert alle API-Requests**
- ⚠️ 2FA verhindert vollautomatische Authentifizierung

---

## 🎯 EMPFEHLUNG: MANUELLE PRÜFUNG + KI-UNTERSTÜTZUNG

### Warum manuelle Prüfung?

1. **Firewall blockiert API:**
   - Automatische API-Integration nicht möglich
   - Firewall-Whitelist würde Zeit benötigen

2. **2FA erforderlich:**
   - Vollautomatische Authentifizierung nicht möglich
   - Serviceberater muss manuell prüfen

3. **Rechtssicherheit:**
   - Manuelle Prüfung durch Serviceberater ist rechtssicher
   - Dokumentation der Prüfung möglich

### KI-Unterstützung:

**KI kann helfen bei:**
- ✅ Begründung: Warum könnte TT-Zeit gerechtfertigt sein?
- ✅ Empfehlung: Basierend auf Diagnose-Komplexität
- ✅ Warnung: "Bitte GSW Portal prüfen!"
- ✅ Dokumentation: Automatische Erstellung der Begründung

---

## 🔧 IMPLEMENTIERUNGS-STRATEGIE

### Workflow:

```
1. Technische Prüfung (automatisch)
   ├─→ Garantieauftrag? ✅
   ├─→ Stempelzeiten vorhanden? ✅
   ├─→ TT-Zeit noch nicht eingereicht? ✅
   └─→ Schadhaften Teil identifiziert? ✅

2. KI-Analyse (automatisch)
   ├─→ Begründung generieren
   ├─→ Empfehlung geben
   └─→ Warnung anzeigen

3. Manuelle Prüfung (Serviceberater)
   ├─→ Serviceberater prüft im GSW Portal
   ├─→ Serviceberater bestätigt: "Keine Arbeitsoperationsnummer"
   └─→ System erlaubt TT-Zeit-Eingabe

4. Dokumentation (automatisch)
   ├─→ Speichere: "TT-Zeit abgerechnet für Teil X"
   ├─→ Speichere: "Manuelle Prüfung bestätigt"
   └─→ Speichere: "KI-Empfehlung: ..."
```

---

## 📋 IMPLEMENTIERUNGS-PLAN

### 1. API-Endpoint erstellen ⏳

**Datei:** `api/ai_api.py`

**Endpoint:**
```python
@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
@login_required
def analysiere_tt_zeit(auftrag_id: int):
    """
    Analysiert ob TT-Zeit möglich ist.
    
    Returns:
    {
        'success': True,
        'technische_pruefung': {...},
        'ki_analyse': {...},
        'warnung': {
            'manuelle_pruefung_erforderlich': True,
            'text': '⚠️ Bitte im GSW Portal prüfen!'
        },
        'tt_zeit_moeglich': None  # Unbekannt, bis manuell bestätigt
    }
    """
```

### 2. Frontend-Integration ⏳

**Button in Arbeitskarte:**
```html
<button onclick="pruefeTTZeit({{ auftrag_id }})">
    TT-Zeit prüfen
</button>
```

**Modal mit:**
- Schadhaften Teil anzeigen
- KI-Empfehlung anzeigen
- Warnung: "Bitte GSW Portal prüfen!"
- Button: "✅ GSW Portal geprüft - Keine Arbeitsoperationsnummer"

### 3. Bestätigung speichern ⏳

**Datenbank:**
```sql
CREATE TABLE tt_zeit_pruefungen (
    id SERIAL PRIMARY KEY,
    auftrag_id INTEGER NOT NULL,
    teilenummer VARCHAR(50),
    ki_empfehlung TEXT,
    manuelle_pruefung_bestaetigt BOOLEAN DEFAULT FALSE,
    bestaetigt_von VARCHAR(100),
    bestaetigt_am TIMESTAMP,
    FOREIGN KEY (auftrag_id) REFERENCES loco_orders(number)
);
```

---

## 💡 VORTEILE DIESER LÖSUNG

1. **Sofort umsetzbar:**
   - Keine Firewall-Whitelist nötig
   - Keine API-Integration nötig
   - Nutzt vorhandene KI-Infrastruktur

2. **Rechtssicher:**
   - Serviceberater prüft manuell
   - Dokumentation der Prüfung
   - Nachvollziehbar

3. **KI-Unterstützung:**
   - Begründung wird generiert
   - Empfehlung basierend auf Daten
   - Serviceberater wird unterstützt

4. **Erweiterbar:**
   - Falls API später verfügbar: Einfach integrierbar
   - Falls SOAP-Methoden verfügbar: Einfach integrierbar

---

## 🚀 NÄCHSTE SCHRITTE

### Sofort umsetzbar:

1. ✅ **API-Endpoint implementieren** (`api/ai_api.py`)
   - Technische Prüfung
   - KI-Analyse
   - Warnung für manuelle Prüfung

2. ✅ **Frontend-Integration**
   - Button in Arbeitskarte
   - Modal mit Warnung
   - Bestätigungs-Button

3. ✅ **Dokumentation**
   - Bestätigung in Datenbank speichern
   - Log der Prüfung

### Optional (später):

4. ⏳ **API-Integration** (falls Firewall-Whitelist)
   - Automatische Prüfung über REST API
   - Fallback auf manuelle Prüfung

5. ⏳ **SOAP-Integration** (falls Methoden verfügbar)
   - Automatische Prüfung über Locosoft SOAP
   - Fallback auf manuelle Prüfung

---

## 📝 ZUSAMMENFASSUNG

**Empfehlung:**
- ✅ **Manuelle Prüfung + KI-Unterstützung** implementieren
- ✅ Sofort umsetzbar, rechtssicher, erweiterbar
- ⏳ API-Integration später möglich (falls Firewall-Whitelist)

**ROI:**
- ~9.000€/Jahr (bis zu 75,87€ pro Auftrag)
- Zeitersparnis durch KI-Unterstützung
- Weniger Fehler durch Warnungen

---

**Erstellt:** TAG 195  
**Status:** Empfehlung erstellt, bereit für Implementierung
