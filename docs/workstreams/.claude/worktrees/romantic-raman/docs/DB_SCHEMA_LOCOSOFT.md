# 🐘 LOCOSOFT POSTGRESQL-SCHEMA (AUTO-GENERIERT)

**Generiert:** 2025-12-12 09:05:02

⚠️ **Diese Datei wird automatisch generiert - nicht manuell editieren!**

---

## 📋 TABELLEN-ÜBERSICHT

**Anzahl Tabellen:** 102

| Tabelle | Spalten | Zeilen (ca.) |
|---------|---------|--------------|
| `absence_calendar` | 11 | 15,307 |
| `absence_reasons` | 3 | -1 |
| `absence_types` | 2 | -1 |
| `accounts_characteristics` | 11 | -1 |
| `appointments` | 47 | 1 |
| `appointments_text` | 11 | -1 |
| `charge_type_descriptions` | 2 | 100 |
| `charge_types` | 4 | 400 |
| `clearing_delay_types` | 2 | -1 |
| `codes_customer_def` | 6 | -1 |
| `codes_customer_list` | 6 | 44,722 |
| `codes_vehicle_date` | 3 | 6,197 |
| `codes_vehicle_date_def` | 6 | -1 |
| `codes_vehicle_def` | 6 | -1 |
| `codes_vehicle_list` | 6 | 27,702 |
| `codes_vehicle_mileage` | 3 | -1 |
| `codes_vehicle_mileage_def` | 5 | -1 |
| `com_number_types` | 3 | -1 |
| `configuration` | 4 | 38 |
| `configuration_numeric` | 4 | 1,433 |
| `countries` | 3 | -1 |
| `customer_codes` | 2 | -1 |
| `customer_com_numbers` | 14 | 76,415 |
| `customer_contact_log_pemissions` | 3 | -1 |
| `customer_profession_codes` | 2 | 90 |
| `customer_supplier_bank_information` | 5 | 993 |
| `customer_to_customercodes` | 2 | 3,260 |
| `customer_to_professioncodes` | 2 | -1 |
| `customers_suppliers` | 55 | 53,524 |
| `dealer_sales_aid` | 8 | 3,599 |
| `dealer_sales_aid_bonus` | 8 | -1 |
| `dealer_vehicles` | 115 | 5,310 |
| `document_types` | 2 | -1 |
| `employees_breaktimes` | 6 | 392 |
| `employees_group_mapping` | 3 | 126 |
| `employees_history` | 22 | 124 |
| `employees_worktimes` | 7 | 487 |
| `external_customer_references` | 7 | -1 |
| `external_reference_parties` | 4 | -1 |
| `financing_examples` | 21 | 140 |
| `fuels` | 2 | -1 |
| `invoice_types` | 2 | -1 |
| `invoices` | 39 | 54,219 |
| `journal_accountings` | 45 | 599,210 |
| `labour_types` | 2 | -1 |
| `labours` | 20 | 281,117 |
| `labours_groups` | 4 | -1 |
| `labours_master` | 6 | 211,786 |
| `leasing_examples` | 15 | 355 |
| `makes` | 16 | 48 |
| `model_options_code` | 8 | 1,730,267 |
| `model_options_inside` | 6 | 182,837 |
| `model_options_outside` | 7 | 1,409,011 |
| `model_options_trim` | 6 | 59,989 |
| `model_to_fuels` | 3 | 54,797 |
| `models` | 52 | 112,807 |
| `nominal_accounts` | 8 | 8,423 |
| `order_classifications_def` | 11 | -1 |
| `orders` | 33 | 41,048 |
| `part_types` | 2 | -1 |
| `parts` | 19 | 142,151 |
| `parts_additional_descriptions` | 4 | 123,831 |
| `parts_inbound_delivery_notes` | 25 | 66,429 |
| `parts_master` | 34 | 1,899,386 |
| `parts_rebate_codes_buy` | 7 | 194 |
| `parts_rebate_codes_sell` | 7 | 309 |
| `parts_rebate_groups_buy` | 2 | -1 |
| `parts_rebate_groups_sell` | 2 | -1 |
| `parts_special_offer_prices` | 6 | -1 |
| `parts_special_prices` | 5 | 128 |
| `parts_stock` | 31 | 42,185 |
| `parts_supplier_numbers` | 2 | 35,394 |
| `parts_to_vehicles` | 8 | -1 |
| `privacy_channels` | 3 | -1 |
| `privacy_details` | 4 | 108,945 |
| `privacy_protection_consent` | 18 | 13,084 |
| `privacy_scopes` | 2 | -1 |
| `salutations` | 8 | -1 |
| `subsidiaries` | 3 | -1 |
| `time_types` | 2 | -1 |
| `tire_storage` | 16 | 4,788 |
| `tire_storage_accessories` | 19 | -1 |
| `tire_storage_wheels` | 25 | 19,178 |
| `transit_customers` | 12 | -1 |
| `transit_vehicles` | 12 | 2,477 |
| `vat_keys` | 9 | 52 |
| `vehicle_accessories_customer` | 9 | 217,172 |
| `vehicle_accessories_dealer` | 10 | 63,836 |
| `vehicle_bodys` | 2 | -1 |
| `vehicle_buy_types` | 2 | -1 |
| `vehicle_contact_log_pemissions` | 3 | -1 |
| `vehicle_pre_owned_codes` | 2 | -1 |
| `vehicle_sale_types` | 2 | -1 |
| `vehicle_types` | 3 | -1 |
| `vehicles` | 79 | 58,561 |
| `wtp_pickup_bring_type` | 2 | -1 |
| `wtp_progress_status` | 2 | -1 |
| `wtp_urgency` | 2 | -1 |
| `wtp_vehicle_status` | 2 | -1 |
| `year_calendar` | 6 | 505 |
| `year_calendar_day_off_codes` | 2 | -1 |
| `year_calendar_subsidiary_mapping` | 3 | -1 |

---

## 📊 TABELLEN-DETAILS

### `absence_calendar` (~15,307 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `employee_number` | integer | NOT NULL |  |
| `date` | date | NOT NULL |  |
| `unique_dummy` | integer | NOT NULL |  |
| `type` | character varying |  |  |
| `is_payed` | boolean |  |  |
| `day_contingent` | numeric |  |  |
| `reason_type` | integer |  |  |
| `reason` | character varying |  |  |
| `booking_flag` | character varying |  |  |
| `time_from` | timestamp without time zone |  |  |
| `time_to` | timestamp without time zone |  |  |

### `absence_reasons` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `is_annual_vacation` | boolean |  |  |

### `absence_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `accounts_characteristics` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | bigint | NOT NULL |  |
| `skr51_branch` | bigint | NOT NULL |  |
| `skr51_make` | bigint | NOT NULL |  |
| `skr51_cost_center` | bigint | NOT NULL |  |
| `skr51_sales_channel` | bigint | NOT NULL |  |
| `skr51_cost_unit` | bigint | NOT NULL |  |
| `skr51_branch_name` | text |  |  |
| `skr51_make_description` | text |  |  |
| `skr51_cost_center_name` | text |  |  |
| `skr51_sales_channel_name` | text |  |  |
| `skr51_cost_unit_name` | text |  |  |

