<!--
  HINWEIS: Dieser Prompt wurde von Claude (claude.ai) erstellt und kennt nicht den
  aktuellen DRIVE-Stand (PostgreSQL, Bootstrap 5, DB-Navigation, Server=Master).
  Für den an DRIVE angepassten Entwicklungsvorschlag siehe: ENTWURF_HILFE_MODUL.md
-->

# CURSOR TASK: Hilfe-System für DRIVE Portal aufbauen

## KONTEXT

Du arbeitest am **Greiner DRIVE Portal** – einem internen ERP-System für ein Autohaus (Autohaus Greiner, Opel/Stellantis + Hyundai + Leapmotor). Das Portal läuft auf einem Linux-Server unter `/opt/greiner-portal/` und ist eine Flask-App mit SQLite, PostgreSQL (Locosoft-Anbindung), LDAP-Auth, Bootstrap 4, jQuery.

**Dein erster Schritt ist IMMER: Den aktuellen Stand des Projekts analysieren.** Ich beschreibe unten die gewünschte Architektur, aber du musst zuerst die bestehende Codebasis lesen, um zu verstehen welche Module, Routes, Templates, APIs und Features aktuell existieren. Der Stand ändert sich laufend.

---

## PHASE 0: CODEBASE-ANALYSE (PFLICHT!)

Bevor du irgendetwas implementierst, führe folgende Analyse durch:

### 0.1 Projektstruktur verstehen
```
- Lies /opt/greiner-portal/app.py → Welche Blueprints sind registriert?
- Lies /opt/greiner-portal/routes/ → Welche Route-Module gibt es?
- Lies /opt/greiner-portal/api/ → Welche API-Blueprints gibt es?
- Lies /opt/greiner-portal/templates/ → Welche Templates existieren?
- Lies /opt/greiner-portal/templates/base.html → Master-Layout, Navigation, eingebundene Libs
- Lies /opt/greiner-portal/static/ → CSS/JS-Struktur
- Lies /opt/greiner-portal/decorators/auth_decorators.py → Auth-Pattern
```

### 0.2 Bestehende Module inventarisieren
Erstelle eine Liste aller aktuell vorhandenen Portal-Module mit:
- Modulname (z.B. Bankenspiegel, Verkauf, Werkstatt, Urlaubsplaner...)
- Haupt-Route(s)
- Template(s)
- Kurzbeschreibung der Funktionalität
- Zielgruppe/Rollen

Diese Liste brauchst du, um die Hilfe-Artikel zu strukturieren.

### 0.3 Navigation & UI-Pattern analysieren
- Wie ist die Sidebar/Navigation aufgebaut?
- Welches Bootstrap-Theme/Layout wird verwendet?
- Gibt es bestehende Modals, Toasts, oder Notification-Patterns?
- Wie werden Icons eingebunden (FontAwesome, etc.)?

### 0.4 Auth-System verstehen
- Welche Rollen gibt es?
- Wie funktioniert @require_auth / @require_role?
- Gibt es ein User-Objekt in der Session?

---

## PHASE 1: HILFE-MODUL AUFBAUEN

### 1.1 Architektur

```
/opt/greiner-portal/
├── api/
│   └── hilfe_api.py              ← NEU: REST-API für Hilfe-Artikel
├── routes/
│   └── hilfe_routes.py           ← NEU: HTML-Routes
├── templates/
│   ├── hilfe/
│   │   ├── hilfe_uebersicht.html ← Hauptseite mit allen Kategorien
│   │   ├── hilfe_kategorie.html  ← Artikel einer Kategorie
│   │   ├── hilfe_artikel.html    ← Einzelner Artikel
│   │   └── hilfe_suche.html      ← Suchergebnisse
│   └── components/
│       └── hilfe_widget.html     ← Chat-Widget (Jinja2-Include für base.html)
├── static/
│   ├── css/
│   │   └── hilfe.css             ← Styling
│   └── js/
│       └── hilfe.js              ← Frontend-Logik + Chat-Widget
├── data/
│   └── greiner_controlling.db    ← Bestehende DB, neue Tabellen hinzufügen
└── migrations/
    └── add_hilfe_tables.sql      ← Migration
```

### 1.2 Datenbank-Schema

