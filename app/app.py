#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Greiner Portal - Flask Application
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE'] = '/opt/greiner-portal/data/greiner_controlling.db'

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Greiner Portal API',
        'version': '2.0'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'greiner-portal'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
