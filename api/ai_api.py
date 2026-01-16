"""
AI API - LM Studio Integration
===============================
TAG 195: Integration mit LM Studio Server für lokale KI-Funktionen

Verwendet LM Studio Server (http://46.229.10.1:4433) für:
- Dokumentationsprüfung
- Textanalyse
- Klassifikation
- Bewertungen
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
import requests
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Blueprint erstellen
ai_api = Blueprint('ai_api', __name__, url_prefix='/api/ai')


# ============================================================================
# CONFIGURATION
# ============================================================================

def get_lm_studio_config():
    """Lädt LM Studio Konfiguration aus credentials.json"""
    creds_file = 'config/credentials.json'
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)
                if 'lm_studio' in creds:
                    return creds['lm_studio']
        except Exception as e:
            logger.error(f"Fehler beim Laden der LM Studio Credentials: {e}")
    
    # Fallback: Environment Variables oder Defaults
    return {
        'api_url': os.getenv('LM_STUDIO_API_URL', 'http://46.229.10.1:4433/v1'),
        'default_model': os.getenv('LM_STUDIO_DEFAULT_MODEL', 'allenai/olmo-3-32b-think'),
        'embedding_model': os.getenv('LM_STUDIO_EMBEDDING_MODEL', 'text-embedding-nomic-embed-text-v1.5'),
        'timeout': int(os.getenv('LM_STUDIO_TIMEOUT', '30'))
    }


# ============================================================================
# LM STUDIO CLIENT
# ============================================================================

class LMStudioClient:
    """Client für LM Studio Server (OpenAI-kompatible API)"""
    
    def __init__(self):
        self.config = get_lm_studio_config()
        self.base_url = self.config.get('api_url', 'http://46.229.10.1:4433/v1')
        self.default_model = self.config.get('default_model', 'allenai/olmo-3-32b-think')
        self.embedding_model = self.config.get('embedding_model', 'text-embedding-nomic-embed-text-v1.5')
        self.timeout = self.config.get('timeout', 30)
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any], method: str = 'POST') -> Optional[Dict[str, Any]]:
        """Macht HTTP-Request an LM Studio API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            else:
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"LM Studio API Timeout: {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio API Fehler: {endpoint} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei LM Studio API: {endpoint} - {str(e)}")
            return None
    
    def chat_completion(self, messages: list, model: Optional[str] = None, max_tokens: int = 500, temperature: float = 0.3) -> Optional[str]:
        """
        Sendet Chat-Completion Request
        
        Args:
            messages: Liste von Nachrichten [{"role": "system|user|assistant", "content": "..."}]
            model: Modell-Name (optional, verwendet default_model)
            max_tokens: Maximale Token-Anzahl
            temperature: Temperatur (0.0-1.0)
        
        Returns:
            Antwort-Text oder None bei Fehler
        """
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        result = self._make_request("chat/completions", payload)
        if result and "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0].get("message", {}).get("content", "")
        return None
    
    def completion(self, prompt: str, model: Optional[str] = None, max_tokens: int = 100, temperature: float = 0.7) -> Optional[str]:
        """
        Sendet Completion Request (Text-Vervollständigung)
        
        Args:
            prompt: Eingabe-Text
            model: Modell-Name (optional)
            max_tokens: Maximale Token-Anzahl
            temperature: Temperatur
        
        Returns:
            Vervollständigter Text oder None bei Fehler
        """
        model = model or self.default_model
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        result = self._make_request("completions", payload)
        if result and "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0].get("text", "")
        return None
    
    def embedding(self, text: str, model: Optional[str] = None) -> Optional[list]:
        """
        Erstellt Embedding-Vektor für Text
        
        Args:
            text: Eingabe-Text
            model: Embedding-Modell (optional)
        
        Returns:
            Embedding-Vektor (Liste von Floats) oder None bei Fehler
        """
        model = model or self.embedding_model
        payload = {
            "model": model,
            "input": text
        }
        
        result = self._make_request("embeddings", payload)
        if result and "data" in result and len(result["data"]) > 0:
            return result["data"][0].get("embedding", [])
        return None
    
    def list_models(self) -> Optional[list]:
        """Listet verfügbare Modelle"""
        result = self._make_request("models", {}, method='GET')
        if result and "data" in result:
            return [model.get("id") for model in result["data"]]
        return None


