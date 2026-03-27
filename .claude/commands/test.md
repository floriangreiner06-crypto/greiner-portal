# /test - API-Endpoints testen

Direkte curl-Aufrufe -- kein SSH noetig.

## Port auto-erkennen

```bash
pwd
```

| Verzeichnis | Port |
|-------------|------|
| /opt/greiner-portal/ | 5000 (Production) |
| /opt/greiner-test/ | 5001 (Develop intern) |

## Standard Health-Checks

```bash
curl -s http://localhost:5000/api/admin/health | python3 -m json.tool
```

Fuer Develop:

```bash
curl -s http://localhost:5001/api/admin/health | python3 -m json.tool
```

## Custom Endpoint testen

Endpoint vom User erfragen oder aus dem Kontext ableiten:

```bash
curl -s http://localhost:[PORT]/[endpoint] | python3 -m json.tool
```

Beispiele:

```bash
# Werkstatt API
curl -s http://localhost:5000/api/werkstatt/live | python3 -m json.tool

# Controlling TEK
curl -s http://localhost:5000/api/controlling/tek | python3 -m json.tool

# Urlaubsplaner
curl -s http://localhost:5000/api/vacation/status | python3 -m json.tool
```

## POST-Request testen

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' \
  http://localhost:[PORT]/[endpoint] | python3 -m json.tool
```

## Mit Session-Cookie (Auth-geschuetzte Endpoints)

Hinweis: Fuer Auth-geschuetzte Endpoints wird ein Session-Cookie benoetigt.
Im Testfall entweder:
1. Oeffentliche Endpoints ohne Auth testen (/api/admin/health, statische Ressourcen)
2. Oder den User bitten den Cookie aus dem Browser zu kopieren:

```bash
curl -s -H "Cookie: session=[COOKIE]" http://localhost:5000/[endpoint] | python3 -m json.tool
```

## Response-Analyse

Nach jedem Test:
1. HTTP-Status-Code pruefen (200, 4xx, 5xx)
2. JSON-Struktur analysieren
3. Erwartete Felder vorhanden?
4. Bei Fehler: `/logs` fuer Details anbieten

## HTTP-Status mit ausgeben

```bash
curl -s -o /tmp/response.json -w "%{http_code}" http://localhost:[PORT]/[endpoint] && echo "" && python3 -m json.tool /tmp/response.json
```
