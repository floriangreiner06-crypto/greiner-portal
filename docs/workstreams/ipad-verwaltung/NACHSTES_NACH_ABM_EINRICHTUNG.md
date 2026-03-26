# Nächste Schritte nach Apple Business Manager (ABM)-Einrichtung

**Stand:** 2026-03-18  
**Voraussetzung:** ABM-Account ist eingerichtet und von Apple verifiziert.

---

## Während Mosyle-Review (aktuell)

Ihr habt euch bei **Mosyle Business** registriert; der Account steht auf **„In Review“**. Das ist üblich – Mosyle prüft neue Business-Accounts manuell.

- **Was tun:** E-Mail posteingang prüfen (Aktivierungs-Link von Mosyle). Status prüfen: [mybusiness.mosyle.com/signup/status/…](https://mybusiness.mosyle.com) (oder den Link aus der Bestätigungsmail).
- **Falls Fragen:** „Send Us a Message“ auf der Statusseite nutzen.
- **In der Wartezeit:** Phase 2 vorbereiten – die 15 iPads in ABM aufnehmen (Apple Configurator oder Seriennummern), damit sie nach Mosyle-Freischaltung sofort dem MDM zugewiesen werden können.

---

## Überblick: Was als Nächstes?

1. **Bestehende 15 iPads in ABM aufnehmen** (Phase 2)
2. **MDM wählen und an ABM anbinden** (Phase 3) – empfohlen: Cloud-MDM (z. B. Jamf Now, Mosyle)
3. **Optional:** In DRIVE einen Navi-Punkt „iPad-Verwaltung“ mit Link zu ABM + MDM anlegen

---

## Schritt 1: Bestehende iPads in ABM aufnehmen

Ihr habt zwei Wege:

### Variante A: Über Apple Configurator (Mac nötig)

- **App:** „Apple Configurator“ aus dem Mac App Store (kostenlos).
- **Ablauf pro iPad:** iPad per USB mit dem Mac verbinden → Apple Configurator öffnen → Gerät auswählen → **„Zu Apple Business Manager hinzufügen“** (bzw. „Add to Apple Business Manager“). Das iPad wird dabei zurückgesetzt und erscheint danach in eurem ABM-Account.
- **Hinweis:** Vorher prüfen, ob Daten auf den iPads gesichert werden müssen; das Hinzufügen zu ABM setzt das Gerät auf Werkseinstellungen.

### Variante B: Seriennummern in ABM eintragen (ohne Reset)

- In **business.apple.com** → **Geräte** → Geräte manuell hinzufügen (per Seriennummer).
- Nicht alle Geräte lassen sich so nachträglich „erfassen“ – bei vielen bereits genutzten iPads ist **Apple Configurator** der zuverlässige Weg, damit sie in ABM erscheinen und später einem MDM zugewiesen werden können.

**Empfehlung:** Einmalig die 15 iPads nacheinander per Apple Configurator durchgehen (mit Mac und USB). Danach sind alle in ABM und bereit für ein MDM.

---

## Schritt 2: MDM-Anbieter wählen und an ABM anbinden

Ohne MDM habt ihr in ABM nur Übersicht und zentrale App-Käufe – **keine** Konfigurations-Profile, kein Remote Lock/Wipe, keine automatische Einrichtung.

**Empfehlung für 15 Geräte:** **Cloud-MDM** (Option B aus dem Vorschlag):

| Anbieter    | Besonderheit                          | Nächster Schritt |
|------------|----------------------------------------|-------------------|
| **Jamf Now** | Für kleine Teams (&lt; 25 Geräte), einfach | [jamf.com](https://www.jamf.com/de/produkte/jamf-now/) – Testversion anfordern, dann in ABM unter „MDM-Server“ den MDM-Anbieter hinzufügen und mit Jamf verbinden. |
| **Mosyle** | Oft günstig / kostenlos bis 30 Geräte   | [mosyle.com](https://mosyle.com) – Account anlegen, Anleitung zur ABM-Anbindung folgen. |

**Ablauf in grob:**

1. Beim MDM-Anbieter (z. B. Jamf Now oder Mosyle) Account anlegen / Test starten.
2. In **ABM** unter **Einstellungen** → **MDM-Server** den neuen MDM-Server hinzufügen (der Anbieter liefert euch die nötigen Daten / eine Anleitung).
3. In ABM die **Geräte** dem neuen MDM zuweisen (einzeln oder in Gruppe).
4. Im MDM **Profile** anlegen (z. B. WLAN, Sicherheit, erlaubte Apps) und auf die Geräte ausrollen.

Danach könnt ihr neue oder zurückgesetzte iPads automatisch ins MDM bringen (Zero Touch), sofern sie in ABM sind und dem MDM zugewiesen wurden.

---

## Schritt 3: Optional – DRIVE als zentraler Einstieg

Im Portal DRIVE könnt ihr:

- Einen **Menüpunkt „iPad-Verwaltung“** anlegen (z. B. unter Admin oder Werkstatt), der auf **business.apple.com** und euren **MDM-Dashboard** verlinkt, plus eine kurze interne Anleitung.
- **Optional:** Eine einfache **Geräteliste** (welches iPad hat welcher Mechaniker?) in DRIVE pflegen – entweder manuell in einer kleinen Tabelle oder später per API vom MDM.

Das ersetzt nicht ABM/MDM, gibt aber einen zentralen Einstieg für alle Berechtigten.

---

## Kurz-Checkliste „Weiter nach ABM“

- [ ] **Phase 2:** Bestehende 15 iPads in ABM aufnehmen (Apple Configurator am Mac oder manuell per Seriennummer, siehe Schritt 1).
- [ ] **Phase 3:** MDM-Anbieter gewählt (z. B. Jamf Now oder Mosyle), Account angelegt.
- [ ] In ABM den MDM-Server eingetragen und Geräte dem MDM zugewiesen.
- [ ] Im MDM erste Profile angelegt und auf Test-iPads ausgerollt.
- [ ] **Optional:** In DRIVE Navi-Punkt „iPad-Verwaltung“ mit Links zu ABM + MDM anlegen (kann ich bei Bedarf konkret ausarbeiten).

Wenn du willst, können wir als Nächstes z. B. die **DRIVE-Navigation** für „iPad-Verwaltung“ konkret bauen (Migration + Route + Template mit Links).
