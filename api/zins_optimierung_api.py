"""
Zins-Optimierung API - TAG 78
Umbuchungs-Empfehlungen und EK-Finanzierung Analyse
MIT HYUNDAI ZINSEN!
"""
from flask import Blueprint, jsonify
from datetime import datetime

# Zentrale DB-Utilities (TAG117)
from api.db_utils import db_session

zins_api = Blueprint('zins_api', __name__)

@zins_api.route('/api/zinsen/report', methods=['GET'])
def zins_report():
    """Kompletter Zins-Report mit Empfehlungen"""
    with db_session() as conn:
        c = conn.cursor()
        return _zins_report_impl(c)

def _zins_report_impl(c):
    """Implementierung des Zins-Reports"""

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
    c.execute("""
        SELECT k.id, k.kontoname, k.sollzins, k.kreditlimit,
               (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
        FROM konten k
        WHERE k.aktiv = 1 AND k.sollzins IS NOT NULL
    """)
    for row in c.fetchall():
        saldo = row['saldo'] or 0
        if saldo < 0:
            zinsen_monat = abs(saldo) * (row['sollzins'] / 100) / 12
            total_zinsen_monat += zinsen_monat
            result['konten_sollzinsen'].append({
                'konto_id': row['id'],
                'kontoname': row['kontoname'],
                'saldo': saldo,
                'sollzins': row['sollzins'],
                'zinsen_monat': round(zinsen_monat, 2)
            })

    # 2. Stellantis über Zinsfreiheit
    c.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Stellantis'")
    stellantis_row = c.fetchone()
    stellantis_zins = stellantis_row['zinssatz'] if stellantis_row else 9.03

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
        ueber_tage = row['alter_tage'] - row['zinsfreiheit_tage']
        saldo = row['aktueller_saldo'] or 0
        zinsen = saldo * (stellantis_zins / 100) / 12
        stellantis_zinsen += zinsen
        result['stellantis_ueber_zinsfreiheit'].append({
            'vin': row['vin'],
            'modell': row['modell'],
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
        potenzielle_zinsen = (row['aktueller_saldo'] or 0) * (stellantis_zins / 100) / 12
        result['stellantis_bald_ablaufend'].append({
            'vin': row['vin'],
            'modell': row['modell'],
            'rest_tage': row['rest_tage'],
            'saldo': row['aktueller_saldo'],
            'potenzielle_zinsen_monat': round(potenzielle_zinsen, 2)
        })

    # 4. Santander
    c.execute("""
        SELECT SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen, COUNT(*) as anzahl
        FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'
    """)
    row = c.fetchone()
    if row and row['saldo']:
        result['santander'] = {
            'anzahl': row['anzahl'],
            'saldo': row['saldo'],
            'zinsen_monat': row['zinsen'] or 0
        }
        total_zinsen_monat += (row['zinsen'] or 0)

    # 5. Hyundai - JETZT MIT ECHTEN ZINSEN AUS DB!
    c.execute("""
        SELECT SUM(aktueller_saldo) as saldo, COUNT(*) as anzahl,
               SUM(zinsen_gesamt) as zinsen_gesamt, SUM(zinsen_letzte_periode) as zinsen_monat
        FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'
    """)
    row = c.fetchone()
    if row and row['saldo']:
        zinsen_monat = row['zinsen_monat'] or 0
        result['hyundai'] = {
            'anzahl': row['anzahl'],
            'saldo': row['saldo'],
            'zinsen_gesamt': row['zinsen_gesamt'] or 0,
            'zinsen_monat': round(zinsen_monat, 2)
        }
        total_zinsen_monat += zinsen_monat

    # 6. Empfehlungen generieren
    # 6a. Konten-Umbuchung
    if result['konten_sollzinsen']:
        c.execute("""
            SELECT k.kontoname,
                   (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
            FROM konten k WHERE k.aktiv = 1 AND k.sollzins IS NOT NULL
            ORDER BY (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) DESC
            LIMIT 1
        """)
        haben_konto = c.fetchone()
        if haben_konto and haben_konto['saldo'] and haben_konto['saldo'] > 10000:
            for soll in result['konten_sollzinsen']:
                result['empfehlungen'].append({
                    'typ': 'konten_umbuchung',
                    'prioritaet': 2,
                    'von': haben_konto['kontoname'],
                    'nach': soll['kontoname'],
                    'betrag': min(haben_konto['saldo'], abs(soll['saldo'])),
                    'ersparnis_monat': soll['zinsen_monat'],
                    'beschreibung': f"Umbuchung von {haben_konto['kontoname']} nach {soll['kontoname']} um Sollzinsen zu vermeiden"
                })

    # 6b. Stellantis → Santander Umfinanzierung
    if result['stellantis_ueber_zinsfreiheit']:
        c.execute("SELECT gesamt_limit FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Santander'")
        santander_limit = c.fetchone()
        santander_limit = santander_limit['gesamt_limit'] if santander_limit else 1500000

        c.execute("SELECT SUM(aktueller_saldo) FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'")
        santander_genutzt = c.fetchone()[0] or 0
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
    """Kompakte Dashboard-Daten - MIT HYUNDAI!"""
    with db_session() as conn:
        c = conn.cursor()

        # Stellantis Zinssatz
        c.execute("SELECT zinssatz FROM ek_finanzierung_konditionen WHERE finanzinstitut = 'Stellantis'")
        row = c.fetchone()
        stellantis_zins = row['zinssatz'] if row else 9.03

        # Konten im Soll
        c.execute("""
            SELECT SUM(ABS(saldo) * k.sollzins / 100 / 12) as zinsen
            FROM konten k
            JOIN (SELECT konto_id, saldo FROM salden WHERE (konto_id, datum) IN
                  (SELECT konto_id, MAX(datum) FROM salden GROUP BY konto_id)) s ON s.konto_id = k.id
            WHERE k.aktiv = 1 AND s.saldo < 0 AND k.sollzins IS NOT NULL
        """)
        konten_zinsen = c.fetchone()['zinsen'] or 0

        # Stellantis über Zinsfreiheit
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen_monat
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Stellantis'
              AND zinsfreiheit_tage IS NOT NULL
              AND alter_tage > zinsfreiheit_tage
        """)
        row = c.fetchone()
        stellantis_ueber = {
            'anzahl': row['anzahl'] or 0,
            'saldo': row['saldo'] or 0,
            'zinsen_monat': round(row['zinsen_monat'] or 0, 2)
        }

        # Stellantis bald ablaufend
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo
            FROM fahrzeugfinanzierungen
            WHERE finanzinstitut = 'Stellantis'
              AND zinsfreiheit_tage IS NOT NULL
              AND (zinsfreiheit_tage - alter_tage) BETWEEN 0 AND 14
        """)
        row = c.fetchone()
        stellantis_bald = {
            'anzahl': row['anzahl'] or 0,
            'saldo': row['saldo'] or 0
        }

        # Santander
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo, SUM(zinsen_letzte_periode) as zinsen
            FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'
        """)
        row = c.fetchone()
        santander = {
            'anzahl': row['anzahl'] or 0,
            'saldo': row['saldo'] or 0,
            'zinsen_monat': round(row['zinsen'] or 0, 2)
        }

        # === NEU: HYUNDAI ===
        c.execute("""
            SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo,
                   SUM(zinsen_gesamt) as zinsen_gesamt, SUM(zinsen_letzte_periode) as zinsen_monat
            FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'
        """)
        row = c.fetchone()
        hyundai = {
            'anzahl': row['anzahl'] or 0,
            'saldo': row['saldo'] or 0,
            'zinsen_gesamt': round(row['zinsen_gesamt'] or 0, 2),
            'zinsen_monat': round(row['zinsen_monat'] or 0, 2)
        }

        # Gesamtzinsen INKL. Hyundai
        total_zinsen = konten_zinsen + stellantis_ueber['zinsen_monat'] + santander['zinsen_monat'] + hyundai['zinsen_monat']

        return jsonify({
            'zinskosten_monat': round(total_zinsen, 2),
            'zinskosten_jahr': round(total_zinsen * 12, 2),
            'konten_sollzinsen': round(konten_zinsen, 2),
            'stellantis_ueber_zinsfreiheit': stellantis_ueber,
            'stellantis_bald_ablaufend': stellantis_bald,
            'santander_zinsen': santander['zinsen_monat'],
            'hyundai': hyundai,
            'handlungsbedarf': stellantis_ueber['anzahl'] + stellantis_bald['anzahl']
        })


@zins_api.route('/api/zinsen/umbuchung-empfehlung', methods=['GET'])
def umbuchung_empfehlung():
    """Umbuchungs-Empfehlungen mit Firmen-Beruecksichtigung"""
    with db_session() as conn:
        c = conn.cursor()
        return _umbuchung_empfehlung_impl(c)

def _umbuchung_empfehlung_impl(c):
    """Implementierung der Umbuchungs-Empfehlungen"""
    empfehlungen = []

    # Konten im Soll finden
    c.execute("""
        SELECT k.id, k.kontoname, k.firma, k.sollzins,
               (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
        FROM konten k
        WHERE k.aktiv = 1 AND k.sollzins IS NOT NULL
        AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) < 0
    """)
    soll_konten = c.fetchall()

    for soll in soll_konten:
        soll_id = soll['id']
        soll_name = soll['kontoname']
        soll_firma = soll['firma']
        sollzins = soll['sollzins']
        soll_saldo = soll['saldo']
        bedarf = abs(soll_saldo)
        zinsen_monat = bedarf * (sollzins / 100) / 12

        # Haben-Konten gleiche Firma (normale Umbuchung)
        c.execute("""
            SELECT k.id, k.kontoname,
                   (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
            FROM konten k
            WHERE k.aktiv = 1 AND k.firma = ? AND k.id != ?
            AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) > 10000
            ORDER BY saldo DESC
        """, (soll_firma, soll_id))

        for haben in c.fetchall():
            umbuchbar = min(haben['saldo'], bedarf)
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
            c.execute("""
                SELECT k.id, k.kontoname, k.firma,
                       (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) as saldo
                FROM konten k
                WHERE k.aktiv = 1
                AND k.firma != ? AND k.firma != 'EXTERN' AND k.firma IS NOT NULL
                AND (SELECT saldo FROM salden WHERE konto_id = k.id ORDER BY datum DESC LIMIT 1) > 10000
                ORDER BY saldo DESC
            """, (soll_firma,))

            for haben in c.fetchall():
                umbuchbar = min(haben['saldo'], bedarf)
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
    santander_limit = row[0] if row else 1500000
    
    c.execute("""SELECT SUM(aktueller_saldo) FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Santander'""")
    row = c.fetchone()
    santander_belegt = row[0] if row and row[0] else 0
    santander_frei = santander_limit - santander_belegt
    
    # Stellantis über Zinsfreiheit (9,03% -> 4,5% = 4,53% Ersparnis)
    c.execute("""
        SELECT vin, modell, aktueller_saldo, (alter_tage - zinsfreiheit_tage) as tage_ueber
        FROM fahrzeugfinanzierungen
        WHERE finanzinstitut = 'Stellantis' AND alter_tage > zinsfreiheit_tage
        ORDER BY tage_ueber DESC
    """)
    stellantis_ueber = c.fetchall()
    
    if stellantis_ueber and santander_frei > 50000:
        gesamt_saldo = sum(f["aktueller_saldo"] for f in stellantis_ueber)
        umfinanzierbar = min(gesamt_saldo, santander_frei)
        # Stellantis 9,03% vs Santander ~4,5% = 4,53% Ersparnis
        ersparnis_prozent = 4.53
        ersparnis_monat = umfinanzierbar * (ersparnis_prozent / 100) / 12
        empfehlungen.append({
            'typ': 'fahrzeug_umfinanzierung',
            'von': 'Stellantis',
            'nach': 'Santander',
            'anzahl_fahrzeuge': len(stellantis_ueber),
            'fahrzeuge': [{"vin": f["vin"], "modell": f["modell"].strip() if f["modell"] else "", "saldo": f["aktueller_saldo"], "tage_ueber": f["tage_ueber"]} for f in stellantis_ueber],
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
        ORDER BY tage_verbleibend ASC
    """)
    stellantis_bald = c.fetchall()
    
    if stellantis_bald:
        gesamt_saldo_bald = sum(f["aktueller_saldo"] for f in stellantis_bald)
        noch_frei = santander_frei - (umfinanzierbar if stellantis_ueber else 0)
        if noch_frei > 50000:
            ersparnis_monat_bald = min(gesamt_saldo_bald, noch_frei) * (4.53 / 100) / 12
            empfehlungen.append({
                'typ': 'fahrzeug_umfinanzierung_warnung',
                'von': 'Stellantis',
                'nach': 'Santander',
                'anzahl_fahrzeuge': len(stellantis_bald),
                'fahrzeuge': [{"vin": f["vin"], "modell": f["modell"].strip() if f["modell"] else "", "saldo": f["aktueller_saldo"], "tage_verbleibend": f["tage_verbleibend"]} for f in stellantis_bald],
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
