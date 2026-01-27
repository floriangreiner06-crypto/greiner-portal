# Technische Herausforderungen & Aufwand: Sinch Conversation API

**TAG:** 211  
**Datum:** 2026-01-26  
**Status:** 📊 **DETAILLIERTE ANALYSE**

---

## 🎯 ZWECK

Detaillierte Analyse von:
- **Aufwand** - Genauere Zeitschätzung
- **Technische Herausforderungen** - Konkrete Probleme und Lösungen
- **Code-Änderungen** - Was muss geändert werden
- **Account-Erstellung** - Wer kann das machen

---

## 📊 DETAILLIERTER AUFWAND

### **Phase 1: Setup & Konfiguration (2-3 Stunden)**

**Aufgaben:**
1. **Sinch Account erstellen** (30 Min)
   - Registrierung auf dashboard.sinch.com
   - E-Mail-Verifizierung
   - Projekt erstellen

2. **WhatsApp Channel einrichten** (1-2 Stunden)
   - Facebook Business Manager verbinden
   - WhatsApp Business Account auswählen/erstellen
   - Telefonnummer verifizieren
   - Channel aktivieren

3. **Credentials sammeln** (30 Min)
   - Project ID notieren
   - Access Key + Secret generieren
   - App ID notieren
   - Webhook Secret Token generieren

**Schwierigkeit:** ⭐⭐ **EINFACH** (hauptsächlich Klickarbeit)

---

### **Phase 2: Code-Anpassung API-Client (6-8 Stunden)**

**Datei:** `api/whatsapp_api.py`

#### **Änderung 1: Konfiguration (30 Min)**

**Aktuell (MessengerPeople):**
```python
def get_whatsapp_config() -> Dict[str, str]:
    return {
        'api_url': 'https://rest.messengerpeople.com/api/v17',
        'api_key': os.getenv('MESSENGERPEOPLE_API_KEY', ''),
        'channel_id': os.getenv('MESSENGERPEOPLE_CHANNEL_ID', ''),
    }
```

**Neu (Sinch):**
```python
def get_whatsapp_config() -> Dict[str, str]:
    return {
        'api_url': 'https://conversation.api.sinch.com/v1',
        'project_id': os.getenv('SINCH_PROJECT_ID', ''),
        'key_id': os.getenv('SINCH_KEY_ID', ''),
        'key_secret': os.getenv('SINCH_KEY_SECRET', ''),
        'app_id': os.getenv('SINCH_APP_ID', ''),
        'region': os.getenv('SINCH_REGION', 'eu'),  # 'eu' oder 'us'
    }
```

**Aufwand:** 30 Minuten

---

#### **Änderung 2: Authentifizierung (1 Stunde)**

**Aktuell (MessengerPeople):**
```python
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json"
}
```

**Neu (Sinch):**
```python
import base64

def _get_auth_header(self):
    credentials = f"{self.key_id}:{self.key_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"

headers = {
    "Authorization": self._get_auth_header(),
    "Content-Type": "application/json"
}
```

**Herausforderung:**
- ⚠️ Basic Auth statt Bearer Token
- ⚠️ Base64-Encoding nötig
- ✅ Einfach umzusetzen

**Aufwand:** 1 Stunde

---

#### **Änderung 3: Request-Struktur send_text_message (2-3 Stunden)**

**Aktuell (MessengerPeople):**
```python
def send_text_message(self, to: str, message: str):
    endpoint = "messages"
    payload = {
        "sender": self.channel_id,
        "recipient": to,
        "payload": {
            "type": "text",
            "text": message
        }
    }
    return self._make_request(endpoint, payload)
```

**Neu (Sinch):**
```python
def send_text_message(self, to: str, message: str):
    endpoint = f"projects/{self.project_id}/messages:send"
    payload = {
        "app_id": self.app_id,
        "recipient": {
            "identified_by": {
                "channel_identities": [
                    {
                        "channel": "WHATSAPP",
                        "identity": to
                    }
                ]
            }
        },
        "message": {
            "text_message": {
                "text": message
            }
        },
        "channel_priority_order": ["WHATSAPP"]
    }
    return self._make_request(endpoint, payload)
```

