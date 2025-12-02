"""
Job Scheduler API & Routes
==========================
Web-UI und API-Endpoints für Job-Management.

Erstellt: 2025-12-02
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime
import sqlite3

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/admin/jobs')

# Import wird in app.py nach Scheduler-Start gemacht
job_manager = None

def init_scheduler_routes(jm):
    """Initialisiert die Routes mit dem Job-Manager."""
    global job_manager
    job_manager = jm


@scheduler_bp.route('/')
def job_overview():
    """Übersicht aller Jobs."""
    jobs = job_manager.get_jobs() if job_manager else []
    history = job_manager.get_job_history(limit=20) if job_manager else []
    
    # Jobs nach Kategorie gruppieren
    categories = {}
    for job in jobs:
        cat = job.get('category', 'allgemein')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(job)
    
    # Statistiken
    stats = {
        'total': len(jobs),
        'active': len([j for j in jobs if j.get('is_active')]),
        'success_today': len([h for h in history if h.get('status') == 'success' 
                              and h.get('started_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))]),
        'errors_today': len([h for h in history if h.get('status') == 'error'
                             and h.get('started_at', '').startswith(datetime.now().strftime('%Y-%m-%d'))])
    }
    
    return render_template('admin/jobs.html', 
                          categories=categories, 
                          history=history,
                          stats=stats)


@scheduler_bp.route('/run/<job_id>', methods=['POST'])
def run_job(job_id):
    """Führt einen Job manuell aus."""
    if not job_manager:
        return jsonify({'success': False, 'error': 'Scheduler nicht initialisiert'}), 500
    
    user = request.args.get('user', 'web')
    success, message = job_manager.run_job_now(job_id, triggered_by=f'manual:{user}')
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': success, 'message': message})
    
    flash(f'Job "{job_id}" gestartet' if success else f'Fehler: {message}', 
          'success' if success else 'danger')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/pause/<job_id>', methods=['POST'])
def pause_job(job_id):
    """Pausiert einen Job."""
    if not job_manager:
        return jsonify({'success': False, 'error': 'Scheduler nicht initialisiert'}), 500
    
    job_manager.pause_job(job_id)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True, 'message': f'Job {job_id} pausiert'})
    
    flash(f'Job "{job_id}" pausiert', 'warning')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/resume/<job_id>', methods=['POST'])
def resume_job(job_id):
    """Reaktiviert einen Job."""
    if not job_manager:
        return jsonify({'success': False, 'error': 'Scheduler nicht initialisiert'}), 500
    
    job_manager.resume_job(job_id)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True, 'message': f'Job {job_id} reaktiviert'})
    
    flash(f'Job "{job_id}" reaktiviert', 'success')
    return redirect(url_for('scheduler.job_overview'))


@scheduler_bp.route('/history')
def job_history():
    """Zeigt die komplette Job-History."""
    job_id = request.args.get('job_id')
    limit = request.args.get('limit', 100, type=int)
    
    history = job_manager.get_job_history(job_id=job_id, limit=limit) if job_manager else []
    jobs = job_manager.get_jobs() if job_manager else []
    
    return render_template('admin/job_history.html', 
                          history=history,
                          jobs=jobs,
                          selected_job=job_id)


@scheduler_bp.route('/api/jobs')
def api_jobs():
    """API: Alle Jobs."""
    jobs = job_manager.get_jobs() if job_manager else []
    return jsonify(jobs)


@scheduler_bp.route('/api/history')
def api_history():
    """API: Job-History."""
    job_id = request.args.get('job_id')
    limit = request.args.get('limit', 50, type=int)
    history = job_manager.get_job_history(job_id=job_id, limit=limit) if job_manager else []
    return jsonify(history)


@scheduler_bp.route('/api/status')
def api_status():
    """API: Scheduler-Status."""
    if not job_manager:
        return jsonify({'running': False, 'error': 'Nicht initialisiert'})
    
    scheduler = job_manager.get_scheduler()
    return jsonify({
        'running': scheduler.running if scheduler else False,
        'job_count': len(job_manager.get_jobs()),
        'timestamp': datetime.now().isoformat()
    })
