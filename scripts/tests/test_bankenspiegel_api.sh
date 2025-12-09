#!/bin/bash
# ============================================================================
# BANKENSPIEGEL API - TEST SCRIPT
# ============================================================================
# Beschreibung: Testet alle Bankenspiegel API Endpoints
# Verwendung: ./test_bankenspiegel_api.sh
# ============================================================================

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE="http://localhost:5000/api/bankenspiegel"

echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}BANKENSPIEGEL API - TESTS${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

# Test 1: Health Check
echo -e "${BLUE}TEST 1: Health Check${NC}"
echo -e "${YELLOW}GET $API_BASE/health${NC}"
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Dashboard
echo -e "${BLUE}TEST 2: Dashboard (KPIs)${NC}"
echo -e "${YELLOW}GET $API_BASE/dashboard${NC}"
curl -s "$API_BASE/dashboard" | python3 -m json.tool
echo ""
echo ""

# Test 3: Konten (alle)
echo -e "${BLUE}TEST 3: Alle aktiven Konten${NC}"
echo -e "${YELLOW}GET $API_BASE/konten${NC}"
curl -s "$API_BASE/konten" | python3 -m json.tool | head -50
echo ""
echo ""

# Test 4: Konten (Filter nach Bank)
echo -e "${BLUE}TEST 4: Konten von Bank ID 1${NC}"
echo -e "${YELLOW}GET $API_BASE/konten?bank_id=1${NC}"
curl -s "$API_BASE/konten?bank_id=1" | python3 -m json.tool
echo ""
echo ""

# Test 5: Transaktionen (letzte 10)
echo -e "${BLUE}TEST 5: Letzte 10 Transaktionen${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?limit=10${NC}"
curl -s "$API_BASE/transaktionen?limit=10" | python3 -m json.tool
echo ""
echo ""

# Test 6: Transaktionen mit Datum-Filter
HEUTE=$(date +%Y-%m-%d)
VOR_30_TAGEN=$(date -d "30 days ago" +%Y-%m-%d)
echo -e "${BLUE}TEST 6: Transaktionen letzte 30 Tage${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?von=$VOR_30_TAGEN&bis=$HEUTE&limit=20${NC}"
curl -s "$API_BASE/transaktionen?von=$VOR_30_TAGEN&bis=$HEUTE&limit=20" | python3 -m json.tool
echo ""
echo ""

# Test 7: Transaktionen mit Suche
echo -e "${BLUE}TEST 7: Transaktionen-Suche (Gehalt)${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?suche=Gehalt&limit=5${NC}"
curl -s "$API_BASE/transaktionen?suche=Gehalt&limit=5" | python3 -m json.tool
echo ""
echo ""

# Test 8: Transaktionen mit Kategorie-Filter
echo -e "${BLUE}TEST 8: Transaktionen nach Kategorie${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?kategorie=Gehalt&limit=5${NC}"
curl -s "$API_BASE/transaktionen?kategorie=Gehalt&limit=5" | python3 -m json.tool
echo ""
echo ""

# Test 9: Nur Ausgaben (negative Beträge)
echo -e "${BLUE}TEST 9: Nur Ausgaben (Betrag < 0)${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?betrag_max=-0.01&limit=10${NC}"
curl -s "$API_BASE/transaktionen?betrag_max=-0.01&limit=10" | python3 -m json.tool
echo ""
echo ""

# Test 10: Nur Einnahmen (positive Beträge)
echo -e "${BLUE}TEST 10: Nur Einnahmen (Betrag > 0)${NC}"
echo -e "${YELLOW}GET $API_BASE/transaktionen?betrag_min=0.01&limit=10${NC}"
curl -s "$API_BASE/transaktionen?betrag_min=0.01&limit=10" | python3 -m json.tool
echo ""
echo ""

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}TESTS ABGESCHLOSSEN${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Weitere Test-Möglichkeiten:${NC}"
echo ""
echo "# Spezifisches Konto"
echo "curl -s '$API_BASE/transaktionen?konto_id=1&limit=10' | python3 -m json.tool"
echo ""
echo "# Großer Betrag"
echo "curl -s '$API_BASE/transaktionen?betrag_min=1000&limit=10' | python3 -m json.tool"
echo ""
echo "# Bestimmter Monat"
echo "curl -s '$API_BASE/transaktionen?von=2025-10-01&bis=2025-10-31&limit=50' | python3 -m json.tool"
echo ""
