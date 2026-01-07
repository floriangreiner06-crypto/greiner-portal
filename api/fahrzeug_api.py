"""
Fahrzeug REST API
Fahrzeugbestand aus Locosoft (GW, NW, VFW)

VERSION 1.0 - Nutzt fahrzeug_data.py als SSOT
- GW-Bestand mit Standzeit-Kategorien
- NW-Pipeline (bestellte Neufahrzeuge)
- VFW-Bestand (Vorführwagen)
- Standzeit-Statistiken und Warnungen

Erstellt: TAG 160 (2026-01-02)
"""

from flask import Blueprint, jsonify, request, Response
from datetime import datetime
import csv
import io

# SSOT Data Module
from api.fahrzeug_data import FahrzeugData

# Blueprint erstellen
fahrzeug_api = Blueprint('fahrzeug_api', __name__, url_prefix='/api/fahrzeug')


# ============================================================================
# HEALTH CHECK
# ============================================================================

@fahrzeug_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({
        'status': 'ok',
        'service': 'fahrzeug_api',
        'version': '1.0-data-module'
    })


# ============================================================================
# GW BESTAND
# ============================================================================

@fahrzeug_api.route('/gw', methods=['GET'])
def get_gw_bestand():
    """
    GET /api/fahrzeug/gw?standort=1&kategorie=penner&limit=50

    Liefert aktuellen GW-Bestand aus Locosoft.

    Parameter:
        standort: 1=DEG Opel, 2=DEG Hyundai, 3=Landau (optional)
        kategorie: frisch|ok|risiko|penner|leiche (optional)
        limit: Max. Anzahl Fahrzeuge (optional)
    """
    standort = request.args.get('standort', type=int)
    kategorie = request.args.get('kategorie')
    limit = request.args.get('limit', type=int)

    result = FahrzeugData.get_gw_bestand(
        standort=standort,
        kategorie=kategorie,
        limit=limit
    )

    return jsonify(result)


@fahrzeug_api.route('/gw/statistik', methods=['GET'])
def get_gw_statistik():
    """
    GET /api/fahrzeug/gw/statistik?standort=1

    Liefert aggregierte Standzeit-Statistik für GW-Bestand.
    """
    standort = request.args.get('standort', type=int)

    result = FahrzeugData.get_standzeit_statistik(standort=standort)

    return jsonify(result)


@fahrzeug_api.route('/gw/warnungen', methods=['GET'])
def get_gw_warnungen():
    """
    GET /api/fahrzeug/gw/warnungen?min_tage=90&standort=1

    Liefert GW mit kritischer Standzeit (brauchen Aktion).
    """
    min_tage = request.args.get('min_tage', 90, type=int)
    standort = request.args.get('standort', type=int)

    result = FahrzeugData.get_standzeit_warnungen(
        min_tage=min_tage,
        standort=standort
    )

    return jsonify(result)


# ============================================================================
# NW PIPELINE
# ============================================================================

@fahrzeug_api.route('/nw', methods=['GET'])
def get_nw_pipeline():
    """
    GET /api/fahrzeug/nw?standort=1&nur_mit_vertrag=true

    Liefert bestellte Neuwagen die noch nicht fakturiert wurden.
    """
    standort = request.args.get('standort', type=int)
    nur_mit_vertrag = request.args.get('nur_mit_vertrag', 'false').lower() == 'true'

    result = FahrzeugData.get_nw_pipeline(
        standort=standort,
        nur_mit_vertrag=nur_mit_vertrag
    )

    return jsonify(result)


# ============================================================================
# VFW BESTAND
# ============================================================================

@fahrzeug_api.route('/vfw', methods=['GET'])
def get_vfw_bestand():
    """
    GET /api/fahrzeug/vfw?standort=1

    Liefert aktuellen Vorführwagen-Bestand.
    """
    standort = request.args.get('standort', type=int)

    result = FahrzeugData.get_vfw_bestand(standort=standort)

    return jsonify(result)


# ============================================================================
# STANDORT-ÜBERSICHT
# ============================================================================

@fahrzeug_api.route('/standorte', methods=['GET'])
def get_bestand_nach_standort():
    """
    GET /api/fahrzeug/standorte

    Liefert Bestandsübersicht gruppiert nach Standort.
    """
    result = FahrzeugData.get_bestand_nach_standort()

    return jsonify(result)


# ============================================================================
# DASHBOARD DATA (Kombiniert für Frontend)
# ============================================================================

@fahrzeug_api.route('/gw/finanzierung', methods=['GET'])
def get_gw_finanzierung():
    """
    GET /api/fahrzeug/gw/finanzierung?standort=1

    GW-Bestand mit Finanzierungsdaten (Zinsen, Finanzinstitut).
    Verbindet Locosoft-Bestand mit DRIVE Finanzierungstabelle.
    """
    standort = request.args.get('standort', type=int)

    result = FahrzeugData.get_gw_mit_finanzierung(standort=standort)

    return jsonify({
        'success': True,
        **result
    })


@fahrzeug_api.route('/gw/dashboard', methods=['GET'])
def get_gw_dashboard():
    """
    GET /api/fahrzeug/gw/dashboard?standort=1

    Kombinierte Daten für GW-Dashboard:
    - Standzeit-Statistik (Kategorien)
    - Top 10 Problemfälle
    - Bestand nach Standort
    """
    standort = request.args.get('standort', type=int)

    # Statistik
    statistik = FahrzeugData.get_standzeit_statistik(standort=standort)

    # Top 10 Problemfälle (>90 Tage)
    warnungen = FahrzeugData.get_standzeit_warnungen(min_tage=90, standort=standort)
    top_problemfaelle = warnungen.get('warnungen', [])[:10]

    # Bestand nach Standort
    standort_uebersicht = FahrzeugData.get_bestand_nach_standort()

    return jsonify({
        'success': True,
        'statistik': statistik,
        'top_problemfaelle': top_problemfaelle,
        'standort_uebersicht': standort_uebersicht,
        'filter': {
            'standort': standort
        },
        'stand': datetime.now().isoformat()
    })


# ============================================================================
# CSV EXPORT
# ============================================================================

@fahrzeug_api.route('/gw/export', methods=['GET'])
def export_gw_csv():
    """
    GET /api/fahrzeug/gw/export?standort=1&kategorie=penner

    Exportiert GW-Bestand als CSV-Datei.
    """
    standort = request.args.get('standort', type=int)
    kategorie = request.args.get('kategorie')

    result = FahrzeugData.get_gw_bestand(
        standort=standort,
        kategorie=kategorie
    )

    fahrzeuge = result.get('fahrzeuge', [])

    # CSV generieren
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        'Haendler-Nr', 'Kennzeichen', 'VIN', 'Modell', 'EZ',
        'KM-Stand', 'EK-Preis', 'VK-Preis', 'Kalk. DB',
        'Standzeit (Tage)', 'Kategorie', 'Standort'
    ])

    # Daten
    for f in fahrzeuge:
        writer.writerow([
            f.get('dealer_vehicle_number', ''),
            f.get('license_plate', ''),
            f.get('vin', ''),
            f.get('modell', ''),
            str(f.get('ez', ''))[:10] if f.get('ez') else '',
            f.get('km_stand', ''),
            f.get('ek_preis', ''),
            f.get('vk_preis', ''),
            f.get('kalk_db', ''),
            f.get('standzeit_tage', ''),
            f.get('standzeit_kategorie', ''),
            f.get('standort_name', '')
        ])

    # Response
    output.seek(0)
    filename = f"gw_bestand_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
