# 🗄️ SQLITE DATENBANK-SCHEMA (AUTO-GENERIERT)

**Generiert:** 2025-12-12 09:05:01
**Datenbank:** `/opt/greiner-portal/data/greiner_controlling.db`

⚠️ **Diese Datei wird automatisch generiert - nicht manuell editieren!**

---

## 📋 TABELLEN-ÜBERSICHT

**Anzahl Tabellen:** 155

| Tabelle | Spalten | Zeilen |
|---------|---------|--------|
| `ad_group_role_mapping` | 8 | 0 |
| `audit_log` | 9 | 0 |
| `auth_audit_log` | 11 | 0 |
| `bank_accounts_old_backup` | 6 | 3 |
| `banken` | 9 | 7 |
| `bwa_monatswerte` | 8 | 11 |
| `charge_type_descriptions_sync` | 3 | 100 |
| `charge_types_sync` | 9 | 400 |
| `customers_suppliers` | 5 | 53,293 |
| `daily_balances_old_backup` | 10 | 90 |
| `dealer_vehicles` | 13 | 1,226 |
| `departments` | 3 | 19 |
| `ek_finanzierung_konditionen` | 9 | 3 |
| `employees` | 23 | 76 |
| `fahrzeugfinanzierungen` | 55 | 192 |
| `fahrzeugfinanzierungen_new` | 49 | 0 |
| `fibu_buchungen` | 14 | 549,224 |
| `finanzierung_snapshots` | 9 | 0 |
| `finanzierungsbanken` | 8 | 3 |
| `holidays` | 6 | 39 |
| `import_log` | 14 | 0 |
| `konten` | 27 | 12 |
| `konto_snapshots` | 11 | 1 |
| `kreditlinien` | 32 | 0 |
| `kreditlinien_snapshots` | 7 | 0 |
| `ldap_employee_mapping` | 7 | 62 |
| `leasys_vehicle_cache` | 7 | 168 |
| `loco_absence_calendar` | 11 | 15,307 |
| `loco_absence_reasons` | 3 | 23 |
| `loco_absence_types` | 2 | 2 |
| `loco_accounts_characteristics` | 11 | 2 |
| `loco_appointments` | 47 | 1 |
| `loco_appointments_text` | 11 | 0 |
| `loco_charge_type_descriptions` | 2 | 100 |
| `loco_charge_types` | 4 | 400 |
| `loco_clearing_delay_types` | 2 | 10 |
| `loco_codes_customer_def` | 6 | 12 |
| `loco_codes_customer_list` | 6 | 44,722 |
| `loco_codes_vehicle_date` | 3 | 6,197 |
| `loco_codes_vehicle_date_def` | 6 | 15 |
| `loco_codes_vehicle_def` | 6 | 47 |
| `loco_codes_vehicle_list` | 6 | 27,702 |
| `loco_codes_vehicle_mileage` | 3 | 1 |
| `loco_codes_vehicle_mileage_def` | 5 | 2 |
| `loco_com_number_types` | 3 | 18 |
| `loco_configuration` | 4 | 38 |
| `loco_configuration_numeric` | 4 | 1,433 |
| `loco_countries` | 3 | 43 |
| `loco_customer_codes` | 2 | 21 |
| `loco_customer_com_numbers` | 14 | 76,415 |
| `loco_customer_contact_log_pemissions` | 3 | 0 |
| `loco_customer_profession_codes` | 2 | 90 |
| `loco_customer_supplier_bank_information` | 5 | 993 |
| `loco_customer_to_customercodes` | 2 | 3,260 |
| `loco_customer_to_professioncodes` | 2 | 1 |
| `loco_customers_suppliers` | 55 | 53,524 |
| `loco_dealer_sales_aid` | 8 | 3,599 |
| `loco_dealer_sales_aid_bonus` | 8 | 0 |
| `loco_dealer_vehicles` | 115 | 5,310 |
| `loco_document_types` | 2 | 13 |
| `loco_employees` | 22 | 114 |
| `loco_employees_breaktimes` | 6 | 392 |
| `loco_employees_group_mapping` | 3 | 126 |
| `loco_employees_history` | 22 | 124 |
| `loco_employees_worktimes` | 7 | 487 |
| `loco_external_customer_references` | 7 | 0 |
| `loco_external_reference_parties` | 4 | 0 |
| `loco_financing_examples` | 21 | 140 |
| `loco_fuels` | 2 | 18 |
| `loco_invoice_types` | 2 | 7 |
| `loco_invoices` | 39 | 54,219 |
| `loco_journal_accountings` | 45 | 599,210 |
| `loco_labour_types` | 2 | 30 |
| `loco_labours` | 20 | 281,117 |
| `loco_labours_groups` | 4 | 0 |
| `loco_labours_master` | 6 | 211,786 |
| `loco_leasing_examples` | 15 | 355 |
| `loco_makes` | 16 | 48 |
| `loco_nominal_accounts` | 8 | 1,239 |
| `loco_order_classifications_def` | 11 | 12 |
| `loco_orders` | 33 | 41,048 |
| `loco_part_types` | 2 | 19 |
| `loco_parts` | 19 | 142,151 |
| `loco_parts_additional_descriptions` | 4 | 123,831 |
| `loco_parts_inbound_delivery_notes` | 25 | 66,429 |
| `loco_parts_master` | 34 | 1,899,386 |
| `loco_parts_rebate_codes_buy` | 7 | 194 |
| `loco_parts_rebate_codes_sell` | 7 | 309 |
| `loco_parts_rebate_groups_buy` | 2 | 6 |
| `loco_parts_rebate_groups_sell` | 2 | 8 |
| `loco_parts_special_offer_prices` | 6 | 27 |
| `loco_parts_special_prices` | 5 | 128 |
| `loco_parts_stock` | 31 | 42,185 |
| `loco_parts_supplier_numbers` | 2 | 35,394 |
| `loco_privacy_channels` | 3 | 12 |
| `loco_privacy_details` | 4 | 117,852 |
| `loco_privacy_protection_consent` | 18 | 13,838 |
| `loco_privacy_scopes` | 2 | 3 |
| `loco_salutations` | 8 | 10 |
| `loco_subsidiaries` | 3 | 4 |
| `loco_time_types` | 2 | 4 |
| `loco_times` | 12 | 188,877 |
| `loco_tire_storage` | 16 | 4,788 |
| `loco_tire_storage_accessories` | 19 | 0 |
| `loco_tire_storage_wheels` | 25 | 19,178 |
| `loco_transit_customers` | 12 | 0 |
| `loco_transit_vehicles` | 12 | 2,477 |
| `loco_vat_keys` | 9 | 52 |
| `loco_vehicle_accessories_customer` | 9 | 217,172 |
| `loco_vehicle_accessories_dealer` | 10 | 63,836 |
| `loco_vehicle_bodys` | 2 | 47 |
| `loco_vehicle_buy_types` | 2 | 6 |
| `loco_vehicle_contact_log_pemissions` | 3 | 0 |
| `loco_vehicle_pre_owned_codes` | 2 | 5 |
| `loco_vehicle_sale_types` | 2 | 5 |
| `loco_vehicle_types` | 3 | 6 |
| `loco_vehicles` | 79 | 58,561 |
| `loco_wtp_pickup_bring_type` | 2 | 4 |
| `loco_wtp_progress_status` | 2 | 6 |
| `loco_wtp_urgency` | 2 | 7 |
| `loco_wtp_vehicle_status` | 2 | 6 |
| `loco_year_calendar` | 6 | 505 |
| `loco_year_calendar_day_off_codes` | 2 | 5 |
| `loco_year_calendar_subsidiary_mapping` | 3 | 12 |
| `manager_assignments` | 7 | 0 |
| `praemien_berechnungen` | 33 | 1 |
| `praemien_exporte` | 7 | 0 |
| `praemien_kulanz_regeln` | 9 | 5 |
| `praemien_mitarbeiter` | 24 | 79 |
| `roles` | 9 | 6 |
| `salden` | 8 | 1,260 |
| `sales` | 27 | 4,983 |
| `santander_zins_staffel` | 7 | 5 |
| `sessions` | 8 | 0 |
| `stellantis_bestellungen` | 17 | 379 |
| `stellantis_positionen` | 14 | 886 |
| `sync_log` | 8 | 9 |
| `sync_status` | 7 | 1 |
| `system_job_history` | 9 | 6 |
| `system_jobs` | 13 | 14 |
| `teile_lieferscheine` | 18 | 1,489 |
| `tilgungen` | 15 | 158 |
| `transaktionen` | 22 | 15,853 |
| `user_roles` | 6 | 17 |
| `users` | 17 | 16 |
| `users_old_backup` | 5 | 3 |
| `vacation_adjustments` | 7 | 0 |
| `vacation_approval_rules` | 11 | 16 |
| `vacation_audit_log` | 10 | 0 |
| `vacation_bookings` | 11 | 1,358 |
| `vacation_entitlements` | 8 | 75 |
| `vacation_types` | 10 | 11 |
| `vehicles` | 13 | 1,023 |
| `werkstatt_auftraege_abgerechnet` | 17 | 15,936 |
| `werkstatt_leistung_daily` | 14 | 10,452 |

---

## 📊 TABELLEN-DETAILS

### `ad_group_role_mapping` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `ad_group_name` | TEXT | ✓ |  |  |
| `ad_group_dn` | TEXT |  |  |  |
| `role_id` | INTEGER | ✓ |  |  |
| `auto_assign` | BOOLEAN |  | 1 |  |
| `priority` | INTEGER |  | 0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_ad_group_mapping_role`: role_id
- `idx_ad_group_mapping_name`: ad_group_name
- `sqlite_autoindex_ad_group_role_mapping_1`: ad_group_name, role_id

### `audit_log` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `tabelle` | TEXT | ✓ |  |  |
| `datensatz_id` | INTEGER |  |  |  |
| `aktion` | TEXT |  |  |  |
| `benutzer` | TEXT |  |  |  |
| `zeitpunkt` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `alte_werte` | TEXT |  |  |  |
| `neue_werte` | TEXT |  |  |  |
| `bemerkung` | TEXT |  |  |  |

**Indizes:**
- `idx_audit_aktion`: aktion
- `idx_audit_zeitpunkt`: zeitpunkt
- `idx_audit_tabelle`: tabelle

### `auth_audit_log` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `user_id` | INTEGER |  |  |  |
| `username` | TEXT |  |  |  |
| `action` | TEXT | ✓ |  |  |
| `success` | BOOLEAN | ✓ |  |  |
| `error_message` | TEXT |  |  |  |
| `ip_address` | TEXT |  |  |  |
| `user_agent` | TEXT |  |  |  |
| `resource_accessed` | TEXT |  |  |  |
| `details_json` | TEXT |  |  |  |
| `timestamp` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_audit_log_ip`: ip_address
- `idx_audit_log_success`: success
- `idx_audit_log_timestamp`: timestamp
- `idx_audit_log_action`: action
- `idx_audit_log_user_id`: user_id

### `bank_accounts_old_backup` (3 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `account_name` | TEXT | ✓ |  |  |
| `account_type` | TEXT | ✓ |  |  |
| `bank_name` | TEXT |  |  |  |
| `account_number` | TEXT |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

### `banken` (7 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `bank_name` | TEXT | ✓ |  |  |
| `bank_typ` | TEXT |  |  |  |
| `bic` | TEXT |  |  |  |
| `blz` | TEXT |  |  |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_banken_typ`: bank_typ
- `idx_banken_aktiv`: aktiv
- `sqlite_autoindex_banken_1`: bank_name

### `bwa_monatswerte` (11 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `jahr` | INTEGER | ✓ |  |  |
| `monat` | INTEGER | ✓ |  |  |
| `position` | TEXT | ✓ |  |  |
| `bezeichnung` | TEXT |  |  |  |
| `betrag` | REAL | ✓ |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_bwa_jahr_monat`: jahr, monat
- `sqlite_autoindex_bwa_monatswerte_1`: jahr, monat, position

### `charge_type_descriptions_sync` (100 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  | 🔑 |
| `description` | TEXT |  |  |  |
| `synced_at` | TEXT | ✓ |  |  |

### `charge_types_sync` (400 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `type` | INTEGER | ✓ |  |  |
| `subsidiary` | INTEGER | ✓ |  |  |
| `timeunit_rate` | REAL |  |  |  |
| `department` | INTEGER |  |  |  |
| `stundensatz` | REAL |  |  |  |
| `kategorie` | TEXT |  |  |  |
| `abteilung_name` | TEXT |  |  |  |
| `synced_at` | TEXT | ✓ |  |  |

**Indizes:**
- `idx_charge_types_department`: department
- `idx_charge_types_subsidiary`: subsidiary
- `sqlite_autoindex_charge_types_sync_1`: type, subsidiary

### `customers_suppliers` (53,293 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `customer_no` | INTEGER |  |  |  |
| `short_name` | TEXT |  |  |  |
| `long_name` | TEXT |  |  |  |
| `synced_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_customers_suppliers_1`: customer_no

