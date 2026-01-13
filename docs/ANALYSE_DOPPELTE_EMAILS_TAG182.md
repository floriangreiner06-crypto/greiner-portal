# Analyse: Doppelte Auftragsüberschreitungs-E-Mails (TAG 182)

**Datum:** 2026-01-13  
**Problem:** Christian Meyer bekam über 80 E-Mails gestern (doppelte Mails)  
**Status:** ✅ Task deaktiviert

---

## 🔍 PROBLEM-ANALYSE

### Symptome
- Christian Meyer bekam über 80 E-Mails gestern
- Viele doppelte Mails für die gleichen Aufträge
- Task `benachrichtige_serviceberater_ueberschreitungen()` läuft alle 15 Minuten

### Identifizierte Ursachen

#### 1. **Keine Tracking-Tabelle für bereits gesendete E-Mails** ⚠️ HAUPTURSACHE

**Problem:**
- Die Task läuft alle 15 Minuten (Mo-Fr, 7-18 Uhr = ca. 40-44 Mal pro Tag)
- Es gibt **KEINE Prüfung**, ob bereits eine E-Mail für einen Auftrag heute gesendet wurde
- Jedes Mal, wenn die Task läuft, werden E-Mails für **alle** überschrittenen Aufträge gesendet

**Beispiel:**
- Auftrag 12345 ist den ganzen Tag überschritten
- Task läuft um 8:00 → E-Mail gesendet
- Task läuft um 8:15 → E-Mail gesendet (nochmal für denselben Auftrag!)
- Task läuft um 8:30 → E-Mail gesendet (nochmal!)
- ... und so weiter alle 15 Minuten

**Ergebnis:** Ein Auftrag kann bis zu 40+ E-Mails pro Tag generieren!

#### 2. **Mehrfache Empfänger pro Auftrag**

**Problem:**
- Wenn ein Auftrag keinen Serviceberater hat, werden Fallback-User benachrichtigt
- Fallback-User können für mehrere Betriebe eingetragen sein
- Christian Meyer könnte als Serviceberater UND als Fallback-User für mehrere Betriebe eingetragen sein

**Code-Stelle:**
```python
# Fall 1: Serviceberater zugeordnet
if serviceberater_nr and serviceberater_nr in employee_emails:
    empfaenger.append(employee_emails[serviceberater_nr])

# Fall 2: Kein Serviceberater → Fallback-User
if not serviceberater_nr and betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
    for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
        if fallback_nr in employee_emails:
            empfaenger.append(employee_emails[fallback_nr])
```

**Problem:** Wenn Christian Meyer sowohl Serviceberater ist als auch in Fallback-Liste steht, bekommt er 2 Mails pro Auftrag!

#### 3. **Kombination aus beiden Problemen**

**Worst Case:**
- 10 überschrittene Aufträge
- Christian Meyer ist Serviceberater für 5 Aufträge
- Christian Meyer ist Fallback-User für alle 10 Aufträge (weil er für mehrere Betriebe eingetragen ist)
- Task läuft 40 Mal pro Tag

**Berechnung:**
- 5 Aufträge × 2 Mails (Serviceberater + Fallback) × 40 Läufe = **400 Mails**
- 5 weitere Aufträge × 1 Mail (nur Fallback) × 40 Läufe = **200 Mails**
- **Gesamt: 600 Mails pro Tag!**

---

## ✅ LÖSUNG (TAG 182)

### Sofortmaßnahme: Task deaktiviert

**Änderung in `celery_app/__init__.py`:**
- Task `benachrichtige-serviceberater-ueberschreitungen` aus dem Celery Beat Schedule entfernt
- Task ist weiterhin manuell aufrufbar, läuft aber nicht mehr automatisch

**Code:**
```python
# TAG 182: DEAKTIVIERT - Buggy, sendet doppelte Mails (Christian Meyer bekam über 80 Mails)
# 'benachrichtige-serviceberater-ueberschreitungen': {
#     'task': 'celery_app.tasks.benachrichtige_serviceberater_ueberschreitungen',
#     'schedule': crontab(minute='*/15', hour='7-18', day_of_week='mon-fri'),
#     'options': {'queue': 'aftersales'}
# },
```

