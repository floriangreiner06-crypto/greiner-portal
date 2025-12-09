// ========================================
// DASHBOARD JAVASCRIPT - Greiner DRIVE
// Live KPI Updates & Interactivity
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialisiert');
    
    // Initial Load
    loadKPIs();
    updateTimestamp();
    
    // Auto-Refresh alle 2 Minuten
    setInterval(loadKPIs, 120000);
    setInterval(updateTimestamp, 1000);
});

// ========================================
// KPI LADEN
// ========================================

function loadKPIs() {
    console.log('Lade KPIs...');
    
    // Parallel alle KPIs laden
    Promise.all([
        loadBankenspiegelKPIs(),
        loadFahrzeugKPIs(),
        loadUrlaubKPIs(),
        loadAuftragseingangsKPIs()
    ]).then(() => {
        console.log('✅ Alle KPIs geladen');
    }).catch(error => {
        console.error('❌ Fehler beim Laden der KPIs:', error);
    });
}

// ========================================
// BANKENSPIEGEL KPIs
// ========================================

async function loadBankenspiegelKPIs() {
    try {
        const response = await fetch('/api/bankenspiegel/dashboard');
        const data = await response.json();
        
        if (data.success === true) {
            const dashboard = data.dashboard;
            
            // Gesamtsaldo
            document.getElementById('kpi-saldo').textContent = 
                formatCurrency(dashboard.gesamtsaldo || 0);
            
            // Konten-Anzahl in Module-Footer
            const bankenCount = document.getElementById('banken-count');
            if (bankenCount) {
                bankenCount.textContent = `${dashboard.konten_aktiv || 0} Konten`;
            }
            
            console.log('✅ Bankenspiegel KPIs geladen');
        }
    } catch (error) {
        console.error('Fehler bei Bankenspiegel KPIs:', error);
        document.getElementById('kpi-saldo').textContent = 'Fehler';
    }
}

// ========================================
// FAHRZEUG KPIs (Stellantis)
// ========================================

async function loadFahrzeugKPIs() {
    try {
        const response = await fetch('/api/bankenspiegel/fahrzeuge-mit-zinsen');
        const data = await response.json();
        
        if (data.success === true) {
            const count = data.statistik?.anzahl_fahrzeuge || 0;
            document.getElementById('kpi-fahrzeuge').textContent = count;
            console.log('✅ Fahrzeug KPIs geladen');
        }
    } catch (error) {
        console.error('Fehler bei Fahrzeug KPIs:', error);
        document.getElementById('kpi-fahrzeuge').textContent = 'N/A';
    }
}

// ========================================
// URLAUB KPIs
// ========================================

async function loadUrlaubKPIs() {
    try {
        // TODO: Wenn Urlaub-API existiert, hier einbinden
        // Für jetzt: Platzhalter
        document.getElementById('kpi-urlaub').textContent = '0';
        
        const vacationCount = document.getElementById('vacation-count');
        if (vacationCount) {
            vacationCount.textContent = '0 offen';
        }
        
        console.log('✅ Urlaub KPIs geladen (Platzhalter)');
    } catch (error) {
        console.error('Fehler bei Urlaub KPIs:', error);
        document.getElementById('kpi-urlaub').textContent = 'N/A';
    }
}

// ========================================
// UMSATZ KPIs (30 Tage)
// ========================================

async function loadAuftragseingangsKPIs() {
    try {
        const response = await fetch('/api/verkauf/auftragseingang/summary');
        const data = await response.json();
        
        if (data.success === true && data.summary?.length > 0) {
            // Summe aller Aufträge im aktuellen Monat
            const gesamt = data.summary.reduce((sum, item) => sum + (item.gesamt || 0), 0);
            
            
            document.getElementById('kpi-umsatz').textContent = 
                gesamt;
            
            console.log('✅ Auftragseingang KPIs geladen');
        }
    } catch (error) {
        console.error('Fehler bei Auftragseingang KPIs:', error);
        document.getElementById('kpi-umsatz').textContent = 'Fehler';
    }
}

// ========================================
// HILFSFUNKTIONEN
// ========================================

function formatCurrency(value) {
    if (value === null || value === undefined) return '0,00 €';
    
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('de-DE');
    
    const lastUpdateEl = document.getElementById('last-update');
    if (lastUpdateEl) {
        lastUpdateEl.textContent = `${timeString} Uhr`;
    }
}

// ========================================
// ERROR HANDLING
// ========================================

window.addEventListener('error', function(e) {
    console.error('JavaScript Fehler:', e.message);
});

console.log('✅ Dashboard JavaScript geladen');
