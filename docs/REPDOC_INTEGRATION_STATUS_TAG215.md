# RepDoc Integration - Status & Aufwand-Einschätzung

**Datum:** 2026-01-27  
**TAG:** 215  
**Status:** ⏸️ **Auf Eis gelegt - Entscheidung Teile & Zubehör ausstehend**

---

## 📋 ZUSAMMENFASSUNG FÜR TEILE & ZUBEHÖR

### Was wurde gemacht:

1. ✅ **RepDoc-Zugang eingerichtet:**
   - Benutzer: `Greiner_drive`
   - Passwort: `Drive2026!`
   - Login funktioniert

2. ✅ **API-Analyse durchgeführt:**
   - RepDoc hat eine REST API (`https://lite.repdoc.com/WsCloudDataServiceLite/api`)
   - JWT-Token-basierte Authentifizierung funktioniert
   - **ABER:** Teile-Suche verwendet serverseitiges Rendering (keine API)

3. ✅ **Scraper-Grundgerüst erstellt:**
   - Login funktioniert bereits
   - HTML-Parsing muss noch optimiert werden

---

## ⚠️ ERKENNTNISSE

### Technische Herausforderungen:

1. **Keine API für Teile-Suche:**
   - RepDoc verwendet HTML-Form-Submit (serverseitiges Rendering)
   - Keine AJAX/API-Calls für Suchergebnisse
   - Muss über Web-Scraping (Selenium) gelöst werden

2. **Performance:**
   - Selenium-Scraping ist langsam (~5-10 Sekunden pro Suche)
   - Ähnlich wie Schäferbarthold/Dello (bereits implementiert)

3. **Wartbarkeit:**
   - HTML-Struktur kann sich ändern → Selektoren müssen angepasst werden
   - Login-Session kann ablaufen → Retry-Logik nötig

---

## 💰 AUFWAND-EINSCHÄTZUNG

### Bereits erledigt (ca. 2-3 Stunden):
- ✅ Zugang eingerichtet
- ✅ API-Analyse
- ✅ Login-Implementierung
- ✅ Grundgerüst Scraper

### Noch zu tun (ca. 3-5 Stunden):
- ⏳ HTML-Parsing der Suchergebnisse optimieren
- ⏳ Robuste Selektoren finden
- ⏳ Preis-Extraktion implementieren
- ⏳ Error-Handling verbessern
- ⏳ Integration in `teile_api.py` testen
- ⏳ Frontend-Integration (optional)

### Gesamtaufwand:
**Ca. 5-8 Stunden** für vollständige Integration

---

## ❓ FRAGEN FÜR TEILE & ZUBEHÖR

1. **Nutzen:**
   - Wie oft wird RepDoc aktuell genutzt?
   - Wie wichtig ist RepDoc im Vergleich zu anderen Lieferanten?
   - Würde eine Integration in DRIVE den Arbeitsablauf verbessern?

2. **Alternativen:**
   - Gibt es andere Lieferanten, die wichtiger sind?
   - Sollte RepDoc Priorität haben oder andere Systeme zuerst?

3. **Anforderungen:**
   - Welche Daten werden von RepDoc benötigt? (Preise, Verfügbarkeit, Lieferzeiten?)
   - Reicht eine manuelle Suche oder muss es automatisch sein?

---

## 📊 VERGLEICH MIT ANDEREN LIEFERANTEN

### Bereits integriert:
- ✅ **Schäferbarthold** - Scraper funktioniert
- ✅ **Dello/Automega** - Scraper funktioniert (optional, langsam)
- ✅ **Locosoft OEM** - Direkte DB-Verbindung (schnell)

### RepDoc:
- ⏸️ **Auf Eis** - Entscheidung ausstehend

---

## 🎯 EMPFEHLUNG

**Wenn RepDoc wichtig ist:**
- Integration ist technisch machbar
- Aufwand: 5-8 Stunden
- Performance: ~5-10 Sekunden pro Suche (ähnlich Dello)

**Wenn RepDoc weniger wichtig:**
- Erst andere, wichtigere Systeme integrieren
- RepDoc später nachholen, falls Bedarf besteht

---

## 📁 DOKUMENTATION

**Erstellte Dateien:**
- `tools/scrapers/repdoc_scraper.py` - Scraper (Login funktioniert)
- `api/teile_api.py` - Integration vorbereitet (Code vorhanden)
- `docs/REPDOC_INTEGRATION_TAG215.md` - Integration-Dokumentation
- `docs/REPDOC_API_ANALYSE_TAG215.md` - API-Analyse
- `docs/REPDOC_API_FAZIT_TAG215.md` - Technisches Fazit

**Zugangsdaten:**
- Benutzer: `Greiner_drive`
- Passwort: `Drive2026!`
- URL: `https://www2.repdoc.com/DE/Login#Start`

---

## ✅ NÄCHSTE SCHRITTE

1. **Entscheidung Teile & Zubehör abwarten**
2. **Falls Ja:** Scraping optimieren und Integration abschließen
3. **Falls Nein:** Code behalten für später, andere Prioritäten setzen

---

**Status:** ⏸️ **Auf Eis gelegt**  
**Nächster Schritt:** Entscheidung Teile & Zubehör
