# TODO FÜR CLAUDE - SESSION START TAG 177

**Erstellt:** 2026-01-09 (nach TAG 176)  
**Status:** Bereit für nächste Session

---

## 📋 ÜBERBLICK

**WICHTIG:** TAG 176 hatte ZWEI Sessions:
1. **Erste Session:** TEK Dashboard, Stückzahlen (siehe `SESSION_WRAP_UP_TAG176.md`)
2. **Zweite Session:** Qualitätskontrolle, Quick Wins, Teile-Status SSOT (siehe `SESSION_WRAP_UP_TAG176_FINAL.md`)

**Zweite Session (TAG 176 Final) hat erledigt:**
- ✅ Qualitätskontrolle des gesamten Drive-Systems
- ✅ Quick Wins: Urlaubsplaner Jahr-Fix, teile_status_api Bugs behoben
- ✅ SSOT für Teile-Lagerbestand implementiert
- ✅ Doppelte Dateien gelöscht
- ✅ Session-Befehle erweitert (Qualitätscheck, Standards)
- ✅ Konfigurationen gesichert (Sync-Verzeichnis)
- ⚠️ **User-Testing steht noch aus!**

**Offene Probleme:**
- ⚠️ Stückzahlen stimmen noch nicht (5 NW / 12 GW erwartet) - aus erster Session
- ⚠️ Weitere Urlaubsplaner-Bugs müssen getestet werden

---

## 🔍 ZU PRÜFEN BEI SESSION-START

1. **Aktueller Stand:**
   - Prüfe `docs/sessions/SESSION_WRAP_UP_TAG176.md`
   - Prüfe welche Abfragen bereits getestet wurden

2. **Stückzahlen-Problem:**
   - Erwartet: 5 NW und 12 GW fakturiert (per heute)
   - Aktuell: 7 NW und 9 GW (mit COALESCE-Logik)
   - Keine der getesteten Abfragen liefert genau 5/12!

---

## 🎯 PRIORITÄT 1: User-Testing der Quick Wins (WICHTIG)

**Status:** ✅ Quick Wins implementiert, aber noch nicht vom User getestet

**Zu testen:**
1. [ ] **Urlaubsplaner:**
   - Prüfen ob Jahr jetzt korrekt ist (2026 statt 2025)
   - Weitere Bugs testen (Genehmigung, Tag-Markierung, Urlaubstyp)
   - Siehe: `docs/ANALYSE_URLAUBSPLANER_BUGS_TAG176.md`

