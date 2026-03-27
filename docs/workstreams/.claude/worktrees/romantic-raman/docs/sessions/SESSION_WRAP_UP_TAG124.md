# SESSION WRAP-UP TAG 124

**Datum:** 17.12.2025
**Branch:** feature/tag82-onwards

---

## Erledigte Aufgaben

### 1. Kapazitätsplanung - Feldnamen-Mapping Fix

**Problem:** WOCHE, UNVERPLANT und TEILE FEHLEN zeigten "-" statt Daten.

**Ursache:** Template verwendete falsche Feldnamen:
- `woche.auslastung` statt `woche.auslastung_prozent`
- `woche.geplant` statt `woche.geplant_aw`
- `data.teile_fehlen?.anzahl` statt `data.teile?.auftraege_warten_auf_teile`

**Lösung:** `templates/aftersales/kapazitaetsplanung.html` - Feldnamen an API angepasst.

**Commit:** `c936e8c`

---

### 2. Stempeluhr-Monitor - Login-Konflikt behoben

**Problem:** Stempeluhr auf neuem Kiosk-PC zeigte Login-Maske statt direkt zu starten.

**Ursache:** Doppelte Route-Definition:
- `app.py:558` - Mit Token-Auth (korrekt, kein Login)
- `werkstatt_routes.py:54` - Mit `@login_required` (falsch)

Die Blueprint-Route überschrieb die korrekte Route aus app.py.

**Lösung:** Doppelte Route aus `routes/werkstatt_routes.py` entfernt.

**Commit:** `4ba8d77`

**Test:** Stempeluhr auf Kiosk-PC nach Neustart erfolgreich getestet ✅

---

### 3. Stellantis ELSE Portal - HAR-Analyse & Anleitungen

**Problem:** Mitarbeiter werden beim Aufruf der Angebotsseite im Stellantis ELSE Finanzierungsportal rausgeworfen.

**Analyse:** Zwei verschiedene Probleme identifiziert:

#### Problem A: Third-Party-Cookie-Blocking
- Cross-Site-Request von `pos.stellantis-financial-services.de` zu `pf1-dealer-finance.stellantis.com`
- Edge blockiert Cookies bei Cross-Site-Navigation
- Fehlermeldung: "Diese Session ist nicht mehr gültig"

#### Problem B: HTTP Basic Auth fehlgeschlagen (Roland)
- Server antwortet mit 401 Unauthorized
- `WWW-Authenticate: BASIC realm="Unspecified"`
- Falsche/fehlende Credentials im Windows Credential Manager

**Erstellte Anleitungen:**

| Datei | Problem | Inhalt |
|-------|---------|--------|
| `Anleitung_Stellantis_Else_Cookie-Fix.html` | Session ungültig | Edge Cookie-Ausnahmen |
| `Anleitung_Stellantis_Else_Credential-Fix.html` | 401 Unauthorized | Windows Credential Manager |
| `Fix_Stellantis_Edge_Cookies.ps1` | Automatisierung | PowerShell-Script für Cookie-Fix |

**Domains für Cookie-Ausnahmen:**
```
[*.]stellantis.com
[*.]stellantis-financial-services.de
```

#### Problem C: Redundante Edge-Profile (Roland)
- Einstellungen wurden im falschen Profil gespeichert
- Cookies/Credentials nicht im aktiven Profil vorhanden
- **Lösung:** Edge-Profile bereinigt und neu eingerichtet

**Zusammenfassung aller Stellantis-Fälle:**

| Problem | Symptom | Ursache | Lösung |
|---------|---------|---------|--------|
| Session ungültig | "Session nicht mehr gültig" | Third-Party-Cookie-Blocking | Cookie-Ausnahme in Edge |
| 401 Unauthorized | Login wird abgelehnt | Falsche Credentials | Credential Manager bereinigen |
| Einstellungen greifen nicht | Trotz Fix kein Erfolg | Redundante Edge-Profile | Profile bereinigen/neu einrichten |

---

## Geänderte Dateien

### Backend
| Datei | Änderung |
|-------|----------|
| `routes/werkstatt_routes.py` | Doppelte Stempeluhr-Monitor Route entfernt |

### Templates
| Datei | Änderung |
|-------|----------|
| `templates/aftersales/kapazitaetsplanung.html` | Feldnamen-Mapping korrigiert |

### Dokumentation (lokal)
| Datei | Beschreibung |
|-------|--------------|
| `C:\temp\Anleitung_Stellantis_Else_Cookie-Fix.html` | Bebilderte Anleitung |
| `C:\temp\Anleitung_Stellantis_Else_Credential-Fix.html` | Bebilderte Anleitung |
| `C:\temp\Fix_Stellantis_Edge_Cookies.ps1` | PowerShell-Automatisierung |

---

## Git-Commits

```
c936e8c fix(TAG124): Kapazitätsplanung Feldnamen an API angepasst (woche, teile, unverplant)
4ba8d77 fix(TAG124): Stempeluhr-Monitor doppelte Route entfernt (login_required Konflikt)
```

---

## Offene Punkte für TAG 125

### 1. Stellantis Cookie-Problem weiter beobachten
- Cookie-Einstellungen greifen bei manchen Mitarbeitern nicht
- Mögliche GPO-Blockierung im Firmennetzwerk prüfen
- Alternative: Stellantis-Support kontaktieren (serverseitiges SameSite-Cookie-Problem)

### 2. Git-Commit auf Server (TAG 123)
```bash
ssh ag-admin@10.80.80.20 "cd /opt/greiner-portal && git add -A && git commit -m 'feat(TAG123): Urlaubsplaner Locosoft-Integration, Scraper-Fix, AD-Sync'"
```

### 3. Mitarbeiter ohne AD prüfen
- Paula Wieser (Elternzeit)
- Stefanie Bittner, Rosmarie Erlmeier, Cornelia Gruber, etc.
- Sind diese ausgeschieden/in Elternzeit oder fehlt das AD-Konto?

---

## Technische Erkenntnisse

### Stellantis ELSE - Root Cause Analyse

**Warum funktioniert es bei manchen Mitarbeitern?**
1. Unterschiedliche Browser-Einstellungen
2. Unterschiedliche Edge-Versionen
3. Cookie-Ausnahmen bereits vorhanden
4. Kein GPO-Override aktiv

**Stellantis sollte serverseitig fixen:**
- Cookies mit `SameSite=None; Secure` setzen
- Damit würden Cross-Site-Requests funktionieren

### Route-Priorität in Flask
- Blueprint-Routen können App-Routen überschreiben
- Reihenfolge der Blueprint-Registrierung bestimmt Priorität
- Doppelte Routen vermeiden!

---

*Erstellt: 17.12.2025*
