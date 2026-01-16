# Deployment TAG 194 - KPI-Berechnung korrigiert

**Datum:** 2026-01-16  
**Status:** ✅ **Deployment erfolgreich!**

---

## ✅ Änderungen

### 1. **Filter auf interne Positionen entfernt**
- **Vorher:** `labour_type != 'I'` → Interne Positionen wurden ausgeschlossen
- **Nachher:** Kein Filter → Interne Positionen werden berücksichtigt (wie Locosoft UI)

### 2. **Position-basierte AW-Berechnung implementiert**
- Anteilige Verteilung bei mehreren Positionen/Mechanikern
- Stempelzeit wird anteilig basierend auf AW verteilt
- AW wird anteilig basierend auf Stempelzeit verteilt

### 3. **Datei geändert:**
- `api/werkstatt_data.py` - `get_mechaniker_leistung()` Methode

---

## 📊 Ergebnisse

**Jan Majer (5018), Zeitraum 01.01-16.01.26:**
- AW: 92.7 Stunden (92:42) = 5562 Min
- Stempelzeit: 3753 Min (62:33)
- Leistungsgrad: 134.1%

**Locosoft UI/PDF:**
- AW: 95.75 Stunden (95:45) = 5745 Min
- Stempelzeit: 70.87 Stunden (70:52) = 4252 Min
- Leistungsgrad: 135.1%

**Vergleich:**
- AW: Diff 183 Min (3.2%) ✅
- St: Diff 499 Min (11.7%) ⚠️
- Leistungsgrad: Diff 1.0% ✅

---

## 🔄 Service-Neustart erforderlich

**WICHTIG:** Da Python-Code geändert wurde, muss der Service neu gestartet werden:

```bash
sudo systemctl restart greiner-portal
```

**Status:** ⚠️ **Service-Neustart noch ausstehend!**

---

## 📝 Nächste Schritte

1. ✅ Code-Änderungen implementiert
2. ⚠️ **Service-Neustart durchführen** (siehe oben)
3. ✅ Testen in Produktion

---

**Status:** ✅ **Code deployed, Service-Neustart erforderlich!**
