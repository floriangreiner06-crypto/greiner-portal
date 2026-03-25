#!/usr/bin/env python3
"""
Werkstatt-Prämien: Mockup mit Realdaten aus Locosoft (und optional drive_portal)
================================================================================
Befüllt die Prämiensystem-Struktur mit echten Daten aus times, labours,
absence_calendar, employees_history, employees_worktimes.

Aufruf:
  python scripts/verguetung/werkstatt_praemien_realdaten.py [YYYY-MM]
  Ohne Argument: Vormonat.

Ausgabe:
  - docs/workstreams/verguetung/Mockup_Werkstatt_Praemien_Realdaten.html
  - docs/workstreams/verguetung/Mockup_Werkstatt_Praemien_Realdaten.csv
  - Optional: Sync-Ordner (wenn /mnt/greiner-portal-sync existiert)
"""

import sys
import os
from datetime import date, timedelta
from calendar import monthrange

# Projekt-Root für Imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from api.db_utils import locosoft_session, rows_to_list
from api.werkstatt_data import WerkstattData
from api.standort_utils import BETRIEB_NAMEN
from psycopg2.extras import RealDictCursor


def get_month_range(year_month: str):
    """'YYYY-MM' -> (first_day, last_day)."""
    y, m = int(year_month[:4]), int(year_month[5:7])
    first = date(y, m, 1)
    last = date(y, m, monthrange(y, m)[1])
    return first, last


def get_mechaniker_mit_stammdaten(bis: date):
    """Mechaniker-Liste inkl. Name, Standort, productivity_factor."""
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                eh.employee_number,
                eh.name,
                eh.subsidiary,
                COALESCE(eh.productivity_factor, 1) as productivity_factor
            FROM employees_history eh
            WHERE eh.is_latest_record = true
              AND eh.mechanic_number IS NOT NULL
              AND eh.subsidiary IN (1, 2, 3)
              AND (eh.leave_date IS NULL OR eh.leave_date > %s)
            ORDER BY eh.subsidiary, eh.name
        """, (bis,))
        return rows_to_list(cur.fetchall())


def get_soll_stunden_pro_monat(von: date, bis: date) -> dict:
    """Soll-Anwesenheitsstunden pro MA aus employees_worktimes × Arbeitstage im Monat."""
    # Arbeitstage pro Wochentag (0=Mo .. 6=So) im Zeitraum
    from collections import defaultdict
    weekdays = defaultdict(int)
    d = von
    while d <= bis:
        if d.weekday() < 5:  # Mo=0 .. Fr=4
            weekdays[d.weekday()] += 1
        d += timedelta(days=1)

    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Pro MA: letzte work_duration pro dayofweek (Locosoft: 1=Mo?)
        cur.execute("""
            WITH latest AS (
                SELECT DISTINCT ON (employee_number, dayofweek)
                    employee_number, dayofweek, COALESCE(work_duration, 8) as work_duration
                FROM employees_worktimes
                WHERE is_latest_record = true
                ORDER BY employee_number, dayofweek, validity_date DESC
            )
            SELECT employee_number, dayofweek, work_duration
            FROM latest
        """)
        rows = cur.fetchall()

    # dayofweek in Locosoft: prüfen ob 0=So oder 1=Mo. Typisch 1=Mo.
    # Python: weekday() 0=Mo, 6=So. Wir zählen Mo=0..Fr=4.
    # Locosoft employees_worktimes dayofweek oft 1-5 für Mo-Fr
    per_ma = {}
    for r in rows:
        eno = r['employee_number']
        dow = int(r['dayofweek'] or 0)
        # Wenn Locosoft 1=Mo: dow 1->0, 2->1, ... 5->4
        if dow >= 1 and dow <= 5:
            py_dow = dow - 1  # 1->0 (Mo), 5->4 (Fr)
        else:
            py_dow = dow
        if py_dow < 0 or py_dow > 4:
            continue
        if eno not in per_ma:
            per_ma[eno] = [0.0] * 5
        per_ma[eno][py_dow] = float(r['work_duration'] or 8)

    default_stunden_pro_tag = 8.0
    result = {}
    for eno, stunden_pro_wochentag in per_ma.items():
        soll = 0.0
        for py_dow in range(5):
            days = weekdays.get(py_dow, 0)
            h = stunden_pro_wochentag[py_dow] if py_dow < len(stunden_pro_wochentag) else None
            soll += (h if h and h > 0 else default_stunden_pro_tag) * days
        result[eno] = round(soll, 1)
    return result


def get_fehlstunden(von: date, bis: date) -> dict:
    """Fehlstunden pro MA aus absence_calendar (time_from/time_to oder 8h/Tag)."""
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                employee_number,
                date,
                time_from,
                time_to,
                EXTRACT(EPOCH FROM (COALESCE(time_to, time_from + INTERVAL '8 hours') - time_from)) / 3600.0 as stunden
            FROM absence_calendar
            WHERE date >= %s AND date <= %s
        """, (von, bis))
        rows = cur.fetchall()

    per_ma = {}
    for r in rows:
        eno = r['employee_number']
        if r['time_from'] and r['time_to']:
            h = float(r['stunden'] or 0)
        else:
            h = 8.0  # Volle Tagesschätzung
        per_ma[eno] = per_ma.get(eno, 0) + h
    return {k: round(v, 1) for k, v in per_ma.items()}


