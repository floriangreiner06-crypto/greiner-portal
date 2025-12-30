#!/bin/bash
# =============================================================================
# PostgreSQL Setup für DRIVE Portal
# =============================================================================
# TAG 135: Erstellt Datenbank, User und importiert Daten von SQLite
#
# Verwendung:
#   sudo ./postgresql_setup.sh
#
# Voraussetzungen:
#   - PostgreSQL 16 installiert
#   - Root/sudo Rechte
#   - SQLite-Datenbank vorhanden
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DRIVE Portal - PostgreSQL Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Konfiguration
DB_NAME="drive_portal"
DB_USER="drive_user"
DB_PASSWORD="DrivePortal2024!"  # ÄNDERN IN PRODUKTION!
SQLITE_DB="/opt/greiner-portal/data/greiner_controlling.db"
BACKUP_DIR="/opt/greiner-portal/backups"

# =============================================================================
# 1. Prüfungen
# =============================================================================
echo -e "\n${YELLOW}[1/6] Prüfe Voraussetzungen...${NC}"

# Root-Check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
    exit 1
fi

# PostgreSQL-Check
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL nicht installiert!${NC}"
    echo "Installation: apt install postgresql postgresql-contrib"
    exit 1
fi

# SQLite-Check
if [ ! -f "$SQLITE_DB" ]; then
    echo -e "${RED}SQLite-Datenbank nicht gefunden: $SQLITE_DB${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Alle Voraussetzungen erfüllt${NC}"

# =============================================================================
# 2. Backup erstellen
# =============================================================================
echo -e "\n${YELLOW}[2/6] Erstelle SQLite-Backup...${NC}"

mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/sqlite_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$SQLITE_DB" "$BACKUP_FILE"
echo -e "${GREEN}✓ Backup erstellt: $BACKUP_FILE${NC}"

# =============================================================================
# 3. PostgreSQL starten
# =============================================================================
echo -e "\n${YELLOW}[3/6] Starte PostgreSQL...${NC}"

systemctl start postgresql
systemctl enable postgresql
sleep 2

if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL läuft${NC}"
else
    echo -e "${RED}PostgreSQL konnte nicht gestartet werden!${NC}"
    exit 1
fi

# =============================================================================
# 4. Datenbank und User anlegen
# =============================================================================
echo -e "\n${YELLOW}[4/6] Erstelle Datenbank und User...${NC}"

# Prüfe ob DB bereits existiert
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${YELLOW}⚠ Datenbank '$DB_NAME' existiert bereits${NC}"
    read -p "Löschen und neu erstellen? (j/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
        sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
    else
        echo "Abbruch."
        exit 0
    fi
fi

# User erstellen
sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"

# Datenbank erstellen
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Rechte setzen
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"

echo -e "${GREEN}✓ Datenbank '$DB_NAME' und User '$DB_USER' erstellt${NC}"

# =============================================================================
# 5. pgloader installieren und Migration
# =============================================================================
echo -e "\n${YELLOW}[5/6] Installiere pgloader und migriere Daten...${NC}"

# pgloader installieren falls nicht vorhanden
if ! command -v pgloader &> /dev/null; then
    apt-get update
    apt-get install -y pgloader
fi

# pgloader Konfiguration erstellen
PGLOADER_CONFIG="/tmp/pgloader_drive.load"
cat > $PGLOADER_CONFIG << EOF
LOAD DATABASE
    FROM sqlite://$SQLITE_DB
    INTO postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '128MB', maintenance_work_mem to '512 MB'

CAST type datetime to timestamp using zero-dates-to-null,
     type integer when (= precision 1) to boolean using tinyint-to-boolean

BEFORE LOAD DO
    \$\$ DROP SCHEMA IF EXISTS public CASCADE; \$\$,
    \$\$ CREATE SCHEMA public; \$\$,
    \$\$ GRANT ALL ON SCHEMA public TO $DB_USER; \$\$
;
EOF

echo "Starte Migration (kann einige Minuten dauern)..."
pgloader $PGLOADER_CONFIG

echo -e "${GREEN}✓ Daten migriert${NC}"

# =============================================================================
# 6. Verifizierung
# =============================================================================
echo -e "\n${YELLOW}[6/6] Verifiziere Migration...${NC}"

# Tabellen zählen
PG_TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
SQLITE_TABLES=$(sqlite3 $SQLITE_DB "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")

echo "SQLite Tabellen:     $SQLITE_TABLES"
echo "PostgreSQL Tabellen: $PG_TABLES"

# Wichtige Tabellen prüfen
echo -e "\nWichtige Tabellen:"
for table in employees sales users vacation_bookings konten; do
    PG_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "FEHLER")
    SQLITE_COUNT=$(sqlite3 $SQLITE_DB "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "FEHLER")

    if [ "$PG_COUNT" = "$SQLITE_COUNT" ]; then
        echo -e "  ${GREEN}✓ $table: $PG_COUNT Zeilen${NC}"
    else
        echo -e "  ${RED}✗ $table: SQLite=$SQLITE_COUNT, PG=$PG_COUNT${NC}"
    fi
done

# =============================================================================
# 7. Konfiguration ausgeben
# =============================================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Füge folgende Zeilen zur .env hinzu:"
echo ""
echo "  DB_TYPE=postgresql"
echo "  DB_HOST=localhost"
echo "  DB_PORT=5432"
echo "  DB_NAME=$DB_NAME"
echo "  DB_USER=$DB_USER"
echo "  DB_PASSWORD=$DB_PASSWORD"
echo ""
echo "Dann Service neustarten:"
echo "  sudo systemctl restart greiner-portal"
echo ""
echo -e "${YELLOW}ROLLBACK:${NC}"
echo "  1. In .env: DB_TYPE=sqlite setzen"
echo "  2. sudo systemctl restart greiner-portal"
echo ""
echo "SQLite-Backup: $BACKUP_FILE"
