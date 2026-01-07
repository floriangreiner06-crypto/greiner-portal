#!/usr/bin/env python3
"""
Prüft den Datenstand der Hypovereinsbank in der PostgreSQL-Datenbank
TAG 165 - Diagnose-Skript
"""

import sys
import os
from datetime import datetime, timedelta

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.db_connection import get_db, sql_placeholder, get_db_type

def check_hvb_datenstand():
    """Prüft den aktuellen Datenstand der Hypovereinsbank"""
    
    print("="*70)
    print("HYPOVEREINSBANK DATENSTAND-PRÜFUNG")
    print("="*70)
    print(f"Datenbank-Typ: {get_db_type()}")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        ph = sql_placeholder()
        
        # 1. Konto-Info
        print("📋 KONTO-INFO:")
        print("-" * 70)
        cursor.execute(f"""
            SELECT id, kontoname, iban, aktiv
            FROM konten
            WHERE iban = {ph}
        """, ('DE22741200710006407420',))
        
        konto = cursor.fetchone()
        if konto:
            konto_id = konto[0] if hasattr(konto, '__getitem__') else konto['id']
            kontoname = konto[1] if hasattr(konto, '__getitem__') else konto['kontoname']
            iban = konto[2] if hasattr(konto, '__getitem__') else konto['iban']
            aktiv = konto[3] if hasattr(konto, '__getitem__') else konto['aktiv']
            
            print(f"  ID: {konto_id}")
            print(f"  Name: {kontoname}")
            print(f"  IBAN: {iban}")
            print(f"  Aktiv: {aktiv}")
            print()
        else:
            print("  ❌ Konto nicht gefunden!")
            conn.close()
            return
        
        # 2. Letzte Transaktionen
        print("📊 TRANSAKTIONEN:")
        print("-" * 70)
        cursor.execute(f"""
            SELECT 
                COUNT(*) as anzahl,
                MIN(buchungsdatum) as erste_buchung,
                MAX(buchungsdatum) as letzte_buchung,
                SUM(CASE WHEN buchungsdatum >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END) as letzte_30_tage
            FROM transaktionen
            WHERE konto_id = {ph}
        """, (konto_id,))
        
        stats = cursor.fetchone()
        if stats:
            anzahl = stats[0] if hasattr(stats, '__getitem__') else stats['anzahl']
            erste = stats[1] if hasattr(stats, '__getitem__') else stats['erste_buchung']
            letzte = stats[2] if hasattr(stats, '__getitem__') else stats['letzte_buchung']
            letzte_30 = stats[3] if hasattr(stats, '__getitem__') else stats['letzte_30_tage']
            
            print(f"  Gesamt: {anzahl} Transaktionen")
            print(f"  Erste Buchung: {erste}")
            print(f"  Letzte Buchung: {letzte}")
            print(f"  Letzte 30 Tage: {letzte_30} Transaktionen")
            print()
            
            # Wie alt ist die letzte Buchung?
            if letzte:
                if isinstance(letzte, str):
                    letzte_date = datetime.strptime(letzte[:10], '%Y-%m-%d').date()
                else:
                    letzte_date = letzte
                
                tage_alt = (datetime.now().date() - letzte_date).days
                print(f"  ⏰ Letzte Buchung ist {tage_alt} Tage alt")
                
                if tage_alt > 3:
                    print(f"  ⚠️  WARNUNG: Daten sind veraltet (>3 Tage)")
                elif tage_alt > 1:
                    print(f"  ⚠️  HINWEIS: Daten sind >1 Tag alt")
                else:
                    print(f"  ✅ Daten sind aktuell")
            else:
                print("  ❌ Keine Transaktionen gefunden!")
        
        # 3. Letzte 5 Transaktionen
        print()
        print("📄 LETZTE 5 TRANSAKTIONEN:")
        print("-" * 70)
        cursor.execute(f"""
            SELECT 
                buchungsdatum,
                betrag,
                LEFT(verwendungszweck, 50) as verwendungszweck_short
            FROM transaktionen
            WHERE konto_id = {ph}
            ORDER BY buchungsdatum DESC, id DESC
            LIMIT 5
        """, (konto_id,))
        
        transaktionen = cursor.fetchall()
        if transaktionen:
            for i, tx in enumerate(transaktionen, 1):
                datum = tx[0] if hasattr(tx, '__getitem__') else tx['buchungsdatum']
                betrag = tx[1] if hasattr(tx, '__getitem__') else tx['betrag']
                vzweck = tx[2] if hasattr(tx, '__getitem__') else tx['verwendungszweck_short']
                
                betrag_str = f"{float(betrag):,.2f} €" if betrag else "0.00 €"
                print(f"  {i}. {datum} | {betrag_str:>15} | {vzweck}")
        else:
            print("  Keine Transaktionen gefunden")
        
        # 4. Salden-Info
        print()
        print("💰 SALDEN:")
        print("-" * 70)
        cursor.execute(f"""
            SELECT 
                COUNT(*) as anzahl,
                MAX(datum) as neuester_saldo,
                MAX(saldo) as aktueller_saldo
            FROM salden
            WHERE konto_id = {ph}
        """, (konto_id,))
        
        saldo_stats = cursor.fetchone()
        if saldo_stats:
            anzahl = saldo_stats[0] if hasattr(saldo_stats, '__getitem__') else saldo_stats['anzahl']
            neuester = saldo_stats[1] if hasattr(saldo_stats, '__getitem__') else saldo_stats['neuester_saldo']
            saldo = saldo_stats[2] if hasattr(saldo_stats, '__getitem__') else saldo_stats['aktueller_saldo']
            
            print(f"  Anzahl Salden: {anzahl}")
            print(f"  Neuester Saldo: {neuester}")
            if saldo:
                print(f"  Aktueller Saldo: {float(saldo):,.2f} €")
        
        # 5. View v_aktuelle_kontostaende prüfen
        print()
        print("🔍 VIEW v_aktuelle_kontostaende:")
        print("-" * 70)
        cursor.execute(f"""
            SELECT 
                saldo,
                letztes_update
            FROM v_aktuelle_kontostaende
            WHERE iban = {ph}
        """, ('DE22741200710006407420',))
        
        view_data = cursor.fetchone()
        if view_data:
            saldo = view_data[0] if hasattr(view_data, '__getitem__') else view_data['saldo']
            letztes_update = view_data[1] if hasattr(view_data, '__getitem__') else view_data['letztes_update']
            
            print(f"  Saldo: {float(saldo):,.2f} €" if saldo else "  Saldo: N/A")
            print(f"  Letztes Update: {letztes_update}")
            
            if letztes_update:
                if isinstance(letztes_update, str):
                    update_date = datetime.strptime(str(letztes_update)[:10], '%Y-%m-%d').date()
                else:
                    update_date = letztes_update
                
                tage_alt = (datetime.now().date() - update_date).days
                print(f"  ⏰ Update ist {tage_alt} Tage alt")
        else:
            print("  ❌ Keine Daten in View gefunden")
        
        conn.close()
        
        print()
        print("="*70)
        print("✅ PRÜFUNG ABGESCHLOSSEN")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_hvb_datenstand()

