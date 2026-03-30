"""
Provisionsmodul – REST-API.
Live-Preview nutzt ausschließlich provision_service (SSOT).
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from api.provision_service import berechne_live_provision, create_vorlauf, delete_vorlauf, get_dashboard_daten, get_lauf_detail
from api.db_utils import db_session, rows_to_list

provision_api = Blueprint('provision_api', __name__, url_prefix='/api/provision')


def _get_vkb_for_request():
    """
    Ermittelt VKB des aktuellen Users (über ldap_employee_mapping → employees.locosoft_id).
    SSOT: gleiche Logik wie Urlaubsplaner (vacation_api.get_employee_from_session).
    """
    from api.vacation_api import get_employee_from_session
    _employee_id, _ldap_user, employee_data = get_employee_from_session()
    if employee_data and employee_data.get('locosoft_id') is not None:
        return int(employee_data['locosoft_id'])
    return None


# Provision-Vollzugriff: NUR diese 3 Personen dürfen das Dashboard, alle Läufe,
# und Bearbeitungsfunktionen nutzen. Andere Admins (z.B. IT) haben KEINEN Zugriff.
_PROVISION_VOLLZUGRIFF_USERS = {
    'florian.greiner@auto-greiner.de',
    'peter.greiner@auto-greiner.de',
    'vanessa.groll@auto-greiner.de',
}


def _has_provision_vollzugriff():
    """Nur Florian Greiner, Peter Greiner und Vanessa Groll haben Vollzugriff auf Provisionen."""
    if not current_user.is_authenticated:
        return False
    username = getattr(current_user, 'username', '') or ''
    return username.lower() in _PROVISION_VOLLZUGRIFF_USERS


def _may_see_all_verkaufer():
    """Nur Provision-Vollzugriff-User dürfen alle Verkäufer sehen."""
    return _has_provision_vollzugriff()


def _get_portal_role():
    """Portal-Rolle des aktuellen Users (portal_role_override > portal_role)."""
    return (getattr(current_user, 'portal_role_override', '') or
            getattr(current_user, 'portal_role', '') or '')


def _may_endlauf():
    """Nur Provision-Vollzugriff-User dürfen Endlauf setzen."""
    return _has_provision_vollzugriff()


def _may_download_pdf_any():
    """Provision-Vollzugriff-User dürfen alle PDFs laden.
    Verkäufer dürfen nur eigene Läufe (VKB-Check separat)."""
    return _has_provision_vollzugriff()


def _may_manage_config():
    """Nur Provision-Vollzugriff-User dürfen Provisionsarten verwalten."""
    return _has_provision_vollzugriff()


@provision_api.route('/live-preview', methods=['GET'])
@login_required
def live_preview():
    """
    GET /api/provision/live-preview?monat=YYYY-MM&verkaufer_id=<optional>
    Berechnung aus sales + provision_config (kein DB-Write).
    Verkäufer: nur eigene VKB. VKL/Admin: verkaufer_id optional.
    """
    monat = request.args.get('monat')
    if not monat or len(monat) != 7 or monat[4] != '-':
        return jsonify({'success': False, 'error': 'Parameter monat (YYYY-MM) fehlt oder ungültig'}), 400

    verkaufer_id_param = request.args.get('verkaufer_id', type=int)
    vkb = None

    if verkaufer_id_param is not None and _may_see_all_verkaufer():
        vkb = verkaufer_id_param
        is_own = False
    else:
        vkb = _get_vkb_for_request()
        if vkb is None:
            return jsonify({
                'success': False,
                'error': 'Kein Verkäufer (VKB) zu Ihrem Benutzer zugeordnet. Bitte prüfen Sie ldap_employee_mapping / employees.locosoft_id.'
            }), 403
        is_own = True

    # Bei eigener Ansicht: prüfen ob Provision für diesen MA deaktiviert ist
    if is_own:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(provision_aktiv, true) FROM employees WHERE locosoft_id = %s LIMIT 1",
                (vkb,)
            )
            row = cur.fetchone()
        if row is not None and row[0] is False:
            return jsonify({
                'success': True,
                'provision_deaktiviert': True,
                'message': 'Für Sie wird keine Provisionsabrechnung durchgeführt (z. B. Verkaufsleitung / Geschäftsführung).',
            })

    try:
        result = berechne_live_provision(vkb, monat)
        result['success'] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@provision_api.route('/vorlauf-erstellen', methods=['POST'])
@login_required
def vorlauf_erstellen():
    """
    POST /api/provision/vorlauf-erstellen
    Body: { "verkaufer_id": 2007, "monat": "2026-01" }
    Nur VKL/Admin. Erstellt provision_laeufe + positionen, optional PDF.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen einen Vorlauf erstellen.'}), 403
    data = request.get_json() or {}
    vkb = data.get('verkaufer_id')
    monat = data.get('monat')
    if vkb is None or not monat or len(monat) != 7 or monat[4] != '-':
        return jsonify({'success': False, 'error': 'verkaufer_id und monat (YYYY-MM) erforderlich'}), 400
    try:
        vkb = int(vkb)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'verkaufer_id muss eine Zahl sein'}), 400
    erstellt_von = getattr(current_user, 'username', None) or getattr(current_user, 'display_name', '') or 'system'
    result = create_vorlauf(vkb, monat, erstellt_von)
    if result.get('error') and not result.get('lauf_id'):
        return jsonify({'success': False, 'error': result['error']}), 400
    return jsonify({
        'success': True,
        'lauf_id': result['lauf_id'],
        'pdf_vorlauf': result.get('pdf_vorlauf'),
        'message': 'Vorlauf erstellt.' if not result.get('error') else result['error'],
    })


