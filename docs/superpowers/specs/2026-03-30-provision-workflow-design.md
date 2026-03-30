# Provision Workflow — Spec

## Ziel

Mehrstufiger Freigabe-Workflow fuer Provisionsabrechnungen mit Einspruch-/Ablehnungsmoeglichkeit und Pflicht-Begruendung. E-Mail-Benachrichtigungen werden vorbereitet aber in der Testversion deaktiviert.

## Statusuebergaenge

```
VORLAUF ──"Zur Pruefung"──> ZUR_PRUEFUNG ──"Freigeben"──> FREIGEGEBEN ──"Genehmigen"──> GENEHMIGT ──"Endlauf"──> ENDLAUF
  (Vanessa)                  (Verkaeufer)                  (Anton/Florian G.)            (Vanessa)
     ^                           |                              |
     └───"Einspruch"─────────────┘                              |
     |    (Pflicht-Text)                                        |
     └───"Ablehnung"────────────────────────────────────────────┘
          (Pflicht-Text)
```

### Uebergaenge im Detail

| Von | Nach | Aktion | Wer | Bedingung |
|-----|------|--------|-----|-----------|
| VORLAUF | ZUR_PRUEFUNG | "Zur Pruefung senden" | Vollzugriff-User (Vanessa/Florian G./Peter G.) | — |
| ZUR_PRUEFUNG | FREIGEGEBEN | "Freigeben" | Der jeweilige Verkaeufer (eigener Lauf) ODER Vollzugriff-User (fuer Test) | — |
| ZUR_PRUEFUNG | VORLAUF | "Einspruch" | Der jeweilige Verkaeufer ODER Vollzugriff-User | Pflicht-Textfeld (min. 1 Zeichen) |
| FREIGEGEBEN | GENEHMIGT | "Genehmigen" | Anton Suess ODER Florian Greiner (nur einer muss) | — |
| FREIGEGEBEN | VORLAUF | "Ablehnen" | Anton Suess ODER Florian Greiner | Pflicht-Textfeld (min. 1 Zeichen) |
| GENEHMIGT | ENDLAUF | "Endlauf erstellen" | Vollzugriff-User | Optional: Korrekturwerte |

### Rueckfluss-Regeln

- **Einspruch** (Verkaeufer): Status zurueck auf VORLAUF. Text, Zeitstempel, Username werden gespeichert.
- **Ablehnung** (Anton/Florian): Status zurueck auf VORLAUF. Text, Zeitstempel, Username werden gespeichert.
- In beiden Faellen: Textfeld ist **Pflichtfeld** — ohne Begruendung kein Zuruecksenden.
- Bei erneutem "Zur Pruefung senden" bleibt der letzte Einspruch/Ablehnung als Historie sichtbar.

## Akteure und Berechtigungen

### Vollzugriff (Dashboard + alle Laeufe + Bearbeiten)

Nur diese 3 Usernames (bestehende `_PROVISION_VOLLZUGRIFF_USERS` in provision_api.py):
- `florian.greiner@auto-greiner.de`
- `peter.greiner@auto-greiner.de`
- `vanessa.groll@auto-greiner.de`

### Genehmiger

Nur diese 2 Personen (einer reicht):
- Anton Suess (`anton.suess@auto-greiner.de`)
- Florian Greiner (`florian.greiner@auto-greiner.de`)

### Verkaeufer (eigene Provision)

Jeder Verkaeufer mit Feature `provision` sieht nur seinen eigenen Lauf und kann:
- Vorlauf pruefen (wenn Status = ZUR_PRUEFUNG und eigener Lauf)
- Freigeben oder Einspruch einlegen
- PDF downloaden (wenn Status = ENDLAUF)

### Vanessa als Testverkaeuferin

Vollzugriff-User koennen auch die Verkaeufer-Aktionen (Freigeben/Einspruch) ausfuehren, damit Vanessa den kompletten Workflow testen kann, ohne einen echten Verkaeufer einzubinden.

## DB-Aenderungen

### Bestehende Felder in `provision_laeufe` (werden jetzt genutzt)

- `pruefung_am TIMESTAMP` — Zeitstempel "Zur Pruefung gesendet"
- `pruefung_von TEXT` — Wer hat zur Pruefung gesendet
- `freigegeben_am TIMESTAMP` — Zeitstempel "Verkaeufer hat freigegeben"
- `freigegeben_von TEXT` — Welcher Verkaeufer
- `genehmigt_am TIMESTAMP` — Zeitstempel "Genehmigt"
- `genehmigt_von TEXT` — Wer hat genehmigt (Anton oder Florian)

### Neue Felder in `provision_laeufe`

```sql
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_text TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_von TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_am TIMESTAMP;
```

Diese Felder speichern den letzten Einspruch/Ablehnung (wird bei jedem Rueckfluss ueberschrieben).

## API-Endpoints (neu)

### POST /api/provision/vorlauf/{id}/zur-pruefung

