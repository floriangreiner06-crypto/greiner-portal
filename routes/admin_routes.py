"""
Admin Routes - System & Rechteverwaltung
TAG 120: Alte system-status UI entfernt
TAG 134: Rechteverwaltung hinzugefügt
"""
from flask import Blueprint, redirect, url_for, render_template
from decorators.auth_decorators import login_required, role_required

admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/admin/system-status')
@login_required
@role_required(['admin'])
def system_status():
    """Redirect zur neuen Celery Task Manager UI"""
    return redirect(url_for('celery_tasks.task_overview'))


@admin_routes.route('/admin/rechte')
@login_required
@role_required(['admin'])
def rechte_verwaltung():
    """Rechteverwaltung - User-Rollen und Feature-Zugriff"""
    return render_template('admin/rechte_verwaltung.html')


@admin_routes.route('/admin/meine-startseite')
@admin_routes.route('/settings/dashboard')
@login_required
@role_required(['admin'])
def user_dashboard_config():
    """Individuelle Startseite konfigurieren (nur für Admin)
    TAG 190: Nur Admin kann Startseiten konfigurieren
    """
    return render_template('admin/user_dashboard_config.html')
