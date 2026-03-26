# Bedrock: Dauerhafter, sicherer und DSGVO-konformer Zugriff

**Stand:** 2026-02-24  
**Workstream:** Hilfe / Fahrzeugschein

---

## Ziel

- **Dauerhaft:** Kein „nur zu Testzwecken“ (kein langfristiger API-Schlüssel).
- **Sicher:** Keine langlebigen API-Keys; Nutzung von IAM oder kurzfristigen Tokens mit automatischer Erneuerung.
- **DSGVO-konform:** Verarbeitung in **eu-central-1** (Frankfurt), keine Abweichung.

---

## Empfohlene Lösung: IAM (ohne API-Schlüssel)

Der **normale und von AWS empfohlene** Weg für Produktion ist **IAM** (Access Key + Secret eines IAM-Benutzers oder einer Rolle). Kein Bedrock-API-Schlüssel nötig.

- **Region:** `eu-central-1` in `config/credentials.json` → Daten bleiben in der EU (DSGVO).
- **Credentials:** Ein IAM-Benutzer (z. B. `drive-bedrock-user`) mit den nötigen Rechten; Keys in `credentials.json`, nicht in Git.
- **Rotation:** Keys nur bei Bedarf rotieren (neuer Key anlegen, eintragen, alten deaktivieren).

---

## Warum „Access not allowed“ trotz IAM?

Laut AWS-Dokumentation können zwei Dinge fehlen:

### 1. AWS-Marketplace-Rechte (für erste Nutzung)

Beim **ersten** Aufruf eines Marketplace-Modells (z. B. Claude) versucht Bedrock, das Modell für das Konto zu aktivieren. Dafür braucht die **aufrufende IAM-Identität** temporär **Marketplace-Rechte**:

- `aws-marketplace:Subscribe`
- `aws-marketplace:Unsubscribe`
- `aws-marketplace:ViewSubscriptions`

**Nach** der einmaligen Aktivierung können alle Identitäten im Konto das Modell nutzen; dann reichen normale Bedrock-Rechte (z. B. `bedrock:InvokeModel`).  
Wenn der erste Aufruf von einem IAM-Benutzer **ohne** diese Marketplace-Rechte kam, kann die Aktivierung fehlschlagen und danach „Access not allowed“ zurückkommen.

**Maßnahme:** Dem IAM-Benutzer `drive-bedrock-user` eine Policy mit diesen drei Aktionen anhängen (z. B. verwaltete Policy **`AWSMarketplaceReadOnlyAccess`** enthält sie nicht; es braucht eine **eigene Inline-Policy** oder eine passende verwaltete Policy mit Marketplace-Subscribe-Rechten). Beispiel-Minimalpolicy:

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

Name z. B. `BedrockMarketplaceSubscribe`. Einmal anhängen, dann **einmal** „Mit KI erweitern“ oder das Test-Skript ausführen. Wenn das Modell danach aktiviert ist, könnt ihr diese Policy wieder entfernen (optional; behalten schadet nicht).

### 2. Anthropic First-Time-Use (FTU) / Use-Case

Für **Anthropic (Claude)** ist einmalig pro Konto das **FTU-Formular** (Use-Case) nötig. Ohne das kann der API-Zugriff blockiert bleiben.

**Maßnahme:**

- In der **Bedrock-Console** (eu-central-1) → **Modellkatalog** → **Claude Sonnet 4.5** öffnen.
- Prüfen, ob ein Hinweis auf **„Use case“** / **„Nutzungsfall übermitteln“** / **„First-time use“** erscheint.
- Falls ja: Formular ausfüllen und absenden (einmal pro Konto). Danach ist der Zugriff „sofort“ freigegeben.
- Alternativ kann ein Admin die **PutUseCaseForModelAccess**-API (mit passenden Rechten) aufrufen.

---

## Konkrete Schritte (Reihenfolge)

1. **Marketplace-Policy** wie oben an `drive-bedrock-user` hängen.
2. **FTU/Use-Case** in der Bedrock-Console (eu-central-1) für Claude prüfen und ggf. absenden.
3. **Einmal** Aufruf vom Server: z. B. `venv/bin/python scripts/test_bedrock_credentials.py` oder „Mit KI erweitern“ im Portal.
4. Wenn es klappt: Optional die Marketplace-Policy wieder entfernen (oder dranlassen für künftige neue Modelle).
5. **credentials.json** weiter nur mit IAM-Keys (region: eu-central-1), **keinen** langfristigen Bedrock-API-Schlüssel für Produktion.

---

## Alternative: Kurzfristige API-Schlüssel mit Auto-Refresh (falls IAM dauerhaft blockiert bleibt)

Falls IAM auch mit Marketplace + FTU nicht funktioniert (z. B. wegen Vorgaben eurer Organisation), kann man **kurzfristige Bedrock-API-Schlüssel** (max. 12 Stunden) nutzen und auf dem Server **automatisch erneuern**:

- Bibliothek: **aws-bedrock-token-generator-python** (pip: `aws-bedrock-token-generator`).
- Die Bibliothek erzeugt aus **IAM-Credentials** einen kurzfristigen Bearer-Token für Bedrock. Der Server braucht also weiterhin IAM (oder eine Rolle); mit diesen Credentials wird periodisch ein neuer Token erzeugt und für Bedrock-Anfragen genutzt.
- **DSGVO:** Unverändert eu-central-1; der Token ist nur ein anderes Authentifizierungsmittel, die Verarbeitung bleibt in Frankfurt.
- **Sicherheit:** Kein langfristiger API-Key; Tokens laufen nach spätestens 12 Stunden ab und werden automatisch erneuert.

Diese Variante lohnt sich nur, wenn IAM-Invoke aus Organisationsgründen nicht genutzt werden darf; ansonsten ist **reines IAM** (oben) einfacher und von AWS empfohlen.

---

## Kurzfassung

| Aspekt            | Empfehlung                                                                 |
|-------------------|----------------------------------------------------------------------------|
| **Dauerhaft**     | IAM-Benutzer mit Bedrock- + ggf. einmalig Marketplace-Rechten.            |
| **Sicher**        | Kein langfristiger API-Key; nur IAM-Keys, Rotation bei Bedarf.             |
| **DSGVO**         | Region **eu-central-1** in credentials und bei allen Aufrufen.            |
| **Nächste Schritte** | 1) Marketplace-Policy an drive-bedrock-user. 2) FTU/Use-Case für Claude prüfen. 3) Test erneut ausführen. |
