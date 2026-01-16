# TT-Zeit Frontend-Integration: Rollback-Anleitung - TAG 195

**Datum:** 2026-01-16  
**Zweck:** Einfacher Rollback der TT-Zeit-Frontend-Integration

---

## 🔄 ROLLBACK

### Geänderte Dateien:

1. **`templates/aftersales/garantie_auftraege_uebersicht.html`**

### Was wurde geändert:

1. **TT-Zeit-Button hinzugefügt** (in `renderAuftragDetail()` Funktion, ca. Zeile 543)
2. **TT-Zeit-Modal hinzugefügt** (nach `auftragModal`, ca. Zeile 113)
3. **JavaScript-Funktionen hinzugefügt** (nach `oeffneAkte()`, ca. Zeile 548):
   - `pruefeTTZeit()`
   - `showTTZeitModal()`
   - `bestaetigeGSWPruefung()`

---

## 🔙 ROLLBACK-SCHRITTE

### Option 1: Git Rollback (Empfohlen)

```bash
cd /opt/greiner-portal
git diff templates/aftersales/garantie_auftraege_uebersicht.html
git checkout templates/aftersales/garantie_auftraege_uebersicht.html
```

### Option 2: Manueller Rollback

**1. Entferne TT-Zeit-Button (ca. Zeile 543-555):**

**Entferne:**
```javascript
    // TAG 195: TT-Zeit-Prüfung Button (nur bei Garantieaufträgen)
    // Prüfe ob Garantieauftrag (alle Aufträge in dieser Übersicht sind Garantieaufträge)
    html += `
        <div class="row mt-3">
            <div class="col-12">
                <div class="d-flex gap-2">
                    <button class="btn btn-primary btn-sm" onclick="erstelleGarantieakte(${a.auftrag_nr || auftragNr || 'null'}, '${escapeHtml(a.kunde || '')}')" id="btnGarantieakte">
                        <i class="bi bi-file-earmark-pdf"></i> Garantieakte erstellen
                    </button>
                    <button class="btn btn-info btn-sm" onclick="pruefeTTZeit(${a.auftrag_nr || auftragNr || 'null'})" id="btnTTZeit">
                        <i class="bi bi-clock-history"></i> TT-Zeit prüfen
                    </button>
                </div>
                <div id="garantieakteStatus" class="mt-2"></div>
                <div id="ttZeitStatus" class="mt-2"></div>
            </div>
        </div>
    `;
```

**Ersetze durch:**
```javascript
    document.getElementById('auftragModalBody').innerHTML = html;
}
```

**2. Entferne TT-Zeit-Modal (ca. Zeile 113-130):**

**Entferne:**
```html
<!-- TT-Zeit Modal (TAG 195) -->
<div class="modal fade" id="ttZeitModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="bi bi-clock-history"></i> TT-Zeit-Analyse - Auftrag <span id="modalTTZeitAuftragNr">-</span>
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

**3. Entferne JavaScript-Funktionen (ca. Zeile 548-700):**

**Entferne:**
```javascript
// ============================================================================
// TT-ZEIT-ANALYSE (TAG 195)
// ============================================================================

function pruefeTTZeit(auftragNr) {
    // ... gesamte Funktion ...
}

function showTTZeitModal(data, auftragNr) {
    // ... gesamte Funktion ...
}

function bestaetigeGSWPruefung() {
    // ... gesamte Funktion ...
}
```

---

## ✅ VERIFIZIERUNG NACH ROLLBACK

1. **Browser-Refresh:** Strg+F5 (Hard Refresh)
2. **Prüfe:** TT-Zeit-Button sollte nicht mehr sichtbar sein
3. **Prüfe:** Keine JavaScript-Fehler in Browser-Konsole
4. **Prüfe:** Garantieakte-Button funktioniert noch

---

## 📝 MARKIERUNGEN FÜR EINFACHEN ROLLBACK

**Alle Änderungen sind mit `TAG 195` markiert:**

- `// TAG 195: TT-Zeit-Prüfung Button`
- `<!-- TT-Zeit Modal (TAG 195) -->`
- `// ============================================================================`
- `// TT-ZEIT-ANALYSE (TAG 195)`
- `// ============================================================================`

**Suche nach `TAG 195` in der Datei, um alle Änderungen zu finden!**

---

## 🔍 SUCHE NACH ÄNDERUNGEN

```bash
cd /opt/greiner-portal
grep -n "TAG 195" templates/aftersales/garantie_auftraege_uebersicht.html
```

---

**Erstellt:** TAG 195  
**Status:** Rollback-Anleitung erstellt
