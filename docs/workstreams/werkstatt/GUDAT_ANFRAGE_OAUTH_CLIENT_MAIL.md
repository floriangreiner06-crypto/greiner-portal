# E-Mail-Anfrage an Gudat: OAuth-Client für DA REST API

**Zweck:** Copy & Paste für Mail an developer@digitalesautohaus.de (oder Ansprechpartner Gudat).  
**Stand:** 2026-03-10

---

## Betreff

```
Anfrage API-Zugang DA REST API (Autohaus Greiner, greiner/deggendorf + greiner/landau)
```

---

## An

```
developer@digitalesautohaus.de
```
(oder bekannter Gudat-Ansprechpartner)

---

## Mail-Text (Copy & Paste)

```
Sehr geehrtes Gudat-Team,

wir betreiben im Autohaus Greiner ein internes Informations-Portal zur Werkstatt-Optimierung und KPI-Auswertung und möchten dieses künftig an das Digitale Autohaus (DA) anbinden.

Konkret möchten wir die DA REST API V1 (https://api.werkstattplanung.net/da/v1) nutzen, um Daten zu Service-Ereignissen, Dossiers, Dokumenten und Statusinformationen automatisiert auszuwerten und in unserem Portal nutzbar zu machen. Perspektivisch sind u. a. folgende Use Cases geplant:

- Service Events und Dossiers in einem definierten Datumsbereich lesen (z. B. wie im service_events-Beispiel der OpenAPI-Doku)
- Dokumente an Dossiers anhängen bzw. abrufen (Endpoint documents)
- Statusänderungen über status_triggers (z. B. Kamera/Scanner)
- ausgewählte orders-Funktionen für Auswertungen nutzen

Laut Ihrer OpenAPI-Spezifikation (DA API V1 Reference, openapi.json) benötigen wir dafür:
- Client ID
- Client Name
- Client Secret
sowie die Freischaltung für unsere Instanzen (Header group/center) zur Nutzung des /oauth/token-Endpoints (Password Grant) und der nachgelagerten Routen.

Unsere Instanzen:
- Gruppe: greiner, Center: deggendorf
- Gruppe: greiner, Center: landau

Unsere Fragen:
1. Können Sie uns bitte einen OAuth-Client (Client ID, Name, Secret) für die DA REST API V1 für die Instanzen greiner/deggendorf und greiner/landau ausstellen?
2. Ist auf Ihrer Seite eine zusätzliche Freigabe/Konfiguration notwendig, damit Requests mit group=greiner und center=deggendorf bzw. center=landau akzeptiert werden?
3. Gibt es aus Ihrer Sicht Empfehlungen oder Einschränkungen, welche Endpoints wir aus einem internen Werkstatt-Informations- und KPI-Portal bevorzugt nutzen oder meiden sollten (z. B. service_events, documents, orders, status_triggers)?

Technische Unterlagen, auf die wir uns beziehen:
- DA API V1 Reference (https://werkstattplanung.net/greiner/deggendorf/kic/da/docs/index.html)
- OpenAPI-Datei openapi.json: **nicht im Repo gespeichert** – ggf. von der Referenz-URL herunterladen oder bei Gudat anfordern und in docs/workstreams/werkstatt/ oder docs/api-specs/ ablegen.

Über die Zusendung der Zugangsdaten und ggf. kurze Hinweise zu Best Practices für die Nutzung der API in einem internen Werkstatt-Portal würden wir uns sehr freuen.

Mit freundlichen Grüßen

[Dein Name]
Autohaus Greiner GmbH & Co. KG
[Funktion / Abteilung]
[Telefon]
[E-Mail]
```

---

## Hinweis

Vor dem Versand die Platzhalter `[Dein Name]`, `[Funktion / Abteilung]`, `[Telefon]`, `[E-Mail]` ersetzen.
