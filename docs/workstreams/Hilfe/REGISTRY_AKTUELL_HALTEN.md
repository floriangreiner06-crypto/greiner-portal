# Kontext-Registry aktuell halten

**Zweck:** Die KI-Registry für „Mit KI erweitern“ soll die **aktuelle** fachliche Logik des DRIVE widerspiegeln. Dieser Prozess und die Quellen-Zuordnung sorgen dafür, dass Änderungen im Code/Doku in der Registry ankommen.

---

## Wo lebt die Registry?

| Ort | Rolle |
|-----|--------|
| **`api/hilfe_bedrock_service.py`** | **Quelle der Wahrheit.** Das Dict `HILFE_KI_KONTEXT_REGISTRY` wird von der Anwendung gelesen. Hier muss jeder inhaltliche Update passieren. |
| **`docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md`** | Lesefassung für Menschen (Redakteure, Entwickler). Nach Änderung in der .py **synchron halten**. |

---

## Quellen-Zuordnung („Bei Änderung hier → Registry dort prüfen“)

Wenn ihr **fachliche Logik** in den folgenden Modulen ändert, den zugehörigen Registry-Eintrag prüfen und ggf. anpassen.

| Registry-Eintrag (Schlüssel) | Quellen im Projekt | Wann aktualisieren? |
|-----------------------------|--------------------|----------------------|
| **tek** (und breakeven, einsatz, db1, …) | `api/controlling_data.py` (get_tek_data, breakeven), TEK-Doku in docs/workstreams/controlling/ | Änderung an Umsatz/Einsatz/DB1/Breakeven-Formel, Werktagen, BWA-Kosten |
| **urlaub** (und resturlaub, urlaubsplaner, …) | `api/vacation_api.py`, `api/vacation_locosoft_service.py`, `docs/workstreams/urlaubsplaner/STELLUNGNAHME_ROLLOUT_SSOT_OHNE_LOCOSOFT.md`, `RESTURLAUB_KEINE_KRANKHEIT.md`, CONTEXT.md Urlaubsplaner | Änderung an Resturlaub-Formel, Anspruch, Locosoft-Nutzung, Krankheit/ZA |
| *(weitere nach Bedarf)* | z. B. bankenspiegel_api.py, verkauf_api.py | Bei neuen Einträgen diese Tabelle ergänzen |

**Neue Einträge:** Wenn ein neues Thema (z. B. Bankenspiegel, Verkauf-Zielplanung) in die Registry aufgenommen wird: hier eine Zeile hinzufügen mit Schlüssel, Quellen und „Wann aktualisieren?“.

---

## Prozess: Registry aktuell halten

1. **Bei fachlicher Änderung in einem Modul** (z. B. „Resturlaub nur noch aus Portal, kein Locosoft“):
   - In dieser Tabelle nachsehen: welcher Registry-Eintrag hängt an diesem Modul?
   - In **`api/hilfe_bedrock_service.py`** den entsprechenden Eintrag in `HILFE_KI_KONTEXT_REGISTRY` anpassen (Text so formulieren, dass die KI die **neue** Logik in Hilfe-Artikeln beschreibt).
   - **`docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md`** mit dem gleichen Inhalt aktualisieren (Abschnitt für dieses Thema).
   - Optional: In diesem Doc (REGISTRY_AKTUELL_HALTEN.md) die Zeile „Quellen“ ergänzen, falls neue relevante Dateien dazu gekommen sind.

2. **Neues Thema für die KI-Hilfe:**
   - Neuen Eintrag in `HILFE_KI_KONTEXT_REGISTRY` anlegen (plus ggf. Aliase wie bei tek/urlaub).
   - Neuen Abschnitt in `hilfe_ki_kontext_registry.md` anlegen.
   - In der Tabelle oben eine neue Zeile mit Schlüssel, Quellen und „Wann aktualisieren?“ ergänzen.

3. **Review:** Bei MRs/Commits, die fachliche Kernlogik ändern (Controlling, Urlaub, Banken, …), im Commit-Kommentar oder in der MR-Beschreibung prüfen: **Registry betroffen?** Wenn ja, Registry-Update im gleichen Commit/MR.

---

## Kurz-Checkliste pro Änderung

- [ ] Code/Doku geändert (z. B. Resturlaub-Formel, TEK-Breakeven)?
- [ ] In REGISTRY_AKTUELL_HALTEN.md nachsehen: welcher Eintrag?
- [ ] `api/hilfe_bedrock_service.py` → `HILFE_KI_KONTEXT_REGISTRY` angepasst?
- [ ] `docs/workstreams/Hilfe/hilfe_ki_kontext_registry.md` synchron gehalten?

So bleibt die Registry eine aktuelle Abbildung der fachlichen SSOT für die KI-Erweiterung.

---

## Automatische Prüfung bei Session-Ende

Beim **Session-End** (.cursor/commands/session-end.md) führt der Agent aus:

- **`python3 scripts/check_hilfe_registry.py`**  
  Der Script vergleicht die Änderungszeit der Registry-Dateien mit den in dieser Tabelle genannten Quell-Dateien. Sind Quellen **neuer** als die Registry, gibt der Script die betroffenen Einträge aus und beendet mit Exit 1. Der Agent soll dann die genannten Einträge prüfen und ggf. in `api/hilfe_bedrock_service.py` und `hilfe_ki_kontext_registry.md` anpassen.

Neue Registry-Einträge und ihre Quellen in **`scripts/check_hilfe_registry.py`** in `SOURCES_BY_ENTRY` ergänzen, damit sie bei Session-End mitgeprüft werden.
