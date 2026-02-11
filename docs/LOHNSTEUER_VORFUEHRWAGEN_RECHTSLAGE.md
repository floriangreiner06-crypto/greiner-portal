# Lohnsteuerprüfung: Pauschale Dienstwagenbesteuerung (Vorführwagen)

**Stand:** Februar 2025  
**Anlass:** Lohnsteuerprüfung – Prüfer möchte die Pauschale für Vorführwagen prüfen.

---

## 1. Sachverhalt (Greiner)

- Verkäufer und weitere MA nutzen **Vorführwagen** aus dem Pool als Dienstwagen.
- Keine dauerhafte Zuweisung: Fahrzeuge müssen für Kunden-Probefahrten verfügbar bleiben.
- **FA Deggendorf** akzeptiert einen **Durchschnittswert** aller Vorführwagen (derzeit **23.000 € UPE brutto** → 1%-Regel = **230 €/Monat** zu versteuern).

---

## 2. Rechtslage (Kurzüberblick)

### 2.1 1%-Regelung (Standard)

- **Bemessungsgrundlage:** Bruttolistenpreis (inkl. Sonderausstattung, USt) zum Zeitpunkt der **Erstzulassung**.
- **Geldwerter Vorteil:** **1 % des Bruttolistenpreises pro Monat** – unabhängig von der tatsächlichen privaten Nutzung.
- **Beispiel:** 40.000 € Listenpreis → 400 €/Monat zu versteuern.

*Quelle: LStR R 8.1 Abs. 9, 10; § 8 Abs. 2 EStG (geldwerter Vorteil).*

### 2.2 Ermäßigung für Elektro- und Plug-in-Hybridfahrzeuge

| Fahrzeugart | Regelung | Bemessung | Zeitraum |
|-------------|----------|-----------|----------|
| **Reine E-Fahrzeuge** (Batterie) | **0,25 %** | Bruttolistenpreis (Basis gekürzt) | Anschaffung/Leasing 2019–2030; Preisgrenze s. unten |
| **Reine E-Fahrzeuge** (teurer) | **0,5 %** | Bruttolistenpreis | Anschaffung 2019–2030, über Preisgrenze |
| **Plug-in-Hybride** | **0,5 %** | **Hälfte** des Bruttolistenpreises | Anschaffung 2019–2030, Auflagen erfüllt |

**Preisgrenzen für 0,25 % (reine E-Fahrzeuge):**

- Bis 31.12.2023: Bruttolistenpreis **bis 60.000 €**
- 01.01.2024 – 30.06.2025: **bis 70.000 €**
- Ab 01.07.2025: **bis 100.000 €** (Stand Gesetzeslage)

Über der Grenze: 0,5 % des Bruttolistenpreises.

**Folge für die Pauschale:**  
Wenn viele Vorführwagen **Elektro** oder **Plug-in-Hybrid** sind, sinkt der **durchschnittliche** monatliche geldwerte Vorteil (0,25 % bzw. 0,5 % statt 1 %) – die **Pauschale kann niedriger** angesetzt werden.

### 2.3 Vorführwagen-Pool und Durchschnittswert

- Bei **wechselnder Nutzung** (Pool, keine feste Zuweisung) ist die **1 %-Regelung** auf den jeweiligen (oder vereinbarten) Wert des genutzten Fahrzeugs anzuwenden.
- Wenn das FA einen **Durchschnittswert** akzeptiert (wie in Deggendorf), muss dieser **sachlich begründet** sein (z. B. Auswertung der tatsächlich als Vorführwagen genutzten Fahrzeuge, ggf. mit Listenpreisen und Antriebsart).
- **Dokumentation:** Welche Fahrzeuge zählen zum Pool? Welche Listenpreise/Antriebsarten? → Auswertung aus Locosoft (VFW 2023/2024, km > 1.000, Antriebsart) unterstützt die Nachvollziehbarkeit und kann eine **möglichst geringe Pauschale** rechtfertigen.

