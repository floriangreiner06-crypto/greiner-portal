/**
 * GREINER DRIVE - CONTROLLING DASHBOARD
 * Executive Dashboard with Live KPIs & Charts
 */

// Utility: Format Currency
function formatCurrency(value) {
    const absValue = Math.abs(value);
    if (absValue >= 1000000) {
        return (value / 1000000).toFixed(2) + ' Mio €';
    } else if (absValue >= 1000) {
        return (value / 1000).toFixed(0) + 'k €';
    }
    return value.toFixed(2) + ' €';
}

// Load Overview KPIs
async function loadOverview() {
    try {
        const response = await fetch('/controlling/api/overview');
        if (!response.ok) throw new Error('API Error');
        
        const data = await response.json();
        
        // Update KPI 1: Liquidität
        document.getElementById('kpi-liquiditaet').innerHTML = 
            `<span style="color: ${data.liquiditaet < 0 ? '#f87171' : '#10b981'}">${formatCurrency(data.liquiditaet)}</span>`;
        
        // Update KPI 2: Zinsen
        document.getElementById('kpi-zinsen').innerHTML = 
            `<span style="color: #f59e0b">${formatCurrency(data.zinsen)}</span>`;
        
        // Update KPI 3: Einkaufsfinanzierung
        document.getElementById('kpi-einkauf').innerHTML = 
            `<div style="font-size: 1.5rem;">${data.einkauf.anzahl} Fzg</div>
             <div style="font-size: 1rem; color: #6b7280;">${formatCurrency(data.einkauf.saldo)}</div>`;
        
        // Update KPI 4: Umsatz
        document.getElementById('kpi-umsatz').innerHTML = 
            `<span style="color: #10b981">${formatCurrency(data.umsatz)}</span>`;
        
        console.log('✅ Overview loaded:', data);
        
    } catch (error) {
        console.error('Error loading overview:', error);
        document.querySelectorAll('.kpi-value .loading').forEach(el => {
            el.textContent = 'Fehler';
            el.style.color = '#ef4444';
        });
    }
}

// Initialize Liquidität Chart
function initLiquiditaetChart() {
    const ctx = document.getElementById('liquiditaet-chart');
    if (!ctx) return;
    
    // Dummy data for now - TODO: Load from API in Phase 2
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
            datasets: [{
                label: 'Liquidität',
                data: [-1200000, -1500000, -1800000, -1650000, -1700000, -1690000],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y);
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Controlling Dashboard loading...');
    
    // Load KPIs
    loadOverview();
    
    // Initialize Chart
    if (typeof Chart !== 'undefined') {
        initLiquiditaetChart();
    } else {
        console.warn('Chart.js not loaded');
    }
    
    // Auto-refresh every 60 seconds
    setInterval(loadOverview, 60000);
});
