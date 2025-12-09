"""
Scheduler Integration für app.py
================================
Füge diesen Code in app.py ein NACH den Blueprint-Registrierungen
und VOR dem if __name__ == '__main__' Block.

Erstellt: 2025-12-02
"""

# ============================================================================
# SCHEDULER INTEGRATION - Füge in app.py ein
# ============================================================================

# 1. Import am Anfang der Datei hinzufügen:
# -----------------------------------------
# from scheduler import job_manager
# from scheduler.routes import scheduler_bp, init_scheduler_routes
# from scheduler.job_definitions import register_all_jobs

# 2. Nach den Blueprint-Registrierungen hinzufügen:
# -------------------------------------------------
"""
# Job-Scheduler Blueprint
try:
    from scheduler import job_manager
    from scheduler.routes import scheduler_bp, init_scheduler_routes
    from scheduler.job_definitions import register_all_jobs
    
    # Routes registrieren
    app.register_blueprint(scheduler_bp)
    init_scheduler_routes(job_manager)
    
    # Jobs registrieren (nur wenn nicht im Debug-Mode mit Reloader)
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        register_all_jobs()
        job_manager.start()
        print("✅ Job-Scheduler gestartet: /admin/jobs/")
    
except Exception as e:
    print(f"⚠️  Job-Scheduler nicht geladen: {e}")
    import traceback
    traceback.print_exc()
"""

# 3. App-Shutdown Handler hinzufügen:
# -----------------------------------
"""
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    try:
        from scheduler import job_manager
        if job_manager and job_manager.get_scheduler().running:
            job_manager.shutdown()
    except:
        pass
"""

# 4. Navigation in base.html erweitern (für Admin-Benutzer):
# ----------------------------------------------------------
"""
{% if current_user.is_admin %}
<li class="nav-item">
    <a class="nav-link" href="/admin/jobs/">
        <i class="bi bi-clock-history"></i> Job-Scheduler
    </a>
</li>
{% endif %}
"""
