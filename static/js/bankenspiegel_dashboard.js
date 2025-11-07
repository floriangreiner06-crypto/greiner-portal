// Bankenspiegel Dashboard JavaScript
// Chart.js Integration für Visualisierungen

let umsatzChart = null;

// Formatierung von Beträgen
function formatBetrag(betrag) {
    if (betrag === null || betrag === undefined) return '0,00 €';
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(betrag);
}

// Formatierung von Zahlen
function formatZahl(zahl) {
    if (zahl === null || zahl === undefined) return '0';
    return new Intl.NumberFormat('de-DE').format(zahl);
}

// Formatierung von Datum
function formatDatum(datum) {
    if (!datum) return '-';
    const date = new Date(datum);
    return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Dashboard-Daten laden
async function loadDashboard() {
    try {
        const response = await fetch('/api/bankenspiegel/dashboard');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        
        // WICHTIG: API gibt data.dashboard zurück!
        const dashboardData = data.dashboard;
        
        // KPI Cards aktualisieren
        updateKPIs(dashboardData);
        
        // Chart aktualisieren
        updateChart(dashboardData);
        
        // Letzte Transaktionen laden
        loadLetzteTransaktionen();
        
    } catch (error) {
        console.error('Fehler beim Laden des Dashboards:', error);
        showError('Dashboard konnte nicht geladen werden');
    }
}

// KPI Cards aktualisieren
function updateKPIs(data) {
    // Gesamtsaldo
    const gesamtsaldo = data.gesamtsaldo || 0;
    const gesamtsaldoElement = document.getElementById('gesamtsaldo');
    gesamtsaldoElement.innerHTML = formatBetrag(gesamtsaldo);
    gesamtsaldoElement.className = gesamtsaldo >= 0 ? 'mb-0 text-success' : 'mb-0 text-danger';
    
    // Banken
    document.getElementById('anzahlBanken').innerHTML = formatZahl(data.anzahl_banken || 0);
    
    // Konten
    document.getElementById('anzahlKontenAktiv').innerHTML = formatZahl(data.anzahl_konten || 0);
    document.getElementById('anzahlKontenGesamt').innerHTML = formatZahl(data.anzahl_konten_gesamt || data.anzahl_konten || 0);
    
    // Transaktionen (letzte 30 Tage)
    const letzte30 = data.letzte_30_tage || {};
    document.getElementById('anzahlTransaktionen').innerHTML = formatZahl(letzte30.anzahl_transaktionen || 0);
    
    // Einnahmen/Ausgaben/Saldo (30 Tage)
    const einnahmen = letzte30.einnahmen || 0;
    const ausgaben = letzte30.ausgaben || 0;
    const saldo = letzte30.saldo || 0;
    
    document.getElementById('einnahmen30Tage').innerHTML = formatBetrag(einnahmen);
    document.getElementById('ausgaben30Tage').innerHTML = formatBetrag(Math.abs(ausgaben));
    
    const saldoElement = document.getElementById('saldo30Tage');
    saldoElement.innerHTML = formatBetrag(saldo);
    saldoElement.className = saldo >= 0 ? 'mb-0 text-success' : 'mb-0 text-danger';
    
    // Interne Transfers
    const interneTransfers = data.interne_transfers_30_tage || {};
    document.getElementById('interneTransfersAnzahl').innerHTML = formatZahl(interneTransfers.anzahl_transaktionen || 0);
    document.getElementById('interneTransfersVolumen').innerHTML = formatBetrag(interneTransfers.volumen || 0);
}

// Chart aktualisieren
function updateChart(data) {
    const letzte30 = data.letzte_30_tage || {};
    const einnahmen = Math.abs(letzte30.einnahmen || 0);
    const ausgaben = Math.abs(letzte30.ausgaben || 0);
    
    const ctx = document.getElementById('umsatzChart');
    
    // Alten Chart zerstören falls vorhanden
    if (umsatzChart) {
        umsatzChart.destroy();
    }
    
    // Neuen Chart erstellen
    umsatzChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Letzte 30 Tage'],
            datasets: [
                {
                    label: 'Einnahmen',
                    data: [einnahmen],
                    backgroundColor: 'rgba(25, 135, 84, 0.8)',
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Ausgaben',
                    data: [ausgaben],
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatBetrag(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatBetrag(value);
                        }
                    }
                }
            }
        }
    });
}

// Letzte Transaktionen laden
async function loadLetzteTransaktionen() {
    try {
        const response = await fetch('/api/bankenspiegel/transaktionen?limit=10&offset=0');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        const tbody = document.querySelector('#letzteTransaktionen tbody');
        
        if (!data.transaktionen || data.transaktionen.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-muted">
                        <i class="bi bi-inbox me-2"></i>Keine Transaktionen vorhanden
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = data.transaktionen.map(t => {
            const betrag = t.betrag || 0;
            const betragClass = betrag >= 0 ? 'text-success' : 'text-danger';
            const icon = betrag >= 0 ? '↑' : '↓';
            
            return `
                <tr>
                    <td class="text-muted">${formatDatum(t.buchungsdatum)}</td>
                    <td>
                        <small class="text-muted d-block">${t.bank_name || '-'}</small>
                        <small>${t.kontoname || t.iban || '-'}</small>
                    </td>
                    <td>
                        <div style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${t.verwendungszweck || '-'}
                        </div>
                    </td>
                    <td class="text-end ${betragClass} fw-bold">
                        ${icon} ${formatBetrag(Math.abs(betrag))}
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Fehler beim Laden der Transaktionen:', error);
        const tbody = document.querySelector('#letzteTransaktionen tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-circle me-2"></i>Fehler beim Laden
                </td>
            </tr>
        `;
    }
}

// Fehlermeldung anzeigen
function showError(message) {
    // Einfache Alert-Box (kann später durch Toast ersetzt werden)
    console.error('Dashboard Error:', message);
}

// Beim Laden der Seite Dashboard initialisieren
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    
    // Auto-Refresh alle 5 Minuten
    setInterval(loadDashboard, 5 * 60 * 1000);
});
