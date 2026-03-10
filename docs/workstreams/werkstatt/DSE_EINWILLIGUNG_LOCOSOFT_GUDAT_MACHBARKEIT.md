# DSE (Datenschutz-Einwilligung) bei Werkstattaufträgen — Machbarkeit

**Stand:** 2026-03-10  
**Workstream:** werkstatt

## Ausgangslage

- In Locosoft gibt es einen Popup-Hinweis zur Datenschutz-Einwilligung (DSE).
- Trotzdem legen Mitarbeiter das Dokument dem Kunden nicht zur Ausfüllung und Unterschrift vor.
- Gewünscht:
  1. **In der Zukunft:** Beim Debitor den Status der Einwilligung zum Datenschutz abfragen (z. B. pro Werkstattauftrag).
  2. **Optional:** DSE-Dokument per SOAP generieren und an den Auftrag in Gudat anhängen.

---

## 1. Status Einwilligung Datenschutz abfragen

### Ergebnis: **Ja, machbar**

In der Locosoft-Datenbank (**loco_auswertung_db**, PostgreSQL auf 10.80.80.8) existieren bereits die Tabellen:

| Tabelle | Zweck |
|--------|--------|
| **`privacy_protection_consent`** | Einwilligungen pro Kunde: `customer_number`, `subsidiary_to_company_ref`, `validity_date_start`, `validity_date_end`, `first_consent_timestamp`, `last_consent_timestamp`, … |
| **`privacy_details`** | Verknüpfung zu Scopes/Kanälen (`scope_code`, `channel_code`) |
| **`privacy_scopes`** | Beschreibung der Scopes |
| **`orders`** | Werkstattaufträge mit `order_customer` (Debitor), `subsidiary` |

**Verknüpfung:**

- Pro Werkstattauftrag: `orders.order_customer` = Kundennummer des Debitors.
- Pro Kunde: In `privacy_protection_consent` nach `customer_number` und ggf. `subsidiary_to_company_ref` (aus `orders.subsidiary`) filtern; Gültigkeit über `validity_date_start` / `validity_date_end` und `last_consent_timestamp` prüfen.

**Umsetzung in DRIVE:**

- API (z. B. in `api/werkstatt_data.py` oder eigenes Modul): Für Auftrag X über Locosoft-DB (read-only) `order_customer` + `subsidiary` lesen, dann Abfrage auf `privacy_protection_consent` (gültige Einwilligung ja/nein).
- Anzeige z. B. in Werkstatt Live oder Auftragsdetail: „DSE-Einwilligung: vorhanden / fehlt / abgelaufen“.
- So kann technisch sichtbar gemacht werden, ob zum Debitor des Auftrags eine Einwilligung vorliegt – unabhängig vom Locosoft-Popup.

**Hinweis:** Die Prüfung ersetzt nicht die Pflicht, das Dokument dem Kunden vorzulegen; sie unterstützt Kontrolle und Erinnerung.

---

## 2. DSE-Dokument per SOAP generieren und an Auftrag anhängen

### 2.1 DSE als PDF generieren

**Machbar in DRIVE.**

- Analog zur Arbeitskarte (`api/arbeitskarte_pdf.py`): PDF aus Vorlage (z. B. Jinja2 + WeasyPrint/ReportLab) mit Kundendaten (aus Locosoft: Kunde/Fahrzeug zum Auftrag) erzeugen.
- Die **inhaltliche** DSE-Vorlage (rechtlicher Text) muss fachlich vorgegeben und gepflegt werden.

### 2.2 Anhängen an Locosoft-Auftrag (SOAP)

**Derzeit unklar – Locosoft-Doku/WSDL nötig.**

- Der bestehende Locosoft-SOAP-Client (`tools/locosoft_soap_client.py`) bietet u. a.:
  - `read_customer`, `read_work_order_details`, `read_appointment`
  - `write_customer_details`, `write_work_order_details`, `write_appointment`, `write_vehicle_details`
- Es gibt **keine** im Projekt genutzte SOAP-Methode zum Hochladen oder Anhängen von Dokumenten an einen Auftrag.
- Ob die Locosoft SOAP-API „Document an Auftrag anhängen“ unterstützt, muss in der **Locosoft SOAP-/WSDL-Dokumentation** (oder beim Anbieter) geklärt werden. Falls ja, könnte der Client um z. B. `attachDocumentToWorkOrder(order_number, pdf_bytes, filename)` ergänzt werden.

### 2.3 Anhängen an Gudat-Auftrag (Dossier)

**Derzeit unklar – Gudat-API-Doku nötig.**

- Gudat wird über REST und GraphQL genutzt (`api/gudat_data.py`, `tools/gudat_client.py`): u. a. `workshopTasks`, `dossier`, `orders`.
- Im Code existiert **keine** Funktion zum Hochladen von Dateien oder zum Anhängen von Dokumenten an Dossier/Auftrag.
- Ob die Gudat-API (werkstattplanung.net) Endpoints/Mutationen für „Upload Document“ / „Attachment an Dossier/Auftrag“ bereitstellt, muss in der **Gudat-API-Dokumentation** geprüft werden. Wenn ja, könnte DRIVE das generierte DSE-PDF dort anhängen.

---

## Zusammenfassung

| Frage | Antwort |
|------|--------|
| Können wir für Werkstattaufträge in Locosoft in der Zukunft beim Debitor den Status der Einwilligung zum Datenschutz abfragen? | **Ja.** Über Locosoft-DB: `orders.order_customer` → `privacy_protection_consent` (gültige Einwilligung). In DRIVE API + Anzeige umsetzbar. |
| Können wir das DSE-Dokument per SOAP generieren? | **Generieren:** Ja (PDF in DRIVE, wie Arbeitskarte). **Per Locosoft-SOAP generieren:** Nein – SOAP liefert Daten, keine Dokumentenerstellung. |
| DSE an Auftrag in Gudat anhängen? | **Technisch möglich**, sofern Gudat eine Upload-/Attachment-API für Dossier/Auftrag anbietet; im Projekt ist das bisher nicht umgesetzt. Klärung über Gudat-Doku/Support. |
| DSE an Locosoft-Auftrag anhängen? | Nur möglich, wenn Locosoft SOAP (oder eine andere Locosoft-API) „Dokument an Auftrag anhängen“ unterstützt. Im aktuellen SOAP-Client nicht vorhanden; Locosoft-WSDL/Doku prüfen. |

---

## Nächste Schritte (Empfehlung)

1. **Priorität 1:** Consent-Status abfragen und anzeigen  
   - Abfrage in Locosoft-DB (`privacy_protection_consent` + `orders`) implementieren.  
   - In Werkstatt-Live oder Auftragsdetail Anzeige „DSE-Einwilligung: vorhanden / fehlt / abgelaufen“.

2. **Priorität 2:** DSE-PDF-Generierung in DRIVE  
   - Rechtliche DSE-Vorlage festlegen.  
   - PDF-Generierung (analog Arbeitskarte) mit Kundendaten aus Locosoft umsetzen.

3. **Priorität 3:** Anhängen an Gudat/Locosoft  
   - Mit Gudat (werkstattplanung.net): API auf Dokument-Upload/Attachment prüfen.  
   - Mit Locosoft: SOAP/WSDL auf „Document an Auftrag anhängen“ prüfen.  
   - Danach ggf. Integration in DRIVE (Upload des generierten DSE-PDFs).

---

*Referenzen: `docs/DB_SCHEMA_LOCOSOFT.md` (privacy_protection_consent, orders), `tools/locosoft_soap_client.py`, `api/gudat_data.py`, `api/arbeitskarte_pdf.py`.*
