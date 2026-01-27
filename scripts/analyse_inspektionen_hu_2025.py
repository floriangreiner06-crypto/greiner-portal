#!/usr/bin/env python3
"""
Analyse: Inspektionen und Hauptuntersuchungen in Locosoft
==========================================================
Zeitraum: 02.01.2025 - 30.12.2025
"""

import sys
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

def analyse_inspektionen_hu():
    """Analysiert Inspektionen und Hauptuntersuchungen in Locosoft"""
    
    # Zeitraum: 02.01.2025 - 30.12.2025
    von_datum = '2025-01-02'
    bis_datum = '2025-12-31'  # bis einschließlich 30.12.2025
    
    print("=" * 100)
    print("Analyse: Inspektionen und Hauptuntersuchungen in Locosoft")
    print(f"Zeitraum: {von_datum} - {bis_datum}")
    print("=" * 100)
    
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Zuerst: Welche Begriffe kommen in text_line vor?
        print("\n1. HÄUFIGSTE BEGRIFFE in text_line (labours):")
        print("-" * 100)
        
        cur.execute("""
            SELECT 
                l.text_line,
                COUNT(*) as anzahl
            FROM labours l
            INNER JOIN invoices i ON l.order_number = i.order_number 
                AND l.invoice_type = i.invoice_type 
                AND l.invoice_number = i.invoice_number
            WHERE l.is_invoiced = true
              AND i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND l.text_line IS NOT NULL
              AND l.text_line != ''
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
                  OR LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
            GROUP BY l.text_line
            ORDER BY anzahl DESC
            LIMIT 50
        """, (von_datum, bis_datum))
        
        begriffe = cur.fetchall()
        print(f"Gefunden: {len(begriffe)} verschiedene Begriffe\n")
        for row in begriffe[:20]:  # Top 20
            print(f"  {row['text_line'][:80]:80s} | {row['anzahl']:6d}x")
        
        # 2. Prüfe Duplikate: Rechnungen pro VIN
        print("\n\n2. DUPLIKAT-PRÜFUNG (Rechnungen pro VIN):")
        print("-" * 100)
        
        cur.execute("""
            SELECT 
                v.vin,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
                  OR LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
              )
              AND v.vin IS NOT NULL
              AND v.vin != ''
            GROUP BY v.vin
            HAVING COUNT(DISTINCT i.invoice_number) > 1
            ORDER BY anzahl_rechnungen DESC
            LIMIT 20
        """, (von_datum, bis_datum))
        
        duplikate = cur.fetchall()
        print(f"VINs mit mehreren Rechnungen: {len(duplikate)} (Top 20)\n")
        for row in duplikate:
            print(f"  VIN {row['vin']:17s} | {row['anzahl_rechnungen']:3d} Rechnungen")
        
        # 3. Inspektionen identifizieren (PRO VIN)
        print("\n\n3. INSPEKTIONEN (pro VIN - fakturierte Fahrzeuge):")
        print("-" * 100)
        
        cur.execute("""
            SELECT COUNT(DISTINCT v.vin) as anzahl_fahrzeuge
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)  -- Werkstatt, Reklamation, Garantie
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu%%'
              AND v.vin IS NOT NULL
              AND v.vin != ''
        """, (von_datum, bis_datum))
        
        inspektionen = cur.fetchone()
        anzahl_inspektionen = inspektionen['anzahl_fahrzeuge'] if inspektionen else 0
        
        # Vergleich: Rechnungen vs. VINs
        cur.execute("""
            SELECT COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu%%'
              AND v.vin IS NOT NULL
              AND v.vin != ''
        """, (von_datum, bis_datum))
        
        rechnungen_inspektion = cur.fetchone()
        anzahl_rechnungen_inspektion = rechnungen_inspektion['anzahl_rechnungen'] if rechnungen_inspektion else 0
        
        print(f"Anzahl Inspektions-Fahrzeuge (VIN): {anzahl_inspektionen}")
        print(f"Anzahl Inspektions-Rechnungen:     {anzahl_rechnungen_inspektion}")
        print(f"Differenz (Duplikate):             {anzahl_rechnungen_inspektion - anzahl_inspektionen}")
        
        # 4. Hauptuntersuchungen identifizieren (PRO VIN)
        print("\n\n4. HAUPTUNTERSUCHUNGEN (pro VIN - fakturierte Fahrzeuge):")
        print("-" * 100)
        
        cur.execute("""
            SELECT COUNT(DISTINCT v.vin) as anzahl_fahrzeuge
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)  -- Werkstatt, Reklamation, Garantie
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
              )
              AND v.vin IS NOT NULL
              AND v.vin != ''
        """, (von_datum, bis_datum))
        
        hu = cur.fetchone()
        anzahl_hu = hu['anzahl_fahrzeuge'] if hu else 0
        
        # Vergleich: Rechnungen vs. VINs
        cur.execute("""
            SELECT COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
              )
              AND v.vin IS NOT NULL
              AND v.vin != ''
        """, (von_datum, bis_datum))
        
        rechnungen_hu = cur.fetchone()
        anzahl_rechnungen_hu = rechnungen_hu['anzahl_rechnungen'] if rechnungen_hu else 0
        
        print(f"Anzahl HU-Fahrzeuge (VIN):          {anzahl_hu}")
        print(f"Anzahl HU-Rechnungen:              {anzahl_rechnungen_hu}")
        print(f"Differenz (Duplikate):             {anzahl_rechnungen_hu - anzahl_hu}")
        
        # 5. Detaillierte Analyse: Beispiele mit VIN
        print("\n\n5. BEISPIEL-FAHRZEUGE (Inspektionen - pro VIN):")
        print("-" * 100)
        
        cur.execute("""
            SELECT DISTINCT
                v.vin,
                v.license_plate as kennzeichen,
                i.subsidiary,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                MIN(i.invoice_date) as erste_rechnung,
                MAX(i.invoice_date) as letzte_rechnung,
                STRING_AGG(DISTINCT l.text_line, ' | ' ORDER BY l.text_line) as positionen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu%%'
              AND v.vin IS NOT NULL
              AND v.vin != ''
            GROUP BY v.vin, v.license_plate, i.subsidiary
            ORDER BY anzahl_rechnungen DESC, letzte_rechnung DESC
            LIMIT 10
        """, (von_datum, bis_datum))
        
        beispiele_inspektion = cur.fetchall()
        print(f"Beispiele (Top 10 - nach Anzahl Rechnungen):\n")
        for row in beispiele_inspektion:
            print(f"  VIN {row['vin']:17s} | {row['kennzeichen'] or 'N/A':10s} | {row['anzahl_rechnungen']:2d}x | {row['erste_rechnung']} - {row['letzte_rechnung']}")
            print(f"    Positionen: {row['positionen'][:80]}")
        
        print("\n\n6. BEISPIEL-FAHRZEUGE (Hauptuntersuchungen - pro VIN):")
        print("-" * 100)
        
        cur.execute("""
            SELECT DISTINCT
                v.vin,
                v.license_plate as kennzeichen,
                i.subsidiary,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                MIN(i.invoice_date) as erste_rechnung,
                MAX(i.invoice_date) as letzte_rechnung,
                STRING_AGG(DISTINCT l.text_line, ' | ' ORDER BY l.text_line) as positionen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
              )
              AND v.vin IS NOT NULL
              AND v.vin != ''
            GROUP BY v.vin, v.license_plate, i.subsidiary
            ORDER BY anzahl_rechnungen DESC, letzte_rechnung DESC
            LIMIT 10
        """, (von_datum, bis_datum))
        
        beispiele_hu = cur.fetchall()
        print(f"Beispiele (Top 10 - nach Anzahl Rechnungen):\n")
        for row in beispiele_hu:
            print(f"  VIN {row['vin']:17s} | {row['kennzeichen'] or 'N/A':10s} | {row['anzahl_rechnungen']:2d}x | {row['erste_rechnung']} - {row['letzte_rechnung']}")
            print(f"    Positionen: {row['positionen'][:80]}")
        
        # 7. Zusammenfassung
        print("\n\n" + "=" * 100)
        print("ZUSAMMENFASSUNG (PRO VIN - EINDEUTIGE FAHRZEUGE):")
        print("=" * 100)
        print(f"Zeitraum: {von_datum} - {bis_datum}")
        print(f"\nInspektions-Fahrzeuge (VIN):      {anzahl_inspektionen:6d}")
        print(f"Hauptuntersuchungs-Fahrzeuge (VIN): {anzahl_hu:6d}")
        print(f"\nGesamt (eindeutige Fahrzeuge):     {anzahl_inspektionen + anzahl_hu:6d}")
        print("\n⚠️  HINWEIS: Ein Fahrzeug kann sowohl Inspektion als auch HU haben!")
        print("=" * 100)
        
        # 8. Nach Betrieb aufgeteilt (PRO VIN)
        print("\n\n7. AUFTEILUNG NACH BETRIEB (PRO VIN):")
        print("-" * 100)
        
        cur.execute("""
            SELECT 
                i.subsidiary,
                COUNT(DISTINCT CASE 
                    WHEN (
                        LOWER(l.text_line) LIKE '%%inspektion%%'
                        OR LOWER(l.text_line) LIKE '%%wartung%%'
                    )
                    AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
                    AND LOWER(l.text_line) NOT LIKE '%%hu%%'
                    THEN v.vin
                END) as inspektionen,
                COUNT(DISTINCT CASE 
                    WHEN (
                        LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                        OR LOWER(l.text_line) LIKE '%%hu%%'
                    )
                    THEN v.vin
                END) as hauptuntersuchungen
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
                  OR LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                  OR LOWER(l.text_line) LIKE '%%hu%%'
              )
              AND v.vin IS NOT NULL
              AND v.vin != ''
            GROUP BY i.subsidiary
            ORDER BY i.subsidiary
        """, (von_datum, bis_datum))
        
        betriebe = cur.fetchall()
        print(f"{'Betrieb':<10} | {'Inspektionen':>15} | {'Hauptuntersuchungen':>20} | {'Gesamt':>10}")
        print("-" * 70)
        for row in betriebe:
            betrieb_name = {1: 'DEGO', 2: 'HYU', 3: 'LAN'}.get(row['subsidiary'], f"Betrieb {row['subsidiary']}")
            gesamt = (row['inspektionen'] or 0) + (row['hauptuntersuchungen'] or 0)
            print(f"{betrieb_name:<10} | {row['inspektionen'] or 0:15d} | {row['hauptuntersuchungen'] or 0:20d} | {gesamt:10d}")
        
        # 9. Fahrzeuge mit BEIDEM (Inspektion UND HU)
        print("\n\n8. FAHRZEUGE MIT BEIDEM (Inspektion UND HU im Zeitraum):")
        print("-" * 100)
        
        cur.execute("""
            WITH inspektion_vin AS (
                SELECT DISTINCT v.vin
                FROM invoices i
                INNER JOIN orders o ON i.order_number = o.number
                INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
                INNER JOIN labours l ON i.order_number = l.order_number
                WHERE i.invoice_date >= %s
                  AND i.invoice_date < %s
                  AND i.is_canceled = false
                  AND i.invoice_type IN (2, 3, 6)
                  AND l.is_invoiced = true
                  AND (
                      LOWER(l.text_line) LIKE '%%inspektion%%'
                      OR LOWER(l.text_line) LIKE '%%wartung%%'
                  )
                  AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
                  AND LOWER(l.text_line) NOT LIKE '%%hu%%'
                  AND v.vin IS NOT NULL
                  AND v.vin != ''
            ),
            hu_vin AS (
                SELECT DISTINCT v.vin
                FROM invoices i
                INNER JOIN orders o ON i.order_number = o.number
                INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
                INNER JOIN labours l ON i.order_number = l.order_number
                WHERE i.invoice_date >= %s
                  AND i.invoice_date < %s
                  AND i.is_canceled = false
                  AND i.invoice_type IN (2, 3, 6)
                  AND l.is_invoiced = true
                  AND (
                      LOWER(l.text_line) LIKE '%%hauptuntersuchung%%'
                      OR LOWER(l.text_line) LIKE '%%hu%%'
                  )
                  AND v.vin IS NOT NULL
                  AND v.vin != ''
            )
            SELECT COUNT(*) as anzahl_beide
            FROM inspektion_vin i
            INNER JOIN hu_vin h ON i.vin = h.vin
        """, (von_datum, bis_datum, von_datum, bis_datum))
        
        beide = cur.fetchone()
        anzahl_beide = beide['anzahl_beide'] if beide else 0
        print(f"Fahrzeuge mit Inspektion UND HU: {anzahl_beide}")
        print(f"\n⚠️  HINWEIS: Diese Fahrzeuge werden in beiden Kategorien gezählt!")
        
        # 10. Umsatz der Inspektionen (nur Arbeitszeit, exklusiv)
        print("\n\n9. UMSATZ DER INSPEKTIONEN (exklusiv - nur Inspektion-Positionen):")
        print("-" * 100)
        
        cur.execute("""
            SELECT 
                COALESCE(SUM(l.net_price_in_order), 0) as umsatz_netto,
                COUNT(*) as anzahl_positionen,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                COUNT(DISTINCT v.vin) as anzahl_fahrzeuge,
                COALESCE(SUM(l.time_units), 0) as gesamt_aw,
                COALESCE(AVG(l.net_price_in_order / NULLIF(l.time_units, 0)), 0) as avg_aw_preis
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
                AND l.invoice_type = i.invoice_type
                AND l.invoice_number = i.invoice_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu%%'
              AND v.vin IS NOT NULL
              AND v.vin != ''
        """, (von_datum, bis_datum))
        
        umsatz_inspektion = cur.fetchone()
        umsatz_netto_inspektion = float(umsatz_inspektion['umsatz_netto'] or 0) if umsatz_inspektion else 0
        anzahl_pos_inspektion = umsatz_inspektion['anzahl_positionen'] if umsatz_inspektion else 0
        anzahl_rechn_inspektion = umsatz_inspektion['anzahl_rechnungen'] if umsatz_inspektion else 0
        anzahl_fahrzeuge_inspektion = umsatz_inspektion['anzahl_fahrzeuge'] if umsatz_inspektion else 0
        gesamt_aw_inspektion = float(umsatz_inspektion['gesamt_aw'] or 0) if umsatz_inspektion else 0
        avg_aw_preis_inspektion = float(umsatz_inspektion['avg_aw_preis'] or 0) if umsatz_inspektion else 0
        
        print(f"Umsatz (Netto, nur Inspektion-Positionen): {umsatz_netto_inspektion:,.2f} EUR")
        print(f"Anzahl Positionen:                          {anzahl_pos_inspektion:6d}")
        print(f"Anzahl Rechnungen:                           {anzahl_rechn_inspektion:6d}")
        print(f"Anzahl Fahrzeuge (VIN):                      {anzahl_fahrzeuge_inspektion:6d}")
        print(f"Gesamt AW:                                   {gesamt_aw_inspektion:,.1f} AW")
        print(f"Durchschnittlicher AW-Preis:                 {avg_aw_preis_inspektion:,.2f} EUR/AW")
        print(f"Durchschnittlicher Umsatz pro Fahrzeug:      {umsatz_netto_inspektion / max(anzahl_fahrzeuge_inspektion, 1):,.2f} EUR")
        
        # 11. Umsatz nach Betrieb aufgeteilt
        print("\n\n10. UMSATZ NACH BETRIEB (Inspektionen):")
        print("-" * 100)
        
        cur.execute("""
            SELECT 
                i.subsidiary,
                COALESCE(SUM(l.net_price_in_order), 0) as umsatz_netto,
                COUNT(*) as anzahl_positionen,
                COUNT(DISTINCT i.invoice_number) as anzahl_rechnungen,
                COUNT(DISTINCT v.vin) as anzahl_fahrzeuge,
                COALESCE(SUM(l.time_units), 0) as gesamt_aw
            FROM invoices i
            INNER JOIN orders o ON i.order_number = o.number
            INNER JOIN vehicles v ON o.vehicle_number = v.internal_number
            INNER JOIN labours l ON i.order_number = l.order_number
                AND l.invoice_type = i.invoice_type
                AND l.invoice_number = i.invoice_number
            WHERE i.invoice_date >= %s
              AND i.invoice_date < %s
              AND i.is_canceled = false
              AND i.invoice_type IN (2, 3, 6)
              AND l.is_invoiced = true
              AND (
                  LOWER(l.text_line) LIKE '%%inspektion%%'
                  OR LOWER(l.text_line) LIKE '%%wartung%%'
              )
              AND LOWER(l.text_line) NOT LIKE '%%hauptuntersuchung%%'
              AND LOWER(l.text_line) NOT LIKE '%%hu%%'
              AND v.vin IS NOT NULL
              AND v.vin != ''
            GROUP BY i.subsidiary
            ORDER BY i.subsidiary
        """, (von_datum, bis_datum))
        
        umsatz_betriebe = cur.fetchall()
        print(f"{'Betrieb':<10} | {'Umsatz (EUR)':>15} | {'Positionen':>12} | {'Rechnungen':>12} | {'Fahrzeuge':>12} | {'AW':>10}")
        print("-" * 85)
        gesamt_umsatz = 0
        for row in umsatz_betriebe:
            betrieb_name = {1: 'DEGO', 2: 'HYU', 3: 'LAN'}.get(row['subsidiary'], f"Betrieb {row['subsidiary']}")
            umsatz = float(row['umsatz_netto'] or 0)
            gesamt_umsatz += umsatz
            print(f"{betrieb_name:<10} | {umsatz:15,.2f} | {row['anzahl_positionen']:12d} | {row['anzahl_rechnungen']:12d} | {row['anzahl_fahrzeuge']:12d} | {float(row['gesamt_aw'] or 0):10.1f}")
        print("-" * 85)
        print(f"{'GESAMT':<10} | {gesamt_umsatz:15,.2f}")

if __name__ == '__main__':
    analyse_inspektionen_hu()
