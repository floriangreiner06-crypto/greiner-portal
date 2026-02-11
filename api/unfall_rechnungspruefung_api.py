"""
Unfall-Rechnungsprüfung M1 – Vollständigkeitscheck
==================================================
API: Versicherungsaufträge aus Locosoft, Vollständigkeitscheck gegen Checkliste.
Ebene 1: Gutachten-PDF-Upload, AI-Extraktion, Abgleich mit loco_labours.
Ebene 2: Checkliste (12 Standard-Positionen) gegen Rechnung/Gutachten.

Endpoints:
- GET  /api/unfall/auftraege                      – Liste Versicherungsaufträge (Filter: von, bis)
- GET  /api/unfall/auftrag/<nummer>/check         – Vollständigkeitscheck (Ebene 1 + 2)
- POST /api/unfall/auftrag/<nummer>/gutachten/upload – Gutachten-PDF hochladen, AI parst, speichern
- GET  /api/unfall/auftrag/<nummer>/gutachten     – Liste Gutachten zum Auftrag

Erstellt: 2026-02-11
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
import logging
import re
import os
import json
from datetime import datetime
from decimal import Decimal

from api.db_utils import db_session, row_to_dict, rows_to_list

logger = logging.getLogger(__name__)

# Verzeichnis für hochgeladene Gutachten-PDFs
UNFALL_GUTACHTEN_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'unfall_gutachten')

unfall_rechnungspruefung_api = Blueprint('unfall_rechnungspruefung_api', __name__, url_prefix='/api/unfall')

# Mapping: Suchbegriffe (lowercase) in text_line → Checklisten-Position (ID aus unfall_checkliste_positionen)
# Reihenfolge: erste Treffer gewinnt; mehrere Keywords können gleiche Position liefern
TEXT_TO_CHECKLIST_MAPPING = [
    (r'verbring', 1),           # Verbringungskosten
    (r'upe|aufschlag', 2),      # UPE-Aufschläge (Ersatzteilpreisaufschläge)
    (r'beilack|farbangleich', 3),  # Beilackierung
    (r'desinfek', 4),           # Desinfektionskosten
    (r'stundenverrechnung|günstigere werkstatt|referenzwerkstatt', 5),  # Stundenverrechnungssätze
    (r'kleinteil|befestigung', 6),  # Kleinersatzteile / Befestigungssätze
    (r'probefahrt', 7),         # Probefahrtkosten
    (r'reinigu', 8),            # Reinigungskosten
    (r'entsorgu', 9),           # Entsorgungskosten
    (r'mietwagen|ersatzwagen|werkstattersatz', 10),  # Mietwagenkosten bei Verzögerung
    (r'ofentrockn', 11),        # Ofentrocknung
    (r'unfallverhüt', 12),      # Unfallverhütungskosten
]


def _erkennbare_positionen_aus_text(text):
    """Ermittelt Checklisten-IDs, die in text (z.B. text_line) vorkommen."""
    if not text or not isinstance(text, str):
        return set()
    text_lower = text.lower()
    found = set()
    for pattern, checklist_id in TEXT_TO_CHECKLIST_MAPPING:
        if re.search(pattern, text_lower):
            found.add(checklist_id)
    return found


@unfall_rechnungspruefung_api.route('/auftraege', methods=['GET'])
@login_required
def get_auftraege():
    """Liste aller Aufträge, bei denen paying_customer in der Versicherungs-Whitelist ist."""
    try:
        von = request.args.get('von')  # YYYY-MM-DD
        bis = request.args.get('bis')  # YYYY-MM-DD
        with db_session() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT o.number AS auftragsnummer, o.order_date AS order_date,
                       o.subsidiary, o.order_customer, o.paying_customer,
                       v.versicherung_name,
                       (SELECT COUNT(*) FROM loco_labours l WHERE l.order_number = o.number) AS anzahl_positionen
                FROM loco_orders o
                JOIN unfall_versicherung_kunden v
                  ON v.customer_number = o.paying_customer AND v.subsidiary = o.subsidiary AND v.ist_aktiv = true
                WHERE 1=1
            """
            params = []
            if von:
                sql += " AND o.order_date::date >= %s"
                params.append(von)
            if bis:
                sql += " AND o.order_date::date <= %s"
                params.append(bis)
            sql += " ORDER BY o.order_date DESC NULLS LAST, o.number DESC LIMIT 500"
            cursor.execute(sql, params or None)
            items = rows_to_list(cursor.fetchall(), cursor)
        # Datum serialisierbar machen
        for row in items:
            if row.get('order_date') is not None:
                row['order_date'] = row['order_date'].isoformat() if hasattr(row['order_date'], 'isoformat') else str(row['order_date'])
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_auftraege")
        return jsonify({'ok': False, 'error': str(e)}), 500


