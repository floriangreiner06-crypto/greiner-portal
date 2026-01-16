# TT-Zeit Voraussetzungen - Korrektur TAG 195

**Erstellt:** 2026-01-16  
**Wichtig:** Korrektur der Voraussetzungen basierend auf Handbuch

---

## ⚠️ KRITISCHE KORREKTUR

### Voraussetzung für TT-Zeit-Abrechnung:

**TT-Zeit ist NUR möglich, wenn:**
- ✅ Hyundai **KEINE** Arbeitsoperationsnummer mit Vorgabezeit zu dem **schadhaften Teil** im **GSW Portal** gibt
- ❌ **Pauschale, ungeprüfte Vorschläge sind NICHT abrechenbar**

**Das bedeutet:**
- Es geht **NICHT** um: "Diagnosezeit > Standardarbeitszeit"
- Es geht **UM**: "Gibt es eine Standardarbeitszeit für das schadhaften Teil?"

---

## 🔍 KORREKTE VORAUSSETZUNGEN

### 1. Grundvoraussetzungen (Muss erfüllt sein)

✅ **Garantieauftrag:**
- `charge_type = 60` ODER
- `labour_type IN ('G', 'GS')` ODER
- `invoice_type = 6`

✅ **Schadhaften Teil identifiziert:**
- Teilenummer aus `parts` Tabelle (bei Garantieaufträgen)
- Oder: Schadenverursachendes Teil aus Arbeitskarte

✅ **Prüfung im GSW Portal:**
- **KEINE** Arbeitsoperationsnummer mit Vorgabezeit vorhanden
- **KEINE** Standardarbeitszeit für dieses Teil

✅ **Stempelzeiten vorhanden:**
- Stempelzeiten in `times` Tabelle (type = 2)
- Mindestens eine Stempelung für den Auftrag

✅ **TT-Zeit noch nicht eingereicht:**
- Keine Position mit `labour_operation_id LIKE '%RTT'` oder `'%HTT'`

### 2. Abrechnungsregeln (unverändert)

**Bis 0,9 Stunden (9 AW):** ✅ **OHNE Freigabe** abrechenbar
- **Umrechnung:** 0,9 Stunden = 54 Minuten = 9 AW (1 AW = 6 Minuten)
- **Max. AW:** 9 AW (ohne Freigabe)
- **Vergütung:** Bis zu **75,87€** (9 AW × 8,43€)

**Ab 1,0 Stunden (10 AW):** ⚠️ **Freigabe erforderlich**
- **Umrechnung:** 1,0 Stunden = 60 Minuten = 10 AW
- **Freigabe:** Über GWMS (Antragstyp: T, Freigabetyp: DK)

---

## 🛠️ LÖSUNGSANSÄTZE

### Option 0: Hyundai Portal SOAP/REST API (Prüfen!) ⭐⭐⭐

