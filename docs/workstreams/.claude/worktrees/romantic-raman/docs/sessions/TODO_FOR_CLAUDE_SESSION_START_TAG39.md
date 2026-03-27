# 📋 TODO FÜR CLAUDE - SESSION START TAG 39

**Letzte Session:** TAG 38 (2025-11-13)  
**Status:** ⚠️ VRBankLandauParser OK, aber parser_factory.py kaputt

---

## 🚨 **KRITISCHES PROBLEM:**
```
parser_factory.py hat IndentationError!
Import schlägt fehl!
```

---

## 🎯 **ERSTE AKTION:**

### **1. Status prüfen:**
```bash
python3 -c "from parsers.parser_factory import ParserFactory" 2>&1
```

### **2. Wenn Fehler → REPARIEREN:**
```bash
# Backup zurück
cp /opt/greiner-portal/parsers/parser_factory.py.backup_20251113_165831 /opt/greiner-portal/parsers/parser_factory.py

# Patch-Script ausführen
/opt/greiner-portal/venv/bin/python3 /opt/greiner-portal/scripts/patch_parser_factory_final.py

# Nochmal testen
python3 -c "from parsers.parser_factory import ParserFactory; print('✅ OK')"
```

---

## ✅ **WAS SCHON FUNKTIONIERT:**

- VRBankLandauParser existiert und funktioniert perfekt
- Limits in DB sind korrekt
- 3700057908 Festgeld-Konto ist angelegt (ID 23)

---

## 📊 **IMPORT-BEDARF:**

1. **VR Bank Landau:** ~5 PDFs (06.11 - 12.11)
2. **3700057908 Festgeld:** PDFs vom 10.11

---

## 📁 **WICHTIGE FILES:**

Lies diese:
- `/opt/greiner-portal/SESSION_WRAP_UP_TAG38.md` ← Komplette Session
- `/opt/greiner-portal/parsers/vrbank_landau_parser.py` ← Neuer Parser

---

**Los geht's! Erst parser_factory reparieren! 🔧**
