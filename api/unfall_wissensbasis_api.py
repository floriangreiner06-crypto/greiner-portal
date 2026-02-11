"""
Unfall-Rechnungsprüfung – Wissensdatenbank (M4)
================================================
API für Checklisten-Positionen, Urteile und Zuordnung Urteil ↔ Position.

Endpoints:
- GET /api/unfall/checkliste          – alle Checklisten-Positionen
- GET /api/unfall/urteile             – alle Urteile (optional: position_id, q)
- GET /api/unfall/urteile/<id>        – ein Urteil inkl. zugeordnete Positionen
- GET /api/unfall/urteile/zu-position/<checkliste_id> – Urteile zu einer Kürzungsposition
- POST/PUT/DELETE für CRUD (optional, für spätere Pflege)

Erstellt: 2026-02-11 (Versicherungs-Rechnungsprüfung)
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
import logging

from api.db_utils import db_session, row_to_dict, rows_to_list

logger = logging.getLogger(__name__)

unfall_wissensbasis_api = Blueprint('unfall_wissensbasis_api', __name__, url_prefix='/api/unfall')


@unfall_wissensbasis_api.route('/checkliste', methods=['GET'])
@login_required
def get_checkliste():
    """Alle typischen Kürzungspositionen (Checkliste für M1/M2). Optional ?mit_textbausteinen=1 liefert pro Position zugehörige UE IWW Textbausteine."""
    try:
        mit_textbausteinen = request.args.get('mit_textbausteinen', '0') == '1'
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, bezeichnung, haeufigkeit, rechtslage, sort_order,
                       created_at, updated_at
                FROM unfall_checkliste_positionen
                ORDER BY sort_order NULLS LAST, bezeichnung
            """)
            items = rows_to_list(cursor.fetchall(), cursor)
            if mit_textbausteinen:
                for it in items:
                    cursor.execute("""
                        SELECT t.id, t.tb_nummer, t.titel, t.kategorie_hk, t.iww_url, t.ist_anwaltsbaustein
                        FROM unfall_textbausteine t
                        JOIN unfall_textbausteine_positionen tp ON tp.textbaustein_id = t.id
                        WHERE tp.checkliste_position_id = %s
                        ORDER BY t.tb_nummer NULLS LAST, t.titel
                    """, (it['id'],))
                    it['textbausteine'] = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_checkliste")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/urteile', methods=['GET'])
@login_required
def get_urteile():
    """Alle Urteile; optional Filter: position_id (Checklisten-ID), q (Suchtext)."""
    try:
        position_id = request.args.get('position_id', type=int)
        q = request.args.get('q', '').strip()
        with db_session() as conn:
            cursor = conn.cursor()
            if position_id:
                cursor.execute("""
                    SELECT u.id, u.aktenzeichen, u.gericht, u.urteil_datum, u.position_kategorie,
                           u.kurzfassung, u.volltext_link, u.created_at
                    FROM unfall_urteile u
                    JOIN unfall_urteile_checkliste uc ON uc.urteil_id = u.id
                    WHERE uc.checkliste_position_id = %s
                    ORDER BY u.urteil_datum DESC NULLS LAST, u.aktenzeichen
                """, (position_id,))
            elif q:
                cursor.execute("""
                    SELECT id, aktenzeichen, gericht, urteil_datum, position_kategorie,
                           kurzfassung, volltext_link, created_at
                    FROM unfall_urteile
                    WHERE aktenzeichen ILIKE %s OR gericht ILIKE %s OR kurzfassung ILIKE %s
                       OR position_kategorie ILIKE %s
                    ORDER BY urteil_datum DESC NULLS LAST, aktenzeichen
                """, (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'))
            else:
                cursor.execute("""
                    SELECT id, aktenzeichen, gericht, urteil_datum, position_kategorie,
                           kurzfassung, volltext_link, created_at
                    FROM unfall_urteile
                    ORDER BY urteil_datum DESC NULLS LAST, aktenzeichen
                """)
            items = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_urteile")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/urteile/<int:urteil_id>', methods=['GET'])
@login_required
def get_urteil(urteil_id):
    """Ein Urteil inkl. zugeordnete Checklisten-Positionen."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, aktenzeichen, gericht, urteil_datum, position_kategorie,
                       kurzfassung, volltext_link, created_at, updated_at
                FROM unfall_urteile WHERE id = %s
            """, (urteil_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Urteil nicht gefunden'}), 404
            urteil = row_to_dict(row, cursor)
            cursor.execute("""
                SELECT c.id, c.bezeichnung, c.haeufigkeit, c.rechtslage
                FROM unfall_checkliste_positionen c
                JOIN unfall_urteile_checkliste uc ON uc.checkliste_position_id = c.id
                WHERE uc.urteil_id = %s
                ORDER BY c.sort_order NULLS LAST
            """, (urteil_id,))
            urteil['positionen'] = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'item': urteil})
    except Exception as e:
        logger.exception("get_urteil")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/urteile/zu-position/<int:checkliste_id>', methods=['GET'])
@login_required
def get_urteile_zu_position(checkliste_id):
    """Urteile, die zu einer bestimmten Kürzungsposition passen (für M2 Abwehr)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.aktenzeichen, u.gericht, u.urteil_datum, u.kurzfassung, u.volltext_link
                FROM unfall_urteile u
                JOIN unfall_urteile_checkliste uc ON uc.urteil_id = u.id
                WHERE uc.checkliste_position_id = %s
                ORDER BY u.urteil_datum DESC NULLS LAST
            """, (checkliste_id,))
            items = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_urteile_zu_position")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/textbausteine', methods=['GET'])