### `appointments` (~1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `appointment_type` | integer |  |  |
| `customer_number` | integer |  |  |
| `vehicle_number` | integer |  |  |
| `comment` | character varying |  |  |
| `created_by_employee` | integer |  |  |
| `created_timestamp` | timestamp without time zone |  |  |
| `modified_by_employee` | integer |  |  |
| `modified_timestamp` | timestamp without time zone |  |  |
| `locked_by_employee` | integer |  |  |
| `blocked_timestamp` | timestamp without time zone |  |  |
| `bring_timestamp` | timestamp without time zone |  |  |
| `return_timestamp` | timestamp without time zone |  |  |
| `pseudo_customer_name` | character varying |  |  |
| `pseudo_customer_country` | character varying |  |  |
| `pseudo_customer_zip_code` | character varying |  |  |
| `pseudo_customer_home_city` | character varying |  |  |
| `pseudo_customer_home_street` | character varying |  |  |
| `pseudo_vehicle_make_number` | integer |  |  |
| `pseudo_vehicle_make_text` | character varying |  |  |
| `pseudo_model_code` | character varying |  |  |
| `pseudo_model_text` | character varying |  |  |
| `pseudo_license_plate` | character varying |  |  |
| `pseudo_vin` | character varying |  |  |
| `order_number` | integer |  |  |
| `is_customer_reminder_allowed` | boolean |  |  |
| `customer_reminder_type` | character varying |  |  |
| `customer_reminder_timestamp` | timestamp without time zone |  |  |
| `bring_duration` | integer |  |  |
| `bring_employee_no` | integer |  |  |
| `return_duration` | integer |  |  |
| `return_employee_no` | integer |  |  |
| `customer_pickup_bring` | integer |  |  |
| `is_general_inspection_service` | boolean |  |  |
| `urgency` | integer |  |  |
| `vehicle_status` | integer |  |  |
| `progress_status` | integer |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |

### `appointments_text` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `appointment_id` | integer | NOT NULL |  |
| `description` | character varying |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |

### `charge_type_descriptions` (~100 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `charge_types` (~400 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `subsidiary` | integer | NOT NULL |  |
| `timeunit_rate` | numeric |  |  |
| `department` | integer |  |  |

### `clearing_delay_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | character | NOT NULL |  |
| `description` | character varying |  |  |

### `codes_customer_def` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `is_defined_by_dms` | boolean |  |  |
| `format` | character varying |  |  |
| `length` | integer |  |  |
| `decimal` | integer |  |  |
| `description` | character varying |  |  |

### `codes_customer_list` (~44,722 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `value_format` | character varying |  |  |
| `value_text` | character varying |  |  |
| `value_numeric` | numeric |  |  |
| `value_date` | date |  |  |

### `codes_vehicle_date` (~6,197 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `vehicle_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `date` | date |  |  |

### `codes_vehicle_date_def` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `is_defined_by_dms` | boolean |  |  |
| `month_increase_factor` | integer |  |  |
| `show_in_211_from_or_to` | character varying |  |  |
| `is_backdate_on_exceeding` | boolean |  |  |
| `description` | character varying |  |  |

### `codes_vehicle_def` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `is_defined_by_dms` | boolean |  |  |
| `format` | character varying |  |  |
| `length` | integer |  |  |
| `decimal` | integer |  |  |
| `description` | character varying |  |  |

### `codes_vehicle_list` (~27,702 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `vehicle_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `value_format` | character varying |  |  |
| `value_text` | character varying |  |  |
| `value_numeric` | numeric |  |  |
| `value_date` | date |  |  |

### `codes_vehicle_mileage` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `vehicle_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `kilometer` | integer |  |  |

### `codes_vehicle_mileage_def` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `is_defined_by_dms` | boolean |  |  |
| `mileage_increase_factor` | integer |  |  |
| `show_in_211_from_or_to` | character varying |  |  |
| `description` | character varying |  |  |

### `com_number_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `typ` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `is_office_number` | boolean |  |  |

### `configuration` (~38 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | character varying | NOT NULL |  |
| `value_numeric` | bigint | NOT NULL |  |
| `value_text` | text | NOT NULL |  |
| `description` | text |  |  |

### `configuration_numeric` (~1,433 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `parameter_number` | integer | NOT NULL |  |
| `subsidiary` | integer | NOT NULL |  |
| `text_value` | character varying |  |  |
| `description` | character varying |  |  |

### `countries` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `iso3166_alpha2` | character varying |  |  |

### `customer_codes` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `customer_com_numbers` (~76,415 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `counter` | bigint | NOT NULL |  |
| `com_type` | character varying |  |  |
| `is_reference` | boolean |  |  |
| `only_on_1st_tab` | boolean |  |  |
| `address` | character varying |  |  |
| `has_contact_person_fields` | boolean |  |  |
| `contact_salutation` | character varying |  |  |
| `contact_firstname` | character varying |  |  |
| `contact_lastname` | character varying |  |  |
| `contact_description` | character varying |  |  |
| `note` | character varying |  |  |
| `search_address` | character varying |  |  |
| `phone_number` | character varying |  |  |

### `customer_contact_log_pemissions` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `case_number` | integer | NOT NULL |  |
| `employee_no` | integer | NOT NULL |  |

### `customer_profession_codes` (~90 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `customer_supplier_bank_information` (~993 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `iban` | character varying |  |  |
| `swift` | character varying |  |  |
| `sepa_mandate_start_date` | date |  |  |
| `note` | character varying |  |  |

### `customer_to_customercodes` (~3,260 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `customer_code` | integer | NOT NULL |  |

### `customer_to_professioncodes` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `profession_code` | integer | NOT NULL |  |

### `customers_suppliers` (~53,524 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `customer_number` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `is_supplier` | boolean |  |  |
| `is_natural_person` | boolean |  |  |
| `is_dummy_customer` | boolean |  |  |
| `salutation_code` | character varying |  |  |
| `name_prefix` | character varying |  |  |
| `first_name` | character varying |  |  |
| `family_name` | character varying |  |  |
| `name_postfix` | character varying |  |  |
| `country_code` | character varying |  |  |
| `zip_code` | character varying |  |  |
| `home_city` | character varying |  |  |
| `home_street` | character varying |  |  |
| `contact_salutation_code` | character varying |  |  |
| `contact_family_name` | character varying |  |  |
| `contact_first_name` | character varying |  |  |
| `contact_note` | character varying |  |  |
| `contact_personal_known` | boolean |  |  |
| `parts_rebate_group_buy` | integer |  |  |
| `parts_rebate_group_sell` | integer |  |  |
| `rebate_labour_percent` | numeric |  |  |
| `rebate_material_percent` | numeric |  |  |
| `rebate_new_vehicles_percent` | numeric |  |  |
| `cash_discount_percent` | numeric |  |  |
| `vat_id_number` | character varying |  |  |
| `vat_id_number_checked_date` | date |  |  |
| `vat_id_free_code_1` | integer |  |  |
| `vat_id_free_code_2` | integer |  |  |
| `birthday` | date |  |  |
| `last_contact` | date |  |  |
| `preferred_com_number_type` | character varying |  |  |
| `created_date` | date |  |  |
| `created_employee_no` | integer |  |  |
| `updated_date` | date |  |  |
| `updated_employee_no` | integer |  |  |
| `name_updated_date` | date |  |  |
| `name_updated_employee_no` | integer |  |  |
| `sales_assistant_employee_no` | integer |  |  |
| `service_assistant_employee_no` | integer |  |  |
| `parts_assistant_employee_no` | integer |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |
| `location_latitude` | numeric |  |  |
| `location_longitude` | numeric |  |  |
| `order_classification_flag` | character |  |  |
| `access_limit` | integer |  |  |
| `fullname_vector` | tsvector |  |  |

