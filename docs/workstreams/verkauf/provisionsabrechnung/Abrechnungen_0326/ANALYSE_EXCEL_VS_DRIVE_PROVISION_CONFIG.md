# Analyse: Excel-Abrechnungen März 2026 vs. DRIVE provision-config

**Stand:** 2026-03-02  
**Quelle:** `Abrechnungen_0326/` – je eine Excel-Datei pro Verkäufer (Provisionsabrechnung_V0.11_*.xlsm) mit gefilterten Daten.

**Ziel:** Konkrete Änderungsvorschläge für http://drive/admin/provision-config, damit DRIVE die gleichen Regeln wie das Excel-Provisionstool anwendet (oder bewusste Abweichungen dokumentiert).

---

## 1. Aus den Excel-Dateien ausgelesen

### 1.1 Optionen (alle 7 Verkäufer-Dateien identisch)

| Zelle | Bedeutung (laut PROVISIONSLOGIK_AUS_EXCEL.md) | Wert in Excel |
|-------|------------------------------------------------|---------------|
| **J52** | Prov. Neuwagen (Block I)                      | **0,12** (12 %) |
| **J53** | Block VFW / 1 %                               | **0,01** (1 %)  |
| **J54** | Block GW / 1 %                                | **0,01** (1 %)  |
| **J55** | (D)                                            | 0,02            |
| **J60** | GW aus Bestand – Kostenfaktor (Prov)          | **0,01**        |
| **J61** | GW aus Bestand – Fixbetrag (Fix)               | **175**        |

### 1.2 Neuwagen (Block I) im Excel

- **Formel in Fahrzeugverkaeufe:** `J11 = H11 * AC11` mit  
  - **H** = Spalte AF im Import = **Deckungsbeitrag (DB)**  
  - **I11** = Optionen!$J$52 = **0,12**
- **Ergebnis:** Provision Neuwagen = **DB × 12 %** (Bemessungsgrundlage = **DB**, nicht Rg.Netto).
- Zusätzlich im Excel: **50 € pro Stück** (max. 15 Stück) – siehe PROVISIONSLOGIK („+ 50 € Fix pro Stück (bis 15 Stück)“).

### 1.3 Testwagen/VFW und Gebrauchtwagen (Block II / III) im Excel

- **Maßgröße:** Erlös = **Rg.Netto** (Spalte R im Import), **Prov.Satz 1 %**.
- **Grenzen in den Formeln:**
  - Im Bereich **„Vorführwagen-Verkäufe“** (Fahrzeugverkaeufe Zeilen 41–65):  
    `=WENN(Erlös*Satz < 103; 103; WENN(Erlös*Satz > 500; 500; Erlös*Satz))` → **Min 103 €, Max 500 €**
  - Im Bereich **„Gebrauchtwagen-Verkäufe“** (Zeilen 81–95):  
    `=WENN(Erlös*Satz < 103; 103; WENN(Erlös*Satz > 300; 300; Erlös*Satz))` → **Min 103 €, Max 300 €**

**Hinweis:** In PROVISIONSLOGIK_AUS_EXCEL.md steht umgekehrt: „II. Testwagen/VFW … max 500“, „Vorführwagen (T/V) … max 300“. Im vorliegenden Excel ist der **Vorführwagen-Block** mit **max 500** und der **Gebrauchtwagen-Block** mit **max 300** umgesetzt. Das sollte fachlich abgeglichen werden (siehe Abschnitt 3).

### 1.4 GW aus Bestand (Block IV) im Excel

- **Formel:** BE II = (DB × J60) + J61, Provision = **(DB − BE II) × 12 %**
- **J60 = 0,01**, **J61 = 175** → bereits in DRIVE abgebildet.

---

## 2. Aktueller Stand DRIVE provision_config (Auszug März 2026)

| Kategorie            | Bemessungsgrundlage | Prozentsatz | Min € | Max € | J60  | J61  | Zielprämie (NW) |
|----------------------|---------------------|------------|-------|-------|------|------|------------------|
| **I_neuwagen**       | rg_netto            | 0,01       | –     | –     | –    | –    | ja (100 €)       |
| **II_testwagen**     | rg_netto            | 0,01       | 103   | 300   | –    | –    | –                |
| **III_gebrauchtwagen** | rg_netto          | 0,01       | 103   | 500   | –    | –    | –                |
| **IV_gw_bestand**    | db                  | 0,12       | –     | –     | 0,01 | 175  | –                |

