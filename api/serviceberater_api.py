#!/usr/bin/env python3
"""
API: Serviceberater Controlling
================================
TEK-basiertes Controlling für Serviceberater

Endpoints:
- GET /api/serviceberater/uebersicht - Alle SB mit Umsatz/Ziel
- GET /api/serviceberater/<ma_id> - Detail eines SB
- GET /api/serviceberater/wettbewerb - Aktiver Verkaufswettbewerb
- GET /api/serviceberater/tek-config - TEK-Konfiguration

Datenquellen:
- Locosoft PostgreSQL: invoices (Rechnungen)
- SQLite: employees (MA-Namen), tek_config
"""

from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import calendar

# Zentrale DB-Utilities (TAG117, TAG136: PostgreSQL-kompatibel)
from api.db_utils import get_locosoft_connection, get_db, locosoft_session, row_to_dict


# ============================================================
# WERKTAGE-BERECHNUNG
# ============================================================

# Bayerische Feiertage 2025
FEIERTAGE_2025 = [
    datetime(2025, 1, 1),    # Neujahr
    datetime(2025, 1, 6),    # Heilige Drei Könige
    datetime(2025, 4, 18),   # Karfreitag
    datetime(2025, 4, 21),   # Ostermontag
    datetime(2025, 5, 1),    # Tag der Arbeit
    datetime(2025, 5, 29),   # Christi Himmelfahrt
    datetime(2025, 6, 9),    # Pfingstmontag
    datetime(2025, 6, 19),   # Fronleichnam
    datetime(2025, 8, 15),   # Mariä Himmelfahrt
    datetime(2025, 10, 3),   # Tag der Deutschen Einheit
    datetime(2025, 11, 1),   # Allerheiligen
    datetime(2025, 12, 25),  # 1. Weihnachtstag
    datetime(2025, 12, 26),  # 2. Weihnachtstag
]


def get_werktage(start_date, end_date, include_end=False):
    """
    Berechnet Werktage zwischen zwei Daten (Mo-Fr, ohne Feiertage)

    Args:
        start_date: Startdatum (datetime oder str YYYY-MM-DD)
        end_date: Enddatum (datetime oder str YYYY-MM-DD)
        include_end: Ob Enddatum inkludiert werden soll

    Returns:
        int: Anzahl Werktage
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    if not include_end:
        end_date = end_date - timedelta(days=1)

    werktage = 0
    current = start_date

    while current <= end_date:
        # Mo-Fr (0-4) und kein Feiertag
        if current.weekday() < 5 and current not in FEIERTAGE_2025:
            werktage += 1
        current += timedelta(days=1)

    return werktage


def get_werktage_monat(jahr, monat):
    """
    Berechnet Werktage im gesamten Monat

    Returns:
        dict: {gesamt, vergangen, verbleibend, fortschritt_prozent}
    """
    erster_tag = datetime(jahr, monat, 1)
    letzter_tag = datetime(jahr, monat, calendar.monthrange(jahr, monat)[1])
    heute = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    werktage_gesamt = get_werktage(erster_tag, letzter_tag, include_end=True)

    # Wenn aktueller Monat: bis heute berechnen
    if heute.year == jahr and heute.month == monat:
        werktage_vergangen = get_werktage(erster_tag, heute, include_end=True)
        werktage_verbleibend = werktage_gesamt - werktage_vergangen
    else:
        # Vergangener Monat: alle Werktage vergangen
        werktage_vergangen = werktage_gesamt
        werktage_verbleibend = 0

    fortschritt = (werktage_vergangen / werktage_gesamt * 100) if werktage_gesamt > 0 else 100

    return {
        'gesamt': werktage_gesamt,
        'vergangen': werktage_vergangen,
        'verbleibend': werktage_verbleibend,
        'fortschritt_prozent': round(fortschritt, 1),
        'ist_aktueller_monat': heute.year == jahr and heute.month == monat,
    }

serviceberater_api = Blueprint('serviceberater_api', __name__, url_prefix='/api/serviceberater')

# ============================================================
# KONFIGURATION
# ============================================================

# TEK-Konfiguration für Serviceberater-Controlling (KORRIGIERT TAG121)
TEK_CONFIG = {
    # Ziel: Aftersales soll X% der Gesamtkosten decken (Service-Absorptionsrate)
    'aftersales_deckung_ziel': 0.65,  # 65% der Hauskosten durch Aftersales-DB

    # Margen für DB-Berechnung (aus BWA Jan-Nov 2025)
    'marge_arbeit': 0.554,   # 55,4% Marge auf Arbeit (BWA: Lohn 84 - Einsatz 74)
    'marge_teile': 0.347,    # 34,7% Marge auf Teile (BWA: Teile 83 - Einsatz 73)
    'marge_gewichtet': 0.424,  # 42,4% gewichtete Marge (37,4% Lohn / 62,6% Teile Anteil)
}

# ============================================================
# SERVICEBERATER KONFIGURATION (TAG122)
# ============================================================

# SB-Konfiguration mit Standort und LDAP-Mapping
SERVICEBERATER_CONFIG = {
    # Deggendorf (Opel + Hyundai)
    4000: {'name': 'Herbert Huber', 'standort': 'deggendorf', 'ldap_cn': 'Herbert Huber'},
    4005: {'name': 'Andreas Kraus', 'standort': 'deggendorf', 'ldap_cn': 'Andreas Kraus'},
    5009: {'name': 'Valentin Salmansberger', 'standort': 'deggendorf', 'ldap_cn': 'Valentin Salmansberger'},
    # Landau (Opel)
    4002: {'name': 'Leonhard Keidl', 'standort': 'landau', 'ldap_cn': 'Leonhard Keidl'},
    4003: {'name': 'Edith Egner', 'standort': 'landau', 'ldap_cn': 'Edith Egner'},
    5003: {'name': 'Walter Smola', 'standort': 'landau', 'ldap_cn': 'Walter Smola'},
    1006: {'name': 'Stephan Metzner', 'standort': 'landau', 'ldap_cn': 'Stephan Metzner'},  # Vertretung
}

# Alle SB-IDs (für Abwärtskompatibilität)
SERVICEBERATER_IDS = list(SERVICEBERATER_CONFIG.keys())

# LDAP CN → Locosoft MA-ID Mapping (für persönliches Dashboard)
LDAP_TO_LOCOSOFT_SB = {
    'Herbert Huber': 4000,
    'Andreas Kraus': 4005,
    'Valentin Salmansberger': 5009,
    'Leonhard Keidl': 4002,
    'Edith Egner': 4003,
    'Walter Smola': 5003,
    'Stephan Metzner': 1006,
}

# SB pro Standort (für Filter)
SB_DEGGENDORF = [k for k, v in SERVICEBERATER_CONFIG.items() if v['standort'] == 'deggendorf']
SB_LANDAU = [k for k, v in SERVICEBERATER_CONFIG.items() if v['standort'] == 'landau']

# Aktiver Wettbewerb
AKTIVER_WETTBEWERB = {
    'name': 'Contrasept Dezember 2025',
    'produkt': 'CONTRASEPT',
    'suchbegriffe': ['contrasept', 'desinfektion', 'innenraum'],
    'start': '2025-12-01',
    'ende': '2025-12-31',
    'ziel_team': 150,
    'praemie_1': 100,
    'praemie_2': 50,
    'praemie_3': 25,
}


# Aliase für Kompatibilität
get_sqlite_connection = get_db


def get_ma_namen():
    """Hole MA-Namen aus employees Tabelle (Portal DB - SQLite/PostgreSQL)
    TAG136: PostgreSQL-kompatibel via db_session
    """
    try:
        from api.db_utils import db_session
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT locosoft_id, first_name, last_name, department_name
                FROM employees
                WHERE locosoft_id IS NOT NULL
            """)
            # RealDictCursor gibt dict-like rows zurück
            namen = {}
            for row in cursor.fetchall():
                row_dict = row_to_dict(row)
                namen[row_dict['locosoft_id']] = {
                    'name': f"{row_dict['first_name']} {row_dict['last_name']}",
                    'title': row_dict['department_name'] or ''
                }
            return namen
    except Exception as e:
        print(f"get_ma_namen error: {e}")
        return {}


