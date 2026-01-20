"""
Zins-Optimierung API - TAG 78
Umbuchungs-Empfehlungen und EK-Finanzierung Analyse
MIT HYUNDAI ZINSEN!
TAG 136: PostgreSQL-kompatibel
"""
from flask import Blueprint, jsonify
from datetime import datetime

# Zentrale DB-Utilities (TAG117, TAG136: PostgreSQL-kompatibel)
from api.db_utils import db_session, row_to_dict, rows_to_list
from api.db_connection import get_db_type, convert_placeholders

zins_api = Blueprint('zins_api', __name__)

@zins_api.route('/api/zinsen/report', methods=['GET'])
def zins_report():
    """Kompletter Zins-Report mit Empfehlungen"""
    with db_session() as conn:
        c = conn.cursor()
        return _zins_report_impl(c)

def _zins_report_impl(c):
    """Implementierung des Zins-Reports
    TAG 136: PostgreSQL-kompatibel
    """
    # TAG 136: Boolean-Check für PostgreSQL/SQLite
    aktiv_check = "k.aktiv = true" if get_db_type() == 'postgresql' else "k.aktiv = true"

    result = {
        'timestamp': datetime.now().isoformat(),
        'konten_sollzinsen': [],
        'stellantis_ueber_zinsfreiheit': [],
        'stellantis_bald_ablaufend': [],
        'santander': {},
        'hyundai': {},
        'empfehlungen': [],
        'zusammenfassung': {}
    }

    total_zinsen_monat = 0

    # 1. Konten im Soll
    c.execute(f"""
        SELECT k.id, k.kontoname, k.sollzins, k.kreditlimit,
               (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
        FROM konten k
        WHERE {aktiv_check} AND k.sollzins IS NOT NULL
    """)
    for row in c.fetchall():
        r = row_to_dict(row)
        saldo = float(r['saldo'] or 0)
        if saldo < 0:
            zinsen_monat = abs(saldo) * (float(r['sollzins']) / 100) / 12
            total_zinsen_monat += zinsen_monat
            result['konten_sollzinsen'].append({
                'konto_id': r['id'],
                'kontoname': r['kontoname'],
                'saldo': saldo,
                'sollzins': float(r['sollzins']),
                'zinsen_monat': round(zinsen_monat, 2)
            })

    # 2. Stellantis über Zinsfreiheit
    c.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Stellantis'")
    stellantis_row = c.fetchone()
    if stellantis_row:
        sr = row_to_dict(stellantis_row)
        stellantis_zins = float(sr['zinssatz']) if sr['zinssatz'] else 9.03
    else:
        stellantis_zins = 9.03

    c.execute("""
        SELECT vin, modell, alter_tage, zinsfreiheit_tage, aktueller_saldo
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis'
          AND zinsfreiheit_tage IS NOT NULL
          AND alter_tage > zinsfreiheit_tage
        ORDER BY aktueller_saldo DESC
    """)
    stellantis_zinsen = 0
    for row in c.fetchall():
        r = row_to_dict(row)
        ueber_tage = int(r['alter_tage'] or 0) - int(r['zinsfreiheit_tage'] or 0)
        saldo = float(r['aktueller_saldo'] or 0)
        zinsen = saldo * (stellantis_zins / 100) / 12
        stellantis_zinsen += zinsen
        result['stellantis_ueber_zinsfreiheit'].append({
            'vin': r['vin'],
            'modell': r['modell'],
            'tage_ueber': ueber_tage,
            'saldo': saldo,
            'zinsen_monat': round(zinsen, 2)
        })
    total_zinsen_monat += stellantis_zinsen

    # 3. Stellantis bald ablaufend (< 14 Tage)
    c.execute("""
        SELECT vin, modell, zinsfreiheit_tage - alter_tage as rest_tage, aktueller_saldo
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis'
          AND zinsfreiheit_tage IS NOT NULL
          AND (zinsfreiheit_tage - alter_tage) BETWEEN 0 AND 14
        ORDER BY (zinsfreiheit_tage - alter_tage) ASC
    """)
    for row in c.fetchall():
        r = row_to_dict(row)
        potenzielle_zinsen = float(r['aktueller_saldo'] or 0) * (stellantis_zins / 100) / 12
        result['stellantis_bald_ablaufend'].append({
            'vin': r['vin'],
            'modell': r['modell'],
            'rest_tage': r['rest_tage'],
            'saldo': float(r['aktueller_saldo'] or 0),
            'potenzielle_zinsen_monat': round(potenzielle_zinsen, 2)
        })

    # 4. Santander
    c.execute("""
        SELECT SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen, COUNT(*) as anzahl
        FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'
    """)
    row = c.fetchone()
    if row:
        r = row_to_dict(row)
        if r['saldo']:
            result['santander'] = {
                'anzahl': int(r['anzahl'] or 0),
                'saldo': float(r['saldo'] or 0),
                'zinsen_monat': float(r['zinsen'] or 0)
            }
            total_zinsen_monat += float(r['zinsen'] or 0)

    # 5. Hyundai - JETZT MIT ECHTEN ZINSEN AUS DB!
    c.execute("""
        SELECT SUM(aktueller_saldo) as saldo, COUNT(*) as anzahl,
               SUM(zinsen_gesamt) as zinsen_gesamt, SUM(zinsen_letzte_periode) as zinsen_monat
        FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'
    """)
    row = c.fetchone()
    if row:
        r = row_to_dict(row)
        if r['saldo']:
            zinsen_monat = float(r['zinsen_monat'] or 0)
            result['hyundai'] = {
                'anzahl': int(r['anzahl'] or 0),
                'saldo': float(r['saldo'] or 0),
                'zinsen_gesamt': float(r['zinsen_gesamt'] or 0),
                'zinsen_monat': round(zinsen_monat, 2)
            }
            total_zinsen_monat += zinsen_monat

    # 6. Empfehlungen generieren
    # 6a. Konten-Umbuchung
    if result['konten_sollzinsen']:
        c.execute(f"""
            SELECT k.kontoname,
                   (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
            FROM konten k WHERE {aktiv_check} AND k.sollzins IS NOT NULL
            ORDER BY (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) DESC
            LIMIT 1
        """)
        haben_konto = c.fetchone()
        if haben_konto:
            hk = row_to_dict(haben_konto)
            if hk['saldo'] and float(hk['saldo']) > 10000:
                for soll in result['konten_sollzinsen']:
                    result['empfehlungen'].append({
                        'typ': 'konten_umbuchung',
                        'prioritaet': 2,
                        'von': hk['kontoname'],
                        'nach': soll['kontoname'],
                        'betrag': min(float(hk['saldo']), abs(soll['saldo'])),
                        'ersparnis_monat': soll['zinsen_monat'],
                        'beschreibung': f"Umbuchung von {hk['kontoname']} nach {soll['kontoname']} um Sollzinsen zu vermeiden"
                    })

    # 6b. Stellantis → Santander Umfinanzierung
    if result['stellantis_ueber_zinsfreiheit']:
        c.execute("SELECT gesamt_limit FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Santander'")
        santander_limit_row = c.fetchone()
        if santander_limit_row:
            sl = row_to_dict(santander_limit_row)
            santander_limit = float(sl['gesamt_limit']) if sl['gesamt_limit'] else 1500000
        else:
            santander_limit = 1500000

        c.execute("SELECT SUM(aktueller_saldo) as summe FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'")
        sg_row = c.fetchone()
        sg = row_to_dict(sg_row) if sg_row else {}
        santander_genutzt = float(sg.get('summe') or 0)
        santander_frei = santander_limit - santander_genutzt

        umfinanzierung_summe = sum(f['saldo'] for f in result['stellantis_ueber_zinsfreiheit'])
        umfinanzierung_moeglich = min(umfinanzierung_summe, santander_frei)

        if umfinanzierung_moeglich > 50000:
            # Ersparnis: Stellantis 9.03% → Santander ~4.5%
            ersparnis_prozent = stellantis_zins - 4.5
            ersparnis_monat = umfinanzierung_moeglich * (ersparnis_prozent / 100) / 12

            result['empfehlungen'].append({
                'typ': 'umfinanzierung',
                'prioritaet': 1,
                'von': 'Stellantis',
                'nach': 'Santander',
                'betrag': umfinanzierung_moeglich,
                'ersparnis_monat': round(ersparnis_monat, 2),
                'beschreibung': f"Umfinanzierung von {len(result['stellantis_ueber_zinsfreiheit'])} Fahrzeugen (über Zinsfreiheit) zu Santander"
            })

    # Zusammenfassung
    result['zusammenfassung'] = {
        'zinskosten_monat_bekannt': round(total_zinsen_monat, 2),
        'zinskosten_jahr_bekannt': round(total_zinsen_monat * 12, 2),
        'anzahl_empfehlungen': len(result['empfehlungen']),
        'potenzielle_ersparnis_monat': round(sum(e['ersparnis_monat'] for e in result['empfehlungen']), 2)
    }

    return jsonify(result)


