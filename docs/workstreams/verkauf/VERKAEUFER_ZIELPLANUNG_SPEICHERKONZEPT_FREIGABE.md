# Verkäufer-Zielplanung – Speicherkonzept & finale Freigabe

**Stand:** 2026-02-19  
**Workstream:** verkauf  
**Auslöser:** Bei Neuaufruf der Seite startet die Zielplanung immer wieder „von vorn“ (Parameter manuell setzen, Berechnen, ggf. Gespeicherte Ziele laden). Gewünscht: Bearbeitungsstand persistent in der DB, weiterhin editierbar, plus explizite **finale Freigabe**, wenn alle Einzelziele geplant sind.

---

## 1. Was du willst (Kernanforderungen)

1. **Speicherkonzept:** Der jeweilige Bearbeitungsstand wird in der DB gehalten – beim nächsten Aufruf der Seite muss nicht wieder „Werte laden / Werte speichern“ von vorne durchgespielt werden.
2. **Weiterhin editierbar:** Auch nach Laden aus der DB bleibt alles änderbar (Parameter + Einzelziele), bis bewusst freigegeben wird.
3. **Finale Freigabe:** Wenn alle Einzelziele geplant sind, gibt es einen expliziten Schritt „Planung freigeben“. Erst danach gelten die Ziele als verbindlich (z. B. für Monatsziele und Auftragseingang-Zielerfüllung).

---

## 2. Ist-Zustand (kurz)

- **Tabelle `verkaeufer_ziele`:** Speichert nur die **Verkäufer-Zeilen** (kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw, planungsgespraech_am, planungsgespraech_notiz, gespeichert_von, gespeichert_am). Kein Status „Entwurf vs. freigegeben“, keine Planungsparameter.
- **Seitenaufruf:** Zieljahr fest/default (z. B. 2026), Referenzjahr/Konzern NW/GW/NW nach Marke sind **nur Frontend-Defaults** (2025, 630, 900). Nichts wird beim Öffnen aus der DB geladen.
- **„Gespeicherte Ziele laden“:** Lädt nur die Verkäufer-Zeilen; die **Parameter** (Referenz, Konzernziel NW/GW, NW nach Marke) werden weder gespeichert noch wiederhergestellt. Zudem braucht man vorher „Berechnen“, damit die Tabelle überhaupt Zeilen hat.
- **„Ziele speichern“:** Schreibt sofort in `verkaeufer_ziele` und die Ziele gelten als „wirksam“. Es gibt keinen Entwurf und keinen Freigabe-Schritt.

**Folge:** Jeder Neuaufruf = wieder Parameter eintragen, Berechnen, ggf. Gespeicherte Ziele laden – kein durchgängiger „Planungsstand“.

---

## 3. Konzept: Drei Bausteine

### 3.1 Planungsstand pro Zieljahr (Parameter + Status)

**Idee:** Pro Kalenderjahr (Zielplanung) einen **einzigen Planungsstand** in der DB führen: alle Parameter, die die Seite braucht, plus ein Status „Entwurf“ oder „Freigegeben“.

- **Neu:** Eine Tabelle (oder ein Satz pro Jahr) für den **Planungsstand**:
  - **Zieljahr** (kalenderjahr)
  - **Parameter:** referenz_jahr, konzernziel_nw, konzernziel_gw, optional ziel_nw_hyundai, ziel_nw_opel, ziel_nw_leapmotor (NULL = „auto“)
  - **Status:** `entwurf` | `freigegeben`
  - **Metadaten:** zuletzt_gespeichert_am, zuletzt_gespeichert_von (für Audit)
  - Optional: freigegeben_am, freigegeben_von (nur bei Status „freigegeben“)

- **Bedeutung:**
  - Beim **Seitenaufruf** für ein Zieljahr: Wenn ein Planungsstand existiert, werden diese Parameter geladen und die Felder (Referenz, Konzern NW/GW, NW nach Marke) gesetzt. Zusätzlich werden die Verkäufer-Ziele für dieses Jahr geladen (siehe 3.2).
  - **„Ziele speichern“** (Entwurf): Speichert die aktuellen Parameter in diesen Planungsstand (Status bleibt „Entwurf“) und schreibt die Einzelziele in `verkaeufer_ziele` (s. u. Entwurf vs. Wirksamkeit).
  - **„Planung freigeben“:** Setzt Status auf „freigegeben“, optional Zeitstempel + User. Ab dann sind die Ziele **verbindlich** für Monatsziele und Auftragseingang.

**Editierbarkeit:** Solange Status = „Entwurf“, ist alles (Parameter + Einzelziele) weiter änderbar. Nach Freigabe kann entweder gesperrt werden (nur Lesen) oder ihr entscheidet: „Freigabe zurücksetzen“ nur für bestimmte Rollen (z. B. admin/geschaeftsleitung), dann zurück auf Entwurf.

---

### 3.2 Verkäufer-Ziele: Entwurf vs. „wirksam“

Aktuell: Alles in `verkaeufer_ziele` ist sofort „wirksam“ für Monatsziele/Auftragseingang.

**Option A – Eine Tabelle, Freigabe steuert Nutzung:**  
- `verkaeufer_ziele` bleibt wie heute (kalenderjahr, mitarbeiter_nr, ziel_nw, ziel_gw, …).  
- Zusätzlich gibt es den **Planungsstand** pro Jahr (3.1) mit Status `entwurf` | `freigegeben`.  
- **Logik:** Monatsziele / Auftragseingang-Zielerfüllung nutzen die Werte aus `verkaeufer_ziele` **nur**, wenn für dieses Jahr der Planungsstand „freigegeben“ ist. Bei „Entwurf“ werden entweder keine Ziele angezeigt oder ein Fallback (z. B. Verteilung aus Referenzjahr).  
- Vorteil: Keine doppelte Speicherung von Zielen; eine Quelle. Nachteil: Beim Speichern im Entwurf überschreibt man bereits die Tabelle – wenn ihr „wirksam“ strikt erst nach Freigabe wollt, braucht ihr Option B.