```sql
-- Hilfe-Kategorien (= Portal-Module)
CREATE TABLE IF NOT EXISTS hilfe_kategorien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- z.B. "Urlaubsplaner"
    slug TEXT NOT NULL UNIQUE,             -- z.B. "urlaubsplaner"
    beschreibung TEXT,                     -- Kurzbeschreibung
    icon TEXT DEFAULT 'fas fa-question-circle',  -- FontAwesome Icon
    sort_order INTEGER DEFAULT 0,
    modul_route TEXT,                      -- z.B. "/urlaub" - Link zum Modul
    aktiv INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Hilfe-Artikel
CREATE TABLE IF NOT EXISTS hilfe_artikel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kategorie_id INTEGER NOT NULL,
    titel TEXT NOT NULL,                   -- z.B. "Wie beantrage ich Urlaub?"
    slug TEXT NOT NULL,                    -- z.B. "urlaub-beantragen"
    inhalt TEXT NOT NULL,                  -- Markdown oder HTML
    inhalt_format TEXT DEFAULT 'markdown', -- 'markdown' oder 'html'
    tags TEXT,                             -- Komma-separierte Tags für Suche
    sort_order INTEGER DEFAULT 0,
    sichtbar_fuer_rollen TEXT,            -- NULL = alle, sonst z.B. "admin,finance"
    aufrufe INTEGER DEFAULT 0,            -- View-Counter
    hilfreich_ja INTEGER DEFAULT 0,       -- Feedback-Counter
    hilfreich_nein INTEGER DEFAULT 0,
    aktiv INTEGER DEFAULT 1,
    erstellt_von TEXT,                     -- Username
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (kategorie_id) REFERENCES hilfe_kategorien(id)
);

-- Volltext-Suche Index
CREATE VIRTUAL TABLE IF NOT EXISTS hilfe_artikel_fts USING fts5(
    titel, inhalt, tags,
    content='hilfe_artikel',
    content_rowid='id'
);

-- Trigger für FTS-Sync
CREATE TRIGGER IF NOT EXISTS hilfe_artikel_ai AFTER INSERT ON hilfe_artikel BEGIN
    INSERT INTO hilfe_artikel_fts(rowid, titel, inhalt, tags) 
    VALUES (new.id, new.titel, new.inhalt, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS hilfe_artikel_ad AFTER DELETE ON hilfe_artikel BEGIN
    INSERT INTO hilfe_artikel_fts(hilfe_artikel_fts, rowid, titel, inhalt, tags) 
    VALUES ('delete', old.id, old.titel, old.inhalt, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS hilfe_artikel_au AFTER UPDATE ON hilfe_artikel BEGIN
    INSERT INTO hilfe_artikel_fts(hilfe_artikel_fts, rowid, titel, inhalt, tags) 
    VALUES ('delete', old.id, old.titel, old.inhalt, old.tags);
    INSERT INTO hilfe_artikel_fts(rowid, titel, inhalt, tags) 
    VALUES (new.id, new.titel, new.inhalt, new.tags);
END;

-- Hilfe-Feedback (detailliert)
CREATE TABLE IF NOT EXISTS hilfe_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artikel_id INTEGER,
    user_id TEXT,
    hilfreich INTEGER,                    -- 1 = ja, 0 = nein
    kommentar TEXT,                        -- Optionaler Freitext
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (artikel_id) REFERENCES hilfe_artikel(id)
);

-- Hilfe-Chat-Verlauf (für spätere KI-Integration)
CREATE TABLE IF NOT EXISTS hilfe_chat_verlauf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,              -- Eindeutige Chat-Session
    user_id TEXT,
    nachricht TEXT NOT NULL,
    rolle TEXT NOT NULL,                   -- 'user' oder 'assistant'
    kontext_modul TEXT,                    -- Welches Modul war aktiv?
    kontext_seite TEXT,                    -- Welche Seite war offen?
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 1.3 API-Endpoints

```python
# api/hilfe_api.py

Blueprint: hilfe_api, url_prefix='/api/hilfe'

GET  /api/hilfe/kategorien
     → Alle aktiven Kategorien mit Artikel-Anzahl

GET  /api/hilfe/kategorie/<slug>
     → Kategorie mit allen Artikeln

GET  /api/hilfe/artikel/<id>
     → Einzelner Artikel (+ aufrufe++)

GET  /api/hilfe/suche?q=<suchbegriff>
     → Volltextsuche über FTS5