### `daily_balances_old_backup` (90 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `account_id` | INTEGER | ✓ |  |  |
| `date` | DATE | ✓ |  |  |
| `balance` | REAL | ✓ |  |  |
| `loans` | REAL |  | 0 |  |
| `vehicles_value` | REAL |  | 0 |  |
| `receivables` | REAL |  | 0 |  |
| `notes` | TEXT |  |  |  |
| `created_by` | INTEGER |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_daily_balances_old_backup_1`: account_id, date

### `dealer_vehicles` (1,226 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | TEXT |  |  |  |
| `out_invoice_date` | DATE |  |  |  |
| `out_invoice_number` | TEXT |  |  |  |
| `out_sale_price` | REAL |  |  |  |
| `out_sale_type` | TEXT |  |  |  |
| `out_subsidiary` | INTEGER |  |  |  |
| `out_sales_contract_date` | DATE |  |  |  |
| `buyer_customer_no` | INTEGER |  |  |  |
| `netto_price` | REAL |  |  |  |
| `is_new_vehicle` | INTEGER |  |  |  |
| `synced_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_dealer_sale_type`: out_sale_type
- `idx_dealer_subsidiary`: out_subsidiary
- `idx_dealer_invoice_date`: out_invoice_date
- `sqlite_autoindex_dealer_vehicles_1`: dealer_vehicle_number, dealer_vehicle_type

### `departments` (19 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `name` | TEXT | ✓ |  |  |
| `sort_order` | INTEGER |  | 0 |  |

**Indizes:**
- `sqlite_autoindex_departments_1`: name

### `ek_finanzierung_konditionen` (3 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `finanzinstitut` | TEXT |  |  |  |
| `gesamt_limit` | REAL |  |  |  |
| `zinssatz` | REAL |  |  |  |
| `zinsfreie_tage` | INTEGER |  | 0 |  |
| `gueltig_ab` | DATE |  |  |  |
| `notizen` | TEXT |  |  |  |
| `mobilitaet_limit` | REAL |  | 0 |  |
| `vertragsnummer` | TEXT |  |  |  |

**Indizes:**
- `sqlite_autoindex_ek_finanzierung_konditionen_1`: finanzinstitut

### `employees` (76 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `email` | TEXT | ✓ |  |  |
| `password_hash` | TEXT | ✓ |  |  |
| `first_name` | TEXT | ✓ |  |  |
| `last_name` | TEXT | ✓ |  |  |
| `birthday` | DATE |  |  |  |
| `entry_date` | DATE |  |  |  |
| `exit_date` | DATE |  |  |  |
| `department_id` | INTEGER |  |  |  |
| `vacation_days_total` | INTEGER |  | 30 |  |
| `role` | TEXT |  | 'user' |  |
| `free_weekdays` | TEXT |  |  |  |
| `locosoft_id` | INTEGER |  |  |  |
| `department_name` | TEXT |  |  |  |
| `location` | TEXT |  |  |  |
| `vacation_entitlement` | INTEGER |  | 30 |  |
| `vacation_used_2025` | REAL |  | 0 |  |
| `supervisor_id` | INTEGER |  | NULL |  |
| `active` | INTEGER |  | 1 |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `personal_nr` | TEXT |  |  |  |
| `is_manager` | INTEGER |  | 0 |  |
| `manager_role` | TEXT |  |  |  |

**Indizes:**
- `idx_employees_locosoft_id`: locosoft_id
- `idx_employees_active`: active
- `idx_employees_supervisor`: supervisor_id
- `idx_employees_exit`: exit_date
- `sqlite_autoindex_employees_1`: email

### `fahrzeugfinanzierungen` (192 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `finanzbank_id` | INTEGER |  |  |  |
| `vin` | TEXT | ✓ |  |  |
| `vin_kurz` | TEXT |  |  |  |
| `finanzierungsnummer` | TEXT |  |  |  |
| `hersteller` | TEXT |  |  |  |
| `modell` | TEXT |  |  |  |
| `farbe` | TEXT |  |  |  |
| `finanzierungsstatus` | TEXT |  |  |  |
| `dokumentstatus` | TEXT |  |  |  |
| `produktfamilie` | TEXT |  |  |  |
| `produkt` | TEXT |  |  |  |
| `finanzierungsbetrag` | REAL |  |  |  |
| `aktueller_saldo` | REAL |  |  |  |
| `waehrung` | TEXT |  | 'EUR' |  |
| `zinsen_gesamt` | REAL |  | 0 |  |
| `zinsen_letzte_periode` | REAL |  | 0 |  |
| `zinsgutschriften_gesamt` | REAL |  | 0 |  |
| `gebuehren_gesamt` | REAL |  | 0 |  |
| `gebuehren_letzte_periode` | REAL |  | 0 |  |
| `vertragsbeginn` | DATE |  |  |  |
| `zinsbeginn` | DATE |  |  |  |
| `finanzierungsende` | DATE |  |  |  |
| `endfaelligkeit` | DATE |  |  |  |
| `lieferdatum` | DATE |  |  |  |
| `aktivierungsdatum` | DATE |  |  |  |
| `anlagedatum` | DATE |  |  |  |
| `rechnungsnummer` | TEXT |  |  |  |
| `rechnungsdatum` | DATE |  |  |  |
| `rechnungsbetrag` | REAL |  |  |  |
| `alter_finanzierung_tage` | INTEGER |  |  |  |
| `zinsfreiheit_tage` | INTEGER |  |  |  |
| `import_quelle` | TEXT |  |  |  |
| `import_datei` | TEXT |  |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `rohdaten` | TEXT |  |  |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `finanzinstitut` | TEXT |  |  |  |
| `rrdi` | TEXT |  |  |  |
| `zins_startdatum` | DATE |  |  |  |
| `alter_tage` | INTEGER |  |  |  |
| `original_betrag` | REAL |  |  |  |
| `datei_quelle` | TEXT |  |  |  |
| `abbezahlt` | REAL |  | 0 |  |
| `hsn` | TEXT |  |  |  |
| `tsn` | TEXT |  |  |  |
| `zinsen_berechnet` | REAL |  | 0 |  |
| `einreicher_id` | TEXT |  |  |  |
| `produkt_marke` | TEXT |  |  |  |
| `produkt_typ` | TEXT |  |  |  |
| `produkt_kategorie` | TEXT |  |  |  |
| `tage_seit_zinsbeginn` | INTEGER |  | 0 |  |

**Indizes:**
- `idx_fahrzeugfinanzierungen_rrdi`: rrdi
- `idx_fahrzeugfinanzierungen_finanzinstitut`: finanzinstitut
- `idx_fahrzeugfinanzierungen_aktiv`: aktiv
- `idx_fahrzeugfinanzierungen_finanzbank_id`: finanzbank_id
- `idx_fahrzeugfinanzierungen_vin`: vin

### `fahrzeugfinanzierungen_new` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `finanzbank_id` | INTEGER |  |  |  |
| `vin` | TEXT | ✓ |  |  |
| `vin_kurz` | TEXT |  |  |  |
| `finanzierungsnummer` | TEXT |  |  |  |
| `hersteller` | TEXT |  |  |  |
| `modell` | TEXT |  |  |  |
| `farbe` | TEXT |  |  |  |
| `finanzierungsstatus` | TEXT |  |  |  |
| `dokumentstatus` | TEXT |  |  |  |
| `produktfamilie` | TEXT |  |  |  |
| `produkt` | TEXT |  |  |  |
| `finanzierungsbetrag` | REAL |  |  |  |
| `aktueller_saldo` | REAL |  |  |  |
| `waehrung` | TEXT |  | 'EUR' |  |
| `zinsen_gesamt` | REAL |  | 0 |  |
| `zinsen_letzte_periode` | REAL |  | 0 |  |
| `zinsgutschriften_gesamt` | REAL |  | 0 |  |
| `gebuehren_gesamt` | REAL |  | 0 |  |
| `gebuehren_letzte_periode` | REAL |  | 0 |  |
| `vertragsbeginn` | DATE |  |  |  |
| `zinsbeginn` | DATE |  |  |  |
| `finanzierungsende` | DATE |  |  |  |
| `endfaelligkeit` | DATE |  |  |  |
| `lieferdatum` | DATE |  |  |  |
| `aktivierungsdatum` | DATE |  |  |  |
| `anlagedatum` | DATE |  |  |  |
| `rechnungsnummer` | TEXT |  |  |  |
| `rechnungsdatum` | DATE |  |  |  |
| `rechnungsbetrag` | REAL |  |  |  |
| `alter_finanzierung_tage` | INTEGER |  |  |  |
| `zinsfreiheit_tage` | INTEGER |  |  |  |
| `import_quelle` | TEXT |  |  |  |
| `import_datei` | TEXT |  |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `rohdaten` | TEXT |  |  |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `finanzinstitut` | TEXT |  |  |  |
| `rrdi` | TEXT |  |  |  |
| `zins_startdatum` | DATE |  |  |  |
| `alter_tage` | INTEGER |  |  |  |
| `original_betrag` | REAL |  |  |  |
| `datei_quelle` | TEXT |  |  |  |
| `abbezahlt` | REAL |  | 0 |  |
| `hsn` | TEXT |  |  |  |
| `tsn` | TEXT |  |  |  |

### `fibu_buchungen` (549,224 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `locosoft_doc_number` | BIGINT | ✓ |  |  |
| `locosoft_position` | BIGINT | ✓ |  |  |
| `accounting_date` | DATE | ✓ |  |  |
| `nominal_account` | INTEGER | ✓ |  |  |
| `amount` | REAL | ✓ |  |  |
| `debit_credit` | TEXT |  |  |  |
| `posting_text` | TEXT |  |  |  |
| `buchungstyp` | TEXT |  |  |  |
| `vehicle_reference` | TEXT |  |  |  |
| `synced_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `bank` | TEXT |  |  |  |
| `kategorie_erweitert` | TEXT |  |  |  |
| `wirtschaftsjahr` | TEXT |  |  |  |

**Indizes:**
- `idx_fibu_wirtschaftsjahr`: wirtschaftsjahr
- `idx_fibu_kategorie_erweitert`: kategorie_erweitert
- `idx_fibu_bank`: bank
- `idx_fibu_synced`: synced_at
- `idx_fibu_debit_credit`: debit_credit
- `idx_fibu_typ`: buchungstyp
- `idx_fibu_account`: nominal_account
- `idx_fibu_date`: accounting_date
- `sqlite_autoindex_fibu_buchungen_1`: locosoft_doc_number, locosoft_position

### `finanzierung_snapshots` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `fahrzeugfin_id` | INTEGER | ✓ |  |  |
| `snapshot_datum` | DATE | ✓ |  |  |
| `saldo` | REAL | ✓ |  |  |
| `finanzierungsstatus` | TEXT |  |  |  |
| `zinsen_gesamt` | REAL |  |  |  |
| `zinsen_periode` | REAL |  |  |  |
| `import_datei` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_fin_snapshots_datum`: snapshot_datum
- `idx_fin_snapshots_fahrzeug`: fahrzeugfin_id
- `sqlite_autoindex_finanzierung_snapshots_1`: fahrzeugfin_id, snapshot_datum

### `finanzierungsbanken` (3 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `bank_name` | TEXT | ✓ |  |  |
| `bank_typ` | TEXT | ✓ |  |  |
| `import_format` | TEXT | ✓ |  |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_finanzbanken_aktiv`: aktiv
- `idx_finanzbanken_typ`: bank_typ
- `sqlite_autoindex_finanzierungsbanken_1`: bank_name

### `holidays` (39 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `date` | DATE | ✓ |  |  |
| `name` | TEXT | ✓ |  |  |
| `bundesland` | TEXT |  | 'Bayern' |  |
| `type` | TEXT |  | 'gesetzlich' |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_holidays_bundesland`: bundesland
- `idx_holidays_date`: date
- `sqlite_autoindex_holidays_1`: date

### `import_log` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `import_typ` | TEXT | ✓ |  |  |
| `dateiname` | TEXT | ✓ |  |  |
| `dateipfad` | TEXT |  |  |  |
| `status` | TEXT | ✓ |  |  |
| `anzahl_zeilen_gelesen` | INTEGER |  | 0 |  |
| `anzahl_zeilen_importiert` | INTEGER |  | 0 |  |
| `anzahl_duplikate` | INTEGER |  | 0 |  |
| `anzahl_fehler` | INTEGER |  | 0 |  |
| `import_start` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `import_ende` | TIMESTAMP |  |  |  |
| `dauer_sekunden` | REAL |  |  |  |
| `fehlermeldungen` | TEXT |  |  |  |
| `notizen` | TEXT |  |  |  |

**Indizes:**
- `idx_import_log_datei`: dateiname
- `idx_import_log_status`: status
- `idx_import_log_datum`: import_start
- `idx_import_log_typ`: import_typ

### `konten` (12 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `bank_id` | INTEGER | ✓ |  |  |
| `kontonummer` | TEXT | ✓ |  |  |
| `iban` | TEXT |  |  |  |
| `bic` | TEXT |  |  |  |
| `kontoname` | TEXT | ✓ |  |  |
| `kontotyp` | TEXT |  | 'Girokonto' |  |
| `waehrung` | TEXT |  | 'EUR' |  |
| `inhaber` | TEXT |  |  |  |
| `kreditlinie` | REAL |  | 0 |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `eroeffnet_am` | DATE |  |  |  |
| `geschlossen_am` | DATE |  |  |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `kontoinhaber` | TEXT |  |  |  |
| `verwendungszweck` | TEXT |  |  |  |
| `ist_operativ` | INTEGER |  | 1 |  |
| `anzeige_gruppe` | TEXT |  |  |  |
| `sort_order` | INTEGER |  | 999 |  |
| `sollzins` | REAL |  |  |  |
| `habenzins` | REAL |  | 0 |  |
| `kreditlimit` | REAL |  | 0 |  |
| `mindest_saldo` | REAL |  | 0 |  |
| `umbuchung_moeglich` | BOOLEAN |  | 1 |  |
| `firma` | TEXT |  |  |  |

**Indizes:**
- `idx_konten_ist_operativ`: ist_operativ
- `idx_konten_anzeige_gruppe`: anzeige_gruppe
- `idx_konten_kontonummer`: kontonummer
- `idx_konten_iban`: iban
- `idx_konten_aktiv`: aktiv
- `idx_konten_bank`: bank_id
- `sqlite_autoindex_konten_1`: bank_id, kontonummer

### `konto_snapshots` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `konto_id` | INTEGER | ✓ |  |  |
| `stichtag` | DATE | ✓ |  |  |
| `kapitalsaldo` | REAL | ✓ |  |  |
| `kreditlinie` | REAL |  |  |  |
| `ausnutzung_prozent` | REAL |  |  |  |
| `zinssatz` | REAL |  |  |  |
| `zinstyp` | TEXT |  |  |  |
| `pdf_quelle` | TEXT |  |  |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_snapshots_stichtag`: stichtag
- `idx_snapshots_konto`: konto_id
- `sqlite_autoindex_konto_snapshots_1`: konto_id, stichtag

### `kreditlinien` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `rrdi` | TEXT | ✓ |  |  |
| `marke` | TEXT |  |  |  |
| `gruppe` | TEXT |  |  |  |
| `haendlername` | TEXT |  |  |  |
| `steuernummer` | TEXT |  |  |  |
| `kl_neuwagen` | REAL |  | 0 |  |
| `kl_vorfuehrwagen` | REAL |  | 0 |  |
| `kl_gebrauchtwagen` | REAL |  | 0 |  |
| `kl_leasingruecklaeufer` | REAL |  | 0 |  |
| `kl_remarketing` | REAL |  | 0 |  |
| `kl_anschlussfinanzierung` | REAL |  | 0 |  |
| `kl_ersatzteile` | REAL |  | 0 |  |
| `kl_direktkonto` | REAL |  | 0 |  |
| `kl_vorauszahlung` | REAL |  | 0 |  |
| `kreditlinie_total` | REAL | ✓ |  |  |
| `saldo_total` | REAL | ✓ |  |  |
| `saldo_neuwagen` | REAL |  | 0 |  |
| `saldo_vorfuehrwagen` | REAL |  | 0 |  |
| `saldo_gebrauchtwagen` | REAL |  | 0 |  |
| `saldo_leasingruecklaeufer` | REAL |  | 0 |  |
| `saldo_remarketing` | REAL |  | 0 |  |
| `saldo_anschlussfinanzierung` | REAL |  | 0 |  |
| `saldo_ersatzteile` | REAL |  | 0 |  |
| `saldo_direktkonto` | REAL |  | 0 |  |
| `saldo_vorauszahlung` | REAL |  | 0 |  |
| `import_datei` | TEXT | ✓ |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktiv` | BOOLEAN |  | 1 |  |
| `notizen` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_kreditlinien_aktiv`: aktiv
- `idx_kreditlinien_marke`: marke
- `idx_kreditlinien_rrdi`: rrdi
- `sqlite_autoindex_kreditlinien_1`: rrdi, marke

### `kreditlinien_snapshots` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `kreditlinie_id` | INTEGER | ✓ |  |  |
| `snapshot_datum` | DATE | ✓ |  |  |
| `kreditlinie_total` | REAL | ✓ |  |  |
| `saldo_total` | REAL | ✓ |  |  |
| `import_datei` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_kl_snapshots_datum`: snapshot_datum
- `idx_kl_snapshots_kreditlinie`: kreditlinie_id
- `sqlite_autoindex_kreditlinien_snapshots_1`: kreditlinie_id, snapshot_datum

### `ldap_employee_mapping` (62 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `ldap_username` | TEXT | ✓ |  |  |
| `ldap_email` | TEXT |  |  |  |
| `employee_id` | INTEGER | ✓ |  |  |
| `locosoft_id` | INTEGER | ✓ |  |  |
| `verified` | INTEGER |  | 0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_ldap_employee_mapping_1`: ldap_username

### `leasys_vehicle_cache` (168 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `brand` | TEXT | ✓ |  |  |
| `fuel` | TEXT |  |  |  |
| `ma_id` | TEXT | ✓ |  |  |
| `data` | TEXT | ✓ |  |  |
| `vehicle_count` | INTEGER |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_leasys_cache_lookup`: brand, fuel, ma_id
- `sqlite_autoindex_leasys_vehicle_cache_1`: brand, fuel, ma_id

### `loco_absence_calendar` (15,307 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `employee_number` | INTEGER |  |  |  |
| `date` | TEXT |  |  |  |
| `unique_dummy` | INTEGER |  |  |  |
| `type` | TEXT |  |  |  |
| `is_payed` | INTEGER |  |  |  |
| `day_contingent` | REAL |  |  |  |
| `reason_type` | INTEGER |  |  |  |
| `reason` | TEXT |  |  |  |
| `booking_flag` | TEXT |  |  |  |
| `time_from` | TEXT |  |  |  |
| `time_to` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_absence_calendar_employee_number`: employee_number

### `loco_absence_reasons` (23 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `is_annual_vacation` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_absence_reasons_id`: id

