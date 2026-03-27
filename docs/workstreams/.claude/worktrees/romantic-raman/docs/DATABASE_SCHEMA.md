# 🗄️ GREINER PORTAL - DATENBANK-SCHEMA

**Letztes Update:** 2025-11-12  
**Datenbank:** SQLite (`/opt/greiner-portal/data/greiner_controlling.db`)

---

## 📋 ALLE TABELLEN

```
Controlling/Finanzen:
├── banken                      - Bankinstitute
├── konten                      - Bankkonten
├── transaktionen               - Kontobewegungen
├── daily_balances              - Tägliche Kontostände
├── kontostand_historie         - Historische Kontostände
├── kategorien                  - Transaktions-Kategorien
├── bankgebuehren               - Bankgebühren
├── kreditlinien                - Kreditlinien pro Konto
└── pdf_imports                 - PDF-Import-Tracking

Verkauf:
├── sales                       - Verkaufs-Transaktionen
├── vehicles                    - Fahrzeuge
├── dealer_vehicles             - Händler-Fahrzeuge
├── customers_suppliers         - Kunden/Lieferanten
└── fahrzeuge_mit_zinsen        - Fahrzeuge mit Finanzierung

Finanzierung:
├── fahrzeugfinanzierungen      - Fahrzeugfinanzierungen
├── zinssaetze_historie         - Zinssatz-Historie
└── bank_accounts               - Bank-Account-Details

Urlaubsverwaltung:
├── employees                   - Mitarbeiter
├── departments                 - Abteilungen
├── vacation_types              - Urlaubsarten
├── vacation_entitlements       - Urlaubsansprüche
├── vacation_bookings           - Urlaubsbuchungen
├── vacation_adjustments        - Urlaubskorrekturen
├── vacation_audit_log          - Audit-Log Urlaub
├── holidays                    - Feiertage
└── manager_assignments         - Manager-Zuordnungen

Auth/User:
├── users                       - Benutzer
├── roles                       - Rollen
├── user_roles                  - User-Rollen-Zuordnung
├── ad_group_role_mapping       - AD-Gruppen → Rollen
├── ldap_employee_mapping       - LDAP → Employee Mapping
├── sessions                    - User-Sessions
├── auth_audit_log              - Auth-Audit-Log
└── audit_log                   - Allgemeiner Audit-Log

Sonstiges:
├── sync_log                    - Synchronisations-Log
├── manuelle_buchungen          - Manuelle Buchungen
└── v_*                         - Views (Auswertungen)
```

---

## 🏦 KONTEN-TABELLE (Haupttabelle!)

```sql
CREATE TABLE konten (
    id               INTEGER PRIMARY KEY,
    bank_id          INTEGER NOT NULL,           -- FK zu banken.id
    kontonummer      TEXT NOT NULL,
    iban             TEXT,
    bic              TEXT,
    kontoname        TEXT,
    kontotyp         TEXT,                       -- z.B. "Girokonto", "Darlehen"
    waehrung         TEXT DEFAULT 'EUR',
    aktiv            BOOLEAN DEFAULT 1,
    eroeffnet_am     DATE,
    geschlossen_am   DATE,
    notizen          TEXT,
    erstellt_am      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inhaber          TEXT,
    kreditlinie      REAL DEFAULT 0,
    FOREIGN KEY (bank_id) REFERENCES banken(id)
);
```

**Wichtige Felder:**
- `bank_id` → JOIN mit `banken.bank_name`
- `kontoname` → Anzeigename (z.B. "057908 KK", "Sparkasse KK")
- `iban` → Eindeutige Identifikation
- `inhaber` → Kontoinhaber (Firma)
- `kreditlinie` → Verfügbarer Kreditrahmen

---

## 🏛️ BANKEN-TABELLE

