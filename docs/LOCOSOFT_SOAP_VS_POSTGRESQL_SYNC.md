# Locosoft: SOAP vs. PostgreSQL-Sync für Adressbuch

**TAG 211** – Warum wir den Sync (PostgreSQL) nutzen und wann SOAP sinnvoll ist.

---

## Erledigt heute

- **Migration:** `locosoft_kunden_sync` in DRIVE PostgreSQL angelegt
- **Sync:** 49.202 Kunden aus Locosoft (PostgreSQL) in `locosoft_kunden_sync` übernommen
- **Adressbuch-Suche:** nutzt die Sync-Tabelle mit Volltextsuche (tsvector)

---

## SOAP-Dienst (Locosoft)

Der Locosoft-SOAP-Client (`tools/locosoft_soap_client.py`) bietet u. a.:

| Methode | Zweck |
|--------|--------|
| `list_customers(search_type, search_value)` | Kunden suchen – Typ: NAM, PHN, NUM, EML |
| `read_customer(customer_number)` | Ein Kunde mit allen Stammdaten |
| `list_changes(change_type='customer', since=...)` | Geänderte Kunden seit Zeitpunkt (für inkrementellen Sync) |
| `write_customer_details(customer)` | Kunde anlegen/aktualisieren |

---

## Warum Adressbuch über Sync (PostgreSQL), nicht SOAP?

1. **Volltextsuche:** Nur in unserer PostgreSQL mit `tsvector`/`plainto_tsquery` möglich – SOAP liefert nur einfache Suche (NAM/PHN/NUM/EML).
2. **Performance:** Suche läuft lokal gegen ~49k Zeilen mit GIN-Index; jede Suche per SOAP wäre ein Roundtrip zu Locosoft und ggf. langsam/begrenzt.
3. **Stabilität:** Adressbuch funktioniert auch, wenn Locosoft SOAP kurz nicht erreichbar ist.
4. **Filter „Nur Handynummern“:** Einfach über Spalte `phone_mobile` in der Sync-Tabelle; SOAP-Ergebnis müsste man nachträglich filtern und das Antwortformat ist nicht fest in unserem Code.

**Fazit:** Für die Adressbuch-**Suche** bleibt die Sync-Tabelle die bessere Wahl.

---

## Wann SOAP sinnvoll ist

- **Einzellookup:** Wenn du zu einer bekannten Kundennummer die aktuellsten Stammdaten brauchst → `read_customer(kundennummer)`.
- **Fallback:** Optional könnte man bei leerer Sync-Tabelle `list_customers('NAM', suchbegriff)` aufrufen statt Locosoft-PostgreSQL – gleiche Abhängigkeit von Locosoft, anderes Protokoll.
- **Inkrementeller Sync:** Statt immer Voll-Sync könnte ein Job `list_changes('customer', since=letzter_sync)` nutzen und nur geänderte Kunden in `locosoft_kunden_sync` nachziehen (spätere Erweiterung).

---

## Zusammenfassung

| Anwendungsfall | Empfehlung |
|----------------|------------|
| Adressbuch-Suche (WhatsApp „Neuer Chat“, Filter Handy) | **Sync-Tabelle** (PostgreSQL DRIVE) |
| Aktuelle Stammdaten zu einer Kundennummer | **SOAP** `read_customer` |
| Kunden-Sync aktuell halten | **Sync-Script** (täglich/Cron); optional später + `list_changes` |

Migration und einmaliger Sync sind erledigt; die Adressbuch-Suche nutzt die Sync-Tabelle mit Volltextsuche.
