# 🏦 GREINER PORTAL - PROJEKT-STATUS

**Letztes Update:** 2025-11-12 11:55:04
**Auto-generiert bei Git-Commit**

---

## ⚡ QUICK FACTS

- **Anzahl Konten:** 14
- **Gesamt-Saldo:** -281,043.07 €
- **Gesamt-Transaktionen:** 50,021

## 🏦 KONTEN-ÜBERSICHT

| ID | Kontoname | IBAN | Bank | Saldo | Trans | Letzte |
|----|-----------|------|------|-------|-------|--------|
| 1 | Sparkasse KK | ...0760036467 | Sparkasse Deggendorf | 2,838.00 € | 7697 | 2025-11-06 |
| 5 | 57908 KK | ...0000057908 | Genobank Autohaus Gr | 140,122.61 € | 11972 | 2025-11-11 |
| 6 | 22225 Immo KK | ...0000022225 | Genobank Greiner Imm | 0.00 € | 3223 | 2025-10-31 00:00:00 |
| 7 | 20057908 Darlehen | ...0020057908 | Genobank Autohaus Gr | 0.00 € | 20 | 2025-10-30 00:00:00 |
| 8 | 1700057908 Festgeld | ...1700057908 | Genobank Autohaus Gr | 0.00 € | 40 | 2025-10-31 00:00:00 |
| 9 | Hypovereinsbank KK | ...0006407420 | Hypovereinsbank | -64,445.92 € | 17924 | 2025-11-07 |
| 10 | Postbank - Hauptkonto | keine | Postbank | 0.00 € | 0 | - |
| 13 | Stellantis - Hauptkonto | keine | Stellantis | 0.00 € | 0 | - |
| 14 | 303585 VR Landau KK | ...0000303585 | VR Bank Landau | 248.00 € | 396 | 2025-10-31 |
| 15 | 1501500 HYU KK | ...0001501500 | Genobank Auto Greine | -2,058.50 € | 8645 | 2025-11-11 |
| 17 | 4700057908 Darlehen | ...4700057908 | Genobank Autohaus Gr | 11,697.74 € | 95 | 2025-11-07 |
| 19 | Darlehen Peter Greiner | keine | Genobank Auto Greine | 0.00 € | 0 | - |
| 20 | KfW 120057908 | ...0120057908 | Genobank Autohaus Gr | -369,445.00 € | 9 | 2025-09-30 |
| 23 | 3700057908 Festgeld | ...3700057908 | Genobank Auto Greine | 0.00 € | 0 | - |
| **TOTAL** | | | **-281,043.07 €** | | |

## 📅 NOVEMBER 2025 - IMPORT-STATUS

| ID | Kontoname | Trans | Von | Bis | Status |
|----|-----------|-------|-----|-----|--------|
| 1 | Sparkasse KK | 7 | 2025-11-03 | 2025-11-06 | ⚠️ Unvollständig (bis 2025-11-06) |
| 5 | 57908 KK | 330 | 2025-11-03 | 2025-11-11 | ✅ Komplett |
| 6 | 22225 Immo KK | 0 | - | - | ❌ Keine Daten |
| 7 | 20057908 Darlehen | 0 | - | - | ❌ Keine Daten |
| 8 | 1700057908 Festgeld | 0 | - | - | ❌ Keine Daten |
| 9 | Hypovereinsbank KK | 128 | 2025-11-03 | 2025-11-07 | ⚠️ Unvollständig (bis 2025-11-07) |
| 10 | Postbank - Hauptkonto | 0 | - | - | ❌ Keine Daten |
| 13 | Stellantis - Hauptkonto | 0 | - | - | ❌ Keine Daten |
| 14 | 303585 VR Landau KK | 0 | - | - | ❌ Keine Daten |
| 15 | 1501500 HYU KK | 212 | 2025-11-03 | 2025-11-11 | ✅ Komplett |
| 17 | 4700057908 Darlehen | 14 | 2025-11-07 | 2025-11-07 | ⚠️ Unvollständig (bis 2025-11-07) |
| 19 | Darlehen Peter Greiner | 0 | - | - | ❌ Keine Daten |
| 20 | KfW 120057908 | 0 | - | - | ❌ Keine Daten |
| 23 | 3700057908 Festgeld | 0 | - | - | ❌ Keine Daten |

## 📊 TRANSAKTIONS-STATISTIK (letzte 3 Monate)

- **2025-11:** 691 Transaktionen
- **2025-10:** 3,287 Transaktionen
- **2025-09:** 2,893 Transaktionen
- **2025-08:** 1,731 Transaktionen

## 🚧 OFFENE AUFGABEN

### ⚠️  Unvollständige November-Daten:
- **ID 1:** Sparkasse KK (nur bis 2025-11-06)
- **ID 9:** Hypovereinsbank KK (nur bis 2025-11-07)
- **ID 17:** 4700057908 Darlehen (nur bis 2025-11-07)

### ❌ Keine November-Daten:
- **ID 10:** Postbank - Hauptkonto
- **ID 13:** Stellantis - Hauptkonto
- **ID 19:** Darlehen Peter Greiner

## 🛠️ SYSTEM-INFO

### Pfade:
```
Projekt-Root:     /opt/greiner-portal
Datenbank:        /opt/greiner-portal/data/greiner_controlling.db
PDFs:             /opt/greiner-portal/data/kontoauszuege/
Status-Export:    /opt/greiner-portal/docs/status/
```

### Parser:
- ✅ `genobank_universal_parser` → 057908, 4700057908
- ✅ `hypovereinsbank_parser` → Hypovereinsbank
- ✅ `sparkasse_parser` → Sparkasse
- ✅ `hyundai_finance_scraper` → 1501500 HYU KK

### Git-Branch:
```bash
# Aktueller Branch:
git branch --show-current

# Alle Branches:
git branch -a
```

---

**🤖 Automatisch generiert** | Siehe auch: `SESSION_WRAP_UP_TAG*.md` für Details