def get_abgerechnete_stunden(von: date, bis: date) -> dict:
    """Abgerechnete Stunden (intern/extern) aus labours is_invoiced, Aufträge mit order_date im Monat.
    time_units in 10-Min -> Stunden = time_units/6.
    """
    with locosoft_session() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                l.mechanic_no as employee_number,
                SUM(CASE WHEN l.labour_type = 'I' THEN l.time_units ELSE 0 END) / 6.0 as std_intern,
                SUM(CASE WHEN COALESCE(l.labour_type, '') != 'I' THEN l.time_units ELSE 0 END) / 6.0 as std_extern
            FROM labours l
            JOIN orders o ON l.order_number = o.number
            WHERE l.is_invoiced = true
              AND l.mechanic_no IS NOT NULL
              AND l.time_units > 0
              AND o.order_date >= %s AND o.order_date <= %s
            GROUP BY l.mechanic_no
        """, (von, bis))
        rows = cur.fetchall()

    result = {}
    for r in rows:
        eno = r['employee_number']
        result[eno] = {
            'intern': round(float(r['std_intern'] or 0), 1),
            'extern': round(float(r['std_extern'] or 0), 1),
        }
        result[eno]['gesamt'] = result[eno]['intern'] + result[eno]['extern']
    return result


def build_rows(von: date, bis: date):
    """Alle Zeilen für das Prämiensystem (Realdaten)."""
    mechaniker = get_mechaniker_mit_stammdaten(bis)
    if not mechaniker:
        return [], von, bis, {}

    anwesenheit_ist = WerkstattData.get_anwesenheit_aus_times(von, bis)
    stempelzeit = WerkstattData.get_stempelzeit_aus_times(von, bis)
    vorgabe = WerkstattData.get_vorgabezeit_aus_labours(von, bis)  # vorgabezeit_std, aw, umsatz
    soll_stunden = get_soll_stunden_pro_monat(von, bis)
    fehlstunden = get_fehlstunden(von, bis)
    abgerechnet = get_abgerechnete_stunden(von, bis)

    # Fallback Soll: wenn keine employees_worktimes → 8h × Arbeitstage
    total_arbeitstage = sum(1 for d in range((bis - von).days + 1) if (von + timedelta(days=d)).weekday() < 5)
    default_soll = total_arbeitstage * 8.0

    rows = []
    for i, ma in enumerate(mechaniker, 1):
        eno = ma['employee_number']
        name = (ma['name'] or '').strip() or f"MA {eno}"
        subsidiary = ma['subsidiary'] or 0
        standort = BETRIEB_NAMEN.get(subsidiary, '?')
        pf = float(ma['productivity_factor'] or 1)

        anw_gesamt = soll_stunden.get(eno, 0) or default_soll
        fehl = fehlstunden.get(eno, 0)
        verfuegbar = max(0, anw_gesamt - fehl) * pf
        prod_gesamt = round(stempelzeit.get(eno, 0), 1)
        # Produktiv extern/intern: aus labours nicht trivial pro Stempelung; wir nutzen gleiche Ratio wie abgerechnet
        abg = abgerechnet.get(eno, {'gesamt': 0, 'intern': 0, 'extern': 0})
        abg_gesamt = abg['gesamt']
        abg_intern = abg['intern']
        abg_extern = abg['extern']
        if abg_gesamt > 0:
            ratio_i = abg_intern / abg_gesamt
            ratio_e = abg_extern / abg_gesamt
        else:
            ratio_i = ratio_e = 0.5
        prod_intern = round(prod_gesamt * ratio_i, 1)
        prod_extern = round(prod_gesamt * ratio_e, 1)

        ist_prod = round(prod_gesamt / verfuegbar, 4) if verfuegbar > 0 else None
        ist_leist = round(abg_gesamt / prod_gesamt, 4) if prod_gesamt > 0 else None
        vorgabe_std = vorgabe.get(eno, {}).get('vorgabezeit_std') or 0
        ist_eff = round(abg_gesamt / vorgabe_std, 4) if vorgabe_std > 0 else None
        umsatz = vorgabe.get(eno, {}).get('umsatz') or 0

        rows.append({
            'nr': i,
            'name': name,
            'standort': standort,
            'funktion': 'Mechaniker',  # Kein Mapping Werkstattleiter/Azubi in Locosoft
            'anw_gesamt': anw_gesamt,
            'fehl': fehl,
            'pf': pf,
            'verfuegbar': round(verfuegbar, 1),
            'prod_gesamt': prod_gesamt,
            'prod_extern': prod_extern,
            'prod_intern': prod_intern,
            'ist_prod': ist_prod,
            'abg_gesamt': round(abg_gesamt, 1),
            'abg_intern': abg_intern,
            'abg_extern': abg_extern,
            'ist_leist': ist_leist,
            'vorgabe_std': vorgabe_std,
            'ist_eff': ist_eff,
            'umsatz': round(umsatz, 2),
            'anmerkung': '',
        })

    # --- TEAM-KPIs entscheiden über die Prämienstufe (nicht Einzelwerte) ---
    team_verfuegbar = sum(r['verfuegbar'] for r in rows)
    team_prod = sum(r['prod_gesamt'] for r in rows)
    team_abg = sum(r['abg_gesamt'] for r in rows)
    team_vorgabe = sum(r['vorgabe_std'] for r in rows)

    team_ist_prod = round(team_prod / team_verfuegbar, 4) if team_verfuegbar > 0 else None
    team_ist_leist = round(team_abg / team_prod, 4) if team_prod > 0 else None
    team_ist_eff = round(team_abg / team_vorgabe, 4) if team_vorgabe > 0 else None

    def stufe_prod(v):
        if v is None: return None, 0
        if v >= 0.80: return "Stufe 1: 80%", 100
        if v >= 0.50: return "Stufe 1: 50%", 75
        return "—", 0

    def stufe_leist(v):
        if v is None: return None, 0
        if v >= 0.95: return "Stufe 1: 95%", 150
        if v >= 0.80: return "Stufe 1: 80%", 100
        return "—", 0

    def stufe_eff(v):
        if v is None: return None, 0
        if v >= 0.85: return "Stufe 1: 85%", 100
        if v >= 0.70: return "Stufe 1: 70%", 75
        return "—", 0

    team_stufe_prod, team_prämie_prod = stufe_prod(team_ist_prod)
    team_stufe_leist, team_prämie_leist = stufe_leist(team_ist_leist)
    team_stufe_eff, team_prämie_eff = stufe_eff(team_ist_eff)

    # Prämie wird pro Mitarbeiter ausgezahlt, Betrag kommt aus TEAM-Stufe (alle bekommen dieselbe Stufe)
    for r in rows:
        r['team_prod'] = team_ist_prod
        r['team_leist'] = team_ist_leist
        r['team_eff'] = team_ist_eff
        r['stufe_prod'] = team_stufe_prod
        r['stufe_leist'] = team_stufe_leist
        r['stufe_eff'] = team_stufe_eff
        r['prämie_prod'] = team_prämie_prod
        r['prämie_leist'] = team_prämie_leist
        r['prämie_eff'] = team_prämie_eff

    team_info = {
        'verfuegbar': team_verfuegbar,
        'prod': team_prod,
        'abg': team_abg,
        'vorgabe': team_vorgabe,
        'ist_prod': team_ist_prod,
        'ist_leist': team_ist_leist,
        'ist_eff': team_ist_eff,
        'stufe_prod': team_stufe_prod,
        'stufe_leist': team_stufe_leist,
        'stufe_eff': team_stufe_eff,
        'prämie_prod': team_prämie_prod,
        'prämie_leist': team_prämie_leist,
        'prämie_eff': team_prämie_eff,
    }
    return rows, von, bis, team_info


def format_num(v):
    if v is None: return "—"
    if isinstance(v, float):
        if v == int(v): return str(int(v))
        return f"{v:.2f}".replace('.', ',')
    return str(v)


def write_html(rows, von, bis, team_info, out_path):
    standorte = "DEG = Deggendorf Opel, HYU = Deggendorf Hyundai, LAN = Landau"
    total_prod = sum(r['prämie_prod'] for r in rows)
    total_leist = sum(r['prämie_leist'] for r in rows)
    total_eff = sum(r['prämie_eff'] for r in rows)

    # Team-KPIs-Box (entscheidend für die Prämienstufe)
    team_box = ""
    if team_info:
        t = team_info
        team_box = f"""
    <div style="background:#e8f4ea; border:1px solid #c8e6c9; padding:10px; margin-bottom:12px; border-radius:4px;">
      <strong>Team-KPIs (maßgeblich für die Prämie)</strong> — Auszahlung pro Mitarbeiter, Stufe aus Teamleistung:<br>
      Produktivität (Team): {format_num(t.get('ist_prod'))} → {t.get('stufe_prod') or '—'} → {t.get('prämie_prod') or 0} €/MA &nbsp;|&nbsp;
      Leistungsgrad (Team): {format_num(t.get('ist_leist'))} → {t.get('stufe_leist') or '—'} → {t.get('prämie_leist') or 0} €/MA &nbsp;|&nbsp;
      Effektivität (Team): {format_num(t.get('ist_eff'))} → {t.get('stufe_eff') or '—'} → {t.get('prämie_eff') or 0} €/MA
    </div>
