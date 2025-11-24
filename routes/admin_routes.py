"""
Admin Routes - System Status Dashboard
"""
from flask import Blueprint, render_template
from decorators.auth_decorators import login_required, role_required

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/system-status')
@login_required
@role_required(['admin'])
def system_status():
    return render_template('admin/system_status.html')
