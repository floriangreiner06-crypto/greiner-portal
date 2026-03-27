# 🎯 DRIVE PHILOSOPHY - Projekt-Leitlinien

**Erstellt:** TAG 94 (05.12.2025)
**Autor:** Florian Greiner / Claude

---

## 🚀 DRIVE = Digital Real-time Integrated Vehicle Enterprise

### KERNPRINZIP: PROFITABILITÄT DURCH TRANSPARENZ

> "Wir bauen alles so, dass wir profitabel werden!" - Florian Greiner

---

## ❌ WAS WIR NICHT ZEIGEN

| Element | Grund | Alternative |
|---------|-------|-------------|
| **Negativer Bankensaldo** | Deprimiert nur | Zeige Cashflow, Trends, Aktionen |
| **Reine Kosten-Ansichten** | Demotivierend | Zeige Effizienz, Einsparpotenzial |
| **Statische Berichte** | Keine Handlung möglich | Zeige Live-Daten mit Aktionen |

---

## ✅ WAS WIR ZEIGEN

### 1. WERKSTATT-KAPAZITÄT (Key Feature!)
- **Auslastung** → Ziel ist 110% (die Jungs packen das!)
- **Unverplante Aufträge** → Umsatzpotenzial!
- **Teile-Status** → Blockaden beseitigen
- **Überfällige Aufträge** → Sofort handeln!

### 2. VERKAUF
- **Auftragseingang** → Pipeline-Wert
- **Auslieferungen** → Realisierter Umsatz
- **Deckungsbeitrag** → Echte Profitabilität

### 3. FINANZEN
- **Zinslast** → Einspar-Potenzial
- **Cashflow** → Liquidität
- **Trends** → Entwicklung

---

## 🎨 DESIGN-PRINZIPIEN

### Farben nach Status:
- 🔵 **Blau** (<50%): Unterausgelastet - POTENZIAL!
- 🟢 **Grün** (50-110%): Optimal - ZIEL!
- 🟡 **Gelb** (110-130%): Hoch - AUFPASSEN!
- 🔴 **Rot** (>130%): Kritisch - HANDELN!

### Ziel-Linie bei 110%
Die Werkstatt-Kapazität zeigt eine grüne Linie bei 110% - das ist das Ziel, nicht 100%!

---

## 📊 KPI-PRIORITÄT IM DASHBOARD

### Haupt-Dashboard (4 KPIs):
1. **Werkstatt-Kapazität HEUTE** (statt Bankensaldo!)
2. **Finanzierte Fahrzeuge** (Zinslast im Blick)
3. **Offene Urlaubsanträge** (HR)
4. **Auftragseingang** (Verkauf)

### Werkstatt-Widget zeigt:
- Tages-Auslastung
- Wochen-Forecast
- Unverplante Aufträge (= versteckter Umsatz!)
- Teile-Blockaden (= Handlungsbedarf!)
- Überfällige Aufträge (= sofort!)

---

## 🔧 TECHNISCHE UMSETZUNG

### API-Endpoints für Kapazität:
```
GET /api/werkstatt/live/kapazitaet
GET /api/werkstatt/live/forecast
```

### Konfiguration:
```javascript
KAPA_CONFIG = {
    ZIEL_AUSLASTUNG: 110,  // Nicht 100!
    STATUS_GRENZEN: {
        niedrig: 50,
        normal: 90,
        hoch: 110,
        kritisch: 130
    }
}
```

---

## 💡 MERKSÄTZE FÜR CLAUDE

1. **Zeige Potenzial, nicht Probleme**
2. **110% ist das Ziel, nicht 100%**
3. **Jeder Screen muss zu Handlung führen**
4. **Negativer Saldo = Nicht anzeigen**
5. **Werkstatt-Profitabilität = Key Feature von DRIVE**

---

*Diese Datei definiert die Philosophie von DRIVE und sollte bei jeder Session berücksichtigt werden.*
