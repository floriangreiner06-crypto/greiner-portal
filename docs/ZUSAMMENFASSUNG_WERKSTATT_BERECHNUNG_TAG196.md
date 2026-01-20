# ZUSAMMENFASSUNG: Werkstatt-KPI-Berechnungen

**Datum:** 2026-01-18  
**Status:** 🔍 **ZU ÜBERPRÜFEN**

---

## 📊 PROBLEM

Dashboard zeigt falsche Werte:
- "Stempelzeit": 2.113,3 Std (sollte St-Anteil sein, ist aber Vorgabezeit)
- "Anwesenheit": 626,4 Std (sollte echte Anwesenheit sein, ist aber St-Anteil)
- Einzelne Mechaniker-Werte sind ebenfalls falsch

---

## 🔍 DATENQUELLEN & ZUORDNUNG

### Funktionen und ihre Rückgabewerte:

| Funktion | Rückgabe | Tatsächlich gibt zurück | Problem |
|----------|----------|-------------------------|---------|
| `get_st_anteil_position_basiert()` | St-Anteil | **AW-Anteil (Vorgabezeit)** | ❌ Falsch benannt/berechnet |
| `get_anwesenheit_rohdaten()` | Anwesenheit | **St-Anteil (Stempelzeit)** | ❌ Falsch benannt/berechnet |
| `get_aw_verrechnet()` | AW-Einheiten | AW-Einheiten | ✅ Korrekt |
| `get_stempelzeit_locosoft()` | Zeit-Spanne | Zeit-Spanne (Fallback) | ✅ Korrekt |

### Aktuelle Zuordnung (Zeile 379-430):

```python
vorgabezeit_min = st_anteil_position.get(emp_nr, 0)  # Aus get_st_anteil_position_basiert()
st_anteil_min = anwesenheit.get(emp_nr, {}).get('anwesend_min', 0)  # Aus get_anwesenheit_rohdaten()
anwesenheit_min = Fallback aus get_stempelzeit_locosoft() oder st_anteil_min * 1.2

rohdaten[emp_nr] = {
    'stempelzeit': st_anteil_min,  # St-Anteil (aus get_anwesenheit_rohdaten)
    'anwesenheit': anwesenheit_min,  # Echte Anwesenheit (Fallback)
    'vorgabezeit': vorgabezeit_min,  # AW-Anteil (aus get_st_anteil_position_basiert)
    'aw': aw_roh,  # AW-Einheiten (aus get_aw_verrechnet)
}
```

**⚠️ PROBLEM:** Die Zuordnung ist vertauscht, weil die Funktionen falsche Werte zurückgeben!

---

## 📐 KPI-BERECHNUNGEN

### Leistungsgrad (Zeile 1225-1231):
```python
leistungsgrad = (vorgabezeit_min / stempelzeit_min) × 100
```

### Produktivität (Zeile 1233-1236):
```python
produktivitaet = (stempelzeit_min / anwesenheit_min) × 100
```

### Anwesenheitsgrad (Zeile 1238-1242):
```python
anwesenheitsgrad = (anwesenheit_min / bezahlt_min) × 100
```

---

## 📊 AKTUELLE WERTE (01.01.2026 - 18.01.2026)

### Gesamt (alle 52 Mechaniker):
- Stempelzeit: 187.175 Min = **3.119,6 Std**
- Anwesenheit: 224.610 Min = **3.743,5 Std**
- Vorgabezeit: 126.798 Min = **2.113,3 Std**
- AW: 5.641,7 AW
- Leistungsgrad: **67,7%**
- Produktivität: **83,3%**

### Top 10 (nach Leistungsgrad):
- Stempelzeit: 37.584 Min = **626,4 Std**
- Anwesenheit: 45.101 Min = **751,7 Std**
- Vorgabezeit: 126.798 Min = **2.113,3 Std**
- AW: 5.641,7 AW
- Leistungsgrad: **562,5%** (unrealistisch!)
- Produktivität: **83,3%**

### Beispiel: MA 5007 (Reitmeier, Tobias):
- Stempelzeit: 4.365 Min = **72,7 Std**
- Anwesenheit: 5.238 Min = **87,3 Std**
- Vorgabezeit: 14.926 Min = **248,8 Std**
- AW: 646,5 AW
- Leistungsgrad: **342,0%** (unrealistisch!)
- Produktivität: **83,3%**

---

## 🔍 ROOT CAUSE

**Problem 1:** `get_st_anteil_position_basiert()` gibt **AW-Anteil** zurück (248,8 Std), nicht St-Anteil
- Erwartet: St-Anteil (z.B. 72,7 Std)
- Tatsächlich: AW-Anteil (248,8 Std)
- **Vergleich:** `get_aw_verrechnet()` gibt 64,7 Std zurück (646,5 AW × 6 / 60)

**Problem 2:** `get_anwesenheit_rohdaten()` gibt **St-Anteil** zurück (72,7 Std), nicht Anwesenheit
- Erwartet: Anwesenheit (z.B. 87,3 Std)
- Tatsächlich: St-Anteil (72,7 Std)
- **Vergleich:** Type=2 roh gibt 331,7 Std zurück (ohne 75% Faktor)

**Problem 3:** Dashboard zeigt Werte vertauscht
- Dashboard "Stempelzeit" = Vorgabezeit (2.113 Std)
- Dashboard "Anwesenheit" = Stempelzeit (626 Std)

---

## ✅ LÖSUNG

### Option 1: Funktionen korrigieren
- `get_st_anteil_position_basiert()` sollte **St-Anteil** zurückgeben
- `get_anwesenheit_rohdaten()` sollte **Anwesenheit** zurückgeben

### Option 2: Zuordnung korrigieren
- `vorgabezeit = get_aw_verrechnet() × 6` (korrekt)
- `stempelzeit = get_st_anteil_position_basiert()` (korrekt, wenn Funktion korrigiert)
- `anwesenheit = get_anwesenheit_rohdaten()` (korrekt, wenn Funktion korrigiert)

### Option 3: Dashboard korrigieren
- Dashboard "Stempelzeit" = `m.vorgabezeit_std` (zeigt Vorgabezeit)
- Dashboard "Anwesenheit" = `m.stempelzeit_std` (zeigt Stempelzeit)

---

## 📝 VOLLSTÄNDIGE DOKUMENTATION

Siehe:
- `docs/BERECHNUNG_WERKSTATT_KPIS_VOLLSTAENDIG_TAG196.md` - Vollständige Dokumentation
- `docs/SQL_QUERIES_WERKSTATT_KPIS_TAG196.md` - Alle SQL-Queries zum Testen

---

**Erstellt:** TAG 196  
**Status:** 🔍 **ZU ÜBERPRÜFEN**
