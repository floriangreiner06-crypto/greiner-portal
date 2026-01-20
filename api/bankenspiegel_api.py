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

        with db_session() as conn:
            cursor = conn.cursor()

            # Query - direkt auf konten mit JOIN zu salden für Sortierung nach kontoinhaber
            # TAG 180: Kreditlinie und verfügbare Kreditlinie hinzugefügt, Sortierung nach Kontoinhaber
            query = """
                SELECT
                    k.id,
                    b.bank_name,
                    k.kontoname,
                    k.iban,
                    k.kontotyp,
                    'EUR' as waehrung,
                    COALESCE(s.saldo, 0) as saldo,
                    s.datum as stand_datum,
                    1 as aktiv,
                    COALESCE(k.kreditlinie, 0) as kreditlinie,
                    CASE 
                        WHEN k.kreditlinie IS NOT NULL AND k.kreditlinie > 0 THEN
                            k.kreditlinie + COALESCE(s.saldo, 0)
                        ELSE NULL
                    END as verfuegbar,
                    k.kontoinhaber
                FROM konten k
                LEFT JOIN banken b ON k.bank_id = b.id
                LEFT JOIN (
                    SELECT konto_id, saldo, datum
                    FROM salden
                    WHERE (konto_id, datum) IN (
                        SELECT konto_id, MAX(datum)
                        FROM salden
                        GROUP BY konto_id
                    )
                ) s ON k.id = s.konto_id
                WHERE k.aktiv = true
            """

            params = []

            # Filter nach Bank - TAG 136: dynamischer Placeholder
            if bank_id:
                query += " AND k.bank_id = %s"
                params.append(bank_id)

            # TAG 180: Sortierung nach Kontoinhaber (Autohaus Greiner zuerst, dann Auto Greiner, dann Rest)
            query += """
                ORDER BY 
                    CASE 
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%autohaus greiner%' THEN 1
                        WHEN LOWER(COALESCE(k.kontoinhaber, '')) LIKE '%auto greiner%' THEN 2
                        ELSE 3
                    END,
                    k.sort_order,
                    k.kontoname
            """

            # TAG 180: Query ist bereits PostgreSQL-kompatibel (%s), kein convert_placeholders nötig
            # WICHTIG: psycopg2 wirft Fehler wenn params=[] - verwende None statt leerer Liste
            cursor.execute(query, params if params else None)
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
                    from api.db_utils import locosoft_session
                    marken_dict = {}  # {marke: {'anzahl': int, 'finanzierung': float}}
                    
                    with locosoft_session() as loco_conn:
                        loco_cursor = loco_conn.cursor()
                        
                        for row in genobank_fahrzeuge:
                            fz = row_to_dict(row, cursor)
                            vin = fz.get('vin')
                            hersteller = fz.get('hersteller')
                            saldo = float(fz.get('aktueller_saldo') or 0)
                            
                            # Bestimme Marke
                            marke = None
                            
                            # Wenn hersteller vorhanden und nicht "Unbekannt"
                            if hersteller and hersteller.strip() != '' and hersteller.strip().lower() != 'unbekannt':
                                marke = hersteller.strip()
                            else:
                                # Hole aus Locosoft
                                vin_upper = vin.upper().strip() if vin else ''
                                if vin_upper:
                                    loco_query = """
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
                                    loco_cursor.execute(loco_query, (
                                        vin_upper, vin_upper, vin_upper, vin_upper, f'%{vin_upper}%'
                                    ))
                                    loco_row = loco_cursor.fetchone()
                                    if loco_row:
                                        loco_data = row_to_dict(loco_row, loco_cursor)
                                        marke = loco_data.get('marke', 'Unbekannt')
                            
                            # Fallback
                            if not marke:
                                marke = 'Unbekannt'
                            
                            # Aggregiere
                            if marke not in marken_dict:
                                marken_dict[marke] = {'anzahl': 0, 'finanzierung': 0}
                            marken_dict[marke]['anzahl'] += 1
                            marken_dict[marke]['finanzierung'] += saldo
                    
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
                        if vin_upper:
                            loco_query = """
                                SELECT 
                                    COALESCE(
                                        NULLIF(TRIM(v.free_form_model_text), ''),
                                        NULLIF(TRIM(mo.description), ''),
                                        ''
                                    ) as modell,
                                    COALESCE(NULLIF(TRIM(m.description), ''), '') as marke
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
                            loco_cursor.execute(loco_query, (
                                vin_upper, vin_upper, vin_upper, vin_upper, f'%{vin_upper}%'
                            ))
                            loco_row = loco_cursor.fetchone()
                            if loco_row:
                                loco_data = row_to_dict(loco_row, loco_cursor)
                                
                                # Modell aktualisieren, falls leer
                                loco_modell = loco_data.get('modell', '')
                                if loco_modell and (not modell or modell.strip() == '' or modell.strip().lower() == 'unbekannt'):
                                    fz_dict['modell'] = loco_modell
                                
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
                        else:
                            # Keine VIN, verwende DB-Werte
                            if not modell or modell.strip() == '' or modell.strip().lower() == 'unbekannt':
                                fz_dict['modell'] = 'Unbekannt'
                            if not marke_db or marke_db.strip() == '' or marke_db.strip().lower() == 'unbekannt':
                                fz_dict['marke'] = 'Unbekannt'
                            else:
                                fz_dict['marke'] = marke_db
                        
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
            vin_upper = vin.upper().strip()
            
            query = """
                SELECT 
                    dv.dealer_vehicle_number as kommissionsnummer,
                    dv.dealer_vehicle_type,
                    CASE 
                        WHEN dv.dealer_vehicle_type = 'G' THEN 'Gebrauchtwagen'
                        WHEN dv.dealer_vehicle_type = 'N' THEN 'Neuwagen'
                        WHEN dv.dealer_vehicle_type = 'D' THEN 'Vorführwagen'
                        WHEN dv.dealer_vehicle_type = 'V' THEN 'Vorführwagen'
                        WHEN dv.dealer_vehicle_type = 'T' THEN 'Tageszulassung'
                        WHEN dv.dealer_vehicle_type = 'L' THEN 'Leihgabe/Mietwagen'
                        ELSE 'Unbekannt'
                    END as fahrzeugtyp,
                    v.vin,
                    v.license_plate as kennzeichen,
                    -- Modell: Priorität: free_form_model_text > models.description > Fallback
                    COALESCE(
                        NULLIF(TRIM(v.free_form_model_text), ''),
                        NULLIF(TRIM(mo.description), ''),
                        'Unbekannt'
                    ) as modell,
                    -- Marke: makes.description
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
                    -- 1. Exakte VIN (Case-insensitive)
                    UPPER(TRIM(v.vin)) = %s
                    OR
                    -- 2. VIN endet mit gesuchter VIN (für gekürzte VINs)
                    (LENGTH(v.vin) >= LENGTH(%s) AND UPPER(RIGHT(TRIM(v.vin), LENGTH(%s))) = %s)
                    OR
                    -- 3. VIN enthält gesuchte VIN (Fallback)
                    UPPER(TRIM(v.vin)) LIKE %s
                )
                ORDER BY 
                    -- Priorität: Exakte Übereinstimmung zuerst
                    CASE WHEN UPPER(TRIM(v.vin)) = %s THEN 1 ELSE 2 END,
                    dv.created_date DESC NULLS LAST
                LIMIT 1
            """
            
            # Parameter für Query
            vin_like = f'%{vin_upper}%'
            loco_cursor.execute(query, (
                vin_upper,  # Exakt
                vin_upper,  # LENGTH für RIGHT
                vin_upper,  # LENGTH für RIGHT
                vin_upper,  # RIGHT Vergleich
                vin_like,   # LIKE
                vin_upper   # ORDER BY Priorität
            ))
            row = loco_cursor.fetchone()
            
            if row:
                fahrzeug = row_to_dict(row, loco_cursor)
                
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
