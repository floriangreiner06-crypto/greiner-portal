# Wie schreiben wir Verkaufspreise in Locosoft?

**Workstream:** Verkauf  
**Stand:** 2026-03-11  
**Ziel:** Verkaufspreis (Händlerfahrzeug, z. B. `dealer_vehicles.out_sale_price`) **programmatisch** setzen – z. B. aus eAutoSeller, damit Dispo nicht manuell in Locosoft tippen muss.

---

## Was wir bereits geprüft haben

### 1. Locosoft PostgreSQL (10.80.80.8)

- **Read-only** für DRIVE (Spiegel/Auswertung). Schreibzugriff auf die Locosoft-DB ist von unserer Seite **nicht vorgesehen** und würde Architektur/Betrieb von Loco-Soft verletzen.
- **Fazit:** Preise dort direkt per SQL zu ändern ist **kein Weg**.

### 2. Locosoft SOAP (10.80.80.7:8086)

Alle **Schreib-Operationen** der WSDL wurden geprüft:

| Operation | Typ / Parameter | Enthält Verkaufspreis? |
|-----------|------------------|------------------------|
| **writeVehicleDetails** | `holderNumber`, `vehicle: DMSServiceVehicle` | **Nein.** DMSServiceVehicle = nur Stammdaten (Marke, Modell, VIN, km, Halter, Farben, Motor, …), **kein** out_sale_price, kein price, kein salePrice. |
| **writePotential** | `potential: DMSServicePotential` | **Nein.** Verkaufspotential/Lead (vehicleNumber, number, state, orderNumber, kvValue, …), nicht der Listenpreis des Händlerfahrzeugs. |
| writeCustomerDetails | DMSServiceCustomer | Nein (Kundenstamm). |
| writeWorkOrderDetails | DMSServiceWorkOrder | Nein (Auftrag). |
| writeAppointment | … | Nein (Termin). |
| writeVehicleAccessories | vehicleNumber + Zubehör | Nein. |
| writeVehicleAdditionalDates | vehicleNumber + Zusatzdaten | Nein. |
| writeVehicleFixedEntry | … | Nein. |
| writeWorkOrderTimes / writeWorkTimes | Zeiten | Nein. |

**Fazit:** In der **aktuellen SOAP-WSDL gibt es keine Operation**, die den Verkaufspreis eines Händlerfahrzeugs (`dealer_vehicles.out_sale_price` o. ä.) setzt.

### 4. Erneute Server-Erkundung (Roh-WSDL)

Zur Absicherung wurde der Locosoft-Server erneut erkundet:

- **Skript:** `scripts/locosoft_wsdl_explore_preis.py` (lädt WSDL, durchsucht nach price/sale/dealer/preis/out_sale/sellingPrice/…).
- **Ergebnis:** Im WSDL-Text kommt „price“ nur einmal vor (in der ersten Zeile, vermutlich Namespace/URL), **keine** Felder oder Typen für Verkaufspreis/Händlerfahrzeug-Preis.
- **Alle Pfade** (`/?wsdl`, `/soap?wsdl`, `/Dataquery?wsdl`) liefern dieselben **33 Operationen**; keine davon heißt z. B. `writeDealerVehicle` oder `updateSalePrice`, und in den Typen erscheinen keine preisbezogenen Schreib-Felder.

**Konklusion:** Eine erneute Exploration bestätigt: SOAP auf diesem Server **kann** Verkaufspreise (Händlerfahrzeug) **nicht** setzen – weder über eine eigene Operation noch über ein Preisfeld in den bestehenden write-Typen.

### 5. Netzwerkverzeichnis \\10.80.80.7\Loco erkunden

**Sinn:** Auf dem Locosoft-Server liegen oft Ordner für **Import/Export**, **Dokumentation** oder **Schnittstellen-Konfiguration**. Dort können Hinweise stehen, ob z. B. ein **Datei-Import** (CSV/Excel) für Fahrzeug- oder Preisaktualisierungen vorgesehen ist, oder ob SOAP/API anders genutzt wird.

**Aktueller Stand:**
- Auf dem DRIVE-Server (Linux) sind **nur zwei Unterpfade** von Loco gemountet:
  - `//srvloco01/Loco/BILDER` → `/mnt/loco-bilder`
  - `//srvloco01/Loco/LOCOAUSTAUSCH/PSABox/.../Teilelieferscheine` → `/mnt/loco-teilelieferscheine`
