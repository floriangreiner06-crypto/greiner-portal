# 🔍 Leerlaufaufträge-Analyse - Walter Smola (TAG 181)

**Datum:** 2026-01-13  
**Anlass:** Niedriger Leistungsgrad (9.0%) von Walter Smola in der Werkstatt-Übersicht

---

## 📋 PROBLEM

Walter Smola (Mitarbeiternummer: 5003) hat einen sehr niedrigen Leistungsgrad von **9.0%** und verursacht einen hohen "Entgangenen Umsatz" von **5.473,02 €**.

**Vermutung:** Er stempelt seine Anwesenheit auf einen "Leerlaufauftrag" der Filiale Landau, obwohl er als Serviceberater aushelft.

---

## 🔎 ANALYSE

### 1. Walter Smola - Stempelungen (letzte 30 Tage)

**Top Aufträge nach Stempelzeit:**

| Order | Betrieb | Minuten | Stunden | Stempelungen | Zeitraum |
|-------|---------|---------|---------|--------------|----------|
| **300014** | ? | **5005** | **83.4** | 11 | 2025-12-22 - 2026-01-12 |
| 313410 | LAN | 924 | 15.4 | 3 | 2026-01-13 |
| 313618 | LAN | 921 | 15.4 | 6 | 2026-01-12 |
| 313634 | LAN | 719 | 12.0 | 10 | 2026-01-12 |
| 31 | DEG | 239 | 4.0 | 9 | 2026-01-12 - 2026-01-13 |

**Gesamt:** 8660 Min (144.3 Std)

### 2. Order 300014 - Leerlaufauftrag für Landau

**Eigenschaften:**
- ✅ **83.4 Stunden** Stempelzeit von Walter Smola (letzte 30 Tage)
- ✅ **Keine Arbeitspositionen** (labours) vorhanden
- ✅ **Keine Rechnungen** vorhanden
- ✅ **2 Mechaniker** stempeln darauf (Smola + Kerscher)
- ❌ **Auftrag existiert nicht mehr** in `orders`-Tabelle (gelöscht/archiviert)

**Stempelungen auf Order 300014 (letzte 30 Tage):**

| Mechaniker | Betrieb | Minuten | Stunden | Stempelungen |
|------------|---------|---------|---------|--------------|
| **Smola, Walter** (5003) | LAN | **5005** | **83.4** | 11 |
| Kerscher, Manuel (5011) | LAN | 13 | 0.2 | 1 |

**Gesamt:** 5018 Min (83.6 Std)

### 3. Problem-Identifikation

**Walter Smola:**
- ✅ Ist **Serviceberater** (2 Aufträge als Serviceberater in letzten 30 Tagen)
- ✅ Stempelt **83.4 Stunden** auf Leerlaufauftrag 300014
- ✅ Stempelt auch auf **echte Landau-Aufträge** (313410, 313618, etc.)
- ❌ **Keine verrechneten AW** auf Leerlaufauftrag → **Leistungsgrad = 0%** für diese Zeit

**Berechnung:**
- Stempelzeit: 144.3 Std (inkl. 83.4 Std Leerlauf)
- Verrechnete AW: ~13.6 AW (nur von echten Aufträgen)
- **Leistungsgrad = (13.6 AW × 6 Min) / (144.3 Std × 60 Min) × 100 = 9.4%** ✅

---

## 💡 LÖSUNG

### Option 1: Leerlaufaufträge aus Leistungsgrad-Berechnung ausschließen

**Aktuell:** `order_number > 31` (schließt nur Order 31 aus)

**Vorschlag:** Alle Aufträge ohne `labours` aus Stempelzeit-Berechnung ausschließen:

```sql
-- In get_mechaniker_leistung():
WHERE type = 2
  AND end_time IS NOT NULL
  AND order_number > 31
  AND EXISTS (
      SELECT 1 FROM labours l 
      WHERE l.order_number = t.order_number 
        AND l.time_units > 0
  )  -- Nur Aufträge mit verrechneten Arbeitspositionen
```

**Vorteil:**
- ✅ Leerlaufaufträge werden automatisch erkannt
- ✅ Keine manuelle Pflege von Leerlaufauftrags-Listen nötig
- ✅ Funktioniert für alle Standorte

**Nachteil:**
- ⚠️ Offene Aufträge (noch nicht abgerechnet) würden auch ausgeschlossen
- ⚠️ Möglicherweise zu restriktiv

### Option 2: Bekannte Leerlaufaufträge manuell ausschließen

**Vorschlag:** Liste von Leerlaufaufträgen pro Standort:

```python
LEERLAUF_AUFTRAEGE = {
    1: [31],      # Deggendorf
    2: [],        # Hyundai
    3: [300014]   # Landau
}
```

**Vorteil:**
- ✅ Kontrolle über ausgeschlossene Aufträge
- ✅ Offene Aufträge bleiben in Berechnung

**Nachteil:**
- ⚠️ Manuelle Pflege nötig
- ⚠️ Neue Leerlaufaufträge müssen manuell hinzugefügt werden

### Option 3: Leerlaufaufträge kennzeichnen und separat anzeigen

**Vorschlag:** Leerlaufaufträge in der Berechnung behalten, aber separat kennzeichnen:

```python
'leerlauf_min': int(m['leerlauf_min'] or 0),
'leerlauf_auftraege': [300014, ...]  # Liste der Leerlaufaufträge
```

**Vorteil:**
- ✅ Transparenz über Leerlaufzeit
- ✅ Serviceberater können ihre Zeit korrekt zuordnen

**Nachteil:**
- ⚠️ Leistungsgrad bleibt niedrig (gewollt?)

---

## 🎯 EMPFEHLUNG

**Option 2 + Option 3 kombiniert:**

1. **Bekannte Leerlaufaufträge ausschließen** (Order 31 für DEG, Order 300014 für LAN)
2. **Leerlaufzeit separat anzeigen** in Mechaniker-Details
3. **Serviceberater kennzeichnen** und optional aus Leistungsgrad-Ranking ausschließen

**Implementierung:**

```python
# In api/werkstatt_data.py
LEERLAUF_AUFTRAEGE_PRO_BETRIEB = {
    1: [31],      # Deggendorf
    2: [],        # Hyundai
    3: [300014]   # Landau
}

# In get_mechaniker_leistung():
leerlauf_filter = ""
if betrieb and betrieb in LEERLAUF_AUFTRAEGE_PRO_BETRIEB:
    leerlauf_liste = LEERLAUF_AUFTRAEGE_PRO_BETRIEB[betrieb]
    if leerlauf_liste:
        leerlauf_filter = f"AND t.order_number NOT IN ({','.join(map(str, leerlauf_liste))})"
```

---

## 📊 NÄCHSTE SCHRITTE

1. [ ] Leerlaufaufträge-Liste in `werkstatt_data.py` implementieren
2. [ ] Filter in `get_mechaniker_leistung()` anpassen
3. [ ] Leerlaufzeit separat in Mechaniker-Details anzeigen
4. [ ] Serviceberater-Option: Aus Leistungsgrad-Ranking ausschließen?
5. [ ] Test: Leistungsgrad von Walter Smola sollte steigen

---

## 🔗 VERWANDTE DOKUMENTE

- `docs/ANALYSE_STEMPELZEITEN_NOVEMBER_JAN_TAG185.md` - Stempelzeit-Analyse
- `api/werkstatt_data.py` - Stempelzeit-Berechnung (Zeile 291: `order_number > 31`)