def _gutachten_position_in_rechnung_gefunden(gutachten_pos, labours):
    """Prüft ob eine Gutachten-Position in loco_labours (text_line/net_price) vorkommt."""
    besch = (gutachten_pos.get('beschreibung') or '').lower()[:80]
    betrag = gutachten_pos.get('betrag_netto')
    teile = (gutachten_pos.get('teilenummer') or '').strip()
    for lab in labours:
        text = (lab.get('text_line') or '').lower()
        if besch and besch in text:
            return True
        if teile and teile in text:
            return True
        net = lab.get('net_price_in_order')
        if betrag is not None and net is not None and abs(float(betrag) - float(net)) < 0.02:
            return True
    return False


@unfall_rechnungspruefung_api.route('/auftrag/<int:nummer>/check', methods=['GET'])
@login_required
def get_auftrag_check(nummer):
    """
    Vollständigkeitscheck für einen Auftrag (Ebene 1 + 2):
    - Ebene 1: Wenn Gutachten vorhanden: Abgleich Gutachten-Positionen mit loco_labours
    - Ebene 2: Checkliste (12 Standard-Positionen) vs. Rechnung/Gutachten
    - Rückgabe: vorhandene/fehlende_positionen, ggf. gutachten_abgleich, ampel (gruen/gelb/rot)
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            # 1) Checkliste laden
            cursor.execute("""
                SELECT id, bezeichnung, haeufigkeit, rechtslage, sort_order
                FROM unfall_checkliste_positionen
                ORDER BY sort_order NULLS LAST, id
            """)
            checkliste = rows_to_list(cursor.fetchall(), cursor)
            alle_ids = {r['id'] for r in checkliste}

            # 2) Labours für Auftrag laden
            cursor.execute("""
                SELECT order_position, order_position_line, charge_type, time_units, net_price_in_order, text_line
                FROM loco_labours
                WHERE order_number = %s
                ORDER BY order_position, order_position_line
            """, (nummer,))
            labours = rows_to_list(cursor.fetchall(), cursor)

            # 3) Ebene 1: Neuestes Gutachten + Positionen laden, Abgleich mit labours
            cursor.execute("""
                SELECT id FROM unfall_gutachten WHERE auftrag_nummer = %s ORDER BY upload_datum DESC LIMIT 1
            """, (nummer,))
            gutachten_row = cursor.fetchone()
            gutachten_abgleich = None
            fehlende_gutachten_positionen = []
            if gutachten_row:
                gid = gutachten_row[0] if hasattr(gutachten_row, '__getitem__') else gutachten_row['id']
                cursor.execute("""
                    SELECT id, position_typ, beschreibung, arbeitswerte, betrag_netto, teilenummer, in_rechnung_gefunden
                    FROM unfall_gutachten_positionen WHERE gutachten_id = %s ORDER BY id
                """, (gid,))
                g_positionen = rows_to_list(cursor.fetchall(), cursor)
                for gp in g_positionen:
                    gefunden = _gutachten_position_in_rechnung_gefunden(gp, labours)
                    if gefunden:
                        cursor.execute("UPDATE unfall_gutachten_positionen SET in_rechnung_gefunden = true, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (gp['id'],))
                    else:
                        fehlende_gutachten_positionen.append({
                            'id': gp.get('id'),
                            'position_typ': gp.get('position_typ'),
                            'beschreibung': gp.get('beschreibung'),
                            'betrag_netto': float(gp['betrag_netto']) if gp.get('betrag_netto') is not None else None,
                        })
                conn.commit()
                gutachten_abgleich = {
                    'gutachten_id': gid,
                    'anzahl_positionen': len(g_positionen),
                    'fehlende_in_rechnung': fehlende_gutachten_positionen,
                }

        # 4) Ebene 2: Aus text_line erkennbare Checklisten-Positionen (Rechnung + ggf. Gutachten-Text)
        vorhanden_ids = set()
        for row in labours:
            text = row.get('text_line') or ''
            vorhanden_ids |= _erkennbare_positionen_aus_text(text)
        fehlend_ids = alle_ids - vorhanden_ids
        vorhandene_positionen = [r for r in checkliste if r['id'] in vorhanden_ids]
        fehlende_positionen = [r for r in checkliste if r['id'] in fehlend_ids]

        # 5) Ampel: Rot wenn Gutachten-Positionen fehlen ODER Checkliste fehlt; Gelb wenn nur Checkliste; Grün wenn alles drin
        if fehlende_gutachten_positionen:
            ampel = 'rot'
        elif fehlende_positionen:
            ampel = 'gelb'  # Checkliste prüfen
        else:
            ampel = 'gruen'

        out = {
            'ok': True,
            'auftragsnummer': nummer,
            'anzahl_labours': len(labours),
            'vorhandene_positionen': vorhandene_positionen,
            'fehlende_positionen': fehlende_positionen,
            'ampel': ampel,
        }
        if gutachten_abgleich is not None:
            out['gutachten_abgleich'] = gutachten_abgleich
        return jsonify(out)
    except Exception as e:
        logger.exception("get_auftrag_check")
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# EBENE 1: Gutachten-PDF-Upload + AI-Extraktion
# =============================================================================

def _pdf_text_extract(filepath):
    """Extrahiert Text aus PDF (pdfplumber)."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber nicht installiert – PDF-Text-Extraktion nicht möglich")
        return None
    try:
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts) if text_parts else None
    except Exception as e:
        logger.exception("PDF-Text-Extraktion fehlgeschlagen: %s", e)
        return None


