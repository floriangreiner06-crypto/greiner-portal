#!/bin/bash
################################################################################
# BANK-PDF AUTO-IMPORT - ALLE BANKEN
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual Environment aktivieren
source venv/bin/activate

# Log-Setup
LOG_FILE="logs/bank_pdf_import.log"
echo "========================================" >> "$LOG_FILE"
echo "Bank-PDF Import: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Basis-Pfad
BASE_PATH="/mnt/buchhaltung/Buchhaltung/Kontoauszüge"

# Hypovereinsbank
echo "Importiere Hypovereinsbank..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank hypovereinsbank \
    "$BASE_PATH/Hypovereinsbank" \
    >> "$LOG_FILE" 2>&1

# Sparkasse
echo "Importiere Sparkasse..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank sparkasse \
    "$BASE_PATH/Sparkasse" \
    >> "$LOG_FILE" 2>&1

# VR Bank
echo "Importiere VR Bank..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank vrbank \
    "$BASE_PATH/VR Bank Landau" \
    >> "$LOG_FILE" 2>&1

# Genobank (mehrere Konten)
echo "Importiere Genobank Auto Greiner..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank auto \
    "$BASE_PATH/Genobank Auto Greiner" \
    >> "$LOG_FILE" 2>&1

echo "Importiere Genobank Autohaus Greiner..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank auto \
    "$BASE_PATH/Genobank Autohaus Greiner" \
    >> "$LOG_FILE" 2>&1

echo "Importiere Genobank Greiner Immob.Verw..." | tee -a "$LOG_FILE"
python3 scripts/imports/import_bank_pdfs.py \
    --bank auto \
    "$BASE_PATH/Genobank Greiner Immob.Verw" \
    >> "$LOG_FILE" 2>&1

echo "========================================" | tee -a "$LOG_FILE"
echo "Import abgeschlossen: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