---

## 3. Abweichungen Excel ↔ DRIVE

| Punkt | Excel | DRIVE aktuell | Bewertung |
|-------|--------|----------------|-----------|
| **I. Neuwagen – Bemessung** | **DB**, 12 % | rg_netto, 1 % | DRIVE wurde bewusst auf „Rg.Netto 1 %“ umgestellt (negativer DB soll nicht zu negativer Provision führen). Wenn Abrechnung 1:1 wie Excel: auf DB 12 % zurücksetzen. |
| **I. Neuwagen – Stückanteil** | 50 €/Stück, max 15 | Zielprämie (100 € bei Zielerreichung + Übererfüllung) | Excel kennt keine Zielprämie, sondern feste Stückprämie. Entweder in DRIVE Zielprämie abschalten und 50 €/15 Stück setzen (Excel-Gleichheit) oder Zielprämie beibehalten (bewusste Abweichung). |
| **II / III – Min/Max** | VFW-Bereich: 103/500; GW-Bereich: 103/300 | II: 103/300; III: 103/500 | Im Excel ist Vorführwagen-Block mit **500** und GW-Block mit **300** begrenzt. In DRIVE ist II (Testwagen/VFW) mit **300** und III (GW) mit **500** hinterlegt. **Fachlich klären:** Welche Kategorie soll max 300 bzw. max 500 haben? |
| **IV. GW Bestand** | J60=0,01, J61=175, 12 % | identisch | Keine Änderung nötig. |

---

## 4. Konkrete Änderungsvorschläge für http://drive/admin/provision-config

### Option A: DRIVE an Excel angleichen (1:1 wie Excel-Tool)

| Kategorie | Aktion | Feld | Wert (Vorschlag) |
|-----------|--------|------|-------------------|
| **I_neuwagen** | Bearbeiten | Bemessungsgrundlage | **db** |
| **I_neuwagen** | Bearbeiten | Prozentsatz | **0,12** (12 %) |
| **I_neuwagen** | Bearbeiten | use_zielpraemie (Zielprämie NW) | **false** (abschalten) |
| **I_neuwagen** | Bearbeiten | stueck_praemie | **50** |
| **I_neuwagen** | Bearbeiten | stueck_max | **15** |
| **II_testwagen** | Prüfen | max_betrag | Wenn fachlich „VFW = max 500“ bestätigt: **500** (aktuell 300). |
| **III_gebrauchtwagen** | Prüfen | max_betrag | Wenn fachlich „GW = max 300“ bestätigt: **300** (aktuell 500). |
| **IV_gw_bestand** | – | – | Keine Änderung (J60=0,01, J61=175 bereits gesetzt). |

### Option B: Bewusste Abweichung beibehalten (Neuwagen auf Rg.Netto 1 %)

- **I_neuwagen:**  
  - Bemessungsgrundlage **rg_netto**, Prozentsatz **0,01** beibehalten (wie bereits eingestellt).  
  - Dann keine Anpassung für Block I nötig; nur dokumentieren, dass Excel weiter mit DB 12 % rechnet.
- **II / III:**  
  - Wie unter Option A: erst nach fachlicher Bestätigung (VFW vs. GW: wer 300 vs. 500) anpassen.

### Zusammenfassung Empfehlung

1. **Fachlich klären:**  
   - Soll Neuwagen in DRIVE wie im Excel mit **DB 12 %** laufen (Option A) oder soll **Rg.Netto 1 %** beibehalten werden (Option B)?  
   - Welche Kategorie hat im Excel/DRIVE **max 300** bzw. **max 500** (Testwagen/VFW vs. Gebrauchtwagen)?

2. **Wenn 1:1 wie Excel gewünscht:**  
   - I_neuwagen: Bemessungsgrundlage **db**, Prozentsatz **0,12**, Zielprämie **aus**, stueck_praemie **50**, stueck_max **15**.  
   - II/III: Min/Max erst nach Klärung von Punkt 1 anpassen.

3. **IV_gw_bestand:**  
   - Keine Änderung; J60=0,01 und J61=175 sind bereits korrekt.

4. **Nach Änderungen:**  
   - Vorläufe für den betroffenen Monat ggf. löschen und neu erzeugen, damit die neuen Sätze in den Positionen und im PDF greifen.
