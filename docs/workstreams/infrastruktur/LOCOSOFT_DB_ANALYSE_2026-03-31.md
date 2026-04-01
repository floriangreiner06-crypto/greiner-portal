# Locosoft PostgreSQL Datenbank-Analyse

**Datum:** 2026-03-31
**Server:** 10.80.80.8 (Docker-Container `locodb`)
**Datenbank:** `loco_auswertung_db`
**PostgreSQL Version:** 16.2
**Gesamtgroesse:** 2.359 MB (ca. 2,3 GB)

---

## 1. Uebersicht

| Kennzahl | Wert |
|----------|------|
| Tabellen (public Schema) | 102 |
| Views (public Schema) | 13 |
| Tabellen (private Schema) | 33 |
| Tabellen (app2 Schema) | 18 |
| Gesamtgroesse | 2.359 MB |
| Benutzer | 2 (postgres, loco_auswertung_benutzer) |

---

## 2. Alle Tabellen (public Schema) - sortiert nach Groesse

| # | Tabelle | Spalten | Zeilen (ca.) | Groesse |
|---|---------|---------|-------------|---------|
| 1 | parts_master | 34 | 1.944.973 | 467 MB |
| 2 | journal_accountings | 45 | 671.436 | 257 MB |
| 3 | model_options_code | 8 | 1.738.096 | 213 MB |
| 4 | model_options_outside | 7 | 1.512.692 | 174 MB |
| 5 | parts_supplier_numbers | 2 | 941.489 | 107 MB |
| 6 | labours | 20 | 320.974 | 76 MB |
| 7 | labours_master | 6 | 211.914 | 59 MB |
| 8 | models | 52 | 113.525 | 47 MB |
| 9 | customers_suppliers | 56 | 54.281 | 39 MB |
| 10 | parts | 19 | 158.586 | 37 MB |
| 11 | vehicle_accessories_customer | 9 | 217.669 | 24 MB |
| 12 | vehicles | 79 | 59.408 | 23 MB |
| 13 | customer_com_numbers | 14 | 78.179 | 21 MB |
| 14 | model_options_inside | 6 | 184.176 | 19 MB |
| 15 | parts_additional_descriptions | 4 | 124.542 | 16 MB |
| 16 | parts_inbound_delivery_notes | 25 | 73.590 | 14 MB |
| 17 | privacy_details | 4 | 130.402 | 12 MB |
| 18 | invoices | 39 | 60.579 | 11 MB |
| 19 | vehicle_accessories_dealer | 10 | 65.541 | 7.552 kB |
| 20 | model_options_trim | 6 | 60.590 | 7.440 kB |
| 21 | parts_stock | 31 | 44.074 | 7.336 kB |
| 22 | orders | 33 | 46.598 | 5.944 kB |
| 23 | model_to_fuels | 3 | 55.334 | 5.000 kB |
| 24 | codes_customer_list | 6 | 45.460 | 3.768 kB |
| 25 | tire_storage_wheels | 25 | 19.570 | 3.280 kB |
| 26 | dealer_vehicles | 115 | 5.766 | 2.504 kB |
| 27 | codes_vehicle_list | 6 | 29.745 | 2.360 kB |
| 28 | absence_calendar | 11 | 17.815 | 1.808 kB |
| 29 | privacy_protection_consent | 18 | 14.119 | 1.744 kB |
| 30 | transit_vehicles | 12 | 2.887 | 712 kB |
| 31 | tire_storage | 16 | 4.886 | 688 kB |
| 32 | codes_vehicle_date | 3 | 6.549 | 544 kB |
| 33 | dealer_sales_aid | 8 | 3.727 | 392 kB |
| 34 | employees_worktimes | 7 | 507 | 256 kB |
| 35 | customer_to_customercodes | 2 | 3.360 | 248 kB |
| 36 | employees_breaktimes | 6 | 413 | 224 kB |
| 37 | nominal_accounts | 8 | 1.267 | 216 kB |
| 38 | configuration_numeric | 4 | 1.437 | 200 kB |
| 39 | appointments | 47 | 9 | 160 kB |
| 40 | customer_supplier_bank_information | 5 | 1.014 | 144 kB |
| 41 | leasing_examples | 15 | 355 | 112 kB |
| 42 | parts_rebate_codes_sell | 7 | 309 | 88 kB |
| 43 | year_calendar | 6 | 505 | 80 kB |
| 44 | financing_examples | 21 | 140 | 80 kB |
| 45 | employees_history | 22 | 128 | 80 kB |
| 46 | configuration | 4 | 38 | 64 kB |
| 47 | charge_types | 4 | 400 | 64 kB |
| 48 | parts_rebate_codes_buy | 7 | 194 | 56 kB |
| 49 | makes | 16 | 48 | 56 kB |
| 50 | parts_to_vehicles | 8 | 0 | 40 kB |
| 51 | appointments_text | 11 | 9 | 32 kB |
| 52 | vat_keys | 9 | 52 | 32 kB |
| 53 | document_types | 2 | 13 | 32 kB |
| 54 | salutations | 8 | 10 | 32 kB |
| 55 | accounts_characteristics | 11 | 2 | 32 kB |
| 56 | wtp_urgency | 2 | 7 | 24 kB |
| 57 | codes_vehicle_mileage_def | 5 | 2 | 24 kB |
| 58 | labour_types | 2 | 30 | 24 kB |
| 59 | parts_rebate_groups_buy | 2 | 6 | 24 kB |
| 60 | parts_rebate_groups_sell | 2 | 8 | 24 kB |
| 61 | time_types | 2 | 4 | 24 kB |
| 62 | vehicle_sale_types | 2 | 5 | 24 kB |
| 63 | vehicle_pre_owned_codes | 2 | 5 | 24 kB |
| 64 | codes_vehicle_date_def | 6 | 15 | 24 kB |
| 65 | codes_vehicle_def | 6 | 48 | 24 kB |
| 66 | vehicle_buy_types | 2 | 6 | 24 kB |
| 67 | vehicle_types | 3 | 6 | 24 kB |
| 68 | subsidiaries | 3 | 4 | 24 kB |
| 69 | absence_types | 2 | 2 | 24 kB |
| 70 | codes_customer_def | 6 | 13 | 24 kB |
| 71 | codes_vehicle_mileage | 3 | 1 | 24 kB |
| 72 | com_number_types | 3 | 18 | 24 kB |
| 73 | wtp_pickup_bring_type | 2 | 4 | 24 kB |
| 74 | wtp_vehicle_status | 2 | 6 | 24 kB |
| 75 | wtp_progress_status | 2 | 6 | 24 kB |
| 76 | customer_codes | 2 | 21 | 24 kB |
| 77 | vehicle_bodys | 2 | 47 | 24 kB |
| 78 | fuels | 2 | 18 | 24 kB |
| 79 | privacy_channels | 3 | 12 | 24 kB |
| 80 | privacy_scopes | 2 | 3 | 24 kB |
| 81 | part_types | 2 | 19 | 24 kB |
| 82 | parts_special_prices | 5 | 135 | 24 kB |
| 83 | parts_special_offer_prices | 6 | 28 | 24 kB |
| 84 | customer_to_professioncodes | 2 | 1 | 24 kB |
| 85 | customer_profession_codes | 2 | 90 | 24 kB |
| 86 | labours_groups | 4 | 0 | 24 kB |
| 87 | invoice_types | 2 | 7 | 24 kB |
| 88 | year_calendar_day_off_codes | 2 | 5 | 24 kB |
| 89 | charge_type_descriptions | 2 | 100 | 24 kB |
| 90 | year_calendar_subsidiary_mapping | 3 | 12 | 24 kB |
| 91 | clearing_delay_types | 2 | 10 | 24 kB |
| 92 | absence_reasons | 3 | 23 | 24 kB |
| 93 | countries | 3 | 44 | 24 kB |
| 94 | employees_group_mapping | 3 | 130 | 24 kB |
| 95 | order_classifications_def | 11 | 12 | 24 kB |
| 96 | transit_customers | 12 | 0 | 16 kB |
| 97 | external_reference_parties | 4 | 0 | 8 kB |
| 98 | external_customer_references | 7 | 0 | 8 kB |
| 99 | dealer_sales_aid_bonus | 8 | 0 | 8 kB |
| 100 | tire_storage_accessories | 19 | 0 | 8 kB |
| 101 | vehicle_contact_log_pemissions | 3 | 0 | 8 kB |
| 102 | customer_contact_log_pemissions | 3 | 0 | 8 kB |

