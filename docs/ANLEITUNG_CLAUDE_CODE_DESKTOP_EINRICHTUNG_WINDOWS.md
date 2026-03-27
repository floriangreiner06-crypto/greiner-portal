# Anleitung: Claude Code Desktop einrichten (Windows) fuer DRIVE-Testsystem

Stand: 2026-03-20  
Ziel: Claude Code Desktop so einrichten, dass Vanessa sicher im Testsystem arbeitet.

---

## 1) Voraussetzungen

- Windows-PC mit Internetzugang
- Zugangsdaten fuer Server `10.80.80.20`
- SSH-User fuer Test, z. B. `vanessa-dev`
- SSH-Key (empfohlen) vorhanden
- Testumgebung ist erreichbar unter `http://drive/test`

---

## 2) SSH auf Windows vorbereiten

### 2.1 Pruefen, ob OpenSSH Client da ist

PowerShell:

```powershell
ssh -V
```

Wenn kein SSH vorhanden ist:  
Windows-Feature "OpenSSH Client" installieren.

### 2.2 SSH-Key erzeugen (falls noch nicht vorhanden)

```powershell
ssh-keygen -t ed25519 -C "vanessa-dev@greiner-test"
```

Standardpfade:
- Private Key: `C:\Users\<User>\.ssh\id_ed25519`
- Public Key: `C:\Users\<User>\.ssh\id_ed25519.pub`

### 2.3 Verbindung testen

```powershell
ssh vanessa-dev@10.80.80.20
```

Optional mit explizitem Key:

```powershell
ssh -i C:\Users\<User>\.ssh\id_ed25519 vanessa-dev@10.80.80.20
```

---

## 3) Claude Code Desktop installieren

1. Claude Code Desktop installieren (offizieller Installer).
2. App starten.
3. Mit Firmen-Account anmelden.
4. Falls abgefragt: Zugriff auf lokale Dateien/Terminal erlauben.

Hinweis: Der genaue Menuname kann je nach Version leicht anders sein.

---

## 4) Remote/SSH-Projekt einrichten

In Claude Code Desktop:

1. Neues Projekt bzw. Workspace erstellen.
2. Verbindungstyp **SSH/Remote** waehlen.
3. Eintragen:
   - Host: `10.80.80.20`
   - User: `vanessa-dev`
   - Auth: SSH-Key (`id_ed25519`)
4. Als Arbeitsverzeichnis setzen:
   - `/data/greiner-test`
5. Verbindung speichern.

Wenn moeglich, in den Projekteinstellungen als "Default Working Directory" fest hinterlegen.

---

## 5) Sicherheits-Instruktion im Projekt hinterlegen (sehr wichtig)

Als feste Projekt-Instruktion eintragen:

1. Arbeite ausschliesslich im Testsystem.
2. Nutze fuer Browser-Tests nur `http://drive/test`.
3. Keine Aenderungen in `/opt/greiner-portal`.
4. Keine produktiven Restarts oder Migrationen.
5. Fokus auf `templates/`, `static/css/`, `static/js/`.
6. Vor groesseren Edits kurz den Plan anzeigen.

---

## 6) Erster Funktionstest

Nach erfolgreicher Verbindung in Claude Code Desktop:

1. Aktuelles Verzeichnis pruefen (`/data/greiner-test`).
2. Kleine Testaenderung in einer Testdatei vornehmen.
3. Browser oeffnen: `http://drive/test`
4. Sicherstellen:
   - TESTSYSTEM-Badge sichtbar
   - Aenderung erscheint nur in Test

---

## 7) Empfohlener Arbeitsablauf fuer Vanessa

1. Aufgabe als klaren Prompt formulieren (UI-Ziel + Akzeptanzkriterien).
2. Kleine Schritte: erst 1 Bereich, dann naechster.
3. Nach jedem Schritt: visuell im Browser pruefen.
4. Ergebnisse kurz dokumentieren und an Florian geben.

---

## 8) Typische Fehler und schnelle Loesung

### Problem: Verbindung klappt nicht
- SSH lokal in PowerShell testen (`ssh vanessa-dev@10.80.80.20`)
- Key-Pfad pruefen
- Firewall/VPN pruefen

### Problem: Falsches System erwischt
- URL muss `http://drive/test` sein
- TESTSYSTEM-Badge muss sichtbar sein
- Wenn nicht: sofort stoppen

### Problem: Keine Schreibrechte in `/data/greiner-test`
- Admin soll Gruppen-/Dateirechte fuer `vanessa-dev` pruefen

---

## 9) Do / Don't

**Do**
- Nur Testsystem
- Kleine, pruefbare Aenderungen
- Klar dokumentieren, was geaendert wurde

**Don't**
- Keine Produktion
- Keine unkontrollierten Systemaenderungen
- Keine Secrets in Prompts/Dateien

