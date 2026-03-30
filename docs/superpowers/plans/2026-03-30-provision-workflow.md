# Provision Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mehrstufiger Freigabe-Workflow (VORLAUF -> ZUR_PRUEFUNG -> FREIGEGEBEN -> GENEHMIGT -> ENDLAUF) mit Einspruch/Ablehnung und vorbereiteten E-Mail-Stubs.

**Architecture:** 5 neue API-Endpoints fuer Statusuebergaenge in provision_api.py, Anpassung des bestehenden Endlauf-Endpoints, DB-Migration fuer Einspruch-Felder, Frontend-Buttons und Modals in provision_detail.html statusabhaengig, Dashboard-Badge-Erweiterung.

**Tech Stack:** Flask/Python, PostgreSQL, Jinja2 + Bootstrap 5 + Vanilla JS

---

## File Structure

| Datei | Aktion | Verantwortung |
|-------|--------|---------------|
| `migrations/add_provision_einspruch_felder.sql` | Create | SQL-Migration fuer einspruch_text/von/am |
| `api/provision_api.py` | Modify | Neue Endpoints (zur-pruefung, freigeben, einspruch, genehmigen, ablehnen), Genehmiger-Liste, E-Mail-Flag, Endlauf-Bedingung aendern |
| `api/provision_service.py` | Modify | get_lauf_detail um einspruch-Felder erweitern |
| `templates/provision/provision_detail.html` | Modify | Workflow-Buttons, Einspruch-Modal, Status-Anzeige |
| `templates/provision/provision_dashboard.html` | Modify | Status-Badge-Farben fuer ZUR_PRUEFUNG und GENEHMIGT |
| `routes/provision_routes.py` | Modify | Detail-Route Zugriff fuer eigenen Lauf erlauben |

---

### Task 1: DB-Migration — Einspruch-Felder hinzufuegen

**Files:**
- Create: `migrations/add_provision_einspruch_felder.sql`

- [ ] **Step 1: Migration-Datei erstellen**

```sql
-- Einspruch/Ablehnung-Felder fuer Provision-Workflow
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_text TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_von TEXT;
ALTER TABLE provision_laeufe ADD COLUMN IF NOT EXISTS einspruch_am TIMESTAMP;
```

- [ ] **Step 2: Migration auf beiden Datenbanken ausfuehren**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -f migrations/add_provision_einspruch_felder.sql
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal -f migrations/add_provision_einspruch_felder.sql
```

- [ ] **Step 3: Verifizieren**

```bash
PGPASSWORD=DrivePortal2024 psql -h 127.0.0.1 -U drive_user -d drive_portal_dev -c "\d provision_laeufe" | grep einspruch
```

Expected: 3 Zeilen (einspruch_text, einspruch_von, einspruch_am)

- [ ] **Step 4: Commit**

```bash
git add migrations/add_provision_einspruch_felder.sql
git commit -m "feat(provision): Migration fuer Einspruch-Felder (Workflow)"
```

---

### Task 2: Backend — Genehmiger-Liste + Workflow-Endpoints

**Files:**
- Modify: `api/provision_api.py`

5 neue Endpoints + Genehmiger-Konstante + E-Mail-Flag + Endlauf-Bedingung anpassen.

- [ ] **Step 1: Genehmiger-Liste und E-Mail-Flag hinzufuegen**

In `api/provision_api.py`, nach der bestehenden `_PROVISION_VOLLZUGRIFF_USERS`-Konstante (Zeile 32), einfuegen:

```python
# Genehmiger: Nur diese 2 Personen duerfen Provisionen genehmigen (einer reicht)
_PROVISION_GENEHMIGER_USERS = {
    'anton.suess@auto-greiner.de',
    'florian.greiner@auto-greiner.de',
}

# E-Mail-Versand: In Testversion deaktiviert
PROVISION_EMAIL_ENABLED = False


def _is_genehmiger():
    """Anton Suess oder Florian Greiner duerfen genehmigen/ablehnen."""
    if not current_user.is_authenticated:
        return False
    username = getattr(current_user, 'username', '') or ''
    return username.lower() in _PROVISION_GENEHMIGER_USERS


def _may_act_on_own_lauf(lauf_verkaufer_id):
    """Verkaeufer darf auf eigenen Lauf reagieren (Freigabe/Einspruch). Vollzugriff-User auch (Test)."""
    if _has_provision_vollzugriff():
        return True
    vkb = _get_vkb_for_request()
    return vkb is not None and vkb == lauf_verkaufer_id


