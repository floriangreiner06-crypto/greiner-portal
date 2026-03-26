# DRIVE Provisionsmodul – Gesamtkonzept & Implementierungsspezifikation

**Version:** 1.0 | **Stand:** 2026-02-18
**Ziel:** Dieses Dokument dient als vollständige Spezifikation für die Implementierung des Provisionsmoduls in DRIVE. Es enthält alle Geschäftslogik, Datenbankschemas, API-Definitionen und UI-Anforderungen.

---

## 1. KONTEXT & EINORDNUNG

### 1.1 Was ist DRIVE?

DRIVE ist ein Flask-basiertes ERP-Portal für Autohaus Greiner (Multi-Marken: Opel/Stellantis, Hyundai, Leapmotor). Stack: Flask 3.x, SQLite (lokal), PostgreSQL (Locosoft extern), Jinja2 + Bootstrap 4 + jQuery, LDAP/AD-Auth, Celery + Redis für Jobs.

### 1.2 Bestehendes Verkaufsmodul

DRIVE hat bereits ein Verkaufsmodul (`api/verkauf_api.py`, `routes/verkauf_routes.py`) das Auftragseingang und Auslieferungen aus Locosoft trackt. Die Verkaufsdaten (Fahrzeuge, Käufer, Verkäufer, DB, Rg.Netto) sind bereits in DRIVE verfügbar – entweder über PostgreSQL-Direktzugriff auf Locosoft oder über die bestehende `sales`-Tabelle in SQLite.

### 1.3 Ist-Zustand der Provisionsabrechnung

Aktuell läuft die Abrechnung so:
1. CSV-Export aus Locosoft (ausgelieferte Fahrzeuge)
2. Excel-Tool (Provisionsabrechnung_V0.11.xlsm) filtert/sortiert per VBA-Makro
3. Manuell: PDF pro Verkäufer, Sammel-PDFs für Lohnbuchhaltung
4. Papierbasiert: VKL druckt aus, gibt an Verkäufer, Verkäufer prüft, gibt zurück, dann Endabrechnung

**Probleme:** Zeitaufwändig, fehleranfällig, keine Live-Transparenz, keine Nachberechnung, kein Audit-Trail.

---

## 2. WORKFLOW – VORLAUF / ENDLAUF

Inspiriert vom ADP/Autonom-System (eines der ersten deutschen DMS) mit 5-Status-Workflow:

```
ENTWURF → VORLAUF → PRÜFUNG → ENDLAUF → LOHNBUCHHALTUNG
```

### 2.1 Status-Definitionen

| Status | Beschreibung | Auslöser | Wer |
|--------|-------------|----------|-----|
| **ENTWURF** | System berechnet automatisch aus Locosoft-Daten. Verkäufer sieht Live-Preview. Noch kein DB-Eintrag als "Lauf". | Automatisch, laufend | System |
| **VORLAUF** | VKL gibt Monat frei → Provisionslauf wird erstellt, PDF "Vorlauf" generiert. Verkäufer wird benachrichtigt. | Button "Vorlauf erstellen" | VKL / Admin |
| **PRÜFUNG** | Verkäufer prüft seine Abrechnung, kann pro Position Einspruch erheben (Textfeld). | Verkäufer öffnet seine Provision | Verkäufer |
| **ENDLAUF** | VKL prüft Einsprüche, korrigiert ggf., gibt Endlauf frei. PDF "Endlauf" wird generiert. Daten sind gesperrt. | Button "Endlauf freigeben" | VKL / Admin |
| **LOHNBUCHHALTUNG** | Sammel-PDF und CSV für Lohnbuchhaltung wird automatisch generiert. | Automatisch nach Endlauf | System |

### 2.2 Live-Preview (Kernfeature)

Während des laufenden Monats sieht der Verkäufer jederzeit eine **Live-Berechnung** seiner aktuellen Provision – basierend auf den bereits ausgelieferten Fahrzeugen. Keine Speicherung in DB, reine Echtzeitberechnung. Das motiviert und schafft Transparenz.

### 2.3 Einspruch-Workflow

- Verkäufer kann pro Position einen Einspruch markieren (Flag + Freitext)
- VKL sieht alle offenen Einsprüche in seiner Dashboard-Übersicht
- VKL kann: Einspruch akzeptieren (Korrektur), ablehnen (mit Begründung), oder Position anpassen
- Erst wenn alle Einsprüche bearbeitet sind, kann Endlauf freigegeben werden

---

## 3. PROVISIONSLOGIK – DIE 5 KATEGORIEN

### Übersichtstabelle

