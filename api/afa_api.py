"""
AfA-Modul API — Vorführwagen und Mietwagen (Anlagevermögen)
============================================================
Monatliche Abschreibung (AfA) linear, 72 Monate, monatsgenau.
Erstellt: 2026-02-16 | Workstream: Controlling
Locosoft-Import: EK-Formel und Fahrzeugfilter (VFW/Mietwagen) wie kalkulation_helpers / DB1.
"""

from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from flask import Blueprint, jsonify, request

from api.db_utils import db_session, row_to_dict, rows_to_list, locosoft_session

afa_api = Blueprint('afa_api', __name__)

# Standort-Mapping Locosoft -> AfA betriebsnr (1=DEG Opel, 2=HYU, 3=LAN)
LOCOSOFT_SUBSIDIARY_TO_BETRIEBSNR = {1: 1, 2: 2, 3: 3}
# Anzeige Standort in Buchungsliste (Sortierung sichtbar: Mietwagen DEG/LAN/HYU, VFW DEG/LAN/HYU/Leapmotor)
BETRIEBSNR_TO_STANDORT = {1: 'DEG', 2: 'HYU', 3: 'LAN'}

# Buchhaltung (Feedback Buchhaltung 2026): Monatsende Buchung "Soll an Haben"
# betriebsnr 1=DEG Opel, 2=HYU, 3=LAN
# Soll: 450001 (DEG/HYU), 450002 (LAN)
# Haben: Mietwagen 090301 (DEG/HYU), 090302 (LAN); VFW 090401 (DEG/HYU/Leapmotor), 090402 (LAN)
AFA_KONTO_SOLL = {1: 450001, 2: 450001, 3: 450002}
AFA_KONTO_HABEN_MIETWAGEN = {1: 90301, 2: 90301, 3: 90302}   # 090301, 090302
AFA_KONTO_HABEN_VFW = {1: 90401, 2: 90401, 3: 90402}         # 090401, 090402 (VFW DEG/HYU/Leapmotor, LAN)


def _afa_konten(betriebsnr, fahrzeugart, fahrzeug=None):
    """Liefert (konto_soll, konto_haben) für Monatsbuchung AfA. fahrzeugart = VFW | MIETWAGEN.
    Mietwagen: 090301 (DEG/HYU), 090302 (LAN). VFW: 090401 (DEG/HYU/Leapmotor), 090402 (LAN)."""
    bn = int(betriebsnr) if betriebsnr is not None else 1
    soll = AFA_KONTO_SOLL.get(bn, 450001)
    if (fahrzeugart or '').upper() == 'MIETWAGEN':
        haben = AFA_KONTO_HABEN_MIETWAGEN.get(bn, 90301)
    else:
        haben = AFA_KONTO_HABEN_VFW.get(bn, 90401)
    return soll, haben

# Geschäftsjahr: 1. September bis 31. August (z.B. 2025/26 = 01.09.2025 - 31.08.2026)
def _geschaeftsjahr_bis_datum(gj_string):
    """gj_string z.B. '2025/26' -> (date(2025,9,1), date(2026,8,31))."""
    try:
        start_jahr = int(gj_string.strip().split('/')[0])
        von = date(start_jahr, 9, 1)
        bis = date(start_jahr + 1, 8, 31)
        return von, bis
    except (ValueError, IndexError):
        return None


# =============================================================================
# Berechnungslogik (SSOT)
# =============================================================================

def berechne_monatliche_afa(fahrzeug):
    """
    Berechnet die monatliche AfA für ein Fahrzeug.
    Lineare AfA: Anschaffungskosten / Nutzungsdauer_Monate
    """
    if not fahrzeug.get('anschaffungskosten_netto') or not fahrzeug.get('nutzungsdauer_monate'):
        return None
    if fahrzeug.get('afa_methode') != 'linear':
        raise ValueError(f"Unbekannte AfA-Methode: {fahrzeug.get('afa_methode', '?')}")
    ak = float(fahrzeug['anschaffungskosten_netto'])
    nd = int(fahrzeug['nutzungsdauer_monate'])
    return round(ak / nd, 2)


def berechne_restbuchwert(fahrzeug, stichtag):
    """
    Restbuchwert zu einem Stichtag.
    Anschaffungsmonat zählt mit, Abgangsmonat zählt voll.
    """
    if isinstance(stichtag, str):
        stichtag = date.fromisoformat(stichtag)
    anschaffung = fahrzeug.get('anschaffungsdatum')
    if isinstance(anschaffung, str):
        anschaffung = date.fromisoformat(anschaffung)
    afa_monatlich = fahrzeug.get('afa_monatlich')
    if afa_monatlich is None:
        afa_monatlich = berechne_monatliche_afa(fahrzeug)
    if afa_monatlich is None:
        return None
    ak = float(fahrzeug['anschaffungskosten_netto'])
    nd = int(fahrzeug.get('nutzungsdauer_monate', 72))

    # Monate seit Anschaffung (Anschaffungsmonat zählt mit)
    monate = (stichtag.year - anschaffung.year) * 12 + (stichtag.month - anschaffung.month) + 1
    monate = min(monate, nd)
    monate = max(monate, 0)

    kumulierte_afa = monate * float(afa_monatlich)
    restbuchwert = ak - kumulierte_afa
    return round(max(restbuchwert, 0), 2)


def _ek_netto_from_locosoft_row(row):
    """
    Berechnet EK netto (Einsatzwert ohne Steuer) aus Locosoft dealer_vehicles-Zeile.
    Formel wie kalkulation_helpers.sql_ek_netto + usage_value_encr_other - total_writedown.
    """
    def _f(key, default=0):
        val = row.get(key)
        return float(val) if val is not None else default
    return round(
        _f('calc_basic_charge') + _f('calc_accessory') + _f('calc_extra_expenses')
        + _f('calc_usage_value_encr_internal') + _f('calc_usage_value_encr_external')
        + _f('calc_usage_value_encr_other') - _f('calc_total_writedown'),
        2
    )


