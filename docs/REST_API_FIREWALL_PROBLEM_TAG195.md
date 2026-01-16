# Hyundai REST API - Firewall-Problem - TAG 195

**Datum:** 2026-01-16  
**Problem:** Web-Firewall blockiert API-Requests

---

## ⚠️ PROBLEM

**Web-Firewall blockiert Requests:**

```
The request / response that are contrary to the Web firewall security policies have been blocked.
```

**Details:**
- **Detect URL:** `https://hmd.wa.hyundai-europe.com/api/tokenauth/authenticateforapp`
- **Client IP:** 85.209.26.80 (Server-IP)
- **Status:** Request wird blockiert, bevor er die API erreicht

---

## 🔍 MÖGLICHE LÖSUNGEN

### Option 1: Browser-ähnliche Headers ⭐

**Versuch:** Headers setzen, die wie ein Browser aussehen

**Headers:**
- `User-Agent`: Browser-User-Agent
- `Origin`: `https://hmd.wa.hyundai-europe.com:9443`
- `Referer`: `https://hmd.wa.hyundai-europe.com:9443/`
- `Accept`: `application/json, text/plain, */*`

**Status:** ⏳ Wird getestet

---

### Option 2: Session-basierte Authentifizierung ⭐⭐

**Erkenntnis:** Das Portal nutzt möglicherweise Session-Cookies statt Bearer Token

**Workflow:**
1. Login über Web-Interface (mit 2FA)
2. Session-Cookie erhalten
3. Cookie für API-Requests verwenden

**Problem:** 2FA kann nicht automatisiert werden!

---

### Option 3: VPN/Whitelist ⭐⭐⭐

**Möglichkeit:** Server-IP muss in Firewall-Whitelist

**Frage:** 
- Ist Server-IP (10.80.80.20) in Firewall-Whitelist?
- Oder muss VPN-Verbindung verwendet werden?

---

### Option 4: Direkter Zugriff über Portal ⭐⭐⭐⭐

**Erkenntnis:** 
- Portal nutzt Locosoft SOAP als Backend
- Möglicherweise können wir über Locosoft SOAP auf Portal-Daten zugreifen

**Vorteil:**
- Keine Firewall-Probleme
- Bereits vorhandene SOAP-Infrastruktur

**Status:** ⏳ Muss geprüft werden

---

## 📋 CREDENTIALS

**Bekannt:**
- Username: `MK`
- Password: `Hyundai_2025`
- 2FA: Aktiv (Google Authenticator?)

**Problem:**
- 2FA kann nicht automatisiert werden
- Firewall blockiert direkte API-Requests

---

## 🎯 EMPFEHLUNG

### Kurzfristig (Fallback):

**Manuelle Prüfung:**
- Serviceberater prüft im Portal
- Bestätigungs-Button im Frontend
- Dokumentation der Prüfung

### Langfristig:

1. **Firewall-Whitelist prüfen:**
   - Ist Server-IP (10.80.80.20) in Whitelist?
   - Oder VPN-Verbindung einrichten?

2. **Locosoft SOAP prüfen:**
   - Kann Locosoft SOAP als Gateway fungieren?
   - Gibt es SOAP-Methoden für Portal-Daten?

3. **Session-basierte Lösung:**
   - Login über Web-Interface (manuell)
   - Session-Cookie speichern
   - Cookie für API-Requests verwenden

---

## 📝 ZUSAMMENFASSUNG

**Status:**
- ❌ Direkte API-Requests werden von Firewall blockiert
- ⚠️ 2FA verhindert vollautomatische Authentifizierung
- ✅ Server sind erreichbar (Konnektivität OK)

**Nächste Schritte:**
1. Browser-ähnliche Headers testen
2. Firewall-Whitelist prüfen
3. Locosoft SOAP als Alternative prüfen
4. Manuelle Prüfung als Fallback implementieren

---

**Erstellt:** TAG 195  
**Status:** Firewall blockiert Requests, weitere Lösungsansätze nötig
