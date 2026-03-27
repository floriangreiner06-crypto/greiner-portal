# /feature - Neues Feature planen

Plant die Implementierung eines neuen Features. Sammelt Anforderungen, analysiert technisch, prueft SSOT, traegt in CONTEXT.md ein und wartet auf OK.

## Voraussetzung: develop-Branch

```bash
pwd && git branch --show-current
```

Wenn nicht auf `develop` in `/opt/greiner-test/`: den User darauf hinweisen. Neue Features gehoeren in develop, nicht in main.

## Schritt 1: Anforderungen sammeln

Den User fragen:
- Was soll das Feature tun? (fachliche Beschreibung)
- Wer nutzt es? (Rolle: Verkaeufer, Admin, Werkstatt, GL)
- Welcher Workstream gehoert es zu?
- Gibt es Mockups, Screenshots oder Beispiele?
- Gibt es Abhaengigkeiten zu anderen Features?

## Schritt 2: Technische Analyse

### Betroffene Module identifizieren

Relevante vorhandene Dateien pruefen:
- `api/[workstream]_api.py` -- existiert schon?
- `routes/[workstream]_routes.py` -- existiert schon?
- `templates/[bereich]/` -- welche Templates betroffen?

### DB-Analyse

Tabellen und Felder pruefen die benoetigt werden:

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "\dt" | grep [relevant]
```

Neue Tabellen oder Spalten noetig? Migration anlegen als `migrations/[name].sql`.

### Navigation

Neuer Menupunkt noetig? `navigation_items`-Tabelle pruefen:

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -c "SELECT id, parent_id, label, url FROM navigation_items ORDER BY parent_id, order_index;"
```

## Schritt 3: SSOT pruefen

Vor der Implementierung sicherstellen dass keine parallele Logik entsteht:

- Gibt es bereits eine Funktion die dasselbe berechnet?
- Gibt es ein bestehendes Modul das erweitert werden sollte statt ein neues anzulegen?
- TEK-Berechnungen: `api/controlling_data.py` verwenden
- Standort-Logik: `api/standort_utils.py` verwenden
- DB-Verbindungen: `api/db_connection.py` -> `get_db()` verwenden

Wenn SSOT-Verszich vorhanden: den User informieren und Loesung vorschlagen.

## Schritt 4: Implementierungsplan erstellen

Konkreter Plan mit Schritten:

1. **Datenbank:** Neue Tabelle/Spalte, Migration-Datei
2. **API:** Neue Funktionen in `api/[modul]_api.py`
3. **Routes:** Neue Endpoints in `routes/[modul]_routes.py`
4. **Templates:** Neue oder geaenderte HTML-Dateien
5. **Navigation:** Neuer Eintrag in `navigation_items` falls noetig
6. **Tests:** Welche Endpoints nach Implementierung testen?

## Schritt 5: CONTEXT.md aktualisieren

In `docs/workstreams/[workstream]/CONTEXT.md` eintragen:
- Geplantes Feature unter "Naechste Schritte" oder "In Planung"
- Technische Entscheidungen festhalten
- Abhaengigkeiten notieren

## Schritt 6: OK abwarten

Den Plan ausgeben und explizit warten auf Bestaetigung: "Soll ich mit der Implementierung starten?"

Nicht eigenstaendig mit dem Coden anfangen -- erst nach "Ja" oder "Los geht's" o.ae.

## Greiner Portal Architektur-Muster

```
api/[modul]_api.py        -- Datenbanklogik, Berechnungen
routes/[modul]_routes.py  -- Flask-Endpoints, Blueprint
templates/[bereich]/      -- Jinja2-Templates
migrations/[name].sql     -- DB-Schema-Aenderungen
```

Blueprints werden in `app.py` registriert.