---

## 3. Spaltendetails der 20 groessten Tabellen

### 3.1 parts_master (467 MB, ~1,9 Mio. Zeilen)

Stammdaten aller Ersatzteile (Teile-Katalog).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| part_number | varchar | 20 | NO |
| description | varchar | 32 | YES |
| rebate_percent | numeric | - | YES |
| package_unit_type | varchar | 2 | YES |
| package_size | integer | - | YES |
| delivery_size | integer | - | YES |
| weight | numeric | - | YES |
| warranty_flag | varchar | 2 | YES |
| last_import_date | date | - | YES |
| price_valid_from_date | date | - | YES |
| storage_flag | varchar | 1 | YES |
| rebate_code | varchar | 4 | YES |
| parts_type | integer | - | YES |
| manufacturer_parts_type | varchar | 4 | YES |
| rr_price | numeric | - | YES |
| price_surcharge_percent | numeric | - | YES |
| selling_price_base_upe | boolean | - | YES |
| is_price_based_on_usage_value | boolean | - | YES |
| is_price_based_on_spcl_price | boolean | - | YES |
| has_price_common_surcharge | boolean | - | YES |
| allow_price_under_margin | boolean | - | YES |
| allow_price_under_usage_value | boolean | - | YES |
| is_stock_neutral | boolean | - | YES |
| is_stock_neutral_usage_v | boolean | - | YES |
| skr_carrier_flag | numeric | - | YES |
| price_import_keeps_description | boolean | - | YES |
| country_of_origin | varchar | 5 | YES |
| manufacturer_assembly_group | varchar | 7 | YES |
| has_information_ref | boolean | - | YES |
| has_costs_ref | boolean | - | YES |
| has_special_prices_ref | boolean | - | YES |
| has_special_offer_ref | boolean | - | YES |
| search_description | varchar | 32 | YES |
| description_vector | tsvector | - | YES |

### 3.2 journal_accountings (257 MB, ~671.000 Zeilen)

Buchungen / Finanzbuchhaltung (Journalbuchungen mit SKR51-Kontierung).

