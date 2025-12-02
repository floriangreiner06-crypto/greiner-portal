
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VacationCalculator Setup für Greiner Portal
===========================================
Erstellt den VacationCalculator mit Tag-Modell-Unterstützung

Ausführen auf dem Server:
cd /opt/greiner-portal
source venv/bin/activate
python3 setup_vacation_calculator.py
"""

import os
from pathlib import Path

# Haupt-Code für vacation_calculator.py
VACATION_CALCULATOR_CODE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vacation Calculator - Angepasst an Tag-Modell
==============================================
Berechnet Arbeitstage unter Berücksichtigung von:
- Wochenenden
- Feiertagen
- Halben Tagen
"""

from datetime import date, timedelta
from typing import List, Tuple, Dict, Optional
import sqlite3

class VacationCalculator:
    """
    Haupt-Klasse für Urlaubsberechnungen
    
    WICHTIG: Arbeitet mit Tag-Modell (vacation_bookings)
    """
    
    def __init__(self, db_path: str = 'data/greiner_controlling.db'):
        self.db_path = db_path
        self._holidays_cache = {}  # Cache für Feiertage
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Erstellt DB-Verbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Ergebnisse als Dict
        return conn
    
    def _load_holidays(self, year: int) -> Dict[date, str]:
        """
        Lädt Feiertage aus DB (mit Caching)
        
        Args:
            year: Jahr (z.B. 2025)
        
        Returns:
            Dict mit {datum: name}
        """
        if year not in self._holidays_cache:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT datum, name FROM holidays
                WHERE strftime('%Y', datum) = ?
                ORDER BY datum
            """, (str(year),))
            
            self._holidays_cache[year] = {
                date.fromisoformat(row['datum']): row['name']
                for row in cursor.fetchall()
            }
            
            conn.close()
        
        return self._holidays_cache[year]
    
    def is_working_day(self, check_date: date) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob ein Tag ein Arbeitstag ist
        
        Args:
            check_date: Zu prüfendes Datum
        
        Returns:
            (ist_arbeitstag, grund_falls_nicht)
            z.B. (False, "Samstag") oder (False, "Neujahr")
        """
        # Wochenende?
        if check_date.weekday() >= 5:  # 5=Samstag, 6=Sonntag
            day_name = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 
                       'Freitag', 'Samstag', 'Sonntag'][check_date.weekday()]
            return False, day_name
        
        # Feiertag?
        holidays = self._load_holidays(check_date.year)
        if check_date in holidays:
            return False, holidays[check_date]
        
        return True, None
    
    def get_working_days(self, start_date: date, end_date: date) -> List[date]:
        """
        Gibt alle Arbeitstage im Zeitraum zurück
        
        Args:
            start_date: Startdatum (inklusive)
            end_date: Enddatum (inklusive)
        
        Returns:
            Liste aller Arbeitstage
        """
        if start_date > end_date:
            return []
        
        working_days = []
        current = start_date
        
        while current <= end_date:
            is_working, _ = self.is_working_day(current)
            if is_working:
                working_days.append(current)
            current += timedelta(days=1)
        
        return working_days
    
    def count_working_days(self, start_date: date, end_date: date) -> int:
        """
        Zählt Arbeitstage im Zeitraum
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
        
        Returns:
            Anzahl Arbeitstage
        """
        return len(self.get_working_days(start_date, end_date))
    
    def get_vacation_balance(self, employee_id: int, year: int) -> Dict:
        """
        Berechnet Urlaubssaldo für einen Mitarbeiter
        
        Args:
            employee_id: ID des Mitarbeiters
            year: Jahr (z.B. 2025)
        
        Returns:
            Dict mit: anspruch, verbraucht, geplant, resturlaub
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # 1. Anspruch aus vacation_entitlements
        cursor.execute("""
            SELECT COALESCE(SUM(days_total), 0) as anspruch
            FROM vacation_entitlements
            WHERE employee_id = ? AND year = ?
        """, (employee_id, year))
        
        result = cursor.fetchone()
        anspruch = float(result['anspruch']) if result else 0.0
        
        # 2. Verbrauchte Tage (approved)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN day_part = 'full' THEN 1 END) as full_days,
                COUNT(CASE WHEN day_part = 'half' THEN 1 END) as half_days
            FROM vacation_bookings
            WHERE employee_id = ?
              AND strftime('%Y', booking_date) = ?
              AND status = 'approved'
        """, (employee_id, str(year)))
        
        result = cursor.fetchone()
        full = result['full_days'] if result else 0
        half = result['half_days'] if result else 0
        verbraucht = float(full) + (float(half) * 0.5)
        
        # 3. Geplante Tage (pending)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN day_part = 'full' THEN 1 END) as full_days,
                COUNT(CASE WHEN day_part = 'half' THEN 1 END) as half_days
            FROM vacation_bookings
            WHERE employee_id = ?
              AND strftime('%Y', booking_date) = ?
              AND status = 'pending'
        """, (employee_id, str(year)))
        
        result = cursor.fetchone()
        full = result['full_days'] if result else 0
        half = result['half_days'] if result else 0
        geplant = float(full) + (float(half) * 0.5)
        
        conn.close()
        
        # Resturlaub berechnen
        resturlaub = anspruch - verbraucht - geplant
        
        return {
            'anspruch': anspruch,
            'verbraucht': verbraucht,
            'geplant': geplant,
            'resturlaub': resturlaub,
            'year': year
        }
    
    def validate_vacation_request(self, employee_id: int, start_date: date, 
                                 end_date: date, vacation_type_id: int = 1) -> Tuple[bool, str, Dict]:
        """
        Validiert einen Urlaubsantrag
        
        Args:
            employee_id: ID des Mitarbeiters
            start_date: Startdatum
            end_date: Enddatum
            vacation_type_id: ID des Urlaubstyps (Standard: 1 = Urlaub)
        
        Returns:
            (ist_valid, fehlermeldung, details)
        """
        # Datum-Plausibilität
        if start_date > end_date:
            return False, "Startdatum liegt nach Enddatum", {}
        
        # Arbeitstage berechnen
        working_days = self.get_working_days(start_date, end_date)
        if not working_days:
            return False, "Keine Arbeitstage im gewählten Zeitraum", {}
        
        required_days = len(working_days)
        year = start_date.year
        
        # Urlaubssaldo prüfen
        balance = self.get_vacation_balance(employee_id, year)
        
        if balance['resturlaub'] < required_days:
            return False, f"Nicht genügend Resturlaub ({balance['resturlaub']:.1f} Tage verfügbar, {required_days} benötigt)", balance
        
        # Überschneidungen prüfen
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as overlaps
            FROM vacation_bookings
            WHERE employee_id = ?
              AND booking_date BETWEEN ? AND ?
              AND status IN ('pending', 'approved')
        """, (employee_id, start_date.isoformat(), end_date.isoformat()))
        
        result = cursor.fetchone()
        overlaps = result['overlaps'] if result else 0
        
        conn.close()
        
        if overlaps > 0:
            return False, f"Überschneidung mit bestehendem Urlaub ({overlaps} Tage)", balance
        
        # Alles OK!
        details = {
            'working_days': required_days,
            'balance': balance,
            'dates': working_days
        }
        
        return True, "Urlaubsantrag ist gültig", details
    
    def bookings_to_request(self, bookings: List[Dict]) -> Optional[Dict]:
        """
        Gruppiert Einzelbuchungen zu einem "Antrag"
        
        Args:
            bookings: Liste von booking-Dicts aus DB
        
        Returns:
            Dict mit start_date, end_date, total_days
        """
        if not bookings:
            return None
        
        # Sortieren nach Datum
        sorted_bookings = sorted(bookings, key=lambda x: x['booking_date'])
        
        start_date = sorted_bookings[0]['booking_date']
        end_date = sorted_bookings[-1]['booking_date']
        
        # Tage zählen
        total_days = sum(
            1.0 if b['day_part'] == 'full' 
            else 0.5 
            for b in sorted_bookings
        )
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': total_days,
            'vacation_type': sorted_bookings[0].get('vacation_type', 'Urlaub'),
            'status': sorted_bookings[0].get('status', 'pending'),
            'bookings': sorted_bookings
        }
    
    def request_to_bookings(self, start_date: date, end_date: date, 
                          vacation_type_id: int,
                          day_parts: Optional[Dict[date, str]] = None) -> List[Dict]:
        """
        Splittet einen "Antrag" (Zeitraum) in einzelne Buchungen
        
        Args:
            start_date: Startdatum
            end_date: Enddatum
            vacation_type_id: ID des Urlaubstyps
            day_parts: Optional dict mit Tagesanteilen {datum: 'full'/'half'}
        
        Returns:
            Liste von booking-Dicts zum Einfügen in DB
        """
        working_days = self.get_working_days(start_date, end_date)
        
        bookings = []
        for day in working_days:
            part = day_parts.get(day, 'full') if day_parts else 'full'
            
            bookings.append({
                'booking_date': day.isoformat(),
                'vacation_type_id': vacation_type_id,
                'day_part': part
            })
        
        return bookings


