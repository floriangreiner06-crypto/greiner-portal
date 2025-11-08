// Verkauf Auftragseingang JavaScript
// Lädt Daten von REST API und befüllt Tabellen

const MONATSNAMEN = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
];

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    // Aktuellen Monat/Jahr setzen
    const now = new Date();
    document.getElementById('filterMonth').value = now.getMonth() + 1;
    document.getElementById('filterYear').value = now.getFullYear();
    
    // Daten laden
    loadData();
});

// Hauptfunktion: Daten von API laden
async function loadData() {
    const month = document.getElementById('filterMonth').value;
    const year = document.getElementById('filterYear').value;
    
    try {
        const response = await fetch(`/api/verkauf/auftragseingang?month=${month}&year=${year}`);
        
        if (!response.ok) {
            throw new Error('API Fehler');
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unbekannter Fehler');
        }
        
        // UI aktualisieren
        updateInfoBoxes(month, year);
        updateTableHeute(data.heute, data.summe_heute, data.alle_verkaeufer);
        updateTablePeriode(data.periode, data.summe_periode, data.alle_verkaeufer, month, year);
        
    } catch (error) {
        console.error('Fehler beim Laden:', error);
        showError(error.message);
    }
}

// Info-Boxen aktualisieren
function updateInfoBoxes(month, year) {
    const heute = new Date().toLocaleDateString('de-DE');
    document.getElementById('periodeInfo').textContent = `${MONATSNAMEN[month-1]} ${year}`;
    document.getElementById('heuteInfo').textContent = heute;
}

// Tabelle HEUTE befüllen
function updateTableHeute(heute, summe, alle_verkaeufer) {
    const tbody = document.querySelector('#tableHeute tbody');
    
    if (summe.gesamt === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted py-5">
                    <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                    Heute noch keine Aufträge erfasst
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    
    // Verkäufer durchgehen
    alle_verkaeufer.forEach(vk => {
        const vk_nr = vk.salesman_number;
        const vk_data = heute[vk_nr];
        
        // Nur Verkäufer mit Aufträgen heute anzeigen
        if (vk_data && vk_data.gesamt > 0) {
            html += `
                <tr>
                    <td class="fw-semibold">${vk_data.name}</td>
                    <td class="text-center">${vk_data.NW || '-'}</td>
                    <td class="text-center">${vk_data.GW || '-'}</td>
                    <td class="text-center fw-bold">${vk_data.gesamt}</td>
                </tr>
            `;
        }
    });
    
    // Summenzeile
    html += `
        <tr class="table-primary fw-bold">
            <td>SUMME HEUTE</td>
            <td class="text-center">${summe.NW}</td>
            <td class="text-center">${summe.GW}</td>
            <td class="text-center">${summe.gesamt}</td>
        </tr>
    `;
    
    tbody.innerHTML = html;
}

// Tabelle PERIODE befüllen
function updateTablePeriode(periode, summe, alle_verkaeufer, month, year) {
    const tbody = document.querySelector('#tablePeriode tbody');
    document.getElementById('periodeTitle').textContent = `(${MONATSNAMEN[month-1]} ${year})`;
    
    if (summe.gesamt === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted py-5">
                    <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                    Keine Aufträge in diesem Monat
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    
    // Alle Verkäufer anzeigen (sortiert nach Gesamt-Anzahl)
    const verkaufer_sortiert = alle_verkaeufer
        .map(vk => ({
            ...vk,
            data: periode[vk.salesman_number] || {gesamt: 0, NW: 0, GW: 0}
        }))
        .sort((a, b) => b.data.gesamt - a.data.gesamt);
    
    verkaufer_sortiert.forEach(vk => {
        const vk_data = vk.data;
        
        html += `
            <tr>
                <td class="fw-semibold">${vk.verkaufer_name}</td>
                <td class="text-center">${vk_data.NW || '-'}</td>
                <td class="text-center">${vk_data.GW || '-'}</td>
                <td class="text-center fw-bold">${vk_data.gesamt || '-'}</td>
            </tr>
        `;
    });
    
    // Summenzeile
    html += `
        <tr class="table-primary fw-bold">
            <td>SUMME ${MONATSNAMEN[month-1].toUpperCase()}</td>
            <td class="text-center">${summe.NW}</td>
            <td class="text-center">${summe.GW}</td>
            <td class="text-center">${summe.gesamt}</td>
        </tr>
    `;
    
    tbody.innerHTML = html;
}

// Fehler anzeigen
function showError(message) {
    const alert = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            <strong>Fehler:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alert);
}