- Der **Loco-Stamm** (`\\10.80.80.7\Loco` bzw. `//srvloco01/Loco`) ist auf dem Linux-Server **nicht** gemountet – eine vollständige Erkundung des Shares von dort aus ist so nicht möglich.

**Was auf dem Loco-Share prüfen (unter Windows oder nach Mount des Stamm-Shares):**

| Was | Wozu |
|-----|------|
| **Import / Export / Austausch** | Ordner wie `Import`, `Export`, `LOCOAUSTAUSCH`, `Schnittstelle` – oft für dateibasierte Anbindung (CSV, Excel). Prüfen ob es Unterordner für „Fahrzeuge“ oder „Verkauf“ gibt. |
| **Doku / API / SOAP** | Ordner oder Dateien mit Namen wie `Dokumentation`, `API`, `SOAP`, `Schnittstellen` – können Format und erlaubte Operationen beschreiben. |
| **Konfiguration** | INI/XML/JSON-Dateien, die Pfade für Import oder Export definieren (z. B. „Fahrzeugpreise aus CSV lesen“). |
| **Beispieldateien** | CSV/Excel im Import-Bereich mit Spalten wie VIN, Preis – zeigen evtl. das erwartete Format für einen Import. |

**Vorgehen:** Entweder (a) unter Windows `\\10.80.80.7\Loco` (bzw. `\\srvloco01\Loco`) öffnen und die Ordnerstruktur sowie ggf. README/Doku durchsehen, oder (b) auf dem Linux-Server den Loco-Stamm mounten (siehe unten) und mit einem Skript nach Ordnernamen/Dateien suchen (z. B. nach „Import“, „Preis“, „Fahrzeug“, „CSV“). Gefundene Hinweise (Pfade, Format) in dieser Doku festhalten und mit Loco-Soft abgleichen.

**Erkundung durchgeführt (nach Mount /mnt/loco):**

