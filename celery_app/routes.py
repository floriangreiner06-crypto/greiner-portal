"""
Celery Task Management Routes
==============================
UI zum manuellen Starten von Tasks und Verwalten von Schedules.
Mit RedBeat für dynamische, editierbare Zeitpläne.

Erstellt: 2025-12-09 (TAG 110)
"""

from flask import Blueprint, render_template, jsonify, request
from celery.result import AsyncResult
from celery.schedules import crontab
import json

celery_bp = Blueprint('celery_tasks', __name__, url_prefix='/admin/celery')


# =============================================================================
# HELPER: Cron zu lesbare Beschreibung
# =============================================================================

WEEKDAY_NAMES = {
    'mon': 'Mo', 'tue': 'Di', 'wed': 'Mi', 'thu': 'Do', 
    'fri': 'Fr', 'sat': 'Sa', 'sun': 'So',
    'mon-fri': 'Mo-Fr', 'mon-sat': 'Mo-Sa', '*': 'Täglich'
}

def cron_to_readable(schedule):
    """Wandelt Crontab in lesbare Beschreibung um."""
    if not hasattr(schedule, '_orig_minute'):
        return str(schedule)
    
    minute = schedule._orig_minute
    hour = schedule._orig_hour
    dow = str(schedule._orig_day_of_week)
    
    # Wochentag
    dow_text = WEEKDAY_NAMES.get(dow, dow)
    
    # Zeit formatieren
    if minute == '*':
        if '/' in str(hour):
            interval = str(hour).split('/')[1]
            return f"Alle {interval}h ({dow_text})"
        time_text = "Jede Stunde"
    elif '*/' in str(minute):
        interval = str(minute).split('/')[1]
        if hour == '*':
            return f"Alle {interval} Min"
        else:
            return f"Alle {interval} Min ({hour}:00-{hour}:59, {dow_text})"
    else:
        # Feste Minute
        if '-' in str(hour):
            h_start, h_end = str(hour).split('-')
            time_text = f"{h_start}:{str(minute).zfill(2)}-{h_end}:{str(minute).zfill(2)}"
        elif '*' in str(hour):
            time_text = f"Jede Stunde um :{str(minute).zfill(2)}"
        else:
            time_text = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
    
    return f"{time_text} Uhr ({dow_text})"


def parse_cron_input(cron_str):
    """Parst einen einfachen Cron-String in ein crontab-Objekt."""
    parts = cron_str.strip().split()
    if len(parts) < 2:
        raise ValueError("Ungültiges Format. Erwartet: 'Minute Stunde [Wochentag]'")
    
    minute = parts[0]
    hour = parts[1]
    dow = parts[2] if len(parts) > 2 else '*'
    
    return crontab(minute=minute, hour=hour, day_of_week=dow)


# =============================================================================
# HELPER: Schedule-Infos aus RedBeat oder Config
# =============================================================================

def get_all_schedules():
    """Holt alle Schedules aus RedBeat (Redis DB 2)."""
    from celery_app import app
    import redis
    
    schedules = []
    
    # RedBeat verwendet Redis DB 2
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=2)
        keys = redis_client.keys('greiner:*')
        
        # Filter: Nur echte Schedule-Keys (nicht ::schedule, ::lock, ::statics)
        schedule_keys = [k for k in keys if not k.decode().startswith('greiner::')]
        
        for key in schedule_keys:
            try:
                from redbeat import RedBeatSchedulerEntry
                entry = RedBeatSchedulerEntry.from_key(key.decode(), app=app)
                schedule = entry.schedule
                
                schedules.append({
                    'key': key.decode(),
                    'name': entry.name,
                    'task': entry.task.split('.')[-1],
                    'task_full': entry.task,
                    'schedule_obj': schedule,
                    'schedule_readable': cron_to_readable(schedule),
                    'schedule_cron': get_cron_string(schedule),
                    'enabled': True,
                    'source': 'redbeat'
                })
            except Exception as e:
                continue
                
    except Exception as e:
        pass
    
    # Wenn keine RedBeat-Entries, lade aus Config (Fallback)
    if not schedules:
        for name, config in app.conf.beat_schedule.items():
            schedule = config.get('schedule')
            task_name = config.get('task', '')
            
            schedules.append({
                'key': f'config:{name}',
                'name': name,
                'task': task_name.split('.')[-1],
                'task_full': task_name,
                'schedule_obj': schedule,
                'schedule_readable': cron_to_readable(schedule),
                'schedule_cron': get_cron_string(schedule),
                'enabled': True,
                'source': 'config',
                'queue': config.get('options', {}).get('queue', 'celery')
            })
    
    return sorted(schedules, key=lambda x: x['name'])


