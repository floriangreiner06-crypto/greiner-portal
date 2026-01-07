"""
ABTEILUNGSLEITER-PLANUNG Routes - HTML-Templates
=================================================
TAG 165: Routes für Abteilungsleiter-Planung (10 Fragen pro KST)

Routes:
- /planung/abteilungsleiter - Übersicht aller Planungen
- /planung/abteilungsleiter/<bereich>/<standort> - Planungsformular
- /planung/abteilungsleiter/<id> - Planung anzeigen
- /planung/freigabe - Freigabe-Übersicht (für Geschäftsführung)
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
        gj_monat: GJ-Monat (1=Sep, 2=Okt, ..., 12=Aug)
    
    Returns:
        Monatsname (z.B. 'September', 'Januar')
    """
    monatsnamen = [
        '',  # 0 (nicht verwendet)
        'September', 'Oktober', 'November', 'Dezember',  # 1-4
        'Januar', 'Februar', 'März', 'April',  # 5-8
        'Mai', 'Juni', 'Juli', 'August'  # 9-12
    ]
    
    if 1 <= gj_monat <= 12:
        return monatsnamen[gj_monat]
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
                # Wenn bereits eine Planung für Standort 1 existiert, Werte zusammenfassen
                if key in planungen:
                    # Werte zusammenfassen (falls beide existieren)
                    existing = planungen[key]
                    planungen[key] = {
                        'id': existing.get('id'),  # Behalte erste ID
                        'bereich': bereich_key,
                        'standort': standort_key,
                        'status': existing.get('status') or row_to_dict(row).get('status'),
                        'umsatz_basis': (existing.get('umsatz_basis') or 0) + (row_to_dict(row).get('umsatz_basis') or 0),
                        'db1_basis': (existing.get('db1_basis') or 0) + (row_to_dict(row).get('db1_basis') or 0),
                        'umsatz_ziel': (existing.get('umsatz_ziel') or 0) + (row_to_dict(row).get('umsatz_ziel') or 0),
                        'db1_ziel': (existing.get('db1_ziel') or 0) + (row_to_dict(row).get('db1_ziel') or 0),
                        'erstellt_von': existing.get('erstellt_von') or row_to_dict(row).get('erstellt_von'),
                        'erstellt_am': existing.get('erstellt_am') or row_to_dict(row).get('erstellt_am'),
                        'freigegeben_von': existing.get('freigegeben_von') or row_to_dict(row).get('freigegeben_von'),
                        'freigegeben_am': existing.get('freigegeben_am') or row_to_dict(row).get('freigegeben_am')
                    }
                else:
                    planungen[key] = row_to_dict(row)
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
        
        # Bestehende Planung laden (falls vorhanden)
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s
                  AND bereich = %s AND standort = %s
            """, (geschaeftsjahr, monat, bereich, standort))
            
            row = cursor.fetchone()
            if row:
                planung = row_to_dict(row)
    
    except Exception as e:
        flash(f'Fehler beim Laden der Planung: {str(e)}', 'danger')
    
    # Standort-Name
    standort_namen = {
        1: 'Deggendorf',
        2: 'Hyundai DEG',
        3: 'Landau'
    }
    
    # Vorjahres-Referenz laden (für Anzeige im Template)
    vorjahr = {}
    try:
        if AbteilungsleiterPlanungData:
            vorjahr = AbteilungsleiterPlanungData._lade_vorjahr_referenz(
                bereich, standort, monat, geschaeftsjahr
            )
            # Vorjahreswerte in planung-Objekt einfügen (falls nicht vorhanden)
            if planung:
                if not planung.get('vj_stueck'):
                    planung['vj_stueck'] = vorjahr.get('stueck', 0)
                if not planung.get('vj_umsatz'):
                    planung['vj_umsatz'] = vorjahr.get('umsatz', 0)
                if not planung.get('vj_db1'):
                    planung['vj_db1'] = vorjahr.get('db1', 0)
                if not planung.get('vj_standzeit'):
                    planung['vj_standzeit'] = vorjahr.get('standzeit', 0)
            else:
                # Wenn keine Planung vorhanden, planung-Objekt mit VJ-Werten erstellen
                planung = {
                    'vj_stueck': vorjahr.get('stueck', 0),
                    'vj_umsatz': vorjahr.get('umsatz', 0),
                    'vj_db1': vorjahr.get('db1', 0),
                    'vj_standzeit': vorjahr.get('standzeit', 0),
                    'vj_stundensatz': vorjahr.get('stundensatz', 0),
                    'vj_stunden_verkauft': vorjahr.get('stunden_verkauft', 0),
                    'vj_lagerumschlag': vorjahr.get('lagerumschlag', 0),
                    'vj_penner_quote': vorjahr.get('penner_quote', 0),
                    'vj_servicegrad': vorjahr.get('servicegrad', 0)
                }
    except Exception as e:
        print(f"Fehler beim Laden der Vorjahres-Referenz: {str(e)}")
    
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
        monat_abgelaufen=monat_abgelaufen,
        vorjahr=vorjahr
    )


@planung_routes.route('/abteilungsleiter/<int:planung_id>')
@login_required
def planung_anzeigen(planung_id: int):
    """Zeigt eine Planung an (Read-Only)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM abteilungsleiter_planung
                WHERE id = %s
            """, (planung_id,))
            
            planung = cursor.fetchone()
            if not planung:
                flash('Planung nicht gefunden', 'danger')
                return redirect(url_for('abteilungsleiter_planung.uebersicht'))
            
            planung_dict = row_to_dict(planung)
            
            # Standort-Name
            standort_namen = {
                1: 'Deggendorf',
                2: 'Hyundai DEG',
                3: 'Landau'
            }
            
            return render_template(
                'planung/abteilungsleiter_detail.html',
                planung=planung_dict,
                standort_name=standort_namen.get(planung_dict['standort'], f'Standort {planung_dict["standort"]}')
            )
    
    except Exception as e:
        flash(f'Fehler: {str(e)}', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))


@planung_routes.route('/freigabe')
@login_required
def freigabe_uebersicht():
    """
    Freigabe-Übersicht für Geschäftsführung.
    
    Zeigt alle Planungen mit Status 'entwurf' zur Freigabe.
    """
    geschaeftsjahr = request.args.get('geschaeftsjahr', get_gj_from_date())
    monat_param = request.args.get('monat', type=int)
    
    # monat_param ist jetzt immer GJ-Monat (1-12), nicht mehr Kalendermonat
    # GJ-Monat 1 = Sep, 2 = Okt, ..., 5 = Jan, ..., 12 = Aug
    if monat_param and 1 <= monat_param <= 12:
        monat = monat_param
    else:
        monat = get_gj_monat()  # Aktueller GJ-Monat
    
    # Prüfen ob User Freigabe-Berechtigung hat
    if not current_user.can_access_feature('admin'):
        flash('Keine Berechtigung für Freigabe', 'danger')
        return redirect(url_for('abteilungsleiter_planung.uebersicht'))
    
    # Planungen mit Status 'entwurf' laden
    planungen = []
    try:
        with db_session() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, bereich, standort, status,
                       umsatz_basis, db1_basis, umsatz_ziel, db1_ziel,
                       erstellt_von, erstellt_am, kommentar
                FROM abteilungsleiter_planung
                WHERE geschaeftsjahr = %s AND monat = %s
                  AND status = 'entwurf'
                ORDER BY bereich, standort
            """, (geschaeftsjahr, monat))
            
            planungen = [row_to_dict(row) for row in cursor.fetchall()]
    
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

