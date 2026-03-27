# Hyundai GWMS API Dokumentation

**Stand:** 2025-12-04  
**Analysiert aus:** HAR-Dateien (ccc_hyundai_com.har, gwms_hyundaicdn_com.har)

---

## Übersicht

Das Hyundai GWMS (Global Warranty Management System) ist über folgende Systeme erreichbar:

| System | URL | Funktion |
|--------|-----|----------|
| CCC Portal | https://ccc.hyundai.com | Login, SSO, Menü |
| SSO | https://sso.ccc.hyundai.com | Token Exchange |
| GWMS | https://gwms.hyundaicdn.com | Garantie-Funktionen |

---

## Authentifizierung

### Flow

```
1. POST ccc.hyundai.com/login/selectUserLogin.do
   └─→ Response: LOGIN_RESULT=2FA_OTP_USER

2. POST ccc.hyundai.com/login/select2FAOtpLimitTime.do
   └─→ Response: OTP_TIME=300 (5 Min Timeout)

3. User gibt Google Authenticator Code ein

4. POST ccc.hyundai.com/login/checkGoogleCode.do
   └─→ Response: UserInfo + Session

5. GET ccc.hyundai.com/common/login/sso.do
   └─→ Redirect zu SSO

6. GET sso.ccc.hyundai.com/svc/tk/AuthFederate.do?t=TOKEN
   └─→ SSO Token für GWMS
```

### Datenformat

Das CCC Portal nutzt **SSV-Format** (Nexacro Server Side Values):

```
SSV:utf-8\u001ekey1=value1\u001ekey2=value2\u001e...
```

- Trennzeichen: `\u001e` (Record Separator)
- Feld-Trennzeichen: `\u001f` (Unit Separator)

---

## GWMS VIN-Abfrage

### Endpoint

```
POST https://gwms.hyundaicdn.com/servlet/hkmc.gwms.w400_basic_data.w400_0980.W400_0980_Servlet
```

### Request

**Content-Type:** `application/x-www-form-urlencoded; charset=UTF-8`

**Body:**
```
gubun=search
KEY_VHL001_DIST_CD=ALL
KEY_VHL001_PLNT_CD=ALL
KEY_VHL001_VIN_NO=KMHKR81CPNU      # Erste 11 Zeichen der VIN
KEY_VHL001_VIN_SRL=005366          # Letzte 6 Zeichen der VIN
currPage=1
pageRow=10
screenID=W400_0980
```

### Response

**Format:** JSON

```json
[
  {
    "Table0": [
      {
        "VHL001_VIN_NO": "KMHKR81CPNU005366",
        "VHL001_LTS_MDL_NM": "NE IONIQ 5",
        "VHL001_LTS_MDL_CD": "NE**A",
        "VHL001_REGST_NO": "DEG-CM 169",
        "VHL001_WARR_START_DT": "20210923",
        "VHL001_RETL_SALE_DT": "20210923",
        "VHL001_SHIP_DT": "20210514",
        "VHL001_DIST_CD2_NM": "Hyundai Motor Deutschland",
        "VHL001_PLNT_CD": "HMC00",
        
        "VT_SPECIALVIN": [
          {"VAL1": "C07AB", "VAL2": "SV8", "VAL3": "Wartungen fehlen / unvollständig"}
        ],
        "VT_OPENCAMPAIGN": [],
        "VT_BLOCKVIN": [],
        "VT_FREESERVICE": []
      }
    ]
  },
  {
    "Table1": [
      {
        "message": "[ N000000001 ]Inquiry is done.",
        "TOTAL_ROW": "1",
        "workGubun": "search"
      }
    ]
  }
]
```

### Response-Felder

| Feld | Beschreibung | Format |
|------|--------------|--------|
| `VHL001_VIN_NO` | Vollständige VIN | String (17) |
| `VHL001_LTS_MDL_NM` | Modellname | String |
| `VHL001_LTS_MDL_CD` | Modell-Code | String |
| `VHL001_REGST_NO` | Kennzeichen | String |
| `VHL001_WARR_START_DT` | Garantie-Start | YYYYMMDD |
| `VHL001_RETL_SALE_DT` | Verkaufsdatum | YYYYMMDD |
| `VHL001_SHIP_DT` | Auslieferungsdatum | YYYYMMDD |
| `VHL001_DIST_CD2_NM` | Importeur-Name | String |
| `VHL001_PLNT_CD` | Werk-Code | String |
| `VT_SPECIALVIN` | Warnungen | Array |
| `VT_OPENCAMPAIGN` | Offene Rückrufe | Array |
| `VT_BLOCKVIN` | VIN-Sperren | Array |
| `VT_FREESERVICE` | Kostenlose Services | Array |

### Special VIN Codes

| Code | Bedeutung |
|------|-----------|
| SV8 | Wartungen fehlen / unvollständig |
| ... | (weitere zu dokumentieren) |

---

## GWMS Menü-Struktur (aus Labels)

| Code | Bezeichnung |
|------|-------------|
| 000010 | Importeur |
| 000020 | VIN |
| 000060 | Garantie-Start |
| 000080 | Information |
| 100010 | VIN Sperre |
| 100020 | Typ |
| 100030 | Beschreibung |
| 100040 | Fahrzeuginformation |
| 100070 | Campaignliste |
| 100080 | Campaigntyp |
| 100090 | Campaignnr. |
| 100100 | Tech. Bulletin |
| 100120 | Fälligkeitsdatum |
| 100130 | Free Service |
| 100135 | Status |
| 100140 | Package Code |
| 100150 | Free Service OP |

---

## Weitere Endpoints (aus HAR)

### CCC Portal

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/login/selectUserLogin.do` | POST | Login Step 1 |
| `/login/select2FAOtpLimitTime.do` | POST | 2FA Timeout |
| `/login/checkGoogleCode.do` | POST | 2FA Verify |
| `/login/selectLoginGlobalDataset.do` | POST | Global Config |
| `/common/login/sso.do` | GET | SSO Redirect |
| `/common/menuAction.do` | GET | Menü laden |
| `/main/selectMainList.do` | POST | Dashboard |
| `/board/selectNotificationMainList.do` | POST | Benachrichtigungen |

### GWMS

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `W900CommonJsnServlet` | POST | Labels/Config |
| `W400_0980_Servlet` | POST | VIN-Suche |

---

## Credentials

| Feld | Wert |
|------|------|
| URL | https://ccc.hyundai.com |
| User | david.moser@auto-greiner.de |
| Password | LuisaSandra092025!! |
| 2FA | Google Authenticator |

**Händler-Code:** C07AB (Autohaus Greiner)

---

## Integration ins Greiner Portal

### Geplante Funktionen

1. **VIN-Vorprüfung bei Werkstatt-Termin**
   - Automatische VIN-Abfrage
   - Warnung bei offenen Campaigns
   - Garantie-Status anzeigen

2. **Garantie-Assistent**
   - Vorausfüllen von Claim-Daten
   - 21-Tage Fristen-Überwachung
   - Vollständigkeitsprüfung

### Nächste Schritte

1. ✅ API analysiert
2. ⏳ Session-Management (Cookies über SSO)
3. ⏳ Integration in Portal
4. ⏳ Automatische VIN-Prüfung bei Termin

---

## Bekannte Probleme

1. **2FA erforderlich** - Kann nicht vollautomatisiert werden
2. **Session-Management** - SSO Token-Handling komplex
3. **Keine direkte API** - Muss über Web-Session laufen

---

*Dokumentation erstellt: 2025-12-04*
