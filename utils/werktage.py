"""
Werktage-Berechnung – SSOT für Mo–Fr ohne Feiertage
====================================================
TAG: Aus controlling_routes ausgelagert für Nutzung in controlling_data (TEK Breakeven SSOT).
Nutzer: controlling_routes, api/controlling_data
"""
from datetime import datetime, timedelta
import calendar

# Bayerische Feiertage (jährlich erweitern)
FEIERTAGE = [
    # 2025
    datetime(2025, 1, 1), datetime(2025, 1, 6), datetime(2025, 4, 18), datetime(2025, 4, 21),
    datetime(2025, 5, 1), datetime(2025, 5, 29), datetime(2025, 6, 9), datetime(2025, 6, 19),
    datetime(2025, 8, 15), datetime(2025, 10, 3), datetime(2025, 11, 1),
    datetime(2025, 12, 25), datetime(2025, 12, 26),
    # 2026
    datetime(2026, 1, 1), datetime(2026, 1, 6), datetime(2026, 4, 3), datetime(2026, 4, 6),
    datetime(2026, 5, 1), datetime(2026, 5, 14), datetime(2026, 5, 25), datetime(2026, 6, 4),
    datetime(2026, 8, 15), datetime(2026, 10, 3), datetime(2026, 11, 1),
    datetime(2026, 12, 25), datetime(2026, 12, 26),
]


def get_werktage(start_date, end_date, include_end=False):
    """Berechnet Werktage zwischen zwei Daten (Mo–Fr, ohne Feiertage)."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date[:10], '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date[:10], '%Y-%m-%d')

    if not include_end:
        end_date = end_date - timedelta(days=1)

    werktage = 0
    current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    feiertage_set = {d.date() for d in FEIERTAGE}

    while current <= end_date:
        if current.weekday() < 5 and current.date() not in feiertage_set:
            werktage += 1
        current += timedelta(days=1)

    return werktage


def get_werktage_monat(jahr, monat, stichtag=None):
    """
    Berechnet Werktage im Monat: {gesamt, vergangen, verbleibend, fortschritt_prozent}.

    stichtag: Optional. Für TEK: Datenstichtag, damit morgens (vor Locosoft-Update)
    „verbleibend“ den heutigen Tag mitzählt. Wenn None, wird Kalender-Heute verwendet.
    Nutzung: Vor 19:00 Uhr Stichtag = gestern übergeben, damit „vergangen“ nur Tage
    mit Daten zählt (Locosoft liefert erst abends).
    """
    erster_tag = datetime(jahr, monat, 1)
    letzter_tag = datetime(jahr, monat, calendar.monthrange(jahr, monat)[1])
    now = datetime.now()
    if stichtag is not None:
        if hasattr(stichtag, 'year') and hasattr(stichtag, 'month'):
            effective_heute = stichtag.date() if hasattr(stichtag, 'date') else stichtag
        else:
            effective_heute = datetime.strptime(str(stichtag)[:10], '%Y-%m-%d').date()
    else:
        effective_heute = now.date()

    werktage_gesamt = get_werktage(erster_tag, letzter_tag, include_end=True)

    if effective_heute.year == jahr and effective_heute.month == monat:
        stichtag_dt = datetime(effective_heute.year, effective_heute.month, effective_heute.day)
        werktage_vergangen = get_werktage(erster_tag, stichtag_dt, include_end=True)
        werktage_verbleibend = werktage_gesamt - werktage_vergangen
    else:
        werktage_vergangen = werktage_gesamt
        werktage_verbleibend = 0

    fortschritt = (werktage_vergangen / werktage_gesamt * 100) if werktage_gesamt > 0 else 100

    return {
        'gesamt': werktage_gesamt,
        'vergangen': werktage_vergangen,
        'verbleibend': werktage_verbleibend,
        'fortschritt_prozent': round(fortschritt, 1),
        'ist_aktueller_monat': now.year == jahr and now.month == monat,
    }
