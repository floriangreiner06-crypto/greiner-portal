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

from flask import Blueprint, jsonify, request, Response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

# Zentrale DB-Utilities (TAG 117, TAG 136: PostgreSQL-kompatibel)
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import sql_placeholder, get_db_type, convert_placeholders

# Blueprint erstellen
bankenspiegel_api = Blueprint('bankenspiegel_api', __name__, url_prefix='/api/bankenspiegel')

# ============================================================================
# HELPER-FUNKTIONEN
# ============================================================================

# Fahrzeugtyp-Anzeige wie im Provisions- und AfA-Modul: out_sale_type (Locosoft) hat Priorität,
# sonst dealer_vehicle_type + pre_owned_car_code + is_rental_or_school_vehicle.
def _fahrzeugtyp_from_locosoft(row):
    """
    Berechnet die Anzeige 'Typ' aus Locosoft-Feldern (konsistent mit Provisionsmodul/AfA).
    row: dict mit out_sale_type, dealer_vehicle_type, pre_owned_car_code, is_rental_or_school_vehicle.
    """
    out_sale = (row.get('out_sale_type') or '').strip().upper()
    dtype = (row.get('dealer_vehicle_type') or '').strip().upper()
    jw = (row.get('pre_owned_car_code') or '').strip().upper()
    is_rental = row.get('is_rental_or_school_vehicle') in (True, 't', 1)
    if is_rental:
        return 'Leihgabe/Mietwagen'
    if dtype == 'G' and jw == 'M':
        return 'Mietwagen'
    if out_sale:
        if out_sale in ('F', 'N', 'D'):
            return 'Neuwagen'
        if out_sale == 'T':
            return 'Tageszulassung'
        if out_sale in ('V', 'L'):
            return 'Vorführwagen' if out_sale == 'V' else 'Leihgabe/Mietwagen'
        if out_sale in ('B', 'G'):
            return 'Gebrauchtwagen'
    if dtype == 'G':
        return 'Gebrauchtwagen'
    if dtype == 'N':
        return 'Neuwagen'
    if dtype in ('D', 'V'):
        return 'Vorführwagen'
    if dtype == 'T':
        return 'Tageszulassung'
    if dtype == 'L':
        return 'Leihgabe/Mietwagen'
    return 'Unbekannt'


def find_vehicle_by_vin(loco_cursor, vin, fields='marke_modell'):
    """
    Helper-Funktion: Findet Fahrzeug in Locosoft anhand VIN (flexible Suche)
    
    Args:
        loco_cursor: Locosoft-DB-Cursor
        vin: VIN (kann vollständig oder gekürzt sein)
        fields: Welche Felder zurückgegeben werden sollen
            - 'marke_modell': Nur Marke und Modell
            - 'marke': Nur Marke
            - 'all': Alle verfügbaren Felder
    
    Returns:
        dict: Fahrzeugdaten oder None wenn nicht gefunden
    
    TAG 203: Code-Duplikat entfernt (war in get_fahrzeuge_by_marke und get_fahrzeug_details)
    """
    if not vin:
        return None
    
    vin_upper = vin.upper().strip()
    vin_like = f'%{vin_upper}%'
    
    if fields == 'marke':
        # Nur Marke
        query = """
            SELECT COALESCE(NULLIF(TRIM(m.description), ''), 'Unbekannt') as marke
            FROM vehicles v
            LEFT JOIN makes m ON v.make_number = m.make_number
            WHERE (
                UPPER(TRIM(v.vin)) = %s
                OR (LENGTH(v.vin) >= LENGTH(%s) AND UPPER(RIGHT(TRIM(v.vin), LENGTH(%s))) = %s)
                OR UPPER(TRIM(v.vin)) LIKE %s
            )
            LIMIT 1
        """
        params = (vin_upper, vin_upper, vin_upper, vin_upper, vin_like)
    elif fields == 'marke_modell':
        # Marke, Modell und Erstzulassung (für EZ-Anzeige auf Fahrzeugfinanzierungen)
        query = """
            SELECT 
                COALESCE(
                    NULLIF(TRIM(v.free_form_model_text), ''),
                    NULLIF(TRIM(mo.description), ''),
                    ''
                ) as modell,
                COALESCE(NULLIF(TRIM(m.description), ''), '') as marke,
                v.first_registration_date as erstzulassung
            FROM vehicles v
            LEFT JOIN makes m
                ON v.make_number = m.make_number
            LEFT JOIN models mo
                ON v.make_number = mo.make_number
                AND v.model_code = mo.model_code
            WHERE (
                UPPER(TRIM(v.vin)) = %s
                OR (LENGTH(v.vin) >= LENGTH(%s) AND UPPER(RIGHT(TRIM(v.vin), LENGTH(%s))) = %s)
                OR UPPER(TRIM(v.vin)) LIKE %s
            )
            LIMIT 1
        """
        params = (vin_upper, vin_upper, vin_upper, vin_upper, vin_like)
    else:
        # Alle Felder (für get_fahrzeug_details). fahrzeugtyp wird in Python aus out_sale_type/
        # pre_owned_car_code/is_rental (wie Provisions- und AfA-Modul) berechnet, nicht nur dealer_vehicle_type.
        query = """
            SELECT 
                dv.dealer_vehicle_number as kommissionsnummer,
                dv.dealer_vehicle_type,
                dv.out_sale_type,
                dv.pre_owned_car_code,
                dv.is_rental_or_school_vehicle,
                v.vin,
                v.license_plate as kennzeichen,
                COALESCE(
                    NULLIF(TRIM(v.free_form_model_text), ''),
                    NULLIF(TRIM(mo.description), ''),
                    'Unbekannt'
                ) as modell,
                COALESCE(NULLIF(TRIM(m.description), ''), 'Unbekannt') as marke,
                v.first_registration_date as erstzulassung,
                v.mileage_km as km_stand,
                dv.in_arrival_date as eingang,
                dv.created_date,
                CURRENT_DATE - COALESCE(dv.in_arrival_date, dv.created_date) as standzeit_tage,
                dv.in_subsidiary as standort,
                dv.location as lagerort,
                CASE 
                    WHEN dv.out_invoice_date IS NOT NULL THEN true
                    ELSE false
                END as verkauft,
                dv.out_invoice_date as verkauft_am
            FROM vehicles v
            LEFT JOIN dealer_vehicles dv
                ON v.dealer_vehicle_number = dv.dealer_vehicle_number
                AND v.dealer_vehicle_type = dv.dealer_vehicle_type
            LEFT JOIN makes m
                ON v.make_number = m.make_number
            LEFT JOIN models mo
                ON v.make_number = mo.make_number
                AND v.model_code = mo.model_code
            WHERE (
                UPPER(TRIM(v.vin)) = %s
                OR (LENGTH(v.vin) >= LENGTH(%s) AND UPPER(RIGHT(TRIM(v.vin), LENGTH(%s))) = %s)
                OR UPPER(TRIM(v.vin)) LIKE %s
            )
            ORDER BY 
                CASE WHEN UPPER(TRIM(v.vin)) = %s THEN 1 ELSE 2 END,
                dv.created_date DESC NULLS LAST
            LIMIT 1
        """
        params = (vin_upper, vin_upper, vin_upper, vin_upper, vin_like, vin_upper)
    
    loco_cursor.execute(query, params)
    row = loco_cursor.fetchone()
    
    if row:
        return row_to_dict(row, loco_cursor)
    
    return None

# ============================================================================
# ENDPOINT 1: DASHBOARD
# ============================================================================