def _get_username():
    """Username des aktuellen Users."""
    return getattr(current_user, 'username', '') or getattr(current_user, 'display_name', '') or 'system'


def _send_provision_email(to_emails, subject, body_html):
    """E-Mail senden (nur wenn PROVISION_EMAIL_ENABLED=True)."""
    if not PROVISION_EMAIL_ENABLED:
        return
    try:
        from api.graph_mail_connector import GraphMailConnector
        connector = GraphMailConnector()
        connector.send_mail('noreply@auto-greiner.de', to_emails, subject, body_html)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Provision-Email fehlgeschlagen: {e}')
```

- [ ] **Step 2: 5 neue Workflow-Endpoints hinzufuegen**

In `api/provision_api.py`, nach dem bestehenden `vorlauf_loeschen`-Endpoint (nach Zeile ~178) und VOR dem `# Endlauf, Position bearbeiten`-Kommentar, einfuegen:

```python
# =============================================================================
# Workflow: Zur Pruefung, Freigeben, Einspruch, Genehmigen, Ablehnen
# =============================================================================

@provision_api.route('/vorlauf/<int:lauf_id>/zur-pruefung', methods=['POST'])
@login_required
def zur_pruefung(lauf_id):
    """POST /api/provision/vorlauf/<id>/zur-pruefung — VORLAUF -> ZUR_PRUEFUNG. Nur Vollzugriff."""
    if not _has_provision_vollzugriff():
        return jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if (lauf['status'] or '').upper() != 'VORLAUF':
            return jsonify({'success': False, 'error': f'Nur aus Status VORLAUF moeglich (aktuell: {lauf["status"]}).'}), 400
        cur.execute("""
            UPDATE provision_laeufe SET
                status = 'ZUR_PRUEFUNG',
                pruefung_am = NOW() AT TIME ZONE 'Europe/Berlin',
                pruefung_von = %s,
                einspruch_text = NULL, einspruch_von = NULL, einspruch_am = NULL
            WHERE id = %s
        """, (_get_username(), lauf_id))
        conn.commit()
    return jsonify({'success': True, 'message': 'Zur Pruefung gesendet.'})


@provision_api.route('/vorlauf/<int:lauf_id>/freigeben', methods=['POST'])
@login_required
def freigeben(lauf_id):
    """POST /api/provision/vorlauf/<id>/freigeben — ZUR_PRUEFUNG -> FREIGEGEBEN. Eigener VK oder Vollzugriff."""
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status, verkaufer_id FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if not _may_act_on_own_lauf(lauf['verkaufer_id']):
            return jsonify({'success': False, 'error': 'Keine Berechtigung (nur eigener Lauf oder Vollzugriff).'}), 403
        if (lauf['status'] or '').upper() != 'ZUR_PRUEFUNG':
            return jsonify({'success': False, 'error': f'Nur aus Status ZUR_PRUEFUNG moeglich (aktuell: {lauf["status"]}).'}), 400
        cur.execute("""
            UPDATE provision_laeufe SET
                status = 'FREIGEGEBEN',
                freigegeben_am = NOW() AT TIME ZONE 'Europe/Berlin',
                freigegeben_von = %s
            WHERE id = %s
        """, (_get_username(), lauf_id))
        conn.commit()
    return jsonify({'success': True, 'message': 'Vorlauf freigegeben.'})


@provision_api.route('/vorlauf/<int:lauf_id>/einspruch', methods=['POST'])
@login_required
def einspruch(lauf_id):
    """POST /api/provision/vorlauf/<id>/einspruch — ZUR_PRUEFUNG -> VORLAUF. Pflicht-Text."""
    data = request.get_json() or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Begruendung ist ein Pflichtfeld.'}), 400
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status, verkaufer_id FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if not _may_act_on_own_lauf(lauf['verkaufer_id']):
            return jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403
        if (lauf['status'] or '').upper() != 'ZUR_PRUEFUNG':
            return jsonify({'success': False, 'error': f'Einspruch nur aus Status ZUR_PRUEFUNG moeglich (aktuell: {lauf["status"]}).'}), 400
        cur.execute("""
            UPDATE provision_laeufe SET
                status = 'VORLAUF',
                einspruch_text = %s,
                einspruch_von = %s,
                einspruch_am = NOW() AT TIME ZONE 'Europe/Berlin'
            WHERE id = %s
        """, (text, _get_username(), lauf_id))
        conn.commit()
    return jsonify({'success': True, 'message': 'Einspruch gesendet.'})


@provision_api.route('/vorlauf/<int:lauf_id>/genehmigen', methods=['POST'])
@login_required
def genehmigen(lauf_id):
    """POST /api/provision/vorlauf/<id>/genehmigen — FREIGEGEBEN -> GENEHMIGT. Nur Genehmiger."""
    if not _is_genehmiger():
        return jsonify({'success': False, 'error': 'Nur Anton Suess oder Florian Greiner duerfen genehmigen.'}), 403
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if (lauf['status'] or '').upper() != 'FREIGEGEBEN':
            return jsonify({'success': False, 'error': f'Nur aus Status FREIGEGEBEN moeglich (aktuell: {lauf["status"]}).'}), 400
        cur.execute("""
            UPDATE provision_laeufe SET
                status = 'GENEHMIGT',
                genehmigt_am = NOW() AT TIME ZONE 'Europe/Berlin',
                genehmigt_von = %s
            WHERE id = %s
        """, (_get_username(), lauf_id))
        conn.commit()
    return jsonify({'success': True, 'message': 'Vorlauf genehmigt.'})


@provision_api.route('/vorlauf/<int:lauf_id>/ablehnen', methods=['POST'])
@login_required
def ablehnen(lauf_id):
    """POST /api/provision/vorlauf/<id>/ablehnen — FREIGEGEBEN -> VORLAUF. Nur Genehmiger. Pflicht-Text."""
    if not _is_genehmiger():
        return jsonify({'success': False, 'error': 'Nur Anton Suess oder Florian Greiner duerfen ablehnen.'}), 403
    data = request.get_json() or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Begruendung ist ein Pflichtfeld.'}), 400
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, status FROM provision_laeufe WHERE id = %s", (lauf_id,))
        lauf = cur.fetchone()
        if not lauf:
            return jsonify({'success': False, 'error': 'Lauf nicht gefunden.'}), 404
        if (lauf['status'] or '').upper() != 'FREIGEGEBEN':
            return jsonify({'success': False, 'error': f'Ablehnung nur aus Status FREIGEGEBEN moeglich (aktuell: {lauf["status"]}).'}), 400
        cur.execute("""
            UPDATE provision_laeufe SET
                status = 'VORLAUF',
                einspruch_text = %s,
                einspruch_von = %s,
                einspruch_am = NOW() AT TIME ZONE 'Europe/Berlin'
            WHERE id = %s
        """, (text, _get_username(), lauf_id))
        conn.commit()
    return jsonify({'success': True, 'message': 'Vorlauf abgelehnt.'})
```

