#!/bin/bash
# GIT CLEANUP & UMSTRUKTURIERUNG - Greiner Portal
# Räumt das Branch-Chaos auf und erstellt saubere Struktur

set -e

echo "========================================="
echo "🧹 GIT CLEANUP & UMSTRUKTURIERUNG"
echo "========================================="
echo ""

cd /opt/greiner-portal

# Sicherheitscheck
echo "⚠️  WICHTIG: Dieser Script macht folgendes:"
echo ""
echo "1. Merged feature/bankenspiegel-komplett → main"
echo "2. Erstellt develop Branch"
echo "3. Archiviert alte Feature-Branches"
echo "4. Committed uncommitted Changes"
echo ""
read -p "Fortfahren? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Abgebrochen."
    exit 0
fi

echo ""
echo "🔄 Starte Cleanup..."
echo ""

# ========================================
# 1. BACKUP ERSTELLEN
# ========================================
echo "📋 1. Backup erstellen..."

BACKUP_TAG="backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"
git tag "$BACKUP_TAG"

echo "✅ Backup-Tag erstellt: $BACKUP_TAG"
echo "   (Falls etwas schiefgeht: git reset --hard $BACKUP_TAG)"
echo ""

# ========================================
# 2. UNCOMMITTED CHANGES COMMITTEN
# ========================================
echo "📋 2. Uncommitted Changes committen..."

git checkout feature/bankenspiegel-komplett

if [ -n "$(git status --porcelain)" ]; then
    echo "Uncommitted files gefunden:"
    git status --short
    echo ""
    
    git add .
    git commit -m "chore: Cleanup - uncommitted changes vor Umstrukturierung"
    
    echo "✅ Changes committed"
else
    echo "✅ Keine uncommitted changes"
fi

echo ""

# ========================================
# 3. MAIN AKTUALISIEREN
# ========================================
echo "📋 3. Main aktualisieren..."

git checkout main
git pull origin main || echo "⚠️  Kein Pull möglich, fahre fort"

echo ""

# ========================================
# 4. FEATURE/BANKENSPIEGEL-KOMPLETT → MAIN
# ========================================
echo "📋 4. feature/bankenspiegel-komplett in main mergen..."

echo "   Dieser Branch enthält:"
echo "   - Verkauf-Features (Deckungsbeitrag, Auftragseingang)"
echo "   - Controlling-Features (Bankenspiegel, Parser)"
echo "   - Auth-System"
echo "   - System-Konfigurationen"
echo ""

git merge feature/bankenspiegel-komplett -m "feat: Merge complete feature set - Verkauf + Controlling + Auth

Merged from feature/bankenspiegel-komplett:
- Verkauf: Deckungsbeitrag-System, Auftragseingang, Auslieferungen
- Controlling: Bankenspiegel-API, Parser-Fixes, November-Import
- Auth: LDAP-Integration, Auth-Manager
- System: Port-Konfiguration, Navigation

Refs: TAG31, TAG32"

echo "✅ Merge nach main abgeschlossen"
echo ""

# ========================================
# 5. DEVELOP BRANCH ERSTELLEN
# ========================================
echo "📋 5. Develop Branch erstellen..."

if git show-ref --verify --quiet refs/heads/develop; then
    echo "⚠️  Develop existiert bereits, überspringe"
else
    git checkout -b develop main
    echo "✅ Develop Branch erstellt (identisch mit main)"
fi

echo ""

# ========================================
# 6. ALTE FEATURE-BRANCHES ARCHIVIEREN
# ========================================
echo "📋 6. Alte Feature-Branches archivieren..."

# Als Tags archivieren
git tag "archive/bankenspiegel-komplett" feature/bankenspiegel-komplett
git tag "archive/bankenspiegel-pdf-import" feature/bankenspiegel-pdf-import
git tag "archive/urlaubsplaner-v2-hybrid" feature/urlaubsplaner-v2-hybrid

echo "✅ Branches als Tags archiviert"
echo ""

# Optional: Branches löschen
echo "Möchtest du die alten Feature-Branches löschen?"
echo "(Sie sind als Tags archiviert: archive/...)"
read -p "Löschen? (yes/no): " delete_branches

if [ "$delete_branches" = "yes" ]; then
    git branch -D feature/bankenspiegel-pdf-import || true
    git branch -D feature/urlaubsplaner-v2-hybrid || true
    # feature/bankenspiegel-komplett behalten wir vorerst
    echo "✅ Alte Branches gelöscht (außer bankenspiegel-komplett)"
else
    echo "⚠️  Branches behalten"
fi

echo ""

# ========================================
# 7. NEUE FEATURE-BRANCHES ERSTELLEN
# ========================================
echo "📋 7. Neue, saubere Feature-Branches erstellen..."

git checkout develop

# Controlling-Branch
git checkout -b feature/controlling-dashboard develop
git checkout develop

# Verkauf-Branch  
git checkout -b feature/verkauf-dashboard develop
git checkout develop

echo "✅ Neue Feature-Branches erstellt:"
echo "   - feature/controlling-dashboard"
echo "   - feature/verkauf-dashboard"
echo ""

# ========================================
# 8. PROJECT_STATUS GENERIEREN
# ========================================
echo "📋 8. Project Status generieren..."

git checkout develop

if [ -f "update_project_status.py" ]; then
    python3 update_project_status.py
    
    git add PROJECT_STATUS.md docs/status/
    git commit -m "docs: Initial PROJECT_STATUS nach Cleanup" || echo "Nichts zu committen"
    
    echo "✅ PROJECT_STATUS generiert"
else
    echo "⚠️  update_project_status.py nicht gefunden, überspringe"
fi

echo ""

# ========================================
# 9. PUSHEN (optional)
# ========================================
echo "📋 9. Änderungen pushen..."

echo "Möchtest du alles zu GitHub pushen?"
read -p "Pushen? (yes/no): " do_push

if [ "$do_push" = "yes" ]; then
    git push origin main
    git push origin develop
    git push origin feature/controlling-dashboard
    git push origin feature/verkauf-dashboard
    git push --tags
    
    echo "✅ Alles gepusht!"
else
    echo "⚠️  Nicht gepusht - du kannst später manuell pushen"
fi

echo ""

# ========================================
# FERTIG!
# ========================================
echo "========================================="
echo "✅ CLEANUP ABGESCHLOSSEN!"
echo "========================================="
echo ""
echo "📊 NEUE STRUKTUR:"
echo ""
echo "main                              ← Produktiv (enthält jetzt alles)"
echo "├── develop                       ← Integration-Layer"
echo "│   ├── feature/controlling-dashboard"
echo "│   └── feature/verkauf-dashboard"
echo ""
echo "Archiviert als Tags:"
echo "├── archive/bankenspiegel-komplett"
echo "├── archive/bankenspiegel-pdf-import"
echo "└── archive/urlaubsplaner-v2-hybrid"
echo ""
echo "📋 NÄCHSTE SCHRITTE:"
echo ""
echo "1. Checkout in gewünschten Branch:"
echo "   git checkout feature/controlling-dashboard  # Für Controlling-Arbeit"
echo "   git checkout feature/verkauf-dashboard      # Für Verkauf-Arbeit"
echo ""
echo "2. Arbeiten & Committen wie gewohnt"
echo ""
echo "3. Wenn Feature fertig:"
echo "   git checkout develop"
echo "   git merge feature/xyz"
echo "   git push"
echo ""
echo "4. PROJECT_STATUS.md ins Claude Project hochladen!"
echo ""
echo "🎉 Bereit für saubere Entwicklung!"