| Spalte | Datentyp | Nullable |
|--------|----------|----------|
| subsidiary_to_company_ref | bigint | NO |
| accounting_date | date | NO |
| document_type | text | NO |
| document_number | bigint | NO |
| position_in_document | bigint | NO |
| customer_number | bigint | YES |
| nominal_account_number | bigint | YES |
| is_balanced | text | YES |
| clearing_number | bigint | YES |
| document_date | date | YES |
| posted_value | bigint | YES |
| debit_or_credit | text | YES |
| posted_count | bigint | YES |
| branch_number | bigint | YES |
| customer_contra_account | bigint | YES |
| nominal_contra_account | bigint | YES |
| contra_account_text | text | YES |
| account_form_page_number | bigint | YES |
| account_form_page_line | bigint | YES |
| serial_number_each_month | text | YES |
| employee_number | bigint | YES |
| invoice_date | date | YES |
| invoice_number | text | YES |
| dunning_level | text | YES |
| last_dunning_date | date | YES |
| journal_page | bigint | YES |
| journal_line | bigint | YES |
| cash_discount | bigint | YES |
| term_of_payment | bigint | YES |
| posting_text | text | YES |
| vehicle_reference | text | YES |
| vat_id_number | text | YES |
| account_statement_number | bigint | YES |
| account_statement_page | bigint | YES |
| vat_key | text | YES |
| days_for_cash_discount | bigint | YES |
| day_of_actual_accounting | date | YES |
| skr51_branch | bigint | YES |
| skr51_make | bigint | YES |
| skr51_cost_center | bigint | YES |
| skr51_sales_channel | bigint | YES |
| skr51_cost_unit | bigint | YES |
| previously_used_account_no | text | YES |
| free_form_accounting_text | text | YES |
| free_form_document_text | text | YES |

### 3.3 model_options_code (213 MB, ~1,7 Mio. Zeilen)

Optionscodes fuer Fahrzeugmodelle (Sonderausstattung).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| make_number | integer | - | NO |
| model_code | varchar | 25 | NO |
| code | varchar | 20 | NO |
| description | varchar | 200 | YES |
| price | numeric | - | YES |
| optional | boolean | - | YES |
| discountable | boolean | - | YES |
| purchase_price | numeric | - | YES |

### 3.4 model_options_outside (174 MB, ~1,5 Mio. Zeilen)

Aussenfarben / Lackcodes fuer Fahrzeugmodelle.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| make_number | integer | - | NO |
| model_code | varchar | 25 | NO |
| code | varchar | 20 | NO |
| description | varchar | 200 | YES |
| price | numeric | - | YES |
| metallic | boolean | - | YES |
| option_reference | varchar | 20 | YES |

### 3.5 parts_supplier_numbers (107 MB, ~941.000 Zeilen)

Zuordnung Teilenummer zu externen Lieferantennummern.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| part_number | varchar | 20 | NO |
| external_number | varchar | 20 | YES |

### 3.6 labours (76 MB, ~321.000 Zeilen)

Arbeitspositionen auf Auftraegen (Werkstatt-Arbeitsleistungen).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| order_number | integer | - | NO |
| order_position | integer | - | NO |
| order_position_line | integer | - | NO |
| subsidiary | integer | - | YES |
| is_invoiced | boolean | - | YES |
| invoice_type | integer | - | YES |
| invoice_number | integer | - | YES |
| employee_no | integer | - | YES |
| mechanic_no | integer | - | YES |
| labour_operation_id | varchar | 20 | YES |
| is_nominal | boolean | - | YES |
| time_units | numeric | - | YES |
| net_price_in_order | numeric | - | YES |
| rebate_percent | numeric | - | YES |
| goodwill_percent | numeric | - | YES |
| charge_type | integer | - | YES |
| text_line | varchar | 80 | YES |
| usage_value | numeric | - | YES |
| negative_flag | varchar | 1 | YES |
| labour_type | varchar | 2 | YES |

### 3.7 labours_master (59 MB, ~212.000 Zeilen)

Arbeitswerte-Katalog (AWs / Standardzeiten).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| source_number | integer | - | NO |
| labour_number | varchar | 15 | NO |
| mapping_code | varchar | 10 | NO |
| text | text | - | YES |
| source | varchar | 4 | YES |
| text_vector | tsvector | - | YES |

### 3.8 models (47 MB, ~113.500 Zeilen)

Fahrzeugmodelle mit technischen Daten.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| make_number | integer | - | NO |
| model_code | varchar | 25 | NO |
| is_actual_model | boolean | - | YES |
| model_currently_available | boolean | - | YES |
| replacing_model_code | varchar | 25 | YES |
| description | varchar | 200 | YES |
| gear_count | integer | - | YES |
| seat_count | integer | - | YES |
| door_count | integer | - | YES |
| cylinder_count | integer | - | YES |
| vehicle_body | varchar | 2 | YES |
| model_labour_group | varchar | 4 | YES |
| has_hour_meter | boolean | - | YES |
| source_extern | boolean | - | YES |
| free_form_vehicle_class | varchar | 4 | YES |
| vin_begin | varchar | 11 | YES |
| vehicle_pool_code | varchar | 25 | YES |
| vehicle_pool_engine_code | varchar | 5 | YES |
| is_manual_transmission | boolean | - | YES |
| is_all_wheel_drive | boolean | - | YES |
| is_plugin_hybride | boolean | - | YES |
| unloaded_weight | integer | - | YES |
| gross_vehicle_weight | integer | - | YES |
| power_kw | integer | - | YES |
| power_kw_at_rotation | integer | - | YES |
| cubic_capacity | integer | - | YES |
| german_kba_hsn | varchar | 4 | YES |
| german_kba_tsn | varchar | 15 | YES |
| annual_tax | numeric | - | YES |
| model_year | numeric | - | YES |
| model_year_postfix | varchar | 1 | YES |
| suggested_net_retail_price | numeric | - | YES |
| suggested_net_shipping_cost | numeric | - | YES |
| european_pollutant_class | varchar | 4 | YES |
| emission_code | varchar | 4 | YES |
| carbondioxid_emission | integer | - | YES |
| nox_exhoust | numeric | - | YES |
| particle_exhoust | numeric | - | YES |
| external_schwacke_code | varchar | 20 | YES |
| skr_carrier_flag | numeric | - | YES |
| free_form_model_specification | varchar | 3 | YES |
| external_technical_type | varchar | 4 | YES |
| european_fuel_consumption_over | numeric | - | YES |
| european_fuel_consumption_coun | numeric | - | YES |
| european_fuel_consumption_city | numeric | - | YES |
| energy_consumption | numeric | - | YES |
| insurance_class_liability | integer | - | YES |
| insurance_class_part_comprehen | integer | - | YES |
| insurance_class_full_comprehen | integer | - | YES |
| fuel_code_1 | char | 1 | YES |
| fuel_code_2 | char | 1 | YES |
| description_vector | tsvector | - | YES |