- [ ] **Step 3: Endlauf-Bedingung aendern**

In `api/provision_api.py`, im bestehenden `endlauf_setzen`-Endpoint, die Status-Pruefung aendern. Finde:

```python
        if status != 'FREIGEGEBEN':
            return jsonify({'success': False, 'error': f'Endlauf nur aus Status FREIGEGEBEN möglich (aktuell: {status}).'}), 400
```

Ersetzen durch:

```python
        if status != 'GENEHMIGT':
            return jsonify({'success': False, 'error': f'Endlauf nur aus Status GENEHMIGT moeglich (aktuell: {status}).'}), 400
```

- [ ] **Step 4: Commit**

```bash
git add api/provision_api.py
git commit -m "feat(provision): 5 Workflow-Endpoints (zur-pruefung, freigeben, einspruch, genehmigen, ablehnen)"
```

---

### Task 3: Backend — get_lauf_detail um Einspruch-Felder und Workflow-Daten erweitern

**Files:**
- Modify: `api/provision_service.py`

Die Lauf-Query in `get_lauf_detail()` muss die neuen Einspruch-Felder zurueckgeben.

- [ ] **Step 1: Lauf-Query erweitern**

In `api/provision_service.py`, Funktion `get_lauf_detail()`, die SELECT-Query fuer den Lauf (ca. Zeile 656-663) erweitern. Finde:

```python
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                   summe_stueckpraemie, summe_gesamt,
                   vorlauf_am, vorlauf_von, pdf_vorlauf, pdf_endlauf,
                   endlauf_am, endlauf_von, belegnummer
            FROM provision_laeufe WHERE id = %s
```

