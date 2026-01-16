# TT-Zeit-Optimierung: Implementierungsstrategie - TAG 195

**Erstellt:** 2026-01-16  
**Basis:** Hyundai Garantie-Richtlinie + LM Studio Integration

---

## 📋 ÜBERBLICK

**Ziel:** Automatische KI-gestützte Analyse, ob TT-Zeit für einen Garantieauftrag abgerechnet werden kann.

**ROI:** ~9.000€/Jahr (bis zu 75,87€ pro Auftrag)

---

## 🔍 VORAUSSETZUNGEN FÜR TT-ZEIT-ABRECHNUNG

### 1. Grundvoraussetzungen (Muss erfüllt sein)

✅ **Garantieauftrag:**
- `charge_type = 60` ODER
- `labour_type IN ('G', 'GS')` ODER
- `invoice_type = 6`

✅ **Stempelzeiten vorhanden:**
- Stempelzeiten in `times` Tabelle (type = 2)
- Mindestens eine Stempelung für den Auftrag

✅ **Diagnosezeit > Standardarbeitszeit:**
- Tatsächliche Stempelzeit > Vorgabe AW (aus `labours.time_units`)
- Oder: Diagnosezeit deutlich höher als erwartet

### 2. Abrechnungsregeln

**Bis 0,9 Stunden (9 AW):** ✅ **OHNE Freigabe** abrechenbar
- **Umrechnung:** 0,9 Stunden = 54 Minuten = 9 AW (1 AW = 6 Minuten)
- **Max. AW:** 9 AW (ohne Freigabe)
- **Vergütung:** Bis zu **75,87€** (9 AW × 8,43€)

**Ab 1,0 Stunden (10 AW):** ⚠️ **Freigabe erforderlich**
- **Umrechnung:** 1,0 Stunden = 60 Minuten = 10 AW
- **Freigabe:** Über GWMS (Antragstyp: T, Freigabetyp: DK)
- **Voraussetzung:** Technik Master hat Diagnose durchgeführt

### 3. Berechnungslogik

```python
# 1. Prüfe ob Garantieauftrag
is_garantie = (
    charge_type == 60 OR
    labour_type IN ('G', 'GS') OR
    invoice_type == 6
)

# 2. Hole Stempelzeiten
stempelzeiten_min = SUM(end_time - start_time) FROM times
    WHERE order_number = X AND type = 2

# 3. Hole Standardarbeitszeit (Vorgabe AW)
vorgabe_aw = SUM(time_units) FROM labours
    WHERE order_number = X AND time_units > 0

# 4. Berechne Diagnosezeit
diagnose_min = stempelzeiten_min - (vorgabe_aw * 6)  # 1 AW = 6 Min
diagnose_aw = diagnose_min / 6

# 5. Prüfe ob TT-Zeit bereits eingereicht
tt_zeit_vorhanden = EXISTS(
    SELECT 1 FROM labours
    WHERE order_number = X
      AND (labour_operation_id LIKE '%RTT' OR labour_operation_id LIKE '%HTT')
)

# 6. Entscheidung
if is_garantie AND stempelzeiten_min > 0 AND diagnose_aw > 0:
    if diagnose_aw <= 9 AND NOT tt_zeit_vorhanden:
        # ✅ TT-Zeit möglich (bis 9 AW ohne Freigabe)
        empfehlung = "TT-Zeit erfassen: +" + (diagnose_aw * 8.43) + "€"
    elif diagnose_aw > 9:
        # ⚠️ Freigabe erforderlich
        empfehlung = "TT-Zeit möglich, aber Freigabe erforderlich (> 9 AW)"
    else:
        # ℹ️ TT-Zeit bereits eingereicht
        empfehlung = "TT-Zeit bereits eingereicht"
else:
    # ❌ Keine TT-Zeit möglich
    empfehlung = "TT-Zeit nicht möglich (kein Garantieauftrag oder keine Diagnosezeit)"
```

---

## 🤖 KI-GESTÜTZTE ENTSCHEIDUNG

