# Christian (Buchhaltung) - Kontonummern-Aufbau TAG 186

**Datum:** 2026-01-13  
**TAG:** 186  
**Quelle:** Kommentare in `api/controlling_api.py` (Zeile 1936-1938)

---

## 🎯 KONTONUMMERN-AUFBAU (Nach Buchhaltung)

### KST-Mapping korrigiert nach Buchhaltung:

**Für Kosten (4xxxxx):**
- **5. Ziffer:** Kostenstellen-Kategorisierung
  - `1` = Neuwagen (NW)
  - `2` = Gebrauchtwagen (GW)
  - `3` = Service
  - `6` = Teile & Zubehör (T+Z)
  - `7` = Mietwagen

**Für Umsatz/Einsatz (7xxxxx/8xxxxx):**
- **6. Ziffer:** Filialcode = Kostenstelle
  - `1` = Deggendorf (DEG)
  - `2` = Landau (LAN)
  - (Andere Werte möglich)

---

## 📊 AKTUELLE INTERPRETATION IN DRIVE

### Einsatzwerte (7xxxxx):

**Aktuelle Logik:**
```python
# Zeile 238: Einsatz (7xxxxx): via Konto-Endziffer (6. Ziffer: 1=DEG, 2=LAN)
```

**Filter:**
- **Deggendorf Opel:** `6. Ziffer='1' OR (74xxxx AND branch=1) AND subsidiary=1 AND branch != 3`
- **Landau:** `branch=3 AND subsidiary=1`
- **Deggendorf Hyundai:** `6. Ziffer='1' AND subsidiary=2`

**Besonderheit (TAG182):**
```python
# Zeile 261: TAG182: Fix - 74xxxx Konten mit 6. Ziffer='2' und branch=1 gehören zu Deggendorf, müssen eingeschlossen werden!
```

**Das bedeutet:**
- **Standard:** 6. Ziffer='1' = Deggendorf, 6. Ziffer='2' = Landau
- **Ausnahme:** 74xxxx Konten mit `branch=1` gehören **immer** zu Deggendorf, auch wenn `6. Ziffer='2'`!

---

## 🔍 PROBLEM-ANALYSE

### Aktuelle Situation:

**74xxxx Konten mit branch=1 und 6. Ziffer='2':**
- **Anzahl:** 289 Buchungen
- **Wert:** 260,160.05 €
- **Aktuelle Zuordnung:** Deggendorf (durch `74xxxx AND branch=1` Filter)
- **Aber:** 6. Ziffer='2' deutet auf Landau hin!

**Frage:**
- Hat Christian gesagt, dass 74xxxx Konten **immer** nach `branch` zugeordnet werden, unabhängig von der 6. Ziffer?
- Oder sollte die 6. Ziffer auch bei 74xxxx Konten beachtet werden?

---

## 📋 CHRISTIAN'S AUSSAGE (Zusammenfassung)

**Kernaussage:**
> "Für Umsatz/Einsatz (7xxxxx/8xxxxx): 6. Ziffer (Filialcode = Kostenstelle)"
> - 6. Ziffer='1' = Deggendorf
> - 6. Ziffer='2' = Landau

**Aber:**
- **Ausnahme für 74xxxx:** Diese werden nach `branch_number` zugeordnet, nicht nach 6. Ziffer!
- **Grund:** 74xxxx Konten haben spezielle Logik (Lohn-Einsatz)

---

## 🎯 INTERPRETATION

### Standard-Regel:
- **6. Ziffer='1'** → Deggendorf
- **6. Ziffer='2'** → Landau

### Ausnahme-Regel (74xxxx):
- **74xxxx Konten** werden nach `branch_number` zugeordnet:
  - `branch=1` → Deggendorf (auch wenn 6. Ziffer='2')
  - `branch=3` → Landau

**Aktuelle DRIVE-Implementierung:**
```sql
-- Deggendorf Opel Filter:
(6. Ziffer='1' OR (74xxxx AND branch=1)) AND subsidiary=1 AND branch != 3
```

**Das bedeutet:**
- Standard-Konten: 6. Ziffer='1' → Deggendorf
- 74xxxx Konten: branch=1 → Deggendorf (unabhängig von 6. Ziffer)

---

## ❓ OFFENE FRAGEN

1. **Sind 74xxxx Konten mit branch=1 und 6. Ziffer='2' korrekt zu Deggendorf zugeordnet?**
   - Oder sollten sie zu Landau gehören?
   - Oder sollten sie ausgeschlossen werden?

2. **Gilt die 6. Ziffer-Regel für ALLE 7xxxxx Konten außer 74xxxx?**
   - Oder gibt es weitere Ausnahmen?

3. **Warum gibt es 74xxxx Konten mit branch=1 und 6. Ziffer='2'?**
   - Sind das Umbuchungen?
   - Oder Fehlbuchungen?

---

**KRITISCHE ERKENNTNIS:** Christian hat gesagt, dass für Einsatz/Umsatz die **6. Ziffer = Filialcode** ist (1=DEG, 2=LAN). Aber für 74xxxx Konten gibt es eine Ausnahme: Sie werden nach `branch_number` zugeordnet, nicht nach 6. Ziffer!
