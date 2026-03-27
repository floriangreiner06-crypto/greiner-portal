# Urlaubsplaner: "undefined.undefined." Fix

**Datum:** 29.12.2025  
**Status:** ✅ Behoben

## Problem

Nach erfolgreicher Buchung wurde in der "Meine Anträge" Sidebar "undefined.undefined." angezeigt statt des Datums und Urlaubstyps.

## Ursache

PostgreSQL gibt `date`-Spalten als Python `date`-Objekte zurück, nicht als Strings. Das Frontend erwartet jedoch Strings im Format `YYYY-MM-DD`. Die API hat diese Objekte nicht konvertiert, was zu `undefined` im JavaScript führte.

## Lösung

Date-Objekte werden jetzt in allen relevanten Endpoints zu ISO-String (`YYYY-MM-DD`) konvertiert:

### Betroffene Endpoints:

1. **`/api/vacation/my-bookings`** (Zeile ~1739)
   - Konvertiert `booking_date` von Date-Objekt zu String
   - Konvertiert auch `created_at` falls vorhanden

2. **`/api/vacation/my-requests`** (Zeile ~1841)
   - Gleiche Konvertierung für `booking_date` und `created_at`

3. **`/api/vacation/all-bookings`** (Zeile ~1566)
   - Konvertiert `date` für alle Portal-Buchungen

### Code-Änderung:

```python
booking_date = row[1]
# TAG 136: Konvertiere Date-Objekt zu String (PostgreSQL gibt date zurück)
if hasattr(booking_date, 'isoformat'):
    booking_date = booking_date.isoformat()  # 'YYYY-MM-DD'
elif not isinstance(booking_date, str):
    booking_date = str(booking_date)
```

## Testing

✅ Buchung funktioniert  
✅ Datum wird korrekt angezeigt  
✅ Keine "undefined" Fehler mehr

## Verwandte Fixes

- [URLAUBSPLANER_POSTGRESQL_FIX_ZUSAMMENFASSUNG.md](./URLAUBSPLANER_POSTGRESQL_FIX_ZUSAMMENFASSUNG.md) - SQL Syntax Fixes
- [URLAUBSPLANER_FIX_FINAL.md](./URLAUBSPLANER_FIX_FINAL.md) - Übersicht aller Fixes

