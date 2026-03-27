# ⚡ CLAUDE - LIES MICH ZUERST! ⚡

## 🚨 KRITISCHE INFO - IMMER ZUERST LESEN!

**Du bist im CONTAINER! Kein Server-Zugriff!**

---

## 📋 3-SCHRITTE-START (JEDE SESSION!)

### **1️⃣ PROJECT_STATUS.md lesen**
```
view /mnt/project/PROJECT_STATUS.md
```
→ Gibt dir: Alle Konten, Salden, November-Status, offene Aufgaben

### **2️⃣ Neuestes SESSION_WRAP_UP lesen**
```
view /mnt/project/SESSION_WRAP_UP_TAG32.md  # (höchste Nummer!)
```
→ Gibt dir: Was in letzter Session passiert ist

### **3️⃣ User fragen**
```
"Was ist dein Ziel heute? Gibt es neue Daten/Änderungen am Server?"
```

**DANN ERST ENTWICKELN!** ✅

---

## 🎯 QUICK FACTS

### **Projekt-Struktur:**
```
Server: /opt/greiner-portal/
User:   ag-admin
DB:     /opt/greiner-portal/data/greiner_controlling.db
Venv:   /opt/greiner-portal/venv
Git:    github.com/floriangreiner06-crypto/greiner-portal.git
```

### **Git-Workflow:**
```
main            ← Produktiv
├── develop     ← Integration
    ├── feature/controlling-dashboard
    └── feature/verkauf-dashboard
```

### **Was User macht (du NICHT!):**
- ✅ SQL-Queries ausführen
- ✅ Python-Scripts ausführen
- ✅ Git-Befehle ausführen
- ✅ Files auf Server kopieren
- ✅ PDFs hochladen

### **Was du machst:**
- ✅ Code schreiben
- ✅ Analyse/Planung
- ✅ Empfehlungen geben
- ✅ User-Scripts erstellen

---

## 🛠️ TYPISCHE TASKS

### **Import neue PDFs:**
1. User gibt dir Info: "Neue PDFs für Konto X"
2. Du: Script erstellen in `/home/claude/`
3. User: Script auf Server kopieren & ausführen
4. Validierung zusammen

### **Dashboard-Check:**
1. Du fragst: "Kannst du diese SQL-Query ausführen?"
2. User führt aus, gibt Ausgabe
3. Du analysierst & gibst Handlungsempfehlung

### **Feature entwickeln:**
1. Code in `/home/claude/` erstellen
2. User testet auf Server
3. Iterativ verbessern
4. User committed in Git

---

## 📊 DATENBANK-SCHEMA (Wichtigste Tabellen)

```sql
-- Konten
konten (id, kontoname, iban, bank)

-- Transaktionen
transaktionen (
    id, konto_id, buchungsdatum, valutadatum,
    verwendungszweck, betrag, saldo_nach_buchung
)

-- Verkauf
verkauf_auftragseingang (fahrzeug_nr, datum, ...)
verkauf_auslieferungen (fahrzeug_nr, datum, ...)
verkauf_deckungsbeitraege (fahrzeug_nr, db_betrag, ...)
```

---

## 🚫 HÄUFIGE FEHLER VERMEIDEN

❌ **NIEMALS:** `ssh ag-admin@auto-greiner.de`  
✅ **STATTDESSEN:** User macht alles am Server

❌ **NIEMALS:** Direkter DB-Zugriff versuchen  
✅ **STATTDESSEN:** User führt SQL aus

❌ **NIEMALS:** In `main` direkt committen  
✅ **STATTDESSEN:** Immer Feature-Branch!

❌ **NIEMALS:** Ohne PROJECT_STATUS.md arbeiten  
✅ **STATTDESSEN:** IMMER zuerst lesen!

---

## ✅ SESSION-END CHECKLIST

Am Ende JEDER Session User sagen:

```bash
# 1. Status aktualisieren
python3 update_project_status.py

# 2. Committen
git add .
git commit -m "TAG33: Beschreibung"

# 3. Mergen (wenn Feature fertig)
git checkout develop
git merge feature/xyz
git push

# 4. Session Wrap-Up erstellen
nano SESSION_WRAP_UP_TAG33.md

# 5. PROJECT_STATUS.md neu hochladen ins Claude Project!
```

---

## 🎯 ERFOLGSMESSUNG

**Guter Start:** 
✅ PROJECT_STATUS.md gelesen  
✅ Letztes WRAP_UP gelesen  
✅ User nach aktuellem Stand gefragt  
✅ Klares Ziel für Session  

**Gutes Ende:**
✅ Code funktioniert  
✅ Committed  
✅ WRAP_UP erstellt  
✅ PROJECT_STATUS aktualisiert  

---

## 📞 NOTFALL-KOMMANDOS FÜR USER

```bash
# Status zeigen
cat PROJECT_STATUS.md

# DB-Konten anzeigen
cd /opt/greiner-portal
source venv/bin/activate
sqlite3 data/greiner_controlling.db "SELECT id, kontoname FROM konten ORDER BY id"

# Letzte Transaktionen
sqlite3 data/greiner_controlling.db "SELECT * FROM transaktionen ORDER BY buchungsdatum DESC LIMIT 5"

# Git-Status
git status
git branch
```

---

## 🎉 DAS WAR'S!

**Wenn du das gelesen hast, bist du startklar!** 

→ Jetzt: PROJECT_STATUS.md lesen!  
→ Dann: SESSION_WRAP_UP lesen!  
→ Dann: User fragen!  
→ Dann: Loslegen! 💪
