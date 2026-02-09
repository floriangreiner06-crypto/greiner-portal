# TEK: Metabase vs. DRIVE / tek_api_helper

**Datum:** 2026-02-09  
**Zweck:** Klarheit, was die „alte“ TEK (DRIVE/PDF) hat und was Metabase zeigt; Rolle von `tek_api_helper.py`.

**Layout:** Damit Metabase weniger Leerraum hat und breiter/höher wie DRIVE wirkt:  
`python3 scripts/resize_tek_dashboard_metabase.py` ausführen (Cards volle Breite 18, hohe size_y). Danach im Browser F5.

---

## Wann Metabase Mehrwert bringt – und wann nicht

Ihr kommt von der **Weiterentwicklung der PDF-Reports** und testet Metabase. Wenn die Dashboard-Erstellung zu aufwendig wird, ist die Frage berechtigt: **Welchen Mehrwert hat Metabase überhaupt?**

### Metabase lohnt sich, wenn …

- **Interaktivität ohne Neuberechnung:** Monat/Standort/Zeitraum im Browser umschalten, ohne dass jemand ein PDF neu generiert oder eine neue E-Mail anstößt.
- **Eine Oberfläche für mehrere Auswertungen:** TEK, BWA, Verlauf, ggf. weitere Ad-hoc-Abfragen an einem Ort – ohne für jede Variante ein eigenes PDF-Template zu pflegen.
- **Selbstbedienung:** Sachbearbeiter/Controlling können eigene Fragen an die Daten stellen (neue Fragen in Metabase anlegen), ohne dass jede Auswertung als Feature in DRIVE gebaut werden muss.
- **Einbettung in DRIVE:** Metabase-Dashboards per iframe/Link in DRIVE einbinden – dann wirkt es wie „ein System“, obwohl die „volle“ TEK-Logik (Stück, KPIs, Tages-Spalten) weiter in DRIVE lebt.
- **Akzeptanz „Überblick statt 1:1-Kopie“:** Ihr nutzt Metabase bewusst als **Überblick** (Monatswerte, Vergleiche, Verlauf) und akzeptiert, dass Stück, DB/Stück, Absatzweg-Detail und KPI-Block **in DRIVE/PDF** bleiben.

### Metabase bringt wenig Mehrwert, wenn …

- Das Ziel ist: **„Genau dasselbe wie DRIVE/Globalcube/PDF, nur als Dashboard“**. Dann ist jeder Schritt (Kumulationszeilen, Stück, Absatzweg-Hierarchie, KPIs) doppelte Entwicklung – einmal in DRIVE, einmal in Metabase – und Metabase kann Teile (Stück, Locosoft) technisch gar nicht abdecken.
- **Hauptbedarf = fertige Reports (PDF/E-Mail) und die DRIVE-TEK im Browser.** Dann reicht: DRIVE TEK weiter ausbauen + PDF-Export aus DRIVE; ein zweites System (Metabase) für „fast wie DRIVE“ erhöht nur den Wartungsaufwand.
- Nur wenige Nutzer, und die sind mit DRIVE + PDF bereits zufrieden – dann rechtfertigt der Aufwand für Metabase-Pflege und -Abstimmung den Nutzen oft nicht.

### Fazit / Empfehlung

- **Metabase als Ergänzung:** Behalten, wenn ihr ihn als **einfachen, interaktiven Überblick** (Monat, Standort, Bereiche, Verlauf) nutzt und **nicht** als 1:1-Ersatz für DRIVE TEK/Globalcube. Dann ist der Aufwand begrenzt (einmal Queries/Views, gelegentlich Resize), und der Mehrwert ist: schneller Blick ohne DRIVE zu öffnen, ggf. Einbettung in DRIVE.
- **Metabase weglassen:** Wenn ihr euch darauf konzentrieren wollt, **eine** Reporting-Front zu haben (DRIVE + PDF), und keine Ressourcen für ein zweites Tool (Metabase) investieren wollt. Dann: DRIVE TEK und PDF-Reports weiter ausbauen; Metabase-Installation kann eingemottet oder nur für Ad-hoc-SQL genutzt werden.