### `dealer_sales_aid` (~3,599 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `dealer_vehicle_type` | character varying | NOT NULL |  |
| `dealer_vehicle_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `claimed_amount` | numeric |  |  |
| `available_until` | date |  |  |
| `granted_amount` | numeric |  |  |
| `was_paid_on` | date |  |  |
| `note` | character varying | NOT NULL |  |

### `dealer_sales_aid_bonus` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `dealer_vehicle_type` | character varying | NOT NULL |  |
| `dealer_vehicle_number` | integer | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `claimed_amount` | numeric |  |  |
| `available_until` | date |  |  |
| `granted_amount` | numeric |  |  |
| `was_paid_on` | date |  |  |
| `note` | character varying | NOT NULL |  |

### `dealer_vehicles` (~5,310 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `dealer_vehicle_type` | character varying | NOT NULL |  |
| `dealer_vehicle_number` | integer | NOT NULL |  |
| `vehicle_number` | integer |  |  |
| `location` | character varying |  |  |
| `buyer_customer_no` | integer |  |  |
| `deregistration_date` | date |  |  |
| `refinancing_start_date` | date |  |  |
| `refinancing_end_date` | date |  |  |
| `refinancing_value` | numeric |  |  |
| `refinancing_refundment` | numeric |  |  |
| `refinancing_bank_customer_no` | integer |  |  |
| `refinanc_interest_free_date` | date |  |  |
| `in_subsidiary` | integer |  |  |
| `in_buy_salesman_number` | integer |  |  |
| `in_buy_order_no` | character varying |  |  |
| `in_buy_order_no_date` | date |  |  |
| `in_buy_invoice_no` | character varying |  |  |
| `in_buy_invoice_no_date` | date |  |  |
| `in_buy_edp_order_no` | character varying |  |  |
| `in_buy_edp_order_no_date` | date |  |  |
| `in_is_trade_in_ken` | character varying |  |  |
| `in_is_trade_in_kom` | integer |  |  |
| `in_used_vehicle_buy_type` | character varying |  |  |
| `in_buy_list_price` | numeric |  |  |
| `in_arrival_date` | date |  |  |
| `in_expected_arrival_date` | date |  |  |
| `in_accounting_document_type` | character varying |  |  |
| `in_accounting_document_number` | bigint |  |  |
| `in_accounting_document_date` | date |  |  |
| `in_acntg_exceptional_group` | character varying |  |  |
| `in_acntg_cost_unit_new_vehicle` | numeric |  |  |
| `in_accounting_make` | numeric |  |  |
| `in_registration_reference` | character varying |  |  |
| `in_expected_repair_cost` | numeric |  |  |
| `in_order_status` | character varying |  |  |
| `out_subsidiary` | integer |  |  |
| `out_is_ready_for_sale` | boolean |  |  |
| `out_ready_for_sale_date` | date |  |  |
| `out_sale_type` | character varying |  |  |
| `out_sales_contract_number` | character varying |  |  |
| `out_sales_contract_date` | date |  |  |
| `out_is_sales_contract_confrmed` | boolean |  |  |
| `out_salesman_number_1` | integer |  |  |
| `out_salesman_number_2` | integer |  |  |
| `out_desired_shipment_date` | date |  |  |
| `out_is_registration_included` | boolean |  |  |
| `out_recommended_retail_price` | numeric |  |  |
| `out_extra_expenses` | numeric |  |  |
| `out_sale_price` | numeric |  |  |
| `out_sale_price_dealer` | numeric |  |  |
| `out_sale_price_minimum` | numeric |  |  |
| `out_sale_price_internet` | numeric |  |  |
| `out_estimated_invoice_value` | numeric |  |  |
| `out_discount_percent_vehicle` | numeric |  |  |
| `out_discount_percent_accessory` | numeric |  |  |
| `out_order_number` | integer |  |  |
| `out_invoice_type` | integer |  |  |
| `out_invoice_number` | integer |  |  |
| `out_invoice_date` | date |  |  |
| `out_deposit_invoice_type` | integer |  |  |
| `out_deposit_invoice_number` | integer |  |  |
| `out_deposit_value` | numeric |  |  |
| `out_license_plate` | character varying |  |  |
| `out_make_number` | integer |  |  |
| `out_model_code` | character varying |  |  |
| `out_license_plate_country` | character varying |  |  |
| `out_license_plate_season` | character varying |  |  |
| `calc_basic_charge` | numeric |  |  |
| `calc_accessory` | numeric |  |  |
| `calc_extra_expenses` | numeric |  |  |
| `calc_insurance` | numeric |  |  |
| `calc_usage_value_encr_external` | numeric |  |  |
| `calc_usage_value_encr_internal` | numeric |  |  |
| `calc_usage_value_encr_other` | numeric |  |  |
| `calc_total_writedown` | numeric |  |  |
| `calc_cost_percent_stockingdays` | numeric |  |  |
| `calc_interest_percent_stkdays` | numeric |  |  |
| `calc_actual_payed_interest` | numeric |  |  |
| `calc_commission_for_arranging` | numeric |  |  |
| `calc_commission_for_salesman` | numeric |  |  |
| `calc_cost_internal_invoices` | numeric |  |  |
| `calc_cost_other` | numeric |  |  |
| `calc_sales_aid` | numeric |  |  |
| `calc_sales_aid_finish` | numeric |  |  |
| `calc_sales_aid_bonus` | numeric |  |  |
| `calc_returns_workshop` | numeric |  |  |
| `exclusive_reserved_employee_no` | integer |  |  |
| `exclusive_reserved_until` | date |  |  |
| `pre_owned_car_code` | character varying |  |  |
| `is_sale_internet` | boolean |  |  |
| `is_sale_prohibit` | boolean |  |  |
| `is_agency_business` | boolean |  |  |
| `is_rental_or_school_vehicle` | boolean |  |  |
| `previous_owner_number` | integer |  |  |
| `mileage_km` | integer |  |  |
| `memo` | character varying |  |  |
| `keys_box_number` | integer |  |  |
| `last_change_date` | date |  |  |
| `last_change_employee_no` | integer |  |  |
| `created_date` | date |  |  |
| `created_employee_no` | integer |  |  |
| `has_financing_example` | boolean |  |  |
| `has_leasing_example_ref` | boolean |  |  |
| `deactivated_by_employee_no` | integer |  |  |
| `deactivated_date` | date |  |  |
| `access_limit` | integer |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |

### `document_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `document_type_in_journal` | text | NOT NULL |  |
| `document_type_description` | text |  |  |