| Kat. | Name | Maßgröße | Satz | Min | Max | Besonderheit |
|------|------|----------|------|-----|-----|-------------|
| **I** | Neuwagen | Deckungsbeitrag (DB) | 12% | – | – | + 50€ Fix/Stück (max 15 Stück/Monat) |
| **II** | Testwagen / VFW | Rg.Netto | 1% | 103€ | 500€ | Vorführwagen ggf. eigener Satz (1%, max 300€) – KLÄREN |
| **III** | Gebrauchtwagen | Rg.Netto | 1% | 103€ | 500€ | |
| **IV** | GW aus Bestand | DB − Kosten | 12% | – | – | Kosten = (DB × J60) + J61 |
| **V** | Zusatzleistungen | Manuell erfasst | Anteil% | – | – | Finanzierung, Versicherung, Garantie etc. |

### 3.1 Kategorie I – Neuwagen

```python
def calc_neuwagen(db_betrag, stueck_gesamt_monat):
    provision_prozent = db_betrag * 0.12
    # Stückprämie: 50€ pro Fahrzeug, max 15 Stück pro Monat
    stueck_praemie = min(stueck_gesamt_monat, 15) * 50
    return provision_prozent  # Stückprämie wird einmal auf Monatsebene addiert
```

- **Bemessungsgrundlage:** Deckungsbeitrag (DB) aus Locosoft
- **Satz:** 12% (konfigurierbar in `provision_config`)
- **Stückprämie:** 50€ pro ausgeliefertem Neuwagen, gedeckelt bei 15 Stück/Monat = max 750€
- **Keine** Min/Max-Grenzen auf die Prozent-Provision

### 3.2 Kategorie II – Testwagen / Vorführwagen (VFW)

```python
def calc_testwagen(rg_netto):
    provision = rg_netto * 0.01
    return max(103, min(500, provision))  # Clamp: min 103€, max 500€
```

- **Bemessungsgrundlage:** Rechnungsbetrag Netto (Rg.Netto)
- **Satz:** 1%
- **Grenzen:** min 103€, max 500€ pro Fahrzeug
- **Offener Punkt:** Vorführwagen evtl. eigener Max-Wert (300€ statt 500€) – Feld `max_betrag` in Config vorsehen

### 3.3 Kategorie III – Gebrauchtwagen

```python
def calc_gebrauchtwagen(rg_netto):
    provision = rg_netto * 0.01
    return max(103, min(500, provision))  # Identisch mit Kat. II
```

- **Bemessungsgrundlage:** Rechnungsbetrag Netto
- **Satz:** 1%
- **Grenzen:** min 103€, max 500€

### 3.4 Kategorie IV – GW aus Bestand

```python
def calc_gw_bestand(db_betrag, j60, j61):
    kosten = round((db_betrag * j60) + j61, 2)
    basis = db_betrag - kosten
    provision = basis * 0.12
    return max(0, provision)  # Keine negative Provision
```

- **Bemessungsgrundlage:** DB minus Kostenabzug
- **Kostenformel:** `(DB × J60) + J61` – J60 = Prozentsatz, J61 = Fixbetrag (beide konfigurierbar)
- **Satz:** 12% auf bereinigten DB
- **OFFENER PUNKT:** Genaue Werte für J60, J61 müssen aus der Excel-Datei / von Anton Süß bestätigt werden
- **OFFENER PUNKT:** Abgrenzung "GW aus Bestand" vs. normaler GW – welches Feld in Locosoft?

### 3.5 Kategorie V – Zusatzleistungen (MANUELL)

```python
def calc_zusatzleistung(betrag_gesamt, anteil_prozent):
    return round(betrag_gesamt * anteil_prozent / 100, 2)
```

- **Manuelle Eingabe** durch Buchhaltung/Lohn, Admin oder VKL
- **Verknüpfung über VIN** zum Fahrzeug → Gesamtprovision pro Fahrzeug sichtbar
- **Betrag:** Gesamtbetrag wird eingegeben (was Bank/Versicherer zahlt)
- **Anteil:** Prozentsatz des Verkäufer-Anteils wird per Config-Regel hinterlegt
- **Berechnung durch DRIVE:** `betrag_gesamt × anteil_prozent = provision_verkäufer`

**Untertypen mit Default-Anteilssätzen:**

| Typ | Beispiel | Default-Anteil VK |
|-----|----------|-------------------|
| `finanzierung` | Bankprovision für Finanzierungsvermittlung | 30% |
| `versicherung` | KFZ-Versicherungsprovision | 25% |
| `garantie` | Garantieverlängerung | 100% |
| `leasing` | Leasingprovision | 30% |
| `sonstiges` | Zubehör-Bonus etc. | frei definierbar |

