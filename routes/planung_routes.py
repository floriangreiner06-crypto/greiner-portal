"""
ABTEILUNGSLEITER-PLANUNG Routes - HTML-Templates
=================================================
TAG 165: Routes für Abteilungsleiter-Planung (10 Fragen pro KST)

Routes:
- /planung/abteilungsleiter - Übersicht aller Planungen
- /planung/abteilungsleiter/<bereich>/<standort> - Planungsformular
- /planung/abteilungsleiter/<id> - Planung anzeigen
- /planung/freigabe - Freigabe-Übersicht (für Geschäftsführung)
- /planung/gesamtplanung - Gesamtplanungsansicht (alle KST, alle Betriebe)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date
from api.db_utils import db_session, row_to_dict
from psycopg2.extras import RealDictCursor

# Optional imports (können fehlen)
try:
    from api.abteilungsleiter_planung_data import AbteilungsleiterPlanungData
except ImportError:
    AbteilungsleiterPlanungData = None

try:
    from api.unternehmensplan_data import get_current_geschaeftsjahr
except ImportError:
    def get_current_geschaeftsjahr():
        from datetime import date
        d = date.today()
        if d.month >= 9:
            return f"{d.year}/{str(d.year + 1)[2:]}"
        else:
            return f"{d.year - 1}/{str(d.year)[2:]}"

planung_routes = Blueprint('abteilungsleiter_planung', __name__, url_prefix='/planung')


def get_gj_from_date(d=None):
    """Ermittelt Geschaeftsjahr aus Datum (Sep-Aug)"""
    if d is None:
        d = date.today()
    if d.month >= 9:
        return f"{d.year}/{str(d.year + 1)[2:]}"
    else:
        return f"{d.year - 1}/{str(d.year)[2:]}"


def get_kalendar_monat():
    """Gibt aktuellen Kalendermonat zurück (1-12)"""
    return date.today().month


def get_gj_monat(d=None):
    """Ermittelt GJ-Monat (Sep=1, Okt=2, ..., Aug=12)"""
    if d is None:
        d = date.today()
    if d.month >= 9:
        return d.month - 8  # Sep=1, Okt=2, Nov=3, Dez=4
    else:
        return d.month + 4  # Jan=5, Feb=6, ..., Aug=12


def kalender_zu_gj_monat(kal_monat: int, geschaeftsjahr: str) -> int:
    """
    Konvertiert Kalendermonat zu GJ-Monat.
    
    Args:
        kal_monat: Kalendermonat (1-12)
        geschaeftsjahr: z.B. '2025/26'
    
    Returns:
        GJ-Monat (1=Sep, 2=Okt, ..., 12=Aug)
    """
    start_jahr = int(geschaeftsjahr.split('/')[0])
    
    if kal_monat >= 9:  # Sep-Dez
        if kal_monat == 9:
            return 1  # September = GJ-Monat 1
        elif kal_monat == 10:
            return 2  # Oktober = GJ-Monat 2
        elif kal_monat == 11:
            return 3  # November = GJ-Monat 3
        elif kal_monat == 12:
            return 4  # Dezember = GJ-Monat 4
    else:  # Jan-Aug
        if kal_monat == 1:
            return 5  # Januar = GJ-Monat 5
        elif kal_monat == 2:
            return 6  # Februar = GJ-Monat 6
        elif kal_monat == 3:
            return 7  # März = GJ-Monat 7
        elif kal_monat == 4:
            return 8  # April = GJ-Monat 8
        elif kal_monat == 5:
            return 9  # Mai = GJ-Monat 9
        elif kal_monat == 6:
            return 10  # Juni = GJ-Monat 10
        elif kal_monat == 7:
            return 11  # Juli = GJ-Monat 11
        elif kal_monat == 8:
            return 12  # August = GJ-Monat 12
    
    return 1  # Fallback


def gj_monat_zu_name(gj_monat: int) -> str:
    """
    Konvertiert GJ-Monat zu Monatsname.
    
    Args:
        gj_monat: GJ-Monat (1-12)
    
    Returns:
        Monatsname (z.B. 'September', 'Januar')
    """
    monate = [
        'September', 'Oktober', 'November', 'Dezember',
        'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August'
    ]
    
    if 1 <= gj_monat <= 12:
        return monate[gj_monat - 1]
    
    return f'Monat {gj_monat}'


@planung_routes.route('/abteilungsleiter')
@planung_routes.route('/abteilungsleiter/')
@login_required
def uebersicht():
    """
    Übersicht aller Planungen.
    
    Query-Params:
        - geschaeftsjahr: z.B. '2025/26'
        - monat: 1-12 (GJ-Monat: 1=Sep, 2=Okt, ..., 5=Jan, ..., 12=Aug)
        - standort: 1, 2, oder 3
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    monat_param = request.args.get('monat', type=int)
    
    # monat_param ist jetzt immer GJ-Monat (1-12), nicht mehr Kalendermonat
    # GJ-Monat 1 = Sep, 2 = Okt, ..., 5 = Jan, ..., 12 = Aug
    if monat_param and 1 <= monat_param <= 12:
        monat = monat_param
    else:
        monat = get_gj_monat()  # Aktueller GJ-Monat
    standort = request.args.get('standort', type=int)
    
    # Bereiche
    bereiche = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
    
    # Standorte: Für Teile und Werkstatt nur Deggendorf (Standort 1), nicht Hyundai DEG (Standort 2)
    standorte = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    # Für Teile und Werkstatt: Nur Standort 1 (Deggendorf) anzeigen, Standort 2 (Hyundai DEG) ausblenden
    standorte_fuer_bereich = {}
    for bereich_key in bereiche:
        if bereich_key in ['Teile', 'Werkstatt']:
            # Nur Deggendorf (1) und Landau (3), nicht Hyundai DEG (2)
            standorte_fuer_bereich[bereich_key] = {1: 'Deggendorf', 3: 'Landau'}
        else:
            # Alle Standorte
            standorte_fuer_bereich[bereich_key] = standorte
    
    # Planungen laden
    planungen = {}
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT id, bereich, standort, status,
                       umsatz_basis, db1_basis, umsatz_ziel, db1_ziel,
                       erstellt_von, erstellt_am, freigegeben_von, freigegeben_am
                FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s
            """
            params = [geschaeftsjahr, monat]
            
            if standort:
                query += " AND standort = %s"
                params.append(standort)
            
            query += " ORDER BY bereich, standort"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                bereich_key = row['bereich']
                standort_key = row['standort']
                
                # Für Teile und Werkstatt: Standort 2 (Hyundai DEG) auf Standort 1 (Deggendorf) mappen
                if bereich_key in ['Teile', 'Werkstatt'] and standort_key == 2:
                    standort_key = 1  # Hyundai DEG -> Deggendorf
                
                key = f"{bereich_key}_{standort_key}"
                row_dict = row_to_dict(row)
                
                # datetime-Objekte zu Strings konvertieren (für Jinja2)
                if row_dict.get('erstellt_am') and hasattr(row_dict['erstellt_am'], 'strftime'):
                    row_dict['erstellt_am'] = row_dict['erstellt_am'].strftime('%Y-%m-%d')
                if row_dict.get('freigegeben_am') and hasattr(row_dict['freigegeben_am'], 'strftime'):
                    row_dict['freigegeben_am'] = row_dict['freigegeben_am'].strftime('%Y-%m-%d')
                
                # Wenn bereits eine Planung für Standort 1 existiert, Werte zusammenfassen
                if key in planungen:
                    # Werte zusammenfassen (falls beide existieren)
                    existing = planungen[key]
                    planungen[key] = {
                        'id': existing.get('id'),  # Behalte erste ID
                        'bereich': bereich_key,
                        'standort': standort_key,
                        'status': existing.get('status') or row_dict.get('status'),
                        'umsatz_basis': (existing.get('umsatz_basis') or 0) + (row_dict.get('umsatz_basis') or 0),
                        'db1_basis': (existing.get('db1_basis') or 0) + (row_dict.get('db1_basis') or 0),
                        'umsatz_ziel': (existing.get('umsatz_ziel') or 0) + (row_dict.get('umsatz_ziel') or 0),
                        'db1_ziel': (existing.get('db1_ziel') or 0) + (row_dict.get('db1_ziel') or 0),
                        'erstellt_von': existing.get('erstellt_von') or row_dict.get('erstellt_von'),
                        'erstellt_am': existing.get('erstellt_am') or row_dict.get('erstellt_am'),
                        'freigegeben_von': existing.get('freigegeben_von') or row_dict.get('freigegeben_von'),
                        'freigegeben_am': existing.get('freigegeben_am') or row_dict.get('freigegeben_am')
                    }
                else:
                    planungen[key] = row_dict
                    planungen[key]['standort'] = standort_key  # Standort auf 1 mappen
    
    except Exception as e:
        flash(f'Fehler beim Laden der Planungen: {str(e)}', 'danger')
    
    # Monatsname für Anzeige
    monat_name = gj_monat_zu_name(monat)
    
    return render_template(
        'planung/abteilungsleiter_uebersicht.html',
        geschaeftsjahr=geschaeftsjahr,
        monat=monat,
        monat_name=monat_name,
        standort=standort,
        bereiche=bereiche,
        standorte=standorte,
        standorte_fuer_bereich=standorte_fuer_bereich,
        planungen=planungen
    )


@planung_routes.route('/abteilungsleiter/<bereich>/<int:standort>')
@login_required
def planungsformular(bereich: str, standort: int):
    """
    Planungsformular für einen Bereich und Standort.
    
    Args:
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        standort: 1, 2, oder 3
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    monat_param = request.args.get('monat', type=int)
    
    # monat_param ist jetzt immer GJ-Monat (1-12), nicht mehr Kalendermonat
    # GJ-Monat 1 = Sep, 2 = Okt, ..., 5 = Jan, ..., 12 = Aug
    if monat_param and 1 <= monat_param <= 12:
        monat = monat_param
    else:
        monat = get_gj_monat()  # Aktueller GJ-Monat
    
    # Validierung
    if bereich not in ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']:
        flash('Ungültiger Bereich', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))
    
    if standort not in [1, 2, 3]:
        flash('Ungültiger Standort', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))
    
    # Bestehende Planung laden (falls vorhanden)
    planung = None
    ist_werte = None
    monat_abgelaufen = False
    
    try:
        from api.abteilungsleiter_planung_data import ist_monat_abgelaufen, lade_ist_werte_fuer_monat
        
        # Prüfen ob Monat bereits abgelaufen
        monat_abgelaufen = ist_monat_abgelaufen(geschaeftsjahr, monat)
        
        # Wenn abgelaufen: IST-Werte laden
        if monat_abgelaufen:
            ist_werte = lade_ist_werte_fuer_monat(
                geschaeftsjahr, monat, bereich, standort
            )
        
        # Bestehende Planung aus DB laden
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s AND bereich = %s AND standort = %s
            """, (geschaeftsjahr, monat, bereich, standort))
            
            row = cursor.fetchone()
            if row:
                planung = row_to_dict(row)
    
    except Exception as e:
        flash(f'Fehler beim Laden der Planung: {str(e)}', 'danger')
    
    # Vorjahres-Referenz laden
    # TAG 169: Für NW/GW auch Jahreswerte laden (ganzes Geschäftsjahr)
    vorjahr = None
    vorjahr_jahr = None  # Vorjahreswerte für ganzes Geschäftsjahr
    try:
        if AbteilungsleiterPlanungData:
            # Monatswerte laden (für Vergleich)
            vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
                bereich, standort, monat, geschaeftsjahr
            )
            
            # Für NW/GW: Auch Jahreswerte laden (ganzes Geschäftsjahr)
            if bereich in ['NW', 'GW']:
                vorjahr_jahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
                    bereich, standort, None, geschaeftsjahr  # monat=None = ganzes Jahr
                )
            
            # Vorjahreswerte in Planung-Objekt übernehmen (für Template)
            # WICHTIG: Auch wenn keine Planung existiert, Vorjahreswerte für Template verfügbar machen
            # Planung-Objekt erstellen falls nicht vorhanden
            if not planung:
                planung = {}
            
            if vorjahr:
                # Gemeinsame Vorjahreswerte für alle Bereiche (Monat)
                planung['vj_umsatz'] = vorjahr.get('umsatz', 0)
                planung['vj_db1'] = vorjahr.get('db1', 0)
                planung['vj_db2'] = vorjahr.get('db2', 0)
                
                # Bereichs-spezifische Vorjahreswerte
                if bereich in ['NW', 'GW']:
                    planung['vj_stueck'] = vorjahr.get('stueck', 0)
                    planung['vj_standzeit'] = vorjahr.get('standzeit', 0)
            
            # Jahreswerte (ganzes Geschäftsjahr) - IMMER für NW/GW laden
            if bereich in ['NW', 'GW']:
                if vorjahr_jahr:
                    planung['vj_umsatz_jahr'] = vorjahr_jahr.get('umsatz', 0)
                    planung['vj_db1_jahr'] = vorjahr_jahr.get('db1', 0)
                    planung['vj_db2_jahr'] = vorjahr_jahr.get('db2', 0)
                    planung['vj_stueck_jahr'] = vorjahr_jahr.get('stueck', 0)
                    planung['vj_standzeit_jahr'] = vorjahr_jahr.get('standzeit', 0)
                else:
                    # Fallback: Wenn vorjahr_jahr None ist, setze auf 0
                    planung['vj_umsatz_jahr'] = 0
                    planung['vj_db1_jahr'] = 0
                    planung['vj_db2_jahr'] = 0
                    planung['vj_stueck_jahr'] = 0
                    planung['vj_standzeit_jahr'] = 0
            
            if vorjahr:
                if bereich == 'Werkstatt':
                    planung['vj_anzahl_mechaniker'] = vorjahr.get('anzahl_mechaniker', 0)
                    planung['vj_avg_aw_pro_auftrag'] = vorjahr.get('avg_aw_pro_auftrag', 0)
                    planung['vj_durchlaufzeit_tage'] = vorjahr.get('durchlaufzeit_tage', 0)
                    planung['vj_wiederkehrrate'] = vorjahr.get('wiederkehrrate', 0)
                    planung['vj_produktivitaet'] = vorjahr.get('produktivitaet', 0)
                    planung['vj_leistungsgrad'] = vorjahr.get('leistungsgrad', 0)
                    planung['vj_stundensatz'] = vorjahr.get('stundensatz', 0)
                elif bereich == 'Teile':
                    planung['vj_lagerumschlag'] = vorjahr.get('lagerumschlag', 0)
                    planung['vj_penner_quote'] = vorjahr.get('penner_quote', 0)
                    planung['vj_servicegrad'] = vorjahr.get('servicegrad', 0)
    except Exception as e:
        flash(f'Fehler beim Laden der Vorjahres-Referenz: {str(e)}', 'warning')
        import traceback
        traceback.print_exc()
    
    # Standort-Name
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    # Monatsname für Anzeige
    monat_name = gj_monat_zu_name(monat)
    
    return render_template(
        'planung/abteilungsleiter_formular.html',
        geschaeftsjahr=geschaeftsjahr,
        monat=monat,
        monat_name=monat_name,
        bereich=bereich,
        standort=standort,
        standort_name=standort_namen.get(standort, f'Standort {standort}'),
        planung=planung,
        ist_werte=ist_werte,
        vorjahr=vorjahr if vorjahr else {},  # Leeres Dict falls None
        monat_abgelaufen=monat_abgelaufen
    )


@planung_routes.route('/freigabe')
@login_required
def freigabe_uebersicht():
    """
    Freigabe-Übersicht für Geschäftsführung.
    Zeigt alle Planungen mit Status 'eingereicht' oder 'entwurf'.
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    monat_param = request.args.get('monat', type=int)
    
    # monat_param ist jetzt immer GJ-Monat (1-12)
    if monat_param and 1 <= monat_param <= 12:
        monat = monat_param
    else:
        monat = get_gj_monat()
    
    standort = request.args.get('standort', type=int)
    
    # Planungen laden
    planungen = []
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT id, bereich, standort, status,
                       umsatz_basis, db1_basis, umsatz_ziel, db1_ziel,
                       erstellt_von, erstellt_am, kommentar
                FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s
                  AND status IN ('entwurf', 'eingereicht')
            """
            params = [geschaeftsjahr, monat]
            
            if standort:
                query += " AND standort = %s"
                params.append(standort)
            
            query += " ORDER BY bereich, standort"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                planungen.append(row_to_dict(row))
    
    except Exception as e:
        flash(f'Fehler beim Laden der Planungen: {str(e)}', 'danger')
    
    # Standort-Namen
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    # Monatsname für Anzeige
    monat_name = gj_monat_zu_name(monat)
    
    return render_template(
        'planung/freigabe_uebersicht.html',
        geschaeftsjahr=geschaeftsjahr,
        monat=monat,
        monat_name=monat_name,
        standort=standort,
        planungen=planungen,
        standort_namen=standort_namen
    )


@planung_routes.route('/abteilungsleiter/jahresplanung/<bereich>/<int:standort>')
@login_required
def jahresplanung(bereich: str, standort: int):
    """
    Jahresplanung-Ansicht für einen Bereich und Standort.
    
    Zeigt alle 12 GJ-Monate mit:
    - Planungswerten pro Monat
    - Kumulierten Werten (YTD)
    - Vorjahreswerten pro Monat
    - Kumulierten Vorjahreswerten
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    
    # Validierung
    if bereich not in ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']:
        flash('Ungültiger Bereich', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))
    
    if standort not in [1, 2, 3]:
        flash('Ungültiger Standort', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))
    
    # Jahresplanung laden
    jahresplanung_data = None
    try:
        if AbteilungsleiterPlanungData:
            jahresplanung_data = AbteilungsleiterPlanungData.lade_jahresplanung(
                geschaeftsjahr, bereich, standort
            )
    except Exception as e:
        flash(f'Fehler beim Laden der Jahresplanung: {str(e)}', 'danger')
        jahresplanung_data = {
            'monate': [],
            'kumuliert': {'umsatz': 0, 'db1': 0, 'db2': 0, 'stueck': 0},
            'kumuliert_vj': {'umsatz': 0, 'db1': 0, 'db2': 0, 'stueck': 0}
        }
    
    # Standort-Name
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    return render_template(
        'planung/jahresplanung.html',
        geschaeftsjahr=geschaeftsjahr,
        bereich=bereich,
        standort=standort,
        standort_name=standort_namen.get(standort, f'Standort {standort}'),
        jahresplanung=jahresplanung_data
    )


