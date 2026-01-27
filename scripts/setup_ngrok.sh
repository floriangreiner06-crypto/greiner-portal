#!/bin/bash
# Ngrok Installation Script für WhatsApp Webhook Testing
# TAG 211

set -e

echo "🔧 Ngrok Installation für WhatsApp Webhook Testing"
echo ""

# Prüfe ob bereits installiert
if command -v ngrok &> /dev/null; then
    echo "✅ Ngrok ist bereits installiert"
    ngrok version
    exit 0
fi

# Download und Installation
echo "📥 Lade Ngrok herunter..."
cd /tmp
wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

echo "📦 Entpacke Ngrok..."
tar -xzf ngrok-v3-stable-linux-amd64.tgz

echo "📁 Verschiebe Ngrok nach /usr/local/bin..."
sudo mv ngrok /usr/local/bin/

echo "🧹 Räume auf..."
rm ngrok-v3-stable-linux-amd64.tgz

echo ""
echo "✅ Ngrok erfolgreich installiert!"
echo ""
echo "📋 Nächste Schritte:"
echo "1. Ngrok Account erstellen (optional, aber empfohlen):"
echo "   https://dashboard.ngrok.com/signup"
echo ""
echo "2. Auth Token setzen (falls Account erstellt):"
echo "   ngrok config add-authtoken DEIN_TOKEN"
echo ""
echo "3. Tunnel starten:"
echo "   ngrok http 5000"
echo ""
echo "4. HTTPS-URL kopieren und in Twilio Sandbox eintragen"
echo ""

ngrok version
