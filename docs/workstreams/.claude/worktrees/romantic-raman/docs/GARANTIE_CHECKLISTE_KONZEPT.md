# 📋 GARANTIE-CHECKLISTEN-KONZEPT

**Stand:** 2025-12-04  
**Basis:** Hyundai Garantie-Richtlinie + Locosoft Mein-Autohaus App Analyse

---

## 🎯 ZIEL

Eine **digitale Checkliste** im Greiner Portal für Garantieaufträge, die:
1. Den Serviceberater durch den Prozess führt
2. Vollständigkeit der Dokumentation sicherstellt
3. Fristen überwacht (21 Tage Einreichung)
4. Daten für GWMS vorbereitet (Copy-Paste)

---

## 📱 VORBILD: Locosoft "Mein-Autohaus" Checklisten

Die Locosoft App hat bereits ein Checklisten-Modul mit:

| Feature | Beschreibung |
|---------|--------------|
| **Kategorien** | Allgemein, Annahmecheckliste, Arbeitsdurchführung, Schlussabnahme, Verkauf |
| **Elemente** | Checkboxen (OK/Nicht OK/Unklar), Drop-Downs, Freitext, Pflichtfelder |
| **Fahrzeugskizze** | Für Schadensmarkierung |
| **Bremswerte** | Spezielle Erfassung |
| **Unterschriften** | Kunde + Mitarbeiter |
| **PDF-Export** | In Auftrag integriert |
| **Import** | Vorgefertigte Checklisten vom Hersteller |

**Schwächen der Locosoft-App (laut Bewertungen):**
- ❌ Keine Bilder in Checklisten
- ❌ Signaturfunktion nicht kundenfreundlich
- ❌ Mobile-only (kein Desktop)

---

## 🔧 UNSER ANSATZ: Garantie-Checkliste im Portal

### Phase 1: Grundstruktur

**Datenbankmodell:**
```sql
-- Checklisten-Vorlagen
CREATE TABLE checklist_templates (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),           -- "Hyundai Garantie-Antrag"
    category VARCHAR(50),        -- "garantie", "inspektion", "annahme"
    brand VARCHAR(50),           -- "Hyundai", "Opel", NULL=alle
    version VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Checklisten-Elemente (Template)
CREATE TABLE checklist_template_items (
    id INTEGER PRIMARY KEY,
    template_id INTEGER REFERENCES checklist_templates(id),
    section VARCHAR(100),        -- "Kundenangabe", "Diagnose", "Reparatur"
    sort_order INTEGER,
    item_type VARCHAR(20),       -- "checkbox", "text", "dropdown", "date", "photo", "signature"
    label TEXT,                  -- "O-Ton Kundenangabe erfasst?"
    is_required BOOLEAN,
    options TEXT,                -- JSON für dropdown-Optionen
    help_text TEXT,              -- Hinweis aus Garantie-Richtlinie
    gwms_field VARCHAR(50)       -- Mapping zu GWMS-Feld
);

-- Ausgefüllte Checklisten
CREATE TABLE checklist_instances (
    id INTEGER PRIMARY KEY,
    template_id INTEGER REFERENCES checklist_templates(id),
    order_id INTEGER,            -- Locosoft Auftragsnummer
    vin VARCHAR(17),
    license_plate VARCHAR(20),
    created_by INTEGER,          -- employee_id
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20),          -- "in_progress", "completed", "submitted"
    gwms_claim_number VARCHAR(50),
    submission_deadline DATE     -- 21 Tage ab Reparaturdatum
);

-- Ausgefüllte Felder
CREATE TABLE checklist_instance_items (
    id INTEGER PRIMARY KEY,
    instance_id INTEGER REFERENCES checklist_instances(id),
    template_item_id INTEGER REFERENCES checklist_template_items(id),
    value TEXT,                  -- Eingetragener Wert
    updated_at TIMESTAMP,
    updated_by INTEGER
);

-- Foto-Anhänge
CREATE TABLE checklist_photos (
    id INTEGER PRIMARY KEY,
    instance_id INTEGER REFERENCES checklist_instances(id),
    template_item_id INTEGER,    -- Optional: zu welchem Feld
    filename VARCHAR(255),
    filepath VARCHAR(500),
    description TEXT,
    uploaded_at TIMESTAMP,
    uploaded_by INTEGER
);
```

---

### Phase 2: Hyundai Garantie-Checkliste (Vorlage)

**Sektionen basierend auf Garantie-Richtlinie:**

#### Sektion 1: Fahrzeug & Kunde
| Feld | Typ | Pflicht | GWMS-Mapping |
|------|-----|---------|--------------|
| VIN | text (auto) | ✅ | VIN_NO |
| Kennzeichen | text (auto) | ✅ | - |
| Modell | text (auto) | ✅ | MDL_CD |
| Erstzulassung | date (auto) | ✅ | WARR_START_DT |
| km-Stand | number | ✅ | MILEAGE |
| Kunde | text (auto) | ✅ | - |

#### Sektion 2: Kundenangabe (O-Ton)
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| O-Ton Beanstandung | textarea | ✅ | "Wörtliche Kundenangabe erfassen!" |
| Symptom seit wann? | text | ⬜ | |
| Symptom wie oft? | dropdown | ⬜ | "Immer / Manchmal / Selten" |
| Kunde informiert über Diagnosezeit? | checkbox | ✅ | |

#### Sektion 3: Diagnose
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| Diagnose durchgeführt | checkbox | ✅ | |
| Diagnose-Ergebnis | textarea | ✅ | "Befund dokumentieren" |
| Fehlercode(s) | text | ⬜ | DTC-Codes |
| Diagnose-Zeit (AW) | number | ✅ | "Standard: 15 AW" |
| Fotos Diagnose | photo | ⬜ | |

