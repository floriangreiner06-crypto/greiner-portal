"""
After Sales - Serviceberater Routes
- Serviceberater Controlling (TEK-basiert)
- Verkaufswettbewerbe
"""
from flask import Blueprint, render_template
from datetime import datetime
from decorators.auth_decorators import login_required
from flask_login import current_user

bp = Blueprint('aftersales_serviceberater', __name__, url_prefix='/aftersales/serviceberater')

@bp.route('/')
@bp.route('/controlling')
@login_required
def controlling():
    """Serviceberater Controlling Dashboard"""
    return render_template('aftersales/serviceberater.html', now=datetime.now())

@bp.route('/uebersicht')
@login_required
def sb_uebersicht():
    """
    Übersicht aller Serviceberater "Mein Bereich" Dashboards
    Für Geschäfts- und Serviceleitung (TAG 164)
    """
    # Berechtigung prüfen: admin oder controlling
    if not (current_user.can_access_feature('admin') or current_user.can_access_feature('controlling')):
        from flask import abort
        abort(403)
    
    from api.serviceberater_api import SERVICEBERATER_CONFIG
    
    # Alle Serviceberater für Übersicht
    serviceberater = []
    for ma_id, config in SERVICEBERATER_CONFIG.items():
        serviceberater.append({
            'ma_id': ma_id,
            'name': config['name'],
            'standort': config['standort'],
            'standort_name': 'Deggendorf' if config['standort'] == 'deggendorf' else 'Landau',
            'url': f'/sb/mein-bereich?ma_id={ma_id}'
        })
    
    # Nach Standort sortieren
    serviceberater.sort(key=lambda x: (x['standort'], x['name']))
    
    return render_template('aftersales/serviceberater_uebersicht.html',
                         serviceberater=serviceberater,
                         now=datetime.now())
