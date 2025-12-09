#!/usr/bin/env python3
"""
PROJEKT-STATUS EXPORT
Exportiert den kompletten aktuellen Stand für Project Knowledge
Führe nach jeder wichtigen Änderung aus!
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Pfade (auf deinem Server anpassen!)
DB_PATH = '/opt/greiner-portal/data/greiner_controlling.db'
OUTPUT_DIR = '/opt/greiner-portal/docs/status'

def export_status():
    """Exportiert kompletten Projekt-Status"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output = []
    
    # Header
    output.append("# GREINER PORTAL - AKTUELLER PROJEKT-STATUS")
    output.append(f"**Letztes Update:** {timestamp}")
    output.append("")
    output.append("---")
    output.append("")
    
    # ========================================
    # 1. KONTEN-ÜBERSICHT
    # ========================================
    output.append("## 🏦 KONTEN-ÜBERSICHT")
    output.append("")
    
    cursor.execute("""
        SELECT 
            k.id,
            k.kontoname,
            k.iban,
            k.bank,
            COALESCE((SELECT t.saldo_nach_buchung 
                      FROM transaktionen t 
                      WHERE t.konto_id = k.id 
                      ORDER BY t.buchungsdatum DESC, t.id DESC LIMIT 1), 0) as saldo,
            (SELECT COUNT(*) FROM transaktionen t WHERE t.konto_id = k.id) as trans_count,
            (SELECT MIN(t.buchungsdatum) FROM transaktionen t WHERE t.konto_id = k.id) as erste_buchung,
            (SELECT MAX(t.buchungsdatum) FROM transaktionen t WHERE t.konto_id = k.id) as letzte_buchung
        FROM konten k 
        ORDER BY k.id
    """)
    
    konten = cursor.fetchall()
    total_saldo = sum(k[4] for k in konten)
    
    output.append("| ID | Kontoname | IBAN | Bank | Saldo | Trans | Erste | Letzte |")
    output.append("|----|-----------|------|------|-------|-------|-------|--------|")
    
    for konto in konten:
        kid, name, iban, bank, saldo, trans, erste, letzte = konto
        iban_short = iban[-10:] if iban else "keine"
        bank_short = bank[:15] if bank else "keine"
        erste_str = erste if erste else "-"
        letzte_str = letzte if letzte else "-"
        output.append(f"| {kid} | {name[:25]} | ...{iban_short} | {bank_short} | {saldo:,.2f} € | {trans} | {erste_str} | {letzte_str} |")
    
    output.append(f"| **TOTAL** | | | | **{total_saldo:,.2f} €** | | | |")
    output.append("")
    
    # ========================================
    # 2. NOVEMBER 2025 STATUS
    # ========================================
    output.append("## 📅 NOVEMBER 2025 - IMPORT-STATUS")
    output.append("")
    
    cursor.execute("""
        SELECT 
            k.id,
            k.kontoname,
            COUNT(t.id) as nov_trans,
            MIN(t.buchungsdatum) as erste_nov,
            MAX(t.buchungsdatum) as letzte_nov,
            (SELECT t2.saldo_nach_buchung 
             FROM transaktionen t2 
             WHERE t2.konto_id = k.id AND t2.buchungsdatum >= '2025-11-01'
             ORDER BY t2.buchungsdatum DESC, t2.id DESC 
             LIMIT 1) as nov_endsaldo
        FROM konten k
        LEFT JOIN transaktionen t ON k.id = t.konto_id AND t.buchungsdatum >= '2025-11-01'
        GROUP BY k.id, k.kontoname
        ORDER BY nov_trans DESC
    """)
    
    nov_konten = cursor.fetchall()
    
    output.append("| ID | Kontoname | Nov-Trans | Von | Bis | Nov-Saldo | Status |")
    output.append("|----|-----------|-----------|-----|-----|-----------|--------|")
    
    for konto in nov_konten:
        kid, name, trans, von, bis, saldo = konto
        
        if trans == 0:
            status = "❌ Keine Nov-Daten"
            von_str, bis_str, saldo_str = "-", "-", "-"
        elif bis and bis >= "2025-11-11":
            status = "✅ Komplett"
            von_str, bis_str = von, bis
            saldo_str = f"{saldo:,.2f} €" if saldo else "-"
        else:
            status = f"⚠️ Unvollständig (bis {bis})"
            von_str, bis_str = von if von else "-", bis if bis else "-"
            saldo_str = f"{saldo:,.2f} €" if saldo else "-"
        
        output.append(f"| {kid} | {name[:25]} | {trans} | {von_str} | {bis_str} | {saldo_str} | {status} |")
    
    output.append("")
    
    # ========================================
    # 3. TRANSAKTIONS-STATISTIKEN
    # ========================================
    output.append("## 📊 TRANSAKTIONS-STATISTIKEN")
    output.append("")
    
    # Gesamt
    cursor.execute("SELECT COUNT(*), MIN(buchungsdatum), MAX(buchungsdatum) FROM transaktionen")
    total_trans, erste_trans, letzte_trans = cursor.fetchone()
    
    output.append(f"- **Gesamt-Transaktionen:** {total_trans:,}")
    output.append(f"- **Zeitraum:** {erste_trans} bis {letzte_trans}")
    output.append("")
    
    # Pro Monat (letzte 3 Monate)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', buchungsdatum) as monat,
            COUNT(*) as anzahl
        FROM transaktionen
        WHERE buchungsdatum >= date('now', '-3 months')
        GROUP BY monat
        ORDER BY monat DESC
    """)
    
    output.append("### Transaktionen pro Monat (letzte 3):")
    for monat, anzahl in cursor.fetchall():
        output.append(f"- **{monat}:** {anzahl:,} Transaktionen")
    output.append("")
    
    # ========================================
    # 4. OFFENE AUFGABEN
    # ========================================
    output.append("## 🚀 OFFENE AUFGABEN")
    output.append("")
    
    # Konten ohne November-Daten
    cursor.execute("""
        SELECT k.id, k.kontoname
        FROM konten k
        WHERE NOT EXISTS (
            SELECT 1 FROM transaktionen t 
            WHERE t.konto_id = k.id AND t.buchungsdatum >= '2025-11-01'
        )
        AND k.id NOT IN (23, 20, 6, 14, 7, 8)  -- Festgeld/Darlehen ausschließen
    """)
    
    keine_nov = cursor.fetchall()
    if keine_nov:
        output.append("### Konten ohne November-Daten:")
        for kid, name in keine_nov:
            output.append(f"- [ ] **ID {kid}:** {name}")
        output.append("")
    
    # Konten mit unvollständigen November-Daten
    cursor.execute("""
        SELECT k.id, k.kontoname, MAX(t.buchungsdatum) as letzte
        FROM konten k
        JOIN transaktionen t ON k.id = t.konto_id
        WHERE t.buchungsdatum >= '2025-11-01'
        GROUP BY k.id, k.kontoname
        HAVING letzte < '2025-11-11'
    """)
    
    unvollst = cursor.fetchall()
    if unvollst:
        output.append("### Konten mit unvollständigen November-Daten:")
        for kid, name, letzte in unvollst:
            output.append(f"- [ ] **ID {kid}:** {name} (nur bis {letzte})")
        output.append("")
    
    # ========================================
    # 5. SYSTEM-INFO
    # ========================================
    output.append("## 🛠️ SYSTEM-INFO")
    output.append("")
    
    # DB-Größe
    db_size = Path(DB_PATH).stat().st_size / (1024 * 1024)  # MB
    output.append(f"- **Datenbank-Größe:** {db_size:.2f} MB")
    
    # Anzahl Konten
    output.append(f"- **Anzahl Konten:** {len(konten)}")
    
    # Parser-Status
    output.append("- **Verfügbare Parser:**")
    output.append("  - ✅ `genobank_universal_parser` (057908, 4700057908)")
    output.append("  - ✅ `hypovereinsbank_parser` (Hypovereinsbank)")
    output.append("  - ✅ `sparkasse_parser` (Sparkasse)")
    output.append("  - ✅ `hyundai_finance_scraper` (1501500 HYU KK)")
    output.append("")
    
    # ========================================
    # 6. WICHTIGE PFADE & CREDENTIALS
    # ========================================
    output.append("## 📁 WICHTIGE PFADE")
    output.append("")
    output.append("```")
    output.append("Projekt-Root:     /opt/greiner-portal")
    output.append("Datenbank:        /opt/greiner-portal/data/greiner_controlling.db")
    output.append("PDFs:             /opt/greiner-portal/data/kontoauszuege/")
    output.append("Parser:           /opt/greiner-portal/*.py")
    output.append("Grafana:          http://10.80.80.20:3000")
    output.append("Virtual Env:      /opt/greiner-portal/venv")
    output.append("```")
    output.append("")
    
    # ========================================
    # EXPORT
    # ========================================
    
    conn.close()
    
    # Als Markdown speichern
    output_file = Path(OUTPUT_DIR) / 'CURRENT_STATUS.md'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"✅ Status exportiert nach: {output_file}")
    print(f"📋 Kopiere diese Datei ins Project Knowledge!")
    
    # Auch als JSON für maschinelle Verarbeitung
    json_file = Path(OUTPUT_DIR) / 'current_status.json'
    json_data = {
        'timestamp': timestamp,
        'konten': [
            {
                'id': k[0],
                'name': k[1],
                'iban': k[2],
                'bank': k[3],
                'saldo': k[4],
                'trans_count': k[5],
                'erste_buchung': k[6],
                'letzte_buchung': k[7]
            }
            for k in konten
        ],
        'total_saldo': total_saldo,
        'total_transaktionen': total_trans
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON exportiert nach: {json_file}")

if __name__ == '__main__':
    export_status()
