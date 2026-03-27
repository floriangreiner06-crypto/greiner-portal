# 🧪 GREINER PORTAL - FEATURE TEST CHECKLISTE
**Datum:** _________________  
**Tester:** _________________  
**Branch:** _________________  
**Version:** _________________

---

## 📋 ANLEITUNG
1. Server starten: `sudo systemctl start greiner-portal`
2. Browser öffnen: `http://srvlinux01:5000` (oder entsprechender Port)
3. Jeden Test durchführen und Ergebnis markieren
4. Bei Fehler: Screenshot + Fehlermeldung notieren

**Legende:**
- ✅ = Funktioniert
- ❌ = Funktioniert nicht
- ⚠️ = Funktioniert teilweise / mit Problemen
- ⏭️ = Übersprungen / nicht getestet

---

## 🔐 1. AUTHENTICATION & AUTHORIZATION

### Login
- [ ] Login-Seite lädt korrekt
- [ ] Formular ist sichtbar
- [ ] Login mit korrekten Credentials funktioniert
- [ ] Login mit falschen Credentials zeigt Fehlermeldung
- [ ] Redirect nach Login geht zu Dashboard (nicht index)
- [ ] Session wird korrekt erstellt

**Bemerkungen:**
```


```

### Logout
- [ ] Logout-Button ist sichtbar
- [ ] Logout funktioniert
- [ ] Session wird beendet
- [ ] Redirect zu Login-Seite

**Bemerkungen:**
```


```

### Session Management
- [ ] Session bleibt nach Reload bestehen
- [ ] Session läuft nach Timeout ab
- [ ] Geschützte Seiten ohne Login nicht erreichbar

**Bemerkungen:**
```


```

---

## 🏦 2. BANKENSPIEGEL

### Transaktionen Anzeige
- [ ] Seite lädt ohne Fehler
- [ ] Transaktionen werden angezeigt
- [ ] Sortierung nach Datum (neueste zuerst)
- [ ] Alle Spalten korrekt dargestellt:
  - [ ] Datum
  - [ ] Betrag
  - [ ] Verwendungszweck
  - [ ] Bank/Konto
  - [ ] Kategorie (falls vorhanden)
- [ ] Keine Duplikate sichtbar

**Anzahl Transaktionen:** _______  
**Bemerkungen:**
```


```

### Sparkasse-Transaktionen
- [ ] Sparkasse-Daten vorhanden
- [ ] Keine Duplikate
- [ ] Datum korrekt formatiert
- [ ] Beträge korrekt

**Bemerkungen:**
```


```

### VR Bank-Transaktionen
- [ ] VR Bank-Daten vorhanden
- [ ] Parsing korrekt
- [ ] Datum korrekt formatiert

**Bemerkungen:**
```


```

### HypoVereinsbank-Transaktionen
- [ ] HypoVereinsbank-Daten vorhanden
- [ ] Parsing korrekt
- [ ] Datum korrekt formatiert

**Bemerkungen:**
```


```

### Filterung
- [ ] Filter nach Datum funktioniert
- [ ] Filter nach Bank funktioniert
- [ ] Filter nach Betrag funktioniert
- [ ] Mehrere Filter kombinierbar

**Bemerkungen:**
```


```

### Suche
- [ ] Suchfeld vorhanden
- [ ] Suche nach Verwendungszweck funktioniert
- [ ] Suche nach Betrag funktioniert

**Bemerkungen:**
```


```

---

## 📤 3. PDF IMPORT

### Import-Funktion
- [ ] Import-Button sichtbar
- [ ] Datei-Upload funktioniert
- [ ] PDF wird akzeptiert
- [ ] Parsing startet

**Bemerkungen:**
```


```

### Sparkasse PDF
- [ ] Import erfolgreich
- [ ] Transaktionen werden erkannt
- [ ] Daten korrekt in DB gespeichert
- [ ] Keine Duplikate erstellt

**Test-Datei:** _________________  
**Bemerkungen:**
```


```

### VR Bank PDF
- [ ] Import erfolgreich
- [ ] Transaktionen werden erkannt

**Test-Datei:** _________________  
**Bemerkungen:**
```


```

### HypoVereinsbank PDF
- [ ] Import erfolgreich
- [ ] Transaktionen werden erkannt