```sql
CREATE TABLE banken (
    id               INTEGER PRIMARY KEY,
    bank_name        TEXT NOT NULL,              -- z.B. "Genobank Auto Greiner"
    bank_typ         TEXT,                       -- z.B. "Genossenschaftsbank"
    iban_prefix      TEXT,                       -- IBAN-Präfix für Auto-Matching
    parser_typ       TEXT,                       -- Welcher Parser für PDFs
    aktiv            BOOLEAN DEFAULT 1,
    notizen          TEXT,
    erstellt_am      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Wichtig:** `bank_name` ist der Bankname (NICHT "name"!)

---

## 💸 TRANSAKTIONEN-TABELLE

```sql
CREATE TABLE transaktionen (
    id                  INTEGER PRIMARY KEY,
    konto_id            INTEGER NOT NULL,       -- FK zu konten.id
    buchungsdatum       DATE NOT NULL,
    valutadatum         DATE,
    buchungstext        TEXT,
    verwendungszweck    TEXT,
    gegenkonto          TEXT,                   -- IBAN des Gegenkontos
    bankleitzahl        TEXT,
    betrag              REAL NOT NULL,          -- Positiv=Eingang, Negativ=Ausgang
    waehrung            TEXT DEFAULT 'EUR',
    saldo_nach_buchung  REAL,                   -- Kontostand nach dieser Buchung
    kategorie           TEXT,
    steuerrelevant      BOOLEAN DEFAULT 0,
    belegnummer         TEXT,
    pdf_quelle          TEXT,                   -- Welches PDF
    seite_im_pdf        INTEGER,
    importiert_am       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verarbeitet         BOOLEAN DEFAULT 0,
    notizen             TEXT,
    FOREIGN KEY (konto_id) REFERENCES konten(id)
);
```

**Wichtig:** 
- `saldo_nach_buchung` → Aktueller Kontostand nach dieser Transaktion
- Für aktuellen Saldo: Neueste Transaktion nach Datum sortieren

---

## 📊 VIEWS (Wichtigste)

### `v_aktuelle_kontostaende`
```sql
-- Aktuelle Kontostände aller Konten
SELECT 
    k.id, k.kontoname, k.iban,
    COALESCE(
        (SELECT t.saldo_nach_buchung 
         FROM transaktionen t 
         WHERE t.konto_id = k.id 
         ORDER BY t.buchungsdatum DESC, t.id DESC 
         LIMIT 1), 
        0
    ) as aktueller_saldo
FROM konten k
WHERE k.aktiv = 1;
```

### `v_monatliche_umsaetze`
```sql
-- Monatliche Ein- und Ausgänge pro Konto
```

### `v_kategorie_auswertung`
```sql
-- Auswertung nach Kategorien
```

---

## 🔗 WICHTIGE BEZIEHUNGEN

```
banken (1) ──< (N) konten
  │
  └─> bank_name wird über bank_id referenziert

konten (1) ──< (N) transaktionen
  │
  └─> Aktueller Saldo = letzte Transaktion.saldo_nach_buchung

konten (1) ──< (N) kreditlinien
konten (1) ──< (N) daily_balances
```

---

## 🎯 TYPISCHE QUERIES

### **Aktueller Kontostand:**
```sql
SELECT 
    k.id, k.kontoname, b.bank_name,
    (SELECT t.saldo_nach_buchung 
     FROM transaktionen t 
     WHERE t.konto_id = k.id 
     ORDER BY t.buchungsdatum DESC, t.id DESC 
     LIMIT 1) as aktueller_saldo
FROM konten k
LEFT JOIN banken b ON k.bank_id = b.id
WHERE k.aktiv = 1;
```

### **November-Transaktionen:**
```sql
SELECT COUNT(*), konto_id
FROM transaktionen
WHERE buchungsdatum >= '2025-11-01'
GROUP BY konto_id;
```

### **Transaktionen eines Kontos:**
```sql
SELECT 
    buchungsdatum, verwendungszweck, betrag, saldo_nach_buchung
FROM transaktionen
WHERE konto_id = 5
ORDER BY buchungsdatum DESC, id DESC
LIMIT 20;
```

---

## ⚠️ WICHTIGE HINWEISE

### **Bei Saldenberechnung:**
- ✅ Immer `ORDER BY buchungsdatum DESC, id DESC`
- ✅ Nicht `SUM(betrag)` verwenden!
- ✅ `saldo_nach_buchung` der neuesten Transaktion nehmen

### **Bei JOINs:**
- ✅ `konten.bank_id` → `banken.id`
- ✅ Bank-Name: `banken.bank_name` (nicht "name"!)
- ✅ Immer `LEFT JOIN` verwenden (falls Bank fehlt)

### **Bei Imports:**
- Parser setzen `saldo_nach_buchung` akkumulativ
- `pdf_quelle` für Nachvollziehbarkeit setzen
- Duplikate-Check über `konto_id + buchungsdatum + betrag`

---

## 📝 BEISPIEL-DATEN

### **Banken:**
```
ID  Bank-Name                      Bank-Typ
4   Genobank Auto Greiner         Genossenschaftsbank
5   Genobank Autohaus Greiner     Genossenschaftsbank
8   Hypovereinsbank               Sonstige
14  Sparkasse                     Sparkasse
```

### **Konten:**
```
ID  Kontoname      IBAN (gekürzt)  Bank                    Inhaber
1   Sparkasse KK   ...760036467    Sparkasse              Autohaus Greiner GmbH
5   057908 KK      ...000057908    Genobank Auto Greiner  Autohaus Greiner GmbH
6   22225 Immo KK  ...000022225    Genobank Greiner Imm.  Greiner Immob.verw. GmbH
```

---

## 🎯 FÜR CLAUDE

**Bei jeder SQL-Query:**
1. ✅ Schema in dieser Datei prüfen
2. ✅ Korrekte Spaltennamen verwenden
3. ✅ JOINs über korrekte Foreign Keys
4. ✅ Keine nicht-existierenden Spalten verwenden!

**Wenn unsicher:**
→ User fragen: "Kannst du `PRAGMA table_info(tabelle);` ausführen?"
