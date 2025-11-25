# GIT-WORKFLOW FÜR GREINER PORTAL

## 🎯 ZIEL
Parallele Features entwickeln ohne sich gegenseitig zu zerschießen!

---

## 📋 BRANCH-STRATEGIE

```
main (PRODUKTIV)
  ├── develop (INTEGRATION)
  │    ├── feature/dashboard-check (TAG33)
  │    ├── feature/november-import (TAG34)
  │    ├── feature/parser-fixes (TAG35)
  │    └── hotfix/critical-bug
```

### **Branch-Typen:**

#### `main` - Produktiv
- ✅ NUR stabile, getestete Version
- ✅ Jeder Commit = Release
- ❌ NIEMALS direkt committen!

#### `develop` - Integration
- Sammelt fertige Features
- Wird regelmäßig in `main` gemerged
- Hier werden Features integriert

#### `feature/*` - Feature-Entwicklung
- Ein Branch pro Session/Feature
- Naming: `feature/beschreibung-tag33`
- Wird in `develop` gemerged wenn fertig

#### `hotfix/*` - Kritische Bugfixes
- Für dringende Fixes
- Wird direkt in `main` + `develop` gemerged

---

## 🚀 WORKFLOW PRO SESSION

### **TAG 33 BEISPIEL:**

```bash
# 1. BRANCH ERSTELLEN
cd /opt/greiner-portal
git checkout develop
git pull
git checkout -b feature/dashboard-check-tag33

# 2. ENTWICKELN
# ... Arbeit am Dashboard-Check ...

# 3. STATUS DOKUMENTIEREN (WICHTIG!)
python3 update_project_status.py

# 4. COMMITTEN
git add .
git commit -m "TAG33: Dashboard-Check - Salden validiert"

# 5. IN DEVELOP MERGEN (wenn fertig und getestet!)
git checkout develop
git merge feature/dashboard-check-tag33
git push

# 6. BRANCH LÖSCHEN (optional)
git branch -d feature/dashboard-check-tag33
```

---

## 📊 PROJEKT-STATUS-FILE (AUTOMATISCH)

Jeder Commit aktualisiert automatisch: `PROJECT_STATUS.md`

### Setup:

```bash
# Git Hook installieren
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Automatisches Status-Update vor jedem Commit

cd /opt/greiner-portal
python3 update_project_status.py --silent

git add PROJECT_STATUS.md docs/status/
HOOK

chmod +x .git/hooks/pre-commit
```

---

## 🔄 PARALLEL-ENTWICKLUNG BEISPIEL

**Szenario:** Du arbeitest an 2 Features gleichzeitig

```bash
# SESSION A: Dashboard-Check
git checkout -b feature/dashboard-check-tag33
# ... Arbeit ...
git commit -m "Dashboard-Check WIP"

# SESSION B: November-Import
git checkout develop
git checkout -b feature/november-import-tag34
# ... Arbeit ...
git commit -m "November Import WIP"

# Zurück zu SESSION A
git checkout feature/dashboard-check-tag33
# Weiter arbeiten...

# Fertig? Beide mergen:
git checkout develop
git merge feature/dashboard-check-tag33
git merge feature/november-import-tag34
```

---

## 📁 STRUKTUR IM GIT

```
/opt/greiner-portal/
├── PROJECT_STATUS.md          ← Automatisch generiert! IMMER aktuell!
├── SESSION_WRAP_UP_TAG33.md   ← Manuell nach Session
├── docs/
│   ├── status/
│   │   ├── konten.json        ← Auto-generiert
│   │   ├── november.json      ← Auto-generiert
│   │   └── system.json        ← Auto-generiert
│   └── sessions/
│       └── SESSION_WRAP_UP_TAG*.md
├── .git/
│   └── hooks/
│       └── pre-commit         ← Status-Update Hook
└── ...
```

---

## ⚡ SCHNELLSTART FÜR NEUE SESSION

```bash
# 1. Status lesen (DAS ERSTE WAS CLAUDE BRAUCHT!)
cat PROJECT_STATUS.md

# 2. Branch erstellen
git checkout develop
git pull
git checkout -b feature/mein-feature-tag35

# 3. Arbeiten...

# 4. Committen (Status wird automatisch aktualisiert!)
git add .
git commit -m "TAG35: Beschreibung"

# 5. Pushen
git push -u origin feature/mein-feature-tag35
```

---

## 🛡️ SCHUTZ VOR KONFLIKTEN

### **Regel 1: Niemals direkt in `main` oder `develop`**
```bash
# Branches schützen (auf GitHub/GitLab)
main:    Require PR + Review
develop: Require PR (optional)
```

### **Regel 2: Immer vor Start pullen**
```bash
git checkout develop
git pull
git checkout -b feature/new-feature
```

### **Regel 3: Regelmäßig Status committen**
```bash
# Nach jeder wichtigen Änderung:
git add .
git commit -m "WIP: Zwischenstand"
```

### **Regel 4: Feature fertig = sofort mergen**
```bash
# Nicht wochenlang Branches offen lassen!
git checkout develop
git merge feature/xyz
git push
```

---

## 🎯 VORTEILE

✅ **Parallel-Entwicklung** ohne Konflikte
✅ **Automatischer Status** bei jedem Commit
✅ **Rollback** möglich (jederzeit zu älterem Stand)
✅ **Klare History** - wer hat was wann gemacht
✅ **CI/CD-ready** - später automatische Tests möglich

---

## 📋 CHECKLISTE PRO SESSION

- [ ] `PROJECT_STATUS.md` gelesen?
- [ ] Branch erstellt? `feature/xyz-tag33`
- [ ] Entwickelt & getestet?
- [ ] Committed mit gutem Message?
- [ ] In `develop` gemerged?
- [ ] `SESSION_WRAP_UP_TAG*.md` erstellt?
- [ ] Gepusht?

---

## 🚨 WICHTIG FÜR CLAUDE

**Bei JEDEM neuen Chat:**

1. ✅ `PROJECT_STATUS.md` aus Git lesen
2. ✅ Aktuellstes `SESSION_WRAP_UP_TAG*.md` lesen
3. ✅ Branch-Status prüfen: `git branch -a`
4. ✅ Dann erst entwickeln!

**So hast du IMMER den aktuellen Stand!** 🎯
