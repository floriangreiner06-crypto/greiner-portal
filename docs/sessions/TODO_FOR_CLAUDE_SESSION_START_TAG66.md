# 📋 TODO FÜR CLAUDE SESSION START - TAG 66

**Datum:** 2025-11-20 (erwartet)  
**Fokus:** 🚨 STELLANTIS-IMPORT FIX + FRONTEND

---

## 🚨 KRITISCH - ZUERST!

### ⚠️ STELLANTIS-SALDO IST FALSCH!

**Problem:**
- Stellantis zeigt: 7.132.166 € (255 Fahrzeuge)
- **Verdacht:** Mehrfachimport wegen mehrerer ZIP-Dateien

**Analyse:**
```bash
# Stellantis-Ordner prüfen:
ls -lh /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Stellantis/*.zip

# ZIP-Dateien gruppiert nach Datum:
ls -lt /mnt/buchhaltung/Buchhaltung/Kontoauszüge/Stellantis/ | grep zip
```

**Erwartetes Verhalten:**
- Pro RRDI (DE0154X, DE08250) nur NEUESTE ZIP importieren
- DELETE before INSERT (nicht addieren!)
- Datum aus Dateinamen: `WHSKRELI_DE0154X_202511190832.zip`

**Script-Check:**
```bash
# Aktuelles Import-Verhalten prüfen:
grep -A 20 "def.*import\|for.*zip\|DELETE" scripts/imports/import_stellantis.py
```

**Fix-Strategie:**
1. Script analysieren
2. Nur neueste ZIP je RRDI selektieren
3. DELETE vor INSERT
4. Neu importieren
5. Saldo verifizieren

---

## 📊 ERWARTETE ZAHLEN (ca.)

**Stellantis sollte sein:**
- ~110-120 Fahrzeuge (nicht 255!)
- ~3-4 Mio € (nicht 7,1 Mio!)

**Hyundai & Santander:**
- ✅ Korrekt (jeweils nur 1 Datei)

---

## 🔍 DIAGNOSE-BEFEHLE
```bash
# 1. Stellantis ZIP-Dateien:
find /mnt/buchhaltung -name "*stellantis*" -o -name "*WHSKRELI*" | head -20

# 2. DB-Check - Duplikate?
sqlite3 data/greiner_controlling.db << 'EOF'
SELECT 
    rrdi,
    COUNT(*) as Anzahl,
    COUNT(DISTINCT vin) as Unique_VINs,
    MAX(import_datum) as Letzter_Import
FROM fahrzeugfinanzierungen
WHERE finanzinstitut = 'Stellantis'
GROUP BY rrdi;
