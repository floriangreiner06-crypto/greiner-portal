#!/usr/bin/env python3
"""
ANALYSE: Kapazitätsplanung Werkstatt - Datenquellen erkunden
============================================================
TAG 94 - Prüft welche Daten für die Kapazitätsplanung verfügbar sind

FIX: is_latest_record ist NULL in Locosoft - wir ermitteln selbst den neuesten Eintrag

Fragestellungen:
1. Offene/vorbereitete Aufträge mit Terminen
2. Vorgabe-AW pro Auftrag
3. Teile-Status (alle Teile da?)
4. Verfügbare Mechaniker
5. Arbeitszeiten pro Tag
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# .env laden
env_path = '/opt/greiner-portal/config/.env'
load_dotenv(env_path)

def get_connection():
    return psycopg2.connect(
        host=os.getenv('LOCOSOFT_HOST'),
        port=os.getenv('LOCOSOFT_PORT', 5432),
        database=os.getenv('LOCOSOFT_DATABASE'),
        user=os.getenv('LOCOSOFT_USER'),
        password=os.getenv('LOCOSOFT_PASSWORD')
    )

def main():
    print("=" * 70)
    print("KAPAZITÄTSPLANUNG - DATENANALYSE (v2 - mit Arbeitszeiten-Fix)")
    print("=" * 70)
    print(f"Zeitpunkt: {datetime.now()}")
    print()
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # =========================================================================
    # 1. OFFENE AUFTRÄGE MIT TERMINEN
    # =========================================================================
    print("\n" + "=" * 70)
    print("1. OFFENE AUFTRÄGE MIT TERMINEN")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.order_date::date as auftragsdatum,
            o.estimated_inbound_time as bringen_termin,
            o.estimated_outbound_time as abhol_termin,
            o.urgency as dringlichkeit,
            o.has_open_positions,
            o.has_closed_positions,
            o.has_empty_positions,
            v.license_plate as kennzeichen,
            m.description as marke
        FROM orders o
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN makes m ON v.make_number = m.make_number
        WHERE o.has_open_positions = true
          AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY o.estimated_inbound_time NULLS LAST
        LIMIT 20
    """)
    
    auftraege = cur.fetchall()
    print(f"\nAnzahl offene Aufträge (letzte 7 Tage): {len(auftraege)}")
    print("\nBeispiel-Aufträge mit Terminen:")
    print("-" * 70)
    
    for a in auftraege[:10]:
        bringen = a['bringen_termin'].strftime('%d.%m. %H:%M') if a['bringen_termin'] else 'KEIN TERMIN'
        abholen = a['abhol_termin'].strftime('%d.%m. %H:%M') if a['abhol_termin'] else 'KEIN TERMIN'
        print(f"  #{a['auftrag_nr']:6} | Betrieb {a['betrieb']} | {a['kennzeichen'] or 'N/A':12} | "
              f"Bringen: {bringen:14} | Abholen: {abholen:14}")
    
    # Statistik: Wie viele haben Termine?
    cur.execute("""
        SELECT 
            COUNT(*) as gesamt,
            COUNT(estimated_inbound_time) as mit_bringen_termin,
            COUNT(estimated_outbound_time) as mit_abhol_termin,
            COUNT(CASE WHEN estimated_inbound_time IS NOT NULL AND estimated_outbound_time IS NOT NULL THEN 1 END) as beide_termine
        FROM orders
        WHERE has_open_positions = true
          AND order_date >= CURRENT_DATE - INTERVAL '7 days'
    """)
    stats = cur.fetchone()
    print(f"\nTermin-Statistik (offene Aufträge):")
    print(f"  Gesamt:           {stats['gesamt']}")
    print(f"  Mit Bringen-Term: {stats['mit_bringen_termin']} ({stats['mit_bringen_termin']*100//max(stats['gesamt'],1)}%)")
    print(f"  Mit Abhol-Term:   {stats['mit_abhol_termin']} ({stats['mit_abhol_termin']*100//max(stats['gesamt'],1)}%)")
    print(f"  Beide Termine:    {stats['beide_termine']} ({stats['beide_termine']*100//max(stats['gesamt'],1)}%)")

    # =========================================================================
    # 2. VORGABE-AW PRO AUFTRAG
    # =========================================================================
    print("\n" + "=" * 70)
    print("2. VORGABE-AW PRO AUFTRAG")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            o.number as auftrag_nr,
            o.estimated_inbound_time as bringen,
            o.estimated_outbound_time as abholen,
            v.license_plate as kennzeichen,
            COUNT(l.order_position) as anzahl_positionen,
            COALESCE(SUM(l.time_units), 0) as summe_aw,
            STRING_AGG(DISTINCT CAST(l.mechanic_no AS TEXT), ', ') as mechaniker
        FROM orders o
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.has_open_positions = true
          AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY o.number, o.estimated_inbound_time, o.estimated_outbound_time, v.license_plate
        HAVING COALESCE(SUM(l.time_units), 0) > 0
        ORDER BY COALESCE(SUM(l.time_units), 0) DESC
        LIMIT 15
    """)
    
    auftraege_aw = cur.fetchall()
    print(f"\nAufträge mit Vorgabe-AW:")
    print("-" * 70)
    
    for a in auftraege_aw:
        bringen = a['bringen'].strftime('%d.%m. %H:%M') if a['bringen'] else 'N/A'
        print(f"  #{a['auftrag_nr']:6} | {a['kennzeichen'] or 'N/A':12} | "
              f"Bringen: {bringen:14} | {a['anzahl_positionen']:2} Pos | "
              f"{float(a['summe_aw']):6.1f} AW | MA: {a['mechaniker'] or '-'}")
    
    # Summe offene AW
    cur.execute("""
        SELECT 
            COALESCE(SUM(l.time_units), 0) as total_aw,
            COUNT(DISTINCT o.number) as anzahl_auftraege
        FROM orders o
        JOIN labours l ON o.number = l.order_number
        WHERE o.has_open_positions = true
          AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
          AND l.time_units > 0
    """)
    summen = cur.fetchone()
    print(f"\n⚡ SUMME OFFENE ARBEIT: {float(summen['total_aw']):.1f} AW in {summen['anzahl_auftraege']} Aufträgen")
    print(f"   = ca. {float(summen['total_aw'])/6:.1f} Stunden Arbeit")

    # =========================================================================
    # 3. TEILE-STATUS PRO AUFTRAG
    # =========================================================================
    print("\n" + "=" * 70)
    print("3. TEILE-STATUS PRO AUFTRAG (aus parts-Tabelle)")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            o.number as auftrag_nr,
            v.license_plate as kennzeichen,
            COUNT(DISTINCT p.part_number) as anzahl_teile,
            COUNT(DISTINCT CASE WHEN ps.stock_level > 0 THEN p.part_number END) as teile_auf_lager,
            SUM(p.amount) as teile_menge,
            SUM(p.sum) as teile_wert
        FROM orders o
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN parts p ON o.number = p.order_number
        LEFT JOIN parts_stock ps ON p.part_number = ps.part_number AND ps.stock_no = 1
        WHERE o.has_open_positions = true
          AND o.order_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY o.number, v.license_plate
        HAVING COUNT(p.part_number) > 0
        ORDER BY COUNT(DISTINCT p.part_number) DESC
        LIMIT 10
    """)
    
    teile_stats = cur.fetchall()
    print(f"\nAufträge mit Teilen:")
    print("-" * 70)
    
    for t in teile_stats:
        auf_lager = t['teile_auf_lager'] or 0
        gesamt = t['anzahl_teile']
        status = "✅" if auf_lager == gesamt else "⚠️"
        print(f"  #{t['auftrag_nr']:6} | {t['kennzeichen'] or 'N/A':12} | "
              f"{auf_lager}/{gesamt} Teile auf Lager {status} | "
              f"Wert: {float(t['teile_wert'] or 0):.2f}€")

    # =========================================================================
    # 4. VERFÜGBARE MECHANIKER (HEUTE)
    # =========================================================================
    print("\n" + "=" * 70)
    print("4. VERFÜGBARE MECHANIKER (HEUTE)")
    print("=" * 70)
    
    # Alle aktiven Mechaniker
    cur.execute("""
        SELECT 
            eh.employee_number,
            eh.name,
            eh.subsidiary,
            eh.mechanic_number,
            eh.leave_date
        FROM employees_history eh
        WHERE eh.is_latest_record = true
          AND eh.employee_number BETWEEN 5000 AND 5999
          AND eh.mechanic_number IS NOT NULL
          AND eh.subsidiary > 0
          AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        ORDER BY eh.subsidiary, eh.name
    """)
    mechaniker = cur.fetchall()
    print(f"\nAlle aktiven Mechaniker: {len(mechaniker)}")
    
    # Heute abwesend
    cur.execute("""
        SELECT 
            ac.employee_number,
            eh.name,
            eh.subsidiary,
            ac.reason,
            ac.type
        FROM absence_calendar ac
        JOIN employees_history eh ON ac.employee_number = eh.employee_number
            AND eh.is_latest_record = true
        WHERE ac.date = CURRENT_DATE
          AND ac.employee_number BETWEEN 5000 AND 5999
    """)
    abwesend = cur.fetchall()
    abwesend_ids = [a['employee_number'] for a in abwesend]
    print(f"Heute abwesend: {len(abwesend)}")
    
    for a in abwesend:
        print(f"  - {a['name']} (Betrieb {a['subsidiary']}): {a['reason'] or a['type']}")
    
    verfuegbar_count = len([m for m in mechaniker if m['employee_number'] not in abwesend_ids])
    print(f"\n👷 VERFÜGBAR HEUTE: {verfuegbar_count} Mechaniker")

    # =========================================================================
    # 5. ARBEITSZEITEN PRO MECHANIKER (MIT FIX!)
    # =========================================================================
    print("\n" + "=" * 70)
    print("5. ARBEITSZEITEN PRO MECHANIKER (FIX: ohne is_latest_record)")
    print("=" * 70)
    
    today_dow = datetime.now().weekday()  # 0=Montag
    
    # FIX: Statt is_latest_record verwenden wir DISTINCT ON mit ORDER BY validity_date DESC
    cur.execute("""
        WITH aktuelle_arbeitszeiten AS (
            SELECT DISTINCT ON (employee_number, dayofweek)
                employee_number,
                dayofweek,
                work_duration,
                worktime_start,
                worktime_end,
                validity_date
            FROM employees_worktimes
            ORDER BY employee_number, dayofweek, validity_date DESC
        ),
        aktive_mechaniker AS (
            SELECT 
                employee_number,
                name,
                subsidiary
            FROM employees_history
            WHERE is_latest_record = true
              AND employee_number BETWEEN 5000 AND 5999
              AND mechanic_number IS NOT NULL
              AND subsidiary > 0
              AND (leave_date IS NULL OR leave_date > CURRENT_DATE)
        )
        SELECT 
            am.employee_number,
            am.name,
            am.subsidiary,
            aw.dayofweek,
            aw.work_duration,
            aw.worktime_start,
            aw.worktime_end
        FROM aktive_mechaniker am
        LEFT JOIN aktuelle_arbeitszeiten aw 
            ON am.employee_number = aw.employee_number
            AND aw.dayofweek = %s
        ORDER BY am.subsidiary, am.name
    """, [today_dow])
    
    arbeitszeiten = cur.fetchall()
    
    total_stunden = 0
    total_stunden_verfuegbar = 0
    print(f"\nArbeitszeiten heute (Tag {today_dow} = {['Mo','Di','Mi','Do','Fr','Sa','So'][today_dow]}):")
    print("-" * 90)
    
    for az in arbeitszeiten:
        ist_abwesend = az['employee_number'] in abwesend_ids
        status = "🔴 ABWESEND" if ist_abwesend else "✅"
        
        if az['work_duration']:
            stunden = float(az['work_duration'])
            total_stunden += stunden
            if not ist_abwesend:
                total_stunden_verfuegbar += stunden
            
            # Arbeitszeit formatieren (ist in Dezimalstunden, z.B. 8.5 = 8:30)
            start_h = int(az['worktime_start'] or 0)
            start_m = int(((az['worktime_start'] or 0) % 1) * 60)
            ende_h = int(az['worktime_end'] or 0)
            ende_m = int(((az['worktime_end'] or 0) % 1) * 60)
            
            print(f"  {az['name']:25} | Betrieb {az['subsidiary']} | "
                  f"{start_h:02d}:{start_m:02d}-{ende_h:02d}:{ende_m:02d} | "
                  f"{stunden:.1f}h | {status}")
        else:
            print(f"  {az['name']:25} | Betrieb {az['subsidiary']} | KEINE DATEN | {status}")
    
    total_aw = total_stunden * 6  # 1 Stunde = 6 AW
    total_aw_verfuegbar = total_stunden_verfuegbar * 6
    
    print(f"\n📊 ARBEITSZEIT ALLE MECHANIKER: {total_stunden:.1f}h = {total_aw:.0f} AW")
    print(f"📊 KAPAZITÄT VERFÜGBAR (ohne Abwesende): {total_stunden_verfuegbar:.1f}h = {total_aw_verfuegbar:.0f} AW")

    # =========================================================================
    # 6. AUSLASTUNGS-BERECHNUNG
    # =========================================================================
    print("\n" + "=" * 70)
    print("6. AUSLASTUNGS-BERECHNUNG")
    print("=" * 70)
    
    offene_aw = float(summen['total_aw'])
    verfuegbare_aw = total_aw_verfuegbar
    
    if verfuegbare_aw > 0:
        auslastung = (offene_aw / verfuegbare_aw) * 100
        print(f"\n  Offene Arbeit (7 Tage):   {offene_aw:8.1f} AW")
        print(f"  Verfügbare Kapazität:     {verfuegbare_aw:8.1f} AW (heute)")
        print(f"  ─────────────────────────────────────")
        
        if auslastung > 100:
            tage_bedarf = offene_aw / verfuegbare_aw
            print(f"  AUSLASTUNG:               {auslastung:8.1f} %")
            print(f"\n  ⚠️  Arbeit für {tage_bedarf:.1f} Tage vorhanden!")
        else:
            print(f"  AUSLASTUNG:               {auslastung:8.1f} %")
            if auslastung > 80:
                print(f"\n  ✅ Gut ausgelastet")
            else:
                print(f"\n  ℹ️  Noch Kapazität frei")
    else:
        print("\n  ⚠️  Keine Arbeitszeiten-Daten verfügbar!")

    # =========================================================================
    # 7. AUFTRÄGE NACH TERMIN (Tagesplanung)
    # =========================================================================
    print("\n" + "=" * 70)
    print("7. AUFTRÄGE FÜR HEUTE (mit Termin)")
    print("=" * 70)
    
    cur.execute("""
        SELECT 
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.estimated_inbound_time as bringen,
            o.estimated_outbound_time as abholen,
            v.license_plate as kennzeichen,
            m.description as marke,
            COALESCE(SUM(l.time_units), 0) as vorgabe_aw,
            o.urgency
        FROM orders o
        LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
        LEFT JOIN makes m ON v.make_number = m.make_number
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.has_open_positions = true
          AND DATE(o.estimated_inbound_time) = CURRENT_DATE
        GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, o.estimated_outbound_time, 
                 v.license_plate, m.description, o.urgency
        ORDER BY o.estimated_inbound_time
    """)
    
    heute_termine = cur.fetchall()
    print(f"\nHeutige Termine: {len(heute_termine)}")
    print("-" * 90)
    
    summe_heute_aw = 0
    for t in heute_termine:
        bringen = t['bringen'].strftime('%H:%M') if t['bringen'] else 'N/A'
        abholen = t['abholen'].strftime('%H:%M') if t['abholen'] else 'N/A'
        aw = float(t['vorgabe_aw'])
        summe_heute_aw += aw
        dringend = "🔴" if t['urgency'] and t['urgency'] >= 4 else ""
        betrieb = {1: 'DEG', 2: 'HYU', 3: 'LAN'}.get(t['betrieb'], '?')
        print(f"  {bringen} #{t['auftrag_nr']:6} | {betrieb} | {t['kennzeichen'] or 'N/A':12} | {t['marke'] or '':12} | "
              f"{aw:5.1f} AW | bis {abholen} {dringend}")
    
    print(f"\n  SUMME HEUTE: {summe_heute_aw:.1f} AW ({summe_heute_aw/6:.1f}h)")
    
    # Auslastung heute
    if total_aw_verfuegbar > 0:
        auslastung_heute = (summe_heute_aw / total_aw_verfuegbar) * 100
        print(f"  AUSLASTUNG HEUTE: {auslastung_heute:.1f}% der verfügbaren Kapazität")

    # =========================================================================
    # 8. KAPAZITÄT PRO BETRIEB
    # =========================================================================
    print("\n" + "=" * 70)
    print("8. KAPAZITÄT PRO BETRIEB (HEUTE)")
    print("=" * 70)
    
    cur.execute("""
        WITH aktuelle_arbeitszeiten AS (
            SELECT DISTINCT ON (employee_number, dayofweek)
                employee_number,
                dayofweek,
                work_duration
            FROM employees_worktimes
            ORDER BY employee_number, dayofweek, validity_date DESC
        ),
        abwesende AS (
            SELECT employee_number
            FROM absence_calendar
            WHERE date = CURRENT_DATE
        )
        SELECT 
            eh.subsidiary,
            COUNT(*) as anzahl_mechaniker,
            COUNT(*) FILTER (WHERE ab.employee_number IS NULL) as anwesend,
            COALESCE(SUM(aw.work_duration) FILTER (WHERE ab.employee_number IS NULL), 0) as stunden,
            COALESCE(SUM(aw.work_duration) FILTER (WHERE ab.employee_number IS NULL), 0) * 6 as aw
        FROM employees_history eh
        LEFT JOIN aktuelle_arbeitszeiten aw 
            ON eh.employee_number = aw.employee_number
            AND aw.dayofweek = %s
        LEFT JOIN abwesende ab ON eh.employee_number = ab.employee_number
        WHERE eh.is_latest_record = true
          AND eh.employee_number BETWEEN 5000 AND 5999
          AND eh.mechanic_number IS NOT NULL
          AND eh.subsidiary > 0
          AND (eh.leave_date IS NULL OR eh.leave_date > CURRENT_DATE)
        GROUP BY eh.subsidiary
        ORDER BY eh.subsidiary
    """, [today_dow])
    
    betriebe = cur.fetchall()
    print(f"\nKapazität nach Betrieb:")
    print("-" * 60)
    
    betrieb_namen = {1: 'Deggendorf (Opel)', 2: 'Hyundai DEG', 3: 'Landau'}
    for b in betriebe:
        name = betrieb_namen.get(b['subsidiary'], f"Betrieb {b['subsidiary']}")
        print(f"  {name:20} | {b['anwesend']}/{b['anzahl_mechaniker']} MA | "
              f"{float(b['stunden']):.1f}h | {float(b['aw']):.0f} AW")

    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 70)


if __name__ == '__main__':
    main()
