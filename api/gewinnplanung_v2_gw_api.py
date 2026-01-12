"""
Gewinnplanungstool V2 - KST 2 (GW) API
=======================================
TAG 169: REST-Endpoints für GW-Planung mit Standzeit und Zinskosten
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from api.db_utils import db_session, row_to_dict
from api.gewinnplanung_v2_gw_data import (
    lade_vorjahr_gw,
    berechne_gw_planung,
    STANDORT_NAMEN
)
from api.unternehmensplan_data import get_current_geschaeftsjahr
from datetime import date

gewinnplanung_v2_gw_api = Blueprint(
    'gewinnplanung_v2_gw_api',
    __name__,
    url_prefix='/api/gewinnplanung/v2/gw'
)

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except:
    pass


@gewinnplanung_v2_gw_api.route('/vorjahr/<int:standort>', methods=['GET'])
@login_required
def get_vorjahr(standort: int):
    """
    Lädt Vorjahreswerte für GW aus BWA (SSOT).
    
    Args:
        standort: 1, 2, 3 (Einzelstandort) oder 0 (Gesamtbetrieb)
        geschaeftsjahr: Optional (Query-Parameter)
        monat: Optional (Query-Parameter, 1-12)
    """
    try:
        geschaeftsjahr = request.args.get('geschaeftsjahr', get_current_geschaeftsjahr())
        monat = request.args.get('monat', type=int)
        
        if standort == 0:
            # Gesamtbetrieb: Alle Standorte zusammen
            # Verwende build_firma_standort_filter('0', '0') für alle
            from api.controlling_api import build_firma_standort_filter, BEREICHE_CONFIG, _berechne_bereich_werte
            from api.db_utils import db_session, row_to_dict
            from api.db_connection import convert_placeholders
            from datetime import datetime
            
            # Geschäftsjahr parsen
            gj_start_jahr = int(geschaeftsjahr.split('/')[0])
            vj_gj_start = gj_start_jahr - 1
            
            if monat is None:
                vj_von = f"{vj_gj_start}-09-01"
                vj_bis = f"{vj_gj_start + 1}-09-01"
            else:
                if monat <= 4:
                    kal_monat = monat + 8
                    kal_jahr = vj_gj_start
                else:
                    kal_monat = monat - 4
                    kal_jahr = vj_gj_start + 1
                
                vj_von = f"{kal_jahr}-{kal_monat:02d}-01"
                if kal_monat == 12:
                    vj_bis = f"{kal_jahr+1}-01-01"
                else:
                    vj_bis = f"{kal_jahr}-{kal_monat+1:02d}-01"
            
            # Gesamtbetrieb BWA-Werte
            with db_session() as conn:
                cursor = conn.cursor()
                firma_filter_umsatz, firma_filter_einsatz, _, _ = build_firma_standort_filter('0', '0')
                # TAG 179: Zentrale Funktion verwenden
                from api.db_utils import get_guv_filter
                guv_filter = get_guv_filter()
                
                gw_config = BEREICHE_CONFIG['GW']
                gw_werte = _berechne_bereich_werte(cursor, 'GW', gw_config, vj_von, vj_bis,
                                                   firma_filter_umsatz, guv_filter, firma_filter_einsatz)
                
                # Variable Kosten
                cursor.execute(convert_placeholders(f"""
                    SELECT COALESCE(SUM(
                        CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END
                    ) / 100.0, 0) as variable
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                      AND (
                        (nominal_account_number BETWEEN 415100 AND 415199)
                        OR (nominal_account_number BETWEEN 435500 AND 435599)
                        OR (nominal_account_number BETWEEN 455000 AND 456999
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR (nominal_account_number BETWEEN 487000 AND 487099
                            AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                        OR (nominal_account_number BETWEEN 491000 AND 497899)
                      )
                      {guv_filter}
                """), (vj_von, vj_bis))
                row = cursor.fetchone()
                variable = float(row_to_dict(row)['variable'] or 0) if row else 0
                
                # Stückzahl aus Locosoft (alle Standorte)
                from api.db_utils import locosoft_session
                with locosoft_session() as conn_loco:
                    cursor_loco = conn_loco.cursor()
                    cursor_loco.execute(f"""
                        SELECT COUNT(*) as stueck
                        FROM dealer_vehicles
                        WHERE out_invoice_date >= %s AND out_invoice_date < %s
                          AND out_invoice_date IS NOT NULL
                          AND dealer_vehicle_type IN ('G', 'D', 'L')
                    """, (vj_von, vj_bis))
                    row = cursor_loco.fetchone()
                    stueck = int(row[0] or 0) if row else 0
                    
                    # Standzeit (Bestand)
                    cursor_loco.execute(f"""
                        SELECT AVG(CURRENT_DATE - COALESCE(in_arrival_date, created_date)) as standzeit
                        FROM dealer_vehicles
                        WHERE out_invoice_date IS NULL
                          AND dealer_vehicle_type IN ('G', 'D', 'L')
                          AND in_arrival_date IS NOT NULL
                    """)
                    row = cursor_loco.fetchone()
                    standzeit = float(row[0] or 0) if row else 0
                
                vorjahr = {
                    'umsatz': gw_werte['erlos'],
                    'db1': gw_werte['bruttoertrag'],
                    'db2': gw_werte['bruttoertrag'] - variable,
                    'stueck': stueck,
                    'standzeit': standzeit,
                    'zinskosten': 0,  # Wird später berechnet
                    'lagerwert': 0
                }
        else:
            # Einzelstandort
            # Für Standort 1: Prüfe ob nur Stellantis (Opel DEG) oder beide (Deggendorf)
            nur_stellantis = request.args.get('nur_stellantis', 'false').lower() == 'true'
            vorjahr = lade_vorjahr_gw(standort, geschaeftsjahr, monat, nur_stellantis=nur_stellantis)
        
        return jsonify({
            'success': True,
            'standort': standort,
            'standort_name': STANDORT_NAMEN.get(standort, 'Gesamtbetrieb' if standort == 0 else f'Standort {standort}'),
            'geschaeftsjahr': geschaeftsjahr,
            'monat': monat,
            'vorjahr': vorjahr
        })
    
    except Exception as e:
        if logger:
            logger.error(f"Fehler beim Laden der Vorjahreswerte: {str(e)}")
            import traceback
            traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gewinnplanung_v2_gw_api.route('/planung/<int:standort>', methods=['GET', 'POST'])
@login_required
def planung(standort: int):
    """
    Lädt oder speichert GW-Planung.
    
    GET: Lädt bestehende Planung
    POST: Speichert neue/aktualisierte Planung
    """
    try:
        geschaeftsjahr = request.args.get('geschaeftsjahr') or request.json.get('geschaeftsjahr') if request.is_json else get_current_geschaeftsjahr()
        
        if request.method == 'GET':
            # Planung laden
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM gewinnplanung_v2_gw
                    WHERE geschaeftsjahr = %s AND standort = %s
                """, (geschaeftsjahr, standort))
                
                row = cursor.fetchone()
                if row:
                    planung = row_to_dict(row)
                    
                    # Vorjahreswerte laden (falls nicht vorhanden)
                    if not planung.get('vj_umsatz'):
                        vorjahr = lade_vorjahr_gw(standort, geschaeftsjahr, None)
                        planung.update({
                            'vj_umsatz': vorjahr.get('umsatz', 0),
                            'vj_db1': vorjahr.get('db1', 0),
                            'vj_db2': vorjahr.get('db2', 0),
                            'vj_stueck': vorjahr.get('stueck', 0),
                            'vj_standzeit': vorjahr.get('standzeit', 0),
                            'vj_zinskosten': vorjahr.get('zinskosten', 0)
                        })
                    
                    return jsonify({
                        'success': True,
                        'planung': planung
                    })
                else:
                    # Keine Planung vorhanden - Vorjahreswerte laden
                    vorjahr = lade_vorjahr_gw(standort, geschaeftsjahr, None)
                    return jsonify({
                        'success': True,
                        'planung': None,
                        'vorjahr': vorjahr
                    })
        
        elif request.method == 'POST':
            # Planung speichern
            data = request.json
            planung_data = data.get('planung', {})
            
            # Prüfe ob nur Stellantis (für Opel DEG)
            nur_stellantis = data.get('nur_stellantis', False)
            
            # Vorjahreswerte laden
            vorjahr = lade_vorjahr_gw(standort, geschaeftsjahr, None, nur_stellantis=nur_stellantis)
            
            # Berechnung durchführen
            berechnung = berechne_gw_planung(planung_data, vorjahr)
            
            # In Datenbank speichern
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Prüfen ob bereits vorhanden
                cursor.execute("""
                    SELECT id FROM gewinnplanung_v2_gw
                    WHERE geschaeftsjahr = %s AND standort = %s
                """, (geschaeftsjahr, standort))
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    cursor.execute("""
                        UPDATE gewinnplanung_v2_gw SET
                            plan_stueck = %s,
                            plan_bruttoertrag_pro_fzg = %s,
                            plan_variable_kosten_pct = %s,
                            plan_verkaufspreis = %s,
                            plan_standzeit_tage = %s,
                            plan_ek_preis = %s,
                            plan_zinssatz_pct = %s,
                            umsatz_plan = %s,
                            bruttoertrag_plan = %s,
                            variable_kosten_plan = %s,
                            db1_plan = %s,
                            direkte_kosten_plan = %s,
                            lagerwert_plan = %s,
                            zinskosten_plan = %s,
                            db2_plan = %s,
                            vj_umsatz = %s,
                            vj_db1 = %s,
                            vj_db2 = %s,
                            vj_stueck = %s,
                            vj_standzeit = %s,
                            vj_zinskosten = %s,
                            impact_standzeit_ersparnis = %s,
                            impact_zinskosten_ersparnis = %s,
                            impact_db1_mehr = %s,
                            impact_db2_mehr = %s,
                            status = %s,
                            kommentar = %s,
                            erstellt_von = COALESCE(erstellt_von, %s),
                            erstellt_am = COALESCE(erstellt_am, CURRENT_TIMESTAMP)
                        WHERE geschaeftsjahr = %s AND standort = %s
                    """, (
                        planung_data.get('plan_stueck'),
                        planung_data.get('plan_bruttoertrag_pro_fzg'),
                        planung_data.get('plan_variable_kosten_pct'),
                        planung_data.get('plan_verkaufspreis'),
                        planung_data.get('plan_standzeit_tage'),
                        planung_data.get('plan_ek_preis'),
                        planung_data.get('plan_zinssatz_pct', 5.0),
                        berechnung['umsatz_plan'],
                        berechnung['bruttoertrag_plan'],
                        berechnung['variable_kosten_plan'],
                        berechnung['db1_plan'],
                        berechnung['direkte_kosten_plan'],
                        berechnung['lagerwert_plan'],
                        berechnung['zinskosten_plan'],
                        berechnung['db2_plan'],
                        vorjahr.get('umsatz', 0),
                        vorjahr.get('db1', 0),
                        vorjahr.get('db2', 0),
                        vorjahr.get('stueck', 0),
                        vorjahr.get('standzeit', 0),
                        vorjahr.get('zinskosten', 0),
                        berechnung['impact']['standzeit'].get('zinskosten_ersparnis', 0),
                        berechnung['impact']['zinskosten'].get('differenz', 0),
                        berechnung['impact']['gesamt'].get('db1_mehr', 0),
                        berechnung['impact']['gesamt'].get('db2_mehr', 0),
                        data.get('status', 'entwurf'),
                        data.get('kommentar'),
                        current_user.username,
                        geschaeftsjahr,
                        standort
                    ))
                else:
                    # Insert
                    cursor.execute("""
                        INSERT INTO gewinnplanung_v2_gw (
                            geschaeftsjahr, standort, status,
                            plan_stueck, plan_bruttoertrag_pro_fzg, plan_variable_kosten_pct,
                            plan_verkaufspreis, plan_standzeit_tage, plan_ek_preis, plan_zinssatz_pct,
                            umsatz_plan, bruttoertrag_plan, variable_kosten_plan,
                            db1_plan, direkte_kosten_plan, lagerwert_plan, zinskosten_plan, db2_plan,
                            vj_umsatz, vj_db1, vj_db2, vj_stueck, vj_standzeit, vj_zinskosten,
                            impact_standzeit_ersparnis, impact_zinskosten_ersparnis,
                            impact_db1_mehr, impact_db2_mehr,
                            erstellt_von, kommentar
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s
                        )
                    """, (
                        geschaeftsjahr, standort, data.get('status', 'entwurf'),
                        planung_data.get('plan_stueck'),
                        planung_data.get('plan_bruttoertrag_pro_fzg'),
                        planung_data.get('plan_variable_kosten_pct'),
                        planung_data.get('plan_verkaufspreis'),
                        planung_data.get('plan_standzeit_tage'),
                        planung_data.get('plan_ek_preis'),
                        planung_data.get('plan_zinssatz_pct', 5.0),
                        berechnung['umsatz_plan'],
                        berechnung['bruttoertrag_plan'],
                        berechnung['variable_kosten_plan'],
                        berechnung['db1_plan'],
                        berechnung['direkte_kosten_plan'],
                        berechnung['lagerwert_plan'],
                        berechnung['zinskosten_plan'],
                        berechnung['db2_plan'],
                        vorjahr.get('umsatz', 0),
                        vorjahr.get('db1', 0),
                        vorjahr.get('db2', 0),
                        vorjahr.get('stueck', 0),
                        vorjahr.get('standzeit', 0),
                        vorjahr.get('zinskosten', 0),
                        berechnung['impact']['standzeit'].get('zinskosten_ersparnis', 0),
                        berechnung['impact']['zinskosten'].get('differenz', 0),
                        berechnung['impact']['gesamt'].get('db1_mehr', 0),
                        berechnung['impact']['gesamt'].get('db2_mehr', 0),
                        current_user.username,
                        data.get('kommentar')
                    ))
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Planung gespeichert',
                    'berechnung': berechnung,
                    'vorjahr': vorjahr
                })
    
    except Exception as e:
        if logger:
            logger.error(f"Fehler in GW-Planung: {str(e)}")
            import traceback
            traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gewinnplanung_v2_gw_api.route('/berechnung', methods=['POST'])
@login_required
def berechnung():
    """
    Berechnet GW-Planung ohne zu speichern (Vorschau).
    """
    try:
        data = request.json
        standort = data.get('standort')
        geschaeftsjahr = data.get('geschaeftsjahr', get_current_geschaeftsjahr())
        planung_data = data.get('planung', {})
        
        # Vorjahreswerte laden
        vorjahr = lade_vorjahr_gw(standort, geschaeftsjahr, None)
        
        # Berechnung durchführen
        berechnung = berechne_gw_planung(planung_data, vorjahr)
        
        return jsonify({
            'success': True,
            'berechnung': berechnung,
            'vorjahr': vorjahr
        })
    
    except Exception as e:
        if logger:
            logger.error(f"Fehler bei Berechnung: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

