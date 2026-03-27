# SSH-Setup fuer Vanessa (Kurzfassung)

## 1) User + Key

- SSH-User: `vanessa-dev`
- Key-basiertes Login verwenden (ed25519)

## 2) Verbindung testen (Windows PowerShell)

```powershell
ssh vanessa-dev@10.80.80.20
```

## 3) Arbeitsbereich

- Nur: `/data/greiner-test`
- Nie: `/opt/greiner-portal`

## 4) Optional begrenzte Rechte

- Falls noetig nur:
  - `systemctl status greiner-test`
  - `systemctl restart greiner-test`
