#!/usr/bin/env python3
"""
Refaktoriert werkstatt_live_api.py um WerkstattData zu nutzen.
TAG 150+151: Automatisches Refactoring Script
"""
import re


def refactor_nachkalkulation(content):
    """Ersetzt get_nachkalkulation() durch WerkstattData-Version (TAG 151)"""
    new_code = '''@werkstatt_live_bp.route('/nachkalkulation', methods=['GET'])
def get_nachkalkulation():
    """
    Auftrags-Nachkalkulation: Vergleich Vorgabe vs. Gestempelt vs. Verrechnet

    TAG 151: Refaktoriert - nutzt WerkstattData.get_nachkalkulation()
    Vorher: 297 LOC | Nachher: 35 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    - typ: alle|extern|intern
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')
        typ_filter = request.args.get('typ', 'alle')

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_nachkalkulation(datum=datum, betrieb=subsidiary, typ=typ_filter)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Nachkalkulation")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/auftrag/<int:auftrag_nr>', methods=['GET'])'''

    pattern = r"@werkstatt_live_bp\.route\('/nachkalkulation', methods=\['GET'\]\)\ndef get_nachkalkulation\(\):.*?@werkstatt_live_bp\.route\('/auftrag/<int:auftrag_nr>', methods=\['GET'\]\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_tagesbericht(content):
    """Ersetzt get_tagesbericht() durch WerkstattData-Version"""
    new_code = '''@werkstatt_live_bp.route('/tagesbericht', methods=['GET'])
def get_tagesbericht():
    """
    Tagesbericht zur Kontrolle: Stempelungen, Zuweisungen, Ueberschreitungen

    TAG 150: Refaktoriert - nutzt WerkstattData.get_tagesbericht()
    Vorher: 220 LOC | Nachher: 35 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)
        datum_str = request.args.get('datum')

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_tagesbericht(datum=datum, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler beim Erstellen des Tagesberichts")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/nachkalkulation', methods=['GET'])'''

    pattern = r"@werkstatt_live_bp\.route\('/tagesbericht', methods=\['GET'\]\)\ndef get_tagesbericht\(\):.*?@werkstatt_live_bp\.route\('/nachkalkulation', methods=\['GET'\]\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_auftrag_detail(content):
    """Ersetzt get_auftrag_detail() durch WerkstattData-Version"""
    new_code = '''@werkstatt_live_bp.route('/auftrag/<int:auftrag_nr>', methods=['GET'])
def get_auftrag_detail(auftrag_nr):
    """
    Detailansicht eines einzelnen Auftrags mit allen Positionen

    TAG 150: Refaktoriert - nutzt WerkstattData.get_auftrag_detail()
    Vorher: 165 LOC | Nachher: 30 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        data = WerkstattData.get_auftrag_detail(auftrag_nr)

        if not data.get('success', True):
            return jsonify(data), 404

        return jsonify({
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception(f"Fehler beim Laden von Auftrag {auftrag_nr}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/problemfaelle', methods=['GET'])'''

    pattern = r"@werkstatt_live_bp\.route\('/auftrag/<int:auftrag_nr>', methods=\['GET'\]\)\ndef get_auftrag_detail\(auftrag_nr\):.*?@werkstatt_live_bp\.route\('/problemfaelle', methods=\['GET'\]\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_problemfaelle(content):
    """Ersetzt get_problemfaelle_live() durch WerkstattData-Version"""
    new_code = '''@werkstatt_live_bp.route('/problemfaelle', methods=['GET'])
def get_problemfaelle_live():
    """
    Problemfaelle: Auftraege mit niedrigem Leistungsgrad

    TAG 150: Refaktoriert - nutzt WerkstattData.get_problemfaelle()
    Vorher: 210 LOC | Nachher: 40 LOC

    Query-Parameter:
    - zeitraum: heute|woche|monat|vormonat|quartal|jahr|custom
    - von/bis: Datumsbereich fuer custom
    - betrieb: 1|3|alle
    - max_lg: Maximaler Leistungsgrad (default: 70)
    - min_stempelzeit: Minimale Stempelzeit in Minuten (default: 30)
    """
    try:
        from api.werkstatt_data import WerkstattData

        zeitraum = request.args.get('zeitraum', 'monat')
        betrieb = request.args.get('betrieb')
        max_lg = request.args.get('max_lg', 70, type=float)
        min_stempelzeit = request.args.get('min_stempelzeit', 30, type=int)
        von = request.args.get('von')
        bis = request.args.get('bis')

        # Betrieb-Konvertierung
        betrieb_int = None
        if betrieb and betrieb != 'alle':
            betrieb_int = int(betrieb)

        data = WerkstattData.get_problemfaelle(
            zeitraum=zeitraum,
            betrieb=betrieb_int,
            max_lg=max_lg,
            min_stempelzeit=min_stempelzeit,
            von=von,
            bis=bis
        )

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Problemfaelle-Abfrage")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/kapazitaet', methods=['GET'])'''

    pattern = r"@werkstatt_live_bp\.route\('/problemfaelle', methods=\['GET'\]\)\ndef get_problemfaelle_live\(\):.*?@werkstatt_live_bp\.route\('/kapazitaet', methods=\['GET'\]\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_anwesenheit(content):
    """Ersetzt get_anwesenheit_v2() durch WerkstattData-Version (TAG 151)"""
    new_code = '''@werkstatt_live_bp.route('/anwesenheit', methods=['GET'])
def get_anwesenheit_v2():
    """
    Anwesenheits-Report V2: Wer hat heute gearbeitet?

    TAG 151: Refaktoriert - nutzt WerkstattData.get_anwesenheit()
    Vorher: 160 LOC | Nachher: 35 LOC

    Query-Parameter:
    - datum: Datum im Format YYYY-MM-DD (default: heute)
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        from api.werkstatt_data import WerkstattData

        datum_str = request.args.get('datum')
        subsidiary = request.args.get('subsidiary', type=int)

        datum = None
        if datum_str:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()

        data = WerkstattData.get_anwesenheit(datum=datum, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Anwesenheits-Report V2")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ANWESENHEITS-REPORT V1 (Legacy) - TAG 116'''

    pattern = r"@werkstatt_live_bp\.route\('/anwesenheit', methods=\['GET'\]\)\ndef get_anwesenheit_v2\(\):.*?# ============================================================\n# ANWESENHEITS-REPORT V1 \(Legacy\) - TAG 116"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_heute_live(content):
    """Ersetzt get_heute_live() durch WerkstattData-Version (TAG 151)"""
    new_code = '''@werkstatt_live_bp.route('/heute', methods=['GET'])
def get_heute_live():
    """
    Echte Zahlen von heute: Gestempelt, Verrechnet, Aktive Mechaniker

    TAG 151: Refaktoriert - nutzt WerkstattData.get_heute_live()
    Vorher: 330 LOC | Nachher: 30 LOC

    Query-Parameter:
    - subsidiary: Filter nach Betrieb (1, 2, 3)
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_heute_live(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei HEUTE LIVE")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# AUFTRÄGE ENRICHED - Kombiniert Locosoft + ML + Gudat (TAG 98)'''

    pattern = r"@werkstatt_live_bp\.route\('/heute', methods=\['GET'\]\)\ndef get_heute_live\(\):.*?# ============================================================================\n# AUFTRÄGE ENRICHED - Kombiniert Locosoft \+ ML \+ Gudat \(TAG 98\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_anwesenheit_legacy(content):
    """Ersetzt get_anwesenheit_report() durch WerkstattData-Version (TAG 151)"""
    new_code = '''@werkstatt_live_bp.route('/anwesenheit/legacy', methods=['GET'])
def get_anwesenheit_report():
    """
    Anwesenheits-Report Legacy: Type 1 basiert

    TAG 151: Refaktoriert - nutzt WerkstattData.get_anwesenheit_legacy()
    Vorher: 130 LOC | Nachher: 25 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_anwesenheit_legacy(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            'timestamp': datetime.now().isoformat(),
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Anwesenheits-Report")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# DRIVE KULANZ-MONITORING - TAG 119'''

    pattern = r"@werkstatt_live_bp\.route\('/anwesenheit/legacy', methods=\['GET'\]\)\ndef get_anwesenheit_report\(\):.*?# ============================================================\n# DRIVE KULANZ-MONITORING - TAG 119"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_kulanz_monitoring(content):
    """Ersetzt get_kulanz_monitoring() durch WerkstattData-Version (TAG 151)"""
    new_code = '''@werkstatt_live_bp.route('/drive/kulanz-monitoring', methods=['GET'])
def get_kulanz_monitoring():
    """
    DRIVE Kulanz-Monitoring: Wo verlieren wir Geld?

    TAG 151: Refaktoriert - nutzt WerkstattData.get_kulanz_monitoring()
    Vorher: 160 LOC | Nachher: 25 LOC

    Query-Parameter:
    - wochen: Anzahl Wochen zurueck (default: 4)
    - subsidiary: Betrieb filtern (optional)
    """
    try:
        from api.werkstatt_data import WerkstattData

        wochen = int(request.args.get('wochen', 4))
        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_kulanz_monitoring(wochen=wochen, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei Kulanz-Monitoring")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# DRIVE TAGES-BRIEFING - TAG 119'''

    pattern = r"@werkstatt_live_bp\.route\('/drive/kulanz-monitoring', methods=\['GET'\]\)\ndef get_kulanz_monitoring\(\):.*?# ============================================================\n# DRIVE TAGES-BRIEFING - TAG 119"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_drive_briefing(content):
    """Ersetzt get_drive_briefing() durch WerkstattData-Version (TAG 152)"""
    new_code = '''@werkstatt_live_bp.route('/drive/briefing', methods=['GET'])
def get_drive_briefing():
    """
    DRIVE Tages-Briefing: 5-Minuten-Ueberblick fuer Werkstattleiter

    TAG 152: Refaktoriert - nutzt WerkstattData.get_drive_briefing()
    Vorher: 165 LOC | Nachher: 30 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_drive_briefing(betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei DRIVE Briefing")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# DRIVE KAPAZITÄT MIT G-FAKTOR - TAG 119'''

    pattern = r"@werkstatt_live_bp\.route\('/drive/briefing', methods=\['GET'\]\)\ndef get_drive_briefing\(\):.*?# ============================================================\n# DRIVE KAPAZITÄT MIT G-FAKTOR - TAG 119"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_drive_kapazitaet(content):
    """Ersetzt get_drive_kapazitaet() durch WerkstattData-Version (TAG 152)"""
    new_code = '''@werkstatt_live_bp.route('/drive/kapazitaet', methods=['GET'])
def get_drive_kapazitaet():
    """
    DRIVE Kapazitaetsplanung: Realistische Auslastung

    TAG 152: Refaktoriert - nutzt WerkstattData.get_drive_kapazitaet()
    Vorher: 210 LOC | Nachher: 35 LOC
    """
    try:
        from api.werkstatt_data import WerkstattData

        wochen = int(request.args.get('wochen', 4))
        subsidiary = request.args.get('subsidiary', type=int)

        data = WerkstattData.get_drive_kapazitaet(wochen=wochen, betrieb=subsidiary)

        return jsonify({
            'success': True,
            'source': 'LIVE_V2',
            **data
        })

    except Exception as e:
        logger.exception("Fehler bei DRIVE Kapazitaet")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# WERKSTATT LIVE-BOARD (TAG 125)'''

    pattern = r"@werkstatt_live_bp\.route\('/drive/kapazitaet', methods=\['GET'\]\)\ndef get_drive_kapazitaet\(\):.*?# =============================================================================\n# WERKSTATT LIVE-BOARD \(TAG 125\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_gudat_disposition(content):
    """
    TAG 153: Ersetzt lokale get_gudat_disposition() durch Import aus gudat_data.py

    Entfernt:
    - GUDAT_CONFIG Dictionary
    - get_gudat_disposition() Funktion (~110 LOC)

    Ersetzt durch:
    - Import aus api.gudat_data
    """
    # 1. GUDAT_CONFIG entfernen
    content = re.sub(
        r"# Gudat Credentials \(TAG 125\)\nGUDAT_CONFIG = \{[^}]+\}\n+",
        "",
        content,
        flags=re.DOTALL
    )

    # 2. get_gudat_disposition() Funktion entfernen und durch Import ersetzen
    # Die Funktion geht von "def get_gudat_disposition" bis "AZUBI_MA_NUMMERN"
    new_code = '''# TAG 153: Gudat-Disposition aus gudat_data.py
# Migration-Plan: docs/GUDAT_TO_LOCOSOFT_MIGRATION.md
from api.gudat_data import GudatData, get_gudat_disposition

# Azubis - stempeln nur Anwesenheit, keine Aufträge
# Diese werden vom Leerlauf-Alarm UND Leistungs-Ranking ausgenommen
AZUBI_MA_NUMMERN'''

    pattern = r"def get_gudat_disposition\(target_date=None\):.*?AZUBI_MA_NUMMERN"
    content = re.sub(pattern, new_code, content, flags=re.DOTALL)

    return content


