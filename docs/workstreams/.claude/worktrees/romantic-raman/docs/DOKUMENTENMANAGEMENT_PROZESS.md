# Dokumentenmanagement - User-Prozess & Systemintegration

**Erstellt:** 2025-12-19 (TAG 129)
**Status:** Konzept zur Abstimmung

---

## Systeme im Überblick

| System | Server | Zweck | Status |
|--------|--------|-------|--------|
| **ecoDMS** | 10.80.80.3:8180 | Dokumentenarchiv, GoBD | ✅ API getestet |
| **Mein-Autohaus App** | Mobile | Werkstatt-Fotos | ✅ Vorhanden |
| **Locosoft Prog. 211** | 10.80.80.7 | Auftragsbilder | ✅ Vorhanden |
| **DRIVE** | 10.80.80.20 | Portal & Disposition | ✅ Aktiv |

---

## Empfohlener User-Prozess

### Szenario: Werkstattauftrag mit Dokumentation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: AUFTRAGSEINGANG                        │
└─────────────────────────────────────────────────────────────────────────┘

Kunde bringt Fahrzeug → Service-Berater erstellt Termin/Auftrag

    ┌─────────────┐        SOAP API         ┌─────────────┐
    │   DRIVE     │ ───────────────────────→│  Locosoft   │
    │  (Web-UI)   │     writeAppointment    │   DMS       │
    └─────────────┘                         └─────────────┘
          │
          │ Zeigt Auftrag an
          ↓
    ┌─────────────────────────────────────────┐
    │ DRIVE Auftragsansicht:                  │
    │ • Kunde: Müller                         │
    │ • Fahrzeug: DEG-AB-123                  │
    │ • Auftrag: #39650                       │
    │ • [Dokumente anhängen] ← Button         │
    └─────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: WERKSTATT-DOKUMENTATION                     │
└─────────────────────────────────────────────────────────────────────────┘

Mechaniker dokumentiert Schäden/Zustand mit Fotos:

    ┌─────────────────┐
    │ Mein-Autohaus   │    Direkt in Locosoft
    │     App         │ ─────────────────────────→ Programm 211
    │  (Smartphone)   │    Bilder zum Auftrag
    └─────────────────┘

    Funktionen:
    • Foto erstellen → Auftrag zuordnen
    • Video aufnehmen
    • Checklist ausfüllen
    • Kilometerstand erfassen


┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 3: BÜRO-DOKUMENTATION                         │
└─────────────────────────────────────────────────────────────────────────┘

Service-Berater / Büro lädt Dokumente hoch:

    ┌─────────────┐        ecoDMS API        ┌─────────────┐
    │   DRIVE     │ ────────────────────────→│   ecoDMS    │
    │  (Web-UI)   │    Upload + Klassif.     │   Archiv    │
    └─────────────┘                          └─────────────┘

    Dokumenttypen:
    • Kostenvoranschläge
    • Schadensgutachten
    • Kundengenehmigungen
    • Unterschriebene Aufträge
    • Rechnungen (nach Abschluss)

    Klassifizierung in ecoDMS:
    ┌────────────────────────────────────┐
    │ Fahrzeugakte                       │
    │ • Auftragsnummer: 39650            │
    │ • Kennzeichen: DEG-AB-123          │
    │ • VIN: WF0XXXGCDXXX12345           │
    │ • Dokumenttyp: Kostenvoranschlag   │
    │ • Datum: 2025-12-19                │
    └────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      PHASE 4: UNIFIED VIEW IN DRIVE                     │
└─────────────────────────────────────────────────────────────────────────┘

DRIVE zeigt alle Dokumente zusammen:

    ┌─────────────────────────────────────────────────────────────────┐
    │ DRIVE - Auftrag #39650                                          │
    │─────────────────────────────────────────────────────────────────│
    │                                                                 │
    │ Auftragsdaten (aus Locosoft SOAP)                              │
    │ ├─ Kunde: Müller, Hans                                         │
    │ ├─ Fahrzeug: DEG-AB-123 (Opel Corsa)                          │
    │ ├─ Status: In Arbeit                                           │
    │ └─ Arbeitswert: 4.5 AW                                         │
    │                                                                 │
    │ Dokumente                                           [+ Upload]  │
    │ ├─────────────────────────────────────────────────────────────│
    │ │ 📷 Werkstatt-Fotos (Mein-Autohaus App via Locosoft)         │
    │ │    → [In Locosoft Prog. 211 ansehen]                        │
    │ │                                                              │
    │ │ 📄 Archivierte Dokumente (ecoDMS)                           │
    │ │    • KV_39650_20251219.pdf     [Ansehen] [Download]         │
    │ │    • Auftrag_signiert.pdf      [Ansehen] [Download]         │
    │ │                                                              │
    │ │ 📎 Neue Dokumente hochladen                                  │
    │ │    [Datei wählen] → ecoDMS                                  │
    │ └─────────────────────────────────────────────────────────────│
    └─────────────────────────────────────────────────────────────────┘
