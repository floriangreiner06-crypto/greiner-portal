"""
OPOS-API – Offene Posten (Controlling)
======================================
Erstellt: 2026-02-19 | Workstream: Controlling
Berechtigung: Feature 'opos' (admin, buchhaltung, verkauf_leitung, verkauf).
Verkäufer sehen nur eigene Posten (Filter über ldap_employee_mapping → locosoft_id).
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from api.db_utils import db_session, row_to_dict

opos_api = Blueprint('opos_api', __name__)


def get_current_user_locosoft_id():
    """
    Liefert die Locosoft-Mitarbeiternummer des eingeloggten Users (für Verkäufer-Filter).
    Returns: int oder None wenn kein Mapping.
    """
    if not current_user.is_authenticated:
        return None
    username = getattr(current_user, 'username', '') or ''
    ldap_username = username.split('@')[0] if '@' in username else username
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT lem.locosoft_id
            FROM ldap_employee_mapping lem
            JOIN employees e ON lem.employee_id = e.id
            WHERE lem.ldap_username = %s AND e.aktiv = true
        """, (ldap_username,))
        row = cur.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return None


def _opos_force_own_only():
    """True wenn für aktuelle Rolle nur eigene Posten (Filter nicht auflösbar). Nutzt feature_filter_mode."""
    if not current_user.is_authenticated:
        return False
    from api.feature_filter_mode import get_filter_mode
    role = getattr(current_user, 'portal_role', '') or 'mitarbeiter'
    return get_filter_mode(role, 'opos') == 'own_only'


@opos_api.route('/api/controlling/opos', methods=['GET'])
def opos_list():
    """
    GET /api/controlling/opos
    Query-Parameter: von (Datum), bis (Datum), verkaeufer_nr (int), nur_fahrzeugverkauf (0|1).
    Verkäufer (Rolle verkauf): verkaeufer_nr wird ignoriert, es wird nur locosoft_id gefiltert.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    if not current_user.can_access_feature('opos'):
        return jsonify({'error': 'Keine Berechtigung für Offene Posten'}), 403

    von = request.args.get('von')
    bis = request.args.get('bis')
    verkaeufer_nr = request.args.get('verkaeufer_nr', type=int)
    nur_fahrzeugverkauf = request.args.get('nur_fahrzeugverkauf', type=int)

    # Rollenfilter: own_only = nur eigene, sonst Request-Parameter nutzen
    filter_verkaeufer_nr = None
    if _opos_force_own_only():
        loco_id = get_current_user_locosoft_id()
        if loco_id is not None:
            filter_verkaeufer_nr = loco_id
    else:
        if verkaeufer_nr is not None:
            filter_verkaeufer_nr = verkaeufer_nr

    # CTE-basierte Abfrage (wie scripts/sql/offene_posten_fahrzeugverkauf.sql), mit optionalen Filtern
    with db_session() as conn:
        cur = conn.cursor()

        # Dynamische Filter
        offene_where = "1=1"
        offene_params = []
        if von:
            offene_where += " AND j.invoice_date >= %s"
            offene_params.append(von)
        if bis:
            offene_where += " AND j.invoice_date <= %s"
            offene_params.append(bis)

        mit_where = "1=1"
        mit_params = []
        if filter_verkaeufer_nr is not None:
            mit_where += " AND COALESCE(verkaeufer_fahrzeugverkauf, rechnungsersteller_nr) = %s"
            mit_params.append(filter_verkaeufer_nr)
        if nur_fahrzeugverkauf == 1:
            mit_where += " AND verkaeufer_fahrzeugverkauf IS NOT NULL"

        sql = f"""