### `employees_breaktimes` (~392 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `is_latest_record` | boolean |  |  |
| `employee_number` | integer | NOT NULL |  |
| `validity_date` | date | NOT NULL |  |
| `dayofweek` | integer | NOT NULL |  |
| `break_start` | numeric | NOT NULL |  |
| `break_end` | numeric |  |  |

### `employees_group_mapping` (~126 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `employee_number` | integer | NOT NULL |  |
| `validity_date` | date | NOT NULL |  |
| `grp_code` | character varying | NOT NULL |  |

### `employees_history` (~124 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `is_latest_record` | boolean |  |  |
| `employee_number` | integer | NOT NULL |  |
| `validity_date` | date | NOT NULL |  |
| `next_validity_date` | date |  |  |
| `subsidiary` | integer |  |  |
| `has_constant_salary` | boolean |  |  |
| `name` | character varying |  |  |
| `initials` | character varying |  |  |
| `customer_number` | integer |  |  |
| `employee_personnel_no` | integer |  |  |
| `mechanic_number` | integer |  |  |
| `salesman_number` | integer |  |  |
| `is_business_executive` | boolean |  |  |
| `is_master_craftsman` | boolean |  |  |
| `is_customer_reception` | boolean |  |  |
| `employment_date` | date |  |  |
| `termination_date` | date |  |  |
| `leave_date` | date |  |  |
| `is_flextime` | boolean |  |  |
| `break_time_registration` | character varying |  |  |
| `productivity_factor` | numeric |  |  |
| `schedule_index` | integer |  |  |

### `employees_worktimes` (~487 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `is_latest_record` | boolean |  |  |
| `employee_number` | integer | NOT NULL |  |
| `validity_date` | date | NOT NULL |  |
| `dayofweek` | integer | NOT NULL |  |
| `work_duration` | numeric |  |  |
| `worktime_start` | numeric |  |  |
| `worktime_end` | numeric |  |  |

### `external_customer_references` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `api_type` | character varying | NOT NULL |  |
| `api_id` | character varying | NOT NULL |  |
| `customer_number` | integer | NOT NULL |  |
| `subsidiary` | integer | NOT NULL |  |
| `reference` | character varying |  |  |
| `last_received_time` | timestamp without time zone |  |  |
| `version` | character varying |  |  |

### `external_reference_parties` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `api_type` | character varying | NOT NULL |  |
| `api_id` | character varying | NOT NULL |  |
| `make` | character varying |  |  |
| `description` | character varying |  |  |

### `financing_examples` (~140 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | integer | NOT NULL | nextval('financing_examples_id |
| `initial_payment` | numeric |  |  |
| `loan_amount` | numeric |  |  |
| `number_rates` | integer |  |  |
| `annual_percentage_rate` | numeric |  |  |
| `debit_interest` | numeric |  |  |
| `debit_interest_type` | character varying |  |  |
| `monthly_rate` | numeric |  |  |
| `differing_first_rate` | numeric |  |  |
| `last_rate` | numeric |  |  |
| `rate_insurance` | numeric |  |  |
| `acquisition_fee` | numeric |  |  |
| `total` | numeric |  |  |
| `interest_free_credit_until` | date |  |  |
| `interest_free_credit_amount` | numeric |  |  |
| `due_date` | integer |  |  |
| `due_date_last_rate` | integer |  |  |
| `bank_customer_no` | integer |  |  |
| `source` | character varying |  |  |
| `referenced_dealer_vehicle_type` | character varying |  |  |
| `referenced_dealer_vehicle_no` | integer |  |  |

### `fuels` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `invoice_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `invoices` (~54,219 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `invoice_type` | integer | NOT NULL |  |
| `invoice_number` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `order_number` | integer |  |  |
| `paying_customer` | integer |  |  |
| `invoice_date` | date |  |  |
| `service_date` | date |  |  |
| `is_canceled` | boolean |  |  |
| `cancelation_number` | integer |  |  |
| `cancelation_date` | date |  |  |
| `cancelation_employee` | integer |  |  |
| `is_own_vehicle` | boolean |  |  |
| `is_credit` | boolean |  |  |
| `credit_invoice_type` | integer |  |  |
| `credit_invoice_number` | integer |  |  |
| `odometer_reading` | integer |  |  |
| `creating_employee` | integer |  |  |
| `internal_cost_account` | integer |  |  |
| `vehicle_number` | integer |  |  |
| `full_vat_basevalue` | numeric |  |  |
| `full_vat_percentage` | numeric |  |  |
| `full_vat_value` | numeric |  |  |
| `reduced_vat_basevalue` | numeric |  |  |
| `reduced_vat_percentage` | numeric |  |  |
| `reduced_vat_value` | numeric |  |  |
| `used_part_vat_value` | numeric |  |  |
| `job_amount_net` | numeric |  |  |
| `job_amount_gross` | numeric |  |  |
| `job_rebate` | numeric |  |  |
| `part_amount_net` | numeric |  |  |
| `part_amount_gross` | numeric |  |  |
| `part_rebate` | numeric |  |  |
| `part_disposal` | numeric |  |  |
| `total_gross` | numeric |  |  |
| `total_net` | numeric |  |  |
| `parts_rebate_group_sell` | integer |  |  |
| `internal_created_time` | timestamp without time zone |  |  |
| `internal_canceled_time` | timestamp without time zone |  |  |
| `order_classification_flag` | character |  |  |

### `journal_accountings` (~599,210 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | bigint | NOT NULL |  |
| `accounting_date` | date | NOT NULL |  |
| `document_type` | text | NOT NULL |  |
| `document_number` | bigint | NOT NULL |  |
| `position_in_document` | bigint | NOT NULL |  |
| `customer_number` | bigint |  |  |
| `nominal_account_number` | bigint |  |  |
| `is_balanced` | text |  |  |
| `clearing_number` | bigint |  |  |
| `document_date` | date |  |  |
| `posted_value` | bigint |  |  |
| `debit_or_credit` | text |  |  |
| `posted_count` | bigint |  |  |
| `branch_number` | bigint |  |  |
| `customer_contra_account` | bigint |  |  |
| `nominal_contra_account` | bigint |  |  |
| `contra_account_text` | text |  |  |
| `account_form_page_number` | bigint |  |  |
| `account_form_page_line` | bigint |  |  |
| `serial_number_each_month` | text |  |  |
| `employee_number` | bigint |  |  |
| `invoice_date` | date |  |  |
| `invoice_number` | text |  |  |
| `dunning_level` | text |  |  |
| `last_dunning_date` | date |  |  |
| `journal_page` | bigint |  |  |
| `journal_line` | bigint |  |  |
| `cash_discount` | bigint |  |  |
| `term_of_payment` | bigint |  |  |
| `posting_text` | text |  |  |
| `vehicle_reference` | text |  |  |
| `vat_id_number` | text |  |  |
| `account_statement_number` | bigint |  |  |
| `account_statement_page` | bigint |  |  |
| `vat_key` | text |  |  |
| `days_for_cash_discount` | bigint |  |  |
| `day_of_actual_accounting` | date |  |  |
| `skr51_branch` | bigint |  |  |
| `skr51_make` | bigint |  |  |
| `skr51_cost_center` | bigint |  |  |
| `skr51_sales_channel` | bigint |  |  |
| `skr51_cost_unit` | bigint |  |  |
| `previously_used_account_no` | text |  |  |
| `free_form_accounting_text` | text |  |  |
| `free_form_document_text` | text |  |  |

