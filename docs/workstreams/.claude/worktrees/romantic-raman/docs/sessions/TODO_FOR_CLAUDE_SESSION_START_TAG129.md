# TODO für Claude - Session Start TAG 129

**Erstellt:** 2025-12-19

---

## Kontext

Locosoft SOAP API ist vollständig getestet und dokumentiert.
Version 2.2 funktioniert mit den richtigen HTTP-Headern.

---

## Offene Aufgaben

### 1. Manuell in Locosoft löschen (User-Aufgabe)
- [ ] Auftrag 39649 (Test, Kunde: Stein, LAN-WS 800)
- [ ] Termin Nr. 6 (Text: "STORNIERT")

### 2. SOAP-Integration weiterentwickeln
- [ ] Python SOAP-Client-Klasse erstellen
- [ ] Error-Handling implementieren
- [ ] Retry-Logik für Verbindungsfehler

### 3. Portal-Integration
- [ ] Termine aus Portal anlegen
- [ ] Werkstatt-Liveboard mit SOAP-Daten

---

## Wichtige Dateien

| Datei | Beschreibung |
|-------|--------------|
| `config/locosoft_soap_config.py` | SOAP-Konfiguration mit v2.2 Headers |
| `L:\soap-ui\dataquery-2-2-soapui-project.xml` | SoapUI-Projekt mit Beispielen |

---

## Quick Reference - SOAP v2.2

```bash
curl -X POST "http://10.80.80.7:8086/" \
  -u "9001:Max2024" \
  -H "Content-Type: text/xml" \
  -H "locosoftinterface: GENE-AUTO" \
  -H "locosoftinterfaceversion: 2.2" \
  -d '<soap-envelope>'
```