def get_cron_string(schedule):
    """Extrahiert Cron-String aus Schedule-Objekt."""
    if hasattr(schedule, '_orig_minute'):
        return f"{schedule._orig_minute} {schedule._orig_hour} * * {schedule._orig_day_of_week}"
    return str(schedule)


def save_schedule(name, task_full, cron_str, enabled=True):
    """Speichert/Aktualisiert einen Schedule in RedBeat."""
    from celery_app import app
    from redbeat import RedBeatSchedulerEntry
    
    schedule = parse_cron_input(cron_str)
    
    entry = RedBeatSchedulerEntry(
        name=name,
        task=task_full,
        schedule=schedule,
        app=app
    )
    entry.save()
    return entry


def delete_schedule(name):
    """Löscht einen Schedule aus RedBeat."""
    from celery_app import app
    from redbeat import RedBeatSchedulerEntry
    
    try:
        entry = RedBeatSchedulerEntry.from_key(f'greiner:{name}', app=app)
        entry.delete()
        return True
    except Exception as e:
        return False


# =============================================================================
# TASK-KATEGORIEN
# =============================================================================

TASK_CATEGORIES = {
    'controlling': {
        'name': 'Controlling & Verwaltung',
        'icon': '💰',
        'tasks': [
            ('import_mt940', 'MT940 Import', 'Bank-Kontoauszüge importieren'),
            ('import_hvb_pdf', 'HypoVereinsbank PDF', 'HVB PDF-Auszüge importieren'),
            ('import_santander', 'Santander Import', 'Santander Bestand importieren'),
            ('import_hyundai', 'Hyundai Import', 'Hyundai Finance CSV importieren'),
            ('scrape_hyundai', 'Hyundai Scraper', 'Hyundai Portal scrapen'),
            ('leasys_cache_refresh', 'Leasys Cache', 'Leasys Cache aktualisieren'),
            ('umsatz_bereinigung', 'Umsatz-Bereinigung', 'Umsatzdaten bereinigen'),
            ('bwa_berechnung', 'BWA Berechnung', 'BWA aus Locosoft berechnen'),
            ('sync_employees', 'Mitarbeiter Sync', 'Mitarbeiter synchronisieren'),
            ('sync_locosoft_employees', 'Locosoft Employees', 'Locosoft Employee Mapping'),
            ('sync_ad_departments', 'AD Abteilungen Sync', 'Abteilungen aus Active Directory'),
            ('email_auftragseingang', 'E-Mail Auftragseingang', 'Täglichen Report senden'),
            ('db_backup', 'DB Backup', 'Datenbank-Backup erstellen'),
            ('cleanup_backups', 'Backup Cleanup', 'Alte Backups löschen'),
        ]
    },
    'aftersales': {
        'name': 'Aftersales & Werkstatt',
        'icon': '🔧',
        'tasks': [
            ('servicebox_scraper', 'ServiceBox Scraper', 'ServiceBox Bestellungen scrapen'),
            ('servicebox_matcher', 'ServiceBox Matcher', 'Mit Locosoft matchen'),
            ('servicebox_import', 'ServiceBox Import', 'In DB importieren'),
            ('servicebox_master', 'ServiceBox Master', 'Komplett neu laden (langsam!)'),
            ('sync_teile', 'Teile Sync', 'Teile synchronisieren'),
            ('import_teile', 'Teile Import', 'Teile-Lieferscheine importieren'),
            ('werkstatt_leistung', 'Werkstatt Leistung', 'Leistungsgrade berechnen'),
            ('email_werkstatt_tagesbericht', 'Werkstatt E-Mail', 'Tagesbericht senden'),
            ('sync_charge_types', 'Charge Types Sync', 'AW-Preise synchronisieren'),
            ('ml_retrain', 'ML Training', 'Modell neu trainieren'),
        ]
    },
    'verkauf': {
        'name': 'Verkauf',
        'icon': '🚗',
        'tasks': [
            ('sync_sales', 'Verkauf Sync', 'Verkaufsdaten synchronisieren'),
            ('import_stellantis', 'Stellantis Import', 'Stellantis Fahrzeuge importieren'),
            ('sync_stammdaten', 'Stammdaten Sync', 'Fahrzeug-Stammdaten sync'),
            ('locosoft_mirror', 'Locosoft Mirror', 'Locosoft komplett spiegeln'),
        ]
    }
}