Ersetzen durch:

```python
            SELECT id, verkaufer_id, verkaufer_name, abrechnungsmonat, status,
                   summe_kat_i, summe_kat_ii, summe_kat_iii, summe_kat_iv, summe_kat_v,
                   summe_stueckpraemie, summe_gesamt,
                   vorlauf_am, vorlauf_von, pdf_vorlauf, pdf_endlauf,
                   pruefung_am, pruefung_von,
                   freigegeben_am, freigegeben_von,
                   genehmigt_am, genehmigt_von,
                   endlauf_am, endlauf_von, belegnummer,
                   einspruch_text, einspruch_von, einspruch_am
            FROM provision_laeufe WHERE id = %s
```

- [ ] **Step 2: Commit**

```bash
git add api/provision_service.py
git commit -m "feat(provision): Lauf-Detail um Workflow- und Einspruch-Felder erweitern"
```

---

### Task 4: Backend — Detail-Route fuer eigenen Lauf oeffnen

**Files:**
- Modify: `routes/provision_routes.py`

Verkaeufer muessen die Detail-Seite ihres eigenen Laufs oeffnen koennen (fuer Pruefung/Freigabe). Die Route hat aktuell keine Einschraenkung — der Schutz liegt in der API. Das ist bereits OK. Aber wir muessen sicherstellen, dass ein Verkaeufer den Link zur Detail-Seite findet.

- [ ] **Step 1: Keine Aenderung an der Route noetig**

Die Route `/detail/<lauf_id>` hat nur `@login_required` und kein Feature-Check — die API prueft den VKB-Zugriff. Das reicht, weil die API nur Daten liefert wenn der User berechtigt ist.

- [ ] **Step 2: Commit (nur wenn Aenderungen)**

Kein Commit noetig — Route ist bereits korrekt.

---

### Task 5: Frontend — Detail-Seite Workflow-Buttons und Einspruch-Modal

**Files:**
- Modify: `templates/provision/provision_detail.html`

Statusabhaengige Workflow-Buttons, Einspruch-Warnbox, Einspruch/Ablehnung-Modal mit Pflicht-Textarea.

- [ ] **Step 1: Neue JS-Variablen fuer Workflow-Berechtigung**

Im `<script>`-Block, nach den bestehenden `pvProvisionVollzugriff`/`pvUserCan*`-Variablen, hinzufuegen:

```javascript
    var pvIsGenehmiger = {% if current_user.username in ('anton.suess@auto-greiner.de', 'florian.greiner@auto-greiner.de') %}true{% else %}false{% endif %};
```

- [ ] **Step 2: Einspruch-Modal HTML einfuegen**

Nach dem bestehenden ZL-Modal und vor dem `<script>`-Tag, einfuegen:

```html
<!-- Modal: Einspruch / Ablehnung -->
<div class="modal fade" id="einspruchModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content modal-edit">
            <div class="modal-header py-2" style="background:#fef3c7; border-bottom:1px solid #fbbf24;">
                <h5 class="modal-title" style="font-size:.95rem; font-weight:700;" id="einspruchModalTitle">Einspruch</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p class="text-muted small" id="einspruchModalHint">Bitte begründen Sie Ihren Einspruch. Dieses Feld ist ein Pflichtfeld.</p>
                <textarea class="form-control" id="einspruchText" rows="4" placeholder="Begründung (Pflichtfeld)..." maxlength="2000"></textarea>
                <div class="form-text text-danger" id="einspruchError" style="display:none;">Bitte Begründung eingeben.</div>
            </div>
            <div class="modal-footer py-2" style="border-top:1px solid #e2e8f0;">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal">Abbrechen</button>
                <button type="button" class="btn btn-sm btn-warning" id="btnEinspruchSend" disabled><i class="bi bi-exclamation-triangle"></i> <span id="btnEinspruchLabel">Einspruch senden</span></button>
            </div>
        </div>
    </div>
</div>
```

- [ ] **Step 3: Workflow-Buttons im Main Data Load einfuegen**

Im JS-Block, nach der Summentabelle und vor dem "Vorlauf löschen button"-Abschnitt, die Workflow-Buttons statusabhaengig einfuegen. Finde:

```javascript
        // Vorlauf löschen button
```