"""

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Prämienkonzept Werkstatt — Realdaten {von.strftime("%Y-%m")}</title>
  <style>
    body {{ font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 12px; margin: 16px; background: #f5f5f5; }}
    .sheet {{ background: #fff; max-width: 100%; overflow-x: auto; box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 12px; }}
    h1 {{ font-size: 14px; color: #333; }}
    .subtitle {{ font-size: 11px; color: #666; margin-bottom: 12px; }}
    table {{ border-collapse: collapse; min-width: 1200px; font-size: 11px; }}
    th, td {{ border: 1px solid #ccc; padding: 4px 6px; }}
    th {{ background: #e0e0e0; font-weight: 600; text-align: center; }}
    td.num {{ text-align: right; }}
    .summe {{ font-weight: 600; background: #f5f5f5; }}
  </style>
</head>
<body>
  <div class="sheet">
    <h1>Prämienkonzept Werkstatt — Realdaten</h1>
    <p class="subtitle">Monat: {von.strftime("%d.%m.%Y")} – {bis.strftime("%d.%m.%Y")} | Standorte: {standorte} | Daten: Locosoft. <strong>Prämie wird pro MA ausgezahlt, die Stufe/Betrag richtet sich nach den Team-KPIs.</strong></p>
    {team_box}
    <table>
      <thead>
        <tr>
          <th>#</th><th>Mitarbeiter</th><th>Standort</th><th>Funktion</th>
          <th>Anw. gesamt</th><th>Fehlstd.</th><th>P-Faktor</th><th>Verfügb. Std</th>
          <th>Produkt. gesamt</th><th>extern</th><th>intern</th>
          <th>IST Prod.<br><small>(einzeln)</small></th><th>Team Prod.</th><th>ZIEL/Stufe</th><th>Prämie €</th>
          <th>Abg. gesamt</th><th>Abg. intern</th><th>Abg. extern</th>
          <th>IST Leist.<br><small>(einzeln)</small></th><th>Team Leist.</th><th>ZIEL/Stufe</th><th>Prämie €</th>
          <th>IST Eff.<br><small>(einzeln)</small></th><th>Team Eff.</th><th>ZIEL/Stufe</th><th>Prämie €</th>
          <th>Umsatz</th>
        </tr>
      </thead>
      <tbody>
'''
    for r in rows:
        html += f'''        <tr>
          <td>{r['nr']}</td>
          <td>{r['name']}</td>
          <td>{r['standort']}</td>
          <td>{r['funktion']}</td>
          <td class="num">{format_num(r['anw_gesamt'])}</td>
          <td class="num">{format_num(r['fehl'])}</td>
          <td class="num">{format_num(r['pf'])}</td>
          <td class="num">{format_num(r['verfuegbar'])}</td>
          <td class="num">{format_num(r['prod_gesamt'])}</td>
          <td class="num">{format_num(r['prod_extern'])}</td>
          <td class="num">{format_num(r['prod_intern'])}</td>
          <td class="num">{format_num(r['ist_prod'])}</td>
          <td class="num">{format_num(r['team_prod'])}</td>
          <td>{r['stufe_prod'] or '—'}</td>
          <td class="num">{r['prämie_prod']}</td>
          <td class="num">{format_num(r['abg_gesamt'])}</td>
          <td class="num">{format_num(r['abg_intern'])}</td>
          <td class="num">{format_num(r['abg_extern'])}</td>
          <td class="num">{format_num(r['ist_leist'])}</td>
          <td class="num">{format_num(r['team_leist'])}</td>
          <td>{r['stufe_leist'] or '—'}</td>
          <td class="num">{r['prämie_leist']}</td>
          <td class="num">{format_num(r['ist_eff'])}</td>
          <td class="num">{format_num(r['team_eff'])}</td>
          <td>{r['stufe_eff'] or '—'}</td>
          <td class="num">{r['prämie_eff']}</td>
          <td class="num">{format_num(r['umsatz'])}</td>
        </tr>
'''
    html += f'''        <tr class="summe">
          <td colspan="14">Prämiensumme Produktivität (Team-Stufe × Anzahl MA)</td>
          <td class="num">{total_prod} €</td>
          <td colspan="6">Prämiensumme Leistungsgrad</td>
          <td class="num">{total_leist} €</td>
          <td colspan="4">Prämiensumme Effektivität</td>
          <td class="num">{total_eff} €</td>
        </tr>
      </tbody>
    </table>
  </div>
</body>
</html>
'''
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def write_csv(rows, von, bis, out_path):
    import csv
    if not rows:
        return
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['#', 'Mitarbeiter', 'Standort', 'Funktion', 'Anw_gesamt', 'Fehlstunden', 'P-Faktor', 'Verfuegbar',
                    'Prod_gesamt', 'Prod_extern', 'Prod_intern', 'IST_Prod', 'Team_Prod', 'Stufe_Prod', 'Praemie_Prod',
                    'Abg_gesamt', 'Abg_intern', 'Abg_extern', 'IST_Leist', 'Team_Leist', 'Stufe_Leist', 'Praemie_Leist',
                    'IST_Eff', 'Team_Eff', 'Stufe_Eff', 'Praemie_Eff', 'Umsatz'])
        for r in rows:
            w.writerow([
                r['nr'], r['name'], r['standort'], r['funktion'],
                r['anw_gesamt'], r['fehl'], r['pf'], r['verfuegbar'],
                r['prod_gesamt'], r['prod_extern'], r['prod_intern'],
                format_num(r['ist_prod']), format_num(r['team_prod']), r['stufe_prod'] or '', r['prämie_prod'],
                r['abg_gesamt'], r['abg_intern'], r['abg_extern'],
                format_num(r['ist_leist']), format_num(r['team_leist']), r['stufe_leist'] or '', r['prämie_leist'],
                format_num(r['ist_eff']), format_num(r['team_eff']), r['stufe_eff'] or '', r['prämie_eff'],
                r['umsatz']
            ])


def main():
    if len(sys.argv) >= 2:
        year_month = sys.argv[1]
        try:
            von, bis = get_month_range(year_month)
        except Exception:
            print("Ungültiges Datum. Nutze: YYYY-MM (z.B. 2026-01)")
            sys.exit(1)
    else:
        today = date.today()
        first = date(today.year, today.month, 1)
        von = first - timedelta(days=1)
        von = date(von.year, von.month, 1)
        bis = date(von.year, von.month, monthrange(von.year, von.month)[1])

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_dir = os.path.join(base, 'docs', 'workstreams', 'verguetung')
    os.makedirs(out_dir, exist_ok=True)
    prefix = os.path.join(out_dir, 'Mockup_Werkstatt_Praemien_Realdaten')

    print(f"Berechne Prämien für {von.strftime('%Y-%m')} ...")
    rows, v, b, team_info = build_rows(von, bis)
    if not rows:
        print("Keine Mechaniker gefunden.")
        sys.exit(0)

    html_path = prefix + '.html'
    csv_path = prefix + '.csv'
    write_html(rows, v, b, team_info, html_path)
    write_csv(rows, v, b, csv_path)
    print(f"HTML: {html_path}")
    print(f"CSV:  {csv_path}")

    sync_dir = '/mnt/greiner-portal-sync/docs/workstreams/verguetung'
    if os.path.isdir(sync_dir):
        import shutil
        for ext in ['.html', '.csv']:
            src = prefix + ext
            dst = os.path.join(sync_dir, 'Mockup_Werkstatt_Praemien_Realdaten' + ext)
            shutil.copy2(src, dst)
        print(f"Sync: {sync_dir}")


if __name__ == '__main__':
    main()