**Kurz:** Der Mehrwert von Metabase ist **interaktiver Überblick und Selbstbedienung auf denselben Daten** – nicht die vollständige Nachbildung von DRIVE/PDF/Globalcube. Wenn ihr Letzteres braucht, ist DRIVE/PDF der richtige Ort; Metabase dann optional nur für „Überblick ohne Locosoft/Stück“.

---

## Wie weiter? Können wir aus Metabase bessere Reports verschicken?

**Ausgangslage:** Die TEK-PDFs wurden verbessert; danach kam Metabase ins Spiel. Die Frage: Kann Metabase die täglichen E-Mail-Reports ersetzen oder verbessern?

### Was Metabase für E-Mails kann (Dashboard-Subscriptions)

- **Dashboard-Subscriptions:** In Metabase kann man zu einem Dashboard **Abonnements** einrichten (E-Mail oder Slack). Metabase verschickt dann in festen Intervallen (täglich, wöchentlich, …) eine E-Mail mit dem **Inhalt des Dashboards** (Tabellen und Charts, wie sie im Browser erscheinen).
- **Voraussetzung:** E-Mail in Metabase konfigurieren (Admin → E-Mail-Einstellungen).
- **Filter pro Abo:** Welche Filterwerte (z. B. Standort, Monat) beim Versand gelten, ist in der **Open-Source-Version** pro Dashboard einheitlich. Pro-Empfänger-Filter (z. B. „nur DEG“ für Filialleiter DEG) gibt es nur in **Metabase Pro/Enterprise**.

### Warum eure TEK-PDFs für die E-Mail-Reports „besser“ sind

| Kriterium | E-Mail aus DRIVE/PDF (heute) | E-Mail aus Metabase (Subscription) |
|-----------|------------------------------|------------------------------------|
| **Stück, DB/Stück** | ✅ Aus Locosoft (tek_api_helper) | ❌ Nicht verfügbar (nur fact_bwa) |
| **Heute, VM/VJ** | ✅ Vollständig | ⚠️ VM/VJ ja, „Heute“ optional per eigener Query |
| **Pro Standort / pro Empfänger** | ✅ Ein Abo pro Report-Typ + Standort (Registry) | ⚠️ Pro/Enterprise für Filter pro Abo, sonst ein Dashboard = eine Version für alle |
| **Layout/Branding** | ✅ Eure PDFs/HTML genau so, wie ihr sie verbessert habt | Metabase-Standard-Layout |
| **Eine Quelle** | ✅ DRIVE + tek_api_helper = eine Logik für Web, PDF, E-Mail | Zwei Systeme (Metabase + DRIVE) pflegen |

**Fazit:** Für die **TEK-täglichen E-Mails** sind die **verbesserten PDFs aus DRIVE/tek_api_helper** inhaltlich und steuerungstechnisch besser als ein Versand aus Metabase. Metabase hat keine Locosoft-Anbindung und kann Stück/DB-Stück nicht liefern; die Abo-Logik (wer bekommt welchen Standort) habt ihr in der Registry bereits sauber gelöst.

### Sinnvolle Nutzung von Metabase trotzdem

1. **Zusätzlicher Link in der E-Mail:** In der TEK-E-Mail einen Link „TEK im Browser öffnen“ auf das Metabase-Dashboard (oder auf DRIVE) einbauen – wer will, klickt für den interaktiven Überblick.
2. **Metabase nur für andere Reports:** Für Auswertungen, die **nur** auf fact_bwa/Datenbank basieren (z. B. reine BWA, Verläufe), kann eine Metabase-Subscription sinnvoll sein – dann ohne Stück/Heute-Anspruch.
3. **Kein Ersatz für TEK-E-Mails:** Die tägliche „Handvoll“ TEK-Reports (tek_daily, tek_filiale, …) weiter wie bisher mit `send_daily_tek.py` + verbesserte PDFs versenden; Metabase nicht als Ersatz für diesen Versand nutzen.

**Kurz:** Aus Metabase **bessere** TEK-Reports zu verschicken geht inhaltlich nicht (Stück/DB-Stück fehlen). Die verbesserten PDFs bleiben die richtige Basis für die täglichen E-Mails; Metabase ergänzt als optionaler „Überblick im Browser“ oder für andere, rein DB-basierte Reports.

---

## Was DRIVE TEK mehr kann (Metabase „noch weit weg“)

