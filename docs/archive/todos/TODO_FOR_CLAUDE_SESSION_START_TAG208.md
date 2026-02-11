# TODO für Claude - Session Start TAG 208

**Erstellt:** 2026-01-22  
**Letzte Session:** TAG 207  
**Fokus:** Bug-Fixes abgeschlossen, optional: Verfeinerungen

---

## 🎯 Hauptziel dieser Session

**Offene Aufgaben und Verbesserungen**

---

## ✅ Abgeschlossen in TAG 207

1. ✅ **Task-Dashboard Laufzeiten** - Funktioniert jetzt
2. ✅ **ML-Task** - Zeigt Warnung statt Fehler
3. ✅ **ServiceBox Kundeninformationen** - Werden korrekt extrahiert und angezeigt

---

## 📋 Optionale Verbesserungen

### PRIO 1: Kundenname-Extraktion verfeinern ⭐

**Problem:**
- Bei einigen Bestellungen ist noch die lokale Bestellnummer im Kundenname enthalten
- Beispiel: "Weber Aholming 1061978 liefern" statt nur "Weber Aholming"

**Lösung:**
- Regex-Patterns optimieren
- Lokale Bestellnummer am Ende besser entfernen
- Prüfen ob Zahl am Ende eine lokale Bestellnummer ist (4-7 Stellen)

**Dateien:**
- `tools/scrapers/servicebox_api_scraper.py` (Zeile 492-499)

### PRIO 2: ML-Task Script erstellen ⭐

**Problem:**
- Script `scripts/ml/retrain.py` existiert nicht
- Task zeigt Warnung, aber läuft nicht wirklich

**Lösung Option A:**
- Script `scripts/ml/retrain.py` erstellen
- Ruft `train_auftragsdauer_model_v2.py` auf

**Lösung Option B:**
- Task direkt auf `train_auftragsdauer_model_v2.py` umstellen
- Oder Task deaktivieren wenn nicht benötigt

**Dateien:**
- `celery_app/tasks.py` (Zeile 1841-1888)
- `scripts/ml/retrain.py` (neu erstellen, falls Option A)

### PRIO 3: Task-Dashboard erweitern ⭐

**Verbesserungen:**
- Historie-Grafik hinzufügen
- Mehr als 5 Einträge anzeigen
- Filter nach Task-Status

**Dateien:**
- `templates/admin/celery_tasks.html`
- `celery_app/routes.py` (API-Endpoint erweitern)

---

## 🔍 Bekannte Issues

### ServiceBox Kundeninformationen
- ✅ Funktioniert grundsätzlich
- ⚠️ Kann noch verfeinert werden (lokale Bestellnummer entfernen)

### Task-Dashboard
- ✅ Laufzeiten werden angezeigt
- ⚠️ Könnte noch erweitert werden (Historie-Grafik)

### ML-Task
- ⚠️ Script existiert nicht
- ⚠️ Task zeigt Warnung, läuft aber nicht wirklich

---

## 📚 Referenzen

### Dokumentation
- `docs/sessions/SESSION_WRAP_UP_TAG207.md` - Diese Session
- `docs/ANALYSE_SERVICEBOX_TAG173.md` - ServiceBox Architektur

### Code-Dateien
- `tools/scrapers/servicebox_api_scraper.py` - ServiceBox Scraper
- `celery_app/routes.py` - Task-Dashboard API
- `celery_app/tasks.py` - Celery Tasks

---

## 💡 Wichtige Hinweise

1. **ServiceBox Kommentar-Feld:**
   - Format: "DE08250 Kundenname 1008603"
   - DE08250 = Händlernummer (nicht Kundenname!)
   - 1008603 = lokale Bestellnummer
   - Kundenname steht dazwischen

2. **Task-Historie:**
   - Celery speichert `duration` manchmal direkt in Metadaten
   - Fallback auf Berechnung nötig

3. **ML-Task:**
   - Aktuell: Warnung bei fehlendem Script
   - Sollte entweder Script erstellt oder Task angepasst werden

---

## 🎯 Erwartete Ergebnisse (falls Verbesserungen durchgeführt)

1. **Kundenname-Extraktion:**
   - Nur Kundenname, keine lokale Bestellnummer
   - Beispiel: "Weber Aholming" statt "Weber Aholming 1061978 liefern"

2. **ML-Task:**
   - Läuft korrekt oder ist deaktiviert
   - Keine Warnungen mehr

3. **Task-Dashboard:**
   - Historie-Grafik (optional)
   - Mehr Einträge anzeigen (optional)

---

**Status:** ⏳ Warten auf neue Aufgaben  
**Nächster Schritt:** Optionale Verbesserungen oder neue Features
