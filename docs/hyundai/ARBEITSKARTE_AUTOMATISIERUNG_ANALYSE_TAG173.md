# Arbeitskarte Automatisierung: Analyse

**Erstellt:** 2026-01-09 (TAG 173)  
**Frage:** Können wir die Arbeitskarte (Rückseite des Werkstattauftrages) automatisiert befüllen?

---

## 📋 ARBEITSKARTE: ERFORDERLICHE FELDER

### Aus Garantie-Richtlinie 2025-09, Seiten 38-43:

**Vorderseite (Werkstattauftrag):**
1. Vollständige Angabe von Namen und Adresse des Kunden
2. Laufende Nummer des Werkstattauftrages
3. Auftragseröffnungsdatum
4. Wie und wann ist der Kunde zu erreichen
5. Amtliches Kennzeichen des Fahrzeuges
6. Bezeichnung des Fahrzeugtyps und des Modells
7. Eintrag des Erstzulassungsdatums
8. Eintrag der vollständigen (17-stelligen) Fahrgestellnummer
9. Tatsächliche Laufleistung des Fahrzeugs (Kilometerstand)
10. Welcher Termin ist mit dem Kunden für die Abholung vereinbart?
11. Serviceberater
12. Positionsbezeichnung (Kunde gibt an)
13. Laufende Nummer (bei mehreren Positionen)
14. Befund bei Fahrzeugannahme/Probefahrt (Diagnose/Veranlassung)
15. Angabe Wageninhalt
16. Vereinbarung und Bestätigung mit Unterschrift durch den Auftraggeber
17. Auftragserweiterung

**Rückseite (Arbeitskarte) - Punkt 23:**
- Diagnose durch den Arbeitsausführenden
- Hinweis über die durchgeführte Reparatur (Reparaturmaßnahme) mit Unterschrift
- Verwendete Hyundai Original-Teile
- Angewandte Arbeitszeit nach Monteur und getrennt nach Arbeitsposition
- TT-Zeiten müssen zeitlich (an/ab) separat ausgewiesen werden
- Angabe des schadenverursachenden Teiles (Teilenummer)
- Eventuelle weitere Feststellungen (durch Meister)
- Endkontrolle mit Datum, Endkilometerstand und Unterschrift

---

## 🔍 LOCOSOFT: VERFÜGBARE DATEN

### Tabellen und Felder

**1. `orders` Tabelle:**
- `number` - Auftragsnummer ✅
- `order_date` - Auftragseröffnungsdatum ✅
- `vehicle_number` - Fahrzeug-Referenz ✅
- `order_customer` - Kunden-Referenz ✅
- `order_taking_employee_no` - Serviceberater ✅

**2. `vehicles` Tabelle:**
- `license_plate` - Kennzeichen ✅
- `vin` - Fahrgestellnummer ✅
- `make_number` / `model_number` - Marke/Modell ✅
- `first_registration_date` - Erstzulassungsdatum ✅
- `mileage` - Kilometerstand ✅

**3. `customers_suppliers` Tabelle:**
- `family_name`, `first_name` - Name ✅
- `street`, `zip_code`, `city` - Adresse ✅
- `phone_number`, `mobile_number` - Kontakt ✅
- `email` - E-Mail ✅

**4. `labours` Tabelle:**
- `order_position` - Laufende Nummer ✅
- `labour_operation_id` - Arbeitsnummer ✅
- `text_line` - Positionsbezeichnung / Arbeitsbeschreibung ✅
- `time_units` - Arbeitszeit (AW) ✅
- `mechanic_no` - Monteur ✅
- `description` - Beschreibung ✅

**5. `times` Tabelle:**
- `order_number` - Auftragsnummer ✅
- `employee_number` - Mechaniker ✅
- `start_time` - Stempelzeit AN ✅
- `end_time` - Stempelzeit AB ✅
- `duration_minutes` - Dauer ✅
- `type` - Typ (2 = Arbeitszeit) ✅

**6. `parts` Tabelle:**
- `order_number` - Auftragsnummer ✅
- `part_number` - Teilenummer ✅
- `description` - Teilbeschreibung ✅
- `quantity` - Menge ✅

**7. `invoices` Tabelle:**
- `invoice_date` - Rechnungsdatum ✅
- `invoice_type` - Typ (6 = Garantie) ✅

**8. `employees_history` Tabelle:**
- `employee_number` - Mitarbeiter-Nummer ✅
- `name` - Name ✅
- `is_latest_record` - Aktueller Datensatz ✅

---

## ✅ MAPPING: ARBEITSKARTE → LOCOSOFT

