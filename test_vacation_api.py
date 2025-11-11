from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/test')
def test():
    try:
        conn = sqlite3.connect('data/greiner_controlling.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM v_vacation_balance_2025 LIMIT 3")
        rows = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'data': [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001)