# Globale Client-Instanz
lm_studio_client = LMStudioClient()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@ai_api.route('/models', methods=['GET'])
@login_required
def list_models():
    """Listet verfügbare Modelle"""
    try:
        models = lm_studio_client.list_models()
        if models:
            return jsonify({'success': True, 'models': models})
        else:
            return jsonify({'success': False, 'error': 'Keine Modelle gefunden'}), 500
    except Exception as e:
        logger.error(f"Fehler beim Laden der Modelle: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_api.route('/chat', methods=['POST'])
@login_required
def chat():
    """Chat-Completion Endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten übermittelt'}), 400
        
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'success': False, 'error': 'Keine Messages übermittelt'}), 400
        
        model = data.get('model')
        max_tokens = data.get('max_tokens', 500)
        temperature = data.get('temperature', 0.3)
        
        response = lm_studio_client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if response:
            return jsonify({'success': True, 'response': response})
        else:
            return jsonify({'success': False, 'error': 'Keine Antwort vom Server'}), 500
            
    except Exception as e:
        logger.error(f"Fehler bei Chat-Completion: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_api.route('/embedding', methods=['POST'])
@login_required
def embedding():
    """Embedding Endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten übermittelt'}), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({'success': False, 'error': 'Kein Text übermittelt'}), 400
        
        model = data.get('model')
        
        embedding = lm_studio_client.embedding(text=text, model=model)
        
        if embedding:
            return jsonify({
                'success': True,
                'embedding': embedding,
                'dimensions': len(embedding)
            })
        else:
            return jsonify({'success': False, 'error': 'Kein Embedding erstellt'}), 500
            
    except Exception as e:
        logger.error(f"Fehler bei Embedding: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# USE CASE: ARBEITSKARTEN-DOKUMENTATIONSPRÜFUNG
# ============================================================================

@ai_api.route('/pruefe/arbeitskarte/<int:auftrag_id>', methods=['POST'])
@login_required
def pruefe_arbeitskarte(auftrag_id: int):
    """
    Prüft Vollständigkeit der Arbeitskarte für einen Auftrag
    
    TAG 195: Erster Use Case - Werkstattauftrag-Dokumentationsprüfung
    ROI: ~24.000€/Jahr (siehe docs/KI_ANWENDUNGSFAELLE_ANALYSE_TAG181.md)
    """
    try:
        # Hole Arbeitskarten-Daten (vereinfacht, sollte aus arbeitskarte_api.py importiert werden)
        from api.arbeitskarte_api import hole_arbeitskarte_daten
        
        arbeitskarte_daten = hole_arbeitskarte_daten(auftrag_id)
        
        if not arbeitskarte_daten:
            return jsonify({
                'success': False,
                'error': f'Auftrag {auftrag_id} nicht gefunden'
            }), 404
        
        # Extrahiere relevante Daten für Prüfung
        locosoft = arbeitskarte_daten.get('locosoft', {})
        auftrag = locosoft.get('auftrag', {})
        kunde = locosoft.get('kunde', {})
        fahrzeug = locosoft.get('fahrzeug', {})
        positionen = locosoft.get('positionen', [])
        teile = locosoft.get('teile', [])
        gudat = arbeitskarte_daten.get('gudat', {})
        
        # GUDAT-Daten extrahieren (Diagnose, Notizen, etc.)
        gudat_tasks = gudat.get('tasks', []) if isinstance(gudat, dict) else []
        diagnose = ""
        notizen = ""
        if gudat_tasks:
            # Hole erste Task mit Beschreibung
            for task in gudat_tasks:
                if task.get('description'):
                    diagnose = task.get('description', '')
                    break
        
        # Positionen-Text zusammenfassen (Reparaturmaßnahmen)
        reparaturmassnahme = "\n".join([
            f"Position {pos.get('position', '')}: {pos.get('text_line', '')} ({pos.get('aw', 0)} AW)"
            for pos in positionen
        ])
        
        # Teile-Nummern extrahieren
        teile_nummern = ", ".join([
            f"{teil.get('teilenummer', '')} ({teil.get('menge', 0)}x)"
            for teil in teile
        ])
        
        # TT-Zeiten (Stempelzeiten)
        stempelzeiten = locosoft.get('stempelzeiten', [])
        tt_zeiten = "\n".join([
            f"{st.get('mechaniker', '')}: {st.get('dauer_min', 0)} Min"
            for st in stempelzeiten
        ])
        
        # Erstelle Prompt für KI-Prüfung
        prompt = f"""
Prüfe die Vollständigkeit der Arbeitskarte für Auftrag {auftrag_id}:

Auftragsdaten:
- Auftragsnummer: {auftrag.get('nummer', 'N/A')}
- Datum: {auftrag.get('datum', 'N/A')}
- Serviceberater: {auftrag.get('serviceberater', 'N/A')}
- Fahrzeug: {fahrzeug.get('marke_modell', 'N/A')} ({fahrzeug.get('kennzeichen', 'N/A')})
- Kunde: {kunde.get('name', 'N/A')}

Dokumentation:
- Diagnose (GUDAT): {diagnose if diagnose else 'Nicht vorhanden'}
- Reparaturmaßnahme (Positionen): {reparaturmassnahme if reparaturmassnahme else 'Nicht vorhanden'}
- TT-Zeiten (Stempelzeiten): {tt_zeiten if tt_zeiten else 'Nicht vorhanden'}
- Teile-Nummern: {teile_nummern if teile_nummern else 'Nicht vorhanden'}
- Kundenangabe (O-Ton): {auftrag.get('job_beschreibung', 'Nicht vorhanden')}

Prüfe bitte:
1. Ist eine Diagnose vorhanden und ausreichend beschrieben?
2. Ist die Reparaturmaßnahme dokumentiert?
3. Sind TT-Zeiten erfasst?
4. Sind Teile-Nummern angegeben (falls Teile verwendet wurden)?
5. Ist eine Kundenangabe (O-Ton) vorhanden?

Antworte im JSON-Format:
{{
    "vollstaendigkeit": 0-100,
    "fehlende_elemente": ["Element1", "Element2"],
    "qualitaet": "gut|mittel|schlecht",
    "empfehlungen": ["Empfehlung1", "Empfehlung2"]
}}
"""
        
        # System-Message für bessere Ergebnisse
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Experte für Autohaus-Dokumentation. Du prüfst Arbeitskarten auf Vollständigkeit und Qualität. Antworte immer im JSON-Format."
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
        
        # Versuche JSON aus Antwort zu extrahieren
        try:
            # Entferne Markdown-Code-Blöcke falls vorhanden
            response_clean = response.strip()
            if response_clean.startswith('```'):
                # Entferne ```json und ```
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
            
            # Parse JSON
            result = json.loads(response_clean)
            
            return jsonify({
                'success': True,
                'auftrag_id': auftrag_id,
                'pruefung': result
            })
        except json.JSONDecodeError:
            # Falls kein JSON, gebe rohe Antwort zurück
            return jsonify({
                'success': True,
                'auftrag_id': auftrag_id,
                'pruefung': {
                    'vollstaendigkeit': None,
                    'fehlende_elemente': [],
                    'qualitaet': 'unbekannt',
                    'empfehlungen': [],
                    'rohe_antwort': response
                }
            })
            
    except Exception as e:
        logger.error(f"Fehler bei Arbeitskarten-Prüfung: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# USE CASE: TT-ZEIT-OPTIMIERUNG
# ============================================================================

def check_garantieauftrag(auftrag_id: int) -> bool:
    """Prüft ob ein Auftrag ein Garantieauftrag ist."""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM loco_labours l 
                    WHERE l.order_number = %s 
                      AND (l.charge_type = 60 OR l.labour_type IN ('G', 'GS'))
                ) THEN true
                WHEN EXISTS (
                    SELECT 1 FROM loco_parts p 
                    WHERE p.order_number = %s 
                      AND p.invoice_type = 6
                ) THEN true
                ELSE false
            END as is_garantie
    """, [auftrag_id, auftrag_id])
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else False


def hole_schadhaftes_teil(auftrag_id: int) -> Optional[Dict]:
    """Identifiziert das schadhaften Teil für einen Garantieauftrag."""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    # Hole Teile für Garantieauftrag (invoice_type = 6 = Garantie)
    cursor.execute("""
        SELECT 
            p.part_number,
            pm.description,
            p.amount,
            p.is_invoiced,
            p.order_position
        FROM loco_parts p
        LEFT JOIN loco_parts_master pm ON p.part_number = pm.part_number
        WHERE p.order_number = %s
          AND p.invoice_type = 6
        ORDER BY p.order_position
        LIMIT 1
    """, [auftrag_id])
    
    teil = cursor.fetchone()
    conn.close()
    
    if teil:
        return {
            'teilenummer': teil[0],
            'beschreibung': teil[1] if teil[1] else 'Unbekannt',
            'menge': float(teil[2]) if teil[2] else 0,
            'abgerechnet': teil[3] if teil[3] else False,
            'position': teil[4] if teil[4] else 0
        }
    
    return None


def get_stempelzeiten(auftrag_id: int) -> Dict:
    """Holt Stempelzeiten für einen Auftrag."""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as anzahl,
            COALESCE(SUM(EXTRACT(EPOCH FROM (end_time - start_time)) / 60), 0) as dauer_minuten
        FROM loco_times
        WHERE order_number = %s
          AND type = 2
    """, [auftrag_id])
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        'anzahl': result[0] if result else 0,
        'dauer_minuten': float(result[1]) if result and result[1] else 0.0
    }