| Arbeitskarte-Feld | Locosoft-Quelle | Status |
|-------------------|-----------------|--------|
| **1. Kundenname & Adresse** | `customers_suppliers` (family_name, first_name, street, zip_code, city) | ✅ Verfügbar |
| **2. Auftragsnummer** | `orders.number` | ✅ Verfügbar |
| **3. Auftragseröffnungsdatum** | `orders.order_date` | ✅ Verfügbar |
| **4. Kundenkontakt** | `customers_suppliers` (phone_number, mobile_number, email) | ✅ Verfügbar |
| **5. Kennzeichen** | `vehicles.license_plate` | ✅ Verfügbar |
| **6. Fahrzeugtyp/Modell** | `makes.description` + `models.description` | ✅ Verfügbar |
| **7. Erstzulassungsdatum** | `vehicles.first_registration_date` | ✅ Verfügbar |
| **8. Fahrgestellnummer (VIN)** | `vehicles.vin` | ✅ Verfügbar |
| **9. Kilometerstand** | `vehicles.mileage` | ✅ Verfügbar |
| **10. Abholtermin** | ❓ Nicht direkt verfügbar (möglicherweise in GUDAT) | ⚠️ Prüfen |
| **11. Serviceberater** | `employees_history` (via `orders.order_taking_employee_no`) | ✅ Verfügbar |
| **12. Positionsbezeichnung** | `labours.text_line` | ✅ Verfügbar |
| **13. Laufende Nummer** | `labours.order_position` | ✅ Verfügbar |
| **14. Befund/Diagnose** | `labours.text_line` oder GUDAT `workshopTasks.description` | ✅ Verfügbar |
| **15. Wageninhalt** | ❓ Nicht direkt verfügbar | ❌ Fehlt |
| **16. Unterschrift Kunde** | ❓ Nicht digital verfügbar | ❌ Fehlt |
| **17. Auftragserweiterung** | `labours.text_line` (bei späteren Positionen) | ✅ Verfügbar |
| **23. Diagnose durch Arbeitsausführenden** | GUDAT `workshopTasks.description` | ✅ Verfügbar |
| **23. Reparaturmaßnahme** | `labours.text_line` | ✅ Verfügbar |
| **23. Verwendete Teile** | `parts` Tabelle (part_number, description, quantity) | ✅ Verfügbar |
| **23. Arbeitszeit nach Monteur** | `times` Tabelle (start_time, end_time, duration_minutes) | ✅ Verfügbar |
| **23. TT-Zeiten (an/ab)** | `times` Tabelle (start_time, end_time) | ✅ Verfügbar |
| **23. Schadenverursachendes Teil** | `parts` Tabelle (bei Garantie) | ✅ Verfügbar |
| **23. Weitere Feststellungen** | GUDAT `workshopTasks.description` oder `labours.text_line` | ✅ Verfügbar |
| **23. Endkontrolle** | ❓ Nicht direkt verfügbar | ⚠️ Prüfen |

---

## 🚀 AUTOMATISIERUNGS-MÖGLICHKEIT

### ✅ JA, AUTOMATISIERUNG IST MÖGLICH!

**Verfügbarkeit:**
- ✅ **~90% der Felder** sind in Locosoft verfügbar
- ✅ **GUDAT-Daten** können ergänzend genutzt werden
- ⚠️ **~10% der Felder** fehlen oder sind nicht digital verfügbar

**Fehlende/Problematische Felder:**
1. **Abholtermin** - Möglicherweise in GUDAT verfügbar
2. **Wageninhalt** - Nicht digital erfasst
3. **Unterschrift Kunde** - Nicht digital verfügbar (muss manuell bleiben)
4. **Endkontrolle** - Möglicherweise in GUDAT oder Locosoft verfügbar

---

## 💡 IMPLEMENTIERUNGS-ANSATZ

### 1. Daten-Quellen kombinieren

```python
def hole_arbeitskarte_daten(order_number: int):
    """
    Holt alle Daten für die Arbeitskarte aus Locosoft + GUDAT
    """
    # Locosoft-Daten
    auftrag = hole_auftrag_aus_locosoft(order_number)
    kunde = hole_kunde_aus_locosoft(auftrag.order_customer)
    fahrzeug = hole_fahrzeug_aus_locosoft(auftrag.vehicle_number)
    positionen = hole_positionen_aus_locosoft(order_number)
    stempelzeiten = hole_stempelzeiten_aus_locosoft(order_number)
    teile = hole_teile_aus_locosoft(order_number)
    
    # GUDAT-Daten (ergänzend)
    gudat_tasks = hole_gudat_tasks(order_number)
    gudat_anmerkungen = [task.description for task in gudat_tasks if task.description]
    
    return {
        'auftrag': auftrag,
        'kunde': kunde,
        'fahrzeug': fahrzeug,
        'positionen': positionen,
        'stempelzeiten': stempelzeiten,
        'teile': teile,
        'gudat_anmerkungen': gudat_anmerkungen
    }
```

### 2. Template erstellen

