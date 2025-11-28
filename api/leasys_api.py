"""
Leasys Programmfinder API
==========================
API für den Leasys Leasing-Programmfinder.
Hilft Verkäufern, das richtige Master Agreement zu finden.

Erstellt: 2025-11-28
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime

leasys_api = Blueprint('leasys_api', __name__, url_prefix='/api/leasys')

# Pfad zur Konfigurationsdatei
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'leasys_programme.json')


def load_programme():
    """Lädt die Leasys-Programme aus der JSON-Datei."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Konfigurationsdatei nicht gefunden", "programme": [], "sonderaktionen": []}
    except json.JSONDecodeError:
        return {"error": "Fehler beim Lesen der Konfiguration", "programme": [], "sonderaktionen": []}


@leasys_api.route('/health', methods=['GET'])
def health():
    """Health-Check Endpoint."""
    data = load_programme()
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "programme_count": len(data.get('programme', [])),
        "sonderaktionen_count": len(data.get('sonderaktionen', [])),
        "meta": data.get('meta', {})
    })


@leasys_api.route('/programme', methods=['GET'])
def get_programme():
    """
    Gibt alle verfügbaren Leasing-Programme zurück.
    
    Query-Parameter:
    - marke: Filter nach Marke (Opel, Leapmotor)
    - fahrzeugtyp: Filter nach Fahrzeugtyp (NW, TZ/VFW)
    - buyback: Filter nach Rücknahme (Leasys, Handel)
    - laufzeit: Filter nach Laufzeit in Monaten
    - sonderfall: Filter nach Sonderfall (individuelle_kondition, haendlereigen, net_price)
    - nur_aktive: Nur aktive Programme (default: true)
    """
    data = load_programme()
    programme = data.get('programme', [])
    
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
    
    data = load_programme()
    programme = data.get('programme', [])
    sonderaktionen = data.get('sonderaktionen', [])
    heute = datetime.now().date()
    
    ergebnis = {
        "success": True,
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
