# Bedrock: IAM-Rechte für Server-Zugangsdaten

**Stand:** 2026-02-24  
**Workstream:** Hilfe (KI „Mit KI erweitern“) / Fahrzeugschein

---

## Problem

- Im **AWS-Bedrock-Playground** (Console) funktioniert Claude Sonnet 4.5.
- Beim Aufruf **vom DRIVE-Server** (Hilfe „Mit KI erweitern“ oder Fahrzeugschein) kommt:  
  **„Access to Bedrock models is not allowed for this account.“**

Ursache: Die **Access Keys** in `config/credentials.json` unter **`aws_bedrock`** gehören einem **IAM-Benutzer**. Dieser Benutzer hat **keine Berechtigung**, Bedrock-Modelle aufzurufen. Die Console nutzt andere Rechte (z. B. Root/Admin).

---

## Lösung

Dem **IAM-Benutzer**, dessen Access Key und Secret Key in `aws_bedrock` eingetragen sind, **Bedrock-Rechte** geben.

### Option A: Verwaltete Policy (einfach)

1. **AWS Console** → **IAM** → **Benutzer**.
2. Den Benutzer auswählen, der die Bedrock-Keys nutzt (oder den, der für den Server gedacht ist).
3. **Berechtigungen** → **Berechtigungen hinzufügen**.
4. Policy anhängen: **`AmazonBedrockFullAccess`** (AWS verwaltet).
5. Speichern.

### Option B: Minimale Rechte (nur Invoke)

Falls nur Invoke erlaubt werden soll, eine **benutzerdefinierte Policy** an den IAM-Benutzer hängen:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
```

(Diese Aktionen decken die Converse-API ab.)

---

## Prüfen

- **Welcher IAM-Benutzer?** In der Console unter **IAM → Benutzer** die Access Keys vergleichen (Key-ID in credentials.json = „Zugriffsschlüssel-ID“ beim Benutzer), oder einen dedizierten Benutzer für Bedrock anlegen und dessen Keys in `config/credentials.json` unter `aws_bedrock` eintragen.
- **Region:** `region` in `aws_bedrock` muss eine Region sein, in der das Modell freigeschaltet ist (z. B. `eu-central-1`). Modellzugriff wird in **Bedrock → Modellkatalog** pro Region aktiviert.

Nach dem Anhängen der Policy 1–2 Minuten warten und „Mit KI erweitern“ im Portal erneut testen.
