/**
 * Einkaufsfinanzierung Frontend
 * Modern JavaScript (ES6+) mit Chart.js
 */

// Global Charts
let chartInstitute = null;
let chartMarken = null;

// Initialisierung beim Laden
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    
    // Refresh Button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadData();
    });
});

/**
 * Hauptfunktion: Daten laden
 */
async function loadData() {
    try {
        showLoading();
        
        const response = await fetch('/api/bankenspiegel/einkaufsfinanzierung');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unbekannter Fehler');
        }
        
        // UI aktualisieren
        updateKPIs(data.gesamt, data.warnungen.length);
        updateInstituteCards(data.institute);
        updateCharts(data.institute);
        updateTopFahrzeuge(data.top_fahrzeuge);
        updateWarnungen(data.warnungen);
        
        // Timestamp
        const timestamp = new Date(data.timestamp);
        document.getElementById('lastUpdate').textContent = 
            `Stand: ${timestamp.toLocaleString('de-DE')}`;
        
        showContent();
        
    } catch (error) {
        console.error('Fehler beim Laden:', error);
        showError(error.message);
    }
}

/**
 * KPI Cards aktualisieren
 */
function updateKPIs(gesamt, anzahlWarnungen) {
    document.getElementById('kpiGesamtFahrzeuge').textContent = gesamt.anzahl_fahrzeuge;
    
    document.getElementById('kpiFinanzierung').textContent = 
        formatCurrency(gesamt.finanzierung);
    document.getElementById('kpiOriginal').textContent = 
        `von ${formatCurrency(gesamt.original)}`;
    
    document.getElementById('kpiAbbezahlt').textContent = 
        formatCurrency(gesamt.abbezahlt);
    document.getElementById('abbezahltProgress').style.width = 
        `${gesamt.abbezahlt_prozent}%`;
    document.getElementById('abbezahltProgress').textContent = 
        `${gesamt.abbezahlt_prozent}%`;
    
    document.getElementById('kpiWarnungen').textContent = anzahlWarnungen;
}

/**
 * Institute Cards dynamisch erstellen
 */