@provision_api.route('/vorlauf/<int:lauf_id>/loeschen', methods=['POST', 'DELETE'])
@login_required
def vorlauf_loeschen(lauf_id):
    """
    POST/DELETE /api/provision/vorlauf/<id>/loeschen
    Löscht einen Vorlauf (nur Status VORLAUF). Nur VKL/Admin.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen einen Vorlauf löschen.'}), 403
    result = delete_vorlauf(lauf_id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Unbekannter Fehler')}), 400
    return jsonify({'success': True, 'message': 'Vorlauf gelöscht.'})


@provision_api.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """GET /api/provision/dashboard?monat=YYYY-MM – Nur VKL/Admin."""
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin'}), 403
    monat = request.args.get('monat')
    if not monat or len(monat) != 7 or monat[4] != '-':
        from datetime import datetime
        monat = datetime.now().strftime('%Y-%m')
    try:
        data = get_dashboard_daten(monat)
        data['success'] = True
        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@provision_api.route('/lauf/<int:lauf_id>', methods=['GET'])
@login_required
def lauf_detail(lauf_id):
    """GET /api/provision/lauf/<id> – Lauf inkl. Positionen. Verkäufer nur eigener Lauf."""
    data = get_lauf_detail(lauf_id)
    if not data:
        return jsonify({'success': False, 'error': 'Lauf nicht gefunden'}), 404
    vkb = data['lauf'].get('verkaufer_id')
    my_vkb = _get_vkb_for_request()
    if not _may_see_all_verkaufer() and my_vkb != vkb:
        return jsonify({'success': False, 'error': 'Kein Zugriff'}), 403
    data['success'] = True
    if _may_see_all_verkaufer():
        from api.provision_service import get_aktive_verkaeufer
        data['aktive_verkaeufer'] = get_aktive_verkaeufer()
    # Config-Regeln (Min/Max) pro Kategorie mitliefern für Frontend-Clamping
    monat = data['lauf'].get('abrechnungsmonat') or ''
    if monat and len(monat) == 7:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT kategorie, min_betrag, max_betrag
                FROM provision_config
                WHERE gueltig_ab <= %s AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
            """, (monat + '-01', monat + '-01'))
            cfg_rows = cur.fetchall()
            data['config_limits'] = {r['kategorie']: {'min_betrag': float(r['min_betrag']) if r['min_betrag'] is not None else None, 'max_betrag': float(r['max_betrag']) if r['max_betrag'] is not None else None} for r in cfg_rows}
    return jsonify(data)


# =============================================================================
# Endlauf, Position bearbeiten/löschen
# =============================================================================

def _recalc_lauf_sums(cursor, lauf_id):
    """Summen in provision_laeufe aus Positionen + Zusatzleistungen neu berechnen."""
    cursor.execute("""
        UPDATE provision_laeufe SET
            summe_kat_i   = COALESCE((SELECT SUM(provision_final) FROM provision_positionen WHERE lauf_id = %s AND kategorie = 'I_neuwagen'), 0),
            summe_kat_ii  = COALESCE((SELECT SUM(provision_final) FROM provision_positionen WHERE lauf_id = %s AND kategorie = 'II_testwagen'), 0),
            summe_kat_iii = COALESCE((SELECT SUM(provision_final) FROM provision_positionen WHERE lauf_id = %s AND kategorie = 'III_gebrauchtwagen'), 0),
            summe_kat_iv  = COALESCE((SELECT SUM(provision_final) FROM provision_positionen WHERE lauf_id = %s AND kategorie = 'IV_gw_bestand'), 0),
            summe_kat_v   = COALESCE((SELECT SUM(provision_verkaufer) FROM provision_zusatzleistungen WHERE lauf_id = %s), 0),
            summe_gesamt  = COALESCE((SELECT SUM(provision_final) FROM provision_positionen WHERE lauf_id = %s), 0)
                          + COALESCE((SELECT SUM(provision_verkaufer) FROM provision_zusatzleistungen WHERE lauf_id = %s), 0)
                          + COALESCE(summe_stueckpraemie, 0),
            aktualisiert_am = NOW()
        WHERE id = %s
    """, (lauf_id, lauf_id, lauf_id, lauf_id, lauf_id, lauf_id, lauf_id, lauf_id))