# Alle Tasks als Flat-Map für schnellen Zugriff
ALL_TASKS = {}
for cat_id, cat in TASK_CATEGORIES.items():
    for task_id, task_name, task_desc in cat['tasks']:
        ALL_TASKS[task_id] = {
            'name': task_name,
            'desc': task_desc,
            'category': cat_id,
            'full_name': f'celery_app.tasks.{task_id}'
        }


# =============================================================================
# ROUTES
# =============================================================================

@celery_bp.route('/')
def task_overview():
    """Task-Übersicht mit Start-Buttons und Schedules."""
    schedules = get_all_schedules()
    return render_template(
        'admin/celery_tasks.html', 
        categories=TASK_CATEGORIES, 
        schedules=schedules,
        all_tasks=ALL_TASKS
    )


@celery_bp.route('/start/<task_name>', methods=['POST'])
def start_task(task_name):
    """Task manuell starten."""
    from celery_app.tasks import (
        import_mt940, import_hvb_pdf, import_santander, import_hyundai,
        scrape_hyundai, leasys_cache_refresh, umsatz_bereinigung, bwa_berechnung,
        sync_employees, sync_locosoft_employees, email_auftragseingang,
        db_backup, cleanup_backups, servicebox_scraper, servicebox_matcher,
        servicebox_import, servicebox_master, sync_teile, import_teile,
        werkstatt_leistung, email_werkstatt_tagesbericht, sync_charge_types,
        ml_retrain, sync_sales, import_stellantis, sync_stammdaten, locosoft_mirror, sync_ad_departments,
        update_penner_marktpreise, email_penner_weekly, sync_eautoseller_data,
        benachrichtige_serviceberater_ueberschreitungen
    )
    
    task_map = {
        'import_mt940': import_mt940,
        'import_hvb_pdf': import_hvb_pdf,
        'import_santander': import_santander,
        'import_hyundai': import_hyundai,
        'scrape_hyundai': scrape_hyundai,
        'leasys_cache_refresh': leasys_cache_refresh,
        'umsatz_bereinigung': umsatz_bereinigung,
        'bwa_berechnung': bwa_berechnung,
        'sync_employees': sync_employees,
        'sync_locosoft_employees': sync_locosoft_employees,
        'email_auftragseingang': email_auftragseingang,
        'db_backup': db_backup,
        'cleanup_backups': cleanup_backups,
        'servicebox_scraper': servicebox_scraper,
        'servicebox_matcher': servicebox_matcher,
        'servicebox_import': servicebox_import,
        'servicebox_master': servicebox_master,
        'sync_teile': sync_teile,
        'import_teile': import_teile,
        'werkstatt_leistung': werkstatt_leistung,
        'email_werkstatt_tagesbericht': email_werkstatt_tagesbericht,
        'sync_charge_types': sync_charge_types,
        'ml_retrain': ml_retrain,
        'sync_sales': sync_sales,
        'import_stellantis': import_stellantis,
        'sync_stammdaten': sync_stammdaten,
        'locosoft_mirror': locosoft_mirror,
        'sync_ad_departments': sync_ad_departments,
        'update_penner_marktpreise': update_penner_marktpreise,
        'email_penner_weekly': email_penner_weekly,
        'sync_eautoseller_data': sync_eautoseller_data,
        'benachrichtige_serviceberater_ueberschreitungen': benachrichtige_serviceberater_ueberschreitungen,
    }
    
    if task_name not in task_map:
        return jsonify({'error': f'Task {task_name} nicht gefunden'}), 404
    
    result = task_map[task_name].delay()
    
    # Speichere Task-ID -> Task-Name Mapping in Redis für Historie
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=1)
        mapping_key = f'task-name-mapping:{result.id}'
        full_task_name = f'celery_app.tasks.{task_name}'
        redis_client.setex(mapping_key, 86400 * 7, full_task_name)  # 7 Tage TTL
    except:
        pass  # Nicht kritisch, nur für Historie
    
    return jsonify({
        'status': 'started',
        'task_id': result.id,
        'task_name': task_name
    })


