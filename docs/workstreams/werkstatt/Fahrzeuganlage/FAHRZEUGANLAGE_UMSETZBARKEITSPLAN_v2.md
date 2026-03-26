# 🚗 DRIVE Modul: Intelligente Fahrzeuganlage
## Umsetzbarkeitsplan & Konzept v2

**Erstellt:** 2025-02-20  
**Autor:** Claude / Florian Greiner  
**Status:** AWS Setup abgeschlossen → Phase 1 Entwicklung steht an  
**DSGVO:** ✅ AWS Bedrock in Frankfurt (eu-central-1)

---

## 📋 Problemanalyse

### IST-Zustand
- Neukunden + Fahrzeuge werden manuell in Locosoft erfasst (Pr. 111/112)
- Fahrzeugscheindaten abgetippt → fehleranfällig (FIN, HSN/TSN, Kennzeichen)
- Zeitaufwand: 5-8 Min pro Neuanlage, Fehlerrate ~15%

### SOLL-Zustand
1. Mitarbeiter fotografiert Fahrzeugschein (Handy/Tablet)
2. DRIVE liest automatisch alle Felder aus (KI-OCR via AWS Bedrock)
3. Mitarbeiter prüft & bestätigt
4. Smart Copy → Locosoft (Phase 1) oder direkte API (Phase 2+)

---

## 🗓️ Roadmap & Status

### ✅ Phase 0: AWS Bedrock Setup – ERLEDIGT (20.02.2025)

| Schritt | Status |
|---------|--------|
| AWS-Account (Autohaus Greiner GmbH Co. KG, ID: 3284-5081-6063) | ✅ |
| Region eu-central-1 (Frankfurt) | ✅ |
| Amazon Bedrock aktiviert | ✅ |
| Anthropic Modelle freigeschaltet | ✅ |
| IAM User `drive-bedrock-user` mit AmazonBedrockFullAccess | ✅ |
| Access Key: AKIAUY6JRXA76PI2MESQ | ✅ |
| Secret Key gesichert | ✅ |
| 100$ Free Tier (182 Tage, bis Aug 2026) | ✅ |

**Noch offen (Server-Seite):**
- [ ] Credentials in `credentials.json` eintragen (Secret Key aus drive-bedrock-user_accessKeys.csv)
- [ ] **OCR mit Bedrock testen** (vor SOAP-Test): `scripts/test_fahrzeuganlage_bedrock.py` (nur Health) bzw. mit Bild für echten OCR-Lauf

### 🔜 Phase 1: MVP "Scan & Copy" (2-3 TAGs)

Neues DRIVE-Modul mit:
- Fahrzeugschein-Upload (Foto/Datei/Kamera)
- OCR via AWS Bedrock Claude Sonnet → JSON
- Editierbare Ergebnismaske mit Confidence-Scores
- Dublettencheck gegen Locosoft PostgreSQL
- Copy-to-Clipboard (einzeln + alle)
- Scan-Archivierung in PostgreSQL (drive_portal)

### ⏳ Phase 2: Locosoft-Anlage per SOAP (parallel klären)
- **Nicht** in Locosoft-PostgreSQL schreiben (read-only für DRIVE).
- Stammdaten-Anlage (Kunde/Fahrzeug) in Locosoft nur über **SOAP**: `writeCustomerDetails`, `writeVehicleDetails` (bereits in `tools/locosoft_soap_client.py`). Siehe **LOCOSOFT_ANLAGE_SOAP.md**.
- DAT: REST-API für Bestandskunden? (optional)

---

## 💡 Technische Spezifikation

### Credentials (`/opt/greiner-portal/config/credentials.json`)

```json
{
    "aws_bedrock": {
        "region": "eu-central-1",
        "access_key_id": "AKIAUY6JRXA76PI2MESQ",
        "secret_access_key": ">>> SECRET KEY EINTRAGEN <<<",
        "model_id": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "max_tokens": 1024,
        "temperature": 0.0
    }
}
```

### API-Endpoints

```
POST /api/fahrzeuganlage/scan              → Bild hochladen + OCR
GET  /api/fahrzeuganlage/scan/<id>         → Scan-Ergebnis
GET  /api/fahrzeuganlage/history           → Letzte Scans
PUT  /api/fahrzeuganlage/scan/<id>          → Daten editieren
GET  /api/fahrzeuganlage/check-duplicate   → Dublettencheck
GET  /api/fahrzeuganlage/health            → Health-Check
```

### OCR-Prompt

Siehe CURSOR_PROMPT_FAHRZEUGANLAGE.md (Scanner-Klasse).

---

## 📊 Kosten

~0,01€ pro Scan. Bei 200 Scans/Monat = ~2€/Monat.  
100$ Free Tier reicht für ~10.000 Scans.
