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
from flask_login import login_required, current_user
import requests
import json
import os
import logging
import re
from typing import Optional, Dict, Any
from datetime import date

from decorators.auth_decorators import login_or_api_key_required

logger = logging.getLogger(__name__)

# Blueprint erstellen
ai_api = Blueprint('ai_api', __name__, url_prefix='/api/ai')


# ============================================================================
# CONFIGURATION – SSOT: config/credentials.json → lm_studio
# ============================================================================

# Nur Fallback, wenn credentials.json keinen lm_studio-Block hat (z. B. Testumgebung)
_LM_STUDIO_FALLBACK = {
    'api_url': 'http://46.229.10.1:4433/v1',
    'default_model': 'mistralai/devstral-small-2-2512',
    'vision_model': 'qwen/qwen3-vl-4b',
    'embedding_model': 'text-embedding-nomic-embed-text-v1.5',
    'timeout': 30,
}


def get_lm_studio_config():
    """Lädt LM Studio Konfiguration aus config/credentials.json (lm_studio)."""
    creds_file = 'config/credentials.json'
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)
                if 'lm_studio' in creds:
                    # Env-Overrides für Deployment/Umgebungen
                    cfg = dict(creds['lm_studio'])
                    if os.getenv('LM_STUDIO_API_URL'):
                        cfg['api_url'] = os.getenv('LM_STUDIO_API_URL')
                    if os.getenv('LM_STUDIO_DEFAULT_MODEL'):
                        cfg['default_model'] = os.getenv('LM_STUDIO_DEFAULT_MODEL')
                    if os.getenv('LM_STUDIO_VISION_MODEL'):
                        cfg['vision_model'] = os.getenv('LM_STUDIO_VISION_MODEL')
                    if os.getenv('LM_STUDIO_TIMEOUT'):
                        cfg['timeout'] = int(os.getenv('LM_STUDIO_TIMEOUT'))
                    return cfg
        except Exception as e:
            logger.error(f"Fehler beim Laden der LM Studio Credentials: {e}")
    out = dict(_LM_STUDIO_FALLBACK)
    out['api_url'] = os.getenv('LM_STUDIO_API_URL', out['api_url'])
    out['default_model'] = os.getenv('LM_STUDIO_DEFAULT_MODEL', out['default_model'])
    out['vision_model'] = os.getenv('LM_STUDIO_VISION_MODEL', out['vision_model'])
    out['timeout'] = int(os.getenv('LM_STUDIO_TIMEOUT', str(out['timeout'])))
    return out


# ============================================================================
# LM STUDIO CLIENT
# ============================================================================

class LMStudioClient:
    """Client für LM Studio Server (OpenAI-kompatible API)"""
    
    def __init__(self):
        self.config = get_lm_studio_config()
        self.base_url = self.config.get('api_url', 'http://46.229.10.1:4433/v1')
        self.default_model = self.config.get('default_model', _LM_STUDIO_FALLBACK['default_model'])
        self.vision_model = self.config.get('vision_model', 'qwen/qwen3-vl-4b')
        self.embedding_model = self.config.get('embedding_model', 'text-embedding-nomic-embed-text-v1.5')
        self.timeout = self.config.get('timeout', 30)
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any], method: str = 'POST', timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Macht HTTP-Request an LM Studio API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        t = timeout if timeout is not None else self.timeout
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=t)
            else:
                response = requests.post(url, json=payload, headers=headers, timeout=t)

            if not response.ok:
                body = (response.text or "")[:500]
                logger.error(
                    "LM Studio API %s: HTTP %s - %s. Body: %s",
                    endpoint, response.status_code, getattr(response, "reason", "") or "",
                    body,
                )
                return None

            return response.json()
        except requests.exceptions.Timeout:
            logger.error(f"LM Studio API Timeout: {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio API Fehler: {endpoint} - {str(e)}")
            return None
        except ValueError as e:
            # response.json() bei HTML-Antwort (z. B. Proxy-Fehlerseite)
            logger.error(f"LM Studio API: Antwort war kein JSON (z. B. HTML): {endpoint} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei LM Studio API: {endpoint} - {str(e)}")
            return None
    
    def chat_completion(self, messages: list, model: Optional[str] = None, max_tokens: int = 500, temperature: float = 0.3, timeout: Optional[int] = None) -> Optional[str]:
        """
        Sendet Chat-Completion Request
        
        Args:
            messages: Liste von Nachrichten [{"role": "system|user|assistant", "content": "..."}]
            model: Modell-Name (optional, verwendet default_model)
            max_tokens: Maximale Token-Anzahl
            temperature: Temperatur (0.0-1.0)
            timeout: Request-Timeout in Sekunden (optional, sonst Config-Default)
        
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
        
        result = self._make_request("chat/completions", payload, timeout=timeout)
        if result and "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0].get("message", {}).get("content", "")
        return None

    def chat_completion_vision(
        self,
        image_base64: str,
        image_media_type: str,
        text_prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: Optional[int] = 90,
    ) -> Optional[str]:
        """
        Chat mit Bild (OpenAI-kompatibel: image_url mit data-URL). Für Fahrzeugschein-OCR.
        content: [ {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}, {"type": "text", "text": "..."} ]
        """
        model = model or self.vision_model
        data_url = f"data:{image_media_type or 'image/jpeg'};base64,{image_base64}"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": text_prompt},
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        result = self._make_request("chat/completions", payload, timeout=timeout)
        if result and "choices" in result and len(result["choices"]) > 0:
            msg = result["choices"][0].get("message", {})
            content = msg.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
            return ""
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
        
        model = model or lm_studio_client.default_model
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
# USE CASE: TRANSAKTIONS-KATEGORISIERUNG (Bankenspiegel)
# ============================================================================

# Kategorien-Liste für KI-Prompt (muss mit transaktion_kategorisierung.REGELN abgestimmt sein)
TRANSAKTION_KATEGORIEN_FUER_KI = [
    "Intern", "Einkaufsfinanzierung", "Personal", "Miete & Nebenkosten", "Versicherung",
    "Steuern", "Betrieb", "Bank & Zinsen", "Lieferanten", "Einnahmen", "Sonstige Ausgaben", "Sonstige Einnahmen"
]


def _hole_kategorisierung_beispiele(limit: int = 12) -> list:
    """Lädt zuletzt vom User bestätigte Kategorisierungen als Few-Shot-Beispiele (nur kategorie_manuell = true = Übernehmen geklickt)."""
    try:
        from api.db_utils import db_session
        from api.db_connection import convert_placeholders
        beispiele = []
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                convert_placeholders("""
                    SELECT verwendungszweck, buchungstext, gegenkonto_name, betrag, kategorie, unterkategorie
                    FROM transaktionen
                    WHERE kategorie IS NOT NULL AND kategorie != '' AND kategorie_manuell = true
                    ORDER BY id DESC
                    LIMIT """ + str(min(int(limit), 20)))
            )
            for row in cur.fetchall():
                vw = row.get("verwendungszweck") if hasattr(row, "get") else (row[0] if len(row) > 0 else None)
                bt = row.get("buchungstext") if hasattr(row, "get") else (row[1] if len(row) > 1 else None)
                gk = row.get("gegenkonto_name") if hasattr(row, "get") else (row[2] if len(row) > 2 else None)
                bet = row.get("betrag") if hasattr(row, "get") else (row[3] if len(row) > 3 else None)
                kat = row.get("kategorie") if hasattr(row, "get") else (row[4] if len(row) > 4 else None)
                unter = row.get("unterkategorie") if hasattr(row, "get") else (row[5] if len(row) > 5 else None)
                if kat:
                    text_parts = [str(vw or ""), str(bt or ""), str(gk or "")]
                    text = " | ".join(p for p in text_parts if p.strip())[:300]
                    bet_str = f"{bet:.2f} €" if bet is not None else "—"
                    beispiele.append({
                        "text": text,
                        "betrag": bet_str,
                        "kategorie": kat,
                        "unterkategorie": unter or ""
                    })
        return beispiele
    except Exception as e:
        logger.warning("Kategorisierung-Beispiele laden: %s", e)
        return []


def kategorisiere_transaktion_mit_ki(
    verwendungszweck: Optional[str] = None,
    buchungstext: Optional[str] = None,
    gegenkonto_name: Optional[str] = None,
    betrag: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Schlägt Kategorie/Unterkategorie für eine Banktransaktion per LM Studio vor.
    Nutzt Few-Shot-Beispiele aus zuletzt gespeicherten Kategorisierungen (KI lernt mit).
    Returns: {"kategorie": "...", "unterkategorie": "..."} oder None bei Fehler.
    """
    text_parts = [
        str(verwendungszweck or ""),
        str(buchungstext or ""),
        str(gegenkonto_name or ""),
    ]
    betrag_str = f"{betrag:.2f} €" if betrag is not None else "nicht angegeben"
    text = " | ".join(p for p in text_parts if p.strip())
    kategorien_str = ", ".join(TRANSAKTION_KATEGORIEN_FUER_KI)

    beispiele = _hole_kategorisierung_beispiele(limit=12)
    beispiele_block = ""
    if beispiele:
        lines = ["Beispiele aus euren bereits kategorisierten Buchungen (daran orientieren):"]
        for b in beispiele[:10]:
            uk = (" / " + b["unterkategorie"]) if b.get("unterkategorie") else ""
            lines.append(f"- Text: {b['text']} | Betrag: {b['betrag']} → Kategorie: {b['kategorie']}{uk}")
        beispiele_block = "\n".join(lines) + "\n\n"

    prompt = f"""{beispiele_block}Kategorisiere diese Banktransaktion (Autohaus) in genau eine Kategorie.
Verwendungszweck/Buchungstext/Gegenkonto: {text[:500]}
Betrag: {betrag_str}

Wähle NUR eine der folgenden Kategorien: {kategorien_str}
Unterkategorie kann spezifischer sein (z.B. bei Einkaufsfinanzierung: Stellantis, Santander, Hyundai; bei Personal: Gehalt; bei Lieferanten: Teile, Sonstige).

Antworte NUR mit diesem JSON, nichts anderes:
{{"kategorie": "Gewählte Kategorie", "unterkategorie": "Unterkategorie oder null"}}
"""

    messages = [
        {
            "role": "system",
            "content": "Du bist ein Buchhalter. Du kategorisierst Bankbuchungen für ein Autohaus. Orientiere dich an den gegebenen Beispielen. Antworte ausschließlich mit gültigem JSON: {\"kategorie\": \"...\", \"unterkategorie\": \"...\"}."
        },
        {"role": "user", "content": prompt}
    ]
    response = lm_studio_client.chat_completion(
        messages=messages,
        max_tokens=150,
        temperature=0.2
    )
    if not response:
        return None
    try:
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            response_clean = "\n".join(lines[1:-1]) if len(lines) > 2 else response_clean
        out = json.loads(response_clean)
        k = (out.get("kategorie") or "").strip()
        if not k:
            return None
        return {
            "kategorie": k,
            "unterkategorie": (out.get("unterkategorie") or "").strip() or None
        }
    except json.JSONDecodeError:
        logger.warning("KI Kategorisierung: Kein gültiges JSON - %s", response[:200])
        return None


