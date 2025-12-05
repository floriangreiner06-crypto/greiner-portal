# 🔧 MACHBARKEITSANALYSE: Werkstattplanung im Greiner Portal

**Erstellt:** 2025-12-02  
**Basierend auf:** DA-Exploration + Locosoft-Analyse  
**Status:** Phase 0 - Discovery

---

## 📊 1. IST-ANALYSE: "Das Digitale Autohaus" (DA)

### Entdeckte Module in DA:

| Modul | Sub-Funktionen | Komplexität |
|-------|----------------|-------------|
| **AW Übersicht** | 16 Abteilungen/Partner mit Live-Zahlen | 🟡 Mittel |
| **Serviceplanung** | Serviceplanung, Gutachter-Kalender, Fahrdienst, Räderwechseltage | 🟡 Mittel |
| **Werkstattplanung** | Annahmetermine, Disposition Mechanik, Endkontrolle | 🔴 Hoch |
| **Fuhrpark** | Ersatzfahrzeuge, Vorführwagen | 🟢 Einfach |
| **Räder/Reifen** | Internes Lager | 🟢 Einfach |
| **Kapazitätsplanung** | Abwesenheiten, Schichten, Produktivität | 🟡 Mittel |
| **Verwaltung** | Admin-Funktionen | 🟡 Mittel |

### Entdeckte Abteilungen/Kapazitäten:

```
Interne Werkstatt:
├── Allgemeine Reparatur      (aktuell: -82 = überbucht!)
├── Diagnosetechnik           (aktuell: -29 = überbucht!)
├── Qualitätsmanagement       (aktuell: 184 frei)
├── NW/GW                     (aktuell: 5 frei)
├── TÜV                       (aktuell: 50 frei)
├── DEKRA                     (aktuell: 0)
├── Hauptuntersuchung         (aktuell: 35 frei)
└── Aufbereitung              (aktuell: 211 frei)

Externe Partner:
├── Windschutzscheiben        (53)
├── Smart Repair Delle        (1)
├── Smart Repair Lack         (1)
├── Auer                      (12)
├── Zitzelsberger             (11)
├── Hagengruber               (11)
├── Petermüller               (72)
└── Kupplung vor Ort          (72)
```

---

## 🗄️ 2. DATEN-ANALYSE: Was haben wir bereits?

### Locosoft PostgreSQL (Live-Zugriff vorhanden!):

| Tabelle | Inhalt | Status | Für Werkstattplanung |
|---------|--------|--------|---------------------|
| `orders` | 39.803 Aufträge | 🟢 LIVE | ⭐ Kernddaten! |
| `invoices` | 52.328 Rechnungen | 🟢 LIVE | Abrechnungen |
| `times` | Zeiterfassung | 🟢 LIVE | Mechaniker-Stunden |
| `dealer_vehicles` | 5.212 Fahrzeuge | 🟡 Sync 18:00 | Ersatzwagen? |
| `customers_suppliers` | Kunden | 🟡 Sync 18:00 | Kundendaten |
| `employees` | Mitarbeiter | 🟡 Sync 18:00 | Mechaniker |
| `workshop_orders` | Werkstattaufträge | ❓ Zu prüfen | ⭐ Kernddaten! |

### Greiner Portal SQLite (bereits vorhanden):

| Feature | Status | Nutzbar für Werkstatt |
|---------|--------|----------------------|
| Mitarbeiter (LDAP) | ✅ Produktiv | Mechaniker-Stammdaten |
| Urlaubsplaner | ✅ Produktiv | Abwesenheiten! |
| Rollen-System | ✅ Produktiv | Werkstatt-Rollen |
| Teilebestellungen | ✅ Produktiv | Ersatzteil-Status |

---

## 🎯 3. EMPFEHLUNG: VEREINFACHTE WERKSTATTPLANUNG

### Was eure Mitarbeiter wirklich brauchen (laut "zu komplex"):

```
EINFACH statt KOMPLEX:
┌─────────────────────────────────────────────────────────────┐
│  📅 TAGESANSICHT                                            │
│  ─────────────────────────────────────────────────────────  │
│  Montag, 02.12.2025                    [← Heute →]          │
│                                                              │
│  08:00  🚗 DEG-AB-123  Inspektion     Müller    [Mechanik]  │
│  08:30  🚗 DEG-CD-456  Ölwechsel      Schmidt   [Mechanik]  │
│  09:00  🚗 DEG-EF-789  TÜV            Weber     [TÜV]       │
│  09:30  ─ FREI ─                                            │
│  10:00  🚗 DEG-GH-012  Bremsen        Müller    [Mechanik]  │
│  ...                                                         │
│                                                              │
│  [+ Neuer Termin]  [📋 Übersicht]  [🚗 Ersatzwagen]         │
└─────────────────────────────────────────────────────────────┘
```

### MVP-Scope (Minimum Viable Product):

