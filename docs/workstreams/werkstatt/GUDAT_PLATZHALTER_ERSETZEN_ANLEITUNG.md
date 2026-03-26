# Gudat – Platzhalter in credentials.json ersetzen

Die Gudat-OAuth-Einträge sind bereits in `config/credentials.json` eingetragen – mit **Platzhaltern**. Du musst nur noch die Platzhalter durch deine echten Werte ersetzen.

**Datei:** `/opt/greiner-portal/config/credentials.json`

---

## Platzhalter und womit ersetzen

| Platzhalter | Ersetzen durch |
|-------------|----------------|
| **PLACEHOLDER_CLIENT_ID_DEGGENDORF** | Client ID für Deggendorf (aus der Gudat-Datei) |
| **PLACEHOLDER_CLIENT_SECRET_DEGGENDORF** | Client Secret für Deggendorf (aus der Gudat-Datei) |
| **PLACEHOLDER_PASSWORD_DEGGENDORF** | Passwort für admin@opel-greiner.de (von Gudat per E-Mail) |
| **PLACEHOLDER_CLIENT_ID_LANDAU** | Client ID für Landau (aus der Gudat-Datei) |
| **PLACEHOLDER_CLIENT_SECRET_LANDAU** | Client Secret für Landau (aus der Gudat-Datei) |
| **PLACEHOLDER_PASSWORD_LANDAU** | Passwort für admin@auto-greiner.de (von Gudat per E-Mail) |

---

## Schritt für Schritt (PuTTY / nano)

### 1. Datei öffnen

```bash
nano /opt/greiner-portal/config/credentials.json
```

### 2. Platzhalter suchen und ersetzen

In **nano** kannst du jeden Platzhalter nacheinander ersetzen:

- **Strg+W** (Suchen)
- Platzhalter eintippen, z. B. **PLACEHOLDER_CLIENT_ID_DEGGENDORF** → Enter
- Cursor steht auf dem Platzhalter. **Strg+K** schneidet die ganze Zeile aus (oder markiere den Text und lösche ihn).
- Echten Wert eintippen (z. B. die Client ID), **ohne** die Anführungszeichen zu löschen – also nur den Text zwischen den `"` ersetzen.

**Reihenfolge (empfohlen):**

1. **Strg+W** → `PLACEHOLDER_CLIENT_ID_DEGGENDORF` → Enter → ersetzen
2. **Strg+W** → `PLACEHOLDER_CLIENT_SECRET_DEGGENDORF` → Enter → ersetzen
3. **Strg+W** → `PLACEHOLDER_PASSWORD_DEGGENDORF` → Enter → ersetzen
4. **Strg+W** → `PLACEHOLDER_CLIENT_ID_LANDAU` → Enter → ersetzen
5. **Strg+W** → `PLACEHOLDER_CLIENT_SECRET_LANDAU` → Enter → ersetzen
6. **Strg+W** → `PLACEHOLDER_PASSWORD_LANDAU` → Enter → ersetzen

**Wichtig:** Nur den Platzhalter-Text ersetzen, die umgebenden Anführungszeichen `"` bleiben stehen. Beispiel:

- Vorher: `"client_id": "PLACEHOLDER_CLIENT_ID_DEGGENDORF"`
- Nachher: `"client_id": "038b08a4-xxxxx"` (deine echte Client ID)

### 3. Speichern und beenden

- **Strg+O** → Enter (speichern)
- **Strg+X** (nano beenden)

### 4. Prüfen (optional)

```bash
python3 -c "import json; json.load(open('/opt/greiner-portal/config/credentials.json')); print('OK – JSON gültig')"
```

Wenn **OK – JSON gültig** erscheint, ist alles in Ordnung.

---

## Kurz-Checkliste

- [ ] `nano /opt/greiner-portal/config/credentials.json`
- [ ] 6 Platzhalter per Strg+W suchen und durch echte Werte ersetzen (Anführungszeichen bleiben)
- [ ] Strg+O, Enter, Strg+X
- [ ] Optional: JSON-Prüfung mit dem python3-Befehl oben

**Hinweis:** Die Datei steht in der `.gitignore` und wird nicht ins Git eingecheckt. Nach dem Ersetzen ist die Gudat-OAuth-Konfiguration fertig; der Code für die API-Nutzung kommt später.