def _ai_extract_gutachten(text):
    """
    Sendet Gutachten-Text an LM Studio, erwartet JSON mit:
    gutachten_nummer, sachverstaendiger, gutachten_summe_netto, positionen[]
    positionen: position_typ (arbeitsposition|ersatzteil|lackierung|nebenkosten), beschreibung, arbeitswerte, betrag_netto, teilenummer (optional)
    """
    try:
        from api.ai_api import lm_studio_client
    except ImportError:
        logger.warning("ai_api nicht verfügbar – AI-Extraktion übersprungen")
        return None
    prompt = f"""Extrahiere aus dem folgenden Sachverständigengutachten (Werkstatt/Unfall) strukturierte Daten.

Text des Gutachtens:
---
{text[:12000]}
---

Antworte NUR mit einem JSON-Objekt (kein anderer Text), Format:
{{
  "gutachten_nummer": "Nummer oder Kennung des Gutachtens",
  "sachverstaendiger": "Name/Firma des Sachverständigen",
  "gutachten_summe_netto": 1234.56,
  "positionen": [
    {{
      "position_typ": "arbeitsposition|ersatzteil|lackierung|nebenkosten",
      "beschreibung": "Kurzbeschreibung der Position",
      "arbeitswerte": 1.5,
      "betrag_netto": 123.45,
      "teilenummer": "optional bei Ersatzteilen"
    }}
  ]
}}

- position_typ: arbeitsposition (Arbeit mit AW), ersatzteil, lackierung (Lack/Beilackierung), nebenkosten (Verbringung, Probefahrt, Reinigung, etc.)
- arbeitswerte: Zahl (AW) oder null
- betrag_netto: Euro-Betrag oder null
- Nur gültiges JSON ausgeben, keine Erklärungen."""

    messages = [
        {"role": "system", "content": "Du extrahierst Daten aus deutschen Sachverständigengutachten. Antworte ausschließlich mit gültigem JSON."},
        {"role": "user", "content": prompt}
    ]
    response = lm_studio_client.chat_completion(
        messages=messages,
        max_tokens=2000,
        temperature=0.2
    )
    if not response:
        return None
    # Optional: Markdown-Codeblock entfernen
    raw = response.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("AI-Antwort kein gültiges JSON: %s", e)
        return None


