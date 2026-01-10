# Standort-Filter Migration - Status TAG 177

**Datum:** 2026-01-10  
**Zweck:** Zentrale Tab-Navigation für Standort-Filter

---

## ✅ Abgeschlossen (8 Features)

1. **GW Dashboard** - Standort-Tabs implementiert
2. **Gesamtplanung** - Standort-Tabs implementiert
3. **KST-Ziele** - Standort-Tabs implementiert
4. **Budget Wizard** - Standort-Tabs implementiert (Button → Tabs)
5. **Lieferforecast** - Standort-Tabs implementiert
6. **Stundensatz-Kalkulation** - Standort-Tabs implementiert
7. **Auftragseingang** - Standort-Tabs implementiert + API erweitert
8. **TEK Dashboard V2** - Standort-Tabs implementiert (Firma-Dropdown entfernt, automatische Ableitung)

---

## 🔄 Noch offen (3 Features)

### Controlling (2)
- **BWA** - Firma + Standort (Dropdowns → Tabs)
- **Unternehmensplan** - Firma + Standort (Dropdowns → Tabs)

### Werkstatt/After Sales (1)
- **Werkstatt-Features** (8 Features) - `betrieb` statt `standort`
  - Component muss erweitert werden für `betrieb`-Parameter
  - Nur Betrieb 1 (Deggendorf) und 3 (Landau), kein Betrieb 2

---

## 📋 Technische Details

### Zentrale Komponenten
- **Component:** `templates/components/standort_filter_tabs.html`
- **Helper:** `utils/standort_filter_helpers.py`
- **SSOT:** `api/standort_utils.py`

### Konsistente Tab-Namen
- Deggendorf Opel
- Deggendorf Hyundai
- Landau Opel
- Deggendorf konsolidiert (für Standort 1+2 zusammen)

### API-Erweiterungen
- `api/verkauf_data.py`: `get_auftragseingang()` und `get_auftragseingang_summary()` erweitert um `location` Parameter
- `api/verkauf_api.py`: Beide Endpunkte erweitert

---

## 🎯 Nächste Schritte

1. **BWA migrieren** - Firma-Dropdown entfernen, Standort-Tabs mit automatischer Firma-Ableitung
2. **Unternehmensplan migrieren** - Gleiche Logik wie BWA
3. **Component erweitern** - `betrieb`-Parameter für Werkstatt-Features
4. **Werkstatt-Features migrieren** - 8 Features auf Tab-Navigation umstellen

---

**Status:** 8/11 Features migriert (73%)
