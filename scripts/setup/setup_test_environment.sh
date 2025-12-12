#!/bin/bash
#===============================================================================
# GREINER PORTAL - TEST-UMGEBUNG SETUP
#===============================================================================
# Erstellt eine separate Test-Instanz neben der Produktiv-Umgebung
# 
# Verwendung:
#   sudo bash setup_test_environment.sh
#
# Ergebnis:
#   - /opt/greiner-test/          (Test-Verzeichnis)
#   - Port 5001                    (Test-Port)
#   - greiner_test.db              (Separate Test-DB)
#   - systemd service              (greiner-test.service)
#
# Erstellt: 2025-12-12
#===============================================================================

set -e  # Bei Fehler abbrechen

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
PROD_DIR="/opt/greiner-portal"
TEST_DIR="/opt/greiner-test"
TEST_PORT="5001"
USER="ag-admin"
GROUP="ag-admin"

#===============================================================================
# FUNKTIONEN
#===============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Dieses Script muss als root ausgeführt werden!"
        log_info "Verwende: sudo bash setup_test_environment.sh"
        exit 1
    fi
}

check_prod_exists() {
    if [[ ! -d "$PROD_DIR" ]]; then
        log_error "Produktiv-Verzeichnis nicht gefunden: $PROD_DIR"
        exit 1
    fi
    log_success "Produktiv-Verzeichnis gefunden: $PROD_DIR"
}

#===============================================================================
# HAUPTSCRIPT
#===============================================================================

echo ""
echo "==============================================================================="
echo "  GREINER PORTAL - TEST-UMGEBUNG SETUP"
echo "==============================================================================="
echo ""

# Prüfungen
check_root
check_prod_exists

# Bestätigung
echo ""
log_warn "Dieses Script wird folgendes erstellen:"
echo "  - Test-Verzeichnis:  $TEST_DIR"
echo "  - Test-Port:         $TEST_PORT"
echo "  - Test-Datenbank:    greiner_test.db (Kopie von Produktiv)"
echo "  - Systemd Service:   greiner-test.service"
echo ""
read -p "Fortfahren? (j/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    log_info "Abgebrochen."
    exit 0
fi

#-------------------------------------------------------------------------------
# Schritt 1: Test-Verzeichnis erstellen
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 1/6: Test-Verzeichnis erstellen..."

if [[ -d "$TEST_DIR" ]]; then
    log_warn "Test-Verzeichnis existiert bereits!"
    read -p "Löschen und neu erstellen? (j/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf "$TEST_DIR"
        log_info "Altes Verzeichnis gelöscht."
    else
        log_error "Abgebrochen. Bitte manuell bereinigen."
        exit 1
    fi
fi

# Kopieren (ohne data/ und logs/ - die erstellen wir separat)
mkdir -p "$TEST_DIR"
cp -r "$PROD_DIR/api" "$TEST_DIR/"
cp -r "$PROD_DIR/auth" "$TEST_DIR/"
cp -r "$PROD_DIR/config" "$TEST_DIR/"
cp -r "$PROD_DIR/decorators" "$TEST_DIR/"
cp -r "$PROD_DIR/migrations" "$TEST_DIR/"
cp -r "$PROD_DIR/parsers" "$TEST_DIR/"
cp -r "$PROD_DIR/routes" "$TEST_DIR/"
cp -r "$PROD_DIR/scheduler" "$TEST_DIR/"
cp -r "$PROD_DIR/scripts" "$TEST_DIR/"
cp -r "$PROD_DIR/static" "$TEST_DIR/"
cp -r "$PROD_DIR/templates" "$TEST_DIR/"
cp -r "$PROD_DIR/tools" "$TEST_DIR/"
cp -r "$PROD_DIR/celery_app" "$TEST_DIR/" 2>/dev/null || true
cp "$PROD_DIR/app.py" "$TEST_DIR/"
cp "$PROD_DIR/requirements.txt" "$TEST_DIR/"
cp "$PROD_DIR/requirements_auth.txt" "$TEST_DIR/" 2>/dev/null || true
cp "$PROD_DIR/README.md" "$TEST_DIR/" 2>/dev/null || true

# Leere Verzeichnisse erstellen
mkdir -p "$TEST_DIR/data"
mkdir -p "$TEST_DIR/logs"
mkdir -p "$TEST_DIR/backups"

log_success "Test-Verzeichnis erstellt: $TEST_DIR"

#-------------------------------------------------------------------------------
# Schritt 2: Test-Datenbank kopieren
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 2/6: Test-Datenbank erstellen..."

PROD_DB="$PROD_DIR/data/greiner_controlling.db"
TEST_DB="$TEST_DIR/data/greiner_test.db"

if [[ -f "$PROD_DB" ]]; then
    cp "$PROD_DB" "$TEST_DB"
    log_success "Datenbank kopiert: $TEST_DB"
else
    log_warn "Produktiv-DB nicht gefunden, erstelle leere DB..."
    touch "$TEST_DB"
fi

