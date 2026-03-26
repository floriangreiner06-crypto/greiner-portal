# Detaillierte Zusammenfassung: Planung 2025/26, GW, NW, Zinskosten, Standzeiten

**Stand:** Februar 2026  
**Zweck:** Kontext für eine weitere Claude-Session; alle Annahmen, Rechnungen, Scripts und Ergebnisse in einem Dokument.

---

## 1. Ausgangslage und Ziele

- **Geschäftsjahr:** 2025/26 (Sep 2025 – Aug 2026).
- **Ergebnisziel:** 1 % Rendite (Gewinnzone) bzw. Break-even (0 €).
- **Prognose ohne Maßnahmen (Hochrechnung YTD):** Umsatz ca. 26,6 Mio €, Ergebnis ca. -572 k€ (-2,15 % Rendite), Gap zum 1 %-Ziel ca. 838 k€.
- **Relevante Bereiche für diese Zusammenfassung:** Neuwagen (NW), Gebrauchtwagen (GW), Zinskosten, Standzeiten, belastbarer Planungsvorschlag.

---

## 2. Zinskosten

### 2.1 Quelle und Konten

- **Primär:** Buchhaltungsdaten aus Locosoft (im Portal gespiegelt in `loco_journal_accountings`).
- **Verwendete Konten:** 895xxx, 4982x; plus tatsächlich belegte Konten (Stellantis Bank, Santander, Genobank): **890501, 891001, 891711, 891712, 896711, 896712**. Es zählt die **SOLL-Seite** (Aufwand). Konten wurden per Suchbegriffen (santander, stellantis, genobank, genossenschaft, zins) in `posting_text` / `contra_account_text` identifiziert (Script: `scripts/planung_finde_zinskosten_konten.py`).
- **Fallback:** Wenn die Summe aus diesen Konten 0 ist, werden Zinsen aus der Tabelle **fahrzeugfinanzierungen** (Portal) genutzt: `zinsen_letzte_periode × 12` (inkl. Zinsfreiheit).
- **Vorjahr 2024/25:** In der Auswertung lieferte vor allem Konto **890501** SOLL-Buchungen (ca. 22 k€); 895xxx/4982x waren 0.

### 2.2 Planungsannahme Zinskosten

- **Annahme:** Nach Zinsfreiheit sind die Zinskosten für den **Gesamtbestand** rechnerisch **90 Tage** unter Zinsen; durchschnittlicher Zinssatz **5 %** p.a.; **Fahrzeugwert ohne MwSt.** (MwSt. wird nicht finanziert).
- **Formel:** `Zinskosten_Plan = Lagerwert_netto_gesamt × (90 / 365) × 5 %`.
- **Lagerwert:** Aus Locosoft `dealer_vehicles` (Bestand mit `out_invoice_date IS NULL`), Wert = `COALESCE(in_acntg_cost_unit_new_vehicle, in_buy_list_price)`. Nur Fahrzeuge mit Wert > 0.
- **Hinweis:** Für Neuwagen sind die Werte in Locosoft oft nicht gepflegt (NW-Ø-Wert unrealistisch niedrig); der Lagerwert wird dann stark vom GW-Bestand getragen.
- **Dokumentation:** `docs/workstreams/planung/GEWINNZONE_STANDZEIT_VORSCHLAG.md` (Abschnitte 6–8: Zinskosten-Quelle, Plan-Zinskosten, Kritik/Gegenvorschläge).

---

## 3. Standzeiten

### 3.1 Zwei Arten

- **Standzeiten des Bestands (für Planung/Zinsen relevant):** Noch nicht verkaufte Fahrzeuge, Stichtag. Berechnung: `Stichtag − COALESCE(in_arrival_date, created_date)` in Locosoft `dealer_vehicles` (`out_invoice_date IS NULL`). Ausgabe im Gewinnzone-Script: NW/GW Stück und Ø Tage.
- **Standzeiten der verkauften Fahrzeuge (Vergleich):** Wie lange lagen sie vor Verkauf? `out_invoice_date − COALESCE(in_arrival_date, created_date)` für im GJ verkaufte Fz. Wird nur zum Vergleich ausgegeben.

### 3.2 Aktuelle Werte (Beispiel Stichtag)

- **Bestand:** NW z. B. 319 Stück, Ø 153 Tage; GW 174 Stück, Ø 85 Tage.
- **Verkaufte Fz VJ 2024/25:** NW Ø 107 Tage, GW Ø 96 Tage (zum Vergleich).

### 3.3 NW Bestandsalter in der Planung

- **Annahme Nutzer:** „NW Bestandsalter wird im restlichen GJ auf **110 Tage** abgebaut.“ Das ist eine Vorgabe für die Planung (Zielstandzeit NW), keine automatisch aus Daten berechnete Größe im aktuellen Script.

---

## 4. Belastbarer Planungsvorschlag

### 4.1 Script und Ablauf

