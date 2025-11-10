# 🚀 NEUE CHAT-SESSION ANLEITUNG

**KRITISCH: Git Workflow für neue Sessions**

## ⚠️ ERSTE SCHRITTE (IMMER!)
```bash
# 1. SSH + Projekt
ssh ag-admin@10.80.80.20
cd /opt/greiner-portal
source venv/bin/activate

# 2. GIT STATUS (KRITISCH!)
git fetch origin
git pull origin feature/bankenspiegel-komplett
git log --oneline -5

# 3. Letzte Session lesen
cat docs/sessions/SESSION_WRAP_UP_TAG23.md
```

## 🚨 DOPPELENTWICKLUNG VERMEIDEN

**VOR jeder Arbeit:**
- `git fetch origin` - Hole Remote-Änderungen
- `git pull origin feature/bankenspiegel-komplett` - Update local
- `git log -5` - Zeige letzte Commits

**NACH jeder Session:**
- Commit + Push ALLES
- Session Wrap-Up erstellen
- Alles gepusht? Verify!

## 📁 PROJEKT-STATUS (TAG 23 Ende)

- Branch: `feature/bankenspiegel-komplett`
- Letzter Commit: `271b2c3` (Login-Fix)
- Tag: `v2.3.1-cache-fixes`
- Module: Auth ✅, Dashboard ✅, Bankenspiegel ✅, Verkauf ✅

## 🔧 WICHTIGE BEFEHLE
```bash
# Code ändern
vim app.py
git add app.py
git commit -m "fix: Beschreibung"

# Produktion neu starten
sudo systemctl restart greiner-portal

# Push
git push origin feature/bankenspiegel-komplett
```

## 🎯 GOLDEN RULES

1. ✅ **IMMER git fetch/pull ZUERST**
2. ✅ Kleine, häufige Commits
3. ✅ Nach Meilensteinen pushen
4. ✅ Gunicorn restart nach Code-Änderungen
5. ✅ Session Wrap-Up am Ende

**Version:** 1.0 | **Erstellt:** TAG 23
