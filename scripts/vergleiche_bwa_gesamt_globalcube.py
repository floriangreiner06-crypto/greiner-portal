#!/usr/bin/env python3
"""
Vergleich BWA Gesamtbetrieb (Alle Standorte) Dezember 2025 - DRIVE vs. Globalcube
"""
import requests
import json

# Globalcube Referenz-Werte für Gesamtbetrieb (aus Screenshots)
GLOBALCUBE_GESAMT = {
    'monat': {
        'umsatz': 2190718.00,
        'einsatz': 1862668.00,
        'bruttoertrag': 328050.00,
        'variable_kosten': 69374.00,
        'bruttoertrag_ii': 258676.00,
        'direkte_kosten': 189866.00,
        'deckungsbeitrag': 68810.00,
        'indirekte_kosten': 185058.00,
        'betriebsergebnis': -116248.00,
        'neutrales_ergebnis': 32629.00,
        'unternehmensergebnis': -83619.00
    },
    'kumuliert': {
        'umsatz': 10618400.00,
        'einsatz': 9191864.00,
        'bruttoertrag': 1426536.00,
        'variable_kosten': 304268.00,
        'bruttoertrag_ii': 1122268.00,
        'direkte_kosten': 659229.00,
        'deckungsbeitrag': 463039.00,
        'indirekte_kosten': 838944.00,
        'betriebsergebnis': -375905.00,
        'neutrales_ergebnis': 130172.00,
        'unternehmensergebnis': -245733.00
    }
}

def vergleiche_werte(drive_wert, globalcube_wert, name):
    """Vergleicht zwei Werte und gibt Differenz aus"""
    diff = drive_wert - globalcube_wert
    if globalcube_wert != 0:
        pct = (diff / abs(globalcube_wert)) * 100
    else:
        pct = 0 if diff == 0 else 100.0
    status = "✅" if abs(diff) < 1000 else "⚠️"
    if abs(diff) > 10000:
        status = "🚨"
    print(f"  {name}:")
    print(f"    DRIVE:      {drive_wert:>15,.2f} €")
    print(f"    Globalcube: {globalcube_wert:>15,.2f} €")
    print(f"    Differenz:  {diff:>15,.2f} € ({pct:+.2f}%) {status}")
    return diff

