#!/usr/bin/env python3
"""
Query: Welche Fahrzeuge haben noch Garantie?
Basierend auf Erstzulassungsdatum + Garantiedauer

Verwendung:
    python3 scripts/query_fahrzeuge_mit_garantie.py
    python3 scripts/query_fahrzeuge_mit_garantie.py --nur-bald-ablaufend  # Nur < 30 Tage
    python3 scripts/query_fahrzeuge_mit_garantie.py --alle  # Alle Fahrzeuge (auch ohne Garantie)
"""

import sys
import os
sys.path.insert(0, '/opt/greiner-portal')
os.chdir('/opt/greiner-portal')

from datetime import date
from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor
import argparse

# ============================================================================
# KONFIGURATION
# ============================================================================

# Garantiedauer je nach Marke (in Jahren)
GARANTIE_DAUER = {
    'HYUNDAI': 5,      # Hyundai: 5 Jahre
    'OPEL': 2,         # Opel: 2 Jahre
    'CITROEN': 2,      # Citroën: 2 Jahre
    'CITROËN': 2,
    'PEUGEOT': 2,      # Peugeot: 2 Jahre
    'DEFAULT': 2       # Standard: 2 Jahre
}


def get_garantie_dauer(marke: str) -> int:
    """Ermittelt Garantiedauer basierend auf Marke"""
    if not marke:
        return GARANTIE_DAUER['DEFAULT']
    
    marke_upper = marke.upper()
    for key, jahre in GARANTIE_DAUER.items():
        if key != 'DEFAULT' and key in marke_upper:
            return jahre
    
    return GARANTIE_DAUER['DEFAULT']


