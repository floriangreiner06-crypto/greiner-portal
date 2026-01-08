"""
Analyse der CSV-Datei mit offenen Aufträgen aus Locosoft
"""
import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.werkstatt_data import WerkstattData

def parse_german_number(value):
    """Konvertiert deutsche Zahlen (z.B. '1.234,56') zu float"""
    if not value or value.strip() == '':
        return 0.0
    # Entferne Tausender-Trennzeichen und ersetze Komma durch Punkt
    return float(value.replace('.', '').replace(',', '.'))

def analyse_csv():
    """Analysiert die CSV-Datei mit offenen Aufträgen"""
    
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'docs', 'Analyse_offene_auftraege', 'offene.csv')
    
    print("=" * 80)
    print("ANALYSE: Offene Aufträge aus CSV (Locosoft Export)")
    print("=" * 80)
    
    total_lohn = 0.0
    total_et = 0.0
    total_gesamt = 0.0
    anzahl_auftraege = 0
    anzahl_mit_lohn = 0
    anzahl_mit_et = 0
    
    # Spalten-Indizes (basierend auf Header)
    # Auftragsnummer, Auftragsdatum, ..., Summe Lohn, Summe ET, Gesamtsumme
    auftrag_nr_idx = 0
    summe_lohn_idx = None
    summe_et_idx = None
    gesamtsumme_idx = None
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter='\t')
        
        # Header-Zeile finden (Zeile mit "Auftragsnummer")
        header_found = False
        for row in reader:
            if len(row) > 0 and 'Auftragsnummer' in row[0]:
                # Header gefunden - Spalten-Indizes bestimmen
                for i, col in enumerate(row):
                    if 'Summe Lohn' in col:
                        summe_lohn_idx = i
                    elif 'Summe ET' in col:
                        summe_et_idx = i
                    elif 'Gesamtsumme' in col:
                        gesamtsumme_idx = i
                header_found = True
                print(f"\nHeader gefunden:")
                print(f"  Summe Lohn: Spalte {summe_lohn_idx}")
                print(f"  Summe ET: Spalte {summe_et_idx}")
                print(f"  Gesamtsumme: Spalte {gesamtsumme_idx}")
                break
        
        if not header_found:
            print("❌ Header nicht gefunden!")
            return
        
        # Daten-Zeilen verarbeiten
        for row in reader:
            if len(row) < max(summe_lohn_idx or 0, summe_et_idx or 0, gesamtsumme_idx or 0):
                continue
            
            auftrag_nr = row[auftrag_nr_idx].strip()
            if not auftrag_nr or auftrag_nr == '' or auftrag_nr == 'Abgrenzungen:':
                continue
            
            try:
                lohn = parse_german_number(row[summe_lohn_idx] if summe_lohn_idx else '0')
                et = parse_german_number(row[summe_et_idx] if summe_et_idx else '0')
                gesamt = parse_german_number(row[gesamtsumme_idx] if gesamtsumme_idx else '0')
                
                total_lohn += lohn
                total_et += et
                total_gesamt += gesamt
                anzahl_auftraege += 1
                
                if lohn > 0:
                    anzahl_mit_lohn += 1
                if et > 0:
                    anzahl_mit_et += 1
                    
            except (ValueError, IndexError) as e:
                # Überspringe ungültige Zeilen
                continue
    
    print(f"\n📊 ERGEBNISSE (CSV-Analyse):")
    print(f"  Anzahl Aufträge: {anzahl_auftraege}")
    print(f"  Aufträge mit Lohn: {anzahl_mit_lohn}")
    print(f"  Aufträge mit ET: {anzahl_mit_et}")
    print(f"  Summe Lohn: {total_lohn:,.2f} EUR")
    print(f"  Summe ET: {total_et:,.2f} EUR")
    print(f"  Gesamtsumme: {total_gesamt:,.2f} EUR")
    
    print(f"\n📊 DRIVE-WERTE (aktuell):")
    data_all = WerkstattData.get_finanz_kpis(betrieb=None)
    print(f"  Offener Lohn: {data_all['offener_lohn']:,.2f} EUR")
    print(f"  Offene Teile: {data_all['offene_teile']:,.2f} EUR")
    
    print(f"\n📊 DRIVE-WERTE (Deggendorf, Betrieb=1):")
    data_deg = WerkstattData.get_finanz_kpis(betrieb=1)
    print(f"  Offener Lohn: {data_deg['offener_lohn']:,.2f} EUR")
    print(f"  Offene Teile: {data_deg['offene_teile']:,.2f} EUR")
    
    print(f"\n" + "=" * 80)
    print("VERGLEICH:")
    print("=" * 80)
    print(f"CSV (Gesamtbetrieb):")
    print(f"  Lohn: {total_lohn:,.2f} EUR")
    print(f"  ET: {total_et:,.2f} EUR")
    print(f"\nDRIVE (Gesamtbetrieb):")
    print(f"  Lohn: {data_all['offener_lohn']:,.2f} EUR")
    print(f"  ET: {data_all['offene_teile']:,.2f} EUR")
    print(f"\nDifferenz:")
    print(f"  Lohn: {total_lohn - data_all['offener_lohn']:,.2f} EUR ({((total_lohn - data_all['offener_lohn']) / total_lohn * 100) if total_lohn > 0 else 0:.1f}%)")
    print(f"  ET: {total_et - data_all['offene_teile']:,.2f} EUR ({((total_et - data_all['offene_teile']) / total_et * 100) if total_et > 0 else 0:.1f}%)")
    
    print(f"\n⚠️  PROBLEM-ANALYSE:")
    if abs(total_lohn - data_all['offener_lohn']) > 100:
        print(f"  ❌ Lohn-Werte weichen stark ab!")
        print(f"     Mögliche Ursachen:")
        print(f"     1. CSV verwendet VK-Wert, DRIVE verwendet net_price_in_order")
        print(f"     2. CSV enthält alle Aufträge, DRIVE filtert nach invoice_number IS NULL")
        print(f"     3. CSV enthält möglicherweise auch teilweise fakturierte Aufträge")
    if abs(total_et - data_all['offene_teile']) > 100:
        print(f"  ❌ ET-Werte weichen stark ab!")
        print(f"     Mögliche Ursachen:")
        print(f"     1. CSV verwendet VK-Wert, DRIVE verwendet usage_value (Einsatzwert)")
        print(f"     2. CSV enthält alle Aufträge, DRIVE filtert nach invoice_number IS NULL")

if __name__ == '__main__':
    analyse_csv()

