# Anleitung: Twilio Auth Token in .env ersetzen (mit PuTTY)

**TAG:** 211  
**Ziel:** Auth Token in `config/.env` auf dem Server ändern – per SSH mit PuTTY.

---

## 1. Mit PuTTY auf den Server verbinden

1. **PuTTY starten** (von Windows aus).
2. **Host Name:** z.B. `10.80.80.20` oder `ag-admin@10.80.80.20` (je nach Einrichtung).
3. **Port:** `22` (Standard für SSH).
4. **Connection type:** SSH.
5. **Open** klicken.
6. Beim ersten Mal evtl. Sicherheitsabfrage mit **Ja** bestätigen.
7. **Login:** Benutzername eingeben (z.B. `ag-admin`).
8. **Passwort:** Passwort eingeben (Eingabe wird nicht angezeigt).

Du bist eingeloggt, wenn eine Eingabezeile mit z.B. `ag-admin@srvlinux01:~$` erscheint.

---

## 2. Zum Projektordner wechseln

In der PuTTY-Konsole eingeben:

```bash
cd /opt/greiner-portal
```

Enter drücken.

---

## 3. Datei `config/.env` bearbeiten

### Option A: Mit `nano` (einfach)

```bash
nano config/.env
```

- **Cursor:** Mit Pfeiltasten zur Zeile `TWILIO_AUTH_TOKEN=...` gehen.
- **Alten Token löschen:** Nach dem `=` alles bis Zeilenende markieren bzw. löschen (z.B. mit Pfeil rechts und Entf oder Backspace).
- **Neuen Token eintragen:** Den neuen Token von Twilio eintippen (ohne Leerzeichen, ohne Anführungszeichen).
- **Speichern:** `Strg + O`, dann Enter.
- **Beenden:** `Strg + X`.

### Option B: Mit `sed` (ohne Editor öffnen)

Alten Token durch neuen ersetzen (nur den **NEUEN_TOKEN** anpassen):

```bash
sed -i 's/TWILIO_AUTH_TOKEN=.*/TWILIO_AUTH_TOKEN=DEIN_NEUER_TOKEN_HIER/' /opt/greiner-portal/config/.env
```

Beispiel, wenn dein neuer Token `abc123xyz` ist:

```bash
sed -i 's/TWILIO_AUTH_TOKEN=.*/TWILIO_AUTH_TOKEN=abc123xyz/' /opt/greiner-portal/config/.env
```

**Prüfen:**

```bash
grep TWILIO_AUTH_TOKEN /opt/greiner-portal/config/.env
```

Es darf nur eine Zeile erscheinen, und der Wert sollte dein neuer Token sein (ohne dass der Token komplett in der Ausgabe steht, wenn du das aus Sicherheitsgründen vermeiden willst, reicht: Zeile existiert und sieht so aus wie `TWILIO_AUTH_TOKEN=...`).

---

## 4. Service neu starten

Damit die App den neuen Token lädt:

```bash
sudo systemctl restart greiner-portal
```

Falls nach einem Passwort gefragt wird: Benutzerpasswort eingeben und Enter drücken.

**Kurz prüfen:**

```bash
sudo systemctl status greiner-portal
```

Status sollte **active (running)** sein.

---

## 5. Neuen Token in Twilio erzeugen (empfohlen nach Wechsel)

1. Im Browser: [Twilio Console](https://console.twilio.com/) → **Account** → **API keys & tokens**.
2. Unter **Auth Token** auf **Create new token** / **Regenerate** klicken.
3. Neuen Token kopieren und **sofort** in der `.env` eintragen (wie in Schritt 3).
4. Alten Token nicht mehr verwenden (Twilio zeigt den alten nach Regenerierung nicht mehr an).

---

## Kurz-Checkliste

- [ ] PuTTY geöffnet, mit Server verbunden (z.B. `10.80.80.20`, User/Passwort).
- [ ] `cd /opt/greiner-portal`
- [ ] `nano config/.env` ODER `sed`-Befehl mit neuem Token ausführen.
- [ ] Zeile `TWILIO_AUTH_TOKEN=NEUER_TOKEN` prüfen (z.B. mit `grep TWILIO_AUTH_TOKEN config/.env`).
- [ ] `sudo systemctl restart greiner-portal`
- [ ] `sudo systemctl status greiner-portal` → **active (running)**.

---

## Häufige Fehler

- **„Permission denied“**  
  Datei gehört root oder anderem User:  
  `sudo nano /opt/greiner-portal/config/.env`  
  oder mit deinem User arbeiten, der Schreibrechte auf `/opt/greiner-portal` hat.

- **Token mit Sonderzeichen**  
  In `nano`: einfach den Token eintippen, keine Anführungszeichen.  
  Bei `sed`: Sonderzeichen wie `&`, `/`, `\` im Token können Probleme machen – dann lieber `nano` verwenden.

- **Service startet nicht**  
  Logs ansehen:  
  `sudo journalctl -u greiner-portal -n 50 --no-pager`

---

**Datei:** `config/.env` auf dem Server (z.B. `/opt/greiner-portal/config/.env`)  
**Zeile:** `TWILIO_AUTH_TOKEN=...`  
**Nach Änderung:** immer `sudo systemctl restart greiner-portal` ausführen.
