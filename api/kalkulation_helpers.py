#!/usr/bin/env python3
"""
Kalkulations-Helpers – SSOT für Fahrzeug-DB-Kalkulation (Locosoft)
==================================================================
Gemeinsame SQL-Fragmente für EK, VK netto, variable Kosten, VKU, DB1.
Verwendet von: fahrzeug_data.py (GW-Bestand), profitabilitaet_data.py (Profitabilität).

TAG 219: Extrahiert aus fahrzeug_data.get_gw_bestand() zur Vermeidung von Duplikaten.

Besteuerung: dealer_vehicle_type (D→Diff, G→Regel) > out_sale_type > out_invoice_type.
EK-Felder (calc_*) sind in Locosoft bereits NETTO.
"""


# Zinssatz für Standkosten (eine Quelle für Portal; ggf. von gewinnplanung_v2_gw_data importieren)
ZINSSATZ_JAHR = 0.05


def _a(alias: str, col: str) -> str:
    """Spalte mit Tabellen-Alias: _a('dv', 'out_sale_price') -> 'dv.out_sale_price'."""
    return f"{alias}.{col}" if alias else col


def sql_ek_netto(alias: str = "dv") -> str:
    """
    SQL-Fragment: EK netto (Einsatzwert).
    EK = calc_basic_charge + calc_accessory + calc_extra_expenses + usage_value_encr_*
    """
    return (
        f"COALESCE({alias}.calc_basic_charge, 0) + COALESCE({alias}.calc_accessory, 0)"
        f" + COALESCE({alias}.calc_extra_expenses, 0)"
        f" + COALESCE({alias}.calc_usage_value_encr_internal, 0)"
        f" + COALESCE({alias}.calc_usage_value_encr_external, 0)"
    )


def sql_variable_kosten(alias: str = "dv") -> str:
    """SQL-Fragment: Variable Kosten (intern + sonstige)."""
    return (
        f"COALESCE({alias}.calc_cost_internal_invoices, 0)"
        f" + COALESCE({alias}.calc_cost_other, 0)"
    )


def sql_besteuerung_art(alias: str = "dv") -> str:
    """
    SQL-Fragment: Besteuerungsart (Regel / Diff25a / Leasing).
    Priorität: dealer_vehicle_type > out_sale_type > out_invoice_type.
    """
    return f"""
        CASE
            WHEN {alias}.dealer_vehicle_type = 'D' THEN 'Diff25a'
            WHEN {alias}.dealer_vehicle_type = 'G' THEN 'Regel'
            WHEN {alias}.out_sale_type = 'F' THEN 'Regel'
            WHEN {alias}.out_sale_type = 'B' THEN 'Diff25a'
            WHEN {alias}.out_sale_type = 'L' THEN 'Leasing'
            WHEN {alias}.out_invoice_type = 8 THEN 'Diff25a'
            ELSE 'Regel'
        END
    """.strip()


def sql_vk_netto(alias: str = "dv") -> str:
    """
    SQL-Fragment: VK netto (effektiv).
    Regel: out_sale_price / 1.19; Diff25a: VK - MwSt auf Marge.
    """
    ek = sql_ek_netto(alias)
    return f"""
        CASE
            WHEN ({sql_besteuerung_art(alias)}) = 'Regel'
            THEN ROUND(COALESCE({alias}.out_sale_price, 0) / 1.19, 2)
            ELSE ROUND(COALESCE({alias}.out_sale_price, 0) - (
                GREATEST(COALESCE({alias}.out_sale_price, 0) - ({ek}), 0) / 1.19 * 0.19
            ), 2)
        END
    """.strip()


def sql_vku_subquery(alias: str = "dv") -> str:
    """
    SQL-Fragment: VKU (Verkaufsunterstützung) als Subquery.
    JOIN über dealer_vehicle_type + dealer_vehicle_number.
    """
    return f"""
        COALESCE(
            (SELECT SUM(claimed_amount)
             FROM dealer_sales_aid dsa
             WHERE dsa.dealer_vehicle_type = {alias}.dealer_vehicle_type
               AND dsa.dealer_vehicle_number = {alias}.dealer_vehicle_number),
            0
        )
    """.strip()


def sql_db1(alias: str = "dv", vku_nur_bei_verkauf: bool = True) -> str:
    """
    SQL-Fragment: Kalkulierter DB1 (Deckungsbeitrag).
    Regel: VK_netto - (EK + variable Kosten) + VKU.
    Diff25a: Marge_netto - variable Kosten + VKU.
    VKU nur bei verkauften Fahrzeugen, wenn vku_nur_bei_verkauf=True.
    """
    ek = sql_ek_netto(alias)
    var = sql_variable_kosten(alias)
    vku_expr = sql_vku_subquery(alias)
    if vku_nur_bei_verkauf:
        vku_part = f"""CASE
            WHEN {alias}.out_invoice_date IS NOT NULL OR {alias}.out_sales_contract_date IS NOT NULL
            THEN {vku_expr}
            ELSE 0
        END"""
    else:
        vku_part = vku_expr

    return f"""
        CASE
            WHEN ({sql_besteuerung_art(alias)}) = 'Regel'
            THEN ROUND(COALESCE({alias}.out_sale_price, 0) / 1.19, 2)
                - ({ek} + {var})
                + {vku_part}
            ELSE ROUND(
                GREATEST(COALESCE({alias}.out_sale_price, 0) - ({ek}), 0) / 1.19, 2
            ) - ({var}) + {vku_part}
        END
    """.strip()


def sql_standzeit_tage(alias: str = "dv", bis_datum_col: str = "CURRENT_DATE") -> str:
    """
    SQL-Fragment: Standzeit in Tagen.
    Standard: bis heute (CURRENT_DATE). Für verkaufte Fz: bis out_invoice_date.
    """
    if bis_datum_col == "CURRENT_DATE":
        return f"CURRENT_DATE - COALESCE({alias}.in_arrival_date, {alias}.created_date)"
    return f"({bis_datum_col}::date - COALESCE({alias}.in_arrival_date, {alias}.created_date))"
