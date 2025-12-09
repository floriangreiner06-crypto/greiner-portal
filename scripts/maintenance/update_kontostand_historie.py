#!/usr/bin/env python3
"""
Befüllt kontostand_historie aus Transaktionen
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'greiner_controlling.db'

def update_historie():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🔄 Befülle kontostand_historie aus Transaktionen...")
    
    # Für jedes Konto: Aktueller Saldo aus letzter Transaktion
    c.execute("""
        INSERT OR REPLACE INTO kontostand_historie (konto_id, datum, saldo, quelle)
        SELECT 
            k.id as konto_id,
            COALESCE(
                (SELECT MAX(buchungsdatum) FROM transaktionen WHERE konto_id = k.id),
                DATE('now')
            ) as datum,
            COALESCE(
                (SELECT saldo_nach_buchung 
                 FROM transaktionen 
                 WHERE konto_id = k.id 
                 ORDER BY buchungsdatum DESC, id DESC 
                 LIMIT 1),
                0.0
            ) as saldo,
            'Berechnet' as quelle
        FROM konten k
        WHERE k.aktiv = 1
    """)
    
    rows = c.rowcount
    conn.commit()
    
    print(f"✅ {rows} Kontostände aktualisiert!")
    
    # Zeige Ergebnis
    c.execute("""
        SELECT 
            b.bank_name,
            k.kontoname,
            kh.saldo,
            kh.datum
        FROM kontostand_historie kh
        JOIN konten k ON kh.konto_id = k.id
        JOIN banken b ON k.bank_id = b.id
        ORDER BY b.bank_name, k.kontoname
    """)
    
    print("\n📊 Aktuelle Kontostände:")
    total = 0
    for bank, konto, saldo, datum in c.fetchall():
        total += saldo
        print(f"{bank:<35} {konto:<30} {saldo:>15,.2f} € ({datum})")
    
    print(f"\n{'GESAMT:':<66} {total:>15,.2f} €")
    
    conn.close()

if __name__ == '__main__':
    update_historie()
