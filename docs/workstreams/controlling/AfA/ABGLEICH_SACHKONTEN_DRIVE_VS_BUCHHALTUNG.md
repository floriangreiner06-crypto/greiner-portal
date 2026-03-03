# AfA Sachkonten – Abgleich DRIVE vs. Buchhaltung

**Wichtig:** Die von euch genannten Sachkontenwerte (090301, 090302, 090401, 090402) sind **AfA-Werte** (kumulierte Abschreibung), **nicht** Restbuchwerte. Der Vergleich muss AfA zu AfA erfolgen; die Differenz der Restbuchwerte leitet sich daraus ab.

---

## 1. Buchhaltung (gegebene Werte = kumulierte AfA)

| Konto  | Bezeichnung     | Buchhaltung **AfA** (€) |
|--------|-----------------|--------------------------|
| 090301 | RENT DEG       | 45.540,69                |
| 090302 | RENT LAN       | 24.921,69                |
| 090401 | VFW Opel DEG   | 66.873,00                |
| 090402 | VFW Opel LAN   | 21.692,90                |
| 090401 | VFW HYU        | 179.172,60               |

**Summe Buchhaltung (kumulierte AfA):** 45.540,69 + 24.921,69 + 66.873,00 + 21.692,90 + 179.172,60 = **338.200,88 €**

---

## 2. DRIVE (nur aktive Fahrzeuge, gleicher Stichtag)

Aus DRIVE berechnet (Summe über alle aktiven AfA-Fahrzeuge):

| Größe | Betrag (€) |
|-------|------------|
| Summe Anschaffungskosten netto | 2.789.126,55 |
| Summe Restbuchwert | 2.360.507,46 |
| **Summe kumulierte AfA (bisher)** | **428.619,09** |

(Formel: kumulierte AfA = Anschaffungskosten − Restbuchwert)

---

## 3. Vergleich AfA → ermittelte Differenz

| | Buchhaltung | DRIVE |
|---|-------------|--------|
| **Kumulierte AfA** | 338.200,88 | 428.619,09 |
| **Differenz (Buchhaltung − DRIVE)** | | **−90.418,21 €** |

**Bedeutung:** Die Buchhaltung hat **90.418,21 € weniger** an AfA gebucht als DRIVE (pauschale Abschreibung liegt hinter der in DRIVE kalkulierten Einzelabschreibung).

---

## 4. Daraus abgeleitet: Restbuchwerte (bei gleichen Anschaffungskosten)

Restbuchwert = Anschaffungskosten − kumulierte AfA. Unter der Annahme **gleicher** Anschaffungskosten in Buchhaltung und DRIVE:

| | Buchhaltung | DRIVE |
|---|-------------|--------|
| Anschaffungskosten (angenommen gleich) | 2.789.126,55 | 2.789.126,55 |
| Kumulierte AfA | 338.200,88 | 428.619,09 |
| **Restbuchwert** | **2.450.925,67** | **2.360.507,46** |
| **Differenz Restbuchwert (Buchhaltung − DRIVE)** | | **+90.418,21 €** |

→ In der Buchhaltung stehen die Restbuchwerte rechnerisch **90.418,21 € höher** als in DRIVE, weil dort **weniger** abgeschrieben wurde. Oder anders: **In der Buchhaltung fehlen 90.418,21 € an kumulierter AfA** gegenüber DRIVE.

---

## 5. Konten-Mapping (DRIVE)

| Konto  | DRIVE Zuordnung |
|--------|------------------|
| 090301 | Mietwagen DEG (bn 1), HYU (bn 2) |
| 090302 | Mietwagen LAN (bn 3) |
| 090401 | VFW DEG (bn 1), HYU (bn 2) |
| 090402 | VFW LAN (bn 3) |

---

## 6. Verwendung im Portal

- **AFA_DIFFERENZ_DRIVE_LOCOSOFT:** Soll den Betrag abbilden, um den die Buchhaltung **hinter** DRIVE liegt (Buchhaltung hat **niedrigere** Restbuchwerte = mehr AfA gebucht).  
  Mit den **hier** verwendeten Buchhaltungs-AfA-Werten (Summe 338.200,88 €) liegt die Buchhaltung **nicht** hinter, sondern **vor** DRIVE: Restbuchwerte in der Buchhaltung sind rechnerisch **90.418,21 € höher** (weil weniger AfA gebucht). In diesem Fall ist die Differenz für den Aufschlag **0** (kein Aufschlag nötig).  
  Wenn ihr umgekehrt Werte habt, bei denen die Buchhaltung **hinter** DRIVE liegt (z. B. „ca. −87.000“ = Buchhaltung RBW 87.000 € niedriger), dann **AFA_DIFFERENZ_DRIVE_LOCOSOFT = 87000** (oder aktueller Betrag) in `config/.env` setzen.
- **Verkaufsempfehlungen – Aufschlag (€):** Wird anteilig aus dieser Differenz berechnet, wenn die Buchhaltung **hinter** DRIVE liegt – damit der „echte“ Buchgewinn (DRIVE-Logik) beim Verkauf wenigstens realisiert werden kann.

---

## 7. Neuberechnung ausführen

DRIVE-Summen (Restbuchwert, kumulierte AfA, Anschaffungskosten) können mit einem Script neu berechnet werden; die Buchhaltung liefert die **AfA-Werte** pro Konto. Dann:

**Differenz kumulierte AfA = Summe(Buchhaltung AfA) − Summe(DRIVE AfA)**  
**Differenz Restbuchwert = − Differenz kumulierte AfA** (bei gleichen AK).

**Stand:** März 2026 · Korrektur: Buchhaltungswerte sind AfA (kumulierte Abschreibung), nicht Buchwerte; Differenz aus AfA-Vergleich ermittelt: **90.418,21 €**.
