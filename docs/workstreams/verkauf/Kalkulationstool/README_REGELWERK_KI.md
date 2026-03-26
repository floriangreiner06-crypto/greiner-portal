# Verkaufsprogramm-PDFs → KI-Regelwerk

**Stand:** 2026-03-02

## Ablauf einmal pro Quartal (empfohlen)

1. **Neue Rundschreiben-PDFs** in den Ordner legen (z. B. `Kalkulationstool` im Sync).
2. **Ein PDF pro Lauf** verarbeiten (Chunk 6000, Timeout 300 s, bei 400/Timeout Retry mit halbiertem Chunk):

   ```bash
   cd /opt/greiner-portal
   KALK="/mnt/greiner-portal-sync/docs/workstreams/verkauf/Kalkulationstool"
   OUT="docs/workstreams/verkauf/Kalkulationstool"

   # Hyundai
   .venv/bin/python scripts/verkauf/vfw_rundschreiben_regelwerk_ki.py --dir "$KALK" \
     --pdf "$KALK/RS-V-2025-125_Aktualisierung Vertriebsprogramm Hyundai Q1.pdf" \
     --chunk-size 6000 --timeout 300 -o "$OUT/Regelwerk_Hyundai.json"

   # Stellantis/Opel
   .venv/bin/python scripts/verkauf/vfw_rundschreiben_regelwerk_ki.py --dir "$KALK" \
     --pdf "$KALK/vp-13_2025_verkaufsprogramme_q1_2026_update5.pdf" \
     --chunk-size 6000 --timeout 300 -o "$OUT/Regelwerk_Stellantis.json"
   ```

3. **Merge** (Hyundai + Stellantis → ein Regelwerk + lesbare .md):

   ```bash
   .venv/bin/python scripts/verkauf/merge_regelwerk.py --dir docs/workstreams/verkauf/Kalkulationstool
   ```

4. **Ergebnis:** `Regelwerk_Vollstaendig.json`, `Regelwerk_Vollstaendig_lesbar.md` (und ggf. Sync-Ordner aktualisieren).

## Erzeugte Dateien

| Datei | Inhalt |
|-------|--------|
| **Regelwerk_Hyundai.json** | Ein Programm (Hyundai) mit Konditionen/Boni aus der Hyundai-PDF |
| **Regelwerk_Stellantis.json** | Ein oder mehrere Programme (Opel/Stellantis) aus der Stellantis-PDF |
| **Regelwerk_Vollstaendig.json** | Merge beider; `programme`: Liste aller Hersteller-Programme |
| **Regelwerk_Vollstaendig_lesbar.md** | Lesbare Tabellen pro Hersteller (Aktionstyp, Modell, Bonus, Typ, Wert) |

## Skript-Optionen

**vfw_rundschreiben_regelwerk_ki.py**

- `--dir` – Ordner mit PDFs (oder für Ausgabe bei `-o` relativ zum Repo)
- `--pdf` – Eine oder mehrere PDF-Dateien (empfohlen: **ein** PDF pro Aufruf)
- `--chunk-size 6000` – Blöcke 6000 Zeichen (LM Studio verträgt ~6–8k)
- `--timeout 300` – Sekunden pro Request
- `-o` – Ausgabe-JSON (z. B. `Regelwerk_Hyundai.json`)

Bei abgeschnittener KI-Antwort oder 400: automatischer **Retry mit halbiertem Chunk** (bis min. 2000 Zeichen).

**merge_regelwerk.py**

- `--dir` – Ordner mit `Regelwerk_Hyundai.json` und `Regelwerk_Stellantis.json`
- `-o` – Ausgabeordner (Standard: wie `--dir`)

## Voraussetzung

- LM Studio erreichbar (`config/credentials.json` → `lm_studio`, z. B. 46.229.10.1:4433).
- Verarbeitungsdauer pro PDF typisch 10–15 Minuten (einmal pro Quartal unkritisch).

## Nächste Schritte

- Regelwerk-JSON in die DB überführen (Tabellen `vfw_verkaufsprogramme`, `vfw_programm_konditionen`) – mit Prüfung/Freigabe durch Verkaufsleitung.
- Im Kalkulationstool: gültige Programme anzeigen und pro Fahrzeug die passenden Konditionen aus dem Regelwerk laden.
