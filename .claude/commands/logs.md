# /logs - Server-Logs anzeigen

Zeige relevante Logs vom Greiner Portal Server.

## Anweisungen

Frage den User welche Logs gewünscht sind:

### Optionen:

1. **Portal-Logs (Standard):**
   ```
   ssh ag-admin@10.80.80.20 "journalctl -u greiner-portal --since '30 minutes ago' --no-pager | tail -50"
   ```

2. **Celery Worker Logs:**
   ```
   ssh ag-admin@10.80.80.20 "journalctl -u celery-worker --since '30 minutes ago' --no-pager | tail -50"
   ```

3. **Error-Logs nur:**
   ```
   ssh ag-admin@10.80.80.20 "journalctl -u greiner-portal --since '1 hour ago' --no-pager | grep -i 'error\|exception\|failed'"
   ```

4. **Live-Logs (Follow):**
   - Informiere dass dies im Terminal ausgeführt werden muss:
   ```
   ssh ag-admin@10.80.80.20 "journalctl -u greiner-portal -f"
   ```

## Parameter
- Zeitraum kann angepasst werden (z.B. "logs letzte stunde")