def refactor_gudat_kapazitaet(content):
    """
    TAG 153: Ersetzt get_gudat_kapazitaet() durch GudatData.get_kapazitaet()

    Entfernt: ~100 LOC
    """
    new_code = '''@werkstatt_live_bp.route('/gudat/kapazitaet', methods=['GET'])
def get_gudat_kapazitaet():
    """
    Proxy für Gudat Kapazitäts-Daten

    TAG 153: Refaktoriert - nutzt GudatData.get_kapazitaet()
    Vorher: 100 LOC | Nachher: 15 LOC
    """
    try:
        from api.gudat_data import GudatData

        data = GudatData.get_kapazitaet()

        if not data.get('success'):
            return jsonify(data), 503

        return jsonify(data)

    except Exception as e:
        logger.exception("Fehler bei Gudat Kapazität")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@werkstatt_live_bp.route('/forecast', methods=['GET'])'''

    pattern = r"@werkstatt_live_bp\.route\('/gudat/kapazitaet', methods=\['GET'\]\)\ndef get_gudat_kapazitaet\(\):.*?@werkstatt_live_bp\.route\('/forecast', methods=\['GET'\]\)"
    return re.sub(pattern, new_code, content, flags=re.DOTALL)


def refactor_liveboard_gudat_usage(content):
    """
    TAG 153: Vereinfacht Gudat-Nutzung im Liveboard

    Ersetzt:
    - Lokales Name-Matching durch GudatData.create_mechaniker_mapping()
    - Lokales Merge durch GudatData.merge_zeitbloecke()
    """
    # Erstmal nur Kommentar einfügen - volle Refaktorierung später
    # Die Komplexität ist zu hoch für automatisches Refactoring

    # Marker für spätere manuelle Refaktorierung
    marker = """
        # ================================================================
        # TAG 153: GUDAT-INTEGRATION - MIGRATION VORBEREITET
        # Nutzt noch lokale Funktionen, später auf GudatData umstellen:
        # - GudatData.create_mechaniker_mapping() statt match_gudat_name()
        # - GudatData.merge_zeitbloecke() statt inline Merge-Logik
        # Siehe: docs/GUDAT_TO_LOCOSOFT_MIGRATION.md
        # ================================================================
"""

    # Füge Marker vor "4b. GUDAT Disposition holen" ein
    content = content.replace(
        "# 4b. GUDAT Disposition holen (TAG 125)",
        marker + "        # 4b. GUDAT Disposition holen (TAG 125)"
    )

    return content


