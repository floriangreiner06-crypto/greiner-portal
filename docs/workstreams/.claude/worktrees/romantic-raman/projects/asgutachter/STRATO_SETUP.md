# Strato Setup Anleitung

## 1. Login & Analyse

Nach Erhalt der Strato-Zugangsdaten:

### Strato Kundenlogin
```
URL: https://www.strato.de/apps/CustomerService
```

### Zu prüfen:
- [ ] **Paketname** (z.B. WP Starter, WP Pro, etc.)
- [ ] **PHP-Version** (mindestens 8.0 empfohlen)
- [ ] **SSL-Zertifikat** aktiv?
- [ ] **Speicherplatz** verfügbar
- [ ] **Datenbanken** - wie viele verfügbar/belegt?
- [ ] **Subdomains** - können erstellt werden?
- [ ] **FTP-Zugang** vorhanden?
- [ ] **Backup-Funktion** verfügbar?

---

## 2. Staging-Subdomain erstellen

### Option A: Strato-Subdomain
```
neu.asgutachter.de
```

### Schritte:
1. Strato Login → Domains → Subdomains
2. Neue Subdomain: `neu`
3. Verzeichnis: `/neu/` oder `/staging/`
4. SSL für Subdomain aktivieren

### Option B: Strato-Test-Domain (falls Subdomains nicht möglich)
```
asgutachter.strato-hosting.eu
```

---

## 3. WordPress Backup erstellen

**WICHTIG: VOR jeder Änderung!**

### Via Strato:
1. Strato Login → Hosting → Backups
2. Manuelles Backup erstellen
3. Download lokal speichern

### Via WordPress (falls Admin-Zugang):
1. Plugin: "UpdraftPlus" oder "All-in-One WP Migration"
2. Vollständiges Backup (DB + Files)
3. Download der Backup-Datei

### Via FTP (Fallback):
```bash
# Verzeichnis /www/ komplett downloaden
# phpMyAdmin: Datenbank exportieren
```

---

## 4. Staging-Installation

### WordPress auf Subdomain:
1. Strato AppWizard → WordPress installieren
2. Ziel: neu.asgutachter.de
3. Admin-Benutzer anlegen (nicht "admin"!)

### Oder: Kopie der Live-Seite:
1. Live-Backup auf Subdomain einspielen
2. wp-config.php anpassen (neue DB)
3. URLs in DB ändern (Search & Replace)

---

## 5. Theme-Entwicklung

### Basis-Theme
Empfehlung: **GeneratePress** oder **Astra**
- Leichtgewichtig
- Gut anpassbar
- SEO-optimiert

### Custom CSS
```css
/* CI Colors */
:root {
    --as-primary: #1a4d7c;
    --as-gold: #c9a227;
    --as-dark: #0d2840;
}

/* Buttons */
.btn-primary {
    background: var(--as-primary);
    border-color: var(--as-primary);
}

.btn-primary:hover {
    background: var(--as-gold);
    border-color: var(--as-gold);
}
```

---

## 6. Plugins (empfohlen)

| Plugin | Zweck |
|--------|-------|
| Contact Form 7 | Kontaktformular |
| WPForms Lite | Alternative für Formulare |
| Yoast SEO | SEO-Optimierung |
| Complianz | DSGVO Cookie-Banner |
| WP Super Cache | Performance |
| Updraft Plus | Backups |

---

## 7. Go-Live Checkliste

- [ ] Alle Formulare getestet (Test-Mail erhalten?)
- [ ] Mobile-Ansicht geprüft
- [ ] SSL funktioniert (https://)
- [ ] 404-Seiten gefixt
- [ ] Meta-Tags gesetzt
- [ ] Google Search Console verbunden
- [ ] Favicon aktualisiert
- [ ] Impressum & Datenschutz aktuell
- [ ] Cookie-Banner funktioniert
- [ ] Backup der alten Seite gespeichert

---

## 8. DNS-Umstellung (Go-Live)

### Bei Strato-interner Änderung:
- Kein DNS-Wechsel nötig
- Einfach Verzeichnis tauschen oder Redirect

### Verzeichnis-Swap:
```
/www/        → /www_backup/    (alte Seite)
/www_neu/    → /www/           (neue Seite)
```

---

## Notfall-Rollback

Falls etwas schiefgeht:
1. Backup wiederherstellen (Strato-Panel)
2. Oder: Verzeichnisse zurück tauschen
3. DNS-Cache: Max 24h bis Änderung sichtbar

---

## Support-Kontakte

- **Strato Hotline:** 030 300 146 0
- **Strato Hilfe:** https://www.strato.de/faq/

---

*Erstellt: 2025-12-29*
