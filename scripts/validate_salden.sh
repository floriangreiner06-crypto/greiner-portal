#!/bin/bash
################################################################################
# Salden-Validierung Script - Greiner Portal
# ===========================================
# Schnelle Validierung der aktuellen Salden ohne Import
#
# Usage: ./validate_salden.sh
#
# Autor: Claude AI
# Datum: 07.11.2025
# Version: 1.0
################################################################################

set -e

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Konfiguration
PORTAL_DIR="/opt/greiner-portal"
DB_PATH="${PORTAL_DIR}/data/greiner_controlling.db"

clear
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  💰 SALDEN-VALIDIERUNG - GREINER PORTAL"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}\n"

# Verzeichnis wechseln
cd "$PORTAL_DIR" || exit 1

# Python Script ausführen
python3 << 'PYEOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/opt/greiner-portal/data/greiner_controlling.db')
c = conn.cursor()

print("="*85)
print(f"🎯 SALDEN-VALIDIERUNG - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
print("="*85 + "\n")

# 1. Bank-Konten einzeln
print("📊 BANK-KONTEN (Einzeln):\n")
c.execute("""
    SELECT 
        k.id,
        b.bank_name,
        k.kontoname,
        (SELECT saldo_nach_buchung 
         FROM transaktionen 
         WHERE konto_id = k.id 
         ORDER BY buchungsdatum DESC, id DESC 
         LIMIT 1) as saldo,
        (SELECT buchungsdatum 
         FROM transaktionen 
         WHERE konto_id = k.id 
         ORDER BY buchungsdatum DESC, id DESC 
         LIMIT 1) as datum,
        (SELECT COUNT(*) 
         FROM transaktionen 
         WHERE konto_id = k.id) as trans_count
    FROM konten k
    JOIN banken b ON k.bank_id = b.id
    WHERE k.aktiv = 1
    ORDER BY b.bank_name, k.kontoname
""")

bank_total = 0
print(f"{'ID':<4} {'Bank':<28} {'Konto':<32} {'Saldo (€)':>15} {'Trans.':<6} {'Stand'}")
print("-" * 110)

for kid, bank, kname, saldo, datum, trans_cnt in c.fetchall():
    bank_total += (saldo or 0)
    saldo_str = f"{(saldo or 0):,.2f}".replace(',', "'")
    print(f"{kid:<4} {bank:<28} {kname:<32} {saldo_str:>15} {trans_cnt:<6} {datum or 'N/A'}")

print("-" * 110)
total_str = f"{bank_total:,.2f}".replace(',', "'")
print(f"{'BANK-KONTEN GESAMT:':<76} {total_str:>15}\n")

# 2. Fahrzeugfinanzierungen
c.execute("""
    SELECT 
        COUNT(*) as anzahl,
        SUM(aktueller_saldo) as saldo_gesamt,
        MIN(vertragsbeginn) as aeltester,
        MAX(vertragsbeginn) as neuester
    FROM fahrzeugfinanzierungen
""")
fz_count, fz_saldo, oldest, newest = c.fetchone()

print("🚗 FAHRZEUGFINANZIERUNGEN (STELLANTIS):\n")
c.execute("""
    SELECT 
        rrdi,
        COUNT(*) as anzahl,
        SUM(aktueller_saldo) as saldo,
        SUM(original_betrag) as original
    FROM fahrzeugfinanzierungen
    GROUP BY rrdi
    ORDER BY rrdi
""")

print(f"{'RRDI':<15} {'Anzahl':>8} {'Aktueller Saldo (€)':>20} {'Original (€)':>20} {'Abbezahlt (%)':>15}")
print("-" * 85)

fz_total_saldo = 0
fz_total_original = 0
for rrdi, cnt, saldo, original in c.fetchall():
    fz_total_saldo += (saldo or 0)
    fz_total_original += (original or 0)
    abbezahlt_pct = ((original - saldo) / original * 100) if original else 0
    saldo_str = f"{(saldo or 0):,.2f}".replace(',', "'")
    orig_str = f"{(original or 0):,.2f}".replace(',', "'")
    print(f"{rrdi:<15} {cnt:>8} {saldo_str:>20} {orig_str:>20} {abbezahlt_pct:>14.1f}%")

print("-" * 85)
fz_saldo_str = f"{fz_total_saldo:,.2f}".replace(',', "'")
fz_orig_str = f"{fz_total_original:,.2f}".replace(',', "'")
abbezahlt_gesamt = ((fz_total_original - fz_total_saldo) / fz_total_original * 100) if fz_total_original else 0
print(f"{'GESAMT:':<15} {fz_count:>8} {fz_saldo_str:>20} {fz_orig_str:>20} {abbezahlt_gesamt:>14.1f}%")
print(f"\nVertragszeitraum: {oldest} bis {newest}\n")

# 3. Gesamtübersicht
print("="*85)
gesamt = bank_total + fz_total_saldo
bank_str = f"{bank_total:,.2f}".replace(',', "'")
fz_str = f"{fz_total_saldo:,.2f}".replace(',', "'")
gesamt_str = f"{gesamt:,.2f}".replace(',', "'")

print(f"{'Bank-Konten:':<40} {bank_str:>20} €")
print(f"{'Fahrzeugfinanzierungen:':<40} {fz_str:>20} €")
print("-" * 85)
print(f"{'💰 GESAMT-VERMÖGEN:':<40} {gesamt_str:>20} €")
print("="*85 + "\n")

# 4. Datenbank-Statistik
print("📈 DATENBANK-STATISTIK:\n")

c.execute("SELECT COUNT(*) FROM transaktionen")
trans_total = c.fetchone()[0]

c.execute("SELECT MIN(buchungsdatum), MAX(buchungsdatum) FROM transaktionen")
min_date, max_date = c.fetchone()

c.execute("SELECT COUNT(*) FROM konten WHERE aktiv=1")
konto_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM banken")
bank_count = c.fetchone()[0]

c.execute("""
    SELECT COUNT(*) 
    FROM transaktionen 
    WHERE buchungsdatum >= date('now', '-7 days')
""")
trans_7_days = c.fetchone()[0]

c.execute("""
    SELECT COUNT(*) 
    FROM transaktionen 
    WHERE buchungsdatum >= date('now', '-30 days')
""")
trans_30_days = c.fetchone()[0]

print(f"  • Transaktionen gesamt:        {trans_total:>10,}".replace(',', "'"))
print(f"  • Transaktionen (letzte 7 T.): {trans_7_days:>10,}".replace(',', "'"))
print(f"  • Transaktionen (letzte 30 T.): {trans_30_days:>10,}".replace(',', "'"))
print(f"  • Zeitraum:                     {min_date} bis {max_date}")
print(f"  • Bank-Konten (aktiv):         {konto_count:>10}")
print(f"  • Banken:                      {bank_count:>10}")
print(f"  • Fahrzeuge (Stellantis):      {fz_count:>10}")

# 5. Neueste Transaktionen
print("\n📅 NEUESTE TRANSAKTIONEN (Top 10):\n")
c.execute("""
    SELECT 
        t.buchungsdatum,
        b.bank_name,
        k.kontoname,
        t.betrag,
        t.verwendungszweck
    FROM transaktionen t
    JOIN konten k ON t.konto_id = k.id
    JOIN banken b ON k.bank_id = b.id
    ORDER BY t.buchungsdatum DESC, t.id DESC
    LIMIT 10
""")

print(f"{'Datum':<12} {'Bank':<20} {'Konto':<25} {'Betrag (€)':>12} {'Verwendungszweck'}")
print("-" * 120)

for datum, bank, konto, betrag, zweck in c.fetchall():
    betrag_str = f"{betrag:,.2f}".replace(',', "'")
    zweck_short = (zweck[:45] + '...') if zweck and len(zweck) > 45 else (zweck or '')
    print(f"{datum:<12} {bank:<20} {konto:<25} {betrag_str:>12} {zweck_short}")

conn.close()

print("\n" + "="*85 + "\n")
PYEOF

echo -e "${GREEN}✅ Validierung abgeschlossen${NC}\n"

echo -e "${CYAN}📋 HINWEISE:${NC}"
echo -e "  • Vergleiche diese Salden mit dem Excel-Bankenspiegel"
echo -e "  • Bei Abweichungen: bank_import.log prüfen"
echo -e "  • Backup vor Änderungen: cp greiner_controlling.db greiner_controlling.db.backup"
echo ""

exit 0
