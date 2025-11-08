from flask import Blueprint, render_template
from datetime import datetime

bankenspiegel_bp = Blueprint('bankenspiegel', __name__, url_prefix='/bankenspiegel')
@bankenspiegel_bp.route('/')
def index():
    """Bankenspiegel Root - leitet zum Dashboard weiter"""
    from flask import redirect, url_for
    return redirect(url_for('bankenspiegel.dashboard'))
@bankenspiegel_bp.route('/dashboard')
def dashboard():
    """Bankenspiegel Dashboard"""
    return render_template('bankenspiegel_dashboard.html', now=datetime.now())

@bankenspiegel_bp.route('/konten')
def konten():
    """Kontenübersicht"""
    return render_template('bankenspiegel_konten.html', now=datetime.now())

@bankenspiegel_bp.route('/transaktionen')
def transaktionen():
    """Transaktionsliste"""
    return render_template('bankenspiegel_transaktionen.html', now=datetime.now())

@bankenspiegel_bp.route('/einkaufsfinanzierung')
def einkaufsfinanzierung():
    """Einkaufsfinanzierung Dashboard (Stellantis & Santander)"""
    return render_template('einkaufsfinanzierung.html', now=datetime.now())
