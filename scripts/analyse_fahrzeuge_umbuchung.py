"""
Analyse: Fahrzeuge nach korrekten Kategorien + Umbuchungen
===========================================================
GW: D, G, L (Gebrauchtwagen)
NW: N, T, V (Neuwagen)

Prüft ob ehemalige Neuwagen durch Umbuchung zu GW wurden
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session

# Geschäftsjahr 2024/25: Sep 2024 - Aug 2025
gj_von = "2024-09-01"
gj_bis = "2025-09-01"

print("=" * 100)
print("Analyse: Fahrzeuge nach korrekten Kategorien + Umbuchungen")
print(f"Geschäftsjahr 2024/25 (Sep 2024 - Aug 2025)")
print("=" * 100)

with locosoft_session() as conn:
    cursor = conn.cursor()
    
    # 1. Prüfe ob "L" Typ existiert
    print("\n1. PRÜFUNG: Existiert Typ 'L'?")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    typen = {}
    for row in cursor.fetchall():
        typ = row[0] or 'NULL'
        anzahl = int(row[1] or 0)
        typen[typ] = anzahl
        typ_name = {
            'D': 'Demo',
            'G': 'Gebrauchtwagen',
            'L': 'Lagerfahrzeug?',
            'N': 'Neuwagen',
            'T': 'Tageszulassung',
            'V': 'Vorführwagen'
        }.get(typ, typ)
        print(f"  {typ}: {anzahl} Stk. ({typ_name})")
    
    # 2. Korrekte Kategorien
    print("\n\n2. KORREKTE KATEGORIEN (nach Benutzer-Angabe):")
    print("-" * 100)
    
    # GW: D + G + L
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_gw_korrekt = int(row[0] or 0) if row else 0
    
    # GW Aufschlüsselung
    cursor.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('D', 'G', 'L')
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    gw_aufschl = {}
    for row in cursor.fetchall():
        typ = row[0]
        anzahl = int(row[1] or 0)
        gw_aufschl[typ] = anzahl
    
    print(f"  GW (D+G+L): {stueck_gw_korrekt} Stk.")
    print(f"    - D (Demo): {gw_aufschl.get('D', 0)} Stk.")
    print(f"    - G (Gebrauchtwagen): {gw_aufschl.get('G', 0)} Stk.")
    print(f"    - L (Lagerfahrzeug?): {gw_aufschl.get('L', 0)} Stk.")
    
    # NW: N + T + V
    cursor.execute("""
        SELECT COUNT(*) as stueck
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
    """, (gj_von, gj_bis))
    row = cursor.fetchone()
    stueck_nw_korrekt = int(row[0] or 0) if row else 0
    
    # NW Aufschlüsselung
    cursor.execute("""
        SELECT 
            dealer_vehicle_type,
            COUNT(*) as anzahl
        FROM dealer_vehicles
        WHERE out_invoice_date >= %s AND out_invoice_date < %s
          AND out_invoice_date IS NOT NULL
          AND dealer_vehicle_type IN ('N', 'T', 'V')
        GROUP BY dealer_vehicle_type
        ORDER BY dealer_vehicle_type
    """, (gj_von, gj_bis))
    
    nw_aufschl = {}
    for row in cursor.fetchall():
        typ = row[0]
        anzahl = int(row[1] or 0)
        nw_aufschl[typ] = anzahl
    
    print(f"\n  NW (N+T+V): {stueck_nw_korrekt} Stk.")
    print(f"    - N (Neuwagen): {nw_aufschl.get('N', 0)} Stk.")
    print(f"    - T (Tageszulassung): {nw_aufschl.get('T', 0)} Stk.")
    print(f"    - V (Vorführwagen): {nw_aufschl.get('V', 0)} Stk.")
    
    # 3. Prüfe Umbuchungen: Fahrzeuge die als NW gestartet, aber als GW verkauft wurden
    print("\n\n3. UMBUCHUNGS-ANALYSE:")
    print("-" * 100)
    print("Prüfe ob Fahrzeuge von NW (N/T/V) zu GW (D/G/L) umgebucht wurden...")
    
    # Finde Fahrzeuge die sowohl als NW als auch als GW existieren
    cursor.execute("""
        WITH nw_fahrzeuge AS (
            SELECT DISTINCT vehicle_number
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('N', 'T', 'V')
              AND vehicle_number IS NOT NULL
        ),
        gw_fahrzeuge AS (
            SELECT DISTINCT vehicle_number
            FROM dealer_vehicles
            WHERE out_invoice_date >= %s AND out_invoice_date < %s
              AND out_invoice_date IS NOT NULL
              AND dealer_vehicle_type IN ('D', 'G', 'L')
              AND vehicle_number IS NOT NULL
        )
        SELECT COUNT(*) as anzahl
        FROM nw_fahrzeuge nw
        INNER JOIN gw_fahrzeuge gw ON nw.vehicle_number = gw.vehicle_number
    """, (gj_von, gj_bis, gj_von, gj_bis))
    
    row = cursor.fetchone()
    umbuchungen_anzahl = int(row[0] or 0) if row else 0
    
    print(f"  Fahrzeuge die sowohl als NW als auch als GW existieren: {umbuchungen_anzahl} Stk.")
    
    if umbuchungen_anzahl > 0:
        # Detaillierte Analyse der Umbuchungen
        print(f"\n  Detaillierte Umbuchungen (erste 10):")
        cursor.execute("""
            WITH nw_fahrzeuge AS (
                SELECT 
                    vehicle_number,
                    dealer_vehicle_number as nw_dv_nr,
                    dealer_vehicle_type as nw_typ,
                    out_invoice_date as nw_datum
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('N', 'T', 'V')
                  AND vehicle_number IS NOT NULL
            ),
            gw_fahrzeuge AS (
                SELECT 
                    vehicle_number,
                    dealer_vehicle_number as gw_dv_nr,
                    dealer_vehicle_type as gw_typ,
                    out_invoice_date as gw_datum
                FROM dealer_vehicles
                WHERE out_invoice_date >= %s AND out_invoice_date < %s
                  AND out_invoice_date IS NOT NULL
                  AND dealer_vehicle_type IN ('D', 'G', 'L')
                  AND vehicle_number IS NOT NULL
            )
            SELECT 
                nw.vehicle_number,
                nw.nw_dv_nr,
                nw.nw_typ,
                nw.nw_datum,
                gw.gw_dv_nr,
                gw.gw_typ,
                gw.gw_datum
            FROM nw_fahrzeuge nw
            INNER JOIN gw_fahrzeuge gw ON nw.vehicle_number = gw.vehicle_number
            ORDER BY nw.nw_datum DESC
            LIMIT 10
        """, (gj_von, gj_bis, gj_von, gj_bis))
        
        print(f"  {'V-Nr':<12} {'NW DV-Nr':<12} {'NW Typ':<8} {'NW Datum':<12} {'GW DV-Nr':<12} {'GW Typ':<8} {'GW Datum':<12}")
        print("  " + "-" * 80)
        
        for row in cursor.fetchall():
            v_nr = str(row[0] or '')[:12]
            nw_dv_nr = str(row[1] or '')[:12]
            nw_typ = row[2] or ''
            nw_datum = str(row[3] or '')[:12]
            gw_dv_nr = str(row[4] or '')[:12]
            gw_typ = row[5] or ''
            gw_datum = str(row[6] or '')[:12]
            print(f"  {v_nr:<12} {nw_dv_nr:<12} {nw_typ:<8} {nw_datum:<12} {gw_dv_nr:<12} {gw_typ:<8} {gw_datum:<12}")
    
    # 4. Vergleich mit Global Cube
    print("\n\n4. VERGLEICH MIT GLOBAL CUBE:")
    print("-" * 100)
    
    # Global Cube Werte (aus vorherigem Script)
    globalcube_nw = 444.02
    globalcube_gw = 625.17
    
    print(f"  NW:")
    print(f"    Global Cube: {globalcube_nw:.2f} Stk.")
    print(f"    DRIVE BWA (N+T+V): {stueck_nw_korrekt} Stk.")
    diff_nw = stueck_nw_korrekt - globalcube_nw
    print(f"    Differenz: {diff_nw:+.2f} Stk. ({diff_nw/globalcube_nw*100 if globalcube_nw > 0 else 0:+.2f}%)")
    
    print(f"\n  GW:")
    print(f"    Global Cube: {globalcube_gw:.2f} Stk.")
    print(f"    DRIVE BWA (D+G+L): {stueck_gw_korrekt} Stk.")
    diff_gw = stueck_gw_korrekt - globalcube_gw
    print(f"    Differenz: {diff_gw:+.2f} Stk. ({diff_gw/globalcube_gw*100 if globalcube_gw > 0 else 0:+.2f}%)")
    
    if abs(diff_nw) < 20 and abs(diff_gw) < 20:
        print(f"\n  ✅ Sehr gute Übereinstimmung mit korrekten Kategorien!")
    elif abs(diff_gw) > 100:
        print(f"\n  ⚠️  GW-Differenz noch groß - möglicherweise durch Umbuchungen oder andere Filter")

