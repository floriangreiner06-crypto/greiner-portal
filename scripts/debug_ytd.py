#!/usr/bin/env python3
"""Debug Script für YTD-Tracking"""

from api.unternehmensplan_data import get_ist_daten, get_letzter_abgeschlossener_monat, get_kumulierte_ytd_ansicht

print("=== Letzter abgeschlossener Monat ===")
letzter = get_letzter_abgeschlossener_monat()
print(f"Monat: {letzter}")

print()
print("=== IST-Daten mit nur_abgeschlossene=False ===")
ist = get_ist_daten("2025/26", 0, nur_abgeschlossene=False)

print(f"Datenstand: {ist.get('datenstand', 'N/A')}")
print()
print("Monate mit Daten:")
for m in ist["monate"]:
    if m["umsatz"] > 0 or m["kosten"] > 0:
        print(f"  {m['label']}: U={m['umsatz']:,.0f} DB1={m['db1']:,.0f} K={m['kosten']:,.0f}")

print()
print("Alle Monate (auch ohne Daten):")
for m in ist["monate"]:
    print(f"  {m['label']}: U={m['umsatz']:,.0f}")

print()
print("=== YTD Tracking ===")
ytd = get_kumulierte_ytd_ansicht("2025/26", 0)
print(f"Anzahl Monate: {ytd.get('anzahl_monate', 0)}")
if "monate" in ytd:
    for m in ytd["monate"]:
        print(f"  {m['label']}: U={m['kumuliert']['umsatz']:,.0f}")
