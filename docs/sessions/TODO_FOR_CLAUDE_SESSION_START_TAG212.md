# TODO für Claude - Session Start TAG 212

**Erstellt:** 2026-01-26  
**Letzte Session:** TAG 211 (Konsistente Deduplizierung von Stempelzeiten)

---

## 📋 Offene Aufgaben

### Aus vorherigen Sessions
- Keine kritischen offenen Aufgaben

### Neue Aufgaben (optional, niedrige Priorität)
1. **Monitoring: Deduplizierung überwachen** (optional)
   - Deduplizierung über längere Zeit beobachten
   - Prüfen ob Ergebnisse mit Locosoft übereinstimmen
   - Performance-Impact von `DISTINCT ON` prüfen

2. **Dokumentation: Weitere Beispiele** (optional)
   - Weitere Beispiele für Deduplizierung dokumentieren
   - Best Practices für Stempelzeiten-Abfragen dokumentieren

---

## 🔍 Qualitätsprobleme die behoben werden sollten

**Keine kritischen Qualitätsprobleme**

Die Deduplizierung ist jetzt konsistent implementiert. Alle Funktionen verwenden die gleiche Logik.

---

## 📝 Wichtige Hinweise für die nächste Session

### Was wurde in TAG 211 gemacht
- ✅ Konsistente Deduplizierung für alle Stempelzeiten-Funktionen implementiert
- ✅ Alle KPI-Berechnungen verwenden jetzt: `DISTINCT ON (employee_number, order_number, start_time, end_time)`
- ✅ API-Endpunkte korrigiert (werkstatt_soap_api, arbeitskarte_api, garantie_auftraege_api)
- ✅ CTEs korrigiert (unique_times in werkstatt_data.py und werkstatt_live_api.py)
- ✅ Service getestet und funktioniert

### Wichtige Dateien
- `api/werkstatt_data.py` - Hauptfunktionen für Stempelzeit-Berechnungen
- `api/werkstatt_soap_api.py` - API-Endpunkt für Stempelzeiten-Status
- `api/arbeitskarte_api.py` - Arbeitskarte mit Stempelzeiten
- `api/garantie_auftraege_api.py` - Garantie-Aufträge mit Stempelzeiten-Count

### Bekannte Issues
- Keine kritischen Issues
- Deduplizierung ist konsistent implementiert

### Deduplizierungslogik
**Standard für alle Stempelzeiten-Abfragen:**
```sql
DISTINCT ON (employee_number, order_number, start_time, end_time)
```

**Regel:** Sekundengleiche Stempelzeiten desselben Mechanikers auf demselben Auftrag werden nur einmal gezählt.

---

## 🎯 Nächste Prioritäten

1. **User-Requests** - Warte auf neue Anforderungen
2. **Monitoring** - Optional: Deduplizierung überwachen
3. **Dokumentation** - Optional: Weitere Beispiele dokumentieren

---

## 📚 Relevante Dokumentation

- `docs/sessions/SESSION_WRAP_UP_TAG211.md` - Letzte Session-Dokumentation
- `api/werkstatt_data.py` - Stempelzeit-Berechnungsfunktionen
- `docs/BEISPIEL_AUFTRAGE_MEHRFACHSTEMPELUNG.md` - Beispiel für Mehrfachstempelung
- `docs/UMFASSENDE_ANALYSE_LOCOSOFT_ZEITERFASSUNG_ENTSCHLUESSELUNG.md` - Locosoft-Analyse

---

**Status:** ✅ Bereit für nächste Session  
**Nächste TAG:** 212