@planung_routes.route('/stundensatz-kalkulation')
@login_required
def stundensatz_kalkulation():
    """
    Stundensatz-Kalkulation Ansicht.
    
    Zeigt BWA-Daten für Werkstatt-Stundensatz-Kalkulation.
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr')
    standort = request.args.get('standort', type=int)
    
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    return render_template(
        'planung/stundensatz_kalkulation.html',
        geschaeftsjahr=geschaeftsjahr,
        standort=standort,
        standort_namen=standort_namen
    )


@planung_routes.route('/gesamtplanung')
@login_required
def gesamtplanung():
    """
    Gesamtplanungsansicht für alle Kostenstellen und Betriebe.
    
    Zeigt aggregierte Planungswerte mit:
    - Filterung nach Geschäftsjahr, Monat, Standort, Bereich
    - Gewinnberechnung (DB2, Betriebsergebnis)
    - Gruppierung nach Bereich und Standort
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    monat_param = request.args.get('monat', type=int)
    standort_filter = request.args.get('standort', type=int)
    bereich_filter = request.args.get('bereich', type=str)
    
    # monat_param ist GJ-Monat (1-12)
    if monat_param and 1 <= monat_param <= 12:
        monat = monat_param
    else:
        monat = get_gj_monat()
    
    # Planungen aggregieren
    gesamtwerte = {
        'umsatz': 0,
        'db1': 0,
        'db2': 0,
        'stueck': 0
    }
    
    # Gruppierung nach Bereich und Standort
    planungen_gruppiert = {}
    
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    bereich,
                    standort,
                    SUM(COALESCE(umsatz_ziel, 0)) as umsatz,
                    SUM(COALESCE(db1_ziel, 0)) as db1,
                    SUM(COALESCE(db2_ziel, 0)) as db2,
                    SUM(COALESCE(plan_stueck, 0)) as stueck,
                    COUNT(*) as anzahl_planungen
                FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s
                  AND status = 'freigegeben'
            """
            params = [geschaeftsjahr, monat]
            
            if standort_filter:
                query += " AND standort = %s"
                params.append(standort_filter)
            
            if bereich_filter:
                query += " AND bereich = %s"
                params.append(bereich_filter)
            
            query += """
                GROUP BY bereich, standort
                ORDER BY bereich, standort
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                r = row_to_dict(row)
                bereich = r['bereich']
                standort = r['standort']
                
                # Für Teile und Werkstatt: Standort 2 auf Standort 1 mappen
                if bereich in ['Teile', 'Werkstatt'] and standort == 2:
                    standort = 1
                
                key = f"{bereich}_{standort}"
                
                if key in planungen_gruppiert:
                    # Werte zusammenfassen
                    existing = planungen_gruppiert[key]
                    planungen_gruppiert[key] = {
                        'bereich': bereich,
                        'standort': standort,
                        'umsatz': existing['umsatz'] + float(r['umsatz'] or 0),
                        'db1': existing['db1'] + float(r['db1'] or 0),
                        'db2': existing['db2'] + float(r['db2'] or 0),
                        'stueck': existing['stueck'] + int(r['stueck'] or 0),
                        'anzahl_planungen': existing['anzahl_planungen'] + int(r['anzahl_planungen'] or 0)
                    }
                else:
                    planungen_gruppiert[key] = {
                        'bereich': bereich,
                        'standort': standort,
                        'umsatz': float(r['umsatz'] or 0),
                        'db1': float(r['db1'] or 0),
                        'db2': float(r['db2'] or 0),
                        'stueck': int(r['stueck'] or 0),
                        'anzahl_planungen': int(r['anzahl_planungen'] or 0)
                    }
                
                # Gesamtwerte
                gesamtwerte['umsatz'] += float(r['umsatz'] or 0)
                gesamtwerte['db1'] += float(r['db1'] or 0)
                gesamtwerte['db2'] += float(r['db2'] or 0)
                gesamtwerte['stueck'] += int(r['stueck'] or 0)
    
    except Exception as e:
        flash(f'Fehler beim Laden der Gesamtplanung: {str(e)}', 'danger')
    
    # Indirekte Kosten aus BWA laden
    indirekte_kosten = 0
    direkte_kosten = 0
    try:
        from api.db_connection import convert_placeholders, get_locosoft_connection
        
        # GJ-Monat zu Kalendermonat konvertieren
        gj_start_jahr = int(geschaeftsjahr.split('/')[0])
        if monat <= 4:  # Sep-Dez
            kal_monat = monat + 8
            kal_jahr = gj_start_jahr
        else:  # Jan-Aug
            kal_monat = monat - 4
            kal_jahr = gj_start_jahr + 1
        
        # Datum für Monat
        datum_von = f"{kal_jahr}-{kal_monat:02d}-01"
        if kal_monat == 12:
            datum_bis = f"{kal_jahr+1}-01-01"
        else:
            datum_bis = f"{kal_jahr}-{kal_monat+1:02d}-01"
        
        # Filter bauen (abhängig von Standort-Filter)
        # WICHTIG: Indirekte Kosten haben 5. Ziffer = '0' (Gemeinkosten), daher kein Endziffer-Filter
        # Direkte Kosten haben Endziffer 1-7, aber für Gesamtplanung ignorieren wir das
        guv_filter = "AND (posting_text IS NULL OR posting_text NOT LIKE '%%G&V-Abschluss%%')"
        
        if standort_filter:
            # Einzelner Standort
            if standort_filter == 1:
                # Deggendorf: Stellantis (subsidiary=1) + Hyundai (subsidiary=2)
                firma_filter_kosten = "AND (subsidiary_to_company_ref = 1 OR subsidiary_to_company_ref = 2)"
            elif standort_filter == 2:
                # Hyundai DEG: Nur Hyundai
                firma_filter_kosten = "AND subsidiary_to_company_ref = 2"
            elif standort_filter == 3:
                # Landau: Nur Stellantis
                firma_filter_kosten = "AND subsidiary_to_company_ref = 1"
            else:
                firma_filter_kosten = ""
        else:
            # Alle Standorte: Alle Firmen
            firma_filter_kosten = ""
        
        # Indirekte Kosten laden
        with get_locosoft_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND (
                    (nominal_account_number BETWEEN 400000 AND 499999
                     AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                    OR (nominal_account_number BETWEEN 424000 AND 424999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR (nominal_account_number BETWEEN 438000 AND 438999
                        AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                    OR nominal_account_number BETWEEN 498000 AND 499999
                    OR (nominal_account_number BETWEEN 891000 AND 896999
                        AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
                  )
                  {firma_filter_kosten}
                  {guv_filter}
            """), (datum_von, datum_bis))
            
            row = cursor.fetchone()
            if row:
                indirekte_kosten = float(row[0] or 0)
            
            # Direkte Kosten laden (für DB3)
            cursor.execute(convert_placeholders(f"""
                SELECT COALESCE(SUM(
                    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
                )/100.0, 0) as wert
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
                  AND nominal_account_number BETWEEN 400000 AND 489999
                  AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
                  AND NOT (
                    nominal_account_number BETWEEN 415100 AND 415199
                    OR nominal_account_number BETWEEN 424000 AND 424999
                    OR nominal_account_number BETWEEN 435500 AND 435599
                    OR nominal_account_number BETWEEN 438000 AND 438999
                    OR nominal_account_number BETWEEN 455000 AND 456999
                    OR nominal_account_number BETWEEN 487000 AND 487099
                    OR nominal_account_number BETWEEN 491000 AND 497999
                  )
                  {firma_filter_kosten}
                  {guv_filter}
            """), (datum_von, datum_bis))
            
            row = cursor.fetchone()
            if row:
                direkte_kosten = float(row[0] or 0)
    
    except Exception as e:
        flash(f'Fehler beim Laden der indirekten Kosten: {str(e)}', 'warning')
        # Fallback: Näherung
        indirekte_kosten = gesamtwerte['db2'] * 0.1
        direkte_kosten = 0
    
    # Gewinnberechnung
    # DB3 = DB2 - direkte Kosten
    db3 = gesamtwerte['db2'] - direkte_kosten
    # Betriebsergebnis = DB3 - indirekte Kosten
    betriebsergebnis = db3 - indirekte_kosten
    
    # Standort-Namen
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    # Bereichs-Namen
    bereich_namen = {
        'NW': 'Neuwagen',
        'GW': 'Gebrauchtwagen',
        'Teile': 'Teile',
        'Werkstatt': 'Werkstatt',
        'Sonstige': 'Sonstige'
    }
    
    # Monatsname
    monat_name = gj_monat_zu_name(monat)
    
    return render_template(
        'planung/gesamtplanung.html',
        geschaeftsjahr=geschaeftsjahr,
        monat=monat,
        monat_name=monat_name,
        standort_filter=standort_filter,
        bereich_filter=bereich_filter,
        planungen_gruppiert=planungen_gruppiert,
        gesamtwerte=gesamtwerte,
        direkte_kosten=direkte_kosten,
        indirekte_kosten=indirekte_kosten,
        db3=db3,
        betriebsergebnis=betriebsergebnis,
        standort_namen=standort_namen,
        bereich_namen=bereich_namen
    )
