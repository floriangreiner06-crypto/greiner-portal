# Alarm E-Mail Auftragsüberschreitung – Konfiguration in Admin (TAG 206)

**Datum:** 2026-01-22  
**TAG:** 206

---

## Übersicht

Die **Alarm E-Mail Auftragsüberschreitung** ist wie die anderen E-Mail-Reports unter **Administration → Rechte → E-Mail Reports** konfigurierbar.

- **Report-ID:** `alarm_auftrag_ueberschreitung`
- **Karte:** erscheint unter „Werkstatt“ mit Icon ⚠️
- **Verwalten:** Empfänger hinzufügen/entfernen wie bei Auftragseingang, TEK, Werkstatt Tagesbericht

---

## Verhalten

1. **Weiterhin automatisch:**  
   Pro überschrittenem Auftrag erhalten wie bisher:
   - der **Serviceberater** des Auftrags,
   - der **Quality-Check** (Matthias König),
   - ggf. **Fallback** (wenn kein Serviceberater).

2. **Zusätzlich aus Admin:**  
   Alle unter **E-Mail Reports → Alarm E-Mail Auftragsüberschreitung → Verwalten** eingetragenen **Empfänger** erhalten dieselbe Alarm-Mail zu jedem überschrittenen Auftrag (max. 1× pro Auftrag pro Tag, sofern Migration ausgeführt wurde).

---

## Migration (optional, für 1× pro Tag pro Report-Subscriber)

Damit konfigurierte Report-Empfänger nur **einmal pro Tag pro Auftrag** eine Mail bekommen, muss die Migration ausgeführt werden:

```bash
cd /opt/greiner-portal
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal \
  -f migrations/add_email_notifications_recipient_email_tag206.sql
```

Ohne Migration werden Report-Subscriber bei jedem Task-Lauf (alle 15 Min) erneut berücksichtigt und können mehrfach pro Tag pro Auftrag eine Mail erhalten.

---

## Geänderte Dateien

- **reports/registry.py** – Report `alarm_auftrag_ueberschreitung` registriert
- **celery_app/tasks.py** – Lädt Report-Subscriber, fügt sie den Empfängern hinzu, Tracking mit `recipient_email`
- **migrations/add_email_notifications_recipient_email_tag206.sql** – Spalte `recipient_email`, neuer Unique-Index

---

## Admin-UI

Unter **http://drive/admin/rechte** → Tab **E-Mail Reports** erscheint die Karte:

- **Alarm E-Mail Auftragsüberschreitung**
- Kategorie: Werkstatt
- Beschreibung: Benachrichtigung wenn ein Werkstattauftrag die Vorgabezeit überschreitet (Serviceberater + konfigurierte Empfänger)
- Zeitplan: alle 15 Min 7–18 Uhr Mo–Fr
- **Verwalten** – Empfänger hinzufügen/entfernen (wie bei anderen Reports)
