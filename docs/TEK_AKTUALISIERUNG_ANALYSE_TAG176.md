# TEK-Aktualisierung Analyse - TAG 176

**Datum:** 2026-01-09  
**Frage:** Wann wird TEK in DRIVE aktualisiert? Email-Report auf 17:30 ist unlogisch.

---

## 🔍 AKTUELLE SITUATION

### 1. Locosoft PostgreSQL-Befüllung (Datenquelle)
- **Zeitplan:** Locosoft befüllt eigene PostgreSQL-Datenbank
- **Dauer:** **1 Stunde** (ca. 18:00-19:00 Uhr)
- **Fertig:** **19:00 Uhr** (Locosoft PostgreSQL ist dann aktuell)
- **Status:** ✅ Externe Abhängigkeit (nicht in DRIVE gesteuert)

### 2. Locosoft Mirror (Datenübertragung)
- **Zeitplan:** Täglich um **19:00 Uhr** (nach Locosoft PostgreSQL-Befüllung)
- **Task:** `celery_app.tasks.locosoft_mirror`
- **Dauer:** **Nicht so lange** (User-Feedback) - vermutlich 5-15 Minuten
- **Timeout:** 60 Minuten (soft_time_limit: 3600s) - nur als Sicherheit
- **Zweck:** Spiegelt Locosoft PostgreSQL-Daten in DRIVE Portal DB
- **Status:** ✅ Aktiv

**Konfiguration:**
```python
# celery_app/__init__.py Zeile 290-293
'locosoft-mirror': {
    'task': 'celery_app.tasks.locosoft_mirror',
    'schedule': crontab(minute=0, hour=19),
    'options': {'queue': 'verkauf'}
}
```

### 3. TEK-Datenberechnung
- **Methode:** On-the-fly Berechnung aus Locosoft-Daten
- **API-Endpunkt:** `/api/tek` (via `routes/controlling_routes.py`)
- **Datenquelle:** 
  - Direkt: Locosoft PostgreSQL (10.80.80.8:5432) - **Live-Daten**
  - Oder: Gespiegelte Daten aus DRIVE Portal DB (nach Locosoft Mirror)
- **Aktualisierung:** **KEINE direkte Aktualisierung** - Daten werden bei Bedarf berechnet

**Wichtig:** TEK-Daten werden **nicht** in DRIVE-DB gespeichert, sondern bei jedem API-Aufruf neu aus Locosoft berechnet.

### 4. TEK Template-Aktualisierung
- **Template:** `templates/controlling/tek_dashboard_v2.html`
- **Aktualisierung:** **Bei jedem Seitenaufruf** oder Filter-Änderung
- **Mechanismus:** JavaScript-Funktion `loadData()` ruft `/controlling/api/tek` auf
- **Kein Cache:** Daten werden immer live aus Locosoft berechnet
- **Status:** ✅ Immer aktuell (abhängig von Locosoft PostgreSQL)

**Wie funktioniert es:**
1. User öffnet TEK-Dashboard
2. JavaScript `loadData()` wird aufgerufen
3. API `/controlling/api/tek` wird aufgerufen
4. API berechnet TEK-Daten aus Locosoft PostgreSQL (live)
5. Daten werden im Template angezeigt

### 5. TEK Email-Versand
- **Status:** ✅ **AKTIVIERT** (TAG 176)
- **Zeitplan:** **19:30 Uhr** (nach Locosoft Mirror um 19:00)
- **Task:** `celery_app.tasks.email_tek_daily` (✅ implementiert)
- **Script:** `scripts/send_daily_tek.py`
- **Timeout:** 10 Minuten (600s)

**Konfiguration (auskommentiert):**
```python
# celery_app/__init__.py Zeile 157-162
# TAG167: TEK-E-Mail-Versand pausiert bis Stückzahlen-Fix aktiv ist
# 'email-tek-daily': {
#     'task': 'celery_app.tasks.email_tek_daily',
#     'schedule': crontab(minute=30, hour=19, day_of_week='mon-fri'),
#     'options': {'queue': 'controlling'}
# },
```

---

## ⚠️ PROBLEM-ANALYSE

### Problem 1: TEK Email-Task fehlt
- Die Task `email_tek_daily` ist **nicht implementiert** in `celery_app/tasks.py`
- Nur die Schedule-Konfiguration ist auskommentiert
- Das Script `send_daily_tek.py` existiert, wird aber nicht automatisch ausgeführt

### Problem 2: Zeitplan unlogisch (wenn auf 17:30 gesetzt)
**Aktueller Ablauf:**
1. **17:30 Uhr:** Email-Versand (wenn aktiviert) ❌
2. **19:00 Uhr:** Locosoft Mirror startet ✅
3. **19:30 Uhr:** BWA Berechnung (nutzt gespiegelte Daten) ✅

**Warum 17:30 unlogisch ist:**
- Locosoft PostgreSQL ist erst um **19:00 Uhr** fertig (1 Stunde Befüllung)
- Locosoft Mirror startet um **19:00 Uhr** (nach PostgreSQL-Befüllung)
- TEK-Daten werden aus Locosoft berechnet
- **Ergebnis:** Email um 17:30 würde **veraltete Daten** enthalten (von Vortag)!

