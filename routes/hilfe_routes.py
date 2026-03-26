"""
Hilfe-Modul – HTML-Routes
Workstream: Hilfe | Erstellt: 2026-02-24
"""
from flask import Blueprint, render_template, request
from flask_login import login_required
from decorators.auth_decorators import admin_required

hilfe_bp = Blueprint('hilfe', __name__, url_prefix='/hilfe')


@hilfe_bp.route('/')
def uebersicht():
    """Hilfe-Übersicht: Kategorien mit Artikelanzahl."""
    return render_template('hilfe/hilfe_uebersicht.html')


@hilfe_bp.route('/suche')
def suche():
    """Suchergebnisse (q aus Query)."""
    q = request.args.get('q', '').strip()
    return render_template('hilfe/hilfe_suche.html', q=q)


@hilfe_bp.route('/artikel/<int:artikel_id>')
def artikel(artikel_id):
    """Einzelner Artikel."""
    return render_template('hilfe/hilfe_artikel.html', artikel_id=artikel_id)


@hilfe_bp.route('/<slug>')
def kategorie(slug):
    """Artikel-Liste einer Kategorie (slug)."""
    return render_template('hilfe/hilfe_kategorie.html', kategorie_slug=slug)


# -----------------------------------------------------------------------------
# Admin (Artikel verwalten)
# -----------------------------------------------------------------------------

@hilfe_bp.route('/admin')
@hilfe_bp.route('/admin/')
@admin_required
def admin():
    """Admin: Artikel- und Kategorienverwaltung."""
    return render_template('hilfe/hilfe_admin.html')


@hilfe_bp.route('/admin/neu')
@admin_required
def admin_neu():
    """Neuen Artikel anlegen."""
    return render_template('hilfe/hilfe_admin_artikel.html', artikel_id=None)


@hilfe_bp.route('/admin/bearbeiten/<int:artikel_id>')
@admin_required
def admin_bearbeiten(artikel_id):
    """Artikel bearbeiten."""
    return render_template('hilfe/hilfe_admin_artikel.html', artikel_id=artikel_id)
