#!/bin/bash
# ============================================================================
# GIT COMMIT - TAG 9 BANKENSPIEGEL
# ============================================================================
# Führe dieses Script aus um alle Änderungen zu committen
# ============================================================================

cd /opt/greiner-portal

echo "🔍 Git Status prüfen..."
git status

echo ""
echo "📦 Füge neue Dateien hinzu..."

# Migrations
git add migrations/phase1/001_add_kontostand_historie.sql
git add migrations/phase1/002_add_kreditlinien.sql
git add migrations/phase1/003_add_kategorien.sql
git add migrations/phase1/004_add_pdf_imports.sql
git add migrations/phase1/005_add_views.sql
git add migrations/phase1/run_phase1_migrations.sh
git add migrations/phase1/README_PHASE1_MIGRATION.md

# API
git add api/bankenspiegel_api.py
git add api/__init__.py

# App
git add app.py

echo "✅ Dateien hinzugefügt"
echo ""
echo "📝 Erstelle Commit..."

git commit -m "feat: Bankenspiegel Phase 1 - REST API + Schema-Migration

- Migrationen: 4 Tabellen + 4 Views
  * kontostand_historie (6 Einträge)
  * kreditlinien (bereit für Daten)
  * kategorien (16 Standard-Kategorien)
  * pdf_imports (1.470 Einträge automatisch erfasst)
  * Views: v_aktuelle_kontostaende, v_monatliche_umsaetze, etc.

- REST API: 4 Endpoints komplett funktional
  * GET /api/bankenspiegel/health
  * GET /api/bankenspiegel/dashboard (KPIs)
  * GET /api/bankenspiegel/konten (mit Filter)
  * GET /api/bankenspiegel/transaktionen (10 Filter-Parameter)

- Features:
  * Pagination & Statistiken
  * Volltext-Suche
  * Datum-Range-Filter
  * Betrags-Filter
  * Alle Tests bestanden

Phase 1 MVP komplett - bereit für Frontend"

echo ""
echo "✅ Commit erstellt!"
echo ""
echo "🚀 Git Log (letzte 3 Commits):"
git log --oneline -3

echo ""
echo "📊 Geänderte Dateien:"
git diff --stat HEAD~1

echo ""
echo "🎉 FERTIG! Bereit für Push:"
echo ""
echo "git push"
echo ""
