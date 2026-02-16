# AfA VFW/Mietwagen — Feedback Buchhaltung (Februar 2026)

**Stand:** 2026-02-16  
**Quelle:** E-Mail Buchhaltung an Florian, Anhänge: Excel-Listen (VFW/Mietwagen je Betrieb) + DATEV-Liste (Vorführwagen)

## Angehängte Unterlagen (Buchhaltung)

- **Excel:** Mietwagen DEG, VFW Opel DEG, VFW Opel Landau, Mietwagen Landau, VFW Hyundai, VFW Leapmotor  
- **DATEV:** Alte Liste Vorführwagen (z. B. Seite 1 Summe EUR 45.566,30); Betrag Monat = Summe abzüglich Vormonat

**Ablage im Repo:** `docs/workstreams/controlling/AfA/`  
- mietwagendeg.xlsx, mietwagenlandau.xlsx, vfwopeldeg.xlsx, vfwopellandau.xlsx, vfwhyundai.xlsx, vfwleapmotor.xlsx, Scan_20260216130905.pdf

**Auswertung (2026-02-16):**
- **Mietwagen-Listen:** Fz.-Art = G (Gebrauchtwagen), **Jw-Kz = M** (Jahreswagenkennzeichen). DRIVE-Filter für Mietwagen wurde um `pre_owned_car_code = 'M'` ergänzt (neben „X“), damit Abgleich mit Buchhaltungs-Listen.
- **VFW-Listen:** Fz.-Art = V, Jw-Kz oft leer. Filter `dealer_vehicle_type = 'V'` unverändert.
- **Nutzungsdauer:** In den Excel-Spalten keine Spalte „Nutzungsdauer“/„AfA-Dauer“ gefunden. Modul nutzt **72 Monate** (6 Jahre). DATEV-PDF (Scan) wurde nicht textlich ausgewertet; bei abweichender Vorgabe bitte melden.

---

## Durchgeführte Buchungen (Buchhaltung)

### Monatsende — Opel-Betrieb (DEG + Landau)

| Buchung (Soll an Haben) | Verwendung |
|-------------------------|------------|
| Konto **450001** an **090301** | Mietwagen DEG |
| Konto **450002** an **090302** | Mietwagen LAN |
| Konto **450001** an **090401** | Vorführwagen DEG |
| Konto **450002** an **090402** | Vorführwagen LAN |

### Monatsende — Hyundai-Betrieb

| Buchung (Soll an Haben) | Verwendung |
|-------------------------|------------|
| Konto **450001** an **090301** | Mietwagen Hyundai |
| Konto **450001** an **090401** | Vorführwagen Hyundai |

### Ermittlung Betrag

- Anhand DATEV-Liste (z. B. Summe Seite 1) **abzüglich Vormonat** = AfA-Betrag des Monats.

---

## Abgang (Verkauf / Umbuchung Gebrauchtwagenbestand)

- Abschreibung wird **aufgelöst** und **einsatzmindernd auf das Fahrzeug** gebucht.
- **Buchung:** Konto **090401** (bzw. 090301/090302/090402 je nach Art und Betrieb) **an Bestandskonto**.

→ Für Abgang in DRIVE: Restbuchwert und ggf. Buchgewinn/-verlust erfassen; Buchhaltung bucht 090xxx an Bestandskonto.

---

## Konten-Mapping für DRIVE (betriebsnr = 1 DEG, 2 HYU, 3 LAN)

| betriebsnr | Standort | Mietwagen (Soll an Haben) | VFW (Soll an Haben) |
|------------|----------|---------------------------|----------------------|
| 1 | DEG Opel | 450001 an **090301** | 450001 an **090401** |
| 2 | HYU | 450001 an **090301** | 450001 an **090401** |
| 3 | LAN | 450002 an **090302** | 450002 an **090402** |

- **450001** = Auflaufende Abschreibung (Deggendorf/Opel + Hyundai)  
- **450002** = Auflaufende Abschreibung (Landau)  
- **090301** = Mietwagen (DEG + HYU)  
- **090302** = Mietwagen (LAN)  
- **090401** = Vorführwagen (DEG + HYU)  
- **090402** = Vorführwagen (LAN)  

---

## Umsetzung im AfA-Modul

- **Monatsübersicht / CSV-Export:** Pro Position optional **Konto Soll** und **Konto Haben** ausgeben (z. B. 450001 / 090401), damit Buchhaltung die Zuordnung hat.
- **Abgang:** Bei „Verkauf/Umbuchung“ in DRIVE nur Restbuchwert/Buchgewinn erfassen; Buchung 090xxx an Bestandskonto erfolgt in der Buchhaltung.
- **Nächste Schritte (optional):** RedBeat-Task am 1. des Monats für Vormonat; ggf. Summen pro Konto (090301, 090302, 090401, 090402) für Abgleich mit DATEV.
