# Marketing — Arbeitskontext

## Status: Aktiv
## Letzte Aktualisierung: 2026-02-21 (Session-Ende)

## Beschreibung

Marketing umfasst alle DRIVE-Funktionen und -Integrationen mit Marketing-Bezug: Kampagnen, Kundenkommunikation, WhatsApp Marketing (z. B. Anleitung für Brigitte), Werbemittel, Leads, Social-Media-Anbindungen und fachliche Schnittstellen zu Verkauf/Integrations.

## Module & Dateien

- Noch keine dedizierten Marketing-APIs; Marketing-relevante Nutzung baut auf bestehenden Modulen auf (z. B. WhatsApp unter Integrations).
- **Anleitung Marketing (WhatsApp):** `docs/workstreams/integrations/WHATSAPP_ANLEITUNG_MARKETING.md` — Schritte bei Meta (Verifizierung, WABA, Nummer); bei hellomateo-Migration übernimmt hellomateo/IT die Anbindung.

### Gegebenenfalls künftig
- Eigene APIs/Routes/Templates für Kampagnen, Leads, Werbemittel-Verwaltung etc., sofern im Portal umgesetzt.

## DB-Tabellen (PostgreSQL drive_portal)

- Noch keine marketing-spezifischen Tabellen. WhatsApp-Daten siehe Workstream Integrations.

## Aktueller Stand (✅ erledigt, 🔧 in Arbeit, ❌ offen)