| Feature | Aufwand | Priorität | Datenquelle |
|---------|---------|-----------|-------------|
| **Tages-Kalender** | 2 Wochen | ⭐⭐⭐ | orders |
| **Mechaniker-Übersicht** | 1 Woche | ⭐⭐⭐ | employees + times |
| **Ersatzwagen-Status** | 1 Woche | ⭐⭐ | dealer_vehicles |
| **Kapazitäts-Anzeige** | 1 Woche | ⭐⭐ | Berechnung |
| **Termin-Anlage** | 3 Wochen | ⭐ | SOAP erforderlich? |

---

## ⚠️ 4. KRITISCHE FRAGEN (noch zu klären)

### A) Daten-Zugriff:

```
❓ Können wir Termine in Locosoft ANLEGEN?
   → PostgreSQL = nur LESEN
   → SOAP-API = SCHREIBEN möglich?
   → Oder: Eigene Termin-Tabelle im Portal?

❓ Was ist in der `workshop_orders` Tabelle?
   → Schema analysieren!
   → Enthält sie Termine oder nur Aufträge?

❓ Wie synchronisiert DA mit Locosoft?
   → SOAP-Endpunkte identifizieren
   → Können wir dieselbe Schnittstelle nutzen?
```

### B) Prozess-Fragen:

```
❓ Wer legt aktuell Termine an?
   → Serviceberater in DA?
   → Direkt in Locosoft?

❓ Was passiert nach Termin-Anlage?
   → Auftrag wird erstellt?
   → Teile werden reserviert?

❓ Ersatzwagen-Prozess?
   → Wie wird aktuell gebucht?
   → Welche Fahrzeuge stehen zur Verfügung?
```

---

## 🚀 5. VORGESCHLAGENER FAHRPLAN

### Phase 1: Discovery (1-2 Wochen)
- [ ] `workshop_orders` Tabelle analysieren
- [ ] `orders` Schema dokumentieren  
- [ ] Locosoft 266 Video auswerten
- [ ] SOAP-Dokumentation von Locosoft anfragen
- [ ] Interview mit Serviceberatern: Was nervt an DA?

### Phase 2: Proof of Concept (2-3 Wochen)
- [ ] Einfache Tagesansicht aus `orders` bauen
- [ ] Mechaniker aus `employees` anzeigen
- [ ] Kapazität berechnen (Stunden verfügbar - gebucht)
- [ ] **ENTSCHEIDUNG:** Eigene Termine oder Locosoft-Sync?

### Phase 3: MVP (4-6 Wochen)
- [ ] Vollständiger Tages-/Wochen-Kalender
- [ ] Ersatzwagen-Modul
- [ ] Einfache Termin-Anlage (falls möglich)
- [ ] User-Test mit 2-3 Mitarbeitern

### Phase 4: Rollout (2 Wochen)
- [ ] Schulung
- [ ] Parallel-Betrieb DA + Portal
- [ ] Feedback einarbeiten

---

## 💰 6. AUFWAND-SCHÄTZUNG

### Optimistisch (nur Lesen aus Locosoft):
```
Kalender-Ansicht:     40h
Mechaniker-Liste:     20h
Ersatzwagen:          30h
Kapazitäts-Anzeige:   20h
─────────────────────────
GESAMT:              110h (~3 Wochen Vollzeit)
```

### Realistisch (mit Termin-Anlage):
```
Basis (wie oben):    110h
SOAP-Integration:     80h
Termin-Workflow:      60h
Tests & Bugfixes:     40h
─────────────────────────
GESAMT:              290h (~7 Wochen Vollzeit)
```

### Pessimistisch (volle DA-Ablösung):
```
Alle DA-Module:      800h+
Timeline:            6-12 Monate
Risiko:              HOCH
```

---

## ✅ 7. NÄCHSTER SCHRITT

**HEUTE:** Locosoft `orders` und `workshop_orders` Tabellen analysieren

```sql
-- Auf Server ausführen:
PGPASSWORD=xxx psql -h 10.80.80.8 -U loco_auswertung_benutzer -d loco_auswertung_db

-- Schema anzeigen:
\d orders
\d workshop_orders

-- Beispiel-Daten:
SELECT * FROM orders LIMIT 5;
SELECT * FROM workshop_orders LIMIT 5;
```

**Dann wissen wir:**
- Welche Daten verfügbar sind
- Ob wir Termine daraus bauen können
- Ob SOAP wirklich nötig ist

---

## 📋 ZUSAMMENFASSUNG

| Aspekt | Bewertung |
|--------|-----------|
| **Machbar?** | ✅ JA - mit Einschränkungen |
| **Aufwand MVP** | 3-7 Wochen |
| **Aufwand Voll** | 6-12 Monate |
| **Risiko** | 🟡 Mittel (SOAP-Abhängigkeit unklar) |
| **Empfehlung** | 🟢 Starten mit Read-Only Kalender |

**Meine Empfehlung:** 
1. Erstmal nur LESEN aus Locosoft (kein SOAP nötig)
2. Einfachen Kalender bauen
3. Feedback sammeln
4. Dann entscheiden ob volle DA-Ablösung sinnvoll

---

*Dokument erstellt von Claude - TAG 88*
