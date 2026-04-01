"""
Provisionsmodul - HTML-Views.
Live-Preview: Daten kommen ausschliesslich aus provision_service (SSOT).
"""
import os
from flask import Blueprint, render_template, abort, send_file, request
from flask_login import login_required, current_user
from datetime import datetime

from api.db_utils import db_session

provision_bp = Blueprint('provision', __name__, url_prefix='/provision')


@provision_bp.route('/meine')
@login_required
def meine():
    """Meine Provision - Zugriff nur mit Feature provision."""
    if not (hasattr(current_user, 'can_access_feature') and current_user.can_access_feature('provision')):
        abort(403)
    now = datetime.now()
    default_monat = now.strftime('%Y-%m')
    return render_template('provision/provision_meine.html', default_monat=default_monat)


@provision_bp.route('/dashboard')
@login_required
def dashboard():
    """Provisions-Dashboard - nur Provision-Vollzugriff-User (Greiner/Groll)."""
    from api.provision_api import _has_provision_vollzugriff
    if not _has_provision_vollzugriff():
        abort(403)
    now = datetime.now()
    monat_param = request.args.get('monat', '')
    # Validierung: YYYY-MM Format
    if monat_param and len(monat_param) == 7 and monat_param[4] == '-':
        default_monat = monat_param
    else:
        default_monat = now.strftime('%Y-%m')
    return render_template('provision/provision_dashboard.html', default_monat=default_monat)


@provision_bp.route('/detail/<int:lauf_id>')
@login_required
def detail(lauf_id):
    """Detail eines Provisionslaufs (Positionen, ggf. Einspruch)."""
    return render_template('provision/provision_detail.html', lauf_id=lauf_id)


@provision_bp.route('/pdf/<int:lauf_id>')
@login_required
def pdf_download(lauf_id):
    """PDF-Download einer Provisionsabrechnung (Vorlauf oder Endlauf)."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   pdf_vorlauf, pdf_endlauf
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
    if not lauf:
        abort(404)

    # Zugriffskontrolle: nur eigener Lauf oder Vollzugriff
    vkb = lauf['verkaufer_id']
    from api.provision_api import _get_vkb_for_request, _may_see_all_verkaufer
    my_vkb = _get_vkb_for_request()
    if not _may_see_all_verkaufer() and my_vkb != vkb:
        abort(403)

    # PDF-Pfad ermitteln (Endlauf bevorzugt, sonst Vorlauf)
    pdf_rel = lauf['pdf_endlauf'] or lauf['pdf_vorlauf']
    if not pdf_rel:
        from api.provision_pdf import generate_provision_pdf
        typ = 'endlauf' if (lauf['status'] or '').upper() == 'ENDLAUF' else 'vorlauf'
        pdf_rel = generate_provision_pdf(lauf_id, typ=typ)
        if not pdf_rel:
            abort(404)

    filepath = os.path.join('/opt/greiner-test/data', pdf_rel)
    if not os.path.isfile(filepath):
        from api.provision_pdf import generate_provision_pdf
        typ = 'endlauf' if (lauf['status'] or '').upper() == 'ENDLAUF' else 'vorlauf'
        pdf_rel = generate_provision_pdf(lauf_id, typ=typ)
        if not pdf_rel:
            abort(404)
        filepath = os.path.join('/opt/greiner-test/data', pdf_rel)

    vk_name = (lauf['verkaufer_name'] or 'Verkaeufer').replace(' ', '_')
    monat = lauf['abrechnungsmonat'] or ''
    download_name = f"Provision_{vk_name}_{monat}.pdf"

    return send_file(filepath, as_attachment=True, download_name=download_name, mimetype='application/pdf')


@provision_bp.route('/pdf-preview/<int:lauf_id>')
@login_required
def pdf_preview(lauf_id):
    """HTML-Preview der Provisionsabrechnung (gleiche Daten wie PDF)."""
    from api.provision_pdf import _lauf_daten, _fmt_eur
    data = _lauf_daten(lauf_id)
    if not data:
        abort(404)
    lauf = data['lauf']

    # Zugriffskontrolle
    vkb = lauf['verkaufer_id']
    from api.provision_api import _get_vkb_for_request, _may_see_all_verkaufer
    my_vkb = _get_vkb_for_request()
    if not _may_see_all_verkaufer() and my_vkb != vkb:
        abort(403)

    # Positionen nach Kategorie gruppieren
    by_kat = {}
    for p in data['positionen']:
        by_kat.setdefault(p.get('kategorie') or '', []).append(p)

    return render_template('provision/provision_pdf_preview.html',
                           lauf=lauf, positionen=data['positionen'], by_kat=by_kat,
                           zusatzleistungen=data.get('zusatzleistungen', []),
                           jahresuebersicht=data['jahresuebersicht'],
                           fmt_eur=_fmt_eur)
