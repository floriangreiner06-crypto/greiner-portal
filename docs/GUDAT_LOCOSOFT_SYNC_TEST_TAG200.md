# Gudat → Locosoft Sync Test (TAG 200)

**Erstellt:** 2026-01-20  
**Zweck:** Test-Integration: Termine von Gudat nach Locosoft Werkstattplaner übertragen

---

## ✅ IMPLEMENTIERT

### 1. API erweitert: Team-Daten pro Tag

**Endpoint:** `GET /api/gudat/workload/week?with_teams=true&start_date=2026-01-20`

Liefert jetzt `teams_per_day` mit Team-Daten pro Tag für alle Teams.

**Beispiel:**
```json
{
  "days": [...],
  "teams_per_day": {
    "2026-01-20": [
      {"id": 2, "name": "Allgemeine Reparatur", "free": 71, ...},
      {"id": 3, "name": "Diagnosetechnik", "free": -66, ...}
    ]
  }
}
```

### 2. SOAP-Integration: Test-Endpoint

**Endpoint:** `POST /api/gudat-locosoft/test-sync-termin`

**Body (JSON):**
```json
{
  "auftrag_nr": 40167,
  "date": "2026-01-20",
  "time": "10:30"
}
```

**Funktionalität:**
1. Liest Auftragsdaten aus Locosoft (Kunde, Fahrzeug)
2. Erstellt Termin im Werkstattplaner per SOAP (`writeAppointment`)
3. Setzt `estimated_inbound_time` im Auftrag (direkt in DB)

**Weitere Endpoints:**
- `GET /api/gudat-locosoft/list-termine-heute` - Liste aller Termine für heute

---

## 🧪 TESTEN

### Option 1: Via Browser (mit Login)
1. Im Browser einloggen
2. Browser-Console öffnen
3. Ausführen:
```javascript
fetch('/api/gudat-locosoft/test-sync-termin', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    auftrag_nr: 40167,
    date: '2026-01-20',
    time: '10:30'
  })
}).then(r => r.json()).then(console.log)
```

### Option 2: Via Python (mit Session)
```python
import requests

session = requests.Session()
# Login durchführen (Cookie setzen)
# Dann:
response = session.post(
    'http://localhost:5000/api/gudat-locosoft/test-sync-termin',
    json={'auftrag_nr': 40167, 'date': '2026-01-20', 'time': '10:30'}
)
print(response.json())
```

---

## 📊 ERGEBNISSE

Nach erfolgreichem Test sollte:
1. ✅ Ein neuer Termin im Locosoft Werkstattplaner erstellt sein
2. ✅ Der Termin mit Kunde und Fahrzeug verknüpft sein (falls Auftragsnummer vorhanden)
3. ✅ `estimated_inbound_time` im Auftrag gesetzt sein

---

## ⚠️ HINWEISE

- Endpoint benötigt Login (`@login_required`)
- SOAP-Verbindung zu 10.80.80.7:8086 muss funktionieren
- Termine werden im Werkstattplaner erstellt (nicht nur im Auftrag)
- `estimated_inbound_time` wird direkt in der DB gesetzt (nicht per SOAP)

---

## 🔄 NÄCHSTE SCHRITTE

1. Test-Termin erstellen und prüfen
2. Validierung: Termin im Werkstattplaner sichtbar?
3. Erweiterung: Gudat Task-Details holen und übertragen
4. Automatisierung: Batch-Sync für mehrere Termine
