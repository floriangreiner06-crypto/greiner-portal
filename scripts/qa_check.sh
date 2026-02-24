#!/usr/bin/env bash
# Qualitätscheck Phase 1: Ruff, Bandit, pip-audit
# Aufruf: aus Projektroot /opt/greiner-portal:  ./scripts/qa_check.sh
# Oder:   bash scripts/qa_check.sh

cd "$(dirname "$0")/.."
VENV="${VENV:-.venv}"

FAIL=0

echo "=== Ruff (api/ routes/ auth/ celery_app/) ==="
"$VENV/bin/ruff" check api/ routes/ auth/ celery_app/ --statistics || FAIL=1

echo ""
echo "=== Bandit (api/ routes/ auth/ celery_app/) ==="
"$VENV/bin/bandit" -r api/ routes/ auth/ celery_app/ -x .venv --format txt || FAIL=1

echo ""
echo "=== pip-audit ==="
"$VENV/bin/pip-audit" || FAIL=1

if [ "$FAIL" -ne 0 ]; then
    echo ""
    echo "Mindestens ein Check ist fehlgeschlagen (Ruff/Bandit/pip-audit)."
    echo "Details siehe docs/QUALITAETSCHECK_ERGEBNIS_2026-02-24.md"
    exit 1
fi

echo ""
echo "Alle Checks bestanden."
exit 0
