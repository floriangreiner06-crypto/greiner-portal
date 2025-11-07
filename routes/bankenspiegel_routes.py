from flask import Blueprint, render_template
from datetime import datetime

bankenspiegel_bp = Blueprint('bankenspiegel', __name__, url_prefix='/bankenspiegel')

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
