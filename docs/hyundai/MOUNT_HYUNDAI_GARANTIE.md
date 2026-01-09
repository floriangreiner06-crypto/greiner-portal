# Mount-Konfiguration: Hyundai Garantie-Verzeichnis

**TAG 173:** Separater Mount-Punkt für `\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie`

## Mount-Informationen

- **Windows-Pfad:** `\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie`
- **Linux Mount-Punkt:** `/mnt/hyundai-garantie`
- **Typ:** CIFS/SMB
- **Credentials:** `/root/.smbcredentials`

## Einmalige Einrichtung

### 1. Mount-Punkt erstellen und mounten

```bash
sudo /opt/greiner-portal/scripts/mount_hyundai_garantie.sh
```

Oder manuell:

```bash
sudo mkdir -p /mnt/hyundai-garantie
sudo mount -t cifs //srvrdb01/Allgemein/DigitalesAutohaus/Hyundai_Garantie /mnt/hyundai-garantie \
    -o credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775
```

### 2. Persistent machen (fstab)

Füge folgende Zeile zu `/etc/fstab` hinzu:

```
//srvrdb01/Allgemein/DigitalesAutohaus/Hyundai_Garantie /mnt/hyundai-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0
```

Dann testen:

```bash
sudo mount -a
```

### 3. Prüfen

```bash
# Mount-Status prüfen
mount | grep hyundai-garantie

# Schreibrechte testen
touch /mnt/hyundai-garantie/test.txt && rm /mnt/hyundai-garantie/test.txt && echo "✅ OK"
```

## Verwendung im Code

Der Mount-Punkt wird automatisch in `api/garantieakte_workflow.py` verwendet:

```python
BASE_PATH_OPTIONS = [
    "/mnt/hyundai-garantie",  # Separater Mount (Priorität 1)
    # ... Fallback-Optionen
]
```

## Troubleshooting

### Mount schlägt fehl

1. Prüfe Credentials: `/root/.smbcredentials` existiert und ist korrekt
2. Prüfe Netzwerk: `ping srvrdb01`
3. Prüfe Windows-Berechtigungen für `\\srvrdb01\Allgemein\DigitalesAutohaus\Hyundai_Garantie`

### Keine Schreibrechte

1. Prüfe Mount-Optionen: `uid=1000,gid=1000` (ag-admin User)
2. Prüfe Windows-Berechtigungen: Ordner muss für "jeder" oder "ag-admin" schreibbar sein
3. Prüfe Mount-Status: `mount | grep hyundai-garantie`

### Automatisches Remount

Falls der Mount nach Reboot nicht automatisch gemountet wird:

1. Prüfe `/etc/fstab` Eintrag
2. Prüfe `nofail` Option (verhindert Boot-Fehler)
3. Teste manuell: `sudo mount -a`