### 3.9 customers_suppliers (39 MB, ~54.000 Zeilen)

Kunden- und Lieferanten-Stammdaten.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| customer_number | integer | - | NO |
| subsidiary | integer | - | YES |
| is_supplier | boolean | - | YES |
| is_natural_person | boolean | - | YES |
| is_dummy_customer | boolean | - | YES |
| salutation_code | varchar | 2 | YES |
| name_prefix | varchar | 40 | YES |
| first_name | varchar | 40 | YES |
| family_name | varchar | 40 | YES |
| name_postfix | varchar | 40 | YES |
| country_code | varchar | 3 | YES |
| zip_code | varchar | 18 | YES |
| home_city | varchar | 40 | YES |
| home_street | varchar | 40 | YES |
| contact_salutation_code | varchar | 2 | YES |
| contact_family_name | varchar | 30 | YES |
| contact_first_name | varchar | 30 | YES |
| contact_note | varchar | 30 | YES |
| contact_personal_known | boolean | - | YES |
| parts_rebate_group_buy | integer | - | YES |
| parts_rebate_group_sell | integer | - | YES |
| rebate_labour_percent | numeric | - | YES |
| rebate_material_percent | numeric | - | YES |
| rebate_new_vehicles_percent | numeric | - | YES |
| cash_discount_percent | numeric | - | YES |
| vat_id_number | varchar | 20 | YES |
| vat_id_number_checked_date | date | - | YES |
| vat_id_free_code_1 | integer | - | YES |
| vat_id_free_code_2 | integer | - | YES |
| birthday | date | - | YES |
| last_contact | date | - | YES |
| preferred_com_number_type | varchar | 1 | YES |
| created_date | date | - | YES |
| created_employee_no | integer | - | YES |
| updated_timestamp | timestamp | - | YES |
| updated_employee_no | integer | - | YES |
| name_updated_date | date | - | YES |
| name_updated_employee_no | integer | - | YES |
| sales_assistant_employee_no | integer | - | YES |
| service_assistant_employee_no | integer | - | YES |
| parts_assistant_employee_no | integer | - | YES |
| lock_by_workstation | integer | - | YES |
| lock_time | timestamp | - | YES |
| lock_trace | varchar | 100 | YES |
| lock_trigger | varchar | 100 | YES |
| lock_by_employee | integer | - | YES |
| lock_sourcecode | varchar | 200 | YES |
| lock_machine | varchar | 18 | YES |
| lock_task | integer | - | YES |
| lock_service_name | varchar | 10 | YES |
| location_latitude | numeric | - | YES |
| location_longitude | numeric | - | YES |
| order_classification_flag | char | 1 | YES |
| access_limit | integer | - | YES |
| updated_date | date | - | YES |
| fullname_vector | tsvector | - | YES |

### 3.10 parts (37 MB, ~158.600 Zeilen)

Teile-Positionen auf Auftraegen (Teile-Verbrauch in der Werkstatt).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| order_number | integer | - | NO |
| order_position | integer | - | NO |
| order_position_line | integer | - | NO |
| subsidiary | integer | - | YES |
| is_invoiced | boolean | - | YES |
| invoice_type | integer | - | YES |
| invoice_number | integer | - | YES |
| employee_no | integer | - | YES |
| mechanic_no | integer | - | YES |
| part_number | varchar | 20 | YES |
| stock_no | integer | - | YES |
| stock_removal_date | date | - | YES |
| amount | numeric | - | YES |
| sum | numeric | - | YES |
| rebate_percent | numeric | - | YES |
| goodwill_percent | numeric | - | YES |
| parts_type | integer | - | YES |
| text_line | varchar | 32 | YES |
| usage_value | numeric | - | YES |

### 3.11 vehicle_accessories_customer (24 MB, ~217.700 Zeilen)

Zubehoer / Sonderausstattung an Kundenfahrzeugen.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| vehicle_number | integer | - | NO |
| sequence | bigint | - | NO |
| code | varchar | 20 | YES |
| description | varchar | 200 | YES |
| package_reference | varchar | 10 | YES |
| optional | boolean | - | YES |
| price | numeric | - | YES |
| discountable | boolean | - | YES |
| purchase_price | numeric | - | YES |

### 3.12 vehicles (23 MB, ~59.400 Zeilen)