### `loco_absence_types` (2 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_accounts_characteristics` (2 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `skr51_branch` | INTEGER |  |  |  |
| `skr51_make` | INTEGER |  |  |  |
| `skr51_cost_center` | INTEGER |  |  |  |
| `skr51_sales_channel` | INTEGER |  |  |  |
| `skr51_cost_unit` | INTEGER |  |  |  |
| `skr51_branch_name` | TEXT |  |  |  |
| `skr51_make_description` | TEXT |  |  |  |
| `skr51_cost_center_name` | TEXT |  |  |  |
| `skr51_sales_channel_name` | TEXT |  |  |  |
| `skr51_cost_unit_name` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_accounts_characteristics_subsidiary_to_company_ref`: subsidiary_to_company_ref

### `loco_appointments` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `appointment_type` | INTEGER |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `vehicle_number` | INTEGER |  |  |  |
| `comment` | TEXT |  |  |  |
| `created_by_employee` | INTEGER |  |  |  |
| `created_timestamp` | TEXT |  |  |  |
| `modified_by_employee` | INTEGER |  |  |  |
| `modified_timestamp` | TEXT |  |  |  |
| `locked_by_employee` | INTEGER |  |  |  |
| `blocked_timestamp` | TEXT |  |  |  |
| `bring_timestamp` | TEXT |  |  |  |
| `return_timestamp` | TEXT |  |  |  |
| `pseudo_customer_name` | TEXT |  |  |  |
| `pseudo_customer_country` | TEXT |  |  |  |
| `pseudo_customer_zip_code` | TEXT |  |  |  |
| `pseudo_customer_home_city` | TEXT |  |  |  |
| `pseudo_customer_home_street` | TEXT |  |  |  |
| `pseudo_vehicle_make_number` | INTEGER |  |  |  |
| `pseudo_vehicle_make_text` | TEXT |  |  |  |
| `pseudo_model_code` | TEXT |  |  |  |
| `pseudo_model_text` | TEXT |  |  |  |
| `pseudo_license_plate` | TEXT |  |  |  |
| `pseudo_vin` | TEXT |  |  |  |
| `order_number` | INTEGER |  |  |  |
| `is_customer_reminder_allowed` | INTEGER |  |  |  |
| `customer_reminder_type` | TEXT |  |  |  |
| `customer_reminder_timestamp` | TEXT |  |  |  |
| `bring_duration` | INTEGER |  |  |  |
| `bring_employee_no` | INTEGER |  |  |  |
| `return_duration` | INTEGER |  |  |  |
| `return_employee_no` | INTEGER |  |  |  |
| `customer_pickup_bring` | INTEGER |  |  |  |
| `is_general_inspection_service` | INTEGER |  |  |  |
| `urgency` | INTEGER |  |  |  |
| `vehicle_status` | INTEGER |  |  |  |
| `progress_status` | INTEGER |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_appointments_customer_number`: customer_number
- `idx_loco_appointments_id`: id

### `loco_appointments_text` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `appointment_id` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |

### `loco_charge_type_descriptions` (100 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_charge_types` (400 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `timeunit_rate` | REAL |  |  |  |
| `department` | INTEGER |  |  |  |

### `loco_clearing_delay_types` (10 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_codes_customer_def` (12 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `is_defined_by_dms` | INTEGER |  |  |  |
| `format` | TEXT |  |  |  |
| `length` | INTEGER |  |  |  |
| `decimal` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_codes_customer_list` (44,722 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `value_format` | TEXT |  |  |  |
| `value_text` | TEXT |  |  |  |
| `value_numeric` | REAL |  |  |  |
| `value_date` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_codes_customer_list_customer_number`: customer_number

### `loco_codes_vehicle_date` (6,197 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `vehicle_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `date` | TEXT |  |  |  |

