# Konzept: Natursprachliche Analysen auf echten DRIVE-Geschäftsdaten (LM Studio)

**Stand:** 2026-03-09  
**Workstream:** integrations  
**Ziel:** KI-Integration (LM Studio) für Fragen in natürlicher Sprache nutzen, die mit **echten Geschäftsdaten aus DRIVE** beantwortet werden.

---

## Klarstellung: LM Studio (nicht „ML Studio“)

- **LM Studio** = lokaler LLM-Server (z. B. 46.229.10.1:4433), bereits im Einsatz für: Transaktions-Kategorisierung, Arbeitskarten-Prüfung, TT-Zeit-Analyse, Hilfe „Mit KI erweitern“, Unfall-Gutachten-Extraktion.
- **ML (XGBoost)** in `api/ml_api.py` = prädiktive Kennzahlen (Auftragsdauer-Vorhersage), keine Sprach-KI.

Für **natursprachliche Analysen** ist **LM Studio** die richtige Integration.

---

## Ausgangslage

- Nutzer sollen Fragen stellen wie: *„Wie war der Auftragseingang im Februar?“*, *„Top 5 Verkäufer nach DB1?“*, *„Wie steht die TEK heute?“*.
- Antworten sollen auf **echten DRIVE-Daten** basieren (Verkauf, TEK, Bankenspiegel-Aggregate usw.), nicht auf generischen Aussagen.

---

## Architektur (sicher, ohne freie SQL-Generierung)

**Prinzip:** Das LLM **generiert kein SQL** und führt keine beliebigen DB-Abfragen aus. Stattdessen:

1. **Vordefinierte Daten-Views:** Backend stellt für den Nutzer konfigurierbare **Daten-Schnappschüsse** aus DRIVE bereit (z. B. TEK-Kennzahlen, Auftragseingang nach Monat, Bankenspiegel-Summen nach Kategorie). Diese werden über bestehende SSOT-APIs/Datenlayer geholt (`controlling_data.get_tek_data`, `verkauf_data`, `bankenspiegel_api` etc.).
2. **Berechtigung:** Nur Daten, die der Nutzer ohnehin sehen darf (Feature + Rolle), werden in den Kontext gepackt.
3. **Prompt:** Nutzerfrage + strukturierte Kontext-Daten (JSON/Text) werden an LM Studio geschickt mit der Anweisung: „Beantworte die Frage ausschließlich anhand der folgenden Daten. Erfinde keine Zahlen.“
4. **Antwort:** LM Studio formuliert eine kurze, verständliche Antwort (und optional 1–2 Handlungsempfehlungen, wo sinnvoll).

Vorteile:
- Kein SQL-Injection-Risiko, keine unbekannten Queries.
- Volle Kontrolle über Datenmenge und -qualität (SSOT).
- Rechte bleiben im Backend (bestehende `can_access_feature`, Rollen).

---

## Mögliche Datenquellen (Beispiele)

| Bereich        | Daten (Beispiel)                    | SSOT / API                    |
|----------------|------------------------------------|-------------------------------|
| TEK / Controlling | Umsatz, Einsatz, DB1, Breakeven, Werktage | `api/controlling_data.get_tek_data` |
| Verkauf       | Auftragseingang nach Monat/Marke   | `api/verkauf_data` / Routes   |
| Bankenspiegel  | Salden, Summen nach Kategorie      | `api/bankenspiegel_api`        |
| Verkäufer-Ziele | Soll/Ist, Top-N Verkäufer         | `api/verkaeufer_zielplanung_api` |

Weitere Bereiche (Urlaub, Teile, Werkstatt) nach Bedarf ergänzbar; jeweils über bestehende APIs, keine neuen Roh-SQL-Views für das LLM.

---

## Rechte & Sichtbarkeit

- Neuer Feature-Flag z. B. `nl_analyse` oder Nutzung bestehender Features (z. B. `controlling`, `verkauf`).
- Pro Bereich: Nur die Daten laden, die `current_user` sehen darf (wie in den bestehenden Dashboards).
- Keine Weitergabe von personenbezogenen oder sensiblen Rohdaten ins LLM beyond dem, was für die Antwort nötig ist (z. B. aggregierte Kennzahlen, keine Einzelpersonen-Details außer wenn berechtigt).

---

## Technische Umsetzung (Vorschlag)

1. **Neuer Endpoint:** z. B. `POST /api/ai/analyse/geschaeftsdaten`
   - Body: `{ "frage": "Wie war der Auftragseingang im Februar?" }`
   - Optional: `bereich` (z. B. `tek`, `verkauf`, `bankenspiegel`) oder automatische Auswahl anhand der Frage (zweiter Schritt).

2. **Backend:**
   - Frage parsen oder Bereich aus Parameter übernehmen.
   - Je nach Bereich/Rechten die passenden SSOT-Funktionen aufrufen und ein **kompaktes JSON** (oder Fließtext) mit Kennzahlen/Datumsbereich erzeugen.
   - LM-Studio-Client aufrufen: System-Prompt („Du bist ein Assistent für DRIVE-Kennzahlen. Antworte nur auf Basis der folgenden Daten.“) + User-Prompt (Frage + Kontext-Daten).
   - Antwort zurückgeben (Text; optional strukturiert mit `zusammenfassung`, `kennzahlen`, `handlungsempfehlung`).

3. **Frontend:** Optional eine kleine „Frage stellen“-Box in einem bestehenden Dashboard (z. B. Controlling oder Startseite), die den Endpoint aufruft und die Antwort anzeigt.

---

## Implementierung (Stand 2026-03-09)

- **Endpoint:** `POST /api/ai/analyse/geschaeftsdaten`
- **Body:** `{ "frage": "Wie steht die TEK heute?", "bereich": "tek" }` (bereich optional, Default: tek)
- **Recht:** Feature `controlling` erforderlich.
- **Erster Bereich:** `tek` – lädt SSOT-Daten aus `get_tek_data(aktueller Monat/Jahr)`, baut Kontext, sendet an LM Studio, liefert `{ "success", "antwort", "kontext_bereich", "stichtag" }`.
- Code: `api/ai_api.py` (Funktion `analyse_geschaeftsdaten`, Helper `_build_tek_context`).

## Nächste Schritte

1. **Weitere Bereiche:** z. B. `verkauf` (Auftragseingang), `bankenspiegel` (Aggregate) – analog mit vordefinierten Daten-Views.
2. **Frontend:** Optionale „Frage stellen“-Box in einem Dashboard (z. B. TEK/Controlling), die den Endpoint aufruft.
3. **CONTEXT.md:** integrations um „NL-Analysen DRIVE-Daten“ ergänzen (erledigt bei Bedarf).

---

## Kurzantwort

**Können wir die KI-Integration für natursprachliche Analysen auf echten Geschäftsdaten aus DRIVE nutzen (LM Studio)?**  

**Ja.** Mit der bestehenden LM-Studio-Anbindung ist das machbar. Sicher und sinnvoll ist es, **keine freie SQL-Generierung** durch das LLM zu erlauben, sondern **vordefinierte Daten-Views** aus unseren SSOT-APIs zu laden und diese als Kontext an LM Studio zu senden. Die KI formuliert dann die Antwort in natürlicher Sprache auf Basis dieser Daten. Rechte und Datenmenge bleiben im Backend unter Kontrolle.
