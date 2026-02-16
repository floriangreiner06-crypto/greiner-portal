"""
AfA-Modul API — Vorführwagen und Mietwagen (Anlagevermögen)
============================================================
Monatliche Abschreibung (AfA) linear, 72 Monate, monatsgenau.
Erstellt: 2026-02-16 | Workstream: Controlling
"""

from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from flask import Blueprint, jsonify, request

from api.db_utils import db_session, row_to_dict, rows_to_list

afa_api = Blueprint('afa_api', __name__)


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
    if d.get('afa_monatlich') is None and d.get('anschaffungskosten_netto') and d.get('nutzungsdauer_monate'):
        d['afa_monatlich'] = berechne_monatliche_afa(d)
    return d


# =============================================================================
# GET /api/afa/dashboard
# =============================================================================

@afa_api.route('/api/afa/dashboard', methods=['GET'])
def dashboard():
    """Übersicht: Aktive VFW/Mietwagen, Gesamt-AfA/Monat, Restbuchwerte."""
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                       fahrzeugart, betriebsnr, firma, anschaffungsdatum, anschaffungskosten_netto,
                       nutzungsdauer_monate, afa_methode, afa_monatlich, status, abgangsdatum,
                       restbuchwert_abgang, buchgewinn_verlust
                FROM afa_anlagevermoegen
                ORDER BY status ASC, anschaffungsdatum DESC
            """)
            rows = cur.fetchall()
        fahrzeuge = [_fahrzeug_from_row(r, cur) for r in rows]

        heute = date.today()
        aktive = [f for f in fahrzeuge if f.get('status') == 'aktiv']
        summe_restbuchwert = 0
        summe_afa_monat = 0
        halte_monate_list = []
        for f in fahrzeuge:
            if f.get('status') == 'aktiv':
                rw = berechne_restbuchwert(f, heute)
                f['restbuchwert_aktuell'] = rw
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
            'kpis': {
                'anzahl_aktive_vfw': sum(1 for f in aktive if f.get('fahrzeugart') == 'VFW'),
                'anzahl_aktive_mietwagen': sum(1 for f in aktive if f.get('fahrzeugart') == 'MIETWAGEN'),
                'anzahl_aktiv': len(aktive),
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
               abgangsgrund, restbuchwert_abgang, buchgewinn_verlust
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
        from datetime import date
        heute = date.today()
        jahr, monat = heute.year, heute.month
    buchungsmonat = date(jahr, monat, 1)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, vin, kennzeichen, fahrzeug_bezeichnung, marke, modell, fahrzeugart,
                       betriebsnr, anschaffungsdatum, anschaffungskosten_netto, nutzungsdauer_monate,
                       afa_methode, afa_monatlich, status, abgangsdatum
                FROM afa_anlagevermoegen
                WHERE status = 'aktiv'
                AND anschaffungsdatum <= %s
                AND (abgangsdatum IS NULL OR abgangsdatum >= %s)
            """, (buchungsmonat, buchungsmonat))
            rows = cur.fetchall()
        aktive = [_fahrzeug_from_row(r, cur) for r in rows]

        positionen = []
        summe = 0
        for f in aktive:
            afa = f.get('afa_monatlich') or berechne_monatliche_afa(f)
            if afa is None:
                continue
            rest = berechne_restbuchwert(f, buchungsmonat)
            positionen.append({
                'anlage_id': f['id'],
                'kennzeichen': f.get('kennzeichen'),
                'fahrzeug_bezeichnung': f.get('fahrzeug_bezeichnung'),
                'fahrzeugart': f.get('fahrzeugart'),
                'afa_betrag': afa,
                'restbuchwert': rest,
            })
            summe += afa

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
        if resp[1] != 200:
            return resp
        data = resp[0].get_json()
        if not data.get('ok'):
            return jsonify(data), 500
        positionen = data.get('positionen', [])
        summe = data.get('summe_afa', 0)
        return jsonify({
            'ok': True,
            'buchungsmonat': data['buchungsmonat'],
            'positionen': positionen,
            'summe_afa': summe,
            'export_csv_zeilen': [
                ['Kennzeichen', 'Bezeichnung', 'Art', 'AfA-Betrag'],
                *[[p.get('kennzeichen'), p.get('fahrzeug_bezeichnung'), p.get('fahrzeugart'), p.get('afa_betrag')] for p in positionen],
                ['', '', 'Summe', summe],
            ],
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
                    locosoft_fahrzeug_id, finanzierung_id, notizen
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'aktiv',
                    %s, %s, %s
                )
                RETURNING id
            """, (
                vin, kennzeichen, fahrzeug_bezeichnung, marke, modell,
                fahrzeugart, betriebsnr, firma, anschaffungsdatum, ak, nd, afa_methode, afa_monatlich,
                locosoft_fahrzeug_id, finanzierung_id, notizen
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
                'nutzungsdauer_monate', 'afa_methode', 'locosoft_fahrzeug_id', 'finanzierung_id', 'notizen'):
        if key not in data:
            continue
        val = data[key]
        if key == 'anschaffungsdatum' and isinstance(val, str):
            val = date.fromisoformat(val)
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
        return jsonify({
            'ok': True,
            'restbuchwert_abgang': rest,
            'buchgewinn_verlust': buchgewinn_verlust,
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
                AND anschaffungsdatum <= %s
                AND (abgangsdatum IS NULL OR abgangsdatum >= %s)
            """, (buchungsmonat, buchungsmonat))
            rows = cur.fetchall()
        fahrzeuge = [_fahrzeug_from_row(r, cur) for r in rows]
        inserted = 0
        with db_session() as conn:
            cur = conn.cursor()
            for f in fahrzeuge:
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