### `labour_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `labours` (~281,117 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `order_number` | integer | NOT NULL |  |
| `order_position` | integer | NOT NULL |  |
| `order_position_line` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `is_invoiced` | boolean |  |  |
| `invoice_type` | integer |  |  |
| `invoice_number` | integer |  |  |
| `employee_no` | integer |  |  |
| `mechanic_no` | integer |  |  |
| `labour_operation_id` | character varying |  |  |
| `is_nominal` | boolean |  |  |
| `time_units` | numeric |  |  |
| `net_price_in_order` | numeric |  |  |
| `rebate_percent` | numeric |  |  |
| `goodwill_percent` | numeric |  |  |
| `charge_type` | integer |  |  |
| `text_line` | character varying |  |  |
| `usage_value` | numeric |  |  |
| `negative_flag` | character varying |  |  |
| `labour_type` | character varying |  |  |

### `labours_groups` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `source_number` | integer | NOT NULL |  |
| `labour_number_range` | character varying | NOT NULL |  |
| `description` | text |  |  |
| `source` | character varying |  |  |

### `labours_master` (~211,786 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `source_number` | integer | NOT NULL |  |
| `labour_number` | character varying | NOT NULL |  |
| `mapping_code` | character varying | NOT NULL |  |
| `text` | text |  |  |
| `source` | character varying |  |  |
| `text_vector` | tsvector |  |  |

### `leasing_examples` (~355 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | integer | NOT NULL | nextval('leasing_examples_id_s |
| `number_rates` | integer |  |  |
| `annual_mileage` | integer |  |  |
| `special_payment` | numeric |  |  |
| `calculation_basis` | numeric |  |  |
| `calculation_basis_factor` | numeric |  |  |
| `gross_residual_value` | numeric |  |  |
| `gross_residual_value_factor` | numeric |  |  |
| `monthly_rate` | numeric |  |  |
| `exceeding_mileage` | numeric |  |  |
| `under_usage_mileage` | numeric |  |  |
| `bank_customer_no` | integer |  |  |
| `source` | character varying |  |  |
| `referenced_dealer_vehicle_type` | character varying |  |  |
| `referenced_dealer_vehicle_no` | integer |  |  |

### `makes` (~48 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `is_actual_make` | boolean |  |  |
| `description` | character varying |  |  |
| `group_name` | character varying |  |  |
| `make_id_in_group` | character varying |  |  |
| `internal_labour_group` | integer |  |  |
| `is_production_year_visible` | boolean |  |  |
| `is_transmission_no_visible` | boolean |  |  |
| `is_engine_no_visible` | boolean |  |  |
| `is_ricambi_no_visible` | boolean |  |  |
| `ricambi_label` | character varying |  |  |
| `is_preset_finance_stock_rate` | boolean |  |  |
| `rate_free_days_new_vehicle` | integer |  |  |
| `rate_free_days_demo_vehicle` | integer |  |  |
| `special_service_2_interval` | numeric |  |  |
| `special_service_3_interval` | numeric |  |  |

### `model_options_code` (~1,730,267 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `price` | numeric |  |  |
| `optional` | boolean |  |  |
| `discountable` | boolean |  |  |
| `purchase_price` | numeric |  |  |

### `model_options_inside` (~182,837 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `price` | numeric |  |  |
| `option_reference` | character varying |  |  |

### `model_options_outside` (~1,409,011 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `price` | numeric |  |  |
| `metallic` | boolean |  |  |
| `option_reference` | character varying |  |  |

### `model_options_trim` (~59,989 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `price` | numeric |  |  |
| `option_reference` | character varying |  |  |

### `model_to_fuels` (~54,797 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `code` | character varying | NOT NULL |  |

### `models` (~112,807 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `make_number` | integer | NOT NULL |  |
| `model_code` | character varying | NOT NULL |  |
| `is_actual_model` | boolean |  |  |
| `model_currently_available` | boolean |  |  |
| `replacing_model_code` | character varying |  |  |
| `description` | character varying |  |  |
| `gear_count` | integer |  |  |
| `seat_count` | integer |  |  |
| `door_count` | integer |  |  |
| `cylinder_count` | integer |  |  |
| `vehicle_body` | character varying |  |  |
| `model_labour_group` | character varying |  |  |
| `has_hour_meter` | boolean |  |  |
| `source_extern` | boolean |  |  |
| `free_form_vehicle_class` | character varying |  |  |
| `vin_begin` | character varying |  |  |
| `vehicle_pool_code` | character varying |  |  |
| `vehicle_pool_engine_code` | character varying |  |  |
| `is_manual_transmission` | boolean |  |  |
| `is_all_wheel_drive` | boolean |  |  |
| `is_plugin_hybride` | boolean |  |  |
| `unloaded_weight` | integer |  |  |
| `gross_vehicle_weight` | integer |  |  |
| `power_kw` | integer |  |  |
| `power_kw_at_rotation` | integer |  |  |
| `cubic_capacity` | integer |  |  |
| `german_kba_hsn` | character varying |  |  |
| `german_kba_tsn` | character varying |  |  |
| `annual_tax` | numeric |  |  |
| `model_year` | numeric |  |  |
| `model_year_postfix` | character varying |  |  |
| `suggested_net_retail_price` | numeric |  |  |
| `suggested_net_shipping_cost` | numeric |  |  |
| `european_pollutant_class` | character varying |  |  |
| `emission_code` | character varying |  |  |
| `carbondioxid_emission` | integer |  |  |
| `nox_exhoust` | numeric |  |  |
| `particle_exhoust` | numeric |  |  |
| `external_schwacke_code` | character varying |  |  |
| `skr_carrier_flag` | numeric |  |  |
| `free_form_model_specification` | character varying |  |  |
| `external_technical_type` | character varying |  |  |
| `european_fuel_consumption_over` | numeric |  |  |
| `european_fuel_consumption_coun` | numeric |  |  |
| `european_fuel_consumption_city` | numeric |  |  |
| `energy_consumption` | numeric |  |  |
| `insurance_class_liability` | integer |  |  |
| `insurance_class_part_comprehen` | integer |  |  |
| `insurance_class_full_comprehen` | integer |  |  |
| `fuel_code_1` | character |  |  |
| `fuel_code_2` | character |  |  |
| `description_vector` | tsvector |  |  |

