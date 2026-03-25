#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hilfe-API – Kategorien, Artikel, Volltextsuche, Feedback
Workstream: Hilfe | Erstellt: 2026-02-24
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from api.db_utils import db_session, row_to_dict, rows_to_list
from decorators.auth_decorators import admin_required

logger = logging.getLogger(__name__)

# KI-Erweiterung (Bedrock) – optional, nur bei Bedarf importieren
def _hilfe_ki_erweitern(artikel_id: int):
    """Lädt Artikel, ruft Bedrock auf, gibt erweiterten Inhalt zurück."""
    from api.hilfe_bedrock_service import erweitern_mit_ki
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, titel, inhalt, tags FROM hilfe_artikel WHERE id = %s',
            (artikel_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        art = row_to_dict(row, cursor)
    return erweitern_mit_ki(
        artikel_titel=art.get('titel') or '',
        aktueller_inhalt=art.get('inhalt') or '',
        tags=art.get('tags'),
    )

hilfe_api = Blueprint('hilfe_api', __name__, url_prefix='/api/hilfe')


def _filter_artikel_nach_rolle(artikel, user_role):
    """Filtert Artikel: sichtbar_fuer_rollen NULL = alle, sonst nur wenn user_role in Liste."""
    if not artikel.get('sichtbar_fuer_rollen'):
        return True
    roles_str = artikel.get('sichtbar_fuer_rollen') or ''
    allowed = [r.strip() for r in roles_str.split(',') if r.strip()]
    return user_role in allowed if allowed else True


# -----------------------------------------------------------------------------
# Öffentliche Endpoints (login_required)
# -----------------------------------------------------------------------------

@hilfe_api.route('/kategorien', methods=['GET'])
@login_required
def get_kategorien():
    """GET /api/hilfe/kategorien – Alle aktiven Kategorien mit Artikelanzahl."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT k.id, k.name, k.slug, k.beschreibung, k.icon, k.sort_order, k.modul_route,
                       COUNT(a.id) FILTER (WHERE a.aktiv = true AND a.freigabe_status = 'freigegeben') AS artikel_anzahl
                FROM hilfe_kategorien k
                LEFT JOIN hilfe_artikel a ON a.kategorie_id = k.id
                WHERE k.aktiv = true
                GROUP BY k.id, k.name, k.slug, k.beschreibung, k.icon, k.sort_order, k.modul_route
                ORDER BY k.sort_order, k.name
            ''')
            rows = cursor.fetchall()
        items = rows_to_list(rows, cursor)
        return jsonify({'kategorien': items})
    except Exception as e:
        logger.exception('get_kategorien: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/kategorie/<slug>', methods=['GET'])
@login_required
def get_kategorie(slug):
    """GET /api/hilfe/kategorie/<slug> – Kategorie inkl. Artikel-Liste."""
    try:
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') or 'mitarbeiter'
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, name, slug, beschreibung, icon, sort_order, modul_route FROM hilfe_kategorien WHERE slug = %s AND aktiv = true',
                (slug,)
            )
            row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Kategorie nicht gefunden'}), 404
        kat = row_to_dict(row)
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, titel, slug, sort_order, aufrufe
                FROM hilfe_artikel
                WHERE kategorie_id = %s AND aktiv = true AND freigabe_status = 'freigegeben'
                ORDER BY sort_order, titel
            ''', (kat['id'],))
            rows = cursor.fetchall()
        artikel_list = rows_to_list(rows, cursor)
        artikel_list = [a for a in artikel_list if _filter_artikel_nach_rolle(a, user_role)]
        kat['artikel'] = artikel_list
        return jsonify(kat)
    except Exception as e:
        logger.exception('get_kategorie: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/artikel/<int:artikel_id>', methods=['GET'])
@login_required
def get_artikel(artikel_id):
    """GET /api/hilfe/artikel/<id> – Einzelartikel (erhöht aufrufe)."""
    try:
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') or 'mitarbeiter'
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.kategorie_id, a.titel, a.slug, a.inhalt, a.inhalt_format, a.tags,
                       a.aufrufe, a.hilfreich_ja, a.hilfreich_nein, a.sichtbar_fuer_rollen,
                       k.name AS kategorie_name, k.slug AS kategorie_slug
                FROM hilfe_artikel a
                JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                WHERE a.id = %s AND a.aktiv = true AND a.freigabe_status = 'freigegeben' AND k.aktiv = true
            ''', (artikel_id,))
            row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Artikel nicht gefunden'}), 404
        art = row_to_dict(row)
        if not _filter_artikel_nach_rolle(art, user_role):
            return jsonify({'error': 'Kein Zugriff'}), 403
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE hilfe_artikel SET aufrufe = aufrufe + 1 WHERE id = %s', (artikel_id,))
            conn.commit()
        art['aufrufe'] = (art.get('aufrufe') or 0) + 1
        return jsonify(art)
    except Exception as e:
        logger.exception('get_artikel: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/suche', methods=['GET'])
@login_required
def suche():
    """GET /api/hilfe/suche?q=... – Volltextsuche (PostgreSQL tsvector)."""
    q = (request.args.get('q') or '').strip()
    if not q or len(q) < 2:
        return jsonify({'artikel': []})
    try:
        user_role = getattr(current_user, 'portal_role', 'mitarbeiter') or 'mitarbeiter'
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.kategorie_id, a.titel, a.slug, a.sichtbar_fuer_rollen,
                       k.name AS kategorie_name, k.slug AS kategorie_slug,
                       ts_headline('german', a.inhalt, plainto_tsquery('german', %s), 'MaxFragments=2, MaxWords=50, MinWords=25') AS snippet
                FROM hilfe_artikel a
                JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                WHERE a.aktiv = true AND a.freigabe_status = 'freigegeben' AND k.aktiv = true AND a.tsv @@ plainto_tsquery('german', %s)
                ORDER BY ts_rank(a.tsv, plainto_tsquery('german', %s)) DESC
                LIMIT 20
            ''', (q, q, q))
            rows = cursor.fetchall()
        items = rows_to_list(rows, cursor)
        items = [x for x in items if _filter_artikel_nach_rolle(x, user_role)]
        return jsonify({'artikel': items})
    except Exception as e:
        logger.exception('suche: %s', e)
        return jsonify({'artikel': [], 'error': str(e)}), 500


@hilfe_api.route('/artikel/<int:artikel_id>/feedback', methods=['POST'])
@login_required
def post_feedback(artikel_id):
    """POST /api/hilfe/artikel/<id>/feedback – Body: { hilfreich: true|false, kommentar?: string }."""
    try:
        data = request.get_json() or {}
        hilfreich = data.get('hilfreich', True)
        kommentar = (data.get('kommentar') or '').strip() or None
        user_id = getattr(current_user, 'username', None) or str(getattr(current_user, 'id', ''))
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM hilfe_artikel WHERE id = %s AND aktiv = true AND freigabe_status = %s', (artikel_id, 'freigegeben'))
            if not cursor.fetchone():
                return jsonify({'error': 'Artikel nicht gefunden'}), 404
            cursor.execute(
                'INSERT INTO hilfe_feedback (artikel_id, user_id, hilfreich, kommentar) VALUES (%s, %s, %s, %s)',
                (artikel_id, user_id, bool(hilfreich), kommentar)
            )
            if hilfreich:
                cursor.execute('UPDATE hilfe_artikel SET hilfreich_ja = hilfreich_ja + 1 WHERE id = %s', (artikel_id,))
            else:
                cursor.execute('UPDATE hilfe_artikel SET hilfreich_nein = hilfreich_nein + 1 WHERE id = %s', (artikel_id,))
            conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        logger.exception('post_feedback: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/beliebt', methods=['GET'])
@login_required
def get_beliebt():
    """GET /api/hilfe/beliebt – Top 10 nach aufrufe."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.titel, a.slug, a.aufrufe, k.name AS kategorie_name, k.slug AS kategorie_slug
                FROM hilfe_artikel a
                JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                WHERE a.aktiv = true AND a.freigabe_status = 'freigegeben' AND k.aktiv = true
                ORDER BY a.aufrufe DESC
                LIMIT 10
            ''')
            rows = cursor.fetchall()
        return jsonify({'artikel': rows_to_list(rows, cursor)})
    except Exception as e:
        logger.exception('get_beliebt: %s', e)
        return jsonify({'artikel': []}), 500


@hilfe_api.route('/health', methods=['GET'])
def health():
    """GET /api/hilfe/health – Health-Check (ohne Login)."""
    return jsonify({'status': 'ok', 'service': 'hilfe-api'})


@hilfe_api.route('/ki/erweitern', methods=['POST'])
@admin_required
def ki_erweitern():
    """
    POST /api/hilfe/ki/erweitern – Artikel mit KI (LM Studio / Bedrock) erweitern.
    Body: { "artikel_id": <int> }. Antwort: { "inhalt": "<markdown>", "kontext_verwendet": bool } oder { "error": "..." }.
    """
    try:
        data = request.get_json() or {}
        artikel_id = data.get('artikel_id')
        if artikel_id is None:
            return jsonify({'error': 'artikel_id fehlt'}), 400
        try:
            artikel_id = int(artikel_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'artikel_id muss eine Zahl sein'}), 400
        result = _hilfe_ki_erweitern(artikel_id)
        if result is None:
            return jsonify({'error': 'Artikel nicht gefunden'}), 404
        if 'error' in result:
            return jsonify({'error': result['error']}), 502
        return jsonify(result)
    except Exception as e:
        logger.exception('ki_erweitern: %s', e)
        return jsonify({'error': f'Serverfehler bei KI-Erweiterung: {str(e)}'}), 500


# -----------------------------------------------------------------------------
# Admin-API (CRUD Kategorien/Artikel) – optional, für Admin-UI
# -----------------------------------------------------------------------------

@hilfe_api.route('/admin/kategorien', methods=['GET'])
@admin_required
def admin_get_kategorien():
    """Alle Kategorien inkl. Artikelanzahl (Admin)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT k.*, COUNT(a.id) AS artikel_anzahl
                FROM hilfe_kategorien k
                LEFT JOIN hilfe_artikel a ON a.kategorie_id = k.id
                GROUP BY k.id
                ORDER BY k.sort_order, k.name
            ''')
            rows = cursor.fetchall()
        return jsonify({'kategorien': rows_to_list(rows, cursor)})
    except Exception as e:
        logger.exception('admin_get_kategorien: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel', methods=['GET'])
