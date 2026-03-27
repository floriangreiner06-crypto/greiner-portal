# /test - API-Endpoints testen

Teste API-Endpoints des Greiner Portals.

## Anweisungen

Frage den User welchen Endpoint er testen möchte, oder führe Standard-Health-Checks aus.

### Standard Health-Checks:
```bash
# Main Health
ssh ag-admin@10.80.80.20 "curl -s http://localhost:5000/api/admin/health"

# Werkstatt API
ssh ag-admin@10.80.80.20 "curl -s http://localhost:5000/api/werkstatt/health"

# Controlling API
ssh ag-admin@10.80.80.20 "curl -s http://localhost:5000/api/controlling/health"
```

### Custom Endpoint testen:
```bash
ssh ag-admin@10.80.80.20 "curl -s http://localhost:5000/[endpoint]"
```

### Mit POST-Daten:
```bash
ssh ag-admin@10.80.80.20 "curl -s -X POST -H 'Content-Type: application/json' -d '[JSON]' http://localhost:5000/[endpoint]"
```

## Output
Formatiere JSON-Output lesbar mit `python3 -m json.tool`
