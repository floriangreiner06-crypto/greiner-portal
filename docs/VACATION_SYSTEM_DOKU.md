# URLAUBSPLANER SYSTEM-DOKUMENTATION

**Stand:** TAG 107 (09.12.2025)

---

## WICHTIGE IDs

| Person | Employee ID | LDAP Username | Rolle |
|--------|-------------|---------------|-------|
| Florian Greiner | **19** | florian.greiner | Geschäftsführung (GL) |
| Peter Greiner | 20 | peter.greiner | **DEAKTIVIERT** (Senior, in Rente) |
| Georg Kandler | 27 | - | Lager & Teile |

⚠️ **ACHTUNG:** Employee ID 27 ist NICHT Florian Greiner!

---

## DATENBANK-TABELLEN

### vacation_approval_rules
```
id                      INTEGER PRIMARY KEY
loco_grp_code          TEXT     -- Gruppencode (GL, VKB, MON, LAG, etc.)
subsidiary             INTEGER  -- Standort (1=Deggendorf, 3=Landau, NULL=alle)
approver_employee_id   INTEGER  -- Employee-ID des Genehmigers
approver_ldap_username TEXT     -- LDAP-Username des Genehmigers
priority               INTEGER  -- 1=Haupt, 2=Stellvertreter
active                 INTEGER  -- 1=aktiv, 0=deaktiviert
created_at, updated_at TIMESTAMP
created_by, notes      TEXT
```

### vacation_bookings
```
id                INTEGER PRIMARY KEY
employee_id       INTEGER  -- Wer beantragt
booking_date      TEXT     -- YYYY-MM-DD
vacation_type_id  INTEGER  -- 1=Urlaub, 3=Krank, 5=Schulung, 6=ZA
day_part          TEXT     -- 'full' oder 'half'
status            TEXT     -- 'pending', 'approved', 'rejected', 'cancelled'
approved_by       INTEGER  -- Employee-ID des Genehmigers
approved_at       TEXT
comment           TEXT
created_at        TEXT
```

### employees (relevante Spalten)
```
id               INTEGER PRIMARY KEY
first_name       TEXT
last_name        TEXT
department_name  TEXT     -- Anzeigename der Abteilung
aktiv            INTEGER  -- 1=aktiv
```

### ldap_employee_mapping
```
id              INTEGER PRIMARY KEY
employee_id     INTEGER  -- FK zu employees.id
ldap_username   TEXT     -- LDAP/AD Username
locosoft_id     INTEGER  -- Locosoft Mitarbeiternummer
```

---

## GRUPPEN-CODES (loco_grp_code)

| Code | Bedeutung | Genehmiger |
|------|-----------|------------|
| GL | Geschäftsführung | Florian Greiner (sich selbst - TODO!) |
| VKB | Verkauf Beratung | Anton Süß |
| MON | Werkstatt/Montage | W. Scheingraber (DEG), Rolf Sterr (LAN) |
| LAG | Lager & Teile | Bruno Wieland |
| SER | Service | Matthias König |
| DIS | Disposition | Margit Loibl |
| CC | Call-Center | Brigitte Lackerbeck |
| VER | Verwaltung | Christian Aichinger |
| FZ | Fahrzeuge | Christian Aichinger |
| FL | Filialleitung | Florian Greiner |

---

## E-MAIL WORKFLOW

| Aktion | E-Mail an | Kalender |
|--------|-----------|----------|
| Neuer Antrag | Genehmiger (Prio 1) | - |
| Genehmigung | HR + Mitarbeiter | ✅ Eintrag erstellen |
| Ablehnung | Mitarbeiter | - |
| Stornierung | Genehmiger + HR (wenn approved) | ✅ Eintrag löschen |

**E-Mail-Adressen:**
- HR: `hr@auto-greiner.de`
- Absender: `drive@auto-greiner.de`
- Kalender: `drive@auto-greiner.de` (Shared Mailbox)

---

## BEKANNTE PROBLEME / TODOS

### ❌ GL hat keinen Genehmiger
- Florian Greiner ist selbst GL-Genehmiger
- System überspringt ihn → keine E-Mail, kein Genehmiger
- **Lösung nötig:** Auto-Approve für GL oder HR genehmigt

### ✅ Peter Greiner deaktiviert
- Senior Chef, in Rente
- `active = 0` in vacation_approval_rules
- **NICHT reaktivieren!**

---

## API ENDPOINTS

```
GET  /api/vacation/my-balance        - Eigener Urlaubsstand
GET  /api/vacation/my-bookings       - Eigene Buchungen
POST /api/vacation/book              - Neuen Urlaub buchen
POST /api/vacation/cancel            - Buchung stornieren
GET  /api/vacation/pending-approvals - Offene Genehmigungen (für Genehmiger)
POST /api/vacation/approve           - Genehmigen
POST /api/vacation/reject            - Ablehnen
GET  /api/vacation/debug/session     - Debug: Session-Info
```

---

## DATEIEN

```
/opt/greiner-portal/api/
├── vacation_api.py              - Haupt-API (v2.4)
├── vacation_approver_service.py - Genehmiger-Logik
├── vacation_calendar_service.py - Outlook Kalender
├── vacation_locosoft_service.py - Locosoft Abwesenheiten
└── graph_mail_connector.py      - Graph API für E-Mails
```