def check_tt_zeit_vorhanden(auftrag_id: int) -> bool:
    """Prüft ob TT-Zeit bereits eingereicht wurde."""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) > 0
        FROM loco_labours
        WHERE order_number = %s
          AND (
              labour_operation_id LIKE '%%RTT' 
              OR labour_operation_id LIKE '%%HTT'
              OR labour_operation_id LIKE '%%TT'
          )
    """, [auftrag_id])
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else False


def get_auftrag_info(auftrag_id: int) -> Optional[Dict]:
    """Holt grundlegende Auftragsinformationen."""
    from api.db_connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.number,
            o.order_date,
            o.subsidiary,
            v.license_plate,
            v.vin,
            m.description as marke
        FROM loco_orders o
        LEFT JOIN loco_vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN loco_makes m ON v.make_number = m.make_number
        WHERE o.number = %s
    """, [auftrag_id])
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'nummer': result[0],
            'datum': result[1].isoformat() if result[1] else None,
            'standort': result[2],
            'kennzeichen': result[3],
            'vin': result[4],
            'marke': result[5]
        }
    
    return None


@ai_api.route('/analysiere/tt-zeit/<int:auftrag_id>', methods=['POST'])
@login_required
def analysiere_tt_zeit(auftrag_id: int):
    """
    Analysiert ob TT-Zeit für einen Garantieauftrag abgerechnet werden kann.
    
    TAG 195: TT-Zeit-Optimierung mit KI-Unterstützung
    
    WICHTIG: Manuelle Prüfung im GSW Portal erforderlich!
    TT-Zeit ist nur möglich, wenn KEINE Arbeitsoperationsnummer mit Vorgabezeit vorhanden ist.
    
    Returns:
    {
        'success': True,
        'auftrag_id': int,
        'technische_pruefung': {...},
        'ki_analyse': {...},
        'warnung': {...},
        'tt_zeit_moeglich': None  # Unbekannt, bis manuell bestätigt
    }
    """
    try:
        # 1. Technische Prüfung
        is_garantie = check_garantieauftrag(auftrag_id)
        stempelzeiten = get_stempelzeiten(auftrag_id)
        tt_zeit_vorhanden = check_tt_zeit_vorhanden(auftrag_id)
        schadhaftes_teil = hole_schadhaftes_teil(auftrag_id)
        auftrag_info = get_auftrag_info(auftrag_id)
        
        if not auftrag_info:
            return jsonify({
                'success': False,
                'error': f'Auftrag {auftrag_id} nicht gefunden'
            }), 404
        
        # 2. Hole zusätzliche Daten für KI-Analyse
        from api.arbeitskarte_api import hole_arbeitskarte_daten
        arbeitskarte_daten = hole_arbeitskarte_daten(auftrag_id)
        
        # Extrahiere relevante Daten
        locosoft = arbeitskarte_daten.get('locosoft', {}) if arbeitskarte_daten else {}
        auftrag = locosoft.get('auftrag', {})
        positionen = locosoft.get('positionen', [])
        gudat = arbeitskarte_daten.get('gudat', {}) if arbeitskarte_daten else {}
        gudat_tasks = gudat.get('tasks', []) if isinstance(gudat, dict) else []
        
        # Diagnose aus GUDAT
        diagnose = ""
        if gudat_tasks:
            for task in gudat_tasks:
                if task.get('description'):
                    diagnose = task.get('description', '')
                    break
        
        # Positionen-Text
        reparaturmassnahme = "\n".join([
            f"Position {pos.get('position', '')}: {pos.get('text_line', '')} ({pos.get('aw', 0)} AW)"
            for pos in positionen[:5]  # Erste 5 Positionen
        ])
        
        # 3. KI-Analyse (Begründung, Empfehlung)
        prompt = f"""
Analysiere ob TT-Zeit (Tatsächliche Zeit) für diesen Garantieauftrag gerechtfertigt sein könnte:

Auftragsdaten:
- Auftragsnummer: {auftrag_id}
- Datum: {auftrag_info.get('datum', 'N/A')}
- Fahrzeug: {auftrag_info.get('marke', 'N/A')} ({auftrag_info.get('kennzeichen', 'N/A')})
- Standort: {auftrag_info.get('standort', 'N/A')}

Schadhaften Teil:
- Teilenummer: {schadhaftes_teil.get('teilenummer', 'Nicht identifiziert') if schadhaftes_teil else 'Nicht identifiziert'}
- Beschreibung: {schadhaftes_teil.get('beschreibung', 'N/A') if schadhaftes_teil else 'N/A'}

Stempelzeiten:
- Anzahl: {stempelzeiten.get('anzahl', 0)}
- Dauer: {stempelzeiten.get('dauer_minuten', 0):.1f} Minuten ({stempelzeiten.get('dauer_minuten', 0) / 60:.2f} Stunden)

Diagnose (GUDAT):
{diagnose if diagnose else 'Nicht vorhanden'}

Reparaturmaßnahme:
{reparaturmassnahme if reparaturmassnahme else 'Nicht vorhanden'}

WICHTIG: TT-Zeit ist nur möglich, wenn Hyundai KEINE Arbeitsoperationsnummer mit Vorgabezeit 
für das schadhaften Teil im GSW Portal hat.

Bewerte:
1. Ist die Diagnose komplex und zeitaufwendig?
2. Gibt es Hinweise, dass die tatsächliche Zeit deutlich höher war als erwartet?
3. Welche Begründung könnte für TT-Zeit sprechen?

Antworte im JSON-Format:
{{
    "begruendung": "Kurze Begründung warum TT-Zeit gerechtfertigt sein könnte",
    "empfehlung": "Empfehlung (z.B. 'TT-Zeit prüfen' oder 'Standardarbeitszeit ausreichend')",
    "bewertung": "hoch|mittel|niedrig",
    "hinweise": ["Hinweis 1", "Hinweis 2"]
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Experte für Hyundai Garantie-Abrechnung. Du analysierst ob TT-Zeit (Tatsächliche Zeit) gerechtfertigt ist. Antworte immer im JSON-Format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        ki_response = lm_studio_client.chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.3
        )
        
        # Parse KI-Antwort
        ki_analyse = {
            'begruendung': 'KI-Analyse nicht verfügbar',
            'empfehlung': 'Bitte manuell prüfen',
            'bewertung': 'unbekannt',
            'hinweise': []
        }
        
        if ki_response:
            try:
                response_clean = ki_response.strip()
                if response_clean.startswith('```'):
                    lines = response_clean.split('\n')
                    response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                
                ki_data = json.loads(response_clean)
                ki_analyse = {
                    'begruendung': ki_data.get('begruendung', ki_analyse['begruendung']),
                    'empfehlung': ki_data.get('empfehlung', ki_analyse['empfehlung']),
                    'bewertung': ki_data.get('bewertung', ki_analyse['bewertung']),
                    'hinweise': ki_data.get('hinweise', ki_analyse['hinweise'])
                }
            except json.JSONDecodeError:
                # Falls kein JSON, nutze rohe Antwort
                ki_analyse['begruendung'] = ki_response[:300]
        
        # 4. Warnung für manuelle Prüfung
        warnung_text = ""
        if schadhaftes_teil:
            warnung_text = f"⚠️ WICHTIG: Bitte im GSW Portal prüfen, ob für Teil {schadhaftes_teil.get('teilenummer', 'unbekannt')} eine Arbeitsoperationsnummer mit Vorgabezeit vorhanden ist!"
        else:
            warnung_text = "⚠️ WICHTIG: Schadhaften Teil identifizieren und im GSW Portal prüfen!"
        
        # 5. Ergebnis zusammenstellen
        ergebnis = {
            'success': True,
            'auftrag_id': auftrag_id,
            'auftrag_info': auftrag_info,
            'technische_pruefung': {
                'is_garantie': is_garantie,
                'stempelzeiten_vorhanden': stempelzeiten.get('anzahl', 0) > 0,
                'stempelzeiten_anzahl': stempelzeiten.get('anzahl', 0),
                'stempelzeiten_minuten': round(stempelzeiten.get('dauer_minuten', 0), 1),
                'stempelzeiten_stunden': round(stempelzeiten.get('dauer_minuten', 0) / 60, 2),
                'tt_zeit_vorhanden': tt_zeit_vorhanden,
                'schadhaftes_teil': schadhaftes_teil
            },
            'ki_analyse': ki_analyse,
            'warnung': {
                'manuelle_pruefung_erforderlich': True,
                'text': warnung_text,
                'hinweis': 'TT-Zeit ist nur möglich, wenn KEINE Arbeitsoperationsnummer mit Vorgabezeit im GSW Portal vorhanden ist!'
            },
            'tt_zeit_moeglich': None,  # Unbekannt, bis manuell bestätigt
            'abrechnungsregeln': {
                'bis_09_stunden': {
                    'max_aw': 9,
                    'max_minuten': 54,
                    'max_stunden': 0.9,
                    'verguetung_max': 75.87,  # 9 AW × 8,43€
                    'freigabe_erforderlich': False
                },
                'ab_10_stunden': {
                    'min_aw': 10,
                    'min_minuten': 60,
                    'min_stunden': 1.0,
                    'freigabe_erforderlich': True,
                    'freigabe_ueber': 'GWMS (Antragstyp: T, Freigabetyp: DK)'
                }
            }
        }
        
        return jsonify(ergebnis)
        
    except Exception as e:
        logger.error(f"Fehler bei TT-Zeit-Analyse für Auftrag {auftrag_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