**Berechtigungen Kategorie V:**
- **Eingabe/Bearbeitung:** Nur Rollen `admin`, `finance` (Buchhaltung/Lohn), `sales_manager` (VKL)
- **Lesen:** Verkäufer sieht seine eigenen Einträge (Betrag + seinen Anteil)
- **Verkäufer kann NICHT selbst Einträge anlegen oder ändern**

---

## 4. IDENTIFIKATION & ZUORDNUNGSLOGIK

### 4.1 Verkäufer-Mapping

In Locosoft hat jeder Verkäufer einen VKB-Code (z.B. 2002). Mapping in DRIVE:

```
Locosoft VKB-Code → DRIVE Verkäufer-ID → Name
2002 → kraus_rafael → Kraus, Rafael
2003 → schmid_roland → Schmid, Roland
```

### 4.2 Fahrzeugart-Zuordnung

Aus Locosoft-Export kommt ein Buchstabe der Fahrzeugart:

| Code | Bedeutung | Provisions-Kategorie |
|------|-----------|---------------------|
| N | Neuwagen | I |
| D | Direktverkauf (Neuwagen) | I |
| T | Testwagen | II |
| V | Vorführwagen | II (evtl. eigener Max-Wert) |
| G | Gebrauchtwagen | III oder IV |

### 4.3 Abgrenzung GW (III) vs. GW aus Bestand (IV)

**OFFENER PUNKT – muss mit Anton/Florian geklärt werden:**
- Welches Feld in Locosoft kennzeichnet "GW aus Bestand"?
- Mögliche Kriterien: Fahrzeug war im eigenen Bestand (Zulassung auf Autohaus), Inzahlungnahme, Ankauf vs. Kundenfahrzeug

### 4.4 Rechnungstyp-Filter

- Nur **H** (Hauptrechnung) wird berücksichtigt
- **Z** (Zusatzrechnung/Storno) wird ausgeschlossen oder gesondert verrechnet
- **OFFENER PUNKT:** Storno-Handling – wird automatisch in Folgemonat korrigiert?

### 4.5 VIN als Schlüssel

Die Fahrgestellnummer (VIN) dient als universeller Schlüssel:
- Verknüpft Verkaufsprovision (Kat. I-IV) mit Zusatzleistungen (Kat. V)
- Ermöglicht Gesamtansicht: "Was hat der Verkäufer an diesem Fahrzeug insgesamt verdient?"
- Verhindert Doppelberechnung

---

## 5. DATENBANK-SCHEMA (SQLite)

### 5.1 Tabelle: `provision_config`

Konfigurierbare Provisionssätze mit Gültigkeitszeiträumen.

```sql
CREATE TABLE provision_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kategorie TEXT NOT NULL,           -- 'I_neuwagen', 'II_testwagen', 'III_gebrauchtwagen', 'IV_gw_bestand', 'V_finanzierung', 'V_versicherung', 'V_garantie', 'V_leasing', 'V_sonstiges'
    bezeichnung TEXT NOT NULL,          -- Anzeigename
    bemessungsgrundlage TEXT NOT NULL,  -- 'db' oder 'rg_netto' oder 'manuell'
    prozentsatz REAL NOT NULL,          -- z.B. 0.12 für 12%, oder Anteilssatz bei Kat. V
    min_betrag REAL,                    -- Mindestprovision pro Position (NULL = keine)
    max_betrag REAL,                    -- Maximalprovision pro Position (NULL = keine)
    stueck_praemie REAL,               -- Fix-Betrag pro Stück (nur Kat. I), NULL sonst
    stueck_max INTEGER,                 -- Max Stückzahl für Prämie (nur Kat. I), NULL sonst
    param_j60 REAL,                     -- Kostenabzug-Prozentsatz (nur Kat. IV), NULL sonst
    param_j61 REAL,                     -- Kostenabzug-Fixbetrag (nur Kat. IV), NULL sonst
    gueltig_ab DATE NOT NULL,           -- Gültigkeitsbeginn
    gueltig_bis DATE,                   -- Gültigkeitsende (NULL = unbefristet)
    erstellt_von TEXT NOT NULL,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kategorie, gueltig_ab)
);
```

**Default-Daten:**

