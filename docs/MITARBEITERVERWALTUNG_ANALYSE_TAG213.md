# Mitarbeiterverwaltung - Analyse & Umsetzungsplan (TAG 213)

**Datum:** 2026-01-27  
**Zweck:** Umfassende Mitarbeiterverwaltung nach Muster "Digitale Personalakte"  
**URL:** `/urlaubsplaner/chef` erweitern oder neue Route `/admin/mitarbeiterverwaltung`

---

## 📋 BESTANDSANALYSE

### ✅ Was bereits existiert:

#### 1. **Datenbank-Struktur:**
- ✅ `employees` Tabelle (23 Spalten)
  - Grunddaten: `id`, `first_name`, `last_name`, `email`, `birthday`, `entry_date`, `exit_date`
  - Abteilung: `department_id`, `department_name`, `location`
  - Urlaub: `vacation_days_total`, `vacation_entitlement`, `vacation_used_2025`
  - Locosoft: `locosoft_id`
  - Status: `aktiv`, `active`, `is_manager`, `manager_role`
  - Sonstiges: `free_weekdays`, `personal_nr`, `supervisor_id`

- ✅ `vacation_entitlements` Tabelle
  - `employee_id`, `year`, `total_days`, `carried_over`, `added_manually`
  - Unterstützt bereits individuelle Ansprüche pro Jahr

- ✅ `ldap_employee_mapping` Tabelle
  - Mapping zwischen LDAP-Username und `employee_id`
  - Enthält `locosoft_id`

#### 2. **Bestehende Templates:**
- ✅ `urlaubsplaner_admin.html` - Einfache Admin-Ansicht (Tabelle mit Urlaubsdaten)
- ✅ `urlaubsplaner_chef.html` - Chef-Übersicht (Team-Struktur)
- ✅ `urlaubsplaner_v2.html` - Hauptansicht (Kalender)

#### 3. **Bestehende API-Endpunkte:**
- ✅ `/api/vacation/admin/employees` - Liste aller Mitarbeiter mit Urlaubsdaten
- ✅ `/api/vacation/admin/update-entitlement` - Urlaubsanspruch aktualisieren
- ✅ `/api/vacation/admin/bulk-update` - Mehrere MA aktualisieren
- ✅ `/api/vacation/chef-overview` - Chef-Übersicht

#### 4. **LDAP/Locosoft Integration:**
- ✅ `auth/ldap_connector.py` - LDAP-Verbindung
- ✅ `api/vacation_locosoft_service.py` - Locosoft-Abwesenheiten
- ✅ `ldap_employee_mapping` - Mapping-Tabelle

---

## ❌ Was fehlt:

### 1. **Datenbank-Erweiterungen:**

#### Neue Tabellen benötigt:
- ❌ `employee_working_time_models` - Arbeitszeitmodelle (Teilzeit, Vollzeit, etc.)
  - `id`, `employee_id`, `start_date`, `end_date`, `hours_per_week`, `working_days_per_week`, `description`
  
- ❌ `employee_working_time_exceptions` - Ausnahmen (Sonderurlaub, etc.)
  - `id`, `employee_id`, `from_date`, `to_date`, `exception_type`, `description`, `affects_vacation_entitlement`
  
- ❌ `employee_vacation_settings` - Urlaubsplaner-Einstellungen
  - `employee_id`, `show_in_planner`, `show_birthday`, `vacation_expires`, `max_carry_over`, `weekend_limit`, `max_vacation_length`, `calculation_method`, `valuation_lock`, `entry_from`, `entry_until`

- ❌ `employee_contact_data` - Kontaktdaten (privat/firma)
  - `employee_id`, `type` (privat/firma), `street`, `city`, `postal_code`, `country`, `phone`, `mobile`, `fax`, `email`

- ❌ `employee_contract_data` - Vertragsdaten
  - `employee_id`, `company`, `hired_as`, `activity`, `probation_end`, `limited_until`, `notice_period_employer`, `notice_period_employee`, `country`, `federal_state`

#### Erweiterungen `employees` Tabelle:
- ❌ `gender` (Geschlecht)
- ❌ `title` (Titel: Dr., etc.)
- ❌ `salutation` (Anrede)
- ❌ `private_street`, `private_city`, `private_postal_code`, `private_country`, `private_phone`, `private_mobile`, `private_email`
- ❌ `company_phone`, `company_mobile`, `company_fax`, `company_email`
- ❌ `personal_nr_1`, `personal_nr_2`

### 2. **Frontend-Features:**

#### Fehlende UI-Komponenten:
- ❌ Detailansicht für einzelnen Mitarbeiter (wie im Muster)
- ❌ Tabs: Deckblatt, Adressdaten, Personalakte, Mitarbeiterdaten, Moduldaten
- ❌ Arbeitszeitmodelle-Verwaltung (Tabelle mit hinzufügen/bearbeiten/löschen)
- ❌ Ausnahmen-Verwaltung (Sonderurlaub, etc.)
- ❌ Urlaubsplaner-Einstellungen pro Mitarbeiter
- ❌ Kontaktdaten (privat/firma) mit Editierfunktion
- ❌ Vertragsdaten mit Editierfunktion
- ❌ Auto-Füllung aus LDAP/Locosoft mit "Überschreiben"-Option

### 3. **API-Endpunkte:**