def query_fahrzeuge_mit_garantie(nur_bald_ablaufend=False, alle=False):
    """
    Holt alle Fahrzeuge die noch Garantie haben.
    
    Args:
        nur_bald_ablaufend: Nur Fahrzeuge deren Garantie < 30 Tage abläuft
        alle: Alle Fahrzeuge anzeigen (auch ohne Garantie)
    """
    with locosoft_session() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            WITH garantie_dauer AS (
                SELECT 
                    v.internal_number,
                    v.dealer_vehicle_number,
                    v.dealer_vehicle_type,
                    v.first_registration_date as erstzulassung,
                    v.vin,
                    v.license_plate as kennzeichen,
                    m.description as marke,
                    COALESCE(
                        NULLIF(TRIM(v.free_form_model_text), ''),
                        NULLIF(TRIM(mo.description), ''),
                        'Unbekannt'
                    ) as modell,
                    v.mileage_km as km_stand,
                    -- Garantiedauer je nach Marke
                    CASE 
                        WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                        WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                        WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                        WHEN UPPER(m.description) LIKE '%CITROËN%' THEN 2
                        WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                        ELSE 2
                    END as garantie_jahre,
                    -- Garantie-Ablaufdatum berechnen
                    CASE 
                        WHEN v.first_registration_date IS NOT NULL THEN
                            v.first_registration_date + INTERVAL '1 year' * 
                            CASE 
                                WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                                WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                                WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                                WHEN UPPER(m.description) LIKE '%CITROËN%' THEN 2
                                WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                                ELSE 2
                            END
                        ELSE NULL
                    END as garantie_ablauf,
                    -- Prüfe ob Garantie noch aktiv ist
                    CASE 
                        WHEN v.first_registration_date IS NOT NULL THEN
                            CURRENT_DATE <= (
                                v.first_registration_date + INTERVAL '1 year' * 
                                CASE 
                                    WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                                    WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                                    WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                                    WHEN UPPER(m.description) LIKE '%CITROËN%' THEN 2
                                    WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                                    ELSE 2
                                END
                            )
                        ELSE false
                    END as hat_garantie,
                    -- Restliche Garantie in Tagen
                    CASE 
                        WHEN v.first_registration_date IS NOT NULL THEN
                            (v.first_registration_date + INTERVAL '1 year' * 
                             CASE 
                                 WHEN UPPER(m.description) LIKE '%HYUNDAI%' THEN 5
                                 WHEN UPPER(m.description) LIKE '%OPEL%' THEN 2
                                 WHEN UPPER(m.description) LIKE '%CITROEN%' THEN 2
                                 WHEN UPPER(m.description) LIKE '%CITROËN%' THEN 2
                                 WHEN UPPER(m.description) LIKE '%PEUGEOT%' THEN 2
                                 ELSE 2
                             END)::date - CURRENT_DATE
                        ELSE NULL
                    END as garantie_rest_tage,
                    -- Fahrzeug-Alter in Jahren
                    CASE 
                        WHEN v.first_registration_date IS NOT NULL THEN
                            EXTRACT(YEAR FROM AGE(CURRENT_DATE, v.first_registration_date))
                        ELSE NULL
                    END as fahrzeug_alter_jahre,
                    -- Kunde (falls verkauft)
                    COALESCE(cs.family_name || COALESCE(', ' || cs.first_name, ''), '') as kunde,
                    dv.out_sales_contract_date as verkauft_am
                FROM vehicles v
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN models mo ON v.make_number = mo.make_number AND v.model_code = mo.model_code
                LEFT JOIN dealer_vehicles dv 
                    ON v.dealer_vehicle_number = dv.dealer_vehicle_number
                    AND v.dealer_vehicle_type = dv.dealer_vehicle_type
                LEFT JOIN customers_suppliers cs ON dv.buyer_customer_no = cs.customer_number
                WHERE v.first_registration_date IS NOT NULL
            )
            SELECT 
                internal_number,
                dealer_vehicle_number,
                dealer_vehicle_type,
                vin,
                kennzeichen,
                marke,
                modell,
                erstzulassung,
                fahrzeug_alter_jahre,
                km_stand,
                garantie_jahre,
                garantie_ablauf,
                garantie_rest_tage,
                hat_garantie,
                kunde,
                verkauft_am,
                -- Warnung wenn Garantie bald abläuft (< 30 Tage)
                CASE 
                    WHEN garantie_rest_tage IS NOT NULL AND garantie_rest_tage < 30 AND garantie_rest_tage > 0 THEN true
                    ELSE false
                END as garantie_laeuft_bald_ab
            FROM garantie_dauer
            WHERE 1=1
        """
        
        # Filter hinzufügen
        if alle:
            # Alle Fahrzeuge (auch ohne Garantie)
            pass
        elif nur_bald_ablaufend:
            # Nur Fahrzeuge deren Garantie < 30 Tage abläuft
            query += " AND hat_garantie = true AND garantie_rest_tage < 30 AND garantie_rest_tage > 0"
        else:
            # Nur Fahrzeuge mit noch aktiver Garantie
            query += " AND hat_garantie = true"
        
        query += " ORDER BY garantie_rest_tage ASC NULLS LAST, marke, modell"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        return rows


def format_output(rows):
    """Formatiert die Ausgabe"""
    if not rows:
        print("\n❌ Keine Fahrzeuge gefunden.\n")
        return
    
    print(f"\n{'='*120}")
    print(f"FAHRZEUGE MIT GARANTIE - {len(rows)} Fahrzeuge gefunden")
    print(f"{'='*120}\n")
    
    # Header
    print(f"{'VIN':<18} {'Kennzeichen':<12} {'Marke':<12} {'Modell':<25} {'EZ':<12} {'Alter':<6} {'Garantie':<10} {'Rest':<8} {'Kunde':<25}")
    print("-" * 120)
    
    for row in rows:
        vin = str(row.get('vin', ''))[:17] if row.get('vin') else '-'
        kennzeichen = str(row.get('kennzeichen', '-'))[:11]
        marke = str(row.get('marke', '-'))[:11]
        modell = str(row.get('modell', '-'))[:24]
        ez = row.get('erstzulassung').strftime('%d.%m.%Y') if row.get('erstzulassung') else '-'
        alter = f"{int(row.get('fahrzeug_alter_jahre', 0))}J" if row.get('fahrzeug_alter_jahre') else '-'
        garantie_jahre = f"{int(row.get('garantie_jahre', 0))}J" if row.get('garantie_jahre') else '-'
        rest_tage = f"{int(row.get('garantie_rest_tage', 0))}T" if row.get('garantie_rest_tage') is not None else '-'
        kunde = str(row.get('kunde', '-'))[:24] if row.get('kunde') else '-'
        
        # Warnung wenn Garantie bald abläuft
        warnung = "⚠️ " if row.get('garantie_laeuft_bald_ab') else "  "
        
        print(f"{warnung}{vin:<18} {kennzeichen:<12} {marke:<12} {modell:<25} {ez:<12} {alter:<6} {garantie_jahre:<10} {rest_tage:<8} {kunde:<25}")
    
    print(f"\n{'='*120}\n")
    
    # Statistik
    mit_garantie = sum(1 for r in rows if r.get('hat_garantie'))
    bald_ablaufend = sum(1 for r in rows if r.get('garantie_laeuft_bald_ab'))
    
    print(f"Statistik:")
    print(f"  - Mit Garantie: {mit_garantie}")
    print(f"  - Garantie läuft bald ab (< 30 Tage): {bald_ablaufend}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Zeigt Fahrzeuge mit noch aktiver Garantie')
    parser.add_argument('--nur-bald-ablaufend', action='store_true', 
                       help='Nur Fahrzeuge deren Garantie < 30 Tage abläuft')
    parser.add_argument('--alle', action='store_true',
                       help='Alle Fahrzeuge anzeigen (auch ohne Garantie)')
    
    args = parser.parse_args()
    
    try:
        rows = query_fahrzeuge_mit_garantie(
            nur_bald_ablaufend=args.nur_bald_ablaufend,
            alle=args.alle
        )
        format_output(rows)
        return 0
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
