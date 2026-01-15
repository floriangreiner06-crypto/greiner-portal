# Mount-Einrichtung: Befehle für Stellantis Garantie

**TAG 189:** Befehle zum Ausführen auf dem Server

---

## 🔧 BEFEHLE ZUM AUSFÜHREN

### 1. Mount-Punkt erstellen

```bash
sudo mkdir -p /mnt/stellantis-garantie
```

### 2. Mounten (einmalig)

```bash
sudo mount -t cifs //srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie \
    -o credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775
```

### 3. Prüfen

```bash
# Mount-Status
mount | grep stellantis-garantie

# Schreibrechte testen
touch /mnt/stellantis-garantie/test.txt && rm /mnt/stellantis-garantie/test.txt && echo "✅ OK"
```

### 4. Persistent machen (fstab)

```bash
# Backup erstellen
sudo cp /etc/fstab /etc/fstab.backup

# Eintrag hinzufügen
sudo bash -c 'echo "" >> /etc/fstab'
sudo bash -c 'echo "# Stellantis Garantie-Verzeichnis (TAG 189)" >> /etc/fstab'
sudo bash -c 'echo "//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0" >> /etc/fstab'

# Testen
sudo mount -a
```

---

## ✅ VERGLEICH MIT HYUNDAI

**Hyundai fstab-Eintrag (bereits vorhanden):**
```
//srvrdb01/Allgemein/DigitalesAutohaus/Hyundai_Garantie /mnt/hyundai-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0
```

**Stellantis fstab-Eintrag (neu):**
```
//srvrdb01/Allgemein/DigitalesAutohaus/Stellantis_Garantie /mnt/stellantis-garantie cifs credentials=/root/.smbcredentials,domain=auto-greiner.de,vers=3.0,uid=1000,gid=1000,file_mode=0775,dir_mode=0775,nofail 0 0
```

**Unterschied:** Nur der Pfad ändert sich (`Hyundai_Garantie` → `Stellantis_Garantie`)

---

*Erstellt: TAG 189 | Autor: Claude AI*