@unfall_rechnungspruefung_api.route('/auftrag/<int:nummer>/gutachten/upload', methods=['POST'])
@login_required
def upload_gutachten(nummer):
    """Gutachten-PDF hochladen: Speichern, Text extrahieren, AI parst Positionen, in DB speichern."""
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'Keine Datei (file) hochgeladen'}), 400
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({'ok': False, 'error': 'Bitte eine PDF-Datei auswählen'}), 400

    os.makedirs(UNFALL_GUTACHTEN_UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = re.sub(r'[^\w\-\.]', '_', file.filename)[:80]
    pdf_name = f"auftrag_{nummer}_{timestamp}_{safe_name}"
    pdf_path = os.path.join(UNFALL_GUTACHTEN_UPLOAD_DIR, pdf_name)
    try:
        file.save(pdf_path)
    except Exception as e:
        logger.exception("PDF speichern fehlgeschlagen")
        return jsonify({'ok': False, 'error': f'Speichern fehlgeschlagen: {e}'}), 500

    text = _pdf_text_extract(pdf_path)
    if not text:
        return jsonify({'ok': False, 'error': 'PDF-Text konnte nicht extrahiert werden (leer oder Fehler)'}), 400

    data = _ai_extract_gutachten(text)
    if not data or not isinstance(data, dict):
        # Trotzdem Gutachten anlegen, ohne Positionen (manuell nachpflegbar)
        data = {
            'gutachten_nummer': None,
            'sachverstaendiger': None,
            'gutachten_summe_netto': None,
            'positionen': []
        }

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO unfall_gutachten (auftrag_nummer, pdf_path, gutachten_nummer, sachverstaendiger, gutachten_summe_netto)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, upload_datum
        """, (
            nummer,
            pdf_path,
            data.get('gutachten_nummer'),
            data.get('sachverstaendiger'),
            float(data.get('gutachten_summe_netto')) if data.get('gutachten_summe_netto') is not None else None
        ))
        row = cursor.fetchone()
        gutachten_id = row[0] if row else None
        upload_datum = row[1] if row and len(row) > 1 else None
        if not gutachten_id:
            return jsonify({'ok': False, 'error': 'Gutachten konnte nicht angelegt werden'}), 500

        for pos in data.get('positionen') or []:
            if not isinstance(pos, dict):
                continue
            typ = (pos.get('position_typ') or 'arbeitsposition')[:50]
            beschreibung = (pos.get('beschreibung') or '')[:2000]
            aw = pos.get('arbeitswerte')
            betrag = pos.get('betrag_netto')
            teilenummer = (pos.get('teilenummer') or '')[:100] if pos.get('teilenummer') else None
            cursor.execute("""
                INSERT INTO unfall_gutachten_positionen (gutachten_id, position_typ, beschreibung, arbeitswerte, betrag_netto, teilenummer)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                gutachten_id,
                typ,
                beschreibung or None,
                float(aw) if aw is not None else None,
                float(betrag) if betrag is not None else None,
                teilenummer
            ))
        conn.commit()

    return jsonify({
        'ok': True,
        'gutachten_id': gutachten_id,
        'auftrag_nummer': nummer,
        'upload_datum': upload_datum.isoformat() if upload_datum and hasattr(upload_datum, 'isoformat') else str(upload_datum),
        'pdf_path': pdf_path,
        'gutachten_nummer': data.get('gutachten_nummer'),
        'sachverstaendiger': data.get('sachverstaendiger'),
        'gutachten_summe_netto': data.get('gutachten_summe_netto'),
        'anzahl_positionen': len(data.get('positionen') or []),
    })


@unfall_rechnungspruefung_api.route('/auftrag/<int:nummer>/gutachten', methods=['GET'])
@login_required
def get_gutachten(nummer):
    """Liste aller Gutachten (inkl. Positionen) für einen Auftrag."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, auftrag_nummer, upload_datum, pdf_path, gutachten_nummer, sachverstaendiger, gutachten_summe_netto
                FROM unfall_gutachten
                WHERE auftrag_nummer = %s
                ORDER BY upload_datum DESC
            """, (nummer,))
            gutachten_liste = rows_to_list(cursor.fetchall(), cursor)
            for g in gutachten_liste:
                if g.get('upload_datum'):
                    g['upload_datum'] = g['upload_datum'].isoformat() if hasattr(g['upload_datum'], 'isoformat') else str(g['upload_datum'])
                cursor.execute("""
                    SELECT id, position_typ, beschreibung, arbeitswerte, betrag_netto, teilenummer, in_rechnung_gefunden
                    FROM unfall_gutachten_positionen
                    WHERE gutachten_id = %s
                    ORDER BY id
                """, (g['id'],))
                g['positionen'] = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'gutachten': gutachten_liste})
    except Exception as e:
        logger.exception("get_gutachten")
        return jsonify({'ok': False, 'error': str(e)}), 500
