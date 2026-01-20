# Leistungsgrad-Berechnung: Abgerechnete vs. Alle Aufträge

**Datum:** 2026-01-19  
**Anlass:** Diskrepanz zwischen Modale (123.9%) und Hauptseite (133.2%) für MA 5018

---

## 📚 Recherche-Ergebnisse: Best Practices

### 1. Definition des Leistungsgrads

**Branchenstandard:**
- **Leistungsgrad = (verrechnete Zeit ÷ gestempelte Zeit) × 100%**
- Misst, wie viel der gestempelten Zeit tatsächlich **verkauft** wurde
- Ziel: Umsatzoptimierung und Kostensteuerung

**Quellen:**
- autoservicepraxis.de: "Leistungsgrad beschreibt, wie viel von der gestempelten Zeit später auch verrechnet werden konnte"
- hermann-direkt.de: "Vergleich von verkauften Stunden mit produktiv gestempelten Stunden"
- bekumoo.de: "Verhältnis von verrechneten zu gearbeiteten Stunden"

---

## ✅ Argumente FÜR nur abgerechnete Aufträge

### 1. **Realistische, faktisch abrechenbare Leistung**
- Nur abgerechnete Stunden sind **Geldwert**
- Reflektiert, was wirklich **verdient** wurde
- Keine Verzerrung durch interne, stornierte oder nicht abrechenbare Aufträge

### 2. **Vergleichbarkeit und Steuerung**
- Bessere Vergleichbarkeit über Zeiträume hinweg
- Unterschiedlich viele interne/unabgerechnete Aufträge verzerren sonst den Wert
- Klare Grundlage für Budgets und Zielvorgaben

### 3. **Kostensteuerung**
- Zeigt klar, wo Kosten entstehen (unverrechnete Nacharbeit, Wartezeiten)
- Identifiziert ineffiziente Vorgaben
- Basis für Prozessoptimierung

**Beispiel:**
```
Mechaniker A: 100 Std gestempelt, 90 Std abgerechnet → 90% Leistungsgrad
Mechaniker B: 100 Std gestempelt, 80 Std abgerechnet → 80% Leistungsgrad

→ Mechaniker A ist effizienter bei der Umsetzung in Umsatz
```

---

## ❌ Argumente GEGEN nur abgerechnete Aufträge

### 1. **Verlust von Erkenntnissen**
- Keine Sicht auf interne Prozesse & Schwachstellen
- Wartezeiten, Nacharbeit, nicht abrechenbare Tätigkeiten werden ausgeblendet
- Wichtige Verlustquellen für Prozessoptimierung fehlen

### 2. **Verzögerung**
- Nicht alle Aufträge sind sofort abrechenbar
- Probleme bei Planung/Kontrolle von Prozesslücken
- Zu viele unvollendete Aufträge werden nicht sichtbar

### 3. **Motivation**
- Mechaniker könnten weniger motiviert sein, ordnungsgemäß zu dokumentieren
- Aufträge könnten nicht abgeschlossen werden, um Kennzahl nicht zu belasten

---

## 🛠 Empfehlung: Kombination beider Ansätze

### **Bewährte Vorgehensweise:**

1. **Leistungsgrad (Haupt-KPI):** Nur abgerechnete Aufträge
   - **Zweck:** Umsatzoptimierung, finanzielle Steuerung
   - **Formel:** `(Abgerechnete AW / Gestempelte Zeit) × 100`
   - **Zeigt:** Wie effizient aus gebuchter Zeit Ertrag wird

2. **Produktivitätsgrad (Sekundär-KPI):** Alle Aufträge
   - **Zweck:** Prozessoptimierung, Ressourcenbindung
   - **Formel:** `(Gestempelte Auftragsstunden / Anwesenheitsstunden) × 100`
   - **Zeigt:** Wie viel überhaupt im Auftragskontext gearbeitet wird

### **Praxiserfahrung:**

- **bekumoo.de:** Leistungsgrad = Verhältnis verrechneter zu gearbeiteten Stunden
- **hermann-direkt.de:** Kombination aus Produktivitätsgrad (alle) und Leistungsgrad (abgerechnet)
- **iww.de:** Gestempelte Stunden sollten nur solche produktiven Aufträge umfassen, die auch abgerechnet werden könnten

---

## 🔍 Aktuelle Situation in DRIVE

### **Problem:**
- **Modale:** Verwendet `werkstatt_auftraege_abgerechnet` → **123.9%** (nur abgerechnete)
- **Hauptseite:** Verwendet `get_vorgabezeit_aus_labours()` → **133.2%** (alle Aufträge)
- **Differenz:** 9.3%