@provision_api.route('/vorlauf/<int:lauf_id>/endlauf', methods=['POST'])
@login_required
def endlauf_setzen(lauf_id):
    """
    POST /api/provision/vorlauf/<id>/endlauf
    Setzt Status FREIGEGEBEN → ENDLAUF. Nur Buchhaltung/Personalbüro/Admin.
    Belegnummer: VK{verkaufer_id}-{YYYY}-{MM}
    Optional im Body: summe_gesamt, summe_kat_i–v (Korrekturwerte).
    """
    if not _may_endlauf():
        return jsonify({'success': False, 'error': 'Keine Berechtigung für Endlauf.'}), 403

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, verkaufer_id, abrechnungsmonat, status
            FROM provision_laeufe WHERE id = %s
        """, (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404

        status = (lauf['status'] or '').upper()
        if status == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Lauf ist bereits Endlauf (gesperrt).'}), 403
        if status != 'FREIGEGEBEN':
            return jsonify({'success': False, 'error': f'Endlauf nur aus Status FREIGEGEBEN möglich (aktuell: {status}).'}), 400

        vkb = lauf['verkaufer_id']
        monat = lauf['abrechnungsmonat'] or ''
        belegnummer = f"VK{vkb}-{monat}"

        endlauf_von = getattr(current_user, 'username', None) or getattr(current_user, 'display_name', '') or 'system'

        # Optionale Korrekturwerte aus Body
        data = request.get_json(silent=True) or {}
        extra_sets = []
        extra_params = []
        for field in ('summe_gesamt', 'summe_kat_i', 'summe_kat_ii', 'summe_kat_iii', 'summe_kat_iv', 'summe_kat_v'):
            if field in data and data[field] is not None:
                try:
                    extra_sets.append(f"{field} = %s")
                    extra_params.append(float(data[field]))
                except (TypeError, ValueError):
                    pass

        extra_sql = (", " + ", ".join(extra_sets)) if extra_sets else ""

        cur.execute(f"""
            UPDATE provision_laeufe SET
                status = 'ENDLAUF',
                endlauf_am = NOW() AT TIME ZONE 'Europe/Berlin',
                endlauf_von = %s,
                belegnummer = %s
                {extra_sql}
            WHERE id = %s
        """, [endlauf_von, belegnummer] + extra_params + [lauf_id])
        conn.commit()

    # PDF generieren (Endlauf)
    try:
        from api.provision_pdf import generate_provision_pdf
        pdf_rel = generate_provision_pdf(lauf_id, typ='endlauf')
        if pdf_rel:
            with db_session() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE provision_laeufe SET pdf_endlauf = %s WHERE id = %s", (pdf_rel, lauf_id))
                conn.commit()
    except Exception:
        pdf_rel = None

    return jsonify({
        'success': True,
        'belegnummer': belegnummer,
        'pdf_endlauf': pdf_rel,
        'message': f'Endlauf erstellt. Belegnummer: {belegnummer}'
    })


@provision_api.route('/position/<int:pos_id>/bearbeiten', methods=['POST'])
@login_required
def position_bearbeiten(pos_id):
    """
    POST /api/provision/position/<id>/bearbeiten
    Body: { "provision_final": 123.45, "provisionssatz": 0.009, "bemessungsgrundlage": 28500.0 }
    Alle Felder optional — nur übergebene Felder werden aktualisiert.
    Nur VKL/Admin. Nicht bei Status ENDLAUF.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Positionen bearbeiten.'}), 403

    data = request.get_json() or {}

    # Mindestens ein Feld muss übergeben werden
    editable_fields = ('provision_final', 'provisionssatz', 'bemessungsgrundlage')
    updates = {}
    for field in editable_fields:
        if field in data and data[field] is not None:
            try:
                updates[field] = float(data[field])
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': f'{field} muss eine Zahl sein.'}), 400

    if not updates:
        return jsonify({'success': False, 'error': 'Mindestens ein Feld (provision_final, provisionssatz, bemessungsgrundlage) ist erforderlich.'}), 400

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.lauf_id, p.kategorie, p.bemessungsgrundlage, p.provisionssatz,
                   l.status, l.abrechnungsmonat
            FROM provision_positionen p
            JOIN provision_laeufe l ON l.id = p.lauf_id
            WHERE p.id = %s
        """, (pos_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Position nicht gefunden.'}), 404
        if (row['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt – keine Änderungen möglich.'}), 403

        lauf_id = row['lauf_id']
        kategorie = row['kategorie']
        monat = row['abrechnungsmonat'] or ''

        # Min/Max aus provision_config laden und auf provision_final anwenden
        if 'provisionssatz' in updates or 'bemessungsgrundlage' in updates or 'provision_final' in updates:
            bem = updates.get('bemessungsgrundlage', float(row['bemessungsgrundlage'] or 0))
            satz = updates.get('provisionssatz', float(row['provisionssatz'] or 0))
            berechnet = round(bem * satz, 2)

            # Config-Limits laden
            min_betrag = None
            max_betrag = None
            if monat and len(monat) == 7:
                cur.execute("""
                    SELECT min_betrag, max_betrag FROM provision_config
                    WHERE kategorie = %s AND gueltig_ab <= %s
                      AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
                    LIMIT 1
                """, (kategorie, monat + '-01', monat + '-01'))
                cfg = cur.fetchone()
                if cfg:
                    min_betrag = float(cfg['min_betrag']) if cfg['min_betrag'] is not None else None
                    max_betrag = float(cfg['max_betrag']) if cfg['max_betrag'] is not None else None

            # Clamping: provision_final auf Min/Max begrenzen
            prov_final = updates.get('provision_final', berechnet)
            if max_betrag is not None and prov_final > max_betrag:
                prov_final = max_betrag
            if min_betrag is not None and prov_final < min_betrag and prov_final > 0:
                prov_final = min_betrag
            updates['provision_final'] = round(prov_final, 2)
            updates['provision_berechnet'] = berechnet

        set_parts = [f"{k} = %s" for k in updates]
        vals = list(updates.values())
        cur.execute(f"UPDATE provision_positionen SET {', '.join(set_parts)} WHERE id = %s", vals + [pos_id])
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'message': 'Position aktualisiert.', 'provision_final': updates.get('provision_final')})


@provision_api.route('/position/<int:pos_id>/loeschen', methods=['POST', 'DELETE'])
@login_required
def position_loeschen(pos_id):
    """
    POST/DELETE /api/provision/position/<id>/loeschen
    Nur VKL/Admin. Nicht bei Status ENDLAUF.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Positionen löschen.'}), 403

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.lauf_id, l.status
            FROM provision_positionen p
            JOIN provision_laeufe l ON l.id = p.lauf_id
            WHERE p.id = %s
        """, (pos_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Position nicht gefunden.'}), 404
        if (row['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt – keine Änderungen möglich.'}), 403

        lauf_id = row['lauf_id']
        cur.execute("DELETE FROM provision_positionen WHERE id = %s", (pos_id,))
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'message': 'Position gelöscht.'})


@provision_api.route('/position/<int:pos_id>/reassign-einkaeufer', methods=['POST'])
@login_required
def position_reassign_einkaeufer(pos_id):
    """
    POST /api/provision/position/<id>/reassign-einkaeufer
    Body: { "neuer_einkaeufer_id": 2008 }
    Verschiebt eine GW-aus-Bestand-Position zu einem anderen Verkäufer.
    Nur VKL/Admin. Nicht bei ENDLAUF.
    Voraussetzung: Ziel-Verkäufer hat bereits einen Vorlauf für denselben Monat.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Einkäufer umzuweisen.'}), 403

    data = request.get_json() or {}
    neuer_einkaeufer_id = data.get('neuer_einkaeufer_id')
    if neuer_einkaeufer_id is None:
        return jsonify({'success': False, 'error': 'neuer_einkaeufer_id ist erforderlich.'}), 400
    try:
        neuer_einkaeufer_id = int(neuer_einkaeufer_id)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'neuer_einkaeufer_id muss eine Zahl sein.'}), 400

    with db_session() as conn:
        cur = conn.cursor()

        # 1. Position + aktueller Lauf laden
        cur.execute("""
            SELECT p.id, p.lauf_id, p.kategorie, p.einkaeufer_name,
                   l.status, l.verkaufer_id, l.abrechnungsmonat
            FROM provision_positionen p
            JOIN provision_laeufe l ON l.id = p.lauf_id
            WHERE p.id = %s
        """, (pos_id,))
        pos = cur.fetchone()
        if not pos:
            return jsonify({'success': False, 'error': 'Position nicht gefunden.'}), 404
        if (pos['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt – keine Änderungen möglich.'}), 403
        if pos['kategorie'] != 'IV_gw_bestand':
            return jsonify({'success': False, 'error': 'Einkäufer-Umzuweisung nur für Kategorie IV (GW aus Bestand).'}), 400

        alter_lauf_id = pos['lauf_id']
        monat = pos['abrechnungsmonat']

        # 2. Ziel-Lauf des neuen Einkäufers finden
        cur.execute("""
            SELECT id, status FROM provision_laeufe
            WHERE verkaufer_id = %s AND abrechnungsmonat = %s
        """, (neuer_einkaeufer_id, monat))
        ziel_lauf = cur.fetchone()
        if not ziel_lauf:
            return jsonify({
                'success': False,
                'error': f'Kein Vorlauf für Verkäufer {neuer_einkaeufer_id} im Monat {monat} vorhanden. Bitte erst einen Vorlauf erstellen.'
            }), 400
        if (ziel_lauf['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Der Ziel-Lauf ist bereits Endlauf (gesperrt).'}), 403

        ziel_lauf_id = ziel_lauf['id']

        # 3. Neuen Einkäufer-Namen ermitteln
        cur.execute("""
            SELECT TRIM(BOTH ' ' FROM COALESCE(TRIM(first_name), '') || ' ' || COALESCE(TRIM(last_name), '')) AS name
            FROM employees WHERE locosoft_id = %s
        """, (neuer_einkaeufer_id,))
        emp = cur.fetchone()
        neuer_name = (emp['name'] if emp else f'VKB {neuer_einkaeufer_id}').strip()

        # 4. Position verschieben: lauf_id ändern + einkaeufer_name aktualisieren
        cur.execute("""
            UPDATE provision_positionen
            SET lauf_id = %s, einkaeufer_name = %s
            WHERE id = %s
        """, (ziel_lauf_id, neuer_name, pos_id))

        # 5. Summen beider Läufe neu berechnen
        _recalc_lauf_sums(cur, alter_lauf_id)
        _recalc_lauf_sums(cur, ziel_lauf_id)
        conn.commit()

    return jsonify({
        'success': True,
        'neuer_lauf_id': ziel_lauf_id,
        'neuer_einkaeufer_name': neuer_name,
        'message': f'Position an {neuer_name} (Lauf {ziel_lauf_id}) übertragen.'
    })


