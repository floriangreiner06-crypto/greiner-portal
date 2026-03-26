# Gudat API – Schritt für Schritt am DRIVE-Server (PuTTY)

**Für dich:** Du bist per PuTTY am DRIVE-Server eingeloggt. Folge diese Schritte nacheinander.

---

## Vorbereitung: Werte bereithalten

Bevor du anfängst, habe bereit (aus der Gudat-Datei und den E-Mails):

- **Client ID Deggendorf**
- **Client Secret Deggendorf**
- **Passwort für Deggendorf** (admin@opel-greiner.de, von Gudat per E-Mail)
- **Client ID Landau**
- **Client Secret Landau**
- **Passwort für Landau** (admin@auto-greiner.de, von Gudat per E-Mail)

---

## Schritt 1: Ins Projektverzeichnis wechseln

In PuTTY eingeben (Enter drücken):

```bash
cd /opt/greiner-portal
```

---

## Schritt 2: Backup der credentials.json anlegen

```bash
cp config/credentials.json config/credentials.json.bak.$(date +%Y%m%d)
```

Damit hast du ein Backup mit heutigem Datum, falls etwas schiefgeht.

---

## Schritt 3: Datei im Editor öffnen

```bash
nano config/credentials.json
```

Die Datei öffnet sich. Du siehst den JSON-Inhalt.

---

## Schritt 4: Zum Gudat-Block gehen

- **In nano:** Drücke **Strg+W** (Suchen), tippe: **gudat** und Enter.
- Der Cursor springt zu „gudat“. Gehe mit den **Pfeiltasten** in die Zeile mit **"notes": "Kapazität..."** (die letzte Zeile im gudat-Block vor der schließenden Klammer **}** ).

Die Zeile sieht ungefähr so aus:

```text
      "notes": "Kapazitätsplanung, Werkstatt-Auslastung, Team-Status"
    },
```

Du musst **hinter dem Anführungszeichen** von `Team-Status"` ein **Komma** einfügen und danach die neuen Zeilen.

---

## Schritt 5: Komma und neue Zeilen einfügen

1. Cursor **hinter** das letzte **"** von `Team-Status"` setzen.
2. **Komma** eintippen: **,**
3. **Enter** für eine neue Zeile.
4. Folgenden Block **exakt** eintippen (die Platzhalter ersetzt du in Schritt 6):

```json
      "api_base_url": "https://api.werkstattplanung.net/da/v1",
      "group": "greiner",
      "centers": {
        "deggendorf": {
          "client_id": "DEINE_CLIENT_ID_DEGGENDORF",
          "client_secret": "DEIN_CLIENT_SECRET_DEGGENDORF",
          "username": "admin@opel-greiner.de",
          "password": "DEIN_PASSWORT_DEGGENDORF"
        },
        "landau": {
          "client_id": "DEINE_CLIENT_ID_LANDAU",
          "client_secret": "DEIN_CLIENT_SECRET_LANDAU",
          "username": "admin@auto-greiner.de",
          "password": "DEIN_PASSWORT_LANDAU"
        }
      }
