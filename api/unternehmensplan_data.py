"""
Unternehmensplan Data - SSOT für Gesamtunternehmensplanung
==========================================================
Ziel: 1% Gesamtrendite pro Geschäftsjahr

Geschäftsjahr: September bis August (z.B. 2025/26 = Sep 2025 - Aug 2026)

Bereiche (Kostenstellen):
- NW: Neuwagen (Konten 810000-819999 / 710000-719999)
- GW: Gebrauchtwagen (Konten 820000-829999 / 720000-729999)
- Teile: Teile/Zubehör (Konten 830000-839999 / 730000-739999)
- Werkstatt: Lohn/Service (Konten 840000-849999 / 740000-749999)
- Sonstige: Sonstige Erlöse (Konten 860000-869999 / 760000-769999 + 893200-893299)
- Kosten: Gemeinkosten (Konten 400000-499999 + 891000-896999)

WICHTIG - GlobalCube-kompatible BWA-Logik:
- Umsatz: 800000-889999 + 893200-893299 (Zinserträge!)
- Einsatz: 700000-799999
- Variable Kosten: 415xxx, 435xxx, 455xxx-456xxx, 487xxx, 491xxx-497xxx
- Direkte Kosten: 4xxxxx mit KST 1-7 (ohne Variable)
- Indirekte Kosten: 4xxxxx mit KST 0 + 424xxx, 438xxx, 498xxx-499xxx, 891xxx-896xxx
- Neutrales Ergebnis: 200000-299999

Referenz: docs/BWA_KONTEN_MAPPING_FINAL.md (validiert gegen GlobalCube)

TAG157: Initiale Implementierung + GlobalCube-kompatible Berechnung
Author: Claude AI + Florian Greiner
Date: 2026-01-02
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
from api.db_connection import get_db
from api.db_utils import db_session, locosoft_session


# Konstanten
BEREICHE = ['NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige']
RENDITE_ZIEL = Decimal('1.0')  # 1% Mindestrendite
BUCHUNGSSCHLUSS_WERKTAG = 5  # Kosten sind erst am 5. Werktag des Folgemonats final

# TAG162: Umlage-Konten für Konzern-Neutralisierung
# Diese Konten werden bei der Konzern-Ansicht (standort=0) ausgeblendet,
# da sie sich zwischen den Firmen gegenseitig aufheben sollten.
# Problem: Die Buchung erfolgt erst zum Monatsende, dadurch sind die Daten
# am Monatsanfang verzerrt (Hyundai zu niedrige Kosten).
#
# Autohaus Greiner (Stellantis) ERHÄLT:
# - 817051 = NW Umlage-Erlös (+12.500€)
# - 827051 = GW Umlage-Erlös (+12.500€)
# - 837051 = Werkstatt Umlage-Erlös (+12.500€)
# - 847051 = Teile Umlage-Erlös (+12.500€)
# = +50.000€/Monat
#
# Auto Greiner (Hyundai) ZAHLT:
# - 498001 = Umlage-Kosten (-50.000€)
# = -50.000€/Monat
#
# Konzern-Effekt bei vollständiger Buchung: 0€ (Nullsumme)
UMLAGE_ERLOESE_KONTEN = [817051, 827051, 837051, 847051]  # +50.000€ bei Autohaus Greiner
UMLAGE_KOSTEN_KONTEN = [498001]  # -50.000€ bei Auto Greiner
UMLAGE_BETRAG_PRO_MONAT = Decimal('50000')  # Fester Umlagebetrag


def get_letzter_abgeschlossener_monat() -> tuple:
    """
    Ermittelt den letzten vollständig abgeschlossenen Monat für Kostenauswertungen.
    Kosten werden erst bis zum 5. Werktag des Folgemonats komplett gebucht.

    Returns:
        (monat, jahr) des letzten abgeschlossenen Monats
    """
    heute = date.today()

    # Werktage im aktuellen Monat zählen
    werktage = 0
    tag = date(heute.year, heute.month, 1)
    while tag <= heute:
        if tag.weekday() < 5:  # Mo-Fr
            werktage += 1
        tag += timedelta(days=1)

    if werktage >= BUCHUNGSSCHLUSS_WERKTAG:
        # 5 Werktage vergangen -> Vormonat ist abgeschlossen
        if heute.month == 1:
            return (12, heute.year - 1)
        else:
            return (heute.month - 1, heute.year)
    else:
        # Noch keine 5 Werktage -> Vor-Vormonat ist abgeschlossen
        if heute.month <= 2:
            return (heute.month + 10, heute.year - 1)
        else:
            return (heute.month - 2, heute.year)


def get_current_geschaeftsjahr() -> str:
    """Ermittelt das aktuelle Geschäftsjahr (Sep-Aug)"""
    heute = date.today()
    if heute.month >= 9:
        return f"{heute.year}/{str(heute.year + 1)[2:]}"
    else:
        return f"{heute.year - 1}/{str(heute.year)[2:]}"


def get_gj_months(geschaeftsjahr: str) -> List[Dict[str, Any]]:
    """
    Gibt die 12 Monate eines Geschäftsjahres zurück

    Args:
        geschaeftsjahr: z.B. '2025/26'

    Returns:
        Liste mit {monat_gj, monat_kalender, jahr, label}
    """
    start_jahr = int(geschaeftsjahr.split('/')[0])
    months = []

    for i in range(12):
        monat_gj = i + 1  # 1-12 im GJ
        if i < 4:  # Sep-Dez
            monat_kalender = 9 + i
            jahr = start_jahr
        else:  # Jan-Aug
            monat_kalender = i - 3
            jahr = start_jahr + 1

        monat_namen = ['Sep', 'Okt', 'Nov', 'Dez', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug']
        months.append({
            'monat_gj': monat_gj,
            'monat_kalender': monat_kalender,
            'jahr': jahr,
            'label': f"{monat_namen[i]} {str(jahr)[2:]}"
        })

    return months


def get_ist_daten(geschaeftsjahr: str, standort: int = 0, nur_abgeschlossene: bool = True) -> Dict[str, Any]:
    """
    Holt IST-Daten aus TEK (Locosoft journal_accountings)

    Args:
        geschaeftsjahr: z.B. '2025/26'
        standort: 0=Alle, 1=DEG, 2=HYU, 3=LAN
        nur_abgeschlossene: True = nur Monate wo Kosten final gebucht (5. Werktag)

    Returns:
        Dict mit monatlichen IST-Daten pro Bereich
    """
    start_jahr = int(geschaeftsjahr.split('/')[0])
    von_datum = f"{start_jahr}-09-01"

    # Letzter abgeschlossener Monat ermitteln
    letzter_monat, letzter_jahr = get_letzter_abgeschlossener_monat()

    if nur_abgeschlossene:
        # Nur bis zum letzten abgeschlossenen Monat
        if letzter_monat == 12:
            bis_datum = f"{letzter_jahr + 1}-01-01"
        else:
            bis_datum = f"{letzter_jahr}-{letzter_monat + 1:02d}-01"
    else:
        bis_datum = f"{start_jahr + 1}-09-01"

    # Info über Datenstand
    datenstand_info = f"Daten bis {letzter_monat:02d}/{letzter_jahr} (Buchungsschluss erreicht)" if nur_abgeschlossene else "Vorläufige Daten inkl. laufender Monat"

    # Standort-Filter
    # WICHTIG: Locosoft verwendet unterschiedliche Zuordnungen:
    # - Umsatz (8xxxxx): branch_number (1=DEG, 3=LAN) oder subsidiary_to_company_ref (2=HYU)
    # - Einsatz (7xxxxx): Konto-Endziffer (xxxxxx1=DEG, xxxxxx2=LAN) oder subsidiary (2=HYU)
    # - Kosten (4xxxxx): Konto-Endziffer (xxxxxx1=DEG, xxxxxx2=LAN) oder subsidiary (2=HYU)

    # Filter für Umsatz-Konten (branch_number basiert)
    umsatz_filter = ""
    # Filter für Einsatz/Kosten (Konto-Endziffer basiert)
    einsatz_filter = ""
    kosten_filter = ""
    # TAG162: Separater Standort-Filter für neutrales Ergebnis (ohne Umlage-Filter)
    standort_neutral_filter = ""

    # TAG162: Umlage-Neutralisierung bei Konzern-Ansicht
    # Bei standort=0 (Alle/Konzern) werden die Umlage-Konten ausgeblendet,
    # da sie sich zwischen den Firmen aufheben sollen (aber erst zum Monatsende gebucht werden)
    umlage_erloese_str = ','.join(map(str, UMLAGE_ERLOESE_KONTEN))  # 817051,827051,837051,847051
    umlage_kosten_str = ','.join(map(str, UMLAGE_KOSTEN_KONTEN))    # 498001

    # TAG162: Separater Filter für indirekte Kosten (Umlage 498001)
    indirekte_umlage_filter = ""

    if standort == 0:  # Alle/Konzern - Umlage-Konten ausfiltern!
        umsatz_filter = f"AND nominal_account_number NOT IN ({umlage_erloese_str})"
        indirekte_umlage_filter = f"AND nominal_account_number NOT IN ({umlage_kosten_str})"
        # standort_neutral_filter bleibt leer - keine Standort-Einschränkung

    if standort == 1:  # Deggendorf Opel
        umsatz_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 1"
        einsatz_filter = "AND subsidiary_to_company_ref = 1 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
        kosten_filter = "AND subsidiary_to_company_ref = 1 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '1'"
        standort_neutral_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 1"
    elif standort == 2:  # Hyundai (eigene Firma)
        umsatz_filter = "AND subsidiary_to_company_ref = 2"
        einsatz_filter = "AND subsidiary_to_company_ref = 2"
        kosten_filter = "AND subsidiary_to_company_ref = 2"
        standort_neutral_filter = "AND subsidiary_to_company_ref = 2"
    elif standort == 3:  # Landau (Konto-Endziffer 2)
        umsatz_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 3"
        einsatz_filter = "AND subsidiary_to_company_ref = 1 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
        kosten_filter = "AND subsidiary_to_company_ref = 1 AND substr(CAST(nominal_account_number AS TEXT), 6, 1) = '2'"
        standort_neutral_filter = "AND subsidiary_to_company_ref = 1 AND branch_number = 3"

    with locosoft_session() as conn:
        cursor = conn.cursor()

        # Umsatz pro Bereich und Monat (branch_number basiert)
        # WICHTIG: Konten 893200-893299 (Zinserträge) gehören zum Umsatz! (GlobalCube-Logik)
        # WICHTIG: 88xxxx (sonstige Erlöse) → Sonstige (nicht ignorieren!)
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 810000 AND 819999 THEN 'NW'
                    WHEN nominal_account_number BETWEEN 820000 AND 829999 THEN 'GW'
                    WHEN nominal_account_number BETWEEN 830000 AND 839999 THEN 'Teile'
                    WHEN nominal_account_number BETWEEN 840000 AND 849999 THEN 'Werkstatt'
                    WHEN nominal_account_number BETWEEN 860000 AND 889999 THEN 'Sonstige'
                    WHEN nominal_account_number BETWEEN 893200 AND 893299 THEN 'Sonstige'
                    ELSE 'Sonstige'
                END as bereich,
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit = 'H' THEN posted_value ELSE -posted_value END) / 100.0 as umsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND ((nominal_account_number BETWEEN 800000 AND 889999)
                   OR (nominal_account_number BETWEEN 893200 AND 893299))
              {umsatz_filter}
            GROUP BY 1, 2, 3
        """, (von_datum, bis_datum))
        umsatz_rows = cursor.fetchall()

        # Einsatz pro Bereich und Monat (Konto-Endziffer basiert!)
        # WICHTIG: 79xxxx (sonstiger Einsatz) → Sonstige (nicht ignorieren!)
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN nominal_account_number BETWEEN 710000 AND 719999 THEN 'NW'
                    WHEN nominal_account_number BETWEEN 720000 AND 729999 THEN 'GW'
                    WHEN nominal_account_number BETWEEN 730000 AND 739999 THEN 'Teile'
                    WHEN nominal_account_number BETWEEN 740000 AND 749999 THEN 'Werkstatt'
                    WHEN nominal_account_number BETWEEN 760000 AND 799999 THEN 'Sonstige'
                    ELSE 'Sonstige'
                END as bereich,
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value ELSE -posted_value END) / 100.0 as einsatz
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 700000 AND 799999
              {einsatz_filter}
            GROUP BY 1, 2, 3
        """, (von_datum, bis_datum))
        einsatz_rows = cursor.fetchall()

        # Kosten pro Monat - Aufgeteilt wie in BWA v2:
        # Variable Kosten (415xxx, 435xxx, 455xxx-456xxx, 487xxx, 491xxx-497xxx)
        cursor.execute(f"""
            SELECT
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as kosten
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR (nominal_account_number BETWEEN 455000 AND 456999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR (nominal_account_number BETWEEN 487000 AND 487099
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) != '0')
                OR nominal_account_number BETWEEN 491000 AND 497899
              )
              {kosten_filter}
            GROUP BY 1, 2
        """, (von_datum, bis_datum))
        variable_kosten_rows = cursor.fetchall()

        # Direkte Kosten (4xxxxx mit Endziffer 1-7, ohne Variable)
        cursor.execute(f"""
            SELECT
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as kosten
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 400000 AND 489999
              AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','4','5','6','7')
              AND NOT (
                nominal_account_number BETWEEN 415100 AND 415199
                OR nominal_account_number BETWEEN 424000 AND 424999
                OR nominal_account_number BETWEEN 435500 AND 435599
                OR nominal_account_number BETWEEN 438000 AND 438999
                OR nominal_account_number BETWEEN 455000 AND 456999
                OR nominal_account_number BETWEEN 487000 AND 487099
                OR nominal_account_number BETWEEN 491000 AND 497999
              )
              {kosten_filter}
            GROUP BY 1, 2
        """, (von_datum, bis_datum))
        direkte_kosten_rows = cursor.fetchall()

        # Indirekte Kosten (Gemeinkosten mit Endziffer 0, plus spezielle)
        # TAG162: indirekte_umlage_filter filtert 498001 bei Konzern-Ansicht aus
        cursor.execute(f"""
            SELECT
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END) / 100.0 as kosten
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND (
                (nominal_account_number BETWEEN 400000 AND 499999
                 AND substr(CAST(nominal_account_number AS TEXT), 5, 1) = '0')
                OR (nominal_account_number BETWEEN 424000 AND 424999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR (nominal_account_number BETWEEN 438000 AND 438999
                    AND substr(CAST(nominal_account_number AS TEXT), 5, 1) IN ('1','2','3','6','7'))
                OR nominal_account_number BETWEEN 498000 AND 499999
                OR (nominal_account_number BETWEEN 891000 AND 896999
                    AND NOT (nominal_account_number BETWEEN 893200 AND 893299))
              )
              {kosten_filter}
              {indirekte_umlage_filter}
            GROUP BY 1, 2
        """, (von_datum, bis_datum))
        indirekte_kosten_rows = cursor.fetchall()

        # TAG157: Neutrales Ergebnis (Konten 2xxxxx) - WICHTIG für Unternehmensergebnis!
        # TAG162: Verwendet standort_neutral_filter statt umsatz_filter (kein Umlage-Filter für 2xxxxx)
        cursor.execute(f"""
            SELECT
                EXTRACT(YEAR FROM accounting_date)::INTEGER as jahr,
                EXTRACT(MONTH FROM accounting_date)::INTEGER as monat,
                SUM(CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END) / 100.0 as neutral
            FROM journal_accountings
            WHERE accounting_date >= %s AND accounting_date < %s
              AND nominal_account_number BETWEEN 200000 AND 299999
              {standort_neutral_filter}
            GROUP BY 1, 2
        """, (von_datum, bis_datum))
        neutral_rows = cursor.fetchall()

    # Daten strukturieren
    months = get_gj_months(geschaeftsjahr)
    result = {
        'geschaeftsjahr': geschaeftsjahr,
        'standort': standort,
        'datenstand': datenstand_info,
        'letzter_abgeschlossener_monat': f"{letzter_monat:02d}/{letzter_jahr}",
        'monate': [],
        'gesamt': {
            'umsatz': Decimal(0),
            'einsatz': Decimal(0),
            'db1': Decimal(0),
            'variable_kosten': Decimal(0),
            'direkte_kosten': Decimal(0),
            'indirekte_kosten': Decimal(0),
            'kosten': Decimal(0),  # Gesamt-Kosten (für Abwärtskompatibilität)
            'betriebsergebnis': Decimal(0),
            'neutrales_ergebnis': Decimal(0),
            'ergebnis': Decimal(0),  # = Unternehmensergebnis
            'rendite': Decimal(0)
        },
        'bereiche': {b: {'umsatz': Decimal(0), 'einsatz': Decimal(0), 'db1': Decimal(0)} for b in BEREICHE}
    }

    # Lookup-Dicts erstellen
    # Locosoft liefert Tuples: (bereich, jahr, monat, wert)
    umsatz_lookup = {}
    for row in umsatz_rows:
        bereich, jahr, monat, umsatz = row
        key = (bereich, int(jahr), int(monat))
        umsatz_lookup[key] = Decimal(str(umsatz or 0))

    einsatz_lookup = {}
    for row in einsatz_rows:
        bereich, jahr, monat, einsatz = row
        key = (bereich, int(jahr), int(monat))
        einsatz_lookup[key] = Decimal(str(einsatz or 0))

    # TAG157: Separate Kosten-Lookups für BWA-konforme Berechnung
    variable_kosten_lookup = {}
    for row in variable_kosten_rows:
        jahr, monat, kosten = row
        key = (int(jahr), int(monat))
        variable_kosten_lookup[key] = Decimal(str(kosten or 0))

    direkte_kosten_lookup = {}
    for row in direkte_kosten_rows:
        jahr, monat, kosten = row
        key = (int(jahr), int(monat))
        direkte_kosten_lookup[key] = Decimal(str(kosten or 0))

    indirekte_kosten_lookup = {}
    for row in indirekte_kosten_rows:
        jahr, monat, kosten = row
        key = (int(jahr), int(monat))
        indirekte_kosten_lookup[key] = Decimal(str(kosten or 0))

    neutral_lookup = {}
    for row in neutral_rows:
        jahr, monat, neutral = row
        key = (int(jahr), int(monat))
        neutral_lookup[key] = Decimal(str(neutral or 0))

    # Monate durchgehen
    for m in months:
        monat_data = {
            'monat_gj': m['monat_gj'],
            'label': m['label'],
            'bereiche': {},
            'umsatz': Decimal(0),
            'einsatz': Decimal(0),
            'db1': Decimal(0),
            'variable_kosten': Decimal(0),
            'direkte_kosten': Decimal(0),
            'indirekte_kosten': Decimal(0),
            'kosten': Decimal(0),
            'betriebsergebnis': Decimal(0),
            'neutrales_ergebnis': Decimal(0)
        }

        for bereich in BEREICHE:
            key = (bereich, m['jahr'], m['monat_kalender'])
            u = umsatz_lookup.get(key, Decimal(0))
            e = einsatz_lookup.get(key, Decimal(0))
            db1 = u - e

            monat_data['bereiche'][bereich] = {
                'umsatz': float(u),
                'einsatz': float(e),
                'db1': float(db1)
            }
            monat_data['umsatz'] += u
            monat_data['einsatz'] += e
            monat_data['db1'] += db1

            # Gesamt pro Bereich
            result['bereiche'][bereich]['umsatz'] += u
            result['bereiche'][bereich]['einsatz'] += e
            result['bereiche'][bereich]['db1'] += db1

        # TAG157: Kosten und Neutrales Ergebnis wie BWA v2
        kosten_key = (m['jahr'], m['monat_kalender'])
        monat_data['variable_kosten'] = variable_kosten_lookup.get(kosten_key, Decimal(0))
        monat_data['direkte_kosten'] = direkte_kosten_lookup.get(kosten_key, Decimal(0))
        monat_data['indirekte_kosten'] = indirekte_kosten_lookup.get(kosten_key, Decimal(0))
        monat_data['neutrales_ergebnis'] = neutral_lookup.get(kosten_key, Decimal(0))

        # Gesamt-Kosten (für Abwärtskompatibilität)
        monat_data['kosten'] = (monat_data['variable_kosten'] +
                                monat_data['direkte_kosten'] +
                                monat_data['indirekte_kosten'])

        # Betriebsergebnis = DB1 - alle Kosten (wie GlobalCube!)
        monat_data['betriebsergebnis'] = monat_data['db1'] - monat_data['kosten']

        # In float konvertieren für JSON
        monat_data['umsatz'] = float(monat_data['umsatz'])
        monat_data['einsatz'] = float(monat_data['einsatz'])
        monat_data['db1'] = float(monat_data['db1'])
        monat_data['variable_kosten'] = float(monat_data['variable_kosten'])
        monat_data['direkte_kosten'] = float(monat_data['direkte_kosten'])
        monat_data['indirekte_kosten'] = float(monat_data['indirekte_kosten'])
        monat_data['kosten'] = float(monat_data['kosten'])
        monat_data['betriebsergebnis'] = float(monat_data['betriebsergebnis'])
        monat_data['neutrales_ergebnis'] = float(monat_data['neutrales_ergebnis'])

        # Unternehmensergebnis = Betriebsergebnis + Neutrales Ergebnis (wie GlobalCube!)
        monat_data['ergebnis'] = monat_data['betriebsergebnis'] + monat_data['neutrales_ergebnis']

        result['monate'].append(monat_data)

        # Gesamt
        result['gesamt']['umsatz'] += Decimal(str(monat_data['umsatz']))
        result['gesamt']['einsatz'] += Decimal(str(monat_data['einsatz']))
        result['gesamt']['db1'] += Decimal(str(monat_data['db1']))
        result['gesamt']['variable_kosten'] += Decimal(str(monat_data['variable_kosten']))
        result['gesamt']['direkte_kosten'] += Decimal(str(monat_data['direkte_kosten']))
        result['gesamt']['indirekte_kosten'] += Decimal(str(monat_data['indirekte_kosten']))
        result['gesamt']['kosten'] += Decimal(str(monat_data['kosten']))
        result['gesamt']['betriebsergebnis'] += Decimal(str(monat_data['betriebsergebnis']))
        result['gesamt']['neutrales_ergebnis'] += Decimal(str(monat_data['neutrales_ergebnis']))

    # TAG157: Gesamt berechnen - Unternehmensergebnis wie GlobalCube!
    result['gesamt']['ergebnis'] = result['gesamt']['betriebsergebnis'] + result['gesamt']['neutrales_ergebnis']
    if result['gesamt']['umsatz'] > 0:
        result['gesamt']['rendite'] = (result['gesamt']['ergebnis'] / result['gesamt']['umsatz']) * 100

    # In float konvertieren
    for key in result['gesamt']:
        result['gesamt'][key] = float(result['gesamt'][key])
    for bereich in result['bereiche']:
        for key in result['bereiche'][bereich]:
            result['bereiche'][bereich][key] = float(result['bereiche'][bereich][key])

    return result


def get_plan_daten(geschaeftsjahr: str, standort: int = 0) -> Dict[str, Any]:
    """
    Holt Plan-Daten aus unternehmensplan Tabelle

    Args:
        geschaeftsjahr: z.B. '2025/26'
        standort: 0=Alle, 1=DEG, 2=HYU, 3=LAN

    Returns:
        Dict mit geplanten Werten pro Monat und Bereich
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT monat, bereich, umsatz_plan, einsatz_plan, db1_plan, kosten_plan, marge_ziel
        FROM unternehmensplan
        WHERE geschaeftsjahr = %s AND standort = %s
        ORDER BY monat, bereich
    """, (geschaeftsjahr, standort))

    rows = cursor.fetchall()
    conn.close()

    months = get_gj_months(geschaeftsjahr)
    result = {
        'geschaeftsjahr': geschaeftsjahr,
        'standort': standort,
        'monate': [],
        'gesamt': {
            'umsatz': 0,
            'einsatz': 0,
            'db1': 0,
            'kosten': 0,
            'ergebnis': 0,
            'rendite': 0
        },
        'hat_plan': len(rows) > 0
    }

    # Lookup erstellen
    plan_lookup = {}
    for row in rows:
        key = (row['monat'], row['bereich'])
        plan_lookup[key] = {
            'umsatz': float(row['umsatz_plan'] or 0),
            'einsatz': float(row['einsatz_plan'] or 0),
            'db1': float(row['db1_plan'] or 0),
            'kosten': float(row['kosten_plan'] or 0),
            'marge_ziel': float(row['marge_ziel'] or 0)
        }

    for m in months:
        monat_data = {
            'monat_gj': m['monat_gj'],
            'label': m['label'],
            'bereiche': {},
            'umsatz': 0,
            'einsatz': 0,
            'db1': 0,
            'kosten': 0
        }

        for bereich in BEREICHE:
            key = (m['monat_gj'], bereich)
            if key in plan_lookup:
                monat_data['bereiche'][bereich] = plan_lookup[key]
                monat_data['umsatz'] += plan_lookup[key]['umsatz']
                monat_data['einsatz'] += plan_lookup[key]['einsatz']
                monat_data['db1'] += plan_lookup[key]['db1']
            else:
                monat_data['bereiche'][bereich] = {'umsatz': 0, 'einsatz': 0, 'db1': 0}

        # Kosten
        kosten_key = (m['monat_gj'], 'Kosten')
        if kosten_key in plan_lookup:
            monat_data['kosten'] = plan_lookup[kosten_key]['kosten']

        monat_data['ergebnis'] = monat_data['db1'] - monat_data['kosten']
        result['monate'].append(monat_data)

        # Gesamt
        result['gesamt']['umsatz'] += monat_data['umsatz']
        result['gesamt']['einsatz'] += monat_data['einsatz']
        result['gesamt']['db1'] += monat_data['db1']
        result['gesamt']['kosten'] += monat_data['kosten']

    result['gesamt']['ergebnis'] = result['gesamt']['db1'] - result['gesamt']['kosten']
    if result['gesamt']['umsatz'] > 0:
        result['gesamt']['rendite'] = (result['gesamt']['ergebnis'] / result['gesamt']['umsatz']) * 100

    return result


def get_gap_analyse(geschaeftsjahr: str, standort: int = 0) -> Dict[str, Any]:
    """
    Berechnet IST vs PLAN Abweichung und Gap zum 1%-Ziel

    Args:
        geschaeftsjahr: z.B. '2025/26'
        standort: 0=Alle

    Returns:
        Dict mit Gap-Analyse und Handlungsempfehlungen
    """
    # TAG162: Alle Monate mit Daten für tägliche Aktualisierung
    ist = get_ist_daten(geschaeftsjahr, standort, nur_abgeschlossene=False)
    plan = get_plan_daten(geschaeftsjahr, standort)

    # Aktueller Monat im GJ bestimmen
    heute = date.today()
    start_jahr = int(geschaeftsjahr.split('/')[0])
    if heute.month >= 9:
        aktueller_monat_gj = heute.month - 8  # Sep=1, Okt=2, ...
    else:
        aktueller_monat_gj = heute.month + 4  # Jan=5, Feb=6, ...

    # IST bis aktueller Monat summieren
    ist_ytd = {
        'umsatz': sum(m['umsatz'] for m in ist['monate'][:aktueller_monat_gj]),
        'einsatz': sum(m['einsatz'] for m in ist['monate'][:aktueller_monat_gj]),
        'db1': sum(m['db1'] for m in ist['monate'][:aktueller_monat_gj]),
        'kosten': sum(m['kosten'] for m in ist['monate'][:aktueller_monat_gj])
    }
    ist_ytd['ergebnis'] = ist_ytd['db1'] - ist_ytd['kosten']
    ist_ytd['rendite'] = (ist_ytd['ergebnis'] / ist_ytd['umsatz'] * 100) if ist_ytd['umsatz'] > 0 else 0

    # Ziel: 1% vom Umsatz
    ziel_ergebnis_ytd = ist_ytd['umsatz'] * 0.01
    gap_ytd = ziel_ergebnis_ytd - ist_ytd['ergebnis']

    # Hochrechnung auf Jahresende
    monate_verbleibend = 12 - aktueller_monat_gj
    durchschnitt_monat = {
        'umsatz': ist_ytd['umsatz'] / aktueller_monat_gj if aktueller_monat_gj > 0 else 0,
        'db1': ist_ytd['db1'] / aktueller_monat_gj if aktueller_monat_gj > 0 else 0,
        'kosten': ist_ytd['kosten'] / aktueller_monat_gj if aktueller_monat_gj > 0 else 0
    }

    prognose_jahresende = {
        'umsatz': ist_ytd['umsatz'] + (durchschnitt_monat['umsatz'] * monate_verbleibend),
        'db1': ist_ytd['db1'] + (durchschnitt_monat['db1'] * monate_verbleibend),
        'kosten': ist_ytd['kosten'] + (durchschnitt_monat['kosten'] * monate_verbleibend)
    }
    prognose_jahresende['ergebnis'] = prognose_jahresende['db1'] - prognose_jahresende['kosten']
    prognose_jahresende['rendite'] = (prognose_jahresende['ergebnis'] / prognose_jahresende['umsatz'] * 100) if prognose_jahresende['umsatz'] > 0 else 0

    ziel_ergebnis_jahr = prognose_jahresende['umsatz'] * 0.01
    gap_jahresende = ziel_ergebnis_jahr - prognose_jahresende['ergebnis']

    # Bereiche analysieren (wo ist am meisten zu holen?)
    bereich_potenzial = []
    for bereich, daten in ist['bereiche'].items():
        if daten['umsatz'] > 0:
            aktuelle_marge = (daten['db1'] / daten['umsatz']) * 100
            # Branchentypische Margen
            ziel_margen = {
                'NW': 8.0,
                'GW': 5.0,
                'Teile': 28.0,
                'Werkstatt': 55.0,
                'Sonstige': 50.0
            }
            ziel_marge = ziel_margen.get(bereich, 10.0)
            potenzial_db1 = (daten['umsatz'] * ziel_marge / 100) - daten['db1']

            bereich_potenzial.append({
                'bereich': bereich,
                'umsatz': daten['umsatz'],
                'db1': daten['db1'],
                'marge_ist': round(aktuelle_marge, 1),
                'marge_ziel': ziel_marge,
                'potenzial_db1': round(potenzial_db1, 0),
                'status': 'ok' if aktuelle_marge >= ziel_marge else ('warnung' if aktuelle_marge >= ziel_marge * 0.8 else 'kritisch')
            })

    # Nach Potenzial sortieren
    bereich_potenzial.sort(key=lambda x: x['potenzial_db1'], reverse=True)

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'aktueller_monat': aktueller_monat_gj,
        'monate_verbleibend': monate_verbleibend,
        'ziel_rendite': 1.0,

        'ist_ytd': ist_ytd,
        'ziel_ytd': {
            'ergebnis': round(ziel_ergebnis_ytd, 0),
            'rendite': 1.0
        },
        'gap_ytd': round(gap_ytd, 0),

        'prognose_jahresende': {
            'umsatz': round(prognose_jahresende['umsatz'], 0),
            'ergebnis': round(prognose_jahresende['ergebnis'], 0),
            'rendite': round(prognose_jahresende['rendite'], 2)
        },
        'ziel_jahresende': {
            'ergebnis': round(ziel_ergebnis_jahr, 0),
            'rendite': 1.0
        },
        'gap_jahresende': round(gap_jahresende, 0),

        'bereiche': bereich_potenzial,

        'empfehlungen': _generate_empfehlungen(gap_jahresende, bereich_potenzial, monate_verbleibend)
    }


def _generate_empfehlungen(gap: float, bereiche: List[Dict], monate: int) -> List[str]:
    """Generiert Handlungsempfehlungen basierend auf Gap-Analyse"""
    empfehlungen = []

    if gap <= 0:
        empfehlungen.append("✅ 1%-Ziel wird voraussichtlich erreicht!")
        return empfehlungen

    gap_pro_monat = gap / monate if monate > 0 else gap
    empfehlungen.append(f"⚠️ Gap zum 1%-Ziel: {gap:,.0f} € ({gap_pro_monat:,.0f} €/Monat nötig)")

    for b in bereiche:
        if b['status'] == 'kritisch' and b['potenzial_db1'] > 10000:
            empfehlungen.append(f"🔴 {b['bereich']}: Marge {b['marge_ist']}% → {b['marge_ziel']}% = +{b['potenzial_db1']:,.0f} € DB1")
        elif b['status'] == 'warnung' and b['potenzial_db1'] > 5000:
            empfehlungen.append(f"🟡 {b['bereich']}: Marge optimieren ({b['marge_ist']}% → {b['marge_ziel']}%)")

    return empfehlungen


def get_kumulierte_ytd_ansicht(geschaeftsjahr: str, standort: int = 0) -> Dict[str, Any]:
    """
    Kumulierte YTD-Ansicht für 1%-Ziel-Tracking

    Zeigt:
    - Monatliche Entwicklung mit kumulierten Werten (nur abgeschlossene Kalendermonate)
    - 1%-Ziel-Erreichung pro Monat
    - Trend-Analyse
    - Prognose für Jahresende

    WICHTIG: Der laufende Kalendermonat wird NICHT kumuliert (nur vergangene Monate)

    Args:
        geschaeftsjahr: z.B. '2025/26'
        standort: 0=Alle, 1=DEG, 2=HYU, 3=LAN

    Returns:
        Dict mit kumulierten Monatsdaten und Prognosen
    """
    # TAG162: Alle Monate mit Daten holen, aber nur abgeschlossene kumulieren
    ist = get_ist_daten(geschaeftsjahr, standort, nur_abgeschlossene=False)

    # Aktueller Kalendermonat (der NICHT kumuliert wird)
    heute = date.today()
    aktueller_kalendermonat = heute.month
    aktuelles_kalenderjahr = heute.year

    # GJ-Monat berechnen, bis zu dem kumuliert wird (Vormonat)
    start_jahr = int(geschaeftsjahr.split('/')[0])

    # Monatsnamen
    monat_namen = ['Sep', 'Okt', 'Nov', 'Dez', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug']

    # Kumulierte Werte berechnen
    kum_umsatz = 0
    kum_db1 = 0
    kum_kosten = 0
    monate_mit_daten = []

    for i, m in enumerate(ist['monate']):
        # Kalendermonat und Jahr für diesen GJ-Monat
        if i < 4:  # Sep-Dez
            kalender_monat = 9 + i
            kalender_jahr = start_jahr
        else:  # Jan-Aug
            kalender_monat = i - 3
            kalender_jahr = start_jahr + 1

        # Ist dieser Monat der aktuelle (laufende) Monat?
        ist_aktueller_monat = (kalender_monat == aktueller_kalendermonat and
                               kalender_jahr == aktuelles_kalenderjahr)

        # Nur vergangene Monate mit Daten in Kumulierung aufnehmen (nicht der laufende!)
        if (m['umsatz'] > 0 or m['kosten'] > 0) and not ist_aktueller_monat:
            kum_umsatz += m['umsatz']
            kum_db1 += m['db1']
            kum_kosten += m['kosten']
            kum_ergebnis = kum_db1 - kum_kosten
            kum_rendite = (kum_ergebnis / kum_umsatz * 100) if kum_umsatz > 0 else 0

            # 1%-Ziel für kumulierten Umsatz
            ziel_1pct = kum_umsatz * 0.01
            gap_zu_ziel = kum_ergebnis - ziel_1pct
            erreichung_pct = (kum_ergebnis / ziel_1pct * 100) if ziel_1pct != 0 else 0

            monate_mit_daten.append({
                'monat_gj': i + 1,
                'label': monat_namen[i],
                'monat': {
                    'umsatz': round(m['umsatz'], 0),
                    'db1': round(m['db1'], 0),
                    'kosten': round(m['kosten'], 0),
                    'ergebnis': round(m['betriebsergebnis'], 0),
                    'rendite_pct': round((m['betriebsergebnis'] / m['umsatz'] * 100) if m['umsatz'] > 0 else 0, 2)
                },
                'kumuliert': {
                    'umsatz': round(kum_umsatz, 0),
                    'db1': round(kum_db1, 0),
                    'kosten': round(kum_kosten, 0),
                    'ergebnis': round(kum_ergebnis, 0),
                    'rendite_pct': round(kum_rendite, 2)
                },
                'ziel_1pct': {
                    'ergebnis': round(ziel_1pct, 0),
                    'gap': round(gap_zu_ziel, 0),
                    'erreichung_pct': round(erreichung_pct, 1),
                    'status': 'positiv' if gap_zu_ziel >= 0 else ('warnung' if erreichung_pct >= -50 else 'negativ')
                }
            })

    # Aktuelle Periode
    anzahl_monate = len(monate_mit_daten)

    if anzahl_monate == 0:
        return {
            'geschaeftsjahr': geschaeftsjahr,
            'standort': standort,
            'monate': [],
            'ytd': {},
            'prognose': {},
            'status': 'keine_daten'
        }

    # YTD-Zusammenfassung
    ytd = monate_mit_daten[-1]['kumuliert'].copy()
    ytd_ziel = monate_mit_daten[-1]['ziel_1pct'].copy()

    # Durchschnittswerte pro Monat
    avg_umsatz = kum_umsatz / anzahl_monate
    avg_db1 = kum_db1 / anzahl_monate
    avg_kosten = kum_kosten / anzahl_monate
    avg_ergebnis = (kum_db1 - kum_kosten) / anzahl_monate

    # Prognose für Jahresende (12 Monate)
    monate_verbleibend = 12 - anzahl_monate

    prognose_umsatz = kum_umsatz + (avg_umsatz * monate_verbleibend)
    prognose_db1 = kum_db1 + (avg_db1 * monate_verbleibend)
    prognose_kosten = kum_kosten + (avg_kosten * monate_verbleibend)
    prognose_ergebnis = prognose_db1 - prognose_kosten
    prognose_rendite = (prognose_ergebnis / prognose_umsatz * 100) if prognose_umsatz > 0 else 0

    # 1%-Ziel für prognostizierten Jahresumsatz
    prognose_ziel_1pct = prognose_umsatz * 0.01
    prognose_gap = prognose_ergebnis - prognose_ziel_1pct

    # Notwendige Verbesserung pro Monat um 1%-Ziel zu erreichen
    if monate_verbleibend > 0 and prognose_gap < 0:
        verbesserung_pro_monat = abs(prognose_gap) / monate_verbleibend
    else:
        verbesserung_pro_monat = 0

    return {
        'geschaeftsjahr': geschaeftsjahr,
        'standort': standort,
        'anzahl_monate': anzahl_monate,
        'monate_verbleibend': monate_verbleibend,
        'monate': monate_mit_daten,
        'ytd': {
            'umsatz': ytd['umsatz'],
            'db1': ytd['db1'],
            'kosten': ytd['kosten'],
            'ergebnis': ytd['ergebnis'],
            'rendite_pct': ytd['rendite_pct'],
            'ziel_1pct': ytd_ziel['ergebnis'],
            'gap': ytd_ziel['gap'],
            'status': ytd_ziel['status']
        },
        'durchschnitt_monat': {
            'umsatz': round(avg_umsatz, 0),
            'db1': round(avg_db1, 0),
            'kosten': round(avg_kosten, 0),
            'ergebnis': round(avg_ergebnis, 0)
        },
        'prognose_jahresende': {
            'umsatz': round(prognose_umsatz, 0),
            'db1': round(prognose_db1, 0),
            'kosten': round(prognose_kosten, 0),
            'ergebnis': round(prognose_ergebnis, 0),
            'rendite_pct': round(prognose_rendite, 2),
            'ziel_1pct': round(prognose_ziel_1pct, 0),
            'gap': round(prognose_gap, 0),
            'status': 'positiv' if prognose_gap >= 0 else 'negativ'
        },
        'verbesserung_noetig': {
            'pro_monat': round(verbesserung_pro_monat, 0),
            'gesamt': round(abs(prognose_gap) if prognose_gap < 0 else 0, 0)
        }
    }


def save_plan(geschaeftsjahr: str, standort: int, plan_data: Dict, erstellt_von: str) -> bool:
    """
    Speichert einen Unternehmensplan

    Args:
        geschaeftsjahr: z.B. '2025/26'
        standort: 0=Alle, 1=DEG, etc.
        plan_data: Dict mit Monatsdaten pro Bereich
        erstellt_von: Username

    Returns:
        True bei Erfolg
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        for monat, monat_data in plan_data.items():
            for bereich, werte in monat_data.items():
                cursor.execute("""
                    INSERT INTO unternehmensplan
                    (geschaeftsjahr, monat, bereich, standort, umsatz_plan, einsatz_plan, db1_plan, kosten_plan, marge_ziel, erstellt_von)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (geschaeftsjahr, monat, bereich, standort)
                    DO UPDATE SET
                        umsatz_plan = EXCLUDED.umsatz_plan,
                        einsatz_plan = EXCLUDED.einsatz_plan,
                        db1_plan = EXCLUDED.db1_plan,
                        kosten_plan = EXCLUDED.kosten_plan,
                        marge_ziel = EXCLUDED.marge_ziel,
                        erstellt_von = EXCLUDED.erstellt_von,
                        geaendert_am = CURRENT_TIMESTAMP
                """, (
                    geschaeftsjahr,
                    int(monat),
                    bereich,
                    standort,
                    werte.get('umsatz', 0),
                    werte.get('einsatz', 0),
                    werte.get('db1', 0),
                    werte.get('kosten', 0),
                    werte.get('marge_ziel')
                ))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
