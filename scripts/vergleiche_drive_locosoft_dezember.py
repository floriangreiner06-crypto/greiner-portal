#!/usr/bin/env python3
"""
Vergleicht DRIVE-Berechnung mit Locosoft CSV für Dezember (Tobias 5007)
und identifiziert konkrete Abweichungen.

Datum: 2026-01-XX
"""

import sys
from pathlib import Path
from datetime import date
from collections import defaultdict

# Projekt-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.werkstatt_data import WerkstattData
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor


def parse_zeit(zeit_str):
    """Konvertiert Zeit-String (HH:MM) in Minuten"""
    if not zeit_str or str(zeit_str).strip() in ['', '--', '-""-', 'nan']:
        return 0.0
    try:
        zeit_str = str(zeit_str).strip()
        if ':' in zeit_str:
            parts = zeit_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        return 0.0
    except:
        return 0.0


def hole_drive_werte(mechaniker_nr: int, von: date, bis: date):
    """Holt Werte aus DRIVE"""
    print("="*80)
    print("DRIVE-BERECHNUNG")
    print("="*80)
    print()
    
    data = WerkstattData.get_mechaniker_leistung(
        von=von,
        bis=bis,
        mechaniker_nr=mechaniker_nr
    )
    
    if not data['mechaniker']:
        print(f"❌ Keine Daten für Mechaniker {mechaniker_nr}")
        return None
    
    mech = data['mechaniker'][0]
    
    print(f"👤 Mechaniker: {mech['name']} ({mechaniker_nr})")
    print(f"📅 Zeitraum: {von} bis {bis}")
    print()
    print(f"📊 DRIVE-Werte:")
    print(f"  Stempelzeit (Stmp.Anteil): {mech['stempelzeit']:.1f} Min ({mech['stempelzeit']/60:.2f} h)")
    print(f"  Stempelzeit (Leistungsgrad): {mech['stempelzeit_leistungsgrad']:.1f} Min ({mech['stempelzeit_leistungsgrad']/60:.2f} h)")
    print(f"  AW-Anteil: {mech['aw']:.1f} AW ({mech['aw']*6:.1f} Min)")
    print(f"  Leistungsgrad: {mech['leistungsgrad']:.1f}%")
    print()
    
    return {
        'st_anteil': mech['stempelzeit'],
        'st_leistungsgrad': mech['stempelzeit_leistungsgrad'],
        'aw_anteil': mech['aw'] * 6,  # In Minuten
        'leistungsgrad': mech['leistungsgrad']
    }


def hole_locosoft_werte_aus_db(mechaniker_nr: int, von: date, bis: date):
    """Holt Werte direkt aus Locosoft-DB für verschiedene Hypothesen"""
    print("="*80)
    print("LOCOSOFT-DB ANALYSE (verschiedene Hypothesen)")
    print("="*80)
    print()
    
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Hypothese 1: AW-Anteil basierend auf invoice_date + mechanic_no
        query1 = """
            SELECT 
                SUM(l.time_units) as aw_summe
            FROM labours l
            JOIN invoices i ON l.invoice_number = i.invoice_number 
                AND l.invoice_type = i.invoice_type
            WHERE i.invoice_date >= %s 
              AND i.invoice_date <= %s
              AND l.mechanic_no = %s
              AND l.time_units > 0
        """
        cursor.execute(query1, [von, bis, mechaniker_nr])
        result1 = cursor.fetchone()
        aw_hyp1 = float(result1['aw_summe'] or 0) * 6
        
        print(f"Hypothese 1 (invoice_date + mechanic_no):")
        print(f"  AW-Anteil: {aw_hyp1:.0f} Min ({aw_hyp1/60:.2f} h) = {aw_hyp1/6:.1f} AW")
        print()
        
        # Hypothese 2: AW-Anteil basierend auf start_time + mechanic_no (proportional)
        query2 = """
            WITH
            stempelzeit_pro_position AS (
                SELECT DISTINCT ON (t.employee_number, t.order_number, t.order_position, t.order_position_line, t.start_time, t.end_time)
                    t.employee_number,
                    t.order_number,
                    t.order_position,
                    t.order_position_line,
                    EXTRACT(EPOCH FROM (t.end_time - t.start_time)) / 60 AS stempel_minuten
                FROM times t
                WHERE t.type = 2
                  AND t.end_time IS NOT NULL
                  AND t.order_number > 31
                  AND t.order_position IS NOT NULL
                  AND t.order_position_line IS NOT NULL
                  AND t.employee_number = %s
                  AND t.start_time >= %s 
                  AND t.start_time < %s + INTERVAL '1 day'
            ),
            gesamt_stempelzeit_pro_position AS (
                SELECT 
                    order_number,
                    order_position,
                    order_position_line,
                    SUM(stempel_minuten) AS gesamt_stempel_minuten
                FROM stempelzeit_pro_position
                GROUP BY order_number, order_position, order_position_line
            ),
            aw_anteil_pro_position AS (
                SELECT
                    spp.employee_number,
                    l.time_units * (spp.stempel_minuten / NULLIF(gst.gesamt_stempel_minuten, 0)) AS aw_anteil
                FROM stempelzeit_pro_position spp
                JOIN gesamt_stempelzeit_pro_position gst 
                    ON spp.order_number = gst.order_number
                    AND spp.order_position = gst.order_position
                    AND spp.order_position_line = gst.order_position_line
                JOIN labours l 
                    ON spp.order_number = l.order_number
                    AND spp.order_position = l.order_position
                    AND spp.order_position_line = l.order_position_line
                WHERE l.time_units > 0
            )
            SELECT 
                SUM(aw_anteil) AS aw_summe
            FROM aw_anteil_pro_position
        """
        cursor.execute(query2, [mechaniker_nr, von, bis])
        result2 = cursor.fetchone()
        aw_hyp2 = float(result2['aw_summe'] or 0) * 6
        
        print(f"Hypothese 2 (start_time + proportional):")
        print(f"  AW-Anteil: {aw_hyp2:.0f} Min ({aw_hyp2/60:.2f} h) = {aw_hyp2/6:.1f} AW")
        print()
        
        # Hypothese 3: AW-Anteil basierend auf start_time + ALLE Positionen (ohne Mechaniker-Filter)
        query3 = """
            WITH auftraege_mit_stempelung AS (
                SELECT DISTINCT t.order_number
                FROM times t
                WHERE t.type = 2
                  AND t.end_time IS NOT NULL
                  AND t.order_number > 31
                  AND t.employee_number = %s
                  AND t.start_time >= %s 
                  AND t.start_time < %s + INTERVAL '1 day'
            )
            SELECT 
                SUM(l.time_units) as aw_summe
            FROM auftraege_mit_stempelung ams
            JOIN labours l ON ams.order_number = l.order_number
            WHERE l.time_units > 0
        """
        cursor.execute(query3, [mechaniker_nr, von, bis])
        result3 = cursor.fetchone()
        aw_hyp3 = float(result3['aw_summe'] or 0) * 6
        
        print(f"Hypothese 3 (start_time + ALLE Positionen):")
        print(f"  AW-Anteil: {aw_hyp3:.0f} Min ({aw_hyp3/60:.2f} h) = {aw_hyp3/6:.1f} AW")
        print()
        
        return {
            'hyp1': aw_hyp1,
            'hyp2': aw_hyp2,
            'hyp3': aw_hyp3
        }