#### Fehlende Endpunkte:
- ❌ `GET /api/vacation/admin/employee/<id>` - Einzelner Mitarbeiter mit allen Daten
- ❌ `PUT /api/vacation/admin/employee/<id>` - Mitarbeiter aktualisieren
- ❌ `GET /api/vacation/admin/employee/<id>/working-time-models` - Arbeitszeitmodelle
- ❌ `POST /api/vacation/admin/employee/<id>/working-time-models` - Arbeitszeitmodell hinzufügen
- ❌ `PUT /api/vacation/admin/employee/<id>/working-time-models/<model_id>` - Arbeitszeitmodell aktualisieren
- ❌ `DELETE /api/vacation/admin/employee/<id>/working-time-models/<model_id>` - Arbeitszeitmodell löschen
- ❌ `GET /api/vacation/admin/employee/<id>/exceptions` - Ausnahmen
- ❌ `POST /api/vacation/admin/employee/<id>/exceptions` - Ausnahme hinzufügen
- ❌ `PUT /api/vacation/admin/employee/<id>/settings` - Urlaubsplaner-Einstellungen
- ❌ `POST /api/vacation/admin/sync-from-ldap` - Sync aus LDAP
- ❌ `POST /api/vacation/admin/sync-from-locosoft` - Sync aus Locosoft

---

## 🎯 UMSETZUNGSSTRATEGIE

### Option 1: `/urlaubsplaner/chef` erweitern (Empfohlen)
**Vorteile:**
- ✅ Bestehende Route nutzen
- ✅ Logische Erweiterung der Chef-Funktionalität
- ✅ Bereits für Admins/Genehmiger verfügbar

**Nachteile:**
- ⚠️ Route-Name könnte verwirrend sein (Chef vs. Admin)

### Option 2: Neue Route `/admin/mitarbeiterverwaltung`
**Vorteile:**
- ✅ Klarer Admin-Bereich
- ✅ Bessere URL-Struktur
- ✅ Kann später erweitert werden

**Nachteile:**
- ⚠️ Neue Route muss registriert werden

**Empfehlung:** Option 2 (neue Route), aber `/urlaubsplaner/chef` als Link beibehalten

---

## 📊 KOMPLEXITÄTS-EINSCHÄTZUNG

### Phase 1: Datenbank-Erweiterungen (2-3 Stunden)
- [ ] Migration-Script für neue Tabellen
- [ ] Erweiterung `employees` Tabelle
- [ ] Indizes und Constraints
- [ ] Test-Daten

### Phase 2: LDAP/Locosoft Sync (2-3 Stunden)
- [ ] Funktionen zum Laden aus LDAP
- [ ] Funktionen zum Laden aus Locosoft
- [ ] Auto-Füllung mit "Überschreiben"-Option
- [ ] Batch-Sync-Funktionalität

### Phase 3: API-Endpunkte (4-5 Stunden)
- [ ] CRUD-Endpunkte für Mitarbeiter
- [ ] Arbeitszeitmodelle-Endpunkte
- [ ] Ausnahmen-Endpunkte
- [ ] Einstellungen-Endpunkte
- [ ] Sync-Endpunkte

### Phase 4: Frontend - Grundstruktur (3-4 Stunden)
- [ ] Template nach Muster erstellen
- [ ] Linke Sidebar (Mitarbeiterliste)
- [ ] Rechte Hauptansicht (Tabs)
- [ ] Navigation zwischen Mitarbeitern

### Phase 5: Frontend - Detailansicht (6-8 Stunden)
- [ ] Tab "Deckblatt" (Grunddaten, Foto, etc.)
- [ ] Tab "Adressdaten" (Kontaktdaten privat/firma)
- [ ] Tab "Mitarbeiterdaten" (Vertrag, Arbeitszeitmodelle, Ausnahmen)
- [ ] Tab "Moduldaten" → "Urlaubsplaner" (Einstellungen)
- [ ] Editierfunktionen für alle Felder

### Phase 6: Integration & Testing (2-3 Stunden)
- [ ] Integration mit bestehenden Systemen
- [ ] Testen der Auto-Füllung
- [ ] Validierung der Daten
- [ ] Performance-Optimierung

**Gesamtaufwand:** ~20-26 Stunden (2,5-3,5 Arbeitstage)

---

## 🏗️ ARCHITEKTUR-VORSCHLAG

### URL-Struktur:
```
/admin/mitarbeiterverwaltung              # Übersicht (Liste)
/admin/mitarbeiterverwaltung/<id>         # Detailansicht
/admin/mitarbeiterverwaltung/<id>/edit   # Bearbeitungsmodus
```

### Template-Struktur:
```
templates/admin/
  ├── mitarbeiterverwaltung.html         # Übersicht
  ├── mitarbeiterverwaltung_detail.html  # Detailansicht
  └── mitarbeiterverwaltung_edit.html    # Bearbeitung
```

### API-Struktur:
```
api/
  ├── employee_management_api.py         # Neue API-Datei
  └── employee_sync_service.py           # LDAP/Locosoft Sync
```

---

## 📝 NÄCHSTE SCHRITTE

1. **Datenbank-Migration erstellen**
   - Neue Tabellen
   - Erweiterungen `employees`
   - Indizes

2. **API-Endpunkte implementieren**
   - CRUD für Mitarbeiter
   - Arbeitszeitmodelle
   - Ausnahmen
   - Sync-Funktionen

3. **Frontend nach Muster bauen**
   - Grundstruktur
   - Tabs
   - Editierfunktionen

4. **LDAP/Locosoft Integration**
   - Auto-Füllung
   - Batch-Sync

---

**Status:** 📋 Analyse abgeschlossen - Bereit für Umsetzung  
**Priorität:** Hoch (löst Urlaubsanspruch-Berechnungsprobleme)
