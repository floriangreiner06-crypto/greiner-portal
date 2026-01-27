# LDAP/Locosoft Sync-Vorschlag für Mitarbeiterverwaltung (TAG 213)

**Datum:** 2026-01-27  
**Zweck:** Auto-Füllung der Mitarbeiterdaten aus LDAP und Locosoft

---

## 📊 VERFÜGBARE DATENQUELLEN

### 1. **LDAP (Active Directory)**

**Verfügbare Attribute (aus `auth/ldap_connector.py`):**
- ✅ `sAMAccountName` → **ldap_username**
- ✅ `displayName` → **Anzeigename** (kann für first_name/last_name geparst werden)
- ✅ `mail` → **email** (Firmen-Email)
- ✅ `userPrincipalName` → **UPN** (alternative Email)
- ✅ `title` → **Titel** (z.B. "Dr.", "Ing.")
- ✅ `department` → **department_name** (Abteilung)
- ✅ `company` → **company** (Standort: DEG, HYU, LAN)
- ✅ `memberOf` → **Gruppen** (für Berechtigungen)

**NICHT verfügbar in LDAP:**
- ❌ Geburtstag (birthday)
- ❌ Privat-Kontaktdaten (Straße, PLZ, Stadt, Telefon, etc.)
- ❌ Eintrittsdatum (entry_date) - könnte in `description` oder `info` sein, aber nicht standard
- ❌ Personalnummer (personal_nr)

---

### 2. **Locosoft (PostgreSQL: 10.80.80.8)**

**Verfügbare Felder (aus `loco_employees` Tabelle):**
- ✅ `employee_number` → **locosoft_id** (Mapping bereits vorhanden)
- ✅ `name` → **Name** (Format: "Nachname, Vorname" oder "Nachname Vorname")
- ✅ `initials` → **Initialen**
- ✅ `employee_personnel_no` → **personal_nr** / **personal_nr_1**
- ✅ `employment_date` → **entry_date** (Eintrittsdatum)
- ✅ `termination_date` → **exit_date** (Austrittsdatum)
- ✅ `leave_date` → **leave_date** (Urlaubsdatum?)
- ✅ `subsidiary` → **location** (1=DEG, 2=HYU, 3=LAN)
- ✅ `is_flextime` → **Gleitzeit-Info**
- ✅ `productivity_factor` → **Produktivitätsfaktor**
- ✅ `schedule_index` → **Arbeitszeitmodell-Index**

**Zusätzliche Locosoft-Tabellen:**
- `loco_employees_group_mapping` → **grp_code** (Abteilungs-Code)
- `loco_employees_history` → **Historische Daten** (für Arbeitszeitmodelle)

**NICHT verfügbar in Locosoft:**
- ❌ Email-Adresse
- ❌ Privat-Kontaktdaten
- ❌ Geburtstag
- ❌ Geschlecht (gender)
- ❌ Titel (title)

---

## 🎯 MAPPING-VORSCHLAG

### **Grunddaten (employees Tabelle)**

| Portal-Feld | LDAP-Quelle | Locosoft-Quelle | Priorität | Hinweise |
|------------|-------------|-----------------|-----------|----------|
| `first_name` | ❌ | ✅ `name` (parsen) | **Locosoft** | Name aus Locosoft parsen |
| `last_name` | ❌ | ✅ `name` (parsen) | **Locosoft** | Name aus Locosoft parsen |
| `email` | ✅ `mail` | ❌ | **LDAP** | Firmen-Email aus LDAP |
| `birthday` | ❌ | ❌ | **Manuell** | Nicht verfügbar |
| `entry_date` | ❌ | ✅ `employment_date` | **Locosoft** | Eintrittsdatum |
| `exit_date` | ❌ | ✅ `termination_date` | **Locosoft** | Austrittsdatum |
| `department_name` | ✅ `department` | ✅ `grp_code` (via mapping) | **LDAP** | LDAP hat bessere Namen |
| `location` | ✅ `company` | ✅ `subsidiary` | **Beide** | Mapping: 1=DEG, 2=HYU, 3=LAN |
| `personal_nr` | ❌ | ✅ `employee_personnel_no` | **Locosoft** | Personalnummer |
| `title` | ✅ `title` | ❌ | **LDAP** | Titel (Dr., Ing., etc.) |
| `company` | ✅ `company` | ❌ | **LDAP** | Standort-Info |

### **Kontaktdaten (privat)**

