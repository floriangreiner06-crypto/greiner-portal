# Schritt-für-Schritt: IAM für Bedrock überprüfen

**Stand:** 2026-02-24  
**Ziel:** Sicherstellen, dass der IAM-Benutzer für Bedrock (Hilfe „Mit KI erweitern“ / Fahrzeugschein) korrekt konfiguriert ist.

---

## 1. In der AWS-Console anmelden

1. Browser öffnen, **AWS Console** aufrufen (z. B. https://console.aws.amazon.com).
2. Mit dem **Konto** anmelden, das auch für Bedrock/DRIVE genutzt wird (z. B. „Autohaus Greiner“).
3. Oben in der Suche **„IAM“** eingeben und **IAM** (Identity and Access Management) öffnen.

**Hinweis:** IAM ist global – die angezeigte Region (z. B. us-east-1) spielt für Benutzer und Richtlinien keine Rolle.

---

## 2. Richtigen Benutzer finden

1. Links im Menü **„Personen“** (Users) klicken.
2. In der Liste den Benutzer finden, der für Bedrock genutzt wird (bei euch: **drive-bedrock-user**).
3. Auf den **Benutzernamen** klicken, um die Detailseite zu öffnen.

**Prüfung:** Stimmt die **Zugriffsschlüssel-ID** (z. B. `AKIAUY6JRXA7...`) mit dem Eintrag in `config/credentials.json` unter `aws_bedrock` → `access_key_id` überein?  
(Die Key-ID steht auf der Benutzer-Detailseite unter „Sicherheitsanmeldeinformationen“ / „Zugriffsschlüssel“.)

---

## 3. Bedrock-Berechtigungen prüfen

1. Auf der Benutzer-Detailseite zum Reiter **„Berechtigungen“** (Permissions) wechseln.
2. Unter **„Berechtigungsrichtlinien“** prüfen:
   - Es sollte mindestens eine der folgenden Richtlinien angehängt sein:
     - **AmazonBedrockFullAccess** (AWS-verwaltet), oder
     - Eine eigene Richtlinie mit den Aktionen **bedrock:InvokeModel** und **bedrock:InvokeModelWithResponseStream**.

**Fazit:** Wenn **AmazonBedrockFullAccess** (oder eine Policy mit InvokeModel) vorhanden ist → Bedrock-Rechte sind gesetzt.  
Wenn nicht → **„Berechtigungen hinzufügen“** → **„Direkt Richtlinien anfügen“** → nach **AmazonBedrockFullAccess** suchen → anhängen → speichern.

---

## 4. Marketplace-Berechtigungen prüfen (wichtig für erste Nutzung)

Für die **erste** Nutzung von Claude (Marketplace-Modell) braucht der Benutzer zusätzlich **AWS-Marketplace-Rechte**, damit Bedrock das Modell für das Konto aktivieren kann.

1. Weiterhin auf der Benutzer-Detailseite unter **„Berechtigungen“** bleiben.
2. Prüfen, ob eine Richtlinie existiert, die folgende Aktionen erlaubt:
   - **aws-marketplace:Subscribe**
   - **aws-marketplace:Unsubscribe**
   - **aws-marketplace:ViewSubscriptions**

**Falls keine solche Richtlinie vorhanden ist:**

1. **„Berechtigungen hinzufügen“** klicken.
2. **„Richtlinie erstellen“** wählen (öffnet neuen Tab).
3. Bei **„Richtlinientyp“** die Option **„JSON“** auswählen.
4. Folgenden Inhalt einfügen:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:Subscribe",
                "aws-marketplace:Unsubscribe",
                "aws-marketplace:ViewSubscriptions"
            ],
            "Resource": "*"
        }
    ]
}
```

5. **„Nächste“** klicken.
6. **Richtlinienname** vergeben, z. B. **BedrockMarketplaceSubscribe**.
7. **„Richtlinie erstellen“** klicken.
8. Zurück zum Tab mit dem IAM-Benutzer wechseln, Seite ggf. aktualisieren.
9. Erneut **„Berechtigungen hinzufügen“** → die neu erstellte Richtlinie **BedrockMarketplaceSubscribe** suchen → anhängen → **„Berechtigungen hinzufügen“** bestätigen.

---

## 5. Zugriffsschlüssel prüfen

1. Auf der Benutzer-Detailseite zum Reiter **„Sicherheitsanmeldeinformationen“** (Security credentials) wechseln.
2. Unter **„Zugriffsschlüssel“** (Access keys) prüfen:
   - Es gibt mindestens einen Zugriffsschlüssel mit Status **„Aktiv“**.
   - Die **Zugriffsschlüssel-ID** (z. B. mit „AKIA…“ beginnend) notieren.

**Abgleich mit dem Server:**  
Auf dem DRIVE-Server muss in **config/credentials.json** unter **aws_bedrock** Folgendes stehen:

- **access_key_id:** muss exakt mit der Zugriffsschlüssel-ID aus IAM übereinstimmen.
- **secret_access_key:** der zum Key gehörende geheime Schlüssel (wird in IAM nicht nochmal angezeigt; nur beim Erstellen des Keys).
- **region:** **eu-central-1** (für Frankfurt / DSGVO).

Falls der Schlüssel in IAM neu erstellt wurde: Den **neuen** Secret Key einmalig in `credentials.json` eintragen; der alte Secret funktioniert dann nicht mehr.

---

## 6. Kurz-Check auf dem Server (optional)

Per SSH (z. B. PuTTY) auf den Server, dann im Projektordner:

```bash
cd /opt/greiner-portal
python3 -c "
import json
with open('config/credentials.json') as f:
    d = json.load(f)