| Pfad (auf /mnt/loco) | Inhalt / Hinweis |
|----------------------|------------------|
| **DOKUMENTE/LocoSoft-SOAP-Datenabfrage-Webservice.pdf** | Offizielle SOAP-Doku (Stand 08.2025): Einrichtung Serverdienst, Zertifikat, Port; beschreibt „Abfrage und bidirektionalen Austausch“ zu Kunden-, Fahrzeug-, Arbeits-, Ersatzteil- und Auftragsinformationen. Keine explizite Nennung von Verkaufspreis-Schreiben. |
| **DOKUMENTE/LocoSoft-Standardschnittstellen für Drittanbieter.pdf** | Variante 3 (bidirektional): Fremdsystem kann „Kunden-, **Kundenfahrzeug-** , Potenzial-, Auftrags- und Stempeldaten** in Loco-Soft schreiben oder bearbeiten“. Es wird **nicht** explizit „Händlerfahrzeug“ oder „Verkaufspreis“ genannt – bei Loco-Soft nachfragen, ob Verkaufspreis (Pr. 132) unter Variante 3 fällt und welche Operation/Feld. |
| **LOCOAUSTAUSCH/eAutoseller/** | Enthält `locosoft_greiner.zip` – Austauschformat eAutoSeller ↔ Locosoft; Inhalt prüfen (evtl. Fahrzeug/Preis-Felder). |
| **LOCOAUSTAUSCH/Excel/** | Excel-Dateien (z. B. VFW, Mietwagen); Import/Export per Excel – kein direkter Hinweis auf Preis-API. |
| **Import/** | L331PR-Profile (FIBU/OPOS), Reifenlager-Import, Bonde Light CSV – Stammdaten/Import, kein Preis-SOAP beschrieben. |
| **LOCOHELP/** | „Fahrzeug Verkaufspreis Berechnungshilfe“ (Videos) – UI-Funktion in Locosoft, keine API. |

**SOAP WSDL (erneut geprüft):** Unverändert 33 Operationen, keine mit Verkaufspreis-Feld. Einzige Schreibzugriffe auf Fahrzeugebene: `writeVehicleDetails` (Stammdaten, keine Preise), `writePotential` (Verkaufspotential).

**Mount auf dem DRIVE-Server (nach Freigabe für AD-Dienstuser am Locosoft-Server):**
- Mount-Point: `/mnt/loco`
- Share: `//srvloco01/Loco` (entspricht `\\10.80.80.7\Loco`)
- Credentials: dieselben wie für die anderen Loco-Mounts (`/root/.smbcredentials`, User svc_portal)
- Script: `scripts/mount_loco_stamm.sh` (mit `sudo bash scripts/mount_loco_stamm.sh` ausführen)
- Dauerhaft in fstab: Zeile `//srvloco01/Loco /mnt/loco cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0664,dir_mode=0775,nofail 0 0`

### 3. Skripte / Referenz

- **Preistest (SOAP):** `scripts/test_locosoft_fahrzeugpreis_update.py` – Aufruf `writeVehicleDetails` mit `outSalePrice` → Fehler „unexpected keyword argument 'outSalePrice'“.
- **WSDL-Introspektion:** `scripts/locosoft_wsdl_introspect.py` – listet alle SOAP-Operationen; Typen `DMSServiceVehicle` und `DMSServicePotential` wurden explizit ausgelesen (keine Preisfelder für Listenpreis).

---

## Was wir brauchen

- **Fachlich:** Setzen des **Verkaufspreises** (Listenpreis) eines **Händlerfahrzeugs** (noch nicht verkauft), identifiziert z. B. über **VIN** oder `vehicle_number` / `dealer_vehicle_number`.
- **Technisch:** Eine von Loco-Soft unterstützte Schnittstelle, z. B.:
  - eine **SOAP-Operation** (z. B. `writeDealerVehicleDetails` oder Erweiterung von `writeVehicleDetails` um Preisfelder),
  - ein **REST-Endpoint** (z. B. `PATCH /dealer-vehicle/{id}` mit `salePrice`),
  - oder ein **CSV-/Datei-Import** in Locosoft mit Preis-Spalte.

---

## Nächster Schritt: Loco-Soft anfragen

**Empfohlene Anfrage an Loco-Soft (Support/Dokumentation):**

> Wir nutzen die Locosoft SOAP-Schnittstelle (10.80.80.7, Dataquery) und die PostgreSQL-Auswertungsdatenbank (read-only).  
> **Frage:** Wie können wir den **Verkaufspreis** eines Händlerfahrzeugs (noch nicht in Rechnung gestellt) **programmatisch setzen**?  
> In der SOAP-WSDL finden wir keine Operation mit Preisfeldern für Händlerfahrzeuge (`writeVehicleDetails` betrifft nur Fahrzeugstammdaten). Gibt es  
> - eine weitere SOAP-Operation (z. B. für Händlerfahrzeug/Verkauf),  
> - eine REST-API oder  
> - einen Import (CSV/Datei)  
> zum Aktualisieren des Verkaufspreises (z. B. `out_sale_price` / Auszeichnung)?  
> Unser Anwendungsfall: Preismanagement läuft in eAutoSeller; wir möchten geänderte Preise automatisch in Locosoft übernehmen.

---

## Kurzfassung

| Weg | Status |
|-----|--------|
| PostgreSQL Locosoft beschreiben | ❌ Read-only, nicht vorgesehen |
| SOAP writeVehicleDetails (Preis) | ❌ Typ ohne Preisfelder |
| SOAP writePotential | ❌ Verkaufspotential, nicht Listenpreis |
| Weitere SOAP-Operation | ❓ In WSDL keine gefunden – Loco-Soft fragen |
| REST / Import von Loco-Soft | ❓ Offen – Loco-Soft fragen |

**Konklusion:** Preise in Locosoft schreiben ist derzeit nur über die **Locosoft-UI** möglich. Für Automatisierung (z. B. eAutoSeller → Locosoft) ist eine **offizielle Antwort von Loco-Soft** nötig, ob und wie eine API/Import für Verkaufspreise existiert oder bereitgestellt werden kann.

---

## Alternative Automatisierungsideen (ohne offizielle Preis-API)

Falls Loco-Soft keine API/Import anbietet: andere Wege **konzeptionell** (noch nichts coden).

### 1. RPA / Robot für Locosoft-UI

**Idee:** Ein Programm steuert die Locosoft-Oberfläche wie ein Mensch – Login, VIN-Suche, Preisfeld öffnen, neuen Preis eintippen, Speichern.

- **Technik:** Selenium, Playwright oder RPA-Tool (z. B. n8n Browser-Node, UiPath, Power Automate) auf einem Rechner mit Zugriff auf Locosoft (Browser oder Client).
- **Ablauf:** DRIVE/eAutoSeller liefert Liste (VIN + neuer Preis) → Robot holt nächsten Eintrag → öffnet Locosoft, sucht VIN, füllt Preisfeld, speichert → markiert erledigt.
- **Vorteile:** Keine API von Loco-Soft nötig; nutzt die bestehende UI.
- **Nachteile:** UI-Änderungen (Update, neue Masken) können den Ablauf brechen; Wartung nötig; langsamer als API; evtl. Lizenzen/AGB („automatisierter Zugriff“); stabiler Betrieb braucht dedizierten Rechner/VM und saubere Fehlerbehandlung.

### 2. Import-Datei (CSV/Excel) in Locosoft

**Idee:** Viele DMS haben Stammdaten-Import (z. B. „Fahrzeuge aus CSV/Excel aktualisieren“). Wenn Locosoft so etwas für Händlerfahrzeuge/Preise kann: DRIVE oder eAutoSeller schreibt eine Datei (Netzlaufwerk, Freigabe), Locosoft importiert sie – manuell ausgelöst oder per geplantem Job (falls von Loco-Soft angeboten).

- **Vorteile:** Kein UI-Robot; oft stabiler als Bildschirmsteuerung.
- **Nachteile:** Muss von Loco-Soft unterstützt werden (Import-Funktion, Format, Spalten). Ohne Doku/Klärung nicht umsetzbar.

### 3. Halbautomatik: Assistenz statt voller Robot

**Idee:** Dispo behält den Klick in Locosoft, wird aber entlastet: z. B. eine kleine Liste „Nächste Preisübernahme“ (VIN + Preis), Buttons „VIN kopieren“ / „Preis kopieren“. Dispo fügt in Locosoft ein (Strg+V), speichert – kein Suchen in E-Mails, kein Abtippen.

- **Vorteile:** Kein Robot, keine UI-Anfälligkeit; schnelle Umsetzung; klare Verantwortung beim Menschen.
- **Nachteile:** Manueller Schritt bleibt; „echte“ Automatisierung erst mit API oder Robot.

### 4. Makro auf festem Arbeitsplatz (Tastatur/Maus)

**Idee:** Auf einem festen PC (z. B. Dispo-PC) läuft ein Makro (AutoHotkey, Python mit pyautogui o. ä.): wartet auf neue Einträge (z. B. aus DRIVE oder lokaler Datei), bringt Locosoft in den Vordergrund, führt Klicks und Tastatureingaben aus (VIN-Suche, Preisfeld, Wert, Speichern).

- **Vorteile:** Nutzt die echte Locosoft-UI; keine Server-API nötig.
- **Nachteile:** Sehr anfällig für Layout-Änderungen; Rechner muss laufen und Locosoft erreichbar sein; Wartung bei jedem UI-Update; eher „Experiment“ als produktiver Dauerbetrieb.

### 5. Locosoft-Plugin / Skript im DMS

**Idee:** Falls Locosoft eine Erweiterungsschnittstelle hat (VBA, Lua, eigenes SDK, „Benutzerdefinierte Aktionen“): ein kleines Plugin/Skript **innerhalb** von Locosoft liest periodisch eine Datei oder eine URL (z. B. von DRIVE) und setzt die Preise über interne Locosoft-Funktionen.

- **Vorteile:** Kein externer Robot; nutzt die Logik des DMS.
- **Nachteile:** Ob so etwas existiert und ob Preise so setzbar sind, **muss Loco-Soft bestätigen**.

### 6. n8n / Low-Code-Workflow mit Browser-Automation

**Idee:** Workflow „Webhook/Datei mit VIN+Preis“ → n8n (oder vergleichbar) öffnet Locosoft im Browser, loggt ein, navigiert, füllt Felder. Entspricht RPA, nur mit Low-Code-Tool.

- **Vorteile:** Keine eigene Codebasis für den Robot; Anpassung oft ohne Entwickler.
- **Nachteile:** Gleiche Risiken wie bei (1): UI-Änderungen, Stabilität, Lizenzen/AGB.

---

## Empfehlung (Reihenfolge)

1. **Zuerst Loco-Soft fragen:** API, Import oder „offizieller“ Weg für Verkaufspreis – das bleibt die sauberste Lösung.
2. **Falls Import möglich:** Konzept „Datei erzeugen (DRIVE/eAutoSeller) + Import in Locosoft“ prüfen.
3. **Falls nur UI bleibt:** Robot/RPA als **Pilot** erwägen (z. B. ein Fahrzeug, eine Maske), mit klarem Abbruchkriterium wenn es zu instabil wird; Alternativ Halbautomatik (3) als pragmatische Verbesserung ohne Robot.
4. **Plugin/Skript in Locosoft (5)** nur, wenn Loco-Soft so etwas anbietet und dokumentiert.