### Warum KI?

Die KI kann zusätzliche Kontext-Informationen berücksichtigen:

1. **Diagnose-Komplexität analysieren:**
   - Mechaniker-Notizen (GUDAT `description`)
   - Kundenangabe (O-Ton)
   - Fehlercodes (DTC)
   - Arbeitspositionen

2. **Begründung generieren:**
   - Warum ist TT-Zeit gerechtfertigt?
   - Was wurde diagnostiziert?
   - Warum dauerte es länger?

3. **Empfehlungen geben:**
   - Sollte TT-Zeit erfasst werden? (Ja/Nein)
   - Wie viele AW? (max. 9 ohne Freigabe)
   - Begründung für die Abrechnung

### KI-Prompt-Struktur

```python
prompt = f"""
Analysiere ob TT-Zeit für Garantieauftrag {auftrag_id} abgerechnet werden kann:

Auftragsdaten:
- Auftragsnummer: {auftrag_id}
- Garantieauftrag: {is_garantie}
- Marke: {marke} (Hyundai/Stellantis)

Zeiterfassung:
- Stempelzeiten gesamt: {stempelzeiten_min} Minuten ({stempelzeiten_aw} AW)
- Standardarbeitszeit (Vorgabe): {vorgabe_aw} AW
- Diagnosezeit: {diagnose_min} Minuten ({diagnose_aw} AW)
- TT-Zeit bereits eingereicht: {tt_zeit_vorhanden}

Dokumentation:
- Kundenangabe (O-Ton): {kundenangabe}
- Mechaniker-Notizen: {mechaniker_notizen}
- Fehlercodes: {fehlercodes}
- Arbeitspositionen: {arbeitspositionen}

Prüfe:
1. Ist es ein Garantieauftrag? ({is_garantie})
2. Gibt es Stempelzeiten? ({stempelzeiten_min > 0})
3. Ist Diagnosezeit > Standardarbeitszeit? ({diagnose_aw > 0})
4. Ist TT-Zeit bereits eingereicht? ({tt_zeit_vorhanden})
5. Wie viele AW sind möglich? (max. 9 AW ohne Freigabe)

Antworte im JSON-Format:
{{
    "tt_zeit_moeglich": true/false,
    "begruendung": "Warum ist TT-Zeit gerechtfertigt?",
    "empfohlene_aw": 0-9,
    "verguetung_eur": 0-75.87,
    "freigabe_erforderlich": true/false,
    "warnung": "Hinweise oder Warnungen"
}}
"""
```

---

## 🛠️ IMPLEMENTIERUNG

### 1. API-Endpoint

