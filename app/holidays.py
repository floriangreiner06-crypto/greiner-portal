"""
Bayerische Feiertage
"""
from datetime import date

HOLIDAYS = {
    # 2025
    '2025-01-01': 'Neujahr',
    '2025-01-06': 'Heilige Drei Könige',
    '2025-04-18': 'Karfreitag',
    '2025-04-21': 'Ostermontag',
    '2025-05-01': 'Tag der Arbeit',
    '2025-05-29': 'Christi Himmelfahrt',
    '2025-06-09': 'Pfingstmontag',
    '2025-06-19': 'Fronleichnam',
    '2025-08-15': 'Mariä Himmelfahrt',
    '2025-10-03': 'Tag der Deutschen Einheit',
    '2025-11-01': 'Allerheiligen',
    '2025-12-25': '1. Weihnachtstag',
    '2025-12-26': '2. Weihnachtstag',
    # 2026
    '2026-01-01': 'Neujahr',
    '2026-01-06': 'Heilige Drei Könige',
    '2026-04-03': 'Karfreitag',
    '2026-04-06': 'Ostermontag',
    '2026-05-01': 'Tag der Arbeit',
    '2026-05-14': 'Christi Himmelfahrt',
    '2026-05-25': 'Pfingstmontag',
    '2026-06-04': 'Fronleichnam',
    '2026-08-15': 'Mariä Himmelfahrt',
    '2026-10-03': 'Tag der Deutschen Einheit',
    '2026-11-01': 'Allerheiligen',
    '2026-12-25': '1. Weihnachtstag',
    '2026-12-26': '2. Weihnachtstag',
}

def is_holiday(check_date):
    """
    Prüft ob ein Datum ein Feiertag ist
    
    Args:
        check_date: date-Objekt oder String (YYYY-MM-DD)
        
    Returns:
        tuple: (bool, str) - (ist_feiertag, feiertags_name)
    """
    # Konvertiere date-Objekt zu String
    if isinstance(check_date, date):
        date_str = check_date.strftime('%Y-%m-%d')
    else:
        date_str = str(check_date)
    
    # Prüfe ob Feiertag
    if date_str in HOLIDAYS:
        return True, HOLIDAYS[date_str]
    else:
        return False, None

def get_holiday_name(check_date):
    """
    Gibt den Namen des Feiertags zurück
    
    Args:
        check_date: date-Objekt oder String
        
    Returns:
        str: Feiertagsname oder leerer String
    """
    is_hol, name = is_holiday(check_date)
    return name if name else ''