def main():
    """Hauptfunktion"""
    mechaniker_nr = 5007
    von = date(2025, 12, 1)
    bis = date(2025, 12, 8)
    
    # Locosoft-UI Werte (aus Screenshot)
    locosoft_aw_min = 85 * 60 + 6  # 85:06
    locosoft_st_min = 142 * 60 + 23  # 142:23
    locosoft_lg = 59.8
    
    print("="*80)
    print("VERGLEICH: DRIVE vs. LOCOSOFT (Tobias 5007, Dezember 2025)")
    print("="*80)
    print()
    
    # Hole DRIVE-Werte
    drive_werte = hole_drive_werte(mechaniker_nr, von, bis)
    if not drive_werte:
        return
    
    print()
    
    # Hole Locosoft-DB Werte (verschiedene Hypothesen)
    db_werte = hole_locosoft_werte_aus_db(mechaniker_nr, von, bis)
    
    print()
    print("="*80)
    print("VERGLEICH")
    print("="*80)
    print()
    
    print(f"📊 AW-Anteil:")
    print(f"  Locosoft-UI: {locosoft_aw_min} Min ({locosoft_aw_min/60:.2f} h) = {locosoft_aw_min/6:.1f} AW")
    print(f"  DRIVE: {drive_werte['aw_anteil']:.0f} Min ({drive_werte['aw_anteil']/60:.2f} h) = {drive_werte['aw_anteil']/6:.1f} AW")
    print(f"    Abweichung: {drive_werte['aw_anteil'] - locosoft_aw_min:+.0f} Min ({((drive_werte['aw_anteil'] - locosoft_aw_min) / locosoft_aw_min * 100):+.1f}%)")
    print()
    print(f"  DB Hypothese 1 (invoice_date): {db_werte['hyp1']:.0f} Min ({((db_werte['hyp1'] - locosoft_aw_min) / locosoft_aw_min * 100):+.1f}%)")
    print(f"  DB Hypothese 2 (proportional): {db_werte['hyp2']:.0f} Min ({((db_werte['hyp2'] - locosoft_aw_min) / locosoft_aw_min * 100):+.1f}%)")
    print(f"  DB Hypothese 3 (ALLE Positionen): {db_werte['hyp3']:.0f} Min ({((db_werte['hyp3'] - locosoft_aw_min) / locosoft_aw_min * 100):+.1f}%)")
    print()
    
    print(f"📊 Stmp.Anteil:")
    print(f"  Locosoft-UI: {locosoft_st_min} Min ({locosoft_st_min/60:.2f} h)")
    print(f"  DRIVE: {drive_werte['st_anteil']:.0f} Min ({drive_werte['st_anteil']/60:.2f} h)")
    print(f"    Abweichung: {drive_werte['st_anteil'] - locosoft_st_min:+.0f} Min ({((drive_werte['st_anteil'] - locosoft_st_min) / locosoft_st_min * 100):+.1f}%)")
    print()
    
    print(f"📊 Leistungsgrad:")
    print(f"  Locosoft-UI: {locosoft_lg:.1f}%")
    print(f"  DRIVE: {drive_werte['leistungsgrad']:.1f}%")
    print(f"    Abweichung: {drive_werte['leistungsgrad'] - locosoft_lg:+.1f}%")
    print()


if __name__ == '__main__':
    main()