@ai_api.route('/kategorisiere/transaktion', methods=['POST'])
@login_required
def api_kategorisiere_transaktion():
    """
    POST /api/ai/kategorisiere/transaktion
    Schlägt für eine Banktransaktion Kategorie/Unterkategorie per LM Studio vor.
    Body: { "verwendungszweck": "...", "buchungstext": "...", "gegenkonto_name": "...", "betrag": 123.45 }
    """
    try:
        data = request.get_json() or {}
        vorschlag = kategorisiere_transaktion_mit_ki(
            verwendungszweck=data.get("verwendungszweck"),
            buchungstext=data.get("buchungstext"),
            gegenkonto_name=data.get("gegenkonto_name"),
            betrag=data.get("betrag"),
        )
        if vorschlag is None:
            return jsonify({
                "success": False,
                "error": "KI konnte keine Kategorie vorschlagen (Timeout oder ungültige Antwort)"
            }), 500
        return jsonify({"success": True, "vorschlag": vorschlag}), 200
    except Exception as e:
        logger.error("Fehler bei KI-Kategorisierung: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


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
        
        response_content = lm_studio_client.chat_completion(
            messages=messages,
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


# ============================================================================
# NATURSPRACHLICHE ANALYSEN AUF DRIVE-GESCHÄFTSDATEN (LM Studio)
# ============================================================================
# Konzept: docs/workstreams/integrations/KONZEPT_NATURSPRACHLICHE_ANALYSEN_DRIVE_DATEN.md
# Keine freie SQL-Generierung – vordefinierte Daten-Views aus SSOT-APIs als Kontext.


def _build_tek_context(tek_data: Dict[str, Any], monat: int, jahr: int) -> str:
    """Baut einen kompakten Text-Kontext aus get_tek_data für das LLM."""
    if not tek_data:
        return "Keine TEK-Daten verfügbar."
    lines = [f"TEK-Daten für {monat}/{jahr} (Tägliche Erfolgskontrolle):"]
    gesamt = tek_data.get("gesamt") or {}
    lines.append(
        f"Gesamt: Umsatz {gesamt.get('umsatz', 0):,.0f} €, Einsatz {gesamt.get('einsatz', 0):,.0f} €, "
        f"DB1 {gesamt.get('db1', 0):,.0f} €, Marge {gesamt.get('marge', 0):.1f} %. "
        f"Prognose Monatsende: {gesamt.get('prognose', 0):,.0f} €, Breakeven: {gesamt.get('breakeven', 0):,.0f} €."
    )
    wg = gesamt.get("werktage") or {}
    if wg:
        lines.append(
            f"Werktage: {wg.get('vergangen', 0)} von {wg.get('gesamt', 0)} (verbleibend: {wg.get('verbleibend', 0)})."
        )
    bereiche = tek_data.get("bereiche") or []
    if bereiche:
        lines.append("Bereiche:")
        for b in bereiche:
            name = b.get("id") or b.get("name") or "?"
            lines.append(
                f"  {name}: Umsatz {float(b.get('umsatz') or 0):,.0f} €, DB1 {float(b.get('db1') or 0):,.0f} €, "
                f"Marge {float(b.get('marge') or 0):.1f} %"
            )
    vm = tek_data.get("vm") or {}
    vj = tek_data.get("vj") or {}
    if vm or vj:
        lines.append(
            f"Vormonat: DB1 {vm.get('db1', 0):,.0f} €, Marge {vm.get('marge', 0):.1f} %. "
            f"Vorjahr (gleicher Zeitraum): DB1 {vj.get('db1', 0):,.0f} €, Marge {vj.get('marge', 0):.1f} %."
        )
    return "\n".join(lines)


def _resolve_time_context(frage: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Löst Zeitbezug auf.
    Regeln:
    - Wenn expliziter Zeitraum im Payload übergeben wird: verwenden.
    - Wenn Frage klare Signale enthält: verwenden.
    - Wenn unklar und kein Payload: Rückfrage.
    - Default: aktueller Monat + YTD.
    """
    heute = date.today()
    raw = (frage or "").lower()
    period = payload.get("zeitraum") if isinstance(payload, dict) else None

    # Expliziter Zeitraum vom Client
    if isinstance(period, dict) and (period.get("von") or period.get("month")):
        try:
            month = int(period.get("month") or heute.month)
            year = int(period.get("year") or heute.year)
        except (TypeError, ValueError):
            return {
                "needs_clarification": True,
                "clarification_question": "Ungültiger Zeitraum. Bitte month (1-12) und year (YYYY) numerisch angeben.",
            }
        if month < 1 or month > 12:
            return {
                "needs_clarification": True,
                "clarification_question": "Ungültiger Monat. Bitte month zwischen 1 und 12 angeben.",
            }
        return {
            "needs_clarification": False,
            "label": "explizit",
            "month": month,
            "year": year,
            "ytd": bool(period.get("ytd", True)),
            "from": period.get("von"),
            "to": period.get("bis"),
        }

    has_time_hint = any(token in raw for token in [
        "heute", "gestern", "tag", "monat", "monatlich", "ytd", "jahr", "quartal", "woche"
    ])
    is_ambiguous = any(token in raw for token in ["bisher", "aktuell", "wie läuft", "status"]) and not has_time_hint

    if is_ambiguous:
        return {
            "needs_clarification": True,
            "clarification_question": "Welchen Zeitraum meinst du genau? (aktueller Monat, YTD, letztes Monat, konkretes Datum)",
        }

    # Default gemäß Anforderung: aktueller Monat + YTD
    return {
        "needs_clarification": False,
        "label": "default_monat_ytd",
        "month": heute.month,
        "year": heute.year,
        "ytd": True,
        "from": None,
        "to": None,
    }


def _extract_entities_with_lm(frage: str) -> Dict[str, Any]:
    """
    Extrahiert Produkt/Modell-Entitäten aus der Frage.
    Fail-safe: Gibt leeres Dict zurück.
    """
    prompt = f"""
Extrahiere relevante Entitäten aus dieser Autohaus-Frage.
Frage: {frage}

Antworte NUR als JSON:
{{
  "modell": "z.B. Astra oder null",
  "teilbegriff": "z.B. Ölfilter oder null",
  "teilenummer": "z.B. 93185674 oder null"
}}
"""
    response = lm_studio_client.chat_completion(
        messages=[
            {"role": "system", "content": "Du extrahierst Entitäten. Nur JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=120,
        temperature=0.0,
        timeout=20,
    )
    if not response:
        return {}
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _detect_intent(frage: str, bereich: str = "") -> Dict[str, Any]:
    raw = (frage or "").lower()
    domain = (bereich or "").strip().lower()

    # Frueh-Intent: Teilebestellungen/ServiceBox auch bei "bestellt" (nicht nur "Bestellungen")
    if (
        any(k in raw for k in ["servicebox", "teilebestellungen", "teilebestellung", "btz"])
        or ("bestell" in raw and ("teil" in raw or "teile" in raw))
        or ((" für " in raw or " fuer " in raw or " von " in raw) and "bestellt" in raw)
    ):
        return {"id": "servicebox_bestellungen", "confidence": 0.95}

    if domain in ("kunden", "kunde", "adressbuch") or any(k in raw for k in [
        "kunde", "kunden", "kundennummer", "adressbuch", "telefonnummer", "email"
    ]):
        return {"id": "kunden_suche", "confidence": 0.9}
    if domain in ("servicebox", "teilebestellungen", "bestellungen"):
        return {"id": "servicebox_bestellungen", "confidence": 0.92}
    if domain == "controlling" or any(k in raw for k in ["tek", "db1", "breakeven", "monat gelaufen", "marge", "gesamtunternehmen", "gesamt unternehmen"]):
        return {"id": "tek_summary", "confidence": 0.9}
    if domain == "verkauf" or any(
        k in raw
        for k in [
            "auftragseingang",
            "auftrag",
            "aufträge",
            "auftraege",
            "auslieferung",
            "auslieferungen",
            "verkäufer",
            "verkaeufer",
        ]
    ):
        return {"id": "verkauf_auftragseingang", "confidence": 0.9}
    if domain in ("teile", "lager") or any(k in raw for k in ["lager", "ölfilter", "oelfilter", "teil", "teilenummer"]):
        return {"id": "teile_lager", "confidence": 0.8}
    # Default für schnelle Ergebnisse: allgemeine Business-Fragen -> TEK
    return {"id": "tek_summary", "confidence": 0.55}


def _run_query_tek(time_ctx: Dict[str, Any]) -> Dict[str, Any]:
    from api.controlling_data import get_tek_data

    monat = time_ctx.get("month")
    jahr = time_ctx.get("year")
    monat_data = get_tek_data(monat=monat, jahr=jahr, firma="0", standort="0")
    return {
        "query_id": "tek_summary",
        "month_data": monat_data,
        "time_context": time_ctx,
    }


def _load_auftragseingang_ziele(monat: Any, jahr: Any) -> Dict[str, Any]:
    """
    Lädt Monats-/YTD-Ziele für Auftragseingang aus der SSOT-Zielplanung.
    Fehler brechen die Query nicht; dann {"success": False, ...}.
    """
    try:
        m = int(monat)
        y = int(jahr)
        if m < 1 or m > 12:
            return {"success": False, "error": "ungueltiger monat"}

        from api.verkaeufer_zielplanung_api import get_monatsziele_konzern_dict

        month_goal = get_monatsziele_konzern_dict(y, m)
        if not month_goal.get("success"):
            return {"success": False, "error": month_goal.get("error") or "Monatsziel nicht verfügbar"}

        ytd_nw = 0
        ytd_gw = 0
        for mm in range(1, m + 1):
            g = get_monatsziele_konzern_dict(y, mm)
            if not g.get("success"):
                continue
            ytd_nw += int(g.get("ziel_nw_konzern") or 0)
            ytd_gw += int(g.get("ziel_gw_konzern") or 0)

        return {
            "success": True,
            "month": {
                "stueck_nw": int(month_goal.get("ziel_nw_konzern") or 0),
                "stueck_gw": int(month_goal.get("ziel_gw_konzern") or 0),
            },
            "ytd": {
                "stueck_nw": int(ytd_nw),
                "stueck_gw": int(ytd_gw),
            },
            "source": "api.verkaeufer_zielplanung_api.get_monatsziele_konzern_dict",
        }
    except Exception as e:
        logger.info("Auftragseingang-Ziele nicht verfügbar: %s", e)
        return {"success": False, "error": str(e)}


def _run_query_verkauf(time_ctx: Dict[str, Any]) -> Dict[str, Any]:
    from api.verkauf_data import VerkaufData

    monat = time_ctx.get("month")
    jahr = time_ctx.get("year")
    segments_month = VerkaufData.get_auftragseingang_segments(month=monat, year=jahr, ytd=False)
    segments_ytd = VerkaufData.get_auftragseingang_segments(month=monat, year=jahr, ytd=True)
    targets = _load_auftragseingang_ziele(monat, jahr)
    return {
        "query_id": "verkauf_auftragseingang",
        "segments_month": segments_month,
        "segments_ytd": segments_ytd,
        "targets": targets,
        "time_context": time_ctx,
    }


def _run_query_teile(frage: str) -> Dict[str, Any]:
    from api.teile_stock_utils import get_stock_level_for_subsidiary
    from api.db_utils import locosoft_session
    from psycopg2.extras import RealDictCursor

    entities = _extract_entities_with_lm(frage)
    raw = (frage or "").lower()

    # Teilenummer direkt aus Frage oder Entitäten
    part_from_text = re.search(r"\b[A-Z0-9]{6,20}\b", (frage or "").upper())
    teilenummer = (entities.get("teilenummer") if isinstance(entities, dict) else None) or (part_from_text.group(0) if part_from_text else None)
    modell = (entities.get("modell") if isinstance(entities, dict) else None) or ("astra" if "astra" in raw else None)
    teilbegriff = (entities.get("teilbegriff") if isinstance(entities, dict) else None) or ("ölfilter" if ("ölfilter" in raw or "oelfilter" in raw) else None)

    if teilenummer:
        standorte = {1: "Deggendorf Opel", 2: "Deggendorf Hyundai", 3: "Landau"}
        stocks = {}
        total = 0.0
        for sid, label in standorte.items():
            info = get_stock_level_for_subsidiary(teilenummer, sid, required_amount=0, use_soap=False)
            level = float(info.get("stock_level", 0) or 0)
            stocks[str(sid)] = {"standort": label, "stock_level": level}
            total += level
        return {
            "query_id": "teile_lager",
            "mode": "part_number_direct",
            "entities": {"teilenummer": teilenummer},
            "stock_total": total,
            "stock_by_location": stocks,
        }

    # Für die Einschätzung: weiche KI-Erkennung auf Teilebeschreibung
    if teilbegriff:
        with locosoft_session() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            model_filter = f"%{modell.lower()}%" if modell else "%"
            cur.execute(
                """
                SELECT
                    pm.part_number,
                    pm.description,
                    COALESCE(SUM(ps.stock_level), 0) AS stock_level
                FROM parts_master pm
                LEFT JOIN parts_stock ps ON ps.part_number = pm.part_number
                WHERE LOWER(pm.description) LIKE %s
                  AND LOWER(pm.description) LIKE %s
                GROUP BY pm.part_number, pm.description
                ORDER BY stock_level DESC
                LIMIT 20
                """,
                (f"%{teilbegriff.lower()}%", model_filter),
            )
            rows = cur.fetchall() or []
        top = [
            {
                "part_number": r.get("part_number"),
                "description": r.get("description"),
                "stock_level": float(r.get("stock_level") or 0),
            }
            for r in rows
        ]
        return {
            "query_id": "teile_lager",
            "mode": "ai_entity_match",
            "entities": {"modell": modell, "teilbegriff": teilbegriff},
            "top_matches": top,
            "stock_total_top_matches": round(sum(x["stock_level"] for x in top), 2),
            "note": "Einschätzung über Beschreibungs-Matching; für produktive Präzision später Mapping-Tabelle empfehlenswert.",
        }

    return {
        "query_id": "teile_lager",
        "mode": "needs_clarification",
        "needs_clarification": True,
        "clarification_question": "Für Teilebestand bitte Teilenummer oder genaue Teilbezeichnung nennen (z. B. Ölfilter + Modell).",
    }


def _extract_servicebox_customer_term(frage: str) -> str:
    """
    Extrahiert Kundensuchbegriff aus Fragen wie:
    - "Welche Teile haben wir fuer Raedlinger bestellt?"
    - "Teilebestellungen von Mueller"
    """
    text = (frage or "").strip()
    if not text:
        return ""
    lower = text.lower()
    for marker in [" für ", " fuer ", " von "]:
        idx = lower.find(marker)
        if idx >= 0:
            candidate = text[idx + len(marker):].strip(" ?.!,:;")
            # haeufiges Endwort entfernen
            candidate = re.sub(r"\b(bestellt|bestellung|teilebestellung|teile)\b", "", candidate, flags=re.IGNORECASE).strip(" ?.!,:;")
            if candidate:
                return candidate
    return ""


def _run_query_servicebox(time_ctx: Dict[str, Any], frage: str = "") -> Dict[str, Any]:
    """
    ServiceBox/Teilebestellungen Kennzahlen (analog Teilebestellungen-UI Kacheln).
    """
    from api.db_utils import db_session, row_to_dict
    from api.db_connection import sql_placeholder

    month = int(time_ctx.get("month"))
    year = int(time_ctx.get("year"))
    ph = sql_placeholder()

    with db_session() as conn:
        cursor = conn.cursor()

        # Monatssicht
        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS total_bestellungen
            FROM stellantis_bestellungen b
            WHERE EXTRACT(YEAR FROM b.bestelldatum) = {ph}
              AND EXTRACT(MONTH FROM b.bestelldatum) = {ph}
            """,
            (str(year), f"{month:02d}")
        )
        total_bestellungen = int((row_to_dict(cursor.fetchone()) or {}).get("total_bestellungen") or 0)

        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS total_positionen,
                COALESCE(SUM(p.summe_inkl_mwst), 0) AS gesamtwert
            FROM stellantis_positionen p
            JOIN stellantis_bestellungen b ON b.id = p.bestellung_id
            WHERE EXTRACT(YEAR FROM b.bestelldatum) = {ph}
              AND EXTRACT(MONTH FROM b.bestelldatum) = {ph}
            """,
            (str(year), f"{month:02d}")
        )
        stats_row = row_to_dict(cursor.fetchone()) or {}

        # Heute
        cursor.execute(
            """
            SELECT COUNT(*) AS today_bestellungen
            FROM stellantis_bestellungen
            WHERE DATE(bestelldatum) = CURRENT_DATE
            """
        )
        today_bestellungen = int((row_to_dict(cursor.fetchone()) or {}).get("today_bestellungen") or 0)

        # Optional: Kundenspezifische Auswertung aus der Frage
        customer_term = _extract_servicebox_customer_term(frage)
        customer_stats = None
        top_parts = []
        if customer_term:
            cursor.execute(
                f"""
                SELECT
                    COUNT(DISTINCT b.id) AS total_bestellungen,
                    COUNT(p.id) AS total_positionen,
                    COALESCE(SUM(p.summe_inkl_mwst), 0) AS gesamtwert
                FROM stellantis_bestellungen b
                LEFT JOIN stellantis_positionen p ON p.bestellung_id = b.id
                WHERE EXTRACT(YEAR FROM b.bestelldatum) = {ph}
                  AND EXTRACT(MONTH FROM b.bestelldatum) = {ph}
                  AND (
                        COALESCE(b.match_kunde_name, '') ILIKE {ph}
                     OR COALESCE(b.parsed_kundennummer, '') ILIKE {ph}
                     OR COALESCE(b.bestellnummer, '') ILIKE {ph}
                  )
                """,
                (str(year), f"{month:02d}", f"%{customer_term}%", f"%{customer_term}%", f"%{customer_term}%")
            )
            c_row = row_to_dict(cursor.fetchone()) or {}
            customer_stats = {
                "search_term": customer_term,
                "total_bestellungen": int(c_row.get("total_bestellungen") or 0),
                "total_positionen": int(c_row.get("total_positionen") or 0),
                "gesamtwert": round(float(c_row.get("gesamtwert") or 0), 2),
            }

            cursor.execute(
                f"""
                SELECT
                    p.teilenummer,
                    COALESCE(MAX(p.beschreibung), 'Unbekannt') AS bezeichnung,
                    COUNT(*) AS anzahl_positionen,
                    COALESCE(SUM(p.summe_inkl_mwst), 0) AS gesamtwert
                FROM stellantis_bestellungen b
                JOIN stellantis_positionen p ON p.bestellung_id = b.id
                WHERE EXTRACT(YEAR FROM b.bestelldatum) = {ph}
                  AND EXTRACT(MONTH FROM b.bestelldatum) = {ph}
                  AND (
                        COALESCE(b.match_kunde_name, '') ILIKE {ph}
                     OR COALESCE(b.parsed_kundennummer, '') ILIKE {ph}
                     OR COALESCE(b.bestellnummer, '') ILIKE {ph}
                  )
                GROUP BY p.teilenummer
                ORDER BY anzahl_positionen DESC, gesamtwert DESC
                LIMIT 15
                """,
                (str(year), f"{month:02d}", f"%{customer_term}%", f"%{customer_term}%", f"%{customer_term}%")
            )
            for r in cursor.fetchall() or []:
                rr = row_to_dict(r) or {}
                top_parts.append({
                    "teilenummer": rr.get("teilenummer"),
                    "bezeichnung": rr.get("bezeichnung"),
                    "anzahl_positionen": int(rr.get("anzahl_positionen") or 0),
                    "gesamtwert": round(float(rr.get("gesamtwert") or 0), 2),
                })

    result = {
        "query_id": "servicebox_bestellungen",
        "time_context": time_ctx,
        "stats": {
            "total_bestellungen": total_bestellungen,
            "total_positionen": int(stats_row.get("total_positionen") or 0),
            "gesamtwert": round(float(stats_row.get("gesamtwert") or 0), 2),
            "today_bestellungen": today_bestellungen,
        },
    }
    if customer_stats:
        result["customer_stats"] = customer_stats
        result["top_parts"] = top_parts
    return result


def _extract_customer_search_term(frage: str) -> str:
    """
    Extrahiert den Suchbegriff für Kundensuche aus der Frage.
    """
    text = (frage or "").strip()
    if not text:
        return ""

    # Kundennummer direkt erkennen
    num_match = re.search(r"\b\d{4,10}\b", text)
    if num_match:
        return num_match.group(0)

    cleaned = re.sub(
        r"\b(wie|wer|ist|sind|der|die|das|ein|eine|zu|von|für|den|dem|mit|suche|finde|zeige|mir|bitte|kunde|kunden|kundennummer|telefon|telefonnummer|email|e-mail)\b",
        " ",
        text,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or text


def _run_query_kunden(frage: str) -> Dict[str, Any]:
    """
    Kundenabfrage über vorhandene Adressbuch-SSOT.
    """
    from api.locosoft_addressbook_api import search_customers

    term = _extract_customer_search_term(frage)
    results = search_customers(q=term, limit=20, mobile_only=False)

    # Auf kompaktes, API-taugliches Ergebnis normalisieren
    kunden = []
    for item in results[:10]:
        kunden.append({
            "customer_number": item.get("customer_number"),
            "display_name": item.get("display_name") or item.get("contact_name"),
            "phone": item.get("phone") or item.get("phone_number"),
            "email": item.get("email"),
            "city": item.get("home_city"),
        })

    return {
        "query_id": "kunden_suche",
        "search_term": term,
        "count": len(results),
        "kunden": kunden,
    }


# =============================================================================
# KI /api/ai/query – optionale Visualisierung (Chart.js-kompatibel, SSOT-Daten)
# =============================================================================

def _coerce_bool_include_visualization(raw: Any) -> bool:
    """Payload-Flag include_visualization (Default: True)."""
    if raw is None:
        return True
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    s = str(raw).strip().lower()
    return s not in ("0", "false", "no", "off", "")


def _build_visualization_tek(result_data: Dict[str, Any], time_ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    md = result_data.get("month_data") or {}
    gesamt = md.get("gesamt") or {}
    if not gesamt:
        return None
    umsatz = float(gesamt.get("umsatz") or 0)
    einsatz = float(gesamt.get("einsatz") or 0)
    db1 = float(gesamt.get("db1") or 0)
    prognose = float(gesamt.get("prognose") or 0)
    breakeven = float(gesamt.get("breakeven") or 0)
    vm = md.get("vm") or {}
    vj = md.get("vj") or {}
    vm_db1 = float(vm.get("db1") or 0)
    vj_db1 = float(vj.get("db1") or 0)
    labels = ["Umsatz", "Einsatz", "DB1", "Prognose", "Breakeven", "DB1 VM", "DB1 VJ"]
    data_values = [umsatz, einsatz, db1, prognose, breakeven, vm_db1, vj_db1]
    month = time_ctx.get("month")
    year = time_ctx.get("year")
    title = "TEK (Gesamtunternehmen)"
    if month is not None and year is not None:
        title = f"TEK {int(month):02d}/{int(year)}"
    return {
        "type": "bar",
        "title": title,
        "labels": labels,
        "datasets": [
            {
                "label": "EUR",
                "data": data_values,
                "backgroundColor": "rgba(13, 110, 253, 0.55)",
            }
        ],
        "options": {
            "scales": {
                "y": {"beginAtZero": True},
                "x": {"ticks": {"maxRotation": 45, "minRotation": 0}},
            },
            "plugins": {"legend": {"display": False}},
        },
        "meta": {
            "unit": "EUR",
            "source": "api.controlling_data.get_tek_data",
            "time_context": time_ctx,
        },
    }


def _build_visualization_verkauf(result_data: Dict[str, Any], time_ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sm = result_data.get("segments_month") or {}
    sy = result_data.get("segments_ytd") or {}
    if sm.get("success") is False or sy.get("success") is False:
        return None
    nw_m = int(sm.get("stueck_nw") or 0)
    gw_m = int(sm.get("stueck_gw") or 0)
    nw_y = int(sy.get("stueck_nw") or 0)
    gw_y = int(sy.get("stueck_gw") or 0)
    month = time_ctx.get("month")
    year = time_ctx.get("year")
    targets = result_data.get("targets") or {}
    has_targets = bool(targets.get("success"))
    target_month = (targets.get("month") or {}) if has_targets else {}
    target_ytd = (targets.get("ytd") or {}) if has_targets else {}

    title = "Auftragseingang NW/GW"
    if month is not None and year is not None:
        title = f"Auftragseingang NW/GW ({int(month):02d}/{int(year)})"

    datasets = [
        {
            "label": "Monat",
            "data": [nw_m, gw_m],
            "backgroundColor": "rgba(25, 135, 84, 0.65)",
        },
        {
            "label": "YTD",
            "data": [nw_y, gw_y],
            "backgroundColor": "rgba(13, 110, 253, 0.55)",
        },
    ]
    if has_targets:
        datasets.append({
            "label": "Ziel Monat",
            "data": [
                int(target_month.get("stueck_nw") or 0),
                int(target_month.get("stueck_gw") or 0),
            ],
            "backgroundColor": "rgba(220, 53, 69, 0.45)",
            "borderColor": "rgba(220, 53, 69, 0.95)",
            "borderWidth": 1,
        })
        datasets.append({
            "label": "Ziel YTD",
            "data": [
                int(target_ytd.get("stueck_nw") or 0),
                int(target_ytd.get("stueck_gw") or 0),
            ],
            "backgroundColor": "rgba(255, 193, 7, 0.45)",
            "borderColor": "rgba(255, 193, 7, 0.95)",
            "borderWidth": 1,
        })

    meta: Dict[str, Any] = {
        "unit": "Stück",
        "source": "api.verkauf_data.VerkaufData.get_auftragseingang_segments",
        "time_context": time_ctx,
    }
    if has_targets:
        meta["target_source"] = targets.get("source")
        meta["target_reached"] = {
            "month_nw_pct": round((nw_m / max(int(target_month.get("stueck_nw") or 0), 1)) * 100, 1),
            "month_gw_pct": round((gw_m / max(int(target_month.get("stueck_gw") or 0), 1)) * 100, 1),
            "ytd_nw_pct": round((nw_y / max(int(target_ytd.get("stueck_nw") or 0), 1)) * 100, 1),
            "ytd_gw_pct": round((gw_y / max(int(target_ytd.get("stueck_gw") or 0), 1)) * 100, 1),
        }

    return {
        "type": "bar",
        "title": title,
        "labels": ["Neuwagen (NW)", "Gebrauchtwagen (GW)"],
        "datasets": datasets,
        "options": {
            "scales": {
                "x": {"stacked": False},
                "y": {"beginAtZero": True},
            },
            "plugins": {"legend": {"display": True}},
        },
        "meta": meta,
    }


def _build_visualization_servicebox(result_data: Dict[str, Any], time_ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    KPI-Balken: Bestellungen, Positionen, Gesamtwert (kEUR), Heute (Bestellungen).
    Gesamtwert in kEUR skaliert, damit er neben Stückzahlen lesbar bleibt.
    """
    base_stats = result_data.get("stats") or {}
    customer_stats = result_data.get("customer_stats")
    if customer_stats:
        agg = customer_stats
        title_extra = f' – Kunde „{agg.get("search_term") or "?"}“'
    else:
        agg = base_stats
        title_extra = ""
    b = int(agg.get("total_bestellungen") or 0)
    p = int(agg.get("total_positionen") or 0)
    g = float(agg.get("gesamtwert") or 0)
    today = int(base_stats.get("today_bestellungen") or 0)
    month = time_ctx.get("month")
    year = time_ctx.get("year")
    title = "ServiceBox Teilebestellungen"
    if month is not None and year is not None:
        title = f"ServiceBox {int(month):02d}/{int(year)}{title_extra}"
    else:
        title = title + title_extra
    labels = ["Bestellungen", "Positionen", "Gesamtwert (kEUR)", "Heute (Best.)"]
    data_values = [b, p, round(g / 1000.0, 2), today]
    return {
        "type": "bar",
        "title": title,
        "labels": labels,
        "datasets": [
            {
                "label": "Kennzahl",
                "data": data_values,
                "backgroundColor": "rgba(111, 66, 193, 0.6)",
            }
        ],
        "options": {
            "scales": {
                "y": {"beginAtZero": True},
                "x": {"ticks": {"maxRotation": 30, "minRotation": 0}},
            },
            "plugins": {"legend": {"display": False}},
        },
        "meta": {
            "unit": "gemischt (Stück / kEUR)",
            "source": "stellantis_bestellungen / stellantis_positionen",
            "time_context": time_ctx,
            "note": "Gesamtwert als Tausend EUR; Heute = alle Bestellungen mit Datum heute (nicht nur gefilterter Kunde).",
        },
    }


def _safe_build_visualization(
    intent_id: str,
    result_data: Optional[Dict[str, Any]],
    time_ctx: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Baut optionalen visualization-Block; Fehler oder fehlende Daten -> None (Antwort bleibt gültig).
    """
    if not isinstance(result_data, dict):
        return None
    tc = time_ctx if isinstance(time_ctx, dict) else {}
    try:
        if intent_id == "tek_summary":
            return _build_visualization_tek(result_data, tc)
        if intent_id == "verkauf_auftragseingang":
            return _build_visualization_verkauf(result_data, tc)
        if intent_id == "servicebox_bestellungen":
            return _build_visualization_servicebox(result_data, tc)
    except Exception as e:
        logger.warning("Visualization-Build fehlgeschlagen (%s): %s", intent_id, e)
    return None


def _compose_answer_text(intent_id: str, data: Dict[str, Any]) -> str:
    if intent_id == "kunden_suche":
        count = int(data.get("count") or 0)
        term = data.get("search_term") or "deiner Suche"
        kunden = data.get("kunden") or []
        if count == 0:
            return f"Ich habe keine Kunden zu '{term}' gefunden."
        if count == 1 and kunden:
            k = kunden[0]
            return (
                f"Ich habe 1 passenden Kunden gefunden: {k.get('display_name')} "
                f"(Nr. {k.get('customer_number')})."
            )
        return f"Ich habe {count} passende Kunden zu '{term}' gefunden. Ich zeige die Top-Treffer."
    if intent_id == "servicebox_bestellungen":
        customer_stats = data.get("customer_stats") or {}
        if customer_stats:
            return (
                f"ServiceBox fuer '{customer_stats.get('search_term')}': "
                f"{customer_stats.get('total_bestellungen', 0)} Bestellungen, "
                f"{customer_stats.get('total_positionen', 0)} Positionen, "
                f"Gesamtwert {customer_stats.get('gesamtwert', 0):,.2f} EUR."
            )
        stats = data.get("stats") or {}
        return (
            f"ServiceBox Teilebestellungen: {stats.get('total_bestellungen', 0)} Bestellungen, "
            f"{stats.get('total_positionen', 0)} Positionen, Gesamtwert {stats.get('gesamtwert', 0):,.2f} EUR. "
            f"Heute: {stats.get('today_bestellungen', 0)} Bestellungen."
        )
    if intent_id == "tek_summary":
        gesamt = ((data.get("month_data") or {}).get("gesamt") or {})
        return (
            f"TEK aktueller Monat: Umsatz {gesamt.get('umsatz', 0):,.0f} EUR, "
            f"DB1 {gesamt.get('db1', 0):,.0f} EUR, Marge {gesamt.get('marge', 0):.1f}%. "
            f"Prognose Monatsende {gesamt.get('prognose', 0):,.0f} EUR."
        )
    if intent_id == "verkauf_auftragseingang":
        seg_m = data.get("segments_month") or {}
        seg_y = data.get("segments_ytd") or {}
        text = (
            f"Auftragseingang Monat: NW {seg_m.get('stueck_nw', 0)}, GW {seg_m.get('stueck_gw', 0)}. "
            f"YTD: NW {seg_y.get('stueck_nw', 0)}, GW {seg_y.get('stueck_gw', 0)}."
        )
        targets = data.get("targets") or {}
        if targets.get("success"):
            tm = targets.get("month") or {}
            ty = targets.get("ytd") or {}
            text += (
                f" Ziel Monat: NW {tm.get('stueck_nw', 0)}, GW {tm.get('stueck_gw', 0)}; "
                f"Ziel YTD: NW {ty.get('stueck_nw', 0)}, GW {ty.get('stueck_gw', 0)}."
            )
        return text
    if intent_id == "teile_lager":
        if data.get("mode") == "part_number_direct":
            return f"Bestand für Teilenummer {data.get('entities', {}).get('teilenummer')}: gesamt {data.get('stock_total', 0):,.1f} Stück."
        if data.get("mode") == "ai_entity_match":
            return (
                f"Für {data.get('entities', {}).get('teilbegriff', 'das Teil')} "
                f"({data.get('entities', {}).get('modell') or 'ohne Modellfilter'}) "
                f"wurden Top-Treffer mit gesamt {data.get('stock_total_top_matches', 0):,.1f} Stück gefunden."
            )
    return "Die Frage konnte noch nicht sicher einer Datenabfrage zugeordnet werden."


def _get_auth_mode() -> str:
    return request.environ.get('drive.auth_mode', 'session')


def _get_auth_scopes() -> set:
    raw = request.environ.get('drive.auth_scopes', '')
    return {s.strip() for s in raw.split(',') if s.strip()}


def _is_feature_allowed(feature: str) -> bool:
    auth_mode = _get_auth_mode()
    if auth_mode == 'api_key':
        scopes = _get_auth_scopes()
        return feature in scopes or '*' in scopes
    if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
        return hasattr(current_user, "can_access_feature") and current_user.can_access_feature(feature)
    return False


def _is_verkauf_intent_allowed() -> bool:
    """
    Berechtigungscheck für Auftragseingang-/Verkaufs-Intent.
    Akzeptiert sowohl grobe als auch feingranulare Features.
    """
    return any([
        _is_feature_allowed("verkauf"),
        _is_feature_allowed("auftragseingang"),
        _is_feature_allowed("verkauf_dashboard"),
        _is_feature_allowed("admin"),
    ])


def _is_servicebox_intent_allowed() -> bool:
    return any([
        _is_feature_allowed("teilebestellungen"),
        _is_feature_allowed("teile"),
        _is_feature_allowed("lager"),
        _is_feature_allowed("admin"),
    ])


def _is_kunden_intent_allowed() -> bool:
    return any([
        _is_feature_allowed("service"),
        _is_feature_allowed("serviceberater"),
        _is_feature_allowed("verkauf"),
        _is_feature_allowed("verkauf_dashboard"),
        _is_feature_allowed("whatsapp_verkauf"),
        _is_feature_allowed("whatsapp_teile"),
        _is_feature_allowed("admin"),
    ])


def _fallback_to_allowed_intent(preferred_intent: str) -> str:
    """
    Liefert einen erlaubten Fallback-Intent statt hartem 403, wenn moeglich.
    Reihenfolge:
    1) bevorzugter Intent (falls erlaubt)
    2) controlling (tek_summary)
    3) teile_lager
    4) preferred_intent (fuehrt dann zu normalem 403)
    """
    intent_feature_map = {
        "tek_summary": "controlling",
        "verkauf_auftragseingang": "verkauf",
        "teile_lager": "teile",
        "servicebox_bestellungen": "teilebestellungen",
        "kunden_suche": "service",
    }

    if preferred_intent == "verkauf_auftragseingang":
        if _is_verkauf_intent_allowed():
            return preferred_intent
    elif preferred_intent == "kunden_suche":
        if _is_kunden_intent_allowed():
            return preferred_intent
    elif preferred_intent == "servicebox_bestellungen":
        if _is_servicebox_intent_allowed():
            return preferred_intent
    elif _is_feature_allowed(intent_feature_map.get(preferred_intent, "")):
        return preferred_intent
    if _is_feature_allowed("controlling"):
        return "tek_summary"
    if _is_feature_allowed("teile"):
        return "teile_lager"
    return preferred_intent


@ai_api.route('/query', methods=['POST'])
@login_or_api_key_required
def query_business_data_hybrid():
    """
    Hybrid MVP für 'Google-like' Business Query API.
    - Fragetext -> Intent -> SSOT-Query
    - Antwort als Text + JSON
    - Optional: Feld ``visualization`` (Chart.js-Daten: type, title, labels, datasets, options, meta)
    - ``include_visualization`` im Body (Default true): bei false kein visualization-Block
    - Zeitbezug: Rückfrage bei Unklarheit, sonst Default aktueller Monat + YTD
    """
    try:
        payload = request.get_json() or {}
        frage = (payload.get("frage") or "").strip()
        clarification_answer = (payload.get("clarification_answer") or "").strip()
        previous_question = (payload.get("previous_question") or "").strip()
        bereich = (payload.get("bereich") or "").strip()
        include_visualization = _coerce_bool_include_visualization(payload.get("include_visualization"))

        # Folgefrage-Kontext: Rückfrage beantworten ohne den ursprünglichen Kontext zu verlieren
        if clarification_answer and previous_question:
            frage = f"{previous_question}. Praezisierung: {clarification_answer}"

        if not frage:
            return jsonify({"success": False, "error": "Bitte 'frage' im JSON-Body angeben."}), 400

        time_ctx = _resolve_time_context(frage, payload)
        if time_ctx.get("needs_clarification"):
            return jsonify({
                "success": True,
                "needs_clarification": True,
                "clarification_question": time_ctx.get("clarification_question"),
                "answer_text": "Zeitbezug unklar, bitte Zeitraum präzisieren.",
                "answer_data": {},
                "conversation": {
                    "requires_input": True,
                    "previous_question": previous_question or frage,
                    "clarification_type": "timeframe",
                },
            }), 200

        intent = _detect_intent(frage, bereich=bereich)
        intent_id = intent.get("id")

        requested_intent = intent_id
        intent_id = _fallback_to_allowed_intent(intent_id)
        fallback_applied = (intent_id != requested_intent)

        if intent_id == "tek_summary":
            if not _is_feature_allowed("controlling"):
                return jsonify({"success": False, "error": "Keine Berechtigung fuer Controlling-Daten."}), 403
            result_data = _run_query_tek(time_ctx)
        elif intent_id == "verkauf_auftragseingang":
            if not _is_verkauf_intent_allowed():
                return jsonify({"success": False, "error": "Keine Berechtigung fuer Verkaufsdaten."}), 403
            result_data = _run_query_verkauf(time_ctx)
        elif intent_id == "teile_lager":
            if not _is_feature_allowed("teile"):
                return jsonify({"success": False, "error": "Keine Berechtigung fuer Teile-/Lagerdaten."}), 403
            result_data = _run_query_teile(frage)
            if result_data.get("needs_clarification"):
                return jsonify({
                    "success": True,
                    "needs_clarification": True,
                    "clarification_question": result_data.get("clarification_question"),
                    "answer_text": "Für eine genaue Lagerantwort brauche ich noch eine Präzisierung.",
                    "answer_data": result_data,
                    "conversation": {
                        "requires_input": True,
                        "previous_question": previous_question or frage,
                        "clarification_type": "entity",
                    },
                }), 200
        elif intent_id == "servicebox_bestellungen":
            if not _is_servicebox_intent_allowed():
                return jsonify({"success": False, "error": "Keine Berechtigung fuer Teilebestellungen/ServiceBox."}), 403
            result_data = _run_query_servicebox(time_ctx, frage=frage)
        elif intent_id == "kunden_suche":
            if not _is_kunden_intent_allowed():
                return jsonify({"success": False, "error": "Keine Berechtigung fuer Kundenabfragen."}), 403
            result_data = _run_query_kunden(frage)
        else:
            # Fallback auf TEK statt Rückfrage, für direkte Ergebnisse
            if not _is_feature_allowed("controlling"):
                return jsonify({"success": False, "error": "Keine Berechtigung für Controlling-Daten."}), 403
            result_data = _run_query_tek(time_ctx)
            intent = {"id": "tek_summary", "confidence": 0.5}
            intent_id = "tek_summary"

        answer_text = _compose_answer_text(intent_id, result_data)
        if fallback_applied:
            answer_text = (
                "Hinweis: Für den ursprünglich erkannten Bereich fehlt die Berechtigung. "
                "Ich zeige stattdessen verfügbare Daten. " + answer_text
            )
        response_body: Dict[str, Any] = {
            "success": True,
            "mode": "hybrid_mvp",
            "needs_clarification": False,
            "query": intent,
            "effective_intent": intent_id,
            "fallback_applied": fallback_applied,
            "time_context": time_ctx,
            "answer_text": answer_text,
            "answer_data": result_data,
        }
        if include_visualization:
            viz = _safe_build_visualization(intent_id, result_data, time_ctx)
            if viz:
                response_body["visualization"] = viz
        return jsonify(response_body), 200

    except Exception as e:
        logger.exception("Fehler in /api/ai/query: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@ai_api.route('/analyse/geschaeftsdaten', methods=['POST'])
@login_required
def analyse_geschaeftsdaten():
    """
    Natursprachliche Analyse auf echten DRIVE-Geschäftsdaten (LM Studio).

    POST Body: { "frage": "Wie steht die TEK heute?", "bereich": "tek" (optional) }
    Nur vordefinierte Daten-Views (SSOT), keine freie SQL-Generierung.
    Erster Bereich: TEK (Controlling) – erfordert Feature 'controlling'.
    """
    try:
        if not (hasattr(current_user, "can_access_feature") and current_user.can_access_feature("controlling")):
            return jsonify({
                "success": False,
                "error": "Keine Berechtigung für Geschäftsdaten-Analyse (Feature 'controlling' erforderlich)."
            }), 403

        data = request.get_json() or {}
        frage = (data.get("frage") or "").strip()
        if not frage:
            return jsonify({"success": False, "error": "Bitte 'frage' im JSON-Body angeben."}), 400

        bereich = (data.get("bereich") or "tek").strip().lower()
        if bereich != "tek":
            return jsonify({
                "success": False,
                "error": f"Bereich '{bereich}' nicht unterstützt. Aktuell nur 'tek' (TEK/Controlling)."
            }), 400

        # SSOT: TEK-Daten aus controlling_data (aktueller Monat)
        from datetime import date
        from api.controlling_data import get_tek_data

        heute = date.today()
        tek_data = get_tek_data(monat=heute.month, jahr=heute.year, firma="0", standort="0")
        kontext_str = _build_tek_context(tek_data, heute.month, heute.year)

        system_prompt = (
            "Du bist ein Assistent für DRIVE-Kennzahlen (Autohaus). "
            "Antworte ausschließlich auf Basis der folgenden Daten. Erfinde keine Zahlen. "
            "Halte die Antwort kurz (2–5 Sätze), auf Deutsch."
        )
        user_prompt = f"Daten:\n{kontext_str}\n\nFrage des Nutzers: {frage}"

        response_text = lm_studio_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0.2,
            timeout=45,
        )

        if not response_text:
            return jsonify({
                "success": False,
                "error": "LM Studio hat keine Antwort geliefert (Timeout oder Server nicht erreichbar).",
                "kontext_bereich": "tek",
            }), 502

        return jsonify({
            "success": True,
            "antwort": response_text.strip(),
            "kontext_bereich": "tek",
            "stichtag": heute.isoformat(),
        }), 200

    except Exception as e:
        logger.exception("Fehler bei Geschäftsdaten-Analyse: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500