| Portal-Feld | LDAP-Quelle | Locosoft-Quelle | Priorität |
|------------|-------------|-----------------|-----------|
| `private_street` | ❌ | ❌ | **Manuell** |
| `private_city` | ❌ | ❌ | **Manuell** |
| `private_postal_code` | ❌ | ❌ | **Manuell** |
| `private_country` | ❌ | ❌ | **Default: "Deutschland"** |
| `private_phone` | ❌ | ❌ | **Manuell** |
| `private_mobile` | ❌ | ❌ | **Manuell** |
| `private_fax` | ❌ | ❌ | **Manuell** |
| `private_email` | ❌ | ❌ | **Manuell** |

**Hinweis:** Privat-Kontaktdaten sind weder in LDAP noch in Locosoft verfügbar. Diese müssen manuell gepflegt werden.

### **Kontaktdaten (Firma)**

| Portal-Feld | LDAP-Quelle | Locosoft-Quelle | Priorität |
|------------|-------------|-----------------|-----------|
| `company_phone` | ❌ | ❌ | **Manuell** |
| `company_mobile` | ❌ | ❌ | **Manuell** |
| `company_fax` | ❌ | ❌ | **Manuell** |
| `company_email` | ✅ `mail` | ❌ | **LDAP** | Firmen-Email |
| `personal_nr_1` | ❌ | ✅ `employee_personnel_no` | **Locosoft** |
| `personal_nr_2` | ❌ | ❌ | **Manuell** |

### **Vertragsdaten**

| Portal-Feld | LDAP-Quelle | Locosoft-Quelle | Priorität |
|------------|-------------|-----------------|-----------|
| `company` | ✅ `company` | ❌ | **LDAP** |
| `hired_as` | ❌ | ❌ | **Manuell** |
| `activity` | ✅ `title` | ❌ | **LDAP** | Kann als Tätigkeit verwendet werden |
| `probation_end` | ❌ | ❌ | **Manuell** |
| `limited_until` | ❌ | ❌ | **Manuell** |
| `notice_period_employer` | ❌ | ❌ | **Manuell** |
| `notice_period_employee` | ❌ | ❌ | **Manuell** |
| `country` | ❌ | ❌ | **Default: "Deutschland"** |
| `federal_state` | ❌ | ❌ | **Manuell** (oder basierend auf location) |

### **Arbeitszeitmodelle**

| Portal-Feld | Locosoft-Quelle | Priorität |
|------------|-----------------|-----------|
| `start_date` | ✅ `validity_date` (aus history) | **Locosoft** |
| `end_date` | ✅ `next_validity_date` (aus history) | **Locosoft** |
| `hours_per_week` | ❌ | **Manuell** |
| `working_days_per_week` | ❌ | **Manuell** |
| `description` | ✅ `schedule_index` → Beschreibung | **Locosoft** |

**Hinweis:** Locosoft hat `loco_employees_history` mit `validity_date` und `next_validity_date`, die für Arbeitszeitmodelle verwendet werden können.

---

## 🔄 SYNC-STRATEGIE

### **Option 1: Vollständiger Sync (Empfohlen)**
- **Trigger:** Button "Aus LDAP/Locosoft synchronisieren" im Frontend
- **Ablauf:**
  1. Hole LDAP-Daten für `ldap_username`
  2. Hole Locosoft-Daten für `locosoft_id`
  3. Merge Daten nach Priorität
  4. Zeige Vorschau der Änderungen
  5. User bestätigt oder überschreibt einzelne Felder
  6. Speichere Änderungen

### **Option 2: Auto-Füllung bei Neuanlage**
- **Trigger:** Neuer Mitarbeiter wird angelegt
- **Ablauf:**
  1. User gibt `ldap_username` oder `locosoft_id` ein
  2. System lädt automatisch verfügbare Daten
  3. Felder werden vorausgefüllt
  4. User kann editieren und speichern

### **Option 3: Batch-Sync**
- **Trigger:** Admin-Funktion "Alle Mitarbeiter synchronisieren"
- **Ablauf:**
  1. Iteriere über alle Mitarbeiter mit `ldap_username` oder `locosoft_id`
  2. Lade Daten aus LDAP/Locosoft
  3. Update nur leere Felder (keine Überschreibung vorhandener Daten)
  4. Protokolliere Änderungen

---

## 💡 UMSETZUNGSVORSCHLAG

### **Phase 1: Sync-Service erstellen**

**Neue Datei:** `api/employee_sync_service.py`

