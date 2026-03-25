// TAG 67: Multi-Entity Dashboard
let showGesellschafter = false;
let zinskostenChart = null;
let liquiditaetChart = null;

document.addEventListener('DOMContentLoaded', function() {
    const toggleCheckbox = document.getElementById('showGesellschafter');
    if (toggleCheckbox) {
        toggleCheckbox.addEventListener('change', function() {
            showGesellschafter = this.checked;
            loadDashboardData();
        });
    }
    
    loadDashboardData();
    setInterval(loadDashboardData, 60000);
});

function loadDashboardData() {
    const apiUrl = showGesellschafter 
        ? '/controlling/api/overview?include_gesellschafter=true'
        : '/controlling/api/overview';

    fetchJson(apiUrl)
        .then(data => {
            updateKPIs(data);
            updateGesellschafterSection(data);
        })
        .catch(error => {
            console.error('Fehler beim Laden des Dashboard-Overview:', error);
            setKpiErrorState();
        });

    fetchJson('/controlling/api/trends')
        .then(data => {
            updateLiquiditaetChart(data);
            updateZinskostenChart(data);
        })
        .catch(error => console.error('Fehler beim Laden der Trends:', error));
}

function updateKPIs(data) {
    // Operative Liquidität
    const operativElement = document.getElementById('kpi-liquiditaet-operativ');
    if (operativElement && data.liquiditaet) {
        operativElement.textContent = formatCurrency(data.liquiditaet.operativ);
    }
    
    // Verfügbare Liquidität
    const verfuegbarElement = document.getElementById('kpi-liquiditaet-verfuegbar');
    if (verfuegbarElement && data.liquiditaet) {
        verfuegbarElement.textContent = formatCurrency(data.liquiditaet.verfuegbar);
    }
    
    // Kreditlinien
    const kreditlinienElement = document.getElementById('kpi-kreditlinien');
    if (kreditlinienElement && data.liquiditaet) {
        const freieLinien = data.liquiditaet.freie_linien ?? data.liquiditaet.kreditlinien ?? 0;
        kreditlinienElement.textContent = formatCurrency(freieLinien);
    }
    
    // Nutzungsgrad
    const nutzungsgradElement = document.getElementById('kpi-nutzungsgrad');
    if (nutzungsgradElement && data.liquiditaet) {
        const grad = data.liquiditaet.nutzungsgrad;
        nutzungsgradElement.textContent = grad.toFixed(1) + '%';
        nutzungsgradElement.className = grad < 50 ? 'text-success' : grad < 80 ? 'text-warning' : 'text-danger';
    }
    
    // Zinsen
    if (data.zinsen) {
        const zinsenEl = document.getElementById('kpi-zinsen');
        if (zinsenEl) zinsenEl.textContent = formatCurrency(data.zinsen);
    }
    
    // Einkauf
    if (data.einkauf) {
        const anzahlEl = document.getElementById('kpi-einkauf-anzahl');
        const summeEl = document.getElementById('kpi-einkauf-summe');
        if (anzahlEl) anzahlEl.textContent = data.einkauf.anzahl_fahrzeuge;
        if (summeEl) summeEl.textContent = formatCurrency(data.einkauf.finanzierungssumme);
    }
    
    // Umsatz
    if (data.umsatz) {
        const umsatzEl = document.getElementById('kpi-umsatz');
        if (umsatzEl) umsatzEl.textContent = formatCurrency(data.umsatz);
    }
}

function updateGesellschafterSection(data) {
    const section = document.getElementById('gesellschafter-section');
    if (!section) return;
    
    if (showGesellschafter && data.gesellschafter && data.gesellschafter.saldo !== null) {
        section.style.display = 'block';
        const saldoElement = document.getElementById('gesellschafter-saldo');
        if (saldoElement) {
            saldoElement.textContent = formatCurrency(data.gesellschafter.saldo);
        }
    } else {
        section.style.display = 'none';
    }
}

function formatCurrency(value) {
    if (value === null || value === undefined) return '0,00 €';
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function fetchJson(url) {
    return fetch(url).then(async (response) => {
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Unerwarteter Content-Type (${contentType || 'leer'}) von ${url}: ${text.slice(0, 120)}`);
        }
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data && data.error ? data.error : `HTTP ${response.status} bei ${url}`);
        }
        return data;
    });
}

function setKpiErrorState() {
    const ids = [
        'kpi-liquiditaet-operativ',
        'kpi-liquiditaet-verfuegbar',
        'kpi-kreditlinien',
        'kpi-nutzungsgrad',
        'kpi-zinsen',
        'kpi-einkauf-anzahl',
        'kpi-einkauf-summe',
        'kpi-umsatz'
    ];
    ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = 'Fehler';
        }
    });
}

function updateZinskostenChart(data) {
    const canvas = document.getElementById('zinskosten-chart');
    if (!canvas || !data || !data.trends || !Array.isArray(data.trends.zinskosten_monat)) return;

    const labels = data.trends.zinskosten_monat.map(item => item.label);
    const values = data.trends.zinskosten_monat.map(item => (
        item.zinskosten === null || item.zinskosten === undefined ? null : Number(item.zinskosten)
    ));
    const monateOhneDaten = data.trends.zinskosten_monat.filter(item => !item.has_data).map(item => item.label);
    const monateFallback = data.trends.zinskosten_monat
        .filter(item => item.source === 'transaktionen_fallback')
        .map(item => item.label);
    const hinweisEl = document.getElementById('zinskosten-hinweis');
    if (hinweisEl) {
        if (monateFallback.length) {
            hinweisEl.textContent = `Hinweis: Monate ${monateFallback.join(', ')} basieren auf zinsbezogenen Banktransaktionen (FiBu-Zinsbuchungen fehlen).`;
        } else if (monateOhneDaten.length) {
            hinweisEl.textContent = `Hinweis: Für ${monateOhneDaten.length} Monat(e) liegen keine Zinsdaten vor (${monateOhneDaten.join(', ')}).`;
        } else {
            hinweisEl.textContent = 'Alle Monate basieren auf FiBu-Zinsbuchungen.';
        }
    }

    if (zinskostenChart) {
        zinskostenChart.destroy();
    }

    zinskostenChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Zinskosten pro Monat',
                data: values,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.08)',
                borderWidth: 2,
                tension: 0.2,
                fill: false,
                pointRadius: 2,
                pointHoverRadius: 4,
                spanGaps: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y ?? 0;
                            if (context.raw === null) return ' Keine FiBu-Zinsbuchung';
                            return ` ${formatCurrency(value)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 12
                    }
                }
            }
        }
    });
}

function updateLiquiditaetChart(data) {
    const canvas = document.getElementById('liquiditaet-chart');
    if (!canvas || !data || !data.trends || !Array.isArray(data.trends.liquiditaet_monat)) return;

    const source = data.trends.liquiditaet_monat.slice(-6);
    const labels = source.map(item => item.label);
    const values = source.map(item => Number(item.saldo || 0));

    if (liquiditaetChart) {
        liquiditaetChart.destroy();
    }

    liquiditaetChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Operative Liquidität (Monatsendstand)',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.10)',
                borderWidth: 2,
                tension: 0.2,
                fill: true,
                pointRadius: 2,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y ?? 0;
                            return ` ${formatCurrency(value)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}