```sql
INSERT INTO provision_config (kategorie, bezeichnung, bemessungsgrundlage, prozentsatz, min_betrag, max_betrag, stueck_praemie, stueck_max, param_j60, param_j61, gueltig_ab, erstellt_von) VALUES
('I_neuwagen', 'Neuwagen', 'db', 0.12, NULL, NULL, 50.0, 15, NULL, NULL, '2024-01-01', 'system'),
('II_testwagen', 'Testwagen/VFW', 'rg_netto', 0.01, 103.0, 500.0, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('III_gebrauchtwagen', 'Gebrauchtwagen', 'rg_netto', 0.01, 103.0, 500.0, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('IV_gw_bestand', 'GW aus Bestand', 'db', 0.12, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_finanzierung', 'Finanzierungsprovision', 'manuell', 30.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_versicherung', 'Versicherungsprovision', 'manuell', 25.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_garantie', 'Garantieverlängerung', 'manuell', 100.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_leasing', 'Leasingprovision', 'manuell', 30.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system'),
('V_sonstiges', 'Sonstiges', 'manuell', 100.0, NULL, NULL, NULL, NULL, NULL, NULL, '2024-01-01', 'system');
```

### 5.2 Tabelle: `provision_laeufe`

Ein Lauf = Provisionsabrechnung eines Verkäufers für einen Monat.

```sql
CREATE TABLE provision_laeufe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verkaufer_id TEXT NOT NULL,         -- Verkäufer-Kennung (z.B. VKB-Code oder DRIVE-User)
    verkaufer_name TEXT NOT NULL,       -- Anzeigename
    abrechnungsmonat TEXT NOT NULL,     -- Format: 'YYYY-MM'
    status TEXT NOT NULL DEFAULT 'ENTWURF',  -- ENTWURF, VORLAUF, PRUEFUNG, ENDLAUF, LOHNBUCHHALTUNG
    -- Beträge (werden bei Vorlauf/Endlauf berechnet und gespeichert)
    summe_kat_i REAL DEFAULT 0,
    summe_kat_ii REAL DEFAULT 0,
    summe_kat_iii REAL DEFAULT 0,
    summe_kat_iv REAL DEFAULT 0,
    summe_kat_v REAL DEFAULT 0,
    summe_stueckpraemie REAL DEFAULT 0,
    summe_gesamt REAL DEFAULT 0,
    -- Timestamps
    vorlauf_am DATETIME,
    vorlauf_von TEXT,                   -- Wer hat Vorlauf erstellt
    pruefung_am DATETIME,              -- Wann hat Verkäufer geprüft
    endlauf_am DATETIME,
    endlauf_von TEXT,                   -- Wer hat Endlauf freigegeben
    lohnbuchhaltung_am DATETIME,
    -- PDF-Pfade
    pdf_vorlauf TEXT,
    pdf_endlauf TEXT,
    -- Audit
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    bemerkung TEXT,
    UNIQUE(verkaufer_id, abrechnungsmonat)
);
```

### 5.3 Tabelle: `provision_positionen`

Einzelne Provisionspositionen eines Laufs – ein Eintrag pro Fahrzeug.

```sql
CREATE TABLE provision_positionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lauf_id INTEGER NOT NULL REFERENCES provision_laeufe(id),
    kategorie TEXT NOT NULL,            -- 'I_neuwagen', 'II_testwagen', etc.
    -- Fahrzeugdaten (Snapshot zum Zeitpunkt der Berechnung)
    vin TEXT,                           -- Fahrgestellnummer
    marke TEXT,
    modell TEXT,
    fahrzeugart TEXT,                   -- N, D, T, V, G
    kaeufer_name TEXT,
    -- Betragsfelder
    rg_netto REAL,                      -- Rechnungsbetrag Netto
    deckungsbeitrag REAL,               -- DB aus Locosoft
    bemessungsgrundlage REAL NOT NULL,  -- Der tatsächlich verwendete Wert (DB oder Rg.Netto oder bereinigter DB)
    kosten_abzug REAL,                  -- Nur Kat. IV: (DB × J60) + J61
    provisionssatz REAL NOT NULL,       -- Angewendeter Satz (z.B. 0.12)
    provision_berechnet REAL NOT NULL,  -- Berechneter Betrag
    provision_final REAL NOT NULL,      -- Nach Min/Max-Clamping
    -- Referenzen
    locosoft_rg_nr TEXT,                -- Rechnungsnummer aus Locosoft
    rg_datum DATE,                      -- Rechnungsdatum
    auslieferung_datum DATE,            -- Auslieferungsdatum
    -- Einspruch
    einspruch_flag BOOLEAN DEFAULT 0,
    einspruch_text TEXT,
    einspruch_am DATETIME,
    einspruch_bearbeitet BOOLEAN DEFAULT 0,
    einspruch_antwort TEXT,
    einspruch_bearbeitet_von TEXT,
    einspruch_bearbeitet_am DATETIME,
    -- Audit
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lauf_id) REFERENCES provision_laeufe(id)
);
```