```

---

## Technische Umsetzung

### ecoDMS API (bereits getestet)

```python
# Server
BASE_URL = 'http://10.80.80.3:8180'

# Dokumente suchen
POST /api/searchDocumentsExtv2
{
    "searchFilter": [{
        "classifyAttribute": "auftrag_nr",  # Custom Field
        "searchValue": "39650",
        "searchOperator": "="
    }],
    "maxDocumentCount": 50
}

# Dokument abrufen
GET /api/document/{docId}

# Dokument hochladen (zu prüfen)
POST /api/upload
```

### Mein-Autohaus App

- **Keine API** für DRIVE-Integration
- Fotos nur in Locosoft Programm 211
- DRIVE zeigt Link: "In Locosoft ansehen"

### DRIVE-Integration

```python
# Neuer Service: tools/ecodms_client.py

class EcoDMSClient:
    def search_by_auftrag(self, auftrag_nr: str) -> List[Document]
    def search_by_kennzeichen(self, kennzeichen: str) -> List[Document]
    def search_by_vin(self, vin: str) -> List[Document]
    def get_document(self, doc_id: int) -> bytes
    def upload_document(self, file, metadata: dict) -> int
```

---

## User-Prozesse nach Rolle

### Mechaniker (Werkstatt)

```
1. Auftrag öffnen (Mein-Autohaus App)
2. Fotos machen (Vorschaden, Befund, Reparatur)
3. Checklist ausfüllen
4. → Bilder sind in Locosoft Prog. 211
```

**Vorteile:**
- Gewohntes Tool
- Mobile-optimiert
- Offline-fähig

### Service-Berater (Büro)

```
1. DRIVE öffnen → Auftrag suchen
2. "Dokumente" Tab
3. Sieht:
   - Info: "Werkstatt-Fotos in Locosoft Prog. 211"
   - Liste: ecoDMS-Dokumente zum Auftrag
4. Upload-Button → Datei wählen → ecoDMS
5. Klassifizierung automatisch:
   - Auftragsnummer aus Kontext
   - Kennzeichen/VIN aus Locosoft
   - Dokumenttyp wählbar
```

### Geschäftsleitung / Controlling

```
1. DRIVE Dashboard
2. Auftrag/Fahrzeug suchen
3. Alle Dokumente auf einen Blick:
   - ecoDMS-Archiv (revisionssicher)
   - Link zu Locosoft für Werkstatt-Fotos
```

---

## Vorteile dieser Lösung

| Aspekt | Vorteil |
|--------|---------|
| **ecoDMS nutzen** | Bereits vorhanden, GoBD-konform, API getestet |
| **Mein-Autohaus App** | Werkstatt-bewährt, mobile Fotos, kein Schulungsaufwand |
| **DRIVE als Hub** | Einheitliche Ansicht, keine Systemwechsel für Büro |
| **Keine Doppelpflege** | Jedes System hat seinen Zweck |
| **Revisionssicher** | ecoDMS für Archiv, erfüllt gesetzliche Anforderungen |

---

## Offene Punkte

### Zu klären

1. **ecoDMS Klassifizierung**
   - Welche Felder für Fahrzeugakte?
   - Gibt es schon Auftragsnummer-Feld?
   - Folder-Struktur für Werkstatt-Dokumente?

2. **ecoDMS Upload-API**
   - Upload-Endpoint testen
   - Automatische Klassifizierung möglich?
   - Max. Dateigröße?

3. **Locosoft Prog. 211 Zugriff**
   - Kann DRIVE direkt verlinken?
   - URL-Schema für Auftrag-Bilder?

4. **Berechtigungen**
   - Wer darf in ecoDMS uploaden?
   - DRIVE-User = ecoDMS-User?

### Nächste Schritte

1. [ ] ecoDMS: Folder-Struktur für Werkstatt-Dokumente anlegen
2. [ ] ecoDMS: Klassifizierungsfelder definieren (Auftrag-Nr, Kennzeichen, VIN)
3. [ ] ecoDMS: Upload-API testen
4. [ ] DRIVE: `tools/ecodms_client.py` erstellen
5. [ ] DRIVE: Dokumente-Tab in Auftragsansicht
6. [ ] Test: End-to-End User-Prozess

---

## Alternativen (nicht empfohlen)

### Alternative A: Alles in DRIVE speichern
- Eigene Dateiablage
- Kein GoBD
- Redundant zu ecoDMS
- **Nicht empfohlen**

### Alternative B: Alles in Locosoft
- SOAP hat keine Dokumenten-API
- Mein-Autohaus App nur für Fotos
- Keine Archiv-Funktion
- **Nicht möglich**

### Alternative C: Gudat Cloud nutzen
- Externe Abhängigkeit
- API-Zugriff unklar
- Doppelte Datenhaltung
- **Nicht empfohlen**

---

*Konzept erstellt: 2025-12-19 (TAG 129)*
