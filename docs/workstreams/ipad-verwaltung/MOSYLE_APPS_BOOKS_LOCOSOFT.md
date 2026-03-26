# Mosyle: Apps-&-Bücher (VPP) verbinden und Locosoft mit ausrollen

**Stand:** 2026-03-18  
**Kontext:** In Mosyle einen „Apps and Books“-Account anlegen, damit Apps (z. B. Locosoft) automatisch auf die verwalteten iPads installiert werden können.

---

## 1. Token aus Apple Business Manager holen

Ohne diesen Token kann Mosyle keine Apps aus eurem ABM-Account beziehen.

1. Bei **[business.apple.com](https://business.apple.com)** anmelden (als Administrator oder Content Manager).
2. **Unten in der linken Sidebar** auf **euren Namen** (oder das Organisations-Symbol) klicken.
3. **„Einstellungen“** / **„Preferences“** öffnen.
4. Zu **„Zahlungen & Abrechnung“** / **„Payments & Billing“** gehen.
5. Unter **„Content-Token“** / **„Content Tokens“** den passenden Token auswählen (oder einen neuen erstellen, falls noch keiner für Mosyle existiert).
6. **Token herunterladen** – es wird eine Datei (z. B. `.vpptoken` oder ähnlich) angeboten. Speichern.

**Hinweis:** Der Token ist in der Regel **1 Jahr** gültig; rechtzeitig vor Ablauf in ABM erneuern und in Mosyle neu hochladen.

### Wenn Sie „Zahlungen & Abrechnung“ nicht sehen

In manchen Ansichten oder Sprachen heißt der Bereich anders oder liegt woanders:

1. **Nach dem Klick auf Ihren Namen (unten links):** In der **mittleren Spalte** nach einem Eintrag wie **„Einstellungen“**, **„Preferences“** oder **„Organisationseinstellungen“** schauen – darunter kann **„Zahlungen & Abrechnung“** / **„Payments & Billing“** liegen.
2. **„Apps und Bücher“ (linke Sidebar):** Einmal **„Apps und Bücher“** öffnen. Oft gibt es dort **Einstellungen** oder **Standort** auswählen; unter **Konto** / **Account** oder bei den Standort-Details kann der **Content-Token** zum Herunterladen angeboten werden.
3. **Rolle prüfen:** Nur Nutzer mit der Rolle **Administrator** oder **Content Manager** sehen die Token-Verwaltung. Sonst einen Admin bitten, den Token herunterzuladen.
4. **Englische Oberfläche:** Falls die Sprache umstellbar ist, kurz auf **Englisch** wechseln – dann nach **„Preferences“** → **„Payments & Billing“** suchen (unten unter Content Tokens).

---

## 2. Token in Mosyle hochladen

1. In Mosyle im Dialog **„Add account“** (Apps and Books / VPP) bleiben.
2. **Account name** ist schon ausgefüllt (z. B. „Autohaus Greiner GmbH Co. KG“).
3. Unten auf **„Select file“** klicken und die **heruntergeladene Token-Datei** (.vpptoken) auswählen.
4. Speichern / Account anlegen. Mosyle verbindet sich damit mit eurem Apple Apps-&-Bücher-Account.

---

## 3. Locosoft-App in Apple Business Manager besorgen

Damit Mosyle Locosoft installieren kann, muss die App in eurem **Apple Business Manager** (Apps und Bücher) verfügbar sein.

- **Falls Locosoft im App Store ist:**  
  In ABM unter **„Apps und Bücher“** / **„Apps and Books“** die App suchen und **„Kaufen“** bzw. **Lizenzen hinzufügen** (bei kostenlosen Apps trotzdem „Kaufen“/Hinzufügen, um Lizenzen zu erhalten).
- **Falls Locosoft eine B2B-/Custom-App ist:**  
  Der Anbieter muss euch die App in ABM bereitstellen (über Apple Business Manager / App Store Connect). Danach erscheint sie unter „Apps und Bücher“.

Ohne Lizenzen in ABM kann Mosyle die App nicht zuweisen.

---

## 4. In Mosyle: App zuweisen und bei automatischer Geräte-Registrierung vorbelegen (optional)

- Unter **Apps** / **„Apps and Books“** in Mosyle die **Locosoft-App** auswählen (sie erscheint nach Token-Sync aus ABM).
- Die App einem **Profil** oder **Gerätegruppe** zuweisen (z. B. „Mechaniker-iPads“), damit sie automatisch installiert wird.

**„Pre-Assign App Licenses for Automated Device Enrollment“:**  
Wenn ihr das auf **YES** stehen habt, könnt ihr unten **„Select the Automated Device Enrollment Profiles“** nutzen und die **Profile** auswählen, für die Lizenzen vorab zugewiesen werden. Dann werden Geräte, die mit diesem Profil registriert werden, direkt die Locosoft-Lizenz erhalten. Dafür müssen zuerst **Automated Device Enrollment-Profile** in Mosyle angelegt sein (ABM-Anbindung + Gerätezuweisung).

---

## Kurz-Checkliste

- [ ] In ABM: **Preferences** → **Payments & Billing** → **Content Token** herunterladen
- [ ] In Mosyle: Token-Datei unter **„Select file“** hochladen und Account speichern
- [ ] In ABM: Unter **Apps und Bücher** Locosoft suchen und Lizenzen hinzufügen (falls noch nicht geschehen)
- [ ] In Mosyle: Locosoft-App dem gewünschten Profil / der Gerätegruppe zuweisen (und ggf. Pre-Assign-Profile auswählen)

Danach werden neue bzw. verwaltete iPads die Locosoft-App automatisch erhalten, sobald sie dem richtigen Profil zugeordnet sind.

---

## E-Mail-Konto für den User auf dem iPad einrichten (Mosyle)

**Ja** – Mosyle kann das E-Mail-Konto des Users auf dem iPad konfigurieren. Dafür legt ihr ein **Konfigurationsprofil** mit dem **E-Mail-Payload** (Apple MDM) an.

- **Exchange / Microsoft 365:** Profil mit **Exchange ActiveSync** (Server, E-Mail-Adresse, ggf. OAuth/Zertifikat). Der User muss ggf. einmal das Passwort eingeben oder wird per SSO angemeldet.
- **IMAP/POP:** Profil mit **E-Mail-Account** (Posteingang/Postausgang Server, Port, SSL, Benutzername). Passwort oft beim ersten Öffnen der Mail-App abfragen oder per Variablen (z. B. %email%) ergänzen.

**In Mosyle:** Unter **Konfigurationen** / **Configuration Profiles** (oder **Policies**) ein neues Profil für **iOS/iPadOS** anlegen und die Sektion **„E-Mail“** / **„Email Account“** bzw. **„Exchange“** ausfüllen (Server, Account-Name, Authentifizierung). Profil der Gerätegruppe oder dem Enrollment-Profil zuweisen – dann wird das Konto auf dem iPad eingerichtet.

**Hinweis:** Das Passwort kann je nach Mosyle-Version und Auth-Methode vom User beim ersten Öffnen eingegeben werden müssen (Sicherheit). Bei Exchange/O365 oft modernere Auth (OAuth) möglich.

---

## Locosoft später nachziehen

Ihr könnt die Geräte zuerst **ohne** Apps-&-Bücher-Token einrichten und Locosoft **später** hinzufügen: Sobald die Steuerverifizierung in ABM durch ist und ihr den Token in Mosyle hochgeladen habt, weist ihr die Locosoft-App dem bestehenden Profil bzw. der Gerätegruppe zu – dann wird sie auf die bereits registrierten iPads gepusht (oder bei der nächsten Sync-/Check-in-Aktion installiert).
