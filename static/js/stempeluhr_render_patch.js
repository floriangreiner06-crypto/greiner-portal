/* ============================================================================
 * JavaScript PATCH für werkstatt_stempeluhr.html - TAG 101 v2
 * ============================================================================
 * 
 * Aktualisierte renderAktiveMechaniker() Funktion mit Cross-Betrieb Support
 * 
 * ANWENDUNG:
 * 1. CSS einbinden: <link rel="stylesheet" href="/static/css/stempeluhr_cross_betrieb.css">
 * 2. Die renderAktiveMechaniker() Funktion im {% block scripts %} ersetzen
 * ============================================================================
 */

function renderAktiveMechaniker(data) {
    const container = document.getElementById('aktivContainer');
    const aktive = data.aktive_mechaniker || [];
    
    if (aktive.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-person-x fs-1"></i>
                <p class="mt-2">Keine aktiven Stempelungen</p>
                ${data.filter && data.filter.hinweis ? `<small class="text-info">${data.filter.hinweis}</small>` : ''}
            </div>`;
        return;
    }
    
    let html = '<div class="row">';
    
    aktive.forEach(m => {
        // Status-Klasse basierend auf Fortschritt
        let statusClass = 'status-aktiv';
        let avatarClass = 'avatar-aktiv';
        if (m.fortschritt_prozent >= 100) {
            statusClass = 'status-kritisch';
            avatarClass = 'avatar-kritisch';
        } else if (m.fortschritt_prozent >= 75) {
            statusClass = 'status-warnung';
            avatarClass = 'avatar-warnung';
        }
        
        // NEU: Cross-Betrieb Markierung (z.B. Stellantis-MA an Hyundai-Auftrag)
        const crossBetriebClass = m.cross_betrieb ? 'cross-betrieb' : '';
        const crossBetriebBadge = m.cross_betrieb 
            ? `<span class="cross-betrieb-badge ${m.auftrag_betrieb === 2 ? 'hyundai' : ''}" 
                     title="Mitarbeiter von ${m.betrieb_name}, arbeitet an ${m.auftrag_betrieb_name}-Auftrag">
                 ${m.auftrag_betrieb_name}
               </span>` 
            : '';
        
        // Initialen aus Name (Format: "Nachname,Vorname")
        const nameParts = (m.name || '').split(',');
        const initialen = nameParts.length >= 2 
            ? (nameParts[1].trim()[0] || '') + (nameParts[0].trim()[0] || '')
            : (m.name || '?').substring(0, 2).toUpperCase();
        
        // Fortschrittsbalken-Farbe
        let progressClass = 'bg-success';
        if (m.fortschritt_prozent >= 100) progressClass = 'bg-danger';
        else if (m.fortschritt_prozent >= 75) progressClass = 'bg-warning';
        
        // Vorgabe-Anzeige
        const vorgabeText = m.vorgabe_aw > 0 
            ? `${m.vorgabe_aw} AW (${m.vorgabe_min} min)` 
            : 'Keine Vorgabe';
        
        // ML-Vorhersage (falls vorhanden)
        const mlInfo = mlPredictions[m.order_number];
        const mlBadge = mlInfo && mlInfo.ml_status === 'unterbewertet'
            ? `<span class="badge bg-warning text-dark ms-1" title="ML: ${mlInfo.ml_vorhersage_aw} AW erwartet">
                 <i class="bi bi-robot"></i> +${mlInfo.ml_potenzial_aw} AW
               </span>`
            : '';
        
        html += `
        <div class="col-lg-4 col-md-6 mb-3">
            <div class="card mechaniker-card ${statusClass} ${crossBetriebClass}" 
                 onclick="showAuftragDetails(${m.order_number})">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="mechaniker-avatar ${avatarClass} me-3">
                            ${initialen}
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="mb-1">
                                ${m.name}
                                ${crossBetriebBadge}
                            </h6>
                            <div class="small text-muted mb-2">
                                <span class="betrieb-badge betrieb-${m.betrieb}">${m.betrieb_name}</span>
                                <span class="ms-2">MA ${m.employee_number}</span>
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="zeit-display text-${m.fortschritt_prozent >= 100 ? 'danger' : 'success'}">
                                ${m.laufzeit_min} min
                            </div>
                            <div class="small text-muted">seit ${m.start_uhrzeit}</div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <div class="d-flex justify-content-between small mb-1">
                            <span>
                                <i class="bi bi-file-text"></i> 
                                Auftrag ${m.order_number}
                                ${mlBadge}
                            </span>
                            <span>Vorgabe: ${vorgabeText}</span>
                        </div>
                        <div class="progress progress-custom">
                            <div class="progress-bar ${progressClass}" 
                                 style="width: ${Math.min(m.fortschritt_prozent, 100)}%">
                                ${m.fortschritt_prozent}%
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-2 small">
                        <span class="text-muted">
                            <i class="bi bi-car-front"></i> ${m.kennzeichen || '?'}
                        </span>
                        <span class="ms-2 text-muted">${m.marke || ''}</span>
                        ${m.serviceberater ? `
                            <span class="ms-2">
                                <i class="bi bi-person"></i> ${m.serviceberater}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>`;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    // Badge-Counts aktualisieren
    document.getElementById('countAktiv').textContent = aktive.length;
    document.getElementById('badgeAktiv').textContent = aktive.length;
}
