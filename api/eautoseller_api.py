"""
eAutoseller API
Integration mit eAutoseller für Live-Bestand und KPIs
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
import json
import logging

# eAutoseller Client
from lib.eautoseller_client import EAutosellerClient
from api.db_utils import db_session

logger = logging.getLogger(__name__)

# Blueprint erstellen
eautoseller_api = Blueprint('eautoseller_api', __name__, url_prefix='/api/eautoseller')

# ============================================================================
# CACHE (In-Memory, TTL)
# vehicles_raw: 15 Min, vehicle_detail: 30 Min, publications: 60 Min, filter_options: 15 Min
# ============================================================================
_EAUTOSELLER_CACHE = {}
TTL_VEHICLES_RAW = 15 * 60
TTL_VEHICLE_DETAIL = 30 * 60
TTL_PUBLICATIONS = 60 * 60
TTL_FILTER_OPTIONS = 15 * 60


def _cache_get(key, ttl_seconds):
    """Liefert (value, True) wenn gültig, sonst (None, False)."""
    entry = _EAUTOSELLER_CACHE.get(key)
    if not entry:
        return None, False
    ts, value = entry
    if (datetime.now() - ts).total_seconds() > ttl_seconds:
        del _EAUTOSELLER_CACHE[key]
        return None, False
    return value, True


def _cache_set(key, value, ttl_seconds):
    """Speichert value mit aktuellem Timestamp."""
    _EAUTOSELLER_CACHE[key] = (datetime.now(), value)


def _get_bwa_placements_from_db(vins):
    """
    Liest gecachte mobile.de Börsenplatzierung (BWA) aus eautoseller_bwa_placement.
    Tabelle wird vom Celery-Task sync_eautoseller_data befüllt.
    Returns: dict vin -> { mobile_platz, total_hits, platz_1_retail_gross, mobile_url, error }
    """
    if not vins:
        return {}
    vins_clean = [v.strip() for v in vins if v and len(str(v).strip()) == 17][:100]
    if not vins_clean:
        return {}
    result = {}
    try:
        with db_session() as conn:
            cur = conn.cursor()
            placeholders = ','.join(['%s'] * len(vins_clean))
            cur.execute(
                """SELECT vin, mobile_platz, total_hits, platz_1_retail_gross, mobile_url, error_message
                   FROM eautoseller_bwa_placement WHERE vin IN (""" + placeholders + """)""",
                vins_clean
            )
            rows = cur.fetchall()
            colnames = [c[0] for c in (cur.description or [])]
            for r in rows:
                row = dict(zip(colnames, r)) if colnames else {}
                vin = (row.get('vin') or '').strip()
                if not vin:
                    continue
                result[vin] = {
                    'mobile_platz': row.get('mobile_platz'),
                    'total_hits': row.get('total_hits'),
                    'platz_1_retail_gross': float(row['platz_1_retail_gross']) if row.get('platz_1_retail_gross') is not None else None,
                    'mobile_url': row.get('mobile_url'),
                    'error': row.get('error_message'),
                }
                result[vin.upper()] = result[vin]
    except Exception as e:
        logger.warning("eAutoseller BWA aus DB: %s", e)
    return result


# ============================================================================
# CONFIGURATION
# ============================================================================

def get_eautoseller_credentials():
    """Lädt eAutoseller Credentials (absoluter Pfad, damit unter Gunicorn gefunden)."""
    creds_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json'))
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                if 'eautoseller' in creds:
                    return creds['eautoseller']
        except Exception:
            pass
    
    # Fallback: Environment Variables
    return {
        'username': os.getenv('EAUTOSELLER_USERNAME', 'fGreiner'),
        'password': os.getenv('EAUTOSELLER_PASSWORD', 'fGreiner12'),
        'loginbereich': os.getenv('EAUTOSELLER_LOGINBEREICH', 'kfz')
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_client():
    """Erstellt eAutoseller Client"""
    creds = get_eautoseller_credentials()
    client = EAutosellerClient(
        username=creds.get('username', 'fGreiner'),
        password=creds.get('password', 'fGreiner12'),
        loginbereich=creds.get('loginbereich', 'kfz')
    )
    return client

def get_swagger_client():
    """Erstellt eAutoseller Client für Swagger API"""
    creds = get_eautoseller_credentials()
    client = EAutosellerClient(
        username=creds.get('username', 'fGreiner'),
        password=creds.get('password', 'fGreiner12'),
        loginbereich=creds.get('loginbereich', 'kfz')
    )
    return client


def calculate_standzeit(hereinnahme_str):
    """Berechnet Standzeit in Tagen"""
    if not hereinnahme_str:
        return None
    
    try:
        if isinstance(hereinnahme_str, str):
            hereinnahme = datetime.strptime(hereinnahme_str, '%Y-%m-%d').date()
        else:
            hereinnahme = hereinnahme_str
        
        today = datetime.now().date()
        standzeit = (today - hereinnahme).days
        return standzeit
    except:
        return None


def get_standzeit_status(standzeit_tage):
    """
    Standzeit-Status laut OpenAPI-Dokumentation:
    < 30 Tage → ok (Neu im Bestand)
    30–60 Tage → warning (X Tage im Bestand)
    > 60 Tage → critical (Jetzt anfragen!)
    """
    if standzeit_tage is None:
        return 'unknown'
    if standzeit_tage < 30:
        return 'ok'
    if standzeit_tage < 60:
        return 'warning'
    return 'critical'


def get_standzeit_badge(standzeit_tage, status):
    """Badge-Text für Standzeit."""
    if standzeit_tage is None:
        return 'Unbekannt'
    if status == 'ok':
        return 'Neu im Bestand'
    if status == 'warning':
        return f'{standzeit_tage} Tage im Bestand'
    return f'{standzeit_tage} Tage – Jetzt anfragen!'


def format_vehicle_response(v, publications_by_vin=None, publications_by_id=None, bwa_placements_by_vin=None):
    """
    Formatiert ein Fahrzeug für das API-Response-Format (Plugin-kompatibel).
    Fügt preis_formatiert, km_formatiert, ez_formatiert, standzeit_badge,
    preis_bewertung / preis_bewertung_text, mobile_link, as24_link,
    mobile_platz, total_hits (mobile.de Börsenplatzierung aus BWA) hinzu.
    """
    standzeit = v.get('standzeit_tage')
    status = v.get('standzeit_status') or get_standzeit_status(standzeit)
    badge = get_standzeit_badge(standzeit, status)
    preis = v.get('preis')
    km = v.get('km')
    ez = v.get('ez') or (f"{v.get('ez_jahr')}-01" if v.get('ez_jahr') else None)
    ez_jahr = v.get('ez_jahr')
    if ez and not ez_jahr and len(ez) >= 4:
        try:
            ez_jahr = int(ez[:4])
        except (TypeError, ValueError):
            ez_jahr = None
    out = {
        'id': v.get('id'),
        'vin': v.get('vin'),
        'offerReference': v.get('offer_reference'),
        'marke': v.get('marke') or '',
        'modell': v.get('modell') or '',
        'typ': v.get('typ') or '',
        'kategorie': v.get('kategorie') or '',
        'preis': round(preis, 2) if preis is not None else None,
        'preis_formatiert': f'{preis:,.0f} €'.replace(',', '.') if preis is not None else '-',
        'haendlerpreis': v.get('haendlerpreis'),
        'km': km,
        'km_formatiert': f'{km:,} km'.replace(',', '.') if km is not None else '-',
        'ez': ez,
        'ez_formatiert': f'{ez[5:7]}/{ez[:4]}' if ez and len(ez) >= 7 else (str(ez) if ez else '-'),
        'ez_jahr': ez_jahr,
        'kraftstoff': v.get('kraftstoff') or '',
        'kraftstoff_id': v.get('kraftstoff_id'),
        'getriebe': v.get('getriebe') or '',
        'getriebe_id': v.get('getriebe_id'),
        'leistung_kw': v.get('leistung_kw'),
        'leistung_ps': v.get('leistung_ps'),
        'farbe_basis': v.get('farbe_basis') or '',
        'farbe_wording': v.get('farbe_wording') or '',
        'ist_metallic': v.get('ist_metallic', False),
        'zustand': v.get('zustand') or '',
        'zustand_wording': v.get('zustand_wording') or '',
        'standzeit_tage': standzeit,
        'standzeit_status': status,
        'standzeit_badge': badge,
        'lagereingang': v.get('lagereingang') or v.get('hereinnahme'),
        'hereinnahme': v.get('lagereingang') or v.get('hereinnahme'),
        'standort': v.get('standort') or '',
        'bilder': v.get('bilder') or [],
        'hauptbild': v.get('hauptbild'),
        'preis_bewertung': None,
        'preis_bewertung_text': None,
        'mobile_link': None,
        'as24_link': None,
        'mobile_platz': None,
        'total_hits': None,
        'status': v.get('status'),
    }
    # BWA: mobile.de Börsenplatzierung (aus Tabelle eautoseller_bwa_placement)
    if bwa_placements_by_vin and v.get('vin'):
        bwa = bwa_placements_by_vin.get(v.get('vin')) or bwa_placements_by_vin.get((v.get('vin') or '').upper())
        if bwa and not bwa.get('error'):
            out['mobile_platz'] = bwa.get('mobile_platz')
            out['total_hits'] = bwa.get('total_hits')
            if bwa.get('mobile_url') and not out['mobile_link']:
                out['mobile_link'] = bwa.get('mobile_url')
    # Publikationsstatistiken (priceRating 1–5, Links)
    pub = None
    if publications_by_vin and v.get('vin'):
        pub = publications_by_vin.get(v.get('vin')) or publications_by_vin.get((v.get('vin') or '').upper())
    if not pub and publications_by_id and v.get('id') is not None:
        pub = publications_by_id.get(v.get('id'))
    if pub:
        stats = pub.get('statistics') or {}
        mob = stats.get('mobileStatistic') or stats.get('mobile_statistic') or {}
        as24 = stats.get('autoscout24Statistic') or stats.get('autoscout24_statistic') or {}
        rating = mob.get('priceRating') or mob.get('price_rating')
        if rating is not None:
            out['preis_bewertung'] = int(rating)
            out['preis_bewertung_text'] = {
                1: 'Sehr guter Preis',
                2: 'Guter Preis',
                3: 'Fairer Preis',
                4: 'Erhöhter Preis',
                5: 'Hoher Preis',
            }.get(int(rating), '')
        mp = pub.get('mobilePublication') or pub.get('mobile_publication') or {}
        out['mobile_link'] = mp.get('link') or mp.get('url')
        ap = pub.get('autoscout24Publication') or pub.get('autoscout24_publication') or {}
        out['as24_link'] = ap.get('link') or ap.get('url')
    return out


# ============================================================================
# API ENDPOINTS
# ============================================================================

@eautoseller_api.route('/vehicles', methods=['GET'])
def get_vehicles():
    """
    GET /api/eautoseller/vehicles

    Liefert Fahrzeugliste aus eAutoseller. API-Abruf nur mit status=1 (Aktiv);
    alle weiteren Filter werden im Backend angewendet.

    Query (API-seitig nur): offer_reference, vin, changed_since.
    Backend-Filter: marke, modell, min_preis, max_preis, min_km, max_km,
    kraftstoff, getriebe, farbe, zustand, ez_von, ez_bis, min_kw, max_kw,
        standort, min_standzeit, max_standzeit, status (ok|warning|critical), sort.
    """
    use_swagger = request.args.get('use_swagger', 'true').lower() == 'true'
    from_cache = False
    is_mock = False

    try:
        client = get_client()
        api_status = 1
        offer_reference = request.args.get('offer_reference') or request.args.get('offerReference')
        vin_param = request.args.get('vin')
        changed_since = request.args.get('changed_since') or request.args.get('changedSince')

        # Cache nur für Standard-Abruf (keine vin/offer_reference/changed_since)
        use_cache = not (offer_reference or vin_param or changed_since)
        cache_key_raw = 'eautoseller:vehicles_raw'
        vehicles = None
        if use_cache:
            vehicles, from_cache = _cache_get(cache_key_raw, TTL_VEHICLES_RAW)

        if vehicles is None:
            if use_swagger:
                try:
                    vehicles = client.get_vehicles_swagger(
                        offer_reference=offer_reference,
                        vin=vin_param,
                        changed_since=changed_since,
                        status=api_status,
                        use_swagger=True
                    )
                    if not vehicles:
                        vehicles = client.get_vehicle_list(active_only=True, fetch_hereinnahme=False)
                except Exception as e:
                    logger.warning("eAutoseller vehicles API error, trying cache: %s", e)
                    if use_cache:
                        vehicles, from_cache = _cache_get(cache_key_raw, TTL_VEHICLES_RAW)
                    if not vehicles:
                        vehicles = client.get_vehicle_list(active_only=True, fetch_hereinnahme=False)
                else:
                    if use_cache:
                        _cache_set(cache_key_raw, vehicles or [], TTL_VEHICLES_RAW)
            else:
                vehicles = client.get_vehicle_list(active_only=True, fetch_hereinnahme=False)
                if use_cache:
                    _cache_set(cache_key_raw, vehicles or [], TTL_VEHICLES_RAW)

        # Gültige Einträge (keine Filter-Optionen mit Riesen-Marke)
        vehicles = [v for v in (vehicles or []) if v and (v.get('marke') or '') and len(str(v.get('marke', ''))) < 100]

        if not vehicles:
            is_mock = True
            vehicles = [
                {'id': 1, 'marke': 'BMW', 'modell': '320d', 'preis': 28900.0, 'hereinnahme': (datetime.now() - timedelta(days=65)).date().isoformat(), 'standzeit_tage': 65, 'km': 85000, 'ez_jahr': 2019, 'kraftstoff': 'Diesel', 'getriebe': 'Automatik', 'standort': 'Deggendorf'},
                {'id': 2, 'marke': 'Audi', 'modell': 'A4', 'preis': 32500.0, 'hereinnahme': (datetime.now() - timedelta(days=12)).date().isoformat(), 'standzeit_tage': 12, 'km': 12000, 'ez_jahr': 2023, 'kraftstoff': 'Benzin', 'getriebe': 'Automatik', 'standort': 'Landau'},
            ]

        # Standzeit aus stockEntrance/lagereingang bereits im Client; Status/Badge setzen
        for v in vehicles:
            st = v.get('standzeit_tage')
            if v.get('standzeit_status') is None:
                v['standzeit_status'] = get_standzeit_status(st)
            if not v.get('lagereingang') and v.get('hereinnahme'):
                v['lagereingang'] = v['hereinnahme']

        # --- Backend-Filter (alle hier, nicht API-seitig) ---
        filter_applied = {}
        marke = (request.args.get('marke') or '').strip()
        if marke:
            filter_applied['marke'] = marke
            vehicles = [v for v in vehicles if (v.get('marke') or '').lower().startswith(marke.lower())]
        modell = (request.args.get('modell') or '').strip()
        if modell:
            filter_applied['modell'] = modell
            vehicles = [v for v in vehicles if modell.lower() in (v.get('modell') or '').lower()]
        min_preis = request.args.get('min_preis', type=float)
        if min_preis is not None:
            filter_applied['min_preis'] = min_preis
            vehicles = [v for v in vehicles if (v.get('preis') or 0) >= min_preis]
        max_preis = request.args.get('max_preis', type=float)
        if max_preis is not None:
            filter_applied['max_preis'] = max_preis
            vehicles = [v for v in vehicles if (v.get('preis') or 0) <= max_preis]
        min_km = request.args.get('min_km', type=int)
        if min_km is not None:
            filter_applied['min_km'] = min_km
            vehicles = [v for v in vehicles if (v.get('km') or 0) >= min_km]
        max_km = request.args.get('max_km', type=int)
        if max_km is not None:
            filter_applied['max_km'] = max_km
            vehicles = [v for v in vehicles if (v.get('km') or 0) <= max_km]
        kraftstoff = (request.args.get('kraftstoff') or '').strip()
        if kraftstoff:
            filter_applied['kraftstoff'] = kraftstoff
            vehicles = [v for v in vehicles if kraftstoff.lower() in (v.get('kraftstoff') or '').lower()]
        getriebe = (request.args.get('getriebe') or '').strip().lower()
        if getriebe:
            filter_applied['getriebe'] = getriebe
            if getriebe == 'automatik':
                vehicles = [v for v in vehicles if v.get('getriebe_id') == 1 or 'automatik' in (v.get('getriebe') or '').lower()]
            elif getriebe == 'manuell':
                vehicles = [v for v in vehicles if v.get('getriebe_id') == 0 or 'manuell' in (v.get('getriebe') or '').lower()]
            else:
                vehicles = [v for v in vehicles if getriebe in (v.get('getriebe') or '').lower()]
        farbe = (request.args.get('farbe') or '').strip().lower()
        if farbe:
            filter_applied['farbe'] = farbe
            vehicles = [v for v in vehicles if (v.get('farbe_basis') or '').lower() == farbe or farbe in (v.get('farbe_wording') or '').lower()]
        zustand = (request.args.get('zustand') or '').strip().upper()
        if zustand:
            filter_applied['zustand'] = zustand
            vehicles = [v for v in vehicles if (v.get('zustand') or '').upper() == zustand]
        ez_von = request.args.get('ez_von', type=int)
        if ez_von is not None:
            filter_applied['ez_von'] = ez_von
            vehicles = [v for v in vehicles if (v.get('ez_jahr') or 0) >= ez_von]
        ez_bis = request.args.get('ez_bis', type=int)
        if ez_bis is not None:
            filter_applied['ez_bis'] = ez_bis
            vehicles = [v for v in vehicles if (v.get('ez_jahr') or 0) <= ez_bis]
        min_kw = request.args.get('min_kw', type=float)
        if min_kw is not None:
            filter_applied['min_kw'] = min_kw
            vehicles = [v for v in vehicles if (v.get('leistung_kw') or 0) >= min_kw]
        max_kw = request.args.get('max_kw', type=float)
        if max_kw is not None:
            filter_applied['max_kw'] = max_kw
            vehicles = [v for v in vehicles if (v.get('leistung_kw') or 0) <= max_kw]
        standort = (request.args.get('standort') or '').strip()
        if standort:
            filter_applied['standort'] = standort
            vehicles = [v for v in vehicles if standort.lower() in (v.get('standort') or '').lower()]
        min_standzeit = request.args.get('min_standzeit', type=int)
        if min_standzeit is not None:
            filter_applied['min_standzeit'] = min_standzeit
            vehicles = [v for v in vehicles if (v.get('standzeit_tage') or 0) >= min_standzeit]
        max_standzeit = request.args.get('max_standzeit', type=int)
        if max_standzeit is not None:
            filter_applied['max_standzeit'] = max_standzeit
            vehicles = [v for v in vehicles if (v.get('standzeit_tage') or 0) <= max_standzeit]
        status_filter = request.args.get('status', '').strip()
        if status_filter in ('ok', 'warning', 'critical'):
            filter_applied['status'] = status_filter
            vehicles = [v for v in vehicles if v.get('standzeit_status') == status_filter]

        # Sortierung
        sort = (request.args.get('sort') or '').strip().lower()
        if sort == 'preis_asc':
            vehicles = sorted(vehicles, key=lambda x: (x.get('preis') or 0))
        elif sort == 'preis_desc':
            vehicles = sorted(vehicles, key=lambda x: -(x.get('preis') or 0))
        elif sort == 'km_asc':
            vehicles = sorted(vehicles, key=lambda x: (x.get('km') or 0))
        elif sort == 'km_desc':
            vehicles = sorted(vehicles, key=lambda x: -(x.get('km') or 0))
        elif sort == 'standzeit_asc':
            vehicles = sorted(vehicles, key=lambda x: (x.get('standzeit_tage') or 0))
        elif sort == 'standzeit_desc' or sort == 'neueste':
            vehicles = sorted(vehicles, key=lambda x: -(x.get('standzeit_tage') or 0))

        # Publikationen für Preis-Bewertung und Links (optional, gecacht 60 Min)
        publications_by_vin = {}
        publications_by_id = {}
        pub_list, pub_cached = _cache_get('eautoseller:publications', TTL_PUBLICATIONS)
        if not pub_cached and use_swagger:
            try:
                pub_list = client.get_publications_swagger(statistics=True, use_swagger=True)
                _cache_set('eautoseller:publications', pub_list or [], TTL_PUBLICATIONS)
            except Exception:
                pub_list = []
        for p in (pub_list or []):
            vid = p.get('id')
            vvin = p.get('vin')
            if vid is not None:
                publications_by_id[vid] = p
            if vvin:
                publications_by_vin[vvin] = p
                publications_by_vin[vvin.upper()] = p

        # BWA: mobile.de Position aus Tabelle eautoseller_bwa_placement (Celery füllt sie)
        vins_for_bwa = [v.get('vin') for v in vehicles if v.get('vin') and len(str(v.get('vin')).strip()) == 17]
        bwa_placements_by_vin = _get_bwa_placements_from_db(vins_for_bwa)

        # Response-Format (Plugin-kompatibel)
        formatted = [
            format_vehicle_response(v, publications_by_vin, publications_by_id, bwa_placements_by_vin)
            for v in vehicles
        ]
        total = len(formatted)

        # Statistiken
        critical = sum(1 for v in formatted if v.get('standzeit_status') == 'critical')
        warning = sum(1 for v in formatted if v.get('standzeit_status') == 'warning')
        ok_count = sum(1 for v in formatted if v.get('standzeit_status') == 'ok')
        standzeiten = [v['standzeit_tage'] for v in formatted if v.get('standzeit_tage') is not None]
        avg_standzeit = sum(standzeiten) / len(standzeiten) if standzeiten else None
        preise = [v['preis'] for v in formatted if v.get('preis') is not None and v.get('preis') > 0]
        lagerwert = sum(preise) if preise else 0.0
        avg_preis = sum(preise) / len(preise) if preise else None
        kritische_fahrzeuge_wert = sum(v['preis'] for v in formatted if v.get('standzeit_status') == 'critical' and (v.get('preis') or 0) > 0)
        potenzielle_abschreibung = kritische_fahrzeuge_wert * 0.0158 if kritische_fahrzeuge_wert else 0.0
        verkaufsrate = None
        try:
            kpis = client.get_dashboard_kpis()
            if kpis.get('widget_202', {}).get('values'):
                verkaufe = int(kpis['widget_202']['values'][0] or 0)
                if verkaufe > 0 and total > 0:
                    verkaufsrate = (verkaufe / total) * 100
        except Exception:
            pass

        out = {
            'success': True,
            'vehicles': formatted,
            'total': total,
            'filter_angewendet': filter_applied,
            'statistics': {
                'total': total,
                'critical': critical,
                'warning': warning,
                'ok': ok_count,
                'avg_standzeit_tage': round(avg_standzeit, 1) if avg_standzeit else None,
                'lagerwert': round(lagerwert, 2),
                'avg_preis': round(avg_preis, 2) if avg_preis else None,
                'kritische_fahrzeuge_wert': round(kritische_fahrzeuge_wert, 2),
                'potenzielle_abschreibung': round(potenzielle_abschreibung, 2),
                'verkaufsrate': round(verkaufsrate, 1) if verkaufsrate else None,
            },
            'timestamp': datetime.now().isoformat(),
        }
        if from_cache:
            out['from_cache'] = True
        if is_mock:
            out['is_mock'] = True
        return jsonify(out)
    except Exception as e:
        logger.exception("eAutoseller vehicles: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@eautoseller_api.route('/kpis', methods=['GET'])
def get_kpis():
    """
    GET /api/eautoseller/kpis
    
    Liefert Dashboard-KPIs aus eAutoseller
    
    Returns:
        {
            'success': True,
            'kpis': {
                'widget_201': {...},
                'widget_202': {...},  # Verkäufe
                'widget_203': {...},  # Bestand
                'widget_204': {...},  # Anfragen
                'widget_205': {...},  # Pipeline
                ...
            },
            'summary': {
                'verkaufe': 24,
                'bestand': 90,
                'anfragen': 20,
                'pipeline': 26
            }
        }
    """
    try:
        client = get_client()
        kpis = client.get_dashboard_kpis()
        
        # Extrahiere wichtige Werte für Summary
        summary = {}
        
        # Widget 202: Verkäufe (erster Wert)
        if 'widget_202' in kpis and kpis['widget_202']['values']:
            try:
                summary['verkaufe'] = int(kpis['widget_202']['values'][0]) if kpis['widget_202']['values'][0] else 0
            except:
                summary['verkaufe'] = 0
        
        # Widget 203: Bestand
        if 'widget_203' in kpis and kpis['widget_203']['values']:
            try:
                summary['bestand'] = int(kpis['widget_203']['values'][0]) if kpis['widget_203']['values'][0] else 0
            except:
                summary['bestand'] = 0
        
        # Widget 204: Anfragen
        if 'widget_204' in kpis and kpis['widget_204']['values']:
            try:
                summary['anfragen'] = int(kpis['widget_204']['values'][0]) if kpis['widget_204']['values'][0] else 0
            except:
                summary['anfragen'] = 0
        
        # Widget 205: Pipeline
        if 'widget_205' in kpis and kpis['widget_205']['values']:
            try:
                summary['pipeline'] = int(kpis['widget_205']['values'][0]) if kpis['widget_205']['values'][0] else 0
            except:
                summary['pipeline'] = 0
        
        return jsonify({
            'success': True,
            'kpis': kpis,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _compute_filter_options(vehicles):
    """Berechnet filter_options aus Fahrzeugliste."""
    vehicles = [v for v in (vehicles or []) if v and len(str(v.get('marke', ''))) < 100]
    marken = sorted(set(v.get('marke') for v in vehicles if v.get('marke')), key=lambda x: (x or ''))
    kraftstoffe = sorted(set(v.get('kraftstoff') for v in vehicles if v.get('kraftstoff')), key=lambda x: (x or ''))
    farben = sorted(set(v.get('farbe_basis') or v.get('farbe_wording') for v in vehicles if (v.get('farbe_basis') or v.get('farbe_wording'))), key=lambda x: (x or ''))
    standorte = sorted(set(v.get('standort') for v in vehicles if v.get('standort')), key=lambda x: (x or ''))
    preise = [v.get('preis') for v in vehicles if v.get('preis') is not None and v.get('preis') > 0]
    km_list = [v.get('km') for v in vehicles if v.get('km') is not None and v.get('km') > 0]
    return {
        'marken': marken,
        'kraftstoffe': kraftstoffe,
        'farben': farben,
        'standorte': standorte,
        'preis_min': min(preise) if preise else None,
        'preis_max': max(preise) if preise else None,
        'km_max': max(km_list) if km_list else None,
    }


@eautoseller_api.route('/vehicles/filter-options', methods=['GET'])
def get_filter_options():
    """
    GET /api/eautoseller/vehicles/filter-options
    Berechnet aus aktuellem Bestand: marken, kraftstoffe, farben, preis_min/max, km_max, standorte.
    Cache: 15 Min.
    """
    try:
        opts, from_cache = _cache_get('eautoseller:filter_options', TTL_FILTER_OPTIONS)
        if from_cache:
            return jsonify({'success': True, **opts, 'timestamp': datetime.now().isoformat(), 'from_cache': True})

        vehicles, veh_cached = _cache_get('eautoseller:vehicles_raw', TTL_FILTER_OPTIONS)
        if not veh_cached:
            client = get_client()
            use_swagger = request.args.get('use_swagger', 'true').lower() == 'true'
            try:
                vehicles = client.get_vehicles_swagger(status=1, use_swagger=use_swagger)
            except Exception:
                vehicles = client.get_vehicle_list(active_only=True, fetch_hereinnahme=False)
        opts = _compute_filter_options(vehicles)
        _cache_set('eautoseller:filter_options', opts, TTL_FILTER_OPTIONS)
        return jsonify({'success': True, **opts, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.exception("eAutoseller filter-options: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@eautoseller_api.route('/vehicle/<int:vehicle_id>', methods=['GET'])
def get_vehicle_detail(vehicle_id):
    """
    GET /api/eautoseller/vehicle/<id>
    Einzelfahrzeug inkl. Details (withAdditionalInformation, resolveEquipments).
    Cache: 30 Min pro vehicle_id.
    """
    cache_key = f'eautoseller:vehicle_detail:{vehicle_id}'
    cached, from_cache = _cache_get(cache_key, TTL_VEHICLE_DETAIL)
    if from_cache:
        return jsonify({'success': True, 'vehicle': cached, 'timestamp': datetime.now().isoformat(), 'from_cache': True})

    try:
        client = get_client()
        detail = client.get_vehicle_details_swagger(vehicle_id, use_swagger=True)
        if not detail:
            return jsonify({'success': False, 'error': 'Fahrzeug nicht gefunden'}), 404
        out = format_vehicle_response(detail)
        if detail.get('highlights'):
            out['highlights'] = detail['highlights']
        if detail.get('co2_wltp') is not None:
            out['co2_wltp'] = detail['co2_wltp']
        if detail.get('verbrauch_wltp') is not None:
            out['verbrauch_wltp'] = detail['verbrauch_wltp']
        _cache_set(cache_key, out, TTL_VEHICLE_DETAIL)
        return jsonify({'success': True, 'vehicle': out, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.exception("eAutoseller vehicle detail: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@eautoseller_api.route('/vehicle/<int:vehicle_id>/reserve', methods=['POST'])
def reserve_vehicle(vehicle_id):
    """POST /api/eautoseller/vehicle/<id>/reserve – Reservierung setzen."""
    try:
        client = get_client()
        data = request.get_json(silent=True) or {}
        name = data.get('name') or request.args.get('name')
        phone = data.get('phone') or request.args.get('phone')
        duration_days = data.get('duration_days', data.get('durationDays', 7))
        if isinstance(duration_days, str):
            duration_days = int(duration_days) if duration_days.isdigit() else 7
        result = client.reservation_post_swagger(vehicle_id, name=name, phone=phone, duration_days=duration_days, use_swagger=True)
        if result.get('success'):
            return jsonify({'success': True, 'message': 'Reservierung gesetzt', 'data': result.get('data', {})})
        return jsonify({'success': False, 'error': result.get('error', 'Unbekannter Fehler')}), 400
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("eAutoseller reserve: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@eautoseller_api.route('/vehicle/<int:vehicle_id>/reserve', methods=['DELETE'])
def unreserve_vehicle(vehicle_id):
    """DELETE /api/eautoseller/vehicle/<id>/reserve – Reservierung löschen."""
    try:
        client = get_client()
        result = client.reservation_delete_swagger(vehicle_id, use_swagger=True)
        if result.get('success'):
            return jsonify({'success': True, 'message': 'Reservierung gelöscht'})
        return jsonify({'success': False, 'error': result.get('error', 'Unbekannter Fehler')}), 400
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("eAutoseller unreserve: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


def get_market_placements_for_vins(vins, max_vins=30):
    """
    Liefert mobile.de Platzierung pro VIN.
    Bevorzugt: GET /dms/vehicles/prices/suggestions (ein Aufruf, DMS-Auth, kein BWA nötig).
    Liefert pro Fahrzeug: current.mobilePosition, target.priceGross (Preis für bessere Platzierung).
    """
    if not vins:
        return {}
    vins_clean = [v.strip() for v in vins if v and len(str(v).strip()) == 17][:max_vins]
    if not vins_clean:
        return {}
    result = {}
    try:
        client = get_client()
        # Ein GET: /dms/vehicles/prices/suggestions (offizielle API, keine BWA-Berechtigung nötig)
        suggestions = client.get_prices_suggestions_swagger(use_swagger=True)
        for vin in vins_clean:
            s = suggestions.get(vin) or suggestions.get(vin.upper())
            if s and not s.get('error'):
                result[vin] = {
                    'mobile_platz': s.get('mobile_platz'),
                    'total_hits': None,  # Suggestions-API liefert keine Trefferanzahl
                    'platz_1_retail_gross': s.get('platz_1_retail_gross'),
                    'target_mobile_platz': s.get('target_mobile_platz'),
                    'current_price_gross': s.get('current_price_gross'),
                    'mobile_url': None,
                    'setup_name': None,
                    'error': None,
                }
                if vin.upper() != vin:
                    result[vin.upper()] = result[vin]
            else:
                result[vin] = {'error': (s.get('error') if s else None) or 'Nicht in Price-Suggestions'}
                if vin.upper() != vin:
                    result[vin.upper()] = result[vin]
    except Exception as e:
        for vin in vins_clean:
            result[vin] = {'error': str(e)[:150]}
    return result


@eautoseller_api.route('/market-placements', methods=['GET'])
def market_placements():
    """
    GET /api/eautoseller/market-placements?vins=VIN1,VIN2,VIN3
    Liefert für jede VIN die mobile.de Börsenplatzierung (eAutoSeller BWA/Bewerter).
    """
    vins_param = request.args.get('vins', '')
    if not vins_param:
        return jsonify({})
    vins_list = [v.strip() for v in vins_param.split(',') if len(v.strip()) == 17]
    data = get_market_placements_for_vins(vins_list)
    return jsonify(data)


@eautoseller_api.route('/credentials-check', methods=['GET'])
def credentials_check():
    """
    Prüft, ob die App die eAutoSeller-Swagger-Credentials lädt (ohne Keys anzuzeigen).
    Aufruf: http://drive/api/eautoseller/credentials-check
    """
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json'))
    out = {
        'path': path,
        'file_exists': os.path.exists(path),
        'has_api_key': False,
        'has_client_secret': False,
        'test_request_status': None,
        'test_request_error': None,
    }
    if not out['file_exists']:
        return jsonify(out)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
        block = creds.get('eautoseller') or {}
        out['has_api_key'] = bool(block.get('api_key'))
        out['has_client_secret'] = bool(block.get('client_secret'))
    except Exception as e:
        out['test_request_error'] = str(e)[:200]
        return jsonify(out)
    # Optional: echten Request ausführen (Price-Suggestions, gleiche Auth wie AfA-BWA-Sync)
    if out['has_api_key'] and out['has_client_secret']:
        try:
            from lib.eautoseller_client import EAutosellerClient
            client = EAutosellerClient(username='', password='', loginbereich='kfz')
            suggestions = client.get_prices_suggestions_swagger(use_swagger=True)
            out['test_request_status'] = 'ok' if isinstance(suggestions, dict) else (str(suggestions)[:120] if suggestions else 'ok')
        except Exception as e:
            out['test_request_error'] = str(e)[:200]
    return jsonify(out)


@eautoseller_api.route('/health', methods=['GET'])
def health():
    """Health-Check"""
    try:
        client = get_client()
        client.login()
        
        return jsonify({
            'status': 'ok',
            'service': 'eautoseller',
            'version': '1.0.0',
            'logged_in': client._logged_in
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'eautoseller',
            'error': str(e)
        }), 500

