"""
Leasys Programmfinder API
==========================
API für den Leasys Leasing-Programmfinder.
Hilft Verkäufern, das richtige Master Agreement zu finden.

NEU: Live-Daten von Leasys API mit Caching und Fallback auf statische JSON.

Erstellt: 2025-11-28
Update: 2025-11-28 - Live API Integration
"""

from flask import Blueprint, jsonify, request, current_app
import json
import os
import threading
import time
from datetime import datetime, timedelta
from functools import lru_cache

leasys_api = Blueprint('leasys_api', __name__, url_prefix='/api/leasys')

# Pfad zur Konfigurationsdatei (Fallback)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'leasys_programme.json')
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'credentials.json')

# Cache für Live-Daten
_live_cache = {
    'master_agreements': None,
    'vehicles_opel': None,
    'vehicles_leapmotor': None,
    'brands': None,
    'last_update': None,
    'client': None,
    'client_valid_until': None
}
_cache_lock = threading.Lock()
CACHE_DURATION = timedelta(minutes=30)


def get_leasys_client():
    """Holt oder erstellt einen Leasys API Client mit gültiger Session."""
    global _live_cache
    
    now = datetime.now()
    
    # Prüfe ob Client noch gültig
    if _live_cache['client'] and _live_cache['client_valid_until']:
        if now < _live_cache['client_valid_until']:
            return _live_cache['client']
    
    # Neuen Client erstellen
    try:
        # Import hier um zirkuläre Imports zu vermeiden
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from tools.scrapers.leasys_api_client import LeasysAPIClient
        
        # Credentials laden
        with open(CREDENTIALS_PATH, 'r') as f:
            creds = json.load(f)
        
        leasys_creds = creds.get('external_systems', {}).get('leasys', {})
        if not leasys_creds:
            print("⚠️ Leasys Credentials nicht gefunden")
            return None
        
        client = LeasysAPIClient(
            username=leasys_creds['username'],
            password=leasys_creds['password']
        )
        
        # Login
        if client.login(headless=True):
            _live_cache['client'] = client
            _live_cache['client_valid_until'] = now + timedelta(minutes=25)  # Session ~30min gültig
            print("✅ Leasys Client erstellt und eingeloggt")
            return client
        else:
            print("❌ Leasys Login fehlgeschlagen")
            return None
            
    except Exception as e:
        print(f"❌ Leasys Client Fehler: {e}")
        return None


def fetch_live_master_agreements():
    """Holt Master Agreements von der Leasys API."""
    client = get_leasys_client()
    if not client:
        return None
    
    try:
        agreements = client.get_master_agreements()
        return agreements
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Master Agreements: {e}")
        return None


def fetch_live_vehicles(brand_code):
    """Holt Fahrzeuge für eine Marke von der Leasys API."""
    client = get_leasys_client()
    if not client:
        return None
    
    try:
        base = "https://e-touch.leasys.com/sap/opu/odata/sap/ZNFC_P23_SRV"
        r = client.session.get(f"{base}/BRAND('{brand_code}')/VHL_SET?$top=100")
        if r.status_code == 200:
            return r.json().get('d', {}).get('results', [])
        return None
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Fahrzeuge: {e}")
        return None


def get_cached_data(key, fetch_func, *args):
    """Holt Daten aus Cache oder lädt neu."""
    global _live_cache
    
    with _cache_lock:
        now = datetime.now()
        
        # Cache prüfen
        if _live_cache[key] and _live_cache['last_update']:
            if now - _live_cache['last_update'] < CACHE_DURATION:
                return _live_cache[key]
        
        # Neu laden
        data = fetch_func(*args) if args else fetch_func()
        if data:
            _live_cache[key] = data
            _live_cache['last_update'] = now
            return data
        
        # Fallback auf gecachte Daten
        return _live_cache.get(key)