**Herausforderungen:**
- ⚠️ **Komplexere Struktur** - Mehr verschachtelt
- ⚠️ **Project ID im Endpoint** - Nicht im Body
- ⚠️ **App ID erforderlich** - Zusätzliche Konfiguration
- ⚠️ **Channel-Identities** - Array-Struktur
- ⚠️ **Message-Typ anders** - `text_message` statt `text`

**Aufwand:** 2-3 Stunden (inkl. Testing)

---

#### **Änderung 4: Request-Struktur send_image_message (1-2 Stunden)**

**Aktuell (MessengerPeople):**
```python
payload = {
    "payload": {
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
}
```

**Neu (Sinch):**
```python
payload = {
    "message": {
        "media_message": {
            "url": image_url,
            "caption": caption
        }
    }
}
```

**Herausforderungen:**
- ⚠️ **Andere Struktur** - `media_message` statt `image`
- ⚠️ **URL statt link** - Anderer Feldname
- ✅ Ähnlich, aber anders

**Aufwand:** 1-2 Stunden

---

#### **Änderung 5: Response-Parsing (1 Stunde)**

**Aktuell (MessengerPeople):**
```python
if result and 'id' in result:
    message_id = result.get('id')
```

**Neu (Sinch):**
```python
if result and 'message_id' in result:
    message_id = result.get('message_id')
# Oder:
if result and 'message' in result:
    message_id = result['message'].get('id')
```

**Herausforderung:**
- ⚠️ **Response-Struktur anders** - Muss geprüft werden
- ⚠️ **Fehler-Format anders** - Error-Handling anpassen

**Aufwand:** 1 Stunde

---

### **Phase 3: Webhook-Anpassung (4-6 Stunden)**

**Datei:** `routes/whatsapp_routes.py`

#### **Änderung 1: Webhook-Verifizierung (30 Min)**

**Aktuell (MessengerPeople):**
```python
if request.method == 'GET':
    token = request.args.get('token')
    challenge = request.args.get('challenge')
    if token == verify_token:
        return challenge or 'ok', 200
```

**Neu (Sinch):**
```python
if request.method == 'GET':
    # Sinch verwendet möglicherweise andere Verifizierung
    # Muss in Dokumentation geprüft werden
    # Vermutlich ähnlich, aber Parameter können anders sein
```

**Herausforderung:**
- ⚠️ **Verifizierung kann anders sein** - Muss geprüft werden
- ✅ Wahrscheinlich ähnlich

**Aufwand:** 30 Minuten

---

#### **Änderung 2: Event-Struktur (2-3 Stunden)**

**Aktuell (MessengerPeople):**
```python
if data.get('type') == 'message':
    message_id = data.get('id')
    from_number = data.get('sender')
    payload = data.get('payload', {})
    message_type = payload.get('type', 'text')
```

**Neu (Sinch):**
```python
# Sinch verwendet Event-basierte Struktur
event = data.get('event', {})
if 'message_event' in event:
    message_event = event['message_event']
    direction = message_event.get('direction')  # TO_APP oder FROM_APP
    message = message_event.get('message', {})
    
    if 'text_message' in message:
        content = message['text_message'].get('text')
    elif 'media_message' in message:
        media_url = message['media_message'].get('url')
        caption = message['media_message'].get('caption')
    
    channel_identity = message_event.get('channel_identity', {})
    from_number = channel_identity.get('identity')
    message_id = message_event.get('id')
```

**Herausforderungen:**
- ⚠️ **Komplexere Struktur** - Event-basiert, mehr verschachtelt
- ⚠️ **Direction-Check** - `TO_APP` (eingehend) vs `FROM_APP` (ausgehend)
- ⚠️ **Channel-Identity** - Telefonnummer in verschachtelter Struktur
- ⚠️ **Message-Typen anders** - `text_message`, `media_message` statt `type: "text"`

**Aufwand:** 2-3 Stunden

---

#### **Änderung 3: Status-Updates (1-2 Stunden)**

**Aktuell (MessengerPeople):**
```python
if data.get('type') == 'status':
    message_id = data.get('id')
    status_value = data.get('status')
```

**Neu (Sinch):**
```python
# Sinch verwendet delivery_receipt_event
if 'delivery_receipt_event' in event:
    receipt = event['delivery_receipt_event']
    message_id = receipt.get('message_id')
    status_value = receipt.get('status')  # DELIVERED, READ, etc.
```

**Herausforderung:**
- ⚠️ **Anderes Event** - `delivery_receipt_event` statt `type: "status"`
- ⚠️ **Status-Werte können anders sein** - Muss geprüft werden

