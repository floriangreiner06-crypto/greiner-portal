# 📊 ANALYSE: fahrzeugfinanzierungen Tabelle

**Datum:** 01.12.2025  
**Tabelle:** fahrzeugfinanzierungen  
**Spalten:** 55 (zu viele!)

---

## 🔴 HAUPTPROBLEME

### 1. rrdi wird für verschiedene Dinge missbraucht
| Institut | Aktuell | Richtig wäre |
|----------|---------|--------------|
| Stellantis | Händler-ID (DE08250) ✅ | Händler-ID |
| Santander | Hersteller (OPEL) ❌ | Leer |
| Hyundai | "Hyundai" (konstant) ❌ | Leer |

### 2. hersteller ist KOMPLETT LEER (0/0/0)

### 3. produktfamilie ist INKONSISTENT
| Institut | Inhalt |
|----------|--------|
| Stellantis | Neuwagen, Vorführwagen |
| Santander | PartPlus/Fahrzeuge/Mobil/Vermieter |
| Hyundai | Hyundai/HNC1/Stock |

### 4. produkt_kategorie nur bei Hyundai befüllt

---

## 🎯 MIGRATIONS-PLAN

### Phase 1: Daten korrigieren
### Phase 2: Import-Scripts anpassen  
### Phase 3: View anpassen
### Phase 4: Template vereinfachen

**Erstellt:** 01.12.2025