```python
@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
@login_required
def analysiere_tt_zeit(auftrag_id: int):
    """
    Analysiert ob TT-Zeit für einen Garantieauftrag abgerechnet werden kann.
    
    TAG 195: TT-Zeit-Optimierung für Garantieaufträge
    ROI: ~9.000€/Jahr (bis zu 75,87€ pro Auftrag)
    """
    try:
        # 1. Hole Auftragsdaten
        from api.db_connection import get_db
        conn = get_db()
        cursor = conn.cursor()
        
        # Prüfe ob Garantieauftrag
        cursor.execute("""
            SELECT 
                o.number,
                o.subsidiary,
                MAX(CASE WHEN l.charge_type = 60 THEN 1 ELSE 0 END) as is_charge_type_60,
                MAX(CASE WHEN l.labour_type IN ('G', 'GS') THEN 1 ELSE 0 END) as is_labour_type_g,
                MAX(CASE WHEN i.invoice_type = 6 THEN 1 ELSE 0 END) as is_invoice_type_6,
                SUM(l.time_units) as vorgabe_aw
            FROM orders o
            LEFT JOIN labours l ON o.number = l.order_number
            LEFT JOIN invoices i ON o.number = i.order_number
            WHERE o.number = %s
            GROUP BY o.number, o.subsidiary
        """, [auftrag_id])
        
        auftrag = cursor.fetchone()
        if not auftrag:
            return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404
        
        is_garantie = (
            auftrag[2] == 1 OR  # charge_type = 60
            auftrag[3] == 1 OR  # labour_type IN ('G', 'GS')
            auftrag[4] == 1     # invoice_type = 6
        )
        
        vorgabe_aw = float(auftrag[5] or 0)
        
        # 2. Hole Stempelzeiten
        cursor.execute("""
            SELECT 
                SUM(EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60) as stempelzeiten_min
            FROM times
            WHERE order_number = %s AND type = 2
        """, [auftrag_id])
        
        stempelzeiten = cursor.fetchone()
        stempelzeiten_min = float(stempelzeiten[0] or 0)
        stempelzeiten_aw = stempelzeiten_min / 6  # 1 AW = 6 Minuten
        
        # 3. Prüfe ob TT-Zeit bereits eingereicht
        cursor.execute("""
            SELECT COUNT(*) > 0
            FROM labours
            WHERE order_number = %s
              AND (labour_operation_id LIKE '%RTT' OR labour_operation_id LIKE '%HTT')
        """, [auftrag_id])
        
        tt_zeit_vorhanden = cursor.fetchone()[0]
        
        # 4. Berechne Diagnosezeit
        diagnose_min = max(0, stempelzeiten_min - (vorgabe_aw * 6))
        diagnose_aw = diagnose_min / 6
        
        # 5. Hole zusätzliche Daten für KI-Analyse
        cursor.execute("""
            SELECT o.order_text as kundenangabe
            FROM orders o
            WHERE o.number = %s
        """, [auftrag_id])
        
        kundenangabe = cursor.fetchone()[0] if cursor.fetchone() else ""
        
        # Hole GUDAT-Daten (Mechaniker-Notizen)
        from api.arbeitskarte_api import hole_arbeitskarte_daten
        arbeitskarte = hole_arbeitskarte_daten(auftrag_id)
        gudat = arbeitskarte.get('gudat', {}) if arbeitskarte else {}
        mechaniker_notizen = ""
        if isinstance(gudat, dict) and 'tasks' in gudat:
            for task in gudat.get('tasks', []):
                if task.get('description'):
                    mechaniker_notizen = task.get('description', '')
                    break
        
        conn.close()
        
        # 6. KI-Analyse
        prompt = f"""
Analysiere ob TT-Zeit für Garantieauftrag {auftrag_id} abgerechnet werden kann:

Auftragsdaten:
- Garantieauftrag: {is_garantie}
- Vorgabe AW: {vorgabe_aw:.1f} AW

Zeiterfassung:
- Stempelzeiten gesamt: {stempelzeiten_min:.0f} Minuten ({stempelzeiten_aw:.1f} AW)
- Diagnosezeit: {diagnose_min:.0f} Minuten ({diagnose_aw:.1f} AW)
- TT-Zeit bereits eingereicht: {tt_zeit_vorhanden}

Dokumentation:
- Kundenangabe: {kundenangabe[:200] if kundenangabe else 'Nicht vorhanden'}
- Mechaniker-Notizen: {mechaniker_notizen[:200] if mechaniker_notizen else 'Nicht vorhanden'}

Regeln:
- Bis 0,9 Stunden (9 AW): OHNE Freigabe abrechenbar = 75,87€
- Ab 1,0 Stunden (10 AW): Freigabe erforderlich
- Nur wenn Diagnosezeit > Standardarbeitszeit

Antworte im JSON-Format:
{{
    "tt_zeit_moeglich": true/false,
    "begruendung": "Warum ist TT-Zeit gerechtfertigt?",
    "empfohlene_aw": 0-9,
    "verguetung_eur": 0-75.87,
    "freigabe_erforderlich": true/false,
    "warnung": "Hinweise oder Warnungen"
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Experte für Hyundai/Stellantis Garantie-Abrechnung. Du analysierst ob TT-Zeit abgerechnet werden kann. Antworte immer im JSON-Format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = lm_studio_client.chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.3
        )
        
        if not response:
            return jsonify({
                'success': False,
                'error': 'KI-Server antwortet nicht'
            }), 500
        
        # Parse JSON aus Antwort
        try:
            response_clean = response.strip()
            if response_clean.startswith('```'):
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
            
            ki_ergebnis = json.loads(response_clean)
            
            # Kombiniere mit technischen Daten
            ergebnis = {
                'success': True,
                'auftrag_id': auftrag_id,
                'technische_daten': {
                    'is_garantie': is_garantie,
                    'vorgabe_aw': vorgabe_aw,
                    'stempelzeiten_min': stempelzeiten_min,
                    'stempelzeiten_aw': stempelzeiten_aw,
                    'diagnose_min': diagnose_min,
                    'diagnose_aw': diagnose_aw,
                    'tt_zeit_vorhanden': tt_zeit_vorhanden
                },
                'ki_analyse': ki_ergebnis
            }
            
            return jsonify(ergebnis)
            
        except json.JSONDecodeError:
            return jsonify({
                'success': True,
                'auftrag_id': auftrag_id,
                'technische_daten': {
                    'is_garantie': is_garantie,
                    'vorgabe_aw': vorgabe_aw,
                    'stempelzeiten_min': stempelzeiten_min,
                    'diagnose_aw': diagnose_aw
                },
                'ki_analyse': {
                    'tt_zeit_moeglich': diagnose_aw > 0 and diagnose_aw <= 9 and not tt_zeit_vorhanden,
                    'rohe_antwort': response
                }
            })
            
    except Exception as e:
        logger.error(f"Fehler bei TT-Zeit-Analyse: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 2. Entscheidungslogik (Technisch)

```python
def pruefe_tt_zeit_voraussetzungen(auftrag_id: int) -> Dict[str, Any]:
    """
    Prüft technisch ob TT-Zeit-Voraussetzungen erfüllt sind.
    (Ohne KI, nur technische Prüfung)
    """
    # 1. Garantieauftrag?
    is_garantie = check_garantieauftrag(auftrag_id)
    
    # 2. Stempelzeiten vorhanden?
    stempelzeiten_min = get_stempelzeiten_min(auftrag_id)
    
    # 3. Diagnosezeit berechnen
    vorgabe_aw = get_vorgabe_aw(auftrag_id)
    diagnose_aw = max(0, (stempelzeiten_min / 6) - vorgabe_aw)
    
    # 4. TT-Zeit bereits eingereicht?
    tt_zeit_vorhanden = check_tt_zeit_vorhanden(auftrag_id)
    
    # 5. Entscheidung
    if not is_garantie:
        return {
            'tt_zeit_moeglich': False,
            'grund': 'Kein Garantieauftrag'
        }
    
    if stempelzeiten_min == 0:
        return {
            'tt_zeit_moeglich': False,
            'grund': 'Keine Stempelzeiten vorhanden'
        }
    
    if diagnose_aw <= 0:
        return {
            'tt_zeit_moeglich': False,
            'grund': 'Diagnosezeit nicht höher als Standardarbeitszeit'
        }
    
    if tt_zeit_vorhanden:
        return {
            'tt_zeit_moeglich': False,
            'grund': 'TT-Zeit bereits eingereicht'
        }
    
    if diagnose_aw > 9:
        return {
            'tt_zeit_moeglich': True,
            'grund': 'TT-Zeit möglich, aber Freigabe erforderlich (> 9 AW)',
            'freigabe_erforderlich': True,
            'empfohlene_aw': 9  # Max. ohne Freigabe
        }
    
    return {
        'tt_zeit_moeglich': True,
        'grund': f'TT-Zeit möglich: {diagnose_aw:.1f} AW ohne Freigabe',
        'freigabe_erforderlich': False,
        'empfohlene_aw': min(diagnose_aw, 9),
        'verguetung_eur': min(diagnose_aw, 9) * 8.43
    }
```

---

## 📊 ENTSCHEIDUNGSBAUM

```
TT-Zeit-Analyse starten
    │
    ├─→ Ist Garantieauftrag?
    │       │
    │       ├─→ Nein → ❌ TT-Zeit nicht möglich
    │       │
    │       └─→ Ja → Weiter
    │
    ├─→ Gibt es Stempelzeiten?
    │       │
    │       ├─→ Nein → ❌ TT-Zeit nicht möglich
    │       │
    │       └─→ Ja → Weiter
    │
    ├─→ Diagnosezeit > Standardarbeitszeit?
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
    ├─→ Diagnosezeit <= 9 AW?
    │       │
    │       ├─→ Ja → ✅ TT-Zeit möglich (ohne Freigabe)
    │       │         Empfehlung: {diagnose_aw} AW = {verguetung}€
    │       │
    │       └─→ Nein → ⚠️ TT-Zeit möglich (Freigabe erforderlich)
    │                   Empfehlung: 9 AW = 75,87€ (max. ohne Freigabe)
    │                   Oder: Freigabe-Antrag für {diagnose_aw} AW
```

---

## 🎯 VORAUSSETZUNGEN ZUSAMMENFASSUNG

### Muss erfüllt sein (Technisch):

1. ✅ **Garantieauftrag:**
   - `charge_type = 60` ODER
   - `labour_type IN ('G', 'GS')` ODER
   - `invoice_type = 6`

2. ✅ **Stempelzeiten vorhanden:**
   - Mindestens eine Stempelung in `times` (type = 2)

3. ✅ **Diagnosezeit > Standardarbeitszeit:**
   - `stempelzeiten_min > (vorgabe_aw * 6)`

4. ✅ **TT-Zeit noch nicht eingereicht:**
   - Keine Position mit `labour_operation_id LIKE '%RTT'` oder `'%HTT'`

### KI-Bewertung (Zusätzlich):

5. 🤖 **Begründung:**
   - Warum ist TT-Zeit gerechtfertigt?
   - Was wurde diagnostiziert?
   - Warum dauerte es länger?

6. 🤖 **Empfehlung:**
   - Sollte TT-Zeit erfasst werden? (Ja/Nein)
   - Wie viele AW? (max. 9 ohne Freigabe)
   - Begründung für die Abrechnung

---

## 💡 BEISPIEL-SZENARIEN

### Szenario 1: TT-Zeit möglich (ohne Freigabe)

**Auftrag:** 12345 (Hyundai Garantie)
- Stempelzeiten: 90 Minuten (15 AW)
- Vorgabe AW: 2 AW
- Diagnosezeit: 90 - (2 × 6) = 78 Minuten = 13 AW
- **Ergebnis:** ✅ TT-Zeit möglich, aber nur 9 AW ohne Freigabe = 75,87€

### Szenario 2: TT-Zeit möglich (mit Freigabe)

**Auftrag:** 12346 (Hyundai Garantie)
- Stempelzeiten: 120 Minuten (20 AW)
- Vorgabe AW: 2 AW
- Diagnosezeit: 120 - (2 × 6) = 108 Minuten = 18 AW
- **Ergebnis:** ⚠️ TT-Zeit möglich, aber Freigabe erforderlich (> 9 AW)

### Szenario 3: Keine TT-Zeit möglich

**Auftrag:** 12347 (Standard-Werkstatt)
- **Ergebnis:** ❌ Kein Garantieauftrag

---

## 🚀 NÄCHSTE SCHRITTE

1. ✅ API-Endpoint implementieren (`/api/ai/analysiere/tt-zeit/<auftrag_id>`)
2. [ ] Frontend-Integration (Button in Arbeitskarte-Ansicht)
3. [ ] Automatische Warnung bei Garantieaufträgen
4. [ ] Integration in Garantie-Workflow
5. [ ] Testing mit echten Daten

---

**Erstellt:** TAG 195  
**Status:** Konzept erstellt, bereit für Implementierung