**Aufwand:** 1-2 Stunden

---

### **Phase 4: Error-Handling & Edge Cases (2-3 Stunden)**

**Aufgaben:**
1. **Error-Response-Parsing** (1 Stunde)
   - Sinch Error-Format verstehen
   - Fehlerbehandlung anpassen
   - Retry-Logik prüfen

2. **Edge Cases** (1-2 Stunden)
   - Leere Responses
   - Timeout-Handling
   - Rate-Limiting
   - Invalid Phone Numbers

**Aufwand:** 2-3 Stunden

---

### **Phase 5: Testing (4-6 Stunden)**

**Aufgaben:**
1. **Unit-Tests** (2 Stunden)
   - API-Client testen
   - Webhook-Handler testen
   - Error-Handling testen

2. **Integration-Tests** (2-3 Stunden)
   - Echte Nachrichten senden
   - Webhook-Events empfangen
   - Status-Updates prüfen

3. **Edge-Case-Tests** (1 Stunde)
   - Fehlerhafte Requests
   - Timeouts
   - Invalid Data

**Aufwand:** 4-6 Stunden

---

### **Phase 6: Dokumentation (1-2 Stunden)**

**Aufgaben:**
1. Code-Kommentare aktualisieren
2. Konfigurations-Dokumentation
3. Setup-Anleitung
4. Troubleshooting-Guide

**Aufwand:** 1-2 Stunden

---

## 📊 GESAMT-AUFWAND

### **Minimal (Basis-Funktionen):**
- Setup: 2-3 Stunden
- API-Client: 6-8 Stunden
- Webhook: 4-6 Stunden
- Testing: 2-3 Stunden
- **Gesamt: ~14-20 Stunden**

### **Vollständig (alle Features + Robustheit):**
- Setup: 2-3 Stunden
- API-Client: 6-8 Stunden
- Webhook: 4-6 Stunden
- Error-Handling: 2-3 Stunden
- Testing: 4-6 Stunden
- Dokumentation: 1-2 Stunden
- **Gesamt: ~17-28 Stunden**

### **Realistische Schätzung:**
**~20-25 Stunden** (inkl. Puffer für unerwartete Probleme)

---

## ⚠️ TECHNISCHE HERAUSFORDERUNGEN

### **1. Komplexere API-Struktur** ⚠️ **MITTEL**

**Problem:**
- Sinch API ist verschachtelter als MessengerPeople
- Mehr Ebenen: `recipient.identified_by.channel_identities[0].identity`
- Mehr Konfiguration: Project ID, App ID, Region

**Lösung:**
- Helper-Funktionen erstellen
- Wrapper-Klassen für Request-Building
- Gute Code-Kommentare

**Aufwand:** +2-3 Stunden

---

### **2. Event-basierte Webhook-Struktur** ⚠️ **MITTEL**

**Problem:**
- Verschiedene Event-Typen: `message_event`, `delivery_receipt_event`, `conversation_start_event`
- Verschachtelte Struktur
- Direction-Check nötig (`TO_APP` vs `FROM_APP`)

**Lösung:**
- Event-Router implementieren
- Separate Handler für jeden Event-Typ
- Gute Logging für Debugging

**Aufwand:** +1-2 Stunden

---

### **3. Response-Struktur unterschiedlich** ⚠️ **NIEDRIG**

**Problem:**
- Message-ID kann an verschiedenen Stellen sein
- Error-Format anders
- Success-Indikatoren anders

**Lösung:**
- Response-Parser implementieren
- Fehlerbehandlung anpassen
- Testing wichtig

**Aufwand:** +1 Stunde

---

### **4. Region-Konfiguration** ⚠️ **NIEDRIG**

**Problem:**
- Sinch hat Regionen: `eu` oder `us`
- API-URL kann sich ändern
- SDK benötigt Region-Konfiguration

**Lösung:**
- Region in Config
- Environment-Variable setzen
- Dokumentation

**Aufwand:** +30 Minuten

---

### **5. App ID & Project ID** ⚠️ **NIEDRIG**

**Problem:**
- Zusätzliche IDs nötig (App ID, Project ID)
- Mehr Konfiguration
- Verwechslungsgefahr

**Lösung:**
- Klare Dokumentation
- Environment-Variablen mit Präfix
- Validierung beim Start