POST /api/hilfe/artikel/<id>/feedback
     Body: { "hilfreich": true/false, "kommentar": "..." }
     → Feedback speichern

GET  /api/hilfe/beliebt
     → Top 10 meistaufgerufene Artikel

GET  /api/hilfe/health
     → Health-Check
```

### 1.4 HTML-Routes

```python
# routes/hilfe_routes.py

GET  /hilfe                         → Übersicht aller Kategorien
GET  /hilfe/<kategorie_slug>        → Artikel einer Kategorie
GET  /hilfe/artikel/<artikel_id>    → Einzelner Artikel
GET  /hilfe/suche?q=...             → Suchergebnisse

# Admin-Bereich (nur @require_role('admin'))
GET  /hilfe/admin                   → Artikel-Verwaltung
GET  /hilfe/admin/neu               → Neuen Artikel erstellen
GET  /hilfe/admin/bearbeiten/<id>   → Artikel bearbeiten
POST /hilfe/admin/speichern         → Artikel speichern
```

---

## PHASE 2: FRONTEND-DESIGN

### 2.1 Design-Prinzipien
- **Konsistent** mit dem bestehenden Portal-Design (Bootstrap 4, gleiche Farben, gleiche Sidebar)
- **Einfach** – keine Überladung, Mitarbeiter sollen schnell finden was sie suchen
- **Durchsuchbar** – prominente Suchleiste oben
- **Kontextuell** – das Hilfe-Widget weiß, auf welcher Seite der User gerade ist

### 2.2 Hilfe-Übersichtsseite
```
┌─────────────────────────────────────────────────┐
│  🔍 Suche in der Hilfe...              [Suchen] │
├─────────────────────────────────────────────────┤
│                                                  │
│  📊 Bankenspiegel    📈 Verkauf                 │
│  5 Artikel           8 Artikel                   │
│                                                  │
│  🏖️ Urlaubsplaner    🔧 Werkstatt              │
│  4 Artikel           6 Artikel                   │
│                                                  │
│  💰 Finanzierungen   👤 Mein Profil             │
│  3 Artikel           2 Artikel                   │
│                                                  │
├─────────────────────────────────────────────────┤
│  ⭐ Häufig gesucht:                             │
│  • Wie beantrage ich Urlaub?                     │
│  • Wo finde ich meine Verkaufszahlen?           │
│  • Was bedeutet DB% im Verkaufsbericht?         │
└─────────────────────────────────────────────────┘
```

### 2.3 Hilfe-Widget (Global)
Ein kleines schwebendes Icon (unten rechts, wie bei Grillfürst), das auf jeder Seite sichtbar ist:

```
┌──────────────────────┐
│ ❓ Hilfe             │
│                      │
│ Du bist auf:         │
│ Urlaubsplaner        │
│                      │
│ 📌 Schnellhilfe:    │
│ • Urlaub beantragen  │
│ • Resturlaub prüfen  │
│ • Team-Übersicht     │
│                      │
│ 🔍 Suche...         │
│                      │
│ [Alle Hilfe-Artikel] │
└──────────────────────┘
```

**Wichtig:** Das Widget erkennt die aktuelle Seite/Route und zeigt kontextbezogene Hilfe-Artikel an. Dazu muss auf jeder Seite ein data-Attribut oder eine JS-Variable das aktuelle Modul identifizieren, z.B.:
```html
<body data-hilfe-modul="urlaubsplaner">
```

### 2.4 Artikel-Ansicht
- Markdown-Rendering im Frontend (z.B. marked.js) ODER serverseitig (Python-Markdown)
- Feedback-Buttons: "War dieser Artikel hilfreich? 👍 👎"
- Breadcrumb-Navigation: Hilfe > Urlaubsplaner > Urlaub beantragen
- "Verwandte Artikel" am Ende (gleiche Kategorie)

---

## PHASE 3: INITIALE HILFE-ARTIKEL

Nachdem du in Phase 0 alle Module analysiert hast, erstelle **für jedes vorhandene Modul** mindestens 3-5 Starter-Artikel. Nutze die Erkenntnisse aus deiner Codebase-Analyse.

### Allgemeine Artikel-Vorlage:
```markdown
# [Titel als Frage formuliert]

## Kurz-Antwort
[1-2 Sätze, die die Kernfrage beantworten]

