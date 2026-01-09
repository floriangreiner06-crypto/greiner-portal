#!/usr/bin/env python3
"""
Analyse der letzten 30 Hyundai Garantieaufträge aus Locosoft
============================================================
TAG 173: Analyse für Diagnose-Vergütung Optimierung
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session, row_to_dict, rows_to_list
from psycopg2.extras import RealDictCursor

def analyse_hyundai_garantie_auftraege():
    """Analysiert die letzten 30 Hyundai Garantieaufträge."""
    
    print("="*80)
    print("ANALYSE: Letzte 30 Hyundai Garantieaufträge")
    print("="*80)
    print()
    
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query: Letzte 30 Garantieaufträge von Hyundai (Betrieb 2)
        query = """
            WITH garantie_rechnungen AS (
                SELECT DISTINCT
                    i.order_number,
                    i.invoice_number,
                    i.invoice_date,
                    i.job_amount_net,
                    i.part_amount_net,
                    i.subsidiary
                FROM invoices i
                WHERE i.invoice_type = 6  -- Garantie
                  AND i.subsidiary = 2    -- Hyundai
                  AND i.is_canceled = false
                  AND i.job_amount_net > 0
                ORDER BY i.invoice_date DESC
                LIMIT 30
            ),
            labour_details AS (
                SELECT
                    l.order_number,
                    l.charge_type,
                    l.labour_type,
                    l.time_units as aw,
                    l.net_price_in_order as preis_eur,
                    l.labour_operation_id as arbeitsnummer,
                    -- TT-Zeit erkennen: Arbeitsnummer endet mit RTT oder HTT
                    CASE 
                        WHEN l.labour_operation_id LIKE '%RTT' OR l.labour_operation_id LIKE '%HTT' THEN true
                        ELSE false
                    END as ist_tt_zeit,
                    -- Diagnose-Codes erkennen
                    CASE
                        WHEN l.labour_operation_id = 'BASICA00' THEN 'GDS-Grundprüfung'
                        WHEN l.labour_operation_id = 'RQ0' THEN 'Erweiterte Diagnose'
                        WHEN l.labour_operation_id LIKE '%RTT' THEN 'TT-Zeit (RTT)'
                        WHEN l.labour_operation_id LIKE '%HTT' THEN 'TT-Zeit (HTT)'
                        ELSE NULL
                    END as diagnose_typ
                FROM labours l
                WHERE l.order_number IN (SELECT order_number FROM garantie_rechnungen)
                  AND l.is_invoiced = true
            ),
            labour_summen AS (
                SELECT
                    order_number,
                    COUNT(*) as anzahl_positionen,
                    SUM(aw) as gesamt_aw,
                    SUM(preis_eur) as gesamt_lohn_eur,
                    SUM(CASE WHEN ist_tt_zeit THEN aw ELSE 0 END) as tt_aw,
                    SUM(CASE WHEN ist_tt_zeit THEN preis_eur ELSE 0 END) as tt_eur,
                    SUM(CASE WHEN diagnose_typ = 'GDS-Grundprüfung' THEN aw ELSE 0 END) as basica00_aw,
                    SUM(CASE WHEN diagnose_typ = 'Erweiterte Diagnose' THEN aw ELSE 0 END) as rq0_aw,
                    STRING_AGG(DISTINCT diagnose_typ, ', ') FILTER (WHERE diagnose_typ IS NOT NULL) as diagnose_typen,
                    STRING_AGG(DISTINCT arbeitsnummer, ', ') FILTER (WHERE ist_tt_zeit = true) as tt_arbeitsnummern
                FROM labour_details
                GROUP BY order_number
            ),
            stempel_summen AS (
                SELECT
                    order_number,
                    SUM(EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 60) as gestempelt_min
                FROM (
                    SELECT DISTINCT ON (order_number, employee_number, start_time, end_time)
                        order_number,
                        start_time,
                        end_time
                    FROM times
                    WHERE type = 2
                      AND order_number IN (SELECT order_number FROM garantie_rechnungen)
                ) dedup
                GROUP BY order_number
            ),
            auftrags_details AS (
                SELECT
                    o.number as order_number,
                    o.order_date,
                    o.order_taking_employee_no as sb_nr,
                    sb.name as sb_name,
                    v.license_plate as kennzeichen,
                    m.description as marke,
                    COALESCE(cs.family_name || ', ' || cs.first_name, cs.family_name, 'Unbekannt') as kunde
                FROM orders o
                LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                    AND sb.is_latest_record = true
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN makes m ON v.make_number = m.make_number
                LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
                WHERE o.number IN (SELECT order_number FROM garantie_rechnungen)
            )
            SELECT
                r.order_number,
                r.invoice_number,
                r.invoice_date,
                ROUND(r.job_amount_net::numeric, 2) as lohn_eur,
                ROUND(r.part_amount_net::numeric, 2) as teile_eur,
                ROUND((r.job_amount_net + r.part_amount_net)::numeric, 2) as gesamt_eur,
                ROUND(COALESCE(l.gesamt_aw, 0)::numeric, 1) as gesamt_aw,
                ROUND(COALESCE(l.tt_aw, 0)::numeric, 1) as tt_aw,
                ROUND(COALESCE(l.tt_eur, 0)::numeric, 2) as tt_eur,
                ROUND(COALESCE(l.basica00_aw, 0)::numeric, 1) as basica00_aw,
                ROUND(COALESCE(l.rq0_aw, 0)::numeric, 1) as rq0_aw,
                l.diagnose_typen,
                l.tt_arbeitsnummern,
                ROUND(COALESCE(s.gestempelt_min, 0)::numeric / 6, 1) as gestempelt_aw,
                ROUND(COALESCE(s.gestempelt_min, 0)::numeric, 0) as gestempelt_min,
                a.sb_name,
                a.kennzeichen,
                a.marke,
                a.kunde,
                CASE
                    WHEN COALESCE(l.gesamt_aw, 0) > 0 THEN
                        ROUND((r.job_amount_net / l.gesamt_aw)::numeric, 2)
                    ELSE 0
                END as aw_preis_eur
            FROM garantie_rechnungen r
            LEFT JOIN labour_summen l ON r.order_number = l.order_number
            LEFT JOIN stempel_summen s ON r.order_number = s.order_number
            LEFT JOIN auftrags_details a ON r.order_number = a.order_number
            ORDER BY r.invoice_date DESC
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        if not rows:
            print("❌ Keine Garantieaufträge gefunden!")
            return
        
        print(f"✅ {len(rows)} Garantieaufträge gefunden\n")
        
        # Statistik
        gesamt_lohn = sum(float(r['lohn_eur'] or 0) for r in rows)
        gesamt_aw = sum(float(r['gesamt_aw'] or 0) for r in rows)
        gesamt_tt_aw = sum(float(r['tt_aw'] or 0) for r in rows)
        gesamt_basica00 = sum(float(r['basica00_aw'] or 0) for r in rows)
        gesamt_rq0 = sum(float(r['rq0_aw'] or 0) for r in rows)
        anzahl_mit_tt = sum(1 for r in rows if float(r['tt_aw'] or 0) > 0)
        anzahl_mit_basica00 = sum(1 for r in rows if float(r['basica00_aw'] or 0) > 0)
        anzahl_mit_rq0 = sum(1 for r in rows if float(r['rq0_aw'] or 0) > 0)
        
        print("="*80)
        print("STATISTIK")
        print("="*80)
        print(f"Anzahl Aufträge:              {len(rows)}")
        print(f"Gesamt Lohn (EUR):            {gesamt_lohn:,.2f} €")
        print(f"Gesamt AW:                    {gesamt_aw:,.1f} AW")
        print(f"Durchschnitt AW/Auftrag:      {gesamt_aw/len(rows):.1f} AW")
        print(f"Durchschnitt Lohn/Auftrag:    {gesamt_lohn/len(rows):,.2f} €")
        print()
        print(f"TT-Zeiten:")
        print(f"  - Aufträge mit TT-Zeit:     {anzahl_mit_tt} ({anzahl_mit_tt/len(rows)*100:.1f}%)")
        print(f"  - Gesamt TT-AW:             {gesamt_tt_aw:,.1f} AW")
        print(f"  - Durchschnitt TT-AW:       {gesamt_tt_aw/max(anzahl_mit_tt,1):.1f} AW (bei Aufträgen mit TT)")
        print()
        print(f"Diagnose-Codes:")
        print(f"  - Aufträge mit BASICA00:    {anzahl_mit_basica00} ({anzahl_mit_basica00/len(rows)*100:.1f}%)")
        print(f"  - Gesamt BASICA00-AW:       {gesamt_basica00:,.1f} AW")
        print(f"  - Aufträge mit RQ0:         {anzahl_mit_rq0} ({anzahl_mit_rq0/len(rows)*100:.1f}%)")
        print(f"  - Gesamt RQ0-AW:            {gesamt_rq0:,.1f} AW")
        print()
        
        # Tabelle
        print("="*80)
        print("DETAILLIERTE AUFLISTUNG")
        print("="*80)
        print()
        
        # Header
        print(f"{'Datum':<12} {'Auftrag':<8} {'SB':<15} {'Kennz.':<10} {'Marke':<12} {'AW':<6} {'TT-AW':<7} {'BASICA00':<9} {'RQ0':<6} {'Lohn €':<10} {'TT €':<10} {'AW-Preis':<10}")
        print("-"*130)
        
        for r in rows:
            datum = r['invoice_date'].strftime('%Y-%m-%d') if r['invoice_date'] else ''
            auftrag = str(r['order_number'] or '')
            sb = (r['sb_name'] or '')[:14]
            kennz = (r['kennzeichen'] or '')[:9]
            marke = (r['marke'] or '')[:11]
            aw = f"{r['gesamt_aw']:.1f}" if r['gesamt_aw'] else "0.0"
            tt_aw = f"{r['tt_aw']:.1f}" if r['tt_aw'] and float(r['tt_aw'] or 0) > 0 else "-"
            basica00 = f"{r['basica00_aw']:.1f}" if r['basica00_aw'] and float(r['basica00_aw'] or 0) > 0 else "-"
            rq0 = f"{r['rq0_aw']:.1f}" if r['rq0_aw'] and float(r['rq0_aw'] or 0) > 0 else "-"
            lohn = f"{r['lohn_eur']:,.2f}" if r['lohn_eur'] else "0.00"
            tt_eur = f"{r['tt_eur']:,.2f}" if r['tt_eur'] and float(r['tt_eur'] or 0) > 0 else "-"
            aw_preis = f"{r['aw_preis_eur']:.2f}" if r['aw_preis_eur'] else "-"
            
            print(f"{datum:<12} {auftrag:<8} {sb:<15} {kennz:<10} {marke:<12} {aw:<6} {tt_aw:<7} {basica00:<9} {rq0:<6} {lohn:<10} {tt_eur:<10} {aw_preis:<10}")
        
        print()
        print("="*80)
        print("ERKLÄRUNG: Was ist eine TT-Zeit?")
        print("="*80)
        print()
        print("TT-Zeit = 'Tatsächliche Zeit' (Time Taken)")
        print()
        print("Definition:")
        print("  - TT-Zeiten werden verwendet, wenn für eine Reparatur keine")
        print("    Standardarbeitszeit (LTS) im System hinterlegt ist")
        print("  - Die tatsächlich aufgewendete Zeit wird abgerechnet")
        print()
        print("Arbeitsnummern-Format:")
        print("  - RTT: Teil aus- und einbauen (z.B. 28257RTT)")
        print("  - HTT: Teil aus- und einbauen + Instandsetzung (z.B. 91860HTT)")
        print()
        print("Vergütungsregeln (Hyundai):")
        print("  - Bis 0,9 Stunden (9 AW): OHNE Freigabe abrechenbar ✅")
        print("  - Ab 1,0 Stunden (10 AW): Freigabe über GWMS erforderlich")
        print("  - Wichtig: Nur tatsächlich aufgewendete Zeit, nicht generell 0,9h!")
        print()
        print("Potenzial:")
        print("  - Bis zu 75,87€ zusätzliche Vergütung pro Auftrag möglich")
        print("  - Wird aktuell vermutlich nicht optimal genutzt")
        print()
        
        cur.close()

if __name__ == '__main__':
    analyse_hyundai_garantie_auftraege()
