# TODO für Claude - Session Start TAG 211

**Erstellt:** 2026-01-26  
**Letzte Session:** TAG 210 (Task Manager Historie-Fix)

---

## 📋 Offene Aufgaben

### Aus vorherigen Sessions
- Keine kritischen offenen Aufgaben

### Neue Aufgaben (optional, niedrige Priorität)
1. **Redis-Client zentralisieren** (optional)
   - Aktuell: Redis-Client wird direkt in Signal-Handler und Routes erstellt
   - Verbesserung: Utility-Funktion `get_redis_client()` in `api/db_utils.py` oder `celery_app/__init__.py`
   - **Niedrige Priorität** (funktioniert aktuell)

2. **Frontend-Test: Historie-Anzeige** (optional)
   - API funktioniert, Frontend sollte Historie jetzt anzeigen
   - Browser-Refresh auf `/admin/celery/` prüfen
   - Bei automatischen Ausführungen: Historie erscheint nach nächstem Schedule-Lauf

---

## 🔍 Qualitätsprobleme die behoben werden sollten

### Niedrige Priorität
1. **Redis-Client könnte zentralisiert werden**
   - Dateien: `celery_app/__init__.py`, `celery_app/routes.py`
   - Aktuell: Direkte Redis-Client-Erstellung
   - Verbesserung: Utility-Funktion für bessere Wartbarkeit

---

## 📝 Wichtige Hinweise für die nächste Session

### Was wurde in TAG 210 gemacht
- ✅ Task Manager Historie-Fix implementiert
- ✅ Celery Signal-Handler hinzugefügt (`task_prerun`)
- ✅ Historie-API verbessert (flexiblere Task-Name-Erkennung)
- ✅ Services getestet und funktionieren

### Wichtige Dateien
- `celery_app/__init__.py` - Signal-Handler für Task-Name-Mapping
- `celery_app/routes.py` - Verbesserte Historie-API

### Bekannte Issues
- Keine kritischen Issues
- Redis-Client könnte zentralisiert werden (niedrige Priorität)

---

## 🎯 Nächste Prioritäten

1. **User-Requests** - Warte auf neue Anforderungen
2. **Qualitätsverbesserungen** - Optional: Redis-Client zentralisieren
3. **Frontend-Test** - Optional: Historie-Anzeige im Browser prüfen

---

## 📚 Relevante Dokumentation

- `docs/sessions/SESSION_WRAP_UP_TAG210.md` - Letzte Session-Dokumentation
- `celery_app/__init__.py` - Signal-Handler-Implementierung
- `celery_app/routes.py` - Historie-API-Implementierung

---

**Status:** ✅ Bereit für nächste Session  
**Nächste TAG:** 211