- ✅ Workstream Marketing angelegt (2026-02-21).
- ✅ **Werkstatt-Potenzial Call-Agent (Verschleißreparatur) – Phase 1 + DRIVE-Anpassungen (2026-02-21):** Spezifikation (mit Claude) angepasst an DRIVE: Phase-1-Queries mit **korrigierten Locosoft-Spalten** (orders.number, vehicles.internal_number, customers_suppliers first_name/family_name, Telefon via customer_com_numbers) ausgeführt. Ergebnisse in [WERKSTATT_POTENZIAL_CALL_AGENT_DRIVE_ANPASSUNGEN.md](WERKSTATT_POTENZIAL_CALL_AGENT_DRIVE_ANPASSUNGEN.md). Für Phase 2–6: **PostgreSQL** (nicht SQLite), **Navigation nur per migration (navigation_items)**, Bootstrap 5, Celery/Task wie üblich. Skript: `scripts/marketing/phase1_datenqualitaet_queries.py`. Phase 2 erst nach Freigabe.
- ✅ **Veact – Erkenntnisse (2026-02-21):** [VEACT_ERKENNTNISSE_UND_NAECHSTE_SCHRITTE.md](VEACT_ERKENNTNISSE_UND_NAECHSTE_SCHRITTE.md) – Was ihr mit Veact anfangen könnt, neue Erkenntnisse (asmc.veact.net, OAuth, user_mgt, ub.veact.net), nächste Schritte (weiternutzen, Listen aus DRIVE, Veact nach API/DataHub fragen).
- ✅ **Werkstattauslastung / Locosoft-Kundenfahrzeuge:** Konzept + **Locosoft-Potenzialanalyse** (Skript `scripts/marketing_locosoft_potenzial_analyse.py`). Analysen 5 (Datenqualität), 1 (HU), 2 (Reaktivierung), **3 (Nächste Inspektion:** 11k fällig 0–1 Monat, 623 km erreicht), Makes (Opel=40, Hyundai=27), Stichprobe Inspektion (Hyundai INSP/ZI; Opel make_number 40, in Top-40 keine Treffer – anderes text_line-Muster). Veact bezieht Daten aus Locosoft via SOAP; keine weitere DRIVE-Veact-Integration. Siehe [WERKSTATT_AUSLASTUNG_LOCOSOFT_KUNDENFAHRZEUGE_VORSCHLAG.md](WERKSTATT_AUSLASTUNG_LOCOSOFT_KUNDENFAHRZEUGE_VORSCHLAG.md).
- ✅ **ML, Bedrock, Inspektionserkennung (2026-02-21):** [ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md](ML_BEDROCK_POTENZIALE_UND_INSPEKTION_ERKENNUNG.md) – Nutzung von ML-Modul und AWS Bedrock für Potenzialerkennung; Ansatz „richtige Inspektion“ für Opel/Hyundai (regelbasiert, Bedrock-Klassifikation text_line, optional ML). Nächste Schritte: Locosoft labour_number/labour_operation_id prüfen; ggf. Bedrock-Pilot für Inspektionstyp.
- ✅ **Predictive Scoring Modul (2026-02-21):** Phase 2+3 umgesetzt. Tabellen in drive_portal (Migration `add_marketing_potenzial_tables.sql`), Script `scripts/marketing/marketing_km_scoring.py` (km-Schätzung + Reparatur-Scores aus Locosoft), API `api/marketing_potenzial_api.py` (Liste, Stats, CSV-Export). Feature **marketing_potenzial** in Rechteverwaltung vergeben, dann `/api/marketing/potenzial/` nutzbar. Siehe [WERKSTATT_POTENZIAL_CALL_AGENT_DRIVE_ANPASSUNGEN.md](WERKSTATT_POTENZIAL_CALL_AGENT_DRIVE_ANPASSUNGEN.md).
- ✅ **Navigation + Seite Werkstatt-Potenzial (2026-02-21):** Migration `add_navigation_marketing_potenzial.sql` (Menüpunkt unter Service), Route `/marketing/potenzial`, Template `templates/marketing/potenzial.html` mit Filtern, Tabelle, CSV-Export. Liste und CSV mit **Halter + Telefon** aus Locosoft angereichert.
- ✅ **Info-Modal Kunde & Fahrzeug (2026-02-21):** API-Detail `/api/marketing/potenzial/detail/<vehicle_number>` (Fahrzeug, Kunde/Halter, **Letzte Rechnung** aus Locosoft). Modal mit robuster Fehlerbehandlung (nicht gefunden → Hinweistext; HTML-Antwort → verständliche Meldung statt Parser-Fehler).
- ✅ **km-Schätzung Verfeinerung (2026-02-21):** Locosoft-Werte > 500.000 als Meter → km; Plausibilität km/Jahr (max. 60.000), sonst keine Extrapolation; Obergrenze 999.999 km.
- 📄 **Scoring durch externe Quellen:** [SCORING_EXTERNE_QUELLEN.md](SCORING_EXTERNE_QUELLEN.md) – TÜV/DEKRA km, Hersteller-Intervalle, Catch/Veact Kontakt-Status, KBA-Rückrufe, Saison; Priorisierung und DSGVO-Hinweise.
- 🔧 **Verfeinerung Liste/Scoring (offen):** Leichen (ausgebuchte/nicht mehr in Locosoft vorhandene Fahrzeuge) und Autohändler bereinigen – Filter oder Ausschluss im Scoring/Anzeige.
- ❌ Konkrete DRIVE-Features (Reports, Export für Catch, Kampagnen) außer Predictive Scoring noch offen; bei Bedarf hier ergänzen.

## Offene Entscheidungen / Nächste Schritte

- **Werkstatt-Potenzial:** Liste bereinigen – Leichen (Fahrzeuge nicht mehr in Locosoft) und Autohändler (z. B. Filter nach Kundentyp/Halter) ausblenden oder ausschließen; Verfeinerung testen.
- Nach Prüfung der Locosoft-Datenqualität: Priorisierung der Analysen (Reaktivierung, Inspektion; HU über Veact). Entscheidung: DRIVE Reports/Exporte für Catch, nur Dokumentation oder beides.
- Inspektionserkennung: In Locosoft prüfen, ob labour_number/labour_operation_id herstellerabhängig Inspektion 1/2/3 (Opel) bzw. 15k/30k (Hyundai) abbilden; falls nein, Bedrock-Pilot für text_line + Marke → Inspektionstyp.
- Fachliche Anforderungen und gewünschte DRIVE-Features für Marketing weiter sammeln und hier dokumentieren.
- Abgrenzung zu Integrations (WhatsApp) und Verkauf (Kundenkommunikation) klären.

## Abhängigkeiten

- Integrations (WhatsApp, ggf. weitere Kanäle), auth-ldap (Zugriff/Berechtigungen), ggf. Verkauf (Kundendaten).
