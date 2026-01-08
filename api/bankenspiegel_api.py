"""
Bankenspiegel REST API - FIXED VERSION
========================================
Kompatibel mit ECHTEM DB-Schema (TAG 71 Fix)

Änderungen:
- Verwendet echte Spaltennamen (id statt konto_id, letztes_update statt stand_datum)
- Nutzt existierende View v_aktuelle_kontostaende
- Keine nicht-existierenden Views mehr
- Direkte Queries auf Tabellen

Fixed: 21.11.2025 - TAG 72 - Einkaufsfinanzierung repariert
Updated: TAG 117 - Migration auf db_session (Connection-Safety)
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

# Zentrale DB-Utilities (TAG 117, TAG 136: PostgreSQL-kompatibel)
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import sql_placeholder, get_db_type, convert_placeholders

# Blueprint erstellen
bankenspiegel_api = Blueprint('bankenspiegel_api', __name__, url_prefix='/api/bankenspiegel')

# ============================================================================
# ENDPOINT 1: DASHBOARD
# ============================================================================

@bankenspiegel_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/bankenspiegel/dashboard
    Dashboard-KPIs
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        # TAG 136: PostgreSQL-kompatible Datumsfunktionen
        is_pg = get_db_type() == 'postgresql'
        date_30_days = "CURRENT_DATE - INTERVAL '30 days'" if is_pg else "DATE('now', '-30 days')"
        date_start_month = "DATE_TRUNC('month', CURRENT_DATE)" if is_pg else "DATE('now', 'start of month')"
        aktiv_check = "aktiv = true" if is_pg else "aktiv = 1"
        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # 1. Gesamtsaldo (aus v_aktuelle_kontostaende View)
            cursor.execute("""
                SELECT
                    COUNT(*) as anzahl_konten,
                    SUM(saldo) as gesamtsaldo,
                    MIN(letztes_update) as aeltester_stand,
                    MAX(letztes_update) as neuester_stand
                FROM v_aktuelle_kontostaende
            """)
            saldo_data = row_to_dict(cursor.fetchone())

            # 2. Transaktionen letzte 30 Tage (OHNE INTERNE TRANSFERS)
            cursor.execute(f"""
                SELECT
                    COUNT(*) as anzahl,
                    SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                    SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben
                FROM transaktionen
                WHERE buchungsdatum >= {date_30_days}
                  AND NOT (
                    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                    OR verwendungszweck LIKE '%Umbuchung%'
                    OR verwendungszweck LIKE '%Einlage%'
                    OR verwendungszweck LIKE '%Rückzahlung Einlage%'
                  )
            """)
            trans_30d = row_to_dict(cursor.fetchone())

            # 2b. Interne Transfers (SEPARAT)
            cursor.execute(f"""
                SELECT
                    COUNT(*) as anzahl,
                    SUM(ABS(betrag)) as volumen
                FROM transaktionen
                WHERE buchungsdatum >= {date_30_days}
                  AND (
                    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                    OR verwendungszweck LIKE '%Umbuchung%'
                    OR verwendungszweck LIKE '%Einlage%'
                    OR verwendungszweck LIKE '%Rückzahlung Einlage%'
                  )
            """)
            interne_30d = row_to_dict(cursor.fetchone())

            # 3. Aktueller Monat - TAG 136: PostgreSQL-kompatibel
            aktueller_monat = date.today().strftime('%Y-%m')
            if is_pg:
                # PostgreSQL: TO_CHAR für Monat-Vergleich
                cursor.execute(f"""
                    SELECT
                        SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                        SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben,
                        SUM(betrag) as saldo,
                        COUNT(*) as anzahl
                    FROM transaktionen
                    WHERE TO_CHAR(buchungsdatum, 'YYYY-MM') = {ph}
                """, (aktueller_monat,))
            else:
                cursor.execute(f"""
                    SELECT
                        SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as einnahmen,
                        SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as ausgaben,
                        SUM(betrag) as saldo,
                        COUNT(*) as anzahl
                    FROM transaktionen
                    WHERE TO_CHAR(buchungsdatum, 'YYYY-MM') = {ph}
                """, (aktueller_monat,))
            monat_data = row_to_dict(cursor.fetchone())

            # 4. Top 5 Ausgaben-Kategorien (aktueller Monat)
            cursor.execute(f"""
                SELECT
                    kategorie,
                    COUNT(*) as anzahl,
                    SUM(ABS(betrag)) as summe
                FROM transaktionen
                WHERE buchungsdatum >= {date_start_month}
                AND betrag < 0
                AND kategorie IS NOT NULL
                AND NOT (
                    verwendungszweck LIKE '%Autohaus Greiner%Autohaus Greiner%'
                    OR verwendungszweck LIKE '%Umbuchung%'
                )
                GROUP BY kategorie
                ORDER BY summe DESC
                LIMIT 5
            """)
            top_kategorien = rows_to_list(cursor.fetchall())

            # 5. Anzahl Banken - TAG 136: Boolean für PostgreSQL
            cursor.execute(f"SELECT COUNT(*) as anzahl FROM banken WHERE {aktiv_check}")
            anzahl_banken = row_to_dict(cursor.fetchone())['anzahl']

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'dashboard': {
                'gesamtsaldo': round(saldo_data['gesamtsaldo'] or 0, 2),
                'anzahl_konten': saldo_data['anzahl_konten'] or 0,
                'anzahl_banken': anzahl_banken,
                'neuester_stand': saldo_data['neuester_stand'],
                'letzte_30_tage': {
                    'anzahl_transaktionen': trans_30d['anzahl'] or 0,
                    'einnahmen': round(trans_30d['einnahmen'] or 0, 2),
                    'ausgaben': round(trans_30d['ausgaben'] or 0, 2),
                    'saldo': round((trans_30d['einnahmen'] or 0) - (trans_30d['ausgaben'] or 0), 2)
                },
                'interne_transfers_30_tage': {
                    'anzahl_transaktionen': interne_30d['anzahl'] or 0,
                    'volumen': round(interne_30d['volumen'] or 0, 2)
                },
                'aktueller_monat': {
                    'monat': aktueller_monat,
                    'einnahmen': round(monat_data['einnahmen'] or 0, 2),
                    'ausgaben': round(monat_data['ausgaben'] or 0, 2),
                    'saldo': round(monat_data['saldo'] or 0, 2),
                    'anzahl_transaktionen': monat_data['anzahl'] or 0
                },
                'top_kategorien': top_kategorien
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 2: KONTEN
# ============================================================================

@bankenspiegel_api.route('/konten', methods=['GET'])
def get_konten():
    """
    GET /api/bankenspiegel/konten?bank_id=1
    Kontenliste mit Salden
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        bank_id = request.args.get('bank_id', type=int)
        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # Query - verwendet v_aktuelle_kontostaende mit ECHTEN Spaltennamen
            query = """
                SELECT
                    id,
                    bank_name,
                    kontoname,
                    iban,
                    kontotyp,
                    'EUR' as waehrung,
                    saldo,
                    letztes_update as stand_datum,
                    1 as aktiv
                FROM v_aktuelle_kontostaende
                WHERE 1=1
            """

            params = []

            # Filter nach Bank - TAG 136: dynamischer Placeholder
            if bank_id:
                query += f" AND bank_id = {ph}"
                params.append(bank_id)

            query += " ORDER BY sort_order, kontoname"

            cursor.execute(query, params)
            konten = rows_to_list(cursor.fetchall())

            # Statistik - TAG 136: float() für PostgreSQL Decimal
            gesamtsaldo = sum(float(k['saldo'] or 0) for k in konten)

        return jsonify({
            'success': True,
            'konten': konten,
            'count': len(konten),
            'gesamtsaldo': round(gesamtsaldo, 2)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 3: TRANSAKTIONEN (TAG 136: PostgreSQL-kompatibel)
# ============================================================================

@bankenspiegel_api.route('/transaktionen', methods=['GET'])
def get_transaktionen():
    """
    GET /api/bankenspiegel/transaktionen?konto_id=1&von=2025-01-01&bis=2025-12-31
    Transaktionsliste mit Filtern
    TAG 136: PostgreSQL-kompatibel
    """
    from api.db_connection import convert_placeholders

    try:
        # Parameter auslesen
        konto_id = request.args.get('konto_id', type=int)
        bank_id = request.args.get('bank_id', type=int)
        von = request.args.get('von')
        bis = request.args.get('bis')
        kategorie = request.args.get('kategorie')
        betrag_min = request.args.get('betrag_min', type=float)
        betrag_max = request.args.get('betrag_max', type=float)
        suche = request.args.get('suche')
        limit = min(request.args.get('limit', default=100, type=int), 1000)
        offset = request.args.get('offset', default=0, type=int)
        order = request.args.get('order', default='desc')

        with db_session() as conn:
            cursor = conn.cursor()

            # Query aufbauen - direkt auf Tabellen
            query = """
                SELECT
                    t.id,
                    b.bank_name,
                    t.konto_id,
                    k.kontoname,
                    k.iban,
                    t.buchungsdatum,
                    t.valutadatum,
                    t.buchungstext,
                    t.verwendungszweck,
                    t.betrag,
                    t.waehrung,
                    t.kategorie,
                    t.steuerrelevant,
                    t.import_datei as pdf_quelle,
                    t.saldo_nach_buchung
                FROM transaktionen t
                JOIN konten k ON t.konto_id = k.id
                JOIN banken b ON k.bank_id = b.id
                WHERE 1=1
            """
            params = []

            # Filter anwenden (TAG 144: alle ? - convert_placeholders macht %s)
            if konto_id:
                query += " AND t.konto_id = ?"
                params.append(konto_id)

            if bank_id:
                query += " AND k.bank_id = ?"
                params.append(bank_id)

            if von:
                query += " AND t.buchungsdatum >= ?"
                params.append(von)

            if bis:
                query += " AND t.buchungsdatum <= ?"
                params.append(bis)

            if kategorie:
                query += " AND t.kategorie = ?"
                params.append(kategorie)

            if betrag_min is not None:
                query += " AND t.betrag >= ?"
                params.append(betrag_min)

            if betrag_max is not None:
                query += " AND t.betrag <= ?"
                params.append(betrag_max)

            if suche:
                query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
                search_term = f"%{suche}%"
                params.extend([search_term, search_term])

            # Sortierung
            order_dir = 'DESC' if order.lower() == 'desc' else 'ASC'
            query += f" ORDER BY t.buchungsdatum {order_dir}, t.id {order_dir}"

            # Limit & Offset
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # TAG 136: ? -> %s für PostgreSQL
            cursor.execute(convert_placeholders(query), params)
            transaktionen = rows_to_list(cursor.fetchall())

            # TAG 136: Datumswerte in ISO-Format konvertieren für JavaScript
            for t in transaktionen:
                if t.get('buchungsdatum'):
                    if hasattr(t['buchungsdatum'], 'isoformat'):
                        t['buchungsdatum'] = t['buchungsdatum'].strftime('%Y-%m-%d')
                    elif isinstance(t['buchungsdatum'], str) and ',' in t['buchungsdatum']:
                        # RFC Format -> ISO
                        from datetime import datetime as dt
                        try:
                            parsed = dt.strptime(t['buchungsdatum'], '%a, %d %b %Y %H:%M:%S %Z')
                            t['buchungsdatum'] = parsed.strftime('%Y-%m-%d')
                        except:
                            pass
                if t.get('valutadatum'):
                    if hasattr(t['valutadatum'], 'isoformat'):
                        t['valutadatum'] = t['valutadatum'].strftime('%Y-%m-%d')
                    elif isinstance(t['valutadatum'], str) and ',' in t['valutadatum']:
                        from datetime import datetime as dt
                        try:
                            parsed = dt.strptime(t['valutadatum'], '%a, %d %b %Y %H:%M:%S %Z')
                            t['valutadatum'] = parsed.strftime('%Y-%m-%d')
                        except:
                            pass

            # Gesamt-Anzahl
            count_query = "SELECT COUNT(*) as total FROM transaktionen t JOIN konten k ON t.konto_id = k.id WHERE 1=1"
            count_params = []

            if konto_id:
                count_query += " AND t.konto_id = %s"
                count_params.append(konto_id)
            if bank_id:
                count_query += " AND k.bank_id = %s"
                count_params.append(bank_id)
            if von:
                count_query += " AND t.buchungsdatum >= ?"
                count_params.append(von)
            if bis:
                count_query += " AND t.buchungsdatum <= ?"
                count_params.append(bis)
            if kategorie:
                count_query += " AND t.kategorie = %s"
                count_params.append(kategorie)
            if betrag_min is not None:
                count_query += " AND t.betrag >= ?"
                count_params.append(betrag_min)
            if betrag_max is not None:
                count_query += " AND t.betrag <= ?"
                count_params.append(betrag_max)
            if suche:
                count_query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
                search_term = f"%{suche}%"
                count_params.extend([search_term, search_term])

            cursor.execute(convert_placeholders(count_query), count_params)
            count_row = row_to_dict(cursor.fetchone())
            total = count_row['total']

            # Statistik
            stats_query = """
                SELECT
                    SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as summe_einnahmen,
                    SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as summe_ausgaben,
                    SUM(betrag) as saldo
                FROM transaktionen t
                JOIN konten k ON t.konto_id = k.id
                WHERE 1=1
            """
            stats_params = []

            if konto_id:
                stats_query += " AND t.konto_id = %s"
                stats_params.append(konto_id)
            if bank_id:
                stats_query += " AND k.bank_id = %s"
                stats_params.append(bank_id)
            if von:
                stats_query += " AND t.buchungsdatum >= ?"
                stats_params.append(von)
            if bis:
                stats_query += " AND t.buchungsdatum <= ?"
                stats_params.append(bis)
            if kategorie:
                stats_query += " AND t.kategorie = %s"
                stats_params.append(kategorie)
            if betrag_min is not None:
                stats_query += " AND t.betrag >= ?"
                stats_params.append(betrag_min)
            if betrag_max is not None:
                stats_query += " AND t.betrag <= ?"
                stats_params.append(betrag_max)
            if suche:
                stats_query += " AND (t.buchungstext LIKE ? OR t.verwendungszweck LIKE ?)"
                search_term = f"%{suche}%"
                stats_params.extend([search_term, search_term])

            cursor.execute(convert_placeholders(stats_query), stats_params)
            stats = row_to_dict(cursor.fetchone())

        return jsonify({
            'success': True,
            'transaktionen': transaktionen,
            'pagination': {
                'count': len(transaktionen),
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total
            },
            'statistik': {
                'einnahmen': round(float(stats['summe_einnahmen'] or 0), 2),
                'ausgaben': round(float(stats['summe_ausgaben'] or 0), 2),
                'saldo': round(float(stats['saldo'] or 0), 2)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 4: EINKAUFSFINANZIERUNG (FIXED - TAG 72, TAG 136: PostgreSQL)
# ============================================================================

@bankenspiegel_api.route('/einkaufsfinanzierung', methods=['GET'])
def get_einkaufsfinanzierung():
    """
    GET /api/bankenspiegel/einkaufsfinanzierung
    Einkaufsfinanzierung - Übersicht Stellantis & Santander
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        # TAG 136: PostgreSQL-Placeholder
        ph = sql_placeholder()

        with db_session() as conn:
            cursor = conn.cursor()

            # 1. GESAMT-ÜBERSICHT
            cursor.execute("""
                SELECT
                    COUNT(*) as anzahl_fahrzeuge,
                    SUM(aktueller_saldo) as gesamt_finanzierung,
                    SUM(original_betrag) as gesamt_original,
                    SUM(original_betrag - aktueller_saldo) as gesamt_abbezahlt
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true
            """)
            gesamt_row = row_to_dict(cursor.fetchone())

            # 2. DATEN PRO INSTITUT
            cursor.execute("""
                SELECT DISTINCT finanzinstitut
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true
                ORDER BY finanzinstitut
            """)
            institute_liste = [row_to_dict(row)['finanzinstitut'] for row in cursor.fetchall()]

            institute = []
            for institut in institute_liste:
                # Statistik pro Institut
                cursor.execute(f"""
                    SELECT
                        COUNT(*) as anzahl,
                        SUM(aktueller_saldo) as finanzierung,
                        SUM(original_betrag) as original,
                        AVG(aktueller_saldo) as durchschnitt,
                        MAX(alter_tage) as aeltestes_fahrzeug,
                        MIN(zinsfreiheit_tage) as min_zinsfreiheit,
                        SUM(original_betrag - aktueller_saldo) as abbezahlt
                    FROM fahrzeugfinanzierungen
                    WHERE finanzinstitut = {ph} AND aktiv = true
                """, (institut,))
                stats = row_to_dict(cursor.fetchone())

                # Marken-Verteilung
                cursor.execute(f"""
                    SELECT
                        rrdi,
                        COUNT(*) as anzahl,
                        SUM(aktueller_saldo) as finanzierung
                    FROM fahrzeugfinanzierungen
                    WHERE finanzinstitut = {ph} AND aktiv = true
                    GROUP BY rrdi
                    ORDER BY anzahl DESC
                """, (institut,))
                marken = []
                for row in cursor.fetchall():
                    r = row_to_dict(row)
                    rrdi_value = r['rrdi'] if r['rrdi'] else None
                    
                    # Marken-Name bestimmen
                    if institut == 'Stellantis':
                        if rrdi_value and "0154X" in str(rrdi_value):
                            marke_name = "Leapmotor"
                        elif rrdi_value:
                            marke_name = "Opel/Hyundai"
                        else:
                            marke_name = "Unbekannt"
                    elif institut == 'Santander':
                        # Santander hat oft kein rrdi, daher "Unbekannt"
                        marke_name = "Unbekannt" if not rrdi_value else rrdi_value
                    else:
                        # Hyundai Finance oder andere
                        marke_name = rrdi_value if rrdi_value else "Unbekannt"

                    marken.append({
                        'name': marke_name,
                        'anzahl': r['anzahl'],
                        'finanzierung': float(r['finanzierung']) if r['finanzierung'] else 0
                    })

                institute.append({
                    'name': institut,
                    'anzahl': stats['anzahl'],
                    'finanzierung': float(stats['finanzierung']) if stats['finanzierung'] else 0,
                    'original': float(stats['original']) if stats['original'] else 0,
                    'durchschnitt': float(stats['durchschnitt']) if stats['durchschnitt'] else 0,
                    'aeltestes': stats['aeltestes_fahrzeug'],
                    'min_zinsfreiheit': stats['min_zinsfreiheit'],
                    'abbezahlt': float(stats['abbezahlt']) if stats['abbezahlt'] else 0,
                    'marken': marken
                })

            # 3. TOP 10 TEUERSTE FAHRZEUGE
            cursor.execute("""
                SELECT
                    finanzinstitut,
                    vin,
                    modell,
                    rrdi,
                    aktueller_saldo,
                    original_betrag,
                    alter_tage,
                    zinsfreiheit_tage
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true
                ORDER BY aktueller_saldo DESC
                LIMIT 10
            """)

            top_fahrzeuge = []
            for row in cursor.fetchall():
                r = row_to_dict(row)
                top_fahrzeuge.append({
                    'institut': r['finanzinstitut'],
                    'vin': r['vin'][-8:] if r['vin'] else '???',
                    'modell': r['modell'],
                    'marke': r['rrdi'],
                    'saldo': float(r['aktueller_saldo']) if r['aktueller_saldo'] else 0,
                    'original': float(r['original_betrag']) if r['original_betrag'] else 0,
                    'alter': r['alter_tage'],
                    'zinsfreiheit': r['zinsfreiheit_tage']
                })

            # 4. ZINSFREIHEIT-WARNUNGEN (<= 30 Tage ODER bereits über Zinsfreiheit)
            cursor.execute("""
                SELECT
                    finanzinstitut,
                    vin,
                    modell,
                    rrdi,
                    zinsfreiheit_tage,
                    aktueller_saldo,
                    alter_tage
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true
                AND zinsfreiheit_tage IS NOT NULL
                AND (
                    zinsfreiheit_tage <= 30
                    OR alter_tage > zinsfreiheit_tage
                )
                ORDER BY 
                    CASE WHEN alter_tage > zinsfreiheit_tage THEN 0 ELSE 1 END,
                    zinsfreiheit_tage ASC
            """)

            warnungen = []
            for row in cursor.fetchall():
                r = row_to_dict(row)
                zinsfreiheit_tage = r['zinsfreiheit_tage']
                alter_tage = r['alter_tage'] or 0
                
                # Berechne tatsächliche Tage übrig (kann negativ sein wenn bereits über Zinsfreiheit)
                if alter_tage > zinsfreiheit_tage:
                    tage_uebrig = -(alter_tage - zinsfreiheit_tage)  # Negativ = bereits über
                else:
                    tage_uebrig = zinsfreiheit_tage - alter_tage  # Positiv = noch übrig
                
                warnungen.append({
                    'institut': r['finanzinstitut'],
                    'vin': r['vin'][-8:] if r['vin'] else '???',
                    'modell': r['modell'],
                    'marke': r['rrdi'],
                    'tage_uebrig': tage_uebrig,
                    'saldo': float(r['aktueller_saldo']) if r['aktueller_saldo'] else 0,
                    'alter': alter_tage,
                    'kritisch': tage_uebrig < 15 if tage_uebrig >= 0 else True  # Negativ = kritisch
                })

        return jsonify({
            'success': True,
            'gesamt': {
                'anzahl_fahrzeuge': gesamt_row['anzahl_fahrzeuge'],
                'finanzierung': float(gesamt_row['gesamt_finanzierung']) if gesamt_row['gesamt_finanzierung'] else 0,
                'original': float(gesamt_row['gesamt_original']) if gesamt_row['gesamt_original'] else 0,
                'abbezahlt': float(gesamt_row['gesamt_abbezahlt']) if gesamt_row['gesamt_abbezahlt'] else 0,
                'abbezahlt_prozent': round(gesamt_row['gesamt_abbezahlt'] / gesamt_row['gesamt_original'] * 100, 1) if gesamt_row['gesamt_original'] else 0
            },
            'institute': institute,
            'top_fahrzeuge': top_fahrzeuge,
            'warnungen': warnungen,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 5: FAHRZEUGE MIT ZINSEN
# ============================================================================

@bankenspiegel_api.route('/fahrzeuge-mit-zinsen', methods=['GET'])
def get_fahrzeuge_mit_zinsen():
    """
    GET /api/bankenspiegel/fahrzeuge-mit-zinsen
    Fahrzeuge mit Zinsen
    TAG 172: PostgreSQL-kompatibel, verwendet row_to_dict
    """
    try:
        status = request.args.get('status', 'zinsen_laufen')
        institut = request.args.get('institut', 'alle')
        limit = int(request.args.get('limit', 100))

        with db_session() as conn:
            c = conn.cursor()

            # TAG 172: Verwende ? als Placeholder, convert_placeholders macht %s daraus
            query = "SELECT * FROM fahrzeuge_mit_zinsen WHERE 1=1"
            params = []

            if status == 'zinsen_laufen':
                query += " AND zinsstatus = 'Zinsen laufen'"
            elif status == 'warnung':
                query += " AND zinsstatus LIKE '%Warnung%'"

            if institut != 'alle':
                query += " AND finanzinstitut = ?"
                params.append(institut)

            query += " ORDER BY zinsen_gesamt DESC LIMIT ?"
            params.append(limit)

            # TAG 172: PostgreSQL-kompatibel - convert_placeholders konvertiert ? zu %s
            final_query = convert_placeholders(query)
            c.execute(final_query, params)
            fahrzeuge = rows_to_list(c.fetchall())

            # Statistik berechnen
            gesamt_saldo = sum(float(f.get('aktueller_saldo') or 0) for f in fahrzeuge)
            gesamt_zinsen = sum(float(f.get('zinsen_gesamt') or 0) for f in fahrzeuge)

            # Santander vs Stellantis Split
            santander = [f for f in fahrzeuge if f.get('finanzinstitut') == 'Santander']
            stellantis = [f for f in fahrzeuge if f.get('finanzinstitut') == 'Stellantis']

            santander_zinsen_monatlich = sum(float(f.get('zinsen_monatlich_geschaetzt') or 0) for f in santander) if santander else None

        return jsonify({
            'success': True,
            'fahrzeuge': fahrzeuge,
            'statistik': {
                'anzahl_fahrzeuge': len(fahrzeuge),
                'gesamt_saldo': round(gesamt_saldo, 2),
                'gesamt_zinsen': round(gesamt_zinsen, 2) if gesamt_zinsen > 0 else None,
                'santander': {
                    'anzahl': len(santander),
                    'zinsen_monatlich': round(santander_zinsen_monatlich, 2) if santander_zinsen_monatlich else None
                },
                'stellantis': {
                    'anzahl': len(stellantis)
                }
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 6: KONTO SNAPSHOTS
# ============================================================================

@bankenspiegel_api.route('/konto/<int:konto_id>/snapshots')
def get_konto_snapshots(konto_id):
    """Historische Snapshots für ein Konto"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT k.kontoname, k.iban, k.kreditlinie, b.bank_name
                FROM konten k
                JOIN banken b ON k.bank_id = b.id
                WHERE k.id = %s
            ''', (konto_id,))

            konto_row = cursor.fetchone()
            if not konto_row:
                return jsonify({'error': 'Konto nicht gefunden'}), 404

            konto_info = dict(konto_row)

            cursor.execute('''
                SELECT
                    stichtag,
                    kapitalsaldo,
                    kreditlinie,
                    zinssatz,
                    ausnutzung_prozent,
                    zinstyp
                FROM konto_snapshots
                WHERE konto_id = %s
                ORDER BY stichtag ASC
            ''', (konto_id,))

            snapshots = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            'konto': {
                'id': konto_id,
                'name': konto_info['kontoname'],
                'iban': konto_info['iban'],
                'kreditlinie': konto_info['kreditlinie'],
                'bank': konto_info['bank_name']
            },
            'snapshots': snapshots,
            'count': len(snapshots)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@bankenspiegel_api.route('/health', methods=['GET'])
def health_check():
    """API Health Check"""
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM banken")
            banken_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM konten")
            konten_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM transaktionen")
            trans_count = cursor.fetchone()['count']

        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'connected': True,
                'banken': banken_count,
                'konten': konten_count,
                'transaktionen': trans_count
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# ENDPOINT: DATENSTAND
# ============================================================================

@bankenspiegel_api.route('/datenstand', methods=['GET'])
def get_datenstand():
    """
    GET /api/bankenspiegel/datenstand
    Zeigt den Datenstand der Kontoauszüge und letzten Imports.
    Wichtig für User-Validierung ob DRIVE aktuell ist.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()

            # 1. Neueste Transaktion (letzter Buchungstag)
            cursor.execute("""
                SELECT
                    MAX(buchungsdatum) as letzte_buchung
                FROM transaktionen
            """)
            trans_data = row_to_dict(cursor.fetchone())

            # 2. Konten mit Stand aus View
            cursor.execute("""
                SELECT
                    kontoname,
                    bank_name,
                    letztes_update,
                    saldo
                FROM v_aktuelle_kontostaende
                ORDER BY letztes_update DESC
                LIMIT 10
            """)
            konten_stand = rows_to_list(cursor.fetchall())

            # 3. Import-Statistik (letzte 7 Tage) - basierend auf Buchungsdatum
            cursor.execute("""
                SELECT
                    buchungsdatum as datum,
                    COUNT(*) as anzahl_transaktionen
                FROM transaktionen
                WHERE buchungsdatum >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY buchungsdatum
                ORDER BY datum DESC
            """)
            import_historie = rows_to_list(cursor.fetchall())

            # 4. Ältester und neuester Stand (aus View)
            cursor.execute("""
                SELECT
                    MIN(letztes_update) as aeltester_stand,
                    MAX(letztes_update) as neuester_stand,
                    COUNT(*) as anzahl_konten
                FROM v_aktuelle_kontostaende
            """)
            stand_range = row_to_dict(cursor.fetchone())

        # Berechne wie aktuell die Daten sind
        neuester_stand = stand_range.get('neuester_stand')
        if neuester_stand:
            try:
                stand_date = datetime.strptime(neuester_stand[:10], '%Y-%m-%d').date()
                tage_alt = (date.today() - stand_date).days
            except:
                tage_alt = None
        else:
            tage_alt = None

        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datenstand': {
                'letzte_buchung': trans_data.get('letzte_buchung'),
                'neuester_kontostand': stand_range.get('neuester_stand'),
                'aeltester_kontostand': stand_range.get('aeltester_stand'),
                'tage_alt': tage_alt,
                'anzahl_aktive_konten': stand_range.get('anzahl_konten', 0),
                'status': 'aktuell' if tage_alt is not None and tage_alt <= 1 else 'veraltet' if tage_alt and tage_alt > 3 else 'ok'
            },
            'konten_detail': konten_stand,
            'import_historie': import_historie
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
