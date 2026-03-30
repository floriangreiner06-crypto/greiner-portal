"""
Ertragsvorschau REST-API
=========================
Erstellt: 2026-03-30 | Workstream: Controlling
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

ertragsvorschau_api = Blueprint('ertragsvorschau_api', __name__, url_prefix='/api/ertragsvorschau')


def _check_access():
    """Prüft ob User Zugriff auf Ertragsvorschau hat."""
    if not current_user.is_authenticated:
        return False
    return hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('ertragsvorschau')


@ertragsvorschau_api.route('/gesamtbild')
@login_required
def api_gesamtbild():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_gesamtbild
    gj = request.args.get('gj')
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_gesamtbild(gj, gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/guv')
@login_required
def api_guv():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_guv_daten
    gj = request.args.get('gj')
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_guv_daten(gj, gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/verkauf')
@login_required
def api_verkauf():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_verkauf_daten
    gj = request.args.get('gj')
    return jsonify(get_verkauf_daten(gj))


@ertragsvorschau_api.route('/service')
@login_required
def api_service():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_service_daten
    gj = request.args.get('gj')
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_service_daten(gj, gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/standzeiten')
@login_required
def api_standzeiten():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_standzeiten_daten
    return jsonify(get_standzeiten_daten())


@ertragsvorschau_api.route('/eigenkapital')
@login_required
def api_eigenkapital():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_eigenkapital_entwicklung
    gj = request.args.get('gj')
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_eigenkapital_entwicklung(gj, gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/mehrjahresvergleich')
@login_required
def api_mehrjahresvergleich():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_mehrjahresvergleich
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_mehrjahresvergleich(gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/prognose')
@login_required
def api_prognose():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.ertragsvorschau_data import get_prognose
    gj = request.args.get('gj')
    gesellschaft = request.args.get('gesellschaft', 'autohaus')
    return jsonify(get_prognose(gj, gesellschaft=gesellschaft))


@ertragsvorschau_api.route('/jahresabschluss/verfuegbar')
@login_required
def api_ja_verfuegbar():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import get_verfuegbare_jahresabschluesse
    return jsonify(get_verfuegbare_jahresabschluesse())


@ertragsvorschau_api.route('/jahresabschluss/import', methods=['POST'])
@login_required
def api_ja_import():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import import_jahresabschluss

    pfad = request.json.get('pfad')
    if not pfad:
        return jsonify({'error': 'Pfad fehlt'}), 400

    user = getattr(current_user, 'username', 'unknown')
    gesellschaft = request.json.get('gesellschaft', 'autohaus')
    result = import_jahresabschluss(pfad, gesellschaft=gesellschaft, importiert_von=user)

    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@ertragsvorschau_api.route('/jahresabschluss/import-alle', methods=['POST'])
@login_required
def api_ja_import_alle():
    if not _check_access():
        return jsonify({'error': 'Kein Zugriff'}), 403

    from api.jahresabschluss_import import import_alle_jahresabschluesse

    user = getattr(current_user, 'username', 'unknown')
    results = import_alle_jahresabschluesse(importiert_von=user)
    return jsonify(results)
