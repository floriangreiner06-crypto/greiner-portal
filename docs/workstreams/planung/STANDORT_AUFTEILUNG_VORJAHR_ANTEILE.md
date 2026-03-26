# Standort-Aufteilung nach Vorjahres-Anteilen

**Zweck:** Planzahlen (NW/GW) auf die drei Standorte verteilen, indem die **Anteile aus dem Vorjahr** (Locosoft) verwendet werden.

**Standorte:** 1 = Deggendorf Opel, 2 = Deggendorf Hyundai, 3 = Landau Opel

---

## Formel

- **Vorjahr:** Geschäftsjahr (z.B. 2024/25) = 1.9. bis 31.8.
- **Stück VJ:** Aus Locosoft `dealer_vehicles`:
  - NW: `dealer_vehicle_type IN ('N','T','V')`, GW: `IN ('G','D','L')`
  - Gruppierung nach `out_subsidiary` (1, 2, 3)
- **Anteil Standort s:**  
  `Anteil_s = Stück_VJ_s / Summe(Stück_VJ_1, Stück_VJ_2, Stück_VJ_3)`
- **Plan Standort s:**  
  `Plan_s = round(Plan_gesamt * Anteil_s)`  
  Standort 3 bekommt den Rest, damit die Summe exakt Plan_gesamt ist.

**Opel 280 (nur Standort 1 + 3):**  
- Anteil_1 = NW_VJ_1 / (NW_VJ_1 + NW_VJ_3), Anteil_3 = 1 - Anteil_1  
- Plan_1 = round(280 * Anteil_1), Plan_3 = 280 - Plan_1  

**Hyundai 200:** komplett Standort 2.  
**Leapmotor 100:** manuell zuordnen (z.B. Standort 1).

---

## Script nutzen

```bash
cd /opt/greiner-portal
python scripts/planung_standort_anteile_vorjahr.py 2024/25
```

- **Argument:** Geschäftsjahr des **Vorjahres** (Referenz für Anteile), z.B. `2024/25`.
- **Ausgabe:**
  - VJ-IST Stück NW und GW pro Standort (und Anteile in %)
  - Vorschlag Plan: NW 580 und GW 850 nach VJ-Anteilen verteilt
  - Opel 280 Aufteilung auf Standort 1 und 3 nach VJ-NW-Anteil

Planzahlen (580 NW, 850 GW) sind im Script konfigurierbar (Variablen `nw_gesamt`, `gw_gesamt`).

---

## Abgleich mit Abteilungsleiter-Planung

Die ausgegebenen Stückzahlen pro Standort können direkt in der **Abteilungsleiter-Planung** (http://drive/planung/abteilungsleiter) pro Bereich/Standort eingetragen werden (z.B. als Jahresplanung oder Monatswerte). Die übrigen „10 Fragen“ (Bruttoertrag/Fzg, Standzeit etc.) weiter aus Vorjahr oder Zielwerten befüllen.