def _fahrzeug_from_row(row, cursor=None):
    """Konvertiert DB-Row zu Dict; Datum/Decimal als Python-Typen."""
    d = row_to_dict(row, cursor) or {}
    for key in ('anschaffungsdatum', 'abgangsdatum', 'erstellt_am', 'aktualisiert_am'):
        if d.get(key) and hasattr(d[key], 'isoformat'):
            d[key] = d[key].isoformat() if hasattr(d[key], 'date') else str(d[key])
    for key in ('anschaffungskosten_netto', 'afa_monatlich', 'nutzungsdauer_monate',
                'restbuchwert_abgang', 'buchgewinn_verlust', 'verkaufspreis_netto'):
        if d.get(key) is not None and isinstance(d[key], Decimal):
            d[key] = float(d[key])
    if d.get('tageszulassung') is not None and not isinstance(d['tageszulassung'], bool):
        d['tageszulassung'] = bool(d['tageszulassung'])
    if d.get('afa_monatlich') is None and d.get('anschaffungskosten_netto') and d.get('nutzungsdauer_monate'):
        d['afa_monatlich'] = berechne_monatliche_afa(d)
    return d


# =============================================================================
# GET /api/afa/dashboard
# =============================================================================

@afa_api.route('/api/afa/dashboard', methods=['GET'])
def dashboard():
    """Übersicht: Aktive VFW/Mietwagen, Gesamt-AfA/Monat, Restbuchwerte.
    Optional: gj=2025/26 filtert auf Bestand im Geschäftsjahr (1.9. - 31.8.)."""
    try:
        gj_param = request.args.get('gj', '').strip()
        gj_range = _geschaeftsjahr_bis_datum(gj_param) if gj_param else None

        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                       fahrzeugart, betriebsnr, firma, anschaffungsdatum, anschaffungskosten_netto,
                       nutzungsdauer_monate, afa_methode, afa_monatlich, status, abgangsdatum,
                       restbuchwert_abgang, buchgewinn_verlust, tageszulassung
                FROM afa_anlagevermoegen
                ORDER BY status ASC, anschaffungsdatum DESC
            """)
            rows = cur.fetchall()
        fahrzeuge = [_fahrzeug_from_row(r, cur) for r in rows]
        for f in fahrzeuge:
            f['standort'] = BETRIEBSNR_TO_STANDORT.get(f.get('betriebsnr') or 1, 'DEG')
        # Sortierung wie Monatsübersicht: Mietwagen DEG/LAN/HYU, dann VFW DEG/LAN/HYU, dann VFW Leapmotor (Buchhaltung)
        def _sort_key_fahrzeug(f):
            art = (f.get('fahrzeugart') or '').upper()
            bn = f.get('betriebsnr') or 1
            is_leap = 'Leapmotor' in (f.get('marke') or '') + (f.get('fahrzeug_bezeichnung') or '')
            return (0 if art == 'MIETWAGEN' else 1, {1: 0, 3: 1, 2: 2}.get(bn, 0), 1 if (art == 'VFW' and is_leap) else 0)
        fahrzeuge.sort(key=_sort_key_fahrzeug)

        if gj_range:
            von, bis = gj_range
            def im_bestand_gj(f):
                ad = f.get('anschaffungsdatum')
                ad = date.fromisoformat(ad) if isinstance(ad, str) else ad
                if not ad or ad > bis:
                    return False
                ag = f.get('abgangsdatum')
                if not ag:
                    return True
                ag = date.fromisoformat(ag) if isinstance(ag, str) else ag
                return ag >= von
            fahrzeuge = [f for f in fahrzeuge if im_bestand_gj(f)]

        heute = date.today()
        aktive = [f for f in fahrzeuge if f.get('status') == 'aktiv']
        # Nur AfA-pflichtige (keine Tageszulassung) für Summen/KPIs
        aktive_afa = [f for f in aktive if not f.get('tageszulassung')]
        summe_restbuchwert = 0
        summe_afa_monat = 0
        halte_monate_list = []
        for f in fahrzeuge:
            if f.get('status') == 'aktiv':
                rw = berechne_restbuchwert(f, heute)
                f['restbuchwert_aktuell'] = rw
                if not f.get('tageszulassung'):
                    if rw is not None:
                        summe_restbuchwert += rw
                    if f.get('afa_monatlich') is not None:
                        summe_afa_monat += f['afa_monatlich']
                    if f.get('anschaffungsdatum'):
                        ad = date.fromisoformat(f['anschaffungsdatum']) if isinstance(f['anschaffungsdatum'], str) else f['anschaffungsdatum']
                        monate = (heute.year - ad.year) * 12 + (heute.month - ad.month) + 1
                        halte_monate_list.append(max(0, monate))

        durchschnitt_halte = (sum(halte_monate_list) / len(halte_monate_list)) if halte_monate_list else 0

        return jsonify({
            'ok': True,
            'geschaeftsjahr': gj_param or None,
            'kpis': {
                'anzahl_aktive_vfw': sum(1 for f in aktive if f.get('fahrzeugart') == 'VFW'),
                'anzahl_aktive_mietwagen': sum(1 for f in aktive if f.get('fahrzeugart') == 'MIETWAGEN'),
                'anzahl_aktiv': len(aktive),
                'anzahl_afa_pflichtig': len(aktive_afa),
                'summe_restbuchwert': round(summe_restbuchwert, 2),
                'afa_monat_gesamt': round(summe_afa_monat, 2),
                'durchschnitt_halte_monate': round(durchschnitt_halte, 1),
            },
            'fahrzeuge': fahrzeuge,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/fahrzeuge
# =============================================================================

@afa_api.route('/api/afa/fahrzeuge', methods=['GET'])
def fahrzeuge_liste():
    """Liste aller AfA-Fahrzeuge mit Filter (status, art, marke, betrieb)."""
    status = request.args.get('status')
    art = request.args.get('art')  # VFW, MIETWAGEN
    marke = request.args.get('marke')
    betrieb = request.args.get('betrieb')  # 1, 2, 3

    sql = """
        SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
               fahrzeugart, betriebsnr, firma, anschaffungsdatum, anschaffungskosten_netto,
               nutzungsdauer_monate, afa_methode, afa_monatlich, status, abgangsdatum,
               abgangsgrund, restbuchwert_abgang, buchgewinn_verlust, tageszulassung
        FROM afa_anlagevermoegen
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND status = %s"
        params.append(status)
    if art:
        sql += " AND fahrzeugart = %s"
        params.append(art)
    if marke:
        sql += " AND marke ILIKE %s"
        params.append(f'%{marke}%')
    if betrieb:
        sql += " AND betriebsnr = %s"
        params.append(int(betrieb))
    sql += " ORDER BY status ASC, anschaffungsdatum DESC"

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(sql, params or None)
            rows = cur.fetchall()
        liste = [_fahrzeug_from_row(r, cur) for r in rows]
        heute = date.today()
        for f in liste:
            if f.get('status') == 'aktiv':
                f['restbuchwert_aktuell'] = berechne_restbuchwert(f, heute)
        return jsonify({'ok': True, 'fahrzeuge': liste})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/fahrzeug/<id>
