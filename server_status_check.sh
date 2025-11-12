#!/bin/bash
################################################################################
# GREINER PORTAL - SERVER STATUS CHECK
# =====================================
# Komplette Analyse des Server-Zustands für Claude-Sessions
#
# Usage: ./server_status_check.sh > SERVER_STATUS.txt
#
# Autor: Claude AI
# Datum: 12.11.2025
# Version: 1.0
################################################################################

set -e

# Farben (nur wenn Terminal)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    CYAN=''
    YELLOW=''
    RED=''
    NC=''
fi

# Konfiguration
PORTAL_DIR="/opt/greiner-portal"
DB_PATH="${PORTAL_DIR}/data/greiner_controlling.db"
VENV_PATH="${PORTAL_DIR}/venv"
PDF_MOUNT="/mnt/buchhaltung/Kontoauszüge"

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🔍 GREINER PORTAL - SERVER STATUS CHECK                              ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Datum: $(date '+%Y-%m-%d %H:%M:%S')"
echo "User:  $(whoami)"
echo "Host:  $(hostname)"
echo ""

################################################################################
# 1. VERZEICHNIS-STRUKTUR
################################################################################
echo "═══════════════════════════════════════════════════════════════════════════"
echo "📁 VERZEICHNIS-STRUKTUR"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

if [ -d "$PORTAL_DIR" ]; then
    echo "✅ Portal-Verzeichnis existiert: $PORTAL_DIR"
    cd "$PORTAL_DIR" || exit 1
    
    echo ""
    echo "Hauptverzeichnis-Inhalt:"
    ls -lah --color=never | head -20
    
    echo ""
    echo "Wichtige Unterverzeichnisse:"
    for dir in api routes auth decorators parsers templates static data scripts docs migrations logs config; do
        if [ -d "$dir" ]; then
            count=$(find "$dir" -type f 2>/dev/null | wc -l)
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            echo "  ✅ $dir/ ($count files, $size)"
        else
            echo "  ❌ $dir/ - FEHLT!"
        fi
    done
    
    echo ""
    echo "Kritische Dateien:"
    for file in app.py config/credentials.json requirements.txt .gitignore; do
        if [ -f "$file" ]; then
            size=$(ls -lh "$file" | awk '{print $5}')
            modified=$(stat -c '%y' "$file" | cut -d'.' -f1)
            echo "  ✅ $file ($size, geändert: $modified)"
        else
            echo "  ❌ $file - FEHLT!"
        fi
    done
else
    echo "❌ Portal-Verzeichnis nicht gefunden: $PORTAL_DIR"
    exit 1
fi

################################################################################
# 2. GIT-STATUS
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🔀 GIT-STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

if [ -d ".git" ]; then
    echo "✅ Git-Repository vorhanden"
    echo ""
    
    echo "Current Branch:"
    git branch --show-current
    
    echo ""
    echo "Alle Branches (lokal):"
    git branch -v
    
    echo ""
    echo "Remote Branches:"
    git branch -r | head -10
    
    echo ""
    echo "Git-Status:"
    git status --short --branch
    
    echo ""
    echo "Letzte 5 Commits:"
    git log --oneline --decorate -5
    
    echo ""
    echo "Remote-URL:"
    git remote -v
    
    echo ""
    echo "Uncommitted Changes:"
    uncommitted=$(git status --porcelain | wc -l)
    if [ $uncommitted -eq 0 ]; then
        echo "  ✅ Keine uncommitted changes"
    else
        echo "  ⚠️  $uncommitted uncommitted changes!"
        git status --short | head -20
    fi
    
    echo ""
    echo "Unpushed Commits:"
    unpushed=$(git log origin/$(git branch --show-current)..HEAD 2>/dev/null | wc -l)
    if [ $unpushed -eq 0 ]; then
        echo "  ✅ Keine unpushed commits"
    else
        echo "  ⚠️  $unpushed unpushed commits!"
        git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "  (Branch nicht auf Remote)"
    fi
else
    echo "❌ KEIN GIT-REPOSITORY! Git muss initialisiert werden!"
fi

