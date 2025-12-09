"""
After Sales - Serviceberater Routes
- Serviceberater Controlling (TEK-basiert)
- Verkaufswettbewerbe
"""
from flask import Blueprint, render_template
from datetime import datetime
from decorators.auth_decorators import login_required

bp = Blueprint('aftersales_serviceberater', __name__, url_prefix='/aftersales/serviceberater')

@bp.route('/')
@bp.route('/controlling')
@login_required
def controlling():
    """Serviceberater Controlling Dashboard"""
    return render_template('aftersales/serviceberater.html', now=datetime.now())