In DRIVE haben Sie u. a.:
- **Standort-Filter** (Landau Opel / Deggendorf Opel / Deggendorf Hyundai) mit sofortiger Umschaltung
- **KPI-Block oben:** Umsatz, Einsatz, DB1, Marge, Abstand; Fortschritt, Ø/Tag, Hochrechnung, vs. VM/vs. VJ, Breakeven-Prognose
- **Tages-Spalten** (z. B. 05.02., 06.02. mit Umsatz/DB1 pro Tag)
- **Stück (Stk)** und **DB1/Stk** mit echten Werten aus Locosoft
- **GESAMT-Zeile** und Kumulation pro Bereich mit Anteil, vs. VM, vs. VJ pro Zeile
- **DB1-Entwicklung nach Bereichen** (Linie pro Bereich über 12 Monate)

Metabase zeigt dieselbe Datenbasis (fact_bwa), aber **ohne** Locosoft-Anbindung, **ohne** interaktiven Standort-Filter im Dashboard, **ohne** KPI-/Prognose-Logik und Tages-Spalten. Mit dem Resize-Script werden **Breite und Höhe** angepasst (volle Breite, hohe Cards), sodass die vorhandenen Tabellen und der Verlauf-Chart den Platz gut nutzen.

---

## Was hat `scripts/tek_api_helper.py` damit zu tun?

**tek_api_helper.py** ist die **Datenquelle für E-Mail- und PDF-TEK-Reports** (tägliche Reports, Filial-Reports). Es nutzt **dieselbe Logik wie die DRIVE-Web-TEK**:

- Ruft **`api.controlling_data.get_tek_data()`** auf (wie `/api/tek`)
- Holt **Stückzahlen** aus **Locosoft** (`get_stueckzahlen_locosoft`) für NW/GW
- Holt **Heute-Daten** (Umsatz, Einsatz, DB1, Stück **des aktuellen Tages**) aus der DRIVE-DB
- Liefert **Vormonat/Vorjahr** (vm, vj) für Vergleich

**Kurz:** Alles, was die **alte TEK** (Web + PDF + E-Mail) anzeigt, kommt entweder aus dieser Helper-Logik oder direkt aus `/api/tek`. Metabase hat **keinen Zugriff auf Locosoft** und keine Anbindung an diesen Helper – Metabase fragt nur die **PostgreSQL-DB** (fact_bwa) ab.

---

## Was zeigt die alte TEK (DRIVE / PDF)?

| Info | Quelle | In Metabase? |
|------|--------|---------------|
| Erlös, Einsatz, DB1 (€), DB1 (%) | DRIVE-DB / fact_bwa | ✅ Ja (erweitert um VM/VJ) |
| **Stück** (Verkaufsstückzahlen NW/GW) | **Locosoft** (tek_api_helper) | ❌ Nein |
| **DB/Stück** | Berechnung aus DB1 + Stück (Locosoft) | ❌ Nein |
| **Heute** (Umsatz/Einsatz/DB1/Stück des Tages) | DRIVE-DB + Locosoft (tek_api_helper) | ⚠️ Optional per eigener Abfrage (siehe unten) |
| **Vormonat / Vorjahr** (DB1-Vergleich) | DRIVE-DB | ✅ Ja (in „TEK Gesamt“ ergänzt) |

---

## Was wurde in Metabase ergänzt?

1. **TEK Gesamt – Monat kumuliert (Query 42)**  
   - Spalten **Stück** und **DB/Stück (€)** ergänzt (in Metabase leer; Werte nur in DRIVE/Locosoft).  
   - **VM DB1 (€)**, **VJ DB1 (€)** (Vormonat, Vorjahr).  
   - Alle Beträge **ROUND(..., 2)**.  

2. **TEK nach Standort (Query 43)**  
   - **Kumulation pro Standort:** Zeile „Summe {Standort}“ je Standort.  
   - **Kumulation pro Kostenstelle (Bereich):** Am Ende Zeilen „Summe Neuwagen“, „Summe Gebrauchtwagen“, … (Gesamt über alle Standorte).  
   - Spalten **Stück** und **DB/Stück (€)** sind enthalten, in Metabase leer (Werte nur aus Locosoft/DRIVE).  
   - Card-Größe: Script `scripts/resize_tek_dashboard_metabase.py` setzt breitere/höhere Cards.  

