# Standort-Filter Fix - TAG 177

**Problem:** Standort-Tabs funktionieren nicht, weil API-Endpunkte den `location`/`standort` Parameter nicht akzeptieren oder nicht verwenden.

## Behobene Stellen

### ✅ Auftragseingang (`/verkauf/auftragseingang`)
- **Problem:** `get_auftragseingang()` und `get_auftragseingang_summary()` akzeptierten keinen `location` Parameter
- **Fix:**
  - `api/verkauf_data.py`: `get_auftragseingang()` erweitert um `location` Parameter
  - `api/verkauf_data.py`: `get_auftragseingang_summary()` erweitert um `location` Parameter
  - `api/verkauf_api.py`: Beide Endpunkte erweitert um `location` Parameter
  - `templates/verkauf_auftragseingang.html`: `loadSummary()` übergibt jetzt `location` Parameter

### ✅ Bereits OK (keine Änderung nötig)
- **GW Dashboard:** API akzeptiert bereits `standort` Parameter
- **KST-Ziele:** API akzeptiert bereits `standort` Parameter
- **Budget Wizard:** API akzeptiert bereits `standort` Parameter
- **Stundensatz-Kalkulation:** API akzeptiert bereits `standort` Parameter
- **TEK Dashboard:** API akzeptiert bereits `standort` Parameter (mit Firma-Ableitung)
- **Lieferforecast:** API akzeptiert bereits `standort` Parameter (mit Mapping)
- **Gesamtplanung:** Verwendet direkt DB-Queries mit Standort-Filter

## Server-Restart erforderlich

**Ja, Server-Restart erforderlich!**

Die Änderungen in `api/verkauf_data.py` und `api/verkauf_api.py` erfordern einen Neustart des Flask-Servers:

```bash
sudo systemctl restart greiner-portal
```

## Test-Checkliste

Nach Server-Restart testen:
1. ✅ Auftragseingang: Standort-Tabs filtern korrekt
2. ✅ GW Dashboard: Standort-Tabs filtern korrekt
3. ✅ KST-Ziele: Standort-Tabs filtern korrekt
4. ✅ Budget Wizard: Standort-Tabs filtern korrekt
5. ✅ Stundensatz-Kalkulation: Standort-Tabs filtern korrekt
6. ✅ TEK Dashboard: Standort-Tabs filtern korrekt (ohne Firma-Dropdown)
7. ✅ Lieferforecast: Standort-Tabs filtern korrekt
8. ✅ Gesamtplanung: Standort-Tabs filtern korrekt
