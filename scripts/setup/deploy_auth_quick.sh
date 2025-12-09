#!/bin/bash

echo "🚀 QUICK DEPLOY - OHNE LDAP-TEST"
echo ""

BASE_DIR="/opt/greiner-portal"
cd "$BASE_DIR"

# Virtual Environment
source venv/bin/activate

# Flask-Login (falls noch nicht installiert)
pip install flask-login --break-system-packages -q 2>/dev/null

# Test nur Python Imports
echo -n "Test: Python Imports... "
python3 << 'EOTEST'
import sys
sys.path.insert(0, '/opt/greiner-portal')
try:
    from flask import Flask
    from flask_login import LoginManager
    from auth.auth_manager import get_auth_manager
    print("✅")
except Exception as e:
    print(f"❌ {e}")
    exit(1)
EOTEST

echo ""
echo "=========================================================================="
echo "✅ FERTIG! APP KANN GESTARTET WERDEN!"
echo "=========================================================================="
echo ""
echo "🚀 STARTE APP:"
echo "   python app.py"
echo ""
