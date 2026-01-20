# TODO für Claude - Session Start TAG 197

**Datum:** Nach TAG 196  
**Status:** 📋 **BEREIT FÜR NÄCHSTE SESSION**

---

## 📋 Offene Tasks

### 1. Stmp.Anteil weiter analysieren (PRIORITÄT: HOCH) 🔴

**Problem:** Stmp.Anteil ist noch zu hoch (989.48 AW vs. 827.67 AW in Locosoft für Tobias, 01.01.26-15.01.26)

**Differenz:** -161.81 AW

**Mögliche Ursachen:**
- Pausen-Logik nicht exakt (Mittagspause 12:00-12:44)
- Weitere Filter in Locosoft (z.B. nur fakturierte Positionen?)
- Andere Berechnungslogik für "Stmp.Anteil" in Mitarbeiter-Tabelle vs. Position-Tabelle
- "Zeitbasis" Werte werden anders berechnet als erwartet

**Nächste Schritte:**
1. Prüfen, ob Locosoft nur fakturierte Positionen verwendet
2. Prüfen, ob Pausen-Logik exakt ist (alle Szenarien testen)
3. Prüfen, ob "Zeitbasis" Werte anders berechnet werden
4. Vergleich mit weiteren Mechanikern (Jan, Jaroslaw)

**Dateien:**
- `api/werkstatt_data.py` → `get_st_anteil_position_basiert()`

---

### 2. Leistungsgrad validieren (PRIORITÄT: MITTEL) 🟡

**Problem:** Leistungsgrad ist noch zu niedrig (53.4% vs. 63.4% in Locosoft für Tobias)

**Ursache:** Abhängig von Stmp.Anteil (wird automatisch korrigiert, wenn Stmp.Anteil korrekt ist)

**Status:** Wird automatisch korrigiert, wenn Stmp.Anteil korrekt ist

**Nächste Schritte:**
- Nach Korrektur von Stmp.Anteil automatisch validieren
- Mit weiteren Mechanikern testen

---

### 3. Testen mit weiteren Mechanikern (PRIORITÄT: MITTEL) 🟡

**Ziel:** Validieren, ob die Berechnung für alle Mechaniker korrekt ist

**Mechaniker:**
- Jan Majer (5018) - Zeitraum 01.01.26-15.01.26
- Jaroslaw (5014) - Zeitraum 01.01.26-15.01.26
- Weitere Mechaniker nach Bedarf

**Vergleich:**
- AW-Anteil
- Stmp.Anteil
- Leistungsgrad
- Anwesenheit
- Produktivität

---

### 4. Service-Neustart nach finaler Korrektur (PRIORITÄT: HOCH) 🔴

**Nach erfolgreicher Korrektur:**
1. Service neu starten: `sudo systemctl restart greiner-portal`
2. Ergebnisse in DRIVE validieren
3. Vergleich mit Locosoft UI

**Passwort:** `OHL.greiner2025` (siehe `CLAUDE.md`)

---

## ✅ Abgeschlossen (TAG 196)

- ✅ `get_aw_verrechnet()` angepasst - verwendet jetzt ALLE AW (auch nicht-fakturierte, auch interne)
- ✅ `get_st_anteil_position_basiert()` angepasst - summiert "Zeitbasis" Werte direkt, nur Positionen MIT AW
- ✅ `berechne_mechaniker_kpis_aus_rohdaten()` korrigiert - Leistungsgrad-Berechnung für AW in AW
- ✅ AW-Anteil ist sehr nah (528.50 AW vs. 524.83 AW in Locosoft) ✅
- ⚠️ Stmp.Anteil noch zu hoch (989.48 AW vs. 827.67 AW) - weitere Analyse erforderlich
- ⚠️ Leistungsgrad noch zu niedrig (53.4% vs. 63.4%) - abhängig von Stmp.Anteil

---

## 📊 Aktueller Status

**AW-Anteil:** ✅ **SEHR NAH!** (Differenz: -3.67 AW)

**Stmp.Anteil:** ⚠️ **Noch zu hoch** (Differenz: -161.81 AW)

**Leistungsgrad:** ⚠️ **Noch zu niedrig** (Differenz: 10.0%) - wird automatisch korrigiert, wenn Stmp.Anteil korrekt ist

**Code-Qualität:** ✅ **SSOT-konform, keine Redundanzen**

---

## 🔍 Wichtige Hinweise für nächste Session

### Locosoft-Logik (TAG 195 Erkenntnisse)

1. **AW-Anteil:**
   - Locosoft verwendet **ALLE AW** von Positionen, die dem Mechaniker zugeordnet sind
   - Nicht nur fakturierte AW
   - Auch interne AW werden berücksichtigt

2. **Stmp.Anteil:**
   - Locosoft verwendet **"Zeitbasis" Werte** (direkt summiert, auch wenn dupliziert)
   - Nur Positionen **MIT AW** werden berücksichtigt
   - Mittagspause (12:00-12:44) wird automatisch abgezogen

3. **Betriebsstätten:**
   - Locosoft berücksichtigt **alle Betriebsstätten** für einen Mechaniker
   - Nicht getrennt nach Betriebsstätte

### Test-Daten

**Tobias (5007) - Zeitraum 01.01.26-15.01.26:**
- Locosoft: AW-Anteil 52:29 (524.83 AW), Stmp.Anteil 82:46 (827.67 AW), Leistungsgrad 63,4%
- DRIVE: AW-Anteil 528.50 AW, Stmp.Anteil 989.48 AW, Leistungsgrad 53.4%

### Dateien

- `api/werkstatt_data.py` - Hauptdatei für KPI-Berechnung
- `utils/kpi_definitions.py` - SSOT für KPI-Formeln
- `docs/ANALYSE_STEMPELZEITEN_TOBIAS_TAG195.md` - Analyse-Dokumentation

---

## 🚨 Kritische Probleme

**Keine kritischen Probleme bekannt.**

---

**Erstellt:** Nach TAG 196  
**Für Session:** TAG 197