@admin_required
def admin_get_artikel():
    """Alle Artikel (Admin), optional ?kategorie_id=."""
    kategorie_id = request.args.get('kategorie_id', type=int)
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            if kategorie_id:
                cursor.execute('''
                    SELECT a.*, k.name AS kategorie_name
                    FROM hilfe_artikel a
                    JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                    WHERE a.kategorie_id = %s
                    ORDER BY a.sort_order, a.titel
                ''', (kategorie_id,))
            else:
                cursor.execute('''
                    SELECT a.*, k.name AS kategorie_name
                    FROM hilfe_artikel a
                    JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                    ORDER BY k.sort_order, a.sort_order, a.titel
                ''')
            rows = cursor.fetchall()
        return jsonify({'artikel': rows_to_list(rows, cursor)})
    except Exception as e:
        logger.exception('admin_get_artikel: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel/<int:artikel_id>', methods=['GET'])
@admin_required
def admin_get_artikel_detail(artikel_id):
    """Einzelartikel für Bearbeitung (Admin)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, k.name AS kategorie_name, k.slug AS kategorie_slug
                FROM hilfe_artikel a
                JOIN hilfe_kategorien k ON k.id = a.kategorie_id
                WHERE a.id = %s
            ''', (artikel_id,))
            row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Artikel nicht gefunden'}), 404
        return jsonify(row_to_dict(row))
    except Exception as e:
        logger.exception('admin_get_artikel_detail: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel', methods=['POST'])
@admin_required
def admin_create_artikel():
    """Artikel anlegen (Admin). Body: kategorie_id, titel, slug, inhalt, inhalt_format?, tags?, sort_order?, sichtbar_fuer_rollen?."""
    try:
        data = request.get_json() or {}
        kategorie_id = data.get('kategorie_id')
        titel = (data.get('titel') or '').strip()
        slug = (data.get('slug') or '').strip() or titel.lower().replace(' ', '-').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        if not kategorie_id or not titel:
            return jsonify({'error': 'kategorie_id und titel erforderlich'}), 400
        inhalt = data.get('inhalt') or ''
        inhalt_format = data.get('inhalt_format') or 'markdown'
        tags = (data.get('tags') or '').strip() or None
        sort_order = data.get('sort_order', 0)
        sichtbar_fuer_rollen = (data.get('sichtbar_fuer_rollen') or '').strip() or None
        erstellt_von = getattr(current_user, 'username', None)
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hilfe_artikel (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order, sichtbar_fuer_rollen, erstellt_von, freigabe_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'entwurf')
                RETURNING id
            ''', (kategorie_id, titel, slug, inhalt, inhalt_format, tags, sort_order, sichtbar_fuer_rollen, erstellt_von))
            row = cursor.fetchone()
            new_id = row[0] if row else None
            conn.commit()
        return jsonify({'id': new_id, 'slug': slug}), 201
    except Exception as e:
        logger.exception('admin_create_artikel: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel/<int:artikel_id>', methods=['PUT'])
@admin_required
def admin_update_artikel(artikel_id):
    """Artikel aktualisieren (Admin)."""
    try:
        data = request.get_json() or {}
        titel = (data.get('titel') or '').strip()
        slug = (data.get('slug') or '').strip()
        inhalt = data.get('inhalt')
        inhalt_format = data.get('inhalt_format')
        tags = (data.get('tags') or '').strip() or None
        sort_order = data.get('sort_order')
        sichtbar_fuer_rollen = (data.get('sichtbar_fuer_rollen') or '').strip() or None
        aktiv = data.get('aktiv') if 'aktiv' in data else None
        with db_session() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if titel:
                updates.append('titel = %s')
                params.append(titel)
            if slug:
                updates.append('slug = %s')
                params.append(slug)
            if inhalt is not None:
                updates.append('inhalt = %s')
                params.append(inhalt)
            if inhalt_format is not None:
                updates.append('inhalt_format = %s')
                params.append(inhalt_format)
            if tags is not None:
                updates.append('tags = %s')
                params.append(tags)
            if sort_order is not None:
                updates.append('sort_order = %s')
                params.append(sort_order)
            if sichtbar_fuer_rollen is not None:
                updates.append('sichtbar_fuer_rollen = %s')
                params.append(sichtbar_fuer_rollen)
            if aktiv is not None:
                updates.append('aktiv = %s')
                params.append(aktiv)
            if not updates:
                return jsonify({'error': 'Keine Felder zum Aktualisieren'}), 400
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(artikel_id)
            cursor.execute(
                'UPDATE hilfe_artikel SET ' + ', '.join(updates) + ' WHERE id = %s',
                params
            )
            if cursor.rowcount == 0:
                return jsonify({'error': 'Artikel nicht gefunden'}), 404
            conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        logger.exception('admin_update_artikel: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel/<int:artikel_id>/freigeben', methods=['POST'])
@admin_required
def admin_artikel_freigeben(artikel_id):
    """Artikel freigeben – erscheint in der öffentlichen Hilfe."""
    try:
        username = getattr(current_user, 'username', None) or str(getattr(current_user, 'id', ''))
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE hilfe_artikel
                SET freigabe_status = 'freigegeben', freigegeben_am = CURRENT_TIMESTAMP, freigegeben_von = %s
                WHERE id = %s
            ''', (username, artikel_id))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Artikel nicht gefunden'}), 404
            conn.commit()
        return jsonify({'ok': True, 'freigabe_status': 'freigegeben'})
    except Exception as e:
        logger.exception('admin_artikel_freigeben: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel/<int:artikel_id>/entwurf', methods=['POST'])
@admin_required
def admin_artikel_entwurf(artikel_id):
    """Artikel zurück auf Entwurf – nur noch im Admin sichtbar."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE hilfe_artikel
                SET freigabe_status = 'entwurf', freigegeben_am = NULL, freigegeben_von = NULL
                WHERE id = %s
            ''', (artikel_id,))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Artikel nicht gefunden'}), 404
            conn.commit()
        return jsonify({'ok': True, 'freigabe_status': 'entwurf'})
    except Exception as e:
        logger.exception('admin_artikel_entwurf: %s', e)
        return jsonify({'error': str(e)}), 500


@hilfe_api.route('/admin/artikel/<int:artikel_id>', methods=['DELETE'])
@admin_required
def admin_delete_artikel(artikel_id):
    """Artikel löschen (Admin)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM hilfe_artikel WHERE id = %s', (artikel_id,))
            if cursor.rowcount == 0:
                return jsonify({'error': 'Artikel nicht gefunden'}), 404
            conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        logger.exception('admin_delete_artikel: %s', e)
        return jsonify({'error': str(e)}), 500
