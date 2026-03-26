# Konzept: Kontext-Injection für KI „Mit KI erweitern“

**Stand:** 2026-02-24  
**Workstream:** Hilfe

---

## Ausgangslage

Hilfe-Artikel (z. B. „TEK“ / „Breakeven“) enthalten oft nur **Begriffsdefinitionen**, aber keine **Berechnungslogik** (z. B. rollierender Schnitt, Werktage, BWA-Kosten). Die KI kann solche Lücken **erkennen und fachlich korrekt ergänzen**, wenn wir ihr gezielt **Kontext aus unserer SSOT** (Code/Doku) mitsenden – **Kontext-Injection**.

---

## Funktionsweise

1. **„Mit KI erweitern“** (geplant): Admin klickt bei einem Artikel auf „Mit KI erweitern“.
2. **Kontext-Lookup:** Backend prüft **Titel** und **Tags** des Artikels (z. B. `tek`, `breakeven`, `erfolgskontrolle`).
3. **Registry:** Eine **Kontext-Registry** (`hilfe_ki_kontext_registry.md` oder Python-Dict) liefert pro Thema einen **kurzen, redigierten SSOT-Text** (kein Code, sondern fachliche Beschreibung der Berechnung/Logik).
4. **Prompt:** An Bedrock wird gesendet: **aktueller Artikel-Inhalt** + **„Fachlicher Kontext (SSOT): …“** mit dem passenden Registry-Eintrag.
5. **Auftrag an die KI:** „Ergänze den Artikel um fehlende **Berechnungsdetails** (z. B. wie Breakeven/Einsatz berechnet werden), ohne die bestehende Struktur zu zerstören. Nutze ausschließlich den angegebenen fachlichen Kontext.“

Ergebnis: Die KI fügt z. B. bei „Breakeven“ einen Abschnitt „So berechnet das DRIVE den Breakeven“ ein (rollierender Schnitt, BWA-Kosten, Werktage, Stichtag 19:00) – **ohne** sich die Logik aus den Fingern zu saugen.

---

## Wann Kontext nutzen?

- **Tags/Kategorie:** Artikel mit Tag `tek`, `breakeven`, `kennzahlen` oder Kategorie „Controlling“ → Kontext „TEK/Breakeven“ injizieren.
- **Titel:** Enthält „TEK“, „Breakeven“, „Einsatz“, „DB1“ → gleicher Kontext.
- Optional: Weitere Einträge für andere Module (z. B. Urlaubsplaner, Bankenspiegel), sobald SSOT-Doku oder Snippets vorliegen.

---

## Registry-Pflege

- **Datei:** `docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md` – pro Thema ein Abschnitt mit **Schlüsselwörtern** (Tags/Titel-Matching) und **Kontext für KI** (reiner Fließtext, keine Code-Blöcke, maximal 1–2 Absätze).
- **Quelle:** SSOT (z. B. `api/controlling_data.py`, CLAUDE.md, Workstream-Docs); bei Änderung der Berechnungslogik Registry aktualisieren.

---

## Umsetzung (später)

- Beim Implementieren von `POST /api/hilfe/ki/erweitern`: Artikel aus DB laden, anhand von `titel` und `tags` passenden Registry-Eintrag auslesen, an den Prompt anhängen.
- Optional: Registry als Python-Dict in `api/hilfe_bedrock_service.py` oder aus Markdown parsen, damit keine doppelte Pflege entsteht.

---

## Kurzantwort für Nutzer

**Kann die KI erkennen, dass bei „Breakeven“ die Berechnung fehlt, und die Hilfe ergänzen?**  
**Ja.** Dafür braucht die KI **Kontext aus unserem System** (wie wir Breakeven/Einsatz berechnen). Wenn wir beim „Mit KI erweitern“ diesen Kontext aus einer kleinen **Kontext-Registry** (z. B. TEK/Breakeven = rollierender Schnitt, BWA-Kosten, Werktage) mitsenden, kann die KI den Artikel **fachlich korrekt** um die fehlenden Berechnungsdetails erweitern.