# =============================================================================

@afa_api.route('/api/afa/fahrzeug/<int:fk_id>', methods=['GET'])
def fahrzeug_detail(fk_id):
    """Detail eines Fahrzeugs inkl. AfA-Verlauf (Buchungen)."""
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM afa_anlagevermoegen WHERE id = %s
            """, (fk_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Fahrzeug nicht gefunden'}), 404
            f = _fahrzeug_from_row(row, cur)
            cur.execute("""
                SELECT id, buchungsmonat, afa_betrag, restbuchwert, kumuliert, ist_anteilig
                FROM afa_buchungen WHERE anlage_id = %s ORDER BY buchungsmonat
            """, (fk_id,))
            buchungen = rows_to_list(cur.fetchall(), cur)
        for b in buchungen:
            if b.get('buchungsmonat') and hasattr(b['buchungsmonat'], 'isoformat'):
                b['buchungsmonat'] = b['buchungsmonat'].isoformat()[:7]
            for k in ('afa_betrag', 'restbuchwert', 'kumuliert'):
                if b.get(k) is not None and isinstance(b[k], Decimal):
                    b[k] = float(b[k])

        f['buchungen'] = buchungen
        heute = date.today()
        f['restbuchwert_aktuell'] = berechne_restbuchwert(f, heute) if f.get('status') == 'aktiv' else f.get('restbuchwert_abgang')
        return jsonify({'ok': True, 'fahrzeug': f})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/fahrzeug/<id>/abgang-vorschau
# =============================================================================

@afa_api.route('/api/afa/fahrzeug/<int:fk_id>/abgang-vorschau', methods=['GET'])
def fahrzeug_abgang_vorschau(fk_id):
    """Für Abgangsdatum: Restbuchwert und aufgelaufene AfA (für Buchhaltung Locosoft)."""
    datum_str = request.args.get('datum')
    if not datum_str:
        return jsonify({'ok': False, 'error': 'Parameter datum (YYYY-MM-DD) erforderlich'}), 400
    try:
        stichtag = date.fromisoformat(datum_str)
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'error': 'Ungültiges Datum'}), 400
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, anschaffungsdatum, anschaffungskosten_netto, nutzungsdauer_monate, afa_methode, afa_monatlich
                FROM afa_anlagevermoegen WHERE id = %s AND status = 'aktiv'
            """, (fk_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Fahrzeug nicht gefunden oder nicht aktiv'}), 404
            f = _fahrzeug_from_row(row, cur)
        rest = berechne_restbuchwert(f, stichtag)
        ak = float(f.get('anschaffungskosten_netto') or 0)
        aufgelaufene_afa = round(ak - (rest or 0), 2) if rest is not None else None
        return jsonify({
            'ok': True,
            'datum': datum_str,
            'restbuchwert': rest,
            'aufgelaufene_afa': aufgelaufene_afa,
            'anschaffungskosten_netto': ak,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# DELETE /api/afa/fahrzeug/<id>
# =============================================================================

@afa_api.route('/api/afa/fahrzeug/<int:fk_id>', methods=['DELETE'])
def fahrzeug_loeschen(fk_id):
    """Fahrzeug und zugehörige AfA-Buchungen löschen (z. B. versehentlicher Import)."""
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM afa_anlagevermoegen WHERE id = %s", (fk_id,))
            if not cur.fetchone():
                return jsonify({'ok': False, 'error': 'Fahrzeug nicht gefunden'}), 404
            cur.execute("DELETE FROM afa_buchungen WHERE anlage_id = %s", (fk_id,))
            cur.execute("DELETE FROM afa_anlagevermoegen WHERE id = %s", (fk_id,))
            conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/monatsberechnung
# =============================================================================

@afa_api.route('/api/afa/monatsberechnung', methods=['GET'])
def monatsberechnung():
    """AfA-Berechnung für einen bestimmten Monat (Query: jahr, monat oder yyyy-mm)."""
    jahr = request.args.get('jahr', type=int)
    monat = request.args.get('monat', type=int)
    ym = request.args.get('yyyy-mm')  # z.B. 2025-03
    if ym:
        parts = ym.split('-')
        if len(parts) == 2:
            jahr, monat = int(parts[0]), int(parts[1])
    if not jahr or not monat:
        heute = date.today()
        jahr, monat = heute.year, heute.month
    buchungsmonat = date(jahr, monat, 1)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell, fahrzeugart,
                       betriebsnr, anschaffungsdatum, anschaffungskosten_netto, nutzungsdauer_monate,
                       afa_methode, afa_monatlich, status, abgangsdatum, tageszulassung
                FROM afa_anlagevermoegen
                WHERE status = 'aktiv'
                AND (tageszulassung IS NULL OR tageszulassung = false)
                AND anschaffungsdatum <= %s
                AND (abgangsdatum IS NULL OR abgangsdatum >= %s)
            """, (buchungsmonat, buchungsmonat))
            rows = cur.fetchall()
        aktive = [_fahrzeug_from_row(r, cur) for r in rows]

        positionen = []
        summe = 0
        for f in aktive:
            if f.get('tageszulassung'):
                continue
            afa = f.get('afa_monatlich') or berechne_monatliche_afa(f)
            if afa is None:
                continue
            rest = berechne_restbuchwert(f, buchungsmonat)
            k_soll, k_haben = _afa_konten(f.get('betriebsnr'), f.get('fahrzeugart'), f)
            bn = f.get('betriebsnr') or 1
            positionen.append({
                'anlage_id': f['id'],
                'vin': f.get('vin'),
                'kennzeichen': f.get('kennzeichen'),
                'standort': BETRIEBSNR_TO_STANDORT.get(bn, 'DEG'),
                'fahrzeug_bezeichnung': f.get('fahrzeug_bezeichnung'),
                'marke': f.get('marke'),
                'fahrzeugart': f.get('fahrzeugart'),
                'betriebsnr': bn,
                'afa_betrag': afa,
                'restbuchwert': rest,
                'konto_soll': k_soll,
                'konto_haben': k_haben,
            })
            summe += afa

        # Sortierung: Mietwagen DEG, LAN, HYU; dann VFW DEG, LAN, HYU, Leapmotor (Buchhaltung zum Kontrollieren)
        def _sort_key_pos(p):
            art = (p.get('fahrzeugart') or '').upper()
            bn = p.get('betriebsnr') or 1
            is_leap = 'Leapmotor' in (p.get('marke') or '') + (p.get('fahrzeug_bezeichnung') or '')
            return (0 if art == 'MIETWAGEN' else 1, {1: 0, 3: 1, 2: 2}.get(bn, 0), 1 if (art == 'VFW' and is_leap) else 0)
        positionen.sort(key=_sort_key_pos)

        return jsonify({
            'ok': True,
            'buchungsmonat': buchungsmonat.isoformat()[:7],
            'positionen': positionen,
            'summe_afa': round(summe, 2),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/buchungsliste
# =============================================================================

@afa_api.route('/api/afa/buchungsliste', methods=['GET'])
def buchungsliste():
    """Exportierbare Buchungsliste für einen Monat (Locosoft-Einbuchung)."""
    jahr = request.args.get('jahr', type=int)
    monat = request.args.get('monat', type=int)
    ym = request.args.get('yyyy-mm')
    if ym:
        parts = ym.split('-')
        if len(parts) == 2:
            jahr, monat = int(parts[0]), int(parts[1])
    if not jahr or not monat:
        heute = date.today()
        jahr, monat = heute.year, heute.month
    buchungsmonat = date(jahr, monat, 1)

    try:
        resp = monatsberechnung()
        if isinstance(resp, tuple):
            resp_obj, status = resp[0], resp[1]
        else:
            resp_obj, status = resp, 200
        if status != 200:
            return resp if isinstance(resp, tuple) else (resp, status)
        data = resp_obj.get_json()
        if not data.get('ok'):
            return jsonify(data), 500
        positionen = data.get('positionen', [])
        # Zwei Buchhaltungen: Standard-CSV = nur Opel/Leapmotor (Betrieb 1+3), Hyundai-CSV = betrieb=2
        betrieb_filter = request.args.get('betrieb', type=int)
        if betrieb_filter is not None:
            positionen = [p for p in positionen if (p.get('betriebsnr') or 0) == betrieb_filter]
        else:
            # "CSV exportieren" ohne Parameter: Hyundai (2) ausschließen, nur DEG/LAN (1, 3)
            positionen = [p for p in positionen if (p.get('betriebsnr') or 0) in (1, 3)]
        summe = round(sum(p.get('afa_betrag') or 0 for p in positionen), 2)
        # CSV mit fortlaufender Nr.
        header = ['Nr.', 'Kennzeichen', 'Fahrgestellnr.', 'Standort', 'Bezeichnung', 'Art', 'Betrieb', 'Soll', 'Haben', 'AfA-Betrag']
        csv_rows = [[i + 1, p.get('kennzeichen'), p.get('vin') or '', p.get('standort') or '', p.get('fahrzeug_bezeichnung'), p.get('fahrzeugart'), p.get('betriebsnr'), '{:06d}'.format(p.get('konto_soll') or 0), '{:06d}'.format(p.get('konto_haben') or 0), p.get('afa_betrag')] for i, p in enumerate(positionen)]
        summe_row = ['', '', '', '', '', '', '', '', 'Summe', summe]
        return jsonify({
            'ok': True,
            'buchungsmonat': data['buchungsmonat'],
            'positionen': positionen,
            'summe_afa': summe,
            'export_csv_zeilen': [header, *csv_rows, summe_row],
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# POST /api/afa/fahrzeug
# =============================================================================

@afa_api.route('/api/afa/fahrzeug', methods=['POST'])
def fahrzeug_anlegen():
    """Neues VFW/Mietwagen anlegen."""
    data = request.get_json() or {}
    vin = data.get('vin')
    kennzeichen = data.get('kennzeichen')
    fahrzeug_bezeichnung = data.get('fahrzeug_bezeichnung')
    marke = data.get('marke')
    modell = data.get('modell')
    fahrzeugart = (data.get('fahrzeugart') or 'VFW').strip().upper()
    if fahrzeugart not in ('VFW', 'MIETWAGEN'):
        fahrzeugart = 'VFW'
    betriebsnr = data.get('betriebsnr', 1)
    firma = data.get('firma')
    anschaffungsdatum = data.get('anschaffungsdatum')
    anschaffungskosten_netto = data.get('anschaffungskosten_netto')
    nutzungsdauer_monate = data.get('nutzungsdauer_monate', 72)
    afa_methode = data.get('afa_methode', 'linear')
    locosoft_fahrzeug_id = data.get('locosoft_fahrzeug_id')
    finanzierung_id = data.get('finanzierung_id')
    notizen = data.get('notizen')
    tageszulassung = bool(data.get('tageszulassung', False))

    if not anschaffungsdatum or not anschaffungskosten_netto:
        return jsonify({'ok': False, 'error': 'anschaffungsdatum und anschaffungskosten_netto erforderlich'}), 400

    if isinstance(anschaffungsdatum, str):
        anschaffungsdatum = date.fromisoformat(anschaffungsdatum)
    ak = float(anschaffungskosten_netto)
    nd = int(nutzungsdauer_monate)
    afa_monatlich = round(ak / nd, 2)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO afa_anlagevermoegen (
                    vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                    fahrzeugart, betriebsnr, firma, anschaffungsdatum, anschaffungskosten_netto,
                    nutzungsdauer_monate, afa_methode, afa_monatlich, status,
                    locosoft_fahrzeug_id, finanzierung_id, notizen, tageszulassung
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'aktiv',
                    %s, %s, %s, %s
                )
                RETURNING id
            """, (
                vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                fahrzeugart, betriebsnr, firma, anschaffungsdatum, ak, nd, afa_methode, afa_monatlich,
                locosoft_fahrzeug_id, finanzierung_id, notizen, tageszulassung
            ))
            new_id = cur.fetchone()[0]
            conn.commit()
        return jsonify({'ok': True, 'id': new_id, 'afa_monatlich': afa_monatlich})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# PUT /api/afa/fahrzeug/<id>
# =============================================================================

@afa_api.route('/api/afa/fahrzeug/<int:fk_id>', methods=['PUT'])
def fahrzeug_bearbeiten(fk_id):
    """Fahrzeug bearbeiten (nur Stammdaten; AfA neu berechnen)."""
    data = request.get_json() or {}
    # Erlaubte Felder
    updates = []
    params = []
    for key in ('vin', 'kennzeichen', 'fahrzeug_bezeichnung', 'marke', 'modell', 'fahrzeugart',
                'betriebsnr', 'firma', 'anschaffungsdatum', 'anschaffungskosten_netto',
                'nutzungsdauer_monate', 'afa_methode', 'locosoft_fahrzeug_id', 'finanzierung_id', 'notizen', 'tageszulassung'):
        if key not in data:
            continue
        val = data[key]
        if key == 'anschaffungsdatum' and isinstance(val, str):
            val = date.fromisoformat(val)
        if key == 'tageszulassung':
            val = bool(val) if val is not None else False
        if key in ('anschaffungskosten_netto', 'nutzungsdauer_monate'):
            val = float(val) if key == 'anschaffungskosten_netto' else int(val)
        if key in ('anschaffungskosten_netto', 'nutzungsdauer_monate') and key == 'anschaffungskosten_netto':
            pass
        updates.append(f"{key} = %s")
        params.append(val)
    if not updates:
        return jsonify({'ok': False, 'error': 'Keine Felder zum Aktualisieren'}), 400

    # AfA monatlich neu berechnen
    if 'anschaffungskosten_netto' in data or 'nutzungsdauer_monate' in data:
        ak = data.get('anschaffungskosten_netto')
        nd = data.get('nutzungsdauer_monate')
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT anschaffungskosten_netto, nutzungsdauer_monate FROM afa_anlagevermoegen WHERE id = %s", (fk_id,))
            row = cur.fetchone()
            if row:
                ak = ak if ak is not None else float(row[0])
                nd = nd if nd is not None else int(row[1])
                afa_monatlich = round(ak / nd, 2)
                updates.append("afa_monatlich = %s")
                params.append(afa_monatlich)
    params.append(fk_id)
    updates.append("aktualisiert_am = NOW()")

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE afa_anlagevermoegen SET " + ", ".join(updates) + " WHERE id = %s",
                params
            )
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'ok': False, 'error': 'Fahrzeug nicht gefunden'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# POST /api/afa/fahrzeug/<id>/abgang
# =============================================================================

@afa_api.route('/api/afa/fahrzeug/<int:fk_id>/abgang', methods=['POST'])
def fahrzeug_abgang(fk_id):
    """Verkauf oder Umbuchung durchführen; Restbuchwert und Buchgewinn/-verlust setzen."""
    data = request.get_json() or {}
    abgangsdatum = data.get('abgangsdatum')
    abgangsgrund = data.get('abgangsgrund', 'verkauf')
    verkaufspreis_netto = data.get('verkaufspreis_netto')

    if not abgangsdatum:
        return jsonify({'ok': False, 'error': 'abgangsdatum erforderlich'}), 400
    if isinstance(abgangsdatum, str):
        abgangsdatum = date.fromisoformat(abgangsdatum)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, anschaffungsdatum, anschaffungskosten_netto, nutzungsdauer_monate, afa_monatlich
                FROM afa_anlagevermoegen WHERE id = %s AND status = 'aktiv'
            """, (fk_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Fahrzeug nicht gefunden oder nicht aktiv'}), 404
            f = _fahrzeug_from_row(row, cur)
        rest = berechne_restbuchwert(f, abgangsdatum)
        buchgewinn_verlust = None
        if verkaufspreis_netto is not None:
            buchgewinn_verlust = round(float(verkaufspreis_netto) - (rest or 0), 2)

        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE afa_anlagevermoegen
                SET status = 'verkauft', abgangsdatum = %s, abgangsgrund = %s,
                    verkaufspreis_netto = %s, restbuchwert_abgang = %s, buchgewinn_verlust = %s,
                    aktualisiert_am = NOW()
                WHERE id = %s
            """, (abgangsdatum, abgangsgrund, verkaufspreis_netto, rest, buchgewinn_verlust, fk_id))
            conn.commit()
        ak = float(f.get('anschaffungskosten_netto') or 0)
        aufgelaufene_afa = round(ak - (rest or 0), 2) if rest is not None else None
        return jsonify({
            'ok': True,
            'restbuchwert_abgang': rest,
            'buchgewinn_verlust': buchgewinn_verlust,
            'aufgelaufene_afa': aufgelaufene_afa,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# POST /api/afa/berechne-monat
# =============================================================================

@afa_api.route('/api/afa/berechne-monat', methods=['POST'])
def berechne_monat():
    """Monatliche AfA für alle aktiven Fahrzeuge berechnen und in afa_buchungen schreiben."""
    data = request.get_json() or {}
    jahr = data.get('jahr', request.args.get('jahr', type=int))
    monat = data.get('monat', request.args.get('monat', type=int))
    ym = data.get('yyyy-mm') or request.args.get('yyyy-mm')
    if ym:
        parts = ym.split('-')
        if len(parts) == 2:
            jahr, monat = int(parts[0]), int(parts[1])
    if not jahr or not monat:
        heute = date.today()
        jahr, monat = heute.year, heute.month
    buchungsmonat = date(jahr, monat, 1)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, anschaffungsdatum, anschaffungskosten_netto, nutzungsdauer_monate, afa_methode, afa_monatlich
                FROM afa_anlagevermoegen
                WHERE status = 'aktiv'
                AND (tageszulassung IS NULL OR tageszulassung = false)
                AND anschaffungsdatum <= %s
                AND (abgangsdatum IS NULL OR abgangsdatum >= %s)
            """, (buchungsmonat, buchungsmonat))
            rows = cur.fetchall()
        fahrzeuge = [_fahrzeug_from_row(r, cur) for r in rows]
        inserted = 0
        with db_session() as conn:
            cur = conn.cursor()
            for f in fahrzeuge:
                if f.get('tageszulassung'):
                    continue
                afa = f.get('afa_monatlich') or berechne_monatliche_afa(f)
                if afa is None:
                    continue
                # Prüfen ob Buchung für diesen Monat schon existiert
                cur.execute(
                    "SELECT id FROM afa_buchungen WHERE anlage_id = %s AND buchungsmonat = %s",
                    (f['id'], buchungsmonat)
                )
                if cur.fetchone():
                    continue
                rest = berechne_restbuchwert(f, buchungsmonat)
                kumuliert = float(f['anschaffungskosten_netto']) - (rest or 0)
                cur.execute("""
                    INSERT INTO afa_buchungen (anlage_id, buchungsmonat, afa_betrag, restbuchwert, kumuliert, ist_anteilig)
                    VALUES (%s, %s, %s, %s, %s, false)
                """, (f['id'], buchungsmonat, afa, rest, round(kumuliert, 2)))
                inserted += 1
            conn.commit()
        return jsonify({
            'ok': True,
            'buchungsmonat': buchungsmonat.isoformat()[:7],
            'inserted': inserted,
            'anzahl_fahrzeuge': len(fahrzeuge),
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/abgangs-kontrolle
# =============================================================================

def get_abgangs_kontrolle_data():
    """
    Liefert Abgleich DRIVE vs. Locosoft (out_invoice_date).
    Für API und E-Mail-Report (send_afa_bestand_report).
    Returns: dict mit abgang_pruefen, abgang_drive_mit_locosoft
    """
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, status, abgangsdatum
            FROM afa_anlagevermoegen
            WHERE vin IS NOT NULL AND TRIM(vin) != ''
            ORDER BY status ASC, abgangsdatum DESC NULLS LAST
        """)
        rows = cur.fetchall()
    portal = rows_to_list(rows, cur) if cur else []
    vins = [r['vin'].strip() for r in portal if r.get('vin')]
    if not vins:
        return {'abgang_pruefen': [], 'abgang_drive_mit_locosoft': []}

    placeholders = ','.join(['%s'] * len(vins))
    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT v.vin, dv.out_invoice_date
            FROM vehicles v
            JOIN dealer_vehicles dv ON dv.vehicle_number = v.internal_number
                AND dv.dealer_vehicle_type = v.dealer_vehicle_type
                AND dv.dealer_vehicle_number = v.dealer_vehicle_number
            WHERE v.vin IN ({placeholders})
        """, vins)
        loco_rows = cur.fetchall()
    loco_map = {}
    for r in loco_rows:
        vin = (r[0] or '').strip()
        if vin:
            loco_map[vin] = r[1]  # out_invoice_date

    abgang_pruefen = []
    abgang_drive_mit_locosoft = []
    for p in portal:
        vin = (p.get('vin') or '').strip()
        if not vin:
            continue
        loco_inv = loco_map.get(vin)
        if p.get('status') == 'aktiv' and loco_inv:
            abgang_pruefen.append({
                'id': p.get('id'), 'vin': vin, 'kennzeichen': p.get('kennzeichen'),
                'fahrzeug_bezeichnung': p.get('fahrzeug_bezeichnung'),
                'locosoft_out_invoice_date': loco_inv.isoformat() if hasattr(loco_inv, 'isoformat') else str(loco_inv),
                'hinweis': 'In Locosoft als verkauft (Rechnungsdatum). Bitte Abgang in DRIVE prüfen.',
            })
        if p.get('status') == 'verkauft':
            abgang_drive_mit_locosoft.append({
                'id': p.get('id'), 'vin': vin, 'kennzeichen': p.get('kennzeichen'),
                'fahrzeug_bezeichnung': p.get('fahrzeug_bezeichnung'),
                'abgangsdatum': p.get('abgangsdatum').isoformat() if p.get('abgangsdatum') and hasattr(p['abgangsdatum'], 'isoformat') else str(p.get('abgangsdatum') or ''),
                'locosoft_out_invoice_date': loco_inv.isoformat() if loco_inv and hasattr(loco_inv, 'isoformat') else (str(loco_inv) if loco_inv else None),
            })
    return {'abgang_pruefen': abgang_pruefen, 'abgang_drive_mit_locosoft': abgang_drive_mit_locosoft}


@afa_api.route('/api/afa/abgangs-kontrolle', methods=['GET'])
def abgangs_kontrolle():
    """
    Kontrollreport: DRIVE vs. Locosoft (out_invoice_date).
    - Bitte prüfen: DRIVE status=aktiv, aber in Locosoft bereits verkauft (out_invoice_date gesetzt).
    - Abgang in DRIVE: Liste mit Locosoft-Verkaufsdatum zur Kontrolle.
    """
    try:
        data = get_abgangs_kontrolle_data()
        return jsonify({'ok': True, **data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/locosoft-kandidaten
# =============================================================================
# Fahrzeugfilter:
#   VFW = dealer_vehicle_type 'V' und nicht Mietwagen (is_rental_or_school_vehicle = false).
#   Mietwagen = (a) is_rental_or_school_vehicle = true mit eigene (Jw-Kz M)
#               (b) dealer_vehicle_type 'G' (Gebrauchtwagen) mit Jw-Kz M (Buchhaltung Mietwagen-Listen).
# EK-Formel: wie kalkulation_helpers + usage_value_encr_other - total_writedown.

def _locosoft_eigene_mietwagen_condition():
    """Bedingung für 'eigene Mietwagen': Jw-Kennzeichen (pre_owned_car_code) = 'M'."""
    return """(
                UPPER(TRIM(COALESCE(dv.pre_owned_car_code, ''))) = 'M'
            )"""

_LOCOSOFT_KANDIDATEN_SQL = """
    SELECT
        dv.dealer_vehicle_type,
        dv.dealer_vehicle_number,
        dv.vehicle_number AS internal_number,
        dv.in_arrival_date,
        dv.calc_basic_charge,
        dv.calc_accessory,
        dv.calc_extra_expenses,
        dv.calc_usage_value_encr_internal,
        dv.calc_usage_value_encr_external,
        dv.calc_usage_value_encr_other,
        dv.calc_total_writedown,
        dv.is_rental_or_school_vehicle,
        dv.pre_owned_car_code,
        COALESCE(dv.in_subsidiary, v.subsidiary, 1) AS subsidiary,
        v.vin,
        v.license_plate,
        dv.out_license_plate,
        v.first_registration_date,
        m.description AS model_description
    FROM dealer_vehicles dv
    LEFT JOIN vehicles v
        ON v.internal_number = dv.vehicle_number
        AND v.dealer_vehicle_type = dv.dealer_vehicle_type
        AND v.dealer_vehicle_number = dv.dealer_vehicle_number
    LEFT JOIN models m
        ON v.model_code = m.model_code
        AND v.make_number = m.make_number
    WHERE (
        (dv.dealer_vehicle_type = 'V' AND (dv.is_rental_or_school_vehicle IS NULL OR dv.is_rental_or_school_vehicle = false))
        OR (dv.is_rental_or_school_vehicle = true AND """ + _locosoft_eigene_mietwagen_condition() + """)
        OR (dv.dealer_vehicle_type = 'G' AND """ + _locosoft_eigene_mietwagen_condition() + """)
    )
    AND (dv.deactivated_date IS NULL AND dv.deactivated_by_employee_no IS NULL)
    AND (dv.out_invoice_date IS NULL)
    AND dv.vehicle_number IS NOT NULL
    ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number
"""


def get_locosoft_kandidaten_data():
    """
    Liefert VFW- und Mietwagen-Kandidaten aus Locosoft (noch nicht in AfA importiert).
    Für API und E-Mail-Report (send_afa_bestand_report).
    Returns: list of kandidaten dicts
    """
    with locosoft_session() as conn:
        cur = conn.cursor()
        cur.execute(_LOCOSOFT_KANDIDATEN_SQL)
        rows = cur.fetchall()
    raw = rows_to_list(rows, cur)

    # Bereits importierte VINs / Locosoft-IDs aus Portal
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT vin, locosoft_fahrzeug_id FROM afa_anlagevermoegen WHERE vin IS NOT NULL OR locosoft_fahrzeug_id IS NOT NULL")
        portal_rows = cur.fetchall()
    existing_vins = {row[0]: True for row in portal_rows if row and row[0]}
    existing_ids = {row[1]: True for row in portal_rows if row and row[1] is not None}

    kandidaten = []
    for r in raw:
        vin = (r.get('vin') or '').strip()
        internal_number = r.get('internal_number')
        if not vin and not internal_number:
            continue
        if vin and existing_vins.get(vin):
            continue
        if internal_number is not None and existing_ids.get(internal_number):
            continue

        ek = _ek_netto_from_locosoft_row(r)
        if ek <= 0:
            continue
        anschaffung = r.get('in_arrival_date') or r.get('first_registration_date')
        if isinstance(anschaffung, date):
            anschaffung = anschaffung.isoformat()
        elif anschaffung:
            anschaffung = str(anschaffung)[:10]

        subsidiary = r.get('subsidiary')
        if subsidiary is not None:
            betriebsnr = LOCOSOFT_SUBSIDIARY_TO_BETRIEBSNR.get(int(subsidiary), 1)
        else:
            betriebsnr = 1

        # Art: Mietwagen wenn is_rental_or_school_vehicle ODER Fz.-Art G mit Jw-Kz M (Buchhaltung)
        if r.get('is_rental_or_school_vehicle'):
            fahrzeugart = 'MIETWAGEN'
        elif (r.get('dealer_vehicle_type') or '').upper() == 'G':
            jw = (r.get('pre_owned_car_code') or '').strip().upper()
            if jw == 'M':
                fahrzeugart = 'MIETWAGEN'
            else:
                fahrzeugart = 'VFW'
        else:
            fahrzeugart = 'VFW'

        kandidaten.append({
            'dealer_vehicle_type': r.get('dealer_vehicle_type'),
            'dealer_vehicle_number': r.get('dealer_vehicle_number'),
            'internal_number': internal_number,
            'vin': vin,
            'kennzeichen': (r.get('license_plate') or r.get('out_license_plate') or '').strip(),
            'fahrzeug_bezeichnung': (r.get('model_description') or '').strip() or None,
            'fahrzeugart': fahrzeugart,
            'anschaffungsdatum': anschaffung,
            'anschaffungskosten_netto': ek,
            'betriebsnr': betriebsnr,
        })
    return kandidaten


@afa_api.route('/api/afa/locosoft-kandidaten', methods=['GET'])
def locosoft_kandidaten():
    """
    Liefert VFW- und Mietwagen-Kandidaten aus Locosoft (noch nicht in AfA importiert).
    Filter: V = Vorführwagen, is_rental_or_school_vehicle = Mietwagen; aktiv (nicht deaktiviert).
    EK = Einsatzwert-Formel inkl. Einsatzerhöhung interne/externe/other - Abschreibung.
    """
    try:
        kandidaten = get_locosoft_kandidaten_data()
        return jsonify({'ok': True, 'kandidaten': kandidaten})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# GET /api/afa/locosoft-fahrzeug-detail
# =============================================================================

@afa_api.route('/api/afa/locosoft-fahrzeug-detail', methods=['GET'])
def locosoft_fahrzeug_detail():
    """
    Einzelnes Fahrzeug aus Locosoft mit allen verfügbaren Feldern (für Detail-Modal).
    Query: dealer_vehicle_type, dealer_vehicle_number.
    """
    dtype = (request.args.get('dealer_vehicle_type') or '').strip().upper()
    dnum = request.args.get('dealer_vehicle_number', type=int)
    if not dtype or dnum is None:
        return jsonify({'ok': False, 'error': 'dealer_vehicle_type und dealer_vehicle_number erforderlich'}), 400
    try:
        sql_one = _LOCOSOFT_KANDIDATEN_SQL.replace(
            "ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number",
            "AND dv.dealer_vehicle_type = %s AND dv.dealer_vehicle_number = %s ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number"
        )
        with locosoft_session() as conn:
            cur = conn.cursor()
            cur.execute(sql_one, (dtype, dnum))
            row = cur.fetchone()
            if not row:
                return jsonify({'ok': False, 'error': 'Fahrzeug in Locosoft nicht gefunden'}), 404
            r = row_to_dict(row, cur)

        def _fmt(v):
            if v is None:
                return None
            if hasattr(v, 'isoformat'):
                return v.isoformat()[:10] if hasattr(v, 'date') else str(v)
            if isinstance(v, Decimal):
                return float(v)
            return str(v)

        detail = {
            'identifikation': {
                'vin': _fmt(r.get('vin')),
                'kennzeichen': _fmt(r.get('license_plate')),
                'out_license_plate': _fmt(r.get('out_license_plate')),
                'dealer_vehicle_type': _fmt(r.get('dealer_vehicle_type')),
                'dealer_vehicle_number': _fmt(r.get('dealer_vehicle_number')),
                'internal_number': _fmt(r.get('internal_number')),
            },
            'fahrzeug': {
                'model_description': _fmt(r.get('model_description')),
                'first_registration_date': _fmt(r.get('first_registration_date')),
            },
            'kalkulation': {
                'in_arrival_date': _fmt(r.get('in_arrival_date')),
                'calc_basic_charge': _fmt(r.get('calc_basic_charge')),
                'calc_accessory': _fmt(r.get('calc_accessory')),
                'calc_extra_expenses': _fmt(r.get('calc_extra_expenses')),
                'calc_usage_value_encr_internal': _fmt(r.get('calc_usage_value_encr_internal')),
                'calc_usage_value_encr_external': _fmt(r.get('calc_usage_value_encr_external')),
                'calc_usage_value_encr_other': _fmt(r.get('calc_usage_value_encr_other')),
                'calc_total_writedown': _fmt(r.get('calc_total_writedown')),
            },
            'sonstiges': {
                'is_rental_or_school_vehicle': r.get('is_rental_or_school_vehicle'),
                'pre_owned_car_code': _fmt(r.get('pre_owned_car_code')),
                'subsidiary': _fmt(r.get('subsidiary')),
            },
        }
        ek = _ek_netto_from_locosoft_row(r)
        detail['ek_netto_berechnet'] = round(float(ek), 2) if ek else None
        return jsonify({'ok': True, 'detail': detail})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# =============================================================================
# POST /api/afa/import-locosoft
# =============================================================================

@afa_api.route('/api/afa/import-locosoft', methods=['POST'])
def import_locosoft():
    """
    Importiert ein oder mehrere Fahrzeuge aus Locosoft in afa_anlagevermoegen.
    Body: { "items": [ { "dealer_vehicle_type": "V", "dealer_vehicle_number": 111454 } ] }
    Holt Daten aus Locosoft, berechnet EK mit Formel, legt AfA-Datensatz an.
    """
    data = request.get_json() or {}
    items = data.get('items') or []
    if not items:
        return jsonify({'ok': False, 'error': 'items (Liste mit dealer_vehicle_type, dealer_vehicle_number) erforderlich'}), 400

    nutzungsdauer_monate = int(data.get('nutzungsdauer_monate', 72))
    importierte = []
    fehler = []

    for item in items:
        dtype = (item.get('dealer_vehicle_type') or '').strip().upper() or 'V'
        dnum = item.get('dealer_vehicle_number')
        if dnum is None:
            fehler.append({'item': item, 'error': 'dealer_vehicle_number fehlt'})
            continue
        try:
            dnum = int(dnum)
        except (TypeError, ValueError):
            fehler.append({'item': item, 'error': 'dealer_vehicle_number ungültig'})
            continue

        try:
            with locosoft_session() as conn:
                cur = conn.cursor()
                sql_one = _LOCOSOFT_KANDIDATEN_SQL.replace(
                    "ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number",
                    "AND dv.dealer_vehicle_type = %s AND dv.dealer_vehicle_number = %s ORDER BY dv.dealer_vehicle_type, dv.dealer_vehicle_number"
                )
                cur.execute(sql_one, (dtype, dnum))
                row = cur.fetchone()
                if not row:
                    fehler.append({'item': item, 'error': 'Fahrzeug in Locosoft nicht gefunden oder kein VFW/Mietwagen'})
                    continue
                r = row_to_dict(row, cur)

            # Bereits importiert?
            vin = (r.get('vin') or '').strip()
            internal_number = r.get('internal_number')
            with db_session() as conn:
                cur = conn.cursor()
                if vin:
                    cur.execute("SELECT id FROM afa_anlagevermoegen WHERE vin = %s", (vin,))
                else:
                    cur.execute("SELECT id FROM afa_anlagevermoegen WHERE locosoft_fahrzeug_id = %s", (internal_number,))
                if cur.fetchone():
                    fehler.append({'item': item, 'error': 'Bereits in AfA importiert'})
                    continue

            ek = _ek_netto_from_locosoft_row(r)
            if ek <= 0:
                fehler.append({'item': item, 'error': 'Einsatzwert <= 0'})
                continue

            anschaffung = r.get('in_arrival_date') or r.get('first_registration_date')
            if not anschaffung:
                fehler.append({'item': item, 'error': 'Anschaffungsdatum fehlt in Locosoft'})
                continue
            if isinstance(anschaffung, str):
                anschaffung = date.fromisoformat(anschaffung[:10])

            subsidiary = r.get('subsidiary')
            betriebsnr = LOCOSOFT_SUBSIDIARY_TO_BETRIEBSNR.get(int(subsidiary), 1) if subsidiary is not None else 1
            # Art wie in Kandidaten: Mietwagen bei is_rental ODER Typ G mit Jw-Kz M (Buchhaltung)
            if r.get('is_rental_or_school_vehicle'):
                fahrzeugart = 'MIETWAGEN'
            elif (r.get('dealer_vehicle_type') or '').upper() == 'G':
                jw = (r.get('pre_owned_car_code') or '').strip().upper()
                fahrzeugart = 'MIETWAGEN' if (jw == 'M') else 'VFW'
            else:
                fahrzeugart = 'VFW'
            afa_monatlich = round(ek / nutzungsdauer_monate, 2)

            with db_session() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO afa_anlagevermoegen (
                        vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                        fahrzeugart, betriebsnr, firma, anschaffungsdatum, anschaffungskosten_netto,
                        nutzungsdauer_monate, afa_methode, afa_monatlich, status,
                        locosoft_fahrzeug_id, notizen
                    ) VALUES (
                        %s, %s, %s, NULL, NULL, %s, %s, NULL, %s, %s, %s, 'linear', %s, 'aktiv',
                        %s, 'Import Locosoft'
                    )
                    RETURNING id
                """, (
                    vin or None,
                    (r.get('license_plate') or '').strip() or None,
                    (r.get('model_description') or '').strip() or None,
                    fahrzeugart, betriebsnr, anschaffung, ek, nutzungsdauer_monate, afa_monatlich,
                    internal_number
                ))
                new_id = cur.fetchone()[0]
                conn.commit()
            importierte.append({'dealer_vehicle_type': dtype, 'dealer_vehicle_number': dnum, 'id': new_id})
        except Exception as e:
            fehler.append({'item': item, 'error': str(e)})

    return jsonify({
        'ok': True,
        'importiert': len(importierte),
        'importierte': importierte,
        'fehler': fehler,
    })


# =============================================================================
# GET /api/afa/health
# =============================================================================

@afa_api.route('/api/afa/health', methods=['GET'])
def health():
    """Health-Check: Tabellen vorhanden, Verbindung OK."""
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM afa_anlagevermoegen")
            n = cur.fetchone()[0]
        return jsonify({'ok': True, 'status': 'ok', 'anzahl_fahrzeuge': n})
    except Exception as e:
        return jsonify({'ok': False, 'status': 'error', 'error': str(e)}), 500