#### Sektion 4: PWA-Prüfung
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| PWA erforderlich? | dropdown | ✅ | "Ja / Nein" |
| PWA-Typ | dropdown | ⬜ | "2=TT>0.9h, 3=Lack, 4=Spät, 5=Rost, B=>1000€, ..." |
| PWA-Nummer | text | ⬜ | |
| PWA-Datum | date | ⬜ | "Gültigkeit: 6 Wochen!" |

#### Sektion 5: Reparatur
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| Reparatur durchgeführt | checkbox | ✅ | |
| Reparaturbeschreibung | textarea | ✅ | |
| Getauschte Teile | textarea | ✅ | "Teilenummern!" |
| Reparatur-Zeit (AW) | number | ✅ | |
| Reparaturdatum | date | ✅ | "Startet 21-Tage-Frist!" |
| Fotos nach Reparatur | photo | ⬜ | |

#### Sektion 6: Teile-Dokumentation
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| Altteile aufbewahrt? | checkbox | ✅ | "3 Monate Aufbewahrungspflicht!" |
| Altteile-Lagerort | text | ⬜ | |
| Fotos Altteile | photo | ⬜ | |

#### Sektion 7: Endkontrolle
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| Endkontrolle durchgeführt | checkbox | ✅ | |
| Probefahrt | checkbox | ⬜ | |
| Beanstandung behoben | checkbox | ✅ | |
| Techniker-Unterschrift | signature | ✅ | |

#### Sektion 8: GWMS-Vorbereitung
| Feld | Typ | Pflicht | Hinweis |
|------|-----|---------|---------|
| Antragstyp | dropdown | ✅ | "W=NW-Garantie, S=ET-Garantie, A=Rost, ..." |
| Schadensart | dropdown | ✅ | Aus Garantie-Richtlinie |
| Einreichungsfrist | date (calc) | auto | "Reparaturdatum + 21 Tage" |
| Vollständigkeit OK | checkbox | auto | Alle Pflichtfelder ausgefüllt |

---

### Phase 3: UI-Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  🔧 GARANTIE-CHECKLISTE                                    │
│  Auftrag: 12345 | VIN: KMHKR81CPNU005366 | IONIQ 5        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏱️ EINREICHUNGSFRIST: 15 Tage verbleibend                │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  71%        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  📋 FORTSCHRITT                                            │
│                                                             │
│  [✅] 1. Fahrzeug & Kunde                                  │
│  [✅] 2. Kundenangabe                                      │
│  [🔄] 3. Diagnose              ← AKTUELL                   │
│  [ ] 4. PWA-Prüfung                                        │
│  [ ] 5. Reparatur                                          │
│  [ ] 6. Teile-Dokumentation                                │
│  [ ] 7. Endkontrolle                                       │
│  [ ] 8. GWMS-Vorbereitung                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  SEKTION 3: DIAGNOSE                                       │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [✅] Diagnose durchgeführt                                │
│                                                             │
│  Diagnose-Ergebnis: *                                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Fehlerspeicher ausgelesen. DTC P1234 aktiv.         │  │
│  │ Sensor XY defekt, Austausch erforderlich.           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Fehlercode(s):                                            │
│  [ P1234, P5678                                      ]     │
│                                                             │
│  Diagnose-Zeit (AW): *                                     │
│  [ 15    ] AW    ℹ️ "Standard: 15 AW"                     │
│                                                             │
│  📷 Fotos Diagnose:                                        │
│  [+] Foto hinzufügen    [📷] [📷] [📷]                    │
│                                                             │
│                      [← Zurück]  [Weiter →]                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 IMPLEMENTIERUNGS-ROADMAP

### Sprint 1: Basis (1-2 Wochen)
- [ ] Datenbank-Schema erstellen
- [ ] API-Endpoints für Checklisten
- [ ] Hyundai Garantie-Vorlage anlegen
- [ ] Einfache UI (nur Formular)

### Sprint 2: Locosoft-Integration (1 Woche)
- [ ] Auftragsdaten aus Locosoft laden
- [ ] VIN/Fahrzeug automatisch befüllen
- [ ] km-Stand aus Auftrag

### Sprint 3: Features (1-2 Wochen)
- [ ] Foto-Upload
- [ ] Frist-Berechnung & Warnungen
- [ ] Vollständigkeits-Check
- [ ] PDF-Export

### Sprint 4: GWMS-Vorbereitung (optional)
- [ ] Daten für GWMS formatieren
- [ ] Copy-Button für Felder
- [ ] Antrags-Übersicht

---

## ❓ OFFENE FRAGEN

1. **Locosoft-Integration:**
   - Können wir Checklisten-Daten zurück nach Locosoft schreiben?
   - Oder nur lesen?

2. **Foto-Speicherung:**
   - Wo werden Fotos gespeichert? (Server? NAS?)
   - Max. Dateigröße?

3. **Benutzer:**
   - Wer füllt aus? (SB? Techniker? Beide?)
   - Brauchen wir Rollen/Berechtigungen?

4. **Workflow:**
   - Soll Checkliste bei Auftragsanlage automatisch starten?
   - Oder manuell?

---

## 💡 VORTEILE GEGENÜBER LOCOSOFT-APP

| Feature | Locosoft App | Greiner Portal |
|---------|--------------|----------------|
| Fotos in Checkliste | ❌ | ✅ |
| Desktop-optimiert | ❌ | ✅ |
| Garantie-spezifisch | ❌ | ✅ |
| GWMS-Vorbereitung | ❌ | ✅ |
| Fristen-Überwachung | ❌ | ✅ |
| Herstellerspezifisch | ❌ | ✅ (Hyundai-Regeln) |

---

*Konzept erstellt: 2025-12-04*