# =============================================================================
# Zusatzleistungen (Kat. V) – CRUD
# =============================================================================

@provision_api.route('/zusatzleistung/erstellen', methods=['POST'])
@login_required
def zusatzleistung_erstellen():
    """
    POST /api/provision/zusatzleistung/erstellen
    Body: { "lauf_id": 39, "bank": "Santander", "name": "Müller", "datum": "2026-03-15", "betrag": 250.00 }
    Nur VKL/Admin. Nicht bei ENDLAUF.
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin dürfen Zusatzleistungen erfassen.'}), 403

    data = request.get_json() or {}
    lauf_id = data.get('lauf_id')
    bank = (data.get('bank') or '').strip()
    name = (data.get('name') or '').strip()
    datum = (data.get('datum') or '').strip() or None
    betrag = data.get('betrag')

    if not lauf_id or betrag is None:
        return jsonify({'success': False, 'error': 'lauf_id und betrag sind erforderlich.'}), 400
    try:
        betrag = float(betrag)
        lauf_id = int(lauf_id)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Ungültige Werte.'}), 400

    erstellt_von = getattr(current_user, 'username', None) or getattr(current_user, 'display_name', '') or 'system'

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status, verkaufer_id, abrechnungsmonat FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if (lauf['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt.'}), 403

        cur.execute("""
            INSERT INTO provision_zusatzleistungen
                (lauf_id, verkaufer_id, abrechnungsmonat, typ, bezeichnung, beleg_referenz, beleg_datum,
                 provision_verkaufer, betrag_gesamt, anteil_prozent, erfasst_von)
            VALUES (%s, %s, %s, 'Finanzierung', %s, %s, %s, %s, %s, 100, %s)
            RETURNING id
        """, (lauf_id, lauf['verkaufer_id'], lauf['abrechnungsmonat'],
              name, bank, datum, betrag, betrag, erstellt_von))
        new_id = cur.fetchone()[0]
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'id': new_id, 'message': 'Zusatzleistung erfasst.'})


@provision_api.route('/zusatzleistung/<int:zl_id>/bearbeiten', methods=['POST'])
@login_required
def zusatzleistung_bearbeiten(zl_id):
    """
    POST /api/provision/zusatzleistung/<id>/bearbeiten
    Body: { "bank": "...", "name": "...", "datum": "...", "betrag": 123.45 }
    """
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin.'}), 403

    data = request.get_json() or {}
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT z.id, z.lauf_id, l.status
            FROM provision_zusatzleistungen z
            JOIN provision_laeufe l ON l.id = z.lauf_id
            WHERE z.id = %s
        """, (zl_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Nicht gefunden.'}), 404
        if (row['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt.'}), 403

        lauf_id = row['lauf_id']
        sets = []
        vals = []
        if 'bank' in data:
            sets.append("beleg_referenz = %s"); vals.append((data['bank'] or '').strip())
        if 'name' in data:
            sets.append("bezeichnung = %s"); vals.append((data['name'] or '').strip())
        if 'datum' in data:
            sets.append("beleg_datum = %s"); vals.append((data['datum'] or '').strip() or None)
        if 'betrag' in data:
            try:
                b = float(data['betrag'])
                sets.append("provision_verkaufer = %s"); vals.append(b)
                sets.append("betrag_gesamt = %s"); vals.append(b)
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': 'betrag muss eine Zahl sein.'}), 400

        if not sets:
            return jsonify({'success': False, 'error': 'Keine Änderungen.'}), 400

        bearbeitet_von = getattr(current_user, 'username', None) or 'system'
        sets.append("geaendert_von = %s"); vals.append(bearbeitet_von)
        sets.append("geaendert_am = NOW()")

        cur.execute(f"UPDATE provision_zusatzleistungen SET {', '.join(sets)} WHERE id = %s", vals + [zl_id])
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'message': 'Aktualisiert.'})


