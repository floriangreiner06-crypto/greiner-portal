# Controlling-Dashboards und tägliches E-Mail-Reporting – Vorgehen

**Stand:** 2026-02  
**Ziel:** DRIVE = interaktive Dashboards mit Filtern; E-Mail = eine Handvoll täglicher Reports für guten Überblick.

---

## Kontext und Anforderungen (wie zu Chatbeginn)

### Kontext

- **DRIVE Controlling:** Dashboards wie bisher mit Filterkriterien (Zeitraum, Standort, KST, Firma, Bereich usw.) – keine Änderung am gewohnten Arbeiten.
- **Tägliches E-Mail-Reporting:** Es soll **eine Handvoll** Reports täglich per E-Mail versendet werden, die einen **guten Überblick** verschaffen – ohne dass jeder alles in DRIVE nachbauen oder manuell abrufen muss.

### Anforderungen (zusammengefasst)

1. **Controlling-Dashboards** bleiben in **DRIVE**, mit allen Filtern (Zeitraum, Standort, KST, usw.).
2. **Täglich per E-Mail** soll eine **überschaubare Anzahl** von Reports laufen („Handvoll“), die einen **guten Überblick** liefern.
3. **Inhalt der E-Mail-Reports:** Gleiche Logik/Daten wie DRIVE (z. B. TEK mit Bereichen, Stück, DB/Stück, Kumulation, VM/VJ), versendet als PDF oder HTML.
4. **Kein 1:1-Nachbau** aller DRIVE-Dashboards in Metabase – Aufwand und Mehrwert stehen in Frage; Fokus auf DRIVE + E-Mail-Reports.

### In der Registry vorhandene Reports (für die „Handvoll“ nutzbar)

| Report-ID | Name | Beschreibung | Kategorie |
|-----------|------|--------------|-----------|
| **tek_daily** | TEK Tagesreport (Gesamt) | TEK alle Bereiche, DB1, Marge, Monat kumuliert + Heute | controlling |
| **tek_filiale** | TEK Filiale | TEK pro Standort – alle Bereiche eines Standorts | controlling |
| **tek_nw** | TEK Neuwagen | Nur Neuwagen-Bereich | controlling |
| **tek_gw** | TEK Gebrauchtwagen | Nur GW-Bereich | controlling |
| **tek_teile** | TEK Teile | Nur Teile-Bereich | controlling |
| **tek_werkstatt** | TEK Werkstatt | Nur Werkstatt-Bereich | controlling |
| **tek_verkauf** | TEK Verkauf (NW+GW) | Neuwagen + Gebrauchtwagen kombiniert | controlling |
| **tek_service** | TEK Service (Teile+Werkstatt) | Teile + Werkstatt kombiniert | controlling |
| **auftragseingang** | Auftragseingang | Stückzahlen nach Verkäufer (NW/GW/TV) | verkauf |
| **werkstatt_tagesbericht** | Werkstatt Tagesbericht | Leistungsgrad, Nachkalkulation, Top-Mechaniker | werkstatt |

Welche davon genau zur täglichen „Handvoll“ gehören (z. B. nur tek_daily + tek_filiale + auftragseingang), legt ihr fest; die Technik (Abos, Celery, send_daily_tek) unterstützt alle.

---

## 1. Wo was passiert

| Anliegen | Wo | Filter / Inhalt |
|----------|-----|------------------|
| **Controlling-Dashboards (TEK, BWA, …)** | **DRIVE** (Controlling-Seiten) | Zeitraum, Standort, KST, Firma, ggf. Bereich – wie bisher |
| **Tägliches E-Mail-Reporting** | **E-Mail** (PDF/HTML aus DRIVE-Logik) | Feste „Handvoll“ Reports, Abo pro Empfänger |

Metabase ist dafür **nicht** zwingend nötig: DRIVE bleibt die Quelle für Logik und Filter; die E-Mails nutzen dieselbe Datenbasis (tek_api_helper, fact_bwa, Locosoft wo nötig).

---

## 2. Die „Handvoll“ täglicher E-Mail-Reports (guter Überblick)

Empfohlene **Kern-Reports** für den täglichen Überblick:

1. **TEK Gesamt** (tek_daily)  
   – Eine E-Mail mit TEK für alle Bereiche, Monat kumuliert + Heute, VM/VJ, Stück/DB-Stück wo möglich.  
   – Ziel: Geschäftsleitung / zentrale Steuerung.

2. **TEK pro Standort** (tek_filiale)  
   – Pro Standort (DEG, LAN, ggf. pro Filiale) eine E-Mail mit allen Bereichen dieses Standorts.  
   – Ziel: Filialleiter.

