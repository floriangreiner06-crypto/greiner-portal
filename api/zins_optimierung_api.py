"""
Zins-Optimierung API - TAG 77
Umbuchungs-Empfehlungen und EK-Finanzierung Analyse
"""
from flask import Blueprint, jsonify
import sqlite3
from datetime import datetime

zins_api = Blueprint('zins_api', __name__)

def get_db():
    conn = sqlite3.connect('data/greiner_controlling.db')
    conn.row_factory = sqlite3.Row
    return conn

@zins_api.route('/api/zinsen/report', methods=['GET'])
def zins_report():
    """Kompletter Zins-Report mit Empfehlungen"""
    conn = get_db()
    c = conn.cursor()
    
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
    
    # 5. Hyundai
    c.execute("""
        SELECT SUM(aktueller_saldo) as saldo, COUNT(*) as anzahl
        FROM fahrzeugfinanzierungen WHERE finanzinstitut = 'Hyundai Finance'
    """)
    row = c.fetchone()
    if row and row['saldo']:
        geschaetzt = row['saldo'] * (4.68 / 100) / 12
        result['hyundai'] = {
            'anzahl': row['anzahl'],
            'saldo': row['saldo'],
            'zinsen_monat_geschaetzt': round(geschaetzt, 2)
        }
    
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
    
    conn.close()
    return jsonify(result)


@zins_api.route('/api/zinsen/dashboard', methods=['GET'])
def zins_dashboard():
    """Kompakte Dashboard-Daten"""
    conn = get_db()
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
        SELECT COUNT(*) as anzahl, SUM(aktueller_saldo) as saldo
        FROM fahrzeugfinanzierungen 
        WHERE finanzinstitut = 'Stellantis'
          AND zinsfreiheit_tage IS NOT NULL 
          AND alter_tage > zinsfreiheit_tage
    """)
    row = c.fetchone()
    stellantis_ueber = {
        'anzahl': row['anzahl'] or 0,
        'saldo': row['saldo'] or 0,
        'zinsen_monat': round((row['saldo'] or 0) * (stellantis_zins / 100) / 12, 2)
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
        'zinsen_monat': row['zinsen'] or 0
    }
    
    total_zinsen = konten_zinsen + stellantis_ueber['zinsen_monat'] + santander['zinsen_monat']
    
    conn.close()
    
    return jsonify({
        'zinskosten_monat': round(total_zinsen, 2),
        'zinskosten_jahr': round(total_zinsen * 12, 2),
        'konten_sollzinsen': round(konten_zinsen, 2),
        'stellantis_ueber_zinsfreiheit': stellantis_ueber,
        'stellantis_bald_ablaufend': stellantis_bald,
        'santander_zinsen': santander['zinsen_monat'],
        'handlungsbedarf': stellantis_ueber['anzahl'] + stellantis_bald['anzahl']
    })