@provision_api.route('/zusatzleistung/<int:zl_id>/loeschen', methods=['POST', 'DELETE'])
@login_required
def zusatzleistung_loeschen(zl_id):
    """POST/DELETE /api/provision/zusatzleistung/<id>/loeschen"""
    if not _may_see_all_verkaufer():
        return jsonify({'success': False, 'error': 'Nur VKL/Admin.'}), 403

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT z.id, z.lauf_id, l.status
            FROM provision_zusatzleistungen z
            JOIN provision_laeufe l ON l.id = z.lauf_id
            WHERE z.id = %s
        """, (zl_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Nicht gefunden.'}), 404
        if (row['status'] or '').upper() == 'ENDLAUF':
            return jsonify({'success': False, 'error': 'Endlauf ist gesperrt.'}), 403

        lauf_id = row['lauf_id']
        cur.execute("DELETE FROM provision_zusatzleistungen WHERE id = %s", (zl_id,))
        _recalc_lauf_sums(cur, lauf_id)
        conn.commit()

    return jsonify({'success': True, 'message': 'Gelöscht.'})


# =============================================================================
# Admin: Provisionsarten (provision_config) verwalten – nur Admin
# =============================================================================

@provision_api.route('/config', methods=['GET'])
@login_required
def config_list():
    """
    GET /api/provision/config?monat=YYYY-MM (optional)
    Liste aller provision_config-Einträge. Mit monat: nur für diesen Monat gültige.
    Ohne monat: alle Einträge (für Admin-Übersicht inkl. Vergangenheit/Zukunft).
    """
    if not _may_manage_config():
        return jsonify({'success': False, 'error': 'Nur Admin darf Provisionsarten verwalten.'}), 403
    monat = request.args.get('monat')
    try:
        with db_session() as conn:
            cur = conn.cursor()
            base_cols = "id, kategorie, bezeichnung, bemessungsgrundlage, prozentsatz, min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61, COALESCE(gw_bestand_operator_abzug, 'minus') AS gw_bestand_operator_abzug, COALESCE(gw_bestand_operator_komponenten, 'plus') AS gw_bestand_operator_komponenten, gueltig_ab, gueltig_bis, erstellt_von, erstellt_am"
            ext_cols = ", COALESCE(use_zielpraemie, false) AS use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, COALESCE(zielpraemie_basis, 'auslieferung') AS zielpraemie_basis, memo_p1_kategorie"
            try:
                if monat and len(monat) == 7 and monat[4] == '-':
                    cur.execute("SELECT " + base_cols + ext_cols + " FROM provision_config WHERE gueltig_ab <= %s AND (gueltig_bis IS NULL OR gueltig_bis >= %s) ORDER BY kategorie", (monat + '-01', monat + '-01'))
                else:
                    cur.execute("SELECT " + base_cols + ext_cols + " FROM provision_config ORDER BY kategorie, gueltig_ab DESC")
            except Exception:
                if monat and len(monat) == 7 and monat[4] == '-':
                    cur.execute("SELECT " + base_cols + " FROM provision_config WHERE gueltig_ab <= %s AND (gueltig_bis IS NULL OR gueltig_bis >= %s) ORDER BY kategorie", (monat + '-01', monat + '-01'))
                else:
                    cur.execute("SELECT " + base_cols + " FROM provision_config ORDER BY kategorie, gueltig_ab DESC")
            rows = rows_to_list(cur.fetchall())
        for r in rows:
            r.setdefault('use_zielpraemie', False)
            r.setdefault('zielerreichung_betrag', None)
            r.setdefault('zielpraemie_fallback_ziel', None)
            r.setdefault('zielpraemie_basis', 'auslieferung')
            r.setdefault('memo_p1_kategorie', None)
        # Datum/Decimal als JSON-tauglich
        for r in rows:
            for key in ('gueltig_ab', 'gueltig_bis', 'erstellt_am'):
                if r.get(key) is not None:
                    r[key] = str(r[key])
            for key in ('prozentsatz', 'min_betrag', 'max_betrag', 'stueck_praemie', 'param_j60', 'param_j61', 'zielerreichung_betrag'):
                if r.get(key) is not None:
                    r[key] = float(r[key])
            if r.get('stueck_max') is not None:
                r['stueck_max'] = int(r['stueck_max'])
            if r.get('zielpraemie_fallback_ziel') is not None:
                r['zielpraemie_fallback_ziel'] = int(r['zielpraemie_fallback_ziel'])
            r['zielpraemie_basis'] = (r.get('zielpraemie_basis') or 'auslieferung')
            r['memo_p1_kategorie'] = (r.get('memo_p1_kategorie') or None)
            r['use_zielpraemie'] = bool(r.get('use_zielpraemie'))
        return jsonify({'success': True, 'items': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@provision_api.route('/config/<int:config_id>', methods=['GET'])
@login_required
def config_get(config_id):
    """GET /api/provision/config/<id> – Einzelne Regel."""
    if not _may_manage_config():
        return jsonify({'success': False, 'error': 'Nur Admin'}), 403
    try:
        with db_session() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    SELECT id, kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                           min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61,
                           COALESCE(gw_bestand_operator_abzug, 'minus') AS gw_bestand_operator_abzug,
                           COALESCE(gw_bestand_operator_komponenten, 'plus') AS gw_bestand_operator_komponenten,
                           gueltig_ab, gueltig_bis, erstellt_von, erstellt_am,
                           COALESCE(use_zielpraemie, false) AS use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel,
                           COALESCE(zielpraemie_basis, 'auslieferung') AS zielpraemie_basis, memo_p1_kategorie
                    FROM provision_config WHERE id = %s
                """, (config_id,))
            except Exception:
                cur.execute("""
                    SELECT id, kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                           min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61,
                           gueltig_ab, gueltig_bis, erstellt_von, erstellt_am
                    FROM provision_config WHERE id = %s
                """, (config_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Nicht gefunden'}), 404
        r = dict(row)
        for key in ('gueltig_ab', 'gueltig_bis', 'erstellt_am'):
            if r.get(key) is not None:
                r[key] = str(r[key])
        for key in ('prozentsatz', 'min_betrag', 'max_betrag', 'stueck_praemie', 'param_j60', 'param_j61', 'zielerreichung_betrag'):
            if r.get(key) is not None:
                r[key] = float(r[key])
        if r.get('stueck_max') is not None:
            r['stueck_max'] = int(r['stueck_max'])
        r.setdefault('use_zielpraemie', False)
        r.setdefault('zielerreichung_betrag', None)
        r.setdefault('zielpraemie_fallback_ziel', None)
        r.setdefault('zielpraemie_basis', 'auslieferung')
        r.setdefault('memo_p1_kategorie', None)
        if r.get('zielpraemie_fallback_ziel') is not None:
            r['zielpraemie_fallback_ziel'] = int(r['zielpraemie_fallback_ziel'])
        r['zielpraemie_basis'] = (r.get('zielpraemie_basis') or 'auslieferung')
        r['memo_p1_kategorie'] = (r.get('memo_p1_kategorie') or None)
        r['use_zielpraemie'] = bool(r.get('use_zielpraemie'))
        return jsonify({'success': True, 'item': r})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@provision_api.route('/config', methods=['POST'])
@login_required
def config_create():
    """
    POST /api/provision/config – Neue Provisionsart anlegen.
    Body: kategorie, bezeichnung, bemessungsgrundlage, prozentsatz, gueltig_ab;
    optional: min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61.
    """
    if not _may_manage_config():
        return jsonify({'success': False, 'error': 'Nur Admin'}), 403
    data = request.get_json() or {}
    kategorie = (data.get('kategorie') or '').strip()
    bezeichnung = (data.get('bezeichnung') or '').strip()
    bemessungsgrundlage = (data.get('bemessungsgrundlage') or 'db').strip()
    gueltig_ab = (data.get('gueltig_ab') or '').strip()
    if not kategorie or not bezeichnung or not gueltig_ab:
        return jsonify({'success': False, 'error': 'kategorie, bezeichnung und gueltig_ab sind Pflichtfelder.'}), 400
    try:
        prozentsatz = float(data.get('prozentsatz', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'prozentsatz muss eine Zahl sein.'}), 400
    erstellt_von = getattr(current_user, 'username', None) or getattr(current_user, 'display_name', '') or 'system'

    def _float_or_none(v):
        if v is None or v == '':
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _int_or_none(v):
        if v is None or v == '':
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    min_betrag = _float_or_none(data.get('min_betrag'))
    max_betrag = _float_or_none(data.get('max_betrag'))
    stueck_praemie = _float_or_none(data.get('stueck_praemie'))
    stueck_max = _int_or_none(data.get('stueck_max'))
    param_j60 = _float_or_none(data.get('param_j60'))
    param_j61 = _float_or_none(data.get('param_j61'))
    gw_op_abzug = (data.get('gw_bestand_operator_abzug') or 'minus').strip().lower()
    if gw_op_abzug not in ('minus', 'plus'):
        gw_op_abzug = 'minus'
    gw_op_komponenten = (data.get('gw_bestand_operator_komponenten') or 'plus').strip().lower()
    if gw_op_komponenten not in ('plus', 'minus'):
        gw_op_komponenten = 'plus'
    use_zielpraemie = data.get('use_zielpraemie') in (True, 'true', 1, '1')
    zielerreichung_betrag = _float_or_none(data.get('zielerreichung_betrag'))
    zielpraemie_fallback_ziel = _int_or_none(data.get('zielpraemie_fallback_ziel'))
    zielpraemie_basis = (data.get('zielpraemie_basis') or 'auslieferung').strip().lower()
    if zielpraemie_basis not in ('auslieferung', 'auftragseingang'):
        zielpraemie_basis = 'auslieferung'
    memo_p1_kategorie = (data.get('memo_p1_kategorie') or '').strip() or None
    if memo_p1_kategorie not in (None, 'II_testwagen', 'III_gebrauchtwagen'):
        memo_p1_kategorie = None

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO provision_config (
                    kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                    min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61,
                    gw_bestand_operator_abzug, gw_bestand_operator_komponenten,
                    gueltig_ab, erstellt_von, use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, zielpraemie_basis, memo_p1_kategorie
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (kategorie, bezeichnung, bemessungsgrundlage, prozentsatz,
                  min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61,
                  gw_op_abzug, gw_op_komponenten,
                  gueltig_ab, erstellt_von, use_zielpraemie, zielerreichung_betrag, zielpraemie_fallback_ziel, zielpraemie_basis, memo_p1_kategorie))
            row = cur.fetchone()
            new_id = row[0] if row else None
            conn.commit()
        return jsonify({'success': True, 'id': new_id, 'message': 'Provisionsart angelegt.'})
    except Exception as e:
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'success': False, 'error': 'Diese Kategorie existiert bereits mit gleichem gueltig_ab.'}), 400
        return jsonify({'success': False, 'error': str(e)}), 500


