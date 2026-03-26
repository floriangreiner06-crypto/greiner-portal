# Transaktionen: Zusammenführung der beiden Seiten — Vorschlag

**Ausgangslage:** Es gibt zwei getrennte Seiten für Banktransaktionen:

| Seite | URL | Inhalt | API |
|-------|-----|--------|-----|
| **Transaktionen** | `/bankenspiegel/transaktionen` | Liste mit Filtern (Von/Bis, Konto, Typ, Kategorie, Suche), **Karten** Einnahmen/Ausgaben/Saldo/Anzahl, Tabelle **ohne** Kategorie-Bearbeitung | `GET /api/bankenspiegel/transaktionen` |
| **Kategorisierung** | `/bankenspiegel/kategorisierung` | Liste mit Filtern (Nur unkategorisiert/trainierte, Kategorie, Von/Bis, Suche), Tabelle **mit** Kategorie/Unterkategorie-Dropdowns, Speichern, KI, Regeln anwenden | `GET /api/bankenspiegel/transaktionen/kategorisierung` |

**Redundanz:** Beide zeigen dieselben Buchungen mit ähnlichen Filtern (Datumsbereich, Kategorie, Suche), aber unterschiedliche Funktionen (nur ansehen vs. kategorisieren).

---

## Option A: Eine Seite „Transaktionen“ mit Modus-Umschalter (empfohlen)

**Idee:** Nur noch **eine** Seite unter `/bankenspiegel/transaktionen`. Oben ein Umschalter (z. B. Tabs oder Toggle):

- **„Übersicht“** (Standard): wie bisher Transaktionen – Filter (inkl. Konto, Typ), Karten Einnahmen/Ausgaben/Saldo/Anzahl, Tabelle mit Datum, Konto, Verwendungszweck, Betrag, **Kategorie/Unterkategorie nur lesbar** (keine Dropdowns).
- **„Kategorisieren“**: gleiche Filter + zusätzlich „Nur unkategorisierte“ / „Nur trainierte“, Tabelle **mit** Kategorie/Unterkategorie-Dropdowns, Speichern, KI; Buttons „Regeln anwenden“, „Regeln erneut anwenden“, „KI vorladen“.

**Vorteile:**
- Ein Einstiegspunkt, eine URL, geteilte Filter (Von/Bis, Kategorie, Suche).
- Keine doppelte Pflege von Filterlogik.
- Karten (Einnahmen/Ausgaben/Saldo) können in beiden Modi angezeigt werden (optional nur in Übersicht).

**Umsetzung (stark vereinfacht):**
- Template: Ein gemeinsames `bankenspiegel_transaktionen.html` mit zwei „Ansichten“ (z. B. zwei Tab-Inhalten); Tabelle im Kategorisierungs-Modus mit zusätzlichen Spalten und Buttons.
- API: Entweder **eine** API erweitern (z. B. `GET /api/bankenspiegel/transaktionen` um Parameter `mode=kategorisierung`, `nur_unkategorisiert`, `nur_kategorisiert` und Rückgabe von `kategorie_manuell` etc.) **oder** Frontend ruft je nach Modus die bestehende Transaktionen- bzw. Kategorisierungs-API auf.
- Navigation: Nur noch **einen** Menüpunkt „Transaktionen“; „Kategorisierung“ entfällt als eigener Punkt (oder bleibt als Deep-Link `/bankenspiegel/transaktionen?mode=kategorisierung` für Lesezeichen).

**Aufwand:** Mittel (Template zusammenführen, Modus-Logik, ggf. eine API vereinheitlichen).

---

## Option B: Kategorisierung als Unteransicht der Transaktionen

**Idee:** Seite „Transaktionen“ bleibt die einzige Liste. **Button „Kategorisieren“** (oder „Kategorisierung öffnen“) öffnet die **gleiche** Liste in einem anderen Kontext:
- Entweder **Modal/Off-Canvas** mit der Kategorisierungs-Tabelle (gleiche Filter übernommen), oder
- **Neuer Tab / neues Fenster** mit URL `/bankenspiegel/kategorisierung?von=…&bis=…` (Filter per URL übergeben), sodass die Kategorisierungs-Seite weiterhin separat existiert, aber gezielt aus der Transaktionen-Übersicht heraus mit gleichem Filter aufgerufen wird.

**Vorteile:** Klare Trennung „Lesen/Filter“ vs. „Kategorisieren“; wenig Änderung an der bestehenden Kategorisierungs-Seite.
**Nachteil:** Zwei URLs/Seiten bleiben erhalten; Redundanz nur gemildert (geteilte Filter beim Aufruf).

---

## Option C: Nur eine Seite „Transaktionen“ inkl. Kategorisierung

**Idee:** Die **Kategorisierungs-Seite** wird zur **einzigen** Transaktionen-Seite. Die bisherige „Transaktionen“-Seite entfällt.

- Auf der Kategorisierungs-Seite: **Karten** Einnahmen/Ausgaben/Saldo/Anzahl (gefiltert) **oben** ergänzen.
- Filter um **Konto** und **Typ (Einnahmen/Ausgaben)** erweitern (wie auf der alten Transaktionen-Seite).
- Tabelle bleibt mit Kategorie/Unterkategorie und Speichern/KI; Nutzer, die nur „gucken“ wollen, nutzen dieselbe Tabelle ohne zwingend zu speichern.

**Vorteile:** Eine URL, eine API (Kategorisierungs-API um Summen und ggf. Konto-Filter erweitern), ein Template.
**Nachteile:** Seite wird funktional reicher und etwas voller; Nutzer die nie kategorisieren sehen trotzdem die Kategorie-Spalten (akzeptabel, da nur Lesen).

---

## Empfehlung

- **Option A** ist der beste Kompromiss: eine Seite, zwei klare Modi (Übersicht vs. Kategorisieren), geteilte Filter, keine doppelte Liste.
- **Option C** ist die radikalste Vereinfachung (nur noch eine Seite mit allen Funktionen) und weniger Aufwand als A, wenn man die Karten und Filter in die bestehende Kategorisierungs-Seite einbaut und die alte Transaktionen-Seite entfernt.

**Nächster Schritt:** Entscheidung (A, B oder C), danach konkrete Aufgaben (API-Anpassung, Template, Navigation, Redirect von `/bankenspiegel/kategorisierung` falls A/C).