### 5.4 Tabelle: `provision_zusatzleistungen`

Manuell erfasste Zusatzprovisionen (Kategorie V), verknüpft über VIN.

```sql
CREATE TABLE provision_zusatzleistungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL,                  -- Fahrgestellnummer → Verknüpfung zum Fahrzeug
    verkaufer_id TEXT NOT NULL,
    typ TEXT NOT NULL,                  -- 'finanzierung', 'versicherung', 'garantie', 'leasing', 'sonstiges'
    bezeichnung TEXT,                   -- Freitext-Beschreibung (z.B. "Santander Finanzierung")
    betrag_gesamt REAL NOT NULL,        -- Gesamtbetrag (was Bank/Versicherer ans Autohaus zahlt)
    anteil_prozent REAL NOT NULL,       -- Verkäufer-Anteil in % (aus provision_config oder manuell überschrieben)
    provision_verkaufer REAL NOT NULL,  -- Berechneter VK-Anteil (betrag_gesamt × anteil_prozent / 100)
    beleg_datum DATE,                   -- Datum des Papierbelegs
    beleg_referenz TEXT,                -- Belegnummer / Referenz
    abrechnungsmonat TEXT NOT NULL,     -- Format: 'YYYY-MM' – in welchem Monat wird das abgerechnet
    lauf_id INTEGER,                    -- Zuordnung zum Provisionslauf (wird bei Vorlauf gesetzt)
    -- Berechtigungen / Audit
    erfasst_von TEXT NOT NULL,          -- User-ID (muss Rolle admin, finance oder sales_manager haben)
    erfasst_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    geaendert_von TEXT,
    geaendert_am DATETIME,
    FOREIGN KEY (lauf_id) REFERENCES provision_laeufe(id)
);
```

### 5.5 Tabelle: `provision_audit_log`

Vollständige Nachvollziehbarkeit aller Änderungen.

```sql
CREATE TABLE provision_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aktion TEXT NOT NULL,               -- 'vorlauf_erstellt', 'einspruch', 'endlauf_freigegeben', 'zusatzleistung_erfasst', 'config_geaendert', etc.
    lauf_id INTEGER,
    position_id INTEGER,
    zusatzleistung_id INTEGER,
    benutzer TEXT NOT NULL,
    details TEXT,                        -- JSON mit Vorher/Nachher-Werten
    zeitstempel DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. API-ENDPOINTS

Alle Endpoints unter `/api/provision/...`. Auth via `@require_auth`.

### 6.1 Live-Preview & Dashboard

```
GET /api/provision/live-preview
    Query: verkaufer_id, monat (YYYY-MM)
    Auth: Verkäufer (eigene), VKL/Admin (alle)
    Response: Berechnete Provision für aktuellen Monat, OHNE DB-Speicherung
    → Zeigt Kat. I-IV automatisch berechnet + Kat. V bereits erfasste Zusatzleistungen

GET /api/provision/dashboard
    Auth: VKL / Admin
    Response: Übersicht aller Verkäufer mit aktuellem Monats-Status,
              offene Einsprüche, Gesamtsummen
```

### 6.2 Vorlauf / Endlauf Workflow

```
POST /api/provision/vorlauf-erstellen
    Body: { verkaufer_id, monat }
    Auth: VKL / Admin
    → Erstellt provision_laeufe + provision_positionen, generiert PDF
    → Setzt Status VORLAUF
    → Verknüpft offene Zusatzleistungen (Kat. V) des Monats mit dem Lauf

GET /api/provision/vorlauf/{lauf_id}
    Auth: VKL / Admin / betroffener Verkäufer
    Response: Komplette Vorlauf-Daten inkl. aller Positionen + Zusatzleistungen

POST /api/provision/einspruch/{position_id}
    Body: { text }
    Auth: Betroffener Verkäufer
    → Setzt einspruch_flag, speichert Text

POST /api/provision/einspruch-bearbeiten/{position_id}
    Body: { antwort, aktion: 'akzeptiert'|'abgelehnt', korrektur_betrag? }
    Auth: VKL / Admin

POST /api/provision/endlauf-freigeben/{lauf_id}
    Auth: VKL / Admin
    Bedingung: Alle Einsprüche müssen bearbeitet sein
    → Setzt Status ENDLAUF, generiert finales PDF, sperrt Daten
```

### 6.3 Zusatzleistungen (Kategorie V)

```
GET /api/provision/zusatzleistungen
    Query: verkaufer_id?, monat?, vin?
    Auth: Verkäufer (eigene), Buchhaltung/VKL/Admin (alle)