def get_ma_namen_locosoft():
    """Hole MA-Namen aus Locosoft employees Tabelle (für 4xxx/5xxx SB)
    Dies geht gegen die EXTERNE Locosoft PostgreSQL-DB (10.80.80.8)
    """
    try:
        with locosoft_session() as conn:
            # Locosoft hat eigenes RealDictCursor nicht aktiviert
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT employee_number, name
                FROM employees
                WHERE is_latest_record = true
                  AND employee_number IS NOT NULL
            """)
            # Name ist "Nachname,Vorname" -> umwandeln zu "Vorname Nachname"
            namen = {}
            for row in cursor.fetchall():
                ma_id = row['employee_number']
                name_raw = row['name'] or f"MA {ma_id}"
                if ',' in name_raw:
                    nachname, vorname = name_raw.split(',', 1)
                    namen[ma_id] = {'name': f"{vorname.strip()} {nachname.strip()}", 'title': 'Serviceberater'}
                else:
                    namen[ma_id] = {'name': name_raw, 'title': 'Serviceberater'}
            return namen
    except Exception as e:
        print(f"get_ma_namen_locosoft error: {e}")
        return {}


def get_breakeven_schwelle():
    """
    Hole Breakeven-Schwelle aus TEK (12-Monats-Durchschnitt Gesamtkosten)
    Gleiche Berechnung wie in controlling_routes.py berechne_breakeven_prognose()

    TAG136: PostgreSQL-kompatibel - nutzt db_session (Portal-DB, NICHT Locosoft!)
    loco_journal_accountings wurde von Locosoft in die Portal-DB importiert.
    """
    from api.db_utils import db_session
    from api.db_connection import convert_placeholders

    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # Datum-Berechnung - DB-unabhängig in Python
            from datetime import date
            from dateutil.relativedelta import relativedelta
            heute = date.today()
            vor_12_monaten = heute - relativedelta(months=12)

            # SUBSTR funktioniert in SQLite und PostgreSQL
            # convert_placeholders: ? -> %s für PostgreSQL
            cursor.execute(convert_placeholders("""
                SELECT
                    COALESCE(SUM(CASE
                        WHEN (nominal_account_number BETWEEN 415100 AND 415199
                              OR nominal_account_number BETWEEN 435500 AND 435599
                              OR (nominal_account_number BETWEEN 455000 AND 456999 AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                              OR (nominal_account_number BETWEEN 487000 AND 487099 AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                              OR nominal_account_number BETWEEN 491000 AND 497899)
                        THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as variable,

                    COALESCE(SUM(CASE
                        WHEN (nominal_account_number BETWEEN 400000 AND 489999
                              AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
                              AND NOT (nominal_account_number BETWEEN 415100 AND 415199
                                       OR nominal_account_number BETWEEN 424000 AND 424999
                                       OR nominal_account_number BETWEEN 435500 AND 435599
                                       OR nominal_account_number BETWEEN 438000 AND 438999
                                       OR nominal_account_number BETWEEN 455000 AND 456999
                                       OR nominal_account_number BETWEEN 487000 AND 487099
                                       OR nominal_account_number BETWEEN 491000 AND 497999))
                        THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as direkte,

                    COALESCE(SUM(CASE
                        WHEN ((nominal_account_number BETWEEN 400000 AND 499999 AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                              OR (nominal_account_number BETWEEN 424000 AND 424999 AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                              OR (nominal_account_number BETWEEN 438000 AND 438999 AND SUBSTR(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                              OR nominal_account_number BETWEEN 498000 AND 499999
                              OR (nominal_account_number BETWEEN 891000 AND 896999 AND NOT (nominal_account_number BETWEEN 893200 AND 893299)))
                        THEN CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END ELSE 0 END) / 100.0, 0) as indirekte
                FROM loco_journal_accountings
                WHERE accounting_date >= ? AND accounting_date < ?
            """), (vor_12_monaten.isoformat(), heute.isoformat()))
            row = cursor.fetchone()

            if row:
                row_dict = row_to_dict(row)
                # float() für Decimal-Werte (PostgreSQL)
                variable = float(row_dict['variable'] or 0)
                direkte = float(row_dict['direkte'] or 0)
                indirekte = float(row_dict['indirekte'] or 0)
                kosten_pro_monat = (variable + direkte + indirekte) / 12
                return {
                    'variable': round(variable / 12, 2),
                    'direkte': round(direkte / 12, 2),
                    'indirekte': round(indirekte / 12, 2),
                    'gesamt': round(kosten_pro_monat, 2)
                }
        return {'variable': 0, 'direkte': 0, 'indirekte': 0, 'gesamt': 430000}  # Fallback
    except Exception as e:
        print(f"get_breakeven_schwelle error: {e}")
        import traceback
        traceback.print_exc()
        return {'variable': 0, 'direkte': 0, 'indirekte': 0, 'gesamt': 430000}  # Fallback


# ============================================================
# API ENDPOINTS
# ============================================================

# Standort-Konfiguration (TAG121)
STANDORTE = {
    'alle': {'name': 'Gesamt', 'subsidiaries': [1, 2, 3]},
    'deggendorf': {'name': 'Deggendorf', 'subsidiaries': [1, 2]},  # Opel (1) + Hyundai (2)
    'landau': {'name': 'Landau', 'subsidiaries': [3]},  # Opel Landau
}


@serviceberater_api.route('/uebersicht', methods=['GET'])
def uebersicht():
    """
    Übersicht aller Serviceberater mit Umsatz und Zielerreichung

    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    - standort: 'alle', 'deggendorf', 'landau' (default: alle)
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))
    standort = request.args.get('standort', 'alle').lower()

    # Standort validieren
    if standort not in STANDORTE:
        standort = 'alle'
    standort_config = STANDORTE[standort]

    try:
        jahr, monat = monat_param.split('-')
        start_datum = f"{jahr}-{monat}-01"
        # Letzter Tag des Monats
        if int(monat) == 12:
            ende_datum = f"{int(jahr)+1}-01-01"
        else:
            ende_datum = f"{jahr}-{int(monat)+1:02d}-01"
    except:
        return jsonify({'success': False, 'error': 'Ungültiges Datumsformat'}), 400

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Standort-Filter (TAG121: Deggendorf = 1+2, Landau = 3)
        subsidiaries = standort_config['subsidiaries']
        if len(subsidiaries) == 3:  # alle
            standort_filter = ""
        else:
            standort_filter = f"AND i.subsidiary IN ({','.join(map(str, subsidiaries))})"

        # Serviceberater-Umsätze (TAG133: is_customer_reception Flag für echte SB)
        # JOIN mit orders.number + employees für Rolle
        cursor.execute(f"""
            SELECT
                o.order_taking_employee_no as ma_id,
                e.name as name_raw,
                e.is_customer_reception,
                e.subsidiary as ma_subsidiary,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                SUM(i.total_gross) as umsatz_gesamt,
                SUM(i.job_amount_gross) as umsatz_arbeit,
                SUM(i.part_amount_gross) as umsatz_teile,
                AVG(i.total_gross) as avg_rechnung
            FROM invoices i
            JOIN orders o ON i.order_number = o.number
            LEFT JOIN employees e ON o.order_taking_employee_no = e.employee_number
                AND e.is_latest_record = true
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.total_gross > 0
              AND i.invoice_type IN (2, 3, 6)
              AND o.order_taking_employee_no IS NOT NULL
              {standort_filter}
            GROUP BY o.order_taking_employee_no, e.name, e.is_customer_reception, e.subsidiary
            ORDER BY umsatz_gesamt DESC
        """, (start_datum, ende_datum))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # MA-Namen direkt aus Query (nicht mehr separater Aufruf nötig)
        ma_namen = get_ma_namen_locosoft()

        # Anzahl SB für Zielberechnung (TAG133: nutze is_customer_reception Flag)
        anzahl_sb = len([r for r in rows if r.get('is_customer_reception')]) or len(SERVICEBERATER_IDS)

        # DYNAMISCHE Zielberechnung aus TEK (TAG121)
        # Breakeven-Schwelle = 12-Monats-Durchschnitt Gesamtkosten (~430.000€)
        # Aftersales soll 65% davon decken = ~280.000€ DB
        # Bei 5 SB = ~56.000€ DB pro SB
        breakeven = get_breakeven_schwelle()
        gesamtkosten = breakeven['gesamt']
        deckung_ziel = TEK_CONFIG['aftersales_deckung_ziel']
        marge = TEK_CONFIG['marge_gewichtet']

        db_ziel_gesamt = gesamtkosten * deckung_ziel
        db_ziel_pro_sb = db_ziel_gesamt / anzahl_sb
        umsatz_ziel_pro_sb = db_ziel_pro_sb / marge

        # Ergebnis aufbereiten
        serviceberater = []
        for row in rows:
            ma_id = row['ma_id']
            umsatz = float(row['umsatz_gesamt'] or 0)
            arbeit = float(row['umsatz_arbeit'] or 0)
            teile = float(row['umsatz_teile'] or 0)

            # Deckungsbeitrag berechnen (100% Marge auf Arbeit, 54,4% auf Teile)
            db1 = (arbeit * TEK_CONFIG['marge_arbeit']) + (teile * TEK_CONFIG['marge_teile'])

            # Zielerreichung: DB des SB vs. DB-Ziel pro SB
            erreichung = (db1 / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0
            
            # Status
            if erreichung >= 100:
                status = 'success'
            elif erreichung >= 80:
                status = 'warning'
            else:
                status = 'danger'
            
            # Name aus Query oder Fallback
            name_raw = row.get('name_raw') or ''
            if ',' in name_raw:
                nachname, vorname = name_raw.split(',', 1)
                name = f"{vorname.strip()} {nachname.strip()}"
            else:
                name = name_raw or f"MA {ma_id}"

            # ist_serviceberater aus Locosoft-Flag (TAG133)
            ist_sb = row.get('is_customer_reception', False)

            serviceberater.append({
                'ma_id': ma_id,
                'name': name,
                'title': 'Serviceberater' if ist_sb else 'Mitarbeiter',
                'ist_serviceberater': ist_sb,
                'anzahl_rechnungen': row['anzahl_rechnungen'],
                'umsatz_gesamt': round(umsatz, 2),
                'umsatz_arbeit': round(arbeit, 2),
                'umsatz_teile': round(teile, 2),
                'avg_rechnung': round(float(row['avg_rechnung'] or 0), 2),
                'db1': round(db1, 2),
                'db_ziel': round(db_ziel_pro_sb, 2),  # 34.125€ DB-Ziel pro SB
                'umsatz_ziel': round(umsatz_ziel_pro_sb, 2),  # 45.500€ Umsatz-Ziel
                'erreichung': round(erreichung, 1),
                'status': status,
            })
        
        # Werktage-Berechnung (echte Werktage ohne Feiertage)
        werktage = get_werktage_monat(int(jahr), int(monat))

        # Hochrechnung für jeden SB berechnen
        for sb in serviceberater:
            if werktage['ist_aktueller_monat'] and werktage['vergangen'] > 0:
                # Prognose: DB / vergangene Tage * Gesamttage
                db_hochrechnung = sb['db1'] / werktage['vergangen'] * werktage['gesamt']
                erreichung_hochrechnung = (db_hochrechnung / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0

                # Erwartete Erreichung basierend auf Zeitfortschritt
                erreichung_soll = werktage['fortschritt_prozent']
                delta_vs_soll = sb['erreichung'] - erreichung_soll

                sb['hochrechnung'] = {
                    'db_prognose': round(db_hochrechnung, 2),
                    'erreichung_prognose': round(erreichung_hochrechnung, 1),
                    'erreichung_soll': round(erreichung_soll, 1),
                    'delta_vs_soll': round(delta_vs_soll, 1),
                    'auf_kurs': sb['erreichung'] >= erreichung_soll,
                }
            else:
                # Abgeschlossener Monat: keine Hochrechnung
                sb['hochrechnung'] = None

        return jsonify({
            'success': True,
            'monat': monat_param,
            'standort': standort,
            'standort_name': standort_config['name'],
            'subsidiaries': subsidiaries,
            'serviceberater': serviceberater,
            'config': {
                # Zielberechnung (dynamisch aus TEK)
                'breakeven_schwelle': gesamtkosten,           # ~430.000€ (12M-Schnitt)
                'break_even': round(umsatz_ziel_pro_sb, 2),   # Break-Even Umsatz pro SB (für Template)
                'aftersales_deckung_ziel': deckung_ziel,      # 65%
                'db_ziel_gesamt': round(db_ziel_gesamt, 2),   # ~280.000€
                'anzahl_sb': anzahl_sb,                       # 5
                'db_ziel_pro_sb': round(db_ziel_pro_sb, 2),   # ~56.000€ DB-Ziel pro SB
                'umsatz_ziel_pro_sb': round(umsatz_ziel_pro_sb, 2),
                # Margen (aus BWA Jan-Nov 2025)
                'marge_arbeit': TEK_CONFIG['marge_arbeit'],   # 55,4%
                'marge_teile': TEK_CONFIG['marge_teile'],     # 34,7%
                'marge_gewichtet': marge,                     # 42,4%
                # Kosten-Aufschlüsselung
                'kosten_variable': breakeven.get('variable', 0),
                'kosten_direkte': breakeven.get('direkte', 0),
                'kosten_indirekte': breakeven.get('indirekte', 0),
            },
            'werktage': werktage,  # {gesamt, vergangen, verbleibend, fortschritt_prozent}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/standorte', methods=['GET'])
def standorte():
    """Liste aller verfügbaren Standorte für Filter"""
    return jsonify({
        'success': True,
        'standorte': [
            {'key': 'alle', 'name': 'Gesamt', 'subsidiaries': [1, 2, 3]},
            {'key': 'deggendorf', 'name': 'Deggendorf', 'subsidiaries': [1, 2]},
            {'key': 'landau', 'name': 'Landau', 'subsidiaries': [3]},
        ]
    })


@serviceberater_api.route('/detail/<int:ma_id>', methods=['GET'])
def detail(ma_id):
    """
    Detail-Ansicht für einen Serviceberater (KORRIGIERT TAG121)

    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))

    try:
        jahr, monat = monat_param.split('-')
        start_datum = f"{jahr}-{monat}-01"
        if int(monat) == 12:
            ende_datum = f"{int(jahr)+1}-01-01"
        else:
            ende_datum = f"{jahr}-{int(monat)+1:02d}-01"
    except:
        return jsonify({'success': False, 'error': 'Ungültiges Datumsformat'}), 400

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Tägliche Umsätze - JOIN mit orders für order_taking_employee_no (TAG121)
        cursor.execute("""
            SELECT
                i.invoice_date as datum,
                COUNT(*) as anzahl,
                SUM(i.total_gross) as umsatz,
                SUM(i.job_amount_gross) as arbeit,
                SUM(i.part_amount_gross) as teile
            FROM invoices i
            JOIN orders o ON i.order_number = o.number
            WHERE o.order_taking_employee_no = %s
              AND i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.total_gross > 0
              AND i.invoice_type IN (2, 3, 6)
            GROUP BY i.invoice_date
            ORDER BY i.invoice_date
        """, (ma_id, start_datum, ende_datum))

        tage = []
        for row in cursor.fetchall():
            tage.append({
                'datum': row['datum'].strftime('%Y-%m-%d'),
                'anzahl': row['anzahl'],
                'umsatz': round(float(row['umsatz'] or 0), 2),
                'arbeit': round(float(row['arbeit'] or 0), 2),
                'teile': round(float(row['teile'] or 0), 2),
            })

        # Letzte 10 Rechnungen - JOIN mit orders (TAG121)
        cursor.execute("""
            SELECT
                i.invoice_type,
                i.invoice_number,
                i.invoice_date,
                i.total_gross,
                i.job_amount_gross,
                i.part_amount_gross,
                i.order_number
            FROM invoices i
            JOIN orders o ON i.order_number = o.number
            WHERE o.order_taking_employee_no = %s
              AND i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
            ORDER BY i.invoice_date DESC, i.invoice_number DESC
            LIMIT 10
        """, (ma_id, start_datum, ende_datum))

        rechnungen = []
        typ_namen = {2: 'Werkstatt', 3: 'Reklamation', 6: 'Garantie'}
        for row in cursor.fetchall():
            rechnungen.append({
                'typ': typ_namen.get(row['invoice_type'], f'Typ {row["invoice_type"]}'),
                'nummer': f"{row['invoice_type']}-{row['invoice_number']}",
                'datum': row['invoice_date'].strftime('%d.%m.%Y'),
                'gesamt': round(float(row['total_gross'] or 0), 2),
                'arbeit': round(float(row['job_amount_gross'] or 0), 2),
                'teile': round(float(row['part_amount_gross'] or 0), 2),
                'auftrag': row['order_number'],
            })

        cursor.close()
        conn.close()

        # MA-Name aus Locosoft (für 4xxx/5xxx)
        ma_namen = get_ma_namen_locosoft()
        ma_info = ma_namen.get(ma_id, {'name': f'MA {ma_id}', 'title': 'Serviceberater'})

        # Summen
        umsatz_gesamt = sum(t['umsatz'] for t in tage)
        arbeit_gesamt = sum(t['arbeit'] for t in tage)
        teile_gesamt = sum(t['teile'] for t in tage)
        anzahl_gesamt = sum(t['anzahl'] for t in tage)

        # DB1 berechnen (TAG121)
        db1 = (arbeit_gesamt * TEK_CONFIG['marge_arbeit']) + (teile_gesamt * TEK_CONFIG['marge_teile'])

        # Dynamische Zielberechnung aus TEK (TAG121)
        breakeven = get_breakeven_schwelle()
        gesamtkosten = breakeven['gesamt']
        anzahl_sb = len(SERVICEBERATER_IDS)
        deckung_ziel = TEK_CONFIG['aftersales_deckung_ziel']
        marge = TEK_CONFIG['marge_gewichtet']

        db_ziel_pro_sb = (gesamtkosten * deckung_ziel) / anzahl_sb
        erreichung = (db1 / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0

        # Werktage für Hochrechnung
        werktage = get_werktage_monat(int(jahr), int(monat))

        return jsonify({
            'success': True,
            'ma_id': ma_id,
            'name': ma_info['name'],
            'title': ma_info['title'],
            'monat': monat_param,
            'zusammenfassung': {
                'anzahl_rechnungen': anzahl_gesamt,
                'umsatz_gesamt': round(umsatz_gesamt, 2),
                'umsatz_arbeit': round(arbeit_gesamt, 2),
                'umsatz_teile': round(teile_gesamt, 2),
                'db1': round(db1, 2),
                'avg_rechnung': round(umsatz_gesamt / anzahl_gesamt, 2) if anzahl_gesamt > 0 else 0,
                'db_ziel': round(db_ziel_pro_sb, 2),
                'erreichung': round(erreichung, 1),
            },
            'tage': tage,
            'rechnungen': rechnungen,
            'werktage': werktage,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/wettbewerb', methods=['GET'])
def wettbewerb():
    """
    Aktueller Verkaufswettbewerb (z.B. Contrasept)

    Query-Parameter:
    - monat: YYYY-MM (default: aus Wettbewerb-Config)

    Datenquelle: labours-Tabelle (Arbeitspositionen) mit Suchbegriffen
    """
    monat_param = request.args.get('monat')

    # Wettbewerb-Zeitraum
    start_datum = AKTIVER_WETTBEWERB['start']
    ende_datum = AKTIVER_WETTBEWERB['ende']
    suchbegriffe = AKTIVER_WETTBEWERB['suchbegriffe']

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Contrasept/Desinfektion aus labours-Tabelle
        # JOIN mit orders für Serviceberater, invoices für Datum
        cursor.execute("""
            SELECT
                o.order_taking_employee_no as ma_id,
                e.name as name_raw,
                COUNT(*) as anzahl,
                ROUND(SUM(l.net_price_in_order)::numeric, 2) as umsatz
            FROM labours l
            JOIN orders o ON l.order_number = o.number
            JOIN invoices i ON l.invoice_type = i.invoice_type AND l.invoice_number = i.invoice_number
            LEFT JOIN employees e ON o.order_taking_employee_no = e.employee_number AND e.is_latest_record = true
            WHERE (l.text_line ILIKE %s OR l.text_line ILIKE %s OR l.text_line ILIKE %s)
              AND l.is_invoiced = true
              AND i.invoice_date >= %s
              AND i.invoice_date <= %s
              AND o.order_taking_employee_no IS NOT NULL
            GROUP BY o.order_taking_employee_no, e.name
            ORDER BY COUNT(*) DESC
        """, (
            f'%{suchbegriffe[0]}%',
            f'%{suchbegriffe[1]}%',
            f'%{suchbegriffe[2]}%',
            start_datum,
            ende_datum
        ))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Ranking aufbereiten
        ranking = []
        for idx, row in enumerate(rows, 1):
            # Name formatieren (Nachname,Vorname → Vorname Nachname)
            name_raw = row['name_raw'] or f"MA {row['ma_id']}"
            if ',' in name_raw:
                nachname, vorname = name_raw.split(',', 1)
                name = f"{vorname.strip()} {nachname.strip()}"
            else:
                name = name_raw

            ranking.append({
                'rang': idx,
                'ma_id': row['ma_id'],
                'name': name,
                'anzahl': row['anzahl'],
                'umsatz': float(row['umsatz'] or 0),
            })

        team_gesamt = sum(r['anzahl'] for r in ranking)

        return jsonify({
            'success': True,
            'wettbewerb': {
                'name': AKTIVER_WETTBEWERB['name'],
                'produkt': AKTIVER_WETTBEWERB['produkt'],
                'start': start_datum,
                'ende': ende_datum,
                'ziel_team': AKTIVER_WETTBEWERB['ziel_team'],
                'praemien': {
                    'platz_1': AKTIVER_WETTBEWERB['praemie_1'],
                    'platz_2': AKTIVER_WETTBEWERB['praemie_2'],
                    'platz_3': AKTIVER_WETTBEWERB['praemie_3'],
                }
            },
            'ranking': ranking,
            'team': {
                'gesamt': team_gesamt,
                'ziel': AKTIVER_WETTBEWERB['ziel_team'],
                'erreichung': round(team_gesamt / AKTIVER_WETTBEWERB['ziel_team'] * 100, 1) if AKTIVER_WETTBEWERB['ziel_team'] > 0 else 0,
            },
            'suchbegriffe': suchbegriffe,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/tek-config', methods=['GET'])
def tek_config():
    """
    TEK-Konfiguration für After Sales mit Werktage-Berechnung

    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))

    try:
        jahr, monat = monat_param.split('-')
    except:
        jahr, monat = datetime.now().year, datetime.now().month

    # Werktage des Monats
    werktage = get_werktage_monat(int(jahr), int(monat))

    # Kosten aus TEK (dynamisch)
    breakeven = get_breakeven_schwelle()
    gesamtkosten = breakeven['gesamt']

    anzahl_sb = len(SERVICEBERATER_IDS)
    deckung_ziel = TEK_CONFIG['aftersales_deckung_ziel']  # 65%
    marge = TEK_CONFIG['marge_gewichtet']  # 42,4%

    # DB-Ziel und Umsatz-Ziel pro SB (Monatswert)
    db_ziel_gesamt = gesamtkosten * deckung_ziel
    db_ziel_pro_sb = db_ziel_gesamt / anzahl_sb
    umsatz_ziel_pro_sb = db_ziel_pro_sb / marge

    # Pro-Werktag-Berechnung
    db_ziel_pro_werktag = db_ziel_pro_sb / werktage['gesamt'] if werktage['gesamt'] > 0 else 0
    umsatz_ziel_pro_werktag = umsatz_ziel_pro_sb / werktage['gesamt'] if werktage['gesamt'] > 0 else 0

    # Erwarteter Stand bis heute (Soll)
    db_soll_bis_heute = db_ziel_pro_werktag * werktage['vergangen']
    umsatz_soll_bis_heute = umsatz_ziel_pro_werktag * werktage['vergangen']

    return jsonify({
        'success': True,
        'monat': monat_param,
        'tek': {
            'gesamtkosten_monat': round(gesamtkosten, 2),
            'kosten_variable': round(breakeven.get('variable', 0), 2),
            'kosten_direkte': round(breakeven.get('direkte', 0), 2),
            'kosten_indirekte': round(breakeven.get('indirekte', 0), 2),
            'margen': {
                'arbeit': TEK_CONFIG['marge_arbeit'],
                'teile': TEK_CONFIG['marge_teile'],
                'gewichtet': TEK_CONFIG['marge_gewichtet'],
            },
        },
        'ziele': {
            # Monatsziele
            'db_ziel_gesamt': round(db_ziel_gesamt, 2),
            'db_ziel_pro_sb': round(db_ziel_pro_sb, 2),
            'umsatz_ziel_pro_sb': round(umsatz_ziel_pro_sb, 2),
            # Pro Werktag
            'db_ziel_pro_werktag': round(db_ziel_pro_werktag, 2),
            'umsatz_ziel_pro_werktag': round(umsatz_ziel_pro_werktag, 2),
            # Soll bis heute
            'db_soll_bis_heute': round(db_soll_bis_heute, 2),
            'umsatz_soll_bis_heute': round(umsatz_soll_bis_heute, 2),
        },
        'werktage': werktage,
        'serviceberater': {
            'anzahl': anzahl_sb,
            'ids': SERVICEBERATER_IDS,
            'break_even': round(umsatz_ziel_pro_sb, 2),  # Umsatz-Ziel pro SB/Monat
        },
        'quelle': 'TEK (12-Monats-Durchschnitt) + BWA-Margen',
    })


# ============================================================
# HELPER-FUNKTIONEN FÜR SB-ROLLE (TAG122)
# ============================================================

def get_sb_ma_id_from_ldap(ldap_cn: str) -> int:
    """
    Ermittelt die Locosoft MA-ID aus dem LDAP CN (Common Name)

    Args:
        ldap_cn: LDAP CN, z.B. "Herbert Huber"

    Returns:
        int: Locosoft MA-ID oder None wenn nicht gefunden
    """
    return LDAP_TO_LOCOSOFT_SB.get(ldap_cn)


def get_sb_standort_from_ma_id(ma_id: int) -> str:
    """
    Ermittelt den Standort eines SB aus der MA-ID

    Args:
        ma_id: Locosoft MA-ID

    Returns:
        str: 'deggendorf' oder 'landau' oder None
    """
    if ma_id in SERVICEBERATER_CONFIG:
        return SERVICEBERATER_CONFIG[ma_id]['standort']
    return None


def get_sb_config_from_ldap(ldap_cn: str) -> dict:
    """
    Holt komplette SB-Konfiguration aus LDAP CN

    Returns:
        dict: {ma_id, name, standort, ldap_cn} oder None
    """
    ma_id = get_sb_ma_id_from_ldap(ldap_cn)
    if ma_id and ma_id in SERVICEBERATER_CONFIG:
        config = SERVICEBERATER_CONFIG[ma_id].copy()
        config['ma_id'] = ma_id
        return config
    return None


@serviceberater_api.route('/mein-dashboard', methods=['GET'])
def mein_dashboard():
    """
    Persönliches Dashboard für eingeloggten Serviceberater (TAG122)

    Query-Parameter:
    - monat: YYYY-MM (default: aktueller Monat)
    - ldap_cn: LDAP Common Name des eingeloggten Users (z.B. "Herbert Huber")

    Hinweis: In Produktion wird ldap_cn aus current_user.cn geholt,
    hier als Parameter für Testing.
    """
    monat_param = request.args.get('monat', datetime.now().strftime('%Y-%m'))
    ldap_cn = request.args.get('ldap_cn', '')

    # SB-Konfiguration ermitteln
    sb_config = get_sb_config_from_ldap(ldap_cn)

    if not sb_config:
        return jsonify({
            'success': False,
            'error': f'Kein Serviceberater-Mapping für "{ldap_cn}" gefunden',
            'bekannte_sb': list(LDAP_TO_LOCOSOFT_SB.keys())
        }), 404

    ma_id = sb_config['ma_id']
    standort = sb_config['standort']

    try:
        jahr, monat = monat_param.split('-')
        start_datum = f"{jahr}-{monat}-01"
        if int(monat) == 12:
            ende_datum = f"{int(jahr)+1}-01-01"
        else:
            ende_datum = f"{jahr}-{int(monat)+1:02d}-01"
    except:
        return jsonify({'success': False, 'error': 'Ungültiges Datumsformat'}), 400

    try:
        conn = get_locosoft_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Persönliche Daten des SB
        cursor.execute("""
            SELECT
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                SUM(i.total_gross) as umsatz_gesamt,
                SUM(i.job_amount_gross) as umsatz_arbeit,
                SUM(i.part_amount_gross) as umsatz_teile,
                AVG(i.total_gross) as avg_rechnung
            FROM invoices i
            JOIN orders o ON i.order_number = o.number
            WHERE o.order_taking_employee_no = %s
              AND i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.total_gross > 0
              AND i.invoice_type IN (2, 3, 6)
        """, (ma_id, start_datum, ende_datum))

        row = cursor.fetchone()

        # Team-Daten (alle SB des gleichen Standorts)
        team_sb_ids = SB_DEGGENDORF if standort == 'deggendorf' else SB_LANDAU

        cursor.execute("""
            SELECT
                o.order_taking_employee_no as ma_id,
                SUM(i.total_gross) as umsatz_gesamt,
                SUM(i.job_amount_gross) as umsatz_arbeit,
                SUM(i.part_amount_gross) as umsatz_teile
            FROM invoices i
            JOIN orders o ON i.order_number = o.number
            WHERE o.order_taking_employee_no = ANY(%s)
              AND i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.total_gross > 0
              AND i.invoice_type IN (2, 3, 6)
            GROUP BY o.order_taking_employee_no
            ORDER BY SUM(i.job_amount_gross) * 0.554 + SUM(i.part_amount_gross) * 0.347 DESC
        """, (team_sb_ids, start_datum, ende_datum))

        team_rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Eigene Werte berechnen
        umsatz = float(row['umsatz_gesamt'] or 0) if row else 0
        arbeit = float(row['umsatz_arbeit'] or 0) if row else 0
        teile = float(row['umsatz_teile'] or 0) if row else 0
        db1 = (arbeit * TEK_CONFIG['marge_arbeit']) + (teile * TEK_CONFIG['marge_teile'])

        # Zielberechnung
        breakeven = get_breakeven_schwelle()
        gesamtkosten = breakeven['gesamt']
        anzahl_sb = len(SERVICEBERATER_IDS)
        db_ziel_pro_sb = (gesamtkosten * TEK_CONFIG['aftersales_deckung_ziel']) / anzahl_sb
        erreichung = (db1 / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0

        # Werktage
        werktage = get_werktage_monat(int(jahr), int(monat))

        # Hochrechnung
        hochrechnung = None
        if werktage['ist_aktueller_monat'] and werktage['vergangen'] > 0:
            db_prognose = db1 / werktage['vergangen'] * werktage['gesamt']
            erreichung_prognose = (db_prognose / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0
            delta_vs_soll = erreichung - werktage['fortschritt_prozent']
            hochrechnung = {
                'db_prognose': round(db_prognose, 2),
                'erreichung_prognose': round(erreichung_prognose, 1),
                'delta_vs_soll': round(delta_vs_soll, 1),
                'auf_kurs': erreichung >= werktage['fortschritt_prozent'],
            }

        # Team-Ranking aufbereiten
        team_ranking = []
        mein_rang = 0
        for idx, tr in enumerate(team_rows, 1):
            tr_arbeit = float(tr['umsatz_arbeit'] or 0)
            tr_teile = float(tr['umsatz_teile'] or 0)
            tr_db1 = (tr_arbeit * TEK_CONFIG['marge_arbeit']) + (tr_teile * TEK_CONFIG['marge_teile'])
            tr_erreichung = (tr_db1 / db_ziel_pro_sb * 100) if db_ziel_pro_sb > 0 else 0

            sb_name = SERVICEBERATER_CONFIG.get(tr['ma_id'], {}).get('name', f'MA {tr["ma_id"]}')
            is_me = tr['ma_id'] == ma_id
            if is_me:
                mein_rang = idx

            team_ranking.append({
                'rang': idx,
                'ma_id': tr['ma_id'],
                'name': sb_name,
                'db1': round(tr_db1, 2),
                'erreichung': round(tr_erreichung, 1),
                'is_me': is_me,
            })

        return jsonify({
            'success': True,
            'monat': monat_param,
            'sb': {
                'ma_id': ma_id,
                'name': sb_config['name'],
                'standort': standort,
                'standort_name': 'Deggendorf' if standort == 'deggendorf' else 'Landau',
            },
            'meine_zahlen': {
                'anzahl_rechnungen': row['anzahl_rechnungen'] if row else 0,
                'umsatz_gesamt': round(umsatz, 2),
                'umsatz_arbeit': round(arbeit, 2),
                'umsatz_teile': round(teile, 2),
                'avg_rechnung': round(float(row['avg_rechnung'] or 0), 2) if row else 0,
                'db1': round(db1, 2),
                'db_ziel': round(db_ziel_pro_sb, 2),
                'erreichung': round(erreichung, 1),
            },
            'hochrechnung': hochrechnung,
            'team_ranking': team_ranking,
            'mein_rang': mein_rang,
            'team_groesse': len(team_ranking),
            'werktage': werktage,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@serviceberater_api.route('/sb-config', methods=['GET'])
def sb_config_endpoint():
    """
    SB-Konfiguration für Frontend (TAG122)

    Gibt alle bekannten SB mit Standort zurück
    """
    sb_list = []
    for ma_id, config in SERVICEBERATER_CONFIG.items():
        sb_list.append({
            'ma_id': ma_id,
            'name': config['name'],
            'standort': config['standort'],
            'ldap_cn': config['ldap_cn'],
        })

    return jsonify({
        'success': True,
        'serviceberater': sb_list,
        'standorte': {
            'deggendorf': SB_DEGGENDORF,
            'landau': SB_LANDAU,
        },
        'ldap_mapping': LDAP_TO_LOCOSOFT_SB,
    })


@serviceberater_api.route('/health', methods=['GET'])
def health():
    """Health Check"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '1.1.0',  # TAG122: SB-Rolle
        'timestamp': datetime.now().isoformat(),
    })
