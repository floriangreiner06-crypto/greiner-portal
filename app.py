#!/usr/bin/env python3
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