Davor einfuegen:

```javascript
        // ── Workflow-Buttons ──
        var wfArea = document.createElement('div');
        wfArea.className = 'mt-3 mb-3';
        wfArea.id = 'workflowArea';
        document.getElementById('katAccordion').parentNode.insertBefore(wfArea, document.getElementById('summenTabelle'));

        // Einspruch-Warnbox (wenn einspruch_text vorhanden und Status = VORLAUF)
        if (statusUpper === 'VORLAUF' && l.einspruch_text) {
            var warnHtml = '<div class="alert alert-warning d-flex align-items-start gap-2 mb-3" style="border-radius:12px;">';
            warnHtml += '<i class="bi bi-exclamation-triangle-fill mt-1" style="font-size:1.2rem;"></i>';
            warnHtml += '<div><strong>Einspruch/Ablehnung</strong> von ' + escapeHtml(l.einspruch_von || '--') + ' am ' + (l.einspruch_am ? new Date(l.einspruch_am).toLocaleDateString('de-DE') : '--') + ':<br>';
            warnHtml += '<span class="mt-1 d-block">' + escapeHtml(l.einspruch_text) + '</span></div></div>';
            wfArea.innerHTML += warnHtml;
        }

        // Workflow-Buttons je nach Status
        var wfBtns = '';

        if (statusUpper === 'VORLAUF' && pvProvisionVollzugriff) {
            wfBtns += '<button class="btn-action btn-action-primary me-2" id="btnZurPruefung"><i class="bi bi-send"></i> Zur Prüfung senden</button>';
        }

        if (statusUpper === 'ZUR_PRUEFUNG') {
            // Verkaeufer (eigener Lauf) oder Vollzugriff-User koennen freigeben/einspruch
            var myVkb = {{ current_user.employee_data.locosoft_id if current_user.employee_data and current_user.employee_data.locosoft_id else 'null' }};
            var isOwnLauf = (myVkb !== null && myVkb === l.verkaufer_id) || pvProvisionVollzugriff;
            if (isOwnLauf) {
                wfBtns += '<button class="btn-action btn-action-success me-2" id="btnFreigeben"><i class="bi bi-check-circle"></i> Freigeben</button>';
                wfBtns += '<button class="btn-action btn-action-danger" id="btnEinspruch"><i class="bi bi-exclamation-triangle"></i> Einspruch</button>';
            }
        }

        if (statusUpper === 'FREIGEGEBEN') {
            if (pvIsGenehmiger) {
                wfBtns += '<button class="btn-action btn-action-success me-2" id="btnGenehmigen"><i class="bi bi-check-circle"></i> Genehmigen</button>';
                wfBtns += '<button class="btn-action btn-action-danger" id="btnAblehnen"><i class="bi bi-x-circle"></i> Ablehnen</button>';
            } else if (pvProvisionVollzugriff) {
                wfBtns += '<div class="alert alert-info py-2 px-3 d-inline-block" style="border-radius:8px; font-size:.85rem;"><i class="bi bi-hourglass-split"></i> Wartet auf Genehmigung durch Anton Süß oder Florian Greiner</div>';
            }
        }

        if (statusUpper === 'GENEHMIGT' && pvProvisionVollzugriff) {
            // Endlauf-Formular wird unten angezeigt (bestehender Code)
            wfBtns += '<div class="alert alert-success py-2 px-3 d-inline-block" style="border-radius:8px; font-size:.85rem;"><i class="bi bi-check-circle-fill"></i> Genehmigt — Endlauf kann erstellt werden</div>';
        }

        if (wfBtns) {
            wfArea.innerHTML += '<div class="d-flex flex-wrap align-items-center gap-2">' + wfBtns + '</div>';
        }

        // Workflow-Button Event Listeners
        var btnZP = document.getElementById('btnZurPruefung');
        if (btnZP) {
            btnZP.addEventListener('click', function() {
                if (!confirm('Vorlauf zur Prüfung an den Verkäufer senden?')) return;
                btnZP.disabled = true;
                fetch('/api/provision/vorlauf/' + id + '/zur-pruefung', {method:'POST', credentials:'same-origin'})
                .then(function(r){return r.json();})
                .then(function(res){ if(res.success) window.location.reload(); else { alert(res.error||'Fehler'); btnZP.disabled=false; }});
            });
        }

        var btnFG = document.getElementById('btnFreigeben');
        if (btnFG) {
            btnFG.addEventListener('click', function() {
                if (!confirm('Vorlauf freigeben?')) return;
                btnFG.disabled = true;
                fetch('/api/provision/vorlauf/' + id + '/freigeben', {method:'POST', credentials:'same-origin'})
                .then(function(r){return r.json();})
                .then(function(res){ if(res.success) window.location.reload(); else { alert(res.error||'Fehler'); btnFG.disabled=false; }});
            });
        }

        var btnGM = document.getElementById('btnGenehmigen');
        if (btnGM) {
            btnGM.addEventListener('click', function() {
                if (!confirm('Vorlauf genehmigen?')) return;
                btnGM.disabled = true;
                fetch('/api/provision/vorlauf/' + id + '/genehmigen', {method:'POST', credentials:'same-origin'})
                .then(function(r){return r.json();})
                .then(function(res){ if(res.success) window.location.reload(); else { alert(res.error||'Fehler'); btnGM.disabled=false; }});
            });
        }

        // Einspruch-Modal oeffnen
        var btnES = document.getElementById('btnEinspruch');
        if (btnES) {
            btnES.addEventListener('click', function() {
                document.getElementById('einspruchModalTitle').textContent = 'Einspruch einlegen';
                document.getElementById('einspruchModalHint').textContent = 'Bitte begründen Sie Ihren Einspruch. Dieses Feld ist ein Pflichtfeld.';
                document.getElementById('btnEinspruchLabel').textContent = 'Einspruch senden';
                document.getElementById('einspruchText').value = '';
                document.getElementById('btnEinspruchSend').className = 'btn btn-sm btn-warning';
                document.getElementById('btnEinspruchSend').setAttribute('data-action', 'einspruch');
                bootstrap.Modal.getOrCreateInstance(document.getElementById('einspruchModal')).show();
            });
        }

        // Ablehnen-Modal oeffnen (nutzt dasselbe Modal)
        var btnAB = document.getElementById('btnAblehnen');
        if (btnAB) {
            btnAB.addEventListener('click', function() {
                document.getElementById('einspruchModalTitle').textContent = 'Vorlauf ablehnen';
                document.getElementById('einspruchModalHint').textContent = 'Bitte begründen Sie die Ablehnung. Dieses Feld ist ein Pflichtfeld.';
                document.getElementById('btnEinspruchLabel').textContent = 'Ablehnen';
                document.getElementById('einspruchText').value = '';
                document.getElementById('btnEinspruchSend').className = 'btn btn-sm btn-danger';
                document.getElementById('btnEinspruchSend').setAttribute('data-action', 'ablehnen');
                bootstrap.Modal.getOrCreateInstance(document.getElementById('einspruchModal')).show();
            });
        }
```

