# ============================================================================
# PATCH FÜR werkstatt_live_api.py - TAG 101
# ============================================================================
# 
# ÄNDERUNGEN:
# 1. Neue Konstanten für spezielle Aufträge
# 2. Angepasste /stempeluhr Funktion mit echtem Leerlauf (Auftrag 31)
#
# ANWENDUNG:
# 1. Öffne /opt/greiner-portal/api/werkstatt_live_api.py
# 2. Füge nach Zeile 76 (nach ARBEITSZEIT_ENDE) die neuen Konstanten ein
# 3. Ersetze die komplette get_stempeluhr_live() Funktion
# ============================================================================

# ============================================================================
# SCHRITT 1: Nach Zeile 76 einfügen (nach "ARBEITSZEIT_ENDE = time(18, 0)")
# ============================================================================

# =============================================================================
# SPEZIELLE AUFTRÄGE IN LOCOSOFT (TAG 101)
# =============================================================================
# Auftrag 0  = Anwesenheit (Kommen/Gehen des Arbeitstages)
# Auftrag 31 = Leerlauf (Kunde: 3000000 = Greiner GmbH & Co. KG)
#              Mechaniker stempeln hierauf wenn kein produktiver Auftrag da ist
ANWESENHEIT_AUFTRAG = 0
LEERLAUF_AUFTRAG = 31


# ============================================================================
# SCHRITT 2: Die komplette get_stempeluhr_live() Funktion ersetzen
# (Von "@werkstatt_live_bp.route('/stempeluhr'..." bis zum nächsten "@werkstatt_live_bp.route")
# ============================================================================

