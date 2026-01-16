# TT-Zeit Frontend-Integration: Plan - TAG 195

**Datum:** 2026-01-16  
**Ziel:** TT-Zeit-Analyse im Frontend integrieren

---

## 🎯 EMPFOHLENE INTEGRATIONSPUNKTE

### Option 1: Im Auftragsdetail-Modal ⭐⭐⭐ (Empfohlen)

**Dateien:**
- `templates/aftersales/garantie_auftraege_uebersicht.html`
- `templates/sb/werkstatt_live.html`

**Position:**
- Direkt neben dem Button "Garantieakte erstellen"
- Im Bereich wo Garantie-Buttons angezeigt werden

**Vorteile:**
- ✅ Serviceberater sieht alle Auftragsdetails
- ✅ Kontext ist klar (Garantieauftrag)
- ✅ Modal bietet Platz für Analyse-Ergebnisse
- ✅ Konsistent mit bestehender UX

**Code-Stelle:**
```javascript
// In renderAuftragDetail() Funktion
${(a.garantie && a.garantie.ist_garantie) ? `
<div class="mt-3">
    <button class="btn btn-primary btn-sm" onclick="erstelleGarantieakte(${a.auftrag_nr || auftragNr})" id="btnGarantieakte">
        <i class="bi bi-file-earmark-pdf"></i> Garantieakte erstellen
    </button>
    <button class="btn btn-info btn-sm ms-2" onclick="pruefeTTZeit(${a.auftrag_nr || auftragNr})" id="btnTTZeit">
        <i class="bi bi-clock-history"></i> TT-Zeit prüfen
    </button>
    <div id="garantieakteStatus" class="mt-2"></div>
    <div id="ttZeitStatus" class="mt-2"></div>
</div>
` : ''}
```

---

### Option 2: In der Garantieaufträge-Tabelle ⭐⭐

**Datei:**
- `templates/aftersales/garantie_auftraege_uebersicht.html`

**Position:**
- In der Spalte "Aktion" neben "Garantieakte erstellen"

**Vorteile:**
- ✅ Schneller Zugriff aus Übersicht
- ✅ Kein Modal öffnen nötig

**Nachteile:**
- ❌ Weniger Platz für Analyse-Ergebnisse
- ❌ Muss eigenes Modal öffnen

**Code-Stelle:**
```javascript
// In renderAuftraege() Funktion, Spalte "Aktion"
aktion = `
    <button class="btn btn-sm btn-primary btn-create-akte" onclick="erstelleGarantieakte(${a.auftrag_nr}, '${escapeHtml(a.kunde)}')">
        <i class="bi bi-file-earmark-pdf"></i> Erstellen
    </button>
    <button class="btn btn-sm btn-info ms-1" onclick="pruefeTTZeit(${a.auftrag_nr})">
        <i class="bi bi-clock-history"></i> TT-Zeit
    </button>
`;
```

---

## 🔧 IMPLEMENTIERUNG

### 1. JavaScript-Funktion `pruefeTTZeit()`

**Datei:** `templates/aftersales/garantie_auftraege_uebersicht.html`

```javascript
function pruefeTTZeit(auftragNr) {
    const btn = event?.target?.closest('button') || document.getElementById('btnTTZeit');
    const originalHtml = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Analysiere...';
    
    fetch(`/api/ai/analysiere/tt-zeit/${auftragNr}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        
        if (!data.success) {
            alert(`Fehler: ${data.error || 'Unbekannter Fehler'}`);
            return;
        }
        
        // Zeige Modal mit Analyse-Ergebnissen
        showTTZeitModal(data, auftragNr);
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
        alert(`Fehler: ${err.message}`);
    });
}
```

### 2. Modal für TT-Zeit-Analyse

**HTML-Struktur:**
```html
<!-- TT-Zeit Modal -->
<div class="modal fade" id="ttZeitModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-clock-history"></i> TT-Zeit-Analyse - Auftrag <span id="modalTTZeitAuftragNr"></span>
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="ttZeitModalBody">
                <!-- Wird dynamisch gefüllt -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Schließen</button>
                <button type="button" class="btn btn-success" id="btnTTZeitBestaetigen" onclick="bestaetigeGSWPruefung()" disabled>
                    <i class="bi bi-check-circle"></i> GSW Portal geprüft - Keine Arbeitsoperationsnummer
                </button>
            </div>
        </div>
    </div>
