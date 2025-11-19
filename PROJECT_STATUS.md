# 🏦 GREINER PORTAL - PROJEKT-STATUS

**Letztes Update:** 2025-11-19 19:41:37
**Auto-generiert bei Git-Commit**

---

## ⚡ QUICK FACTS

- **Anzahl Konten:** 12
- **Gesamt-Saldo:** 0.00 €
- **Gesamt-Transaktionen:** 14,311

## 🏦 KONTEN-ÜBERSICHT

| ID | Kontoname | IBAN | Bank | Saldo | Trans | Letzte |
|----|-----------|------|------|-------|-------|--------|
| 1 | Sparkasse KK | ...0760036467 | Sparkasse Deggendorf | 0.00 € | 279 | 2025-11-18 |
| 5 | 57908 KK | ...0000057908 | Genobank Autohaus Gr | 0.00 € | 7160 | 2025-11-19 |
| 6 | 22225 Immo KK | ...0000022225 | Genobank Greiner Imm | 0.00 € | 232 | 2025-11-17 |
| 7 | 20057908 Darlehen | ...0020057908 | Genobank Autohaus Gr | 0.00 € | 20 | 2025-10-30 |
| 8 | 1700057908 Festgeld | ...1700057908 | Genobank Autohaus Gr | 0.00 € | 40 | 2025-10-31 |
| 9 | Hypovereinsbank KK | ...0006407420 | Hypovereinsbank | 0.00 € | 2574 | 2025-11-18 |
| 14 | 303585 VR Landau KK | ...0000303585 | VR Bank Landau | 0.00 € | 423 | 2025-11-18 |
| 15 | 1501500 HYU KK | ...0001501500 | Genobank Auto Greine | 0.00 € | 3504 | 2025-11-19 |
| 17 | 4700057908 Darlehen | ...4700057908 | Genobank Autohaus Gr | 0.00 € | 70 | 2025-11-10 |
| 20 | KfW 120057908 | ...0120057908 | Genobank Autohaus Gr | 0.00 € | 9 | 2025-09-30 |
| 21 | 3700057908 Festgeld | ...3700057908 | Genobank Auto Greine | 0.00 € | 0 | - |
| 22 | Peter Greiner Darlehen | keine | Intern / Gesellschaf | 0.00 € | 0 | - |
| **TOTAL** | | | **0.00 €** | | |

## 📅 NOVEMBER 2025 - IMPORT-STATUS

| ID | Kontoname | Trans | Von | Bis | Status |
|----|-----------|-------|-----|-----|--------|
| 1 | Sparkasse KK | 22 | 2025-11-01 | 2025-11-18 | ✅ Komplett |
| 5 | 57908 KK | 444 | 2025-11-03 | 2025-11-19 | ✅ Komplett |
| 6 | 22225 Immo KK | 13 | 2025-11-03 | 2025-11-17 | ✅ Komplett |
| 7 | 20057908 Darlehen | 0 | - | - | ❌ Keine Daten |
| 8 | 1700057908 Festgeld | 0 | - | - | ❌ Keine Daten |
| 9 | Hypovereinsbank KK | 150 | 2025-11-03 | 2025-11-18 | ✅ Komplett |
| 14 | 303585 VR Landau KK | 26 | 2025-11-03 | 2025-11-18 | ✅ Komplett |
| 15 | 1501500 HYU KK | 207 | 2025-11-03 | 2025-11-19 | ✅ Komplett |
| 17 | 4700057908 Darlehen | 3 | 2025-11-04 | 2025-11-10 | ⚠️ Unvollständig (bis 2025-11-10) |
| 20 | KfW 120057908 | 0 | - | - | ❌ Keine Daten |
| 21 | 3700057908 Festgeld | 0 | - | - | ❌ Keine Daten |
| 22 | Peter Greiner Darlehen | 0 | - | - | ❌ Keine Daten |

## 📊 TRANSAKTIONS-STATISTIK (letzte 3 Monate)

- **2025-11:** 865 Transaktionen
- **2025-10:** 1,476 Transaktionen
- **2025-09:** 1,435 Transaktionen
- **2025-08:** 565 Transaktionen

## 🚧 OFFENE AUFGABEN

### ⚠️  Unvollständige November-Daten:
- **ID 17:** 4700057908 Darlehen (nur bis 2025-11-10)

### ❌ Keine November-Daten:
- **ID 21:** 3700057908 Festgeld
- **ID 22:** Peter Greiner Darlehen

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