@celery_bp.route('/status/<task_id>')
def task_status(task_id):
    """Task-Status abfragen."""
    result = AsyncResult(task_id)
    
    response = {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response['result'] = result.result
        else:
            response['error'] = str(result.result)
    
    return jsonify(response)


@celery_bp.route('/schedule/save', methods=['POST'])
def save_schedule_route():
    """Schedule speichern/aktualisieren."""
    data = request.json
    
    name = data.get('name')
    task_full = data.get('task_full')
    cron_str = data.get('cron')
    
    if not all([name, task_full, cron_str]):
        return jsonify({'error': 'Name, Task und Cron erforderlich'}), 400
    
    try:
        entry = save_schedule(name, task_full, cron_str)
        return jsonify({
            'status': 'success',
            'message': f'Schedule "{name}" gespeichert'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@celery_bp.route('/schedule/delete/<name>', methods=['DELETE'])
def delete_schedule_route(name):
    """Schedule löschen."""
    if delete_schedule(name):
        return jsonify({'status': 'success', 'message': f'Schedule "{name}" gelöscht'})
    else:
        return jsonify({'error': 'Schedule nicht gefunden'}), 404


@celery_bp.route('/schedule/init', methods=['POST'])
def init_schedules():
    """Initialisiert RedBeat mit den Standard-Schedules aus der Config."""
    from celery_app import app
    
    count = 0
    for name, config in app.conf.beat_schedule.items():
        schedule = config.get('schedule')
        task = config.get('task')
        
        try:
            cron_str = get_cron_string(schedule)
            save_schedule(name, task, cron_str)
            count += 1
        except Exception as e:
            continue
    
    return jsonify({
        'status': 'success',
        'message': f'{count} Schedules initialisiert'
    })


@celery_bp.route('/api/tasks')
def api_tasks():
    """API: Alle Tasks als JSON."""
    return jsonify(ALL_TASKS)


@celery_bp.route('/api/schedules')
def api_schedules():
    """API: Alle Schedules als JSON."""
    schedules = get_all_schedules()
    # Schedule-Objekte entfernen (nicht JSON-serialisierbar)
    for s in schedules:
        s.pop('schedule_obj', None)
    return jsonify(schedules)


@celery_bp.route('/api/task-history/<task_name>')
def task_history(task_name):
    """Holt die letzten Task-Läufe für einen Task-Namen."""
    import redis
    from datetime import datetime
    import json as json_lib
    from celery_app import app
    
    try:
        # Task-Namen zu vollständigem Celery-Task-Namen mappen
        task_map = {
            'import_mt940': 'celery_app.tasks.import_mt940',
            'import_hvb_pdf': 'celery_app.tasks.import_hvb_pdf',
            'import_santander': 'celery_app.tasks.import_santander',
            'import_hyundai': 'celery_app.tasks.import_hyundai',
            'scrape_hyundai': 'celery_app.tasks.scrape_hyundai',
            'leasys_cache_refresh': 'celery_app.tasks.leasys_cache_refresh',
            'umsatz_bereinigung': 'celery_app.tasks.umsatz_bereinigung',
            'bwa_berechnung': 'celery_app.tasks.bwa_berechnung',
            'sync_employees': 'celery_app.tasks.sync_employees',
            'sync_locosoft_employees': 'celery_app.tasks.sync_locosoft_employees',
            'email_auftragseingang': 'celery_app.tasks.email_auftragseingang',
            'db_backup': 'celery_app.tasks.db_backup',
            'cleanup_backups': 'celery_app.tasks.cleanup_backups',
            'servicebox_scraper': 'celery_app.tasks.servicebox_scraper',
            'servicebox_matcher': 'celery_app.tasks.servicebox_matcher',
            'servicebox_import': 'celery_app.tasks.servicebox_import',
            'servicebox_master': 'celery_app.tasks.servicebox_master',
            'sync_teile': 'celery_app.tasks.sync_teile',
            'import_teile': 'celery_app.tasks.import_teile',
            'werkstatt_leistung': 'celery_app.tasks.werkstatt_leistung',
            'email_werkstatt_tagesbericht': 'celery_app.tasks.email_werkstatt_tagesbericht',
            'sync_charge_types': 'celery_app.tasks.sync_charge_types',
            'ml_retrain': 'celery_app.tasks.ml_retrain',
            'sync_sales': 'celery_app.tasks.sync_sales',
            'import_stellantis': 'celery_app.tasks.import_stellantis',
            'sync_stammdaten': 'celery_app.tasks.sync_stammdaten',
            'locosoft_mirror': 'celery_app.tasks.locosoft_mirror',
            'sync_ad_departments': 'celery_app.tasks.sync_ad_departments',
            'update_penner_marktpreise': 'celery_app.tasks.update_penner_marktpreise',
            'email_penner_weekly': 'celery_app.tasks.email_penner_weekly',
            'sync_eautoseller_data': 'celery_app.tasks.sync_eautoseller_data',
            'benachrichtige_serviceberater_ueberschreitungen': 'celery_app.tasks.benachrichtige_serviceberater_ueberschreitungen',
        }
        
        full_task_name = task_map.get(task_name)
        if not full_task_name:
            return jsonify({'error': 'Task nicht gefunden'}), 404
        
        # Redis Client für Result Backend (DB 1)
        redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=False)
        
        # Suche nach allen Task-Metadaten-Keys
        pattern = 'celery-task-meta-*'
        keys = redis_client.keys(pattern)
        
        if not keys:
            return jsonify({
                'task_name': task_name,
                'last_run': None,
                'history': []
            })
        
        # Durchsuche die letzten Keys (für Performance)
        history = []
        checked = 0
        max_checks = min(500, len(keys))  # Maximal 500 Keys prüfen
        
        # Sortiere Keys nach Timestamp (neueste zuerst)
        for key in reversed(keys):
            if checked >= max_checks:
                break
            checked += 1
            
            try:
                # Extrahiere Task-ID aus Key
                task_id = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                task_id = task_id.replace('celery-task-meta-', '')
                
                # Hole Task-Name aus Redis-Mapping (wenn vorhanden)
                mapping_key = f'task-name-mapping:{task_id}'
                stored_task_name = redis_client.get(mapping_key)
                
                if stored_task_name:
                    # Decode bytes to string
                    if isinstance(stored_task_name, bytes):
                        stored_task_name = stored_task_name.decode('utf-8')
                    if stored_task_name != full_task_name:
                        continue
                else:
                    # Fallback: Versuche über AsyncResult (funktioniert oft nicht)
                    try:
                        from celery.result import AsyncResult
                        result = AsyncResult(task_id, app=app)
                        result_name = result.name
                        if not result_name or result_name != full_task_name:
                            continue
                    except:
                        # Wenn kein Mapping und AsyncResult fehlschlägt, überspringe
                        continue
                
                # Hole Metadaten für Status und Dauer
                meta_data = redis_client.get(key)
                if not meta_data:
                    continue
                
                try:
                    if isinstance(meta_data, bytes):
                        meta_data = meta_data.decode('utf-8')
                    data = json_lib.loads(meta_data)
                except (json_lib.JSONDecodeError, UnicodeDecodeError):
                    continue
                
                # Berechne Dauer
                date_done = data.get('date_done')
                started = None
                
                # Versuche started aus result.info zu holen
                try:
                    if hasattr(result, 'info') and result.info:
                        if isinstance(result.info, dict):
                            started = result.info.get('started')
                except:
                    pass
                
                duration = None
                if date_done and started:
                    try:
                        date_done_str = date_done.replace('Z', '+00:00') if 'Z' in date_done else date_done
                        started_str = started.replace('Z', '+00:00') if 'Z' in started else started
                        date_done_ts = datetime.fromisoformat(date_done_str)
                        started_ts = datetime.fromisoformat(started_str)
                        duration = (date_done_ts - started_ts).total_seconds()
                    except (ValueError, AttributeError, TypeError):
                        pass
                
                history.append({
                    'task_id': task_id,
                    'status': data.get('status', 'UNKNOWN'),
                    'date_done': date_done,
                    'started': started,
                    'duration': duration,
                    'success': data.get('status') == 'SUCCESS'
                })
                
                # Nur die letzten 5 Einträge
                if len(history) >= 5:
                    break
            except Exception as e:
                continue
        
        # Sortiere nach Datum (neueste zuerst)
        history.sort(key=lambda x: x.get('date_done') or '', reverse=True)
        
        # Hole den letzten Eintrag
        last_run = history[0] if history else None
        
        return jsonify({
            'task_name': task_name,
            'last_run': last_run,
            'history': history[:5]  # Maximal 5 Einträge
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
