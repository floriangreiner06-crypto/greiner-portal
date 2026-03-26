# Gudat-Fakturierungsstatus in DRIVE – Machbarkeit

**Stand:** 2026-02-26  
**Workstream:** werkstatt  
**Frage:** Können die Gudat-Status „interne Abrechnung fakturiert“ und „Auftrag fakturiert“ in DRIVE angezeigt/verwendet werden?

## Ausgangslage (Screenshots)

- **Gudat:** Zeigt für den Auftrag grüne Status „interne Abrechnung Vorgang fakturiert“ und „Auftrag fakturiert“.
- **DRIVE:** Zeigt korrekt „Fakturiert: 0 AW | Offen: 5 AW“ (Quelle: Locosoft `labours.is_invoiced`).
- **Realität:** Der Auftrag wurde vergessen abzurechnen; nur der Status in Gudat wurde geändert.

DRIVE wertet damit **richtig** aus: SSOT für die tatsächliche Abrechnung ist Locosoft. Gudat-Status sind Prozess-/Vorgangsstatus und können von der Realität abweichen.

## Machbarkeit: **Ja**

### 1. Woher kommen die Gudat-Status?

Die Status wie „interne Abrechnung Vorgang fakturiert“ und „Auftrag fakturiert“ kommen in Gudat vom **Dossier** und sind über die GraphQL-API abrufbar:

- **Pfad:** `dossier.states[]` mit `{ id, name }`
- **Beleg:** In `tools/gudat_termine_export.py` wird bereits `dossier.states { id name }` abgefragt; `states[].name` entspricht dem „Vorgangsstatus“ (inkl. Fakturierungsstatus).

### 2. Was fehlt aktuell in DRIVE?

- **Auftragsdetail:** `api/werkstatt_live_api.py` → `get_auftrag_detail(auftrag_nr)` lädt bereits Gudat-Daten über `hole_arbeitskarte_daten(auftrag_nr)`. Dort wird das **Dossier** per GraphQL geholt (`api/arbeitskarte_api.py`, Query `GetDossierDrawerData`).
- Die aktuelle Dossier-Query fragt **nicht** `states` ab. Sobald `states { id name }` am Dossier angefragt wird, stehen die gleichen Status wie in der Gudat-UI (inkl. „interne Abrechnung … fakturiert“, „Auftrag fakturiert“) zur Verfügung.

### 3. Sinnvoller Use-Case

Die Gudat-Status **nicht** als Ersatz für Locosoft nutzen (das wäre fachlich falsch), sondern **ergänzend** anzeigen:

- **Locosoft (SSOT):** „Fakturiert: X AW | Offen: Y AW“ (wie heute).
- **Gudat:** Zusätzlich z. B. „Gudat-Vorgangsstatus: [Auftrag fakturiert], [interne Abrechnung Vorgang fakturiert].“

Bei **Abweichung** (Gudat = „fakturiert“, Locosoft = AW noch offen) ist so sofort erkennbar: „In Gudat als erledigt markiert, aber noch nicht abgerechnet“ – genau der Fall aus den Screenshots.

### 4. Technische Umsetzung (Kurz)

| Schritt | Ort | Aktion |
|--------|-----|--------|
| 1 | `api/arbeitskarte_api.py` | In der Dossier-GraphQL-Query (GetDossierDrawerData + Fallbacks) `states { id name }` am `dossier` anfragen. |
| 2 | `api/arbeitskarte_api.py` | In `gudat_daten` z. B. `'states': dossier.get('states', [])` übernehmen (Liste der Objekte mit `name` = Status-Label). |
| 3 | Frontend Auftrags-Modal | Gudat-Status (z. B. als Badges/Liste) anzeigen, klar getrennt von „Fakturiert/Offen (Locosoft)“. Optional: Hinweis, wenn Gudat „fakturiert“ zeigt, Locosoft aber noch AW offen hat. |

### 5. Einbauort (Vorschlag) – umgesetzt

- **Stelle:** Im **Auftrags-Detail-Modal**, direkt unter dem Block „AW-Summen“ (Fakturiert/Offen) und den Status-Badges, **vor** der Tabelle „Positionen“. So sehen Mitarbeiter zuerst die Locosoft-Werte und darunter die Gudat-Vorgangsstatus zur Kontrolle.
- **Inhalt:**
  - Überschrift: „Gudat-Vorgangsstatus (zur Kontrolle)“
  - Liste der Status-Namen aus Gudat als Badges (z. B. „Auftrag fakturiert“, „interne Abrechnung Vorgang fakturiert“).
  - **Diskrepanz-Hinweis:** Wenn mindestens ein Gudat-Status „fakturiert“ enthält **und** in Locosoft noch offene AW existieren: gelber Hinweis „In Gudat als erledigt markiert – in Locosoft noch nicht abgerechnet. Bitte prüfen.“
- **Bereits umgesetzt in:**
  - `templates/aftersales/werkstatt_uebersicht.html` (Werkstatt-Übersicht)
  - `templates/sb/werkstatt_uebersicht.html` (Serviceberater-Werkstatt-Übersicht)
- **Gleicher Block kann übernommen werden in:** Werkstatt Live (`werkstatt_live.html`), Stempeluhr, Tagesbericht, Garantie-Aufträge, Kapazitätsplanung, Cockpit, Liveboard – überall dort, wo das Auftrags-Modal per `/api/werkstatt/live/auftrag/<nr>` befüllt wird und `data.gudat` sowie `data.auftrag.summen.offen_aw` verfügbar sind.

### 6. SSOT-Regel

- **Fakturierung (AW/Rechnung):** SSOT bleibt **Locosoft** (`labours.is_invoiced`, `invoices`). Keine Entscheidung „ist abgerechnet“ aus Gudat ableiten.
- **Gudat-Status:** Nur als **Anzeige/Abgleich** nutzen, um Diskrepanzen („in Gudat abgehakt, in Locosoft noch offen“) sichtbar zu machen.

## Fazit

- **Machbarkeit:** Ja; die nötigen Daten liefert die Gudat GraphQL API über `dossier.states`.
- **Aufwand:** Gering (Query erweitern, Daten durchreichen, kleine UI-Erweiterung im Auftrags-Modal).
- **Empfehlung:** Umsetzung wie unter Abschnitt 4, mit klarer Trennung „Locosoft = Fakturierung“, „Gudat = Vorgangsstatus“ und optionalem Diskrepanz-Hinweis.
