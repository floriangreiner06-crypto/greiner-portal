# KPI & Handlungsempfehlungen – DRIVE-weit

**Gültig für:** Alle Workstreams und alle im Portal angezeigten Kennzahlen.

---

## Grundsatz

1. **KPIs müssen belastbar und korrekt sein.**  
   Jede Kennzahl muss fachlich stimmen, nachvollziehbar berechnet werden und aus einer einzigen Quelle (SSOT) kommen. Bei Unsicherheit: validieren, in Doku festhalten oder erst nach Klärung ausrollen.

2. **Zu jeder KPI eine Handlungsempfehlung.**  
   Wo eine KPI angezeigt wird, soll eine konkrete Handlungsempfehlung entwickelt und angegeben werden. **Zuerst vorschlagen (z. B. in Doku, CONTEXT.md, Controlling), nicht gleich coden** – nach Freigabe können Empfehlungen in UI oder Reports umgesetzt werden.

---

## Warum Handlungsempfehlungen?

- Kennzahlen allein beantworten oft nicht: „Was soll ich jetzt tun?“
- Kurze, klare Empfehlungen erhöhen den Nutzen von Dashboards und Reports.
- Einheitliche Regel: Keine KPI ohne zugehörige Empfehlung (mindestens als Ziel formuliert, wo noch nicht umgesetzt).

---

## Beispiele (Orientierung)

| KPI / Kontext | Beispiel Handlungsempfehlung |
|---------------|------------------------------|
| TEK Breakeven (DB1 vs. Kosten) | „Wenn hochgerechneter DB1 unter Breakeven: Kosten prüfen, Fokus auf margenstarke Bereiche.“ |
| Liquiditätsvorschau, Saldo unter Mindestbestand | „Wenn projizierter Saldo unter X €: kurzfristige Liquidität sichern (z. B. Fälligkeiten prüfen, Dispo).“ |
| KST-Ziele, Tagesstatus | „Wenn IST unter Soll: …“ (workstreamspezifisch ausformulieren.) |
| Offene Posten (OPOS), Alter | „Wenn Posten älter als X Tage: Mahnstufe prüfen, Kundenkontakt.“ |

---

## KI-gestützte Handlungsempfehlungen (LM Studio)

**Ja – LM Studio kann für Handlungsempfehlungen genutzt werden.**

- **Bereits im Einsatz:** LM Studio (RZ) wird u. a. für Hilfe „Mit KI erweitern“, Transaktions-Kategorisierung, Fahrzeugschein-OCR und Regelwerk-Extraktion genutzt (`api/ai_api.py`, `lm_studio_client`).
- **Idee:** Zu einer KPI den Kontext (Kennzahl, Schwellwert, Vergleich, ggf. SSOT-Snippet aus Workstream-Doku) an LM Studio übergeben und eine **kurze, konkrete Handlungsempfehlung auf Deutsch** generieren lassen.
- **Umsetzung:** Zuerst **Vorschläge** für Empfehlungen (und ggf. KI-Nutzung) machen – nicht sofort coden. Nach Freigabe: z. B. On-demand-Button oder Anzeige beim Laden (mit Caching).
- **Qualität:** Feste Regeln/Texte pro KPI bleiben die Basis; LM Studio kann sie ergänzen oder situationsabhängig formulieren. Ausgabe auf Länge und Ton prüfen (Prompt + max_tokens).

---

## Umsetzung in den Workstreams

- **Neue KPIs:** Im gleichen Zug Definition der Kennzahl + **Vorschlag** für eine Handlungsempfehlung (z. B. in Doku, CONTEXT.md); erst nach Freigabe in UI/Tooltip coden; optional später LM Studio für dynamische Empfehlung.
- **Bestehende KPIs:** Nach und nach Handlungsempfehlungen **vorschlagen** (in CONTEXT.md oder diesem Doc); wo noch offen, vermerken.
- **Referenzen:** CLAUDE.md und .cursorrules verweisen auf dieses Prinzip; diese Datei ist die zentrale Referenz für KPI + Handlungsempfehlung.