```

Wichtig:
- Vor **"api_base_url"** keine Komma-Zeile vergessen (du hast ja schon ein Komma nach `Team-Status"` gesetzt).
- Einrückung: gleiche Anzahl Leerzeichen wie die Zeile mit `"notes"` (z. B. 6 Leerzeichen am Zeilenanfang).
- Alle Anführungszeichen **doppelt** (") – keine typografischen “.

---

## Schritt 6: Platzhalter ersetzen

Ersetze in der Datei (mit den Pfeiltasten und Löschen/Einfügen):

| Platzhalter | Ersetzen durch |
|-------------|----------------|
| DEINE_CLIENT_ID_DEGGENDORF | Die echte Client ID für Deggendorf aus der Gudat-Datei |
| DEIN_CLIENT_SECRET_DEGGENDORF | Das echte Client Secret für Deggendorf |
| DEIN_PASSWORT_DEGGENDORF | Das Passwort aus der E-Mail von Gudat für Deggendorf (admin@opel-greiner.de) |
| DEINE_CLIENT_ID_LANDAU | Die echte Client ID für Landau aus der Gudat-Datei |
| DEIN_CLIENT_SECRET_LANDAU | Das echte Client Secret für Landau |
| DEIN_PASSWORT_LANDAU | Das Passwort aus der E-Mail von Gudat für Landau (admin@auto-greiner.de) |

---

## Schritt 7: Prüfen, ob das JSON gültig ist

- Jede geöffnete **{** muss mit **}** geschlossen sein.
- Zwischen allen Einträgen auf gleicher Ebene steht ein **Komma** (außer vor **}** oder **]**).
- Kein Komma nach dem letzten Eintrag vor **}** im Block **centers** und **gudat**.

Der gudat-Block endet danach so (Beispiel, ohne echte Geheimnisse):

```text
    "gudat": {
      "description": "...",
      "portal_url": "...",
      "username": "florian.greiner@auto-greiner.de",
      "password": "Hyundai2025!",
      "api_endpoints": { ... },
      "notes": "Kapazitätsplanung, ...",
      "api_base_url": "https://api.werkstattplanung.net/da/v1",
      "group": "greiner",
      "centers": {
        "deggendorf": { ... },
        "landau": { ... }
      }
    },
```

---

## Schritt 8: Speichern und nano beenden

- **Strg+O** (O wie Oben) → Enter (Speichern).
- **Strg+X** (nano beenden).

Du bist wieder in der Shell.

---

## Schritt 9: JSON-Syntax prüfen (optional)

Damit du siehst, ob die Datei gültiges JSON ist:

```bash
python3 -c "import json; json.load(open('config/credentials.json')); print('OK – JSON ist gültig')"
```

Wenn **OK – JSON ist gültig** erscheint, ist die Syntax in Ordnung.  
Wenn eine Fehlermeldung kommt: wieder `nano config/credentials.json` öffnen und Kommas/Klammern prüfen.

---

## Schritt 10: Berechtigung der Datei (optional)

Nur der Benutzer soll die Datei lesen können:

```bash
chmod 600 config/credentials.json
```

---

## Schritt 11: Portal testen (KIC)

Die bestehenden Gudat-Funktionen (Werkstatt Live, Kapazität) nutzen weiter **username** und **password** aus der oberen Ebene von **gudat** (derzeit florian.greiner@… / Hyundai2025!).  

Wenn du das **nicht** geändert hast, musst du nichts neu starten.  
Wenn du **doch** auf die neuen API-User umgestellt hast: Portal neu starten:

```bash
sudo systemctl restart greiner-portal
```

Dann im Browser **Werkstatt Live** oder **Kapazitätsplanung** aufrufen und prüfen, ob Daten kommen.

---

## Kurz-Checkliste

- [ ] PuTTY: `cd /opt/greiner-portal`
- [ ] Backup: `cp config/credentials.json config/credentials.json.bak.$(date +%Y%m%d)`
- [ ] `nano config/credentials.json` → zu „gudat“ / „notes“ gehen
- [ ] Komma nach `Team-Status"` + neue Zeilen (api_base_url, group, centers) einfügen
- [ ] Platzhalter durch echte Client IDs, Secrets und Passwörter ersetzen
- [ ] Strg+O, Enter, Strg+X
- [ ] Optional: `python3 -c "import json; json.load(open('config/credentials.json')); print('OK')"`
- [ ] Optional: `chmod 600 config/credentials.json`
- [ ] **Nicht** committen – credentials.json steht in .gitignore

Fertig. Die OAuth-API (api.werkstattplanung.net) nutzt diese Einträge, sobald der Code dafür eingebaut ist; die Konfiguration ist dann schon da.