POST /api/provision/zusatzleistung
    Body: { vin, verkaufer_id, typ, bezeichnung?, betrag_gesamt, beleg_datum?, beleg_referenz?, abrechnungsmonat }
    Auth: NUR admin, finance, sales_manager
    → Berechnet provision_verkaufer aus betrag_gesamt × anteil_prozent (aus provision_config)

PUT /api/provision/zusatzleistung/{id}
    Auth: NUR admin, finance, sales_manager
    Bedingung: Zugehöriger Lauf darf NICHT Status ENDLAUF/LOHNBUCHHALTUNG haben

DELETE /api/provision/zusatzleistung/{id}
    Auth: NUR admin
    Bedingung: Zugehöriger Lauf darf NICHT Status ENDLAUF/LOHNBUCHHALTUNG haben
```

### 6.4 Exports & Übersichten

```
GET /api/provision/jahresuebersicht
    Query: verkaufer_id, jahr
    Auth: Verkäufer (eigene), VKL/Admin (alle)
    Response: Monat-für-Monat: was wurde abgerechnet, was ist offen,
              kumulierte Jahressumme

GET /api/provision/lohnbuchhaltung
    Query: monat
    Auth: finance, admin
    Response: Sammel-PDF + CSV aller Verkäufer des Monats
              (nur abgeschlossene Endläufe)

GET /api/provision/fahrzeug-gesamt/{vin}
    Auth: VKL / Admin
    Response: Gesamtprovision für ein Fahrzeug:
              Verkaufsprovision (Kat. I-IV) + alle Zusatzleistungen (Kat. V)

GET /api/provision/config
    Auth: Admin
    Response: Aktuelle Provisionskonfiguration

PUT /api/provision/config/{id}
    Auth: Admin
    → Ändert Config (erstellt neuen Eintrag mit neuem gueltig_ab, alter wird gueltig_bis gesetzt)
