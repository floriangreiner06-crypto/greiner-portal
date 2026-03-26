# SSOT-Strategie Urlaubsplaner: Vorschlag für konsistente Daten

**Stand:** 2026-02-24  
**Kontext:** Locosoft ist prinzipiell das führende System; gebuchte Tage werden von HR manuell in Locosoft nachgepflegt → Zeitversatz. Sollen wir für die Resturlaubsberechnung ganz auf Locosoft-Daten verzichten?  
**Kein Coding** – nur strategischer Vorschlag.

---

## 1. Ausgangslage

| Größe | Aktuell Portal | Aktuell Locosoft | Problem |
|-------|-----------------|------------------|--------|
| **Jahresanspruch** | `vacation_entitlements` (total_days, Übertrag, Korrektur) | Nicht direkt in DB; in Locosoft-Anwendung berechnet | Abweichungen (z. B. 23 vs. 27), kein automatischer Abgleich |
| **Verbraucht / Genommen** | `vacation_bookings` (approved, nur Urlaub) | `absence_calendar` (Url, BUr) | HR pflegt Locosoft nach → Locosoft hinkt hinter Portal-Buchungen her |
| **Resturlaub** | Berechnet: Anspruch − Verbraucht − Geplant (View) | In Locosoft-Anwendung berechnet | Wir mischen beide: Rest = min(Portal-Rest, Anspruch − Locosoft-Urlaub) → Inkonsistenzen, Safeguards, Bugs |

**Kernkonflikt:**  
- **Locosoft** = fachlich führend (Lohn, Personalplaner, HR-Arbeit).  
- **Zeitversatz:** Was im Portal genehmigt ist, ist in Locosoft erst nach manueller Pflege sichtbar.  
- **Folge:** Wenn wir Rest aus Locosoft mitrechnen, ist der Rest im Portal oft **höher** als in Locosoft (weil Locosoft die neuesten genehmigten Tage noch nicht hat). Wenn wir nur Portal nehmen, fehlen ggf. Urlaubstage, die **nur** in Locosoft stehen (z. B. außerhalb des Portals gebucht).

---

## 2. Optionen

### Option A: Resturlaub **nur aus Portal** (DRIVE = SSOT für Rest)

**Regel:**  
Resturlaub = Anspruch (Portal, nach Abzügen Weihnachten/Silvester etc.) − Verbraucht (Portal: approved Urlaub) − Geplant (Portal: pending Urlaub). **Keine** Locosoft-Urlaubstage in der Rest-Berechnung.

**Vorteile:**
- **Konsistent:** Eine Quelle, eine Formel. Keine Mischlogik, keine Safeguards gegen „Locosoft falsch“.
- **Aktuell:** Sobald eine Buchung im Portal genehmigt ist, sinkt der Rest sofort – kein Warten auf HR-Nachpflege in Locosoft.
- **Validierung = Anzeige:** Buchungsprüfung und angezeigter Rest nutzen dieselbe Basis (Portal-View + einheitliche Abzüge).
- **Weniger Abhängigkeit:** Kein Locosoft-API-Zugriff nötig für die Rest-Zahl; Ausfälle/Falschmeldungen von Locosoft beeinflussen den Rest nicht.

**Nachteile:**
- **Nicht identisch mit Locosoft:** Der in Locosoft angezeigte Rest kann abweichen (z. B. wenn in Locosoft noch Urlaub aus Vorjahren oder manuell erfasste Tage stehen, die nicht im Portal sind). Für Lohn/HR bleibt Locosoft maßgeblich; das Portal zeigt dann explizit „Rest laut DRIVE (genehmigte/geplante Buchungen)“.
- **Nur Portal-Buchungen zählen:** Urlaub, der **nur** in Locosoft eingetragen wurde (ohne Portal-Genehmigung), würde den Portal-Rest **nicht** mindern. Das ist sachlich dann so gewollt: Planung/Verfügbarkeit im Portal = nur was über DRIVE läuft; alles andere ist HR/Locosoft-Thema.

**Anspruch:**  
Anspruch bleibt im **Portal** (`vacation_entitlements`) als SSOT, abgeglichen mit HR/Locosoft (manuell oder künftig per Import). Locosoft liefert dann **keine** Rest- oder Verbrauchswerte mehr für die Berechnung.

---

### Option B: Resturlaub **nur aus Locosoft**

**Regel:**  
Resturlaub = Wert aus Locosoft (sofern die Anwendung/DB einen Rest oder „J.Url.ges.“ − Verbraucht liefert). Portal zeigt nur an, was Locosoft meldet.

**Vorteile:**
- **Gleichstand mit HR/Lohn:** Eine Zahl, die mit Locosoft übereinstimmt.

**Nachteile:**
- **Zeitversatz:** Nach Genehmigung im Portal bleibt der Rest bis zur HR-Nachpflege in Locosoft zu hoch. Nutzer buchen ggf. doppelt oder sind verunsichert.
- **Technik:** Locosoft liefert „Rest“ oft nicht direkt aus der DB; oft nur Aggregation (J.Url.ges. − Verbraucht). Abweichungen bei Stichtag, Übertrag, Sonderregeln (Weihnachten/Silvester) müssten wir in Locosoft oder in unserer Auswertung abbilden.
- **Verfügbarkeit/Fehler:** Wenn Locosoft nicht erreichbar ist oder falsche Daten liefert, haben wir im Portal keine stabile Rest-Anzeige.

**Fazit:** Für ein Planungstool, in dem **sofort** nach Genehmigung der Rest sinken soll, ist Option B ungünstig.

---

