# Refactoring-Plan: KPI-Berechnung TAG 194

**Datum:** 2026-01-16  
**Zweck:** Aufteilung der komplexen `get_mechaniker_leistung()` Query in kleinere, wartbare Funktionen

---

## Problem

1. **Query-Komplexität:** 283 Zeilen, 20+ CTEs, schwer wartbar
2. **Parameter-Problem:** `IndexError: list index out of range` trotz korrekter Parameter-Anzahl
3. **Wartbarkeit:** Änderungen sind riskant, schwer zu testen
4. **Performance:** Eine große Query ist nicht immer optimal

---

## Lösung: Refactoring in separate Funktionen

### Architektur

```
get_mechaniker_leistung()
├── get_stempelungen_dedupliziert(von, bis) → List[Dict]
├── get_stempelzeit_locosoft(von, bis) → Dict[employee_number, stempelzeit]
├── get_stempelzeit_leistungsgrad(von, bis) → Dict[employee_number, stempelzeit]
├── get_stempelungen_roh(von, bis) → List[Dict] (position-basiert)
├── get_aw_verrechnet(von, bis) → Dict[employee_number, {aw, umsatz}]
├── get_anwesenheit(von, bis) → Dict[employee_number, {tage, anwesenheit}]
└── berechne_kpis_python(rohdaten) → Dict[employee_number, KPIs]
```

### Vorteile

1. **Einfachere Queries:** Jede Funktion hat 1-3 CTEs, max. 50 Zeilen
2. **Keine Parameter-Probleme:** Jede Query hat eigene Parameter-Liste
3. **Bessere Testbarkeit:** Einzelne Funktionen können isoliert getestet werden
4. **Wiederverwendbarkeit:** Funktionen können in anderen Kontexten genutzt werden
5. **KPI-Berechnung in Python:** Nutzt `utils/kpi_definitions.py` (SSOT)

---

## Implementierungsplan

### Phase 1: Separate Daten-Funktionen

#### 1.1 `get_stempelungen_dedupliziert(von, bis)`
```python
def get_stempelungen_dedupliziert(von: date, bis: date) -> List[Dict]:
    """
    Holt deduplizierte Stempelungen (type=2) für Zeitraum.
    Returns: List mit {employee_number, datum, start_time, end_time, order_number}
    """
```

#### 1.2 `get_stempelzeit_locosoft(von, bis)`
```python
def get_stempelzeit_locosoft(von: date, bis: date) -> Dict[int, Dict]:
    """
    Berechnet Stempelzeit nach Locosoft-Logik (Zeit-Spanne - Lücken - Pausen).
    Returns: {employee_number: {tage, auftraege, stempel_min}}
    """
```

#### 1.3 `get_stempelzeit_leistungsgrad(von, bis)`
```python
def get_stempelzeit_leistungsgrad(von: date, bis: date) -> Dict[int, float]:
    """
    Berechnet Stempelzeit für Leistungsgrad (Summe aller gestempelten Zeiten).
    Returns: {employee_number: stempel_min_leistungsgrad}
    """
```

#### 1.4 `get_stempelungen_roh(von, bis)`
```python
def get_stempelungen_roh(von: date, bis: date) -> List[Dict]:
    """
    Holt position-basierte Stempelungen (TAG 194).
    Returns: List mit {employee_number, order_number, order_position, 
             order_position_line, start_time, end_time, stempel_minuten}
    """
```

#### 1.5 `get_aw_verrechnet(von, bis)`
```python
def get_aw_verrechnet(von: date, bis: date) -> Dict[int, Dict]:
    """
    Berechnet AW-Anteil und Umsatz pro Mechaniker (position-basiert, TAG 194).
    Returns: {employee_number: {aw, umsatz}}
    """
```

#### 1.6 `get_anwesenheit(von, bis)`
```python
def get_anwesenheit(von: date, bis: date) -> Dict[int, Dict]:
    """
    Holt Anwesenheitsdaten (type=1).
    Returns: {employee_number: {tage, anwesend_min}}
    """
```

### Phase 2: Hybrid-Ansatz für St-Anteil

#### 2.1 `berechne_st_anteil_hybrid(stempelzeit_locosoft, stempelungen_roh)`
```python
def berechne_st_anteil_hybrid(
    stempelzeit_locosoft: Dict[int, Dict],
    stempelungen_roh: List[Dict]
) -> Dict[int, float]:
    """
    Berechnet St-Anteil nach Hybrid-Ansatz:
    - Basis: Zeit-Spanne (aus stempelzeit_locosoft)
    - Plus: 10.6% der Stempelzeit für Positionen OHNE AW auf Aufträgen MIT AW
    
    Returns: {employee_number: stempel_min_hybrid}
    """
```

### Phase 3: KPI-Berechnung in Python