@login_required
def get_textbausteine():
    """Alle UE IWW Textbausteine; optional Filter: position_id, kategorie_hk, thema."""
    try:
        position_id = request.args.get('position_id', type=int)
        kategorie_hk = request.args.get('kategorie_hk', '').strip()
        thema = request.args.get('thema', '').strip()
        with db_session() as conn:
            cursor = conn.cursor()
            if position_id:
                cursor.execute("""
                    SELECT t.id, t.tb_nummer, t.titel, t.beschreibung, t.kategorie_hk, t.datum, t.typ, t.thema, t.rubrik, t.iww_url, t.ist_anwaltsbaustein
                    FROM unfall_textbausteine t
                    JOIN unfall_textbausteine_positionen tp ON tp.textbaustein_id = t.id
                    WHERE tp.checkliste_position_id = %s
                    ORDER BY t.tb_nummer NULLS LAST, t.titel
                """, (position_id,))
            else:
                sql = """
                    SELECT id, tb_nummer, titel, beschreibung, kategorie_hk, datum, typ, thema, rubrik, iww_url, ist_anwaltsbaustein
                    FROM unfall_textbausteine WHERE 1=1
                """
                params = []
                if kategorie_hk:
                    sql += " AND kategorie_hk = %s"
                    params.append(kategorie_hk)
                if thema:
                    sql += " AND thema ILIKE %s"
                    params.append(f'%{thema}%')
                sql += " ORDER BY tb_nummer NULLS LAST, titel LIMIT 500"
                cursor.execute(sql, params or None)
            items = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_textbausteine")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/textbausteine/zu-position/<int:checkliste_id>', methods=['GET'])
@login_required
def get_textbausteine_zu_position(checkliste_id):
    """Textbausteine (UE IWW) zu einer Kürzungsposition."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, t.tb_nummer, t.titel, t.beschreibung, t.kategorie_hk, t.iww_url, t.ist_anwaltsbaustein
                FROM unfall_textbausteine t
                JOIN unfall_textbausteine_positionen tp ON tp.textbaustein_id = t.id
                WHERE tp.checkliste_position_id = %s
                ORDER BY t.tb_nummer NULLS LAST, t.titel
            """, (checkliste_id,))
            items = rows_to_list(cursor.fetchall(), cursor)
        return jsonify({'ok': True, 'items': items})
    except Exception as e:
        logger.exception("get_textbausteine_zu_position")
        return jsonify({'ok': False, 'error': str(e)}), 500


@unfall_wissensbasis_api.route('/externe-quellen', methods=['GET'])
@login_required
def get_externe_quellen():
    """Link-Sammlung externe Referenzquellen (statisch aus Feature-Plan)."""
    quellen = [
        {'name': 'UE IWW (Unfallregulierung effektiv)', 'url': 'https://www.iww.de/ue/downloads', 'nutzen': '702 Textbausteine für Kürzungsabwehr (Digital-Abo)'},
        {'name': 'ZKF (Zentralverband Karosserie- und Fahrzeugtechnik)', 'url': 'https://www.zkf.de', 'nutzen': 'SOS Rechnungskürzung, Branchenstandards'},
        {'name': 'Captain HUK', 'url': 'https://www.captain-huk.de', 'nutzen': 'Größte Urteilsdatenbank zu Kürzungen, nach Versicherer sortiert'},
        {'name': 'schaden.news', 'url': 'https://www.schaden.news', 'nutzen': 'Aktuelle Berichte über Kürzungspraktiken'},
        {'name': 'Kanzlei Voigt', 'url': 'https://www.kanzlei-voigt.de', 'nutzen': 'Fachanwalt Werkstattrecht, Musterurteile'},
        {'name': 'Kanzlei Schleyer', 'url': 'https://www.kanzlei-schleyer.de', 'nutzen': 'Praxisbeispiele Kürzungsabwehr'},
        {'name': 'CarRight.de', 'url': 'https://www.carright.de', 'nutzen': 'Stellungnahmen gegen ControlExpert'},
        {'name': 'Stiftung Warentest', 'url': 'https://www.test.de', 'nutzen': 'Verbraucherübersicht Versicherer-Tricks'},
        {'name': 'ra-kotz.de', 'url': 'https://www.ra-kotz.de', 'nutzen': 'Aktuelle Urteile zum Werkstattrisiko'},
    ]
    return jsonify({'ok': True, 'items': quellen})