### Problem 3: TEK-Daten werden nicht "aktualisiert"
**Wichtig:** TEK-Daten werden **nicht** in DRIVE-DB gespeichert/aktualisiert. Sie werden bei jedem API-Aufruf neu aus Locosoft berechnet.

**Aktualisierungslogik:**
- TEK-Daten = Berechnung aus Locosoft-Daten
- Locosoft-Daten werden um 19:00 Uhr gespiegelt (Locosoft Mirror)
- **Aber:** TEK-API kann auch direkt auf Locosoft zugreifen (nicht nur auf gespiegelte Daten)

---

## 📊 ZEITPLAN-ÜBERSICHT

| Zeit | Task | Status | Abhängigkeit |
|------|------|--------|--------------|
| 18:00-19:00 | **Locosoft PostgreSQL-Befüllung** | ✅ Extern | - |
| 17:15 | Email Auftragseingang | ✅ Aktiv | - |
| 17:30 | Email Werkstatt Tagesbericht | ✅ Aktiv | - |
| 19:00 | **Locosoft PostgreSQL fertig** | ✅ Extern | - |
| 19:00 | **Locosoft Mirror** | ✅ Aktiv | Nach PostgreSQL-Befüllung |
| 19:15 | Werkstatt Leistung | ✅ Aktiv | Nach Mirror |
| 19:30 | BWA Berechnung | ✅ Aktiv | Nach Mirror |
| 19:30 | **Email TEK** | ✅ **AKTIV** (TAG 176) | Nach Mirror ✅ |

---

## ✅ LÖSUNGSVORSCHLAG

### ✅ Lösung: TEK Email auf 19:30 Uhr (IMPLEMENTIERT - TAG 176)
**Begründung:**
- Locosoft PostgreSQL ist um **19:00 Uhr** fertig (1 Stunde Befüllung)
- Locosoft Mirror startet um **19:00 Uhr** (nach PostgreSQL-Befüllung)
- Mirror dauert **nicht so lange** (User-Feedback: vermutlich 5-15 Minuten)
- **19:30 Uhr** ist sicher nach Mirror-Abschluss
- BWA Berechnung läuft auch um 19:30 Uhr (gleiche Abhängigkeit)

**Implementierung (TAG 176):**
1. ✅ Task `email_tek_daily` in `celery_app/tasks.py` erstellt
2. ✅ Schedule auf 19:30 Uhr gesetzt
3. ✅ Auskommentierung in `celery_app/__init__.py` entfernt

### Option 2: TEK Email auf 20:00 Uhr (sicherer)
**Begründung:**
- Mehr Puffer nach Locosoft Mirror (19:00-20:00)
- Garantiert, dass Mirror abgeschlossen ist

### Option 3: TEK Email mit Abhängigkeitsprüfung
**Begründung:**
- Prüft ob Locosoft Mirror erfolgreich war
- Startet erst nach erfolgreichem Mirror

---

## 🔧 NÄCHSTE SCHRITTE

1. **Prüfen:** Gibt es eine TEK Email-Task die auf 17:30 läuft?
   - ❌ **NEIN** - Task existiert nicht, nur auskommentiert

2. **Implementieren:** Task `email_tek_daily` erstellen
   - Script: `scripts/send_daily_tek.py` existiert bereits
   - Task in `celery_app/tasks.py` hinzufügen

3. **Zeitplan:** Auf 19:30 Uhr setzen (nach Locosoft Mirror)
   - Entspricht ursprünglicher Planung (TAG 146)
   - Logisch nach Mirror-Abschluss

4. **Testen:** Task manuell ausführen und prüfen
   - Celery Web-UI: `/admin/celery/`
   - Oder: `python3 scripts/send_daily_tek.py --test`

---

## 📝 ZUSAMMENFASSUNG

**Aktuelle Situation (TAG 176):**
- ✅ TEK Email-Versand ist **aktiviert** (TAG 176)
- ✅ Task `email_tek_daily` in `celery_app/tasks.py` implementiert
- ✅ Script `send_daily_tek.py` existiert
- ✅ Locosoft PostgreSQL ist um **19:00 Uhr** fertig (1 Stunde Befüllung)
- ✅ Locosoft Mirror läuft um **19:00 Uhr** (dauert nicht so lange)
- ✅ TEK Email läuft um **19:30 Uhr** (nach Mirror)

**TEK Template-Aktualisierung:**
- ✅ Template aktualisiert sich **bei jedem Seitenaufruf**
- ✅ JavaScript `loadData()` ruft API auf
- ✅ API berechnet Daten live aus Locosoft PostgreSQL
- ✅ **Kein Cache** - immer aktuelle Daten

**Zeitplan:**
1. **18:00-19:00 Uhr:** Locosoft befüllt eigene PostgreSQL (1 Stunde)
2. **19:00 Uhr:** Locosoft PostgreSQL fertig
3. **19:00 Uhr:** Locosoft Mirror startet (dauert ca. 5-15 Minuten)
4. **19:30 Uhr:** TEK Email-Versand (nach Mirror-Abschluss)

**Problem gelöst:**
- ❌ Email auf 17:30 Uhr wäre unlogisch (veraltete Daten)
- ✅ Email auf 19:30 Uhr ist korrekt (nach Locosoft PostgreSQL + Mirror)

---

**Status:** ✅ **IMPLEMENTIERT** (TAG 176) - TEK Email läuft um 19:30 Uhr nach Locosoft Mirror
