#!/usr/bin/env python3
"""MCP Server für Claude Desktop - Greiner Portal"""
import json
import sys
import subprocess
import sqlite3
from pathlib import Path

BASE_DIR = Path('/opt/greiner-portal')
DB_PATH = BASE_DIR / 'data/greiner_controlling.db'

def handle_request(request):
    method = request.get('method')
    params = request.get('params', {})
    request_id = request.get('id')
    
    try:
        # MCP Protocol: initialize
        if method == 'initialize':
            response = {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': '2025-06-18',
                    'capabilities': {
                        'tools': {}
                    },
                    'serverInfo': {
                        'name': 'greiner-portal',
                        'version': '1.0.0'
                    }
                }
            }
            return response
        
        # MCP Protocol: initialized (notification)
        elif method == 'initialized':
            return None  # No response for notifications
        
        # Custom methods
        elif method == 'files/read':
            path = BASE_DIR / params.get('path', '')
            with open(path, 'r') as f:
                result = {'content': f.read(), 'path': str(path)}
        
        elif method == 'files/list':
            path = BASE_DIR / params.get('path', '')
            items = [{'name': p.name, 'type': 'dir' if p.is_dir() else 'file'} 
                    for p in path.iterdir()]
            result = {'items': items, 'path': str(path)}
        
        elif method == 'shell/exec':
            res = subprocess.run(
                params.get('command'),
                shell=True,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30
            )
            result = {
                'stdout': res.stdout,
                'stderr': res.stderr,
                'returncode': res.returncode
            }
        
        elif method == 'db/query':
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(params.get('query'))
            
            if params.get('query').strip().upper().startswith('SELECT'):
                rows = [dict(row) for row in cursor.fetchall()]
                result = {'results': rows, 'count': len(rows)}
            else:
                conn.commit()
                result = {'affected_rows': cursor.rowcount}
        
        elif method == 'system/info':
            result = {
                'base_dir': str(BASE_DIR),
                'db_path': str(DB_PATH),
                'python_version': sys.version
            }
        
        else:
            result = {'error': f'Unknown method: {method}'}
        
        # Return JSON-RPC response
        if request_id is not None:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result
            }
        return None
    
    except Exception as e:
        if request_id is not None:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }
        return None

def main():
    """Main MCP Server Loop"""
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("MCP Server started", file=sys.stderr, flush=True)
    
    try:
        while True:
            line = sys.stdin.readline()
            
            if not line:
                print("EOF received", file=sys.stderr, flush=True)
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                print(f"Received: {request.get('method')}", file=sys.stderr, flush=True)
                
                response = handle_request(request)
                
                if response:
                    print(json.dumps(response), flush=True)
            
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}", file=sys.stderr, flush=True)
            
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr, flush=True)
    
    except KeyboardInterrupt:
        print("Stopped", file=sys.stderr, flush=True)

if __name__ == '__main__':
    main()
