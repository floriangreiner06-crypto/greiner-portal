# BWA Test-Ergebnisse nach 498001-Korrektur - TAG 188

**Datum:** 2026-01-XX  
**Status:** ⚠️ Service-Neustart erforderlich

---

## 📊 AKTUELLE WERTE (vor Neustart)

### Monat Dezember 2025

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Betriebsergebnis | -116.147,37 € | -116.248,00 € | +100,63 € | ✅ Sehr gut (0,09%) |

**Indirekte Kosten:** 185.057,99 €  
→ Entspricht **OHNE** 498001 (Service noch nicht neu gestartet)

### YTD bis Dezember 2025

| Position | DRIVE | GlobalCube | Differenz | Status |
|----------|-------|------------|-----------|--------|
| Betriebsergebnis | -391.157,71 € | -245.733,00 € | -145.424,71 € | ❌ Noch groß (59,18%) |

**Indirekte Kosten:** 838.937,55 €  
→ Entspricht **OHNE** 498001 (Service noch nicht neu gestartet)

---

## 🔄 ERWARTETE WERTE (nach Neustart mit 498001 enthalten)

### Monat Dezember 2025

**Mit 498001 enthalten (als HABEN = Kostenminderung):**
- Indirekte Kosten: 135.057,99 € (185.057,99 - 50.000)
- Betriebsergebnis: -66.147,37 € (-116.147,37 + 50.000)
- GlobalCube BE: -116.248,00 €
- **Erwartete Differenz:** +50.100,63 € (DRIVE zu positiv)

### YTD bis Dezember 2025

**Mit 498001 enthalten (4 Monate × 50.000 € = 200.000 €):**
- Indirekte Kosten: 638.937,55 € (838.937,55 - 200.000)
- Betriebsergebnis: -191.157,71 € (-391.157,71 + 200.000)
- GlobalCube BE: -245.733,00 €
- **Erwartete Differenz:** +54.575,29 € (DRIVE zu positiv)

---

## ⚠️ PROBLEM

**Aktuelle Situation:**
- Code wurde korrigiert (498001 wieder eingeschlossen)
- Service wurde **NICHT neu gestartet** (sudo-Passwort-Problem)
- API zeigt noch alte Werte (ohne 498001)

**Nächste Schritte:**
1. Service manuell neu starten: `sudo systemctl restart greiner-portal`
2. BWA-Werte erneut testen
3. Mit GlobalCube vergleichen

---

## 💡 ERKENNTNISSE

1. **Monat Dezember:** Sehr gute Übereinstimmung (100,63 € Differenz = 0,09%)
2. **YTD:** Noch große Differenz (-145.424,71 €)
3. **498001:** Muss enthalten sein (echte Kostenposition, Auto Greiner zahlt 50.000 €/Monat)

---

*Erstellt: TAG 188 | Autor: Claude AI*