- **Script:** `scripts/planung_vorschlag_belastbar.py`.
- **Ablauf:** Ruft `get_gap_analyse(gj)` (Prognose, IST YTD, Bereiche mit Ziel-Margen), lädt VJ-Kosten aus Portal (`lade_vj_aus_portal`), berechnet Kosten-Budget = Mittelwert (VJ-Kosten + YTD-Kosten hochgerechnet auf 12 Monate), Zinskosten-Plan (90 Tage, 5 %, Lagerwert netto), Standzeiten aus Locosoft. **Plan pro Bereich:** Umsatz-Anteil (aus YTD-Anteil an Gesamtumsatz) × **Ziel-Marge** → Plan-DB1 je Bereich. Plan-Ergebnis = Summe Plan-DB1 − Kosten-Budget.
- **Standard-Ziel-Margen (Basis):** NW 8 %, GW 5 %, Teile 28 %, Werkstatt 55 %, Sonstige 50 % (aus `api/unternehmensplan_data.py`, Gap-Analyse).
- **Ausgabe:** Konsole + Markdown-Datei **`docs/workstreams/planung/PLANUNGSVORSCHLAG.md`** (Ziel, Ausgangslage, Annahmen, Plan-Tabelle, Ergebnis, Kernaussage bei negativem Ergebnis, Nächste Schritte).
- **Sync:** `PLANUNGSVORSCHLAG.md` wird auf Wunsch nach **Windows-Sync** kopiert: `\\Srvrdb01\...\Server\docs\workstreams\planung\` (auf dem Server: `/mnt/greiner-portal-sync/docs/workstreams/planung/`).

### 4.2 Basisszenario (8 % NW, 5 % GW) – Beispielrechnung

- Plan-DB1 gesamt z. B. 3.824.625 €, Kosten-Budget z. B. 4.974.359 € → **Plan-Ergebnis ca. -1.149.734 €**, Plan-Rendite ca. -4,33 %.
- **Kernaussage:** Selbst bei Erreichen der Ziel-Margen reicht der Plan-DB1 nicht; für Break-even oder 1 % sind Kostensenkung und/oder weitere DB1-Hebel nötig.

---

## 5. GW-Planung (859 GW, 6 % DB-Marge)

### 5.1 Nutzer-Annahmen

- Gesamtumsatz wird um **5 %** gesteigert.
- NW Bestandsalter wird im restlichen GJ auf **110 Tage** abgebaut.
- **Per Januar:** 289 GW fakturiert, **DB1 GW = -38.982 €** (defizitär).
- Es gibt **53 GW-Bestandsfahrzeuge mit Standzeit ≥ 120 Tage** (Locosoft, Stichtag; Ø 190 Tage); diese werden noch verkauft und gelten als defizitär.
- **Frische GW:** durchschnittlich **1.200 € DB1** pro Fahrzeug.
- **Ziel:** GW-Bereich soll auf **6 % DB-Marge** kommen (nicht 5 %).

### 5.2 Rechnung (Kurzfassung)

- **GW-Plan-Umsatz (mit +5 %):** Basis aus Plan (z. B. 9.110.189 €) × 1,05 = **9.565.698 €**.
- **Ziel GW-DB (6 %):** 9.565.698 € × 6 % = **573.942 €**.
- Bereits realisiert: **-38.982 €** (289 GW). Noch fehlende DB: 573.942 − (-38.982) = **612.924 €**.
- Die 53 Bestandsfahrzeuge (≥120 Tage) werden beim Verkauf mit durchschnittlich **-135 €** DB angesetzt (analog zu -38.982/289). Beitrag der 53: 53 × (-135) = **-7.149 €**.
- DB, die aus **frischen GW** kommen muss: 612.924 − (-7.149) = **620.073 €**.
- **Anzahl frischer GW (Ø 1.200 € DB):** 620.073 / 1.200 = **517 Fahrzeuge** (bei -200 € pro Altfahrzeug: ca. 520).

### 5.3 GW-Gesamtzahl 2025/26

- **289** (bereits per Januar) + **53** (Bestand ≥120 Tage) + **517** (frische GW) = **859 GW** für 2025/26.

---

## 6. NW-Entwicklung und Trend

### 6.1 Daten (erste 6 Monate GJ, Sep–Feb)

- **NW-Umsatz / DB1 / Marge** aus BWA/Unternehmensplan-IST.
- **NW-Stück** aus Locosoft `dealer_vehicles` (N, T, V), gleicher Zeitraum.

Beispielwerte:

| GJ     | NW-Umsatz (6 Mon.) | NW-DB1   | NW-Marge | NW-Stück |
|--------|--------------------|----------|----------|----------|
| 2023/24 | 6.531.188 €       | 460.025 € | 7,0 %   | 242      |
| 2024/25 | 5.737.225 €       | 501.012 € | 8,7 %   | 214      |
| 2025/26 | 5.442.568 €       | 515.760 € | **9,5 %** | **232**  |

### 6.2 Abgeleiteter Trend

- **Stück (Sep–Feb):** 2025/26 vs 2024/25: **+8,4 %** (232 vs 214).
- **Marge:** 7,0 % → 8,7 % → **9,5 %** (Ziel NW war 8 % → positiv, Ziel übertroffen).

### 6.3 Nutzung in der Planung

- **NW-Ziel-Marge** kann testweise von 8 % auf **9 %** (oder 9,5 %) angehoben werden (Trend).
- **GW-Ziel-Marge** von 5 % auf **6 %** (wie in der GW-Planung oben).
- Dokumentation: **`docs/workstreams/planung/NW_TREND_2025_26.md`**.

---

## 7. Test: Planung mit NW 9 % und GW 6 %

### 7.1 Umsetzung im Script

- Im Script `planung_vorschlag_belastbar.py` wird **nach** dem Basislauf ein zweiter Durchlauf mit **`marge_override={'NW': 9, 'GW': 6}`** ausgeführt.
- Die Funktion `build_planungsvorschlag(gj, standort, marge_override)` nutzt für NW und GW dann 9 % bzw. 6 % statt 8 % bzw. 5 %.

### 7.2 Testergebnis (Beispiel)

- **Plan-DB1 gesamt:** 4.024.578 € (statt 3.824.625 € im Basis-Szenario).
- **Plan-Ergebnis:** -949.781 € (statt -1.149.734 €).
- **Plan-Rendite:** -3,57 % (statt -4,33 %).
- **Differenz zum Basisszenario:** **+199.953 € DB1** bzw. **+199.953 € Ergebnis**.

Die genauen Zahlen hängen vom aktuellen Datenstand (YTD, Prognose) ab; die Logik und die Richtung der Verbesserung bleiben gültig.

---

## 8. Wichtige Dateien und Befehle

| Zweck | Datei / Befehl |
|-------|-----------------|
| Belastbarer Planungsvorschlag (Basis + Test NW 9 %/GW 6 %) | `python3 scripts/planung_vorschlag_belastbar.py` |
| Ausgabe Markdown Planungsvorschlag | `docs/workstreams/planung/PLANUNGSVORSCHLAG.md` |
| Gewinnzone, Standzeit, Zinskosten, Plan-Zinsen | `python3 scripts/planung_gewinnzone_standzeit_vorschlag.py` |
| Zinskosten-Konten suchen (Santander, Stellantis, Genobank) | `python3 scripts/planung_finde_zinskosten_konten.py` |
| NW-Trend (Sep–Feb, Marge/Stück) | `docs/workstreams/planung/NW_TREND_2025_26.md` |
| Planung Kontext, Workstream | `docs/workstreams/planung/CONTEXT.md` |
| Zinskosten-Quelle, Kritik, Standzeiten | `docs/workstreams/planung/GEWINNZONE_STANDZEIT_VORSCHLAG.md` |
| Ergebnis aus aktuellen Daten (VJ, YTD, Kosten Mittelwert) | `scripts/planung_ergebnis_aus_aktuellen_daten.py` |

---

## 9. Technik und Datenquellen

- **Portal-DB (PostgreSQL):** `loco_journal_accountings`, `fahrzeugfinanzierungen`; Verbindung über `api/db_connection.py` (`get_db()`).
- **Locosoft (read-only):** `dealer_vehicles`, `journal_accountings`; Verbindung über `api/db_utils.py` (`locosoft_session()`).
- **Standort:** Konzern = 0; 1 = Deggendorf, 2 = Hyundai, 3 = Landau.
- **GJ-Monate:** 1 = Sep, …, 12 = Aug. Geschäftsjahr z. B. 2025/26 = Sep 2025 – Aug 2026.
- **BWA-Konten:** NW Umsatz 81xxxx, Einsatz 71xxxx; GW Umsatz 82xxxx (ohne 827051 Umlage), Einsatz 72xxxx. G&V-Filter: `get_guv_filter()` aus `api/db_utils.py`.

---

## 10. Was du in einer neuen Claude-Session sagen kannst

Du kannst z. B. so prompten:

- „Lies `docs/workstreams/planung/ZUSAMMENFASSUNG_PLANUNG_GW_NW_2025_26.md` und CLAUDE.md. Dann [konkrete Frage, z. B.: Planungsvorschlag dauerhaft auf NW 9 % und GW 6 % umstellen / GW-Zahl 859 im Plan abbilden / …].“
- „Laut ZUSAMMENFASSUNG_PLANUNG_GW_NW_2025_26: GW 859, 6 % DB, NW-Trend 9 %. Bitte [Erweiterung/Anpassung/Export] im Planungsvorschlag vornehmen.“

Damit hat die nächste Session den vollen Kontext (Annahmen, Rechnungen, Scripts, Pfade) und kann gezielt weiterarbeiten.
