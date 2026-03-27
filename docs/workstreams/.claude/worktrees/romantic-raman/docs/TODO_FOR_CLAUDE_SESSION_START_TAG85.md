# 🚀 TODO FOR CLAUDE - SESSION START TAG 85

**Datum:** Nach 27.11.2025  
**Vorgänger:** TAG84 - BWA Dashboard + GlobalCube Mapping Analyse

---

## 📋 KONTEXT SCHNELL HERSTELLEN

```bash
cd /opt/greiner-portal
source venv/bin/activate

# Session Wrap-Up TAG84 lesen (WICHTIG!)
cat docs/SESSION_WRAP_UP_TAG84.md

# GlobalCube Mapping (bereits entpackt von TAG84)
ls -la /tmp/gcstruct_aktuell/
head -30 /tmp/kontenrahmen_utf8.csv

# Falls /tmp gelöscht wurde, neu entpacken:
# unzip -o "/mnt/globalcube/GCStruct/AutohausGreiner_20250825_102814.zip" -d /tmp/gcstruct_aktuell
# iconv -f ISO-8859-1 -t UTF-8 /tmp/gcstruct_aktuell/Kontenrahmen/Kontenrahmen.csv > /tmp/kontenrahmen_utf8.csv
```

---

## 🎯 HAUPTZIEL TAG 85

**BWA Direkte/Indirekte Kosten korrekt berechnen**

### Aktuelle Abweichung:

| Position | GlobalCube | DRIVE | Problem |
|----------|------------|-------|---------|
| Direkte Kosten | 154.432 € | ~96.000 € | -58.000 € |
| Indirekte Kosten | 205.358 € | ~270.000 € | +65.000 € |

### Lösung:

Die **LETZTE ZIFFER** der Kontonummer = Kostenstelle!

```
Konto 41500 → letzte Ziffer 0 → INDIREKT
Konto 41501 → letzte Ziffer 1 → DIREKT  
Konto 41502 → letzte Ziffer 2 → DIREKT
...
Konto 41509 → letzte Ziffer 9 → INDIREKT (Sonstige)
```

### SQL für Direkte Kosten (korrigiert):

```sql
-- DIREKTE KOSTEN = Personalkonten mit Kostenstelle 1-8
SELECT SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 
                ELSE -posted_value/100.0 END)
FROM loco_journal_accountings
WHERE accounting_date BETWEEN ? AND ?
  AND nominal_account_number BETWEEN 410000 AND 449999
  AND substr(nominal_account_number, 6, 1) IN ('1','2','3','4','5','6','7','8')
  AND nominal_account_number NOT BETWEEN 415100 AND 415199;  -- Provisionen = Variabel
```

### SQL für Indirekte Kosten:

```sql
-- INDIREKTE KOSTEN = Rest von 4xxxxx
-- = Kostenstelle 0 oder 9 bei Personalkonten
-- + Alle 4xxxxx die NICHT variabel und NICHT direkt sind
```

---

## 📂 RELEVANTE DATEIEN

```
routes/controlling_routes.py     ← BWA API anpassen (ab Zeile ~390)
/tmp/kontenrahmen_utf8.csv       ← GlobalCube Mapping Referenz
docs/SESSION_WRAP_UP_TAG84.md    ← Vollständige Analyse
```

---

## ✅ BEREITS ERLEDIGT (TAG84)

- [x] BWA Dashboard erstellt
- [x] Variable Kosten stimmen (84.858 € ≈ 84.861 €)
- [x] teile_api registriert
- [x] Tag-Filter Verkauf repariert
- [x] GlobalCube Kontenrahmen entschlüsselt

---

## 🔧 OPTIONAL TAG 85

- [ ] 498xxx Umlage bei Konsolidierung eliminieren
- [ ] BWA Vorjahresvergleich implementieren
- [ ] BWA Export (Excel/PDF)

---

## 🧪 TEST-BEFEHLE

```bash
# BWA API testen (Oktober 2025)
curl -s "http://localhost:5000/controlling/api/bwa?von=2025-10-01&bis=2025-10-31" | python3 -m json.tool

# Direkte Kosten prüfen (Ziel: 154.432 €)
sqlite3 data/greiner_controlling.db "
SELECT printf('%,.0f €', SUM(CASE WHEN debit_or_credit = 'S' THEN posted_value/100.0 ELSE -posted_value/100.0 END))
FROM loco_journal_accountings
WHERE accounting_date BETWEEN '2025-10-01' AND '2025-10-31'
  AND nominal_account_number BETWEEN 410000 AND 449999
  AND substr(nominal_account_number, 6, 1) IN ('1','2','3','4','5','6','7','8')
  AND nominal_account_number NOT BETWEEN 415100 AND 415199;
"
```

---

**Erstellt:** 27.11.2025
