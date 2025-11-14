#!/bin/bash
# Import nur der modernen Genobank PDFs (mit Kontonummer im Namen)

echo "========================================================================"
echo "GENOBANK IMPORT - NUR MODERNE PDFs"
echo "========================================================================"
echo ""

TOTAL_IMPORTED=0
TOTAL_FAILED=0
TOTAL_DUPLICATES=0

for dir in "/mnt/buchhaltung/Buchhaltung/Kontoauszüge/Genobank"*; do
    account_name=$(basename "$dir")
    echo ""
    echo "========================================"
    echo "=== $account_name ==="
    echo "========================================"
    
    # Zähle moderne PDFs
    pdf_count=$(find "$dir" -name "[0-9]*.pdf" -type f | wc -l)
    echo "Moderne PDFs gefunden: $pdf_count"
    
    if [ $pdf_count -eq 0 ]; then
        echo "⏩ Übersprungen (keine modernen PDFs)"
        continue
    fi
    
    # Import für jede moderne PDF
    find "$dir" -name "[0-9]*.pdf" -type f | sort | while read pdf; do
        filename=$(basename "$pdf")
        echo -n "  → $filename ... "
        
        # Import mit Fehler-Handling
        output=$(python import_bank_pdfs.py import "$dir/" --file "$filename" 2>&1)
        
        if echo "$output" | grep -q "importiert"; then
            imported=$(echo "$output" | grep -oP '\d+(?= Transaktionen importiert)')
            echo "✅ $imported Trans."
            TOTAL_IMPORTED=$((TOTAL_IMPORTED + imported))
        elif echo "$output" | grep -q "Duplikat"; then
            duplicates=$(echo "$output" | grep -oP '\d+(?= Duplikate)')
            echo "⏩ $duplicates Duplikate"
            TOTAL_DUPLICATES=$((TOTAL_DUPLICATES + duplicates))
        else
            echo "❌ Fehler"
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
        fi
    done
done

echo ""
echo "========================================================================"
echo "ZUSAMMENFASSUNG"
echo "========================================================================"
echo "✅ Importiert:  $TOTAL_IMPORTED Transaktionen"
echo "⏩ Duplikate:   $TOTAL_DUPLICATES"
echo "❌ Fehler:      $TOTAL_FAILED PDFs"
echo ""
echo "Datenbank-Status:"
python import_bank_pdfs.py info