---

## 🔧 VORGESCHLAGENE FIXES (für zukünftige Reaktivierung)

### Fix 1: Tracking-Tabelle für gesendete E-Mails

**Lösung:** Datenbank-Tabelle `email_notifications_sent` erstellen

```sql
CREATE TABLE email_notifications_sent (
    id SERIAL PRIMARY KEY,
    auftrag_nr INTEGER NOT NULL,
    employee_locosoft_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,  -- 'ueberschreitung'
    sent_date DATE NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(auftrag_nr, employee_locosoft_id, notification_type, sent_date)
);
```

**Code-Änderung:**
```python
# Vor dem Senden prüfen
cursor.execute("""
    SELECT 1 FROM email_notifications_sent
    WHERE auftrag_nr = %s
      AND employee_locosoft_id = %s
      AND notification_type = 'ueberschreitung'
      AND sent_date = CURRENT_DATE
""", (auftrag_nr, serviceberater_nr))

if cursor.fetchone():
    logger.debug(f"E-Mail für Auftrag {auftrag_nr} bereits heute gesendet - überspringe")
    continue

# Nach dem Senden eintragen
cursor.execute("""
    INSERT INTO email_notifications_sent (auftrag_nr, employee_locosoft_id, notification_type, sent_date)
    VALUES (%s, %s, 'ueberschreitung', CURRENT_DATE)
    ON CONFLICT DO NOTHING
""", (auftrag_nr, serviceberater_nr))
```

### Fix 2: Deduplizierung der Empfänger-Liste

**Problem:** Ein Empfänger kann mehrfach in der Liste stehen (Serviceberater + Fallback)

**Lösung:**
```python
# Empfänger bestimmen
empfaenger = []
empfaenger_ids = set()  # Verhindert Duplikate

# Fall 1: Serviceberater zugeordnet
if serviceberater_nr and serviceberater_nr in employee_emails:
    if serviceberater_nr not in empfaenger_ids:
        empfaenger.append(employee_emails[serviceberater_nr])
        empfaenger_ids.add(serviceberater_nr)

# Fall 2: Kein Serviceberater → Fallback-User
if not serviceberater_nr and betrieb and betrieb in FALLBACK_USER_BY_BETRIEB:
    for fallback_nr in FALLBACK_USER_BY_BETRIEB[betrieb]:
        if fallback_nr in employee_emails and fallback_nr not in empfaenger_ids:
            empfaenger.append(employee_emails[fallback_nr])
            empfaenger_ids.add(fallback_nr)
```

### Fix 3: Reduzierte Frequenz

**Alternative:** Statt alle 15 Minuten, nur 1x pro Stunde oder 2x pro Tag

**Vorschlag:**
- 1x morgens (8:00) - Zusammenfassung aller Überschreitungen
- 1x nachmittags (14:00) - Update

**Oder:** Nur bei neuer Überschreitung (nicht bei bestehenden)

---

## 📊 ZUSAMMENFASSUNG

### Problem
- ❌ Keine Tracking-Tabelle → E-Mails werden alle 15 Minuten für dieselben Aufträge gesendet
- ❌ Keine Deduplizierung → Empfänger können mehrfach in Liste stehen
- ❌ Zu hohe Frequenz → 40+ Läufe pro Tag

### Lösung (TAG 182)
- ✅ Task deaktiviert (aus Schedule entfernt)
- ✅ Keine weiteren doppelten Mails

### Nächste Schritte (für Reaktivierung)
1. Tracking-Tabelle erstellen
2. Empfänger-Deduplizierung implementieren
3. Frequenz reduzieren oder nur bei neuen Überschreitungen senden
4. Testing mit echten Daten

---

## 🔗 RELEVANTE DATEIEN

- `celery_app/tasks.py` - Task-Funktion `benachrichtige_serviceberater_ueberschreitungen()`
- `celery_app/__init__.py` - Celery Beat Schedule (Task deaktiviert)
- `api/graph_mail_connector.py` - E-Mail-Versand

---

**Status:** ✅ Task deaktiviert, Problem analysiert, Fixes dokumentiert
