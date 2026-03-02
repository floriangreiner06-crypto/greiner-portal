# eAutoseller & Verkauf – wo finde ich das Feature?

## Kurzantwort

- **Im Menü „Verkauf“** erscheint **eAutoseller Bestand** nur für Rollen mit Feature **eautoseller**: Admin, Verkaufsleitung, Disposition. Die Rolle **Verkauf** (normale Verkäufer) hat dieses Feature **bewusst nicht** – sie sehen den Menüpunkt nicht.
- **In der Rechteverwaltung** erscheint das Feature **eautoseller** unter **User & Rollen → Feature-Zugriff → Nach Rolle** (Rolle wählen, dann in der Checkbox-Liste „eautoseller“ an- oder abwählen). **Nicht** unter dem Tab „Navigation“ – dort wird nur die Menüstruktur gepflegt, nicht der Feature-Zugriff pro Rolle.

## „Verlorene“ Features – was fehlte in der Config?

Folgende Features existierten nur in der **Datenbank** (Migrationen) und in der **Navigation** (`requires_feature`), aber **nicht** in der Config `FEATURE_ACCESS` in `config/roles_config.py`. Dadurch konnten sie in der Rechteverwaltung fehlen oder nur erscheinen, wenn die Navi-Abfrage sie lieferte:

| Feature | Bedeutung | Jetzt |
|--------|-----------|--------|
| **eautoseller** | eAutoseller Bestand (Menü unter Verkauf) | In `FEATURE_ACCESS` ergänzt; in Rechteverwaltung sichtbar. |
| **gw_standzeit** | GW-Standzeit | In `FEATURE_ACCESS` ergänzt. |
| **planung** | Planung, Budget-Planung, Lieferforecast | In `FEATURE_ACCESS` ergänzt. |
| **verkaeufer_zielplanung** | Verkäufer-Zielplanung | In `FEATURE_ACCESS` ergänzt. |
| **leasys** | Leasys Programmfinder / Kalkulator | In `FEATURE_ACCESS` ergänzt. |

**provision**, **provision_vkl** und **whatsapp_verkauf** standen bereits in der Config.

## Wenn Verkäufer eAutoseller sehen sollen

1. **Rechteverwaltung** → Tab **User & Rollen** → Bereich **Feature-Zugriff** → Pill **Nach Rolle**.
2. Rolle **Verkauf** auswählen (Button oder Dropdown).
3. In der Liste der Features **eautoseller** anhaken und **Speichern**.

Danach sehen alle User mit Rolle „Verkauf“ den Menüpunkt **eAutoseller Bestand** unter Verkauf.

## Technisch (für Entwickler)

- `config/roles_config.py`: `FEATURE_ACCESS` enthält jetzt **eautoseller**, **gw_standzeit**, **planung**, **verkaeufer_zielplanung**, **leasys** mit den gleichen Rollen wie in der DB (Migrationen). So erscheinen diese Features immer in der Rechteverwaltung, unabhängig von der Navi-Abfrage.
- Die **tatsächlichen** Zuordnungen (welche Rolle welches Feature hat) kommen weiterhin aus der Tabelle **feature_access** (PostgreSQL); die Config dient als Fallback und für die vollständige Anzeige der Feature-Liste.