@zins_api.route('/api/zinsen/dashboard', methods=['GET'])
def zins_dashboard():
    """Kompakte Dashboard-Daten - MIT HYUNDAI!
    TAG 136: PostgreSQL-kompatibel
    """
    with db_session() as conn:
        c = conn.cursor()

        # TAG 136: Boolean-Check für PostgreSQL/SQLite
        aktiv_check = "k.aktiv = true" if get_db_type() == 'postgresql' else "k.aktiv = true"

        # Stellantis Zinssatz
        c.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Stellantis'")
        row = c.fetchone()
        if row:
            r = row_to_dict(row)
            stellantis_zins = float(r['zinssatz']) if r['zinssatz'] else 9.03
        else:
            stellantis_zins = 9.03

        # Konten im Soll - Subquery für PostgreSQL-Kompatibilität
        c.execute(f"""
            SELECT SUM(ABS(s.saldo) * k.sollzins / 100 / 12) as zinsen
            FROM konten k
            JOIN (
                SELECT s1.konto_id, s1.saldo
                FROM salden s1
                JOIN (SELECT konto_id, MAX(datum) as max_datum FROM salden GROUP BY konto_id) s2
                  ON s1.konto_id = s2.konto_id AND s1.datum = s2.max_datum
            ) s ON s.konto_id = k.id
            WHERE {aktiv_check} AND s.saldo < 0 AND k.sollzins IS NOT NULL
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        konten_zinsen = float(r.get('zinsen') or 0)

        # Stellantis GESAMT (alle aktiven Fahrzeuge für Tabelle)
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Stellantis' AND aktiv = true
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        stellantis_gesamt = {
            'anzahl': int(r.get('anzahl') or 0),
            'saldo': float(r.get('saldo') or 0)
        }
        
        # Stellantis über Zinsfreiheit (nur für Zinsen-Berechnung)
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen_monat
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Stellantis'
              AND aktiv = true
              AND zinsfreiheit_tage IS NOT NULL
              AND alter_tage > zinsfreiheit_tage
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        stellantis_ueber = {
            'anzahl': int(r.get('anzahl') or 0),
            'saldo': float(r.get('saldo') or 0),
            'zinsen_monat': round(float(r.get('zinsen_monat') or 0), 2)
        }

        # Stellantis bald ablaufend
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Stellantis'
              AND aktiv = true
              AND zinsfreiheit_tage IS NOT NULL
              AND (zinsfreiheit_tage - alter_tage) BETWEEN 0 AND 14
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        stellantis_bald = {
            'anzahl': int(r.get('anzahl') or 0),
            'saldo': float(r.get('saldo') or 0)
        }

        # Santander
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen
            FROM fahrzeugfinanzierungen 
            WHERE finanzinstitut = 'Santander' AND aktiv = true
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        santander = {
            'anzahl': int(r.get('anzahl') or 0),
            'saldo': float(r.get('saldo') or 0),
            'zinsen_monat': round(float(r.get('zinsen') or 0), 2)
        }

        # === NEU: HYUNDAI ===
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo,
                   SUM(zinsen_gesamt) as zinsen_gesamt, SUM(zinsen_letzte_periode) as zinsen_monat
            FROM fahrzeugfinanzierungen 
            WHERE finanzinstitut = 'Hyundai Finance' AND aktiv = true
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        hyundai = {
            'anzahl': int(r.get('anzahl') or 0),
            'saldo': float(r.get('saldo') or 0),
            'zinsen_gesamt': round(float(r.get('zinsen_gesamt') or 0), 2),
            'zinsen_monat': round(float(r.get('zinsen_monat') or 0), 2)
        }

        # === NEU: GENOBANK ===
        # Genobank Zinssatz aus Konto 4700057908 (sollzins-Feld) - über MT940 verfügbar
        # WICHTIG: Genobank-Finanzierungen sind im Konto 4700057908 als Soll-Saldo
        # Die Zinsen werden bereits über "Konten Sollzinsen" erfasst!
        # Hier zeigen wir nur die Fahrzeug-Anzahl und den Saldo für die Übersicht
        c.execute("""
            SELECT k.id, k.kontoname, k.sollzins, 
                   (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as konto_saldo
            FROM konten k
            WHERE k.kontonummer = '4700057908' OR k.iban LIKE '%4700057908%'
            LIMIT 1
        """)
        row = c.fetchone()
        genobank_zins = None
        genobank_konto_saldo = None
        genobank_konto_id = None
        
        if row:
            r = row_to_dict(row)
            genobank_konto_id = r.get('id')
            genobank_zins = float(r['sollzins']) if r.get('sollzins') else None
            genobank_konto_saldo = float(r['konto_saldo'] or 0)
        
        # Fallback: ek_finanzierung_konditionen
        if genobank_zins is None:
            c.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Genobank'")
            row = c.fetchone()
            if row:
                r = row_to_dict(row)
                genobank_zins = float(r['zinssatz']) if r['zinssatz'] else 5.5
            else:
                genobank_zins = 5.5  # Default
        
        # Genobank: Alle Fahrzeuge haben Zinsen (keine Zinsfreiheit)
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo
            FROM fahrzeugfinanzierungen 
            WHERE finanzinstitut = 'Genobank' AND aktiv = true
        """)
        row = c.fetchone()
        r = row_to_dict(row) if row else {}
        genobank_anzahl = int(r.get('anzahl') or 0)
        genobank_saldo = float(r.get('saldo') or 0)
        
        # Zinsen berechnen: Saldo * Zinssatz / 12 (monatlich)
        # WICHTIG: Genobank-Finanzierungen sind im Konto 4700057908 als Soll-Saldo
        # Die Zinsen werden bereits über "Konten Sollzinsen" erfasst!
        # Hier berechnen wir nur die Zinsen für die einzelnen Fahrzeuge (falls separat benötigt)
        genobank_zinsen_monat = (genobank_saldo * genobank_zins / 100 / 12) if genobank_saldo > 0 else 0
        
        # Prüfe ob Genobank-Konto bereits in "Konten Sollzinsen" enthalten ist
        # Falls ja, sollten wir die Zinsen nicht doppelt zählen
        genobank_in_konten_zinsen = False
        if genobank_konto_id:
            # Prüfe ob dieses Konto bereits in konten_zinsen enthalten ist
            c.execute(f"""
                SELECT COUNT(*) as count
                FROM konten k
                JOIN (
                    SELECT s1.konto_id, s1.saldo
                    FROM salden s1
                    JOIN (SELECT konto_id, MAX(datum) as max_datum FROM salden GROUP BY konto_id) s2
                      ON s1.konto_id = s2.konto_id AND s1.datum = s2.max_datum
                ) s ON s.konto_id = k.id
                WHERE k.id = {genobank_konto_id} AND {aktiv_check} AND s.saldo < 0 AND k.sollzins IS NOT NULL
            """)
            row = c.fetchone()
            if row:
                r = row_to_dict(row)
                genobank_in_konten_zinsen = (r.get('count', 0) > 0)
        
        genobank = {
            'anzahl': genobank_anzahl,
            'saldo': genobank_saldo,
            'zinsen_monat': round(genobank_zinsen_monat, 2),
            'zinssatz': genobank_zins,
            'konto_saldo': genobank_konto_saldo,  # Saldo des Kontos 4700057908
            'konto_id': genobank_konto_id,
            'in_konten_zinsen': genobank_in_konten_zinsen  # Flag: Bereits in "Konten Sollzinsen" enthalten
        }

        # Gesamtzinsen INKL. Hyundai + Genobank
        # WICHTIG: Genobank-Zinsen sind bereits in konten_zinsen enthalten (Konto 4700057908)
        # Nur hinzufügen wenn nicht bereits in konten_zinsen enthalten
        genobank_zinsen_fuer_gesamt = 0
        if not genobank.get('in_konten_zinsen', False):
            # Genobank-Zinsen noch nicht in konten_zinsen enthalten, separat hinzufügen
            genobank_zinsen_fuer_gesamt = genobank['zinsen_monat']
        
        total_zinsen = konten_zinsen + stellantis_ueber['zinsen_monat'] + santander['zinsen_monat'] + hyundai['zinsen_monat'] + genobank_zinsen_fuer_gesamt

        return jsonify({
            'zinskosten_monat': round(total_zinsen, 2),
            'zinskosten_jahr': round(total_zinsen * 12, 2),
            'konten_sollzinsen': round(konten_zinsen, 2),
            'stellantis_gesamt': stellantis_gesamt,  # TAG 172: Alle aktiven Fahrzeuge für Tabelle
            'stellantis_ueber_zinsfreiheit': stellantis_ueber,  # Nur die mit Zinsen
            'stellantis_bald_ablaufend': stellantis_bald,
            'santander': santander,  # TAG 172: Vollständige Daten (anzahl, saldo, zinsen_monat)
            'hyundai': hyundai,
            'genobank': genobank,  # Genobank Finanzierungen
            'handlungsbedarf': stellantis_ueber['anzahl'] + stellantis_bald['anzahl']
        })


@zins_api.route('/api/zinsen/umbuchung-empfehlung', methods=['GET'])
def umbuchung_empfehlung():
    """Umbuchungs-Empfehlungen mit Firmen-Beruecksichtigung"""
    with db_session() as conn:
        c = conn.cursor()
        return _umbuchung_empfehlung_impl(c)

def _umbuchung_empfehlung_impl(c):
    """Implementierung der Umbuchungs-Empfehlungen
    TAG 136: PostgreSQL-kompatibel
    """
    # TAG 136: Boolean-Check für PostgreSQL/SQLite
    aktiv_check = "k.aktiv = true" if get_db_type() == 'postgresql' else "k.aktiv = true"
    empfehlungen = []

    # Konten im Soll finden
    c.execute(f"""
        SELECT k.id, k.kontoname, k.firma, k.sollzins,
               (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
        FROM konten k
        WHERE {aktiv_check} AND k.sollzins IS NOT NULL
        AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) < 0
    """)
    soll_konten = rows_to_list(c.fetchall())

    for soll in soll_konten:
        soll_id = soll['id']
        soll_name = soll['kontoname']
        soll_firma = soll['firma']
        sollzins = float(soll['sollzins'] or 0)
        soll_saldo = float(soll['saldo'] or 0)
        bedarf = abs(soll_saldo)
        zinsen_monat = bedarf * (sollzins / 100) / 12

        # Haben-Konten gleiche Firma (normale Umbuchung)
        c.execute(convert_placeholders(f"""
            SELECT k.id, k.kontoname,
                   (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
            FROM konten k
            WHERE {aktiv_check} AND k.firma = %s AND k.id != %s
            AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) > 10000
            ORDER BY (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) DESC
        """), (soll_firma, soll_id))

        for haben_row in c.fetchall():
            haben = row_to_dict(haben_row)
            umbuchbar = min(float(haben['saldo'] or 0), bedarf)
            ersparnis = umbuchbar * (sollzins / 100) / 12
            empfehlungen.append({
                'von_konto': haben['kontoname'],
                'nach_konto': soll_name,
                'betrag': umbuchbar,
                'firma': soll_firma,
                'typ': 'normale_umbuchung',
                'beschreibung': 'Bank an Bank (gleiche Firma)',
                'ersparnis_monat': round(ersparnis, 2),
                'ersparnis_jahr': round(ersparnis * 12, 2),
                'prioritaet': 1
            })
            bedarf -= umbuchbar
            if bedarf <= 0:
                break

        # Falls noch Bedarf: Andere Firmen (Privatentnahme)
        if bedarf > 10000:
            c.execute(convert_placeholders(f"""
                SELECT k.id, k.kontoname, k.firma,
                       (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
                FROM konten k
                WHERE {aktiv_check}
                AND k.firma != %s AND k.firma != 'EXTERN' AND k.firma IS NOT NULL
                AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) > 10000
                ORDER BY (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) DESC
            """), (soll_firma,))

            for haben_row in c.fetchall():
                haben = row_to_dict(haben_row)
                umbuchbar = min(float(haben['saldo'] or 0), bedarf)
                ersparnis = umbuchbar * (sollzins / 100) / 12
                empfehlungen.append({
                    'von_konto': haben['kontoname'],
                    'von_firma': haben['firma'],
                    'nach_konto': soll_name,
                    'nach_firma': soll_firma,
                    'betrag': umbuchbar,
                    'typ': 'privatentnahme_einlage',
                    'beschreibung': 'Privatentnahme an Bank / Bank an Privateinlage',
                    'ersparnis_monat': round(ersparnis, 2),
                    'ersparnis_jahr': round(ersparnis * 12, 2),
                    'prioritaet': 2
                })
                bedarf -= umbuchbar
                if bedarf <= 0:
                    break


    # ============================================
    # FAHRZEUG-UMFINANZIERUNGEN (Stellantis -> Santander)
    # ============================================

    # Santander freies Limit prüfen
    c.execute("""SELECT gesamt_limit FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Santander'""")
    row = c.fetchone()
    if row:
        r = row_to_dict(row)
        santander_limit = float(r['gesamt_limit']) if r['gesamt_limit'] else 1500000
    else:
        santander_limit = 1500000

    c.execute("""SELECT SUM(aktueller_saldo) as summe FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'""")
    row = c.fetchone()
    r = row_to_dict(row) if row else {}
    santander_belegt = float(r.get('summe') or 0)
    santander_frei = santander_limit - santander_belegt

    # Stellantis über Zinsfreiheit (9,03% -> 4,5% = 4,53% Ersparnis)
    c.execute("""
        SELECT vin, modell, aktueller_saldo, (alter_tage - zinsfreiheit_tage) as tage_ueber
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis' AND alter_tage > zinsfreiheit_tage
        ORDER BY (alter_tage - zinsfreiheit_tage) DESC
    """)
    stellantis_ueber = rows_to_list(c.fetchall())

    umfinanzierbar = 0
    if stellantis_ueber and santander_frei > 50000:
        gesamt_saldo = sum(float(f["aktueller_saldo"] or 0) for f in stellantis_ueber)
        umfinanzierbar = min(gesamt_saldo, santander_frei)
        # Stellantis 9,03% vs Santander ~4,5% = 4,53% Ersparnis
        ersparnis_prozent = 4.53
        ersparnis_monat = umfinanzierbar * (ersparnis_prozent / 100) / 12
        empfehlungen.append({
            'typ': 'fahrzeug_umfinanzierung',
            'von': 'Stellantis',
            'nach': 'Santander',
            'anzahl_fahrzeuge': len(stellantis_ueber),
            'fahrzeuge': [{"vin": f["vin"], "modell": (f["modell"] or "").strip(), "saldo": float(f["aktueller_saldo"] or 0), "tage_ueber": int(f["tage_ueber"] or 0)} for f in stellantis_ueber],
            'betrag': round(gesamt_saldo, 2),
            'santander_frei': round(santander_frei, 2),
            'beschreibung': f'Umfinanzierung von {len(stellantis_ueber)} Fahrzeugen (über Zinsfreiheit) zu Santander',
            'ersparnis_monat': round(ersparnis_monat, 2),
            'ersparnis_jahr': round(ersparnis_monat * 12, 2),
            'prioritaet': 1
        })

    # Stellantis bald ablaufend (< 14 Tage)
    c.execute("""
        SELECT vin, modell, aktueller_saldo, (zinsfreiheit_tage - alter_tage) as tage_verbleibend
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis'
        AND alter_tage <= zinsfreiheit_tage
        AND (zinsfreiheit_tage - alter_tage) <= 14
        ORDER BY (zinsfreiheit_tage - alter_tage) ASC
    """)
    stellantis_bald = rows_to_list(c.fetchall())

    if stellantis_bald:
        gesamt_saldo_bald = sum(float(f["aktueller_saldo"] or 0) for f in stellantis_bald)
        noch_frei = santander_frei - umfinanzierbar
        if noch_frei > 50000:
            ersparnis_monat_bald = min(gesamt_saldo_bald, noch_frei) * (4.53 / 100) / 12
            empfehlungen.append({
                'typ': 'fahrzeug_umfinanzierung_warnung',
                'von': 'Stellantis',
                'nach': 'Santander',
                'anzahl_fahrzeuge': len(stellantis_bald),
                'fahrzeuge': [{"vin": f["vin"], "modell": (f["modell"] or "").strip(), "saldo": float(f["aktueller_saldo"] or 0), "tage_verbleibend": int(f["tage_verbleibend"] or 0)} for f in stellantis_bald],
                'betrag': round(gesamt_saldo_bald, 2),
                'santander_noch_frei': round(noch_frei, 2),
                'beschreibung': f'{len(stellantis_bald)} Fahrzeuge mit bald ablaufender Zinsfreiheit (<14 Tage) - Umfinanzierung prüfen',
                'potenzielle_zinsen_monat': round(gesamt_saldo_bald * (9.03 / 100) / 12, 2),
                'ersparnis_monat': round(ersparnis_monat_bald, 2),
                'ersparnis_jahr': round(ersparnis_monat_bald * 12, 2),
                'prioritaet': 2
            })

    return jsonify({
        'empfehlungen': sorted(empfehlungen, key=lambda x: x['prioritaet']),
        'gesamt_ersparnis_monat': round(sum(e['ersparnis_monat'] for e in empfehlungen), 2),
        'gesamt_ersparnis_jahr': round(sum(e['ersparnis_jahr'] for e in empfehlungen), 2)
    })
