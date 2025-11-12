#!/usr/bin/env python3
"""
AUTO-UPDATE PROJECT STATUS
Wird automatisch bei jedem Git-Commit ausgeführt via Pre-Commit Hook
Generiert PROJECT_STATUS.md mit komplettem Projekt-Zustand
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

# Pfade
BASE_DIR = Path('/opt/greiner-portal')
DB_PATH = BASE_DIR / 'data' / 'greiner_controlling.db'
OUTPUT_MD = BASE_DIR / 'PROJECT_STATUS.md'
OUTPUT_JSON_DIR = BASE_DIR / 'docs' / 'status'

SILENT = '--silent' in sys.argv

def log(msg):
    if not SILENT:
        print(msg)

def export_status():
    """Exportiert kompletten Projekt-Status"""
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
    except Exception as e:
        log(f"⚠️  Konnte DB nicht öffnen: {e}")
        return False
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ========================================
    # KONTEN LADEN
    # ========================================
    cursor.execute("""
        SELECT 
            k.id, k.kontoname, k.iban, b.bank_name,
            COALESCE((SELECT t.saldo_nach_buchung FROM transaktionen t 
                      WHERE t.konto_id = k.id ORDER BY t.buchungsdatum DESC, t.id DESC LIMIT 1), 0) as saldo,
            (SELECT COUNT(*) FROM transaktionen t WHERE t.konto_id = k.id) as trans_count,
            (SELECT MAX(t.buchungsdatum) FROM transaktionen t WHERE t.konto_id = k.id) as letzte
        FROM konten k
        LEFT JOIN banken b ON k.bank_id = b.id
        ORDER BY k.id
    """)
    konten = cursor.fetchall()
    total_saldo = sum(k[4] for k in konten)
    
    # ========================================
    # NOVEMBER STATUS
    # ========================================
    cursor.execute("""
        SELECT k.id, k.kontoname, COUNT(t.id) as nov_trans,
               MIN(t.buchungsdatum) as von, MAX(t.buchungsdatum) as bis
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id AND t.buchungsdatum >= '2025-11-01'
        GROUP BY k.id ORDER BY k.id
    """)
    nov_status = cursor.fetchall()
    
    # ========================================
    # TRANSAKTIONS-STATS
    # ========================================
    cursor.execute("SELECT COUNT(*) FROM transaktionen")
    total_trans = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT strftime('%Y-%m', buchungsdatum) as monat, COUNT(*) 
        FROM transaktionen 
        WHERE buchungsdatum >= date('now', '-3 months')
        GROUP BY monat ORDER BY monat DESC
    """)
    monthly_trans = cursor.fetchall()
    
    conn.close()
    
    # ========================================
    # MARKDOWN GENERIEREN
    # ========================================
    md = []
    md.append("# 🏦 GREINER PORTAL - PROJEKT-STATUS")
    md.append("")
    md.append(f"**Letztes Update:** {timestamp}")
    md.append(f"**Auto-generiert bei Git-Commit**")
    md.append("")
    md.append("---")
    md.append("")
    
    # QUICK FACTS
    md.append("## ⚡ QUICK FACTS")
    md.append("")
    md.append(f"- **Anzahl Konten:** {len(konten)}")
    md.append(f"- **Gesamt-Saldo:** {total_saldo:,.2f} €")
    md.append(f"- **Gesamt-Transaktionen:** {total_trans:,}")
    md.append("")
    
    # KONTEN-ÜBERSICHT
    md.append("## 🏦 KONTEN-ÜBERSICHT")
    md.append("")
    md.append("| ID | Kontoname | IBAN | Bank | Saldo | Trans | Letzte |")
    md.append("|----|-----------|------|------|-------|-------|--------|")
    
    for k in konten:
        kid, name, iban, bank, saldo, trans, letzte = k
        iban_short = f"...{iban[-10:]}" if iban else "keine"
        bank_short = bank[:20] if bank else "keine"
        letzte_str = letzte if letzte else "-"
        md.append(f"| {kid} | {name[:25]} | {iban_short} | {bank_short} | {saldo:,.2f} € | {trans} | {letzte_str} |")
    
    md.append(f"| **TOTAL** | | | **{total_saldo:,.2f} €** | | |")
    md.append("")
    
    # NOVEMBER STATUS
    md.append("## 📅 NOVEMBER 2025 - IMPORT-STATUS")
    md.append("")
    md.append("| ID | Kontoname | Trans | Von | Bis | Status |")
    md.append("|----|-----------|-------|-----|-----|--------|")
    
    for k in nov_status:
        kid, name, trans, von, bis = k
        
        if trans == 0:
            status = "❌ Keine Daten"
            von_str, bis_str = "-", "-"
        elif bis and bis >= "2025-11-11":
            status = "✅ Komplett"
            von_str, bis_str = von, bis
        else:
            status = f"⚠️ Unvollständig (bis {bis})"
            von_str, bis_str = von if von else "-", bis if bis else "-"
        
        md.append(f"| {kid} | {name[:30]} | {trans} | {von_str} | {bis_str} | {status} |")
    
    md.append("")
    
    # TRANSAKTIONS-STATS
    md.append("## 📊 TRANSAKTIONS-STATISTIK (letzte 3 Monate)")
    md.append("")
    for monat, anzahl in monthly_trans:
        md.append(f"- **{monat}:** {anzahl:,} Transaktionen")
    md.append("")
    
    # OFFENE AUFGABEN
    md.append("## 🚧 OFFENE AUFGABEN")
    md.append("")
    
    # Konten ohne November-Daten (excl. Festgeld/Darlehen)
    unvollstaendig = [k for k in nov_status if k[2] > 0 and k[4] and k[4] < "2025-11-11"]
    keine_daten = [k for k in nov_status if k[2] == 0 and k[0] not in (23, 20, 6, 14, 7, 8)]
    
    if unvollstaendig:
        md.append("### ⚠️  Unvollständige November-Daten:")
        for k in unvollstaendig:
            md.append(f"- **ID {k[0]}:** {k[1]} (nur bis {k[4]})")
        md.append("")
    
    if keine_daten:
        md.append("### ❌ Keine November-Daten:")
        for k in keine_daten:
            md.append(f"- **ID {k[0]}:** {k[1]}")
        md.append("")
    
    # SYSTEM-INFO
    md.append("## 🛠️ SYSTEM-INFO")
    md.append("")
    md.append("### Pfade:")
    md.append("```")
    md.append("Projekt-Root:     /opt/greiner-portal")
    md.append("Datenbank:        /opt/greiner-portal/data/greiner_controlling.db")
    md.append("PDFs:             /opt/greiner-portal/data/kontoauszuege/")
    md.append("Status-Export:    /opt/greiner-portal/docs/status/")
    md.append("```")
    md.append("")
    md.append("### Parser:")
    md.append("- ✅ `genobank_universal_parser` → 057908, 4700057908")
    md.append("- ✅ `hypovereinsbank_parser` → Hypovereinsbank")
    md.append("- ✅ `sparkasse_parser` → Sparkasse")
    md.append("- ✅ `hyundai_finance_scraper` → 1501500 HYU KK")
    md.append("")
    md.append("### Git-Branch:")
    md.append("```bash")
    md.append("# Aktueller Branch:")
    md.append("git branch --show-current")
    md.append("")
    md.append("# Alle Branches:")
    md.append("git branch -a")
    md.append("```")
    md.append("")
    
    # FOOTER
    md.append("---")
    md.append("")
    md.append("**🤖 Automatisch generiert** | Siehe auch: `SESSION_WRAP_UP_TAG*.md` für Details")
    
    # ========================================
    # SPEICHERN
    # ========================================
    
    # Markdown
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    log(f"✅ Status exportiert: {OUTPUT_MD}")
    
    # JSON (für maschinelle Verarbeitung)
    OUTPUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    json_data = {
        'timestamp': timestamp,
        'konten': [
            {
                'id': k[0], 'name': k[1], 'iban': k[2], 'bank': k[3],
                'saldo': k[4], 'trans_count': k[5], 'letzte_buchung': k[6]
            }
            for k in konten
        ],
        'november_status': [
            {'id': k[0], 'name': k[1], 'trans': k[2], 'von': k[3], 'bis': k[4]}
            for k in nov_status
        ],
        'total_saldo': total_saldo,
        'total_transaktionen': total_trans
    }
    
    json_file = OUTPUT_JSON_DIR / 'current_status.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    log(f"✅ JSON exportiert: {json_file}")
    
    return True

if __name__ == '__main__':
    success = export_status()
    sys.exit(0 if success else 1)
