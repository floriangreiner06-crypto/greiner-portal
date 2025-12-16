"""
Admin Routes - Redirects zu Celery Task Manager
Bereinigt: TAG 120 - Alte system-status UI entfernt
"""
from flask import Blueprint, redirect, url_for
from decorators.auth_decorators import login_required, role_required

admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/admin/system-status')
@login_required
@role_required(['admin'])
def system_status():
    """Redirect zur neuen Celery Task Manager UI"""
    return redirect(url_for('celery_tasks.task_overview'))