```python
def generiere_arbeitskarte_pdf(order_number: int):
    """
    Generiert PDF der Arbeitskarte mit automatisch befüllten Daten
    """
    daten = hole_arbeitskarte_daten(order_number)
    
    # PDF-Template befüllen
    template = ArbeitskarteTemplate()
    template.setze_kunde(daten['kunde'])
    template.setze_auftrag(daten['auftrag'])
    template.setze_fahrzeug(daten['fahrzeug'])
    template.setze_positionen(daten['positionen'])
    template.setze_stempelzeiten(daten['stempelzeiten'])
    template.setze_teile(daten['teile'])
    template.setze_anmerkungen(daten['gudat_anmerkungen'])
    
    return template.generiere_pdf()
```

### 3. API-Endpoint

```python
@bp.route('/api/garantie/arbeitskarte/<int:order_number>')
@login_required
def get_arbeitskarte(order_number):
    """
    Gibt Arbeitskarte-Daten als JSON zurück
    """
    daten = hole_arbeitskarte_daten(order_number)
    return jsonify(daten)

@bp.route('/api/garantie/arbeitskarte/<int:order_number>/pdf')
@login_required
def get_arbeitskarte_pdf(order_number):
    """
    Generiert PDF der Arbeitskarte
    """
    pdf = generiere_arbeitskarte_pdf(order_number)
    return send_file(pdf, mimetype='application/pdf')
```

---

## 📊 VOLLSTÄNDIGKEITS-CHECKLISTE

| Feld | Automatisch | Manuell | Status |
|------|-------------|---------|--------|
| Kundenname & Adresse | ✅ | | ✅ Verfügbar |
| Auftragsnummer | ✅ | | ✅ Verfügbar |
| Auftragseröffnungsdatum | ✅ | | ✅ Verfügbar |
| Kundenkontakt | ✅ | | ✅ Verfügbar |
| Kennzeichen | ✅ | | ✅ Verfügbar |
| Fahrzeugtyp/Modell | ✅ | | ✅ Verfügbar |
| Erstzulassungsdatum | ✅ | | ✅ Verfügbar |
| Fahrgestellnummer | ✅ | | ✅ Verfügbar |
| Kilometerstand | ✅ | | ✅ Verfügbar |
| Abholtermin | ⚠️ | ⚠️ | ⚠️ Prüfen (GUDAT?) |
| Serviceberater | ✅ | | ✅ Verfügbar |
| Positionsbezeichnung | ✅ | | ✅ Verfügbar |
| Befund/Diagnose | ✅ | | ✅ Verfügbar (GUDAT) |
| Wageninhalt | | ❌ | ❌ Fehlt |
| Unterschrift Kunde | | ❌ | ❌ Muss manuell |
| Reparaturmaßnahme | ✅ | | ✅ Verfügbar |
| Verwendete Teile | ✅ | | ✅ Verfügbar |
| Arbeitszeit nach Monteur | ✅ | | ✅ Verfügbar |
| TT-Zeiten (an/ab) | ✅ | | ✅ Verfügbar |
| Schadenverursachendes Teil | ✅ | | ✅ Verfügbar |
| Weitere Feststellungen | ✅ | | ✅ Verfügbar (GUDAT) |
| Endkontrolle | ⚠️ | ⚠️ | ⚠️ Prüfen |

**Automatisierungsgrad: ~90%**

---

## ✅ FAZIT

### Automatisierung ist möglich!

**Ja, die Arbeitskarte kann zu ~90% automatisiert befüllt werden.**

**Verfügbare Datenquellen:**
1. ✅ **Locosoft** - Hauptdatenquelle für Auftrag, Kunde, Fahrzeug, Positionen, Teile, Stempelzeiten
2. ✅ **GUDAT** - Ergänzend für Diagnose-Anmerkungen (`workshopTasks.description`)
3. ⚠️ **Fehlende Felder** - Wageninhalt, Unterschrift (müssen manuell bleiben)

**Vorteile:**
- ✅ Reduziert manuelle Eingaben
- ✅ Konsistente Datenqualität
- ✅ Schnellere Abwicklung
- ✅ Vollständigkeits-Check möglich

**Einschränkungen:**
- ⚠️ ~10% der Felder müssen manuell ergänzt werden
- ⚠️ PDF-Generierung benötigt Template
- ⚠️ Integration in bestehende Workflows erforderlich

---

## 🚀 NÄCHSTE SCHRITTE

1. ✅ **Analyse abgeschlossen** → ~90% der Felder können automatisiert werden
2. ⏳ **Test-Query erstellen** → Prüfen, ob alle Daten korrekt geholt werden können
3. ⏳ **PDF-Template erstellen** → Arbeitskarte als PDF generieren
4. ⏳ **API-Endpoint** → Für Dashboard-Integration
5. ⏳ **Fehlende Felder** → Abholtermin und Endkontrolle prüfen (GUDAT?)

---

*Analyse erstellt: 2026-01-09 (TAG 173)*
