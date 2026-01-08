"""
Gewinnplanungstool V2 - Routes
===============================
TAG 169: Frontend-Routes für neues Gewinnplanungstool
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from api.gewinnplanung_v2_gw_data import STANDORT_NAMEN
from api.unternehmensplan_data import get_current_geschaeftsjahr

gewinnplanung_v2_routes = Blueprint(
    'gewinnplanung_v2',
    __name__,
    url_prefix='/planung/v2'
)


@gewinnplanung_v2_routes.route('/gw/<int:standort>')
@login_required
def gw_planung(standort: int):
    """
    GW-Planungsformular (KST 2) - Einzelstandort.
    
    Args:
        standort: 1, 2, oder 3
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_current_geschaeftsjahr())
    
    standort_name = STANDORT_NAMEN.get(standort, f'Standort {standort}')
    
    return render_template(
        'planung/v2/gw_planung.html',
        geschaeftsjahr=geschaeftsjahr,
        standort=standort,
        standort_name=standort_name
    )


@gewinnplanung_v2_routes.route('/gw/gesamt')
@login_required
def gw_planung_gesamt():
    """
    GW-Planungsformular (KST 2) - Gesamtbetrieb (alle Standorte nebeneinander).
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_current_geschaeftsjahr())
    
    return render_template(
        'planung/v2/gw_planung_gesamt.html',
        geschaeftsjahr=geschaeftsjahr
    )

