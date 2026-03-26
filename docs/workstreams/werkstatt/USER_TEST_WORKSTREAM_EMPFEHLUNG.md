# User-Tests: Eigener Workstream oder dem getesteten Workstream zuordnen?

**Stand:** 2026-02-26

## Empfehlung: **Testanleitungen dem getesteten Workstream zuordnen**

- **Testanleitungen** (z. B. für Edith, Offene Aufträge) liegen im **Workstream des getesteten Features** – hier: `docs/workstreams/werkstatt/`.
- **Vorteile:** Kontext bleibt gebündelt (Werkstatt-Feature + Testanleitung + spätere Anpassungen an einem Ort). Wer am Workstream arbeitet, hat die Testdoku direkt dabei. Kein zusätzlicher Workstream für „nur“ Testanleitungen nötig.
- **Struktur:** Pro Feature/Release eine Testanleitung, z. B. `TESTANLEITUNG_EDITH_OFFENE_AUFTRAEGE.md` im Werkstatt-Ordner. Weitere Tester:innen (z. B. Vanessa Urlaubsplaner) → Testanleitung im jeweiligen Workstream (z. B. `docs/workstreams/urlaubsplaner/`).

## Wann ein eigener Workstream „Testing/QA“ sinnvoll sein kann

- Wenn **übergreifende** Testprozesse, Testdaten oder QA-Richtlinien für das gesamte Portal dokumentiert werden (z. B. „Wie testen wir Rollouts?“).
- Wenn eine zentrale **Test-Checkliste** oder ein **Release-Testplan** viele Workstreams berührt und an einer Stelle gepflegt werden soll.

**Kurz:** Für **Feature-spezifische User-Tests** (wie Edith für Offene Aufträge) → Testanleitung im **betroffenen Workstream** belassen. Für **portalweite QA-Prozesse** kann später ein eigener Workstream angelegt werden.
