"""
KST-Ziele API - Kostenstellenbezogene Zielplanung
==================================================
TAG 161: Monatliche Ziele pro Bereich mit IST-Vergleich

Endpunkte:
- /api/kst-ziele/health - Health-Check
- /api/kst-ziele/dashboard - Uebersicht mit IST/SOLL/Hochrechnung
- /api/kst-ziele/ziele - CRUD fuer Ziele
- /api/kst-ziele/status - Taeglicher Status (Daumen hoch/runter)
"""

from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from decimal import Decimal
from api.db_connection import get_db
from api.db_utils import db_session, get_locosoft_connection
from api.aufhol_logik import apply_aufhol_auf_kst_ziel, get_aufhol_beitrag_fuer_kst
from api.unternehmensplan_data import get_current_geschaeftsjahr
from api.kst_planung_bottom_up import get_basis_planung_pro_kst

kst_ziele_bp = Blueprint('kst_ziele', __name__, url_prefix='/api/kst-ziele')

# TAG162: Umlage-Konten für Konzern-Neutralisierung
# Bei Konzern-Ansicht (standort=0) werden diese Konten ausgeblendet,
# da sie sich zwischen den Firmen gegenseitig aufheben sollten.
# Problem: Die Buchung erfolgt erst zum Monatsende, dadurch sind die Daten
# am Monatsanfang verzerrt.
#
# Autohaus Greiner (Stellantis) ERHÄLT: 817051, 827051, 837051, 847051 (+50.000€)
# Auto Greiner (Hyundai) ZAHLT: 498001 (-50.000€)
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]
UMLAGE_KOSTEN_KONTEN = [498001]


def get_gj_from_date(d=None):
    """Ermittelt Geschaeftsjahr aus Datum (Sep-Aug)"""
    if d is None:
        d = date.today()
    if d.month >= 9:
        return f"{d.year}/{str(d.year + 1)[2:]}"
    else:
        return f"{d.year - 1}/{str(d.year)[2:]}"


def get_gj_monat(d=None):
    """Ermittelt GJ-Monat (Sep=1, Okt=2, ..., Aug=12)"""
    if d is None:
        d = date.today()
    if d.month >= 9:
        return d.month - 8  # Sep=1, Okt=2, Nov=3, Dez=4
    else:
        return d.month + 4  # Jan=5, Feb=6, ..., Aug=12


def get_kalendar_monat(gj_monat, gj):
    """Konvertiert GJ-Monat zurueck zu Kalendermonat und Jahr"""
    start_year = int(gj.split('/')[0])
    if gj_monat <= 4:  # Sep-Dez
        return gj_monat + 8, start_year
    else:  # Jan-Aug
        return gj_monat - 4, start_year + 1


@kst_ziele_bp.route('/health')
def health():
    """Health-Check"""
    return jsonify({
        'status': 'ok',
        'service': 'kst-ziele',
        'timestamp': datetime.now().isoformat(),
        'geschaeftsjahr': get_gj_from_date(),
        'gj_monat': get_gj_monat()
    })


