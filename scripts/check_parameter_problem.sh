#!/bin/bash
# Schnell-Check: Parameter-Problem prüfen
# TAG 194: Hybrid-Ansatz Parameter-Problem

echo "=========================================="
echo "PARAMETER-PROBLEM SCHNELL-CHECK"
echo "=========================================="
echo ""

# 1. Query-Info
echo "=== 1. Query-Info ==="
if [ -f /tmp/debug_query.sql ]; then
    COUNT=$(grep -o '%s' /tmp/debug_query.sql | wc -l)
    LINES=$(wc -l < /tmp/debug_query.sql)
    echo "✅ Query gefunden: $LINES Zeilen"
    echo "   %s Platzhalter: $COUNT"
    if [ "$COUNT" -eq 9 ]; then
        echo "   ✅ Korrekt (9 erwartet)"
    else
        echo "   ❌ Falsch (9 erwartet, $COUNT gefunden)"
    fi
else
    echo "❌ /tmp/debug_query.sql nicht gefunden"
    echo "   → Führe zuerst einen Test aus, um die Datei zu erstellen"
fi

echo ""

# 2. Parameter-Info
echo "=== 2. Parameter-Info (vor execute) ==="
if [ -f /tmp/debug_params.txt ]; then
    COUNT=$(head -1 /tmp/debug_params.txt | grep -o '[0-9]*' | head -1)
    echo "✅ Parameter-Datei gefunden"
    echo "   Anzahl Parameter: $COUNT"
    if [ "$COUNT" -eq 9 ]; then
        echo "   ✅ Korrekt (9 erwartet)"
    else
        echo "   ❌ Falsch (9 erwartet, $COUNT gefunden)"
    fi
    echo ""
    echo "   Parameter-Details:"
    tail -n +2 /tmp/debug_params.txt | head -10 | sed 's/^/      /'
else
    echo "❌ /tmp/debug_params.txt nicht gefunden"
fi

echo ""

# 3. Parameter nach Erstellung
echo "=== 3. Parameter-Info (nach Erstellung) ==="
if [ -f /tmp/debug_params_created.txt ]; then
    COUNT=$(head -1 /tmp/debug_params_created.txt | grep -o '[0-9]*' | head -1)
    echo "✅ Parameter-Datei gefunden"
    echo "   Anzahl Parameter: $COUNT"
    if [ "$COUNT" -eq 9 ]; then
        echo "   ✅ Korrekt (9 erwartet)"
    else
        echo "   ❌ Falsch (9 erwartet, $COUNT gefunden)"
    fi
else
    echo "⚠️  /tmp/debug_params_created.txt nicht gefunden"
    echo "   → Wird nur erstellt, wenn Debug-Code aktiv ist"
fi

echo ""

# 4. Vergleich
echo "=== 4. Vergleich ==="
if [ -f /tmp/debug_query.sql ] && [ -f /tmp/debug_params.txt ]; then
    QUERY_COUNT=$(grep -o '%s' /tmp/debug_query.sql | wc -l)
    PARAM_COUNT=$(head -1 /tmp/debug_params.txt | grep -o '[0-9]*' | head -1)
    
    if [ "$QUERY_COUNT" -eq "$PARAM_COUNT" ]; then
        echo "✅ Query und Parameter stimmen überein ($QUERY_COUNT)"
    else
        echo "❌ Query und Parameter stimmen NICHT überein!"
        echo "   Query: $QUERY_COUNT %s Platzhalter"
        echo "   Parameter: $PARAM_COUNT Parameter"
        echo "   Differenz: $((QUERY_COUNT - PARAM_COUNT))"
    fi
else
    echo "⚠️  Kann nicht verglichen werden (Dateien fehlen)"
fi

echo ""
echo "=========================================="
echo "NÄCHSTE SCHRITTE:"
echo "=========================================="
echo "1. Prüfe /tmp/debug_query.sql (Query-Struktur)"
echo "2. Prüfe /tmp/debug_params.txt (Parameter-Liste)"
echo "3. Teste Query direkt in PostgreSQL"
echo "4. Siehe: docs/MANUELLE_PRUEFUNG_PARAMETER_PROBLEM_TAG194.md"
echo ""