```

---

## 7. FRONTEND-VIEWS

### 7.1 Provisions-Dashboard (VKL / Admin)

**Route:** `/provision/dashboard`
**Template:** `provision_dashboard.html`

Inhalte:
- **KPI-Cards oben:** Gesamt-Provision Monat, Anzahl Fahrzeuge, abgeschlossene Läufe, offene Einsprüche
- **Tabelle:** Alle Verkäufer mit Spalten: Name, Anzahl FZ, Provision Kat. I-IV, Zusatzleistungen (V), Gesamt, Status, Aktionen
- **Aktionen pro Zeile:** "Vorlauf erstellen", "Details", "Endlauf freigeben" (je nach Status)
- **Filter:** Monat (Dropdown), Status (Dropdown)

### 7.2 Meine Provision (Verkäufer-Ansicht)

**Route:** `/provision/meine`
**Template:** `provision_meine.html`

Inhalte:
- **Live-Preview** des aktuellen Monats (Echtzeit-Berechnung)
- **Tabellen** getrennt nach Kategorie I-V mit allen Einzelpositionen
- **Pro Position:** Marke, Modell, Käufer, Berechnungsbasis, Provision, Einspruch-Button
- **Monats-Summary** unten: Summe pro Kategorie + Gesamt
- **Tab/Accordion:** Historie vergangener Monate mit Status
- **Jahresübersicht:** Kumulierte Summen, "was wurde bereits ausgezahlt"

### 7.3 Provision Detail (VKL)

**Route:** `/provision/detail/<lauf_id>`
**Template:** `provision_detail.html`

Inhalte:
- Komplette Abrechnung eines Verkäufers für einen Monat
- Alle Positionen Kat. I-V
- Einsprüche bearbeiten (inline)
- PDF-Download (Vorlauf / Endlauf)
- Status-Workflow-Buttons

### 7.4 Zusatzleistungen erfassen (Buchhaltung/VKL)

**Route:** `/provision/zusatzleistungen`
**Template:** `provision_zusatzleistungen.html`

Inhalte:
- **Erfassungsformular:** VIN (Autocomplete aus Locosoft), Verkäufer (Dropdown), Typ (Dropdown), Betrag, Beleg-Datum, Beleg-Referenz, Monat
- **Tabelle:** Alle erfassten Zusatzleistungen mit Filter (Monat, Verkäufer, Typ)
- **VIN-Lookup:** Bei Eingabe der VIN automatisch Fahrzeug-Info anzeigen (Marke, Modell, Käufer)
- **Berechnung live:** Bei Eingabe des Betrags sofort den VK-Anteil anzeigen (basierend auf Config)

### 7.5 Provisions-Konfiguration (Admin)

**Route:** `/provision/config`
**Template:** `provision_config.html`

Inhalte:
- Tabelle aller aktiven Provisions-Regeln
- Bearbeiten von Sätzen, Min/Max, Anteilssätzen
- Historie: Wann wurde was geändert

### 7.6 Lohnbuchhaltung-Export

**Route:** `/provision/lohnbuchhaltung`
**Template:** `provision_lohnbuchhaltung.html`

Inhalte:
- Monatsauswahl
- Liste aller abgeschlossenen Endläufe
- Buttons: "Sammel-PDF generieren", "CSV exportieren"
- Status-Anzeige: Welche Verkäufer sind fertig, welche noch offen

---

## 8. PDF-LAYOUT (Vorlauf & Endlauf)

### 8.1 Aufbau der Provisionsabrechnung

```
┌─────────────────────────────────────────────────────────┐
│ AUTOHAUS GREINER – Provisionsabrechnung                 │
│                                                          │
│ Verkäufer: Kraus, Rafael          Monat: Januar 2026    │
│ Status: VORLAUF / ENDLAUF         Datum: 18.02.2026    │
│ Erstellt von: Anton Süß                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ I. NEUWAGEN (12% auf DB + 50€/Stück)                   │
│ ─────────────────────────────────────────────────────── │
│ Datum  | Marke | Modell    | Käufer      | DB      |Prov│
│ 05.01. | Opel  | Corsa     | Müller, H.  | 1.850€  |222€│
│ 12.01. | Opel  | Mokka     | Schmidt, P. | 2.100€  |252€│
│                              Stückprämie: 2×50€ = 100€  │
│                              Summe Kat. I:        574€  │
│                                                          │
│ II. TESTWAGEN / VFW (1% auf Rg.Netto, min 103€)        │
│ ─────────────────────────────────────────────────────── │
│ Datum  | Marke | Modell    | Käufer      |Rg.Netto |Prov│
│ 18.01. | Opel  | Astra VFW | Weber, K.   |22.500€  |225€│
│                              Summe Kat. II:        225€  │
│                                                          │
│ III. GEBRAUCHTWAGEN (1% auf Rg.Netto, min 103€)        │
│ ─────────────────────────────────────────────────────── │
│ (keine Positionen)           Summe Kat. III:        0€  │
│                                                          │
│ IV. GW AUS BESTAND (12% auf DB - Kosten)                │
│ ─────────────────────────────────────────────────────── │
│ (keine Positionen)           Summe Kat. IV:         0€  │
│                                                          │
│ V. ZUSATZLEISTUNGEN                                      │
│ ─────────────────────────────────────────────────────── │
│ Datum  | VIN / Fahrzeug      | Typ          |Gesamt|VK  │
│ 20.01. | Corsa (Müller)      | Finanzierung |300€ | 90€│
│                              Summe Kat. V:         90€  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ ZUSAMMENFASSUNG MONAT                                    │
│ Kat. I   Neuwagen:           574,00 €                   │
│ Kat. II  Testwagen/VFW:      225,00 €                   │
│ Kat. III Gebrauchtwagen:       0,00 €                   │
│ Kat. IV  GW Bestand:           0,00 €                   │
│ Kat. V   Zusatzleistungen:    90,00 €                   │
│ ─────────────────────────────────────────────────────── │
│ GESAMT PROVISION MONAT:      889,00 €                   │
├─────────────────────────────────────────────────────────┤
│ JAHRESÜBERSICHT 2026                                     │
│ Bereits abgerechnet (Sep-Dez 2025):   3.245,00 €       │
│ Dieser Monat (Jan 2026):                889,00 €       │
│ Kumuliert Geschäftsjahr:              4.134,00 €       │
├─────────────────────────────────────────────────────────┤
│ Unterschrift VKL: ____________  Datum: ______________   │
│ Unterschrift VK:  ____________  Datum: ______________   │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Sammel-PDF Lohnbuchhaltung

Einfache Übersicht pro Monat:

| Verkäufer | Kat. I | Kat. II | Kat. III | Kat. IV | Kat. V | Gesamt |
|-----------|--------|---------|----------|---------|--------|--------|
| Kraus, R. | 574€   | 225€    | 0€       | 0€      | 90€    | 889€   |
| Schmid, R.| 312€   | 103€    | 206€     | 0€      | 45€    | 666€   |
| **Summe** | 886€   | 328€    | 206€     | 0€      | 135€   | 1.555€ |

---

## 9. PROJEKTSTRUKTUR IN DRIVE