### 2.4 Zusätzlich: Entfernungspauschale (0,03 %)

- Für **Fahrten Wohnung–Arbeitsstätte** gilt zusätzlich die **0,03 %-Regel** pro Entfernungskilometer (oder tageweise 0,002 %).
- Unabhängig von der 1 %- bzw. 0,5 %-/0,25 %-Regelung.

---

## 3. Pauschale möglichst gering halten – Handlungsoptionen

1. **Antriebsart auswerten**  
   Alle Vorführwagen, die in die Pauschale einfließen, nach **Verbrenner / Elektro / Plug-in-Hybrid** trennen. E und PHEV senken den Durchschnittswert (0,25 % bzw. 0,5 %).

2. **Nur Fahrzeuge mit nennenswerter Nutzung**  
   Fahrzeuge mit **sehr geringer Laufleistung** (z. B. unter 1.000 km) könnten fachlich ggf. aus dem „typischen“ Pool herausgenommen werden, wenn so mit dem FA vereinbart. Die Auswertung „VFW mit > 1.000 km“ schafft Transparenz.

3. **Durchschnittswert neu berechnen**  
   - Pro Fahrzeug: Bruttolistenpreis (oder Ersatzwert) × richtigen Satz (1 % / 0,5 % / 0,25 %)  
   - **Durchschnitt** dieser monatlichen Werte über alle relevanten VFW → ergibt die **sachlich begründete Pauschale**.

4. **Dokumentation für die Lohnsteuerprüfung**  
   - Liste: Vorführwagen 2023/2024, Kennzeichen, Modell, EZ, km, Antriebsart, ggf. Listenpreis.  
   - Daraus: Berechnung des Durchschnitts (1 % / 0,5 % / 0,25 %) und Begründung der gewählten Pauschale (z. B. 230 € oder niedriger).

---

## 4. Technische Auswertung (Locosoft)

- Siehe Skript: **`scripts/vfw_lohnsteuer_2023_2024.py`**
- **Prüfungszeitraum:** 01.2022 bis 12.2025 (Ankunft bis 31.12.2025, Abmeldung frühestens 01.01.2022).
- **VFW-Erkennung (Locosoft):** Kommissionsnummer (Kom.Nr.) nur **V** oder **G** (T ausgeschlossen). V = unverkauft, G = z. B. verkaufte Ex-VFW (Jahreswagenkennzeichen X).
- Liefert: Alle so erkannten VFW im Prüfungszeitraum mit **mehr als 1.000 km**, inkl. **Antriebsart**, Status Unverkauft/Verkauft und **UPE-Werte**.
- **UPE brutto (für 1%-Regel):** Ermittlung aus Locosoft mit Priorität:  
  1. `out_recommended_retail_price` (empf. VK, oft bereits Brutto),  
  2. `in_buy_list_price` × 1,19 (Listenpreis Netto → Brutto),  
  3. `models.suggested_net_retail_price` × 1,19 (Modell-Stücklistenpreis).  
  Daraus: **geldwerter Vorteil/Monat** (1 % bzw. 0,5 % bei E/Hybrid von UPE brutto). Durchschnitt UPE und Durchschnitt geldwerter Vorteil werden ausgegeben.
- Ausgabe: Konsolen-Tabelle + optional CSV mit allen Preisspalten für Prüfer und Pauschalen-Berechnung.

---

## 5. Kurzfassung für Prüfer

- **1 %-Regel:** Standard für Verbrenner; Bemessung = Bruttolistenpreis.
- **0,5 % / 0,25 %:** Für E und Plug-in-Hybrid; senken den durchschnittlichen geldwerten Vorteil.
- **Pauschale:** FA akzeptiert Durchschnittswert; Auswertung VFW 2023/2024 mit km > 1.000 und Antriebsart dient der **sachlichen Begründung** und kann eine **möglichst geringe Pauschale** (z. B. unter 230 €) stützen.

*Kein Steuerberatungsersatz – bei Unsicherheiten bitte Steuerberater/FA einschalten.*
