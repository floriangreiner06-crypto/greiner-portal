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
        'default_model': os.getenv('LM_STUDIO_DEFAULT_MODEL', 'mistralai/magistral-small-2509'),  # TAG 195: Geändert von olmo-3-32b-think (Think-Modell) zu mistralai (bessere JSON-Ausgaben)
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
        self.default_model = self.config.get('default_model', 'mistralai/magistral-small-2509')  # TAG 195: Geändert für bessere JSON-Ausgaben
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
        
        # TAG 195: Verwende mistralai als Default für bessere JSON-Ausgaben
        model = model or "mistralai/magistral-small-2509"
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
        
        # TAG 195: Verwende mistralai für bessere JSON-Ausgaben
        response = lm_studio_client.chat_completion(
            messages=messages,
            model="mistralai/magistral-small-2509",  # Explizit setzen
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
        
        # TAG 195: Explizit mistralai-Modell für bessere JSON-Ausgaben
        ki_response = lm_studio_client.chat_completion(
            messages=messages,
            model="mistralai/magistral-small-2509",  # Explizit setzen für strukturierte Ausgaben
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


# ============================================================================
# USE CASE: FAHRZEUGBESCHREIBUNG-GENERIERUNG (VERKAUF)
# ============================================================================

def hole_fahrzeug_daten(dealer_vehicle_number: int) -> Optional[Dict]:
    """Holt alle relevanten Fahrzeugdaten für Beschreibung aus Locosoft."""
    from api.db_utils import locosoft_session
    from psycopg2.extras import RealDictCursor
    
    try:
        with locosoft_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Hole Fahrzeugdaten aus dealer_vehicles + vehicles
            cursor.execute("""
                SELECT
                    dv.dealer_vehicle_number,
                    dv.dealer_vehicle_type,
                    v.vin,
                    v.license_plate as kennzeichen,
                    v.free_form_model_text as modell,
                    v.first_registration_date as erstzulassung,
                    v.mileage_km as kilometerstand,
                    m.description as marke,
                    mo.description as modell_detail,
                    dv.in_arrival_date as eingang,
                    dv.out_sale_price as verkaufspreis,
                    dv.mileage_km as km_stand,
                    dv.in_used_vehicle_buy_type as ankauf_typ,
                    dv.out_sale_type as besteuerung,
                    dv.in_subsidiary as standort,
                    dv.location as lagerort,
                    -- Zusatzinfos
                    CASE 
                        WHEN dv.dealer_vehicle_type = 'G' THEN 'Gebrauchtwagen'
                        WHEN dv.dealer_vehicle_type = 'N' THEN 'Neuwagen'
                        WHEN dv.dealer_vehicle_type = 'D' THEN 'Vorführwagen'
                        WHEN dv.dealer_vehicle_type = 'V' THEN 'Vorführwagen'  -- V = Vorführwagen (nicht Vermietwagen!)
                        WHEN dv.dealer_vehicle_type = 'T' THEN 'Tageszulassung'
                        WHEN dv.dealer_vehicle_type = 'L' THEN 'Leihgabe/Mietwagen'  -- L = Leihgabe (Mietwagen)
                        ELSE 'Unbekannt'
                    END as fahrzeugtyp,
                    CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as standzeit_tage
                FROM dealer_vehicles dv
                LEFT JOIN vehicles v ON dv.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
                WHERE dv.dealer_vehicle_number = %s
                LIMIT 1
            """, [dealer_vehicle_number])
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return dict(row)
            
    except Exception as e:
        logger.error(f"Fehler beim Holen der Fahrzeugdaten: {str(e)}")
        return None


@ai_api.route('/generiere/fahrzeugbeschreibung/<int:dealer_vehicle_number>', methods=['POST'])
@login_required
def generiere_fahrzeugbeschreibung(dealer_vehicle_number: int):
    """
    Generiert eine marktgerechte Fahrzeugbeschreibung für Verkaufsplattformen.
    
    TAG 195: Use Case für Verkauf - Fahrzeugbeschreibung-Generierung
    
    Args:
        dealer_vehicle_number: Locosoft dealer_vehicle_number
        
    Returns:
        JSON mit generierter Beschreibung, Verkaufsargumenten, SEO-Keywords
    """
    try:
        # 1. Hole Fahrzeugdaten
        fahrzeug = hole_fahrzeug_daten(dealer_vehicle_number)
        
        if not fahrzeug:
            return jsonify({
                'success': False,
                'error': f'Fahrzeug {dealer_vehicle_number} nicht gefunden'
            }), 404
        
        # 2. Baue Prompt für KI
        marke = fahrzeug.get('marke', 'Unbekannt')
        modell = fahrzeug.get('modell', fahrzeug.get('modell_detail', 'Unbekannt'))
        fahrzeugtyp = fahrzeug.get('fahrzeugtyp', 'Fahrzeug')
        erstzulassung = fahrzeug.get('erstzulassung')
        kilometerstand = fahrzeug.get('kilometerstand') or fahrzeug.get('km_stand', 0)
        verkaufspreis = fahrzeug.get('verkaufspreis', 0)
        standzeit_tage = fahrzeug.get('standzeit_tage', 0)
        vin = fahrzeug.get('vin', '')
        kennzeichen = fahrzeug.get('kennzeichen', '')
        
        # Formatierung
        erstzulassung_str = erstzulassung.strftime('%m/%Y') if erstzulassung else 'Unbekannt'
        km_str = f"{int(kilometerstand):,} km" if kilometerstand else 'Unbekannt'
        preis_str = f"{float(verkaufspreis):,.2f} €" if verkaufspreis else 'Preis auf Anfrage'
        
        # Elektrofahrzeug-Erkennung
        modell_lower = (modell or '').lower()
        is_elektro = any(keyword in modell_lower for keyword in [
            'ioniq', 'kona electric', 'electric', 'ev', 'e-', 'elektro', 'battery', 'zero emission'
        ])
        
        # Modell-Name extrahieren (z.B. "Ioniq 5" statt nur "Hyundai")
        modell_name = modell if modell and modell != marke else fahrzeug.get('modell_detail', modell) or 'Unbekannt'
        
        prompt = f"""
Generiere eine professionelle, marktgerechte Fahrzeugbeschreibung für ein {fahrzeugtyp}.

FAHRZEUGDATEN:
- Marke: {marke}
- Modell: {modell_name}
- Fahrzeugtyp: {fahrzeugtyp}
- Erstzulassung: {erstzulassung_str}
- Kilometerstand: {km_str}
- Verkaufspreis: {preis_str}
- Standzeit: {int(standzeit_tage)} Tage
- VIN: {vin[-8:] if len(vin) >= 8 else vin}
{"- Elektrofahrzeug: Ja (z.B. Ioniq 5, Ioniq 6, Kona Electric)" if is_elektro else ""}

ANFORDERUNGEN:
1. Schreibe eine ansprechende, professionelle Beschreibung (150-250 Wörter)
2. Hebe die wichtigsten Verkaufsargumente hervor
3. Verwende eine freundliche, vertrauenswürdige Sprache
4. Erwähne Marke, Modell (z.B. "Hyundai Ioniq 5"), Erstzulassung und Kilometerstand
5. Bei Gebrauchtwagen: Betone Zustand und Wartungshistorie (falls bekannt)
6. Bei langer Standzeit: Formuliere positiv (z.B. "gut gepflegt", "selten gefahren")
7. Keine negativen Formulierungen
8. SEO-optimiert (natürlich, nicht übertrieben)
{"9. Bei Elektrofahrzeugen: Erwähne Reichweite, Ladeleistung, Ausstattung (z.B. Ioniq 5: ~480 km WLTP, 800V-System, schnelles Laden)" if is_elektro else ""}

FORMAT:
- Hauptbeschreibung (2-3 Absätze)
- Verkaufsargumente (3-5 Bullet Points)
- SEO-Keywords (5-10 relevante Begriffe)

Antworte im JSON-Format:
{{
  "beschreibung": "Haupttext der Beschreibung...",
  "verkaufsargumente": ["Argument 1", "Argument 2", ...],
  "seo_keywords": ["Keyword1", "Keyword2", ...],
  "zusammenfassung": "Kurze Zusammenfassung (1 Satz)"
}}
"""
        
        # 3. KI-Anfrage
        messages = [
            {
                "role": "system",
                "content": "Du bist ein Experte für Fahrzeugverkauf und Autohaus-Marketing. Du schreibst professionelle, ansprechende Fahrzeugbeschreibungen für Verkaufsplattformen."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Verwende alternatives Modell für bessere JSON-Ausgabe (kein "think"-Modell)
        # "think"-Modelle geben Denkprozess statt direkter Antwort aus
        model = "mistralai/magistral-small-2509"  # Besseres Modell für strukturierte Ausgaben
        
        response_content = lm_studio_client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=800,
            temperature=0.7  # Etwas kreativer für Beschreibungen
        )
        
        if not response_content:
            return jsonify({
                'success': False,
                'error': 'KI-Antwort konnte nicht generiert werden'
            }), 500
        
        # 4. Parse JSON-Antwort
        try:
            # Entferne Markdown-Code-Blöcke falls vorhanden
            cleaned = response_content.strip()
            if cleaned.startswith('```'):
                import re
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
            else:
                cleaned = response_content
            
            # Versuche JSON aus Antwort zu extrahieren
            import re
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                ki_result = json.loads(json_match.group())
            else:
                # Fallback: Strukturierte Antwort parsen
                ki_result = {
                    'beschreibung': cleaned,
                    'verkaufsargumente': [],
                    'seo_keywords': [],
                    'zusammenfassung': cleaned[:100] + '...' if len(cleaned) > 100 else cleaned
                }
        except json.JSONDecodeError:
            # Fallback: Verwende rohe Antwort als Beschreibung
            ki_result = {
                'beschreibung': response_content,
                'verkaufsargumente': [],
                'seo_keywords': [],
                'zusammenfassung': response_content[:100] + '...' if len(response_content) > 100 else response_content
            }
        
        # 5. Rückgabe
        return jsonify({
            'success': True,
            'dealer_vehicle_number': dealer_vehicle_number,
            'fahrzeug': {
                'marke': marke,
                'modell': modell_name,
                'fahrzeugtyp': fahrzeugtyp,
                'erstzulassung': erstzulassung_str,
                'kilometerstand': km_str,
                'verkaufspreis': preis_str,
                'standzeit_tage': int(standzeit_tage),
                'is_elektro': is_elektro
            },
            'beschreibung': {
                'haupttext': ki_result.get('beschreibung', ''),
                'verkaufsargumente': ki_result.get('verkaufsargumente', []),
                'seo_keywords': ki_result.get('seo_keywords', []),
                'zusammenfassung': ki_result.get('zusammenfassung', ''),
                'rohe_antwort': response_content  # Für Debugging
            }
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Fahrzeugbeschreibung-Generierung: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