```
/opt/greiner-portal/
├── api/
│   └── provision_api.py              ← REST-API (alle Endpoints)
├── routes/
│   └── provision_routes.py           ← Flask-Routes (HTML-Views)
├── services/
│   └── provision_service.py          ← Geschäftslogik (Berechnung, PDF, Workflow)
├── templates/
│   ├── provision_dashboard.html      ← VKL Dashboard
│   ├── provision_meine.html          ← Verkäufer-Ansicht
│   ├── provision_detail.html         ← Einzelabrechnung
│   ├── provision_zusatzleistungen.html ← Kat. V Erfassung
│   ├── provision_config.html         ← Admin-Config
│   └── provision_lohnbuchhaltung.html ← Export
├── static/
│   ├── css/provision.css
│   └── js/provision.js
└── migrations/
    └── provision_schema.sql          ← DDL für alle Tabellen
```

---

## 10. IMPLEMENTIERUNGSPLAN

### Phase 1: Fundament (Berechnung + Live-Preview)
1. DB-Schema anlegen (alle Tabellen)
2. `provision_service.py`: Berechnungslogik Kat. I-IV
3. API: `/live-preview` Endpoint
4. Frontend: "Meine Provision" mit Live-Preview
5. Locosoft-Query: Verkaufsdaten für Berechnung abfragen

### Phase 2: Workflow + PDF
1. Vorlauf erstellen (Positionen in DB, PDF generieren)
2. Einspruch-Workflow
3. Endlauf freigeben
4. PDF-Generierung (reportlab oder weasyprint)
5. VKL-Dashboard

### Phase 3: Zusatzleistungen + Lohnbuchhaltung
1. Kat. V: Erfassungsmaske + API
2. VIN-Verknüpfung + Gesamtansicht pro Fahrzeug
3. Lohnbuchhaltung-Export (Sammel-PDF + CSV)
4. Jahresübersicht

### Phase 4: VKL-Provision (Anton Süß)
- Eigenes Provisionsmodell, getrennte Logik
- Eigene Config-Einträge
- Separate Dateien/Module

---

## 11. OFFENE PUNKTE (VOR IMPLEMENTIERUNG KLÄREN)

| # | Thema | Frage | Wer klärt |
|---|-------|-------|-----------|
| 1 | J60/J61 | Genaue Werte für Kostenabzug Kat. IV (GW Bestand) | Anton Süß / Florian |
| 2 | GW vs. GW Bestand | Welches Locosoft-Feld unterscheidet III von IV? | Florian (DB-Analyse) |
| 3 | Max VFW | 205€, 300€ oder 500€? Vorführwagen = eigene Kategorie? | Anton Süß |
| 4 | Rg-Typ Filter | Nur "H"? Wie werden Stornos/Korrekturen behandelt? | Anton Süß |
| 5 | Anteilssätze Kat. V | Default-% für Finanzierung, Versicherung etc. bestätigen | GF / Anton |
| 6 | Geschäftsjahr | Sep-Aug – Jahresübersicht folgt GJ, nicht Kalenderjahr? | Florian |
| 7 | Nicht importieren | Schwellwert "n_nichtimportieren" – welche Beträge ausschließen? | Anton Süß |
| 8 | VKB-Mapping | Aktuelle Liste VKB-Code → Verkäufer für DRIVE | Florian (Locosoft) |

---

## 12. ENTSCHEIDUNGEN & AUSSCHLÜSSE

### Bewusst NICHT implementiert:

| Feature | Begründung |
|---------|-----------|
| **Standtage-Provision** | Erzeugt Gaming-Anreize (Verkäufer verzögert Vertrag bis Schwelle). Standtage-Steuerung ist VKL-Führungsthema, kein Provisionshebel. |
| **Staffelprovision** | Aktuell nicht benötigt, kann aber über `provision_config` mit mehreren Einträgen pro Kategorie + Schwellwerten nachgerüstet werden |
| **Multi-Splitting** | Aktuell nicht benötigt (kein Team-Verkauf). DB-Schema unterstützt Erweiterung. |

### Bewusst SO entschieden:

| Entscheidung | Begründung |
|-------------|-----------|
| **Kat. V: Gesamtbetrag erfassen, Anteil per Config** | Flexibel – wenn sich Split ändert, nur Config anpassen, Belege bleiben sauber |
| **Kat. V: Nur Buchhaltung/VKL/Admin dürfen erfassen** | Verkäufer sieht Beträge, kann aber nichts eintragen – keine Diskussionen |
| **VIN als universeller Schlüssel** | Verknüpft Verkaufs- und Zusatzprovision → Gesamtansicht pro Fahrzeug |
| **Live-Preview ohne DB-Speicherung** | Motivation durch Echtzeit-Transparenz, kein Overhead |

---

*Dokument erstellt: 2026-02-18 | Für Cursor/Claude als Implementierungsgrundlage*