WITH
-- Gesamtsaldo pro Kunde (Soll − Haben auf Debitoren): nur Kunden mit Saldo > 0 sind „wirklich“ offen.
-- Nur Buchungszeilen, die in Locosoft als offen gelten: clearing_number IS NULL bzw. 0 = „OP“, sonst Auszifferungsnummer (bezahlt).
-- Nur Forderungen (Debitoren), keine Kreditoren (Einkaufsrechnungen):
-- 140001 = Forderungen an Banken (Stellantis etc.), 150000-159999 = Debitoren, 170000-199999 = sonstige Forderungen
-- 160000-169999 = Kreditoren (Verbindlichkeiten) ausgeschlossen
kunde_saldo AS (
  SELECT customer_number,
    SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 AS saldo_gesamt
  FROM loco_journal_accountings
  WHERE nominal_account_number BETWEEN 140000 AND 199999
    AND (nominal_account_number < 160000 OR nominal_account_number >= 170000)
    AND (clearing_number IS NULL OR clearing_number = 0)
  GROUP BY customer_number
  HAVING SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) > 0
),
offene AS (
  SELECT
    j.customer_number,
    NULLIF(TRIM(j.invoice_number), '') AS invoice_number,
    j.invoice_date,
    SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) / 100.0 AS saldo_eur,
    MAX(j.employee_number) AS rechnungsersteller_nr
  FROM loco_journal_accountings j
  INNER JOIN kunde_saldo ks ON ks.customer_number = j.customer_number
  WHERE j.nominal_account_number BETWEEN 140000 AND 199999
    AND (j.nominal_account_number < 160000 OR j.nominal_account_number >= 170000)
    AND (j.clearing_number IS NULL OR j.clearing_number = 0)
    AND j.invoice_number IS NOT NULL
    AND TRIM(j.invoice_number) <> ''
    AND j.invoice_date IS NOT NULL
    AND {offene_where}
  GROUP BY j.customer_number, j.invoice_number, j.invoice_date
  HAVING SUM(CASE WHEN j.debit_or_credit = 'S' THEN j.posted_value ELSE -j.posted_value END) > 0
),
-- Bei Stellantis Bank (1007422) steht in sales oft der Endkunde, nicht 1007422.
-- Mehrere Sales am gleichen Datum: Verkäufer per Betragsnähe (out_sale_price ~ saldo_eur) wählen.
sales_treffer AS (
  SELECT DISTINCT ON (o.customer_number, o.invoice_number, o.invoice_date)
    o.customer_number,
    o.invoice_number,
    o.invoice_date,
    o.saldo_eur,
    o.rechnungsersteller_nr,
    s.salesman_number AS verkaeufer_fahrzeugverkauf
  FROM offene o
  LEFT JOIN sales s
    ON s.out_invoice_date = o.invoice_date
   AND (s.out_invoice_number::text = o.invoice_number
        OR s.buyer_customer_no::text = o.customer_number::text
        OR (o.customer_number = 1007422 AND s.out_invoice_date = o.invoice_date))
  ORDER BY o.customer_number, o.invoice_number, o.invoice_date,
           (s.out_invoice_number::text = o.invoice_number) DESC NULLS LAST,
           (s.buyer_customer_no::text = o.customer_number::text) DESC NULLS LAST,
           (CASE WHEN o.customer_number = 1007422 THEN ABS(COALESCE(s.out_sale_price, 0) - o.saldo_eur) ELSE 0 END) ASC NULLS LAST,
           s.salesman_number NULLS LAST
),
mit_verkaeufer AS (
  SELECT
    customer_number,
    invoice_number,
    invoice_date,
    saldo_eur,
    COALESCE(verkaeufer_fahrzeugverkauf, rechnungsersteller_nr) AS verkaufer_nr,
    (verkaeufer_fahrzeugverkauf IS NOT NULL) AS ist_fahrzeugverkauf
  FROM sales_treffer
  WHERE {mit_where}
)
SELECT
  mv.customer_number,
  COALESCE(e.first_name || ' ' || e.last_name, 'Nr. ' || mv.verkaufer_nr::text, 'Ohne Zuordnung') AS verkaeufer_oder_ersteller,
  mv.verkaufer_nr,
  mv.ist_fahrzeugverkauf,
  COALESCE(cs.kunde, 'Kunde Nr. ' || mv.customer_number::text) AS kunde,
  mv.invoice_date AS rechnung_datum,
  mv.invoice_number AS rechnung_nr,
  ROUND(mv.saldo_eur, 2) AS betrag_eur,
  'OP' AS posten_art
