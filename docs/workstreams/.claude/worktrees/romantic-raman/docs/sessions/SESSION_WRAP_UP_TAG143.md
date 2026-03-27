# SESSION WRAP-UP TAG 143

**Datum:** 2025-12-29
**Fokus:** Budget-Planung mit DB1-Fokus (Profit statt Stueckzahlen)

---

## Was wurde erledigt

### 1. Jahresabschluss-Analyse (GJ 09/24 - 08/25)

Analysiert wurden die GuV-Kontennachweise beider Gesellschaften:

| Gesellschaft | Umsatz | Gewinn | NW-Marge | GW-Marge |
|--------------|--------|--------|----------|----------|
| Auto Greiner (Hyundai) | 10.87 M | +163k (-52% VJ) | 7.1% | **10.1%** (Benchmark) |
| Autohaus Greiner (Opel) | 18.64 M | +193k (+478% VJ) | 4.9% | **0.7%** (KRITISCH!) |

**Kritische Erkenntnis:** Opel GW-Marge nur 0.7% = 46k DB1 auf 6.5M Umsatz!

### 2. Budget-API mit DB1-Fokus erweitert

**Neue Endpunkte:**
- `GET /api/budget/margen-analyse` - Margen pro Standort/Marke mit Ampelsystem
- `GET /api/budget/vkl-provision` - VKL-Provisionsrechner nach DB1-Staffel
- `GET /api/budget/jahresabschluss-referenz` - Referenzwerte aus Bilanz

**Neue Konfiguration:**
```python
ZIEL_MARGEN = {
    'opel': {'nw': 6.0%, 'gw': 6.0%},    # Von 0.7% auf 6%!
    'hyundai': {'nw': 7.5%, 'gw': 10.0%} # Benchmark halten
}

VKL_PROVISION_STAFFEL = [
    5.0% Basis,
    7.5% ab 50k DB1,
    10.0% ab 100k DB1,
    12.5% ab 150k DB1
]
```

### 3. Template mit Profit-Fokus ueberarbeitet

- DB1 und Marge als Haupt-KPIs (statt nur Stueckzahlen)
- Margen-Warnung (pulsierend bei kritischen Werten)
- Jahresabschluss-Info-Banner mit Erkenntnissen
- VKL-Provisions-Card mit Staffel-Anzeige
- Verkaeufer-Leaderboard nach DB1 sortiert mit Marge-Badge

---

## Geaenderte Dateien

### Neu/Stark modifiziert:
- `api/budget_api.py` - Erweitert mit DB1-Fokus, Margen-Analyse, VKL-Provision
- `templates/verkauf_budget.html` - Komplett ueberarbeitet mit Profit-Fokus

### Navigation:
- `templates/base.html` - Budget-Planung unter Verkauf (GF + VKL only)

---

## Bekannte Issues / TODO

1. **Template "shitty" laut User** - Muss noch ueberarbeitet werden (naechste Session)
2. **Leasingauslaeufer** - User erwaehnt als naechstes Thema
3. **Plan speichern** - savePlan() nur als Stub implementiert
4. **Monatsziele editieren** - updatePlan() nur als Stub

---

## Vorbereitet fuer TAG 144

- Leasingauslaeufer-Integration (VFW aus Leasing-Ruecklauf)
- Template-Ueberarbeitung nach User-Feedback
- Plan-Speicherung vollstaendig implementieren

---

## Server-Sync Status

Dateien muessen noch auf Server gesynct werden:
```bash
rsync -av --exclude '.git' /mnt/greiner-portal-sync/api/budget_api.py /opt/greiner-portal/api/
rsync -av --exclude '.git' /mnt/greiner-portal-sync/templates/verkauf_budget.html /opt/greiner-portal/templates/
sudo systemctl restart greiner-portal
```