# ============================================================================
# TESTS / BEISPIELE
# ============================================================================

if __name__ == '__main__':
    """
    Test-Funktionen für den VacationCalculator
    """
    import sys
    
    print("=" * 70)
    print("VACATIONCALCULATOR - TEST")
    print("=" * 70)
    
    # Calculator initialisieren
    calc = VacationCalculator()
    
    # Test 1: Arbeitstage berechnen
    print("\\n🔹 TEST 1: Arbeitstage Weihnachten 2025")
    print("-" * 70)
    
    start = date(2025, 12, 24)
    end = date(2025, 12, 31)
    
    print(f"Zeitraum: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}")
    working_days = calc.get_working_days(start, end)
    
    print(f"\\nArbeitstage:")
    for day in working_days:
        print(f"  ✓ {day.strftime('%d.%m.%Y (%A)')}")
    
    print(f"\\n📊 Gesamt: {len(working_days)} Arbeitstage")
    
    # Test 2: Einzelne Tage prüfen
    print("\\n🔹 TEST 2: Einzelne Tage prüfen")
    print("-" * 70)
    
    test_dates = [
        date(2025, 12, 25),  # 1. Weihnachtsfeiertag
        date(2025, 12, 26),  # 2. Weihnachtsfeiertag
        date(2025, 12, 27),  # Samstag
        date(2025, 12, 29),  # Montag
    ]
    
    for test_date in test_dates:
        is_working, reason = calc.is_working_day(test_date)
        status = "✓ Arbeitstag" if is_working else f"✗ KEIN Arbeitstag ({reason})"
        print(f"{test_date.strftime('%d.%m.%Y (%A)')}: {status}")
    
    # Test 3: Urlaubsvalidierung
    print("\\n🔹 TEST 3: Urlaubsantrag validieren")
    print("-" * 70)
    
    # Beispiel: 1 Woche im Januar 2025
    request_start = date(2025, 1, 6)
    request_end = date(2025, 1, 10)
    
    print(f"Antrag: {request_start.strftime('%d.%m.%Y')} - {request_end.strftime('%d.%m.%Y')}")
    
    # Arbeitstage berechnen
    request_days = calc.get_working_days(request_start, request_end)
    print(f"Benötigte Arbeitstage: {len(request_days)}")
    
    # Bookings generieren
    bookings = calc.request_to_bookings(
        request_start, 
        request_end, 
        vacation_type_id=1
    )
    
    print(f"\\nGenerierte Buchungen: {len(bookings)}")
    for booking in bookings:
        print(f"  • {booking['booking_date']} ({booking['day_part']})")
    
    print("\\n" + "=" * 70)
    print("✅ VacationCalculator Tests abgeschlossen!")
    print("=" * 70)
