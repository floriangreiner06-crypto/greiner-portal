# AfA Abgang: Buchungen in Locosoft (Verkauf / Umbuchung) — Umsetzungsvorschlag

**Stand:** 2026-02  
**Quelle:** Feedback Buchhaltung (Christian)  
**Status:** Option A (Doku/Referenz) von Christian bestätigt. **Umgesetzt:** Im Fahrzeug-Detail kann ein Abgangsdatum eingegeben werden; DRIVE ermittelt und zeigt die **aufgelaufene AfA** (und Restbuchwert) – Buchung in Locosoft erfolgt weiterhin manuell durch die Buchhaltung.

---

## 1. Ausgangslage

Bei **Verkauf** eines Fahrzeugs aus dem Anlagevermögen bzw. **Umbuchung in den Gebrauchtwagenbestand** wird in der Buchhaltung u. a. folgendes durchgeführt:

- **Vollabgang** in DATEV
- DATEV ermittelt die **bisher aufgelaufene AfA** des Fahrzeugs
- Dieser Betrag wird in **Locosoft** je nach Vorgang unterschiedlich gebucht (siehe unten)

Die Konten für die **laufende Monats-AfA** (Soll 450001/450002 an Haben 090301/090302/090401/090402) sind im AfA-Modul bereits umgesetzt.  
Hier geht es um die **Abgangs-Buchung** (Auflösung der AfA-Anlagenkonten) in Locosoft.

---

## 2. Konten-Matrix (Feedback Christian)

Buchungssatz in Locosoft: **Haben an Soll** (Auflösung des AfA-Habenkontos).

| Kategorie            | Bei Fakturierung (Verkauf)     | Bei Umbuchung in Gebrauchtwagenbestand |
|----------------------|---------------------------------|----------------------------------------|
| Mietwagen DEG        | 090301 an **022501**            | 090301 an **324001**                    |
| Mietwagen LAN        | 090302 an **022502**            | 090302 an **324002**                    |
| VFW DEG              | 090401 an **318001**            | 090401 an **324001**                    |
| VFW LAN              | 090402 an **318002**            | 090402 an **324002**                    |
| VFW Leapmotor        | 090401 an **318201**            | 090401 an **324001**                    |
| Mietwagen Hyundai    | 090301 an **022501**            | 090301 an **324001**                    |
| VFW Hyundai          | 090401 an **318001**            | 090401 an **324001**                    |

- **Linke Spalte (Fakturierung):** Abgang Anlagevermögen durch Verkauf → Auflösung gegen die bisherigen Anlagenkonten (022501, 022502, 318001, 318002, 318201).
- **Rechte Spalte (Umbuchung):** Umbuchung in Gebrauchtwagenbestand → Auflösung gegen Bestandskonten 324001 / 324002.

---

## 3. Wo betrifft das das AfA-Modul im Portal?

- **Abgang buchen:** Im Fahrzeug-Detail kann heute ein **Abgangsdatum** (und optional Verkaufspreis/Buchgewinn) erfasst werden. Es wird **kein** Buchungssatz für Locosoft erzeugt; die Buchung macht die Buchhaltung in Locosoft/DATEV.
- **Abgangs-Kontrolle:** Zeigt DRIVE vs. Locosoft (Verkaufsdatum), damit Abgänge in DRIVE nachgezogen werden können.
- **Monatsübersicht / CSV:** Liefert die **laufenden** AfA-Buchungen (450001/450002 an 090xxx), nicht die Abgangs-Buchungen.

Eine **Abgangs-Buchung** (090301/090302/090401 an 022501/022502/318001/318002/318201 bzw. 324001/324002) wird vom Portal aktuell **nicht** erzeugt oder exportiert.

---

## 4. Umsetzungsvorschlag (Optionen)

### Option A: Nur Doku / Referenz (minimal)