```python
def sync_from_ldap(employee_id, ldap_username):
    """Lädt Daten aus LDAP und füllt leere Felder"""
    # 1. Hole LDAP-Daten
    # 2. Update employees Tabelle (nur leere Felder)
    # 3. Return: Dict mit geänderten Feldern

def sync_from_locosoft(employee_id, locosoft_id):
    """Lädt Daten aus Locosoft und füllt leere Felder"""
    # 1. Hole Locosoft-Daten
    # 2. Parse Name (first_name, last_name)
    # 3. Update employees Tabelle
    # 4. Return: Dict mit geänderten Feldern

def sync_full(employee_id):
    """Vollständiger Sync aus beiden Quellen"""
    # 1. Hole ldap_username und locosoft_id
    # 2. Sync aus LDAP
    # 3. Sync aus Locosoft
    # 4. Merge nach Priorität
    # 5. Return: Vorschau der Änderungen
```

### **Phase 2: API-Endpunkte**

**Neue Endpunkte in `api/employee_management_api.py`:**

```python
@employee_management_api.route('/employee/<int:employee_id>/sync-from-ldap', methods=['POST'])
def sync_from_ldap(employee_id):
    """Sync aus LDAP"""
    
@employee_management_api.route('/employee/<int:employee_id>/sync-from-locosoft', methods=['POST'])
def sync_from_locosoft(employee_id):
    """Sync aus Locosoft"""
    
@employee_management_api.route('/employee/<int:employee_id>/sync-preview', methods=['GET'])
def sync_preview(employee_id):
    """Zeigt Vorschau der Sync-Änderungen"""
    
@employee_management_api.route('/employee/<int:employee_id>/sync-full', methods=['POST'])
def sync_full(employee_id):
    """Vollständiger Sync aus beiden Quellen"""
```

### **Phase 3: Frontend-Integration**

**Buttons im Frontend:**
- "Aus LDAP synchronisieren" (Tab Deckblatt)
- "Aus Locosoft synchronisieren" (Tab Deckblatt)
- "Vollständig synchronisieren" (Tab Deckblatt)

**Vorschau-Modal:**
- Zeigt alle Änderungen vor dem Speichern
- User kann einzelne Felder deaktivieren
- "Überschreiben" vs. "Nur leere Felder"

---

## 📋 PRIORITÄTEN-MATRIX

### **Hoch (sollte automatisch gefüllt werden):**
1. ✅ `first_name`, `last_name` → Locosoft
2. ✅ `email` → LDAP
3. ✅ `entry_date` → Locosoft
4. ✅ `department_name` → LDAP
5. ✅ `location` → LDAP/Locosoft
6. ✅ `personal_nr` → Locosoft
7. ✅ `title` → LDAP

### **Mittel (kann automatisch gefüllt werden):**
1. ✅ `company` → LDAP
2. ✅ `activity` → LDAP (title)
3. ✅ `company_email` → LDAP
4. ✅ `exit_date` → Locosoft (wenn vorhanden)

### **Niedrig (manuell):**
1. ❌ Privat-Kontaktdaten
2. ❌ Geburtstag
3. ❌ Vertragsdetails (Probezeit, Kündigungsfristen)
4. ❌ Arbeitszeitmodelle (Details)

---

## ⚠️ HINWEISE

1. **Name-Parsing:** Locosoft `name` kann verschiedene Formate haben:
   - "Nachname, Vorname"
   - "Nachname Vorname"
   - "Vorname Nachname"
   - **Lösung:** Intelligentes Parsing mit Fallback

2. **Standort-Mapping:**
   - LDAP `company`: "DEG", "HYU", "LAN"
   - Locosoft `subsidiary`: 1=DEG, 2=HYU, 3=LAN
   - **Lösung:** Mapping-Tabelle

3. **Abteilungs-Mapping:**
   - LDAP `department`: Vollständiger Name (z.B. "Geschäftsführung")
   - Locosoft `grp_code`: Code (z.B. "GF")
   - **Lösung:** LDAP bevorzugen, Locosoft als Fallback

4. **Überschreiben vs. Ergänzen:**
   - **Standard:** Nur leere Felder füllen
   - **Option:** "Überschreiben" für explizite Updates

---

## ✅ NÄCHSTE SCHRITTE

1. **Sync-Service implementieren** (`api/employee_sync_service.py`)
2. **API-Endpunkte hinzufügen**
3. **Frontend-Buttons und Vorschau-Modal**
4. **Testen mit echten Daten**

**Geschätzter Aufwand:** 3-4 Stunden
