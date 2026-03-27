# TODO FOR CLAUDE - SESSION START TAG 144

**Erstellt:** 2025-12-29
**Vorherige Session:** TAG 143 (Budget-Planung mit DB1-Fokus)

---

## Prioritaet 1: Template ueberarbeiten

User-Feedback: "shitty ueberarbeiten"

Das Budget-Template muss verbessert werden:
- UI/UX optimieren
- Klarer, aufgeraeumter
- Weniger "busy", mehr Fokus

**Datei:** `templates/verkauf_budget.html`

---

## Prioritaet 2: Leasingauslaeufer

User erwaehnte "Stichwort Leasingauslaeufer" - mehr Kontext kommt.

Vermutlich:
- VFW (Vorfuehrwagen) die aus Leasing zurueckkommen
- Planbare GW-Zugaenge aus Leasing-Ruecklauf
- Integration in Budget-Planung fuer GW

**Warten auf User-Input mit Details.**

---

## Offene Punkte aus TAG 143

1. **savePlan()** - Nur Stub, muss vollstaendig implementiert werden
2. **updatePlan()** - Monatsziele editieren funktioniert nicht
3. **DB1-Trend** - Vergleich mit Vorjahr fehlt noch

---

## Kontext: Jahresabschluss-Erkenntnisse

Wichtig fuer Planung 2026:

| Bereich | IST GJ24 | ZIEL GJ26 | Aktion |
|---------|----------|-----------|--------|
| Opel GW-Marge | 0.7% | 6.0% | KRITISCH - drastisch steigern! |
| Opel NW-Marge | 4.9% | 6.0% | Verbessern |
| Hyundai GW-Marge | 10.1% | 10.0% | Benchmark halten |
| Hyundai NW-Marge | 7.1% | 7.5% | Leicht optimieren |

---

## Dateien zum Lesen bei Session-Start

1. `CLAUDE.md` - Projekt-Kontext
2. `api/budget_api.py` - Aktuelle Budget-API
3. `templates/verkauf_budget.html` - Aktuelles Template (ueberarbeiten!)

---

## Server-Sync

Falls noch nicht gesynct:
```bash
rsync -av --exclude '.git' /mnt/greiner-portal-sync/api/budget_api.py /opt/greiner-portal/api/
rsync -av --exclude '.git' /mnt/greiner-portal-sync/templates/ /opt/greiner-portal/templates/
sudo systemctl restart greiner-portal
```
