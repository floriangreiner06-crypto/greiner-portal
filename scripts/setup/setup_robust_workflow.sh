#!/bin/bash
# SETUP: Robuster Git-Workflow für Greiner Portal
# Führe dieses Script EINMAL auf dem Server aus!

set -e  # Bei Fehler abbrechen

echo "========================================="
echo "🔧 GREINER PORTAL - ROBUSTER SETUP"
echo "========================================="
echo ""

# Prüfen ob im richtigen Verzeichnis
if [ ! -d "/opt/greiner-portal" ]; then
    echo "❌ Fehler: /opt/greiner-portal nicht gefunden!"
    exit 1
fi

cd /opt/greiner-portal

# ========================================
# 1. GIT-BRANCH-STRUKTUR
# ========================================
echo "📋 1. Git-Branch-Struktur einrichten..."

# Prüfen ob Git initialisiert
if [ ! -d ".git" ]; then
    echo "Git initialisieren..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Develop Branch erstellen falls nicht vorhanden
if ! git show-ref --verify --quiet refs/heads/develop; then
    echo "Develop-Branch erstellen..."
    git checkout -b develop
    git checkout main 2>/dev/null || git checkout master
else
    echo "✅ Develop-Branch existiert bereits"
fi

echo ""

# ========================================
# 2. STATUS-UPDATE-SCRIPT INSTALLIEREN
# ========================================
echo "📋 2. Status-Update-Script installieren..."

# Script kopieren (wird vom User bereitgestellt)
if [ -f "update_project_status.py" ]; then
    chmod +x update_project_status.py
    echo "✅ update_project_status.py ist bereit"
else
    echo "⚠️  update_project_status.py noch nicht vorhanden"
    echo "    Kopiere das Script manuell hierher!"
fi

echo ""

# ========================================
# 3. GIT PRE-COMMIT HOOK
# ========================================
echo "📋 3. Git Pre-Commit Hook einrichten..."

mkdir -p .git/hooks

cat > .git/hooks/pre-commit << 'HOOK_END'
#!/bin/bash
# Auto-Update Project Status bei jedem Commit

cd /opt/greiner-portal

# Status-Update ausführen
if [ -f "update_project_status.py" ]; then
    python3 update_project_status.py --silent
    
    # PROJECT_STATUS.md zum Commit hinzufügen
    git add PROJECT_STATUS.md 2>/dev/null || true
    git add docs/status/ 2>/dev/null || true
fi

exit 0
HOOK_END

chmod +x .git/hooks/pre-commit

echo "✅ Pre-Commit Hook installiert"
echo ""

# ========================================
# 4. VERZEICHNISSE ERSTELLEN
# ========================================
echo "📋 4. Verzeichnis-Struktur erstellen..."

mkdir -p docs/status
mkdir -p docs/sessions
mkdir -p data/backups

echo "✅ Verzeichnisse erstellt"
echo ""

# ========================================
# 5. .GITIGNORE ERGÄNZEN
# ========================================
echo "📋 5. .gitignore aktualisieren..."

cat >> .gitignore << 'GITIGNORE_END'

# Greiner Portal spezifisch
data/greiner_controlling.db
data/greiner_controlling.db-*
data/backups/*.db
data/kontoauszuege/*.pdf
*.pyc
__pycache__/
venv/
.env
*.log
GITIGNORE_END

echo "✅ .gitignore aktualisiert"
echo ""

# ========================================
# 6. INITIALES STATUS-UPDATE
# ========================================
echo "📋 6. Initiales Status-Update..."

if [ -f "update_project_status.py" ]; then
    python3 update_project_status.py
    echo "✅ Initialer Status erstellt"
else
    echo "⚠️  Status-Update übersprungen (Script fehlt noch)"
fi

echo ""

# ========================================
# 7. COMMIT DES SETUPS
# ========================================
echo "📋 7. Setup committen..."

git add .
git commit -m "Setup: Robuster Git-Workflow installiert" 2>/dev/null || echo "Nichts zu committen"

echo ""

# ========================================
# FERTIG!
# ========================================
echo "========================================="
echo "✅ SETUP ABGESCHLOSSEN!"
echo "========================================="
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo ""
echo "1. Files ins Git-Repo kopieren:"
echo "   - GIT_WORKFLOW.md"
echo "   - README_SESSION_START.md"
echo "   - update_project_status.py"
echo ""
echo "2. Committen:"
echo "   git add ."
echo "   git commit -m 'Doku: Robuster Workflow'"
echo ""
echo "3. Pushen (falls Remote vorhanden):"
echo "   git push origin main"
echo "   git push origin develop"
echo ""
echo "4. Ab jetzt immer Feature-Branches nutzen:"
echo "   git checkout develop"
echo "   git checkout -b feature/xyz-tag33"
echo ""
echo "5. PROJECT_STATUS.md in Claude Project hochladen!"
echo ""
echo "🎉 Bereit für robuste Entwicklung!"
