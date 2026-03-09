# Transaktionen-Kategorisierung: Manuell vorschlagen & KI verbessern

**Kontext:** Liquiditätsvorschau braucht saubere Kategorien. Zu viele Fehler bei rein automatischer KI → User-Vorschlag: alle Transaktionen manuell vorschlagen und KI „trainieren“.

---

## Empfehlung

**Ja – dein Ansatz ist sinnvoll.** Sinnvolle Reihenfolge:

1. **Regeln zuerst (Batch ohne KI)**  
   Alle unkategorisierten Transaktionen mit den **regelbasierten** Mustern kategorisieren (`POST /api/bankenspiegel/transaktionen/kategorisieren` mit `mit_ki: false`, z. B. `limit: 2000`). Das reduziert die Menge, die die KI sehen muss, und nutzt sichere Muster (z. B. Gehalt, bekannte Gegenkonten).

2. **Rest: KI nur als Vorschlag, nicht sofort speichern**  
   Statt KI-Ergebnisse direkt in die DB zu schreiben: **Vorschläge** abrufen und in einer **Review-Liste** anzeigen. Ein Mensch prüft und bestätigt oder korrigiert. So entstehen weniger Fehler in den Daten und du sammelst gleichzeitig „gute Beispiele“ für die KI.

3. **„KI trainieren“ ohne echtes Fine-Tuning**  
   - **Few-Shot im Prompt:** 5–15 echte, bereits bestätigte Transaktionen (Verwendungszweck/Buchungstext + Kategorie/Unterkategorie) aus euren Daten in den KI-Prompt einbauen. Die KI orientiert sich dann an euren konkreten Fällen.  
   - **Regeln nachziehen:** Was User oft korrigiert (z. B. „war Sonstige, soll Personal/Gehalt“), als neue Regel in `transaktion_kategorisierung.py` aufnehmen → weniger Rest für die KI.

4. **Projektionen bleiben korrekt**  
   Die erwarteten Ausgaben (`cashflow_erwartung_ausgaben.py`) lesen nur **bereits gespeicherte** Kategorien aus der Historie. Sobald mehr Transaktionen sauber kategorisiert sind, werden die Projektionen automatisch besser – ohne Änderung an der Projektionslogik.

---

## Konkreter Workflow (Vorschlag)

| Schritt | Aktion | Wo |
|--------|--------|-----|
| 1 | Batch-Kategorisierung **nur Regeln** (limit 2000), ggf. mehrmals | Admin/Bankenspiegel oder Script |
| 2 | Unkategorisierte z. B. als Liste laden; pro Zeile **KI-Vorschlag abrufen** (ohne Speichern) | Neues UI „Kategorisierungsvorschläge“ oder Erweiterung Transaktionen-Liste |
| 3 | User prüft Vorschlag, übernimmt oder korrigiert | Gleiche Liste mit Buttons „Übernehmen“ / „Kategorie ändern“ |
| 4 | Nach Übernahme: bei Bedarf **Regel** für wiederkehrende Muster ergänzen | `api/transaktion_kategorisierung.py` |
| 5 | Optional: **Beispiele für KI** aus bestätigten Kategorisierungen sammeln und in den LM-Studio-Prompt einbauen | `api/ai_api.py` → `kategorisiere_transaktion_mit_ki` |

---

## Technisch bereits vorhanden

- **Batch (nur Regeln):** `POST /api/bankenspiegel/transaktionen/transaktionen/kategorisieren` mit `mit_ki: false`
- **KI pro Einzeltransaktion (Vorschlag):** `POST /api/ai/kategorisiere/transaktion` – liefert nur JSON, schreibt **nicht** in die DB
- **Batch mit KI:** aktuell schreibt die KI bei `mit_ki: true` **direkt** in die DB (max 50) – für „nur vorschlagen“ fehlt ein Batch-Endpoint, der nur Vorschläge zurückgibt

---

## Lernt die KI beim Speichern?

**Ja (Few-Shot).** Beim Aufruf der KI (Button „KI“ in der Kategorisierung) werden bis zu 12 zuletzt kategorisierte Transaktionen aus der DB geladen und als Beispiele in den Prompt eingebaut. Die KI orientiert sich daran – eure gespeicherten Zuordnungen (z. B. EFA → Lieferanten) verbessern die Vorschläge für ähnliche Buchungen. Umsetzung: `api/ai_api.py` → `_hole_kategorisierung_beispiele()`, `kategorisiere_transaktion_mit_ki()`.

## Nächste Schritte (optional)

1. **Endpoint „Vorschläge nur“:** z. B. `POST /api/bankenspiegel/transaktionen/kategorisieren-vorschlaege` mit `limit` – gibt für unkategorisierte Transaktionen nur `[{ id, verwendungszweck, …, kategorie_vorschlag, unterkategorie_vorschlag }]` zurück, **ohne** UPDATE. Frontend zeigt Liste; User klickt „Übernehmen“ → dann ein UPDATE pro Zeile oder kleiner Batch.
2. **Batch „mit_ki“ umschalten:** Bei `mit_ki: true` **nicht** mehr automatisch speichern, sondern nur Vorschläge zurückgeben (Breaking Change für bestehendes UI – besser neuer Endpoint wie oben).
3. **Few-Shot im Prompt:** Abfrage „N zufällige kategorisierte Transaktionen“ aus der DB; diese als Beispiele im Prompt an LM Studio übergeben.

Wenn du willst, können wir als Nächstes den Endpoint für reine Vorschläge (ohne Speichern) und ein kleines UI „Vorschläge prüfen“ skizzieren oder umsetzen.
