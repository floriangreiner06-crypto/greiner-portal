# TODO FOR CLAUDE - SESSION START TAG 105

**Datum:** 09.12.2025  
**Vorgänger:** TAG 104 (Outlook Kalender-Integration)

---

## 🚀 SESSION-START ANWEISUNGEN

**WICHTIG - ARBEITSWEISE:**

1. **ZUERST lesen:**
   ```
   Filesystem:read_text_file → \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\CLAUDE.md
   Filesystem:read_text_file → \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\WORKFLOW.md
   ```

2. **Code-Änderungen IMMER im Sync-Verzeichnis:**
   ```
   \\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
   ```

3. **Dann User bitten zu kopieren:**
   ```bash
   cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]
   sudo systemctl restart greiner-portal
   ```

4. **NIEMALS:**
   - `python3 << 'EOF'` Patches
   - `cat > datei << 'EOF'`
   - `sed -i` für Code-Änderungen
   - Direkte Server-Bearbeitung

---

## 🎯 HAUPTAUFGABE TAG 105

### Urlaubsplaner V2 - UI/UX Überarbeitung

**Probleme aus TAG 104:**
1. Kalender zu "bold" / unübersichtlich
2. Bedienung buggy
3. Team-Kalender vs. persönlicher Kalender unklar
4. Storno-Button fehlt im Frontend

---

## 📋 KONKRETE TODOS

### 1. Storno-Button im Frontend
- Template: `templates/urlaubsplaner_v2.html`
- API existiert: `POST /api/vacation/cancel`
- Button bei eigenen Buchungen anzeigen
- Bestätigungsdialog mit Grund-Eingabe

### 2. Kalender-Darstellung verbessern
- Weniger "bold" / dezenter
- Bessere Farbgebung
- Übersichtlichere Monatsansicht

### 3. Outlook-Integration klären
**Aktuell:**
- Team-Kalender: `drive@auto-greiner.de` (für alle sichtbar)
- Format: `🏖️ [Abteilung] Name`

**Fehlt:**
- Eintrag in **eigenen** Outlook-Kalender des Mitarbeiters
- Option: Meeting-Einladung an Mitarbeiter?

### 4. Vertretungsregelung (Erweiterung)
- Bei Urlaubsantrag: Wer vertritt?
- Überlappungsprüfung mit Vertreter
- Minimale Belegung pro Abteilung

---

## 📁 RELEVANTE DATEIEN

```
# Frontend
templates/urlaubsplaner_v2.html

# Backend API
api/vacation_api.py              - Endpoints (book, approve, reject, cancel)
api/vacation_approver_service.py - Genehmiger-Logik
api/vacation_calendar_service.py - Outlook-Kalender
api/vacation_locosoft_service.py - Locosoft-Abwesenheiten

# Konfiguration
config/credentials.json          - Azure Graph API Credentials
```

---

## 🗄️ DB-TABELLEN

```sql
-- Buchungen
vacation_bookings (id, employee_id, booking_date, day_part, status, vacation_type_id, ...)

-- Genehmiger-Regeln
vacation_approval_rules (id, loco_grp_code, subsidiary, approver_employee_id, approver_ldap_username, priority, active, ...)

-- Urlaubsarten
vacation_types (id, name, ...)
```

---

## ⚡ SCHNELLSTART

```bash
# Server-Status prüfen
sudo systemctl status greiner-portal

# Logs
journalctl -u greiner-portal -f

# API testen
curl -s http://localhost:5000/api/vacation/health | python3 -m json.tool

# Nach Änderungen
cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]
sudo systemctl restart greiner-portal
```

---

## 🔑 CREDENTIALS

- **Azure App:** Greiner DRIVE
- **Graph API Mailboxes:**
  - `drive@auto-greiner.de` (Absender, Team-Kalender)
  - `hr@auto-greiner.de` (Empfänger für Locosoft-Einträge)

---

## 📝 KONTEXT TAG 104

- Outlook Team-Kalender funktioniert ✅
- E-Mail-Workflow funktioniert ✅
- Cancel-Endpoint existiert ✅
- Selbst-Genehmiger → GL Eskalation ✅
- Peter Greiner deaktiviert ✅

**Hauptproblem:** Frontend fehlt Storno-Button und UI ist unübersichtlich.
