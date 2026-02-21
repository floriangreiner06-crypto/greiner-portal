# Veact – Erkenntnisse und was wir damit anfangen können

**Stand:** 2026-02-21  
**Kontext:** Veact für HU/AU im Einsatz; Erkundung Login, Oberfläche, API-Endpunkte.

---

## 1. Kurz: Können wir mit Veact was anfangen?

**Ja – aber in zwei Ebenen.**

| Ebene | Heute | Mit Veact erweitert |
|-------|--------|----------------------|
| **Nutzung wie jetzt** | HU/AU-Ansprache läuft über Veact (Brigitte/Kampagnen Manager). Ihr könnt Kampagnen erstellen, Zielgruppen ansprechen, Follow-up (Review/Followup). | Nichts ändern nötig – weiter so nutzen. |
| **DRIVE ↔ Veact** | Keine technische Anbindung: DRIVE kennt keine Veact-API, Veact keine DRIVE-Listen. | **Wenn** Veact eine **Partner-API oder DataHub** anbietet: DRIVE könnte z. B. Listen (Inspektionsfällige, Reaktivierung) exportieren oder Veact könnte Daten aus Locosoft/DRIVE beziehen. Das steht noch aus (Veact anfragen). |

**Fazit:** Mit Veact **an sich** könnt ihr sofort weitermachen (Kampagnen, HU, ggf. Inspektion/Reaktivierung manuell oder über Veact-Oberfläche). **Technische Integration** DRIVE ↔ Veact ist möglich, sobald Veact API/DataHub bereitstellt oder dokumentiert.

---

## 2. Neue Erkenntnisse aus der Erkundung

### 2.1 Was wir jetzt wissen

- **Login funktioniert** mit brigitte.lackerbeck@auto-greiner.de (Passwort über Umgebungsvariable im Skript, nicht im Repo).
- **App-URL:** Die Oberfläche läuft unter **asmc.veact.net** (nicht app.veact.net im Alltag). Direktlink Kampagnen Manager:  
  `https://asmc.veact.net/organisation/646c5ffae49ebe10c9e40ef0/cm/`
- **OAuth2:** Authorization unter `accounts.veact.net/v1/oauth2/auth`, Callback unter `asmc.veact.net/oauth/callback`. Für eine spätere **API-Integration** (z. B. DRIVE) fehlt noch der **Token-Endpoint** (z. B. `/v1/oauth2/token`) – den müsste Veact nennen oder man im Network-Tab beim Login prüfen.
- **user_mgt/login:** Wenn asmc keine Session hat, Weiterleitung zu `asmc.veact.net/user_mgt/login?target=...`. Das erklärt, warum manchmal ein zweiter Login nötig ist.
- **Weitere Hosts:**  
  - **ub.veact.net** – Surveys/Analytics (`/api/surveys/`, `/flags/`), für euch eher nicht relevant für Kampagnen-Daten.  
  - **mc.veact.net** – in der App referenziert, Rolle unklar.
- **Kampagnen-Liste:** Wird vermutlich **server-seitig** (Lift) ausgeliefert – keine sichtbaren REST-Calls wie `/api/campaigns` im Log. Für echte Geschäfts-APIs (Kampagnen, Kundendaten) müsste man in der App „Verwalten“, „Kundendaten pflegen“ oder Suche nutzen und in den **Browser-DevTools (Network)** die XHR/Fetch-URLs notieren.

### 2.2 Was wir (noch) nicht haben

- Öffentliche **API-Dokumentation** von Veact (Partner Connect API, DataHub, Token-Endpoint).
- Gesicherte **REST-Endpunkte** für Kampagnen, Kundendaten oder Zielgruppen-Import (nur Vermutungen aus der Oberfläche, siehe VEACT_ACCOUNT_ERKUNDUNG.md Abschnitt 6).
- ~~Bestätigung, ob und wie Locosoft an Veact angebunden ist~~ → **Veact bezieht Daten aus Locosoft via SOAP.** Keine weitere DRIVE-Integration geplant.

---

## 3. Konkrete nächste Schritte

### Sofort umsetzbar (ohne Veact-API)

1. **Veact wie gewohnt nutzen** für HU/AU und ggf. weitere Kampagnen (Inspektion, Reaktivierung), Zielgruppen manuell oder über Veact-Oberfläche definieren.
2. **Locosoft-Potenzial nutzen:** Die DRIVE-Analyse (Skript `marketing_locosoft_potenzial_analyse.py`) liefert Mengen und Listen (Reaktivierung pro Standort, HU-Fälligkeit, Datenqualität). Diese **Listen** könnt ihr manuell oder per Export (CSV/Excel) für Veact oder Catch verwenden – z. B. „Fahrzeuge > 12 Monate kein Besuch“ als Zielgruppe für eine Reaktivierungs-Kampagne in Veact.
3. **Catch (Prof4net)** bleibt euer Marketing-Modul; Veact fokussiert sich auf HU/AU/Kampagnen. Abgrenzung und ggf. Arbeitsteilung (wer schreibt welche Kampagne) intern klären.

### Mittelfristig (wenn Integration gewünscht)

4. **Bei Veact anfragen:**  
   - Gibt es eine **Partner Connect API** oder **DataHub-API** für Händler?  
   - **Token-Endpoint** und Doku für OAuth2 (Client Credentials oder Authorization Code)?  
   - Kann Veact **Zielgruppen/Listen** aus externen Systemen (DMS, DRIVE) importieren?
5. **Falls Veact API anbietet:** In DRIVE einen kleinen Export-Service oder Celery-Task bauen, der Listen (z. B. „Inspektion fällig“, „Reaktivierung > 12 Monate“) im von Veact geforderten Format erzeugt und per API oder Datei-Import an Veact übergibt.
6. **Falls Veact nur DataHub/DMS-Anbindung hat:** Prüfen, ob Locosoft bereits an Veact angebunden ist; wenn ja, ob die Daten (HU, Inspektion, Kunden) in Veact ankommen und ob DRIVE darauf aufsetzen oder nur Locosoft nutzen soll.

---

## 4. Zusammenfassung

| Frage | Antwort |
|-------|---------|
| **Können wir mit Veact was anfangen?** | **Ja.** Weiter nutzen für HU/AU/Kampagnen; Potenzial-Listen aus DRIVE/Locosoft manuell oder per Export für Veact/Catch verwenden. |
| **Neue Erkenntnisse?** | App-URL (asmc.veact.net), OAuth-Flow, user_mgt/login, ub.veact.net (Surveys), keine offene Kampagnen-REST-API im Log. |
| **Technische Integration DRIVE ↔ Veact?** | Möglich, sobald Veact API/DataHub/Token dokumentiert oder bereitgestellt wird – dann nächster Schritt: Veact anfragen und ggf. kleinen Export-/API-Client in DRIVE bauen. |

Alle technischen Details und URLs stehen in [VEACT_ACCOUNT_ERKUNDUNG.md](VEACT_ACCOUNT_ERKUNDUNG.md). Die Locosoft-Potenzialanalyse und Vorschläge für Inspektion/Reaktivierung sind in [WERKSTATT_AUSLASTUNG_LOCOSOFT_KUNDENFAHRZEUGE_VORSCHLAG.md](WERKSTATT_AUSLASTUNG_LOCOSOFT_KUNDENFAHRZEUGE_VORSCHLAG.md) und [ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md](ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md).
