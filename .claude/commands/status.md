# /status - Server & Service Status

Zeige den aktuellen Status des Greiner Portal Servers.

## Anweisungen

Führe folgende Checks via SSH auf 10.80.80.20 aus:

1. **Service Health Check:**
   ```
   curl -s http://localhost:5000/api/admin/health
   ```

2. **Celery Worker Status:**
   ```
   systemctl is-active celery-worker
   ```

3. **Redis Status:**
   ```
   redis-cli ping
   ```

4. **Disk Space:**
   ```
   df -h /opt/greiner-portal
   ```

5. **Letzte Log-Einträge:**
   ```
   journalctl -u greiner-portal --since "10 minutes ago" --no-pager | tail -10
   ```

## Output Format
Zeige eine übersichtliche Zusammenfassung mit Status-Indikatoren.