### `loco_codes_vehicle_date_def` (15 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `is_defined_by_dms` | INTEGER |  |  |  |
| `month_increase_factor` | INTEGER |  |  |  |
| `show_in_211_from_or_to` | TEXT |  |  |  |
| `is_backdate_on_exceeding` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_codes_vehicle_def` (47 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `is_defined_by_dms` | INTEGER |  |  |  |
| `format` | TEXT |  |  |  |
| `length` | INTEGER |  |  |  |
| `decimal` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_codes_vehicle_list` (27,702 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `vehicle_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `value_format` | TEXT |  |  |  |
| `value_text` | TEXT |  |  |  |
| `value_numeric` | REAL |  |  |  |
| `value_date` | TEXT |  |  |  |

### `loco_codes_vehicle_mileage` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `vehicle_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `kilometer` | INTEGER |  |  |  |

### `loco_codes_vehicle_mileage_def` (2 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `is_defined_by_dms` | INTEGER |  |  |  |
| `mileage_increase_factor` | INTEGER |  |  |  |
| `show_in_211_from_or_to` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_com_number_types` (18 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `typ` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `is_office_number` | INTEGER |  |  |  |

### `loco_configuration` (38 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | TEXT |  |  |  |
| `value_numeric` | INTEGER |  |  |  |
| `value_text` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_configuration_numeric` (1,433 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `parameter_number` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `text_value` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_countries` (43 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `iso3166_alpha2` | TEXT |  |  |  |

### `loco_customer_codes` (21 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_customer_com_numbers` (76,415 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `counter` | INTEGER |  |  |  |
| `com_type` | TEXT |  |  |  |
| `is_reference` | INTEGER |  |  |  |
| `only_on_1st_tab` | INTEGER |  |  |  |
| `address` | TEXT |  |  |  |
| `has_contact_person_fields` | INTEGER |  |  |  |
| `contact_salutation` | TEXT |  |  |  |
| `contact_firstname` | TEXT |  |  |  |
| `contact_lastname` | TEXT |  |  |  |
| `contact_description` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |
| `search_address` | TEXT |  |  |  |
| `phone_number` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_customer_com_numbers_customer_number`: customer_number

### `loco_customer_contact_log_pemissions` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `case_number` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_customer_contact_log_pemissions_customer_number`: customer_number

### `loco_customer_profession_codes` (90 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_customer_supplier_bank_information` (993 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `iban` | TEXT |  |  |  |
| `swift` | TEXT |  |  |  |
| `sepa_mandate_start_date` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_customer_supplier_bank_information_customer_number`: customer_number

### `loco_customer_to_customercodes` (3,260 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `customer_code` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_customer_to_customercodes_customer_number`: customer_number

### `loco_customer_to_professioncodes` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `profession_code` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_customer_to_professioncodes_customer_number`: customer_number

### `loco_customers_suppliers` (53,524 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `customer_number` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `is_supplier` | INTEGER |  |  |  |
| `is_natural_person` | INTEGER |  |  |  |
| `is_dummy_customer` | INTEGER |  |  |  |
| `salutation_code` | TEXT |  |  |  |
| `name_prefix` | TEXT |  |  |  |
| `first_name` | TEXT |  |  |  |
| `family_name` | TEXT |  |  |  |
| `name_postfix` | TEXT |  |  |  |
| `country_code` | TEXT |  |  |  |
| `zip_code` | TEXT |  |  |  |
| `home_city` | TEXT |  |  |  |
| `home_street` | TEXT |  |  |  |
| `contact_salutation_code` | TEXT |  |  |  |
| `contact_family_name` | TEXT |  |  |  |
| `contact_first_name` | TEXT |  |  |  |
| `contact_note` | TEXT |  |  |  |
| `contact_personal_known` | INTEGER |  |  |  |
| `parts_rebate_group_buy` | INTEGER |  |  |  |
| `parts_rebate_group_sell` | INTEGER |  |  |  |
| `rebate_labour_percent` | REAL |  |  |  |
| `rebate_material_percent` | REAL |  |  |  |
| `rebate_new_vehicles_percent` | REAL |  |  |  |
| `cash_discount_percent` | REAL |  |  |  |
| `vat_id_number` | TEXT |  |  |  |
| `vat_id_number_checked_date` | TEXT |  |  |  |
| `vat_id_free_code_1` | INTEGER |  |  |  |
| `vat_id_free_code_2` | INTEGER |  |  |  |
| `birthday` | TEXT |  |  |  |
| `last_contact` | TEXT |  |  |  |
| `preferred_com_number_type` | TEXT |  |  |  |
| `created_date` | TEXT |  |  |  |
| `created_employee_no` | INTEGER |  |  |  |
| `updated_date` | TEXT |  |  |  |
| `updated_employee_no` | INTEGER |  |  |  |
| `name_updated_date` | TEXT |  |  |  |
| `name_updated_employee_no` | INTEGER |  |  |  |
| `sales_assistant_employee_no` | INTEGER |  |  |  |
| `service_assistant_employee_no` | INTEGER |  |  |  |
| `parts_assistant_employee_no` | INTEGER |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |
| `location_latitude` | REAL |  |  |  |
| `location_longitude` | REAL |  |  |  |
| `order_classification_flag` | TEXT |  |  |  |
| `access_limit` | INTEGER |  |  |  |
| `fullname_vector` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_customers_suppliers_customer_number`: customer_number

### `loco_dealer_sales_aid` (3,599 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `claimed_amount` | REAL |  |  |  |
| `available_until` | TEXT |  |  |  |
| `granted_amount` | REAL |  |  |  |
| `was_paid_on` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |

### `loco_dealer_sales_aid_bonus` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `claimed_amount` | REAL |  |  |  |
| `available_until` | TEXT |  |  |  |
| `granted_amount` | REAL |  |  |  |
| `was_paid_on` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |

### `loco_dealer_vehicles` (5,310 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `vehicle_number` | INTEGER |  |  |  |
| `location` | TEXT |  |  |  |
| `buyer_customer_no` | INTEGER |  |  |  |
| `deregistration_date` | TEXT |  |  |  |
| `refinancing_start_date` | TEXT |  |  |  |
| `refinancing_end_date` | TEXT |  |  |  |
| `refinancing_value` | REAL |  |  |  |
| `refinancing_refundment` | REAL |  |  |  |
| `refinancing_bank_customer_no` | INTEGER |  |  |  |
| `refinanc_interest_free_date` | TEXT |  |  |  |
| `in_subsidiary` | INTEGER |  |  |  |
| `in_buy_salesman_number` | INTEGER |  |  |  |
| `in_buy_order_no` | TEXT |  |  |  |
| `in_buy_order_no_date` | TEXT |  |  |  |
| `in_buy_invoice_no` | TEXT |  |  |  |
| `in_buy_invoice_no_date` | TEXT |  |  |  |
| `in_buy_edp_order_no` | TEXT |  |  |  |
| `in_buy_edp_order_no_date` | TEXT |  |  |  |
| `in_is_trade_in_ken` | TEXT |  |  |  |
| `in_is_trade_in_kom` | INTEGER |  |  |  |
| `in_used_vehicle_buy_type` | TEXT |  |  |  |
| `in_buy_list_price` | REAL |  |  |  |
| `in_arrival_date` | TEXT |  |  |  |
| `in_expected_arrival_date` | TEXT |  |  |  |
| `in_accounting_document_type` | TEXT |  |  |  |
| `in_accounting_document_number` | INTEGER |  |  |  |
| `in_accounting_document_date` | TEXT |  |  |  |
| `in_acntg_exceptional_group` | TEXT |  |  |  |
| `in_acntg_cost_unit_new_vehicle` | REAL |  |  |  |
| `in_accounting_make` | REAL |  |  |  |
| `in_registration_reference` | TEXT |  |  |  |
| `in_expected_repair_cost` | REAL |  |  |  |
| `in_order_status` | TEXT |  |  |  |
| `out_subsidiary` | INTEGER |  |  |  |
| `out_is_ready_for_sale` | INTEGER |  |  |  |
| `out_ready_for_sale_date` | TEXT |  |  |  |
| `out_sale_type` | TEXT |  |  |  |
| `out_sales_contract_number` | TEXT |  |  |  |
| `out_sales_contract_date` | TEXT |  |  |  |
| `out_is_sales_contract_confrmed` | INTEGER |  |  |  |
| `out_salesman_number_1` | INTEGER |  |  |  |
| `out_salesman_number_2` | INTEGER |  |  |  |
| `out_desired_shipment_date` | TEXT |  |  |  |
| `out_is_registration_included` | INTEGER |  |  |  |
| `out_recommended_retail_price` | REAL |  |  |  |
| `out_extra_expenses` | REAL |  |  |  |
| `out_sale_price` | REAL |  |  |  |
| `out_sale_price_dealer` | REAL |  |  |  |
| `out_sale_price_minimum` | REAL |  |  |  |
| `out_sale_price_internet` | REAL |  |  |  |
| `out_estimated_invoice_value` | REAL |  |  |  |
| `out_discount_percent_vehicle` | REAL |  |  |  |
| `out_discount_percent_accessory` | REAL |  |  |  |
| `out_order_number` | INTEGER |  |  |  |
| `out_invoice_type` | INTEGER |  |  |  |
| `out_invoice_number` | INTEGER |  |  |  |
| `out_invoice_date` | TEXT |  |  |  |
| `out_deposit_invoice_type` | INTEGER |  |  |  |
| `out_deposit_invoice_number` | INTEGER |  |  |  |
| `out_deposit_value` | REAL |  |  |  |
| `out_license_plate` | TEXT |  |  |  |
| `out_make_number` | INTEGER |  |  |  |
| `out_model_code` | TEXT |  |  |  |
| `out_license_plate_country` | TEXT |  |  |  |
| `out_license_plate_season` | TEXT |  |  |  |
| `calc_basic_charge` | REAL |  |  |  |
| `calc_accessory` | REAL |  |  |  |
| `calc_extra_expenses` | REAL |  |  |  |
| `calc_insurance` | REAL |  |  |  |
| `calc_usage_value_encr_external` | REAL |  |  |  |
| `calc_usage_value_encr_internal` | REAL |  |  |  |
| `calc_usage_value_encr_other` | REAL |  |  |  |
| `calc_total_writedown` | REAL |  |  |  |
| `calc_cost_percent_stockingdays` | REAL |  |  |  |
| `calc_interest_percent_stkdays` | REAL |  |  |  |
| `calc_actual_payed_interest` | REAL |  |  |  |
| `calc_commission_for_arranging` | REAL |  |  |  |
| `calc_commission_for_salesman` | REAL |  |  |  |
| `calc_cost_internal_invoices` | REAL |  |  |  |
| `calc_cost_other` | REAL |  |  |  |
| `calc_sales_aid` | REAL |  |  |  |
| `calc_sales_aid_finish` | REAL |  |  |  |
| `calc_sales_aid_bonus` | REAL |  |  |  |
| `calc_returns_workshop` | REAL |  |  |  |
| `exclusive_reserved_employee_no` | INTEGER |  |  |  |
| `exclusive_reserved_until` | TEXT |  |  |  |
| `pre_owned_car_code` | TEXT |  |  |  |
| `is_sale_internet` | INTEGER |  |  |  |
| `is_sale_prohibit` | INTEGER |  |  |  |
| `is_agency_business` | INTEGER |  |  |  |
| `is_rental_or_school_vehicle` | INTEGER |  |  |  |
| `previous_owner_number` | INTEGER |  |  |  |
| `mileage_km` | INTEGER |  |  |  |
| `memo` | TEXT |  |  |  |
| `keys_box_number` | INTEGER |  |  |  |
| `last_change_date` | TEXT |  |  |  |
| `last_change_employee_no` | INTEGER |  |  |  |
| `created_date` | TEXT |  |  |  |
| `created_employee_no` | INTEGER |  |  |  |
| `has_financing_example` | INTEGER |  |  |  |
| `has_leasing_example_ref` | INTEGER |  |  |  |
| `deactivated_by_employee_no` | INTEGER |  |  |  |
| `deactivated_date` | TEXT |  |  |  |
| `access_limit` | INTEGER |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |

### `loco_document_types` (13 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `document_type_in_journal` | TEXT |  |  |  |
| `document_type_description` | TEXT |  |  |  |

### `loco_employees` (114 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `is_latest_record` | INTEGER |  |  |  |
| `employee_number` | INTEGER |  |  |  |
| `validity_date` | TEXT |  |  |  |
| `next_validity_date` | TEXT |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `has_constant_salary` | INTEGER |  |  |  |
| `name` | TEXT |  |  |  |
| `initials` | TEXT |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `employee_personnel_no` | INTEGER |  |  |  |
| `mechanic_number` | INTEGER |  |  |  |
| `salesman_number` | INTEGER |  |  |  |
| `is_business_executive` | INTEGER |  |  |  |
| `is_master_craftsman` | INTEGER |  |  |  |
| `is_customer_reception` | INTEGER |  |  |  |
| `employment_date` | TEXT |  |  |  |
| `termination_date` | TEXT |  |  |  |
| `leave_date` | TEXT |  |  |  |
| `is_flextime` | INTEGER |  |  |  |
| `break_time_registration` | TEXT |  |  |  |
| `productivity_factor` | REAL |  |  |  |
| `schedule_index` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_employees_employee_number`: employee_number
- `idx_loco_employees_customer_number`: customer_number

### `loco_employees_breaktimes` (392 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `is_latest_record` | INTEGER |  |  |  |
| `employee_number` | INTEGER |  |  |  |
| `validity_date` | TEXT |  |  |  |
| `dayofweek` | INTEGER |  |  |  |
| `break_start` | REAL |  |  |  |
| `break_end` | REAL |  |  |  |

**Indizes:**
- `idx_loco_employees_breaktimes_employee_number`: employee_number

### `loco_employees_group_mapping` (126 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `employee_number` | INTEGER |  |  |  |
| `validity_date` | TEXT |  |  |  |
| `grp_code` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_employees_group_mapping_employee_number`: employee_number

### `loco_employees_history` (124 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `is_latest_record` | INTEGER |  |  |  |
| `employee_number` | INTEGER |  |  |  |
| `validity_date` | TEXT |  |  |  |
| `next_validity_date` | TEXT |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `has_constant_salary` | INTEGER |  |  |  |
| `name` | TEXT |  |  |  |
| `initials` | TEXT |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `employee_personnel_no` | INTEGER |  |  |  |
| `mechanic_number` | INTEGER |  |  |  |
| `salesman_number` | INTEGER |  |  |  |
| `is_business_executive` | INTEGER |  |  |  |
| `is_master_craftsman` | INTEGER |  |  |  |
| `is_customer_reception` | INTEGER |  |  |  |
| `employment_date` | TEXT |  |  |  |
| `termination_date` | TEXT |  |  |  |
| `leave_date` | TEXT |  |  |  |
| `is_flextime` | INTEGER |  |  |  |
| `break_time_registration` | TEXT |  |  |  |
| `productivity_factor` | REAL |  |  |  |
| `schedule_index` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_employees_history_employee_number`: employee_number
- `idx_loco_employees_history_customer_number`: customer_number

### `loco_employees_worktimes` (487 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `is_latest_record` | INTEGER |  |  |  |
| `employee_number` | INTEGER |  |  |  |
| `validity_date` | TEXT |  |  |  |
| `dayofweek` | INTEGER |  |  |  |
| `work_duration` | REAL |  |  |  |
| `worktime_start` | REAL |  |  |  |
| `worktime_end` | REAL |  |  |  |

**Indizes:**
- `idx_loco_employees_worktimes_employee_number`: employee_number

### `loco_external_customer_references` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `api_type` | TEXT |  |  |  |
| `api_id` | TEXT |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `reference` | TEXT |  |  |  |
| `last_received_time` | TEXT |  |  |  |
| `version` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_external_customer_references_customer_number`: customer_number

### `loco_external_reference_parties` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `api_type` | TEXT |  |  |  |
| `api_id` | TEXT |  |  |  |
| `make` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_financing_examples` (140 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  |  |
| `initial_payment` | REAL |  |  |  |
| `loan_amount` | REAL |  |  |  |
| `number_rates` | INTEGER |  |  |  |
| `annual_percentage_rate` | REAL |  |  |  |
| `debit_interest` | REAL |  |  |  |
| `debit_interest_type` | TEXT |  |  |  |
| `monthly_rate` | REAL |  |  |  |
| `differing_first_rate` | REAL |  |  |  |
| `last_rate` | REAL |  |  |  |
| `rate_insurance` | REAL |  |  |  |
| `acquisition_fee` | REAL |  |  |  |
| `total` | REAL |  |  |  |
| `interest_free_credit_until` | TEXT |  |  |  |
| `interest_free_credit_amount` | REAL |  |  |  |
| `due_date` | INTEGER |  |  |  |
| `due_date_last_rate` | INTEGER |  |  |  |
| `bank_customer_no` | INTEGER |  |  |  |
| `source` | TEXT |  |  |  |
| `referenced_dealer_vehicle_type` | TEXT |  |  |  |
| `referenced_dealer_vehicle_no` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_financing_examples_id`: id

### `loco_fuels` (18 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_invoice_types` (7 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_invoices` (54,219 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `invoice_type` | INTEGER |  |  |  |
| `invoice_number` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `order_number` | INTEGER |  |  |  |
| `paying_customer` | INTEGER |  |  |  |
| `invoice_date` | TEXT |  |  |  |
| `service_date` | TEXT |  |  |  |
| `is_canceled` | INTEGER |  |  |  |
| `cancelation_number` | INTEGER |  |  |  |
| `cancelation_date` | TEXT |  |  |  |
| `cancelation_employee` | INTEGER |  |  |  |
| `is_own_vehicle` | INTEGER |  |  |  |
| `is_credit` | INTEGER |  |  |  |
| `credit_invoice_type` | INTEGER |  |  |  |
| `credit_invoice_number` | INTEGER |  |  |  |
| `odometer_reading` | INTEGER |  |  |  |
| `creating_employee` | INTEGER |  |  |  |
| `internal_cost_account` | INTEGER |  |  |  |
| `vehicle_number` | INTEGER |  |  |  |
| `full_vat_basevalue` | REAL |  |  |  |
| `full_vat_percentage` | REAL |  |  |  |
| `full_vat_value` | REAL |  |  |  |
| `reduced_vat_basevalue` | REAL |  |  |  |
| `reduced_vat_percentage` | REAL |  |  |  |
| `reduced_vat_value` | REAL |  |  |  |
| `used_part_vat_value` | REAL |  |  |  |
| `job_amount_net` | REAL |  |  |  |
| `job_amount_gross` | REAL |  |  |  |
| `job_rebate` | REAL |  |  |  |
| `part_amount_net` | REAL |  |  |  |
| `part_amount_gross` | REAL |  |  |  |
| `part_rebate` | REAL |  |  |  |
| `part_disposal` | REAL |  |  |  |
| `total_gross` | REAL |  |  |  |
| `total_net` | REAL |  |  |  |
| `parts_rebate_group_sell` | INTEGER |  |  |  |
| `internal_created_time` | TEXT |  |  |  |
| `internal_canceled_time` | TEXT |  |  |  |
| `order_classification_flag` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_invoices_invoice_date`: invoice_date

### `loco_journal_accountings` (599,210 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `accounting_date` | TEXT |  |  |  |
| `document_type` | TEXT |  |  |  |
| `document_number` | INTEGER |  |  |  |
| `position_in_document` | INTEGER |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `nominal_account_number` | INTEGER |  |  |  |
| `is_balanced` | TEXT |  |  |  |
| `clearing_number` | INTEGER |  |  |  |
| `document_date` | TEXT |  |  |  |
| `posted_value` | INTEGER |  |  |  |
| `debit_or_credit` | TEXT |  |  |  |
| `posted_count` | INTEGER |  |  |  |
| `branch_number` | INTEGER |  |  |  |
| `customer_contra_account` | INTEGER |  |  |  |
| `nominal_contra_account` | INTEGER |  |  |  |
| `contra_account_text` | TEXT |  |  |  |
| `account_form_page_number` | INTEGER |  |  |  |
| `account_form_page_line` | INTEGER |  |  |  |
| `serial_number_each_month` | TEXT |  |  |  |
| `employee_number` | INTEGER |  |  |  |
| `invoice_date` | TEXT |  |  |  |
| `invoice_number` | TEXT |  |  |  |
| `dunning_level` | TEXT |  |  |  |
| `last_dunning_date` | TEXT |  |  |  |
| `journal_page` | INTEGER |  |  |  |
| `journal_line` | INTEGER |  |  |  |
| `cash_discount` | INTEGER |  |  |  |
| `term_of_payment` | INTEGER |  |  |  |
| `posting_text` | TEXT |  |  |  |
| `vehicle_reference` | TEXT |  |  |  |
| `vat_id_number` | TEXT |  |  |  |
| `account_statement_number` | INTEGER |  |  |  |
| `account_statement_page` | INTEGER |  |  |  |
| `vat_key` | TEXT |  |  |  |
| `days_for_cash_discount` | INTEGER |  |  |  |
| `day_of_actual_accounting` | TEXT |  |  |  |
| `skr51_branch` | INTEGER |  |  |  |
| `skr51_make` | INTEGER |  |  |  |
| `skr51_cost_center` | INTEGER |  |  |  |
| `skr51_sales_channel` | INTEGER |  |  |  |
| `skr51_cost_unit` | INTEGER |  |  |  |
| `previously_used_account_no` | TEXT |  |  |  |
| `free_form_accounting_text` | TEXT |  |  |  |
| `free_form_document_text` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_journal_accountings_invoice_date`: invoice_date
- `idx_loco_journal_accountings_employee_number`: employee_number
- `idx_loco_journal_accountings_nominal_account_number`: nominal_account_number
- `idx_loco_journal_accountings_branch_number`: branch_number
- `idx_loco_journal_accountings_subsidiary_to_company_ref`: subsidiary_to_company_ref
- `idx_loco_journal_accountings_document_date`: document_date
- `idx_loco_journal_accountings_accounting_date`: accounting_date
- `idx_loco_journal_accountings_vehicle_reference`: vehicle_reference
- `idx_loco_journal_accountings_customer_number`: customer_number
- `idx_loco_journal_accountings_document_number`: document_number

### `loco_labour_types` (30 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_labours` (281,117 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `order_number` | INTEGER |  |  |  |
| `order_position` | INTEGER |  |  |  |
| `order_position_line` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `is_invoiced` | INTEGER |  |  |  |
| `invoice_type` | INTEGER |  |  |  |
| `invoice_number` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |
| `mechanic_no` | INTEGER |  |  |  |
| `labour_operation_id` | TEXT |  |  |  |
| `is_nominal` | INTEGER |  |  |  |
| `time_units` | REAL |  |  |  |
| `net_price_in_order` | REAL |  |  |  |
| `rebate_percent` | REAL |  |  |  |
| `goodwill_percent` | REAL |  |  |  |
| `charge_type` | INTEGER |  |  |  |
| `text_line` | TEXT |  |  |  |
| `usage_value` | REAL |  |  |  |
| `negative_flag` | TEXT |  |  |  |
| `labour_type` | TEXT |  |  |  |

### `loco_labours_groups` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `source_number` | INTEGER |  |  |  |
| `labour_number_range` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `source` | TEXT |  |  |  |

### `loco_labours_master` (211,786 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `source_number` | INTEGER |  |  |  |
| `labour_number` | TEXT |  |  |  |
| `mapping_code` | TEXT |  |  |  |
| `text` | TEXT |  |  |  |
| `source` | TEXT |  |  |  |
| `text_vector` | TEXT |  |  |  |

### `loco_leasing_examples` (355 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  |  |
| `number_rates` | INTEGER |  |  |  |
| `annual_mileage` | INTEGER |  |  |  |
| `special_payment` | REAL |  |  |  |
| `calculation_basis` | REAL |  |  |  |
| `calculation_basis_factor` | REAL |  |  |  |
| `gross_residual_value` | REAL |  |  |  |
| `gross_residual_value_factor` | REAL |  |  |  |
| `monthly_rate` | REAL |  |  |  |
| `exceeding_mileage` | REAL |  |  |  |
| `under_usage_mileage` | REAL |  |  |  |
| `bank_customer_no` | INTEGER |  |  |  |
| `source` | TEXT |  |  |  |
| `referenced_dealer_vehicle_type` | TEXT |  |  |  |
| `referenced_dealer_vehicle_no` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_leasing_examples_id`: id

### `loco_makes` (48 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `make_number` | INTEGER |  |  |  |
| `is_actual_make` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |
| `group_name` | TEXT |  |  |  |
| `make_id_in_group` | TEXT |  |  |  |
| `internal_labour_group` | INTEGER |  |  |  |
| `is_production_year_visible` | INTEGER |  |  |  |
| `is_transmission_no_visible` | INTEGER |  |  |  |
| `is_engine_no_visible` | INTEGER |  |  |  |
| `is_ricambi_no_visible` | INTEGER |  |  |  |
| `ricambi_label` | TEXT |  |  |  |
| `is_preset_finance_stock_rate` | INTEGER |  |  |  |
| `rate_free_days_new_vehicle` | INTEGER |  |  |  |
| `rate_free_days_demo_vehicle` | INTEGER |  |  |  |
| `special_service_2_interval` | REAL |  |  |  |
| `special_service_3_interval` | REAL |  |  |  |

### `loco_nominal_accounts` (1,239 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `nominal_account_number` | INTEGER |  |  |  |
| `account_description` | TEXT |  |  |  |
| `is_profit_loss_account` | TEXT |  |  |  |
| `vat_key` | TEXT |  |  |  |
| `create_date` | TEXT |  |  |  |
| `create_employee_number` | INTEGER |  |  |  |
| `oldest_accountable_month` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_nominal_accounts_nominal_account_number`: nominal_account_number
- `idx_loco_nominal_accounts_subsidiary_to_company_ref`: subsidiary_to_company_ref

### `loco_order_classifications_def` (12 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `surcharge_type` | TEXT |  |  |  |
| `is_bulk_buyer` | INTEGER |  |  |  |
| `is_special_sale` | INTEGER |  |  |  |
| `target_group` | TEXT |  |  |  |
| `same_calculation_as_other` | TEXT |  |  |  |
| `special_price_rebate_type` | TEXT |  |  |  |
| `skr51_sales_channel` | INTEGER |  |  |  |
| `user_group` | TEXT |  |  |  |
| `with_disposal_cost` | INTEGER |  |  |  |

### `loco_orders` (41,048 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `number` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `order_date` | TEXT |  |  |  |
| `created_employee_no` | INTEGER |  |  |  |
| `updated_employee_no` | INTEGER |  |  |  |
| `estimated_inbound_time` | TEXT |  |  |  |
| `estimated_outbound_time` | TEXT |  |  |  |
| `order_print_date` | TEXT |  |  |  |
| `order_taking_employee_no` | INTEGER |  |  |  |
| `order_delivery_employee_no` | INTEGER |  |  |  |
| `vehicle_number` | INTEGER |  |  |  |
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `order_mileage` | INTEGER |  |  |  |
| `order_customer` | INTEGER |  |  |  |
| `paying_customer` | INTEGER |  |  |  |
| `parts_rebate_group_sell` | INTEGER |  |  |  |
| `clearing_delay_type` | TEXT |  |  |  |
| `urgency` | INTEGER |  |  |  |
| `has_empty_positions` | INTEGER |  |  |  |
| `has_open_positions` | INTEGER |  |  |  |
| `has_closed_positions` | INTEGER |  |  |  |
| `is_over_the_counter_order` | INTEGER |  |  |  |
| `order_classification_flag` | TEXT |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_orders_order_date`: order_date

### `loco_part_types` (19 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_parts` (142,151 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `order_number` | INTEGER |  |  |  |
| `order_position` | INTEGER |  |  |  |
| `order_position_line` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `is_invoiced` | INTEGER |  |  |  |
| `invoice_type` | INTEGER |  |  |  |
| `invoice_number` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |
| `mechanic_no` | INTEGER |  |  |  |
| `part_number` | TEXT |  |  |  |
| `stock_no` | INTEGER |  |  |  |
| `stock_removal_date` | TEXT |  |  |  |
| `amount` | REAL |  |  |  |
| `sum` | REAL |  |  |  |
| `rebate_percent` | REAL |  |  |  |
| `goodwill_percent` | REAL |  |  |  |
| `parts_type` | INTEGER |  |  |  |
| `text_line` | TEXT |  |  |  |
| `usage_value` | REAL |  |  |  |

### `loco_parts_additional_descriptions` (123,831 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `search_description` | TEXT |  |  |  |
| `description_vector` | TEXT |  |  |  |

### `loco_parts_inbound_delivery_notes` (66,429 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `supplier_number` | INTEGER |  |  |  |
| `year_key` | INTEGER |  |  |  |
| `number_main` | TEXT |  |  |  |
| `number_sub` | TEXT |  |  |  |
| `counter` | INTEGER |  |  |  |
| `purchase_invoice_year` | INTEGER |  |  |  |
| `purchase_invoice_number` | TEXT |  |  |  |
| `part_number` | TEXT |  |  |  |
| `stock_no` | INTEGER |  |  |  |
| `amount` | REAL |  |  |  |
| `delivery_note_date` | TEXT |  |  |  |
| `parts_order_number` | INTEGER |  |  |  |
| `parts_order_note` | TEXT |  |  |  |
| `deliverers_note` | TEXT |  |  |  |
| `referenced_order_number` | INTEGER |  |  |  |
| `referenced_order_position` | INTEGER |  |  |  |
| `referenced_order_line` | INTEGER |  |  |  |
| `is_veryfied` | INTEGER |  |  |  |
| `parts_order_type` | INTEGER |  |  |  |
| `rr_gross_price` | REAL |  |  |  |
| `purchase_total_net_price` | REAL |  |  |  |
| `parts_type` | INTEGER |  |  |  |
| `employee_number_veryfied` | INTEGER |  |  |  |
| `employee_number_imported` | INTEGER |  |  |  |
| `employee_number_last` | INTEGER |  |  |  |

### `loco_parts_master` (1,899,386 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `rebate_percent` | REAL |  |  |  |
| `package_unit_type` | TEXT |  |  |  |
| `package_size` | INTEGER |  |  |  |
| `delivery_size` | INTEGER |  |  |  |
| `weight` | REAL |  |  |  |
| `warranty_flag` | TEXT |  |  |  |
| `last_import_date` | TEXT |  |  |  |
| `price_valid_from_date` | TEXT |  |  |  |
| `storage_flag` | TEXT |  |  |  |
| `rebate_code` | TEXT |  |  |  |
| `parts_type` | INTEGER |  |  |  |
| `manufacturer_parts_type` | TEXT |  |  |  |
| `rr_price` | REAL |  |  |  |
| `price_surcharge_percent` | REAL |  |  |  |
| `selling_price_base_upe` | INTEGER |  |  |  |
| `is_price_based_on_usage_value` | INTEGER |  |  |  |
| `is_price_based_on_spcl_price` | INTEGER |  |  |  |
| `has_price_common_surcharge` | INTEGER |  |  |  |
| `allow_price_under_margin` | INTEGER |  |  |  |
| `allow_price_under_usage_value` | INTEGER |  |  |  |
| `is_stock_neutral` | INTEGER |  |  |  |
| `is_stock_neutral_usage_v` | INTEGER |  |  |  |
| `skr_carrier_flag` | REAL |  |  |  |
| `price_import_keeps_description` | INTEGER |  |  |  |
| `country_of_origin` | TEXT |  |  |  |
| `manufacturer_assembly_group` | TEXT |  |  |  |
| `has_information_ref` | INTEGER |  |  |  |
| `has_costs_ref` | INTEGER |  |  |  |
| `has_special_prices_ref` | INTEGER |  |  |  |
| `has_special_offer_ref` | INTEGER |  |  |  |
| `search_description` | TEXT |  |  |  |
| `description_vector` | TEXT |  |  |  |

### `loco_parts_rebate_codes_buy` (194 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `rebate_group_code` | INTEGER |  |  |  |
| `rebate_code` | TEXT |  |  |  |
| `rebate_code_counter` | INTEGER |  |  |  |
| `parts_type_boundary_from` | INTEGER |  |  |  |
| `parts_type_boundary_until` | INTEGER |  |  |  |
| `rebate_percent` | REAL |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_parts_rebate_codes_sell` (309 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `rebate_group_code` | INTEGER |  |  |  |
| `rebate_code` | TEXT |  |  |  |
| `rebate_code_counter` | INTEGER |  |  |  |
| `parts_type_boundary_from` | INTEGER |  |  |  |
| `parts_type_boundary_until` | INTEGER |  |  |  |
| `rebate_percent` | REAL |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_parts_rebate_groups_buy` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_parts_rebate_groups_sell` (8 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_parts_special_offer_prices` (27 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `is_active` | INTEGER |  |  |  |
| `valid_from_date` | TEXT |  |  |  |
| `valid_until_date` | TEXT |  |  |  |
| `price` | REAL |  |  |  |
| `addition_percent` | REAL |  |  |  |

### `loco_parts_special_prices` (128 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `order_classification_flag` | TEXT |  |  |  |
| `is_active` | INTEGER |  |  |  |
| `price` | REAL |  |  |  |
| `addition_percent` | REAL |  |  |  |

### `loco_parts_stock` (42,185 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `stock_no` | INTEGER |  |  |  |
| `storage_location_1` | TEXT |  |  |  |
| `storage_location_2` | TEXT |  |  |  |
| `usage_value` | REAL |  |  |  |
| `stock_level` | REAL |  |  |  |
| `stock_allocated` | REAL |  |  |  |
| `minimum_stock_level` | REAL |  |  |  |
| `has_warn_on_below_min_level` | INTEGER |  |  |  |
| `maximum_stock_level` | INTEGER |  |  |  |
| `stop_order_flag` | TEXT |  |  |  |
| `revenue_account_group` | TEXT |  |  |  |
| `average_sales_statstic` | REAL |  |  |  |
| `sales_current_year` | REAL |  |  |  |
| `sales_previous_year` | REAL |  |  |  |
| `total_buy_value` | REAL |  |  |  |
| `total_sell_value` | REAL |  |  |  |
| `provider_flag` | TEXT |  |  |  |
| `last_outflow_date` | TEXT |  |  |  |
| `last_inflow_date` | TEXT |  |  |  |
| `unevaluated_inflow_positions` | INTEGER |  |  |  |
| `is_disabled_in_parts_platforms` | INTEGER |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |

### `loco_parts_supplier_numbers` (35,394 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `part_number` | TEXT |  |  |  |
| `external_number` | TEXT |  |  |  |

### `loco_privacy_channels` (12 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `channel_code` | TEXT |  |  |  |
| `is_business` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_privacy_details` (117,852 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `internal_id` | INTEGER |  |  |  |
| `scope_code` | TEXT |  |  |  |
| `channel_code` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_privacy_details_subsidiary_to_company_ref`: subsidiary_to_company_ref

### `loco_privacy_protection_consent` (13,838 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `internal_id` | INTEGER |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `make_name` | TEXT |  |  |  |
| `validity_date_start` | TEXT |  |  |  |
| `validity_date_end` | TEXT |  |  |  |
| `created_timestamp` | TEXT |  |  |  |
| `created_employee_no` | INTEGER |  |  |  |
| `last_change_timestamp` | TEXT |  |  |  |
| `last_change_employee_no` | INTEGER |  |  |  |
| `first_ackno_timestamp` | TEXT |  |  |  |
| `first_ackno_employee_no` | INTEGER |  |  |  |
| `last_ackno_timestamp` | TEXT |  |  |  |
| `last_ackno_employee_no` | INTEGER |  |  |  |
| `first_consent_timestamp` | TEXT |  |  |  |
| `first_consent_employee_no` | INTEGER |  |  |  |
| `last_consent_timestamp` | TEXT |  |  |  |
| `last_consent_employee_no` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_privacy_protection_consent_subsidiary_to_company_ref`: subsidiary_to_company_ref
- `idx_loco_privacy_protection_consent_customer_number`: customer_number

### `loco_privacy_scopes` (3 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `scope_code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_salutations` (10 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `main_salutation` | TEXT |  |  |  |
| `title` | TEXT |  |  |  |
| `salutation_in_forms` | TEXT |  |  |  |
| `receiver_salutation` | TEXT |  |  |  |
| `full_salutation` | TEXT |  |  |  |
| `multiline_line_1` | TEXT |  |  |  |
| `multiline_line_2` | TEXT |  |  |  |

### `loco_subsidiaries` (4 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |
| `subsidiary_to_company_ref` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_subsidiaries_subsidiary_to_company_ref`: subsidiary_to_company_ref

### `loco_time_types` (4 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_times` (188,877 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `employee_number` | INTEGER |  |  |  |
| `order_number` | INTEGER |  |  |  |
| `start_time` | TEXT |  |  |  |
| `type` | INTEGER |  |  |  |
| `order_positions` | TEXT |  |  |  |
| `order_position` | INTEGER |  |  |  |
| `order_position_line` | INTEGER |  |  |  |
| `end_time` | TEXT |  |  |  |
| `duration_minutes` | INTEGER |  |  |  |
| `exact_duration_seconds` | INTEGER |  |  |  |
| `duration` | TEXT |  |  |  |
| `is_historic` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_times_employee_number`: employee_number

### `loco_tire_storage` (4,788 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `case_number` | INTEGER |  |  |  |
| `customer_number` | INTEGER |  |  |  |
| `vehicle_number` | INTEGER |  |  |  |
| `order_number` | INTEGER |  |  |  |
| `is_historic` | INTEGER |  |  |  |
| `is_planned` | INTEGER |  |  |  |
| `start_date` | TEXT |  |  |  |
| `scheduled_end_date` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |
| `stock_no` | INTEGER |  |  |  |
| `date_of_removal` | TEXT |  |  |  |
| `removal_employee_no` | INTEGER |  |  |  |
| `price` | REAL |  |  |  |
| `pressure_front` | REAL |  |  |  |
| `pressure_rear` | REAL |  |  |  |
| `torque` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_tire_storage_customer_number`: customer_number

### `loco_tire_storage_accessories` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `case_number` | INTEGER |  |  |  |
| `internal_counter` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |
| `manufacturer` | TEXT |  |  |  |
| `description_1` | TEXT |  |  |  |
| `description_2` | TEXT |  |  |  |
| `description_3` | TEXT |  |  |  |
| `bin_location` | TEXT |  |  |  |
| `product_type` | TEXT |  |  |  |
| `manufacturer_code` | TEXT |  |  |  |
| `main_position` | TEXT |  |  |  |
| `sub_position` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |
| `space_requirement` | INTEGER |  |  |  |
| `malfunction_date` | TEXT |  |  |  |
| `malfunction_employee` | INTEGER |  |  |  |
| `renewal_date` | TEXT |  |  |  |
| `renewal_employee` | INTEGER |  |  |  |
| `removal_state` | TEXT |  |  |  |

### `loco_tire_storage_wheels` (19,178 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `case_number` | INTEGER |  |  |  |
| `internal_counter` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |
| `manufacturer` | TEXT |  |  |  |
| `product_name` | TEXT |  |  |  |
| `tire_dimension` | TEXT |  |  |  |
| `rim_description` | TEXT |  |  |  |
| `bin_location` | TEXT |  |  |  |
| `product_type` | TEXT |  |  |  |
| `note` | TEXT |  |  |  |
| `manufacturer_code` | TEXT |  |  |  |
| `wheel_position` | TEXT |  |  |  |
| `tire_tread_depth` | REAL |  |  |  |
| `rim_nuts_included` | INTEGER |  |  |  |
| `wheel_cover_included` | INTEGER |  |  |  |
| `is_runflat` | INTEGER |  |  |  |
| `is_uhp` | INTEGER |  |  |  |
| `has_rdks` | INTEGER |  |  |  |
| `rdks_code` | TEXT |  |  |  |
| `space_requirement` | INTEGER |  |  |  |
| `malfunction_date` | TEXT |  |  |  |
| `malfunction_employee` | INTEGER |  |  |  |
| `renewal_date` | TEXT |  |  |  |
| `renewal_employee` | INTEGER |  |  |  |
| `removal_state` | TEXT |  |  |  |

### `loco_transit_customers` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `order_number` | INTEGER |  |  |  |
| `order_position` | INTEGER |  |  |  |
| `order_position_line` | INTEGER |  |  |  |
| `first_name` | TEXT |  |  |  |
| `family_name` | TEXT |  |  |  |
| `salutation_code` | TEXT |  |  |  |
| `country` | TEXT |  |  |  |
| `zip_code` | TEXT |  |  |  |
| `home_city` | TEXT |  |  |  |
| `home_street` | TEXT |  |  |  |
| `phone_number` | TEXT |  |  |  |
| `fullname_vector` | TEXT |  |  |  |

### `loco_transit_vehicles` (2,477 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `order_number` | INTEGER |  |  |  |
| `order_position` | INTEGER |  |  |  |
| `order_position_line` | INTEGER |  |  |  |
| `make_number` | INTEGER |  |  |  |
| `make_text` | TEXT |  |  |  |
| `model_code` | TEXT |  |  |  |
| `model_text` | TEXT |  |  |  |
| `color_text` | TEXT |  |  |  |
| `license_plate` | TEXT |  |  |  |
| `vin` | TEXT |  |  |  |
| `first_registration_date` | TEXT |  |  |  |
| `model_vector` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_transit_vehicles_license_plate`: license_plate
- `idx_loco_transit_vehicles_vin`: vin

### `loco_vat_keys` (52 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary_to_company_ref` | INTEGER |  |  |  |
| `vat_key` | TEXT |  |  |  |
| `key_validity_date` | TEXT |  |  |  |
| `branch` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |
| `vat_rate` | INTEGER |  |  |  |
| `create_date` | TEXT |  |  |  |
| `vat_account` | INTEGER |  |  |  |
| `advanced_turnover_tax_pos` | INTEGER |  |  |  |

**Indizes:**
- `idx_loco_vat_keys_subsidiary_to_company_ref`: subsidiary_to_company_ref

### `loco_vehicle_accessories_customer` (217,172 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `vehicle_number` | INTEGER |  |  |  |
| `sequence` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `package_reference` | TEXT |  |  |  |
| `optional` | INTEGER |  |  |  |
| `price` | REAL |  |  |  |
| `discountable` | INTEGER |  |  |  |
| `purchase_price` | REAL |  |  |  |

### `loco_vehicle_accessories_dealer` (63,836 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `sequence` | INTEGER |  |  |  |
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |
| `package_reference` | TEXT |  |  |  |
| `optional` | INTEGER |  |  |  |
| `price` | REAL |  |  |  |
| `discountable` | INTEGER |  |  |  |
| `purchase_price` | REAL |  |  |  |

### `loco_vehicle_bodys` (47 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_vehicle_buy_types` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_vehicle_contact_log_pemissions` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `vehicle_number` | INTEGER |  |  |  |
| `case_number` | INTEGER |  |  |  |
| `employee_no` | INTEGER |  |  |  |

### `loco_vehicle_pre_owned_codes` (5 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_vehicle_sale_types` (5 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_vehicle_types` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | TEXT |  |  |  |
| `is_new_or_similar` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_vehicles` (58,561 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `internal_number` | INTEGER |  |  |  |
| `vin` | TEXT |  |  |  |
| `license_plate` | TEXT |  |  |  |
| `license_plate_country` | TEXT |  |  |  |
| `license_plate_season` | TEXT |  |  |  |
| `make_number` | INTEGER |  |  |  |
| `free_form_make_text` | TEXT |  |  |  |
| `model_code` | TEXT |  |  |  |
| `free_form_model_text` | TEXT |  |  |  |
| `is_roadworthy` | INTEGER |  |  |  |
| `is_customer_vehicle` | INTEGER |  |  |  |
| `dealer_vehicle_type` | TEXT |  |  |  |
| `dealer_vehicle_number` | INTEGER |  |  |  |
| `first_registration_date` | TEXT |  |  |  |
| `readmission_date` | TEXT |  |  |  |
| `next_service_date` | TEXT |  |  |  |
| `next_service_km` | INTEGER |  |  |  |
| `next_service_miles` | INTEGER |  |  |  |
| `production_year` | REAL |  |  |  |
| `owner_number` | INTEGER |  |  |  |
| `holder_number` | INTEGER |  |  |  |
| `previous_owner_number` | INTEGER |  |  |  |
| `previous_owner_counter` | INTEGER |  |  |  |
| `last_holder_change_date` | TEXT |  |  |  |
| `german_kba_hsn` | TEXT |  |  |  |
| `german_kba_tsn` | TEXT |  |  |  |
| `austria_nat_code` | TEXT |  |  |  |
| `is_prefer_km` | INTEGER |  |  |  |
| `mileage_km` | INTEGER |  |  |  |
| `mileage_miles` | INTEGER |  |  |  |
| `odometer_reading_date` | TEXT |  |  |  |
| `engine_number` | TEXT |  |  |  |
| `gear_number` | TEXT |  |  |  |
| `unloaded_weight` | INTEGER |  |  |  |
| `gross_vehicle_weight` | INTEGER |  |  |  |
| `power_kw` | INTEGER |  |  |  |
| `cubic_capacity` | INTEGER |  |  |  |
| `is_all_accidents_repaired` | INTEGER |  |  |  |
| `accidents_counter` | INTEGER |  |  |  |
| `has_tyre_pressure_sensor` | INTEGER |  |  |  |
| `carkey_number` | TEXT |  |  |  |
| `internal_source_flag` | TEXT |  |  |  |
| `emission_code` | TEXT |  |  |  |
| `first_sold_country` | TEXT |  |  |  |
| `first_sold_dealer_code` | INTEGER |  |  |  |
| `body_paint_code` | TEXT |  |  |  |
| `body_paint_description` | TEXT |  |  |  |
| `is_body_paint_metallic` | INTEGER |  |  |  |
| `interior_paint_code` | TEXT |  |  |  |
| `interior_paint_description` | TEXT |  |  |  |
| `trim_code` | TEXT |  |  |  |
| `trim_description` | TEXT |  |  |  |
| `fine_dust_label` | TEXT |  |  |  |
| `internal_assignment` | TEXT |  |  |  |
| `ricambi_free_input` | TEXT |  |  |  |
| `document_number` | TEXT |  |  |  |
| `salesman_number` | INTEGER |  |  |  |
| `sale_date` | TEXT |  |  |  |
| `next_emission_test_date` | TEXT |  |  |  |
| `next_general_inspection_date` | TEXT |  |  |  |
| `next_rust_inspection_date` | TEXT |  |  |  |
| `next_exceptional_inspection_da` | TEXT |  |  |  |
| `last_change_date` | TEXT |  |  |  |
| `last_change_employee_no` | INTEGER |  |  |  |
| `created_date` | TEXT |  |  |  |
| `created_employee_no` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `last_change_subsidiary` | INTEGER |  |  |  |
| `other_date_1` | TEXT |  |  |  |
| `lock_by_workstation` | INTEGER |  |  |  |
| `lock_time` | TEXT |  |  |  |
| `lock_trace` | TEXT |  |  |  |
| `lock_trigger` | TEXT |  |  |  |
| `lock_by_employee` | INTEGER |  |  |  |
| `lock_sourcecode` | TEXT |  |  |  |
| `lock_machine` | TEXT |  |  |  |
| `lock_task` | INTEGER |  |  |  |
| `lock_service_name` | TEXT |  |  |  |
| `free_form_model_text_vector` | TEXT |  |  |  |

**Indizes:**
- `idx_loco_vehicles_license_plate`: license_plate
- `idx_loco_vehicles_vin`: vin
- `idx_loco_vehicles_document_number`: document_number

### `loco_wtp_pickup_bring_type` (4 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `type` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_wtp_progress_status` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_wtp_urgency` (7 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_wtp_vehicle_status` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_year_calendar` (505 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `calendar_id` | INTEGER |  |  |  |
| `date` | TEXT |  |  |  |
| `day_off_declaration` | INTEGER |  |  |  |
| `is_school_holid` | INTEGER |  |  |  |
| `is_public_holid` | INTEGER |  |  |  |
| `day_note` | TEXT |  |  |  |

### `loco_year_calendar_day_off_codes` (5 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `code` | INTEGER |  |  |  |
| `description` | TEXT |  |  |  |

### `loco_year_calendar_subsidiary_mapping` (12 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `subsidiary` | INTEGER |  |  |  |
| `year` | INTEGER |  |  |  |
| `calendar_id` | INTEGER |  |  |  |

### `manager_assignments` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `manager_id` | INTEGER | ✓ |  |  |
| `employee_id` | INTEGER | ✓ |  |  |
| `department_id` | INTEGER |  |  |  |
| `valid_from` | DATE | ✓ | '2025-01-01' |  |
| `valid_to` | DATE |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_manager_assignments_1`: manager_id, employee_id

### `praemien_berechnungen` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `wirtschaftsjahr` | TEXT | ✓ |  |  |
| `wj_start` | DATE | ✓ |  |  |
| `wj_ende` | DATE | ✓ |  |  |
| `praemientopf` | REAL | ✓ |  |  |
| `kulanz_volumen` | REAL |  | 0 |  |
| `bereinigter_topf` | REAL |  |  |  |
| `vz_tz_grenze` | REAL |  | 30 |  |
| `hoechstes_festgehalt` | REAL |  |  |  |
| `hoechstes_festgehalt_ma_id` | INTEGER |  |  |  |
| `berechnungsbasis` | REAL |  |  |  |
| `praemie_I_topf` | REAL |  |  |  |
| `praemie_II_topf` | REAL |  |  |  |
| `prokopf_vollzeit` | REAL |  |  |  |
| `prokopf_teilzeit` | REAL |  |  |  |
| `prokopf_minijob` | REAL |  |  |  |
| `prokopf_azubi_1` | REAL |  | 100 |  |
| `prokopf_azubi_2` | REAL |  | 125 |  |
| `prokopf_azubi_3` | REAL |  | 150 |  |
| `anzahl_gesamt` | INTEGER |  | 0 |  |
| `anzahl_vollzeit` | INTEGER |  | 0 |  |
| `anzahl_teilzeit` | INTEGER |  | 0 |  |
| `anzahl_minijob` | INTEGER |  | 0 |  |
| `anzahl_azubi_1` | INTEGER |  | 0 |  |
| `anzahl_azubi_2` | INTEGER |  | 0 |  |
| `anzahl_azubi_3` | INTEGER |  | 0 |  |
| `lohnjournal_datei` | TEXT |  |  |  |
| `lohnjournal_hash` | TEXT |  |  |  |
| `status` | TEXT |  | 'entwurf' |  |
| `erstellt_am` | DATETIME |  | CURRENT_TIMESTAMP |  |
| `geaendert_am` | DATETIME |  |  |  |
| `freigegeben_am` | DATETIME |  |  |  |
| `freigegeben_von` | TEXT |  |  |  |

**Indizes:**
- `sqlite_autoindex_praemien_berechnungen_1`: wirtschaftsjahr

### `praemien_exporte` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `berechnung_id` | INTEGER | ✓ |  |  |
| `export_typ` | TEXT | ✓ |  |  |
| `dateiname` | TEXT |  |  |  |
| `dateipfad` | TEXT |  |  |  |
| `erstellt_am` | DATETIME |  | CURRENT_TIMESTAMP |  |
| `erstellt_von` | TEXT |  |  |  |

**Indizes:**
- `idx_praemien_exporte_berechnung`: berechnung_id

### `praemien_kulanz_regeln` (5 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `berechnung_id` | INTEGER | ✓ |  |  |
| `regel_typ` | TEXT | ✓ |  |  |
| `kategorie` | TEXT |  |  |  |
| `pauschal_betrag` | REAL |  |  |  |
| `mitarbeiter_id` | INTEGER |  |  |  |
| `beschreibung` | TEXT |  |  |  |
| `aktiv` | INTEGER |  | 1 |  |
| `erstellt_am` | DATETIME |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_praemien_kulanz_berechnung`: berechnung_id

### `praemien_mitarbeiter` (79 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `berechnung_id` | INTEGER | ✓ |  |  |
| `personalnummer` | TEXT |  |  |  |
| `vorname` | TEXT |  |  |  |
| `nachname` | TEXT |  |  |  |
| `eintritt` | DATE |  |  |  |
| `austritt` | DATE |  |  |  |
| `std_woche` | REAL |  |  |  |
| `taetigkeit` | TEXT |  |  |  |
| `ang_arb` | TEXT |  |  |  |
| `kategorie` | TEXT |  |  |  |
| `ist_festgehalt` | INTEGER |  | 1 |  |
| `jahresbrutto` | REAL |  |  |  |
| `jahresbrutto_gekappt` | REAL |  |  |  |
| `ist_berechtigt` | INTEGER |  | 0 |  |
| `berechtigung_grund` | TEXT |  |  |  |
| `ist_kulanz` | INTEGER |  | 0 |  |
| `kulanz_betrag` | REAL |  |  |  |
| `kulanz_grund` | TEXT |  |  |  |
| `anteil_lohnsumme` | REAL |  |  |  |
| `praemie_I` | REAL |  | 0 |  |
| `praemie_II` | REAL |  | 0 |  |
| `praemie_gesamt` | REAL |  | 0 |  |
| `praemie_gerundet` | INTEGER |  | 0 |  |

**Indizes:**
- `idx_praemien_ma_berechtigt`: ist_berechtigt
- `idx_praemien_ma_kategorie`: kategorie
- `idx_praemien_ma_berechnung`: berechnung_id

### `roles` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `name` | TEXT | ✓ |  |  |
| `display_name` | TEXT | ✓ |  |  |
| `description` | TEXT |  |  |  |
| `permissions_json` | TEXT | ✓ |  |  |
| `is_active` | BOOLEAN |  | 1 |  |
| `is_system_role` | BOOLEAN |  | 0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_roles_is_active`: is_active
- `idx_roles_name`: name
- `sqlite_autoindex_roles_1`: name

### `salden` (1,260 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `konto_id` | INTEGER | ✓ |  |  |
| `datum` | DATE | ✓ |  |  |
| `saldo` | REAL | ✓ |  |  |
| `waehrung` | TEXT |  | 'EUR' |  |
| `import_datei` | TEXT |  |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `quelle` | TEXT |  | 'MT940' |  |

**Indizes:**
- `idx_salden_konto_datum`: konto_id, datum
- `idx_salden_datum`: datum
- `idx_salden_konto`: konto_id
- `sqlite_autoindex_salden_1`: konto_id, datum

### `sales` (4,983 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `dealer_vehicle_number` | TEXT |  |  |  |
| `dealer_vehicle_type` | TEXT |  |  |  |
| `vin` | TEXT |  |  |  |
| `internal_number` | INTEGER |  |  |  |
| `out_invoice_date` | DATE |  |  |  |
| `out_invoice_number` | TEXT |  |  |  |
| `out_sale_price` | REAL |  |  |  |
| `out_sale_type` | TEXT |  |  |  |
| `out_subsidiary` | INTEGER |  |  |  |
| `out_sales_contract_date` | DATE |  |  |  |
| `make_number` | INTEGER |  |  |  |
| `model_description` | TEXT |  |  |  |
| `body_paint_description` | TEXT |  |  |  |
| `mileage_km` | INTEGER |  |  |  |
| `salesman_number` | INTEGER |  |  |  |
| `buyer_customer_no` | TEXT |  |  |  |
| `netto_price` | REAL |  |  |  |
| `synced_at` | TIMESTAMP |  |  |  |
| `deckungsbeitrag` | REAL |  |  |  |
| `db_prozent` | REAL |  |  |  |
| `fahrzeuggrundpreis` | REAL |  |  |  |
| `zubehoer` | REAL |  |  |  |
| `fracht_brief_neben` | REAL |  |  |  |
| `kosten_intern_rg` | REAL |  |  |  |
| `verkaufsunterstuetzung` | REAL |  |  |  |
| `netto_vk_preis` | REAL |  |  |  |

**Indizes:**
- `idx_sales_db_prozent`: db_prozent
- `idx_sales_deckungsbeitrag`: deckungsbeitrag
- `sqlite_autoindex_sales_1`: dealer_vehicle_number, dealer_vehicle_type

### `santander_zins_staffel` (5 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `fahrzeugtyp` | TEXT | ✓ |  |  |
| `von_tag` | INTEGER | ✓ |  |  |
| `bis_tag` | INTEGER |  |  |  |
| `aufschlag_prozent` | REAL | ✓ |  |  |
| `gueltig_ab` | DATE |  | '2025-07-15' |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

### `sessions` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `session_id` | TEXT | ✓ |  |  |
| `user_id` | INTEGER | ✓ |  |  |
| `ip_address` | TEXT |  |  |  |
| `user_agent` | TEXT |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `last_activity` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `expires_at` | TIMESTAMP | ✓ |  |  |

**Indizes:**
- `idx_sessions_expires_at`: expires_at
- `idx_sessions_user_id`: user_id
- `idx_sessions_session_id`: session_id
- `sqlite_autoindex_sessions_1`: session_id

### `stellantis_bestellungen` (379 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `bestellnummer` | TEXT | ✓ |  |  |
| `bestelldatum` | DATETIME |  |  |  |
| `absender_code` | TEXT |  |  |  |
| `absender_name` | TEXT |  |  |  |
| `empfaenger_code` | TEXT |  |  |  |
| `lokale_nr` | TEXT |  |  |  |
| `url` | TEXT |  |  |  |
| `import_timestamp` | DATETIME |  | CURRENT_TIMESTAMP |  |
| `import_datei` | TEXT |  |  |  |
| `kommentar_werkstatt` | TEXT |  |  |  |
| `parsed_kundennummer` | TEXT |  |  |  |
| `parsed_vin` | TEXT |  |  |  |
| `parsed_werkstattauftrag` | TEXT |  |  |  |
| `match_typ` | TEXT |  |  |  |
| `match_kunde_name` | TEXT |  |  |  |
| `match_confidence` | INTEGER |  |  |  |

**Indizes:**
- `idx_stellantis_bestellungen_import`: import_timestamp
- `idx_stellantis_bestellungen_lokale_nr`: lokale_nr
- `idx_stellantis_bestellungen_empfaenger`: empfaenger_code
- `idx_stellantis_bestellungen_absender`: absender_code
- `idx_stellantis_bestellungen_datum`: bestelldatum
- `sqlite_autoindex_stellantis_bestellungen_1`: bestellnummer

### `stellantis_positionen` (886 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `bestellung_id` | INTEGER | ✓ |  |  |
| `teilenummer` | TEXT | ✓ |  |  |
| `beschreibung` | TEXT |  |  |  |
| `menge` | REAL |  |  |  |
| `menge_in_lieferung` | REAL |  |  |  |
| `menge_in_bestellung` | REAL |  |  |  |
| `preis_ohne_mwst_text` | TEXT |  |  |  |
| `preis_mit_mwst_text` | TEXT |  |  |  |
| `summe_inkl_mwst_text` | TEXT |  |  |  |
| `preis_ohne_mwst` | REAL |  |  |  |
| `preis_mit_mwst` | REAL |  |  |  |
| `summe_inkl_mwst` | REAL |  |  |  |
| `import_timestamp` | DATETIME |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_stellantis_positionen_beschreibung`: beschreibung
- `idx_stellantis_positionen_teilenummer`: teilenummer
- `idx_stellantis_positionen_bestellung`: bestellung_id

### `sync_log` (9 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `sync_type` | TEXT | ✓ |  |  |
| `started_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `finished_at` | TIMESTAMP |  |  |  |
| `status` | TEXT |  |  |  |
| `records_synced` | INTEGER |  | 0 |  |
| `error_message` | TEXT |  |  |  |
| `details` | TEXT |  |  |  |

### `sync_status` (1 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `sync_name` | TEXT | ✓ |  |  |
| `last_run` | DATETIME |  |  |  |
| `status` | TEXT |  |  |  |
| `records_processed` | INTEGER |  |  |  |
| `records_matched` | INTEGER |  |  |  |
| `error_message` | TEXT |  |  |  |

**Indizes:**
- `sqlite_autoindex_sync_status_1`: sync_name

### `system_job_history` (6 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `job_name` | TEXT | ✓ |  |  |
| `run_start` | TIMESTAMP |  |  |  |
| `run_end` | TIMESTAMP |  |  |  |
| `status` | TEXT |  |  |  |
| `message` | TEXT |  |  |  |
| `records_processed` | INTEGER |  |  |  |
| `error_details` | TEXT |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_job_history_start`: run_start
- `idx_job_history_name`: job_name

### `system_jobs` (14 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `job_name` | TEXT | ✓ |  |  |
| `job_description` | TEXT |  |  |  |
| `last_run` | TIMESTAMP |  |  |  |
| `last_status` | TEXT |  |  |  |
| `last_message` | TEXT |  |  |  |
| `records_processed` | INTEGER |  | 0 |  |
| `duration_seconds` | REAL |  |  |  |
| `cron_schedule` | TEXT |  |  |  |
| `next_run_description` | TEXT |  |  |  |
| `is_active` | BOOLEAN |  | 1 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_system_jobs_1`: job_name

### `teile_lieferscheine` (1,489 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `datei_name` | TEXT |  |  |  |
| `standort` | TEXT |  |  |  |
| `lieferschein_nr` | TEXT |  |  |  |
| `zeile` | INTEGER |  |  |  |
| `lieferdatum` | DATE |  |  |  |
| `servicebox_bestellnr` | TEXT |  |  |  |
| `lieferanten_note` | TEXT |  |  |  |
| `teilenummer` | TEXT |  |  |  |
| `beschreibung` | TEXT |  |  |  |
| `menge` | INTEGER |  | 1 |  |
| `preis_ek_cent` | INTEGER |  |  |  |
| `preis_vk_cent` | INTEGER |  |  |  |
| `empfaenger` | TEXT |  |  |  |
| `locosoft_gefunden` | BOOLEAN |  | 0 |  |
| `locosoft_zugebucht` | BOOLEAN |  | 0 |  |
| `locosoft_sync_datum` | TIMESTAMP |  |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_tl_zugebucht`: locosoft_zugebucht
- `idx_tl_lsnr`: lieferschein_nr
- `idx_tl_bestell`: servicebox_bestellnr
- `idx_tl_teilenr`: teilenummer
- `idx_tl_datum`: lieferdatum
- `sqlite_autoindex_teile_lieferscheine_1`: datei_name, teilenummer, zeile

### `tilgungen` (158 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `fahrzeugfinanzierung_id` | INTEGER |  |  |  |
| `vin` | TEXT | ✓ |  |  |
| `finanzierungsnummer` | TEXT |  |  |  |
| `faellig_am` | DATE | ✓ |  |  |
| `betrag` | REAL | ✓ |  |  |
| `beschreibung` | TEXT |  | 'Tilgung' |  |
| `status` | TEXT |  |  |  |
| `lastschrift_referenz` | TEXT |  |  |  |
| `oem_rechnungsnr` | TEXT |  |  |  |
| `finanzinstitut` | TEXT | ✓ |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `import_datei` | TEXT |  |  |  |
| `erstellt_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `aktualisiert_am` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_tilgungen_status`: status
- `idx_tilgungen_finanzinstitut`: finanzinstitut
- `idx_tilgungen_faellig_am`: faellig_am
- `idx_tilgungen_vin`: vin

### `transaktionen` (15,853 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `konto_id` | INTEGER | ✓ |  |  |
| `buchungsdatum` | DATE | ✓ |  |  |
| `valutadatum` | DATE |  |  |  |
| `betrag` | REAL | ✓ |  |  |
| `waehrung` | TEXT |  | 'EUR' |  |
| `saldo_nach_buchung` | REAL |  |  |  |
| `buchungstext` | TEXT |  |  |  |
| `verwendungszweck` | TEXT |  |  |  |
| `auftraggeber_empfaenger` | TEXT |  |  |  |
| `gegenkonto_iban` | TEXT |  |  |  |
| `gegenkonto_bic` | TEXT |  |  |  |
| `gegenkonto_name` | TEXT |  |  |  |
| `kategorie` | TEXT |  |  |  |
| `unterkategorie` | TEXT |  |  |  |
| `steuerrelevant` | BOOLEAN |  | 0 |  |
| `import_datei` | TEXT | ✓ |  |  |
| `import_datum` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `rohdaten` | TEXT |  |  |  |
| `verarbeitet` | BOOLEAN |  | 0 |  |
| `notizen` | TEXT |  |  |  |
| `import_quelle` | TEXT |  | 'MT940' |  |

**Indizes:**
- `idx_trans_unique`: konto_id, buchungsdatum, betrag, verwendungszweck
- `idx_trans_import`: import_datei, import_datum
- `idx_trans_verarbeitet`: verarbeitet
- `idx_trans_kategorie`: kategorie
- `idx_trans_betrag`: betrag
- `idx_trans_buchungsdatum`: buchungsdatum
- `idx_trans_konto`: konto_id

### `user_roles` (17 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `user_id` | INTEGER | ✓ |  |  |
| `role_id` | INTEGER | ✓ |  |  |
| `assigned_by` | INTEGER |  |  |  |
| `assigned_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `expires_at` | TIMESTAMP |  |  |  |

**Indizes:**
- `idx_user_roles_role_id`: role_id
- `idx_user_roles_user_id`: user_id
- `sqlite_autoindex_user_roles_1`: user_id, role_id

### `users` (16 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `username` | TEXT | ✓ |  |  |
| `upn` | TEXT |  |  |  |
| `display_name` | TEXT | ✓ |  |  |
| `email` | TEXT |  |  |  |
| `ad_dn` | TEXT |  |  |  |
| `ad_groups` | TEXT |  |  |  |
| `ou` | TEXT |  |  |  |
| `department` | TEXT |  |  |  |
| `title` | TEXT |  |  |  |
| `is_active` | BOOLEAN |  | 1 |  |
| `is_locked` | BOOLEAN |  | 0 |  |
| `failed_login_attempts` | INTEGER |  | 0 |  |
| `last_login` | TIMESTAMP |  |  |  |
| `last_ad_sync` | TIMESTAMP |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `sqlite_autoindex_users_1`: username

### `users_old_backup` (3 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `username` | TEXT | ✓ |  |  |
| `password` | TEXT | ✓ |  |  |
| `role` | TEXT | ✓ |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_users_username`: username
- `sqlite_autoindex_users_old_backup_1`: username

### `vacation_adjustments` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `employee_id` | INTEGER | ✓ |  |  |
| `year` | INTEGER | ✓ |  |  |
| `days` | INTEGER | ✓ |  |  |
| `adjustment_type` | TEXT | ✓ |  |  |
| `reason` | TEXT |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

### `vacation_approval_rules` (16 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `loco_grp_code` | TEXT | ✓ |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `approver_employee_id` | INTEGER | ✓ |  |  |
| `approver_ldap_username` | TEXT | ✓ |  |  |
| `priority` | INTEGER |  | 1 |  |
| `active` | INTEGER |  | 1 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `created_by` | TEXT |  |  |  |
| `notes` | TEXT |  |  |  |

**Indizes:**
- `idx_approval_rules_approver`: approver_ldap_username, active
- `idx_approval_rules_lookup`: loco_grp_code, subsidiary, active
- `sqlite_autoindex_vacation_approval_rules_1`: loco_grp_code, subsidiary, approver_employee_id

### `vacation_audit_log` (0 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `table_name` | TEXT | ✓ |  |  |
| `record_id` | INTEGER | ✓ |  |  |
| `action` | TEXT | ✓ |  |  |
| `old_values` | TEXT |  |  |  |
| `new_values` | TEXT |  |  |  |
| `changed_by` | INTEGER |  |  |  |
| `changed_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `ip_address` | TEXT |  |  |  |
| `user_agent` | TEXT |  |  |  |

**Indizes:**
- `idx_vacation_audit_log_changed_at`: changed_at
- `idx_vacation_audit_log_changed_by`: changed_by
- `idx_vacation_audit_log_table`: table_name, record_id

### `vacation_bookings` (1,358 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `employee_id` | INTEGER | ✓ |  |  |
| `booking_date` | DATE | ✓ |  |  |
| `vacation_type_id` | INTEGER | ✓ |  |  |
| `day_part` | TEXT |  | 'full' |  |
| `status` | TEXT |  | 'pending' |  |
| `comment` | TEXT |  |  |  |
| `created_by` | INTEGER |  |  |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `approved_by` | INTEGER |  |  |  |
| `approved_at` | TIMESTAMP |  |  |  |

**Indizes:**
- `idx_bookings_emp_date`: employee_id, booking_date
- `idx_bookings_date`: booking_date
- `idx_bookings_employee`: employee_id

### `vacation_entitlements` (75 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `employee_id` | INTEGER | ✓ |  |  |
| `year` | INTEGER | ✓ |  |  |
| `total_days` | REAL | ✓ | 30.0 |  |
| `carried_over` | REAL |  | 0.0 |  |
| `added_manually` | REAL |  | 0.0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |
| `updated_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_vacation_entitlements_year`: year
- `idx_vacation_entitlements_employee`: employee_id
- `sqlite_autoindex_vacation_entitlements_1`: employee_id, year

### `vacation_types` (11 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `name` | TEXT | ✓ |  |  |
| `color` | TEXT | ✓ |  |  |
| `icon` | TEXT |  |  |  |
| `available_for_user` | BOOLEAN |  | 0 |  |
| `available_for_approver` | BOOLEAN |  | 0 |  |
| `available_for_admin` | BOOLEAN |  | 1 |  |
| `deduct_from_contingent` | INTEGER |  | 1 |  |
| `needs_approval` | INTEGER |  | 1 |  |
| `loco_reason` | TEXT |  |  |  |

**Indizes:**
- `sqlite_autoindex_vacation_types_1`: name

### `vehicles` (1,023 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `internal_number` | INTEGER |  |  |  |
| `vin` | TEXT |  |  |  |
| `dealer_vehicle_number` | TEXT |  |  |  |
| `dealer_vehicle_type` | TEXT |  |  |  |
| `sale_date` | DATE |  |  |  |
| `salesman_number` | INTEGER |  |  |  |
| `make_number` | INTEGER |  |  |  |
| `model_description` | TEXT |  |  |  |
| `body_paint_description` | TEXT |  |  |  |
| `mileage_km` | INTEGER |  |  |  |
| `subsidiary` | INTEGER |  |  |  |
| `synced_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_vehicles_subsidiary`: subsidiary
- `idx_vehicles_salesman`: salesman_number
- `idx_vehicles_sale_date`: sale_date
- `sqlite_autoindex_vehicles_1`: dealer_vehicle_number, dealer_vehicle_type

### `werkstatt_auftraege_abgerechnet` (15,936 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `rechnungs_datum` | DATE |  |  |  |
| `rechnungs_nr` | INTEGER |  |  |  |
| `rechnungs_typ` | INTEGER |  |  |  |
| `auftrags_nr` | INTEGER |  |  |  |
| `betrieb` | INTEGER |  |  |  |
| `kennzeichen` | TEXT |  |  |  |
| `serviceberater_nr` | INTEGER |  |  |  |
| `serviceberater_name` | TEXT |  |  |  |
| `lohn_netto` | REAL |  | 0 |  |
| `teile_netto` | REAL |  | 0 |  |
| `gesamt_netto` | REAL |  | 0 |  |
| `summe_aw` | REAL |  | 0 |  |
| `summe_stempelzeit_min` | REAL |  | 0 |  |
| `leistungsgrad` | REAL |  |  |  |
| `storniert` | INTEGER |  | 0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_waa_betrieb`: betrieb
- `idx_waa_datum`: rechnungs_datum
- `sqlite_autoindex_werkstatt_auftraege_abgerechnet_1`: rechnungs_nr, rechnungs_typ

### `werkstatt_leistung_daily` (10,452 Zeilen)

| Spalte | Typ | NotNull | Default | PK |
|--------|-----|---------|---------|-----|
| `id` | INTEGER |  |  | 🔑 |
| `datum` | DATE |  |  |  |
| `mechaniker_nr` | INTEGER |  |  |  |
| `mechaniker_name` | TEXT |  |  |  |
| `betrieb_nr` | INTEGER |  |  |  |
| `ist_aktiv` | INTEGER |  | 1 |  |
| `anzahl_auftraege` | INTEGER |  | 0 |  |
| `vorgabezeit_aw` | REAL |  | 0 |  |
| `stempelzeit_min` | REAL |  | 0 |  |
| `anwesenheit_min` | REAL |  | 0 |  |
| `leistungsgrad` | REAL |  |  |  |
| `produktivitaet` | REAL |  |  |  |
| `umsatz` | REAL |  | 0 |  |
| `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

**Indizes:**
- `idx_wld_betrieb`: betrieb_nr
- `idx_wld_mech`: mechaniker_nr
- `idx_wld_datum`: datum
- `sqlite_autoindex_werkstatt_leistung_daily_1`: datum, mechaniker_nr

---

## 👁️ VIEWS

### `fahrzeuge_mit_zinsen`

```sql
CREATE VIEW fahrzeuge_mit_zinsen AS
SELECT
    f.id,
    f.finanzinstitut,
    f.rrdi,
    f.hersteller,
    f.vin,
    f.modell,
    f.produkt_kategorie,
    f.aktueller_saldo,
    f.original_betrag,
    f.zinsen_gesamt,
    f.zinsen_letzte_periode,
    f.zinsen_berechnet,
    f.vertragsbeginn,
    f.alter_tage,
    f.zinsfreiheit_tage,
    f.zins_startdatum,
    f.endfaelligkeit,
    f.aktiv,
    
    -- Zinsstatus ermitteln
    CASE
        WHEN f.zins_startdatum IS NOT NULL 
             AND date(f.zins_startdatum) <= date('now') THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage < 0 THEN 'Zinsen laufen'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 30 THEN 'Warnung (< 30 Tage)'
        WHEN f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 60 THEN 'Achtung (< 60 Tage)'
        WHEN f.zinsen_gesamt > 0 THEN 'Zinsen laufen'
        ELSE 'OK'
    END as zinsstatus,
    
    -- Tage seit Zinsstart
    CASE
        WHEN f.zins_startdatum IS NOT NULL THEN
            CAST(julianday('now') - julianday(f.zins_startdatum) AS INTEGER)
        WHEN f.zinsfreiheit_tage < 0 THEN ABS(f.zinsfreiheit_tage)
        ELSE 0
    END as tage_seit_zinsstart,
    
    -- Tage bis Endfälligkeit
    CASE
        WHEN f.endfaelligkeit IS NOT NULL THEN
            CAST(julianday(f.endfaelligkeit) - julianday('now') AS INTEGER)
        ELSE NULL
    END as tage_bis_endfaelligkeit,
    
    -- Tilgung in Prozent
    ROUND(((f.original_betrag - f.aktueller_saldo) / NULLIF(f.original_betrag, 0) * 100), 2) as tilgung_prozent,
    
    -- Monatliche Zinskosten (beste verfügbare Quelle)
    COALESCE(
        NULLIF(f.zinsen_letzte_periode, 0),
        ROUND(f.aktueller_saldo * 0.09 * 30 / 365, 2)
    ) as zinsen_monatlich_geschaetzt

FROM fahrzeugfinanzierungen f
WHERE f.aktiv = 1
  AND (
    -- Zinsen laufen bereits
    (f.zins_startdatum IS NOT NULL AND date(f.zins_startdatum) <= date('now'))
    -- Oder bald zinspflichtig (< 60 Tage Zinsfreiheit übrig)
    OR (f.zinsfreiheit_tage IS NOT NULL AND f.zinsfreiheit_tage <= 60)
    -- Oder hat bereits Zinsen
    OR f.zinsen_gesamt > 0
  )
ORDER BY
    -- Erst die mit laufenden Zinsen (höchste zuerst)
    CASE WHEN f.zinsen_gesamt > 0 THEN 0 ELSE 1 END,
    f.zinsen_gesamt DESC,
    f.zinsfreiheit_tage ASC
```

### `v_aktuelle_kontosalden`

```sql
CREATE VIEW v_aktuelle_kontosalden AS
SELECT 
    k.id AS konto_id,
    k.kontoname,
    k.kontonummer,
    k.iban,
    b.bank_name,
    s.datum AS saldo_datum,
    s.saldo,
    s.waehrung,
    k.kreditlinie,
    (k.kreditlinie + s.saldo) AS verfuegbar
FROM konten k
JOIN banken b ON k.bank_id = b.id
LEFT JOIN salden s ON k.id = s.konto_id
WHERE k.aktiv = 1
AND s.datum = (
    SELECT MAX(datum) 
    FROM salden 
    WHERE konto_id = k.id
)
```

### `v_aktuelle_kontostaende`

```sql
CREATE VIEW v_aktuelle_kontostaende AS
SELECT
    k.id,
    k.kontoname,
    k.iban,
    k.bank_id,
    k.kontotyp,
    k.kreditlinie,
    k.kontoinhaber,
    k.verwendungszweck,
    k.ist_operativ,
    k.anzeige_gruppe,
    k.sort_order,
    b.bank_name as bank_name,
    COALESCE(s.saldo, 0) as saldo,
    s.datum as letztes_update
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
LEFT JOIN (
    SELECT
        konto_id,
        saldo,
        datum
    FROM salden
    WHERE (konto_id, datum) IN (
        SELECT konto_id, MAX(datum)
        FROM salden
        GROUP BY konto_id
    )
) s ON k.id = s.konto_id
WHERE k.aktiv = 1
ORDER BY k.sort_order, k.kontoname
```

### `v_approver_teams`

```sql
CREATE VIEW v_approver_teams AS
SELECT 
    ar.approver_ldap_username,
    ae.first_name || ' ' || ae.last_name as approver_name,
    ar.loco_grp_code,
    ar.subsidiary,
    CASE ar.subsidiary 
        WHEN 1 THEN 'Deggendorf'
        WHEN 3 THEN 'Landau'
        ELSE 'Alle Standorte'
    END as standort,
    ar.priority,
    COUNT(DISTINCT e.id) as team_size
FROM vacation_approval_rules ar
JOIN ldap_employee_mapping alem ON ar.approver_ldap_username = alem.ldap_username
JOIN employees ae ON alem.employee_id = ae.id
JOIN loco_employees_group_mapping gm ON ar.loco_grp_code = gm.grp_code
JOIN loco_employees le ON gm.employee_number = le.employee_number
    AND (ar.subsidiary IS NULL OR ar.subsidiary = le.subsidiary)
JOIN ldap_employee_mapping lem ON le.employee_number = lem.locosoft_id
JOIN employees e ON lem.employee_id = e.id AND e.aktiv = 1
WHERE ar.active = 1
GROUP BY ar.approver_ldap_username, ar.loco_grp_code, ar.subsidiary, ar.priority
ORDER BY ar.approver_ldap_username, ar.priority
```

### `v_cashflow_aktuell`

```sql
CREATE VIEW v_cashflow_aktuell AS
SELECT 
    strftime('%Y-%m', accounting_date) as monat,
    kategorie_erweitert,
    COUNT(*) as buchungen,
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
  -- Aktuelles Wirtschaftsjahr (ab 01.09.2025)
  AND accounting_date >= DATE('2025-09-01')
GROUP BY monat, kategorie_erweitert
ORDER BY monat DESC, kategorie_erweitert
```

### `v_cashflow_jahresuebersicht`

```sql
CREATE VIEW v_cashflow_jahresuebersicht AS
SELECT 
    wirtschaftsjahr,
    kategorie_erweitert,
    COUNT(*) as anzahl_buchungen,
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
GROUP BY wirtschaftsjahr, kategorie_erweitert
ORDER BY wirtschaftsjahr DESC, kategorie_erweitert
```

### `v_cashflow_kategorien`

```sql
CREATE VIEW v_cashflow_kategorien AS
SELECT 
    wirtschaftsjahr,
    strftime('%Y-%m', accounting_date) as monat,
    kategorie_erweitert,
    COUNT(*) as anzahl_buchungen,
    
    -- Kosten (Soll)
    ROUND(SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE 0 END), 2) as kosten,
    
    -- Umsätze (Haben)
    ROUND(SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE 0 END), 2) as umsatz,
    
    -- Netto (Umsatz - Kosten)
    ROUND(SUM(CASE 
        WHEN debit_credit = 'H' THEN amount 
        WHEN debit_credit = 'S' THEN -amount 
        ELSE 0 
    END), 2) as netto
    
FROM fibu_buchungen
WHERE kategorie_erweitert IS NOT NULL 
  AND kategorie_erweitert != 'bilanz'
GROUP BY wirtschaftsjahr, monat, kategorie_erweitert
ORDER BY wirtschaftsjahr DESC, monat DESC, kategorie_erweitert
```

### `v_employee_approvers`

```sql
CREATE VIEW v_employee_approvers AS
SELECT 
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as employee_name,
    lem.ldap_username as employee_ldap,
    gm.grp_code,
    le.subsidiary,
    CASE le.subsidiary 
        WHEN 1 THEN 'Deggendorf'
        WHEN 3 THEN 'Landau'
        ELSE 'Unbekannt'
    END as standort,
    ar.approver_ldap_username,
    ar.priority,
    ae.first_name || ' ' || ae.last_name as approver_name
FROM employees e
JOIN ldap_employee_mapping lem ON e.id = lem.employee_id
JOIN loco_employees le ON lem.locosoft_id = le.employee_number
JOIN loco_employees_group_mapping gm ON le.employee_number = gm.employee_number
LEFT JOIN vacation_approval_rules ar ON (
    ar.loco_grp_code = gm.grp_code 
    AND (ar.subsidiary IS NULL OR ar.subsidiary = le.subsidiary)
    AND ar.active = 1
)
LEFT JOIN ldap_employee_mapping alem ON ar.approver_ldap_username = alem.ldap_username
LEFT JOIN employees ae ON alem.employee_id = ae.id
WHERE e.aktiv = 1
ORDER BY e.last_name, e.first_name, ar.priority
```

### `v_fahrzeugfinanzierungen_aktuell`

```sql
CREATE VIEW v_fahrzeugfinanzierungen_aktuell AS
SELECT 
    f.id,
    fb.bank_name,
    fb.bank_typ,
    f.vin,
    f.finanzierungsnummer,
    f.hersteller,
    f.modell,
    f.finanzierungsstatus,
    f.produktfamilie,
    f.finanzierungsbetrag,
    f.aktueller_saldo,
    f.zinsen_gesamt,
    f.zinsen_letzte_periode,
    f.vertragsbeginn,
    f.finanzierungsende,
    JULIANDAY(f.finanzierungsende) - JULIANDAY('now') AS tage_bis_ende,
    f.import_datum
FROM fahrzeugfinanzierungen f
JOIN finanzierungsbanken fb ON f.finanzbank_id = fb.id
WHERE f.aktiv = 1
ORDER BY f.aktueller_saldo DESC
```

### `v_hyundai_fahrzeuge_zinsen`

```sql
CREATE VIEW v_hyundai_fahrzeuge_zinsen AS
SELECT 
    f.id,
    f.vin,
    f.modell,
    f.produkt,
    f.produkt_kategorie,
    f.aktueller_saldo,
    f.vertragsbeginn,
    f.zinsbeginn,
    f.zinsfreiheit_tage,
    f.tage_seit_zinsbeginn,
    CASE 
        WHEN f.zinsbeginn IS NOT NULL AND date(f.zinsbeginn) <= date('now') 
        THEN ROUND(ABS(f.aktueller_saldo) * 0.0468 * 
             (julianday('now') - julianday(f.zinsbeginn)) / 365, 2)
        ELSE 0 
    END as zinsen_berechnet_live,
    f.finanzinstitut
FROM fahrzeugfinanzierungen f
WHERE f.finanzinstitut = 'Hyundai Finance'
  AND f.aktiv = 1
```

### `v_kategorie_auswertung`

```sql
CREATE VIEW v_kategorie_auswertung AS
SELECT 
    t.kategorie,
    COUNT(*) as anzahl,
    SUM(t.betrag) as summe,
    AVG(t.betrag) as durchschnitt,
    MIN(t.buchungsdatum) as erste_buchung,
    MAX(t.buchungsdatum) as letzte_buchung
FROM transaktionen t
WHERE t.kategorie IS NOT NULL
GROUP BY t.kategorie
```

### `v_kreditlinien_aktuell`

```sql
CREATE VIEW v_kreditlinien_aktuell AS
SELECT 
    id,
    rrdi,
    marke,
    haendlername,
    kreditlinie_total,
    saldo_total,
    (kreditlinie_total - saldo_total) AS verfuegbar,
    ROUND((saldo_total * 100.0 / kreditlinie_total), 2) AS auslastung_prozent,
    import_datum
FROM kreditlinien
WHERE aktiv = 1
ORDER BY saldo_total DESC
```

### `v_monatliche_umsaetze`

```sql
CREATE VIEW v_monatliche_umsaetze AS
SELECT 
    b.bank_name,
    k.id as konto_id,
    k.kontoname,
    strftime('%Y-%m', t.buchungsdatum) as monat,
    SUM(CASE WHEN t.betrag > 0 THEN t.betrag ELSE 0 END) as einnahmen,
    SUM(CASE WHEN t.betrag < 0 THEN ABS(t.betrag) ELSE 0 END) as ausgaben,
    SUM(t.betrag) as saldo,
    COUNT(*) as anzahl_transaktionen
FROM transaktionen t
JOIN konten k ON t.konto_id = k.id
JOIN banken b ON k.bank_id = b.id
GROUP BY b.bank_name, k.id, k.kontoname, strftime('%Y-%m', t.buchungsdatum)
```

### `v_praemien_mitarbeiter_detail`

```sql
CREATE VIEW v_praemien_mitarbeiter_detail AS
SELECT 
    m.*,
    b.wirtschaftsjahr,
    b.praemientopf,
    b.status as berechnung_status
FROM praemien_mitarbeiter m
JOIN praemien_berechnungen b ON m.berechnung_id = b.id
```

### `v_praemien_uebersicht`

```sql
CREATE VIEW v_praemien_uebersicht AS
SELECT 
    b.id,
    b.wirtschaftsjahr,
    b.praemientopf,
    b.bereinigter_topf,
    b.anzahl_gesamt,
    b.status,
    b.erstellt_am,
    COALESCE(SUM(m.praemie_gerundet), 0) as summe_praemien,
    COUNT(CASE WHEN m.ist_berechtigt = 1 THEN 1 END) as anzahl_berechtigt
FROM praemien_berechnungen b
LEFT JOIN praemien_mitarbeiter m ON b.id = m.berechnung_id
GROUP BY b.id
```

### `v_stellantis_bestellungen_overview`

```sql
CREATE VIEW v_stellantis_bestellungen_overview AS
SELECT 
    b.id,
    b.bestellnummer,
    b.bestelldatum,
    b.absender_code,
    b.absender_name,
    b.empfaenger_code,
    b.lokale_nr,
    COUNT(p.id) as anzahl_positionen,
    SUM(p.summe_inkl_mwst) as gesamt_betrag,
    b.import_timestamp
FROM stellantis_bestellungen b
LEFT JOIN stellantis_positionen p ON b.id = p.bestellung_id
GROUP BY b.id
```

### `v_stellantis_bestellungen_pro_tag`

```sql
CREATE VIEW v_stellantis_bestellungen_pro_tag AS
SELECT 
    DATE(bestelldatum) as datum,
    COUNT(*) as anzahl_bestellungen,
    SUM((SELECT SUM(summe_inkl_mwst) FROM stellantis_positionen WHERE bestellung_id = b.id)) as gesamt_betrag
FROM stellantis_bestellungen b
WHERE bestelldatum IS NOT NULL
GROUP BY DATE(bestelldatum)
ORDER BY datum DESC
```

### `v_stellantis_top_teile`

```sql
CREATE VIEW v_stellantis_top_teile AS
SELECT 
    p.teilenummer,
    p.beschreibung,
    COUNT(*) as anzahl_bestellungen,
    SUM(p.menge) as gesamt_menge,
    AVG(p.preis_mit_mwst) as durchschnittspreis,
    SUM(p.summe_inkl_mwst) as gesamt_umsatz
FROM stellantis_positionen p
GROUP BY p.teilenummer, p.beschreibung
ORDER BY anzahl_bestellungen DESC
```

### `v_tilgungen_monatlich`

```sql
CREATE VIEW v_tilgungen_monatlich AS
SELECT 
    strftime('%Y-%m', faellig_am) as monat,
    finanzinstitut,
    COUNT(*) as anzahl_tilgungen,
    ROUND(SUM(betrag), 2) as summe_tilgungen,
    SUM(CASE WHEN status = 'erledigt' THEN betrag ELSE 0 END) as erledigt,
    SUM(CASE WHEN status = 'in Transfer' THEN betrag ELSE 0 END) as in_transfer,
    SUM(CASE WHEN status = 'geplant' THEN betrag ELSE 0 END) as geplant
FROM tilgungen
GROUP BY strftime('%Y-%m', faellig_am), finanzinstitut
ORDER BY monat
```

### `v_tilgungen_naechste_30_tage`

```sql
CREATE VIEW v_tilgungen_naechste_30_tage AS
SELECT 
    t.faellig_am,
    t.vin,
    t.betrag,
    t.status,
    t.finanzinstitut,
    f.modell,
    f.produkt_kategorie
FROM tilgungen t
LEFT JOIN fahrzeugfinanzierungen f ON t.vin = f.vin
WHERE t.faellig_am BETWEEN date('now') AND date('now', '+30 days')
ORDER BY t.faellig_am
```

### `v_times_clean`

```sql
CREATE VIEW v_times_clean AS
        SELECT 
            employee_number,
            order_number,
            start_time,
            end_time,
            duration_minutes
        FROM (
            SELECT 
                employee_number,
                order_number,
                start_time,
                end_time,
                duration_minutes,
                ROW_NUMBER() OVER (
                    PARTITION BY employee_number, start_time, end_time
                    ORDER BY order_number
                ) as rn
            FROM loco_times
            WHERE end_time IS NOT NULL
            AND duration_minutes > 0
            AND order_number >= 1000
            AND type = 2
        )
        WHERE rn = 1
```

### `v_vacation_balance_2025`

```sql
CREATE VIEW v_vacation_balance_2025 AS
SELECT
    e.id as employee_id,
    e.first_name || ' ' || e.last_name as name,
    e.department_name,
    e.location as location,
    ve.total_days + ve.carried_over + ve.added_manually as anspruch,
    COALESCE(SUM(CASE
        WHEN vb.day_part = 'full' AND vb.status = 'approved' THEN 1.0
        WHEN vb.day_part = 'half' AND vb.status = 'approved' THEN 0.5
        ELSE 0
    END), 0) as verbraucht,
    COALESCE(SUM(CASE
        WHEN vb.day_part = 'full' AND vb.status = 'pending' THEN 1.0
        WHEN vb.day_part = 'half' AND vb.status = 'pending' THEN 0.5
        ELSE 0
    END), 0) as geplant,
    ve.total_days + ve.carried_over + ve.added_manually -
    COALESCE(SUM(CASE
        WHEN vb.day_part = 'full' AND vb.status = 'approved' THEN 1.0
        WHEN vb.day_part = 'half' AND vb.status = 'approved' THEN 0.5
        ELSE 0
    END), 0) as resturlaub
FROM employees e
JOIN vacation_entitlements ve ON e.id = ve.employee_id AND ve.year = 2025
LEFT JOIN vacation_bookings vb ON vb.employee_id = e.id
    AND strftime('%Y', vb.booking_date) = '2025'
WHERE e.aktiv = 1
GROUP BY e.id, e.first_name, e.last_name, e.department_name, e.location,
         ve.total_days, ve.carried_over, ve.added_manually
```

### `v_zinsbuchungen`

```sql
CREATE VIEW v_zinsbuchungen AS
SELECT 
    id,
    accounting_date,
    nominal_account,
    amount,
    debit_credit,
    posting_text,
    vehicle_reference,
    -- Bank-Gruppierung basierend auf Sachkonto & Text
    CASE 
        WHEN nominal_account IN (230011, 230101, 230311) 
             OR LOWER(posting_text) LIKE '%stellantis%'
             OR LOWER(posting_text) LIKE '%santander%'
        THEN 'Stellantis/Santander'
        
        WHEN nominal_account = 233001 
             OR LOWER(posting_text) LIKE '%genobank%'
             OR LOWER(posting_text) LIKE '%geno bank%'
        THEN 'Genobank'
        
        WHEN LOWER(posting_text) LIKE '%sparkasse%'
        THEN 'Sparkasse'
        
        WHEN LOWER(posting_text) LIKE '%hypovereinsbank%'
             OR LOWER(posting_text) LIKE '%hvb%'
        THEN 'HypoVereinsbank'
        
        ELSE 'Sonstige'
    END as bank_gruppe,
    synced_at
FROM fibu_buchungen
WHERE buchungstyp = 'zinsen'
ORDER BY accounting_date DESC
```

### `v_zinsen_monatlich`

```sql
CREATE VIEW v_zinsen_monatlich AS
SELECT 
    strftime('%Y-%m', accounting_date) as monat,
    COUNT(*) as anzahl_buchungen,
    SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END) as zinsen_soll,
    SUM(CASE WHEN debit_credit = 'H' THEN amount ELSE -amount END) as zinsen_haben,
    SUM(CASE WHEN debit_credit = 'S' THEN amount ELSE -amount END) as zinsen_netto,
    
    -- Nach Banken aufschlüsseln
    SUM(CASE 
        WHEN (nominal_account IN (230011, 230101, 230311) 
              OR LOWER(posting_text) LIKE '%stellantis%'
              OR LOWER(posting_text) LIKE '%santander%')
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as stellantis_santander,
    
    SUM(CASE 
        WHEN (nominal_account = 233001 
              OR LOWER(posting_text) LIKE '%genobank%')
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as genobank,
    
    SUM(CASE 
        WHEN LOWER(posting_text) LIKE '%sparkasse%'
             AND debit_credit = 'S'
        THEN amount 
        ELSE 0 
    END) as sparkasse,
    
    MAX(synced_at) as letzter_sync
FROM fibu_buchungen
WHERE buchungstyp = 'zinsen'
GROUP BY strftime('%Y-%m', accounting_date)
ORDER BY monat DESC
```
