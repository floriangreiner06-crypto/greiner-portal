# 🚀 START NEUE CLAUDE SESSION - GREINER PORTAL

## ⚠️ WICHTIG FÜR CLAUDE

**DU BIST IM CONTAINER! KEIN ZUGRIFF AUF SERVER!**

- ❌ Kein SSH zu `auto-greiner.de` / `10.80.80.20`
- ❌ Kein direkter DB-Zugriff
- ❌ Kein Filesystem-Zugriff auf Server
- ✅ Nur Project Knowledge Files verfügbar

**DAHER:**
1. ✅ **ZUERST** `PROJECT_STATUS.md` lesen!
2. ✅ **DANN** neuestes `SESSION_WRAP_UP_TAG*.md` lesen
3. ✅ **DANN** mit Entwicklung starten

---

## 📋 SCHRITT-FÜR-SCHRITT: NEUE SESSION STARTEN

### **SCHRITT 1: Projekt-Status laden**

```bash
# Diese Files ZUERST lesen:
view /mnt/project/PROJECT_STATUS.md
view /mnt/project/SESSION_WRAP_UP_TAG32.md  # (neueste Nummer!)
```

### **SCHRITT 2: User nach aktuellem Stand fragen**

**Frage den User:**
- "Welches Feature/Problem sollen wir heute angehen?"
- "Gibt es neue PDFs oder Daten die importiert werden sollen?"
- "Wurde seit letzter Session etwas am Server geändert?"

### **SCHRITT 3: Branch erstellen (User macht das!)**

**Sage dem User:**
```bash
# Auf Server:
cd /opt/greiner-portal
git checkout develop
git pull
git checkout -b feature/beschreibung-tag33
```

### **SCHRITT 4: Entwickeln**

- Code erstellen in `/home/claude/`
- User kopiert Files zum Server
- Iterativ testen & verbessern

### **SCHRITT 5: Session beenden**

**Sage dem User:**

```bash
# Status aktualisieren
python3 update_project_status.py

# Committen
git add .
git commit -m "TAG33: Kurze Beschreibung"

# In develop mergen (wenn fertig!)
git checkout develop
git merge feature/beschreibung-tag33
git push

# Session Wrap-Up erstellen
nano SESSION_WRAP_UP_TAG33.md
```

**Dann:** User lädt `PROJECT_STATUS.md` + `SESSION_WRAP_UP_TAG33.md` ins Project hoch!

---

## 🎯 WORKFLOW-DIAGRAMM

```
┌─────────────────────────────────────────────────────────┐
│ NEUE SESSION STARTET                                     │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Claude liest PROJECT_STATUS.md aus Project Knowledge │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Claude liest SESSION_WRAP_UP_TAG*.md (neueste)      │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Claude fragt User nach aktuellem Stand              │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 4. User erstellt Feature-Branch am Server              │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 5. ENTWICKLUNG (Claude + User iterativ)                │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 6. User committed + merged + pushed                     │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 7. User lädt PROJECT_STATUS.md + WRAP_UP hoch          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 FILE-STRUKTUR (wichtigste Files)

```
/mnt/project/                    ← Project Knowledge (read-only!)
├── PROJECT_STATUS.md            ← **WICHTIGSTER FILE!** Immer zuerst lesen!
├── SESSION_WRAP_UP_TAG32.md     ← Neueste Session
├── SESSION_WRAP_UP_TAG31.md
├── GIT_WORKFLOW.md              ← Git-Strategie
├── README_SESSION_START.md      ← Diese Datei!
└── ...

