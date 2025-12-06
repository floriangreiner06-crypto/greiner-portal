#!/usr/bin/env python3
"""
KAPAZITÄTS-FORECAST API ENDPOINT
=================================
TAG 94 - Der MEGA-Endpoint für Werkstattplanung

Features:
1. Tagesweise Vorschau (nächste 10 Arbeitstage)
2. Berücksichtigt geplante Abwesenheiten
3. Unverplante Aufträge (ohne Termin) als Warnung
4. Überfällige Aufträge (Termin in Vergangenheit)
5. Teile-Status aus Locosoft UND Servicebox-Bestellungen
6. Auslastungs-Prognose pro Tag

Endpoint: GET /api/werkstatt/live/forecast
"""

# Dieser Code wird an werkstatt_live_api.py angehängt

FORECAST_ENDPOINT_CODE = '''

@werkstatt_live_bp.route('/forecast', methods=['GET'])
def get_kapazitaets_forecast():
    """
    MEGA Kapazitäts-Forecast: Vorausschau auf die nächsten Arbeitstage
    
    Features:
    - Tagesweise Kapazität vs. geplante Arbeit
    - Berücksichtigt geplante Abwesenheiten (Urlaub etc.)
    - Warnung bei unverplanten Aufträgen (ohne Termin)
    - Warnung bei überfälligen Aufträgen
    - Teile-Status: Locosoft Lager + Servicebox Bestellungen
    
    Query-Parameter:
    - tage: Anzahl Tage Vorschau (default: 10)
    - subsidiary: Filter nach Betrieb (1, 3)
    """
    try:
        import sqlite3
        from datetime import timedelta
        
        tage_vorschau = request.args.get('tage', 10, type=int)
        subsidiary = request.args.get('subsidiary', type=int)
        
        conn_loco = get_locosoft_connection()
        cur_loco = conn_loco.cursor(cursor_factory=RealDictCursor)
        
        # SQLite für Servicebox
        sqlite_path = '/opt/greiner-portal/data/greiner_controlling.db'
        conn_sqlite = sqlite3.connect(sqlite_path)
        conn_sqlite.row_factory = sqlite3.Row
        cur_sqlite = conn_sqlite.cursor()
        
        heute = datetime.now().date()
        
        # =====================================================================
        # 1. ARBEITSTAGE ERMITTELN (ohne Wochenende, mit Feiertagen)
        # =====================================================================
        
        # Feiertage aus Locosoft holen
        cur_loco.execute("""
            SELECT date FROM year_calendar 
            WHERE is_public_holid = true 
              AND date >= CURRENT_DATE 
              AND date <= CURRENT_DATE + INTERVAL '%s days'
        """, [tage_vorschau + 14])  # Extra Puffer für Wochenenden
        
        feiertage = set(row['date'] for row in cur_loco.fetchall())
        
        # Arbeitstage berechnen
        arbeitstage = []
        check_date = heute
        while len(arbeitstage) < tage_vorschau:
            # Wochenende überspringen (5=Sa, 6=So)
            if check_date.weekday() < 5 and check_date not in feiertage:
                arbeitstage.append(check_date)
            check_date += timedelta(days=1)
        
        # =====================================================================
        # 2. KAPAZITÄT PRO TAG (mit geplanten Abwesenheiten)
        # =====================================================================
        
        tages_forecast = []
        
        for tag in arbeitstage:
            dow = tag.weekday()  # 0=Mo, 4=Fr
            
            # Mechaniker mit Arbeitszeiten für diesen Wochentag
            kapa_query = """
                WITH aktuelle_arbeitszeiten AS (
                    SELECT DISTINCT ON (employee_number, dayofweek)
                        employee_number,
                        dayofweek,
                        work_duration
                    FROM employees_worktimes
                    ORDER BY employee_number, dayofweek, validity_date DESC
                ),
                abwesende_tag AS (
                    SELECT employee_number, reason, type
                    FROM absence_calendar
                    WHERE date = %s
                )
                SELECT 
                    eh.employee_number,
                    eh.name,
                    eh.subsidiary,
                    COALESCE(aw.work_duration, 8) as stunden,
                    ab.reason as abwesenheit_grund,
                    CASE WHEN ab.employee_number IS NOT NULL THEN true ELSE false END as ist_abwesend
                FROM employees_history eh
                LEFT JOIN aktuelle_arbeitszeiten aw 
                    ON eh.employee_number = aw.employee_number
                    AND aw.dayofweek = %s
                LEFT JOIN abwesende_tag ab ON eh.employee_number = ab.employee_number
                WHERE eh.is_latest_record = true
                  AND eh.employee_number BETWEEN 5000 AND 5999
                  AND eh.mechanic_number IS NOT NULL
                  AND eh.subsidiary > 0
                  AND (eh.leave_date IS NULL OR eh.leave_date > %s)
            """
            
            kapa_params = [tag, dow, tag]
            if subsidiary:
                kapa_query += " AND eh.subsidiary = %s"
                kapa_params.append(subsidiary)
            
            cur_loco.execute(kapa_query, kapa_params)
            mechaniker_tag = cur_loco.fetchall()
            
            anwesend = [m for m in mechaniker_tag if not m['ist_abwesend']]
            abwesend = [m for m in mechaniker_tag if m['ist_abwesend']]
            
            kapazitaet_h = sum(float(m['stunden']) for m in anwesend)
            kapazitaet_aw = kapazitaet_h * 6
            
            # Geplante Aufträge für diesen Tag
            auftraege_query = """
                SELECT 
                    o.number as auftrag_nr,
                    o.subsidiary as betrieb,
                    o.estimated_inbound_time as bringen,
                    o.estimated_outbound_time as abholen,
                    o.urgency,
                    v.license_plate as kennzeichen,
                    COALESCE(SUM(l.time_units), 0) as vorgabe_aw
                FROM orders o
                LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
                LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
                WHERE o.has_open_positions = true
                  AND DATE(o.estimated_inbound_time) = %s
            """
            
            auftraege_params = [tag]
            if subsidiary:
                auftraege_query += " AND o.subsidiary = %s"
                auftraege_params.append(subsidiary)
            
            auftraege_query += """
                GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, 
                         o.estimated_outbound_time, o.urgency, v.license_plate
            """
            
            cur_loco.execute(auftraege_query, auftraege_params)
            auftraege_tag = cur_loco.fetchall()
            
            geplant_aw = sum(float(a['vorgabe_aw']) for a in auftraege_tag)
            
            # Auslastung berechnen
            if kapazitaet_aw > 0:
                auslastung = (geplant_aw / kapazitaet_aw) * 100
            else:
                auslastung = 0
            
            # Status bestimmen
            if auslastung > 120:
                status = 'kritisch'
                status_icon = '🔴'
            elif auslastung > 90:
                status = 'hoch'
                status_icon = '🟠'
            elif auslastung > 50:
                status = 'normal'
                status_icon = '🟢'
            else:
                status = 'niedrig'
                status_icon = '🔵'
            
            tages_forecast.append({
                'datum': str(tag),
                'datum_formatiert': tag.strftime('%a %d.%m.'),
                'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][dow],
                'ist_heute': tag == heute,
                'mechaniker_anwesend': len(anwesend),
                'mechaniker_abwesend': len(abwesend),
                'abwesende': [{'name': m['name'], 'grund': m['abwesenheit_grund']} for m in abwesend],
                'kapazitaet_h': kapazitaet_h,
                'kapazitaet_aw': kapazitaet_aw,
                'geplant_aw': geplant_aw,
                'geplant_anzahl': len(auftraege_tag),
                'auslastung_prozent': round(auslastung, 1),
                'freie_kapazitaet_aw': max(0, kapazitaet_aw - geplant_aw),
                'status': status,
                'status_icon': status_icon
            })
        
        # =====================================================================
        # 3. UNVERPLANTE AUFTRÄGE (ohne Bringen-Termin)
        # =====================================================================
        
        unverplant_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.order_date,
                o.urgency,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name, 'Unbekannt') as kunde,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw,
                COUNT(DISTINCT l.order_position) as anzahl_positionen
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND o.estimated_inbound_time IS NULL
              AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        if subsidiary:
            unverplant_query += " AND o.subsidiary = %s"
        
        unverplant_query += """
            GROUP BY o.number, o.subsidiary, o.order_date, o.urgency, 
                     v.license_plate, m.description, cs.family_name
            HAVING COALESCE(SUM(l.time_units), 0) > 0
            ORDER BY o.urgency DESC NULLS LAST, o.order_date ASC
        """
        
        if subsidiary:
            cur_loco.execute(unverplant_query, [subsidiary])
        else:
            cur_loco.execute(unverplant_query)
        
        unverplante = cur_loco.fetchall()
        
        unverplante_auftraege = [{
            'auftrag_nr': a['auftrag_nr'],
            'betrieb': a['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
            'kennzeichen': a['kennzeichen'],
            'marke': a['marke'],
            'kunde': a['kunde'],
            'vorgabe_aw': float(a['vorgabe_aw']),
            'anzahl_positionen': a['anzahl_positionen'],
            'auftragsdatum': a['order_date'].strftime('%d.%m.%Y') if a['order_date'] else None,
            'dringend': a['urgency'] and a['urgency'] >= 4
        } for a in unverplante]
        
        summe_unverplant_aw = sum(a['vorgabe_aw'] for a in unverplante_auftraege)
        
        # =====================================================================
        # 4. ÜBERFÄLLIGE AUFTRÄGE (Termin in Vergangenheit)
        # =====================================================================
        
        ueberfaellig_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.estimated_inbound_time as bringen,
                o.estimated_outbound_time as abholen,
                o.urgency,
                v.license_plate as kennzeichen,
                m.description as marke,
                COALESCE(cs.family_name, 'Unbekannt') as kunde,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN customers_suppliers cs ON o.order_customer = cs.customer_number
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND DATE(o.estimated_inbound_time) < CURRENT_DATE
        """
        
        if subsidiary:
            ueberfaellig_query += " AND o.subsidiary = %s"
        
        ueberfaellig_query += """
            GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, 
                     o.estimated_outbound_time, o.urgency, v.license_plate, 
                     m.description, cs.family_name
            ORDER BY o.estimated_inbound_time ASC
        """
        
        if subsidiary:
            cur_loco.execute(ueberfaellig_query, [subsidiary])
        else:
            cur_loco.execute(ueberfaellig_query)
        
        ueberfaellige = cur_loco.fetchall()
        
        ueberfaellige_auftraege = [{
            'auftrag_nr': a['auftrag_nr'],
            'betrieb': a['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(a['betrieb'], '?'),
            'kennzeichen': a['kennzeichen'],
            'marke': a['marke'],
            'kunde': a['kunde'],
            'vorgabe_aw': float(a['vorgabe_aw'] or 0),
            'bringen': a['bringen'].strftime('%d.%m.%Y %H:%M') if a['bringen'] else None,
            'tage_ueberfaellig': (heute - a['bringen'].date()).days if a['bringen'] else 0,
            'dringend': a['urgency'] and a['urgency'] >= 4
        } for a in ueberfaellige]
        
        # =====================================================================
        # 5. TEILE-STATUS (Locosoft Lager + Servicebox Bestellungen)
        # =====================================================================
        
        # Aufträge mit fehlenden Teilen aus Locosoft
        teile_query = """
            SELECT 
                o.number as auftrag_nr,
                o.subsidiary as betrieb,
                o.estimated_inbound_time as bringen,
                v.license_plate as kennzeichen,
                COUNT(DISTINCT p.part_number) as teile_gesamt,
                COUNT(DISTINCT CASE WHEN COALESCE(ps.stock_level, 0) > 0 THEN p.part_number END) as teile_auf_lager,
                COALESCE(SUM(l.time_units), 0) as vorgabe_aw
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN parts p ON o.number = p.order_number
            LEFT JOIN parts_stock ps ON p.part_number = ps.part_number AND ps.stock_no = 1
            LEFT JOIN labours l ON o.number = l.order_number AND l.time_units > 0
            WHERE o.has_open_positions = true
              AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        if subsidiary:
            teile_query += " AND o.subsidiary = %s"
        
        teile_query += """
            GROUP BY o.number, o.subsidiary, o.estimated_inbound_time, v.license_plate
            HAVING COUNT(DISTINCT p.part_number) > 0
               AND COUNT(DISTINCT CASE WHEN COALESCE(ps.stock_level, 0) > 0 THEN p.part_number END) 
                   < COUNT(DISTINCT p.part_number)
            ORDER BY o.estimated_inbound_time NULLS LAST
        """
        
        if subsidiary:
            cur_loco.execute(teile_query, [subsidiary])
        else:
            cur_loco.execute(teile_query)
        
        teile_fehlen = cur_loco.fetchall()
        
        auftraege_teile_fehlen = [{
            'auftrag_nr': t['auftrag_nr'],
            'betrieb': t['betrieb'],
            'betrieb_name': BETRIEB_NAMEN.get(t['betrieb'], '?'),
            'kennzeichen': t['kennzeichen'],
            'vorgabe_aw': float(t['vorgabe_aw'] or 0),
            'teile_auf_lager': t['teile_auf_lager'],
            'teile_gesamt': t['teile_gesamt'],
            'teile_fehlen': t['teile_gesamt'] - t['teile_auf_lager'],
            'bringen': t['bringen'].strftime('%d.%m.') if t['bringen'] else 'Kein Termin'
        } for t in teile_fehlen]
        
        # Offene Servicebox-Bestellungen (noch nicht zugebucht)
        cur_sqlite.execute("""
            SELECT 
                b.bestellnummer,
                b.bestelldatum,
                b.lokale_nr,
                b.match_kunde_name as kunde,
                COUNT(p.id) as anzahl_positionen,
                SUM(p.summe_inkl_mwst) as gesamtwert,
                (SELECT COUNT(*) FROM teile_lieferscheine tl 
                 WHERE tl.servicebox_bestellnr = b.bestellnummer 
                   AND tl.locosoft_zugebucht = 1) as zugebucht_count,
                (SELECT COUNT(*) FROM teile_lieferscheine tl 
                 WHERE tl.servicebox_bestellnr = b.bestellnummer) as lieferschein_count
            FROM stellantis_bestellungen b
            LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
            WHERE b.bestelldatum >= date('now', '-30 days')
            GROUP BY b.id
            HAVING zugebucht_count < anzahl_positionen OR lieferschein_count = 0
            ORDER BY b.bestelldatum DESC
            LIMIT 20
        """)
        
        offene_bestellungen_raw = cur_sqlite.fetchall()
        
        offene_servicebox = [{
            'bestellnummer': b['bestellnummer'],
            'bestelldatum': b['bestelldatum'],
            'lokale_nr': b['lokale_nr'],
            'kunde': b['kunde'],
            'anzahl_positionen': b['anzahl_positionen'],
            'gesamtwert': round(float(b['gesamtwert'] or 0), 2),
            'status': 'bestellt' if b['lieferschein_count'] == 0 else 'teilweise_geliefert',
            'zugebucht': b['zugebucht_count'] or 0,
            'geliefert': b['lieferschein_count'] or 0
        } for b in offene_bestellungen_raw]
        
        # =====================================================================
        # 6. ZUSAMMENFASSUNG & WARNUNGEN
        # =====================================================================
        
        warnungen = []
        
        if len(unverplante_auftraege) > 0:
            warnungen.append({
                'typ': 'unverplant',
                'icon': '📋',
                'text': f"{len(unverplante_auftraege)} Aufträge ohne Termin ({summe_unverplant_aw:.0f} AW)",
                'severity': 'warning'
            })
        
        if len(ueberfaellige_auftraege) > 0:
            warnungen.append({
                'typ': 'ueberfaellig',
                'icon': '⏰',
                'text': f"{len(ueberfaellige_auftraege)} überfällige Aufträge",
                'severity': 'danger'
            })
        
        if len(auftraege_teile_fehlen) > 0:
            warnungen.append({
                'typ': 'teile_fehlen',
                'icon': '🔧',
                'text': f"{len(auftraege_teile_fehlen)} Aufträge warten auf Teile",
                'severity': 'warning'
            })
        
        if len(offene_servicebox) > 0:
            warnungen.append({
                'typ': 'servicebox_offen',
                'icon': '📦',
                'text': f"{len(offene_servicebox)} offene Servicebox-Bestellungen",
                'severity': 'info'
            })
        
        # Tage mit kritischer Auslastung
        kritische_tage = [t for t in tages_forecast if t['status'] == 'kritisch']
        if kritische_tage:
            warnungen.append({
                'typ': 'ueberbucht',
                'icon': '🔴',
                'text': f"{len(kritische_tage)} Tage überbucht (>120%)",
                'severity': 'danger'
            })
        
        # Gesamtkapazität nächste Woche
        kapazitaet_woche = sum(t['kapazitaet_aw'] for t in tages_forecast[:5])
        geplant_woche = sum(t['geplant_aw'] for t in tages_forecast[:5])
        
        cur_loco.close()
        conn_loco.close()
        cur_sqlite.close()
        conn_sqlite.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'datum': str(heute),
            'filter': {
                'subsidiary': subsidiary,
                'tage_vorschau': tage_vorschau
            },
            
            # Tages-Forecast
            'forecast': tages_forecast,
            
            # Warnungen
            'warnungen': warnungen,
            'anzahl_warnungen': len(warnungen),
            
            # Unverplante Aufträge
            'unverplant': {
                'anzahl': len(unverplante_auftraege),
                'summe_aw': round(summe_unverplant_aw, 1),
                'auftraege': unverplante_auftraege[:15]  # Max 15
            },
            
            # Überfällige Aufträge
            'ueberfaellig': {
                'anzahl': len(ueberfaellige_auftraege),
                'auftraege': ueberfaellige_auftraege[:10]  # Max 10
            },
            
            # Teile-Status
            'teile': {
                'auftraege_warten_auf_teile': len(auftraege_teile_fehlen),
                'auftraege': auftraege_teile_fehlen[:10],  # Max 10
                'offene_servicebox_bestellungen': len(offene_servicebox),
                'servicebox': offene_servicebox[:10]  # Max 10
            },
            
            # Wochen-Zusammenfassung
            'woche': {
                'kapazitaet_aw': kapazitaet_woche,
                'geplant_aw': geplant_woche,
                'auslastung_prozent': round((geplant_woche / kapazitaet_woche * 100) if kapazitaet_woche > 0 else 0, 1),
                'freie_kapazitaet_aw': kapazitaet_woche - geplant_woche
            }
        })
        
    except Exception as e:
        logger.exception("Fehler bei Kapazitäts-Forecast")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''

print("Forecast-Endpoint Code generiert!")
print("Muss an werkstatt_live_api.py angehängt werden.")