def load_programme():
    """Lädt die Leasys-Programme aus der JSON-Datei (Fallback)."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Konfigurationsdatei nicht gefunden", "programme": [], "sonderaktionen": []}
    except json.JSONDecodeError:
        return {"error": "Fehler beim Lesen der Konfiguration", "programme": [], "sonderaktionen": []}


def map_live_to_local(live_agreements):
    """
    Mappt Live Master Agreements auf unser lokales Format.
    Ergänzt fehlende Infos aus der statischen Konfiguration.
    """
    local_data = load_programme()
    local_programme = {p['ma_id']: p for p in local_data.get('programme', []) if p.get('ma_id')}
    
    mapped = []
    for ma in live_agreements:
        ma_id = ma.get('mastAgId', '')
        ma_desc = ma.get('mastAgDescription', '')
        favorite = ma.get('Favorite') == 'X'
        
        # Versuche lokale Daten zu finden
        local = local_programme.get(ma_id, {})
        
        # Automatische Erkennung aus Beschreibung
        marke = 'Opel'  # Default
        if 'leapmotor' in ma_desc.lower():
            marke = 'Leapmotor'
        
        fahrzeugtyp = 'NW'  # Default
        if 'vfw' in ma_desc.lower() or 'tz' in ma_desc.lower() or 'as new' in ma_desc.lower():
            fahrzeugtyp = 'TZ/VFW'
        
        buyback = 'Handel'  # Default (BB = Buyback)
        if 'leasys' in ma_desc.lower() and 'bb' not in ma_desc.lower():
            buyback = 'Leasys'
        
        # Laufzeit aus Beschreibung extrahieren
        laufzeit_min = 24
        laufzeit_max = 60
        if '36-60' in ma_desc:
            laufzeit_min = 36
            laufzeit_max = 60
        elif '24-35' in ma_desc:
            laufzeit_min = 24
            laufzeit_max = 35
        
        # Kombiniere Live + Local
        mapped.append({
            'id': ma_id,
            'ma_id': ma_id,
            'name': ma_desc,
            'marke': local.get('marke', marke),
            'fahrzeugtyp': local.get('fahrzeugtyp', fahrzeugtyp),
            'buyback': local.get('buyback', buyback),
            'laufzeit_min': local.get('laufzeit_min', laufzeit_min),
            'laufzeit_max': local.get('laufzeit_max', laufzeit_max),
            'subventioniert': local.get('subventioniert', True),
            'sonderfall': local.get('sonderfall'),
            'erklaerung': local.get('erklaerung', ma_desc),
            'hinweise': local.get('hinweise', []),
            'aktiv': True,
            'sonderaktion': False,
            'favorite': favorite,
            'live': True  # Markierung dass aus Live-API
        })
    
    return mapped


@leasys_api.route('/health', methods=['GET'])
def health():
    """Health-Check Endpoint."""
    data = load_programme()
    
    # Live-Status prüfen
    live_status = "nicht verbunden"
    live_count = 0
    
    if _live_cache['master_agreements']:
        live_status = "verbunden (cached)"
        live_count = len(_live_cache['master_agreements'])
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "programme_count": len(data.get('programme', [])),
        "sonderaktionen_count": len(data.get('sonderaktionen', [])),
        "live_status": live_status,
        "live_count": live_count,
        "cache_age": str(datetime.now() - _live_cache['last_update']) if _live_cache['last_update'] else None,
        "meta": data.get('meta', {})
    })


@leasys_api.route('/live/master-agreements', methods=['GET'])
def get_live_master_agreements():
    """
    Holt Master Agreements direkt von der Leasys API.
    Mit Caching (30 Minuten).
    """
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if force_refresh:
        with _cache_lock:
            _live_cache['master_agreements'] = None
            _live_cache['last_update'] = None
    
    # Live-Daten holen
    live_data = get_cached_data('master_agreements', fetch_live_master_agreements)
    
    if live_data:
        # Auf unser Format mappen
        mapped = map_live_to_local(live_data)
        
        return jsonify({
            "success": True,
            "source": "live",
            "count": len(mapped),
            "cache_age_seconds": (datetime.now() - _live_cache['last_update']).seconds if _live_cache['last_update'] else 0,
            "programme": mapped
        })
    else:
        # Fallback auf statische Daten
        data = load_programme()
        return jsonify({
            "success": True,
            "source": "fallback",
            "count": len(data.get('programme', [])),
            "warning": "Live-API nicht erreichbar, nutze lokale Daten",
            "programme": data.get('programme', [])
        })


@leasys_api.route('/live/vehicles', methods=['GET'])
def get_live_vehicles():
    """
    Holt Fahrzeuge von der Leasys API.
    
    Query-Parameter:
    - marke: Opel oder Leapmotor (default: Opel)
    """
    marke = request.args.get('marke', 'Opel').lower()
    
    # Brand Code mapping
    brand_codes = {
        'opel': '000020',
        'leapmotor': 'B00151'
    }
    
    brand_code = brand_codes.get(marke, '000020')
    cache_key = f'vehicles_{marke}'
    
    # Live-Daten holen
    if cache_key not in _live_cache:
        _live_cache[cache_key] = None
    
    def fetch():
        return fetch_live_vehicles(brand_code)
    
    live_data = get_cached_data(cache_key, fetch)
    
    if live_data:
        # Vereinfachtes Format
        vehicles = [
            {
                'code': v.get('vhlSetCode'),
                'name': v.get('vhlSet'),
                'brand': marke.capitalize()
            }
            for v in live_data
        ]
        
        return jsonify({
            "success": True,
            "source": "live",
            "marke": marke.capitalize(),
            "count": len(vehicles),
            "vehicles": vehicles
        })
    else:
        # Fallback auf statische Liste
        static_vehicles = {
            'opel': ['Corsa', 'Astra', 'Mokka', 'Grandland', 'Frontera', 'Combo', 'Vivaro', 'Movano', 'Zafira'],
            'leapmotor': ['T03', 'C10', 'C16', 'B10']
        }
        
        return jsonify({
            "success": True,
            "source": "fallback",
            "marke": marke.capitalize(),
            "count": len(static_vehicles.get(marke, [])),
            "warning": "Live-API nicht erreichbar",
            "vehicles": [{'name': v, 'brand': marke.capitalize()} for v in static_vehicles.get(marke, [])]
        })


@leasys_api.route('/programme', methods=['GET'])
def get_programme():
    """
    Gibt alle verfügbaren Leasing-Programme zurück.
    Versucht zuerst Live-Daten, dann Fallback auf statische JSON.
    
    Query-Parameter:
    - marke: Filter nach Marke (Opel, Leapmotor)
    - fahrzeugtyp: Filter nach Fahrzeugtyp (NW, TZ/VFW)
    - buyback: Filter nach Rücknahme (Leasys, Handel)
    - laufzeit: Filter nach Laufzeit in Monaten
    - sonderfall: Filter nach Sonderfall
    - nur_aktive: Nur aktive Programme (default: true)
    - live: Nutze Live-API (default: true)
    """
    use_live = request.args.get('live', 'true').lower() == 'true'
    
    # Versuche Live-Daten
    programme = []
    source = "fallback"
    
    if use_live:
        live_data = get_cached_data('master_agreements', fetch_live_master_agreements)
        if live_data:
            programme = map_live_to_local(live_data)
            source = "live"
    
    # Fallback
    if not programme:
        data = load_programme()
        programme = data.get('programme', [])
        source = "fallback"
    
    # Filter anwenden
    marke = request.args.get('marke')
    fahrzeugtyp = request.args.get('fahrzeugtyp')
    buyback = request.args.get('buyback')
    laufzeit = request.args.get('laufzeit', type=int)
    sonderfall = request.args.get('sonderfall')
    nur_aktive = request.args.get('nur_aktive', 'true').lower() == 'true'
    
    gefiltert = []
    for prog in programme:
        # Aktiv-Filter
        if nur_aktive and not prog.get('aktiv', True):
            continue
        
        # Marke-Filter
        if marke and prog.get('marke', '').lower() != marke.lower():
            continue
        
        # Fahrzeugtyp-Filter
        if fahrzeugtyp:
            prog_typ = prog.get('fahrzeugtyp', '')
            if fahrzeugtyp.lower() == 'nw' and prog_typ != 'NW':
                continue
            if fahrzeugtyp.lower() in ['tz', 'vfw', 'tz/vfw'] and prog_typ != 'TZ/VFW':
                continue
        
        # BuyBack-Filter
        if buyback and prog.get('buyback', '').lower() != buyback.lower():
            continue
        
        # Laufzeit-Filter
        if laufzeit:
            lz_min = prog.get('laufzeit_min', 0)
            lz_max = prog.get('laufzeit_max', 999)
            if not (lz_min <= laufzeit <= lz_max):
                continue
        
        # Sonderfall-Filter
        if sonderfall:
            if sonderfall == 'standard' and prog.get('sonderfall') is not None:
                continue
            elif sonderfall != 'standard' and prog.get('sonderfall') != sonderfall:
                continue
        
        gefiltert.append(prog)
    
    return jsonify({
        "success": True,
        "source": source,
        "count": len(gefiltert),
        "filter": {
            "marke": marke,
            "fahrzeugtyp": fahrzeugtyp,
            "buyback": buyback,
            "laufzeit": laufzeit,
            "sonderfall": sonderfall
        },
        "programme": gefiltert
    })


@leasys_api.route('/sonderaktionen', methods=['GET'])
def get_sonderaktionen():
    """
    Gibt alle aktiven Sonderaktionen zurück.
    (Sonderaktionen kommen aus der statischen JSON, nicht von der Live-API)
    
    Query-Parameter:
    - marke: Filter nach Marke
    - modell: Filter nach Modell (Teilstring-Suche)
    - nur_gueltige: Nur aktuell gültige Aktionen (default: true)
    """
    data = load_programme()
    sonderaktionen = data.get('sonderaktionen', [])
    
    marke = request.args.get('marke')
    modell = request.args.get('modell')
    nur_gueltige = request.args.get('nur_gueltige', 'true').lower() == 'true'
    heute = datetime.now().date()
    
    gefiltert = []
    for aktion in sonderaktionen:
        # Aktiv-Filter
        if not aktion.get('aktiv', True):
            continue
        
        # Gültigkeits-Filter
        if nur_gueltige:
            gueltig_von = aktion.get('gueltig_von')
            gueltig_bis = aktion.get('gueltig_bis')
            
            if gueltig_von:
                von_date = datetime.strptime(gueltig_von, '%Y-%m-%d').date()
                if heute < von_date:
                    continue
            
            if gueltig_bis:
                bis_date = datetime.strptime(gueltig_bis, '%Y-%m-%d').date()
                if heute > bis_date:
                    continue
        
        # Marke-Filter
        if marke and aktion.get('marke', '').lower() != marke.lower():
            continue
        
        # Modell-Filter (Teilstring-Suche in der Modell-Liste)
        if modell:
            modelle = aktion.get('modelle', [])
            modell_gefunden = any(modell.lower() in m.lower() for m in modelle)
            if not modell_gefunden:
                continue
        
        gefiltert.append(aktion)
    
    return jsonify({
        "success": True,
        "count": len(gefiltert),
        "datum": heute.isoformat(),
        "sonderaktionen": gefiltert
    })


@leasys_api.route('/finder', methods=['GET', 'POST'])
def programmfinder():
    """
    Intelligenter Programmfinder.
    Nutzt Live-API wenn verfügbar, sonst Fallback auf statische Daten.
    
    Findet das passende Leasing-Programm basierend auf:
    - marke: Opel oder Leapmotor (required)
    - fahrzeugtyp: NW oder TZ/VFW (required)
    - buyback: Leasys oder Handel (required)
    - laufzeit: Gewünschte Laufzeit in Monaten (required)
    - sonderfall: Optional (individuelle_kondition, haendlereigen, net_price)
    - modell: Optional - für Sonderaktionen
    """
    # Parameter aus GET oder POST
    if request.method == 'POST':
        params = request.get_json() or {}
    else:
        params = request.args
    
    marke = params.get('marke')
    fahrzeugtyp = params.get('fahrzeugtyp')
    buyback = params.get('buyback')
    laufzeit = params.get('laufzeit', type=int) if request.method == 'GET' else params.get('laufzeit')
    sonderfall = params.get('sonderfall')
    modell = params.get('modell')
    
    # Validierung
    if not all([marke, fahrzeugtyp, buyback, laufzeit]):
        return jsonify({
            "success": False,
            "error": "Fehlende Parameter",
            "required": ["marke", "fahrzeugtyp", "buyback", "laufzeit"],
            "received": {
                "marke": marke,
                "fahrzeugtyp": fahrzeugtyp,
                "buyback": buyback,
                "laufzeit": laufzeit
            }
        }), 400
    
    if isinstance(laufzeit, str):
        try:
            laufzeit = int(laufzeit)
        except ValueError:
            return jsonify({"success": False, "error": "Laufzeit muss eine Zahl sein"}), 400
    
    # Versuche Live-Daten
    live_data = get_cached_data('master_agreements', fetch_live_master_agreements)
    if live_data:
        programme = map_live_to_local(live_data)
        source = "live"
    else:
        data = load_programme()
        programme = data.get('programme', [])
        source = "fallback"
    
    # Sonderaktionen immer aus lokaler Datei
    data = load_programme()
    sonderaktionen = data.get('sonderaktionen', [])
    heute = datetime.now().date()
    
    ergebnis = {
        "success": True,
        "source": source,
        "eingabe": {
            "marke": marke,
            "fahrzeugtyp": fahrzeugtyp,
            "buyback": buyback,
            "laufzeit": laufzeit,
            "sonderfall": sonderfall,
            "modell": modell
        },
        "empfehlung": None,
        "alternativen": [],
        "sonderaktionen": [],
        "hinweise": []
    }
    
    # 1. Passende Sonderaktionen finden (wenn Modell angegeben)
    if modell:
        for aktion in sonderaktionen:
            if not aktion.get('aktiv', True):
                continue
            if aktion.get('marke', '').lower() != marke.lower():
                continue
            if aktion.get('buyback', '').lower() != buyback.lower():
                continue
            
            # Laufzeit prüfen
            lz_min = aktion.get('laufzeit_min', 0)
            lz_max = aktion.get('laufzeit_max', 999)
            if not (lz_min <= laufzeit <= lz_max):
                continue
            
            # Modell prüfen
            modelle = aktion.get('modelle', [])
            if any(modell.lower() in m.lower() for m in modelle):
                # Gültigkeit prüfen
                gueltig = True
                gueltig_von = aktion.get('gueltig_von')
                gueltig_bis = aktion.get('gueltig_bis')
                
                if gueltig_von and heute < datetime.strptime(gueltig_von, '%Y-%m-%d').date():
                    gueltig = False
                if gueltig_bis and heute > datetime.strptime(gueltig_bis, '%Y-%m-%d').date():
                    gueltig = False
                
                if gueltig:
                    ergebnis['sonderaktionen'].append(aktion)
                    ergebnis['hinweise'].append(f"🎯 Sonderaktion verfügbar: {aktion.get('name')}")
    
    # 2. Standard-Programm finden
    beste_treffer = []
    for prog in programme:
        if not prog.get('aktiv', True):
            continue
        if prog.get('marke', '').lower() != marke.lower():
            continue
        if prog.get('buyback', '').lower() != buyback.lower():
            continue
        
        # Fahrzeugtyp
        prog_typ = prog.get('fahrzeugtyp', '')
        if fahrzeugtyp.lower() == 'nw' and prog_typ != 'NW':
            continue
        if fahrzeugtyp.lower() in ['tz', 'vfw', 'tz/vfw'] and prog_typ != 'TZ/VFW':
            continue
        
        # Laufzeit
        lz_min = prog.get('laufzeit_min', 0)
        lz_max = prog.get('laufzeit_max', 999)
        if not (lz_min <= laufzeit <= lz_max):
            continue
        
        # Sonderfall
        prog_sonderfall = prog.get('sonderfall')
        if sonderfall:
            if sonderfall == 'standard' and prog_sonderfall is not None:
                continue
            elif sonderfall != 'standard' and prog_sonderfall != sonderfall:
                continue
        
        # Score berechnen (höher = besser)
        score = 100
        if prog_sonderfall is None and not sonderfall:
            score += 50  # Standard-Programme bevorzugen wenn kein Sonderfall gewünscht
        if prog.get('subventioniert', False):
            score += 20  # Subventionierte Programme bevorzugen
        if prog.get('favorite', False):
            score += 30  # Favoriten aus Leasys bevorzugen
        
        beste_treffer.append((score, prog))
    
    # Sortieren nach Score
    beste_treffer.sort(key=lambda x: x[0], reverse=True)
    
    if beste_treffer:
        ergebnis['empfehlung'] = beste_treffer[0][1]
        ergebnis['alternativen'] = [t[1] for t in beste_treffer[1:3]]  # Top 2 Alternativen
        
        # Hinweise vom Programm hinzufügen
        prog_hinweise = ergebnis['empfehlung'].get('hinweise', [])
        ergebnis['hinweise'].extend(prog_hinweise)
        
        # Allgemeine Hinweise
        if fahrzeugtyp.lower() in ['tz', 'vfw', 'tz/vfw']:
            ergebnis['hinweise'].append("⚠️ Bei TZ/VFW: Echte VIN und Kennzeichen verwenden!")
            ergebnis['hinweise'].append("📅 Max. 360 Tage seit EZ und max. 10.000 km")
    else:
        ergebnis['success'] = False
        ergebnis['error'] = "Kein passendes Programm gefunden"
        ergebnis['hinweise'].append("❌ Keine Übereinstimmung - bitte Parameter prüfen")
    
    return jsonify(ergebnis)


@leasys_api.route('/marken', methods=['GET'])
def get_marken():
    """Gibt die verfügbaren Marken zurück."""
    data = load_programme()
    return jsonify({
        "success": True,
        "marken": data.get('marken_filter', ['Opel', 'Leapmotor'])
    })


@leasys_api.route('/optionen', methods=['GET'])
def get_optionen():
    """Gibt alle Auswahloptionen für den Wizard zurück."""
    return jsonify({
        "success": True,
        "optionen": {
            "marken": ["Opel", "Leapmotor"],
            "fahrzeugtypen": [
                {"value": "NW", "label": "Neuwagen", "beschreibung": "Fabrikneues Fahrzeug"},
                {"value": "TZ/VFW", "label": "Tageszulassung / VFW", "beschreibung": "Bis 360 Tage seit EZ, max. 10.000 km"}
            ],
            "buyback": [
                {"value": "Leasys", "label": "Rücknahme Leasys", "beschreibung": "Leasys nimmt das Fahrzeug zurück"},
                {"value": "Handel", "label": "Rückkauf Händler", "beschreibung": "Händler kauft das Fahrzeug zurück"}
            ],
            "laufzeiten": [
                {"value": 24, "label": "24 Monate"},
                {"value": 30, "label": "30 Monate"},
                {"value": 36, "label": "36 Monate"},
                {"value": 42, "label": "42 Monate"},
                {"value": 48, "label": "48 Monate"},
                {"value": 54, "label": "54 Monate"},
                {"value": 60, "label": "60 Monate"}
            ],
            "sonderfaelle": [
                {"value": "standard", "label": "Standard", "beschreibung": "Normales B2B Leasing mit Subvention"},
                {"value": "individuelle_kondition", "label": "Individuelle Kondition", "beschreibung": "A0-Protokoll, Gesamtmargen, Net Price"},
                {"value": "haendlereigen", "label": "Händlereigenes Fahrzeug", "beschreibung": "Gewerbliche Untervermietung, z.B. Werkstattersatz"},
                {"value": "net_price", "label": "Net Price (nur TZ/VFW)", "beschreibung": "Ohne B2B Standard Konditionen"}
            ]
        }
    })


@leasys_api.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Leert den Live-Daten Cache."""
    global _live_cache
    
    with _cache_lock:
        _live_cache = {
            'master_agreements': None,
            'vehicles_opel': None,
            'vehicles_leapmotor': None,
            'brands': None,
            'last_update': None,
            'client': None,
            'client_valid_until': None
        }
    
    return jsonify({
        "success": True,
        "message": "Cache geleert"
    })


