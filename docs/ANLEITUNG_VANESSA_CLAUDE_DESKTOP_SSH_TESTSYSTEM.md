# Anleitung: Vanessa + Claude Desktop per SSH ins Testsystem

Stand: 2026-03-20  
Ziel: Vanessa soll sicher im **Testsystem** arbeiten, ohne Produktivrisiko.

---

## 1) Zielbild (kurz)

- Vanessa arbeitet mit Claude Desktop/Cursor auf dem Server.
- Technischer Arbeitsbereich ist nur: `/data/greiner-test` (bzw. `/opt/greiner-test`).
- Test-URL ist: `http://drive/test`
- Produktion (`/opt/greiner-portal`) bleibt tabu.

---

## 2) Linux-User fuer Vanessa anlegen

> Als `ag-admin` auf dem Server ausfuehren.

```bash
sudo adduser vanessa-dev
```

Empfehlung:
- Starkes Passwort setzen (auch wenn spaeter Key-Login erzwungen wird).
- Benutzer nur fuer Entwicklung/Test nutzen.

---

## 3) SSH-Key-Login einrichten (empfohlen, ohne Passwort)

### 3.1 Vanessa erzeugt auf Windows ein SSH-Keypair

In PowerShell (Windows):

```powershell
ssh-keygen -t ed25519 -C "vanessa-dev@greiner-test"
```

Standardpfad meist:
- Private Key: `C:\Users\<User>\.ssh\id_ed25519`
- Public Key: `C:\Users\<User>\.ssh\id_ed25519.pub`

### 3.2 Public Key auf Server hinterlegen

```bash
sudo mkdir -p /home/vanessa-dev/.ssh
sudo nano /home/vanessa-dev/.ssh/authorized_keys
```

Den Inhalt der `id_ed25519.pub` als **eine Zeile** einfuegen, dann:

```bash
sudo chown -R vanessa-dev:vanessa-dev /home/vanessa-dev/.ssh
sudo chmod 700 /home/vanessa-dev/.ssh
sudo chmod 600 /home/vanessa-dev/.ssh/authorized_keys
```

---

## 4) Test-Zugriff pruefen

Von Windows:

```powershell
ssh vanessa-dev@10.80.80.20
```

Erwartung:
- Login klappt
- Shell startet als `vanessa-dev`

Optional direkt mit Key:

```powershell
ssh -i C:\Users\<User>\.ssh\id_ed25519 vanessa-dev@10.80.80.20
```

---

## 5) Dateirechte fuer Test-Workspace

Vanessa muss in `/data/greiner-test` schreiben koennen.

Variante A (sauber): Gruppe nutzen

```bash
sudo groupadd greiner-dev || true
sudo usermod -aG greiner-dev vanessa-dev
sudo usermod -aG greiner-dev ag-admin
sudo chgrp -R greiner-dev /data/greiner-test
sudo chmod -R g+rwX /data/greiner-test
sudo find /data/greiner-test -type d -exec chmod g+s {} \;
```

Danach neu anmelden, damit Gruppenmitgliedschaft aktiv ist.

---

## 6) Optional: sudo stark begrenzen (nur falls benoetigt)

Wenn Vanessa den Test-Service selbst neu starten darf, dann **nur** diesen einen Befehl freigeben:

```bash
sudo visudo -f /etc/sudoers.d/vanessa-test
```

Inhalt:

```text
vanessa-dev ALL=(root) NOPASSWD: /bin/systemctl restart greiner-test, /bin/systemctl status greiner-test
```

Wichtig:
- **Kein** Zugriff auf `greiner-portal`
- **Kein** generelles `ALL`

---

## 7) Claude Desktop auf Windows konfigurieren

In Claude Desktop fuer SSH/Remote:

- Host: `10.80.80.20`
- User: `vanessa-dev`
- Key: `C:\Users\<User>\.ssh\id_ed25519`
- Startpfad: `/data/greiner-test`

System-/Projekt-Instruktion in Claude (empfohlen als feste Vorgabe):

1. Arbeite nur im Testsystem.
2. Verwende nur `http://drive/test` zum UI-Test.
3. Keine Aenderungen in `/opt/greiner-portal`.
4. Keine produktiven Services/Migrationen.
5. Fokus auf `templates/`, `static/css/`, `static/js/`.

---

## 8) Sicherer Tagesablauf fuer Vanessa

1. Claude/Cursor starten
2. Sicherstellen: Arbeitsverzeichnis = `/data/greiner-test`
3. Browser nur auf `http://drive/test`
4. Visuelle Kontrolle: TESTSYSTEM-Badge sichtbar
5. In kleinen Schritten aendern, testen, dokumentieren

---

## 9) Schnellchecks (Admin)

### Pruefen, ob User korrekt angelegt ist

```bash
id vanessa-dev
```

### Pruefen, ob Schreibrechte im Test da sind

```bash
sudo -u vanessa-dev bash -lc 'touch /data/greiner-test/.write_test && rm /data/greiner-test/.write_test && echo OK'
```

### Pruefen, ob Testservice laeuft

```bash
systemctl status greiner-test --no-pager -n 20
```

---

## 10) Nicht erlauben (wichtig)

- Arbeiten auf `http://drive` statt `http://drive/test`
- Datei-Edits direkt in `/opt/greiner-portal`
- Produktiv-Restarts oder Produktiv-Migrationen durch Vanessa
- Commits/Deploys ohne technische Freigabe

