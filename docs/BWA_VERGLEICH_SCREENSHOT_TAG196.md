# BWA Vergleich: Screenshot vs. Erwartete Werte - TAG 196

**Datum:** 2026-01-16  
**Status:** 🔍 Diskrepanz identifiziert

---

## 📊 SCREENSHOT WERTE (Web-UI)

### YTD bis Dezember 2025

| Position | DRIVE (Screenshot) | GlobalCube (Screenshot) | Differenz |
|----------|-------------------|------------------------|-----------|
| Indirekte Kosten YTD | -838.938 € | 838.944 € | -1.677.882 € ⚠️ |
| Betriebsergebnis YTD | -407.613 € | -375.905 € | -31.708 € ⚠️ |

**Hinweis:** Indirekte Kosten haben unterschiedliche Vorzeichen! (DRIVE: negativ, GlobalCube: positiv)

---

## 🔍 PROBLEM IDENTIFIZIERT

### 1. Indirekte Kosten Vorzeichen

**DRIVE zeigt:** -838.938 € (negativ)  
**GlobalCube zeigt:** 838.944 € (positiv)

**Problem:** Die Vorzeichen sind unterschiedlich! Das deutet auf ein Problem in der Berechnungslogik hin.

**Erwartung:**
- Indirekte Kosten sollten **positiv** sein (als Betrag)
- In der BWA werden sie dann **abgezogen** (negativ dargestellt)

### 2. Betriebsergebnis YTD-Differenz

**DRIVE:** -407.613 €  
**GlobalCube:** -375.905 €  
**Differenz:** -31.708 € (DRIVE zu negativ)

**Erwartung nach 498001-Korrektur:**
- Indirekte Kosten YTD: 638.937,55 € (838.937,55 - 200.000)
- Betriebsergebnis YTD: -205.863,59 € (-405.863,59 + 200.000)
- Differenz zu GlobalCube: +170.041,41 € (DRIVE zu positiv)

**Aktuelle Situation:**
- DRIVE zeigt -407.613 € (nicht -205.863,59 €)
- Das bedeutet: **498001 wird noch nicht korrekt ausgeschlossen!**

---

## ⚠️ MÖGLICHE URSACHEN

### 1. 498001 wird noch nicht ausgeschlossen

**Prüfung:**
- Indirekte Kosten YTD: -838.938 € (entspricht 838.937,55 € ohne 498001-Ausschluss)
- Wenn 498001 ausgeschlossen wäre: 638.937,55 €
- **Fazit:** 498001 wird noch nicht ausgeschlossen!

### 2. Service wurde nicht neu gestartet

**Status:**
- Code wurde korrigiert (498001-Ausschluss implementiert)
- Service wurde neu gestartet (14:04:59)
- **Aber:** Web-UI zeigt noch alte Werte

**Mögliche Ursachen:**
1. Browser-Cache (alte JavaScript-Dateien)
2. API verwendet noch alte Logik
3. Service-Neustart war nicht erfolgreich

### 3. Vorzeichen-Problem

**Indirekte Kosten:**
- DRIVE zeigt: -838.938 € (negativ)
- GlobalCube zeigt: 838.944 € (positiv)
- **Problem:** Vorzeichen-Unterschied deutet auf Berechnungsfehler hin

---

## 🔧 LÖSUNG

### 1. Browser-Cache leeren

**Schritte:**
1. Strg+F5 (Hard Refresh)
2. Oder: Inkognito-Modus verwenden
3. Oder: Browser-Cache komplett leeren

### 2. API direkt testen

**Test-URL:**
```
http://10.80.80.20:5000/api/controlling/bwa/v2?monat=12&jahr=2025&firma=0&standort=0
```

**Erwartete Response:**
- `indirekte` (YTD): sollte 638.937,55 € sein (nicht 838.937,55 €)
- `betriebsergebnis` (YTD): sollte -205.863,59 € sein (nicht -405.863,59 €)

### 3. Service-Status prüfen

```bash
sudo systemctl status greiner-portal
journalctl -u greiner-portal -n 50
```

---

## 📋 NÄCHSTE SCHRITTE

### Priorität HOCH:
1. **API direkt testen** (ohne Browser-Cache)
2. **Prüfen ob Service korrekt läuft**
3. **Prüfen ob 498001 wirklich ausgeschlossen wird**

### Priorität MITTEL:
4. **Vorzeichen-Problem analysieren** (warum zeigt DRIVE negative Indirekte Kosten?)
5. **Weitere Differenzen identifizieren**

---

*Erstellt: TAG 196 | Autor: Claude AI*
