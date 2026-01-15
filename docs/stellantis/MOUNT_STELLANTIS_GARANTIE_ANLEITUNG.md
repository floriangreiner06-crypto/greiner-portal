# Mount-Einrichtung: Stellantis Garantie-Verzeichnis

**TAG 189:** Anleitung zur Einrichtung des Mount-Punkts für Stellantis Garantieaufträge

---

## 📋 VORAUSSETZUNGEN

1. ✅ Windows-Ordner erstellt: `\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie\`
2. ✅ Berechtigungen: Schreibrechte für Server-User (`ag-admin`)

---

## 🔧 EINRICHTUNG

### Option 1: Mount-Script ausführen (Empfohlen)

```bash
sudo /opt/greiner-portal/scripts/mount_stellantis_garantie.sh
```

**Hinweis:** Benötigt sudo-Passwort (`OHL.greiner2025`)

### Option 2: Manuell mounten

```bash
# 1. Mount-Punkt erstellen
sudo mkdir -p /mnt/stellantis-garantie

# 2. Mounten
sudo mount -t cifs //srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie \
    -o credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775

# 3. Prüfen
mount | grep stellantis-garantie
ls -la /mnt/stellantis-garantie/
```

---

## 🔄 PERSISTENT MACHEN (fstab)

Füge folgende Zeile zu `/etc/fstab` hinzu:

```bash
sudo nano /etc/fstab
```

**Eintrag hinzufügen:**
```
//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0
```

**Dann testen:**
```bash
sudo mount -a
```

**Prüfen:**
```bash
mount | grep stellantis-garantie
```

---

## ✅ PRÜFUNG

### 1. Mount-Status prüfen

```bash
mount | grep stellantis-garantie
```

**Erwartete Ausgabe:**
```
//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie on /mnt/stellantis-garantie type cifs (...)
```

### 2. Schreibrechte testen

```bash
touch /mnt/stellantis-garantie/test.txt && rm /mnt/stellantis-garantie/test.txt && echo "✅ OK"
```

### 3. Ordner-Inhalt prüfen

```bash
ls -la /mnt/stellantis-garantie/
```

---

## 🔍 TROUBLESHOOTING

### Mount schlägt fehl

**Prüfe:**
1. Netzwerk-Verbindung: `ping srvrdb01`
2. Credentials: `/root/.smbcredentials` existiert und ist korrekt
3. Windows-Berechtigungen für `\\srvrdb01\Allgemein\DigitalesAutohaus\Stellantis_Garantie`

### Keine Schreibrechte

**Prüfe:**
1. Mount-Optionen: `uid=1000,gid=1000` (ag-admin User)
2. Windows-Berechtigungen: Ordner muss für "jeder" oder "ag-admin" schreibbar sein
3. Mount-Status: `mount | grep stellantis-garantie`

### Mount geht nach Reboot verloren

**Lösung:**
- `/etc/fstab`-Eintrag hinzufügen (siehe oben)

---

## 📝 VERGLEICH: Hyundai vs. Stellantis

| Aspekt | Hyundai | Stellantis |
|--------|---------|------------|
| **Mount-Punkt** | `/mnt/hyundai-garantie` | `/mnt/stellantis-garantie` |
| **Windows-Pfad** | `\\srvrdb01\...\Hyundai_Garantie\` | `\\srvrdb01\...\Stellantis_Garantie\` |
| **Script** | `mount_hyundai_garantie.sh` | `mount_stellantis_garantie.sh` |

---

*Erstellt: TAG 189 | Autor: Claude AI*
