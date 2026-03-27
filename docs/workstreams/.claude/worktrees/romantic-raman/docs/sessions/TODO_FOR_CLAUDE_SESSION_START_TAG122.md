# TODO FÜR CLAUDE SESSION START - TAG 122

**Erstellt:** 2025-12-16
**Letzte Session:** TAG 121

---

## 1. Offene Aufgaben

### 1.1 Locosoft Anwesenheits-Problem (EXTERN)
- **Status:** Wartet auf Locosoft
- **Problem:** Type 1 (Anwesenheit) für Werkstatt-MA (5xxx) wird nicht exportiert
- **Aktion:** User muss Locosoft kontaktieren

### 1.2 Werkstatt Tagesbericht Email Script
- **Datei:** `scripts/reports/werkstatt_tagesbericht_email.py`
- **Status:** Lokal erstellt, noch nicht deployed
- **TODO:**
  - [ ] Script auf Server deployen
  - [ ] In Celery Task integrieren
  - [ ] Email-Versand testen

---

## 2. Abgeschlossene Aufgaben (TAG 121)

### 2.1 SB-Controlling Komplett-Überarbeitung
- Echte Serviceberater (4xxx) statt Fakturisten (1xxx)
- Werktage-Berechnung (ohne Wochenenden + Feiertage)
- Hochrechnung/Prognose für Monatsende
- Trend-Badges ("Auf Kurs", "+X%", "-X%")
- Detail-Modal Fix (JOIN + dynamische Ziele)
- Standort-Filter (Gesamt/Deggendorf/Landau)

### 2.2 TEK-Dashboard Werktage
- Breakeven-Prognose auf Werktage umgestellt
- DB-Soll bis heute basierend auf Werktage-Fortschritt

---

## 3. Wichtige Dateien dieser Session

```
api/serviceberater_api.py          # Werktage, Hochrechnung, Detail-Fix
routes/controlling_routes.py       # Werktage-Funktionen
templates/aftersales/serviceberater.html
templates/controlling/tek_dashboard.html
```

---

## 4. API-Referenz (TAG 121)

### Neue Felder in SB-Responses:
```
werktage.gesamt           - Werktage im Monat (z.B. 23 für Dez 2025)
werktage.vergangen        - Vergangene Werktage
werktage.fortschritt_prozent - Zeitlicher Fortschritt
hochrechnung.erreichung_prognose - Erwartete Erreichung Monatsende
hochrechnung.delta_vs_soll - Differenz zu erwartetem Stand
hochrechnung.auf_kurs     - Boolean
```

### Standort-Filter:
```
/api/serviceberater/uebersicht?standort=alle        # Gesamt
/api/serviceberater/uebersicht?standort=deggendorf  # Opel + Hyundai
/api/serviceberater/uebersicht?standort=landau      # Opel Landau
```

---

## 5. Bekannte Einschränkungen

### Feiertage
- Aktuell nur 2025 hardcodiert
- Für 2026 müssen neue Feiertage hinzugefügt werden (Ostern, Himmelfahrt etc.)

---

## 6. Quick-Start Befehle

```bash
# Service-Status
sudo systemctl status greiner-portal

# Neustart
sudo systemctl restart greiner-portal

# Logs
journalctl -u greiner-portal -f

# API testen
curl -s 'http://localhost:5000/api/serviceberater/uebersicht?monat=2025-12' | python3 -m json.tool | head -50
```

---

*Nächste Session: Bei Bedarf*