/opt/greiner-portal/             ← Server (User hat Zugriff, Claude NICHT!)
├── PROJECT_STATUS.md            ← Auto-generiert bei Commit
├── SESSION_WRAP_UP_TAG*.md
├── data/
│   ├── greiner_controlling.db
│   └── kontoauszuege/
├── docs/
│   └── status/
│       └── current_status.json
└── ...
```

---

## 🛠️ TYPISCHE ENTWICKLUNGS-TASKS

### **Import neue PDFs:**
1. User legt PDFs nach `/opt/greiner-portal/data/kontoauszuege/`
2. Claude erstellt Import-Script
3. User führt auf Server aus
4. Validierung der Salden
5. Commit

### **Parser-Fix:**
1. Claude erstellt/ändert Parser-Code
2. User testet auf Server
3. Iterative Verbesserung
4. Commit

### **Dashboard-Check:**
1. User führt SQL-Query aus
2. Claude analysiert Daten
3. Claude gibt Handlungsempfehlungen
4. User führt Fixes aus

### **Neue Feature:**
1. Claude designed Lösung
2. Claude schreibt Code
3. User testet
4. Iterative Verbesserung
5. Commit

---

## ⚡ QUICK-REFERENCE: WICHTIGSTE BEFEHLE

### **User am Server:**
```bash
# Status anzeigen
cat PROJECT_STATUS.md

# Status aktualisieren
python3 update_project_status.py

# Branch erstellen
git checkout -b feature/xyz-tag33

# Committen (Status wird automatisch aktualisiert!)
git add .
git commit -m "TAG33: Beschreibung"

# SQL-Query für Dashboard-Check
cd /opt/greiner-portal
sqlite3 data/greiner_controlling.db "SELECT * FROM konten"

# Python im venv
source venv/bin/activate
python3 mein_script.py
```

### **Claude:**
```bash
# Files erstellen
create_file description path content

# Files ansehen
view /mnt/project/FILE.md

# Project Knowledge durchsuchen
project_knowledge_search query="suchbegriff"
```

---

## 🚨 HÄUFIGE FEHLER VERMEIDEN

### ❌ **Fehler 1: Claude versucht SSH**
**Symptom:** `ssh ag-admin@auto-greiner.de`  
**Warum falsch:** Claude ist im Container, kein Zugriff!  
**Richtig:** User macht alles am Server, Claude nur Code/Analyse

### ❌ **Fehler 2: Direkt in `main` oder `develop` committen**
**Symptom:** `git checkout main && git commit`  
**Warum falsch:** Zerschießt stabile Versionen!  
**Richtig:** Immer Feature-Branch erstellen!

### ❌ **Fehler 3: Veraltete Files im Project Knowledge**
**Symptom:** Claude arbeitet mit alten Salden  
**Warum falsch:** Project Knowledge nicht aktualisiert  
**Richtig:** Nach jeder Session `PROJECT_STATUS.md` neu hochladen!

### ❌ **Fehler 4: Parallel-Entwicklung ohne Branches**
**Symptom:** Feature A überschreibt Feature B  
**Warum falsch:** Keine Branch-Isolation  
**Richtig:** Ein Branch pro Feature!

---

## ✅ SUCCESS-CHECKLIST

### **Session-Start:**
- [ ] `PROJECT_STATUS.md` gelesen?
- [ ] Neueste `SESSION_WRAP_UP` gelesen?
- [ ] User nach aktuellem Stand gefragt?
- [ ] Feature-Branch erstellt?

### **Session-Ende:**
- [ ] Code funktioniert am Server?
- [ ] `update_project_status.py` ausgeführt?
- [ ] Committed mit gutem Message?
- [ ] Feature-Branch in `develop` gemerged?
- [ ] `SESSION_WRAP_UP_TAG*.md` erstellt?
- [ ] `PROJECT_STATUS.md` + `SESSION_WRAP_UP` hochgeladen?

---

## 🎯 ZIEL

**Robuste, parallele Entwicklung ohne Datenverlust oder Konflikte!**

✅ Claude hat IMMER aktuellen Stand  
✅ Parallel-Features möglich  
✅ Rollback möglich  
✅ Keine doppelte Arbeit  
✅ Professionelles Projekt-Management  

---

**Los geht's! 🚀**
