#!/usr/bin/env python3
"""
Detaillierte Analyse der letzten 10 Hyundai Garantieaufträge
============================================================
TAG 173: Mit konkreten Handlungsempfehlungen
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Projekt-Pfad
sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session, row_to_dict, rows_to_list
from psycopg2.extras import RealDictCursor

def analyse_hyundai_garantie_detailed():
    """Detaillierte Analyse der letzten 10 Hyundai Garantieaufträge."""
    
    print("="*80)
    print("DETAILLIERTE ANALYSE: Letzte 10 Hyundai Garantieaufträge")
    print("="*80)
    print()
    
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query: Letzte 10 Garantieaufträge von Hyundai (Betrieb 2)
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
                LIMIT 10
            ),
            labour_details AS (
                SELECT
                    l.order_number,
                    l.charge_type,
                    l.labour_type,
                    l.time_units as aw,
                    l.net_price_in_order as preis_eur,
                    l.labour_operation_id as arbeitsnummer,
                    l.text_line as beschreibung,
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
            ),
            arbeitspositionen AS (
                SELECT
                    ld.order_number,
                    STRING_AGG(
                        COALESCE(ld.arbeitsnummer, '') || ' (' || ROUND(ld.aw::numeric, 1) || ' AW)',
                        ', ' ORDER BY ld.aw DESC
                    ) as positionen_liste
                FROM labour_details ld
                GROUP BY ld.order_number
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
                ap.positionen_liste,
                CASE
                    WHEN COALESCE(l.gesamt_aw, 0) > 0 THEN
                        ROUND((r.job_amount_net / l.gesamt_aw)::numeric, 2)
                    ELSE 0
                END as aw_preis_eur
            FROM garantie_rechnungen r
            LEFT JOIN labour_summen l ON r.order_number = l.order_number
            LEFT JOIN stempel_summen s ON r.order_number = s.order_number
            LEFT JOIN auftrags_details a ON r.order_number = a.order_number
            LEFT JOIN arbeitspositionen ap ON r.order_number = ap.order_number
            ORDER BY r.invoice_date DESC
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        if not rows:
            print("❌ Keine Garantieaufträge gefunden!")
            return
        
        print(f"✅ {len(rows)} Garantieaufträge analysiert\n")
        
        # Detaillierte Analyse für jeden Auftrag
        for idx, r in enumerate(rows, 1):
            print("="*80)
            print(f"AUFTRAG {idx}: #{r['order_number']}")
            print("="*80)
            print()
            
            # Basis-Informationen
            print(f"Datum:              {r['invoice_date'].strftime('%d.%m.%Y') if r['invoice_date'] else 'N/A'}")
            print(f"Serviceberater:     {r['sb_name'] or 'N/A'}")
            print(f"Kennzeichen:        {r['kennzeichen'] or 'N/A'}")
            print(f"Marke:              {r['marke'] or 'N/A'}")
            print(f"Kunde:              {r['kunde'] or 'N/A'}")
            print()
            
            # Abrechnungsdaten
            print("ABRECHNUNG:")
            print(f"  Lohn (EUR):        {r['lohn_eur']:,.2f} €")
            print(f"  Teile (EUR):       {r['teile_eur']:,.2f} €")
            print(f"  Gesamt (EUR):      {r['gesamt_eur']:,.2f} €")
            print(f"  AW gesamt:         {r['gesamt_aw']:.1f} AW")
            print(f"  AW-Preis:          {r['aw_preis_eur']:.2f} €/AW")
            print(f"  Gestempelt:        {r['gestempelt_aw']:.1f} AW ({r['gestempelt_min']:.0f} Min)")
            print()
            
            # Arbeitspositionen
            if r['positionen_liste']:
                print("ARBEITSPOSITIONEN:")
                positionen = r['positionen_liste'].split(', ')
                for pos in positionen[:10]:  # Max 10 anzeigen
                    print(f"  - {pos}")
                if len(positionen) > 10:
                    print(f"  ... und {len(positionen) - 10} weitere")
                print()
            
            # Diagnose-Codes
            print("DIAGNOSE-VERGÜTUNG:")
            basica00_vorhanden = r['basica00_aw'] and float(r['basica00_aw'] or 0) > 0
            rq0_vorhanden = r['rq0_aw'] and float(r['rq0_aw'] or 0) > 0
            tt_vorhanden = r['tt_aw'] and float(r['tt_aw'] or 0) > 0
            
            if basica00_vorhanden:
                print(f"  ✅ BASICA00 (GDS-Grundprüfung): {r['basica00_aw']:.1f} AW = {float(r['basica00_aw']) * 8.43:.2f} €")
            else:
                print(f"  ❌ BASICA00 (GDS-Grundprüfung): NICHT eingereicht")
            
            if rq0_vorhanden:
                print(f"  ✅ RQ0 (Erweiterte Diagnose): {r['rq0_aw']:.1f} AW = {float(r['rq0_aw']) * 8.43:.2f} €")
            else:
                print(f"  ❌ RQ0 (Erweiterte Diagnose): NICHT eingereicht")
            
            if tt_vorhanden:
                tt_aw = float(r['tt_aw'] or 0)
                tt_eur = float(r['tt_eur'] or 0)
                print(f"  ✅ TT-Zeit: {tt_aw:.1f} AW = {tt_eur:.2f} €")
                if tt_aw >= 10:
                    print(f"     ⚠️  WARNUNG: {tt_aw:.1f} AW = {tt_aw/10:.1f} Stunden - Freigabe erforderlich!")
                elif tt_aw < 9:
                    print(f"     ℹ️  Noch {9 - tt_aw:.1f} AW möglich ohne Freigabe (bis 9 AW = 0,9h)")
            else:
                print(f"  ❌ TT-Zeit: NICHT eingereicht")
            
            print()
            
            # Handlungsempfehlungen
            print("HANDLUNGSEMPFEHLUNGEN:")
            empfehlungen = []
            potenzial = 0.0
            
            # 1. BASICA00 prüfen
            if not basica00_vorhanden and not rq0_vorhanden:
                empfehlungen.append("  ✅ GDS-Grundprüfung (BASICA00) einreichen → +1 AW = +8,43€")
                potenzial += 8.43
            
            # 2. TT-Zeit prüfen
            if not tt_vorhanden:
                # Prüfe ob Diagnosezeit vorhanden (gestempelt > vorgabe)
                gestempelt_aw = float(r['gestempelt_aw'] or 0)
                vorgabe_aw = float(r['gesamt_aw'] or 0)
                
                if gestempelt_aw > vorgabe_aw:
                    differenz_aw = gestempelt_aw - vorgabe_aw
                    if differenz_aw <= 9:
                        empfehlungen.append(f"  ✅ TT-Zeit einreichen ({differenz_aw:.1f} AW) → +{differenz_aw * 8.43:.2f}€")
                        potenzial += differenz_aw * 8.43
                    else:
                        empfehlungen.append(f"  ⚠️  TT-Zeit möglich ({differenz_aw:.1f} AW), aber Freigabe erforderlich (ab 10 AW)")
                        empfehlungen.append(f"     → Potenzial: +{min(differenz_aw, 9) * 8.43:.2f}€ ohne Freigabe, +{differenz_aw * 8.43:.2f}€ mit Freigabe")
                        potenzial += min(differenz_aw, 9) * 8.43
                else:
                    empfehlungen.append("  ℹ️  TT-Zeit möglich, wenn Diagnosezeit > Standardarbeitszeit")
                    empfehlungen.append("     → Prüfen: Wurde Diagnose durchgeführt?")
            else:
                tt_aw = float(r['tt_aw'] or 0)
                if tt_aw < 9:
                    rest_aw = 9 - tt_aw
                    empfehlungen.append(f"  ℹ️  TT-Zeit bereits vorhanden ({tt_aw:.1f} AW)")
                    empfehlungen.append(f"     → Noch {rest_aw:.1f} AW möglich ohne Freigabe (bis 9 AW)")
            
            # 3. RQ0 prüfen (wenn Fehlercodes vorhanden)
            if not rq0_vorhanden and not basica00_vorhanden:
                empfehlungen.append("  ℹ️  RQ0 (Erweiterte Diagnose) möglich, wenn Fehlercodes gefunden → +3 AW = +25,29€")
            
            if not empfehlungen:
                print("  ✅ Keine weiteren Optimierungen möglich (alle Möglichkeiten genutzt)")
            else:
                for emp in empfehlungen:
                    print(emp)
            
            if potenzial > 0:
                print()
                print(f"  💰 VERBESSERUNGSPOTENZIAL: +{potenzial:.2f}€")
            
            print()
            print()
        
        # Zusammenfassung
        print("="*80)
        print("ZUSAMMENFASSUNG")
        print("="*80)
        print()
        
        gesamt_potenzial = 0.0
        anzahl_mit_basica00 = sum(1 for r in rows if r['basica00_aw'] and float(r['basica00_aw'] or 0) > 0)
        anzahl_mit_rq0 = sum(1 for r in rows if r['rq0_aw'] and float(r['rq0_aw'] or 0) > 0)
        anzahl_mit_tt = sum(1 for r in rows if r['tt_aw'] and float(r['tt_aw'] or 0) > 0)
        
        print(f"Aufträge analysiert:         {len(rows)}")
        print(f"Mit BASICA00:                {anzahl_mit_basica00} ({anzahl_mit_basica00/len(rows)*100:.1f}%)")
        print(f"Mit RQ0:                      {anzahl_mit_rq0} ({anzahl_mit_rq0/len(rows)*100:.1f}%)")
        print(f"Mit TT-Zeit:                 {anzahl_mit_tt} ({anzahl_mit_tt/len(rows)*100:.1f}%)")
        print()
        
        # Potenzial-Berechnung
        for r in rows:
            # BASICA00 Potenzial
            if not (r['basica00_aw'] and float(r['basica00_aw'] or 0) > 0) and not (r['rq0_aw'] and float(r['rq0_aw'] or 0) > 0):
                gesamt_potenzial += 8.43
            
            # TT-Zeit Potenzial (vereinfacht)
            if not (r['tt_aw'] and float(r['tt_aw'] or 0) > 0):
                gestempelt_aw = float(r['gestempelt_aw'] or 0)
                vorgabe_aw = float(r['gesamt_aw'] or 0)
                if gestempelt_aw > vorgabe_aw:
                    differenz_aw = min(gestempelt_aw - vorgabe_aw, 9)
                    gesamt_potenzial += differenz_aw * 8.43
        
        print(f"GESAMT-POTENZIAL:            +{gesamt_potenzial:.2f}€")
        print(f"Durchschnitt pro Auftrag:    +{gesamt_potenzial/len(rows):.2f}€")
        print()
        
        cur.close()

if __name__ == '__main__':
    analyse_hyundai_garantie_detailed()