- [ ] **Step 4: Einspruch-Modal Logik (Textarea Pflicht + Senden)**

Im JS-Block, nach den Workflow-Button-Listeners und vor dem Endlauf-Formular-Code, einfuegen:

```javascript
        // Einspruch/Ablehnung Textarea Pflicht-Validierung
        document.getElementById('einspruchText').addEventListener('input', function() {
            var hasText = this.value.trim().length > 0;
            document.getElementById('btnEinspruchSend').disabled = !hasText;
            document.getElementById('einspruchError').style.display = hasText ? 'none' : 'block';
        });

        // Einspruch/Ablehnung senden
        document.getElementById('btnEinspruchSend').addEventListener('click', function() {
            var text = document.getElementById('einspruchText').value.trim();
            if (!text) { document.getElementById('einspruchError').style.display = 'block'; return; }
            var action = this.getAttribute('data-action'); // 'einspruch' oder 'ablehnen'
            var btn = this;
            btn.disabled = true;
            var url = '/api/provision/vorlauf/' + id + '/' + action;
            fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin', body:JSON.stringify({text: text})})
            .then(function(r){return r.json();})
            .then(function(res){
                if(res.success) window.location.reload();
                else { alert(res.error||'Fehler'); btn.disabled=false; }
            });
        });
```

- [ ] **Step 5: Endlauf-Formular Bedingung aendern**

Finde im JS:

```javascript
        if (statusUpper === 'FREIGEGEBEN' && pvUserCanEndlauf) {
```

Ersetzen durch:

```javascript
        if (statusUpper === 'GENEHMIGT' && pvUserCanEndlauf) {
```

