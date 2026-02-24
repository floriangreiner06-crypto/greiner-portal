# Checkliste: CONTEXT & SSOT (Qualitätscheck Säule E)

**Zweck:** Einmal pro Quartal oder vor größeren Releases – Doku und Struktur prüfen, ohne neue Tools.  
**Referenz:** [QUALITAETSCHECK_VORSCHLAG.md](QUALITAETSCHECK_VORSCHLAG.md) (Säule E).

---

## 1. Workstream CONTEXT.md

- [ ] **controlling** — `docs/workstreams/controlling/CONTEXT.md` vorhanden und „Letzte Aktualisierung“ plausibel?
- [ ] **werkstatt** — `docs/workstreams/werkstatt/CONTEXT.md`
- [ ] **verkauf** — `docs/workstreams/verkauf/CONTEXT.md`
- [ ] **teile-lager** — `docs/workstreams/teile-lager/CONTEXT.md`
- [ ] **urlaubsplaner** — `docs/workstreams/urlaubsplaner/CONTEXT.md`
- [ ] **hr** — `docs/workstreams/hr/CONTEXT.md`
- [ ] **planung** — `docs/workstreams/planung/CONTEXT.md`
- [ ] **fahrzeugfinanzierungen** — `docs/workstreams/fahrzeugfinanzierungen/CONTEXT.md`
- [ ] **infrastruktur** — `docs/workstreams/infrastruktur/CONTEXT.md`
- [ ] **auth-ldap** — `docs/workstreams/auth-ldap/CONTEXT.md`
- [ ] **integrations** — `docs/workstreams/integrations/CONTEXT.md`
- [ ] **marketing** — `docs/workstreams/marketing/CONTEXT.md`
- [ ] **verguetung** — `docs/workstreams/verguetung/CONTEXT.md`

**Hinweis:** Fehlende CONTEXT.md oder veraltete Einträge (z. B. „Offene Punkte“, „Aktueller Stand“) aktualisieren oder im Backlog erfassen.

---

## 2. SSOT (Single Source of Truth)

- [ ] **TEK / Controlling:** SSOT für TEK-KPIs laut CLAUDE.md in `api/controlling_data.py` (`get_tek_data`, `berechne_breakeven_prognose`). Keine parallelen Berechnungen in Routes oder Templates für dieselben Kennzahlen?
- [ ] **Verkauf / Budget:** Eine SSOT für Budget/Zielplanung (laut CLAUDE/Workstream-Doku)? Doppellogik identifiziert?
- [ ] **Urlaub:** Eine SSOT für Resturlaub / Genehmigungslogik? (Siehe urlaubsplaner CONTEXT.)
- [ ] **Weitere Workstreams:** Pro aktiv genutztem Modul: Gibt es eine vereinbarte SSOT? Wird sie im Code eingehalten?

**Hinweis:** Abweichungen (z. B. „Berechnung X auch in Route Y“) in einer kurzen Liste festhalten und priorisieren.

---

## 3. Navigation & Rechte

- [ ] **DB-Navigation:** Menüpunkte aus `navigation_items` (PostgreSQL). Keine hardcodierten Navi-Punkte in `base.html` außer Fallback?
- [ ] **requires_feature / role_restriction:** Zu neueren Features passen Einträge in `navigation_items` und ggf. `auth_decorators` / `auth_manager`?
- [ ] **Broken Links:** Keine Routes/URLs in Navi, die nicht mehr existieren?

**Hinweis:** Optional kleines Script: alle `url` aus `navigation_items` laden und gegen registrierte Blueprints/Routes prüfen.

---

## 4. DB-Schema vs. Code

- [ ] **Schema-Doku:** `docs/DB_SCHEMA_POSTGRESQL.md` vorhanden und grob aktuell?
- [ ] **Migrationen:** Neue Tabellen/Spalten nur über `migrations/*.sql` angelegt? Keine Ad-hoc-Änderungen ohne Migration?
- [ ] **Stichprobe:** 2–3 zentrale Tabellen (z. B. `employees`, `vacation_bookings`, `konten`) – stimmen Spaltennamen und Nutzung im Code mit Schema-Doku überein?

---

## 5. Durchführungsvermerk

| Durchführung | Datum | Durchgeführt von | Anmerkungen |
|--------------|--------|------------------|-------------|
| 1. Lauf      | 2026-02-24 | Phase-1-Setup | Checkliste angelegt, noch nicht vollständig abgearbeitet |

---

Bei Bedarf diese Checkliste kopieren und mit neuem Datum für den nächsten Lauf führen (z. B. „2. Lauf – 2026-05-xx“).
