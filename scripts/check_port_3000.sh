#!/bin/bash
# Prüft was auf Port 3000 läuft

echo "=== Port 3000 Status ==="
echo ""

# Prüfe mit netstat
echo "Netstat:"
netstat -tlnp 2>/dev/null | grep :3000 || echo "Kein Prozess gefunden"

echo ""
echo "Lsof (benötigt sudo):"
sudo lsof -i :3000 2>/dev/null || echo "Kein Prozess gefunden"

echo ""
echo "HTTP-Test:"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$HTTP_RESPONSE" != "000" ]; then
    echo "HTTP Response Code: $HTTP_RESPONSE"
    curl -s http://localhost:3000 2>&1 | head -10
else
    echo "Keine HTTP-Antwort"
fi

echo ""
echo "=== Ende ==="