def main():
    print("=" * 80)
    print("BWA GESAMTBETRIEB (ALLE STANDORTE) DEZEMBER 2025 - VERGLEICH DRIVE vs. GLOBALCUBE")
    print("=" * 80)
    print()
    
    # DRIVE API aufrufen (firma=0, standort=0 = Gesamtsumme)
    url = "http://localhost:5000/api/controlling/bwa"
    params = {'monat': 12, 'jahr': 2025, 'firma': '0', 'standort': '0'}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Fehler beim API-Aufruf: {e}")
        return
    
    if data.get('status') != 'ok':
        print(f"❌ API-Fehler: {data.get('message', 'Unbekannt')}")
        return
    
    drive_monat = data['data']
    drive_ytd = data['ytd']
    
    # Monat Dezember 2025
    print("📊 MONAT DEZEMBER 2025")
    print("-" * 80)
    
    diff_umsatz = vergleiche_werte(drive_monat['umsatz'], GLOBALCUBE_GESAMT['monat']['umsatz'], 'Umsatz')
    diff_einsatz = vergleiche_werte(drive_monat['einsatz'], GLOBALCUBE_GESAMT['monat']['einsatz'], 'Einsatz')
    diff_db1 = vergleiche_werte(drive_monat['db1'], GLOBALCUBE_GESAMT['monat']['bruttoertrag'], 'Bruttoertrag (DB1)')
    diff_variable = vergleiche_werte(drive_monat['variable'], GLOBALCUBE_GESAMT['monat']['variable_kosten'], 'Variable Kosten')
    diff_db2 = vergleiche_werte(drive_monat['db2'], GLOBALCUBE_GESAMT['monat']['bruttoertrag_ii'], 'Bruttoertrag II (DB2)')
    diff_direkte = vergleiche_werte(drive_monat['direkte'], GLOBALCUBE_GESAMT['monat']['direkte_kosten'], 'Direkte Kosten')
    diff_db3 = vergleiche_werte(drive_monat['db3'], GLOBALCUBE_GESAMT['monat']['deckungsbeitrag'], 'Deckungsbeitrag (DB3)')
    diff_indirekte = vergleiche_werte(drive_monat['indirekte'], GLOBALCUBE_GESAMT['monat']['indirekte_kosten'], 'Indirekte Kosten')
    diff_be = vergleiche_werte(drive_monat['betriebsergebnis'], GLOBALCUBE_GESAMT['monat']['betriebsergebnis'], 'Betriebsergebnis')
    diff_neutral = vergleiche_werte(drive_monat.get('neutral', 0), GLOBALCUBE_GESAMT['monat']['neutrales_ergebnis'], 'Neutrales Ergebnis')
    diff_ue = vergleiche_werte(drive_monat['unternehmensergebnis'], GLOBALCUBE_GESAMT['monat']['unternehmensergebnis'], 'Unternehmensergebnis')
    
    print()
    
    # YTD (Kumuliert Sep-Dez 2025)
    print("=" * 80)
    print("📊 KUMULIERT (YTD SEP-DEZ 2025)")
    print("-" * 80)
    
    # YTD-Werte aus API extrahieren (verwendet andere Schlüssel als Monat!)
    ytd_umsatz = drive_ytd.get('umsatz', 0)
    ytd_einsatz = drive_ytd.get('einsatz', 0)
    ytd_db1 = drive_ytd.get('db1', 0)
    ytd_variable = drive_ytd.get('variable_kosten', drive_ytd.get('variable', 0))
    ytd_db2 = drive_ytd.get('db2', 0)
    ytd_direkte = drive_ytd.get('direkte_kosten', drive_ytd.get('direkte', 0))
    ytd_db3 = drive_ytd.get('db3', 0)
    ytd_indirekte = drive_ytd.get('indirekte_kosten', drive_ytd.get('indirekte', 0))
    ytd_be = drive_ytd.get('betriebsergebnis', 0)
    ytd_neutral = drive_ytd.get('neutrales_ergebnis', drive_ytd.get('neutral', 0))
    ytd_ue = drive_ytd.get('unternehmensergebnis', 0)
    
    diff_ytd_umsatz = vergleiche_werte(ytd_umsatz, GLOBALCUBE_GESAMT['kumuliert']['umsatz'], 'Umsatz')
    diff_ytd_einsatz = vergleiche_werte(ytd_einsatz, GLOBALCUBE_GESAMT['kumuliert']['einsatz'], 'Einsatz')
    diff_ytd_db1 = vergleiche_werte(ytd_db1, GLOBALCUBE_GESAMT['kumuliert']['bruttoertrag'], 'Bruttoertrag (DB1)')
    diff_ytd_variable = vergleiche_werte(ytd_variable, GLOBALCUBE_GESAMT['kumuliert']['variable_kosten'], 'Variable Kosten')
    diff_ytd_db2 = vergleiche_werte(ytd_db2, GLOBALCUBE_GESAMT['kumuliert']['bruttoertrag_ii'], 'Bruttoertrag II (DB2)')
    diff_ytd_direkte = vergleiche_werte(ytd_direkte, GLOBALCUBE_GESAMT['kumuliert']['direkte_kosten'], 'Direkte Kosten')
    diff_ytd_db3 = vergleiche_werte(ytd_db3, GLOBALCUBE_GESAMT['kumuliert']['deckungsbeitrag'], 'Deckungsbeitrag (DB3)')
    diff_ytd_indirekte = vergleiche_werte(ytd_indirekte, GLOBALCUBE_GESAMT['kumuliert']['indirekte_kosten'], 'Indirekte Kosten')
    diff_ytd_be = vergleiche_werte(ytd_be, GLOBALCUBE_GESAMT['kumuliert']['betriebsergebnis'], 'Betriebsergebnis')
    diff_ytd_neutral = vergleiche_werte(ytd_neutral, GLOBALCUBE_GESAMT['kumuliert']['neutrales_ergebnis'], 'Neutrales Ergebnis')
    diff_ytd_ue = vergleiche_werte(ytd_ue, GLOBALCUBE_GESAMT['kumuliert']['unternehmensergebnis'], 'Unternehmensergebnis')
    
    print()
    print("=" * 80)
    print("📋 ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    print(f"Monat Dezember 2025:")
    print(f"  Betriebsergebnis Differenz: {diff_be:,.2f} €")
    print(f"  Unternehmensergebnis Differenz: {diff_ue:,.2f} €")
    print()
    print(f"Kumuliert (YTD Sep-Dez 2025):")
    print(f"  Betriebsergebnis Differenz: {diff_ytd_be:,.2f} €")
    print(f"  Unternehmensergebnis Differenz: {diff_ytd_ue:,.2f} €")

if __name__ == '__main__':
    main()
