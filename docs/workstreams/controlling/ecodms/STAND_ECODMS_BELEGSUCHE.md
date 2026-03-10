# ecoDMS Belegsuche — Stand & Änderungshistorie

**Workstream:** Controlling (Bankenspiegel / Kategorisierung)

## Aktueller Stand (2026-02-28)

- **Suche:** Nur **Belegdatum** + **Ordner** (konfigurierter Ordner + Buchhaltung 1). Kein Filter mehr nach Transaktionstext (Kreditor/Rechnungsnummer), da in der Praxis oft 0 Treffer oder unpassende Belege.
- **UI:** Nutzer wählt den passenden Beleg aus der Liste; Transaktionstext wird nur als Hinweis angezeigt.
- **API:** `api/ecodms_api.py` → `search_belege(buchungsdatum, …)`; Endpoints unter `api/bankenspiegel_api.py` (transaktionen/ecodms/*).

## Entwicklung über mehrere Chats/Sessions

Die ecoDMS-Anbindung und die Belegsuche wurden in **mehreren Cursor-Chats** umgesetzt und angepasst (Filter nach Rechnungsnummer/Kreditor, Fallback-Ordner Buchhaltung, dann Umstellung auf reine Datums-Suche). Einheitliche Dokumentation des aktuellen Verhaltens steht in:

- **CONTEXT.md** (Controlling) — Abschnitt „ecoDMS Belege zur Kategorisierung“
- **ECODMS_API_PLAN_UND_TEST.md** (dieser Ordner)
- **api/ecodms_api.py** — Docstring von `search_belege`

Bei weiteren Änderungen: CONTEXT.md und ggf. dieses Dokument aktualisieren.
