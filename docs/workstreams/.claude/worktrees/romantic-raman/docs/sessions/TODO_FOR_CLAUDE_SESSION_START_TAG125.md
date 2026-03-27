# TODO für TAG 125

**Erstellt:** 17.12.2025
**Vorherige Session:** TAG 124

---

## Offene Punkte

### 1. Stellantis ELSE - Anleitungen verfügbar
Roland wurde gefixt (redundante Edge-Profile bereinigt).

**Bekannte Probleme & Lösungen:**
| Problem | Lösung |
|---------|--------|
| Session ungültig | Cookie-Ausnahme in Edge |
| 401 Unauthorized | Credential Manager bereinigen |
| Einstellungen greifen nicht | Edge-Profile bereinigen |

**Erstellte Hilfsmittel:**
- `C:\temp\Anleitung_Stellantis_Else_Cookie-Fix.html`
- `C:\temp\Anleitung_Stellantis_Else_Credential-Fix.html`
- `C:\temp\Fix_Stellantis_Edge_Cookies.ps1`

**Langfristige Lösung:** Stellantis-Support kontaktieren - Server muss Cookies mit `SameSite=None; Secure` setzen.

---

### 2. Mitarbeiter ohne AD prüfen
Folgende Mitarbeiter haben kein AD-Mapping:
- Paula Wieser (Elternzeit)
- Stefanie Bittner
- Rosmarie Erlmeier
- Cornelia Gruber
- Fabian Klammsteiner
- Luca-Emanuel Löw
- Andrea Pfeffer
- Vincent Pursch
- Andreas Karl Suttner
- Daniel Thammer
- Michael Ulrich
- Lena Wagner

**Frage:** Sind diese ausgeschieden/in Elternzeit oder fehlt das AD-Konto?

---

## Abgeschlossen in TAG 124

- [x] Kapazitätsplanung Feldnamen-Fix (woche, teile, unverplant)
- [x] Stempeluhr-Monitor Login-Konflikt behoben (doppelte Route)
- [x] Stellantis ELSE HAR-Analyse (2 verschiedene Probleme identifiziert)
- [x] Anleitungen für Cookie-Fix und Credential-Fix erstellt
- [x] PowerShell-Script für automatisierten Cookie-Fix

---

## Kontext

### Geänderte Dateien in TAG 124
- `templates/aftersales/kapazitaetsplanung.html`
- `routes/werkstatt_routes.py`

### Git-Commits TAG 124
```
c936e8c fix(TAG124): Kapazitätsplanung Feldnamen an API angepasst
4ba8d77 fix(TAG124): Stempeluhr-Monitor doppelte Route entfernt
```

### Wichtige Erkenntnisse
- Blueprint-Routen können App-Routen überschreiben
- Third-Party-Cookie-Blocking ist Standard in modernen Browsern
- Stellantis nutzt Cross-Site-Navigation ohne SameSite=None Cookies
