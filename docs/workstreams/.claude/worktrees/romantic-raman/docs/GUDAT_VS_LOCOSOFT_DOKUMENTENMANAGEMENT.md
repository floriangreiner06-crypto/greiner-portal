# Gudat vs. Locosoft - Dokumentenmanagement & Bilder Analyse

**Erstellt:** 2025-12-19 (TAG 129)
**Frage:** Wo werden Bilder/Dokumente zu Aufträgen gespeichert? Kann Locosoft Gudat ersetzen?

---

## Executive Summary

| Aspekt | Gudat | Locosoft (SOAP) | Locosoft (Mein-Autohaus App) |
|--------|-------|-----------------|------------------------------|
| Bilder zu Aufträgen | Cloud-basiert | KEINE API-Funktion | Ja, in Programm 211 |
| Dokumente speichern | Cloud-basiert | DOCBOX-Integration | Programm 211 + DOCBOX |
| API-Zugriff auf Bilder | Unbekannt | Nicht vorhanden | Nicht vorhanden |
| Mobile Upload | Web/App | - | Mein-Autohaus App |

**Kurze Antwort:** Die SOAP-API bietet **KEINE** Dokumenten-/Bilderverwaltung. Die **Mein-Autohaus App** ermöglicht Foto-Upload zu Aufträgen, speichert aber direkt in Locosoft (Programm 211). Für DRIVE-Integration wäre ein eigenes Dokumentenmanagement nötig.

---

## 1. Gudat "Digitales Autohaus" - Dokumentenfunktionen

### 1.1 Was wir wissen

Gudat ist eine **web- und cloudbasierte Plattform** für:
- Terminplanung
- Werkstattplanung
- Serviceplanung
- Schichtplanung
- Echtzeit-Monitoring

**Dokumentenfunktionen (angenommen):**
- Cloud-Speicherung von Bildern zu Dossiers/Aufträgen
- Integration in Werkstattprozesse
- Möglicherweise über separate Felder in GraphQL API

### 1.2 GraphQL API - Dokumentenfelder

Bei unserer API-Analyse haben wir **KEINE expliziten Felder** für Dokumente/Bilder gefunden:

```graphql
# Dossier-Type enthält:
- id, created_at, updated_at
- vehicle, orders, appointments
- states, tags
# KEINE: documents, images, attachments, files
```

**Mögliche Erklärung:**
- Dokumente werden über separate Endpoints verwaltet
- Oder über UI-only Funktionen (nicht API-exponiert)
- DSGVO-Schutz für Bilddaten

### 1.3 Was Gudat laut Website bietet

