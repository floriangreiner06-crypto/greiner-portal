# Vorgehen: Verbesserung & Ergänzung Urlaubsplaner

**Stand:** 2026-02  
**Zweck:** Einheitlicher Ablauf für alle weiteren Verbesserungen und Ergänzungen am DRIVE-Urlaubsplaner.

---

## 1. Grundlage

- **Feature-Liste:** `FEATURE_LISTE_DRIVE_UMSETZUNG.md`  
  → Alle bekannten Funktionen (✅/🔶/❌), Referenz personal-login.de, Priorisierung am Ende.
- **Kontext:** `CONTEXT.md`  
  → Aktueller Stand, offene Punkte, nächste Vorhaben.
- **Kein Big Bang:** Änderungen schrittweise, pro Feature oder kleinem Paket, mit Test.

---

## 2. Ablauf pro Verbesserung/Ergänzung

| Schritt | Aktion |
|--------|--------|
| **1. Auswählen** | Ein Feature aus der Liste wählen (priorisiert: P1 → P2 → P3) oder einen Bug/Usertest-Punkt aus CONTEXT. |
| **2. Klären** | Kurz festhalten: Was genau soll rauskommen? (Akzeptanzkriterium, 1–3 Sätze.) Bei Unklarheit: mit HR/Vanessa absprechen. |
| **3. Umsetzen** | Code/Template/DB wie gewohnt; bei DB-Änderungen Migration anlegen. |
| **4. Prüfen** | Manuell testen (inkl. Rollen: MA, Genehmiger, Admin); ggf. Locosoft-Verhalten beachten. |
| **5. Dokumentieren** | In `FEATURE_LISTE_DRIVE_UMSETZUNG.md`: Status 🔶/❌ → ✅ (oder 🔶 bei Teilumsetzung). In `CONTEXT.md`: unter „Aktueller Stand“ den neuen Punkt eintragen, offene Punkte anpassen. |
| **6. Sync** | Relevante .md bei Bedarf ins Windows-Sync-Verzeichnis kopieren (`rsync` siehe CLAUDE.md). |

---

## 3. Priorisierung (Empfehlung)

### Zuerst: Schnelle Wirkung & offene Baustellen

1. **Outlook: Löschung bei Widerruf** (CONTEXT: 🔧)  
   - `VacationCalendarService.delete_vacation_event` implementieren, damit bei Storno/Widerruf der Kalender-Eintrag entfernt wird.
2. **Mitarbeiterverwaltung: Phasen 2–5** (Vertrag, Urlaubseinstellungen, Arbeitszeitmodell, Ausnahmen, Zeiten ohne Urlaub)  
   - Frontend-Anbindung an bestehende APIs; Buttons/Modals statt Dummy – siehe `MITARBEITERVERWALTUNG_VORGEHENSWEISE_TAG213.md`.
3. **Urlaubsanspruch aus Mitarbeiterverwaltung**  
   - Balance pro Jahr im Employee-Detail anzeigen und bearbeiten – siehe `URLAUBSANSPRUCH_AUS_MITARBEITERVERWALTUNG_VORSCHLAG.md`.

### Danach: Feature-Liste (P1)

- **2.7** Kein Verfall (Übertrag nicht verfallen) – Konfiguration pro MA oder global.
- **4.5** Urlaubssperre pro Standort (Landau vs. Deggendorf).
- **8.6** Freie Tage im Arbeitszeitmodell im Planer anzeigen (Teilzeit) – siehe `FREIE_TAGE_ARBEITSZEITMODELL_VORSCHLAG.md`.

### Optional (P2/P3)

- **2.8** Max. Urlaubslänge pro Buchung (z.B. 14 Tage).
- **3.8** Buchungszeitraum einschränken (von–bis).
- **5.5** E-Mail bei Genehmigung/Ablehnung.
- **6.3** Outlook: Eintrag bei Genehmigung (bereits teilweise); Löschung siehe oben.

---

## 4. Wo was pflegen

| Was | Wo |
|-----|-----|
| Backlog / Priorität | `FEATURE_LISTE_DRIVE_UMSETZUNG.md` (Priorisierung am Ende + Spalte Status) |
| Nächstes Vorhaben / laufende Baustellen | `CONTEXT.md` („Aktueller Stand“, „Nächstes Vorhaben“) |
| Konkrete Umsetzungsideen | Eigene .md bei Bedarf (z.B. `URLAUBSANSPRUCH_AUS_...`, `FREIE_TAGE_...`) |
| Session-Fortschritt | CONTEXT.md aktualisieren; bei Session-Ende Commit-Vorschlag (feat(urlaubsplaner): …) |

---

## 5. Regeln

- **Eine Quelle für Saldo:** Urlaubsanspruch und Rest kommen aus `vacation_entitlements` + `v_vacation_balance_*` (+ Locosoft für Anzeige). Keine parallelen „Urlaubsrechner“ einführen.
- **Locosoft:** Bleibt führend für Lohn/Abwesenheiten; DRIVE zeigt Rest korrekt an (min(View, Anspruch − Locosoft-Urlaub)) und ergänzt Genehmigungsworkflow.
- **Rechte:** Bestehende Rollen (MA, Genehmiger, HR/Admin) und `vacation_approval_rules` beibehalten; neue Rechte nur bewusst und dokumentiert.

---

## 6. Nächster konkreter Schritt (Vorschlag)

**Option A – Technische Lücke schließen:**  
Outlook-Löschung bei Widerruf implementieren (CONTEXT 🔧), dann in CONTEXT auf ✅ setzen.

**Option B – Sichtbarkeit für HR:**  
„Urlaubsanspruch aus Mitarbeiterverwaltung“ umsetzen (Balance im MA-Detail, Jahr-Auswahl, Speichern über update-entitlement).

**Option C – Usertest abarbeiten:**  
Mitarbeiterverwaltung Phasen 2–5 (Urlaubseinstellungen, Arbeitszeitmodell, Ausnahmen, Zeiten ohne Urlaub) mit Modals/API-Anbindung fertigstellen.

Sobald du dich für A, B oder C (oder ein anderes Feature aus der Liste) entscheidest, kann die Umsetzung daran ausgerichtet werden.