3. **Optional, je nach Bedarf:**  
   - **Auftragseingang** (Stückzahlen/Verkäufer)  
   - **Werkstatt-Tagesbericht** (Leistung, Nachkalkulation)  
   - **TEK Verkauf** (NW+GW) oder **TEK Service** (Teile+Werkstatt) für entsprechende Leitungen  

Die genaue „Handvoll“ (z. B. nur 1+2 oder 1+2+Auftragseingang) legt ihr fest; die Technik (Registry, send_daily_tek, Abos) ist bereits vorhanden.

---

## 3. Konkretes Vorgehen

### A) DRIVE Controlling-Dashboards (wie bisher)

- **Filter beibehalten und ausbauen:** Zeitraum, Standort, KST, Firma, ggf. Bereich – alles in DRIVE.
- **Keine Doppelpflege:** Keine zweite „Vollversion“ der TEK in Metabase anstreben; DRIVE ist die Referenz für Logik und Darstellung.
- **Metabase:** Optional nur für einfachen Überblick oder Ad-hoc-Abfragen; kein Muss für euer definiertes Ziel.

### B) Tägliches E-Mail-Reporting

1. **Report-Set festlegen**  
   - Welche der vorhandenen Reports gehören zur „Handvoll“?  
   - Z. B.: 1× TEK Gesamt + 1× TEK pro Standort (DEG, LAN) + 1× Auftragseingang.

2. **Empfänger und Abos**  
   - In der Report-Registry / Abo-Verwaltung: Wer bekommt welchen Report (tek_daily, tek_filiale pro Standort, auftragseingang, …)?  
   - Bereits angelegt: `reports/registry.py`, Celery-Task `email_tek_daily`, Script `send_daily_tek.py`.  
   - **Admin unter `drive/admin/rechte` → E-Mail Reports:** Die Einstellungen (z. B. Standort bei „TEK Filiale“, KST/Bereich bei anderen Reports) **steuern den Versand** – sie sind **nicht hardcoded**. Beim täglichen Versand liest `send_daily_tek.py` die Abos aus der Tabelle `report_subscriptions` und gruppiert nach Standort; wer z. B. „LAN“ gewählt hat, bekommt nur den Filiale-Report für Landau.

3. **Inhalt der E-Mail-Reports**  
   - Daten wie in DRIVE: `tek_api_helper` bzw. `/api/tek`-Logik nutzen (identische Werte).  
   - PDF oder HTML: bestehende PDF-Generatoren bzw. HTML-Mails aus `send_daily_tek.py`; Inhalte wie zu Beginn des Chats (TEK mit Bereichen, Stück, DB/Stück, Kumulation, VM/VJ wo schon umgesetzt).

4. **Versand**  
   - Zeitplan beibehalten: z. B. nach Locosoft-Mirror (19:00), TEK-Versand z. B. 19:30.  
   - Weitere tägliche Mails (Auftragseingang, Werkstatt) wie bereits in Celery konfiguriert.

### C) Prioritäten

| Priorität | Aufgabe |
|-----------|--------|
| 1 | DRIVE-Controlling-Dashboards mit Filtern (Zeitraum, Standort, KST, …) wie gewohnt nutzen und bei Bedarf verfeinern. |
| 2 | „Handvoll“ täglicher E-Mail-Reports definieren (welche 2–4 Reports?) und Abos/Empfänger sauber zuordnen. |
| 3 | E-Mail-Inhalt prüfen: Reicht die aktuelle TEK-Gesamt- und Filial-Logik (inkl. Stück/DB-Stück/Kumulation) oder sollen nur kleine Anpassungen (z. B. Layout, Reihenfolge) erfolgen? |
| 4 | Metabase nur dann weiter pflegen, wenn ihr den Zusatznutzen (schneller Überblick ohne DRIVE) wollt; sonst Fokus auf DRIVE + E-Mails. |

---

## 4. Kurzfassung

- **DRIVE:** Maßgebend für Controlling-Dashboards mit allen Filterkriterien (Zeitraum, Standort, KST, usw.).
- **E-Mail:** Eine fest definierte „Handvoll“ täglicher Reports (z. B. TEK Gesamt + TEK pro Standort + ggf. Auftragseingang/Werkstatt), gleiche Datenbasis wie DRIVE, Versand wie bisher (Celery, send_daily_tek, Registry).
- **Nächste Schritte:** (1) Report-Set „Handvoll“ final festlegen, (2) Abos/Empfänger zuordnen, (3) bei Bedarf nur noch Feinschliff an Inhalt/Layout der E-Mails – keine parallele Vollversion in Metabase nötig.