Fahrzeug-Stammdaten (Kunden- und Haendlerfahrzeuge).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| internal_number | integer | - | NO |
| vin | varchar | 17 | YES |
| license_plate | varchar | 12 | YES |
| license_plate_country | varchar | 3 | YES |
| license_plate_season | varchar | 6 | YES |
| make_number | integer | - | YES |
| free_form_make_text | varchar | 10 | YES |
| model_code | varchar | 25 | YES |
| free_form_model_text | varchar | 40 | YES |
| is_roadworthy | boolean | - | YES |
| is_customer_vehicle | boolean | - | YES |
| dealer_vehicle_type | varchar | 1 | YES |
| dealer_vehicle_number | integer | - | YES |
| first_registration_date | date | - | YES |
| readmission_date | date | - | YES |
| next_service_date | date | - | YES |
| next_service_km | integer | - | YES |
| next_service_miles | integer | - | YES |
| production_year | numeric | - | YES |
| owner_number | integer | - | YES |
| holder_number | integer | - | YES |
| previous_owner_number | integer | - | YES |
| previous_owner_counter | integer | - | YES |
| last_holder_change_date | date | - | YES |
| german_kba_hsn | varchar | 4 | YES |
| german_kba_tsn | varchar | 15 | YES |
| austria_nat_code | varchar | 15 | YES |
| is_prefer_km | boolean | - | YES |
| mileage_km | integer | - | YES |
| mileage_miles | integer | - | YES |
| odometer_reading_date | date | - | YES |
| engine_number | varchar | 20 | YES |
| gear_number | varchar | 20 | YES |
| unloaded_weight | integer | - | YES |
| gross_vehicle_weight | integer | - | YES |
| power_kw | integer | - | YES |
| cubic_capacity | integer | - | YES |
| is_all_accidents_repaired | boolean | - | YES |
| accidents_counter | integer | - | YES |
| has_tyre_pressure_sensor | boolean | - | YES |
| carkey_number | varchar | 15 | YES |
| internal_source_flag | varchar | 3 | YES |
| emission_code | varchar | 4 | YES |
| first_sold_country | varchar | 3 | YES |
| first_sold_dealer_code | integer | - | YES |
| body_paint_code | varchar | 20 | YES |
| body_paint_description | varchar | 40 | YES |
| is_body_paint_metallic | boolean | - | YES |
| interior_paint_code | varchar | 20 | YES |
| interior_paint_description | varchar | 40 | YES |
| trim_code | varchar | 20 | YES |
| trim_description | varchar | 40 | YES |
| fine_dust_label | varchar | 1 | YES |
| internal_assignment | varchar | 10 | YES |
| ricambi_free_input | varchar | 20 | YES |
| document_number | varchar | 10 | YES |
| salesman_number | integer | - | YES |
| sale_date | date | - | YES |
| next_emission_test_date | date | - | YES |
| next_general_inspection_date | date | - | YES |
| next_rust_inspection_date | date | - | YES |
| next_exceptional_inspection_da | date | - | YES |
| last_change_date | date | - | YES |
| last_change_employee_no | integer | - | YES |
| created_date | date | - | YES |
| created_employee_no | integer | - | YES |
| subsidiary | integer | - | YES |
| last_change_subsidiary | integer | - | YES |
| other_date_1 | date | - | YES |
| lock_by_workstation | integer | - | YES |
| lock_time | timestamp | - | YES |
| lock_trace | varchar | 100 | YES |
| lock_trigger | varchar | 100 | YES |
| lock_by_employee | integer | - | YES |
| lock_sourcecode | varchar | 200 | YES |
| lock_machine | varchar | 18 | YES |
| lock_task | integer | - | YES |
| lock_service_name | varchar | 10 | YES |
| free_form_model_text_vector | tsvector | - | YES |

### 3.13 customer_com_numbers (21 MB, ~78.200 Zeilen)

Kommunikationsnummern der Kunden (Telefon, E-Mail, etc.).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| customer_number | integer | - | NO |
| counter | bigint | - | NO |
| com_type | varchar | 1 | YES |
| is_reference | boolean | - | YES |
| only_on_1st_tab | boolean | - | YES |
| address | varchar | 300 | YES |
| has_contact_person_fields | boolean | - | YES |
| contact_salutation | varchar | 20 | YES |
| contact_firstname | varchar | 80 | YES |
| contact_lastname | varchar | 80 | YES |
| contact_description | varchar | 80 | YES |
| note | varchar | 80 | YES |
| search_address | varchar | 300 | YES |
| phone_number | varchar | 30 | YES |

### 3.14 model_options_inside (19 MB, ~184.200 Zeilen)

Innenausstattung-Optionen fuer Fahrzeugmodelle.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| make_number | integer | - | NO |
| model_code | varchar | 25 | NO |
| code | varchar | 20 | NO |
| description | varchar | 200 | YES |
| price | numeric | - | YES |
| option_reference | varchar | 20 | YES |

### 3.15 parts_additional_descriptions (16 MB, ~124.500 Zeilen)

Zusaetzliche Beschreibungen fuer Ersatzteile.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| part_number | varchar | 20 | NO |
| description | varchar | 50 | YES |
| search_description | varchar | 50 | YES |
| description_vector | tsvector | - | YES |

### 3.16 parts_inbound_delivery_notes (14 MB, ~73.600 Zeilen)