Laut [digitalesautohaus.de](https://www.digitalesautohaus.de/):
- Serviceplanung mit Leistungen/Optionen
- Werkstattplanung mit Kapazitäten
- Automatisierte Workflows
- Kommunikation (SMS/Email)
- **Kein expliziter Hinweis auf Dokumentenmanagement**

---

## 2. Locosoft - Dokumentenmanagement

### 2.1 SOAP API (Programm 266)

Die SOAP-Schnittstelle bietet **KEINE** Operationen für:
- Dokumente hochladen/herunterladen
- Bilder zu Aufträgen speichern
- Dateien verwalten
- Attachments lesen/schreiben

**WSDL-Analyse zeigt nur:**
- Kunden/Fahrzeuge/Aufträge/Termine
- Kapazitäten und Arbeitsgruppen
- Teile und Stundensätze
- KEINE: document, image, file, upload, attachment, blob, binary

### 2.2 DOCBOX-Integration

Loco-Soft nutzt **DOCBOX** als externes Dokumentenmanagement-System:

| Feature | DOCBOX-Integration |
|---------|-------------------|
| Fahrzeugakte | Elektronisch, über VIN identifizierbar |
| Dokumententypen | Rechnungen, Aufträge, Belege |
| Zugriff | Aus Loco-Soft Programmen heraus |
| Revisionssicher | Ja (GoBD-konform) |
| PDF-Archiv | Automatisch bei Rechnungsdruck |

**Wichtig:** DOCBOX ist ein **separates System**, nicht Teil der SOAP-API!

Quelle: [docbox.eu - Loco-Soft](https://www.docbox.eu/partner/loco-soft.html)

### 2.3 Mein-Autohaus App

Die mobile App ([App Store](https://apps.apple.com/de/app/mein-autohaus/id6449280675)) bietet:

| Funktion | Verfügbar | Details |
|----------|-----------|---------|
| **Fotos erstellen** | Ja | Für Fahrzeuge und Aufträge |
| **Bilder hochladen** | Ja | Direkt in Auftrag |
| **Videos hochladen** | Ja | In Programm 211 sichtbar |
| **Dokumente unterschreiben** | Ja | Signatur-Funktion |
| **Checklisten** | Ja | ABER: Keine Bildanhänge möglich! |
| **Räder-Fotos** | Ja | Für Reifeneinlagerung |

**Speicherort:** Programm 211 in Locosoft (nicht SOAP-zugänglich)

---

## 3. Feature-Vergleich: Bilder/Dokumente

### 3.1 Detaillierte Matrix

| Feature | Gudat | Locosoft SOAP | Mein-Autohaus App | DOCBOX |
|---------|-------|---------------|-------------------|--------|
| Foto zu Auftrag | ? (Cloud) | NEIN | JA (Prog. 211) | Nein |
| Video zu Auftrag | ? | NEIN | JA | Nein |
| Dokument speichern | ? (Cloud) | NEIN | Nein | JA |
| API-Zugriff | Unbekannt | NEIN | NEIN | Separat |
| Mobile Upload | Web-App | - | JA | - |
| Unterschrift | ? | NEIN | JA | - |
| Revisionssicher | ? | - | Nein | JA (GoBD) |
| DSGVO-konform | Ja | - | ? | JA |

### 3.2 Der kritische Gap

**Was wir brauchen:**
- Bilder/Dokumente zu Aufträgen in DRIVE speichern
- API-Zugriff für Integration
- Cloudbasierte Lösung

**Was verfügbar ist:**
- Locosoft SOAP: Keine Dokumentenfunktion
- Mein-Autohaus App: Nur proprietärer Zugriff (Prog. 211)
- DOCBOX: Separates System, eigene Integration nötig

---

## 4. Lösungsoptionen

### Option A: Eigenes Dokumentenmanagement in DRIVE

```
DRIVE-Datenbank (SQLite/PostgreSQL):
├── documents (id, auftrag_nr, type, filename, path, created_at)
├── document_types (id, name, category)
└── Storage: Filesystem oder S3-kompatibel

API-Endpoints:
├── POST /api/documents/upload
├── GET /api/documents/{auftrag_nr}
├── DELETE /api/documents/{id}
```

**Vorteile:**
- Volle Kontrolle
- API-Zugriff
- Integration mit DRIVE-Features

**Nachteile:**
- Entwicklungsaufwand
- Speicher-Management
- Backup-Strategie nötig

**Aufwand:** 2-3 Wochen

### Option B: DOCBOX-Integration für DRIVE

```
DRIVE → DOCBOX API → Dokumentenarchiv
                  ↓
       Locosoft kann darauf zugreifen
```

**Vorteile:**
- Revisionssicher (GoBD)
- Bereits bei Greiner im Einsatz?
- Integration mit Locosoft

**Nachteile:**
- Zusätzliche Lizenzkosten?
- API-Dokumentation nötig
- Komplexere Integration

**Aufwand:** 3-4 Wochen + DOCBOX-Setup

### Option C: Hybrid - DRIVE + Mein-Autohaus App

```
Werkstatt-Mitarbeiter:
  └── Mein-Autohaus App → Fotos → Locosoft Prog. 211

Büro/Disposition:
  └── DRIVE → Eigene Dokumente → DRIVE-Storage

Verknüpfung:
  └── Auftragsnummer als gemeinsamer Key
```

**Vorteile:**
- Nutzt bestehende Infrastruktur
- Werkstatt hat bewährte App
- DRIVE für Management-Dokumente

**Nachteile:**
- Zwei Systeme
- Keine einheitliche Ansicht

---

## 5. Empfehlung

### Kurzfristig (Sofort umsetzbar)

1. **Mein-Autohaus App** für Werkstatt-Fotos nutzen
   - Bereits vorhanden
   - Direkt in Locosoft
   - Keine Entwicklung nötig

2. **DRIVE-Dokumenten-Modul** als MVP bauen:
   ```python
   # Einfaches Dokumenten-Upload für DRIVE
   class DriveDocumentStorage:
       def upload(self, auftrag_nr, file, doc_type)
       def list_documents(self, auftrag_nr)
       def get_document(self, doc_id)
   ```

### Mittelfristig (1-3 Monate)

3. **DOCBOX-Integration prüfen**
   - Ist DOCBOX bei Greiner im Einsatz?
   - API-Dokumentation besorgen
   - Integration als Option bewerten

4. **Unified Document View** in DRIVE
   - Zeigt DRIVE-Dokumente
   - Zeigt Locosoft-Auftragsinfo (via SOAP)
   - Optional: DOCBOX-Dokumente anzeigen

---

## 6. Mein-Autohaus App - Vollständige Feature-Liste

### Verfügbare Funktionen

| Bereich | Feature | Details |
|---------|---------|---------|
| **Stammdaten** | Adressen hinzufügen | Kundenkontakte |
| | Kunden anrufen | Direktwahl |
| | Fahrzeugdaten einsehen | Mobil abrufbar |
| **Aufträge** | Auftragsdaten einsehen | Unterwegs |
| | Aufträge erstellen/bearbeiten | Mobile Erfassung |
| | Positionsinfos hinterlegen | Monteur-Notizen |
| | Bilder hochladen | Direkt zum Auftrag |
| | Videos hochladen | Sichtbar in Prog. 211 |
| **Werkstatt** | Checklisten | Ohne Bildanhang |
| | Kilometerstand erfassen | In Auftrag/Checkliste |
| | Arbeitszeiten erfassen | Mobile Stempelung |
| **Räder** | Rädereinlagerung | Lagerort-Suche |
| | Reifenetiketten drucken | Per Klick |
| **Inventur** | Barcode scannen | Teileerfassung |
| | Offline-Modus | Ohne Internet |
| | Manuelle Auswahl | Fallback |
| **Kommunikation** | Interne Nachrichten | Weltweit lesen/schreiben |
| | Kontaktnotizen | Zu Kunden/Interessenten |

Quelle: [App Store - Mein Autohaus](https://apps.apple.com/de/app/mein-autohaus/id6449280675)

---

## 7. Fazit

### Gudat ersetzen für Dokumente?

**Antwort: Nicht empfohlen, aber machbar**

| Aspekt | Empfehlung |
|--------|------------|
| Werkstatt-Fotos | Mein-Autohaus App nutzen (bereits vorhanden) |
| Kunden-Dokumente | Eigenes DRIVE-Modul bauen |
| Archiv/GoBD | DOCBOX prüfen |
| API-Integration | SOAP hat keine Dokumenten-Features |

### Prioritäten

1. **Jetzt:** Mein-Autohaus App für Werkstatt-Fotos empfehlen
2. **Sprint 1:** Einfaches DRIVE-Dokumenten-Upload bauen
3. **Sprint 2:** DOCBOX-Integration evaluieren
4. **Langfristig:** Unified Document View in DRIVE

---

## Quellen

- [Digitales Autohaus - Website](https://www.digitalesautohaus.de/)
- [Mein-Autohaus App - App Store](https://apps.apple.com/de/app/mein-autohaus/id6449280675)
- [DOCBOX - Loco-Soft Integration](https://www.docbox.eu/partner/loco-soft.html)
- [Loco-Soft - Website](https://loco-soft.de/)
- [MAHA übernimmt Digitales Autohaus](https://www.kfz-betrieb.vogel.de/maha-uebernimmt-digitales-autohaus-a-659527/)

---

*Analyse erstellt: 2025-12-19 (TAG 129)*