- [ ] **Step 6: Status-Badge Farben erweitern**

Finde im JS:

```javascript
        if (statusUpper === 'VORLAUF') statusEl.className = 'status-badge status-vorlauf ms-2';
        else if (statusUpper === 'FREIGEGEBEN') statusEl.className = 'status-badge status-freigegeben ms-2';
        else if (statusUpper === 'ENDLAUF') statusEl.className = 'status-badge status-endlauf ms-2';
```

Ersetzen durch:

```javascript
        if (statusUpper === 'VORLAUF') statusEl.className = 'status-badge status-vorlauf ms-2';
        else if (statusUpper === 'ZUR_PRUEFUNG') statusEl.className = 'status-badge status-zurpruefung ms-2';
        else if (statusUpper === 'FREIGEGEBEN') statusEl.className = 'status-badge status-freigegeben ms-2';
        else if (statusUpper === 'GENEHMIGT') statusEl.className = 'status-badge status-genehmigt ms-2';
        else if (statusUpper === 'ENDLAUF') statusEl.className = 'status-badge status-endlauf ms-2';
```

Und im `<style>`-Block die neuen CSS-Klassen hinzufuegen (nach `.status-endlauf`):

```css
    .status-zurpruefung { background: #fed7aa; color: #9a3412; }
    .status-genehmigt { background: #ccfbf1; color: #0f766e; }
```

- [ ] **Step 7: Bearbeitung nur bei VORLAUF erlauben**

Aktuell ist `pvEditable = statusUpper !== 'ENDLAUF' && pvUserCanEdit`. Das erlaubt Bearbeitung auch bei ZUR_PRUEFUNG/FREIGEGEBEN/GENEHMIGT. Fuer den Workflow soll Bearbeitung nur bei VORLAUF moeglich sein:

Finde:

```javascript
        var pvEditable = statusUpper !== 'ENDLAUF' && pvUserCanEdit;
```

Ersetzen durch:

```javascript
        var pvEditable = statusUpper === 'VORLAUF' && pvUserCanEdit;
```

- [ ] **Step 8: Commit**

```bash
git add templates/provision/provision_detail.html
git commit -m "feat(provision): Workflow-UI (Buttons, Einspruch-Modal, Status-Badges)"
```

---

### Task 6: Frontend — Dashboard Status-Badge-Farben erweitern

**Files:**
- Modify: `templates/provision/provision_dashboard.html`

- [ ] **Step 1: Status-Badge CSS/Logik im Dashboard erweitern**

Im Dashboard-Template nach den bestehenden Status-Badge-Zuweisungen suchen (bg-secondary, bg-info, bg-success) und ZUR_PRUEFUNG + GENEHMIGT hinzufuegen. Die genaue Stelle haengt vom Template ab — suche nach `status` Badge-Logik und stelle sicher, dass:

- ZUR_PRUEFUNG: orange Badge (`background: #fed7aa; color: #9a3412;`)
- GENEHMIGT: tuerkis Badge (`background: #ccfbf1; color: #0f766e;`)

- [ ] **Step 2: Commit**

```bash
git add templates/provision/provision_dashboard.html
git commit -m "feat(provision): Dashboard Status-Badges fuer ZUR_PRUEFUNG und GENEHMIGT"
```

---

### Task 7: Restart und E2E-Test

- [ ] **Step 1: Service neustarten**

```bash
sudo -n /usr/bin/systemctl restart greiner-test
```

- [ ] **Step 2: Workflow durchspielen**

1. Lauf 39 (Daniel Fialkowski, VORLAUF) oeffnen
2. "Zur Prüfung senden" klicken -> Status wird ZUR_PRUEFUNG
3. "Freigeben" klicken (als Vollzugriff-Test) -> Status wird FREIGEGEBEN
4. "Genehmigen" klicken (als Florian Greiner) -> Status wird GENEHMIGT
5. "Endlauf erstellen" -> Status wird ENDLAUF

Auch testen:
- Einspruch mit Pflicht-Text (leeres Feld -> Button deaktiviert)
- Ablehnung mit Pflicht-Text
- Einspruch-Warnbox erscheint nach Zurueckweisung

- [ ] **Step 3: Commit falls Fixes noetig**

```bash
git add -A && git commit -m "fix(provision): Workflow E2E-Fixes"
```