################################################################################
# 3. DATENBANK-STATUS
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🗄️  DATENBANK-STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

if [ -f "$DB_PATH" ]; then
    db_size=$(ls -lh "$DB_PATH" | awk '{print $5}')
    db_modified=$(stat -c '%y' "$DB_PATH" | cut -d'.' -f1)
    echo "✅ Datenbank vorhanden: $DB_PATH"
    echo "   Größe: $db_size"
    echo "   Geändert: $db_modified"
    echo ""
    
    echo "Konten-Übersicht:"
    sqlite3 "$DB_PATH" <<SQL
.mode column
.headers on
SELECT 
    k.id,
    k.kontoname,
    COALESCE(b.bank_name, 'keine') as bank,
    COALESCE(
        (SELECT t.saldo_nach_buchung 
         FROM transaktionen t 
         WHERE t.konto_id = k.id 
         ORDER BY t.buchungsdatum DESC, t.id DESC 
         LIMIT 1), 
        0
    ) as saldo,
    (SELECT COUNT(*) FROM transaktionen WHERE konto_id = k.id) as trans,
    (SELECT MAX(buchungsdatum) FROM transaktionen WHERE konto_id = k.id) as letzte
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
WHERE k.aktiv = 1
ORDER BY k.id;
SQL
    
    echo ""
    echo "Gesamt-Statistik:"
    sqlite3 "$DB_PATH" <<SQL
.mode line
SELECT 
    (SELECT COUNT(*) FROM konten WHERE aktiv = 1) as konten_gesamt,
    (SELECT COUNT(*) FROM transaktionen) as transaktionen_gesamt,
    ROUND((
        SELECT SUM(saldo)
        FROM (
            SELECT COALESCE(
                (SELECT t.saldo_nach_buchung 
                 FROM transaktionen t 
                 WHERE t.konto_id = k.id 
                 ORDER BY t.buchungsdatum DESC, t.id DESC 
                 LIMIT 1), 
                0
            ) as saldo
            FROM konten k
            WHERE k.aktiv = 1
        )
    ), 2) as gesamt_saldo;
SQL
    
    echo ""
    echo "November 2025 Import-Status:"
    sqlite3 "$DB_PATH" <<SQL
.mode column
.headers on
SELECT 
    k.id,
    k.kontoname,
    COUNT(t.id) as trans_nov,
    MIN(t.buchungsdatum) as von,
    MAX(t.buchungsdatum) as bis
FROM konten k
LEFT JOIN transaktionen t ON k.id = t.konto_id AND t.buchungsdatum >= '2025-11-01'
WHERE k.aktiv = 1
GROUP BY k.id, k.kontoname
ORDER BY k.id;
SQL
    
    echo ""
    echo "Letzte 10 Transaktionen (gesamt):"
    sqlite3 "$DB_PATH" <<SQL
.mode column
.headers on
SELECT 
    t.id,
    t.buchungsdatum,
    k.kontoname,
    ROUND(t.betrag, 2) as betrag,
    ROUND(t.saldo_nach_buchung, 2) as saldo,
    SUBSTR(t.verwendungszweck, 1, 40) as zweck
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
ORDER BY t.buchungsdatum DESC, t.id DESC
LIMIT 10;
SQL
    
else
    echo "❌ DATENBANK FEHLT: $DB_PATH"
fi

################################################################################
# 4. PYTHON-ENVIRONMENT
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🐍 PYTHON-ENVIRONMENT"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "System Python:"
python3 --version
echo ""

if [ -d "$VENV_PATH" ]; then
    echo "✅ Virtual Environment vorhanden: $VENV_PATH"
    echo ""
    
    echo "VEnv Python:"
    "$VENV_PATH/bin/python" --version
    echo ""
    
    echo "Installierte Packages (wichtigste):"
    "$VENV_PATH/bin/pip" list 2>/dev/null | grep -E "(Flask|SQLAlchemy|gunicorn|ldap|requests|pandas)" || echo "  (Liste nicht verfügbar)"
    
else
    echo "❌ Virtual Environment fehlt: $VENV_PATH"
fi