**Test-Datei:** _________________  
**Bemerkungen:**
```


```

---

## 📊 4. GRAFANA INTEGRATION

### Dashboard Einbindung
- [ ] Grafana-Seite erreichbar
- [ ] iFrame lädt korrekt
- [ ] Dashboard wird angezeigt
- [ ] Keine CORS-Fehler
- [ ] Responsive Design funktioniert

**URL:** _________________  
**Bemerkungen:**
```


```

### Authentifizierung
- [ ] Automatisches Login in Grafana
- [ ] Session-Handling funktioniert
- [ ] Keine doppelte Login-Aufforderung

**Bemerkungen:**
```


```

### Dashboard-Funktionen
- [ ] Zeitraum-Auswahl funktioniert
- [ ] Refresh funktioniert
- [ ] Drill-Down funktioniert
- [ ] Panels sind interaktiv

**Bemerkungen:**
```


```

---

## 🏖️ 5. URLAUBSPLANER

### Anzeige
- [ ] Urlaubsplaner-Seite lädt
- [ ] Kalenderansicht sichtbar
- [ ] Urlaube werden angezeigt

**Bemerkungen:**
```


```

### CRUD Operations
- [ ] Neuen Urlaub anlegen funktioniert
- [ ] Urlaub bearbeiten funktioniert
- [ ] Urlaub löschen funktioniert
- [ ] Urlaub genehmigen funktioniert (falls Funktion vorhanden)

**Bemerkungen:**
```


```

---

## 🎨 6. FRONTEND / UI

### Navigation
- [ ] Menü ist sichtbar
- [ ] Alle Links funktionieren
- [ ] Aktive Seite wird markiert
- [ ] Responsive Navigation auf Mobile

**Bemerkungen:**
```


```

### Static Files
- [ ] CSS lädt korrekt
- [ ] JavaScript lädt korrekt
- [ ] Bilder werden angezeigt
- [ ] Cache-Busting funktioniert (Versionsnummer in URL)

**Bemerkungen:**
```


```

### Responsive Design
- [ ] Desktop-Ansicht OK
- [ ] Tablet-Ansicht OK
- [ ] Mobile-Ansicht OK

**Bemerkungen:**
```


```

### Dashboard (Startseite)
- [ ] Dashboard lädt
- [ ] Widgets/Kacheln werden angezeigt
- [ ] Statistiken sind aktuell
- [ ] Charts/Diagramme funktionieren

**Bemerkungen:**
```


```

---

## 🔧 7. TECHNISCHE PRÜFUNGEN

### Server / Service
- [ ] Service läuft: `systemctl status greiner-portal`
- [ ] Keine Fehler in Logs: `journalctl -u greiner-portal -n 50`
- [ ] Speicherverbrauch OK
- [ ] CPU-Last OK

**Bemerkungen:**
```


```

### Datenbank
- [ ] DB-Verbindung funktioniert
- [ ] Queries laufen ohne Fehler
- [ ] Keine SQL-Errors in Logs

**Bemerkungen:**
```


```

### Performance
- [ ] Ladezeiten akzeptabel (<2 Sekunden)
- [ ] Keine Timeouts
- [ ] Smooth Navigation

**Bemerkungen:**
```


```

---

## 🐛 8. FEHLER & ISSUES

### Kritische Fehler
```
1. 
2. 
3. 
```

### Mittlere Fehler
```
1. 
2. 
3. 
```

### Kleinere Probleme
```
1. 
2. 
3. 
```

---

## 📊 ZUSAMMENFASSUNG

**Funktionierende Features:** _____ / _____  
**Fehlerhafte Features:** _____ / _____  
**Nicht getestet:** _____ / _____

**Gesamt-Bewertung:**
- [ ] 🟢 Gut - System läuft stabil
- [ ] 🟡 Mittel - Kleinere Probleme vorhanden
- [ ] 🔴 Kritisch - Große Probleme, nicht produktionsreif

**Prioritäre Fixes:**
```
1. 
2. 
3. 
```

---

## 📝 NÄCHSTE SCHRITTE

**Sofort:**
1. 
2. 
3. 

**Kurzfristig:**
1. 
2. 
3. 

**Mittelfristig:**
1. 
2. 
3. 

---

**Test abgeschlossen am:** _________________  
**Unterschrift:** _________________