Wareneingangs-Lieferscheine (Teile-Eingang).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| supplier_number | integer | - | NO |
| year_key | integer | - | NO |
| number_main | varchar | 10 | NO |
| number_sub | varchar | 4 | NO |
| counter | integer | - | NO |
| purchase_invoice_year | integer | - | YES |
| purchase_invoice_number | varchar | 12 | YES |
| part_number | varchar | 20 | YES |
| stock_no | integer | - | YES |
| amount | numeric | - | YES |
| delivery_note_date | date | - | YES |
| parts_order_number | integer | - | YES |
| parts_order_note | varchar | 15 | YES |
| deliverers_note | varchar | 12 | YES |
| referenced_order_number | integer | - | YES |
| referenced_order_position | integer | - | YES |
| referenced_order_line | integer | - | YES |
| is_veryfied | boolean | - | YES |
| parts_order_type | integer | - | YES |
| rr_gross_price | numeric | - | YES |
| purchase_total_net_price | numeric | - | YES |
| parts_type | integer | - | YES |
| employee_number_veryfied | integer | - | YES |
| employee_number_imported | integer | - | YES |
| employee_number_last | integer | - | YES |

### 3.17 privacy_details (12 MB, ~130.400 Zeilen)

Datenschutz-Einwilligungsdetails (DSGVO).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| subsidiary_to_company_ref | integer | - | NO |
| internal_id | bigint | - | NO |
| scope_code | char | 1 | NO |
| channel_code | char | 1 | NO |

### 3.18 invoices (11 MB, ~60.600 Zeilen)

Rechnungen (Werkstatt, Teile, Kasse).

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| invoice_type | integer | - | NO |
| invoice_number | integer | - | NO |
| subsidiary | integer | - | YES |
| order_number | integer | - | YES |
| paying_customer | integer | - | YES |
| invoice_date | date | - | YES |
| service_date | date | - | YES |
| is_canceled | boolean | - | YES |
| cancelation_number | integer | - | YES |
| cancelation_date | date | - | YES |
| cancelation_employee | integer | - | YES |
| is_own_vehicle | boolean | - | YES |
| is_credit | boolean | - | YES |
| credit_invoice_type | integer | - | YES |
| credit_invoice_number | integer | - | YES |
| odometer_reading | integer | - | YES |
| creating_employee | integer | - | YES |
| internal_cost_account | integer | - | YES |
| vehicle_number | integer | - | YES |
| full_vat_basevalue | numeric | - | YES |
| full_vat_percentage | numeric | - | YES |
| full_vat_value | numeric | - | YES |
| reduced_vat_basevalue | numeric | - | YES |
| reduced_vat_percentage | numeric | - | YES |
| reduced_vat_value | numeric | - | YES |
| used_part_vat_value | numeric | - | YES |
| job_amount_net | numeric | - | YES |
| job_amount_gross | numeric | - | YES |
| job_rebate | numeric | - | YES |
| part_amount_net | numeric | - | YES |
| part_amount_gross | numeric | - | YES |
| part_rebate | numeric | - | YES |
| part_disposal | numeric | - | YES |
| total_gross | numeric | - | YES |
| total_net | numeric | - | YES |
| parts_rebate_group_sell | integer | - | YES |
| internal_created_time | timestamp | - | YES |
| internal_canceled_time | timestamp | - | YES |
| order_classification_flag | char | 1 | YES |

### 3.19 vehicle_accessories_dealer (7,5 MB, ~65.500 Zeilen)

Zubehoer/Ausstattung an Haendlerfahrzeugen.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| dealer_vehicle_type | varchar | 1 | NO |
| dealer_vehicle_number | integer | - | NO |
| sequence | bigint | - | NO |
| code | varchar | 20 | YES |
| description | varchar | 200 | YES |
| package_reference | varchar | 10 | YES |
| optional | boolean | - | YES |
| price | numeric | - | YES |
| discountable | boolean | - | YES |
| purchase_price | numeric | - | YES |

### 3.20 model_options_trim (7,4 MB, ~60.600 Zeilen)

Polster- / Bezugstoff-Optionen fuer Fahrzeugmodelle.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| make_number | integer | - | NO |
| model_code | varchar | 25 | NO |
| code | varchar | 20 | NO |
| description | varchar | 200 | YES |
| price | numeric | - | YES |
| option_reference | varchar | 20 | YES |

---

## Zusaetzlich abgefragt: parts_stock und orders

### parts_stock (7,3 MB, ~44.000 Zeilen)

Lagerbestand pro Teilenummer und Lagernummer.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| part_number | varchar | 20 | NO |
| stock_no | integer | - | NO |
| storage_location_1 | varchar | 8 | YES |
| storage_location_2 | varchar | 8 | YES |
| usage_value | numeric | - | YES |
| stock_level | numeric | - | YES |
| stock_allocated | numeric | - | YES |
| minimum_stock_level | numeric | - | YES |
| has_warn_on_below_min_level | boolean | - | YES |
| maximum_stock_level | integer | - | YES |
| stop_order_flag | varchar | 1 | YES |
| revenue_account_group | varchar | 4 | YES |
| average_sales_statstic | numeric | - | YES |
| sales_current_year | numeric | - | YES |
| sales_previous_year | numeric | - | YES |
| total_buy_value | numeric | - | YES |
| total_sell_value | numeric | - | YES |
| provider_flag | varchar | 1 | YES |
| last_outflow_date | date | - | YES |
| last_inflow_date | date | - | YES |
| unevaluated_inflow_positions | integer | - | YES |
| is_disabled_in_parts_platforms | boolean | - | YES |
| lock_* (8 Spalten) | diverse | - | YES |

### orders (5,9 MB, ~46.600 Zeilen)

Werkstatt-Auftraege.