- **Dieses Dokument** und die Konten-Matrix in die bestehende AfA-Doku (z. B. Anleitung oder CONTEXT) übernehmen.
- Beim Abgang im Portal **keine** Änderung; Buchhaltung nutzt die Tabelle als Referenz für die manuelle Buchung in Locosoft.
- **Vorteil:** Kein Entwicklungsaufwand, sofort nutzbar.  
- **Nachteil:** Kein direkter Bezug im Portal (z. B. kein Hinweis „Welcher Buchungssatz?“ beim Abgang).

### Option B: Hinweis beim Abgang im Portal (klein)

- Beim **„Abgang buchen“** im Fahrzeug-Detail einen **Hinweistext** anzeigen, z. B.:
  - „Buchung in Locosoft: [Kategorie] → 090xxx an [Zielkonto]. Bei Verkauf: 090xxx an 022501/022502/318001/318002/318201; bei Umbuchung in GW-Bestand: 090xxx an 324001/324002. Siehe AfA-Doku.“
- Kategorie und 090xxx aus dem Fahrzeug (Art, Standort, ggf. Leapmotor) ableiten; Zielkonto je nach Auswahl „Verkauf“ vs. „Umbuchung GW“ (falls wir diese Auswahl einführen).
- **Vorteil:** Buchhaltung sieht den passenden Buchungssatz direkt beim Abgang.  
- **Aufwand:** Kleine Anpassung im Abgang-Modal (Text + ggf. Logik für Verkauf vs. Umbuchung).

### Option C: Abgangs-Buchungssatz in der Abgangs-Kontrolle

- In der **Abgangs-Kontrolle** (DRIVE vs. Locosoft) pro „Bitte prüfen“-Zeile optional anzeigen: „Vorschlag Buchung Locosoft: 090301 an 022501“ (Beispiel), abhängig von Art/Standort.
- **Vorteil:** Kontext wo Abgänge fehlen.  
- **Nachteil:** Zusätzliche Logik und evtl. Verwechslung mit der laufenden AfA-Buchung.

### Option D: Separater Export „Abgangs-Buchungen“ (größer)

- Neue Funktion: z. B. „Abgänge im Monat XY“ mit Export einer CSV/Liste mit: Fahrzeug, aufgelaufene AfA (kumuliert), Kategorie, **vorgeschlagener Buchungssatz** (090xxx an Zielkonto) für Verkauf bzw. Umbuchung.
- Buchhaltung könnte diese Liste als Vorlage für Locosoft nutzen.
- **Vorteil:** Sehr nahe an der Buchhaltungsarbeit.  
- **Aufwand:** Deutlich mehr (Berechnung kumulierte AfA, Auswahl Verkauf/Umbuchung, Konten-Logik, Export).

---

## 5. Empfehlung

- **Kurzfristig:** **Option A** umsetzen (Doku/Konten-Matrix in AfA-Doku aufnehmen und mit Christian abgleichen).
- **Mittelfristig:** **Option B** prüfen – Hinweis beim Abgang buchen, welcher Buchungssatz in Locosoft zu buchen ist (inkl. Unterscheidung Verkauf vs. Umbuchung GW, sofern gewünscht).

Sobald entschieden ist, welche Option gewünscht ist, kann die konkrete Umsetzung (inkl. evtl. neuer Felder „Abgangsart: Verkauf / Umbuchung GW“) geplant werden.

---

## 6. Referenz Konten (Kurz)

| Kategorie        | Haben (AfA) | Ziel bei Verkauf | Ziel bei Umbuchung GW |
|------------------|-------------|-------------------|------------------------|
| Mietwagen DEG    | 090301      | 022501            | 324001                 |
| Mietwagen LAN    | 090302      | 022502            | 324002                 |
| VFW DEG          | 090401      | 318001            | 324001                 |
| VFW LAN          | 090402      | 318002            | 324002                 |
| VFW Leapmotor    | 090401      | 318201            | 324001                 |
| Mietwagen Hyundai| 090301      | 022501            | 324001                 |
| VFW Hyundai      | 090401      | 318001            | 324001                 |

(Standorte: DEG = 1, Hyundai = 2, LAN = 3.)