@leasys_api.route('/cache/status', methods=['GET'])
def cache_status():
    """Zeigt den aktuellen Cache-Status."""
    return jsonify({
        "success": True,
        "cache": {
            "master_agreements": len(_live_cache['master_agreements']) if _live_cache['master_agreements'] else 0,
            "vehicles_opel": len(_live_cache.get('vehicles_opel', [])) if _live_cache.get('vehicles_opel') else 0,
            "vehicles_leapmotor": len(_live_cache.get('vehicles_leapmotor', [])) if _live_cache.get('vehicles_leapmotor') else 0,
            "last_update": _live_cache['last_update'].isoformat() if _live_cache['last_update'] else None,
            "client_valid_until": _live_cache['client_valid_until'].isoformat() if _live_cache['client_valid_until'] else None,
            "cache_duration_minutes": CACHE_DURATION.seconds // 60
        }
    })


# =============================================================================
# KALKULATOR ENDPOINTS (NEU - TAG86)
# Nutzt leasys_full_api.py für Fahrzeugsuche mit Preisen
# =============================================================================

# Cache für Kalkulator-Daten
_kalkulator_cache = {
    'client': None,
    'client_authenticated': False,
    'vehicles': {},  # {brand_fuel: [vehicles]}
    'models': {},    # {brand: [models]}
    'last_update': None
}
KALKULATOR_CACHE_DURATION = timedelta(minutes=15)