| Spalte | Datentyp | Max. Laenge | Nullable |
|--------|----------|-------------|----------|
| number | integer | - | NO |
| subsidiary | integer | - | YES |
| order_date | timestamp | - | YES |
| created_employee_no | integer | - | YES |
| updated_employee_no | integer | - | YES |
| estimated_inbound_time | timestamp | - | YES |
| estimated_outbound_time | timestamp | - | YES |
| order_print_date | date | - | YES |
| order_taking_employee_no | integer | - | YES |
| order_delivery_employee_no | integer | - | YES |
| vehicle_number | integer | - | YES |
| dealer_vehicle_type | varchar | 1 | YES |
| dealer_vehicle_number | integer | - | YES |
| order_mileage | integer | - | YES |
| order_customer | integer | - | YES |
| paying_customer | integer | - | YES |
| parts_rebate_group_sell | integer | - | YES |
| clearing_delay_type | varchar | 1 | YES |
| urgency | integer | - | YES |
| has_empty_positions | boolean | - | YES |
| has_open_positions | boolean | - | YES |
| has_closed_positions | boolean | - | YES |
| is_over_the_counter_order | boolean | - | YES |
| order_classification_flag | char | 1 | YES |
| lock_* (8 Spalten) | diverse | - | YES |

---

## 4. Alle Views (public Schema)

| # | View | Beschreibung |
|---|------|-------------|
| 1 | customer_top_note | Oberste Notiz zum Kunden (aus private.customer_contact_log, case_number=0) |
| 2 | employees | Aktuelle Mitarbeiterdaten (employees_history WHERE is_latest_record=true) |
| 3 | times | Stempelzeiten - kombiniert Kommen/Gehen (Typ 3/4) mit Auftragsbuchungen (Typ 2) |
| 4 | vehicle_top_note | Oberste Notiz zum Fahrzeug (aus private.vehicle_contact_log, case_number=0) |
| 5 | view_invoices | Rechnungsumsaetze gruppiert nach Datum/Standort/Marke (ohne Kasse/Storno) |
| 6 | view_invoices_cash | Kassenrechnungen gruppiert nach Datum/Standort (invoice_type=5) |
| 7 | view_labours_external | Fremdleistungen: Arbeit mit charge_type 90-99 / 900-999 |
| 8 | view_labours_goodwill | Kulanz-Anteile auf Arbeitsleistungen (labour_type K/k/Ik/S/s/Is) |
| 9 | view_labours_rebate | Rabatt-Betraege auf Arbeitsleistungen |
| 10 | view_labours_usagevalue | Einstandswerte (Usage Values) fuer Arbeitsleistungen |
| 11 | view_parts_goodwill | Kulanz-Anteile auf Teile-Positionen |
| 12 | view_parts_rebate | Rabatt-Betraege auf Teile-Positionen |
| 13 | view_parts_usagevalue | Einstandswerte (Usage Values) fuer Teile |

---

## 5. Benutzer und Rechte

| Benutzer | Superuser | Login | Erstellt DBs | Erstellt Rollen | Replikation | Rechte |
|----------|-----------|-------|-------------|-----------------|-------------|--------|
| postgres | Ja | Ja | Ja | Ja | Ja | Voll (Superuser) |
| loco_auswertung_benutzer | Nein | Ja | Nein | Nein | Nein | SELECT auf alle 102 Tabellen + 13 Views (read-only) |

**Hinweis:** Der User `loco_auswertung_benutzer` hat ausschliesslich **SELECT-Rechte** (read-only) auf alle oeffentlichen Tabellen und Views. Kein INSERT, UPDATE oder DELETE.

---

## 6. Nicht-oeffentliche Schemas

### Schema: private (33 Tabellen)

Diese Tabellen sind nur ueber den `postgres`-User zugaenglich und enthalten interne Locosoft-Daten:

| Tabelle | Beschreibung |
|---------|-------------|
| appointments_items | Termin-Einzelpositionen |
| appointments_references | Termin-Referenzen |
| appointments_rentals | Mietfahrzeuge bei Terminen |
| appointments_to_orders | Zuordnung Termine zu Auftraegen |
| contract_brands | Vertragsmarken |
| customer_contact_log | Kunden-Kontaktprotokoll (Basis fuer View customer_top_note) |
| exclusions_dealer_vehicles | Ausschluss-Regeln Haendlerfahrzeuge |
| exclusions_employees | Ausschluss-Regeln Mitarbeiter |
| exclusions_stations | Ausschluss-Regeln Stationen |
| exclusions_workshop | Ausschluss-Regeln Werkstatt |
| journal_accountings | Interne Journalbuchungen (ggf. Detail-Version) |
| journal_notes | Journal-Notizen |
| journal_texts | Journal-Texte |
| menue_permissions | Menuberechtigungen |
| messages_headers | Nachrichtenkoepfe |
| messages_receivers | Nachrichtenempfaenger |
| messages_text_blocks | Nachrichtentextbausteine |
| nominal_accounts | Interne Sachkonten |
| parts_stock_take | Inventur-Positionen |
| parts_stock_take_criteria_def | Inventur-Kriterien-Definition |
| parts_stock_take_heads | Inventur-Koepfe |
| parts_stock_take_search_criteria | Inventur-Suchkriterien |
| permission_conditions | Berechtigungsbedingungen |
| permission_rule_descriptions | Berechtigungsregel-Beschreibungen |
| permission_rules | Berechtigungsregeln |
| queries | Gespeicherte Abfragen |
| rental_and_demo_vehicles | Miet- und Vorfuehrfahrzeuge |
| times | Stempelzeiten (Basis fuer View times) |
| timetable | Arbeitszeitplan |
| timetable_day_information | Arbeitszeitplan-Tagesinformationen |
| tire_bin_locations | Reifenlager-Stellplaetze |
| vehicle_contact_log | Fahrzeug-Kontaktprotokoll (Basis fuer View vehicle_top_note) |
| vehicle_license_plate_history | Kennzeichen-Historie |

