#!/usr/bin/env python3
"""
AVG-Verzögerungsgründe gegen Locosoft matchen
==============================================
Prüft ob Aufträge mit AVG-Gründen bereits:
- Abgerechnet sind (invoices)
- Termine bereits vorbei sind (estimated_inbound_time < heute)

TAG 200
"""

import os
import sys
from datetime import datetime, date

sys.path.insert(0, '/opt/greiner-portal')

from api.db_utils import locosoft_session
from psycopg2.extras import RealDictCursor

print("=" * 80)
print("AVG-VERZÖGERUNGSGRÜNDE GEGEN LOCOSOFT MATCHEN")
print("=" * 80)
print(f"Zeitpunkt: {datetime.now()}")
print()

heute = date.today()

with locosoft_session() as conn:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # =============================================================================
    # 1. HOLE ALLE AVG-GRÜNDE
    # =============================================================================
    
    print("=" * 80)
    print("1. AVG-VERZÖGERUNGSGRÜNDE")
    print("=" * 80)
    print()
    
    avg_query = """
        SELECT
            o.number as auftrag_nr,
            o.subsidiary as betrieb,
            o.clearing_delay_type as avg_code,
            cdt.description as avg_text,
            o.estimated_inbound_time as bringen_termin,
            o.estimated_outbound_time as abhol_termin,
            o.order_date,
            COALESCE(SUM(l.time_units), 0) as vorgabe_aw
        FROM orders o
        LEFT JOIN clearing_delay_types cdt ON o.clearing_delay_type = cdt.type
        LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
        WHERE o.has_open_positions = true
          AND o.clearing_delay_type IS NOT NULL
          AND o.clearing_delay_type != ''
        GROUP BY o.number, o.subsidiary, o.clearing_delay_type, cdt.description,
                 o.estimated_inbound_time, o.estimated_outbound_time, o.order_date
        ORDER BY o.clearing_delay_type, o.number
    """
    
    cur.execute(avg_query)
    avg_auftraege = cur.fetchall()
    
    print(f"✅ {len(avg_auftraege)} Aufträge mit AVG-Gründen gefunden")
    print()
    
    # =============================================================================
    # 2. PRÜFE ABRECHNUNGS-STATUS
    # =============================================================================
    
    print("=" * 80)
    print("2. ABRECHNUNGS-STATUS PRÜFEN")
    print("=" * 80)
    print()
    
    auftrag_nrs = [a['auftrag_nr'] for a in avg_auftraege]
    
    # Prüfe ob Aufträge bereits abgerechnet sind
    abgerechnet_query = """
        SELECT DISTINCT
            i.order_number,
            i.invoice_number,
            i.invoice_date,
            i.invoice_type,
            i.is_canceled,
            COUNT(DISTINCT l.order_number) as fakturierte_aw_count,
            COALESCE(SUM(l.time_units), 0) as fakturierte_aw
        FROM invoices i
        LEFT JOIN labours l ON i.order_number = l.order_number AND l.is_invoiced = true
        WHERE i.order_number = ANY(%s)
          AND i.is_canceled = false
        GROUP BY i.order_number, i.invoice_number, i.invoice_date, i.invoice_type, i.is_canceled
    """
    
    cur.execute(abgerechnet_query, (auftrag_nrs,))
    abgerechnet_raw = cur.fetchall()
    
    abgerechnet_dict = {}
    for r in abgerechnet_raw:
        auftrag_nr = r['order_number']
        if auftrag_nr not in abgerechnet_dict:
            abgerechnet_dict[auftrag_nr] = {
                'invoice_number': r['invoice_number'],
                'invoice_date': r['invoice_date'],
                'invoice_type': r['invoice_type'],
                'fakturierte_aw': float(r['fakturierte_aw'] or 0)
            }
    
    print(f"✅ {len(abgerechnet_dict)} Aufträge bereits abgerechnet")
    print()
    
    # =============================================================================
    # 3. PRÜFE TERMIN-STATUS
    # =============================================================================
    
    print("=" * 80)
    print("3. TERMIN-STATUS PRÜFEN")
    print("=" * 80)
    print()
    
    termin_vorbei = []
    termin_heute = []
    termin_zukunft = []
    kein_termin = []
    
    for a in avg_auftraege:
        bringen = a['bringen_termin']
        if bringen:
            bringen_date = bringen.date() if hasattr(bringen, 'date') else bringen
            if bringen_date < heute:
                termin_vorbei.append(a['auftrag_nr'])
            elif bringen_date == heute:
                termin_heute.append(a['auftrag_nr'])
            else:
                termin_zukunft.append(a['auftrag_nr'])
        else:
            kein_termin.append(a['auftrag_nr'])
    
    print(f"📅 Termine bereits vorbei: {len(termin_vorbei)}")
    print(f"📅 Termine heute: {len(termin_heute)}")
    print(f"📅 Termine in Zukunft: {len(termin_zukunft)}")
    print(f"📅 Kein Termin: {len(kein_termin)}")
    print()
    
    # =============================================================================
    # 4. ANALYSE NACH AVG-CODE
    # =============================================================================
    
    print("=" * 80)
    print("4. ANALYSE NACH AVG-CODE")
    print("=" * 80)
    print()
    
    # Gruppiere nach AVG-Code
    avg_gruppen = {}
    for a in avg_auftraege:
        code = a['avg_code']
        auftrag_nr = a['auftrag_nr']
        
        if code not in avg_gruppen:
            avg_gruppen[code] = {
                'text': a['avg_text'] or 'Unbekannt',
                'auftraege': [],
                'anzahl': 0,
                'summe_aw': 0,
                'abgerechnet': 0,
                'termin_vorbei': 0,
                'termin_heute': 0,
                'termin_zukunft': 0,
                'kein_termin': 0
            }
        
        avg_gruppen[code]['auftraege'].append(auftrag_nr)
        avg_gruppen[code]['anzahl'] += 1
        avg_gruppen[code]['summe_aw'] += float(a['vorgabe_aw'] or 0)
        
        # Status prüfen
        if auftrag_nr in abgerechnet_dict:
            avg_gruppen[code]['abgerechnet'] += 1
        
        if auftrag_nr in termin_vorbei:
            avg_gruppen[code]['termin_vorbei'] += 1
        elif auftrag_nr in termin_heute:
            avg_gruppen[code]['termin_heute'] += 1
        elif auftrag_nr in termin_zukunft:
            avg_gruppen[code]['termin_zukunft'] += 1
        else:
            avg_gruppen[code]['kein_termin'] += 1
    
    # Ausgabe
    print(f"{'Code':<6} {'Beschreibung':<40} {'Gesamt':<8} {'Abgerechnet':<12} {'Termin vorbei':<14} {'Termin heute':<12} {'Termin Zukunft':<14} {'Kein Termin':<12}")
    print("-" * 120)
    
    for code in sorted(avg_gruppen.keys()):
        g = avg_gruppen[code]
        abg_pct = (g['abgerechnet'] / g['anzahl'] * 100) if g['anzahl'] > 0 else 0
        termin_vorbei_pct = (g['termin_vorbei'] / g['anzahl'] * 100) if g['anzahl'] > 0 else 0
        
        print(f"{code:<6} {g['text'][:38]:<40} {g['anzahl']:<8} "
              f"{g['abgerechnet']} ({abg_pct:.1f}%){'':<6} "
              f"{g['termin_vorbei']} ({termin_vorbei_pct:.1f}%){'':<6} "
              f"{g['termin_heute']:<12} "
              f"{g['termin_zukunft']:<14} "
              f"{g['kein_termin']:<12}")
    
    print()
    
    # =============================================================================
    # 5. DETAILLIERTE ANALYSE: "S - Termin bereits vereinbart"
    # =============================================================================
    
    print("=" * 80)
    print("5. DETAILLIERTE ANALYSE: 'S - Termin bereits vereinbart'")
    print("=" * 80)
    print()
    
    s_auftraege = [a for a in avg_auftraege if a['avg_code'] == 'S']
    print(f"📊 Gesamt: {len(s_auftraege)} Aufträge")
    
    s_abgerechnet = [a for a in s_auftraege if a['auftrag_nr'] in abgerechnet_dict]
    s_termin_vorbei = [a for a in s_auftraege if a['auftrag_nr'] in termin_vorbei]
    s_beides = [a for a in s_auftraege if a['auftrag_nr'] in abgerechnet_dict and a['auftrag_nr'] in termin_vorbei]
    
    print(f"   ✅ Abgerechnet: {len(s_abgerechnet)} ({len(s_abgerechnet)/len(s_auftraege)*100:.1f}%)")
    print(f"   📅 Termin vorbei: {len(s_termin_vorbei)} ({len(s_termin_vorbei)/len(s_auftraege)*100:.1f}%)")
    print(f"   🔄 Beides (abgerechnet + Termin vorbei): {len(s_beides)} ({len(s_beides)/len(s_auftraege)*100:.1f}%)")
    print()
    
    # Beispiel-Aufträge
    print("   📋 Beispiel-Aufträge (Termin vorbei, aber nicht abgerechnet):")
    beispiel = [a for a in s_auftraege if a['auftrag_nr'] in termin_vorbei and a['auftrag_nr'] not in abgerechnet_dict][:10]
    for a in beispiel:
        bringen = a['bringen_termin']
        tage_vorbei = (heute - bringen.date()).days if bringen else 0
        print(f"      #{a['auftrag_nr']:6} | Termin: {bringen.strftime('%d.%m.%Y') if bringen else 'N/A':12} | "
              f"{tage_vorbei:3} Tage vorbei | {float(a['vorgabe_aw']):6.1f} AW")
    print()
    
    # =============================================================================
    # 6. DETAILLIERTE ANALYSE: "G - zur Fakturierung Garantie/ Kasse"
    # =============================================================================
    
    print("=" * 80)
    print("6. DETAILLIERTE ANALYSE: 'G - zur Fakturierung Garantie/ Kasse'")
    print("=" * 80)
    print()
    
    g_auftraege = [a for a in avg_auftraege if a['avg_code'] == 'G']
    print(f"📊 Gesamt: {len(g_auftraege)} Aufträge")
    
    g_abgerechnet = [a for a in g_auftraege if a['auftrag_nr'] in abgerechnet_dict]
    g_nicht_abgerechnet = [a for a in g_auftraege if a['auftrag_nr'] not in abgerechnet_dict]
    
    print(f"   ✅ Abgerechnet: {len(g_abgerechnet)} ({len(g_abgerechnet)/len(g_auftraege)*100:.1f}%)")
    print(f"   ⚠️  Nicht abgerechnet: {len(g_nicht_abgerechnet)} ({len(g_nicht_abgerechnet)/len(g_auftraege)*100:.1f}%)")
    print()
    
    if g_abgerechnet:
        print("   📋 Abgerechnete Aufträge:")
        for a in g_abgerechnet[:10]:
            inv = abgerechnet_dict[a['auftrag_nr']]
            print(f"      #{a['auftrag_nr']:6} | Rechnung: {inv['invoice_number']:10} | "
                  f"Datum: {inv['invoice_date'].strftime('%d.%m.%Y') if inv['invoice_date'] else 'N/A':12} | "
                  f"{float(a['vorgabe_aw']):6.1f} AW")
        print()
    
    if g_nicht_abgerechnet:
        print("   ⚠️  Nicht abgerechnete Aufträge (sollten abgerechnet sein!):")
        for a in g_nicht_abgerechnet[:10]:
            print(f"      #{a['auftrag_nr']:6} | Auftragsdatum: {a['order_date'].strftime('%d.%m.%Y') if a['order_date'] else 'N/A':12} | "
                  f"{float(a['vorgabe_aw']):6.1f} AW")
        print()
    
    # =============================================================================
    # 7. ZUSAMMENFASSUNG
    # =============================================================================
    
    print("=" * 80)
    print("7. ZUSAMMENFASSUNG")
    print("=" * 80)
    print()
    
    gesamt_abgerechnet = len(abgerechnet_dict)
    gesamt_termin_vorbei = len(termin_vorbei)
    gesamt_beides = len([a for a in avg_auftraege if a['auftrag_nr'] in abgerechnet_dict and a['auftrag_nr'] in termin_vorbei])
    
    print(f"📊 Gesamt AVG-Aufträge: {len(avg_auftraege)}")
    print(f"   ✅ Abgerechnet: {gesamt_abgerechnet} ({gesamt_abgerechnet/len(avg_auftraege)*100:.1f}%)")
    print(f"   📅 Termin vorbei: {gesamt_termin_vorbei} ({gesamt_termin_vorbei/len(avg_auftraege)*100:.1f}%)")
    print(f"   🔄 Beides: {gesamt_beides} ({gesamt_beides/len(avg_auftraege)*100:.1f}%)")
    print()
    
    print("💡 EMPFEHLUNGEN:")
    print()
    
    # S - Termin bereits vereinbart
    s_problem = len([a for a in s_auftraege if a['auftrag_nr'] in termin_vorbei and a['auftrag_nr'] not in abgerechnet_dict])
    if s_problem > 0:
        print(f"   ⚠️  '{avg_gruppen['S']['text']}': {s_problem} Aufträge haben Termin vorbei, sind aber nicht abgerechnet")
        print(f"      → Diese sollten abgerechnet oder AVG-Grund aktualisiert werden")
        print()
    
    # G - zur Fakturierung
    if len(g_nicht_abgerechnet) > 0:
        print(f"   ⚠️  '{avg_gruppen['G']['text']}': {len(g_nicht_abgerechnet)} Aufträge sind noch nicht abgerechnet")
        print(f"      → Diese sollten abgerechnet werden oder AVG-Grund ist falsch")
        print()
    
    print("=" * 80)
    print("ANALYSE ABGESCHLOSSEN")
    print("=" * 80)
