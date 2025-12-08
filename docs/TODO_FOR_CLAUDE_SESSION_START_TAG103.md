# TODO FOR CLAUDE - SESSION START TAG 103

**Erstellt:** 2025-12-08  
**Kontext:** Greiner Portal DRIVE - Frontend-Weiterentwicklung

---

## 📋 LETZTER STAND (TAG 102)

### Was wurde gemacht:
- HR Datenqualitäts-Check Script (`scripts/hr_datenqualitaet_check.py`)
- Anleitung für Vanessa aktualisiert (`docs/HR_LOCOSOFT_DATENPFLEGE_ANLEITUNG_V2.md`)
- Locosoft-Schema analysiert (is_latest_record ist immer NULL)
- 15 MA ohne Pausen, 9 MA mit unvollständigen Arbeitszeiten identifiziert

### Offene Punkte aus TAG 102:
- [ ] Überstunden-Dashboard im Portal (`/hr/ueberstunden`) - optional
- [ ] Vanessa muss Daten in Locosoft pflegen

---

## 🎯 FOKUS TAG 103: FRONTEND-WEITERENTWICKLUNG

### Mögliche Aufgaben:

**Option A: Dashboard-Konsolidierung**
- Werkstatt-Bereich hat viele ähnliche Seiten
- Rollenbasierte Startseiten einrichten
- Mobile-Optimierung für Werkstatt-Monitor

**Option B: HR Überstunden-Dashboard**
- Neue Route `/hr/ueberstunden`
- Zeigt Soll/Ist/Differenz pro Mitarbeiter
- Nutzt Locosoft-Daten (times, worktimes, breaktimes)

**Option C: UX-Verbesserungen**
- Einheitliche Farbgebung
- Loading-States
- Bessere Fehlerbehandlung

**Option D: Teile-Status Erweiterung**
- E-Mail Alert bei kritischen Aufträgen
- Excel-Export
- Lieferzeit-Prognose (ML)

---

## 📁 WICHTIGE DATEIEN

### Session-Docs:
- `docs/SESSION_WRAP_UP_TAG102.md` - Was wurde gemacht
- `docs/PROMPT_TAG103.md` - Kontext für diese Session

### Schemas:
- `docs/DB_SCHEMA_SQLITE.md` - Portal-Datenbank
- `docs/DB_SCHEMA_LOCOSOFT.md` - Locosoft-Datenbank

### Bestehende Frontends:
- `templates/werkstatt/` - Werkstatt-Bereich
- `templates/aftersales/` - After-Sales
- `templates/controlling/` - Controlling
- `templates/verkauf/` - Verkauf

---

## 🔧 ARBEITSWEISE

1. **Florian gibt konkreten Fokus** (welche Option?)
2. **Claude liest relevante Templates/APIs**
3. **Claude schreibt Dateien ins Sync-Verzeichnis**
4. **Florian kopiert mit:** `cp /mnt/greiner-portal-sync/[pfad] /opt/greiner-portal/[pfad]`
5. **Bei Python:** `sudo systemctl restart greiner-portal`
6. **Bei Templates:** Nur Browser-Refresh (Strg+F5)

---

## ⚠️ REMINDER

- **KEIN rsync** - einfacher `cp` Befehl
- **Sync-Verzeichnis:** `\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\`
- **Server-Mount:** `/mnt/greiner-portal-sync/`
- **Credentials:** In `/opt/greiner-portal/config/.env`

---

**Warte auf Florians Entscheidung welcher Fokus!**