</div>
```

**JavaScript-Funktion `showTTZeitModal()`:**
```javascript
function showTTZeitModal(data, auftragNr) {
    const modal = new bootstrap.Modal(document.getElementById('ttZeitModal'));
    document.getElementById('modalTTZeitAuftragNr').textContent = auftragNr;
    
    const tp = data.technische_pruefung;
    const ki = data.ki_analyse;
    const warnung = data.warnung;
    const regeln = data.abrechnungsregeln;
    const teil = tp.schadhaftes_teil;
    
    let html = `
        <!-- Technische Prüfung -->
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0"><i class="bi bi-check-circle"></i> Technische Prüfung</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Garantieauftrag:</strong> ${tp.is_garantie ? '<span class="badge bg-success">Ja</span>' : '<span class="badge bg-danger">Nein</span>'}</p>
                        <p><strong>Stempelzeiten:</strong> ${tp.stempelzeiten_vorhanden ? '<span class="badge bg-success">Vorhanden</span>' : '<span class="badge bg-danger">Fehlt</span>'}</p>
                        ${tp.stempelzeiten_vorhanden ? `
                            <p class="small text-muted">
                                ${tp.stempelzeiten_anzahl} Stempelungen<br>
                                ${tp.stempelzeiten_stunden.toFixed(2)} Stunden (${tp.stempelzeiten_minuten.toFixed(1)} Min)
                            </p>
                        ` : ''}
                    </div>
                    <div class="col-md-6">
                        <p><strong>TT-Zeit bereits eingereicht:</strong> ${tp.tt_zeit_vorhanden ? '<span class="badge bg-warning">Ja</span>' : '<span class="badge bg-success">Nein</span>'}</p>
                        ${teil ? `
                            <p><strong>Schadhaften Teil:</strong></p>
                            <p class="small">
                                <strong>${teil.teilenummer}</strong><br>
                                ${teil.beschreibung}
                            </p>
                        ` : '<p class="text-warning"><strong>Schadhaften Teil nicht identifiziert!</strong></p>'}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- KI-Analyse -->
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0"><i class="bi bi-robot"></i> KI-Analyse</h6>
            </div>
            <div class="card-body">
                <p><strong>Begründung:</strong></p>
                <p class="small">${ki.begruendung || 'Nicht verfügbar'}</p>
                
                <p class="mt-2"><strong>Empfehlung:</strong></p>
                <p class="small"><strong>${ki.empfehlung || 'Bitte manuell prüfen'}</strong></p>
                
                ${ki.hinweise && ki.hinweise.length > 0 ? `
                    <p class="mt-2"><strong>Hinweise:</strong></p>
                    <ul class="small">
                        ${ki.hinweise.map(h => `<li>${h}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        </div>
        
        <!-- Warnung -->
        <div class="alert alert-warning">
            <h6><i class="bi bi-exclamation-triangle"></i> ${warnung.text}</h6>
            <p class="mb-0 small">${warnung.hinweis}</p>
        </div>
        
        <!-- Abrechnungsregeln -->
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0"><i class="bi bi-info-circle"></i> Abrechnungsregeln</h6>
            </div>
            <div class="card-body">
                <p><strong>Bis 0,9 Stunden (9 AW):</strong></p>
                <p class="small">
                    ✅ Ohne Freigabe abrechenbar<br>
                    Max. ${regeln.bis_09_stunden.max_aw} AW (${regeln.bis_09_stunden.max_minuten} Min)<br>
                    Max. Vergütung: ${regeln.bis_09_stunden.verguetung_max.toFixed(2)}€
                </p>
                
                <p class="mt-2"><strong>Ab 1,0 Stunden (10 AW):</strong></p>
                <p class="small">
                    ⚠️ Freigabe erforderlich<br>
                    Min. ${regeln.ab_10_stunden.min_aw} AW (${regeln.ab_10_stunden.min_minuten} Min)<br>
                    Freigabe über: ${regeln.ab_10_stunden.freigabe_ueber}
                </p>
            </div>
        </div>
    `;
    
    document.getElementById('ttZeitModalBody').innerHTML = html;
    
    // Button aktivieren wenn technische Prüfung OK
    const btnBestaetigen = document.getElementById('btnTTZeitBestaetigen');
    if (tp.is_garantie && tp.stempelzeiten_vorhanden && !tp.tt_zeit_vorhanden && teil) {
        btnBestaetigen.disabled = false;
    } else {
        btnBestaetigen.disabled = true;
    }
    
    modal.show();
}
```

### 3. Bestätigungs-Funktion

```javascript
function bestaetigeGSWPruefung() {
    const auftragNr = parseInt(document.getElementById('modalTTZeitAuftragNr').textContent);
    
    if (!confirm(`Bestätigen Sie, dass Sie im GSW Portal geprüft haben und KEINE Arbeitsoperationsnummer für das schadhaften Teil vorhanden ist?\n\nAuftrag: ${auftragNr}`)) {
        return;
    }
    
    // TODO: Bestätigung in Datenbank speichern (optional)
    // fetch(`/api/ai/tt-zeit/bestaetigen/${auftragNr}`, { method: 'POST' })
    
    alert('✅ Bestätigung gespeichert! Sie können nun TT-Zeit über die Garantie SOAP API hinzufügen.');
    
    // Modal schließen
    bootstrap.Modal.getInstance(document.getElementById('ttZeitModal')).hide();
}
```

---

## 📋 INTEGRATION IN DATEIEN

### 1. `templates/aftersales/garantie_auftraege_uebersicht.html`

**Zu ändern:**
- `renderAuftragDetail()` Funktion erweitern (Button hinzufügen)
- `pruefeTTZeit()` Funktion hinzufügen
- `showTTZeitModal()` Funktion hinzufügen
- `bestaetigeGSWPruefung()` Funktion hinzufügen
- Modal HTML hinzufügen

### 2. `templates/sb/werkstatt_live.html`

**Zu ändern:**
- `renderAuftragDetail()` Funktion erweitern (Button hinzufügen)
- `pruefeTTZeit()` Funktion hinzufügen
- `showTTZeitModal()` Funktion hinzufügen
- `bestaetigeGSWPruefung()` Funktion hinzufügen
- Modal HTML hinzufügen

---

## 🎨 UI/UX

### Button-Design:
- **Icon:** `bi-clock-history` (Bootstrap Icons)
- **Farbe:** `btn-info` (Blau, für Analyse)
- **Text:** "TT-Zeit prüfen"

### Modal-Design:
- **Größe:** `modal-lg` (groß, für viele Informationen)
- **Struktur:**
  1. Technische Prüfung (Card)
  2. KI-Analyse (Card)
  3. Warnung (Alert)
  4. Abrechnungsregeln (Card)

### Bestätigungs-Button:
- **Farbe:** `btn-success` (Grün)
- **Icon:** `bi-check-circle`
- **Text:** "GSW Portal geprüft - Keine Arbeitsoperationsnummer"
- **Disabled:** Wenn technische Prüfung nicht OK

---

## ✅ NÄCHSTE SCHRITTE

1. **Modal HTML hinzufügen** (in beide Dateien)
2. **JavaScript-Funktionen hinzufügen** (in beide Dateien)
3. **Button in renderAuftragDetail() hinzufügen** (in beide Dateien)
4. **Testing** mit echten Aufträgen
5. **Optional:** Bestätigung in Datenbank speichern

---

**Erstellt:** TAG 195  
**Status:** Plan erstellt, bereit für Implementierung
