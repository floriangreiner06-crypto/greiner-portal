// TAG 67: Multi-Entity Dashboard
let showGesellschafter = false;

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
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            updateKPIs(data);
            updateGesellschafterSection(data);
        })
        .catch(error => console.error('Fehler:', error));
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
        kreditlinienElement.textContent = formatCurrency(data.liquiditaet.kreditlinien);
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
