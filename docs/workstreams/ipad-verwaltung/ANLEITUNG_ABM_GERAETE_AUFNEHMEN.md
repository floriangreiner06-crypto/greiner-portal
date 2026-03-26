# Anleitung: iPads in Apple Business Manager (ABM) aufnehmen

**Stand:** 2026-03-18  
**Ziel:** Die 15 Mechaniker-iPads (und künftige Geräte) in eurem ABM-Account erfassen, damit sie später dem MDM (z. B. Mosyle) zugewiesen werden können.

---

## Ich habe nur einen Windows-PC – wo ist die App?

**Apple Configurator 2** gibt es **nur für den Mac** – es gibt **keine Windows-Version**.

**Ihre Optionen:**

| Option | Was Sie brauchen | Wo / wie |
|--------|------------------|----------|
| **A: Apple Configurator (iPhone/iPad)** | Ein **iPhone** oder **iPad** (iOS 16+) mit der App **„Apple Configurator“** | **App Store** (iPhone/iPad) → nach **„Apple Configurator“** suchen → installieren. Damit können Sie andere iPhones/iPads **ohne Mac** zu ABM hinzufügen (siehe Methode 2 unten). |
| **B: Mac nutzen** | Einen Mac (Firma, Kollege, kurz ausleihen) | Auf dem Mac: **Mac App Store** → **„Apple Configurator 2“** suchen und installieren (Methode 1). |
| **C: Manuell in ABM** | Nur Browser + Seriennummern | [business.apple.com](https://business.apple.com) → Geräte → „Geräte hinzufügen“ → Seriennummern eintragen. Funktioniert bei vielen bereits genutzten iPads nicht zuverlässig (siehe Methode 3). |

---

## Voraussetzungen

- **Apple Business Manager** ist eingerichtet und von Apple verifiziert (habt ihr bereits).
- **Methode mit Mac:** Ein **Mac** mit **Apple Configurator 2** (kostenlos im **Mac App Store**), **USB-Kabel** (Lightning oder USB-C je nach iPad).
- **Methode ohne Mac:** Ein **iPhone** oder **iPad** (iOS 16 oder neuer) mit der App **„Apple Configurator“** aus dem **App Store**.
- **Optional:** Seriennummern der iPads (für manuelle Aufnahme oder Checkliste).

**Wichtig:** Beim Hinzufügen zu ABM (mit Configurator 2 oder mit der iPhone-App) wird das iPad **auf Werkseinstellungen zurückgesetzt**. Vorher prüfen, ob Daten gesichert werden müssen.

---

## Methode 1: Aufnahme mit Apple Configurator 2 (Mac) – empfohlen für bestehende iPads

Diese Methode ist für **bereits genutzte iPads** der zuverlässigste Weg. Das Gerät erscheint danach in ABM und kann einem MDM zugewiesen werden.

### Schritt 1: Apple Configurator 2 installieren und anmelden

1. Auf dem Mac den **Mac App Store** öffnen und **„Apple Configurator 2“** suchen und installieren (kostenlos).
2. **Apple Configurator 2** starten.
3. Menü **„Apple Configurator 2“** → **„Einstellungen“** (oder **„Preferences“**).
4. Unter **„Organisationen“** (bzw. **„Organizations“**) auf **„+“** klicken und mit der **Apple-ID** anmelden, die euren **Apple Business Manager** verwaltet (oder die mit ABM verknüpft ist). So verbindet sich Configurator mit eurem ABM-Account.

### Schritt 2: iPad vorbereiten (Backup optional)

1. **Daten sichern**, falls nötig (iCloud, iTunes/Finder-Backup oder manuell).
2. iPad per **USB** mit dem Mac verbinden.
3. Wenn das iPad entsperrt ist und dem Mac vertraut, erscheint es in Apple Configurator 2 in der Geräteliste.

### Schritt 3: iPad zu Apple Business Manager hinzufügen

1. In Apple Configurator 2 das **verbundene iPad** in der Liste auswählen (einzelnes Gerät anklicken).
2. Menü **„Aktion“** (bzw. **„Action“**) → **„Zu Apple Business Manager hinzufügen“** (bzw. **„Add to Apple Business Manager“**).
   - Alternativ: **Rechtsklick** auf das Gerät → **„Zu Apple Business Manager hinzufügen“**.
3. Im Dialog **mit der Apple-ID anmelden**, die zu eurem **Apple Business Manager** gehört (falls noch nicht in Schritt 1 erledigt).
4. Bestätigen. Der Vorgang **setzt das iPad zurück** und registriert es bei Apple; die **Seriennummer** wird eurer ABM-Organisation zugeordnet.
5. Warten, bis der Vorgang abgeschlossen ist. Das iPad startet neu und zeigt den **Einrichtungsassistenten** („Hallo“).
6. **iPad nicht vollständig einrichten** – sobald Mosyle (oder ein anderes MDM) verbunden ist, könnt ihr die Geräte dem MDM zuweisen; neue Geräte aus ABM werden dann beim ersten Einschalten automatisch vom MDM erfasst (Zero Touch).

### Schritt 4: Prüfen in ABM

1. Im Browser ** [business.apple.com](https://business.apple.com)** öffnen und anmelden.
2. **„Geräte“** (bzw. **„Devices“**) aufrufen.
3. Das iPad sollte in der Liste erscheinen (erkennbar an Seriennummer, Modell, ggf. „Wartet auf Zuweisung“).

### Wiederholen für alle 15 iPads

- Jedes iPad **einzeln** per USB verbinden und den Vorgang (Schritt 2–3) durchführen.
- Optional: Liste mit Seriennummern führen, um in ABM zu prüfen, dass alle 15 erfasst sind.

---

## Methode 2: Aufnahme mit Apple Configurator (iPhone oder iPad) – ohne Mac

Wenn Sie **keinen Mac** haben, können Sie ein **iPhone** oder **iPad** mit der App **„Apple Configurator“** nutzen. Die App gibt es **nur im App Store für iOS** (nicht für Windows).

### Voraussetzungen

- **iPhone oder iPad** mit **iOS 16 oder neuer**.
- Die **Apple-ID** auf diesem Gerät muss **Administrator** in eurem Apple Business Manager sein (oder Sie melden sich in der App mit dieser Apple-ID an).
- Das **zu registrierende iPad** wird **zurückgesetzt** – vorher Daten sichern.

### Wo finde ich die App?

- Auf dem **iPhone** oder **iPad** den **App Store** öffnen.
- Nach **„Apple Configurator“** suchen (Hersteller: Apple).
- App **installieren** (kostenlos).

### Ablauf (pro iPad)

1. **Zu registrierendes iPad zurücksetzen:** Einstellungen → Allgemein → „Übertragen oder iPad zurücksetzen“ → „Alle Inhalte und Einstellungen löschen“. Oder über einen Mac/PC mit Finder/iTunes (falls vorhanden). Das iPad startet neu und zeigt den Einrichtungsassistenten („Hallo“).
2. Auf dem iPad **bis zum Bildschirm „WLAN auswählen“** gehen und **dort anhalten** (noch kein WLAN wählen).
3. **iPhone/iPad mit der App „Apple Configurator“** zur Hand nehmen, App öffnen und mit der **ABM-Administrator-Apple-ID** anmelden.
4. **Beide Geräte nah beieinander** halten. Auf dem zu registrierenden iPad erscheint eine Meldung zur **Kopplung**; auf dem Gerät mit Apple Configurator erscheint die Aufforderung, das andere Gerät zu ABM hinzuzufügen.
5. Vorgang bestätigen und abwarten. Das iPad wird eurem Apple Business Manager zugeordnet.
6. In **[business.apple.com](https://business.apple.com)** unter **Geräte** prüfen, ob das iPad erscheint.

Für jedes weitere iPad: iPad zurücksetzen → bis „WLAN auswählen“ → mit Apple Configurator auf dem iPhone/iPad koppeln und zu ABM hinzufügen.

---

## Methode 3: Manuell in ABM eintragen (nur Seriennummer) – oft nicht verfügbar

In vielen Apple-Business-Manager-Accounts gibt es **keinen** Menüpunkt „Geräte hinzufügen“ oder ein Feld für Seriennummern. Auf der Seite **Geräte** steht dann nur das Formular für **Apple-Kundennummer** bzw. **Händlernummer** („Hinzufügen“ bezieht sich nur auf diese Nummer, nicht auf einzelne Geräte).

Falls in eurem ABM unter **Geräte** dennoch eine Option **„Geräte hinzufügen“** / **„Add devices“** existiert (z. B. nach Klick auf ein Plus-Symbol oder in einem Untermenü), könnt ihr dort Seriennummern eintragen. Sonst gilt: **Bestehende iPads nur über Apple Configurator** (Methode 1 oder 2) in ABM aufnehmen – danach erscheinen sie auf derselben Geräte-Seite und können dem MDM zugewiesen werden.

**Wichtig:** Geräte können **nicht** per WLAN „gegrabbt“ oder automatisch erkannt werden. Jedes iPad muss einzeln per Configurator (USB oder iPhone-App) erfasst werden, sofern kein Seriennummer-Feld angeboten wird.

---

## Künftige Geräte (Neukauf)

Damit **neu gekaufte** iPads automatisch in eurem ABM landen:

- Beim **Kauf** (Apple, autorisierter Händler, Business-Partner) eure **ABM-Organisations-ID** und ggf. die **Kundennummer** angeben.
- Die Geräte werden dann bei der ersten Aktivierung eurer Organisation zugeordnet und erscheinen in ABM – **ohne** manuelles Hinzufügen per Configurator.

Die **Organisations-ID** findet ihr in ABM unter **Einstellungen** (bzw. **„Account“** / **„Organization“**) → **„Informationen zur Organisation“**.

---

## Kurz-Checkliste: 15 iPads in ABM

- [ ] **Mit Mac:** Apple Configurator 2 installiert (Mac App Store) und mit ABM-Apple-ID verbunden; USB-Kabel bereit. **Ohne Mac:** App „Apple Configurator“ auf iPhone/iPad installieren (App Store, iOS 16+)
- [ ] Pro iPad: Backup erledigt (falls nötig)
- [ ] Pro iPad: Verbinden → „Zu Apple Business Manager hinzufügen“ → Reset abwarten
- [ ] In business.apple.com unter „Geräte“ prüfen, dass alle 15 erscheinen
- [ ] Nach Mosyle-Freischaltung: In ABM die Geräte dem Mosyle-MDM zuweisen (siehe NACHSTES_NACH_ABM_EINRICHTUNG.md)

---

## Häufige Fragen

**Das iPad wird nach dem Hinzufügen nicht in ABM angezeigt.**  
- Einige Minuten warten und ABM-Seite aktualisieren.  
- Prüfen, dass ihr mit der gleichen Apple-ID angemeldet wart, die mit eurem ABM-Account verknüpft ist.

**Kann ich mehrere iPads gleichzeitig verbinden?**  
- Apple Configurator 2 kann mehrere Geräte anzeigen; das „Zu ABM hinzufügen“ wird aber typischerweise **pro Gerät** ausgeführt. Nacheinander abarbeiten ist übersichtlich.

**iPad ist schon im Einsatz – gehen Daten verloren?**  
- Ja. „Zu Apple Business Manager hinzufügen“ setzt das Gerät zurück. Vorher sichern, danach das iPad neu einrichten (oder über MDM bereitstellen).

**Wo ist die Seriennummer?**  
- Am Gerät (feine Aufschrift) oder auf dem iPad: **Einstellungen** → **Allgemein** → **Info** → **Seriennummer**.

---

Nach der Aufnahme aller Geräte in ABM: Sobald Mosyle freigeschaltet ist, in ABM unter **„MDM-Server“** Mosyle hinzufügen und die Geräte dem MDM zuweisen. Siehe **NACHSTES_NACH_ABM_EINRICHTUNG.md** (Schritt 2).