function updateInstituteCards(institute) {
    const container = document.getElementById('instituteCards');
    container.innerHTML = '';
    
    institute.forEach(institut => {
        const card = document.createElement('div');
        card.className = 'col-lg-6';
        
        const color = institut.name === 'Stellantis' ? 'primary' : 'info';
        const icon = institut.name === 'Stellantis' ? 'lightning-charge-fill' : 'bank';
        
        card.innerHTML = `
            <div class="card institut-card border-${color}">
                <div class="card-header bg-${color} bg-opacity-10">
                    <h5 class="mb-0">
                        <i class="bi bi-${icon} text-${color} me-2"></i>
                        ${institut.name} Bank
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <i class="bi bi-car-front text-muted" style="font-size: 1.5rem;"></i>
                                </div>
                                <div>
                                    <p class="text-muted small mb-0">Fahrzeuge</p>
                                    <h4 class="mb-0">${institut.anzahl}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <i class="bi bi-wallet2 text-muted" style="font-size: 1.5rem;"></i>
                                </div>
                                <div>
                                    <p class="text-muted small mb-0">Finanzierung</p>
                                    <h4 class="mb-0">${formatCurrencyShort(institut.finanzierung)}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <i class="bi bi-graph-up text-success" style="font-size: 1.5rem;"></i>
                                </div>
                                <div>
                                    <p class="text-muted small mb-0">Abbezahlt</p>
                                    <h5 class="mb-0 text-success">
                                        ${formatCurrencyShort(institut.abbezahlt)}
                                        <small>(${((institut.abbezahlt / institut.original) * 100).toFixed(1)}%)</small>
                                    </h5>
                                </div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <div class="me-3">
                                    <i class="bi bi-calculator text-muted" style="font-size: 1.5rem;"></i>
                                </div>
                                <div>
                                    <p class="text-muted small mb-0">Ø pro Fahrzeug</p>
                                    <h5 class="mb-0">${formatCurrencyShort(institut.durchschnitt)}</h5>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    ${institut.marken.length > 0 ? `
                    <hr class="my-3">
                    <div>
                        <p class="text-muted small mb-2"><strong>Marken:</strong></p>
                        <div class="d-flex flex-wrap gap-2">
                            ${institut.marken.map(marke => `
                                <span class="badge bg-${color} bg-opacity-25 text-${color} border border-${color}">
                                    ${marke.name}: ${marke.anzahl} Fzg.
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${institut.aeltestes ? `
                    <div class="mt-2">
                        <small class="text-muted">
                            <i class="bi bi-clock-history"></i>
                            Ältestes Fahrzeug: ${institut.aeltestes} Tage im Bestand
                        </small>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

/**
 * Charts aktualisieren
 */
function updateCharts(institute) {
    // 1. Institute Pie Chart
    const instituteData = {
        labels: institute.map(i => i.name),
        datasets: [{
            data: institute.map(i => i.finanzierung),
            backgroundColor: [
                'rgba(156, 39, 176, 0.8)',  // Stellantis: Lila
                'rgba(3, 169, 244, 0.8)'    // Santander: Blau
            ],
            borderColor: [
                'rgb(156, 39, 176)',
                'rgb(3, 169, 244)'
            ],
            borderWidth: 2
        }]
    };
    
    if (chartInstitute) {
        chartInstitute.destroy();
    }
    
    const ctxInstitute = document.getElementById('chartInstitute').getContext('2d');
    chartInstitute = new Chart(ctxInstitute, {
        type: 'pie',
        data: instituteData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatCurrency(context.parsed);
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // 2. Marken Bar Chart
    const markenLabels = [];
    const markenData = [];
    const markenColors = [];
    
    institute.forEach((institut, idx) => {
        const color = idx === 0 ? 'rgba(156, 39, 176, 0.8)' : 'rgba(3, 169, 244, 0.8)';
        
        institut.marken.forEach(marke => {
            markenLabels.push(`${marke.name} (${institut.name})`);
            markenData.push(marke.anzahl);
            markenColors.push(color);
        });
    });
    
    if (chartMarken) {
        chartMarken.destroy();
    }
    
    const ctxMarken = document.getElementById('chartMarken').getContext('2d');
    chartMarken = new Chart(ctxMarken, {
        type: 'bar',
        data: {
            labels: markenLabels,
            datasets: [{
                label: 'Anzahl Fahrzeuge',
                data: markenData,
                backgroundColor: markenColors,
                borderColor: markenColors.map(c => c.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 10
                    }
                }
            }
        }
    });
}

/**
 * Top Fahrzeuge Tabelle
 */
function updateTopFahrzeuge(fahrzeuge) {
    const tbody = document.getElementById('topFahrzeugeTable');
    tbody.innerHTML = '';
    
    fahrzeuge.forEach((fz, index) => {
        const row = document.createElement('tr');
        
        const badge = fz.institut === 'Stellantis' ? 'primary' : 'info';
        
        row.innerHTML = `
            <td><strong>${index + 1}</strong></td>
            <td><span class="badge bg-${badge}">${fz.institut}</span></td>
            <td><code>${fz.vin}</code></td>
            <td>${fz.modell || '-'}</td>
            <td>${fz.marke || '-'}</td>
            <td class="text-end"><strong>${formatCurrency(fz.saldo)}</strong></td>
            <td class="text-end text-muted">${formatCurrency(fz.original)}</td>
            <td class="text-end">${fz.alter || '-'} Tage</td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Warnungen Tabelle
 */
function updateWarnungen(warnungen) {
    if (warnungen.length === 0) {
        document.getElementById('warnungenSection').classList.add('d-none');
        return;
    }
    
    document.getElementById('warnungenSection').classList.remove('d-none');
    
    const tbody = document.getElementById('warnungenTable');
    tbody.innerHTML = '';
    
    warnungen.forEach(warnung => {
        const row = document.createElement('tr');
        
        const badgeColor = warnung.kritisch ? 'danger' : 'warning';
        const tageClass = warnung.kritisch ? 'text-danger fw-bold' : 'text-warning';
        
        row.innerHTML = `
            <td><span class="badge bg-primary">Stellantis</span></td>
            <td><code>${warnung.vin}</code></td>
            <td>${warnung.modell || '-'}</td>
            <td class="${tageClass}">
                <i class="bi bi-exclamation-triangle-fill"></i>
                ${warnung.tage_uebrig} Tage
                ${warnung.kritisch ? '<span class="badge bg-danger ms-1">KRITISCH</span>' : ''}
            </td>
            <td class="text-end">${formatCurrency(warnung.saldo)}</td>
            <td class="text-end text-muted">${warnung.alter} Tage</td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Währung formatieren
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

/**
 * Währung kurz formatieren (1.234.567 → 1,23M)
 */
function formatCurrencyShort(amount) {
    if (amount >= 1000000) {
        return `${(amount / 1000000).toFixed(2)}M €`;
    } else if (amount >= 1000) {
        return `${(amount / 1000).toFixed(0)}K €`;
    }
    return formatCurrency(amount);
}

/**
 * UI Zustand: Loading
 */
function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('mainContent').classList.add('d-none');
    document.getElementById('errorAlert').classList.add('d-none');
}

/**
 * UI Zustand: Content
 */
function showContent() {
    document.getElementById('loadingSpinner').classList.add('d-none');
    document.getElementById('mainContent').classList.remove('d-none');
    document.getElementById('errorAlert').classList.add('d-none');
}

/**
 * UI Zustand: Error
 */
function showError(message) {
    document.getElementById('loadingSpinner').classList.add('d-none');
    document.getElementById('mainContent').classList.add('d-none');
    document.getElementById('errorAlert').classList.remove('d-none');
    document.getElementById('errorMessage').textContent = message;
}