### `nominal_accounts` (~8,423 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | bigint | NOT NULL |  |
| `nominal_account_number` | bigint | NOT NULL |  |
| `account_description` | text |  |  |
| `is_profit_loss_account` | text |  |  |
| `vat_key` | text |  |  |
| `create_date` | date |  |  |
| `create_employee_number` | bigint |  |  |
| `oldest_accountable_month` | date |  |  |

### `order_classifications_def` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character | NOT NULL |  |
| `description` | character varying |  |  |
| `surcharge_type` | character |  |  |
| `is_bulk_buyer` | boolean |  |  |
| `is_special_sale` | boolean |  |  |
| `target_group` | character |  |  |
| `same_calculation_as_other` | character |  |  |
| `special_price_rebate_type` | character |  |  |
| `skr51_sales_channel` | integer |  |  |
| `user_group` | character |  |  |
| `with_disposal_cost` | boolean |  |  |

### `orders` (~41,048 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `number` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `order_date` | timestamp without time zone |  |  |
| `created_employee_no` | integer |  |  |
| `updated_employee_no` | integer |  |  |
| `estimated_inbound_time` | timestamp without time zone |  |  |
| `estimated_outbound_time` | timestamp without time zone |  |  |
| `order_print_date` | date |  |  |
| `order_taking_employee_no` | integer |  |  |
| `order_delivery_employee_no` | integer |  |  |
| `vehicle_number` | integer |  |  |
| `dealer_vehicle_type` | character varying |  |  |
| `dealer_vehicle_number` | integer |  |  |
| `order_mileage` | integer |  |  |
| `order_customer` | integer |  |  |
| `paying_customer` | integer |  |  |
| `parts_rebate_group_sell` | integer |  |  |
| `clearing_delay_type` | character varying |  |  |
| `urgency` | integer |  |  |
| `has_empty_positions` | boolean |  |  |
| `has_open_positions` | boolean |  |  |
| `has_closed_positions` | boolean |  |  |
| `is_over_the_counter_order` | boolean |  |  |
| `order_classification_flag` | character |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |

### `part_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `parts` (~142,151 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `order_number` | integer | NOT NULL |  |
| `order_position` | integer | NOT NULL |  |
| `order_position_line` | integer | NOT NULL |  |
| `subsidiary` | integer |  |  |
| `is_invoiced` | boolean |  |  |
| `invoice_type` | integer |  |  |
| `invoice_number` | integer |  |  |
| `employee_no` | integer |  |  |
| `mechanic_no` | integer |  |  |
| `part_number` | character varying |  |  |
| `stock_no` | integer |  |  |
| `stock_removal_date` | date |  |  |
| `amount` | numeric |  |  |
| `sum` | numeric |  |  |
| `rebate_percent` | numeric |  |  |
| `goodwill_percent` | numeric |  |  |
| `parts_type` | integer |  |  |
| `text_line` | character varying |  |  |
| `usage_value` | numeric |  |  |

### `parts_additional_descriptions` (~123,831 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `search_description` | character varying |  |  |
| `description_vector` | tsvector |  |  |

### `parts_inbound_delivery_notes` (~66,429 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `supplier_number` | integer | NOT NULL |  |
| `year_key` | integer | NOT NULL |  |
| `number_main` | character varying | NOT NULL |  |
| `number_sub` | character varying | NOT NULL |  |
| `counter` | integer | NOT NULL |  |
| `purchase_invoice_year` | integer |  |  |
| `purchase_invoice_number` | character varying |  |  |
| `part_number` | character varying |  |  |
| `stock_no` | integer |  |  |
| `amount` | numeric |  |  |
| `delivery_note_date` | date |  |  |
| `parts_order_number` | integer |  |  |
| `parts_order_note` | character varying |  |  |
| `deliverers_note` | character varying |  |  |
| `referenced_order_number` | integer |  |  |
| `referenced_order_position` | integer |  |  |
| `referenced_order_line` | integer |  |  |
| `is_veryfied` | boolean |  |  |
| `parts_order_type` | integer |  |  |
| `rr_gross_price` | numeric |  |  |
| `purchase_total_net_price` | numeric |  |  |
| `parts_type` | integer |  |  |
| `employee_number_veryfied` | integer |  |  |
| `employee_number_imported` | integer |  |  |
| `employee_number_last` | integer |  |  |

### `parts_master` (~1,899,386 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `description` | character varying |  |  |
| `rebate_percent` | numeric |  |  |
| `package_unit_type` | character varying |  |  |
| `package_size` | integer |  |  |
| `delivery_size` | integer |  |  |
| `weight` | numeric |  |  |
| `warranty_flag` | character varying |  |  |
| `last_import_date` | date |  |  |
| `price_valid_from_date` | date |  |  |
| `storage_flag` | character varying |  |  |
| `rebate_code` | character varying |  |  |
| `parts_type` | integer |  |  |
| `manufacturer_parts_type` | character varying |  |  |
| `rr_price` | numeric |  |  |
| `price_surcharge_percent` | numeric |  |  |
| `selling_price_base_upe` | boolean |  |  |
| `is_price_based_on_usage_value` | boolean |  |  |
| `is_price_based_on_spcl_price` | boolean |  |  |
| `has_price_common_surcharge` | boolean |  |  |
| `allow_price_under_margin` | boolean |  |  |
| `allow_price_under_usage_value` | boolean |  |  |
| `is_stock_neutral` | boolean |  |  |
| `is_stock_neutral_usage_v` | boolean |  |  |
| `skr_carrier_flag` | numeric |  |  |
| `price_import_keeps_description` | boolean |  |  |
| `country_of_origin` | character varying |  |  |
| `manufacturer_assembly_group` | character varying |  |  |
| `has_information_ref` | boolean |  |  |
| `has_costs_ref` | boolean |  |  |
| `has_special_prices_ref` | boolean |  |  |
| `has_special_offer_ref` | boolean |  |  |
| `search_description` | character varying |  |  |
| `description_vector` | tsvector |  |  |

### `parts_rebate_codes_buy` (~194 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `rebate_group_code` | integer | NOT NULL |  |
| `rebate_code` | character varying | NOT NULL |  |
| `rebate_code_counter` | integer | NOT NULL |  |
| `parts_type_boundary_from` | integer |  |  |
| `parts_type_boundary_until` | integer |  |  |
| `rebate_percent` | numeric |  |  |
| `description` | character varying |  |  |

### `parts_rebate_codes_sell` (~309 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `rebate_group_code` | integer | NOT NULL |  |
| `rebate_code` | character varying | NOT NULL |  |
| `rebate_code_counter` | integer | NOT NULL |  |
| `parts_type_boundary_from` | integer |  |  |
| `parts_type_boundary_until` | integer |  |  |
| `rebate_percent` | numeric |  |  |
| `description` | character varying |  |  |

### `parts_rebate_groups_buy` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `parts_rebate_groups_sell` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `parts_special_offer_prices` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `is_active` | boolean |  |  |
| `valid_from_date` | date |  |  |
| `valid_until_date` | date |  |  |
| `price` | numeric |  |  |
| `addition_percent` | numeric |  |  |

