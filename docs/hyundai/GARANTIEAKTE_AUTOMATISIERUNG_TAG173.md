# Garantieakte: Vollständige Automatisierung

**Erstellt:** 2026-01-09 (TAG 173)  
**Zweck:** Vollständige Garantieakte automatisiert erstellen (PDF + Bilder + Dokumente)

---

## 📋 ANFORDERUNGEN

### 1. Vollständige Akte zur Garantieabrechnung
- ✅ Arbeitskarte-PDF (bereits implementiert)
- ✅ Bilder aus GUDAT
- ✅ Alle Dokumente kombinieren
- ✅ Stempelzeiten auf Arbeitszeilen verteilen

### 2. Stempelzeiten-Verteilung per SOAP
- ✅ **Nicht nur Garantie, sondern grundsätzlich**
- ✅ Unzugeordnete Stempelzeiten auf Positionen verteilen
- ✅ `write_work_order_times()` mit `workOrderLineNumber`

---

## 🔍 ANALYSE: AKTE 220266

### Locosoft-Daten
- ✅ 8 Arbeitspositionen
- ✅ 7 Stempelzeiten (alle bereits zugeordnet)
- ✅ 2 Teile
- ⚠️ Keine unzugeordneten Stempelzeiten (in diesem Fall)

### GUDAT-Daten
- ⚠️ Dossier nicht gefunden (Auftrag zu alt oder nicht in GUDAT angelegt)
- ✅ **Attachments-API verfügbar:**
  ```graphql
  dossier {
    attachments {
      id
      name
      file_name
      mime_type
      size
      created_at
    }
  }
  ```

---

## 🚀 IMPLEMENTIERUNG

### 1. Stempelzeiten-Verteilung per SOAP

**Methode:** `write_work_order_times()`

**Parameter:**
```python
{
    'workOrderNumber': int,
    'mechanicId': int,
    'startTimestamp': datetime,
    'endTimestamp': datetime,
    'isFinished': bool,
    'workOrderLineNumber': int oder List[int]  # ← WICHTIG!
}
```

**Workflow:**
1. Unzugeordnete Stempelzeiten aus Locosoft holen (`times` Tabelle, `order_position IS NULL`)
2. Für jede Stempelzeit:
   - Bestehende Positionen prüfen (nach Mechaniker, Zeitfenster)
   - Oder neue Position erstellen
   - `write_work_order_times()` mit `workOrderLineNumber` aufrufen

**API-Endpoint:**
```python
POST /api/werkstatt/verteile-stempelzeiten/<int:order_number>
```

### 2. Bilder aus GUDAT holen

**GraphQL-Query:**
```graphql
query GetDossierAttachments($id: ID!) {
  dossier(id: $id) {
    id
    attachments {
      id
      name
      file_name
      mime_type
      size
      created_at
      url  # Falls verfügbar
    }
  }
}
```

**Workflow:**
1. Dossier-ID für Auftrag finden
2. Attachments abfragen
3. Bilder filtern (`mime_type.startswith('image/')`)
4. Bilder herunterladen (falls URL verfügbar)
5. In PDF einbinden

**API-Endpoint:**
```python
GET /api/arbeitskarte/<int:order_number>/bilder
```

### 3. Vollständige Akte erstellen

**Workflow:**
1. Arbeitskarte-PDF generieren (bereits implementiert)
2. Bilder aus GUDAT holen
3. Bilder in PDF einbinden (ReportLab `Image`)
4. Alle Dokumente kombinieren
5. Finale PDF erstellen

**API-Endpoint:**
```python
GET /api/arbeitskarte/<int:order_number>/vollstaendig
```

---

## 📊 STATUS

| Feature | Status | Implementierung |
|---------|--------|------------------|
| Arbeitskarte-PDF | ✅ | `api/arbeitskarte_pdf.py` |
| Stempelzeiten-Verteilung | ⏳ | `api/werkstatt_soap_api.py` |
| GUDAT-Bilder holen | ⏳ | `api/arbeitskarte_api.py` |
| Vollständige Akte | ⏳ | `api/arbeitskarte_api.py` |

---

## 🔧 NÄCHSTE SCHRITTE

1. ✅ **Stempelzeiten-Verteilung implementieren**
   - API-Endpoint erstellen
   - Unzugeordnete Stempelzeiten identifizieren
   - Auf Positionen verteilen

2. ✅ **GUDAT-Bilder-API erweitern**
   - Attachments-Query testen
   - Bild-Download implementieren
   - In PDF einbinden

3. ✅ **Vollständige Akte**
   - Alle Komponenten kombinieren
   - Finale PDF generieren

---

## 💡 HINWEISE

- **Stempelzeiten-Verteilung:** Funktioniert für **alle Aufträge**, nicht nur Garantie
- **Bilder:** Können auch manuell hochgeladen werden (nicht nur GUDAT)
- **PDF-Größe:** Bei vielen Bildern kann PDF sehr groß werden
