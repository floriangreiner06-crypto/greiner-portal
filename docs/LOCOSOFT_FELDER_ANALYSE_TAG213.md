# Locosoft-Felder Analyse (TAG 213)

**Datum:** 2026-01-27  
**Zweck:** Analyse aller verfügbaren Felder in Locosoft `employees` Tabelle

---

## 📊 VERFÜGBARE FELDER IN LOCOSOFT

### **Aktuell genutzte Felder:**

| Locosoft-Feld | Portal-Feld | Status |
|--------------|-------------|--------|
| `name` | `first_name`, `last_name` (geparst) | ✅ Genutzt |
| `employment_date` | `entry_date` | ✅ Genutzt |
| `termination_date` | `exit_date` | ✅ Genutzt |
| `employee_personnel_no` | `personal_nr`, `personal_nr_1` | ✅ Genutzt |
| `subsidiary` | `location` (gemappt) | ✅ Genutzt |
| `leave_date` | `exit_date` (Fallback) | ✅ Genutzt |

### **Verfügbare aber noch nicht genutzte Felder:**

| Locosoft-Feld | Typ | Beispiel-Wert | Mögliche Verwendung |
|--------------|-----|----------------|---------------------|
| `initials` | VARCHAR(3) | "EEG", "HHU", "AKR" | Initialen (kein Feld in employees) |
| `customer_number` | INTEGER | 1036458, 1022948 | Kunden-Nummer (kein Feld in employees) |
| `validity_date` | DATE | 2014-02-10 | Startdatum für Arbeitszeitmodell |
| `next_validity_date` | DATE | NULL | Enddatum für Arbeitszeitmodell |
| `is_flextime` | BOOLEAN | false | Gleitzeit-Info (könnte für Arbeitszeitmodelle) |
| `schedule_index` | INTEGER | 0, 100 | Arbeitszeitmodell-Index |
| `is_business_executive` | BOOLEAN | false | Geschäftsführer-Flag |
| `is_master_craftsman` | BOOLEAN | false | Meister-Flag |
| `is_customer_reception` | BOOLEAN | true | Kundenempfang-Flag |
| `productivity_factor` | NUMERIC(2,1) | 0.0 | Produktivitätsfaktor |

---

## 💡 VERWENDUNGSVORSCHLÄGE

### **1. Arbeitszeitmodelle (employee_working_time_models)**

**Felder die genutzt werden könnten:**
- `validity_date` → `start_date` (Startdatum des Arbeitszeitmodells)
- `next_validity_date` → `end_date` (Enddatum, NULL = aktuell gültig)
- `schedule_index` → `description` (Arbeitszeitmodell-Beschreibung)
- `is_flextime` → Info für Gleitzeit

**Beispiel:**
```python
# Wenn validity_date vorhanden, erstelle automatisch Arbeitszeitmodell
if loco_dict.get('validity_date'):
    # Erstelle Eintrag in employee_working_time_models
    # start_date = validity_date
    # end_date = next_validity_date (oder NULL)
    # description = f"Schedule {schedule_index}" oder ähnlich
```

### **2. Rollen/Positionen**

**Felder die genutzt werden könnten:**
- `is_business_executive` → `is_manager` oder `manager_role`
- `is_master_craftsman` → `activity` oder zusätzliches Feld
- `is_customer_reception` → Info für Rollen

### **3. Zusätzliche IDs**

**Felder die genutzt werden könnten:**
- `customer_number` → könnte als zusätzliche ID gespeichert werden
- `initials` → könnte in Kommentar oder zusätzlichem Feld

---

## 🔄 ERWEITERTE SYNC-STRATEGIE

### **Option 1: Automatische Arbeitszeitmodell-Erstellung**

Wenn `validity_date` vorhanden ist, automatisch ein Arbeitszeitmodell erstellen:

```python
# In sync_from_locosoft() nach dem Update von employees:
if loco_dict.get('validity_date'):
    # Prüfe ob Arbeitszeitmodell bereits existiert
    # Wenn nicht, erstelle neues mit:
    # - start_date = validity_date
    # - end_date = next_validity_date (oder NULL)
    # - description = f"Locosoft Schedule {schedule_index}"
```

### **Option 2: Rollen-Sync**

```python
# is_business_executive → is_manager
if loco_dict.get('is_business_executive'):
    # Setze is_manager = true
```

### **Option 3: Zusätzliche Felder in employees erweitern**

Falls benötigt, könnten wir `employees` Tabelle erweitern:
- `initials` VARCHAR(3)
- `customer_number` INTEGER
- `productivity_factor` NUMERIC(2,1)

---

## 📋 BEISPIEL-DATEN

**Edith Egner (4003):**
```
name: "Egner,Edith"
initials: "EEG"
customer_number: 1036458
employee_personnel_no: 72
employment_date: 2014-02-10
validity_date: 2014-02-10
subsidiary: 1 (Deggendorf)
is_flextime: false
schedule_index: 0
is_customer_reception: true
```

**Herbert Huber (4000):**
```
name: "Huber,Herbert"
initials: "HHU"
customer_number: 1022948
employee_personnel_no: 53
employment_date: 1986-08-11
validity_date: 1986-08-11
subsidiary: 1 (Deggendorf)
is_flextime: false
schedule_index: 100
is_customer_reception: true
```

---

## ✅ NÄCHSTE SCHRITTE

1. **Query erweitert** ✅ - Alle Felder werden jetzt abgefragt
2. **Leave Date hinzugefügt** ✅ - Wird als Fallback für exit_date genutzt
3. **Debug-Logging** ✅ - Alle Felder werden geloggt

**Optional:**
- Automatische Arbeitszeitmodell-Erstellung aus `validity_date`
- Rollen-Sync aus `is_business_executive`, etc.
- Erweiterung `employees` Tabelle für zusätzliche Felder