2. [ ] **Teile-Status:**
   - Prüfen ob Teil 1620012580 (Auftrag #20853) jetzt korrekt als verfügbar angezeigt wird
   - Prüfen ob Teil 9825371480 (Auftrag #25353) jetzt korrekt als verfügbar angezeigt wird
   - Prüfen ob "Fehlende Teile (0)" korrekt angezeigt wird wenn alle Teile verfügbar sind
   - Siehe: `docs/TEST_ANLEITUNG_TEILE_STATUS_API_TAG176.md`

3. [ ] **Allgemein:**
   - Prüfen ob keine neuen Fehler aufgetreten sind
   - Service-Logs prüfen auf Warnings/Errors

**Nach User-Testing:**
- Feedback sammeln
- Weitere Bugs fixen falls nötig
- Dokumentation aktualisieren

---

## 🎯 PRIORITÄT 2: Stückzahlen korrigieren (KRITISCH - aus erster Session)

**Problem:** Stückzahlen stimmen nicht - erwartet 5 NW / 12 GW, aber Abfrage liefert andere Werte.

**User-Anforderung:**
> "fakt ist in locosoft sind per heut 5 Nw fakturiert und 12 gw. das ist die wahrheit. die muss in der tek stehen."

**Nächste Schritte:**

### 1. Per VIN analysieren (WICHTIG!)

**Ziel:** Herausfinden, welche Fahrzeuge in Locosoft als fakturiert gelten.

**Schritte:**
1. [ ] Liste aller fakturierten Fahrzeuge aus Locosoft holen
   - Per VIN identifizieren
   - Welche haben `out_invoice_date`?
   - Welche haben `out_sales_contract_date`?
   - Welche haben beide?
   - Welche haben keines?

2. [ ] Prüfen ob und wie gefiltert wird
   - Gibt es Status-Felder, die relevant sind?
   - Gibt es `out_invoice_number` Bedingung?
   - Gibt es andere Filter (Standort, Firma)?

3. [ ] Vergleich: Welche 5 NW und 12 GW sind fakturiert?
   - Liste der erwarteten Fahrzeuge (per VIN)
   - Mit Datenbank-Abfrage vergleichen
   - Herausfinden, welche Bedingung fehlt oder falsch ist

### 2. Verschiedene Abfragen testen

**Bereits getestet:**
- ❌ Nur `out_invoice_date`: 4 NW, 5 GW
- ❌ `out_invoice_date` ODER `out_sales_contract_date`: 7 NW, 9 GW
- ❌ `COALESCE(out_invoice_date, out_sales_contract_date)`: 7 NW, 9 GW
- ❌ Alle Datumsfelder kombiniert: 7 NW, 14 GW
- ❌ Mit `out_invoice_number` Bedingung: 4 NW, 6 GW

**Noch zu testen:**
- [ ] Kombination mit anderen Bedingungen
- [ ] Andere Datumsfelder (z.B. `out_ready_for_sale_date`)
- [ ] Status-Felder prüfen
- [ ] Spezielle Filter-Logik in Locosoft

### 3. Logik anpassen

**Ziel:** Abfrage so anpassen, dass genau 5 NW und 12 GW geliefert werden.

**Schritte:**
1. [ ] Basierend auf VIN-Analyse die richtige Logik identifizieren
2. [ ] Abfrage in `get_stueckzahlen_locosoft()` anpassen
3. [ ] Testen mit echten Daten
4. [ ] Service neu starten und prüfen

---

## 📝 WICHTIGE HINWEISE

### Stückzahlen-Abfrage (`get_stueckzahlen_locosoft`)

**Aktuelle Logik:**
```python
COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) >= von
AND COALESCE(dv.out_invoice_date, dv.out_sales_contract_date) <= heute
```

**Problem:** Liefert 7 NW / 9 GW statt 5 NW / 12 GW

**Mögliche Ursachen:**
- Falsche Datumsfelder verwendet
- Zusätzliche Bedingungen fehlen (Status, Invoice-Number, etc.)
- Filter-Logik in Locosoft anders als erwartet

### TEK Dashboard

**Status:** ✅ Funktioniert korrekt
- Zwei Tage nebeneinander (08.01. und 09.01.)
- Datum statt Wochentag
- GESAMT-Zeile korrekt

### DB1/Stk für GESAMT

**Status:** ✅ Korrigiert
- Berechnung: Nur DB1 von NW+GW durch Stückzahl
- Ergebnis: ~1.888 €/Stk (korrekt)

---

## 🔗 RELEVANTE DATEIEN

### Code:
- `routes/controlling_routes.py` - `get_stueckzahlen_locosoft()` Funktion (Zeile ~195)
- `routes/controlling_routes.py` - `api_tek()` Funktion (Zeile ~631)

### Dokumentation:
- `docs/sessions/SESSION_WRAP_UP_TAG176.md` - Erste Session (TEK Dashboard)
- `docs/sessions/SESSION_WRAP_UP_TAG176_FINAL.md` - Zweite Session (Quick Wins, SSOT)
- `docs/TEK_DASHBOARD_ZWEI_TAGE_TAG176.md` - Dashboard-Implementierung
- `docs/QUALITAETSKONTROLLE_TAG176.md` - Qualitätskontrolle
- `docs/QUICK_WINS_ABGESCHLOSSEN_TAG176.md` - Quick Wins Zusammenfassung
- `docs/TEILE_STOCK_SSOT_TAG176.md` - SSOT für Lagerbestand
- `docs/TEST_ANLEITUNG_TEILE_STATUS_API_TAG176.md` - Test-Anleitung

---

## 🧪 TEST-ABFRAGEN

**Für VIN-Analyse:**
```sql
SELECT 
    dv.vehicle_number,
    dv.dealer_vehicle_type,
    dv.out_invoice_date,
    dv.out_sales_contract_date,
    dv.out_invoice_number,
    dv.out_sale_price,
    dv.location
FROM dealer_vehicles dv
WHERE dv.out_sale_price > 0
  AND dv.dealer_vehicle_type IN ('N', 'G')
ORDER BY dv.dealer_vehicle_type, dv.out_invoice_date
```

**Vergleich mit erwarteten 5 NW / 12 GW:**
- Welche VINs sind fakturiert?
- Welche Datumsfelder haben sie?
- Welche Bedingungen erfüllen sie?

---

## 🚨 KRITISCH

**Stückzahlen müssen korrekt sein!**
- User sagt: "das ist die wahrheit. die muss in der tek stehen."
- Per VIN analysieren ist ESSENTIELL
- Herausfinden, welche genaue Logik Locosoft verwendet

---

**Bereit für nächste Session! 🚀**
