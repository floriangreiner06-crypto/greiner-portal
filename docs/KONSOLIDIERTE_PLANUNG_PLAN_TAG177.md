# Konsolidierte Planung - Implementierungsplan TAG 177

**Datum:** 2026-01-10  
**Zweck:** Bug-Fix + Konsolidierte Ansicht für "Service Deggendorf"

---

## 🎯 ANFORDERUNGEN

1. **Bug-Fix:** Standort 3 (Landau) = subsidiary 3 (nicht 1!)
2. **Konsolidierte Ansicht:** "Service Deggendorf" = Standort 1 (Opel) + Standort 2 (Hyundai) zusammen

---

## 📋 IMPLEMENTIERUNGS-PLAN

### Phase 1: Bug-Fix (Standort 3 = subsidiary 3)

**Betroffene Dateien:**
- `api/abteilungsleiter_planung_data.py` (5 Stellen)

**Änderungen:**
- Zeile 1130: `o.subsidiary = 1` → `o.subsidiary = 3`
- Zeile 1141: `out_subsidiary = 1` → `out_subsidiary = 3`
- Zeile 1270: `out_subsidiary = 1` → `out_subsidiary = 3`
- Zeile 1308: `out_subsidiary = 1` → `out_subsidiary = 3`
- Zeile 1390: `o.subsidiary = 1` → `o.subsidiary = 3`
- Kommentare aktualisieren

**Verwendung:**
- Statt hardcoded Filter: `build_locosoft_filter_*()` aus `standort_utils.py` verwenden

---

### Phase 2: Konsolidierte Ansicht hinzufügen

#### 2.1 Standort-Utils erweitern

**Neue Funktionen in `api/standort_utils.py`:**

```python
def get_standorte_fuer_bereich(bereich: str, konsolidiert: bool = False) -> Dict[int, str]:
    """
    Gibt verfügbare Standorte für einen Bereich zurück (UI-Filter).
    
    Args:
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
        konsolidiert: True = konsolidierte Ansicht (Service Deggendorf = 1+2)
    
    Returns:
        {1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau'}  # normal
        {0: 'Service Deggendorf', 1: 'Deggendorf Opel', 2: 'Deggendorf Hyundai', 3: 'Landau'}  # konsolidiert
        {1: 'Deggendorf Opel', 3: 'Landau'}  # für Teile/Werkstatt (ohne 2)
    """
    if bereich in ['Teile', 'Werkstatt']:
        if konsolidiert:
            return {0: 'Service Deggendorf', 1: 'Deggendorf Opel', 3: 'Landau'}
        else:
            return {1: STANDORT_NAMEN[1], 3: STANDORT_NAMEN[3]}
    else:
        if konsolidiert:
            return {0: 'Service Deggendorf', 1: STANDORT_NAMEN[1], 2: STANDORT_NAMEN[2], 3: STANDORT_NAMEN[3]}
        else:
            return STANDORT_NAMEN

def build_consolidated_filter(standort: int, bereich: str) -> str:
    """
    Baut Filter für konsolidierte Ansicht (Standort 0 = Service Deggendorf = 1+2).
    
    Args:
        standort: 0 = konsolidiert (1+2), 1, 2, oder 3
        bereich: 'NW', 'GW', 'Teile', 'Werkstatt', 'Sonstige'
    
    Returns:
        SQL WHERE-Clause für konsolidierte Ansicht
    """
    if standort == 0:
        # Service Deggendorf = Standort 1 + 2 zusammen
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            return "AND (o.subsidiary = 1 OR o.subsidiary = 2)"
        else:
            return "AND (out_subsidiary = 1 OR out_subsidiary = 2)"
    else:
        # Normale Filter-Logik
        if bereich in ['Werkstatt', 'Teile', 'Sonstige']:
            return build_locosoft_filter_orders(standort)
        else:
            return build_locosoft_filter_verkauf(standort, nur_stellantis=False)
```

#### 2.2 Routes anpassen

**`routes/planung_routes.py`:**

```python
# Query-Parameter für konsolidierte Ansicht
konsolidiert = request.args.get('konsolidiert', type=bool, default=False)

# Standorte mit konsolidierter Option
standorte = get_standorte_fuer_bereich(bereich, konsolidiert=konsolidiert)
```

#### 2.3 Template anpassen

**`templates/planung/abteilungsleiter_uebersicht.html`:**

- Checkbox/Toggle für "Konsolidierte Ansicht"
- Wenn aktiv: Standort 0 ("Service Deggendorf") in Dropdown anzeigen
- Bei Standort 0: Daten von Standort 1 + 2 zusammenfassen

---

## 🔧 KONKRETE UMSETZUNG

### Option A: Standort 0 für konsolidiert

**Vorteile:**
- Einfach zu implementieren
- Klare Trennung (0 = konsolidiert, 1-3 = einzelne Standorte)

**Nachteile:**
- Standort 0 ist nicht intuitiv
- Muss in DB-Schema berücksichtigt werden

### Option B: Query-Parameter `konsolidiert=true`

**Vorteile:**
- Keine DB-Änderungen nötig
- Flexibler (kann für verschiedene Bereiche unterschiedlich sein)

**Nachteile:**
- Zusätzlicher Parameter
- Logik etwas komplexer

### Option C: Spezieller Standort-Name "Service Deggendorf"

**Vorteile:**
- Intuitiv
- Kann als virtueller Standort behandelt werden

**Nachteile:**
- Muss in UI und Backend konsistent sein

---

## 🎯 EMPFOHLENE LÖSUNG

**Option B + C kombiniert:**
- Query-Parameter `konsolidiert=true` für Backend-Logik
- UI zeigt "Service Deggendorf" als Option (virtueller Standort)
- Bei konsolidiert=true: Standort 1+2 werden zusammen abgefragt und summiert

**Beispiel:**
```
/planung/abteilungsleiter?bereich=Werkstatt&konsolidiert=true
→ Zeigt "Service Deggendorf" (Standort 1+2 zusammen)
→ Filter: subsidiary IN (1, 2)
→ Daten werden summiert
```

---

## 📊 UI-ÄNDERUNGEN

### Dropdown-Optionen (mit konsolidiert=true):

| Bereich | Standorte (normal) | Standorte (konsolidiert) |
|---------|-------------------|--------------------------|
| **NW** | 1, 2, 3 | 0 (Service DEG), 1, 2, 3 |
| **GW** | 1, 2, 3 | 0 (Service DEG), 1, 2, 3 |
| **Teile** | 1, 3 | 0 (Service DEG), 1, 3 |
| **Werkstatt** | 1, 3 | 0 (Service DEG), 1, 3 |
| **Sonstige** | 1, 2, 3 | 0 (Service DEG), 1, 2, 3 |

**"Service Deggendorf" (Standort 0):**
- Name: "Service Deggendorf" oder "Deggendorf (konsolidiert)"
- Filter: Standort 1 + 2 zusammen
- Daten: Summe von Standort 1 + 2

---

## 🚨 WICHTIGE HINWEISE

1. **Bug-Fix zuerst:** Standort 3 muss auf subsidiary=3 korrigiert werden
2. **Konsolidierte Ansicht:** Nur für Anzeige, nicht für Planung-Erstellung
3. **Daten-Integrität:** Bei konsolidierter Ansicht werden Daten summiert, nicht gespeichert
4. **Rückwärtskompatibilität:** Bestehende Planungen müssen weiterhin funktionieren

---

**Status:** ✅ Plan erstellt - Bereit für Implementierung