**Erkenntnis:** Das Hyundai Portal (https://hmd.wa.hyundai-europe.com:9443) nutzt Locosoft SOAP!

**Möglichkeit:**
- Über Locosoft SOAP auf Hyundai Portal-Daten zugreifen
- Prüfen ob Arbeitsoperationsnummern vorhanden sind
- Automatische Prüfung möglich?

**Status:** ⏳ **MUSS GEPRÜFT WERDEN**
- Test-Script: `scripts/test_hyundai_soap_methods.py`
- Prüfe verfügbare SOAP-Methoden
- Prüfe ob Hyundai-spezifische Methoden existieren

**Siehe:** `docs/HYUNDAI_PORTAL_SOAP_ANALYSE_TAG195.md`

---

### Option 1: Manuelle Prüfung durch Serviceberater ⭐ (Fallback)

**Workflow:**
1. System identifiziert schadhaften Teil (aus `parts` Tabelle)
2. System zeigt Warnung: "TT-Zeit möglich? Bitte im GSW Portal prüfen!"
3. Serviceberater prüft manuell im GSW Portal
4. Serviceberater bestätigt: "Keine Arbeitsoperationsnummer vorhanden"
5. System erlaubt TT-Zeit-Eingabe

**Vorteile:**
- ✅ Keine API-Integration nötig
- ✅ Serviceberater hat Kontrolle
- ✅ Rechtssicher (manuelle Prüfung)

**Nachteile:**
- ❌ Manueller Schritt erforderlich
- ❌ Kann vergessen werden

**Implementierung:**
```python
@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
def analysiere_tt_zeit(auftrag_id: int):
    # 1. Identifiziere schadhaften Teil
    schadhaftes_teil = hole_schadhaftes_teil(auftrag_id)
    
    # 2. Prüfe technische Voraussetzungen
    is_garantie = check_garantieauftrag(auftrag_id)
    stempelzeiten = get_stempelzeiten(auftrag_id)
    tt_zeit_vorhanden = check_tt_zeit_vorhanden(auftrag_id)
    
    # 3. KI-Analyse (Begründung, Empfehlung)
    ki_ergebnis = ki_analysiere_tt_zeit(auftrag_id, schadhaftes_teil)
    
    # 4. Ergebnis (mit Warnung für manuelle Prüfung)
    return {
        'tt_zeit_moeglich': is_garantie and stempelzeiten > 0 and not tt_zeit_vorhanden,
        'schadhaftes_teil': schadhaftes_teil,
        'warnung': '⚠️ WICHTIG: Bitte im GSW Portal prüfen, ob Arbeitsoperationsnummer vorhanden ist!',
        'manuelle_pruefung_erforderlich': True,
        'ki_empfehlung': ki_ergebnis
    }
```

---

### Option 2: GSW Portal API-Integration (Falls möglich)

**Voraussetzung:**
- GSW Portal bietet API für Arbeitsoperationsnummer-Suche
- Oder: Web-Scraping möglich (komplex, nicht empfohlen)

**Workflow:**
1. System identifiziert schadhaften Teil
2. System fragt GSW Portal API: "Gibt es Arbeitsoperationsnummer für Teil X?"
3. Wenn NEIN → TT-Zeit möglich
4. Wenn JA → TT-Zeit NICHT möglich

**Vorteile:**
- ✅ Vollautomatisch
- ✅ Kein manueller Schritt

**Nachteile:**
- ❌ API möglicherweise nicht verfügbar
- ❌ Komplexe Integration
- ❌ Rechtliche Unsicherheit (automatische Prüfung)

**Status:** ⏳ **Unbekannt** - Müsste geprüft werden, ob GSW Portal API verfügbar ist

---

### Option 3: Historische Daten-Analyse (KI-gestützt)

**Workflow:**
1. System analysiert historische Garantieaufträge
2. KI lernt: "Für Teil X wurde nie TT-Zeit abgerechnet" → Wahrscheinlich gibt es Standardarbeitszeit
3. KI lernt: "Für Teil Y wurde oft TT-Zeit abgerechnet" → Wahrscheinlich gibt es KEINE Standardarbeitszeit
4. System gibt Empfehlung basierend auf historischen Daten

**Vorteile:**
- ✅ Nutzt vorhandene Daten
- ✅ Lernen aus Erfahrung

**Nachteile:**
- ❌ Nicht 100% sicher
- ❌ Neue Teile nicht erkannt
- ❌ Rechtlich unsicher (nur Empfehlung)

**Status:** ⏳ **Möglich, aber nicht empfohlen** - Nur als zusätzliche Information

---

## 🎯 EMPFOHLENE LÖSUNG

### Kombination: Technische Prüfung + Manuelle Bestätigung

**Workflow:**

1. **Technische Prüfung (automatisch):**
   - ✅ Garantieauftrag?
   - ✅ Stempelzeiten vorhanden?
   - ✅ TT-Zeit noch nicht eingereicht?
   - ✅ Schadhaften Teil identifiziert?

2. **KI-Analyse (automatisch):**
   - Begründung: Warum könnte TT-Zeit gerechtfertigt sein?
   - Empfehlung: Basierend auf Diagnose-Komplexität
   - Warnung: "Bitte GSW Portal prüfen!"

3. **Manuelle Prüfung (Serviceberater):**
   - Serviceberater prüft im GSW Portal
   - Serviceberater bestätigt: "Keine Arbeitsoperationsnummer vorhanden"
   - System erlaubt TT-Zeit-Eingabe

4. **Dokumentation:**
   - System speichert: "TT-Zeit abgerechnet für Teil X"
   - System speichert: "Manuelle Prüfung bestätigt: Keine Arbeitsoperationsnummer"

---

## 📊 ENTSCHEIDUNGSBAUM (KORRIGIERT)

```
TT-Zeit-Analyse starten
    │
    ├─→ Ist Garantieauftrag?
    │       │
    │       ├─→ Nein → ❌ TT-Zeit nicht möglich
    │       │
    │       └─→ Ja → Weiter
    │
    ├─→ Schadhaften Teil identifiziert?
    │       │
    │       ├─→ Nein → ⚠️ Teil muss identifiziert werden
    │       │
    │       └─→ Ja → Weiter
    │
    ├─→ Gibt es Stempelzeiten?
    │       │
    │       ├─→ Nein → ❌ TT-Zeit nicht möglich
    │       │
    │       └─→ Ja → Weiter
    │
    ├─→ TT-Zeit bereits eingereicht?
    │       │
    │       ├─→ Ja → ℹ️ TT-Zeit bereits vorhanden
    │       │
    │       └─→ Nein → Weiter
    │
    ├─→ ⚠️ MANUELLE PRÜFUNG ERFORDERLICH
    │       │
    │       ├─→ Serviceberater prüft GSW Portal
    │       │
    │       ├─→ Arbeitsoperationsnummer vorhanden?
    │       │       │
    │       │       ├─→ Ja → ❌ TT-Zeit NICHT möglich
    │       │       │
    │       │       └─→ Nein → ✅ TT-Zeit möglich
    │       │
    │       └─→ Serviceberater bestätigt Prüfung
    │
    └─→ TT-Zeit erfassen (wenn bestätigt)
```

---

## 🔧 IMPLEMENTIERUNG

### 1. Schadhaften Teil identifizieren

```python
def hole_schadhaftes_teil(auftrag_id: int) -> Optional[Dict]:
    """
    Identifiziert das schadhaften Teil für einen Garantieauftrag.
    
    Quellen:
    - parts Tabelle (bei Garantieaufträgen)
    - Arbeitskarte (schadenverursachendes Teil)
    - GUDAT (Mechaniker-Notizen)
    """
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    # Hole Teile für Garantieauftrag
    cursor.execute("""
        SELECT 
            p.part_number,
            pm.description,
            p.amount,
            p.is_invoiced
        FROM parts p
        LEFT JOIN parts_master pm ON p.part_number = pm.part_number
        WHERE p.order_number = %s
          AND p.invoice_type = 6  -- Garantie
        ORDER BY p.order_position
        LIMIT 1
    """, [auftrag_id])
    
    teil = cursor.fetchone()
    conn.close()
    
    if teil:
        return {
            'teilenummer': teil[0],
            'beschreibung': teil[1],
            'menge': teil[2],
            'abgerechnet': teil[3]
        }
    
    return None
```

### 2. API-Endpoint mit Warnung

```python
@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
@login_required
def analysiere_tt_zeit(auftrag_id: int):
    """
    Analysiert ob TT-Zeit für einen Garantieauftrag abgerechnet werden kann.
    
    WICHTIG: Manuelle Prüfung im GSW Portal erforderlich!
    """
    try:
        # 1. Technische Prüfung
        is_garantie = check_garantieauftrag(auftrag_id)
        stempelzeiten = get_stempelzeiten(auftrag_id)
        tt_zeit_vorhanden = check_tt_zeit_vorhanden(auftrag_id)
        schadhaftes_teil = hole_schadhaftes_teil(auftrag_id)
        
        # 2. KI-Analyse (Begründung, Empfehlung)
        ki_ergebnis = ki_analysiere_tt_zeit(auftrag_id, schadhaftes_teil)
        
        # 3. Ergebnis mit Warnung
        ergebnis = {
            'success': True,
            'auftrag_id': auftrag_id,
            'technische_pruefung': {
                'is_garantie': is_garantie,
                'stempelzeiten_vorhanden': stempelzeiten > 0,
                'tt_zeit_vorhanden': tt_zeit_vorhanden,
                'schadhaftes_teil': schadhaftes_teil
            },
            'ki_analyse': ki_ergebnis,
            'warnung': {
                'manuelle_pruefung_erforderlich': True,
                'text': '⚠️ WICHTIG: Bitte im GSW Portal prüfen, ob für Teil {} eine Arbeitsoperationsnummer mit Vorgabezeit vorhanden ist!'.format(
                    schadhaftes_teil.get('teilenummer', 'unbekannt') if schadhaftes_teil else 'unbekannt'
                ),
                'hinweis': 'TT-Zeit ist nur möglich, wenn KEINE Arbeitsoperationsnummer vorhanden ist!'
            },
            'tt_zeit_moeglich': (
                is_garantie and 
                stempelzeiten > 0 and 
                not tt_zeit_vorhanden and
                schadhaftes_teil is not None
                # ⚠️ Manuelle Bestätigung erforderlich!
            )
        }
        
        return jsonify(ergebnis)
        
    except Exception as e:
        logger.error(f"Fehler bei TT-Zeit-Analyse: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 3. Frontend-Integration

**Button in Arbeitskarte-Ansicht:**
```html
<button onclick="pruefeTTZeit({{ auftrag_id }})">
    TT-Zeit prüfen
</button>
```

**Modal mit Warnung:**
```html
<div class="modal">
    <h4>TT-Zeit-Analyse</h4>
    <p><strong>Schadhaften Teil:</strong> {{ teilenummer }} - {{ beschreibung }}</p>
    <div class="alert alert-warning">
        ⚠️ <strong>WICHTIG:</strong> Bitte im GSW Portal prüfen, ob für dieses Teil 
        eine Arbeitsoperationsnummer mit Vorgabezeit vorhanden ist!
    </div>
    <p><strong>KI-Empfehlung:</strong> {{ ki_empfehlung }}</p>
    <button onclick="bestätigeGSWPruefung()">
        ✅ GSW Portal geprüft - Keine Arbeitsoperationsnummer vorhanden
    </button>
</div>
```

---

## 📝 ZUSAMMENFASSUNG

### Korrekte Voraussetzungen:

1. ✅ **Garantieauftrag**
2. ✅ **Schadhaften Teil identifiziert**
3. ✅ **Stempelzeiten vorhanden**
4. ✅ **TT-Zeit noch nicht eingereicht**
5. ⚠️ **Manuelle Prüfung:** KEINE Arbeitsoperationsnummer im GSW Portal

### Empfohlene Lösung:

- **Technische Prüfung:** Automatisch (System)
- **GSW Portal Prüfung:** Manuell (Serviceberater)
- **KI-Analyse:** Unterstützung (Begründung, Empfehlung)
- **Dokumentation:** System speichert Bestätigung

### Nächste Schritte:

1. ✅ Schadhaften Teil identifizieren (aus `parts` Tabelle)
2. ✅ API-Endpoint mit Warnung implementieren
3. ✅ Frontend-Integration mit Bestätigungs-Button
4. ⏳ GSW Portal API prüfen (falls verfügbar, optional)

---

**Erstellt:** TAG 195  
**Status:** Korrigiert, bereit für Implementierung mit manueller Prüfung
