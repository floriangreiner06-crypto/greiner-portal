# Kontenmapping KST-Logik - Korrektur nach Buchhaltung

**Datum:** 2026-01-12  
**TAG:** 181  
**Status:** KORRIGIERT nach Rückmeldung der Buchhaltung

---

## ✅ KORREKTE LOGIK (nach Buchhaltung)

### Umsatz/Einsatz-Konten (7xxxxx/8xxxxx)

**Beispiel: 810001**
- **8** = Erlöskonto
- **1** (2. Ziffer) = **Kostenstelle** ← KORRIGIERT!
- 0 = ohne Bedeutung
- 0 = ohne Bedeutung
- 0 = Absatzweg
- **1** (6. Ziffer) = **Filiale** (1 = DEG, 2 = Landau bei Opel; bei Hyundai nur 1)

**Kostenstellen-Mapping (2. Ziffer):**
- 1 = Neuwagen (NW)
- 2 = Gebrauchtwagen (GW)
- 3 = Teile & Zubehör (T+Z)
- 4 = Service/Werkstatt
- 6 = Mietwagen

**Filialen-Mapping (6. Ziffer):**
- 1 = Deggendorf (Opel) oder Hyundai (nur eine Filiale)
- 2 = Landau (nur Opel)

### Kosten-Konten (4xxxxx)

**Unverändert korrekt:**
- 5. Ziffer = Kostenstelle
- KST-Mapping: 0=Gemeinkosten, 1=NW, 2=GW, 3=Service, 6=T+Z, 7=Mietwagen

---

## 🔧 ÄNDERUNGEN

### 1. Kontenmapping-API (`api/kontenmapping_api.py`)

**Vorher (FALSCH):**
```sql
-- Umsatz/Einsatz: 6. Ziffer = Kostenstelle
CAST(substr(CAST(n.nominal_account_number AS TEXT), 6, 1) AS INTEGER)
```

**Nachher (KORREKT):**
```sql
-- Umsatz/Einsatz: 2. Ziffer = Kostenstelle, 6. Ziffer = Filiale
CAST(substr(CAST(n.nominal_account_number AS TEXT), 2, 1) AS INTEGER) as kst_stelle
CAST(substr(CAST(n.nominal_account_number AS TEXT), 6, 1) AS INTEGER) as filiale
```

**Zusätzlich:**
- Neue Spalte `filiale` (6. Ziffer)
- Neue Spalte `filiale_name` (DEG/Landau)

### 2. Dokumentation

- `docs/BWA_KST_LOGIK_ERKLAERUNG_TAG181.md` → Aktualisiert
- Diese Datei erstellt

---

## 📊 WARUM FUNKTIONIERT DIE BWA TROTZDEM?

**Die BWA filtert nach Kontonummer-Präfix, nicht nach Kostenstellen!**

- 81xxxx = alle Neuwagen-Erlöse (unabhängig von KST in Ziffer 2)
- 82xxxx = alle Gebrauchtwagen-Erlöse
- Die Kostenstelle in Ziffer 2 unterscheidet nur die interne Zuordnung, nicht den Bereich

**ABER:** Für KST-Filter oder detaillierte Auswertungen muss die 2. Ziffer verwendet werden!

---

## ✅ VALIDIERUNG

**Beispiel-Konten:**
- 810001: KST = 1 (NW), Filiale = 1 (DEG)
- 820002: KST = 2 (GW), Filiale = 2 (Landau)
- 840001: KST = 4 (Service), Filiale = 1 (DEG)

**Kosten-Konten (unverändert):**
- 410001: KST = 0 (Gemeinkosten)
- 411001: KST = 1 (NW)
- 416001: KST = 6 (T+Z)

---

## 🎯 FAZIT

**Korrigiert:**
- ✅ Kontenmapping zeigt jetzt 2. Ziffer als KST-Stelle für Umsatz/Einsatz
- ✅ Filiale (6. Ziffer) wird zusätzlich angezeigt
- ✅ Dokumentation aktualisiert

**Unverändert:**
- ✅ BWA funktioniert weiterhin (filtert nach Präfix)
- ✅ Kosten-Konten: 5. Ziffer bleibt korrekt