def get_kalkulator_client():
    """Holt oder erstellt einen LeasysAPI Client - NUR mit Cookie-Cache, KEIN Selenium."""
    global _kalkulator_cache
    
    now = datetime.now()
    
    # Prüfe ob Client im Memory-Cache noch gültig
    if _kalkulator_cache['client'] and _kalkulator_cache['client_authenticated']:
        if _kalkulator_cache['last_update'] and (now - _kalkulator_cache['last_update']) < KALKULATOR_CACHE_DURATION:
            return _kalkulator_cache['client']
    
    try:
        import sys
        import pickle
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from tools.scrapers.leasys_full_api import LeasysAPI
        
        COOKIE_FILE = "/tmp/leasys_session.pkl"
        
        # Prüfe ob Cookie-Datei existiert
        if not os.path.exists(COOKIE_FILE):
            print("❌ Keine Cookie-Datei - bitte manuell authentifizieren")
            return None
        
        # Cookie-Alter prüfen (max 25 Minuten)
        import time
        cookie_age = time.time() - os.path.getmtime(COOKIE_FILE)
        if cookie_age > 1500:  # 25 Minuten
            print(f"⚠️ Cookies zu alt ({cookie_age/60:.0f} min) - bitte erneuern")
            return None
        
        # Client erstellen und Cookies DIREKT laden (ohne Selenium)
        client = LeasysAPI()
        
        with open(COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
        
        for c in cookies:
            client.session.cookies.set(c['name'], c['value'])
        
        # Kurzer Test ob Session gültig
        if client._test_session():
            _kalkulator_cache['client'] = client
            _kalkulator_cache['client_authenticated'] = True
            _kalkulator_cache['last_update'] = now
            print(f"✅ Kalkulator Client aus Cookie-Cache ({cookie_age/60:.1f} min alt)")
            return client
        else:
            print("❌ Cookie-Session ungültig - bitte erneuern")
            return None
            
    except Exception as e:
        print(f"❌ Kalkulator Client Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None


@leasys_api.route('/kalkulator/vehicles', methods=['GET'])
def kalkulator_vehicles():
    """
    Holt Fahrzeuge mit Preisen für den Kalkulator.
    
    Query-Parameter:
    - brand: OPEL, FIAT, etc. (default: OPEL)
    - fuel: Benzin, Diesel, Elektro, Hybrid (optional)
    - ma_id: Master Agreement ID (default: 1000026115 = KM LEASING Opel 36-60)
    - refresh: true = Cache ignorieren
    """
    brand = request.args.get('brand', 'OPEL').upper()
    fuel = request.args.get('fuel')
    ma_id = request.args.get('ma_id', '1000026115')
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    cache_key = f"{brand}_{fuel or 'ALL'}_{ma_id}"
    
    # Cache prüfen
    if not refresh and cache_key in _kalkulator_cache['vehicles']:
        cache_entry = _kalkulator_cache['vehicles'][cache_key]
        if cache_entry.get('timestamp') and (datetime.now() - cache_entry['timestamp']) < KALKULATOR_CACHE_DURATION:
            return jsonify({
                "success": True,
                "source": "cache",
                "brand": brand,
                "fuel": fuel,
                "ma_id": ma_id,
                "count": len(cache_entry['data']),
                "cache_age_seconds": (datetime.now() - cache_entry['timestamp']).seconds,
                "vehicles": cache_entry['data']
            })
    
    # Live-Daten holen
    client = get_kalkulator_client()
    if not client:
        return jsonify({
            "success": False,
            "error": "Leasys API nicht verfügbar",
            "hint": "Authentifizierung fehlgeschlagen"
        }), 503
    
    try:
        vehicles = client.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
        
        # In Cache speichern
        _kalkulator_cache['vehicles'][cache_key] = {
            'data': vehicles,
            'timestamp': datetime.now()
        }
        
        return jsonify({
            "success": True,
            "source": "live",
            "brand": brand,
            "fuel": fuel,
            "ma_id": ma_id,
            "count": len(vehicles),
            "vehicles": vehicles
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@leasys_api.route('/kalkulator/models', methods=['GET'])
def kalkulator_models():
    """
    Holt verfügbare Modelle für eine Marke.
    
    Query-Parameter:
    - brand: OPEL, FIAT, etc. (default: OPEL)
    """
    brand = request.args.get('brand', 'OPEL').upper()
    
    # Cache prüfen
    if brand in _kalkulator_cache['models']:
        cache_entry = _kalkulator_cache['models'][brand]
        if cache_entry.get('timestamp') and (datetime.now() - cache_entry['timestamp']) < KALKULATOR_CACHE_DURATION:
            return jsonify({
                "success": True,
                "source": "cache",
                "brand": brand,
                "count": len(cache_entry['data']),
                "models": cache_entry['data']
            })
    
    client = get_kalkulator_client()
    if not client:
        return jsonify({
            "success": False,
            "error": "Leasys API nicht verfügbar"
        }), 503
    
    try:
        models = client.get_models(brand=brand)
        
        _kalkulator_cache['models'][brand] = {
            'data': models,
            'timestamp': datetime.now()
        }
        
        return jsonify({
            "success": True,
            "source": "live",
            "brand": brand,
            "count": len(models),
            "models": models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@leasys_api.route('/kalkulator/brands', methods=['GET'])
def kalkulator_brands():
    """Gibt verfügbare Marken und deren Codes zurück."""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from tools.scrapers.leasys_full_api import LeasysAPI
        
        return jsonify({
            "success": True,
            "brands": [
                {"code": code, "name": name}
                for name, code in LeasysAPI.BRANDS.items()
            ],
            "fuel_types": [
                {"code": code, "name": name}
                for name, code in LeasysAPI.FUEL_CODES.items()
            ],
            "master_agreements": [
                {"id": ma_id, "name": name}
                for name, ma_id in LeasysAPI.MASTER_AGREEMENTS.items()
            ]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@leasys_api.route('/kalkulator/health', methods=['GET'])
def kalkulator_health():
    """Health-Check für Kalkulator API."""
    client = get_kalkulator_client()
    
    return jsonify({
        "success": True,
        "status": "connected" if client else "disconnected",
        "authenticated": _kalkulator_cache.get('client_authenticated', False),
        "cache": {
            "vehicles_cached": len(_kalkulator_cache.get('vehicles', {})),
            "models_cached": len(_kalkulator_cache.get('models', {})),
            "last_update": _kalkulator_cache['last_update'].isoformat() if _kalkulator_cache.get('last_update') else None
        }
    })


# PATCH TAG86: Health ohne Auto-Auth
@leasys_api.route('/kalkulator/status', methods=['GET'])
def kalkulator_status():
    """Schneller Status-Check OHNE Authentifizierung."""
    import os
    
    cookie_exists = os.path.exists('/tmp/leasys_session.pkl')
    cookie_age = None
    
    if cookie_exists:
        import time
        mtime = os.path.getmtime('/tmp/leasys_session.pkl')
        cookie_age = int(time.time() - mtime)
    
    return jsonify({
        "success": True,
        "status": "ready" if cookie_exists else "needs_auth",
        "cookie_cached": cookie_exists,
        "cookie_age_seconds": cookie_age,
        "cache": {
            "vehicles_cached": len(_kalkulator_cache.get('vehicles', {})),
            "models_cached": len(_kalkulator_cache.get('models', {}))
        }
    })


# =============================================================================
# CACHING FUNKTIONEN (TAG86)
# =============================================================================

import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'greiner_controlling.db')

# Fuel-Mapping: Frontend sendet "Benzin", Cache hat "B"
FUEL_MAP = {
    'Benzin': 'B', 'benzin': 'B',
    'Diesel': 'D', 'diesel': 'D',
    'Elektro': 'E', 'elektro': 'E',
    'Hybrid': 'H', 'hybrid': 'H',
    'B': 'B', 'D': 'D', 'E': 'E', 'H': 'H'  # Falls schon Kurzform
}

def get_cached_vehicles(brand, fuel, ma_id, max_age_minutes=180):
    """Holt Fahrzeuge aus dem SQLite-Cache."""
    try:
        # Fuel-Mapping anwenden (Frontend: "Benzin" -> Cache: "B")
        if fuel:
            fuel = FUEL_MAP.get(fuel, fuel)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # NULL-Handling für fuel
        if fuel:
            cursor.execute('''
                SELECT data, vehicle_count, created_at,
                       ROUND((julianday('now') - julianday(created_at)) * 24 * 60, 1) as age_minutes
                FROM leasys_vehicle_cache
                WHERE brand = ? AND fuel = ? AND ma_id = ?
                AND (julianday('now') - julianday(created_at)) * 24 * 60 < ?
            ''', (brand, fuel, ma_id, max_age_minutes))
        else:
            cursor.execute('''
                SELECT data, vehicle_count, created_at,
                       ROUND((julianday('now') - julianday(created_at)) * 24 * 60, 1) as age_minutes
                FROM leasys_vehicle_cache
                WHERE brand = ? AND fuel IS NULL AND ma_id = ?
                AND (julianday('now') - julianday(created_at)) * 24 * 60 < ?
            ''', (brand, ma_id, max_age_minutes))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            import json
            return {
                'vehicles': json.loads(row[0]),
                'count': row[1],
                'cached_at': row[2],
                'age_minutes': row[3]
            }
        return None
    except Exception as e:
        print(f"Cache read error: {e}")
        return None


def save_vehicles_to_cache(brand, fuel, ma_id, vehicles):
    """Speichert Fahrzeuge im SQLite-Cache."""
    try:
        import json
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO leasys_vehicle_cache (brand, fuel, ma_id, data, vehicle_count, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (brand, fuel, ma_id, json.dumps(vehicles), len(vehicles)))
        
        conn.commit()
        conn.close()
        print(f"✅ Cache: {len(vehicles)} {brand} {fuel or 'ALL'} Fahrzeuge gespeichert")
        return True
    except Exception as e:
        print(f"Cache write error: {e}")
        return False


@leasys_api.route('/kalkulator/vehicles-cached', methods=['GET'])
def kalkulator_vehicles_cached():
    """
    Holt Fahrzeuge - erst aus Cache, dann Live falls nötig.
    Viel schneller als /vehicles weil Cache-First.
    """
    brand = request.args.get('brand', 'OPEL').upper()
    fuel = request.args.get('fuel')
    ma_id = request.args.get('ma_id', '1000026115')
    max_age = request.args.get("max_age", 180, type=int)
    
    # 1. Versuche Cache
    cached = get_cached_vehicles(brand, fuel, ma_id, max_age)
    if cached:
        return jsonify({
            "success": True,
            "source": "cache",
            "brand": brand,
            "fuel": fuel,
            "ma_id": ma_id,
            "count": cached['count'],
            "cache_age_minutes": cached['age_minutes'],
            "cached_at": cached['cached_at'],
            "vehicles": cached['vehicles']
        })
    
    # 2. Kein Cache - Live laden
    client = get_kalkulator_client()
    if not client:
        return jsonify({
            "success": False,
            "error": "Leasys API nicht verfügbar - kein Cache vorhanden",
            "hint": "Bitte Session erneuern"
        }), 503
    
    try:
        vehicles = client.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
        
        # In Cache speichern
        save_vehicles_to_cache(brand, fuel, ma_id, vehicles)
        
        return jsonify({
            "success": True,
            "source": "live",
            "brand": brand,
            "fuel": fuel,
            "ma_id": ma_id,
            "count": len(vehicles),
            "vehicles": vehicles
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@leasys_api.route('/kalkulator/cache/refresh', methods=['POST'])
def refresh_cache():
    """Manuelles Cache-Refresh für alle gängigen Kombinationen."""
    client = get_kalkulator_client()
    if not client:
        return jsonify({"success": False, "error": "Keine gültige Session"}), 503
    
    results = []
    combinations = [
        ('OPEL', 'Benzin', '1000026115'),
        ('OPEL', 'Diesel', '1000026115'),
        ('OPEL', 'Elektro', '1000026115'),
        ('OPEL', None, '1000026115'),  # Alle
    ]
    
    for brand, fuel, ma_id in combinations:
        try:
            vehicles = client.get_vehicles(brand=brand, fuel=fuel, mast_ag_id=ma_id)
            save_vehicles_to_cache(brand, fuel, ma_id, vehicles)
            results.append({"brand": brand, "fuel": fuel, "count": len(vehicles), "status": "ok"})
        except Exception as e:
            results.append({"brand": brand, "fuel": fuel, "error": str(e), "status": "error"})
    
    return jsonify({
        "success": True,
        "message": "Cache aktualisiert",
        "results": results
    })
