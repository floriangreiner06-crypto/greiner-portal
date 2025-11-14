#!/bin/bash
echo "🧹 FINALES CLEANUP - Letzte 13 Dateien..."

# Maintenance Scripts
mv cleanup_now.sh cleanup_root_complete.sh scripts/maintenance/ 2>/dev/null
mv add_missing_columns.py delete_bookings.py scripts/maintenance/ 2>/dev/null
echo "✅ Maintenance Scripts verschoben"

# Setup Scripts
mv install.sh patch_app_auth.sh scripts/setup/ 2>/dev/null
echo "✅ Setup Scripts verschoben"

# Tests
mv test_bankenspiegel_api.sh scripts/tests/ 2>/dev/null
echo "✅ Test Scripts verschoben"

# Archive (alte/ungenutzte)
mv debug_hyundai_bestandsliste.py liquiditaets_dashboard.py scripts/archive/ 2>/dev/null
mv import_november_all_accounts_v2.py scripts/imports/archive/ 2>/dev/null
echo "✅ Alte Scripts archiviert"

# Sync
if [ -f "sync_ldap_employees.py" ] && [ -f "sync_employees.py" ]; then
    # Prüfen ob Duplikat
    if diff sync_ldap_employees.py sync_employees.py > /dev/null 2>&1; then
        mv sync_ldap_employees.py scripts/sync/archive/
        echo "✅ sync_ldap_employees.py (Duplikat archiviert)"
    else
        mv sync_ldap_employees.py scripts/sync/
        echo "✅ sync_ldap_employees.py → scripts/sync/"
    fi
elif [ -f "sync_ldap_employees.py" ]; then
    mv sync_ldap_employees.py scripts/sync/
    echo "✅ sync_ldap_employees.py → scripts/sync/"
fi

# Alte Requirements
mv requirements_auth.txt docs/archive/ 2>/dev/null
echo "✅ requirements_auth.txt → docs/archive/"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ FINALES CLEANUP ABGESCHLOSSEN"
echo "════════════════════════════════════════════════════════════"
ls -1 *.md *.py *.sh *.txt 2>/dev/null | wc -l | xargs echo "Dateien im Root:"
