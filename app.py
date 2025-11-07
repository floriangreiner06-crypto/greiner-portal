# -*- coding: utf-8 -*-
"""
Greiner Portal - Flask Application
"""
from flask import Flask, jsonify, render_template
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

# Neue Route für Urlaubsplaner V2
@app.route('/urlaubsplaner/v2')
def urlaubsplaner_v2():
    """Moderne Urlaubsplaner Oberfläche (V2)"""
    return render_template('urlaubsplaner_v2.html')


# ============================================================================
# BANKENSPIEGEL REST API
# ============================================================================
from api.bankenspiegel_api import bankenspiegel_api
app.register_blueprint(bankenspiegel_api)
print("✅ Bankenspiegel API registriert: /api/bankenspiegel/")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


