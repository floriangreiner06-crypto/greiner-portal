"""
QA Routes - Feature-Prüfung & Bug-Reporting
==============================================
TAG 192: MVP für tägliche Feature-Prüfung und Fehlermeldung
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from decorators.auth_decorators import role_required

qa_routes = Blueprint('qa_routes', __name__)


# QA Dashboard Route entfernt (TAG 192) - Integration direkt in Feature-Seiten


@qa_routes.route('/qa/bugs')
@login_required
def bugs_overview():
    """Bug-Übersicht - Alle gemeldeten Bugs"""
    # Nur Admin kann alle Bugs sehen (später erweitern)
    if hasattr(current_user, 'role') and current_user.role == 'admin':
        return render_template('qa/bugs.html')
    else:
        # Normale User sehen nur ihre eigenen Bugs
        return render_template('qa/bugs.html', user_only=True)


@qa_routes.route('/qa/bugs/<int:bug_id>')
@login_required
def bug_detail(bug_id):
    """Bug-Details - Einzelansicht eines Bugs"""
    return render_template('qa/bug_detail.html', bug_id=bug_id)