3. **Spalten in Metabase sichtbar machen**  
   - In Metabase: Card bearbeiten → **Formatting** / Spaltenbreiten anpassen oder Dashboard-Layout vergrößern, damit „DB1 (€)“ und „DB1 (%)“ vollständig angezeigt werden.

---

## Optional: „TEK Heute“ in Metabase

Wenn ihr in Metabase auch **Tageswerte (Heute)** sehen wollt, kann eine zusätzliche **native Abfrage** „TEK Heute“ angelegt werden. Beispiel-SQL (nur aus fact_bwa, ohne Locosoft-Stück):

```sql
-- TEK Heute: Umsatz/Einsatz/DB1 pro Bereich für den aktuellen Tag
WITH umsatz_heute AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 810000 AND 819999 THEN 'Neuwagen' WHEN konto_id BETWEEN 820000 AND 829999 THEN 'Gebrauchtwagen'
        WHEN konto_id BETWEEN 830000 AND 839999 THEN 'Teile' WHEN konto_id BETWEEN 840000 AND 849999 THEN 'Werkstatt'
        WHEN konto_id BETWEEN 860000 AND 869999 THEN 'Sonstige' END as bereich,
        SUM(-betrag) as umsatz
    FROM fact_bwa
    WHERE zeit_id >= CURRENT_DATE AND zeit_id < CURRENT_DATE + INTERVAL '1 day'
      AND ((konto_id BETWEEN 800000 AND 889999) OR (konto_id BETWEEN 893200 AND 893299)) AND debit_or_credit = 'H'
      AND NOT (standort_id = 0 AND document_number::text LIKE 'GV%')
    GROUP BY 1
),
einsatz_heute AS (
    SELECT 
        CASE WHEN konto_id BETWEEN 710000 AND 719999 THEN 'Neuwagen' WHEN konto_id BETWEEN 720000 AND 729999 THEN 'Gebrauchtwagen'
        WHEN konto_id BETWEEN 730000 AND 739999 THEN 'Teile' WHEN konto_id BETWEEN 740000 AND 749999 THEN 'Werkstatt'
        WHEN konto_id BETWEEN 760000 AND 769999 THEN 'Sonstige' END as bereich,
        SUM(betrag) as einsatz
    FROM fact_bwa
    WHERE zeit_id >= CURRENT_DATE AND zeit_id < CURRENT_DATE + INTERVAL '1 day'
      AND konto_id BETWEEN 700000 AND 799999 AND debit_or_credit = 'S'
    GROUP BY 1
)
SELECT 
    COALESCE(u.bereich, e.bereich) as "Bereich",
    ROUND(COALESCE(u.umsatz, 0), 2) as "Erlös Heute (€)",
    ROUND(COALESCE(e.einsatz, 0), 2) as "Einsatz Heute (€)",
    ROUND(COALESCE(u.umsatz, 0) - COALESCE(e.einsatz, 0), 2) as "DB1 Heute (€)"
FROM umsatz_heute u
FULL OUTER JOIN einsatz_heute e ON u.bereich = e.bereich
WHERE COALESCE(u.bereich, e.bereich) IS NOT NULL
ORDER BY CASE COALESCE(u.bereich, e.bereich) WHEN 'Neuwagen' THEN 1 WHEN 'Gebrauchtwagen' THEN 2 WHEN 'Teile' THEN 3 WHEN 'Werkstatt' THEN 4 ELSE 5 END;
```

In Metabase: **Neue Frage** → Native Query → oben einfügen → speichern → als Card zum TEK-Dashboard hinzufügen.

---

## Zusammenfassung

- **tek_api_helper.py** = zentrale Stelle für **E-Mail- und PDF-TEK**; nutzt dieselbe Logik wie DRIVE-Web-TEK (inkl. Locosoft-Stück, Heute, VM/VJ).
- **Metabase-TEK** nutzt nur die **DRIVE-DB (fact_bwa)** und wurde um **Vormonat/Vorjahr** und einheitliche Formatierung erweitert.
- **Stück und DB/Stück** gibt es in Metabase nicht (kommen aus Locosoft); **Heute** optional über eigene Abfrage „TEK Heute“.
- **Abgeschnittene Spalten** in Metabase: Card/Dashboard breiter machen oder Formatierung der Tabelle anpassen.
