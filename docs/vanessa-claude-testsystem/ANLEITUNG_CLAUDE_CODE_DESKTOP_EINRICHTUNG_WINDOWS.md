# Claude Code Desktop (Windows) - Einrichtung

## 1) SSH lokal pruefen

```powershell
ssh -V
ssh vanessa-dev@10.80.80.20
```

## 2) Projekt in Claude Code Desktop

- Verbindung: SSH/Remote
- Host: `10.80.80.20`
- User: `vanessa-dev`
- Working Directory: `/data/greiner-test`

## 3) Projektregeln hinterlegen

- nur Testsystem
- nur `http://drive/test`
- keine Produktivpfade/-restars/-migrationen