### `parts_special_prices` (~128 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `order_classification_flag` | character varying | NOT NULL |  |
| `is_active` | boolean |  |  |
| `price` | numeric |  |  |
| `addition_percent` | numeric |  |  |

### `parts_stock` (~42,185 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `stock_no` | integer | NOT NULL |  |
| `storage_location_1` | character varying |  |  |
| `storage_location_2` | character varying |  |  |
| `usage_value` | numeric |  |  |
| `stock_level` | numeric |  |  |
| `stock_allocated` | numeric |  |  |
| `minimum_stock_level` | numeric |  |  |
| `has_warn_on_below_min_level` | boolean |  |  |
| `maximum_stock_level` | integer |  |  |
| `stop_order_flag` | character varying |  |  |
| `revenue_account_group` | character varying |  |  |
| `average_sales_statstic` | numeric |  |  |
| `sales_current_year` | numeric |  |  |
| `sales_previous_year` | numeric |  |  |
| `total_buy_value` | numeric |  |  |
| `total_sell_value` | numeric |  |  |
| `provider_flag` | character varying |  |  |
| `last_outflow_date` | date |  |  |
| `last_inflow_date` | date |  |  |
| `unevaluated_inflow_positions` | integer |  |  |
| `is_disabled_in_parts_platforms` | boolean |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |

### `parts_supplier_numbers` (~35,394 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `external_number` | character varying |  |  |

### `parts_to_vehicles` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `part_number` | character varying | NOT NULL |  |
| `unique_reference` | character varying | NOT NULL |  |
| `unique_counter` | integer | NOT NULL |  |
| `note` | character varying |  |  |
| `vin_pattern` | character varying |  |  |
| `model_pattern` | character varying |  |  |
| `model_date_start` | date |  |  |
| `model_date_end` | date |  |  |

### `privacy_channels` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `channel_code` | character | NOT NULL |  |
| `is_business` | boolean |  |  |
| `description` | character varying |  |  |

### `privacy_details` (~108,945 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | integer | NOT NULL |  |
| `internal_id` | bigint | NOT NULL |  |
| `scope_code` | character | NOT NULL |  |
| `channel_code` | character | NOT NULL |  |

### `privacy_protection_consent` (~13,084 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | integer | NOT NULL |  |
| `internal_id` | bigint | NOT NULL |  |
| `customer_number` | integer |  |  |
| `make_name` | character varying |  |  |
| `validity_date_start` | date |  |  |
| `validity_date_end` | date |  |  |
| `created_timestamp` | timestamp without time zone |  |  |
| `created_employee_no` | integer |  |  |
| `last_change_timestamp` | timestamp without time zone |  |  |
| `last_change_employee_no` | integer |  |  |
| `first_ackno_timestamp` | timestamp without time zone |  |  |
| `first_ackno_employee_no` | integer |  |  |
| `last_ackno_timestamp` | timestamp without time zone |  |  |
| `last_ackno_employee_no` | integer |  |  |
| `first_consent_timestamp` | timestamp without time zone |  |  |
| `first_consent_employee_no` | integer |  |  |
| `last_consent_timestamp` | timestamp without time zone |  |  |
| `last_consent_employee_no` | integer |  |  |

### `privacy_scopes` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `scope_code` | character | NOT NULL |  |
| `description` | character varying |  |  |

### `salutations` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `main_salutation` | character varying |  |  |
| `title` | character varying |  |  |
| `salutation_in_forms` | character varying |  |  |
| `receiver_salutation` | character varying |  |  |
| `full_salutation` | character varying |  |  |
| `multiline_line_1` | character varying |  |  |
| `multiline_line_2` | character varying |  |  |

### `subsidiaries` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary` | integer | NOT NULL |  |
| `description` | character varying |  |  |
| `subsidiary_to_company_ref` | integer |  |  |

### `time_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `tire_storage` (~4,788 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `case_number` | integer | NOT NULL |  |
| `customer_number` | integer |  |  |
| `vehicle_number` | integer |  |  |
| `order_number` | integer |  |  |
| `is_historic` | boolean |  |  |
| `is_planned` | boolean |  |  |
| `start_date` | date |  |  |
| `scheduled_end_date` | date |  |  |
| `note` | character varying |  |  |
| `stock_no` | integer |  |  |
| `date_of_removal` | date |  |  |
| `removal_employee_no` | integer |  |  |
| `price` | numeric |  |  |
| `pressure_front` | numeric |  |  |
| `pressure_rear` | numeric |  |  |
| `torque` | integer |  |  |

### `tire_storage_accessories` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `case_number` | integer | NOT NULL |  |
| `internal_counter` | integer | NOT NULL |  |
| `employee_no` | integer |  |  |
| `manufacturer` | character varying |  |  |
| `description_1` | character varying |  |  |
| `description_2` | character varying |  |  |
| `description_3` | character varying |  |  |
| `bin_location` | character varying |  |  |
| `product_type` | character varying |  |  |
| `manufacturer_code` | character varying |  |  |
| `main_position` | character varying |  |  |
| `sub_position` | character varying |  |  |
| `note` | character varying |  |  |
| `space_requirement` | integer |  |  |
| `malfunction_date` | date |  |  |
| `malfunction_employee` | integer |  |  |
| `renewal_date` | date |  |  |
| `renewal_employee` | integer |  |  |
| `removal_state` | character varying |  |  |

### `tire_storage_wheels` (~19,178 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `case_number` | integer | NOT NULL |  |
| `internal_counter` | integer | NOT NULL |  |
| `employee_no` | integer |  |  |
| `manufacturer` | character varying |  |  |
| `product_name` | character varying |  |  |
| `tire_dimension` | character varying |  |  |
| `rim_description` | character varying |  |  |
| `bin_location` | character varying |  |  |
| `product_type` | character varying |  |  |
| `note` | character varying |  |  |
| `manufacturer_code` | character varying |  |  |
| `wheel_position` | character varying |  |  |
| `tire_tread_depth` | numeric |  |  |
| `rim_nuts_included` | boolean |  |  |
| `wheel_cover_included` | boolean |  |  |
| `is_runflat` | boolean |  |  |
| `is_uhp` | boolean |  |  |
| `has_rdks` | boolean |  |  |
| `rdks_code` | character varying |  |  |
| `space_requirement` | integer |  |  |
| `malfunction_date` | date |  |  |
| `malfunction_employee` | integer |  |  |
| `renewal_date` | date |  |  |
| `renewal_employee` | integer |  |  |
| `removal_state` | character varying |  |  |

### `transit_customers` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `order_number` | integer | NOT NULL |  |
| `order_position` | integer | NOT NULL |  |
| `order_position_line` | integer | NOT NULL |  |
| `first_name` | character varying |  |  |
| `family_name` | character varying |  |  |
| `salutation_code` | character varying |  |  |
| `country` | character varying |  |  |
| `zip_code` | character varying |  |  |
| `home_city` | character varying |  |  |
| `home_street` | character varying |  |  |
| `phone_number` | character varying |  |  |
| `fullname_vector` | tsvector |  |  |