'''

# __init__.py für utils
UTILS_INIT = '''"""
Utility-Module für Greiner Portal Urlaubsplaner
"""

from .vacation_calculator import VacationCalculator

__all__ = ['VacationCalculator']
'''


def main():
    """Hauptfunktion"""
    
    print("\n" + "="*70)
    print("🚀 VACATIONCALCULATOR SETUP")
    print("="*70)
    
    # Verzeichnisse erstellen
    base_dir = Path('/opt/greiner-portal')
    utils_dir = base_dir / 'vacation_v2' / 'utils'
    
    print(f"\n📁 Erstelle Verzeichnisse...")
    utils_dir.mkdir(parents=True, exist_ok=True)
    print(f"   ✓ {utils_dir}")
    
    # VacationCalculator erstellen
    calc_file = utils_dir / 'vacation_calculator.py'
    print(f"\n📝 Erstelle {calc_file.name}...")
    with open(calc_file, 'w', encoding='utf-8') as f:
        f.write(VACATION_CALCULATOR_CODE)
    os.chmod(calc_file, 0o755)
    print(f"   ✓ {calc_file}")
    
    # __init__.py erstellen
    init_file = utils_dir / '__init__.py'
    print(f"\n📝 Erstelle {init_file.name}...")
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(UTILS_INIT)
    print(f"   ✓ {init_file}")
    
    print("\n" + "="*70)
    print("✅ SETUP ABGESCHLOSSEN!")
    print("="*70)
    
    print("\n📋 Nächste Schritte:")
    print("   1. Tests ausführen:")
    print("      cd /opt/greiner-portal")
    print("      source venv/bin/activate")
    print("      python3 vacation_v2/utils/vacation_calculator.py")
    print("")
    print("   2. Im Code verwenden:")
    print("      from vacation_v2.utils import VacationCalculator")
    print("      calc = VacationCalculator()")
    print("")
    
    return 0


if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