@kst_ziele_bp.route('/dashboard')
def dashboard():
    """
    Haupt-Dashboard: IST vs SOLL mit Hochrechnung pro Bereich

    Query-Parameter:
    - gj: Geschaeftsjahr (default: aktuell)
    - monat: GJ-Monat 1-12 (default: aktuell)
    - standort: 0=Alle, 1=DEG, 2=HYU, 3=LAN
    """
    heute = date.today()
    gj = request.args.get('gj', get_gj_from_date())
    gj_monat = int(request.args.get('monat', get_gj_monat()))
    standort = int(request.args.get('standort', 0))

    # Kalendermonat ermitteln
    kal_monat, kal_jahr = get_kalendar_monat(gj_monat, gj)

    try:
        # Datums-Filter
        von = f"{kal_jahr}-{kal_monat:02d}-01"
        bis = f"{kal_jahr}-{kal_monat+1:02d}-01" if kal_monat < 12 else f"{kal_jahr+1}-01-01"

        # Standort-Filter fuer Locosoft
        firma_filter = ""
        # TAG162: Umlage-Filter für Konzern-Ansicht
        umlage_umsatz_filter = ""

        if standort == 0:  # Alle/Konzern - Umlage-Konten ausfiltern!
            umlage_erloese_str = ','.join(map(str, UMLAGE_ERLOESE_KONTEN))
            umlage_umsatz_filter = f"AND nominal_account_number NOT IN ({umlage_erloese_str})"
        elif standort == 1:
            firma_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 1"
        elif standort == 2:
            firma_filter = "AND subsidiary_to_company_ref = 2"
        elif standort == 3:
            firma_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 3"

            # 1. Ziele aus DRIVE Portal laden
        with db_session() as conn:
            cursor = conn.cursor()
            ziele_query = """
                SELECT bereich, umsatz_ziel, db1_ziel, marge_ziel,
                       stueck_ziel, avg_standzeit_ziel, stunden_ziel, auslastung_ziel
                FROM kst_ziele
                WHERE geschaeftsjahr = %s AND monat = %s
                  AND (standort = %s OR standort = 0)
                ORDER BY bereich
            """
            cursor.execute(ziele_query, (gj, gj_monat, standort))
            ziele_rows = cursor.fetchall()

            ziele = {}
            ziele_mit_aufhol = {}  # TAG 165: Ziele mit Aufhol-Logik
            
            # Geschäftsjahr für Aufhol-Logik
            geschaeftsjahr = get_current_geschaeftsjahr()
            
            # TAG 165: Standort für Aufhol-Logik bestimmen
            # Deggendorf = Standort 1+2 kombiniert → 'deggendorf'
            # Landau = Standort 3
            standort_fuer_aufhol = None
            if standort == 0:
                standort_fuer_aufhol = 0  # Alle
            elif standort in [1, 2]:
                standort_fuer_aufhol = 'deggendorf'  # Deggendorf kombiniert (1+2)
            elif standort == 3:
                standort_fuer_aufhol = 3  # Landau
            
            for row in ziele_rows:
                bereich = row['bereich']
                umsatz_ziel_basis = float(row['umsatz_ziel'] or 0)
                db1_ziel_basis = float(row['db1_ziel'] or 0)
                
                # TAG 165: Aufhol-Logik anwenden (standort-spezifisch)
                aufhol_result = apply_aufhol_auf_kst_ziel(
                    umsatz_ziel_basis, 
                    db1_ziel_basis, 
                    geschaeftsjahr, 
                    bereich,
                    standort=standort_fuer_aufhol
                )
                
                ziele[bereich] = {
                    'umsatz_ziel': umsatz_ziel_basis,
                    'db1_ziel': db1_ziel_basis,
                    'marge_ziel': float(row['marge_ziel'] or 0),
                    'stueck_ziel': int(row['stueck_ziel'] or 0) if row['stueck_ziel'] else None,
                    'avg_standzeit_ziel': int(row['avg_standzeit_ziel'] or 0) if row['avg_standzeit_ziel'] else None,
                    'stunden_ziel': float(row['stunden_ziel'] or 0) if row['stunden_ziel'] else None,
                    'auslastung_ziel': float(row['auslastung_ziel'] or 0) if row['auslastung_ziel'] else None
                }
                
                # Ziele mit Aufhol-Logik (für Vergleich)
                ziele_mit_aufhol[bereich] = {
                    'umsatz_ziel': aufhol_result['umsatz_ziel_mit_aufhol'],
                    'db1_ziel': aufhol_result['db1_ziel_mit_aufhol'],
                    'aufhol_beitrag_db1': aufhol_result['aufhol_beitrag_db1'],
                    'aufhol_beitrag_umsatz': aufhol_result['aufhol_beitrag_umsatz']
                }

            # 2. IST-Daten aus loco_journal_accountings (gespiegelt in DRIVE Portal)
            # Umsatz pro Bereich
            # TAG162: umlage_umsatz_filter filtert Umlage-Erlöse bei Konzern-Ansicht aus
            cursor.execute(f"""
                SELECT
                    CASE
                        WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN 'NW'
                        WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN 'GW'
                        WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN 'Teile'
                        WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN 'Werkstatt'
                        WHEN nominal_account_number BETWEEN 860000 AND 869999 THEN 'Sonstige'
                        ELSE 'Andere'
                    END as bereich,
                    SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 800000 AND 889999
                  {firma_filter}
                  {umlage_umsatz_filter}
                GROUP BY bereich
            """, (von, bis))
            umsatz_ist = {r['bereich']: float(r['umsatz'] or 0) for r in cursor.fetchall()}

            # Einsatz pro Bereich
            cursor.execute(f"""
                SELECT
                    CASE
                        WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN 'NW'
                        WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN 'GW'
                        WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN 'Teile'
                        WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN 'Werkstatt'
                        WHEN nominal_account_number BETWEEN 760000 AND 769999 THEN 'Sonstige'
                        ELSE 'Andere'
                    END as bereich,
                    SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 799999
                  {firma_filter}
                GROUP BY bereich
            """, (von, bis))
            einsatz_ist = {r['bereich']: float(r['einsatz'] or 0) for r in cursor.fetchall()}

            # 6. Hochrechnung berechnen - Buchungstage im Monat
            cursor.execute(f"""
                SELECT COUNT(DISTINCT accounting_date) as tage
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 899999
            """, (von, bis))
            tage_mit_daten = cursor.fetchone()['tage'] or 1

        # 3. Locosoft-spezifische Daten (Fahrzeuge, Stunden)
        stueck_ist = {'NW': 0, 'GW': 0}
        stunden_gestempelt = 0
        stunden_verrechnet = 0
        avg_standzeit_ist = 0

        try:
            conn_loco = get_locosoft_connection()
            cursor_loco = conn_loco.cursor()

            # Stueckzahlen NW/GW
            cursor_loco.execute(f"""
                SELECT
                    CASE WHEN dealer_vehicle_type = 'N' THEN 'NW' ELSE 'GW' END as bereich,
                    COUNT(*) as stueck
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                GROUP BY bereich
            """, (von, bis))
            stueck_ist = {r['bereich']: int(r['stueck']) for r in cursor_loco.fetchall()}

            # Werkstatt-Stunden
            cursor_loco.execute(f"""
                SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as stunden_gestempelt
                FROM times
                WHERE start_time >= %s AND start_time < %s
            """, (von, bis))
            row = cursor_loco.fetchone()
            stunden_gestempelt = float(row['stunden_gestempelt'] or 0) if row else 0

            # Verrechnete Stunden
            cursor_loco.execute(f"""
                SELECT COALESCE(SUM(l.time_units), 0) as stunden_verrechnet
                FROM labours l
                JOIN orders o ON l.order_number = o.number
                WHERE o.invoice_date >= %s AND o.invoice_date < %s
                  AND l.is_invoiced = true
            """, (von, bis))
            row = cursor_loco.fetchone()
            stunden_verrechnet = float(row['stunden_verrechnet'] or 0) if row else 0

            # GW Durchschnitts-Standzeit
            cursor_loco.execute("""
                SELECT AVG(CURRENT_DATE - in_arrival_date) as avg_standzeit
                FROM dealer_vehicles
                WHERE out_invoice_date IS NULL
                  AND dealer_vehicle_type = 'G'
                  AND in_arrival_date IS NOT NULL
            """)
            row = cursor_loco.fetchone()
            avg_standzeit_ist = int(row['avg_standzeit'] or 0) if row else 0

            conn_loco.close()
        except Exception as loco_err:
            # Locosoft nicht erreichbar - nur FIBU-Daten verwenden
            print(f"Locosoft-Verbindung fehlgeschlagen: {loco_err}")

        auslastung_ist = (stunden_verrechnet / stunden_gestempelt * 100) if stunden_gestempelt > 0 else 0

        # Werktage im Monat (ca. 22)
        werktage_monat = 22
        # Hochrechnungsfaktor: nur hochrechnen wenn Monat noch nicht voll
        # Wenn Buchungstage >= Werktage, keine Hochrechnung (Faktor = 1)
        if tage_mit_daten >= werktage_monat:
            faktor = 1.0  # Monat ist voll, keine Hochrechnung
        else:
            faktor = werktage_monat / tage_mit_daten if tage_mit_daten > 0 else 1

        # 7. Bereiche zusammenstellen
        bereiche_liste = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
        bereiche = []

        for b in bereiche_liste:
            umsatz = umsatz_ist.get(b, 0)
            einsatz = einsatz_ist.get(b, 0)
            db1 = umsatz - einsatz
            marge = (db1 / umsatz * 100) if umsatz > 0 else 0

            ziel = ziele.get(b, {})
            umsatz_ziel_basis = ziel.get('umsatz_ziel', 0)
            db1_ziel_basis = ziel.get('db1_ziel', 0)
            marge_ziel = ziel.get('marge_ziel', 0)
            
            # TAG 165: Aufhol-Logik - verwende Ziele mit Aufhol
            aufhol_data = ziele_mit_aufhol.get(b, {})
            umsatz_ziel = aufhol_data.get('umsatz_ziel', umsatz_ziel_basis)
            db1_ziel = aufhol_data.get('db1_ziel', db1_ziel_basis)

            # Hochrechnung
            umsatz_prognose = umsatz * faktor
            db1_prognose = db1 * faktor

            # Status: Daumen hoch/runter
            status = 'neutral'
            if db1_ziel > 0:
                if db1_prognose >= db1_ziel:
                    status = 'positiv'  # Daumen hoch
                elif db1_prognose >= db1_ziel * 0.9:
                    status = 'warnung'  # Knapp
                else:
                    status = 'negativ'  # Daumen runter

            bereich_data = {
                'bereich': b,
                'ist': {
                    'umsatz': round(umsatz, 2),
                    'einsatz': round(einsatz, 2),
                    'db1': round(db1, 2),
                    'marge': round(marge, 1)
                },
                'ziel': {
                    'umsatz': umsatz_ziel,
                    'db1': db1_ziel,
                    'marge': marge_ziel,
                    'umsatz_basis': umsatz_ziel_basis,  # TAG 165: Basis-Ziel ohne Aufhol
                    'db1_basis': db1_ziel_basis,  # TAG 165: Basis-Ziel ohne Aufhol
                    'aufhol_beitrag_db1': aufhol_data.get('aufhol_beitrag_db1', 0),  # TAG 165
                    'aufhol_beitrag_umsatz': aufhol_data.get('aufhol_beitrag_umsatz', 0)  # TAG 165
                },
                'prognose': {
                    'umsatz': round(umsatz_prognose, 2),
                    'db1': round(db1_prognose, 2),
                    'erreichung_pct': round((db1_prognose / db1_ziel * 100) if db1_ziel > 0 else 0, 1)
                },
                'status': status
            }

            # Bereichsspezifische KPIs
            if b == 'NW':
                bereich_data['ist']['stueck'] = stueck_ist.get('NW', 0)
                bereich_data['ziel']['stueck'] = ziel.get('stueck_ziel')
                bereich_data['prognose']['stueck'] = int(stueck_ist.get('NW', 0) * faktor)

            elif b == 'GW':
                bereich_data['ist']['stueck'] = stueck_ist.get('GW', 0)
                bereich_data['ist']['avg_standzeit'] = avg_standzeit_ist
                bereich_data['ziel']['stueck'] = ziel.get('stueck_ziel')
                bereich_data['ziel']['avg_standzeit'] = ziel.get('avg_standzeit_ziel')
                bereich_data['prognose']['stueck'] = int(stueck_ist.get('GW', 0) * faktor)

            elif b == 'Werkstatt':
                bereich_data['ist']['stunden'] = round(stunden_verrechnet, 1)
                bereich_data['ist']['auslastung'] = round(auslastung_ist, 1)
                bereich_data['ziel']['stunden'] = ziel.get('stunden_ziel')
                bereich_data['ziel']['auslastung'] = ziel.get('auslastung_ziel')
                bereich_data['prognose']['stunden'] = round(stunden_verrechnet * faktor, 1)

            bereiche.append(bereich_data)

        # 8. Gesamt-Status
        total_db1_ist = sum(umsatz_ist.get(b, 0) - einsatz_ist.get(b, 0) for b in bereiche_liste)
        total_db1_ziel = sum(ziele.get(b, {}).get('db1_ziel', 0) for b in bereiche_liste)
        total_db1_prognose = total_db1_ist * faktor

        gesamt_status = 'neutral'
        if total_db1_ziel > 0:
            erreichung = total_db1_prognose / total_db1_ziel * 100
            if erreichung >= 100:
                gesamt_status = 'positiv'
            elif erreichung >= 90:
                gesamt_status = 'warnung'
            else:
                gesamt_status = 'negativ'

        return jsonify({
            'success': True,
            'geschaeftsjahr': gj,
            'gj_monat': gj_monat,
            'kalender_monat': kal_monat,
            'kalender_jahr': kal_jahr,
            'standort': standort,
            'tage_mit_daten': tage_mit_daten,
            'werktage_monat': werktage_monat,
            'hochrechnung_faktor': round(faktor, 2),
            'bereiche': bereiche,
            'gesamt': {
                'db1_ist': round(total_db1_ist, 2),
                'db1_ziel': round(total_db1_ziel, 2),
                'db1_prognose': round(total_db1_prognose, 2),
                'erreichung_pct': round((total_db1_prognose / total_db1_ziel * 100) if total_db1_ziel > 0 else 0, 1),
                'status': gesamt_status
            },
            'stand': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@kst_ziele_bp.route('/ziele', methods=['GET', 'POST', 'PUT'])
def ziele_crud():
    """
    CRUD fuer Ziele

    GET: Alle Ziele fuer GJ laden
    POST: Neues Ziel anlegen
    PUT: Ziel aktualisieren
    """
    gj = request.args.get('gj', get_gj_from_date())
    standort = int(request.args.get('standort', 0))

    try:
        with db_session() as conn:
            cursor = conn.cursor()

            if request.method == 'GET':
                cursor.execute("""
                    SELECT * FROM kst_ziele
                    WHERE geschaeftsjahr = %s
                      AND (standort = %s OR %s = 0)
                    ORDER BY monat, bereich
                """, (gj, standort, standort))

                ziele = []
                for row in cursor.fetchall():
                    ziele.append({
                        'id': row['id'],
                        'geschaeftsjahr': row['geschaeftsjahr'],
                        'monat': row['monat'],
                        'bereich': row['bereich'],
                        'standort': row['standort'],
                        'umsatz_ziel': float(row['umsatz_ziel'] or 0),
                        'db1_ziel': float(row['db1_ziel'] or 0),
                        'marge_ziel': float(row['marge_ziel'] or 0) if row['marge_ziel'] else None,
                        'stueck_ziel': row['stueck_ziel'],
                        'avg_standzeit_ziel': row['avg_standzeit_ziel'],
                        'stunden_ziel': float(row['stunden_ziel']) if row['stunden_ziel'] else None,
                        'auslastung_ziel': float(row['auslastung_ziel']) if row['auslastung_ziel'] else None,
                        'kommentar': row['kommentar'],
                        'erstellt_von': row['erstellt_von'],
                        'erstellt_am': row['erstellt_am'].isoformat() if row['erstellt_am'] else None
                    })

                return jsonify({
                    'success': True,
                    'geschaeftsjahr': gj,
                    'ziele': ziele
                })

            elif request.method == 'POST':
                data = request.get_json()

                cursor.execute("""
                    INSERT INTO kst_ziele
                    (geschaeftsjahr, monat, bereich, standort,
                     umsatz_ziel, db1_ziel, marge_ziel,
                     stueck_ziel, avg_standzeit_ziel, stunden_ziel, auslastung_ziel,
                     kommentar, erstellt_von)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
                    DO UPDATE SET
                        umsatz_ziel = EXCLUDED.umsatz_ziel,
                        db1_ziel = EXCLUDED.db1_ziel,
                        marge_ziel = EXCLUDED.marge_ziel,
                        stueck_ziel = EXCLUDED.stueck_ziel,
                        avg_standzeit_ziel = EXCLUDED.avg_standzeit_ziel,
                        stunden_ziel = EXCLUDED.stunden_ziel,
                        auslastung_ziel = EXCLUDED.auslastung_ziel,
                        kommentar = EXCLUDED.kommentar,
                        geaendert_am = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    data.get('geschaeftsjahr', gj),
                    data['monat'],
                    data['bereich'],
                    data.get('standort', 0),
                    data.get('umsatz_ziel', 0),
                    data.get('db1_ziel', 0),
                    data.get('marge_ziel'),
                    data.get('stueck_ziel'),
                    data.get('avg_standzeit_ziel'),
                    data.get('stunden_ziel'),
                    data.get('auslastung_ziel'),
                    data.get('kommentar'),
                    data.get('erstellt_von', 'api')
                ))

                new_id = cursor.fetchone()['id']
                conn.commit()

                return jsonify({
                    'success': True,
                    'id': new_id,
                    'message': 'Ziel gespeichert'
                })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@kst_ziele_bp.route('/status')
def tages_status():
    """
    Kompakter Tagesstatus fuer E-Mail-Report

    Liefert: Daumen hoch/runter pro Bereich + Handlungsempfehlungen
    """
    heute = date.today()
    gj = get_gj_from_date()
    gj_monat = get_gj_monat()
    standort = int(request.args.get('standort', 0))

    try:
        # Dashboard-Daten holen (intern)
        with db_session() as conn:
            cursor = conn.cursor()

            kal_monat, kal_jahr = get_kalendar_monat(gj_monat, gj)
            von = f"{kal_jahr}-{kal_monat:02d}-01"
            bis = f"{kal_jahr}-{kal_monat+1:02d}-01" if kal_monat < 12 else f"{kal_jahr+1}-01-01"

            # Ziele laden
            cursor.execute("""
                SELECT bereich, db1_ziel, stueck_ziel, stunden_ziel, auslastung_ziel
                FROM kst_ziele
                WHERE geschaeftsjahr = %s AND monat = %s AND standort = %s
            """, (gj, gj_monat, standort))

            ziele = {r['bereich']: dict(r) for r in cursor.fetchall()}

            # IST-DB1 pro Bereich
            cursor.execute(f"""
                SELECT
                    CASE
                        WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN 'NW'
                        WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN 'GW'
                        WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN 'Teile'
                        WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN 'Werkstatt'
                        ELSE 'Sonstige'
                    END as bereich,
                    SUM(CASE
                        WHEN nominal_account_number BETWEEN 800000 AND 889999 THEN
                            CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END
                        WHEN nominal_account_number BETWEEN 700000 AND 799999 THEN
                            CASE WHEN debit_or_credit = 'S' THEN -posted_value ELSE posted_value END
                        ELSE 0
                    END) / 100.0 as db1
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
                  AND nominal_account_number BETWEEN 700000 AND 899999
                GROUP BY bereich
            """, (von, bis))

            db1_ist = {r['bereich']: float(r['db1'] or 0) for r in cursor.fetchall()}

            # Buchungstage
            cursor.execute(f"""
                SELECT COUNT(DISTINCT accounting_date) as tage
                FROM loco_journal_accountings
                WHERE accounting_date >= %s AND accounting_date < %s
            """, (von, bis))
            tage = cursor.fetchone()['tage'] or 1
            faktor = 22 / tage

            # Status berechnen
            status_liste = []
            empfehlungen = []

            for bereich in ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']:
                ist = db1_ist.get(bereich, 0)
                prognose = ist * faktor
                ziel = ziele.get(bereich, {})
                db1_ziel = float(ziel.get('db1_ziel', 0) or 0)

                if db1_ziel > 0:
                    erreichung = prognose / db1_ziel * 100
                    if erreichung >= 100:
                        status = 'up'
                        icon = '👍'
                    elif erreichung >= 85:
                        status = 'warning'
                        icon = '⚠️'
                    else:
                        status = 'down'
                        icon = '👎'
                else:
                    erreichung = 0
                    status = 'neutral'
                    icon = '➖'

                status_liste.append({
                    'bereich': bereich,
                    'db1_ist': round(ist, 0),
                    'db1_prognose': round(prognose, 0),
                    'db1_ziel': round(db1_ziel, 0),
                    'erreichung_pct': round(erreichung, 0),
                    'status': status,
                    'icon': icon
                })

                # Handlungsempfehlungen
                if status == 'down':
                    if bereich == 'NW':
                        empfehlungen.append(f"NW: Auslieferungen beschleunigen, Pipeline pruefen")
                    elif bereich == 'GW':
                        empfehlungen.append(f"GW: Standzeit-Leichen abbauen, Rabattaktion starten")
                    elif bereich == 'Teile':
                        empfehlungen.append(f"Teile: Werkstatt-Umsatz steigern, Lagerreichweite pruefen")
                    elif bereich == 'Werkstatt':
                        empfehlungen.append(f"Werkstatt: Offene Auftraege abschliessen, Leerlauf reduzieren")

            # Gesamt
            total_ist = sum(s['db1_ist'] for s in status_liste)
            total_prognose = sum(s['db1_prognose'] for s in status_liste)
            total_ziel = sum(s['db1_ziel'] for s in status_liste)

            if total_ziel > 0:
                total_erreichung = total_prognose / total_ziel * 100
                if total_erreichung >= 100:
                    total_status = 'up'
                    total_icon = '👍'
                    total_text = 'ZIEL ERREICHT'
                elif total_erreichung >= 85:
                    total_status = 'warning'
                    total_icon = '⚠️'
                    total_text = 'KNAPP'
                else:
                    total_status = 'down'
                    total_icon = '👎'
                    delta = total_ziel - total_prognose
                    total_text = f'FEHLEN {delta:,.0f} EUR'
            else:
                total_erreichung = 0
                total_status = 'neutral'
                total_icon = '➖'
                total_text = 'KEINE ZIELE'

            return jsonify({
                'success': True,
                'datum': heute.isoformat(),
                'geschaeftsjahr': gj,
                'monat': gj_monat,
                'tag_im_monat': heute.day,
                'bereiche': status_liste,
                'gesamt': {
                    'db1_ist': round(total_ist, 0),
                    'db1_prognose': round(total_prognose, 0),
                    'db1_ziel': round(total_ziel, 0),
                    'erreichung_pct': round(total_erreichung, 0),
                    'status': total_status,
                    'icon': total_icon,
                    'text': total_text
                },
                'empfehlungen': empfehlungen
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@kst_ziele_bp.route('/kumuliert')
def kumuliert():
    """
    Kumulierte Jahres-Uebersicht (YTD)

    Zeigt alle bisherigen Monate im GJ mit Status
    """
    gj = request.args.get('gj', get_gj_from_date())
    standort = int(request.args.get('standort', 0))
    aktueller_monat = get_gj_monat()

    try:
        with db_session() as conn:
            cursor = conn.cursor()

            monate = []
            kum_ist = 0
            kum_ziel = 0

            for m in range(1, aktueller_monat + 1):
                kal_monat, kal_jahr = get_kalendar_monat(m, gj)
                von = f"{kal_jahr}-{kal_monat:02d}-01"
                bis = f"{kal_jahr}-{kal_monat+1:02d}-01" if kal_monat < 12 else f"{kal_jahr+1}-01-01"

                # IST DB1
                cursor.execute(f"""
                    SELECT
                        SUM(CASE WHEN debit_or_credit = 'H' AND nominal_account_number BETWEEN 800000 AND 889999
                            THEN posted_value ELSE 0 END) / 100.0 as umsatz,
                        SUM(CASE WHEN debit_or_credit = 'S' AND nominal_account_number BETWEEN 700000 AND 799999
                            THEN posted_value ELSE 0 END) / 100.0 as einsatz
                    FROM loco_journal_accountings
                    WHERE accounting_date >= %s AND accounting_date < %s
                """, (von, bis))
                row = cursor.fetchone()
                db1_ist = float(row['umsatz'] or 0) - float(row['einsatz'] or 0)

                # Ziel DB1
                cursor.execute("""
                    SELECT SUM(db1_ziel) as db1_ziel
                    FROM kst_ziele
                    WHERE geschaeftsjahr = %s AND monat = %s
                      AND (standort = %s OR standort = 0)
                """, (gj, m, standort))
                db1_ziel = float(cursor.fetchone()['db1_ziel'] or 0)

                kum_ist += db1_ist
                kum_ziel += db1_ziel

                monats_namen = ['Sep', 'Okt', 'Nov', 'Dez', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug']

                monate.append({
                    'monat': m,
                    'name': monats_namen[m-1],
                    'db1_ist': round(db1_ist, 0),
                    'db1_ziel': round(db1_ziel, 0),
                    'kum_ist': round(kum_ist, 0),
                    'kum_ziel': round(kum_ziel, 0),
                    'status': 'up' if db1_ist >= db1_ziel else 'down'
                })

            # Jahres-Prognose
            if aktueller_monat > 0:
                jahres_prognose = kum_ist / aktueller_monat * 12
            else:
                jahres_prognose = 0

            # Jahres-Ziel (alle 12 Monate)
            cursor.execute("""
                SELECT SUM(db1_ziel) as jahres_ziel
                FROM kst_ziele
                WHERE geschaeftsjahr = %s
                  AND (standort = %s OR standort = 0)
            """, (gj, standort))
            jahres_ziel = float(cursor.fetchone()['jahres_ziel'] or 0)

            return jsonify({
                'success': True,
                'geschaeftsjahr': gj,
                'aktueller_monat': aktueller_monat,
                'monate': monate,
                'ytd': {
                    'db1_ist': round(kum_ist, 0),
                    'db1_ziel': round(kum_ziel, 0),
                    'status': 'up' if kum_ist >= kum_ziel else 'down'
                },
                'jahres_prognose': round(jahres_prognose, 0),
                'jahres_ziel': round(jahres_ziel, 0)
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@kst_ziele_bp.route('/planung')
def planung():
    """
    Bottom-Up + Top-Down Planung pro KST (TAG 165)
    
    Zeigt Basis-Planung (Bottom-Up) + Aufhol-Beitrag (Top-Down) getrennt.
    
    Query-Parameter:
    - gj: Geschaeftsjahr (default: aktuell)
    - monat: GJ-Monat 1-12 (default: aktuell)
    - standort: 1=DEG, 2=HYU, 3=LAN (default: 1)
    
    Returns:
        Dict mit Basis/Aufhol/Gesamt pro Bereich
    """
    gj = request.args.get('gj', get_gj_from_date())
    gj_monat = int(request.args.get('monat', get_gj_monat()))
    standort = int(request.args.get('standort', 1))
    
    # Standort für Aufhol-Logik bestimmen
    standort_fuer_aufhol = None
    if standort == 0:
        standort_fuer_aufhol = 0
    elif standort in [1, 2]:
        standort_fuer_aufhol = 'deggendorf'  # Deggendorf kombiniert
    elif standort == 3:
        standort_fuer_aufhol = 3  # Landau
    
    bereiche = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
    result = {
        'geschaeftsjahr': gj,
        'monat': gj_monat,
        'standort': standort,
        'bereiche': {}
    }
    
    try:
        for bereich in bereiche:
            # 1. Basis-Planung (Bottom-Up)
            basis = get_basis_planung_pro_kst(gj, bereich, gj_monat, standort)
            
            # 2. Aufhol-Beitrag (Top-Down)
            aufhol = get_aufhol_beitrag_fuer_kst(gj, bereich, standort=standort_fuer_aufhol)
            
            # 3. Gesamt = Basis + Aufhol
            umsatz_gesamt = basis['umsatz_basis'] + aufhol['aufhol_beitrag_umsatz']
            db1_gesamt = basis['db1_basis'] + aufhol['aufhol_beitrag_db1']
            
            # 4. Pro Mitarbeiter (falls relevant)
            pro_mitarbeiter = {}
            if bereich == 'Werkstatt' and basis['anzahl_mitarbeiter'] > 0:
                pro_mitarbeiter = {
                    'umsatz': round(umsatz_gesamt / basis['anzahl_mitarbeiter'], 2),
                    'stunden': basis['stunden_basis'] // basis['anzahl_mitarbeiter'] if basis['stunden_basis'] > 0 else 0
                }
            elif bereich in ['NW', 'GW'] and basis['anzahl_mitarbeiter'] > 0:
                pro_mitarbeiter = {
                    'umsatz': round(umsatz_gesamt / basis['anzahl_mitarbeiter'], 2),
                    'stueck': basis['stueck_basis'] // basis['anzahl_mitarbeiter'] if basis['stueck_basis'] > 0 else 0
                }
            
            result['bereiche'][bereich] = {
                'basis': {
                    'umsatz': basis['umsatz_basis'],
                    'db1': basis['db1_basis'],
                    'stueck': basis.get('stueck_basis', 0),
                    'stunden': basis.get('stunden_basis', 0),
                    'anzahl_mitarbeiter': basis['anzahl_mitarbeiter']
                },
                'aufhol': {
                    'umsatz': aufhol['aufhol_beitrag_umsatz'],
                    'db1': aufhol['aufhol_beitrag_db1'],
                    'gap_jahr': aufhol['gap_jahr'],
                    'monate_verbleibend': aufhol['monate_verbleibend']
                },
                'gesamt': {
                    'umsatz': round(umsatz_gesamt, 2),
                    'db1': round(db1_gesamt, 2),
                    'stueck': basis.get('stueck_basis', 0),
                    'stunden': basis.get('stunden_basis', 0)
                },
                'pro_mitarbeiter': pro_mitarbeiter,
                'parameter': basis['parameter']
            }
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
