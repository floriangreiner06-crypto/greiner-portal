# Stundensatz-Kalkulation Template
## TAG 169: Template für genauere Werkstatt-Planung

### Ziel
Erstellung eines Templates zur präzisen Stundensatz-Kalkulation basierend auf BWA-Daten.

### Excel-Vorlage
**Datei:** `docs/2021-10-11_Stundenverrechnungssatz berechnen(1).xls`

### Benötigte BWA-Daten für Werkstatt

#### 1. Umsatz (Geschäftsjahr)
- **Konten:** 840000-849999
- **Berechnung:** HABEN - SOLL
- **SQL:**
```sql
SELECT COALESCE(SUM(
    CASE WHEN debit_or_credit='H' THEN posted_value ELSE -posted_value END
)/100.0, 0) as umsatz
FROM loco_journal_accountings
WHERE accounting_date >= '2024-09-01' AND accounting_date < '2025-09-01'
  AND nominal_account_number BETWEEN 840000 AND 849999
  AND subsidiary = 1  -- Standort-Filter
```

#### 2. Einsatz (Geschäftsjahr)
- **Konten:** 740000-749999
- **Berechnung:** SOLL - HABEN
- **SQL:**
```sql
SELECT COALESCE(SUM(
    CASE WHEN debit_or_credit='S' THEN posted_value ELSE -posted_value END
)/100.0, 0) as einsatz
FROM loco_journal_accountings
WHERE accounting_date >= '2024-09-01' AND accounting_date < '2025-09-01'
  AND nominal_account_number BETWEEN 740000 AND 749999
  AND subsidiary = 1
```

#### 3. DB1 (Bruttoertrag)
- **Formel:** Umsatz - Einsatz

#### 4. Variable Kosten (Geschäftsjahr)
- **Konten:** 415xxx, 435xxx, 455xxx-456xxx, 487xxx, 491xxx-497xxx
- **KST:** 3 (5. Ziffer = 3 = Werkstatt)
- **Berechnung:** SOLL - HABEN

#### 5. Direkte Kosten (Geschäftsjahr)
- **Konten:** 400000-499999 mit KST 3 (ohne Variable Kosten)
- **Berechnung:** SOLL - HABEN

#### 6. DB2
- **Formel:** DB1 - Variable Kosten - Direkte Kosten

#### 7. Stunden verkauft (Geschäftsjahr)
- **Quelle:** `labours.time_units` (AW) aus Locosoft
- **Umrechnung:** AW / 6 = Stunden
- **SQL:**
```sql
SELECT COALESCE(SUM(l.time_units), 0) / 6.0 as stunden_verkauft
FROM labours l
JOIN invoices i ON l.invoice_number = i.invoice_number 
    AND l.invoice_type = i.invoice_type
JOIN orders o ON l.order_number = o.number
WHERE i.invoice_date >= '2024-09-01' AND i.invoice_date < '2025-09-01'
  AND l.is_invoiced = true
  AND i.is_canceled = false
  AND o.subsidiary = 1
```

#### 8. Stundensatz
- **Formel:** Umsatz / Stunden verkauft

#### 9. Kosten pro Stunde
- **Formel:** (Variable Kosten + Direkte Kosten) / Stunden verkauft

### Standort-Mapping

| Standort | Name | Subsidiary Filter |
|----------|------|-------------------|
| 1 | Deggendorf | `subsidiary = 1 OR subsidiary = 2` |
| 2 | Hyundai DEG | `subsidiary = 2` |
| 3 | Landau | `subsidiary = 1` |

### Nächste Schritte

1. **Excel-Struktur analysieren:**
   - Welche Felder sind in der Excel?
   - Welche Formeln werden verwendet?
   - Welche Daten müssen befüllt werden?

2. **Mapping erstellen:**
   - Excel-Feld → BWA-Datenquelle
   - Excel-Formel → Berechnungslogik

3. **Template erstellen:**
   - Python-Script, das Excel mit BWA-Daten befüllt
   - Oder: Web-Interface im Planungstool

4. **Integration:**
   - Template in Planungstool integrieren
   - Automatische Berechnung beim Planen

### Script zum Befüllen

**Datei:** `scripts/stundensatz_kalkulation_template.py`

**Verwendung:**
```bash
# Auf Server ausführen (mit psycopg2):
cd /opt/greiner-portal
python scripts/stundensatz_kalkulation_template.py
```

**Ausgabe:**
- Analysiert Excel-Struktur
- Lädt BWA-Daten für alle 3 Standorte
- Erstellt befülltes Template

### Integration ins Planungstool

**Option 1: Excel-Export**
- Button "Stundensatz-Kalkulation exportieren"
- Generiert Excel mit aktuellen BWA-Daten

**Option 2: Web-Interface**
- Neue Seite im Planungstool
- Zeigt Stundensatz-Kalkulation interaktiv
- Basierend auf Excel-Struktur

**Option 3: Automatische Berechnung**
- Stundensatz wird automatisch aus BWA berechnet
- Anzeige im Planungstool mit Erklärung