def refactor_match_gudat_name(content):
    """
    TAG 154: Ersetzt lokale match_gudat_name() durch GudatData.create_mechaniker_mapping()

    Entfernt: ~30 LOC (lokale Funktion + Mapping-Loop)
    """
    # Alten Code-Block (match_gudat_name + Mapping-Loop)
    old_code = '''        # Name-Mapping: Gudat "Vorname Nachname" → Locosoft "Nachname, Vorname"
        def match_gudat_name(locosoft_name, gudat_names):
            """Findet passenden Gudat-Namen für Locosoft-Namen"""
            if not locosoft_name:
                return None
            # Locosoft: "Reitmeier, Tobias" → parts = ["Reitmeier", "Tobias"]
            parts = [p.strip() for p in locosoft_name.split(',')]
            if len(parts) >= 2:
                nachname, vorname = parts[0], parts[1].split()[0]  # Nur erster Vorname
                # Gudat: "Tobias Reitmeier"
                gudat_pattern1 = f"{vorname} {nachname}"
                gudat_pattern2 = f"{nachname} {vorname}"
                for gn in gudat_names:
                    gn_lower = gn.lower()
                    if gudat_pattern1.lower() == gn_lower or gudat_pattern2.lower() == gn_lower:
                        return gn
                    # Fuzzy: enthält Vor- und Nachname
                    if vorname.lower() in gn_lower and nachname.lower() in gn_lower:
                        return gn
            return None

        # Gudat-Mechaniker-Mapping erstellen
        gudat_to_locosoft = {}
        for mech in mechaniker_list:
            matched = match_gudat_name(mech['name'], gudat_disposition.keys())
            if matched:
                gudat_to_locosoft[mech['employee_number']] = gudat_disposition[matched]'''

    # Neuer Code mit GudatData
    new_code = '''        # TAG 154: Gudat-Mechaniker-Mapping über GudatData (vorher ~30 LOC)
        gudat_to_locosoft = GudatData.create_mechaniker_mapping(mechaniker_list, gudat_disposition)'''

    content = content.replace(old_code, new_code)
    return content


def main():
    filepath = '/opt/greiner-portal/api/werkstatt_live_api.py'

    print(f"Lese {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_len = len(content)

    # TAG 154: match_gudat_name durch GudatData ersetzen
    print("Refaktoriere match_gudat_name (TAG 154)...")
    content = refactor_match_gudat_name(content)

    new_len = len(content)

    print(f"Schreibe {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fertig! {original_len} -> {new_len} Zeichen ({new_len - original_len:+d})")


if __name__ == '__main__':
    main()