### Schema: app2 (18 Tabellen)

Locosoft App2-Erweiterungen (Checklisten, Tracking, NFC):

| Tabelle | Beschreibung |
|---------|-------------|
| checklist | Checklisten |
| checklist_media | Checklisten-Medien |
| checklist_template | Checklisten-Vorlagen |
| checklist_template_filter | Checklisten-Vorlagen-Filter |
| checklist_template_group | Checklisten-Vorlagen-Gruppen |
| customer_devices | Kundengeraete |
| internal_devices | Interne Geraete |
| inventory_lock | Inventur-Sperren |
| inventory_process | Inventur-Prozesse |
| media_download_link | Medien-Download-Links |
| settings | Einstellungen |
| table_change_tracker | Aenderungs-Tracker |
| tire_storage_history | Reifenlager-Historie |
| tracking | Tracking |
| vehicle_nfc | Fahrzeug-NFC-Tags |
| vehicle_tracking | Fahrzeug-Tracking |
| version | Versions-Info |
| worktime_log | Arbeitszeitprotokoll |

---

## 7. Lokaler Spiegel - Vergleich

### Tabellen im lokalen Spiegel (drive_portal, Praefix loco_)

Wir haben **99 lokale Spiegel-Tabellen** (inkl. 1 Backup-Tabelle und 1 Sync-Tabelle).

### Tabellen auf Locosoft die NICHT lokal gespiegelt sind

| Locosoft-Tabelle | Schema | Zeilen | Groesse | Kommentar |
|-----------------|--------|--------|---------|-----------|
| model_options_code | public | 1.738.096 | 213 MB | Optionscodes Modelle - sehr gross |
| model_options_outside | public | 1.512.692 | 174 MB | Aussenfarben Modelle - sehr gross |
| model_options_inside | public | 184.176 | 19 MB | Innenausstattung Modelle |
| model_options_trim | public | 60.590 | 7,4 MB | Polster/Bezug Modelle |
| model_to_fuels | public | 55.334 | 5 MB | Modell-Kraftstoff-Zuordnung |
| models | public | 113.525 | 47 MB | Fahrzeugmodelle |
| parts_to_vehicles | public | 0 | 40 kB | Teile-Fahrzeug-Zuordnung (leer) |

**Gesamtvolumen nicht gespiegelter Tabellen:** ca. 466 MB (davon 434 MB model_options_*)

### Tabellen die NUR lokal existieren (kein Locosoft-Aequivalent)

| Lokale Tabelle | Typ | Beschreibung |
|---------------|-----|-------------|
| loco_employees | View-Spiegel | Spiegel des Views `employees` (nicht Tabelle) |
| loco_times | View-Spiegel | Spiegel des Views `times` (nicht Tabelle) |
| loco_journal_accountings_backup_20241222 | Backup | Backup der journal_accountings vom 22.12.2024 |
| locosoft_kunden_sync | Eigene Tabelle | Lokale Sync-Steuerungstabelle |

### Nicht zugaengliche Tabellen (private/app2 Schema)

Die 51 Tabellen in den Schemas `private` (33) und `app2` (18) sind mit dem User `loco_auswertung_benutzer` nicht erreichbar und daher auch nicht gespiegelt. Wichtige Tabellen dort:

- `private.times` - Basis fuer den View `times` (den wir als `loco_times` spiegeln)
- `private.journal_accountings` - Interne Buchungsdetails
- `private.customer_contact_log` - Kundenkontakt-Protokoll
- `private.vehicle_contact_log` - Fahrzeugkontakt-Protokoll
- `private.timetable` / `timetable_day_information` - Arbeitszeitplaene
- `app2.worktime_log` - Arbeitszeitprotokoll
- `app2.checklist*` - Checklisten-System
- `app2.vehicle_tracking` / `vehicle_nfc` - Fahrzeug-Tracking

---

## 8. Zusammenfassung

### Datenbankgroesse nach Bereich

| Bereich | Tabellen | Groesse (ca.) | Anteil |
|---------|----------|--------------|--------|
| Teile-Stammdaten (parts_master, parts_supplier_numbers, parts_additional_descriptions) | 3 | 590 MB | 25% |
| Modell-Optionen (model_options_*) | 4 | 414 MB | 18% |
| Buchhaltung (journal_accountings) | 1 | 257 MB | 11% |
| Werkstatt (labours, labours_master, orders, invoices, parts) | 5 | 188 MB | 8% |
| Fahrzeuge (vehicles, models, dealer_vehicles, vehicle_accessories_*) | 5 | 104 MB | 4% |
| Kunden (customers_suppliers, customer_com_numbers, privacy_*) | 4 | 73 MB | 3% |
| Uebrige | 80 | ~35 MB | 1% |
| **Gesamt** | **102** | **~2.359 MB** | **100%** |

### Spiegelungs-Status

- **95 von 102 Tabellen** (public Schema) werden lokal gespiegelt
- **7 Tabellen fehlen** im Spiegel (hauptsaechlich model_options_* und models)
- **13 Views** auf dem Server, davon werden **2 als Tabelle** gespiegelt (employees, times)
- **51 Tabellen** in private/app2 Schemas sind nicht zugaenglich
- **2 zusaetzliche lokale Tabellen** (Backup + Sync-Steuerung)