### Option C: **Hybrid mit klarer Rollenverteilung** (Empfehlung)

**Prinzip:** Zwei klare Rollen, keine Mischformel mehr.

| Rolle | SSOT | Verwendung im Portal |
|-------|------|----------------------|
| **Resturlaub (für Anzeige & Buchungsprüfung)** | **Portal** | Rest = Anspruch (Portal) − Verbraucht (Portal) − Geplant (Portal), nach Abzügen (Weihnachten/Silvester, freie Tage). **Kein** Locosoft in dieser Formel. |
| **Anspruch (Jahresanspruch)** | **Portal** (`vacation_entitlements`), abgeglichen mit HR/Locosoft | Pflege in Mitarbeiterverwaltung; optional periodischer Abgleich mit Locosoft (Import/Report), aber Portal ist die Quelle für die Berechnung. |
| **Locosoft** | Führend für Lohn, HR, Archiv | Im Portal **nur** zur **Information**: z. B. Kalender zeigt weiterhin Locosoft-Einträge (Url, ZA, Krn) zusätzlich zu Portal-Buchungen, oder eine Infozeile „In Locosoft gebucht: X Tage (Stand: …)“. Keine Einrechnung in die Rest-Zahl. |

**Konkret:**
- **Resturlaub:** Wir **verzichten** auf die Nutzung von Locosoft-Resturlaubs- bzw. Locosoft-Verbrauchsdaten **in der Berechnung** von Rest und in der Buchungsvalidierung. Damit entfällt die Mischlogik und die Abhängigkeit vom Zeitversatz.
- **Kalender:** Kann weiterhin Locosoft-Tage anzeigen (z. B. anders gefärbt oder mit Hinweis „Locosoft“), damit MA und HR sehen, was bereits in Locosoft steht – aber die **Zahl „Rest“** kommt nur aus dem Portal.
- **Anspruch:** Portal bleibt SSOT; Prozess: HR/Locosoft und Mitarbeiterverwaltung abgleichen (z. B. zu Jahresbeginn oder bei Teilzeitänderung), damit `vacation_entitlements` stimmt.

**Vorteile:**
- Konsistente, nachvollziehbare Rest-Berechnung ohne Safeguards und Sonderfälle Locosoft.
- Sofortige Aktualität nach Genehmigung im Portal.
- Locosoft bleibt führend für alles, was Lohn/Personal betrifft; das Portal ist führend für **Planung und Verfügbarkeit** auf Basis der im Portal geführten Buchungen.
- Klare Kommunikation möglich: „Rest im DRIVE = nach genehmigten/geplanten Buchungen im Portal; für endgültigen Stand siehe Locosoft.“

---

## 3. Empfehlung: Option C (Hybrid, Rest nur aus Portal)

**Kurz:**  
- **Ja:** Für die **Resturlaubsberechnung** auf Locosoft-Rest- bzw. Locosoft-Verbrauchsdaten **verzichten**.  
- **Nein:** Locosoft nicht „ausblenden“ – weiter zur Information nutzen (Kalender, ggf. Info „in Locosoft gebucht“), aber **nicht** in die Formel für Rest und Validierung einfließen lassen.

**Damit erreicht ihr:**
1. **Eine** klare Formel: Rest = Anspruch (Portal) − Verbraucht (Portal) − Geplant (Portal), mit einheitlichen Abzügen (Weihnachten/Silvester, freie Tage).
2. **Keine** Abhängigkeit der Rest-Zahl vom Zeitversatz oder von Locosoft-Fehlern/Codierung (Krn vs. Url).
3. **Konsistenz** zwischen Anzeige und Buchungsvalidierung aus einer Quelle.
4. **Locosoft** bleibt führend für Lohn/HR; das Portal ist führend für Planung und die angezeigte Rest-Zahl.

---

## 4. Was das für Anspruch und Abgleich bedeutet

- **Anspruch:** SSOT = Portal (`vacation_entitlements`), gepflegt in der Mitarbeiterverwaltung.  
- **Abgleich mit Locosoft:**  
  - Entweder **manuell:** HR gleicht zu Stichtagen (z. B. Jahresbeginn) mit Locosoft ab und passt die Mitarbeiterverwaltung an.  
  - Oder **technisch:** Optional später ein Import/Report aus Locosoft (z. B. J.Url.ges. oder Anspruch pro MA/Jahr), der `vacation_entitlements` befüllt oder als Vorlage dient.  
  Wichtig: **Eine** Stelle, an der der Anspruch für die Portal-Berechnung steht (Portal-DB), kein paralleles „Anspruch aus Locosoft“ in der Rest-Formel.

---

## 5. Nächste Schritte (wenn Option C gewählt wird)

1. **Fachlich abstimmen:** HR/Vanessa bestätigen: Rest im Portal = nur Portal-Buchungen; Locosoft dient zur Info, nicht zur Rest-Berechnung.
2. **Technisch:** In einer späteren Umsetzung die Locosoft-Rest-/Verbrauchs-Logik aus Balance, Validierung und allen Exporten entfernen; eine zentrale Berechnungsfunktion nur auf Basis Portal (View + Abzüge) nutzen.
3. **Kommunikation:** Kurze Erklärung im Urlaubsplaner oder in der Hilfe: „Ihr Resturlaub im DRIVE basiert auf den hier genehmigten und geplanten Buchungen. Der endgültige Stand für Lohn/Personal steht in Locosoft.“

Damit habt ihr eine klare SSOT-Strategie und konsistente Daten, ohne Locosoft fachlich abzuwerten – aber ohne den Zeitversatz und die Mischlogik in der Resturlaubsberechnung.
