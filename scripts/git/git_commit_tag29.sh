#!/bin/bash
# Git-Commits für TAG 29 - Verkauf-Modul PRODUKTIONSREIF
# Datum: 11.11.2025
# Branch: feature/bankenspiegel-komplett

set -e

echo "🚀 TAG 29 - Git-Commits werden erstellt..."
echo ""

# Pfad prüfen
if [ ! -d "/opt/greiner-portal" ]; then
    echo "❌ Fehler: /opt/greiner-portal nicht gefunden!"
    exit 1
fi

cd /opt/greiner-portal

# Git-Status prüfen
echo "📊 Aktueller Git-Status:"
git status --short
echo ""

# Bestätigung
read -p "Möchten Sie fortfahren? (j/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    echo "❌ Abgebrochen."
    exit 1
fi

# ============================================================
# COMMIT 1: Port-Konfiguration Fix
# ============================================================
echo ""
echo "📝 COMMIT 1: Port-Konfiguration (unified 5000)..."

git add config/gunicorn.conf.py || true
git add install_nginx_config.sh || true
git add greiner-portal.conf || true

git commit -m "fix(config): Unified port configuration - all services on 5000

PROBLEM:
- NGINX: Routes pointed to different ports (5000 vs 8000)
- Gunicorn: Running on port 8000
- Result: HTTP 502 Bad Gateway on /urlaubsplaner/v2

SOLUTION:
- Gunicorn: Changed bind from 8000 → 5000
- NGINX: Unified all routes to proxy_pass port 5000
- Removed port inconsistencies

CHANGES:
- config/gunicorn.conf.py: bind = '127.0.0.1:5000'
- greiner-portal.conf: Unified NGINX config
- install_nginx_config.sh: Automated deployment

TESTING:
✅ curl http://127.0.0.1:5000/health → 200 OK
✅ curl http://10.80.80.20/urlaubsplaner/v2 → 200 OK
✅ Service restart successful

Resolves: Bug #1 (Urlaubsplaner 502 Error)
" || echo "⚠️  Commit 1 übersprungen (keine Änderungen)"

# ============================================================
# COMMIT 2: Navigation Updates
# ============================================================
echo ""
echo "📝 COMMIT 2: Navigation erweitert..."

git add templates/base.html || true

git commit -m "feat(navigation): Add Fahrzeugfinanzierungen menu + activate Urlaubsplaner

CHANGES:
1. Bankenspiegel Dropdown:
   - Added: Fahrzeugfinanzierungen link
   - Icon: bi-car-front
   - Route: /bankenspiegel/fahrzeugfinanzierungen

2. Urlaubsplaner Menu:
   - Removed: 'disabled' class
   - Changed: alert() → href='/urlaubsplaner/v2'
   - Status: Now fully clickable

CONTEXT:
- Page /bankenspiegel/fahrzeugfinanzierungen existed
- Displayed 191 vehicles, 5.22M EUR correctly
- But was not accessible via menu

FILES:
- templates/base.html: Navigation structure updated

TESTING:
✅ Menu displays Fahrzeugfinanzierungen
✅ Click navigates to correct page
✅ Data loads successfully

Resolves: Bug #3 (Missing menu link)
" || echo "⚠️  Commit 2 übersprungen (keine Änderungen)"

# ============================================================
# COMMIT 3: Verkauf Detail-Ansichten
# ============================================================
echo ""
echo "📝 COMMIT 3: Verkauf Detail-Ansichten (HAUPTFEATURE)..."

git add routes/verkauf_routes.py || true
git add api/verkauf_api.py || true

git commit -m "feat(verkauf): Complete detail views implementation with advanced filters

NEW ROUTES:
- GET /verkauf/auftragseingang/detail
- GET /verkauf/auslieferung/detail

NEW API ENDPOINTS (4):
1. GET /api/verkauf/auftragseingang/summary
   - Summary by brand and vehicle type
   - Based on: out_sales_contract_date
   
2. GET /api/verkauf/auftragseingang/detail
   - Detailed breakdown per salesman
   - Per salesman: Models grouped by type
   - Based on: out_sales_contract_date

3. GET /api/verkauf/auslieferung/summary
   - Summary by brand and vehicle type
   - Based on: out_invoice_date

4. GET /api/verkauf/auslieferung/detail
   - Detailed breakdown per salesman
   - Based on: out_invoice_date

FEATURES:
- Filter: Zeit (Tag/Monat)
- Filter: Standort (1=Deggendorf, 2=Landau)
- Filter: Verkäufer (dynamic from DB)
- Categorization:
  * N → Neuwagen
  * T/V → Test/Vorführwagen
  * G/D → Gebrauchtwagen

DATA SOURCES:
- sales table (LocoSoft PostgreSQL sync)
- employees table (for salesman names)
- LEFT JOIN: Shows inactive salesmen with sales

SQL LOGIC:
- Auftragseingang: WHERE strftime('%Y-%m', out_sales_contract_date) = ?
- Auslieferungen: WHERE strftime('%Y-%m', out_invoice_date) = ?
- Location filter: WHERE out_subsidiary = ?
- Salesman filter: WHERE salesman_number = ?

DIFFERENCE EXPLAINED:
- Auftragseingang: Contract date (when signed)
- Auslieferungen: Invoice date (when delivered)
- Shows: Lead time from order to delivery

RESPONSE FORMAT:
{
  'success': true,
  'month': 11,
  'year': 2025,
  'verkaufer': [
    {
      'verkaufer_nummer': 2003,
      'verkaufer_name': 'Max Mustermann',
      'neu': [{'modell': 'KONA', 'anzahl': 3}],
      'test_vorfuehr': [],
      'gebraucht': [],
      'summe_neu': 3,
      'summe_test_vorfuehr': 0,
      'summe_gebraucht': 0,
      'summe_gesamt': 3
    }
  ]
}

FILES:
- routes/verkauf_routes.py: 2 new routes
- api/verkauf_api.py: 4 new endpoints

TESTING:
✅ curl /api/verkauf/auftragseingang/summary?month=11&year=2025
✅ curl /api/verkauf/auftragseingang/detail?month=11&year=2025
✅ curl /api/verkauf/auslieferung/summary?month=11&year=2025
✅ curl /api/verkauf/auslieferung/detail?month=11&year=2025
✅ Browser: Pages load with data
✅ Filters working correctly

RESOLVES:
- Bug #4: /verkauf/auftragseingang/detail 404
- Bug #5: /verkauf/auslieferung/detail 404

IMPACT:
Sales management now has complete visibility:
- Who sold what?
- New vs. used breakdown
- Location-specific performance
- Time-based comparisons
" || echo "⚠️  Commit 3 übersprungen (keine Änderungen)"

# ============================================================
# Summary
# ============================================================
echo ""
echo "✅ Alle Commits erstellt!"
echo ""
echo "📊 Git-Log (letzte 5 Commits):"
git log --oneline -5
echo ""

# Push-Frage
read -p "Möchten Sie zum Remote-Repository pushen? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    echo "🚀 Pushing to origin/feature/bankenspiegel-komplett..."
    git push origin feature/bankenspiegel-komplett
    echo "✅ Push erfolgreich!"
else
    echo "ℹ️  Nicht gepusht. Führe später aus:"
    echo "   git push origin feature/bankenspiegel-komplett"
fi

echo ""
echo "🎉 TAG 29 - Git-Commits abgeschlossen!"
echo ""
echo "📋 Nächste Schritte:"
echo "1. User-Testing durchführen"
echo "2. Feedback sammeln"
echo "3. Bei Bedarf: Merge in main-Branch"
