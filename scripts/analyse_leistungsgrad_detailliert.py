#!/usr/bin/env python3
"""
Detaillierte Analyse der Leistungsgrad-Berechnung
Vergleicht DRIVE-Berechnung mit Locosoft-Logik

Datum: 2026-01-XX
"""

import sys
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Any

# Projekt-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.werkstatt_data import WerkstattData
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def parse_zeit_string(zeit_str: str) -> float:
    """
    Konvertiert Zeit-String (z.B. "1:06" oder "1:06:00") in Minuten.
    """
    if not zeit_str or str(zeit_str).strip() == '':
        return 0.0
    
    try:
        parts = str(zeit_str).strip().split(':')
        if len(parts) == 2:
            # Format: "1:06" = 1 Stunde 6 Minuten
            stunden = int(parts[0])
            minuten = int(parts[1])
            return stunden * 60 + minuten
        elif len(parts) == 3:
            # Format: "1:06:00" = 1 Stunde 6 Minuten 0 Sekunden
            stunden = int(parts[0])
            minuten = int(parts[1])
            sekunden = int(parts[2])
            return stunden * 60 + minuten + sekunden / 60.0
        else:
            # Versuche als Zahl zu interpretieren
            return float(zeit_str)
    except:
        return 0.0


def analyse_mechaniker_detailliert(
    mechaniker_nr: int,
    von: date,
    bis: date,
    excel_daten: List[Dict[str, Any]] = None
):
    """
    Analysiert die Leistungsgrad-Berechnung für einen Mechaniker detailliert.
    """
    print(f"\n{'='*80}")
    print(f"ANALYSE: Mechaniker {mechaniker_nr} ({von} bis {bis})")
    print(f"{'='*80}\n")
    
    # 1. Hole DRIVE-Berechnung
    print("📊 DRIVE-Berechnung:")
    print("-" * 80)
    drive_data = WerkstattData.get_mechaniker_leistung(
        von=von,
        bis=bis,
        mechaniker_nr=mechaniker_nr
    )
    
    if not drive_data['mechaniker']:
        print(f"❌ Keine Daten für Mechaniker {mechaniker_nr}")
        return
    
    mech = drive_data['mechaniker'][0]
    print(f"  Stempelzeit (St-Anteil): {mech['stempelzeit']:.1f} Min ({mech['stempelzeit']/60:.2f} h)")
    print(f"  Stempelzeit (Leistungsgrad): {mech['stempelzeit_leistungsgrad']:.1f} Min ({mech['stempelzeit_leistungsgrad']/60:.2f} h)")
    print(f"  AW-Anteil: {mech['aw']:.1f} AW ({mech['aw']*6:.1f} Min)")
    print(f"  Leistungsgrad: {mech['leistungsgrad']:.1f}%")
    print(f"  Anwesenheit: {mech['anwesenheit']:.1f} Min ({mech['anwesenheit']/60:.2f} h)")
    print(f"  Aufträge: {mech['auftraege']}")
    print(f"  Tage: {mech['tage']}")
    
    # 2. Hole Rohdaten aus Datenbank
    print(f"\n📊 Rohdaten aus Datenbank:")
    print("-" * 80)
    
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Stempelungen mit Positionen
        query_stempelungen = """
            SELECT 
                t.employee_number,
                t.order_number,
                t.order_position,
                t.order_position_line,
                t.start_time,
                t.end_time,
                EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 as stempel_minuten,
                o.subsidiary as betrieb
            FROM times t
            JOIN orders o ON t.order_number = o.number
            WHERE t.type = 2
                AND t.end_time IS NOT NULL
                AND t.order_number > 31
                AND t.employee_number = %s
                AND t.start_time >= %s AND t.start_time < %s + INTERVAL '1 day'
            ORDER BY t.start_time
        """
        cursor.execute(query_stempelungen, [mechaniker_nr, von, bis])
        stempelungen = cursor.fetchall()
        
        print(f"  Anzahl Stempelungen: {len(stempelungen)}")
        
        # Zeige erste 10 Stempelungen
        print(f"\n  Erste 10 Stempelungen:")
        for i, st in enumerate(stempelungen[:10]):
            print(f"    {i+1}. Auftrag {st['order_number']}, Pos {st['order_position']},{st['order_position_line']}, "
                  f"{st['start_time']} - {st['end_time']}, {st['stempel_minuten']:.1f} Min")
        
        # AW pro Position
        query_aw = """
            SELECT 
                l.order_number,
                l.order_position,
                l.order_position_line,
                l.time_units as aw,
                l.mechanic_no,
                l.labour_type,
                l.net_price_in_order as umsatz
            FROM labours l
            WHERE l.order_number IN (
                SELECT DISTINCT order_number 
                FROM times 
                WHERE type = 2 
                    AND employee_number = %s
                    AND start_time >= %s AND start_time < %s + INTERVAL '1 day'
            )
            AND l.time_units > 0
            ORDER BY l.order_number, l.order_position, l.order_position_line
        """
        cursor.execute(query_aw, [mechaniker_nr, von, bis])
        positionen = cursor.fetchall()
        
        print(f"\n  Anzahl Positionen mit AW: {len(positionen)}")
        
        # AW pro Mechaniker
        aw_gesamt = sum(p['aw'] for p in positionen if p['mechanic_no'] == mechaniker_nr)
        aw_gesamt_alle = sum(p['aw'] for p in positionen)
        
        print(f"  AW gesamt (nur diesem Mechaniker): {aw_gesamt:.1f} AW ({aw_gesamt*6:.1f} Min)")
        print(f"  AW gesamt (alle Mechaniker): {aw_gesamt_alle:.1f} AW ({aw_gesamt_alle*6:.1f} Min)")
        
        # Stempelungen pro Position
        print(f"\n  Stempelungen pro Position:")
        positionen_mit_stempelung = {}
        for st in stempelungen:
            key = (st['order_number'], st['order_position'], st['order_position_line'])
            if key not in positionen_mit_stempelung:
                positionen_mit_stempelung[key] = []
            positionen_mit_stempelung[key].append(st)
        
        for key, st_list in list(positionen_mit_stempelung.items())[:10]:
            gesamt_min = sum(s['stempel_minuten'] for s in st_list)
            print(f"    Auftrag {key[0]}, Pos {key[1]},{key[2]}: {len(st_list)} Stempelungen, {gesamt_min:.1f} Min gesamt")
    
    # 3. Vergleiche mit Excel-Daten (falls vorhanden)
    if excel_daten:
        print(f"\n📊 Vergleich mit Excel-Daten:")
        print("-" * 80)
        
        excel_zeilen = [z for z in excel_daten if z.get('MA') == mechaniker_nr]
        print(f"  Anzahl Excel-Zeilen: {len(excel_zeilen)}")
        
        if excel_zeilen:
            # Summiere Excel-Daten
            excel_st_anteil = sum(parse_zeit_string(z.get('St-Ant.', 0)) for z in excel_zeilen)
            excel_aw_anteil = sum(parse_zeit_string(z.get('AW-Ant.', 0)) for z in excel_zeilen)
            
            # Berechne Leistungsgrad aus Excel
            if excel_st_anteil > 0:
                excel_leistungsgrad = (excel_aw_anteil / excel_st_anteil) * 100
            else:
                excel_leistungsgrad = None
            
            print(f"  Excel St-Anteil: {excel_st_anteil:.1f} Min ({excel_st_anteil/60:.2f} h)")
            print(f"  Excel AW-Anteil: {excel_aw_anteil:.1f} Min ({excel_aw_anteil/60:.2f} h)")
            if excel_leistungsgrad:
                print(f"  Excel Leistungsgrad: {excel_leistungsgrad:.1f}%")
            
            # Vergleich
            print(f"\n  Vergleich:")
            diff_st = mech['stempelzeit'] - excel_st_anteil
            diff_aw = (mech['aw'] * 6) - excel_aw_anteil
            diff_lg = mech['leistungsgrad'] - excel_leistungsgrad if excel_leistungsgrad else None
            
            print(f"    St-Anteil Diff: {diff_st:+.1f} Min ({diff_st/excel_st_anteil*100:+.1f}%)" if excel_st_anteil > 0 else "    St-Anteil Diff: N/A")
            print(f"    AW-Anteil Diff: {diff_aw:+.1f} Min ({diff_aw/excel_aw_anteil*100:+.1f}%)" if excel_aw_anteil > 0 else "    AW-Anteil Diff: N/A")
            if diff_lg is not None:
                print(f"    Leistungsgrad Diff: {diff_lg:+.1f}%")
    
    # 4. Analysiere St-Anteil-Berechnung
    print(f"\n📊 St-Anteil-Berechnung (get_st_anteil_position_basiert):")
    print("-" * 80)
    
    st_anteil = WerkstattData.get_st_anteil_position_basiert(von, bis)
    st_anteil_mech = st_anteil.get(mechaniker_nr, 0)
    
    print(f"  St-Anteil (position-basiert): {st_anteil_mech:.1f} Min ({st_anteil_mech/60:.2f} h)")
    print(f"  St-Anteil (aus get_mechaniker_leistung): {mech['stempelzeit']:.1f} Min ({mech['stempelzeit']/60:.2f} h)")
    diff_st = st_anteil_mech - mech['stempelzeit']
    print(f"  Differenz: {diff_st:+.1f} Min ({diff_st/mech['stempelzeit']*100:+.1f}%)" if mech['stempelzeit'] > 0 else "  Differenz: N/A")
    
    # 5. Analysiere AW-Berechnung
    print(f"\n📊 AW-Berechnung (get_aw_verrechnet):")
    print("-" * 80)
    
    aw_data = WerkstattData.get_aw_verrechnet(von, bis)
    aw_mech = aw_data.get(mechaniker_nr, {})
    
    print(f"  AW (aus get_aw_verrechnet): {aw_mech.get('aw', 0):.1f} AW ({aw_mech.get('aw', 0)*6:.1f} Min)")
    print(f"  AW (aus get_mechaniker_leistung): {mech['aw']:.1f} AW ({mech['aw']*6:.1f} Min)")
    diff_aw = (aw_mech.get('aw', 0) - mech['aw']) * 6
    print(f"  Differenz: {diff_aw:+.1f} Min ({diff_aw/(mech['aw']*6)*100:+.1f}%)" if mech['aw'] > 0 else "  Differenz: N/A")
    
    print(f"\n{'='*80}\n")


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Usage: python analyse_leistungsgrad_detailliert.py <mechaniker_nr> [von] [bis]")
        print("Beispiel: python analyse_leistungsgrad_detailliert.py 5018 2026-01-01 2026-01-15")
        sys.exit(1)
    
    mechaniker_nr = int(sys.argv[1])
    
    if len(sys.argv) >= 4:
        von = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
        bis = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()
    else:
        # Default: Aktueller Monat
        heute = date.today()
        von = heute.replace(day=1)
        bis = heute
    
    analyse_mechaniker_detailliert(mechaniker_nr, von, bis)


if __name__ == '__main__':
    main()