## Schritt für Schritt
1. ...
2. ...
3. ...

## Hinweise
- ...

## Verwandte Themen
- [Link zu anderem Artikel]
```

### Pflicht-Kategorien (mindestens):

**Allgemein / Erste Schritte:**
- Wie logge ich mich im Portal ein?
- Wie ist das Portal aufgebaut? (Navigation erklären)
- An wen wende ich mich bei Problemen?

**Pro Modul** (basierend auf was du in der Codebase findest):
- Was kann ich in diesem Modul tun?
- Die 2-3 häufigsten Aktionen als Schritt-für-Schritt
- Erklärung wichtiger Begriffe/Kennzahlen

Die Artikel sollen in einem Migrations-Script als INSERT-Statements erstellt werden, damit sie reproduzierbar sind.

---

## PHASE 4: KI-CHAT VORBEREITUNG (OPTIONAL / SPÄTER)

### 4.1 Chat-Widget Grundgerüst
Baue das Chat-UI bereits auf, aber zunächst OHNE KI-Backend. Stattdessen:
- Suche in der FTS-Datenbank nach passenden Artikeln
- Zeige die besten Treffer als Antwort-Vorschläge
- "Kein passender Artikel gefunden? Kontaktiere den Admin."

### 4.2 Spätere KI-Integration (nur vorbereiten, nicht implementieren)
Das Chat-Widget soll so gebaut sein, dass man später einfach ein KI-Backend (AWS Bedrock / Claude API) anschließen kann:

```python
# Späterer Endpoint (NOCH NICHT IMPLEMENTIEREN):
# POST /api/hilfe/chat
# Body: { "nachricht": "...", "session_id": "...", "kontext_modul": "..." }
# → KI-Antwort basierend auf Hilfe-Artikeln als Kontext (RAG-Pattern)
```

Dafür soll der Chat-Verlauf in `hilfe_chat_verlauf` gespeichert werden, damit man später Trainings-Daten hat.

---

## TECHNISCHE VORGABEN

### Must-Have:
- Flask Blueprint-Pattern (wie die bestehenden Module)
- Auth: Mindestens @require_auth für alle Hilfe-Seiten
- Admin-Bereich: @require_role('admin') für Artikel-Verwaltung
- SQLite (gleiche DB wie der Rest: greiner_controlling.db)
- Bootstrap 4 + jQuery (konsistent mit dem Rest)
- Responsive Design
- FTS5-Volltextsuche
- Feedback-System (👍👎)

### Nice-to-Have:
- Markdown-Editor im Admin (z.B. SimpleMDE oder EasyMDE)
- Artikel-Vorschau im Admin
- Export/Import von Artikeln (JSON)
- View-Counter Analytics im Admin

### Verboten:
- Keine neuen CSS-Frameworks (kein Tailwind, kein Material)
- Keine neuen JS-Frameworks (kein React, kein Vue)
- Keine externen API-Calls für die Basis-Funktionalität
- Keine Änderungen am bestehenden Auth-System

---

## DEPLOYMENT-HINWEISE

### Datei-Sync:
Dateien werden über Windows-Netzlaufwerk bearbeitet:
```
\\Srvrdb01\Allgemein\Greiner Portal\Greiner_Portal_NEU\Server\
```
Dann manuell auf den Server kopiert und Service neu gestartet:
```bash
systemctl restart greiner-portal
```

### Migration ausführen:
```bash
cd /opt/greiner-portal
source venv/bin/activate
sqlite3 data/greiner_controlling.db < migrations/add_hilfe_tables.sql
```

### Blueprint registrieren:
In `app.py` muss der neue Blueprint registriert werden – prüfe wie die bestehenden registriert sind und folge dem gleichen Pattern.

---

## ZUSAMMENFASSUNG DER REIHENFOLGE

1. **Phase 0:** Codebase lesen und analysieren (PFLICHT ZUERST!)
2. **Phase 1:** DB-Schema + API + Routes implementieren
3. **Phase 2:** Frontend (Templates + CSS + JS)
4. **Phase 3:** Initiale Hilfe-Artikel basierend auf Codebase-Analyse erstellen
5. **Phase 4:** Chat-Widget UI (ohne KI, nur FTS-basiert)
6. **Test:** Alles zusammen testen, Migration dokumentieren

Frage bei Unklarheiten BEVOR du implementierst!