@bankenspiegel_api.route('/dashboard', methods=['GET'])
@login_required
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
@login_required
def get_konten():
    """
    GET /api/bankenspiegel/konten?bank_id=1&alle=1
    Kontenliste mit Salden. alle=1: inkl. inaktive Konten, liefert bank_id und aktiv (für Verwaltung).
    TAG 136: PostgreSQL-kompatibel
    """
    from flask_login import current_user

    try:
        bank_id = request.args.get('bank_id', type=int)
        alle = request.args.get('alle', type=int) == 1

        with db_session() as conn:
            cursor = conn.cursor()

            if alle:
                # Verwaltung: alle Konten, mit bank_id und aktiv
                query = """
                    SELECT
                        k.id,
                        k.bank_id,
                        CASE WHEN b.bank_name = 'Intern / Gesellschafter' THEN NULL ELSE b.bank_name END as bank_name,
                        k.kontoname,
                        k.iban,
                        k.kontotyp,
                        'EUR' as waehrung,
                        COALESCE(s.saldo, 0) as saldo,
                        s.datum as stand_datum,
                        (k.aktiv = true) as aktiv,
                        COALESCE(k.kreditlinie, 0) as kreditlinie,
                        CASE WHEN k.kreditlinie IS NOT NULL AND k.kreditlinie > 0 THEN k.kreditlinie + COALESCE(s.saldo, 0) ELSE NULL END as verfuegbar,
                        k.kontoinhaber,
                        COALESCE(k.sort_order, 999) as sort_order
                    FROM konten k
                    LEFT JOIN banken b ON k.bank_id = b.id
                    LEFT JOIN (
                        SELECT konto_id, saldo, datum FROM salden
                        WHERE (konto_id, datum) IN (SELECT konto_id, MAX(datum) FROM salden GROUP BY konto_id)
                    ) s ON k.id = s.konto_id
                    WHERE 1=1
                """
            else:
                # Normale Übersicht: nur aktive
                query = """
                    SELECT
                        k.id,
                        CASE WHEN b.bank_name = 'Intern / Gesellschafter' THEN NULL ELSE b.bank_name END as bank_name,
                        k.kontoname,
                        k.iban,
                        k.kontotyp,
                        'EUR' as waehrung,
                        COALESCE(s.saldo, 0) as saldo,
                        s.datum as stand_datum,
                        1 as aktiv,
                        COALESCE(k.kreditlinie, 0) as kreditlinie,
                        CASE WHEN k.kreditlinie IS NOT NULL AND k.kreditlinie > 0 THEN k.kreditlinie + COALESCE(s.saldo, 0) ELSE NULL END as verfuegbar,
                        k.kontoinhaber
                    FROM konten k
                    LEFT JOIN banken b ON k.bank_id = b.id
                    LEFT JOIN (
                        SELECT konto_id, saldo, datum FROM salden
                        WHERE (konto_id, datum) IN (SELECT konto_id, MAX(datum) FROM salden GROUP BY konto_id)
                    ) s ON k.id = s.konto_id
                    WHERE k.aktiv = true
                """

            params = []
            if bank_id:
                query += " AND k.bank_id = %s"
                params.append(bank_id)

            # Primär manuelle Sortierung; Kontoinhaber-Bucket nur als sekundärer Tie-Breaker
            query += """
                ORDER BY 
                    COALESCE(k.sort_order, 999),
                    CASE 
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%autohaus greiner%' THEN 1
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%auto greiner%' THEN 2
                        ELSE 3
                    END,
                    k.kontoname
            """

            # TAG 180: Query ist bereits PostgreSQL-kompatibel (%s), kein convert_placeholders nötig
            # WICHTIG: psycopg2 wirft Fehler wenn params=[] - verwende None statt leerer Liste
            cursor.execute(query, params if params else None)
            konten = rows_to_list(cursor.fetchall())

            # TAG 213: Saldo vom Sachkonto 071101 aus Loco-Soft für "Darlehen Peter Greiner" holen
            # WICHTIG: Das Sachkonto 071101 IST das "Darlehen Peter Greiner" Konto!
            # Der Saldo soll beim bestehenden Konto (ID 22) verwendet werden, nicht als separates Konto
            # Saldo muss NEGATIV sein (rot), da die Gesellschaft dem Gesellschafter schuldet
            # IBAN wird auf Sachkontonummer "071101" gesetzt
            locosoft_saldo_071101 = None
            try:
                from api.db_utils import locosoft_session, row_to_dict
                with locosoft_session() as loco_conn:
                    loco_cursor = loco_conn.cursor()
                    # Saldo berechnen: HABEN - SOLL (für Passivkonto/Darlehen)
                    # Kontonummer 071101 = 71101 in Loco-Soft (Integer ohne führende Null)
                    loco_cursor.execute("""
                        SELECT COALESCE(SUM(
                            CASE WHEN debit_or_credit='H' THEN posted_value 
                                 ELSE -posted_value END
                        )/100.0, 0) as saldo
                        FROM journal_accountings
                        WHERE nominal_account_number = 71101
                    """)
                    saldo_row = loco_cursor.fetchone()
                    if saldo_row:
                        # Saldo aus Loco-Soft ist positiv (41.000,00 €)
                        # Aber: Die Gesellschaft schuldet dem Gesellschafter, also muss es NEGATIV sein
                        locosoft_saldo_071101 = -float(row_to_dict(saldo_row, loco_cursor).get('saldo', 0) or 0)
            except Exception as e:
                print(f"Fehler beim Holen des Saldos vom Sachkonto 071101 aus Loco-Soft: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fehler ignorieren, Saldo bleibt None

            # TAG 213: Saldo und IBAN beim bestehenden "Darlehen Peter Greiner" Konto (ID 22) verwenden
            if locosoft_saldo_071101 is not None:
                for konto in konten:
                    if konto.get('id') == 22:  # "Darlehen Peter Greiner"
                        # Loco-Soft Saldo überschreibt den DB-Saldo
                        konto['saldo'] = locosoft_saldo_071101
                        konto['stand_datum'] = None  # Kein Stand-Datum verfügbar
                        # IBAN auf "Sachkonto Locosoft 071101" setzen
                        konto['iban'] = 'Sachkonto Locosoft 071101'
                        break

            # TAG 214: Saldo vom Sachkonto 070101 aus Loco-Soft für "Hypovereinsbank Eurokredit" holen
            # WICHTIG: Das Sachkonto 070101 IST das "Hypovereinsbank Eurokredit" Konto!
            # Der Saldo soll beim bestehenden Konto (ID 23) verwendet werden
            # Saldo muss NEGATIV sein (rot), da die Gesellschaft der Bank schuldet (Kredit)
            # IBAN wird auf Sachkontonummer "070101" gesetzt
            locosoft_saldo_070101 = None
            try:
                from api.db_utils import locosoft_session, row_to_dict
                with locosoft_session() as loco_conn:
                    loco_cursor = loco_conn.cursor()
                    # Saldo berechnen: HABEN - SOLL (für Passivkonto/Kredit)
                    # Kontonummer 070101 = 70101 in Loco-Soft (Integer ohne führende Null)
                    loco_cursor.execute("""
                        SELECT COALESCE(SUM(
                            CASE WHEN debit_or_credit='H' THEN posted_value 
                                 ELSE -posted_value END
                        )/100.0, 0) as saldo
                        FROM journal_accountings
                        WHERE nominal_account_number = 70101
                    """)
                    saldo_row = loco_cursor.fetchone()
                    if saldo_row:
                        # Saldo aus Loco-Soft ist positiv (300.000,00 €)
                        # Aber: Die Gesellschaft schuldet der Bank, also muss es NEGATIV sein
                        locosoft_saldo_070101 = -float(row_to_dict(saldo_row, loco_cursor).get('saldo', 0) or 0)
            except Exception as e:
                print(f"Fehler beim Holen des Saldos vom Sachkonto 070101 aus Loco-Soft: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fehler ignorieren, Saldo bleibt None

            # TAG 214: Saldo und IBAN beim bestehenden "Hypovereinsbank Eurokredit" Konto (ID 23) verwenden
            if locosoft_saldo_070101 is not None:
                for konto in konten:
                    if konto.get('id') == 23:  # "Hypovereinsbank Eurokredit"
                        # Loco-Soft Saldo überschreibt den DB-Saldo
                        konto['saldo'] = locosoft_saldo_070101
                        konto['stand_datum'] = None  # Kein Stand-Datum verfügbar
                        # IBAN auf "Sachkonto Locosoft 070101" setzen
                        konto['iban'] = 'Sachkonto Locosoft 070101'
                        break

            # EKF-Konten (Einkaufsfinanzierung): Stellantis, Hyundai Finance, Santander aus fahrzeugfinanzierungen
            # Aggregierte Salden pro Institut als virtuelle Konten für die Kontenübersicht
            ekf_institute = ('Stellantis', 'Hyundai Finance', 'Santander')
            cursor.execute("""
                SELECT finanzinstitut, COALESCE(SUM(aktueller_saldo), 0) as saldo_sum
                FROM fahrzeugfinanzierungen
                WHERE aktiv = true AND finanzinstitut IN %s
                GROUP BY finanzinstitut
            """, (ekf_institute,))
            ekf_rows = cursor.fetchall()
            cursor.execute("""
                SELECT finanzinstitut, gesamt_limit
                FROM ek_finanzierung_konditionen
                WHERE finanzinstitut IN %s
            """, (ekf_institute,))
            ekf_limits = {}
            for r in cursor.fetchall():
                d = row_to_dict(r, cursor)
                ekf_limits[d['finanzinstitut']] = float(d.get('gesamt_limit') or 0)
            for idx, row in enumerate(ekf_rows):
                r = row_to_dict(row, cursor)
                inst = r['finanzinstitut']
                saldo_sum = float(r.get('saldo_sum') or 0)
                # Saldo aus Sicht Liquidität: Schulden = negativ (wie bei Kreditkonten)
                saldo_eur = -saldo_sum
                kreditlinie = ekf_limits.get(inst) or 0
                verfuegbar = (kreditlinie + saldo_eur) if kreditlinie and kreditlinie > 0 else None
                ekf_konto = {
                    'id': -(idx + 1),  # negative ID: kein echtes Konto, kein Transaktionen-Link
                    'bank_name': inst,
                    'kontoname': f'EKF {inst}',
                    'iban': 'EKF (aggregiert)',
                    'saldo': round(saldo_eur, 2),
                    'stand_datum': None,
                    'aktiv': 1,
                    'kreditlinie': kreditlinie if kreditlinie else 0,
                    'verfuegbar': round(verfuegbar, 2) if verfuegbar is not None else None,
                    'ekf': True,
                }
                if alle:
                    ekf_konto['bank_id'] = None  # Verwaltung: EKF sind keine Bankkonten
                konten.append(ekf_konto)

            # Statistik - TAG 136: float() für PostgreSQL Decimal (inkl. EKF-Schulden)
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


@bankenspiegel_api.route('/banken', methods=['GET'])
@login_required
def get_banken():
    """
    GET /api/bankenspiegel/banken
    Liste aller Banken (für Dropdown in Konten-Verwaltung).
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, bank_name FROM banken
                ORDER BY bank_name
            """)
            rows = cursor.fetchall()
        banken = [{'id': r['id'], 'bank_name': r['bank_name']} for r in rows]
        return jsonify({'success': True, 'banken': banken}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/ekf-bewegungen', methods=['GET'])
@login_required
def get_ekf_bewegungen():
    """
    GET /api/bankenspiegel/ekf-bewegungen?institut=Stellantis
    EKF-Positionen (aktive Verträge) als „Bewegungen“ – Stand aus CSV-Import, keine Kontoauszüge.
    Pro Fahrzeug eine Zeile: Vertragsbeginn, aktueller Saldo (als negative Verbindlichkeit), VIN/Modell/Kennzeichen.
    """
    institut = request.args.get('institut', type=str)
    if not institut or institut not in ('Stellantis', 'Hyundai Finance', 'Santander'):
        return jsonify({'success': False, 'error': 'Parameter institut fehlt oder ungültig (Stellantis, Hyundai Finance, Santander)'}), 400
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    vertragsbeginn AS buchungsdatum,
                    (-1.0 * COALESCE(aktueller_saldo, 0)) AS betrag,
                    vin,
                    modell,
                    kennzeichen,
                    original_betrag,
                    aktueller_saldo,
                    alter_tage,
                    zinsfreiheit_tage
                FROM fahrzeugfinanzierungen
                WHERE finanzinstitut = %s AND aktiv = true
                ORDER BY vertragsbeginn DESC NULLS LAST, vin
            """, (institut,))
            rows = cursor.fetchall()
        bewegungen = []
        for r in rows:
            d = row_to_dict(r, cursor)
            vin = (d.get('vin') or '').strip()
            modell = (d.get('modell') or '').strip()
            kennz = (d.get('kennzeichen') or '').strip()
            verwendungszweck = ' | '.join(filter(None, [vin and f'VIN {vin[-8:]}', modell or None, kennz or None])) or vin or '—'
            buchungsdatum = d.get('buchungsdatum')
            if hasattr(buchungsdatum, 'strftime'):
                buchungsdatum = buchungsdatum.strftime('%Y-%m-%d')
            bewegungen.append({
                'id': None,
                'konto_id': None,
                'buchungsdatum': buchungsdatum,
                'betrag': round(float(d.get('betrag') or 0), 2),
                'verwendungszweck': verwendungszweck,
                'buchungstext': f"EKF {institut}",
                'kategorie': 'EKF Position',
                'vin': vin,
                'modell': modell,
                'kennzeichen': kennz,
                'original_betrag': float(d.get('original_betrag') or 0),
                'aktueller_saldo': float(d.get('aktueller_saldo') or 0),
            })
        return jsonify({
            'success': True,
            'institut': institut,
            'transaktionen': bewegungen,
            'count': len(bewegungen),
            'hinweis': 'Stand aus CSV-Import – keine Kontoauszüge.'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/konten/<int:konto_id>', methods=['PATCH'])
@login_required
def patch_konto(konto_id):
    """
    PATCH /api/bankenspiegel/konten/<id>
    Konto bearbeiten (nur admin/buchhaltung). Erlaubte Felder: kontoname, iban, bank_id, kreditlinie, aktiv, kontoinhaber, sort_order.
    """
    from flask_login import current_user

    if not (current_user.has_role('admin') or current_user.has_role('buchhaltung')):
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403

    # EKF-Konten (negative ID) sind virtuelle Aggregate, nicht bearbeitbar
    if konto_id <= 0:
        return jsonify({'success': False, 'error': 'EKF-Konten (Einkaufsfinanzierung) sind nicht bearbeitbar'}), 400

    data = request.get_json() or {}
    updates = []
    params = []
    ziel_position = None
    aktuelle_position = None

    if 'kontoname' in data and data['kontoname'] is not None:
        v = (data['kontoname'] or '').strip()
        if not v:
            return jsonify({'success': False, 'error': 'Kontoname darf nicht leer sein'}), 400
        updates.append('kontoname = %s')
        params.append(v)
    if 'iban' in data:
        updates.append('iban = %s')
        params.append((data['iban'] or '').strip() or None)
    if 'bank_id' in data and data['bank_id'] is not None:
        try:
            bid = int(data['bank_id'])
            if bid <= 0:
                return jsonify({'success': False, 'error': 'Ungültige bank_id'}), 400
            updates.append('bank_id = %s')
            params.append(bid)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Ungültige bank_id'}), 400
    if 'kreditlinie' in data:
        try:
            kl = float(data['kreditlinie']) if data['kreditlinie'] not in (None, '') else 0
            if kl < 0:
                return jsonify({'success': False, 'error': 'Kreditlinie darf nicht negativ sein'}), 400
            updates.append('kreditlinie = %s')
            params.append(kl)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Ungültige Kreditlinie'}), 400
    if 'aktiv' in data:
        updates.append('aktiv = %s')
        params.append(bool(data['aktiv']))
    if 'kontoinhaber' in data:
        updates.append('kontoinhaber = %s')
        params.append((data['kontoinhaber'] or '').strip() or None)
    if 'sort_order' in data and data['sort_order'] is not None:
        try:
            so = int(data['sort_order'])
            if so < 1:
                return jsonify({'success': False, 'error': 'Sortierung muss >= 1 sein'}), 400
            ziel_position = so
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Ungültige Sortierung'}), 400

    if not updates and ziel_position is None:
        return jsonify({'success': False, 'error': 'Keine Felder zum Aktualisieren'}), 400

    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sort_order FROM konten WHERE id = %s", (konto_id,))
            row = cursor.fetchone()
            if row is None:
                return jsonify({'success': False, 'error': 'Konto nicht gefunden'}), 404
            try:
                aktuelle_position = int(row['sort_order']) if row['sort_order'] is not None else 999
            except Exception:
                aktuelle_position = int(row[0]) if isinstance(row, (list, tuple)) and row[0] is not None else 999

            # Nur bei echter Positionsänderung verschieben
            if ziel_position is not None and ziel_position == aktuelle_position:
                ziel_position = None

            if updates:
                updates.append('aktualisiert_am = NOW()')
                params.append(konto_id)
                cursor.execute(
                    "UPDATE konten SET " + ", ".join(updates) + " WHERE id = %s",
                    params
                )

            # Manuelle Reihenfolge inkl. "Verrutschen" der anderen Konten
            if ziel_position is not None:
                cursor.execute("SELECT COUNT(*) AS cnt FROM konten")
                cnt_row = cursor.fetchone()
                try:
                    gesamt = int(cnt_row['cnt'])
                except Exception:
                    gesamt = int(cnt_row[0]) if isinstance(cnt_row, (list, tuple)) and cnt_row else 0
                if gesamt <= 0:
                    return jsonify({'success': False, 'error': 'Keine Konten für Sortierung gefunden'}), 500

                ziel_position = max(1, min(ziel_position, gesamt))

                if ziel_position < aktuelle_position:
                    # Nach oben verschieben: Zwischenbereich nach unten schieben
                    cursor.execute(
                        """
                        UPDATE konten
                        SET sort_order = COALESCE(sort_order, 999) + 1,
                            aktualisiert_am = NOW()
                        WHERE id <> %s
                          AND COALESCE(sort_order, 999) >= %s
                          AND COALESCE(sort_order, 999) < %s
                        """,
                        (konto_id, ziel_position, aktuelle_position)
                    )
                elif ziel_position > aktuelle_position:
                    # Nach unten verschieben: Zwischenbereich nach oben schieben
                    cursor.execute(
                        """
                        UPDATE konten
                        SET sort_order = COALESCE(sort_order, 999) - 1,
                            aktualisiert_am = NOW()
                        WHERE id <> %s
                          AND COALESCE(sort_order, 999) > %s
                          AND COALESCE(sort_order, 999) <= %s
                        """,
                        (konto_id, aktuelle_position, ziel_position)
                    )

                # Zielkonto auf gewünschte Position setzen
                cursor.execute(
                    "UPDATE konten SET sort_order = %s, aktualisiert_am = NOW() WHERE id = %s",
                    (ziel_position, konto_id)
                )
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ENDPOINT 3: TRANSAKTIONEN (TAG 136: PostgreSQL-kompatibel)
# ============================================================================

@bankenspiegel_api.route('/transaktionen', methods=['GET'])
@login_required
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
# TRANSAKTIONS-KATEGORISIERUNG (regelbasiert + optional KI)
# ============================================================================

@bankenspiegel_api.route('/transaktionen/kategorisierung', methods=['GET'])
@login_required
def get_transaktionen_kategorisierung():
    """
    GET /api/bankenspiegel/transaktionen/kategorisierung
    Transaktionen für die Kategorisierungs-UI (mit gegenkonto_name, unterkategorie).
    Query: nur_unkategorisiert=true|false, nur_kategorisiert=true|false, kategorie=..., von=, bis=, limit=100, offset=0
    """
    from api.db_connection import convert_placeholders
    try:
        nur_unkategorisiert = request.args.get('nur_unkategorisiert', 'false').lower() in ('true', '1', 'yes')
        nur_kategorisiert = request.args.get('nur_kategorisiert', 'false').lower() in ('true', '1', 'yes')
        kategorie_filter = request.args.get('kategorie')
        von = request.args.get('von')
        bis = request.args.get('bis')
        suche = (request.args.get('suche') or '').strip()
        limit = min(request.args.get('limit', default=100, type=int), 500)
        offset = request.args.get('offset', default=0, type=int)
        if nur_unkategorisiert and nur_kategorisiert:
            nur_kategorisiert = False  # beide = alle

        with db_session() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    t.id,
                    t.buchungsdatum,
                    t.betrag,
                    t.verwendungszweck,
                    t.buchungstext,
                    t.gegenkonto_name,
                    t.kategorie,
                    t.unterkategorie,
                    COALESCE(t.kategorie_manuell, false) AS kategorie_manuell,
                    k.kontoname,
                    b.bank_name
                FROM transaktionen t
                JOIN konten k ON t.konto_id = k.id
                JOIN banken b ON k.bank_id = b.id
                WHERE 1=1
            """
            params = []
            if nur_unkategorisiert:
                query += " AND (t.kategorie IS NULL OR t.kategorie = '')"
            if nur_kategorisiert:
                query += " AND t.kategorie IS NOT NULL AND t.kategorie != ''"
            if kategorie_filter:
                query += " AND t.kategorie = ?"
                params.append(kategorie_filter)
            if von:
                query += " AND t.buchungsdatum >= ?"
                params.append(von)
            if bis:
                query += " AND t.buchungsdatum <= ?"
                params.append(bis)
            search_term = None
            if suche:
                # ILIKE = case-insensitive (PostgreSQL), damit "Krebs" auch "IT Krebs" / "KREBS" findet
                query += " AND (t.buchungstext ILIKE ? OR t.verwendungszweck ILIKE ? OR COALESCE(t.gegenkonto_name, '') ILIKE ?)"
                search_term = "%" + str(suche).replace("%", "\\%").replace("_", "\\_") + "%"
                params.extend([search_term, search_term, search_term])
            query += " ORDER BY t.buchungsdatum DESC, t.id DESC"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(convert_placeholders(query), params)
            rows = cursor.fetchall()
            transaktionen = rows_to_list(rows)

            for t in transaktionen:
                if t.get('buchungsdatum') and hasattr(t['buchungsdatum'], 'isoformat'):
                    t['buchungsdatum'] = t['buchungsdatum'].strftime('%Y-%m-%d')
                # Kategorie/Unterkategorie + nur bei kategorie_manuell grün (vom User gespeichert)
                t['kategorie'] = t.get('kategorie') if t.get('kategorie') else None
                t['unterkategorie'] = t.get('unterkategorie') if t.get('unterkategorie') else None
                t['kategorie_manuell'] = bool(t.get('kategorie_manuell'))

            count_query = """
                SELECT COUNT(*) as total FROM transaktionen t
                JOIN konten k ON t.konto_id = k.id
                JOIN banken b ON k.bank_id = b.id
                WHERE 1=1
            """
            count_params = []
            if nur_unkategorisiert:
                count_query += " AND (t.kategorie IS NULL OR t.kategorie = '')"
            if nur_kategorisiert:
                count_query += " AND t.kategorie IS NOT NULL AND t.kategorie != ''"
            if kategorie_filter:
                count_query += " AND t.kategorie = ?"
                count_params.append(kategorie_filter)
            if von:
                count_query += " AND t.buchungsdatum >= ?"
                count_params.append(von)
            if bis:
                count_query += " AND t.buchungsdatum <= ?"
                count_params.append(bis)
            if suche and search_term:
                count_query += " AND (t.buchungstext ILIKE ? OR t.verwendungszweck ILIKE ? OR COALESCE(t.gegenkonto_name, '') ILIKE ?)"
                count_params.extend([search_term, search_term, search_term])
            cursor.execute(convert_placeholders(count_query), count_params)
            total = (row_to_dict(cursor.fetchone()) or {}).get('total', 0)
        resp = jsonify({
            'success': True,
            'transaktionen': transaktionen,
            'total': total,
            'limit': limit,
            'offset': offset,
        })
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp, 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/kategorien', methods=['GET'])
@login_required
def get_transaktion_kategorien():
    """
    GET /api/bankenspiegel/kategorien
    Liste der Kategorien/Unterkategorien aus den Regeln (für Filter/Dropdown).
    """
    from api.transaktion_kategorisierung import get_kategorien_liste
    return jsonify({'success': True, 'kategorien': get_kategorien_liste()}), 200


@bankenspiegel_api.route('/transaktionen/ecodms/openapi-status', methods=['GET'])
@login_required
def get_ecodms_openapi_status():
    """
    GET /api/bankenspiegel/transaktionen/ecodms/openapi-status
    Liefert, ob die ecoDMS OpenAPI/Swagger-Spec geladen werden konnte (für Diagnose bei 404).
    """
    from api.ecodms_api import get_openapi_spec, ECODMS_OPENAPI_SPEC_URL, BASE_URL
    spec = get_openapi_spec()
    paths = list((spec.get("paths") or {}).keys()) if spec else []
    return jsonify({
        "spec_loaded": spec is not None,
        "config_url": ECODMS_OPENAPI_SPEC_URL,
        "base_url": BASE_URL,
        "paths_count": len(paths),
        "paths_sample": paths[:30],
    }), 200


@bankenspiegel_api.route('/transaktionen/ecodms/folders', methods=['GET'])
@login_required
def get_ecodms_folders():
    """
    GET /api/bankenspiegel/transaktionen/ecodms/folders
    Liest die Ordnerliste von ecoDMS per API (für Konfiguration/Diagnose).
    """
    from api.ecodms_api import get_folders, resolve_folder_id, FOLDER_BELEGE
    result = get_folders()
    resolved_id = resolve_folder_id(FOLDER_BELEGE) if result.get('success') else None
    return jsonify({
        'success': result.get('success', False),
        'folders': result.get('folders', []),
        'config_folder_belege': FOLDER_BELEGE,
        'resolved_folder_id': resolved_id,
        'error': result.get('error'),
    }), 200


@bankenspiegel_api.route('/transaktionen/ecodms/belege', methods=['GET'])
@login_required
def get_ecodms_belege():
    """
    GET /api/bankenspiegel/transaktionen/ecodms/belege?datum=2025-01-15&betrag=-123.45&referenz=...
    Sucht im ecoDMS-Archiv nach Belegen passend zur Buchung (Kategorisierung „Beleg suchen“).
    Liegt unter transaktionen/, da Transaktions-URLs zusammengefasst sind.
    Immer JSON-Antwort (kein HTML), damit das Frontend nicht mit Parse-Fehlern abbricht.
    """
    from api.ecodms_api import search_belege
    try:
        datum_str = request.args.get('datum')
        betrag = request.args.get('betrag', type=float)
        referenz = request.args.get('referenz', '').strip() or None
        buchungsdatum = None
        if datum_str:
            try:
                buchungsdatum = datetime.strptime(datum_str[:10], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        result = search_belege(buchungsdatum=buchungsdatum, betrag=betrag, referenz=referenz)
        if result.get('error') and not result.get('success'):
            return jsonify({
                'success': False,
                'documents': [],
                'error': result['error'],
            }), 200
        return jsonify({
            'success': result['success'],
            'documents': result.get('documents', []),
            'kreditor_vermutet': result.get('kreditor_vermutet'),
            'filter_gelockert': result.get('filter_gelockert', False),
            'error': result.get('error'),
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'documents': [],
            'error': f'ecoDMS-Anfrage fehlgeschlagen: {e!s}',
        }), 200


@bankenspiegel_api.route('/transaktionen/ecodms/document/<int:doc_id>/download', methods=['GET'])
@login_required
def get_ecodms_document_download(doc_id):
    """
    GET /api/bankenspiegel/transaktionen/ecodms/document/<docId>/download
    Proxy-Download: lädt Beleg von ecoDMS und streamt als Datei (ohne ecoDMS-Login).
    Unter transaktionen/ für konsistente API-Struktur.
    """
    from api.ecodms_api import get_document_stream
    stream, content_type = get_document_stream(str(doc_id))
    if stream is None:
        return jsonify({'success': False, 'error': 'Dokument nicht gefunden oder ecoDMS nicht erreichbar.'}), 404
    ext = '.pdf' if content_type and 'pdf' in content_type else '.bin'
    filename = f'beleg_{doc_id}{ext}'
    return Response(
        stream,
        mimetype=content_type or 'application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bankenspiegel_api.route('/transaktionen/kategorisieren', methods=['POST'])
@login_required
def post_transaktionen_kategorisieren():
    """
    POST /api/bankenspiegel/transaktionen/kategorisieren
    Wendet regelbasierte Kategorisierung auf (unkategorisierte) Transaktionen an.
    Body: { "limit": 500, "nur_unkategorisiert": true, "mit_ki": false, "sonstige_neu_pruefen": false, "regeln_ueberschreiben": false }
    mit_ki=true: nach Regeln noch unkategorisierte per LM Studio vorschlagen (Batch).
    sonstige_neu_pruefen=true: bestehende "Sonstige Ausgaben" mit aktuellen Regeln neu prüfen.
    regeln_ueberschreiben=true: Regeln auf die letzten limit Transaktionen erneut anwenden (überschreibt bestehende Kategorie).
    """
    from api.transaktion_kategorisierung import kategorisiere_batch
    try:
        data = request.get_json() or {}
        limit = min(int(data.get('limit', 500)), 2000)
        nur_unkategorisiert = data.get('nur_unkategorisiert', True)
        mit_ki = data.get('mit_ki', False)
        sonstige_neu_pruefen = data.get('sonstige_neu_pruefen', False)
        regeln_ueberschreiben = data.get('regeln_ueberschreiben', False)

        with db_session() as conn:
            if regeln_ueberschreiben:
                result = kategorisiere_batch(conn, limit=limit, nur_unkategorisiert=False, overwrite=True)
            else:
                result = kategorisiere_batch(conn, limit=limit, nur_unkategorisiert=nur_unkategorisiert, overwrite=False)
            sonstige_result = None
            if sonstige_neu_pruefen:
                sonstige_result = kategorisiere_batch(
                    conn, limit=limit, nur_unkategorisiert=False, nur_sonstige_ausgaben=True
                )

        if mit_ki:
            # Bei "Mit KI": immer noch unkategorisierte holen und an LM Studio schicken (max 50)
            try:
                from api.ai_api import kategorisiere_transaktion_mit_ki
                with db_session() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        convert_placeholders("""
                            SELECT id, verwendungszweck, buchungstext, gegenkonto_name, betrag
                            FROM transaktionen
                            WHERE (kategorie IS NULL OR kategorie = '')
                            ORDER BY buchungsdatum DESC LIMIT 50
                        """),
                    )
                    rows = cursor.fetchall()
                updates = []
                for row in rows:
                    rid = row.get('id') if hasattr(row, 'get') else row[0]
                    vw = row.get('verwendungszweck') if hasattr(row, 'get') else (row[1] if len(row) > 1 else None)
                    bt = row.get('buchungstext') if hasattr(row, 'get') else (row[2] if len(row) > 2 else None)
                    gk = row.get('gegenkonto_name') if hasattr(row, 'get') else (row[3] if len(row) > 3 else None)
                    betrag = row.get('betrag') if hasattr(row, 'get') else (row[4] if len(row) > 4 else None)
                    vorschlag = kategorisiere_transaktion_mit_ki(verwendungszweck=vw, buchungstext=bt, gegenkonto_name=gk, betrag=betrag)
                    if vorschlag and vorschlag.get('kategorie'):
                        updates.append((vorschlag.get('kategorie'), vorschlag.get('unterkategorie'), rid))
                ki_count = 0
                if updates:
                    ph = sql_placeholder()
                    with db_session() as conn2:
                        cur = conn2.cursor()
                        for kat, unterkat, rid in updates:
                            cur.execute(
                                convert_placeholders("""
                                    UPDATE transaktionen SET kategorie = """ + ph + """, unterkategorie = """ + ph + """ WHERE id = """ + ph
                                ),
                                (kat, unterkat, rid),
                            )
                            if cur.rowcount > 0:
                                ki_count += 1
                        conn2.commit()
                result['ki_aktualisiert'] = ki_count
            except Exception as ki_err:
                result['ki_fehler'] = str(ki_err)
                result['ki_aktualisiert'] = 0
        else:
            result['ki_aktualisiert'] = 0

        if sonstige_result is not None:
            result['sonstige_neu_pruefen'] = sonstige_result

        return jsonify({'success': True, 'ergebnis': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/transaktionen/<int:trans_id>/kategorie', methods=['PATCH', 'PUT'])
@login_required
def patch_transaktion_kategorie(trans_id):
    """
    PATCH /api/bankenspiegel/transaktionen/<id>/kategorie
    Setzt Kategorie einer Transaktion (manuell oder nach KI-Vorschlag).
    Body: { "kategorie": "...", "unterkategorie": "..." }
    Oder Body leer: Regeln anwenden.
    """
    from api.transaktion_kategorisierung import kategorisiere_transaktion_in_db
    from api.db_connection import convert_placeholders
    try:
        data = request.get_json() or {}
        kategorie = data.get('kategorie')
        unterkategorie = data.get('unterkategorie')
        regeln_anwenden = data.get('regeln_anwenden', False)
        if isinstance(kategorie, str):
            kategorie = kategorie.strip() or None
        if isinstance(unterkategorie, str):
            unterkategorie = unterkategorie.strip() or None

        with db_session() as conn:
            if regeln_anwenden or (kategorie is None and unterkategorie is None):
                ok = kategorisiere_transaktion_in_db(conn, trans_id, overwrite=True)
            else:
                ok = kategorisiere_transaktion_in_db(conn, trans_id, kategorie=kategorie, unterkategorie=unterkategorie, overwrite=True)
            if ok:
                conn.commit()
        if not ok:
            return jsonify({'success': False, 'error': 'Transaktion nicht gefunden oder nicht aktualisiert'}), 404
        return jsonify({'success': True, 'trans_id': trans_id}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def build_einkaufsfinanzierung_top_und_warnungen(cursor, top_limit: int = 10):
    """
    Top-Fahrzeuge nach aktuellem Finanzierungssaldo + Zinsfreiheit-Warnungen.
    Gleiche Logik wie get_einkaufsfinanzierung (SSOT, auch für VKL-Dashboard).
    """
    from api.db_utils import locosoft_session

    cursor.execute(
        """
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
        LIMIT %s
        """,
        (top_limit,),
    )
    top_rows = cursor.fetchall()
    top_fahrzeuge = []
    with locosoft_session() as loco_conn:
        loco_cursor = loco_conn.cursor()
        for row in top_rows:
            r = row_to_dict(row, cursor)
            loco_data = find_vehicle_by_vin(loco_cursor, r.get("vin"), fields="marke_modell")
            if loco_data:
                if not (r.get("modell") or "").strip() or (r.get("modell") or "").strip().lower() == "unbekannt":
                    if (loco_data.get("modell") or "").strip():
                        r["modell"] = (loco_data["modell"] or "").strip()
                ez = loco_data.get("erstzulassung")
                r["erstzulassung"] = ez.isoformat() if ez and hasattr(ez, "isoformat") else (ez if ez else None)
            else:
                r["erstzulassung"] = None
            top_fahrzeuge.append({
                "institut": r["finanzinstitut"],
                "vin": r["vin"][-8:] if r["vin"] else "???",
                "modell": r.get("modell") or "-",
                "marke": r["rrdi"],
                "saldo": float(r["aktueller_saldo"]) if r["aktueller_saldo"] else 0,
                "original": float(r["original_betrag"]) if r["original_betrag"] else 0,
                "alter": r["alter_tage"],
                "zinsfreiheit": r["zinsfreiheit_tage"],
                "erstzulassung": r.get("erstzulassung"),
            })

    cursor.execute(
        """
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
        """
    )
    warn_rows = cursor.fetchall()
    warnungen = []
    with locosoft_session() as loco_conn:
        loco_cursor = loco_conn.cursor()
        for row in warn_rows:
            r = row_to_dict(row, cursor)
            loco_data = find_vehicle_by_vin(loco_cursor, r.get("vin"), fields="marke_modell")
            if loco_data:
                if not (r.get("modell") or "").strip() or (r.get("modell") or "").strip().lower() == "unbekannt":
                    if (loco_data.get("modell") or "").strip():
                        r["modell"] = (loco_data["modell"] or "").strip()
                ez = loco_data.get("erstzulassung")
                r["erstzulassung"] = ez.isoformat() if ez and hasattr(ez, "isoformat") else (ez if ez else None)
            else:
                r["erstzulassung"] = None
            zinsfreiheit_tage = r["zinsfreiheit_tage"]
            alter_tage = r["alter_tage"] or 0
            if alter_tage > zinsfreiheit_tage:
                tage_uebrig = -(alter_tage - zinsfreiheit_tage)
            else:
                tage_uebrig = zinsfreiheit_tage - alter_tage
            warnungen.append({
                "institut": r["finanzinstitut"],
                "vin": r["vin"][-8:] if r["vin"] else "???",
                "modell": r.get("modell") or "-",
                "marke": r["rrdi"],
                "tage_uebrig": tage_uebrig,
                "saldo": float(r["aktueller_saldo"]) if r["aktueller_saldo"] else 0,
                "alter": alter_tage,
                "kritisch": tage_uebrig < 15 if tage_uebrig >= 0 else True,
                "erstzulassung": r.get("erstzulassung"),
            })

    return top_fahrzeuge, warnungen


# ============================================================================
# ENDPOINT 4: EINKAUFSFINANZIERUNG (FIXED - TAG 72, TAG 136: PostgreSQL)
# ============================================================================

@bankenspiegel_api.route('/einkaufsfinanzierung', methods=['GET'])
@login_required
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
            
            # === NEU: Genobank hinzufügen, auch wenn keine Fahrzeuge vorhanden ===
            # Genobank sollte immer angezeigt werden, wenn das Konto 4700057908 existiert
            if 'Genobank' not in institute_liste:
                # Prüfe ob Genobank-Konto existiert
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM konten
                    WHERE (kontonummer = '4700057908' OR iban LIKE '%4700057908%')
                      AND aktiv = true
                """)
                row = cursor.fetchone()
                if row:
                    r = row_to_dict(row)
                    if r.get('count', 0) > 0:
                        institute_liste.append('Genobank')

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
                # Für Genobank: hersteller-Feld verwenden, sonst rrdi
                # WICHTIG: Für Genobank müssen wir Marken aus Locosoft holen, falls hersteller leer ist
                if institut == 'Genobank':
                    # 1. Hole alle Genobank-Fahrzeuge mit VINs
                    cursor.execute(f"""
                        SELECT vin, hersteller, aktueller_saldo
                        FROM fahrzeugfinanzierungen
                        WHERE finanzinstitut = {ph} AND aktiv = true
                          AND vin IS NOT NULL AND vin != ''
                    """, (institut,))
                    genobank_fahrzeuge = cursor.fetchall()
                    
                    # 2. Für Fahrzeuge mit leerem/Unbekanntem hersteller: Hole Marke aus Locosoft
                    # TAG 203: Bulk-Abfrage statt N+1 Queries
                    from api.db_utils import locosoft_session
                    marken_dict = {}  # {marke: {'anzahl': int, 'finanzierung': float}}
                    
                    # Sammle alle VINs die aus Locosoft geholt werden müssen
                    vins_zu_pruefen = []
                    fahrzeuge_mit_marke = {}  # {vin: {'hersteller': str, 'saldo': float}}
                    
                    for row in genobank_fahrzeuge:
                        fz = row_to_dict(row, cursor)
                        vin = fz.get('vin')
                        hersteller = fz.get('hersteller')
                        saldo = float(fz.get('aktueller_saldo') or 0)
                        
                        # Wenn hersteller vorhanden und nicht "Unbekannt", verwende direkt
                        if hersteller and hersteller.strip() != '' and hersteller.strip().lower() != 'unbekannt':
                            marke = hersteller.strip()
                            # Aggregiere direkt
                            if marke not in marken_dict:
                                marken_dict[marke] = {'anzahl': 0, 'finanzierung': 0}
                            marken_dict[marke]['anzahl'] += 1
                            marken_dict[marke]['finanzierung'] += saldo
                        else:
                            # Muss aus Locosoft geholt werden
                            if vin:
                                vins_zu_pruefen.append(vin.upper().strip())
                                fahrzeuge_mit_marke[vin.upper().strip()] = {'saldo': saldo}
                    
                    # Bulk-Abfrage für alle VINs auf einmal
                    if vins_zu_pruefen:
                        with locosoft_session() as loco_conn:
                            loco_cursor = loco_conn.cursor()
                            
                            # Erstelle WHERE-Bedingung für alle VINs
                            # Verwende ANY() für PostgreSQL
                            vin_conditions = []
                            vin_params = []
                            
                            for vin_upper in vins_zu_pruefen:
                                vin_conditions.append("""
                                    (UPPER(TRIM(v.vin)) = %s
                                     OR (LENGTH(v.vin) >= LENGTH(%s) AND UPPER(RIGHT(TRIM(v.vin), LENGTH(%s))) = %s)
                                     OR UPPER(TRIM(v.vin)) LIKE %s)
                                """)
                                vin_params.extend([vin_upper, vin_upper, vin_upper, vin_upper, f'%{vin_upper}%'])
                            
                            # Bulk-Query: Hole Marke für alle VINs
                            bulk_query = f"""
                                SELECT DISTINCT
                                    v.vin,
                                    COALESCE(NULLIF(TRIM(m.description), ''), 'Unbekannt') as marke
                                FROM vehicles v
                                LEFT JOIN makes m ON v.make_number = m.make_number
                                WHERE ({' OR '.join(vin_conditions)})
                            """
                            
                            loco_cursor.execute(bulk_query, vin_params)
                            bulk_results = loco_cursor.fetchall()
                            
                            # Erstelle Mapping: VIN → Marke
                            vin_to_marke = {}
                            for bulk_row in bulk_results:
                                bulk_dict = row_to_dict(bulk_row, loco_cursor)
                                vin_key = bulk_dict.get('vin', '').upper().strip()
                                marke = bulk_dict.get('marke', 'Unbekannt')
                                if vin_key:
                                    vin_to_marke[vin_key] = marke
                            
                            # Für jede VIN: Bestimme Marke und aggregiere
                            for vin_upper, fz_data in fahrzeuge_mit_marke.items():
                                # Suche passende Marke (exakt, suffix, contains)
                                marke = 'Unbekannt'
                                
                                # Exakte Übereinstimmung
                                if vin_upper in vin_to_marke:
                                    marke = vin_to_marke[vin_upper]
                                else:
                                    # Suche nach Suffix-Match oder Contains-Match
                                    for loco_vin, loco_marke in vin_to_marke.items():
                                        if (len(loco_vin) >= len(vin_upper) and 
                                            loco_vin.endswith(vin_upper)) or vin_upper in loco_vin:
                                            marke = loco_marke
                                            break
                                
                                # Leapmotor-Erkennung (falls Modell bekannt wäre, hier vereinfacht)
                                # Da wir nur Marke haben, können wir Leapmotor nicht direkt erkennen
                                # Das wird später in get_fahrzeuge_by_marke gemacht
                                
                                # Aggregiere
                                if marke not in marken_dict:
                                    marken_dict[marke] = {'anzahl': 0, 'finanzierung': 0}
                                marken_dict[marke]['anzahl'] += 1
                                marken_dict[marke]['finanzierung'] += fz_data['saldo']
                    
                    # 3. Konvertiere zu Liste
                    marken = []
                    for marke_name, data in sorted(marken_dict.items(), key=lambda x: x[1]['anzahl'], reverse=True):
                        marken.append({
                            'name': marke_name,
                            'anzahl': data['anzahl'],
                            'finanzierung': data['finanzierung']
                        })
                else:
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
                    # Nur für Nicht-Genobank: Standard-Logik
                    marken = []
                    for row in cursor.fetchall():
                        r = row_to_dict(row)
                        
                        # Marken-Name bestimmen
                        if institut == 'Stellantis':
                            rrdi_value = r.get('rrdi')
                            if rrdi_value and "0154X" in str(rrdi_value):
                                marke_name = "Leapmotor"
                            elif rrdi_value:
                                marke_name = "Opel/Hyundai"
                            else:
                                marke_name = "Unbekannt"
                        elif institut == 'Santander':
                            rrdi_value = r.get('rrdi')
                            # Santander hat oft kein rrdi, daher "Unbekannt"
                            marke_name = "Unbekannt" if not rrdi_value else rrdi_value
                        else:
                            # Hyundai Finance oder andere
                            rrdi_value = r.get('rrdi')
                            marke_name = rrdi_value if rrdi_value else "Unbekannt"

                        marken.append({
                            'name': marke_name,
                            'anzahl': r['anzahl'],
                            'finanzierung': float(r['finanzierung']) if r['finanzierung'] else 0
                        })

                # Für Genobank: Falls keine Fahrzeuge, verwende Konto-Saldo
                if institut == 'Genobank' and stats['anzahl'] == 0:
                    # Hole Konto-Saldo für Genobank
                    cursor.execute("""
                        SELECT 
                            (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as konto_saldo
                        FROM konten k
                        WHERE (k.kontonummer = '4700057908' OR k.iban LIKE '%4700057908%')
                          AND k.aktiv = true
                        LIMIT 1
                    """)
                    konto_row = cursor.fetchone()
                    if konto_row:
                        konto_r = row_to_dict(konto_row)
                        konto_saldo = abs(float(konto_r.get('konto_saldo') or 0))
                        if konto_saldo > 0:
                            # Verwende Konto-Saldo als Finanzierung
                            stats['finanzierung'] = konto_saldo
                            stats['original'] = konto_saldo
                            stats['durchschnitt'] = konto_saldo
                            stats['anzahl'] = 0  # Keine Fahrzeuge, aber Konto existiert
                
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

            top_fahrzeuge, warnungen = build_einkaufsfinanzierung_top_und_warnungen(cursor, top_limit=10)

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
@login_required
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

            # Modell und Erstzulassung aus Locosoft nachladen
            from api.db_utils import locosoft_session
            with locosoft_session() as loco_conn:
                loco_cursor = loco_conn.cursor()
                for f in fahrzeuge:
                    loco_data = find_vehicle_by_vin(loco_cursor, f.get('vin'), fields='marke_modell')
                    if loco_data:
                        if not (f.get('modell') or '').strip() or (f.get('modell') or '').strip().lower() == 'unbekannt':
                            if (loco_data.get('modell') or '').strip():
                                f['modell'] = (loco_data['modell'] or '').strip()
                        ez = loco_data.get('erstzulassung')
                        f['erstzulassung'] = ez.isoformat() if ez and hasattr(ez, 'isoformat') else (ez if ez else None)
                    else:
                        f['erstzulassung'] = None

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
@login_required
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
# ENDPOINT: ZEITVERLAUF (TAG 180)
# ============================================================================

@bankenspiegel_api.route('/zeitverlauf', methods=['GET'])
def get_zeitverlauf():
    """
    GET /api/bankenspiegel/zeitverlauf?tage=6
    Zeitverlauf-Ansicht mit mehreren Tagen nebeneinander
    
    Returns:
    - Liste von Konten mit historischen Daten
    - Für jeden Tag: Guthaben, Darl.-Stand, Freie Linie
    """
    try:
        tage = request.args.get('tage', default=6, type=int)
        tage = min(max(tage, 1), 30)  # Limit: 1-30 Tage
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Letzte N Tage mit Snapshots finden
            cursor.execute(f"""
                SELECT DISTINCT stichtag
                FROM konto_snapshots
                WHERE stichtag >= CURRENT_DATE - INTERVAL '{tage} days'
                ORDER BY stichtag DESC
                LIMIT {tage}
            """)
            
            stichtage = [row[0] for row in cursor.fetchall()]
            
            if not stichtage:
                return jsonify({
                    'success': True,
                    'stichtage': [],
                    'konten': [],
                    'message': 'Keine historischen Daten gefunden'
                }), 200
            
            # Alle Konten mit Kreditlinien holen
            # TAG 180: Sortierung nach Kontoinhaber
            cursor.execute("""
                SELECT 
                    k.id,
                    k.kontoname,
                    k.iban,
                    k.kreditlinie,
                    b.bank_name,
                    k.kontotyp
                FROM konten k
                JOIN banken b ON k.bank_id = b.id
                WHERE k.aktiv = true
                ORDER BY 
                    CASE 
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%autohaus greiner%' THEN 1
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%auto greiner%' THEN 2
                        ELSE 3
                    END,
                    k.sort_order,
                    k.kontoname
            """)
            
            konten = rows_to_list(cursor.fetchall())
            
            # Für jedes Konto: Snapshots für alle Stichtage holen
            result_konten = []
            for konto in konten:
                konto_id = konto['id']
                konto_data = {
                    'id': konto_id,
                    'kontoname': konto['kontoname'],
                    'iban': konto['iban'],
                    'bank_name': konto['bank_name'],
                    'kontotyp': konto['kontotyp'],
                    'kreditlinie': float(konto['kreditlinie'] or 0),
                    'tage': {}
                }
                
                # Snapshots für alle Stichtage holen
                for stichtag in stichtage:
                    cursor.execute(f"""
                        SELECT 
                            kapitalsaldo,
                            kreditlinie
                        FROM konto_snapshots
                        WHERE konto_id = {ph} AND stichtag = {ph}
                        ORDER BY stichtag DESC
                        LIMIT 1
                    """, (konto_id, stichtag))
                    
                    snapshot = cursor.fetchone()
                    if snapshot:
                        snap_dict = row_to_dict(snapshot)
                        kapitalsaldo = float(snap_dict['kapitalsaldo'] or 0)
                        kreditlinie_snap = float(snap_dict['kreditlinie'] or konto['kreditlinie'] or 0)
                        
                        # Berechnungen
                        guthaben = kapitalsaldo if kapitalsaldo > 0 else 0
                        darlehen_stand = abs(kapitalsaldo) if kapitalsaldo < 0 else 0
                        freie_linie = kreditlinie_snap + kapitalsaldo if kreditlinie_snap > 0 else None
                        
                        konto_data['tage'][stichtag.strftime('%Y-%m-%d')] = {
                            'guthaben': round(guthaben, 2),
                            'darlehen_stand': round(darlehen_stand, 2),
                            'freie_linie': round(freie_linie, 2) if freie_linie is not None else None,
                            'kapitalsaldo': round(kapitalsaldo, 2),
                            'kreditlinie': round(kreditlinie_snap, 2)
                        }
                    else:
                        # Kein Snapshot für diesen Tag
                        konto_data['tage'][stichtag.strftime('%Y-%m-%d')] = None
                
                result_konten.append(konto_data)
            
            # Stichtage als Strings formatieren
            stichtage_str = [d.strftime('%Y-%m-%d') for d in stichtage]
            
        return jsonify({
            'success': True,
            'stichtage': stichtage_str,
            'konten': result_konten,
            'count': len(result_konten)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT: BANKIMPORT (Celery MT940 + HVB-PDF)
# ============================================================================

@bankenspiegel_api.route('/bankimport-anstossen', methods=['POST'])
@login_required
def post_bankimport_anstossen():
    """
    POST /api/bankenspiegel/bankimport-anstossen
    Stößt die gleichen Jobs an wie im Task Manager: import_mt940, import_hvb_pdf.
    Nur admin oder buchhaltung (wie Konten-Verwaltung).
    """
    try:
        if not (current_user.has_role('admin') or current_user.has_role('buchhaltung')):
            return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403

        from celery_app.tasks import import_mt940, import_hvb_pdf

        r_mt940 = import_mt940.delay()
        r_hvb = import_hvb_pdf.delay()

        return jsonify({
            'success': True,
            'message': 'Bankimport (MT940 und HVB-PDF) wurde in die Warteschlange gelegt.',
            'tasks': [
                {'name': 'import_mt940', 'task_id': r_mt940.id},
                {'name': 'import_hvb_pdf', 'task_id': r_hvb.id},
            ],
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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

# ============================================================================
# ENDPOINT 5: FAHRZEUGE NACH INSTITUT & MARKE (für Modal)
# ============================================================================

@bankenspiegel_api.route('/einkaufsfinanzierung/fahrzeuge', methods=['GET'])
def get_fahrzeuge_by_marke():
    """
    GET /api/bankenspiegel/einkaufsfinanzierung/fahrzeuge?institut=Genobank&marke=Unbekannt
    Fahrzeuge nach Institut und Marke filtern (für Modal)
    TAG 136: PostgreSQL-kompatibel
    """
    try:
        institut = request.args.get('institut', type=str)
        marke = request.args.get('marke', type=str)
        
        if not institut:
            return jsonify({
                'success': False,
                'error': 'Parameter "institut" fehlt'
            }), 400
        
        ph = sql_placeholder()
        
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Query: Fahrzeuge nach Institut und Marke
            # Für Genobank: hersteller-Feld verwenden, sonst rrdi
            # WICHTIG: Modell aus Locosoft holen, falls in fahrzeugfinanzierungen leer
            if institut == 'Genobank':
                # Erweiterte Query mit Locosoft-JOIN für Modell-Daten
                from api.db_utils import locosoft_session
                
                # 1. Hole ALLE Genobank-Fahrzeuge (ohne Marken-Filter)
                # WICHTIG: Marken-Filter erfolgt NACH Locosoft-Abruf, da Marke aus Locosoft kommt
                query = f"""
                    SELECT 
                        ff.vin,
                        ff.modell,
                        ff.hersteller as marke,
                        ff.aktueller_saldo,
                        ff.original_betrag,
                        ff.alter_tage,
                        ff.zins_startdatum,
                        ff.zinsen_gesamt,
                        ff.zinsen_letzte_periode,
                        ff.zinsfreiheit_tage
                    FROM fahrzeugfinanzierungen ff
                    WHERE ff.finanzinstitut = {ph} 
                      AND ff.aktiv = true
                """
                params = [institut]
                
                cursor.execute(query, params)
                fahrzeuge_rows = cursor.fetchall()
                
                # 2. Für jede VIN: Hole Marke/Modell aus Locosoft und filtere dann
                fahrzeuge = []
                with locosoft_session() as loco_conn:
                    loco_cursor = loco_conn.cursor()
                    
                    for row in fahrzeuge_rows:
                        fz_dict = row_to_dict(row, cursor)
                        vin = fz_dict.get('vin')
                        modell = fz_dict.get('modell')
                        marke_db = fz_dict.get('marke')  # Aus DB
                        
                        vin_upper = vin.upper().strip() if vin else ''
                        
                        # Hole Marke/Modell aus Locosoft (immer, da Marke für Filterung benötigt wird)
                        # TAG 203: Helper-Funktion verwendet
                        if vin_upper:
                            loco_data = find_vehicle_by_vin(loco_cursor, vin, fields='marke_modell')
                            if loco_data:
                                # Modell aktualisieren, falls leer
                                loco_modell = loco_data.get('modell', '')
                                if loco_modell and (not modell or modell.strip() == '' or modell.strip().lower() == 'unbekannt'):
                                    fz_dict['modell'] = loco_modell
                                # Erstzulassung für Anzeige
                                ez = loco_data.get('erstzulassung')
                                fz_dict['erstzulassung'] = ez.isoformat() if ez and hasattr(ez, 'isoformat') else (ez if ez else None)
                                # Marke aus Locosoft (hat Priorität)
                                loco_marke = loco_data.get('marke', '')
                                if loco_marke:
                                    # Leapmotor-Erkennung: Basierend auf Modell (B10, C10, T03)
                                    modell_str = loco_modell.upper() if loco_modell else ''
                                    if any(x in modell_str for x in ['B10', 'C10', 'T03', 'LEAPMOTOR']):
                                        fz_dict['marke'] = 'Leapmotor'
                                    else:
                                        fz_dict['marke'] = loco_marke
                                elif marke_db and marke_db.strip() != '' and marke_db.strip().lower() != 'unbekannt':
                                    # Fallback: Marke aus DB
                                    fz_dict['marke'] = marke_db
                                else:
                                    fz_dict['marke'] = 'Unbekannt'
                            else:
                                # VIN nicht in Locosoft gefunden, verwende DB-Werte
                                if not modell or modell.strip() == '' or modell.strip().lower() == 'unbekannt':
                                    fz_dict['modell'] = 'Unbekannt'
                                if not marke_db or marke_db.strip() == '' or marke_db.strip().lower() == 'unbekannt':
                                    fz_dict['marke'] = 'Unbekannt'
                                else:
                                    fz_dict['marke'] = marke_db
                                fz_dict['erstzulassung'] = None
                        else:
                            # Keine VIN, verwende DB-Werte
                            if not modell or modell.strip() == '' or modell.strip().lower() == 'unbekannt':
                                fz_dict['modell'] = 'Unbekannt'
                            if not marke_db or marke_db.strip() == '' or marke_db.strip().lower() == 'unbekannt':
                                fz_dict['marke'] = 'Unbekannt'
                            else:
                                fz_dict['marke'] = marke_db
                            fz_dict['erstzulassung'] = None
                        
                        # Marken-Filter NACH Locosoft-Abruf
                        if marke:
                            if marke == 'Unbekannt':
                                if fz_dict.get('marke', '').strip().lower() not in ['unbekannt', '', None]:
                                    continue  # Überspringe, wenn nicht "Unbekannt"
                            else:
                                if fz_dict.get('marke', '').strip() != marke.strip():
                                    continue  # Überspringe, wenn Marke nicht übereinstimmt
                        
                        # Für Genobank: Zinsen berechnen, falls noch nicht vorhanden
                        if institut == 'Genobank':
                            saldo = float(fz_dict.get('aktueller_saldo') or 0)
                            zins_start = fz_dict.get('zins_startdatum')
                            zinsen_gesamt = fz_dict.get('zinsen_gesamt')
                            zinsen_letzte_periode = fz_dict.get('zinsen_letzte_periode')
                            
                            # Nur berechnen, wenn noch nicht vorhanden
                            if (not zinsen_gesamt or zinsen_gesamt == 0) and saldo > 0 and zins_start:
                                from datetime import date, datetime
                                
                                # Hole Zinssatz aus konten
                                cursor.execute("""
                                    SELECT sollzins FROM konten
                                    WHERE (kontonummer = '4700057908' OR iban LIKE '%4700057908%')
                                      AND aktiv = true
                                    LIMIT 1
                                """)
                                zins_row = cursor.fetchone()
                                zinssatz = 5.5  # Default
                                if zins_row and zins_row[0]:
                                    zinssatz = float(zins_row[0])
                                else:
                                    # Fallback: ek_finanzierung_konditionen
                                    cursor.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Genobank'")
                                    kond_row = cursor.fetchone()
                                    if kond_row and kond_row[0]:
                                        zinssatz = float(kond_row[0])
                                
                                # Parse zins_startdatum
                                if isinstance(zins_start, str):
                                    try:
                                        if 'T' in zins_start or ' ' in zins_start:
                                            zins_start = datetime.fromisoformat(zins_start.replace('Z', '+00:00')).date()
                                        else:
                                            zins_start = datetime.strptime(zins_start, '%Y-%m-%d').date()
                                    except:
                                        zins_start = None
                                
                                # Berechne Tage seit Zinsstart
                                if zins_start and isinstance(zins_start, date):
                                    tage_seit_zinsstart = (date.today() - zins_start).days
                                    if tage_seit_zinsstart > 0:
                                        zinsen_gesamt = round(saldo * zinssatz / 100 * tage_seit_zinsstart / 365, 2)
                                        zinsen_monat = round(saldo * zinssatz / 100 * 30 / 365, 2)
                                        fz_dict['zinsen_gesamt'] = zinsen_gesamt
                                        fz_dict['zinsen_letzte_periode'] = zinsen_monat
                        
                        fahrzeuge.append(fz_dict)
                
                # Sortiere nach Standzeit (alter_tage) absteigend
                fahrzeuge.sort(key=lambda x: (x.get('alter_tage') or 0), reverse=True)
                
                return jsonify({
                    'success': True,
                    'institut': institut,
                    'marke': marke,
                    'fahrzeuge': fahrzeuge,
                    'anzahl': len(fahrzeuge)
                }), 200
            else:
                # Stellantis, Santander, Hyundai Finance: rrdi verwenden (inkl. Zinskosten)
                query = f"""
                    SELECT 
                        vin,
                        modell,
                        CASE 
                            WHEN rrdi IS NOT NULL AND rrdi != '' THEN rrdi
                            ELSE 'Unbekannt'
                        END as marke,
                        aktueller_saldo,
                        original_betrag,
                        alter_tage,
                        zins_startdatum,
                        zinsen_gesamt,
                        zinsen_letzte_periode,
                        zinsfreiheit_tage
                    FROM fahrzeugfinanzierungen
                    WHERE finanzinstitut = {ph} 
                      AND aktiv = true
                """
                params = [institut]
                
                if marke and marke != 'Unbekannt':
                    # Für Stellantis: Marken-Logik
                    if institut == 'Stellantis':
                        if marke == 'Opel/Hyundai':
                            query += f" AND (rrdi IS NOT NULL AND rrdi != '' AND rrdi NOT LIKE %s)"
                            params.append('%0154X%')
                        elif marke == 'Leapmotor':
                            query += f" AND rrdi LIKE %s"
                            params.append('%0154X%')
                        else:
                            query += f" AND rrdi = {ph}"
                            params.append(marke)
                    else:
                        query += f" AND rrdi = {ph}"
                        params.append(marke)
                elif marke == 'Unbekannt':
                    query += f" AND (rrdi IS NULL OR rrdi = '' OR rrdi = 'Unbekannt')"
            
            query += " ORDER BY alter_tage DESC NULLS LAST, vin"
            
            cursor.execute(query, params if len(params) > 1 else (params[0],))
            fahrzeuge = rows_to_list(cursor.fetchall())
            
            # Modell und Erstzulassung aus Locosoft nachladen
            if fahrzeuge:
                from api.db_utils import locosoft_session
                with locosoft_session() as loco_conn:
                    loco_cursor = loco_conn.cursor()
                    for fz in fahrzeuge:
                        vin = fz.get('vin')
                        if not vin:
                            continue
                        loco_data = find_vehicle_by_vin(loco_cursor, vin, fields='marke_modell')
                        if loco_data:
                            modell = (loco_data.get('modell') or '').strip()
                            if modell and (not (fz.get('modell') or '').strip() or (fz.get('modell') or '').strip().lower() == 'unbekannt'):
                                fz['modell'] = modell
                            ez = loco_data.get('erstzulassung')
                            fz['erstzulassung'] = ez.isoformat() if ez and hasattr(ez, 'isoformat') else (ez if ez else None)
                        else:
                            fz['erstzulassung'] = None
            
        return jsonify({
            'success': True,
            'institut': institut,
            'marke': marke,
            'fahrzeuge': fahrzeuge,
            'anzahl': len(fahrzeuge)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDPOINT 6: FAHRZEUGDETAILS AUS LOCOSOFT (für Modal)
# ============================================================================

@bankenspiegel_api.route('/fahrzeug-details', methods=['GET'])
def get_fahrzeug_details():
    """
    GET /api/bankenspiegel/fahrzeug-details?vin=VXKFCYHZ4R1068101
    Fahrzeuggrunddaten aus Locosoft holen (Typ, EZ, KM, etc.)
    """
    try:
        vin = request.args.get('vin', type=str)
        
        if not vin:
            return jsonify({
                'success': False,
                'error': 'Parameter "vin" fehlt'
            }), 400
        
        from api.db_utils import locosoft_session, row_to_dict
        
        fahrzeug = None
        finanzierung = None
        
        # 1. Fahrzeugdaten aus Locosoft
        with locosoft_session() as loco_conn:
            loco_cursor = loco_conn.cursor()
            
            # VIN-Suche: Exakt, dann Teil-VIN (Ende), dann Teil-VIN (enthält)
            # Problem: VINs in fahrzeugfinanzierungen können gekürzt sein (z.B. "T6004025")
            # während Locosoft die vollständige VIN hat (z.B. "VXKKAHPY3T6004025")
            # TAG 203: Helper-Funktion verwendet
            fahrzeug = find_vehicle_by_vin(loco_cursor, vin, fields='all')
            
            if fahrzeug:
                # Typ wie im Provisions- und AfA-Modul aus out_sale_type / dealer_vehicle_type / pre_owned_car_code
                fahrzeug['fahrzeugtyp'] = _fahrzeugtyp_from_locosoft(fahrzeug)
                
                # Standort-Name aus subsidiaries (falls vorhanden)
                if fahrzeug.get('standort'):
                    try:
                        loco_cursor.execute("""
                            SELECT description FROM subsidiaries WHERE subsidiary = %s
                        """, (fahrzeug.get('standort'),))
                        standort_row = loco_cursor.fetchone()
                        if standort_row:
                            standort_dict = row_to_dict(standort_row, loco_cursor)
                            fahrzeug['standort_name'] = standort_dict.get('description', '')
                    except:
                        # Falls subsidiaries-Tabelle nicht verfügbar oder andere Struktur
                        pass
        
                # 2. Finanzierungsdaten aus DRIVE Portal (inkl. Zinskosten)
        if fahrzeug:
            with db_session() as drive_conn:
                drive_cursor = drive_conn.cursor()
                
                # Aktuelle Finanzierung
                drive_cursor.execute("""
                    SELECT 
                        finanzinstitut,
                        aktueller_saldo,
                        original_betrag,
                        alter_tage,
                        zins_startdatum,
                        zinsen_gesamt,
                        zinsen_letzte_periode,
                        zinsfreiheit_tage
                    FROM fahrzeugfinanzierungen
                    WHERE vin = %s AND aktiv = true
                    ORDER BY aktualisiert_am DESC
                    LIMIT 1
                """, (vin,))
                
                fin_row = drive_cursor.fetchone()
                if fin_row:
                    finanzierung = row_to_dict(fin_row, drive_cursor)
                    
                    # Historie der Finanzinstitute abrufen (alle Einträge für diese VIN, auch inaktive)
                    drive_cursor.execute("""
                        SELECT DISTINCT
                            finanzinstitut,
                            zins_startdatum,
                            aktualisiert_am,
                            aktiv
                        FROM fahrzeugfinanzierungen
                        WHERE vin = %s
                        ORDER BY aktualisiert_am ASC
                    """, (vin,))
                    
                    historie_rows = drive_cursor.fetchall()
                    institut_historie = []
                    for hist_row in historie_rows:
                        hist_dict = row_to_dict(hist_row, drive_cursor)
                        institut_historie.append({
                            'finanzinstitut': hist_dict.get('finanzinstitut'),
                            'zins_startdatum': hist_dict.get('zins_startdatum'),
                            'aktualisiert_am': hist_dict.get('aktualisiert_am'),
                            'aktiv': hist_dict.get('aktiv', True)
                        })
                    
                    # Bestimme den Text für Zinsstartdatum
                    aktuelles_institut = finanzierung.get('finanzinstitut')
                    zins_start = finanzierung.get('zins_startdatum')
                    zinsstart_text = None
                    
                    if zins_start:
                        # Versuche vorheriges Institut zu finden
                        # Strategie 1: Prüfe alle anderen Institute für diese VIN (auch inaktive)
                        andere_institute = set()
                        for hist in institut_historie:
                            if hist.get('finanzinstitut') != aktuelles_institut:
                                andere_institute.add(hist.get('finanzinstitut'))
                        
                        if andere_institute:
                            # Es gibt andere Institute in der Historie
                            # Nimm das erste andere Institut (chronologisch)
                            vorheriges_institut = list(andere_institute)[0] if len(andere_institute) == 1 else None
                            
                            # Strategie 2: Prüfe ob es ein Institut gibt, das VOR dem zins_startdatum aktiv war
                            # (basierend auf aktualisiert_am)
                            if len(institut_historie) > 1:
                                for i, hist in enumerate(institut_historie):
                                    if hist.get('finanzinstitut') == aktuelles_institut:
                                        # Aktuelles Institut gefunden, prüfe vorherige
                                        if i > 0:
                                            vorheriges_institut = institut_historie[i-1].get('finanzinstitut')
                                        break
                            
                            if vorheriges_institut and vorheriges_institut != aktuelles_institut:
                                zinsstart_text = f"Datum der Umfinanzierung von {vorheriges_institut} zu {aktuelles_institut}"
                            else:
                                # Mehrere andere Institute, aber nicht eindeutig
                                zinsstart_text = f"Datum der Umfinanzierung zu {aktuelles_institut}"
                        else:
                            # Kein anderes Institut in Historie
                            zinsstart_text = f"Zinsstartdatum bei {aktuelles_institut}"
                    else:
                        zinsstart_text = None
                    
                    finanzierung['zinsstart_text'] = zinsstart_text
                    finanzierung['institut_historie'] = institut_historie
                    
                    # Für Genobank: Falls keine Zinsen vorhanden, berechnen
                    if finanzierung.get('finanzinstitut') == 'Genobank':
                        saldo = float(finanzierung.get('aktueller_saldo') or 0)
                        alter_tage = int(finanzierung.get('alter_tage') or 0)
                        
                        # Hole Zinssatz aus konten
                        drive_cursor.execute("""
                            SELECT sollzins FROM konten
                            WHERE (kontonummer = '4700057908' OR iban LIKE '%4700057908%')
                              AND aktiv = true
                            LIMIT 1
                        """)
                        zins_row = drive_cursor.fetchone()
                        zinssatz = 5.5  # Default
                        if zins_row:
                            zins_dict = row_to_dict(zins_row, drive_cursor)
                            zinssatz = float(zins_dict.get('sollzins') or 5.5)
                        
                        # Berechne Zinsen (falls noch nicht vorhanden)
                        if not finanzierung.get('zinsen_gesamt') or finanzierung.get('zinsen_gesamt') == 0:
                            if alter_tage > 0 and saldo > 0:
                                # Zinsen seit Zinsstart (NICHT seit Standzeit!)
                                # WICHTIG: Bei Genobank fallen Zinsen erst ab dem Datum an, 
                                # an dem das Fahrzeug von Stellantis zu Genobank umfinanziert wurde
                                zins_start = finanzierung.get('zins_startdatum')
                                if zins_start:
                                    from datetime import date, datetime
                                    if isinstance(zins_start, str):
                                        try:
                                            # Versuche verschiedene Datumsformate
                                            if 'T' in zins_start or ' ' in zins_start:
                                                zins_start = datetime.fromisoformat(zins_start.replace('Z', '+00:00')).date()
                                            else:
                                                zins_start = datetime.strptime(zins_start, '%Y-%m-%d').date()
                                        except:
                                            zins_start = None
                                    if zins_start and isinstance(zins_start, date):
                                        tage_seit_zinsstart = (date.today() - zins_start).days
                                    else:
                                        # Fallback: Wenn kein zins_startdatum vorhanden, KEINE Zinsen berechnen
                                        # (da wir nicht wissen, ab wann Zinsen anfallen)
                                        tage_seit_zinsstart = 0
                                else:
                                    # WICHTIG: Ohne zins_startdatum keine Zinsen berechnen!
                                    # Das Fahrzeug könnte noch bei Stellantis sein oder 
                                    # das Umfinanzierungsdatum ist unbekannt
                                    tage_seit_zinsstart = 0
                                
                                if tage_seit_zinsstart > 0:
                                    # Zinsen nur berechnen, wenn zins_startdatum vorhanden ist
                                    zinsen_gesamt = round(saldo * zinssatz / 100 * tage_seit_zinsstart / 365, 2)
                                    zinsen_monat = round(saldo * zinssatz / 100 * 30 / 365, 2)
                                    finanzierung['zinsen_gesamt'] = zinsen_gesamt
                                    finanzierung['zinsen_letzte_periode'] = zinsen_monat
                                else:
                                    # Keine Zinsen berechnen, wenn kein zins_startdatum vorhanden
                                    finanzierung['zinsen_gesamt'] = 0
                                    finanzierung['zinsen_letzte_periode'] = 0
                        else:
                            # Zinsen bereits vorhanden, aber monatlich berechnen falls fehlt
                            if not finanzierung.get('zinsen_letzte_periode') or finanzierung.get('zinsen_letzte_periode') == 0:
                                if saldo > 0:
                                    zinsen_monat = round(saldo * zinssatz / 100 * 30 / 365, 2)
                                    finanzierung['zinsen_letzte_periode'] = zinsen_monat
        
        if not fahrzeug:
            return jsonify({
                'success': False,
                'error': f'Fahrzeug mit VIN {vin} nicht in Locosoft gefunden'
            }), 404
        
        return jsonify({
            'success': True,
            'fahrzeug': fahrzeug,
            'finanzierung': finanzierung
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# KREDITVERTRÄGE / AUSFÜHRUNGSBESTIMMUNGEN (Modalitäten-DB)
# =============================================================================

@bankenspiegel_api.route('/modalitaeten', methods=['GET'])
@login_required
def get_modalitaeten():
    """
    GET /api/bankenspiegel/modalitaeten
    Query: anbieter (Kuerzel), regel_key, vertragsart_id
    Liefert Anbieter, Vertragsarten und Ausführungsbestimmungen (strukturiert).
    """
    try:
        anbieter_filter = request.args.get('anbieter')
        regel_key_filter = request.args.get('regel_key')
        vertragsart_id = request.args.get('vertragsart_id', type=int)

        with db_session() as conn:
            cur = conn.cursor()

            # Anbieter
            cur.execute("""
                SELECT id, name, kuerzel, aktiv
                FROM kredit_anbieter
                WHERE aktiv = true
                ORDER BY name
            """)
            anbieter = rows_to_list(cur.fetchall(), cur)

            # Vertragsarten (mit Anbieter-Name)
            cur.execute("""
                SELECT va.id, va.anbieter_id, a.name as anbieter_name, a.kuerzel as anbieter_kuerzel,
                       va.bezeichnung, va.produkt_code, va.gueltig_von, va.gueltig_bis
                FROM kredit_vertragsart va
                JOIN kredit_anbieter a ON va.anbieter_id = a.id
                WHERE va.aktiv = true AND a.aktiv = true
                ORDER BY a.name, va.bezeichnung
            """)
            vertragsarten = rows_to_list(cur.fetchall(), cur)

            # Ausführungsbestimmungen (mit Vertragsart + Anbieter)
            params = []
            where_parts = ["ab.aktiv = true"]
            if anbieter_filter:
                where_parts.append("a.kuerzel = %s")
                params.append(anbieter_filter.strip())
            if regel_key_filter:
                where_parts.append("ab.regel_key = %s")
                params.append(regel_key_filter.strip())
            if vertragsart_id:
                where_parts.append("ab.vertragsart_id = %s")
                params.append(vertragsart_id)

            cur.execute(f"""
                SELECT ab.id, ab.vertragsart_id, ab.dokument_id, ab.regel_typ, ab.regel_key,
                       ab.regel_wert, ab.einheit, ab.bedingung, ab.volltext, ab.gueltig_von, ab.gueltig_bis, ab.sortierung,
                       va.bezeichnung as vertragsart_bezeichnung, va.produkt_code,
                       a.name as anbieter_name, a.kuerzel as anbieter_kuerzel,
                       d.titel as dokument_titel
                FROM kredit_ausfuehrungsbestimmungen ab
                JOIN kredit_vertragsart va ON ab.vertragsart_id = va.id
                JOIN kredit_anbieter a ON va.anbieter_id = a.id
                LEFT JOIN kredit_dokumente d ON ab.dokument_id = d.id
                WHERE {' AND '.join(where_parts)}
                ORDER BY a.name, va.bezeichnung, ab.sortierung, ab.regel_typ
            """, tuple(params) if params else ())
            regeln = rows_to_list(cur.fetchall(), cur)

        return jsonify({
            'success': True,
            'anbieter': anbieter,
            'vertragsarten': vertragsarten,
            'ausfuehrungsbestimmungen': regeln
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/modalitaeten/suche', methods=['GET'])
@login_required
def suche_modalitaeten():
    """
    GET /api/bankenspiegel/modalitaeten/suche?q=zinsfreiheit
    Volltextsuche in Ausführungsbestimmungen (regel_typ, regel_key, regel_wert, bedingung, volltext).
    """
    try:
        q = (request.args.get('q') or '').strip()
        if not q:
            return jsonify({'success': True, 'treffer': []}), 200

        with db_session() as conn:
            cur = conn.cursor()
            # plainto_tsquery für deutsche Begriffe; Limit 50
            cur.execute("""
                SELECT ab.id, ab.vertragsart_id, ab.regel_typ, ab.regel_key, ab.regel_wert, ab.einheit, ab.bedingung,
                       left(ab.volltext, 300) as volltext_auszug,
                       va.bezeichnung as vertragsart_bezeichnung, a.name as anbieter_name, a.kuerzel as anbieter_kuerzel
                FROM kredit_ausfuehrungsbestimmungen ab
                JOIN kredit_vertragsart va ON ab.vertragsart_id = va.id
                JOIN kredit_anbieter a ON va.anbieter_id = a.id
                WHERE ab.aktiv = true AND ab.tsv @@ plainto_tsquery('german', %s)
                ORDER BY a.name, va.bezeichnung, ab.sortierung
                LIMIT 50
            """, (q,))
            treffer = rows_to_list(cur.fetchall(), cur)

        return jsonify({'success': True, 'treffer': treffer}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/modalitaeten/<int:regel_id>', methods=['PATCH'])
@login_required
def update_modalitaet(regel_id):
    """
    PATCH /api/bankenspiegel/modalitaeten/<id>
    Body: { "regel_wert": "...", "bedingung": "optional" }
    Aktualisiert eine Ausführungsbestimmung (nur admin).
    """
    from flask_login import current_user
    if not current_user.is_authenticated or not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Nur Admin'}), 403
    try:
        data = request.get_json() or {}
        regel_wert = data.get('regel_wert')
        bedingung = data.get('bedingung')
        if regel_wert is None:
            return jsonify({'success': False, 'error': 'regel_wert fehlt'}), 400
        with db_session() as conn:
            cur = conn.cursor()
            if bedingung is not None:
                cur.execute("""
                    UPDATE kredit_ausfuehrungsbestimmungen
                    SET regel_wert = %s, bedingung = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND aktiv = true
                """, (regel_wert, bedingung, regel_id))
            else:
                cur.execute("""
                    UPDATE kredit_ausfuehrungsbestimmungen
                    SET regel_wert = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND aktiv = true
                """, (regel_wert, regel_id))
            if cur.rowcount == 0:
                return jsonify({'success': False, 'error': 'Regel nicht gefunden oder inaktiv'}), 404
            conn.commit()
        return jsonify({'success': True, 'id': regel_id}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@bankenspiegel_api.route('/modalitaeten', methods=['POST'])
@login_required
def create_modalitaet():
    """
    POST /api/bankenspiegel/modalitaeten
    Body: vertragsart_id, regel_typ, regel_key, regel_wert, einheit (optional), bedingung (optional)
    Legt eine neue Ausführungsbestimmung an (nur admin).
    """
    from flask_login import current_user
    if not current_user.is_authenticated or not current_user.has_role('admin'):
        return jsonify({'success': False, 'error': 'Nur Admin'}), 403
    try:
        data = request.get_json() or {}
        vertragsart_id = data.get('vertragsart_id')
        regel_typ = (data.get('regel_typ') or '').strip()
        regel_key = (data.get('regel_key') or '').strip()
        regel_wert = (data.get('regel_wert') or '').strip()
        if not vertragsart_id or not regel_typ or not regel_key or not regel_wert:
            return jsonify({'success': False, 'error': 'vertragsart_id, regel_typ, regel_key, regel_wert erforderlich'}), 400
        einheit = (data.get('einheit') or '').strip() or None
        bedingung = (data.get('bedingung') or '').strip() or None
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO kredit_ausfuehrungsbestimmungen (vertragsart_id, regel_typ, regel_key, regel_wert, einheit, bedingung, sortierung, aktiv)
                VALUES (%s, %s, %s, %s, %s, %s, 999, true)
                RETURNING id
            """, (vertragsart_id, regel_typ, regel_key, regel_wert, einheit, bedingung))
            row = cur.fetchone()
            new_id = row_to_dict(row)['id'] if row else None
            conn.commit()
        return jsonify({'success': True, 'id': new_id}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