**Aufwand:** +30 Minuten

---

## 🔐 ACCOUNT-ERSTELLUNG

### **Kann ich einen Test-Account erstellen?** ❌ **NEIN**

**Warum:**
- ❌ **Registrierung erfordert E-Mail-Verifizierung**
- ❌ **Facebook Business Manager Verbindung nötig**
- ❌ **WhatsApp Business Account erforderlich**
- ❌ **Telefonnummer-Verifizierung nötig**

**Du musst das machen:**
- ✅ **Registrierung** - dashboard.sinch.com
- ✅ **E-Mail-Verifizierung** - Deine E-Mail
- ✅ **Facebook Business Manager** - Dein Account
- ✅ **WhatsApp Business Account** - Dein Account

---

### **Schritt-für-Schritt: Account-Erstellung**

**Schritt 1: Registrierung (5 Min)**
1. Gehe zu: https://dashboard.sinch.com/signup
2. E-Mail eingeben
3. Passwort erstellen
4. E-Mail-Verifizierung (Link in E-Mail klicken)

**Schritt 2: Projekt erstellen (5 Min)**
1. Login auf dashboard.sinch.com
2. "Create Project" oder "New Project"
3. Projekt-Name: "Greiner Portal DRIVE"
4. Project ID notieren

**Schritt 3: Access Keys generieren (5 Min)**
1. Projekt öffnen
2. "API Keys" oder "Credentials"
3. "Create API Key"
4. Key ID und Secret notieren (Secret nur einmal sichtbar!)

**Schritt 4: App erstellen (10 Min)**
1. "Conversation API" → "Apps"
2. "Create App"
3. App-Name: "WhatsApp Teile-Service"
4. App ID notieren

**Schritt 5: WhatsApp Channel einrichten (1-2 Stunden)**
1. App öffnen → "Channels" → "WhatsApp"
2. "Connect WhatsApp"
3. Facebook Business Manager verbinden
4. WhatsApp Business Account auswählen
5. Telefonnummer verifizieren (SMS oder Voice)
6. Channel aktivieren

**Schritt 6: Webhook konfigurieren (10 Min)**
1. App → "Webhooks"
2. "Add Webhook"
3. URL: `https://auto-greiner.de/whatsapp/webhook`
4. Secret Token generieren und notieren
5. Events auswählen: `message_event`, `delivery_receipt_event`

**Gesamt-Zeit:** ~2-3 Stunden (hauptsächlich Wartezeit bei Verifizierung)

---

## 📋 CREDENTIALS SAMMELN

Nach Account-Erstellung brauche ich:

1. **Project ID** - Aus Dashboard
2. **Key ID** - Aus API Keys
3. **Key Secret** - Aus API Keys (nur einmal sichtbar!)
4. **App ID** - Aus Conversation API Apps
5. **Webhook Secret Token** - Aus Webhook-Konfiguration
6. **Region** - `eu` oder `us` (vermutlich `eu` für Deutschland)

**Diese werden in `.env` eingetragen:**
```bash
SINCH_PROJECT_ID=dein-project-id
SINCH_KEY_ID=dein-key-id
SINCH_KEY_SECRET=dein-key-secret
SINCH_APP_ID=dein-app-id
SINCH_REGION=eu
SINCH_WEBHOOK_SECRET=dein-webhook-secret
```

---

## 🎯 FAZIT

### **Aufwand:**
- **Minimal:** ~14-20 Stunden
- **Vollständig:** ~17-28 Stunden
- **Realistisch:** ~20-25 Stunden

### **Technische Herausforderungen:**
- ⚠️ Komplexere API-Struktur (mittel)
- ⚠️ Event-basierte Webhooks (mittel)
- ⚠️ Response-Parsing (niedrig)
- ⚠️ Region-Konfiguration (niedrig)
- ⚠️ Mehr IDs nötig (niedrig)

### **Account-Erstellung:**
- ❌ **Ich kann das NICHT machen** (erfordert deine Accounts)
- ✅ **Du musst das machen** (~2-3 Stunden)
- ✅ **Ich kann dir helfen** (Schritt-für-Schritt-Anleitung)

---

**Status:** 📊 Detaillierte Analyse abgeschlossen  
**Nächster Schritt:** Account-Erstellung durch dich, dann Code-Anpassung durch mich
