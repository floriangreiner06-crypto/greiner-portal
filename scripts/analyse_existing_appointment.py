#!/usr/bin/env python3
"""
Analysiert einen bestehenden Termin aus Locosoft
Zweck: Vergleich mit unseren erstellten Terminen
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from tools.locosoft_soap_client import LocosoftSOAPClient
from datetime import date, timedelta

def analyse_appointment(termin_nr: int):
    """Analysiert einen Termin und gibt alle Felder aus."""
    soap_client = LocosoftSOAPClient()
    
    print(f"\n{'='*80}")
    print(f"ANALYSE: Termin #{termin_nr}")
    print(f"{'='*80}\n")
    
    try:
        termin = soap_client.read_appointment(termin_nr)
        if not termin:
            print(f"❌ Termin {termin_nr} nicht gefunden")
            return
        
        print("✅ Termin gefunden!\n")
        print("📋 Alle Felder:")
        print("-" * 80)
        
        for key, value in sorted(termin.items()):
            print(f"  {key:30s}: {value}")
        
        print("\n" + "-" * 80)
        print("\n🔍 Wichtige Felder für Planer:")
        print(f"  type:                    {termin.get('type')}")
        print(f"  bringDateTime:            {termin.get('bringDateTime')}")
        print(f"  returnDateTime:           {termin.get('returnDateTime')}")
        print(f"  workOrderNumber:          {termin.get('workOrderNumber')}")
        print(f"  customerNumber:           {termin.get('customerNumber')}")
        print(f"  vehicleNumber:            {termin.get('vehicleNumber')}")
        print(f"  bringServiceAdvisor:      {termin.get('bringServiceAdvisor')}")
        print(f"  returnServiceAdvisor:     {termin.get('returnServiceAdvisor')}")
        print(f"  urgency:                  {termin.get('urgency')}")
        print(f"  vehicleStatus:            {termin.get('vehicleStatus')}")
        print(f"  inProgress:               {termin.get('inProgress')}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

def list_appointments_for_date(date_str: str):
    """Listet alle Termine für ein Datum."""
    soap_client = LocosoftSOAPClient()
    
    print(f"\n{'='*80}")
    print(f"TERMINE FÜR {date_str}")
    print(f"{'='*80}\n")
    
    try:
        termine = soap_client.list_appointments_by_date(date_str)
        print(f"✅ {len(termine)} Termine gefunden\n")
        
        for i, termin in enumerate(termine[:10], 1):  # Max 10 anzeigen
            print(f"{i}. Termin #{termin.get('number')}")
            print(f"   Text: {termin.get('text', 'N/A')}")
            print(f"   bringDateTime: {termin.get('bringDateTime')}")
            print(f"   returnDateTime: {termin.get('returnDateTime')}")
            print(f"   type: {termin.get('type')}")
            print(f"   workOrderNumber: {termin.get('workOrderNumber')}")
            print()
        
        if len(termine) > 10:
            print(f"... und {len(termine) - 10} weitere Termine")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Termin-Nummer als Argument
        termin_nr = int(sys.argv[1])
        analyse_appointment(termin_nr)
    else:
        # Liste Termine für heute und morgen
        heute = date.today().strftime('%Y-%m-%d')
        morgen = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        list_appointments_for_date(heute)
        list_appointments_for_date(morgen)
        
        # Analysiere Test-Termine
        print("\n" + "="*80)
        print("ANALYSE TEST-TERMINE")
        print("="*80)
        for termin_nr in [14, 15]:
            analyse_appointment(termin_nr)