**Option B – Entwurf-Ziele getrennt speichern:**  
- Zusätzliche Tabelle z. B. `verkaeufer_ziele_entwurf` (gleiche Struktur wie `verkaeufer_ziele`, nur für Entwurf).  
- „Ziele speichern“ im Entwurf schreibt nur in `verkaeufer_ziele_entwurf`.  
- „Planung freigeben“ kopiert/übernimmt Entwurf → `verkaeufer_ziele` (und setzt Planungsstand auf „freigegeben“).  
- Monatsziele/Auftragseingang lesen **nur** aus `verkaeufer_ziele`.  
- Vorteil: Bis zur Freigabe ist die „offizielle“ Tabelle unberührt. Nachteil: Doppelte Struktur, Freigabe = einmaliger Kopiervorgang.

**Empfehlung:** Option A, sofern ihr akzeptiert, dass im Entwurf die gleiche Tabelle beschrieben wird, aber **verbindlich** sind die Werte erst nach Freigabe (Leselogik in API: nur bei Status „freigegeben“ aus `verkaeufer_ziele` lesen). Dann reicht eine Tabelle und ein klarer Status pro Jahr.

---

### 3.3 Seitenablauf (UX)

- **Beim Aufruf der Seite (Zielplanung):**
  - Zieljahr aus URL oder Default (z. B. 2026).
  - **Laden:** Ein neuer Endpoint (z. B. `GET /api/verkaeufer-zielplanung/planungsstand/<jahr>`) liefert:
    - Planungsparameter (referenz_jahr, konzernziel_nw, konzernziel_gw, nw nach Marke), falls vorhanden;
    - Status (entwurf/freigegeben);
    - Liste der gespeicherten Verkäufer-Ziele für dieses Jahr.
  - Wenn **kein** Planungsstand existiert: aktuelle Defaults anzeigen (wie heute), Tabelle leer bis „Berechnen“.
  - Wenn Planungsstand existiert: Parameter in die Felder füllen, Verkäufer-Ziele laden. **Ohne** „Berechnen“ zu rufen, fehlt die Verkäuferliste (Namen, IST) – daher entweder:
    - Beim Laden bei vorhandenem Planungsstand automatisch **eine** Verteilung anfordern (nur um die Tabelle mit Verkäuferzeilen + Namen zu füllen), und die Zellwerte aus den gespeicherten Zielen befüllen, **oder**
    - Beim Laden Verkäuferliste aus Referenz-Stückzahl holen und Tabelle mit Namen + gespeicherten Zielwerten aufbauen (ohne Vorschlagsberechnung). Dann bleibt „Berechnen“ für einen neuen Vorschlag.

- **„Ziele speichern“:**  
  - Parameter (Referenz, Konzern NW/GW, NW nach Marke) + aktuelle Tabelle (Einzelziele) in DB schreiben.  
  - Planungsstand für dieses Jahr anlegen/aktualisieren, Status = **Entwurf**.  
  - Kurzer Hinweis: „Entwurf gespeichert. Noch nicht freigegeben.“

- **„Planung freigeben“ (neuer Button, z. B. nur sichtbar wenn Status = Entwurf):**  
  - Prüfung (optional): Alle Verkäufer mit Zielen belegt? Summe NW/GW plausibel (Warnung bei großer Differenz zum Konzernziel)?  
  - Status auf „freigegeben“ setzen, freigegeben_am / freigegeben_von setzen.  
  - Ab dann: Monatsziele und Auftragseingang nutzen diese Ziele.  
  - UI: Klarer Hinweis „Planung 2026 freigegeben“; Button „Freigabe zurücksetzen“ nur bei Bedarf und mit Rolle.

- **Editierbarkeit:** Bis Freigabe: alles editierbar. Nach Freigabe: nach eurer Entscheidung entweder nur noch Anzeige oder „Freigabe zurücksetzen“ (admin/GL) mit erneutem Bearbeiten.

---

## 4. Kurzfassung

| Thema | Vorschlag |
|-------|-----------|
| **Parameter speichern** | Neue Struktur „Planungsstand“ pro Zieljahr: referenz_jahr, konzernziel_nw/gw, nw nach Marke, status (entwurf/freigegeben), Zeitstempel/User. |
| **Seitenaufruf** | Beim Öffnen Planungsstand + Ziele für gewähltes Zieljahr laden und Formular + Tabelle befüllen (ggf. Verkäuferliste aus Referenz-Stückzahl). |
| **Editierbarkeit** | Immer editierbar im Entwurf; nach Freigabe nach Vereinbarung sperren oder „Freigabe zurücksetzen“. |
| **Wirksamkeit** | Monatsziele / Auftragseingang nutzen `verkaeufer_ziele` **nur**, wenn Planungsstand für dieses Jahr = „freigegeben“. |
| **Finale Freigabe** | Button „Planung freigeben“ setzt Status auf „freigegeben“, optional Prüfung (alle geplant, Summen plausibel). |

Wenn du willst, können wir im nächsten Schritt daraus konkrete DB-Felder (Migration), API-Endpoints und kleine Änderungen am Template/JS ableiten – ohne hier schon zu coden.