#### 3.1 `berechne_mechaniker_kpis_aus_rohdaten(rohdaten)`
```python
def berechne_mechaniker_kpis_aus_rohdaten(
    rohdaten: Dict[int, Dict]
) -> Dict[int, Dict]:
    """
    Berechnet alle KPIs für Mechaniker aus Rohdaten.
    Nutzt utils/kpi_definitions.py (SSOT).
    
    Args:
        rohdaten: {
            employee_number: {
                'tage': int,
                'auftraege': int,
                'stempelzeit': float,  # Minuten (Hybrid)
                'stempelzeit_leistungsgrad': float,  # Minuten
                'anwesenheit': float,  # Minuten
                'aw': float,  # Stunden
                'umsatz': float  # EUR
            }
        }
    
    Returns:
        {
            employee_number: {
                'leistungsgrad': float,
                'produktivitaet': float,
                'anwesenheitsgrad': float,
                'auslastungsgrad': float,
                ...
            }
        }
    """
```

### Phase 4: Hauptfunktion refactoren

#### 4.1 `get_mechaniker_leistung()` (neu)
```python
@staticmethod
def get_mechaniker_leistung(
    von: date,
    bis: date,
    mechaniker_nr: Optional[int] = None,
    betrieb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Hauptfunktion - holt Daten und berechnet KPIs.
    """
    # 1. Hole Rohdaten (parallel möglich)
    stempelzeit_locosoft = get_stempelzeit_locosoft(von, bis)
    stempelzeit_leistungsgrad = get_stempelzeit_leistungsgrad(von, bis)
    stempelungen_roh = get_stempelungen_roh(von, bis)
    aw_verrechnet = get_aw_verrechnet(von, bis)
    anwesenheit = get_anwesenheit(von, bis)
    
    # 2. Berechne St-Anteil (Hybrid)
    st_anteil_hybrid = berechne_st_anteil_hybrid(
        stempelzeit_locosoft, 
        stempelungen_roh
    )
    
    # 3. Aggregiere Rohdaten
    rohdaten = aggregiere_rohdaten(
        stempelzeit_locosoft,
        st_anteil_hybrid,
        stempelzeit_leistungsgrad,
        aw_verrechnet,
        anwesenheit
    )
    
    # 4. Berechne KPIs (Python)
    kpis = berechne_mechaniker_kpis_aus_rohdaten(rohdaten)
    
    # 5. Hole Mechaniker-Details (employees_history)
    mechaniker_details = get_mechaniker_details(list(rohdaten.keys()))
    
    # 6. Kombiniere und filtere
    result = kombiniere_ergebnisse(rohdaten, kpis, mechaniker_details)
    
    return result
```

---

## Migration

### Schritt 1: Neue Funktionen erstellen
- [ ] Erstelle `get_stempelungen_dedupliziert()`
- [ ] Erstelle `get_stempelzeit_locosoft()`
- [ ] Erstelle `get_stempelzeit_leistungsgrad()`
- [ ] Erstelle `get_stempelungen_roh()`
- [ ] Erstelle `get_aw_verrechnet()`
- [ ] Erstelle `get_anwesenheit()`

### Schritt 2: Hybrid-Ansatz implementieren
- [ ] Erstelle `berechne_st_anteil_hybrid()`
- [ ] Teste gegen aktuelle Implementierung

### Schritt 3: KPI-Berechnung
- [ ] Erstelle `berechne_mechaniker_kpis_aus_rohdaten()`
- [ ] Nutze `utils/kpi_definitions.py`

### Schritt 4: Hauptfunktion refactoren
- [ ] Refactore `get_mechaniker_leistung()`
- [ ] Teste gegen aktuelle Implementierung
- [ ] Vergleiche Ergebnisse

### Schritt 5: Alte Implementierung entfernen
- [ ] Entferne alte Query
- [ ] Entferne alte Parameter-Liste
- [ ] Cleanup

---

## Vorteile des Refactorings

1. **Wartbarkeit:** Jede Funktion ist < 50 Zeilen, leicht zu verstehen
2. **Testbarkeit:** Einzelne Funktionen können isoliert getestet werden
3. **Performance:** Kleinere Queries können besser optimiert werden
4. **Wiederverwendbarkeit:** Funktionen können in anderen Kontexten genutzt werden
5. **KPI-Berechnung:** Nutzt SSOT (`utils/kpi_definitions.py`)
6. **Parameter-Probleme:** Jede Query hat eigene Parameter-Liste, keine Konflikte

---

## Risiken

1. **Performance:** Mehrere Queries statt einer großen Query
   - **Mitigation:** Queries können parallel ausgeführt werden
   - **Mitigation:** Kleinere Queries sind oft schneller

2. **Konsistenz:** Daten könnten zwischen Queries ändern
   - **Mitigation:** Alle Queries verwenden denselben Zeitraum
   - **Mitigation:** Transaktionen wenn nötig

3. **Migration:** Alte Implementierung muss parallel laufen
   - **Mitigation:** Feature-Flag für alte/neue Implementierung
   - **Mitigation:** Vergleichstests

---

## Nächste Schritte

1. ✅ Refactoring-Plan erstellt
2. ⏳ Benutzer-Feedback einholen
3. ⏳ Phase 1 starten (separate Daten-Funktionen)

---

**Status:** 📋 **BEREIT FÜR IMPLEMENTIERUNG**
