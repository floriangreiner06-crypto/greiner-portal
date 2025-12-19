"""
Reparaturpotenzial API - Upselling-Empfehlungen für Serviceberater
===================================================================
Rule-Based System für Reparaturempfehlungen basierend auf:
- Fahrzeug-km-Stand
- Fahrzeugalter
- Reparaturhistorie
- Saisonale Muster

Erstellt: 2025-12-18 (TAG 127)
Basierend auf Datenanalyse: 10k Fahrzeuge, 77k Arbeitspositionen
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date
from api.db_utils import db_session, locosoft_session

reparaturpotenzial_api = Blueprint('reparaturpotenzial_api', __name__, url_prefix='/api/werkstatt')


# ============================================================================
# KONSTANTEN UND FILTER
# ============================================================================

# Mindest-km für Empfehlungen (Neuwagen-Filter)
MIN_KM_FUER_EMPFEHLUNGEN = 5000

# E-Auto Marken (keine Zahnriemen, Kupplung, etc.)
E_AUTO_MARKEN = [
    'leapmotor', 'tesla', 'polestar', 'nio', 'byd', 'lucid', 'rivian',
    'xpeng', 'aiways', 'smart'  # Smart ab 2020 nur noch elektrisch
]

# Regeln die für E-Autos nicht relevant sind
E_AUTO_AUSSCHLUSS_REGELN = ['zahnriemen', 'kupplung', 'klimaanlage']


# ============================================================================
# REGEL-DEFINITIONEN (basierend auf Datenanalyse TAG 127)
# ============================================================================

REPARATUR_REGELN = {
    'batterie': {
        'name': 'Batterie-Check',
        'icon': '🔋',
        'km_schwelle': 40000,
        'km_median': 49000,
        'alter_schwelle': 4,
        'prioritaet': 1,
        'beschreibung': 'Batterie-Zustand prüfen - ø Wechsel bei 49.000 km / 5 Jahren',
        'keywords': ['batterie']
    },
    'bremsen': {
        'name': 'Bremsbeläge prüfen',
        'icon': '🛑',
        'km_schwelle': 55000,
        'km_median': 73000,
        'alter_schwelle': 4,
        'prioritaet': 2,
        'beschreibung': 'Bremsbeläge und -scheiben prüfen - ø Wechsel bei 73.000 km',
        'keywords': ['bremse', 'bremsbelag', 'bremsscheibe']
    },
    'klimaanlage': {
        'name': 'Klimaservice',
        'icon': '❄️',
        'km_schwelle': 60000,
        'km_median': 81000,
        'alter_schwelle': 5,
        'prioritaet': 3,
        'beschreibung': 'Klimaanlage warten - ø Service bei 81.000 km / 6 Jahren',
        'keywords': ['klima', 'klimaanlage', 'klimaservice'],
        'saison_monate': [4, 5, 6]  # April-Juni
    },
    'zahnriemen': {
        'name': 'Zahnriemen-Intervall',
        'icon': '⚙️',
        'km_schwelle': 80000,
        'km_median': 92000,
        'alter_schwelle': 5,
        'prioritaet': 1,
        'beschreibung': 'Zahnriemen prüfen - KRITISCH bei >80.000 km / 6 Jahren',
        'keywords': ['zahnriemen', 'steuerkette']
    },
    'kupplung': {
        'name': 'Kupplung prüfen',
        'icon': '🔧',
        'km_schwelle': 50000,
        'km_median': 62000,
        'alter_schwelle': 4,
        'prioritaet': 3,
        'beschreibung': 'Kupplungszustand prüfen - ø Wechsel bei 62.000 km',
        'keywords': ['kupplung']
    },
    'stossdaempfer': {
        'name': 'Fahrwerk/Stoßdämpfer',
        'icon': '🚗',
        'km_schwelle': 80000,
        'km_median': 98000,
        'alter_schwelle': 6,
        'prioritaet': 3,
        'beschreibung': 'Stoßdämpfer und Fahrwerk prüfen - ø bei 98.000 km',
        'keywords': ['stoßdämpfer', 'stossdaempfer', 'fahrwerk', 'feder']
    }
}

SAISONALE_EMPFEHLUNGEN = {
    'wintercheck': {
        'name': 'Wintercheck',
        'icon': '🌨️',
        'monate': [9, 10, 11],
        'beschreibung': 'Batterie, Frostschutz, Beleuchtung, Winterreifen prüfen'
    },
    'sommercheck': {
        'name': 'Klimacheck',
        'icon': '☀️',
        'monate': [4, 5, 6],
        'beschreibung': 'Klimaanlage, Pollenfilter, Kühlsystem prüfen'
    },
    'reifenwechsel': {
        'name': 'Reifenwechsel-Saison',
        'icon': '🛞',
        'monate': [3, 4, 10, 11],
        'beschreibung': 'Reifenwechsel + Profiltiefe + Einlagerung'
    }
}


def get_fahrzeug_info(kennzeichen=None, vehicle_number=None):
    """Holt Fahrzeugdaten aus Locosoft"""
    with locosoft_session() as conn:
        cursor = conn.cursor()

        if kennzeichen:
            # Suche nach Kennzeichen
            cursor.execute("""
                SELECT
                    v.internal_number,
                    v.license_plate,
                    v.production_year,
                    v.first_registration_date,
                    m.description as marke,
                    v.free_form_model_text as modell
                FROM vehicles v
                LEFT JOIN makes m ON v.make_number = m.make_number
                WHERE UPPER(REPLACE(v.license_plate, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
                LIMIT 1
            """, (kennzeichen,))
        elif vehicle_number:
            cursor.execute("""
                SELECT
                    v.internal_number,
                    v.license_plate,
                    v.production_year,
                    v.first_registration_date,
                    m.description as marke,
                    v.free_form_model_text as modell
                FROM vehicles v
                LEFT JOIN makes m ON v.make_number = m.make_number
                WHERE v.internal_number = %s
            """, (vehicle_number,))
        else:
            return None

        row = cursor.fetchone()
        if not row:
            return None

        return {
            'vehicle_number': row[0],
            'kennzeichen': row[1],
            'baujahr': row[2],
            'erstzulassung': row[3],
            'marke': row[4],
            'modell': row[5]
        }


def get_fahrzeug_historie(vehicle_number):
    """Holt Reparaturhistorie aus Locosoft"""
    with locosoft_session() as conn:
        cursor = conn.cursor()

        # Letzte Aufträge mit Arbeiten
        cursor.execute("""
            SELECT
                o.number as order_number,
                o.order_date,
                o.order_mileage,
                array_agg(DISTINCT LOWER(l.text_line)) as arbeiten
            FROM orders o
            JOIN labours l ON o.number = l.order_number
            WHERE o.vehicle_number = %s
              AND o.order_date >= NOW() - INTERVAL '3 years'
              AND l.time_units > 0
              AND l.text_line IS NOT NULL
              AND l.text_line != ''
            GROUP BY o.number, o.order_date, o.order_mileage
            ORDER BY o.order_date DESC
            LIMIT 20
        """, (vehicle_number,))

        auftraege = []
        letzter_km = 0

        for row in cursor.fetchall():
            if row[2] and row[2] > letzter_km:
                letzter_km = row[2]
            auftraege.append({
                'order_number': row[0],
                'datum': row[1].isoformat() if row[1] else None,
                'km_stand': row[2],
                'arbeiten': row[3] if row[3] else []
            })

        # Prüfe welche Reparaturen bereits durchgeführt wurden
        durchgefuehrt = {}
        for regel_id, regel in REPARATUR_REGELN.items():
            for auftrag in auftraege:
                for arbeit in auftrag['arbeiten']:
                    if arbeit and any(kw in arbeit for kw in regel['keywords']):
                        if regel_id not in durchgefuehrt:
                            durchgefuehrt[regel_id] = {
                                'datum': auftrag['datum'],
                                'km_stand': auftrag['km_stand']
                            }
                        break

        return {
            'auftraege': auftraege,
            'letzter_km': letzter_km,
            'durchgefuehrt': durchgefuehrt
        }


def ist_elektrofahrzeug(marke, kennzeichen):
    """Prüft ob es sich um ein Elektrofahrzeug handelt"""
    # Marken-Check
    if marke and marke.lower() in E_AUTO_MARKEN:
        return True

    # E-Kennzeichen Check (endet auf E, z.B. DEG-AB 123E)
    if kennzeichen:
        kz_clean = kennzeichen.replace(' ', '').replace('-', '').upper()
        if kz_clean.endswith('E') and len(kz_clean) >= 6:
            return True

    return False


def berechne_empfehlungen(fahrzeug, historie, aktueller_km=None):
    """Berechnet Reparaturempfehlungen basierend auf Regeln"""
    empfehlungen = []
    heute = date.today()
    aktueller_monat = heute.month

    # Fahrzeugalter berechnen - Fallback auf aktuelles Jahr (= 0 Jahre alt)
    if fahrzeug.get('baujahr') and fahrzeug['baujahr'] > 1990:
        alter = heute.year - fahrzeug['baujahr']
    else:
        alter = 0  # Unbekanntes Baujahr = keine Altersempfehlungen

    # km-Stand: Entweder Parameter oder letzter bekannter
    km = aktueller_km or historie.get('letzter_km', 0)

    # NEUWAGEN-FILTER: Unter 5.000 km keine Empfehlungen
    if km < MIN_KM_FUER_EMPFEHLUNGEN:
        return []

    # E-Auto Erkennung
    ist_e_auto = ist_elektrofahrzeug(
        fahrzeug.get('marke'),
        fahrzeug.get('kennzeichen')
    )

    # Regel-basierte Empfehlungen
    for regel_id, regel in REPARATUR_REGELN.items():
        # E-Auto Filter: Bestimmte Regeln überspringen
        if ist_e_auto and regel_id in E_AUTO_AUSSCHLUSS_REGELN:
            continue
        # Bereits kürzlich durchgeführt?
        if regel_id in historie.get('durchgefuehrt', {}):
            letzte = historie['durchgefuehrt'][regel_id]
            letzte_km = letzte.get('km_stand', 0) or 0

            # Innerhalb der letzten 20.000 km? → Überspringen
            if km > 0 and letzte_km > 0 and (km - letzte_km) < 20000:
                continue

        # km-basierte Prüfung
        km_relevant = km >= regel['km_schwelle']

        # Alters-basierte Prüfung
        alter_relevant = alter >= regel['alter_schwelle']

        # Saison-Prüfung (falls definiert)
        saison_relevant = True
        if 'saison_monate' in regel:
            saison_relevant = aktueller_monat in regel['saison_monate']

        # Empfehlung generieren
        if km_relevant or (alter_relevant and saison_relevant):
            dringlichkeit = 'mittel'

            # Hohe Dringlichkeit bei deutlicher Überschreitung
            if km > regel['km_median'] * 1.1:
                dringlichkeit = 'hoch'
            elif km > regel['km_median']:
                dringlichkeit = 'mittel'
            else:
                dringlichkeit = 'niedrig'

            # Zahnriemen ist immer kritisch
            if regel_id == 'zahnriemen' and km >= regel['km_schwelle']:
                dringlichkeit = 'hoch'

            empfehlungen.append({
                'id': regel_id,
                'name': regel['name'],
                'icon': regel['icon'],
                'beschreibung': regel['beschreibung'],
                'dringlichkeit': dringlichkeit,
                'prioritaet': regel['prioritaet'],
                'grund': f"km-Stand: {km:,} / Alter: {alter} Jahre".replace(',', '.'),
                'km_bis_median': max(0, regel['km_median'] - km)
            })

    # Saisonale Empfehlungen
    for saison_id, saison in SAISONALE_EMPFEHLUNGEN.items():
        if aktueller_monat in saison['monate']:
            empfehlungen.append({
                'id': saison_id,
                'name': saison['name'],
                'icon': saison['icon'],
                'beschreibung': saison['beschreibung'],
                'dringlichkeit': 'niedrig',
                'prioritaet': 4,
                'grund': 'Saisonale Empfehlung',
                'ist_saisonal': True
            })

    # Sortieren nach Dringlichkeit und Priorität
    dringlichkeit_order = {'hoch': 0, 'mittel': 1, 'niedrig': 2}
    empfehlungen.sort(key=lambda x: (dringlichkeit_order.get(x['dringlichkeit'], 2), x['prioritaet']))

    return empfehlungen


# ============================================================================
# API ENDPOINTS
# ============================================================================

@reparaturpotenzial_api.route('/reparaturpotenzial', methods=['GET'])
def get_reparaturpotenzial():
    """
    GET /api/werkstatt/reparaturpotenzial?kennzeichen=DEG-XX123&km=85000

    Gibt Reparaturempfehlungen für ein Fahrzeug zurück.
    """
    try:
        kennzeichen = request.args.get('kennzeichen', '').strip()
        vehicle_number = request.args.get('vehicle_number')
        aktueller_km = request.args.get('km', type=int)

        if not kennzeichen and not vehicle_number:
            return jsonify({
                'success': False,
                'error': 'Kennzeichen oder vehicle_number erforderlich'
            }), 400

        # Fahrzeug suchen
        fahrzeug = get_fahrzeug_info(kennzeichen=kennzeichen, vehicle_number=vehicle_number)

        if not fahrzeug:
            return jsonify({
                'success': False,
                'error': f'Fahrzeug nicht gefunden: {kennzeichen or vehicle_number}'
            }), 404

        # Historie laden
        historie = get_fahrzeug_historie(fahrzeug['vehicle_number'])

        # Empfehlungen berechnen
        empfehlungen = berechne_empfehlungen(fahrzeug, historie, aktueller_km)

        return jsonify({
            'success': True,
            'fahrzeug': {
                'kennzeichen': fahrzeug['kennzeichen'],
                'marke': fahrzeug['marke'],
                'modell': fahrzeug['modell'],
                'baujahr': fahrzeug['baujahr'],
                'letzter_km': historie.get('letzter_km', 0),
                'aktueller_km': aktueller_km or historie.get('letzter_km', 0)
            },
            'empfehlungen': empfehlungen,
            'historie': {
                'anzahl_auftraege': len(historie.get('auftraege', [])),
                'durchgefuehrt': historie.get('durchgefuehrt', {})
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reparaturpotenzial_api.route('/reparaturpotenzial/regeln', methods=['GET'])
def get_regeln():
    """GET /api/werkstatt/reparaturpotenzial/regeln - Alle Regeln anzeigen"""
    return jsonify({
        'success': True,
        'regeln': REPARATUR_REGELN,
        'saisonal': SAISONALE_EMPFEHLUNGEN
    })