@provision_api.route('/config/<int:config_id>', methods=['PUT'])
@login_required
def config_update(config_id):
    """
    PUT /api/provision/config/<id> – Bestehende Regel bearbeiten.
    Body: beliebige Felder (bezeichnung, prozentsatz, min_betrag, max_betrag, …).
    kategorie und gueltig_ab können nicht geändert werden (Versionierung).
    """
    if not _may_manage_config():
        return jsonify({'success': False, 'error': 'Nur Admin'}), 403
    data = request.get_json() or {}

    def _float_or_none(v):
        if v is None or v == '':
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _int_or_none(v):
        if v is None or v == '':
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    updates = []
    params = []
    for key, col in [
        ('bezeichnung', 'bezeichnung'), ('bemessungsgrundlage', 'bemessungsgrundlage'),
        ('prozentsatz', 'prozentsatz'), ('min_betrag', 'min_betrag'), ('max_betrag', 'max_betrag'),
        ('stueck_praemie', 'stueck_praemie'), ('stueck_max', 'stueck_max'),
        ('param_j60', 'param_j60'), ('param_j61', 'param_j61'), ('gueltig_bis', 'gueltig_bis'),
        ('gw_bestand_operator_abzug', 'gw_bestand_operator_abzug'),
        ('gw_bestand_operator_komponenten', 'gw_bestand_operator_komponenten'),
        ('use_zielpraemie', 'use_zielpraemie'), ('zielerreichung_betrag', 'zielerreichung_betrag'),
        ('zielpraemie_fallback_ziel', 'zielpraemie_fallback_ziel'),
        ('zielpraemie_basis', 'zielpraemie_basis'),
        ('memo_p1_kategorie', 'memo_p1_kategorie'),
    ]:
        v = data.get(key)
        if key == 'gueltig_bis':
            # Nur setzen wenn explizit im Body (erlaubt NULL zum Leeren)
            if key not in data:
                continue
            val = v.strip() if isinstance(v, str) and v else (str(v) if v else None)
            updates.append("gueltig_bis = %s")
            params.append(val)
            continue
        if key == 'use_zielpraemie':
            val = v in (True, 'true', 1, '1')
            updates.append("use_zielpraemie = %s")
            params.append(val)
            continue
        if key in ('gw_bestand_operator_abzug', 'gw_bestand_operator_komponenten', 'zielpraemie_basis'):
            val = (v or '').strip().lower() if v is not None else None
            if key in ('gw_bestand_operator_abzug', 'gw_bestand_operator_komponenten'):
                if val not in ('minus', 'plus'):
                    continue
            elif val not in ('auslieferung', 'auftragseingang'):
                continue
            updates.append(f"{col} = %s")
            params.append(val)
            continue
        if key == 'memo_p1_kategorie':
            if key not in data:
                continue
            val = (v or '').strip() if isinstance(v, str) else None
            if val == '':
                val = None
            if val not in (None, 'II_testwagen', 'III_gebrauchtwagen'):
                continue
            updates.append("memo_p1_kategorie = %s")
            params.append(val)
            continue
        if v is None:
            continue
        elif key in ('prozentsatz', 'min_betrag', 'max_betrag', 'stueck_praemie', 'param_j60', 'param_j61', 'zielerreichung_betrag'):
            val = _float_or_none(v)
            if val is None and v is not None and v != '':
                continue
        elif key == 'zielpraemie_fallback_ziel':
            if key not in data:
                continue
            val = _int_or_none(v)
            updates.append("zielpraemie_fallback_ziel = %s")
            params.append(val)
            continue
        elif key == 'stueck_max':
            val = _int_or_none(v)
            if val is None and v is not None and v != '':
                continue
        else:
            val = (v or '').strip() if isinstance(v, str) else v
        updates.append(f"{col} = %s")
        params.append(val)
    if not updates:
        return jsonify({'success': False, 'error': 'Keine Felder zum Aktualisieren angegeben.'}), 400
    params.append(config_id)
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE provision_config SET " + ", ".join(updates) + " WHERE id = %s",
                params
            )
            if cur.rowcount == 0:
                return jsonify({'success': False, 'error': 'Eintrag nicht gefunden.'}), 404
            conn.commit()
        return jsonify({'success': True, 'message': 'Aktualisiert.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