echo ""
if [ -f "requirements.txt" ]; then
    echo "requirements.txt vorhanden ($(wc -l < requirements.txt) Zeilen)"
else
    echo "❌ requirements.txt fehlt!"
fi

################################################################################
# 5. SERVICE-STATUS
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "⚙️  SERVICE-STATUS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Greiner Portal Service
if systemctl is-active --quiet greiner-portal 2>/dev/null; then
    echo "✅ greiner-portal.service: LÄUFT"
    systemctl status greiner-portal --no-pager -l | head -15
else
    echo "❌ greiner-portal.service: NICHT AKTIV"
    echo ""
    echo "Status-Check:"
    systemctl status greiner-portal --no-pager -l 2>&1 | head -15 || echo "(Service nicht gefunden)"
fi

echo ""
echo "Listening Ports:"
netstat -tlnp 2>/dev/null | grep -E ":(5000|8000|3000)" || ss -tlnp 2>/dev/null | grep -E ":(5000|8000|3000)" || echo "(netstat/ss nicht verfügbar)"

################################################################################
# 6. LETZTE ÄNDERUNGEN
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "📝 LETZTE ÄNDERUNGEN (7 Tage)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

echo "Geänderte Python-Files:"
find . -name "*.py" -type f -mtime -7 2>/dev/null | head -10 || echo "(keine gefunden)"

echo ""
echo "Geänderte Templates:"
find templates/ -name "*.html" -type f -mtime -7 2>/dev/null | head -10 || echo "(keine gefunden)"

echo ""
echo "Neue/geänderte Logs:"
find logs/ -type f -mtime -7 2>/dev/null | head -10 || echo "(keine gefunden oder logs/ fehlt)"

################################################################################
# 7. DISK SPACE
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "💾 DISK SPACE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

df -h "$PORTAL_DIR" 2>/dev/null || df -h .

echo ""
echo "Größte Verzeichnisse in Portal:"
du -sh "$PORTAL_DIR"/* 2>/dev/null | sort -rh | head -10 || echo "(nicht verfügbar)"

################################################################################
# 8. KRITISCHE PRÜFUNGEN
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🚨 KRITISCHE PRÜFUNGEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

critical_issues=0

# Git-Check
if [ ! -d ".git" ]; then
    echo "❌ KRITISCH: Git nicht initialisiert!"
    critical_issues=$((critical_issues + 1))
fi

# DB-Check
if [ ! -f "$DB_PATH" ]; then
    echo "❌ KRITISCH: Datenbank fehlt!"
    critical_issues=$((critical_issues + 1))
fi

# VEnv-Check
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ KRITISCH: Virtual Environment fehlt!"
    critical_issues=$((critical_issues + 1))
fi

# Credentials-Check
if [ ! -f "config/credentials.json" ]; then
    echo "❌ KRITISCH: Credentials fehlen!"
    critical_issues=$((critical_issues + 1))
fi

# App-Check
if [ ! -f "app.py" ]; then
    echo "❌ KRITISCH: app.py fehlt!"
    critical_issues=$((critical_issues + 1))
fi

if [ $critical_issues -eq 0 ]; then
    echo "✅ Keine kritischen Issues gefunden!"
else
    echo ""
    echo "⚠️  WARNUNG: $critical_issues kritische Issues gefunden!"
fi

################################################################################
# ZUSAMMENFASSUNG
################################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "📊 ZUSAMMENFASSUNG"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

if [ -d ".git" ]; then
    branch=$(git branch --show-current)
    uncommitted=$(git status --porcelain | wc -l)
    echo "Git Branch:     $branch"
    echo "Uncommitted:    $uncommitted"
fi

if [ -f "$DB_PATH" ]; then
    konten=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM konten WHERE aktiv = 1")
    trans=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM transaktionen")
    echo "Konten (aktiv): $konten"
    echo "Transaktionen:  $trans"
fi

if systemctl is-active --quiet greiner-portal 2>/dev/null; then
    echo "Service:        ✅ LÄUFT"
else
    echo "Service:        ❌ NICHT AKTIV"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "✅ STATUS-CHECK ABGESCHLOSSEN"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