### **Aktuelle Implementierung:**

#### Modale (`/api/werkstatt/mechaniker/<nr>`):
```python
# Verwendet werkstatt_auftraege_abgerechnet
# → Nur abgerechnete Aufträge
# → Leistungsgrad: 123.9%
```

#### Hauptseite (`get_mechaniker_leistung()`):
```python
# Verwendet get_vorgabezeit_aus_labours()
# → Alle Aufträge mit Stempelung
# → Leistungsgrad: 133.2%
```

### **Dokumentation (docs/leistungsgrad_berechnung_erklaerung.md):**
```
### 3. Nur fakturierte Positionen zählen

Filter:
- Nur Positionen mit is_invoiced = true
- Nur Positionen, bei denen der Mechaniker tatsächlich gestempelt hat
- Nur Positionen mit time_units > 0

Warum?
- Nur verrechnete Arbeit zählt
- Keine "Luftbuchungen"
- Realistische Bewertung
```

**⚠️ Widerspruch:** Die Dokumentation sagt "nur fakturierte Positionen", aber die Hauptseite verwendet alle Aufträge!

---

## 💡 Empfehlung für DRIVE

### **Option 1: Konsistenz mit Modale (EMPFOHLEN)**

**Vorgehen:**
- Hauptseite sollte **nur abgerechnete Aufträge** verwenden (wie Modale)
- Verwendet `werkstatt_auftraege_abgerechnet` als Datenquelle
- **Vorteil:** Konsistenz zwischen Modale und Hauptseite
- **Vorteil:** Reflektiert tatsächlichen Umsatz
- **Vorteil:** Entspricht Branchenstandard

**Implementierung:**
```python
# Statt get_vorgabezeit_aus_labours() verwenden:
# werkstatt_auftraege_abgerechnet für Vorgabezeit
# werkstatt_auftraege_abgerechnet für Stempelzeit
```

### **Option 2: Zwei KPIs anzeigen**

**Vorgehen:**
- **Leistungsgrad (abgerechnet):** Nur abgerechnete Aufträge (wie Modale)
- **Produktivitätsgrad (alle):** Alle Aufträge mit Stempelung
- **Vorteil:** Beide Perspektiven sichtbar
- **Nachteil:** Komplexer, könnte verwirren

### **Option 3: Konfigurierbar**

**Vorgehen:**
- Dropdown im Dashboard: "Alle Aufträge" vs. "Nur abgerechnete"
- **Vorteil:** Flexibilität
- **Nachteil:** Mehr Komplexität

---

## ✅ Finale Empfehlung

**Für DRIVE empfehle ich Option 1:**

1. **Hauptseite sollte nur abgerechnete Aufträge verwenden**
   - Konsistenz mit Modale
   - Entspricht Branchenstandard
   - Reflektiert tatsächlichen Umsatz

2. **Zusätzlich: Produktivitätsgrad für alle Aufträge**
   - Als sekundäre Kennzahl
   - Für Prozessoptimierung
   - Zeigt Ressourcenbindung

3. **Dokumentation aktualisieren**
   - Klarstellen: Leistungsgrad = nur abgerechnete Aufträge
   - Produktivitätsgrad = alle Aufträge

---

## 📊 Erwartete Auswirkungen

### **Für MA 5018 (Majer, Jan):**

**Aktuell:**
- Modale: 123.9% (nur abgerechnet)
- Hauptseite: 133.2% (alle Aufträge)
- Differenz: 9.3%

**Nach Änderung (Option 1):**
- Modale: 123.9% (nur abgerechnet)
- Hauptseite: ~123.9% (nur abgerechnet)
- Differenz: ~0% ✅

**Interpretation:**
- 123.9% bedeutet: Jan hat 23.9% mehr AW abgerechnet als Zeit gestempelt
- Sehr gute Leistung! (über 100% = schneller als Vorgabe)

---

## 🔗 Quellen

1. **autoservicepraxis.de:** "Tempo ist nicht alles" - Leistungsgrad-Definition
2. **hermann-direkt.de:** "Produktivität erhöhen" - Werkstatt-Kennzahlen
3. **bekumoo.de:** Werkstatt-Kennzahlen - Leistungsgrad-Berechnung
4. **iww.de:** "Der Werkstattumsatz darf es ein bisschen mehr sein" - Kennzahlen im Kfz-Gewerbe
5. **controllingportal.de:** Kennzahl Leistungsgrad

---

**Status:** Empfehlung erstellt, wartet auf Entscheidung  
**Nächster Schritt:** Implementierung von Option 1 (Konsistenz mit Modale)
