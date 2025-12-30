"""
Ersatzwagen-Kalender API
========================
Werkstatt-Ersatzwagen-Verwaltung mit Carloop-Sync und Locosoft SOAP.

Endpoints:
- GET /api/ersatzwagen/fahrzeuge - Liste aller Ersatzwagen
- GET /api/ersatzwagen/kalender?von=YYYY-MM-DD&bis=YYYY-MM-DD - Belegungskalender
- GET /api/ersatzwagen/verfuegbar?datum=YYYY-MM-DD - Freie Fahrzeuge an einem Tag
- POST /api/ersatzwagen/zuweisen - Ersatzwagen zu Termin zuweisen
- POST /api/ersatzwagen/sync - Carloop-Daten synchronisieren
- GET /api/ersatzwagen/carloop - Carloop-Reservierungen

Erstellt: TAG 131 (2025-12-20)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime, date, timedelta
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)

ersatzwagen_bp = Blueprint('ersatzwagen', __name__, url_prefix='/api/ersatzwagen')

# Ersatzwagen-Mapping (Carloop Kennzeichen -> Locosoft Nr)
ERSATZWAGEN = {
    'DEG-OR 33': {'loco_nr': 57960, 'modell': 'Astra'},
    'DEG-OR 44': {'loco_nr': 57953, 'modell': 'Astra'},
    'DEG-OR 50': {'loco_nr': 57169, 'modell': 'Grandland'},
    'DEG-OR 88': {'loco_nr': 57959, 'modell': 'Astra L'},
    'DEG-OR 99': {'loco_nr': 57170, 'modell': 'Grandland'},
    'DEG-OR 106': {'loco_nr': 56989, 'modell': 'Astra L'},
    'DEG-OR 110': {'loco_nr': 56969, 'modell': 'Astra L Sports Tourer'},
    'DEG-OR 113': {'loco_nr': 56029, 'modell': 'Frontera'},
    'DEG-OR 115': {'loco_nr': 56740, 'modell': 'Movano'},
    'DEG-OR 120': {'loco_nr': 57932, 'modell': 'Corsa'},
    'DEG-OR 141': {'loco_nr': 57507, 'modell': 'Mokka'},
    'DEG-OR 155': {'loco_nr': 56977, 'modell': 'Combo Life'},
    'DEG-OR 200': {'loco_nr': 57930, 'modell': 'Corsa'},
    'DEG-OR 222': {'loco_nr': 57772, 'modell': 'Mokka'},
    'DEG-OR 280': {'loco_nr': 57505, 'modell': 'Mokka'},
    'DEG-OR 333': {'loco_nr': 58067, 'modell': 'Grandland'},
    'DEG-OR 444': {'loco_nr': 57773, 'modell': 'Corsa'},
    'DEG-OR 555': {'loco_nr': 58124, 'modell': 'Corsa'},
    'DEG-OR 700': {'loco_nr': 58453, 'modell': 'Frontera'},
    'DEG-OR 796': {'loco_nr': 57948, 'modell': 'Corsa Edition'},
    'DEG-OR 800': {'loco_nr': 57945, 'modell': 'Corsa Edition'},
}

# Reverse-Mapping: Locosoft Nr -> Kennzeichen
LOCO_TO_KENNZEICHEN = {v['loco_nr']: k for k, v in ERSATZWAGEN.items()}


def get_soap_client():
    """SOAP-Client lazy laden."""
    try:
        from tools.locosoft_soap_client import get_soap_client as _get_client
        return _get_client()
    except Exception as e:
        logger.error(f"SOAP-Client nicht verfügbar: {e}")
        return None


@ersatzwagen_bp.route('/fahrzeuge', methods=['GET'])
@login_required
def get_ersatzwagen():
    """
    Liste aller Ersatzwagen.

    Returns:
        JSON mit Fahrzeugliste
    """
    fahrzeuge = []
    for kennzeichen, info in sorted(ERSATZWAGEN.items()):
        fahrzeuge.append({
            'kennzeichen': kennzeichen,
            'locosoft_nr': info['loco_nr'],
            'modell': info['modell'],
        })

    return jsonify({
        'success': True,
        'fahrzeuge': fahrzeuge,
        'anzahl': len(fahrzeuge)
    })


@ersatzwagen_bp.route('/kalender', methods=['GET'])
@login_required
def get_kalender():
    """
    Belegungskalender für Ersatzwagen.

    Query Params:
        von: Startdatum (YYYY-MM-DD), default: heute
        bis: Enddatum (YYYY-MM-DD), default: heute + 14 Tage

    Returns:
        JSON mit Belegungen pro Fahrzeug
    """
    # Parameter parsen
    heute = date.today()
    von_str = request.args.get('von', heute.isoformat())
    bis_str = request.args.get('bis', (heute + timedelta(days=14)).isoformat())

    try:
        von = datetime.fromisoformat(von_str).date() if isinstance(von_str, str) else von_str
        bis = datetime.fromisoformat(bis_str).date() if isinstance(bis_str, str) else bis_str
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Ungültiges Datum: {e}'}), 400

    # SOAP-Client
    client = get_soap_client()
    if not client:
        return jsonify({'success': False, 'error': 'SOAP-Verbindung nicht verfügbar'}), 503

    # Termine laden
    try:
        appointments = client.list_appointments_by_date(
            datetime.combine(von, datetime.min.time()),
            datetime.combine(bis, datetime.max.time())
        )
    except Exception as e:
        logger.error(f"SOAP listAppointmentsByDate fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    # Belegungen extrahieren
    belegungen = []
    for apt in appointments:
        rental_car = apt.get('rentalCar')
        if rental_car and rental_car.get('number'):
            loco_nr = rental_car.get('number')
            kennzeichen = LOCO_TO_KENNZEICHEN.get(loco_nr, f'Unbekannt #{loco_nr}')

            # Kundeninfo
            customer = apt.get('customer', {})
            vehicle = apt.get('vehicle', {})

            belegungen.append({
                'termin_nr': apt.get('number'),
                'ersatzwagen': {
                    'kennzeichen': kennzeichen,
                    'locosoft_nr': loco_nr,
                    'modell': rental_car.get('model', ''),
                },
                'kunde': {
                    'nummer': customer.get('number'),
                    'name': f"{customer.get('lastName', '')} {customer.get('firstName', '')}".strip(),
                },
                'fahrzeug': {
                    'kennzeichen': vehicle.get('licensePlate', ''),
                    'modell': vehicle.get('model', ''),
                },
                'von': apt.get('bringDateTime', ''),
                'bis': apt.get('returnDateTime', ''),
                'text': apt.get('text', ''),
            })

    # Nach Ersatzwagen gruppieren
    kalender = {}
    for kennzeichen in ERSATZWAGEN.keys():
        kalender[kennzeichen] = {
            'modell': ERSATZWAGEN[kennzeichen]['modell'],
            'belegungen': [b for b in belegungen if b['ersatzwagen']['kennzeichen'] == kennzeichen]
        }

    return jsonify({
        'success': True,
        'zeitraum': {'von': von.isoformat(), 'bis': bis.isoformat()},
        'termine_gesamt': len(appointments),
        'termine_mit_ersatzwagen': len(belegungen),
        'kalender': kalender,
        'belegungen': belegungen,
    })


@ersatzwagen_bp.route('/verfuegbar', methods=['GET'])
@login_required
def get_verfuegbar():
    """
    Verfügbare Ersatzwagen an einem bestimmten Tag.

    Query Params:
        datum: Datum (YYYY-MM-DD), default: heute

    Returns:
        JSON mit freien und belegten Fahrzeugen
    """
    datum_str = request.args.get('datum', date.today().isoformat())

    try:
        datum = datetime.fromisoformat(datum_str).date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Ungültiges Datum'}), 400

    # SOAP-Client
    client = get_soap_client()
    if not client:
        return jsonify({'success': False, 'error': 'SOAP-Verbindung nicht verfügbar'}), 503

    # Termine für diesen Tag
    try:
        appointments = client.list_appointments_by_date(
            datetime.combine(datum, datetime.min.time()),
            datetime.combine(datum + timedelta(days=1), datetime.min.time())
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # Belegte Fahrzeuge ermitteln
    belegt = {}
    for apt in appointments:
        rental_car = apt.get('rentalCar')
        if rental_car and rental_car.get('number'):
            loco_nr = rental_car.get('number')
            kennzeichen = LOCO_TO_KENNZEICHEN.get(loco_nr)
            if kennzeichen:
                customer = apt.get('customer', {})
                belegt[kennzeichen] = {
                    'kunde': f"{customer.get('lastName', '')} {customer.get('firstName', '')}".strip(),
                    'kunde_nr': customer.get('number'),
                    'termin_nr': apt.get('number'),
                    'bis': apt.get('returnDateTime', ''),
                }

    # Freie und belegte Listen erstellen
    frei = []
    belegt_liste = []

    for kennzeichen, info in sorted(ERSATZWAGEN.items()):
        fahrzeug = {
            'kennzeichen': kennzeichen,
            'modell': info['modell'],
            'locosoft_nr': info['loco_nr'],
        }
        if kennzeichen in belegt:
            fahrzeug['belegung'] = belegt[kennzeichen]
            belegt_liste.append(fahrzeug)
        else:
            frei.append(fahrzeug)

    return jsonify({
        'success': True,
        'datum': datum.isoformat(),
        'frei': frei,
        'belegt': belegt_liste,
        'statistik': {
            'gesamt': len(ERSATZWAGEN),
            'frei': len(frei),
            'belegt': len(belegt_liste),
        }
    })


@ersatzwagen_bp.route('/zuweisen', methods=['POST'])
@login_required
def zuweisen_ersatzwagen():
    """
    Ersatzwagen zu einem Termin zuweisen.

    Body (JSON):
        termin_nr: Termin-Nummer in Locosoft
        kennzeichen: Ersatzwagen-Kennzeichen (z.B. "DEG-OR 120")

    Returns:
        JSON mit Erfolg/Fehler
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'JSON-Body erforderlich'}), 400

    termin_nr = data.get('termin_nr')
    kennzeichen = data.get('kennzeichen')

    if not termin_nr:
        return jsonify({'success': False, 'error': 'termin_nr erforderlich'}), 400
    if not kennzeichen:
        return jsonify({'success': False, 'error': 'kennzeichen erforderlich'}), 400

    # Kennzeichen validieren
    if kennzeichen not in ERSATZWAGEN:
        return jsonify({'success': False, 'error': f'Unbekanntes Kennzeichen: {kennzeichen}'}), 400

    loco_nr = ERSATZWAGEN[kennzeichen]['loco_nr']

    # SOAP-Client
    client = get_soap_client()
    if not client:
        return jsonify({'success': False, 'error': 'SOAP-Verbindung nicht verfügbar'}), 503

    # Termin lesen
    try:
        termin = client.read_appointment(termin_nr)
        if not termin:
            return jsonify({'success': False, 'error': f'Termin {termin_nr} nicht gefunden'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': f'Termin lesen fehlgeschlagen: {e}'}), 500

    # Termin mit Ersatzwagen aktualisieren
    try:
        termin['rentalCar'] = {'number': loco_nr}
        result = client.write_appointment(termin)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'Ersatzwagen {kennzeichen} zu Termin {termin_nr} zugewiesen',
                'termin_nr': result.get('number'),
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Unbekannter Fehler')
            }), 500
    except Exception as e:
        logger.error(f"writeAppointment fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ersatzwagen_bp.route('/health', methods=['GET'])
def health_check():
    """Health-Check für SOAP-Verbindung."""
    client = get_soap_client()
    if not client:
        return jsonify({'healthy': False, 'error': 'SOAP-Client nicht verfügbar'}), 503

    try:
        health = client.health_check()
        return jsonify(health)
    except Exception as e:
        return jsonify({'healthy': False, 'error': str(e)}), 500


@ersatzwagen_bp.route('/sync', methods=['POST'])
@login_required
def sync_carloop():
    """
    Carloop-Reservierungen synchronisieren.
    Scrapt Carloop und speichert Reservierungen in SQLite.
    """
    try:
        from tools.carloop_scraper import get_carloop_scraper
        from models.carloop_models import upsert_reservierung, upsert_fahrzeug
    except ImportError as e:
        return jsonify({'success': False, 'error': f'Import-Fehler: {e}'}), 500

    scraper = get_carloop_scraper()

    # Fahrzeuge syncen
    try:
        fahrzeuge = scraper.get_fahrzeuge()
        for fz in fahrzeuge:
            kennzeichen = fz.get('kennzeichen', '')
            # Locosoft-Nr aus Mapping holen
            loco_nr = ERSATZWAGEN.get(kennzeichen, {}).get('loco_nr')
            upsert_fahrzeug(kennzeichen, fz.get('modell', ''), loco_nr)
    except Exception as e:
        logger.error(f"Fahrzeuge-Sync fehlgeschlagen: {e}")

    # Reservierungen syncen
    try:
        reservierungen = scraper.get_reservierungen()
        synced = 0
        for res in reservierungen:
            upsert_reservierung({
                'reservierung_id': res.reservierung_id,
                'kennzeichen': res.kennzeichen,
                'fahrzeug_modell': res.fahrzeug_modell,
                'kunde_name': res.kunde_name,
                'kunde_nr': res.kunde_nr,
                'von': res.von.isoformat() if res.von else None,
                'bis': res.bis.isoformat() if res.bis else None,
                'status': res.status,
                'tarif': res.tarif,
                'bemerkung': res.bemerkung,
                'carloop_url': res.carloop_url,
            })
            synced += 1

        return jsonify({
            'success': True,
            'message': f'{synced} Reservierungen synchronisiert',
            'fahrzeuge': len(fahrzeuge),
            'reservierungen': synced,
        })
    except Exception as e:
        logger.error(f"Reservierungen-Sync fehlgeschlagen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ersatzwagen_bp.route('/carloop', methods=['GET'])
@login_required
def get_carloop_reservierungen():
    """
    Carloop-Reservierungen aus DB holen.
    Query Params:
        von: Startdatum (YYYY-MM-DD)
        bis: Enddatum (YYYY-MM-DD)
        kennzeichen: Filter auf bestimmtes Fahrzeug
    """
    try:
        from models.carloop_models import get_reservierungen
    except ImportError as e:
        return jsonify({'success': False, 'error': f'Import-Fehler: {e}'}), 500

    von_str = request.args.get('von')
    bis_str = request.args.get('bis')
    kennzeichen = request.args.get('kennzeichen')

    von = None
    bis = None
    if von_str:
        try:
            von = datetime.fromisoformat(von_str).date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Ungültiges von-Datum'}), 400
    if bis_str:
        try:
            bis = datetime.fromisoformat(bis_str).date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Ungültiges bis-Datum'}), 400

    reservierungen = get_reservierungen(von=von, bis=bis, kennzeichen=kennzeichen)

    return jsonify({
        'success': True,
        'reservierungen': reservierungen,
        'anzahl': len(reservierungen),
    })