@werkstatt_live_bp.route('/stempeluhr', methods=['GET'])
def get_stempeluhr_live():
    """
    LIVE Stempeluhr-Übersicht für Mechaniker (TAG 101)
    
    NEU: Nutzt echte Leerlauf-Stempelungen (Auftrag 31) statt berechneter Lücken!
    
    Kategorien:
    - Produktiv: Arbeitet an echtem Auftrag (order_number > 31)
    - Leerlauf: Gestempelt auf Auftrag 31 (echter Leerlauf!)
    - Abwesend: Urlaub/Krank laut absence_calendar
    
    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        subsidiary = request.args.get('subsidiary', type=int)
        
        conn = get_locosoft_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # =====================================================================
        # 1. PRODUKTIVE STEMPELUNGEN (Auftrag > 31, also echte Kundenaufträge)
        # =====================================================================
        produktiv_query = """
            WITH aktuelle_stempelungen AS (
                SELECT DISTINCT ON (t.employee_number)
                    t.employee_number,
                    t.order_number,
                    t.start_time,
                    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as laufzeit_min
                FROM times t
                WHERE t.end_time IS NULL
                  AND t.type = 2
                  AND t.order_number > 31  -- Echte Aufträge, nicht Leerlauf!
                  AND DATE(t.start_time) = CURRENT_DATE
                ORDER BY t.employee_number, t.start_time DESC
            )
            SELECT 
                a.employee_number,
                eh.name as mechaniker,
                eh.subsidiary as betrieb,
                a.order_number,
                a.start_time,
                ROUND(a.laufzeit_min::numeric, 0) as laufzeit_min,
                COALESCE(l.vorgabe_aw, 0) as vorgabe_aw,
                COALESCE(l.vorgabe_aw * 6, 0) as vorgabe_min,
                o.order_taking_employee_no as sb_nr,
                sb.name as sb_name,
                v.license_plate as kennzeichen,
                m.description as marke
            FROM aktuelle_stempelungen a
            LEFT JOIN employees_history eh ON a.employee_number = eh.employee_number 
                AND eh.is_latest_record = true
            LEFT JOIN orders o ON a.order_number = o.number
            LEFT JOIN employees_history sb ON o.order_taking_employee_no = sb.employee_number
                AND sb.is_latest_record = true
            LEFT JOIN vehicles v ON o.vehicle_number = v.internal_number
            LEFT JOIN makes m ON v.make_number = m.make_number
            LEFT JOIN LATERAL (
                SELECT SUM(time_units) as vorgabe_aw
                FROM labours 
                WHERE order_number = a.order_number 
                  AND mechanic_no = a.employee_number
            ) l ON true
        """
        
        if subsidiary:
            produktiv_query += " WHERE eh.subsidiary = %s"
            produktiv_query += " ORDER BY a.start_time"
            cur.execute(produktiv_query, [subsidiary])
        else:
            produktiv_query += " ORDER BY a.start_time"
            cur.execute(produktiv_query)
        
        produktiv = cur.fetchall()
        
        # =====================================================================
        # 2. LEERLAUF-STEMPELUNGEN (Auftrag 31 = echter Leerlauf!)
        # =====================================================================
        leerlauf_query = """
            WITH leerlauf_stempelungen AS (
                SELECT DISTINCT ON (t.employee_number)
                    t.employee_number,
                    t.start_time,
                    EXTRACT(EPOCH FROM (NOW() - t.start_time))/60 as leerlauf_minuten
                FROM times t
                WHERE t.end_time IS NULL
                  AND t.type = 2
                  AND t.order_number = 31  -- Leerlauf-Auftrag!
                  AND DATE(t.start_time) = CURRENT_DATE
                ORDER BY t.employee_number, t.start_time DESC
            )
            SELECT 
                ls.employee_number,
                eh.name,
                eh.subsidiary,
                ls.start_time as leerlauf_seit,
                ROUND(ls.leerlauf_minuten::numeric, 0) as leerlauf_minuten
            FROM leerlauf_stempelungen ls
            JOIN employees_history eh ON ls.employee_number = eh.employee_number
                AND eh.is_latest_record = true
            WHERE eh.leave_date IS NULL
              AND eh.subsidiary > 0
        """
        
        if subsidiary:
            leerlauf_query += " AND eh.subsidiary = %s"
            leerlauf_query += " ORDER BY ls.leerlauf_minuten DESC"
            cur.execute(leerlauf_query, [subsidiary])
        else:
            leerlauf_query += " ORDER BY eh.subsidiary, ls.leerlauf_minuten DESC"
            cur.execute(leerlauf_query)
        
        leerlauf_raw = cur.fetchall()
        
        # Azubis und nicht-produktive MA aus Leerlauf entfernen
        leerlauf = [r for r in leerlauf_raw if r['employee_number'] not in LEERLAUF_AUSNAHMEN]
        
        # Außerhalb der Arbeitszeit = kein Leerlauf anzeigen
        jetzt_zeit = datetime.now().time()
        ist_arbeitszeit = ARBEITSZEIT_START <= jetzt_zeit <= ARBEITSZEIT_ENDE
        
        if not ist_arbeitszeit:
            leerlauf = []
        
        # =====================================================================
        # 3. ABWESENDE MECHANIKER
        # =====================================================================
        abwesend_query = """
            SELECT 
                ac.employee_number,
                eh.name,
                eh.subsidiary,
                ac.reason as grund
            FROM absence_calendar ac
            JOIN employees_history eh ON ac.employee_number = eh.employee_number
                AND eh.is_latest_record = true
            WHERE ac.date = CURRENT_DATE
              AND ac.employee_number BETWEEN 5000 AND 5999
              AND eh.leave_date IS NULL
              AND eh.subsidiary > 0
        """
        
        if subsidiary:
            abwesend_query += " AND eh.subsidiary = %s"
            abwesend_query += " ORDER BY eh.name"
            cur.execute(abwesend_query, [subsidiary])
        else:
            abwesend_query += " ORDER BY eh.subsidiary, eh.name"
            cur.execute(abwesend_query)
        
        abwesend = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # =====================================================================
        # 4. RESPONSE AUFBAUEN
        # =====================================================================
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'ist_arbeitszeit': ist_arbeitszeit,
            'filter': {'subsidiary': subsidiary},
            'info': {
                'leerlauf_auftrag': LEERLAUF_AUFTRAG,
                'anwesenheit_auftrag': ANWESENHEIT_AUFTRAG,
                'hinweis': 'Leerlauf = Mechaniker hat auf Auftrag 31 gestempelt'
            },
            'aktive_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['mechaniker'] or f"MA {r['employee_number']}",
                    'betrieb': r['betrieb'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['betrieb'], '?'),
                    'order_number': r['order_number'],
                    'serviceberater': r['sb_name'] or f"MA {r['sb_nr']}" if r['sb_nr'] else None,
                    'serviceberater_nr': r['sb_nr'],
                    'kennzeichen': r['kennzeichen'],
                    'marke': r['marke'],
                    'start_time': format_datetime(r['start_time']),
                    'start_uhrzeit': r['start_time'].strftime('%H:%M') if r['start_time'] else None,
                    'laufzeit_min': berechne_netto_laufzeit(r['start_time']) if r['start_time'] else 0,
                    'vorgabe_aw': float(r['vorgabe_aw'] or 0),
                    'vorgabe_min': int(r['vorgabe_min'] or 0),
                    'fortschritt_prozent': int(
                        (berechne_netto_laufzeit(r['start_time']) / (r['vorgabe_aw'] * 6) * 100)
                        if r['start_time'] and r['vorgabe_aw'] and r['vorgabe_aw'] > 0 
                        else 0
                    ),
                    'status': 'produktiv'
                } for r in produktiv
            ],
            'leerlauf_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'leerlauf_minuten': int(r['leerlauf_minuten']) if r['leerlauf_minuten'] else 0,
                    'leerlauf_seit': r['leerlauf_seit'].strftime('%H:%M') if r.get('leerlauf_seit') else None,
                    'status': 'leerlauf',
                    'ist_echt': True  # TAG 101: Echter gestempelter Leerlauf!
                } for r in leerlauf
            ],
            'abwesend_mechaniker': [
                {
                    'employee_number': r['employee_number'],
                    'name': r['name'] or f"MA {r['employee_number']}",
                    'betrieb': r['subsidiary'],
                    'betrieb_name': BETRIEB_NAMEN.get(r['subsidiary'], '?'),
                    'grund': r['grund'],
                    'status': 'abwesend'
                } for r in abwesend
            ],
            'summary': {
                'produktiv': len(produktiv),
                'leerlauf': len(leerlauf),
                'abwesend': len(abwesend),
                'gesamt': len(produktiv) + len(leerlauf) + len(abwesend)
            }
        })
        
    except Exception as e:
        logger.exception("Fehler beim Laden der Stempeluhr")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ENDE DES PATCHES
# ============================================================================
