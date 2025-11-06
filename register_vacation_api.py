#!/usr/bin/env python3
"""
Registriert Vacation API in app.py
"""

import os

print("🔧 Registriere Vacation API in app.py...")

app_py = 'app.py'

# Prüfe ob app.py existiert
if not os.path.exists(app_py):
    print(f"❌ {app_py} nicht gefunden!")
    print("   Erstelle minimale app.py...")
    
    minimal_app = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Greiner Portal - Flask Application
"""

from flask import Flask, jsonify
from api.vacation_api import vacation_api

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(vacation_api)

@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'app': 'Greiner Portal',
        'apis': [
            '/api/vacation/health',
            '/api/vacation/balance/<id>',
            '/api/vacation/requests'
        ]
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    with open(app_py, 'w') as f:
        f.write(minimal_app)
    
    print(f"   ✓ Minimale app.py erstellt")
else:
    # Lese bestehende app.py
    with open(app_py, 'r') as f:
        content = f.read()
    
    # Prüfe ob API bereits registriert
    if 'vacation_api' in content:
        print("   ✓ API bereits registriert")
    else:
        print("   ⚠️  app.py existiert, aber API nicht registriert")
        print("   💡 Füge manuell hinzu:")
        print("")
        print("   from api.vacation_api import vacation_api")
        print("   app.register_blueprint(vacation_api)")

print("\n✅ Fertig!")
