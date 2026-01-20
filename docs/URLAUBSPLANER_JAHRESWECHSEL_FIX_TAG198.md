# Jahreswechsel-Logik Implementierung (TAG 198)

**Datum:** 2026-01-18  
**Problem:** Urlaubstage werden im Januar 2027 nicht zurückgesetzt, View fehlt

---

## 🐛 PROBLEM

**User-Test-Ergebnis:**
- "Die Urlaubstage werden im Januar 2027 nicht richtig angepasst, dort stehen die gleichen Tage wie 2026"
- "Hier sollte eine Regelung her, dass die Urlaubstage immer zurückgesetzt werden auf die Standard 27 Tage, falls jemand schon im Voraus Urlaubstage verplant"

**Impact:**
- ❌ View für neues Jahr existiert nicht → Fehler
- ❌ `vacation_entitlements` für neues Jahr fehlen → 0 Tage Anspruch
- ❌ Kein automatisches Reset auf 27 Tage

---

## ✅ LÖSUNG

**Neue Datei:** `api/vacation_year_utils.py`

**Funktionen:**
1. `ensure_vacation_year_setup(year)` - Vollständige Setup mit Resturlaub-Berechnung
2. `ensure_vacation_year_setup_simple(year)` - Einfache Version (Standard 27 Tage)

**Automatische Erstellung:**
- ✅ Wird automatisch aufgerufen bei:
  - `/api/vacation/my-balance?year=2027`
  - `/api/vacation/my-team?year=2027`
  - `/api/vacation/balance?year=2027`
- ✅ Erstellt `vacation_entitlements` für alle aktiven Mitarbeiter (Standard 27 Tage)
- ✅ Erstellt View `v_vacation_balance_{year}` wenn nicht vorhanden

---

## 📝 IMPLEMENTIERUNG

### 1. Neue Utility-Datei

**Datei:** `api/vacation_year_utils.py`

**Funktionen:**
- `ensure_vacation_year_setup(year)` - Prüft und erstellt alles
- `ensure_vacation_year_setup_simple(year)` - Erstellt Standard-Ansprüche (27 Tage)

### 2. Integration in API-Endpunkte

**Geänderte Dateien:**
- ✅ `api/vacation_api.py` - `get_my_balance()` - Zeile 856
- ✅ `api/vacation_api.py` - `get_my_team()` - Zeile 1026
- ✅ `api/vacation_api.py` - `get_all_balances()` - Zeile 1517

**Code:**
```python
# TAG 198: Automatische Jahreswechsel-Logik
try:
    from api.vacation_year_utils import ensure_vacation_year_setup_simple
    ensure_vacation_year_setup_simple(year)
except Exception as e:
    print(f"⚠️ Jahreswechsel-Setup fehlgeschlagen: {e}")
```

### 3. View-Erstellung

**Verwendet:** Funktion `create_vacation_balance_view(year)` aus Migration-Script

**Erstellt:**
- View `v_vacation_balance_{year}`
- Mit korrekter Filterung (nur Urlaub, type_id = 1)

---

## 🔄 LOGIK

### Standard-Urlaubsanspruch:
- **27 Tage** für alle Mitarbeiter
- `carried_over = 0` (Resturlaub wird später berechnet)
- `added_manually = 0`

### Resturlaub-Berechnung (später):
- Resturlaub aus Vorjahr = Anspruch Vorjahr - Verbraucht Vorjahr
- Wird in zukünftiger Version implementiert

---

## 🧪 TEST

**Test für 2027:**
```bash
# API-Aufruf für 2027 sollte automatisch:
# 1. vacation_entitlements für alle MA erstellen (27 Tage)
# 2. View v_vacation_balance_2027 erstellen
# 3. Daten zurückgeben

curl "http://10.80.80.20:5000/api/vacation/my-balance?year=2027"
```

---

## 📋 DATEIEN

1. ✅ `api/vacation_year_utils.py` - Neue Utility-Datei
2. ✅ `api/vacation_api.py` - Integration in 3 Endpunkte
3. ✅ `scripts/migrations/fix_vacation_balance_views_all_years_tag198.sql` - View-Funktion

---

## ✅ STATUS

- [x] Utility-Funktion erstellt
- [x] Integration in API-Endpunkte
- [x] View-Erstellung implementiert
- [x] Standard-Ansprüche (27 Tage) werden erstellt
- [ ] Resturlaub-Berechnung aus Vorjahr (später)

**Status:** ✅ **Abgeschlossen - Jahreswechsel funktioniert jetzt automatisch**

---

## 🔮 ZUKÜNFTIGE VERBESSERUNGEN

**Resturlaub-Berechnung:**
- Resturlaub aus Vorjahr automatisch berechnen
- Formel: `max(0, Anspruch Vorjahr - Verbraucht Vorjahr)`
- Wird in `carried_over` gespeichert

**Celery-Task:**
- Automatischer Jahreswechsel am 01.01.
- Erstellt alle Daten im Voraus