Setzt Status VORLAUF -> ZUR_PRUEFUNG. Nur Vollzugriff-User.
- Setzt `pruefung_am = NOW()`, `pruefung_von = username`
- Loescht vorherigen Einspruch-Text (einspruch_text/von/am = NULL)

### POST /api/provision/vorlauf/{id}/freigeben

Setzt Status ZUR_PRUEFUNG -> FREIGEGEBEN. Eigener Verkaeufer ODER Vollzugriff-User.
- Setzt `freigegeben_am = NOW()`, `freigegeben_von = username`

### POST /api/provision/vorlauf/{id}/einspruch

Setzt Status ZUR_PRUEFUNG -> VORLAUF. Eigener Verkaeufer ODER Vollzugriff-User.
- Body: `{ "text": "Provision fuer Fahrzeug XY fehlt" }` — Pflichtfeld, min 1 Zeichen
- Setzt `einspruch_text`, `einspruch_von`, `einspruch_am`
- Setzt Status zurueck auf VORLAUF

### POST /api/provision/vorlauf/{id}/genehmigen

Setzt Status FREIGEGEBEN -> GENEHMIGT. Nur Genehmiger (Anton/Florian).
- Setzt `genehmigt_am = NOW()`, `genehmigt_von = username`

### POST /api/provision/vorlauf/{id}/ablehnen

Setzt Status FREIGEGEBEN -> VORLAUF. Nur Genehmiger (Anton/Florian).
- Body: `{ "text": "Summe Kat III stimmt nicht" }` — Pflichtfeld, min 1 Zeichen
- Setzt `einspruch_text`, `einspruch_von`, `einspruch_am`
- Setzt Status zurueck auf VORLAUF

### Bestehender Endpoint anpassen

`POST /api/provision/vorlauf/{id}/endlauf` — Bedingung aendern: Status muss GENEHMIGT sein (statt FREIGEGEBEN).

## Frontend-Aenderungen

### Detail-Seite (provision_detail.html)

**Status-abhaengige Buttons:**

| Status | Vollzugriff-User sieht | Verkaeufer sieht |
|--------|----------------------|-----------------|
| VORLAUF | "Zur Pruefung senden" + Bearbeiten | (kein Zugriff auf fremde) |
| ZUR_PRUEFUNG | "Freigeben" + "Einspruch" (Test) | "Freigeben" + "Einspruch" (eigener Lauf) |
| FREIGEGEBEN | Warten-Hinweis | — |
| GENEHMIGT | "Endlauf erstellen" | — |
| ENDLAUF | PDF-Download | PDF-Download (eigener Lauf) |

**Einspruch/Ablehnung-Info:**
- Wenn `einspruch_text` vorhanden und Status = VORLAUF: gelbes Warnfeld mit Einspruch-Text, Von, Datum anzeigen

**Einspruch/Ablehnung-Modal:**
- Textarea (Pflichtfeld) + "Einspruch senden" / "Ablehnen" Button
- Button bleibt deaktiviert bis Text eingegeben

### Dashboard (provision_dashboard.html)

- Status-Badge erweitern um ZUR_PRUEFUNG (orange) und GENEHMIGT (blau-gruen)
- Farben: VORLAUF=grau, ZUR_PRUEFUNG=orange, FREIGEGEBEN=blau, GENEHMIGT=tuerkis, ENDLAUF=gruen

### "Meine Provision"-Seite (provision_meine.html)

- Wenn ein Lauf mit Status ZUR_PRUEFUNG fuer den eigenen VKB existiert: Hinweis-Banner anzeigen mit Link zur Detail-Seite
- Verkaeufer muss Detail-Seite oeffnen koennen (auch wenn nicht Vollzugriff) — Route `/detail/{id}` erlauben wenn eigener Lauf

## E-Mail-Benachrichtigungen (vorbereitet, deaktiviert)

Flag in provision_api.py:
```python
PROVISION_EMAIL_ENABLED = False  # Testversion: keine E-Mails
```

Funktionen werden angelegt aber nur ausgefuehrt wenn Flag = True:

| Schritt | Empfaenger | Betreff |
|---------|-----------|---------|
| Zur Pruefung | Verkaeufer | "Provisionsvorlauf {Monat} liegt zur Pruefung bereit" |
| Freigegeben | Anton + Florian G. | "Vorlauf von {Name} wartet auf Genehmigung" |
| Einspruch | Vanessa | "Einspruch von {Verkaeufer}: {Text}" |
| Ablehnung | Vanessa | "Ablehnung von {Genehmiger}: {Text}" |
| Genehmigt | Vanessa | "Vorlauf {Name} genehmigt" |
| Endlauf | Verkaeufer | "Provisionsabrechnung {Monat} fertig — PDF verfuegbar" |

## Nicht im Scope

- Einspruch auf Positions-Ebene (einzelne Zeilen beanstanden)
- Mehrere Einspruch-Runden als Historie (nur letzter wird gespeichert)
- Automatische E-Mails (erst nach Testphase aktivieren)
- Batch-Workflow (alle Verkaeufer gleichzeitig zur Pruefung senden)