b = d.get('aws_bedrock') or {}
print('region:', b.get('region'))
print('access_key_id (erste 12 Zeichen):', (b.get('access_key_id') or '')[:12] + '...')
print('secret_access_key gesetzt:', 'ja' if b.get('secret_access_key') else 'nein')
"
```

- **region** sollte **eu-central-1** sein.
- **access_key_id** muss mit der Key-ID von **drive-bedrock-user** in IAM übereinstimmen.
- **secret_access_key gesetzt: ja**.

---

## 7. Anthropic First-Time Use (FTU) prüfen

Für Claude-Modelle ist einmal pro Konto ein **Use-Case-Formular** nötig.

1. In der AWS-Console **„Amazon Bedrock“** öffnen (Suche: Bedrock).
2. Oben die **Region „Europa (Frankfurt)“ / eu-central-1** auswählen.
3. Links **„Modellkatalog“** (Model catalog) öffnen.
4. Nach **„Claude Sonnet 4.5“** suchen und die Karte anklicken.
5. Auf der Modell-Detailseite prüfen:
   - Wird **„Use case übermitteln“** / **„Nutzungsfall“** / **„First-time use“** angezeigt?  
     → Formular ausfüllen und absenden.
   - Steht dort **„In Playground öffnen“** ohne Hinweis auf Use Case?  
     → FTU wurde vermutlich schon erledigt.

---

## 8. Test nach der Überprüfung

1. Nach allen Änderungen 1–2 Minuten warten.
2. Auf dem DRIVE-Server ausführen:

```bash
cd /opt/greiner-portal && venv/bin/python scripts/test_bedrock_credentials.py
```

3. Wenn **„Erfolg. Antwort: …“** erscheint: IAM und Bedrock-Zugriff sind in Ordnung.
4. Im DRIVE-Portal **Hilfe → Verwaltung → Artikel bearbeiten → „Mit KI erweitern“** testen.

---

## Checkliste (Kurz)

| Schritt | Inhalt | Erledigt |
|--------|--------|----------|
| 1 | AWS Console → IAM öffnen | ☐ |
| 2 | Benutzer **drive-bedrock-user** öffnen, Key-ID prüfen | ☐ |
| 3 | Berechtigungen: **AmazonBedrockFullAccess** (oder InvokeModel) vorhanden | ☐ |
| 4 | Marketplace-Policy (Subscribe/Unsubscribe/ViewSubscriptions) angehängt | ☐ |
| 5 | Zugriffsschlüssel aktiv; Key-ID = access_key_id in credentials.json | ☐ |
| 6 | Server: credentials.json mit region eu-central-1, secret gesetzt | ☐ |
| 7 | Bedrock → Modellkatalog → Claude Sonnet 4.5: FTU/Use Case ggf. abgeschickt | ☐ |
| 8 | test_bedrock_credentials.py ausführen → Erfolg | ☐ |
