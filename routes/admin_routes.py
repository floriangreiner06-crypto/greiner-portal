"""
Admin Routes - System & Rechteverwaltung
TAG 120: Alte system-status UI entfernt
TAG 134: Rechteverwaltung hinzugefügt
Konfiguration-Hub und Konten-Verwaltung: 2026-03-02
"""
from flask import Blueprint, redirect, url_for, render_template
from flask_login import current_user
from decorators.auth_decorators import login_required, role_required

admin_routes = Blueprint('admin_routes', __name__)

# Konfigurations-Hub: Unterseiten mit je eigener Berechtigung (roles ODER feature)
# Nur Einträge, die der User darf, werden angezeigt.
CONFIG_ITEMS = [
    {'group': 'Finanzen & Controlling', 'group_order': 1,
     'label': 'Konten & Banken', 'url': '/admin/konten-verwaltung', 'description': 'Bankkonten und Kreditlinien verwalten',
     'icon': 'bi-wallet2', 'feature': 'bankenspiegel'},
    {'group': 'Finanzen & Controlling', 'group_order': 1,
     'label': 'Modalitäten & Parameter', 'url': '/admin/modalitaeten', 'description': 'Kreditrahmen, Zinsfreiheit, Ziele (z. B. Linienauslastung) – selten änderbar',
     'icon': 'bi-sliders', 'roles': ['admin']},
    {'group': 'Vergütung', 'group_order': 2,
     'label': 'Provisionsarten', 'url': '/admin/provision-config', 'description': 'Provisionsregeln (SSOT Abrechnungslogik)',
     'icon': 'bi-percent', 'roles': ['admin']},
    {'group': 'Zugänge & Dienste', 'group_order': 3,
     'label': 'ServiceBox (Stellantis)', 'url': '/admin/servicebox-zugang', 'description': 'Passwort & Ablaufdatum',
     'icon': 'bi-key', 'roles': ['admin']},
    {'group': 'Organisation', 'group_order': 4,
     'label': 'Organigramm', 'url': '/admin/organigramm', 'description': 'Struktur und Vertretungen',
     'icon': 'bi-diagram-3', 'roles': ['admin']},
    {'group': 'Organisation', 'group_order': 4,
     'label': 'Startseiten', 'url': '/admin/meine-startseite', 'description': 'Individuelle Startseite konfigurieren',
     'icon': 'bi-house', 'roles': ['admin']},
    {'group': 'Organisation', 'group_order': 4,
     'label': 'Mitarbeiterverwaltung', 'url': '/admin/mitarbeiterverwaltung', 'description': 'Personalakte, Verträge, Urlaub',
     'icon': 'bi-people', 'roles': ['admin']},
    {'group': 'System', 'group_order': 5,
     'label': 'Rechteverwaltung', 'url': '/admin/rechte', 'description': 'Rollen, Features, Reports, Navigation',
     'icon': 'bi-person-lock', 'roles': ['admin']},
    {'group': 'System', 'group_order': 5,
     'label': 'Task Manager', 'url': '/admin/celery/', 'description': 'Celery-Tasks und Zeitplan',
     'icon': 'bi-list-task', 'roles': ['admin']},
]


def _can_access_config_item(user, item):
    """Prüft, ob der User die Unterseite sehen darf (roles ODER feature)."""
    if not user.is_authenticated:
        return False
    if item.get('roles'):
        if any(user.has_role(r) for r in item['roles']):
            return True
    if item.get('feature'):
        if user.can_access_feature(item['feature']):
            return True
    return False


def _grouped_config_items_for_user(user):
    """Filtert CONFIG_ITEMS nach Berechtigung und gruppiert nach group."""
    visible = [it for it in CONFIG_ITEMS if _can_access_config_item(user, it)]
    groups = {}
    for it in visible:
        g = it['group']
        if g not in groups:
            groups[g] = []
        groups[g].append(it)
    # Sortierung: nach group_order, dann nach label
    order = {g: next((x['group_order'] for x in CONFIG_ITEMS if x['group'] == g), 99) for g in groups}
    return [(g, groups[g]) for g in sorted(groups.keys(), key=lambda x: (order[x], x))]


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


@admin_routes.route('/admin/servicebox-zugang')
@login_required
@role_required(['admin'])
def servicebox_zugang():
    """ServiceBox (Stellantis) Passwort & Ablaufdatum verwalten.
    Teile-Lager/Werkstatt; Erinnerungs-E-Mails bei ablaufendem Passwort.
    """
    return render_template('admin/servicebox_zugang.html')


@admin_routes.route('/admin/provision-config')
@login_required
@role_required(['admin'])
def provision_config():
    """Provisionsarten (provision_config) verwalten – Sätze, Min/Max, J60/J61.
    SSOT für die Berechnungslogik des Provisionsmoduls.
    """
    return render_template('admin/provision_config.html')


@admin_routes.route('/admin/konfiguration')
@login_required
def konfiguration():
    """Zentrale Konfiguration & Verwaltung – Hub mit berechtigungsabhängigen Unterseiten."""
    grouped = _grouped_config_items_for_user(current_user)
    if not grouped:
        return render_template('admin/konfiguration.html', grouped=[], no_access=True)
    return render_template('admin/konfiguration.html', grouped=grouped, no_access=False)


@admin_routes.route('/admin/konten-verwaltung')
@login_required
@role_required(['admin', 'buchhaltung'])
def konten_verwaltung():
    """Konten & Banken verwalten (Kontoname, IBAN, Kreditlinie, Aktiv)."""
    return render_template('admin/konten_verwaltung.html')


@admin_routes.route('/admin/modalitaeten')
@login_required
@role_required(['admin'])
def modalitaeten_verwaltung():
    """Modalitäten & Parameter – Kreditrahmen, Zinsfreiheit, Ziele (z. B. Linienauslastung Stellantis). Änderungen quartalsweise."""
    return render_template('admin/modalitaeten_verwaltung.html')
