#!/usr/bin/env python3
"""
TEK nur als Test an eine E-Mail senden – ruft NICHT den Task auf, versendet nicht an Abonnenten.

Verwendung:
    python3 scripts/send_tek_nur_test_an_mich.py florian.greiner@auto-greiner.de

Es werden alle TEK-Report-Varianten (Gesamt, Filiale, Bereich, Verkauf, Service)
ausschließlich an die angegebene Adresse gesendet. --force ist gesetzt, damit
der Versand auch vor 19:00 Uhr möglich ist.
"""

import subprocess
import sys
import os

def main():
    if len(sys.argv) != 2:
        print("Verwendung: python3 scripts/send_tek_nur_test_an_mich.py <florian.greiner@auto-greiner.de>")
        print("")
        print("Sendet alle TEK-Reports NUR an diese eine E-Mail (Test-Versand).")
        print("Der reguläre Task und die Abonnenten werden NICHT aufgerufen.")
        sys.exit(2)

    email = sys.argv[1].strip()
    if not email or "@" not in email:
        print("Bitte eine gültige E-Mail-Adresse angeben.")
        sys.exit(2)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    send_script = os.path.join(script_dir, "send_daily_tek.py")

    print(f"TEK-Testversand ausschließlich an: {email}")
    print("(Task/Abonnenten werden nicht verwendet)\n")

    rc = subprocess.call(
        [sys.executable, send_script, "--test-email", email, "--force"],
        cwd=project_root,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