#-------------------------------------------------------------------------------
# Schritt 3: Virtual Environment erstellen
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 3/6: Virtual Environment erstellen..."

python3 -m venv "$TEST_DIR/venv"
source "$TEST_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$TEST_DIR/requirements.txt" -q
deactivate

log_success "Virtual Environment erstellt"

#-------------------------------------------------------------------------------
# Schritt 4: Konfiguration anpassen
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 4/6: Konfiguration anpassen..."

# .env anpassen (falls vorhanden)
ENV_FILE="$TEST_DIR/config/.env"
if [[ -f "$ENV_FILE" ]]; then
    # DB-Pfad ändern
    sed -i 's|greiner_controlling.db|greiner_test.db|g' "$ENV_FILE"
    sed -i 's|/opt/greiner-portal|/opt/greiner-test|g' "$ENV_FILE"
    log_success ".env angepasst"
else
    log_warn ".env nicht gefunden, überspringe..."
fi

# Gunicorn Config erstellen
cat > "$TEST_DIR/config/gunicorn_test.conf.py" << 'EOF'
# Gunicorn Konfiguration für TEST-Umgebung
bind = "0.0.0.0:5001"
workers = 2
worker_class = "sync"
timeout = 120
accesslog = "/opt/greiner-test/logs/access.log"
errorlog = "/opt/greiner-test/logs/error.log"
loglevel = "debug"
EOF

log_success "Gunicorn-Config erstellt"

#-------------------------------------------------------------------------------
# Schritt 5: Rechte setzen
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 5/6: Rechte setzen..."

chown -R "$USER:$GROUP" "$TEST_DIR"
chmod -R 755 "$TEST_DIR"
chmod 664 "$TEST_DB"

log_success "Rechte gesetzt für $USER:$GROUP"

#-------------------------------------------------------------------------------
# Schritt 6: Systemd Service erstellen
#-------------------------------------------------------------------------------
echo ""
log_info "Schritt 6/6: Systemd Service erstellen..."

SERVICE_FILE="/etc/systemd/system/greiner-test.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Greiner Portal TEST Environment
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$TEST_DIR
Environment="PATH=$TEST_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_ENV=development"
Environment="FLASK_DEBUG=1"
ExecStart=$TEST_DIR/venv/bin/gunicorn -c $TEST_DIR/config/gunicorn_test.conf.py app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable greiner-test

log_success "Systemd Service erstellt: greiner-test.service"

#-------------------------------------------------------------------------------
# Service starten
#-------------------------------------------------------------------------------
echo ""
log_info "Starte Test-Service..."

systemctl start greiner-test
sleep 2

if systemctl is-active --quiet greiner-test; then
    log_success "Test-Service läuft!"
else
    log_error "Service konnte nicht gestartet werden!"
    log_info "Prüfe mit: journalctl -u greiner-test -f"
fi

#===============================================================================
# ZUSAMMENFASSUNG
#===============================================================================

echo ""
echo "==============================================================================="
echo "  SETUP ABGESCHLOSSEN!"
echo "==============================================================================="
echo ""
echo "  TEST-UMGEBUNG:"
echo "  ─────────────────────────────────────────────────────────────────────────"
echo "  Verzeichnis:    $TEST_DIR"
echo "  Datenbank:      $TEST_DIR/data/greiner_test.db"
echo "  Port:           $TEST_PORT"
echo "  URL:            http://10.80.80.20:$TEST_PORT"
echo ""
echo "  BEFEHLE:"
echo "  ─────────────────────────────────────────────────────────────────────────"
echo "  Status:         sudo systemctl status greiner-test"
echo "  Starten:        sudo systemctl start greiner-test"
echo "  Stoppen:        sudo systemctl stop greiner-test"
echo "  Neustart:       sudo systemctl restart greiner-test"
echo "  Logs:           journalctl -u greiner-test -f"
echo ""
echo "  WORKFLOW:"
echo "  ─────────────────────────────────────────────────────────────────────────"
echo "  1. Datei nach TEST kopieren:"
echo "     cp /mnt/greiner-portal-sync/api/xyz.py /opt/greiner-test/api/"
echo ""
echo "  2. Test-Service neustarten:"
echo "     sudo systemctl restart greiner-test"
echo ""
echo "  3. Testen auf: http://10.80.80.20:$TEST_PORT"
echo ""
echo "  4. Wenn OK → Nach PRODUKTIV kopieren:"
echo "     cp /opt/greiner-test/api/xyz.py /opt/greiner-portal/api/"
echo "     sudo systemctl restart greiner-portal"
echo ""
echo "  DB AKTUALISIEREN (Test-DB mit frischen Produktiv-Daten):"
echo "  ─────────────────────────────────────────────────────────────────────────"
echo "  sudo systemctl stop greiner-test"
echo "  cp $PROD_DIR/data/greiner_controlling.db $TEST_DIR/data/greiner_test.db"
echo "  sudo systemctl start greiner-test"
echo ""
echo "==============================================================================="
