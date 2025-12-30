#!/usr/bin/env python3
"""
Sendet die Umfrage-Ergebnisse per E-Mail an den Initiator
"""

import sys
import os

# Pfad für Imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.portal_name_survey_api import send_results_email

if __name__ == '__main__':
    print("=" * 60)
    print("Portal-Namen Umfrage - Ergebnisse senden")
    print("=" * 60)
    print()
    
    if send_results_email():
        print("✅ Ergebnisse erfolgreich per E-Mail versendet!")
    else:
        print("❌ Fehler beim Versenden der Ergebnisse")
        print("   (Möglicherweise keine Abstimmungen vorhanden)")