FROM mit_verkaeufer mv
LEFT JOIN employees e ON e.locosoft_id = mv.verkaufer_nr
LEFT JOIN (
  SELECT customer_number,
         COALESCE(NULLIF(TRIM(MAX(COALESCE(family_name, '') || ', ' || COALESCE(first_name, ''))), ''), 'Kunde ' || customer_number) AS kunde
  FROM loco_customers_suppliers
  GROUP BY customer_number
) cs ON cs.customer_number = mv.customer_number
ORDER BY verkaeufer_oder_ersteller NULLS LAST, rechnung_datum, mv.customer_number
"""
        params = offene_params + mit_params
        cur.execute(sql, params)
        rows = cur.fetchall()

    list_result = []
    for r in rows:
        d = row_to_dict(r)
        # Datum serialisierbar
        if d.get('rechnung_datum'):
            d['rechnung_datum'] = d['rechnung_datum'].isoformat() if hasattr(d['rechnung_datum'], 'isoformat') else str(d['rechnung_datum'])
        list_result.append(d)

    gesamt = sum(x.get('betrag_eur') or 0 for x in list_result)
    return jsonify({
        'rows': list_result,
        'gesamt_eur': round(gesamt, 2),
        'anzahl': len(list_result),
        'nur_eigene': _opos_force_own_only(),
    })


@opos_api.route('/api/controlling/opos/rechnung-detail', methods=['GET'])
def opos_rechnung_detail():
    """
    GET /api/controlling/opos/rechnung-detail?customer_number=&invoice_number=&invoice_date=
    Liefert Locosoft-Infos zu einer Rechnung: FIBU-Buchungszeilen (loco_journal_accountings)
    und ggf. Rechnungskopf aus loco_invoices (Datum + Nr. Match).
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    if not current_user.can_access_feature('opos'):
        return jsonify({'error': 'Keine Berechtigung für Offene Posten'}), 403

    customer_number = request.args.get('customer_number', type=int)
    invoice_number = request.args.get('invoice_number', type=str)
    invoice_date = request.args.get('invoice_date', type=str)
    if not invoice_number or not invoice_date:
        return jsonify({'error': 'invoice_number und invoice_date erforderlich'}), 400

    with db_session() as conn:
        cur = conn.cursor()

        # FIBU-Buchungszeilen zu dieser Rechnung (Debitorenbereich wie OPOS)
        if customer_number is not None:
            cur.execute("""
                SELECT
                    j.nominal_account_number,
                    j.debit_or_credit,
                    j.posted_value / 100.0 AS betrag_eur,
                    j.document_type,
                    j.document_number,
                    j.document_date,
                    j.clearing_number,
                    j.employee_number,
                    NULLIF(TRIM(j.posting_text), '') AS posting_text,
                    j.accounting_date
                FROM loco_journal_accountings j
                WHERE j.nominal_account_number BETWEEN 140000 AND 199999
                  AND (j.nominal_account_number < 160000 OR j.nominal_account_number >= 170000)
                  AND j.customer_number = %s
                  AND TRIM(j.invoice_number) = TRIM(%s)
                  AND j.invoice_date = %s
                ORDER BY j.position_in_document, j.nominal_account_number
            """, (customer_number, invoice_number, invoice_date))
        else:
            cur.execute("""
                SELECT
                    j.nominal_account_number,
                    j.debit_or_credit,
                    j.posted_value / 100.0 AS betrag_eur,
                    j.document_type,
                    j.document_number,
                    j.document_date,
                    j.clearing_number,
                    j.employee_number,
                    NULLIF(TRIM(j.posting_text), '') AS posting_text,
                    j.accounting_date
                FROM loco_journal_accountings j
                WHERE j.nominal_account_number BETWEEN 140000 AND 199999
                  AND (j.nominal_account_number < 160000 OR j.nominal_account_number >= 170000)
                  AND TRIM(j.invoice_number) = TRIM(%s)
                  AND j.invoice_date = %s
                ORDER BY j.customer_number, j.position_in_document, j.nominal_account_number
            """, (invoice_number, invoice_date))

        buchungen = [row_to_dict(r) for r in cur.fetchall()]
        for b in buchungen:
            for key in ('document_date', 'accounting_date'):
                if b.get(key) and hasattr(b[key], 'isoformat'):
                    b[key] = b[key].isoformat()

        # Optional: Rechnungskopf aus loco_invoices (Match über Datum + Nr.)
        try:
            inv_num_int = int(invoice_number.strip())
        except (ValueError, TypeError):
            inv_num_int = None
        rechnungen_inv = []
        if inv_num_int is not None:
            cur.execute("""
                SELECT invoice_type, invoice_number, subsidiary, invoice_date,
                       total_net, total_gross, job_amount_net, part_amount_net,
                       order_number, paying_customer, is_canceled
                FROM loco_invoices
                WHERE invoice_date = %s AND invoice_number = %s
                ORDER BY invoice_type
            """, (invoice_date, inv_num_int))
            for r in cur.fetchall():
                rechnungen_inv.append(row_to_dict(r))
            for inv in rechnungen_inv:
                if inv.get('total_net') is not None:
                    inv['total_net'] = float(inv['total_net'])
                if inv.get('total_gross') is not None:
                    inv['total_gross'] = float(inv['total_gross'])
                if inv.get('job_amount_net') is not None:
                    inv['job_amount_net'] = float(inv['job_amount_net'])
                if inv.get('part_amount_net') is not None:
                    inv['part_amount_net'] = float(inv['part_amount_net'])

        # Kundenname
        kunde = None
        if customer_number is not None:
            cur.execute("""
                SELECT COALESCE(NULLIF(TRIM(MAX(COALESCE(family_name, '') || ', ' || COALESCE(first_name, ''))), ''), 'Kunde ' || %s) AS kunde
                FROM loco_customers_suppliers
                WHERE customer_number = %s
            """, (customer_number, customer_number))
            row = cur.fetchone()
            if row and row[0]:
                kunde = row[0]

    return jsonify({
        'customer_number': customer_number,
        'invoice_number': invoice_number,
        'invoice_date': invoice_date,
        'kunde': kunde,
        'buchungen': buchungen,
        'rechnungen': rechnungen_inv,
    })


@opos_api.route('/api/controlling/opos/verkaeufer', methods=['GET'])
def opos_verkaeufer_list():
    """
    Liste Verkäufer mit offenen Posten (für Dropdown, nur wenn User alle sehen darf).
    """
    if not current_user.is_authenticated or not current_user.can_access_feature('opos'):
        return jsonify({'error': 'Keine Berechtigung'}), 403
    if _opos_force_own_only():
        return jsonify({'verkaeufer': []})

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT e.id, e.locosoft_id,
                   COALESCE(e.first_name || ' ' || e.last_name, 'Nr. ' || e.locosoft_id::text) AS name
            FROM employees e
            WHERE e.aktiv = true AND e.locosoft_id IS NOT NULL
            ORDER BY name
        """)
        rows = cur.fetchall()

    verkaeufer = [{'id': r[0], 'locosoft_id': r[1], 'name': r[2]} for r in rows]
    return jsonify({'verkaeufer': verkaeufer})
