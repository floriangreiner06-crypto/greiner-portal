# TODO FOR CLAUDE - SESSION START TAG142

**Erstellt:** 2025-12-29

---

## Erledigte Aufgaben (TAG141)

- [x] Renner & Penner API implementiert (`/api/lager/...`)
- [x] Dashboard unter `/werkstatt/renner-penner` live
- [x] Garantie/Gewährleistung korrekt ausgeschlossen
- [x] CSV-Export für Matthias verfügbar
- [x] Marktcheck-Links zu 5 Plattformen
- [x] SOAP-API vollständig analysiert

---

## Aktuelle Aufgaben (TAG142)

### 1. Automatischer Preisvergleich implementieren
- eBay Scraping/API für Marktpreise
- Daparto als zweite Quelle
- Cache-Tabelle in PostgreSQL
- Ampel-System: Grün/Gelb/Rot

### 2. Verkaufschancen-Dashboard
- Erweiterung von Renner & Penner
- Top-Verkaufschancen mit Marktpreisen
- Empfehlungen pro Teil

### 3. Celery Nacht-Job
- Automatisches Preis-Update um 3:00 Uhr
- Nur Penner/Leichen mit Lagerwert >50€

### 4. Wöchentlicher E-Mail Report
- Top 20 Verkaufschancen an Matthias
- Montags um 7:00 Uhr

---

## Mockup

Siehe: `docs/MOCKUP_PENNER_PREISVERGLEICH.md`

---

## Technischer Plan

```
1. DB-Schema: penner_marktpreise Tabelle
2. Service: services/preisvergleich_service.py
3. API: Erweiterung von renner_penner_api.py
4. Celery: Task für Nacht-Update
5. Template: Verkaufschancen-Tab im Dashboard
6. E-Mail: Celery Beat für wöchentlichen Report
```

---

## Zeitschätzung

| Phase | Aufwand |
|-------|---------|
| DB-Schema | 30 min |
| eBay Scraper | 2h |
| API-Endpoints | 1h |
| Dashboard-Erweiterung | 2h |
| Celery Task | 1h |
| E-Mail Report | 1h |
| **Gesamt** | **~7h** |

---

*Erstellt von Claude - TAG 141 Ende*