### `transit_vehicles` (~2,477 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `order_number` | integer | NOT NULL |  |
| `order_position` | integer | NOT NULL |  |
| `order_position_line` | integer | NOT NULL |  |
| `make_number` | integer |  |  |
| `make_text` | character varying |  |  |
| `model_code` | character varying |  |  |
| `model_text` | character varying |  |  |
| `color_text` | character varying |  |  |
| `license_plate` | character varying |  |  |
| `vin` | character varying |  |  |
| `first_registration_date` | date |  |  |
| `model_vector` | tsvector |  |  |

### `vat_keys` (~52 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary_to_company_ref` | bigint | NOT NULL |  |
| `vat_key` | text | NOT NULL |  |
| `key_validity_date` | date |  |  |
| `branch` | bigint |  |  |
| `description` | text |  |  |
| `vat_rate` | bigint |  |  |
| `create_date` | date |  |  |
| `vat_account` | bigint |  |  |
| `advanced_turnover_tax_pos` | bigint |  |  |

### `vehicle_accessories_customer` (~217,172 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `vehicle_number` | integer | NOT NULL |  |
| `sequence` | bigint | NOT NULL |  |
| `code` | character varying |  |  |
| `description` | character varying |  |  |
| `package_reference` | character varying |  |  |
| `optional` | boolean |  |  |
| `price` | numeric |  |  |
| `discountable` | boolean |  |  |
| `purchase_price` | numeric |  |  |

### `vehicle_accessories_dealer` (~63,836 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `dealer_vehicle_type` | character varying | NOT NULL |  |
| `dealer_vehicle_number` | integer | NOT NULL |  |
| `sequence` | bigint | NOT NULL |  |
| `code` | character varying |  |  |
| `description` | character varying |  |  |
| `package_reference` | character varying |  |  |
| `optional` | boolean |  |  |
| `price` | numeric |  |  |
| `discountable` | boolean |  |  |
| `purchase_price` | numeric |  |  |

### `vehicle_bodys` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `vehicle_buy_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `vehicle_contact_log_pemissions` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `vehicle_number` | integer | NOT NULL |  |
| `case_number` | integer | NOT NULL |  |
| `employee_no` | integer | NOT NULL |  |

### `vehicle_pre_owned_codes` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `vehicle_sale_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `description` | character varying |  |  |

### `vehicle_types` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | character varying | NOT NULL |  |
| `is_new_or_similar` | boolean |  |  |
| `description` | character varying |  |  |

### `vehicles` (~58,561 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `internal_number` | integer | NOT NULL |  |
| `vin` | character varying |  |  |
| `license_plate` | character varying |  |  |
| `license_plate_country` | character varying |  |  |
| `license_plate_season` | character varying |  |  |
| `make_number` | integer |  |  |
| `free_form_make_text` | character varying |  |  |
| `model_code` | character varying |  |  |
| `free_form_model_text` | character varying |  |  |
| `is_roadworthy` | boolean |  |  |
| `is_customer_vehicle` | boolean |  |  |
| `dealer_vehicle_type` | character varying |  |  |
| `dealer_vehicle_number` | integer |  |  |
| `first_registration_date` | date |  |  |
| `readmission_date` | date |  |  |
| `next_service_date` | date |  |  |
| `next_service_km` | integer |  |  |
| `next_service_miles` | integer |  |  |
| `production_year` | numeric |  |  |
| `owner_number` | integer |  |  |
| `holder_number` | integer |  |  |
| `previous_owner_number` | integer |  |  |
| `previous_owner_counter` | integer |  |  |
| `last_holder_change_date` | date |  |  |
| `german_kba_hsn` | character varying |  |  |
| `german_kba_tsn` | character varying |  |  |
| `austria_nat_code` | character varying |  |  |
| `is_prefer_km` | boolean |  |  |
| `mileage_km` | integer |  |  |
| `mileage_miles` | integer |  |  |
| `odometer_reading_date` | date |  |  |
| `engine_number` | character varying |  |  |
| `gear_number` | character varying |  |  |
| `unloaded_weight` | integer |  |  |
| `gross_vehicle_weight` | integer |  |  |
| `power_kw` | integer |  |  |
| `cubic_capacity` | integer |  |  |
| `is_all_accidents_repaired` | boolean |  |  |
| `accidents_counter` | integer |  |  |
| `has_tyre_pressure_sensor` | boolean |  |  |
| `carkey_number` | character varying |  |  |
| `internal_source_flag` | character varying |  |  |
| `emission_code` | character varying |  |  |
| `first_sold_country` | character varying |  |  |
| `first_sold_dealer_code` | integer |  |  |
| `body_paint_code` | character varying |  |  |
| `body_paint_description` | character varying |  |  |
| `is_body_paint_metallic` | boolean |  |  |
| `interior_paint_code` | character varying |  |  |
| `interior_paint_description` | character varying |  |  |
| `trim_code` | character varying |  |  |
| `trim_description` | character varying |  |  |
| `fine_dust_label` | character varying |  |  |
| `internal_assignment` | character varying |  |  |
| `ricambi_free_input` | character varying |  |  |
| `document_number` | character varying |  |  |
| `salesman_number` | integer |  |  |
| `sale_date` | date |  |  |
| `next_emission_test_date` | date |  |  |
| `next_general_inspection_date` | date |  |  |
| `next_rust_inspection_date` | date |  |  |
| `next_exceptional_inspection_da` | date |  |  |
| `last_change_date` | date |  |  |
| `last_change_employee_no` | integer |  |  |
| `created_date` | date |  |  |
| `created_employee_no` | integer |  |  |
| `subsidiary` | integer |  |  |
| `last_change_subsidiary` | integer |  |  |
| `other_date_1` | date |  |  |
| `lock_by_workstation` | integer |  |  |
| `lock_time` | timestamp without time zone |  |  |
| `lock_trace` | character varying |  |  |
| `lock_trigger` | character varying |  |  |
| `lock_by_employee` | integer |  |  |
| `lock_sourcecode` | character varying |  |  |
| `lock_machine` | character varying |  |  |
| `lock_task` | integer |  |  |
| `lock_service_name` | character varying |  |  |
| `free_form_model_text_vector` | tsvector |  |  |

### `wtp_pickup_bring_type` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `type` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `wtp_progress_status` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `wtp_urgency` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `wtp_vehicle_status` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `year_calendar` (~505 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `calendar_id` | integer | NOT NULL |  |
| `date` | date | NOT NULL |  |
| `day_off_declaration` | integer |  |  |
| `is_school_holid` | boolean |  |  |
| `is_public_holid` | boolean |  |  |
| `day_note` | character varying |  |  |

### `year_calendar_day_off_codes` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `code` | integer | NOT NULL |  |
| `description` | character varying |  |  |

### `year_calendar_subsidiary_mapping` (~-1 Zeilen)

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `subsidiary` | integer | NOT NULL |  |
| `year` | integer | NOT NULL |  |
| `calendar_id` | integer |  |  |
