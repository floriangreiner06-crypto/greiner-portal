# Navigation: Parent-Kind-Rechte (alle Menüs)

## Übersicht

Die Menüpunkte kommen aus der Tabelle `navigation_items`. Sichtbarkeit wird durch **Feature** (`requires_feature`) und optional **Rolle** (`role_restriction`) gesteuert. Damit alle Menüs konsistent rechtsbeschränkt sind, gilt:

1. **Effektives Feature:** Einträge ohne eigenes `requires_feature` erben das Feature des **Eltern-Menüpunkts** (berechnet in `api/navigation_utils.py`). So sind z. B. alle Werkstatt-Unterpunkte ohne eigenes Feature effektiv `aftersales`, bis auf Ausnahmen wie „Fahrzeuganlage“ (`fahrzeuganlage`).
2. **Eltern-Nachzug:** Wenn ein Kind sichtbar ist, der Eltern-Knoten aber nicht (weil er ein anderes Feature hat), wird der Eltern-Knoten trotzdem angezeigt. Beispiel: User mit nur Feature „Fahrzeuganlage“ sieht „Service → Werkstatt → Fahrzeuganlage“, obwohl „Werkstatt“ selbst `aftersales` verlangt.
3. **Leere Dropdowns:** Menüpunkte ohne sichtbare Kinder werden ausgeblendet (`remove_empty_dropdowns`).

## Stand pro Menü (nach Prüfung)

| Top-Level / Bereich | requires_feature (DB) | Kinder ohne Feature → erben | Migration/Fix |
|---------------------|------------------------|------------------------------|----------------|
| **Dashboard** (1) | – | – | Für alle sichtbar (kein Feature). |
| **Controlling** (2) | `controlling` | Divider 13, 17, 23, 29 → `controlling` | `fix_navigation_controlling_requires_feature.sql` |
| **Verkauf** (3) | `auftragseingang` | Divider 36, 40 → `auftragseingang` | Bereits gesetzt (Verkauf-Kinder haben Features). |
| **Team Greiner** (4) | – | 44 (Mein Urlaub), 45 (Divider) → `urlaubsplaner` | `fix_navigation_admin_team_requires_feature.sql` |
| **Service** (5) | – | Keine Kinder ohne Feature; Unterpunkte (Werkstatt, DRIVE, …) haben eigenes Feature. Ohne Berechtigung: 0 Kinder → Dropdown wird ausgeblendet. | Kein DB-Fix nötig. |
| **Admin** (6) | `admin` | 53, 54, 55, 56, 85, 92, 96, 99, 100, 102, 103 → erben `admin` | `fix_navigation_admin_team_requires_feature.sql` |
| **Teile & Zubehör** (57) | `teilebestellungen` | Alle Kinder haben bereits Feature. | – |
| **Werkstatt** (62, unter Service) | `aftersales` | Cockpit, Kapazitätsplanung, Stempeluhr, … → erben `aftersales`; „Fahrzeuganlage“ (94) hat `fahrzeuganlage`. | Logik in navigation_utils (Vererbung). |
| **DRIVE** (69, unter Service) | `werkstatt_live` | Morgen-Briefing, Kulanz-Monitor, ML-Kapazität → erben `werkstatt_live`. | Logik in navigation_utils. |
| **Übersichten** (73, unter Controlling) | `controlling` | TEK v1 (79) → erbt `controlling`. | Logik in navigation_utils. |
| **Hilfe** (101) | – | – | Für alle sichtbar. |

## Code-Referenz

- **Berechnung effektives Feature:** `api/navigation_utils.py` – nach dem Laden aller Items wird `effective_feature_by_id` befüllt (Vererbung vom Parent).
- **Filter:** Es wird mit `effective_feature_by_id[item['id']]` gefiltert; zusätzlich `role_restriction`.
- **Parent-Nachzug:** Nach dem Filter werden fehlende Eltern aus `all_items_by_id` nachgezogen.
- **Leere Dropdowns:** `remove_empty_dropdowns()` entfernt Menüpunkte mit `is_dropdown` und ohne sichtbare Kinder.

## Neue Navi-Punkte

- Immer **`requires_feature`** setzen (oder bewusst leer lassen, dann Vererbung vom Parent).
- Bei neuen Top-Level-Bereichen: entweder Feature setzen (dann nur mit Berechtigung sichtbar) oder bewusst für alle sichtbar lassen (z. B. Dashboard, Hilfe).
