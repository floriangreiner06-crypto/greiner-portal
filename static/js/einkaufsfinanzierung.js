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
        updateKPIs(data.gesamt, data.warnungen ? data.warnungen.length : 0);
        updateInstituteCards(data.institute);
        updateCharts(data.institute);
        updateTopFahrzeuge(data.top_fahrzeuge);
        updateWarnungen(data.warnungen || []);
        loadFahrzeugeMitZinsen();
        loadZinsenAnalyse();  // Neue Funktion für Zinsen-Analyse
        
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
        
        // Farben und Icons für verschiedene Institute
        let color, icon;
        switch(institut.name) {
            case 'Stellantis':
                color = 'primary';
                icon = 'lightning-charge-fill';
                break;
            case 'Santander':
                color = 'info';
                icon = 'bank';
                break;
            case 'Hyundai Finance':
                color = 'success';
                icon = 'car-front-fill';
                break;
            case 'Genobank':
                color = 'warning';
                icon = 'building';
                break;
            default:
                color = 'secondary';
                icon = 'bank';
        }
        
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
                                <span class="badge bg-${color} bg-opacity-25 text-${color} border border-${color} marke-badge" 
                                      style="cursor: pointer;" 
                                      onclick="showMarkeFahrzeuge('${institut.name}', '${marke.name.replace(/'/g, "\\'")}')"
                                      title="Klicken für Details">
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
    // Farben für verschiedene Institute
    const instituteColors = {
        'Stellantis': 'rgba(156, 39, 176, 0.8)',      // Lila
        'Santander': 'rgba(3, 169, 244, 0.8)',        // Blau
        'Hyundai Finance': 'rgba(40, 167, 69, 0.8)',  // Grün
        'Genobank': 'rgba(255, 193, 7, 0.8)'          // Gelb/Warning
    };
    
    const instituteBorderColors = {
        'Stellantis': 'rgb(156, 39, 176)',
        'Santander': 'rgb(3, 169, 244)',
        'Hyundai Finance': 'rgb(40, 167, 69)',
        'Genobank': 'rgb(255, 193, 7)'
    };
    
    const instituteData = {
        labels: institute.map(i => i.name),
        datasets: [{
            data: institute.map(i => i.finanzierung),
            backgroundColor: institute.map(i => instituteColors[i.name] || 'rgba(108, 117, 125, 0.8)'),
            borderColor: institute.map(i => instituteBorderColors[i.name] || 'rgb(108, 117, 125)'),
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
    
    // Farben für Marken-Chart basierend auf Institut
    const markenChartColors = {
        'Stellantis': 'rgba(156, 39, 176, 0.8)',
        'Santander': 'rgba(3, 169, 244, 0.8)',
        'Hyundai Finance': 'rgba(40, 167, 69, 0.8)',
        'Genobank': 'rgba(255, 193, 7, 0.8)'
    };
    
    institute.forEach((institut, idx) => {
        const color = markenChartColors[institut.name] || `rgba(${idx * 50}, ${idx * 100}, ${idx * 150}, 0.8)`;
        
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
            <td>
                <code class="vin-clickable" 
                      onclick="showFahrzeugDetails('${fz.vin || ''}')" 
                      title="Klicken für Fahrzeugdetails">
                    ${fz.vin}
                </code>
            </td>
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
        
        const tage_uebrig = warnung.tage_uebrig || 0;
        const ist_ueber = tage_uebrig < 0;
        const badgeColor = ist_ueber ? 'danger' : (warnung.kritisch ? 'danger' : 'warning');
        const tageClass = ist_ueber ? 'text-danger fw-bold' : (warnung.kritisch ? 'text-danger fw-bold' : 'text-warning');
        
        // Text für Tage-Anzeige
        let tageText = '';
        if (ist_ueber) {
            tageText = `<span class="badge bg-danger">ÜBER Zinsfreiheit: ${Math.abs(tage_uebrig)} Tage</span>`;
        } else {
            tageText = `${tage_uebrig} Tage übrig`;
            if (warnung.kritisch) {
                tageText += ' <span class="badge bg-danger ms-1">KRITISCH</span>';
            }
        }
        
        row.innerHTML = `
            <td><span class="badge bg-primary">${warnung.institut || 'Stellantis'}</span></td>
            <td>
                <code class="vin-clickable" 
                      onclick="showFahrzeugDetails('${warnung.vin || ''}')" 
                      title="Klicken für Fahrzeugdetails">
                    ${warnung.vin}
                </code>
            </td>
            <td>${warnung.modell || '-'}</td>
            <td class="${tageClass}">
                <i class="bi bi-exclamation-triangle-fill"></i>
                ${tageText}
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

/**
 * Fahrzeuge mit laufenden Zinsen laden
 */
async function loadFahrzeugeMitZinsen() {
    try {
        const response = await fetch('/api/bankenspiegel/fahrzeuge-mit-zinsen?status=zinsen_laufen&institut=alle');
        
        if (!response.ok) {
            console.error('Zinsen-API Fehler:', response.status);
            return;
        }
        
        const data = await response.json();
        
        if (!data.success || !data.fahrzeuge || data.fahrzeuge.length === 0) {
            // Keine Fahrzeuge mit Zinsen - Section ausblenden
            document.getElementById('zinsenSection').classList.add('d-none');
            return;
        }
        
        // Section anzeigen
        document.getElementById('zinsenSection').classList.remove('d-none');
        
        // Statistik aktualisieren
        document.getElementById('zinsenAnzahl').textContent = data.statistik.anzahl_fahrzeuge;
        document.getElementById('zinsenSaldo').textContent = formatCurrency(data.statistik.gesamt_saldo);
        
        // Santander/Stellantis Split
        document.getElementById('zinsenSantanderCount').textContent = data.statistik.santander.anzahl;
        document.getElementById('zinsenStellantisCount').textContent = data.statistik.stellantis.anzahl;
        
        // Zinsen Gesamt (nur Santander)
        if (data.statistik.gesamt_zinsen) {
            document.getElementById('zinsenGesamt').textContent = formatCurrency(data.statistik.gesamt_zinsen);
        } else {
            document.getElementById('zinsenGesamt').textContent = 'N/A';
        }
        
        // Zinsen Monatlich (nur Santander)
        if (data.statistik.santander.zinsen_monatlich) {
            document.getElementById('zinsenMonatlich').textContent = formatCurrency(data.statistik.santander.zinsen_monatlich);
        } else {
            document.getElementById('zinsenMonatlich').textContent = 'N/A';
        }
        
        // Tabelle füllen
        const tbody = document.getElementById('zinsenTableBody');
        tbody.innerHTML = data.fahrzeuge.map(fz => {
            const tage = fz.tage_seit_zinsstart || 0;
            const severity = tage > 90 ? 'danger' : tage > 60 ? 'warning' : 'info';
            
            // Zinsen-Spalten (nur bei Santander)
            const zinsenGesamt = fz.zinsen_gesamt 
                ? `<span class="text-danger fw-bold">${formatCurrency(fz.zinsen_gesamt)}</span>`
                : '<span class="text-muted">N/A</span>';
            
            const zinsenMonatlich = fz.zinsen_monatlich_geschaetzt 
                ? `<span class="text-warning">${formatCurrency(fz.zinsen_monatlich_geschaetzt)}</span>`
                : '<span class="text-muted">N/A</span>';
            
            // Endfälligkeit (nur bei Santander)
            let endfaelligkeit = '<span class="text-muted">N/A</span>';
            if (fz.endfaelligkeit) {
                const tage_bis = fz.tage_bis_endfaelligkeit || 0;
                const datum = new Date(fz.endfaelligkeit).toLocaleDateString('de-DE');
                const color = tage_bis < 180 ? 'danger' : tage_bis < 365 ? 'warning' : 'info';
                endfaelligkeit = `
                    <div class="small">
                        ${datum}<br>
                        <span class="badge bg-${color}">${tage_bis} Tage</span>
                    </div>
                `;
            }
            
            return `
                <tr>
                    <td><span class="badge bg-${severity}">${fz.finanzinstitut}</span></td>
                    <td>
                        <code class="small vin-clickable" 
                              onclick="showFahrzeugDetails('${fz.vin || ''}')" 
                              title="Klicken für Fahrzeugdetails">
                            ${fz.vin}
                        </code>
                    </td>
                    <td>${fz.modell || 'N/A'}</td>
                    <td class="text-end">
                        <span class="badge bg-${severity} px-3">
                            <strong>${tage}</strong> Tage
                        </span>
                    </td>
                    <td class="text-end text-danger fw-bold">
                        ${formatCurrency(fz.aktueller_saldo)}
                    </td>
                    <td class="text-end">${zinsenGesamt}</td>
                    <td class="text-end">${zinsenMonatlich}</td>
                    <td class="text-end">${endfaelligkeit}</td>
                    <td class="text-end">
                        <div class="progress" style="height: 8px; width: 80px; display: inline-block;">
                            <div class="progress-bar bg-success" 
                                 style="width: ${parseFloat(fz.tilgung_prozent) || 0}%"></div>
                        </div>
                        <small class="ms-2">${(parseFloat(fz.tilgung_prozent) || 0).toFixed(1)}%</small>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Fehler beim Laden der Zinsen-Daten:', error);
        document.getElementById('zinsenSection').classList.add('d-none');
    }
}

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
 * Modal für Marken-Fahrzeuge öffnen
 */
async function showMarkeFahrzeuge(institut, marke) {
    const modal = new bootstrap.Modal(document.getElementById('markeFahrzeugeModal'));
    const titleEl = document.getElementById('modalMarkeTitle');
    const loadingEl = document.getElementById('markeFahrzeugeLoading');
    const contentEl = document.getElementById('markeFahrzeugeContent');
    const tbody = document.getElementById('markeFahrzeugeTableBody');
    
    // Modal-Title setzen
    titleEl.textContent = `${institut} - ${marke}`;
    
    // Loading anzeigen
    loadingEl.classList.remove('d-none');
    contentEl.classList.add('d-none');
    tbody.innerHTML = '';
    
    // Modal öffnen
    modal.show();
    
    try {
        // API-Call: Fahrzeuge nach Institut und Marke
        const response = await fetch(`/api/bankenspiegel/einkaufsfinanzierung/fahrzeuge?institut=${encodeURIComponent(institut)}&marke=${encodeURIComponent(marke)}`);
        const data = await response.json();
        
        if (!data.success) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Fehler: ${data.error || 'Unbekannter Fehler'}</td></tr>`;
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');
            return;
        }
        
        const fahrzeuge = data.fahrzeuge || [];
        
        if (fahrzeuge.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Keine Fahrzeuge gefunden</td></tr>`;
        } else {
            // Tabelle füllen
            let gesamtSaldo = 0;
            let gesamtOriginal = 0;
            let gesamtAbbezahlt = 0;
            let gesamtStandzeitTage = 0;
            let anzahlMitStandzeit = 0;
            let gesamtZinsen = 0;
            let gesamtZinsenMonat = 0;
            
            tbody.innerHTML = fahrzeuge.map((fz, idx) => {
                const saldo = parseFloat(fz.aktueller_saldo || 0);
                const original = parseFloat(fz.original_betrag || 0);
                const abbezahlt = original - saldo;
                const standzeitTage = parseInt(fz.alter_tage || 0);
                const zinsenGesamt = parseFloat(fz.zinsen_gesamt || 0);
                const zinsenMonat = parseFloat(fz.zinsen_letzte_periode || 0);
                
                gesamtSaldo += saldo;
                gesamtOriginal += original;
                gesamtAbbezahlt += abbezahlt;
                gesamtZinsen += zinsenGesamt;
                gesamtZinsenMonat += zinsenMonat;
                
                if (standzeitTage > 0) {
                    gesamtStandzeitTage += standzeitTage;
                    anzahlMitStandzeit++;
                }
                
                return `
                    <tr>
                        <td>
                            <code class="small vin-clickable" 
                                  onclick="showFahrzeugDetails('${fz.vin || ''}')" 
                                  title="Klicken für Fahrzeugdetails">
                                ${fz.vin || '-'}
                            </code>
                        </td>
                        <td>${fz.modell || 'Unbekannt'}</td>
                        <td>${fz.marke || fz.hersteller || 'Unbekannt'}</td>
                        <td class="text-end text-danger fw-bold">${formatCurrency(saldo)}</td>
                        <td class="text-end">${formatCurrency(original)}</td>
                        <td class="text-end">${standzeitTage > 0 ? standzeitTage + ' Tage' : '-'}</td>
                        <td class="text-end text-danger">${zinsenGesamt > 0 ? formatCurrency(zinsenGesamt) : '-'}</td>
                        <td class="text-end text-warning">${zinsenMonat > 0 ? formatCurrency(zinsenMonat) : '-'}</td>
                        <td class="text-end text-success">${formatCurrency(abbezahlt)}</td>
                    </tr>
                `;
            }).join('');
            
            // Gesamt-Summen
            document.getElementById('modalGesamtSaldo').textContent = formatCurrency(gesamtSaldo);
            document.getElementById('modalGesamtOriginal').textContent = formatCurrency(gesamtOriginal);
            document.getElementById('modalGesamtAbbezahlt').textContent = formatCurrency(gesamtAbbezahlt);
            document.getElementById('modalGesamtZinsen').textContent = gesamtZinsen > 0 ? formatCurrency(gesamtZinsen) : '-';
            document.getElementById('modalGesamtZinsenMonat').textContent = gesamtZinsenMonat > 0 ? formatCurrency(gesamtZinsenMonat) : '-';
            
            // Durchschnittliche Standzeit berechnen
            const durchschnittStandzeit = anzahlMitStandzeit > 0 
                ? Math.round(gesamtStandzeitTage / anzahlMitStandzeit) 
                : 0;
            document.getElementById('modalDurchschnittStandzeit').textContent = durchschnittStandzeit > 0 
                ? `Ø ${durchschnittStandzeit} Tage` 
                : '-';
        }
        
        // Content anzeigen
        loadingEl.classList.add('d-none');
        contentEl.classList.remove('d-none');
        
    } catch (error) {
        console.error('Fehler beim Laden der Fahrzeuge:', error);
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Fehler beim Laden: ${error.message}</td></tr>`;
        loadingEl.classList.add('d-none');
        contentEl.classList.remove('d-none');
    }
}

/**
 * Fahrzeugdetails aus Locosoft anzeigen
 */
async function showFahrzeugDetails(vin) {
    if (!vin || vin === '-') {
        alert('Keine VIN angegeben');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('fahrzeugDetailsModal'));
    const titleEl = document.getElementById('modalFahrzeugTitle');
    const loadingEl = document.getElementById('fahrzeugDetailsLoading');
    const contentEl = document.getElementById('fahrzeugDetailsContent');
    const finanzSection = document.getElementById('detailFinanzierungSection');
    
    // Modal-Title setzen
    titleEl.textContent = `Fahrzeugdetails - ${vin}`;
    
    // Loading anzeigen
    loadingEl.classList.remove('d-none');
    contentEl.classList.add('d-none');
    finanzSection.classList.add('d-none');
    
    // Modal öffnen
    modal.show();
    
    try {
        // API-Call: Fahrzeugdetails aus Locosoft
        const response = await fetch(`/api/bankenspiegel/fahrzeug-details?vin=${encodeURIComponent(vin)}`);
        const data = await response.json();
        
        if (!data.success) {
            contentEl.innerHTML = `<div class="alert alert-danger">Fehler: ${data.error || 'Unbekannter Fehler'}</div>`;
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');
            return;
        }
        
        const fz = data.fahrzeug || {};
        const finanz = data.finanzierung || null;
        
        // Helper: Datum formatieren
        function formatDate(dateStr) {
            if (!dateStr) return '-';
            try {
                const date = new Date(dateStr);
                if (isNaN(date.getTime())) return dateStr;
                return date.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit', day: '2-digit' });
            } catch {
                return dateStr;
            }
        }
        
        // Fahrzeugdaten füllen
        document.getElementById('detailVin').textContent = fz.vin || '-';
        document.getElementById('detailTyp').textContent = fz.fahrzeugtyp || fz.typ || '-';
        document.getElementById('detailModell').textContent = `${fz.marke || ''} ${fz.modell || ''}`.trim() || '-';
        document.getElementById('detailEZ').textContent = formatDate(fz.erstzulassung || fz.ez);
        document.getElementById('detailKM').textContent = fz.km_stand ? `${parseInt(fz.km_stand).toLocaleString('de-DE')} km` : '-';
        document.getElementById('detailKZ').textContent = fz.kennzeichen || fz.license_plate || '-';
        
        // Bestandsdaten füllen
        document.getElementById('detailEingang').textContent = formatDate(fz.eingang || fz.in_arrival_date);
        document.getElementById('detailStandzeit').textContent = fz.standzeit_tage ? `${fz.standzeit_tage} Tage` : '-';
        document.getElementById('detailStandort').textContent = fz.standort_name || (fz.standort ? `Standort ${fz.standort}` : '-');
        document.getElementById('detailLagerort').textContent = fz.lagerort || fz.location || '-';
        document.getElementById('detailKomNr').textContent = fz.kommissionsnummer || fz.dealer_vehicle_number || '-';
        document.getElementById('detailStatus').innerHTML = fz.verkauft 
            ? `<span class="badge bg-success">Verkauft${fz.verkauft_am ? ' (' + formatDate(fz.verkauft_am) + ')' : ''}</span>` 
            : '<span class="badge bg-info">Im Bestand</span>';
        
        // Finanzierungsdaten (falls vorhanden)
        if (finanz) {
            document.getElementById('detailFinanzinstitut').textContent = finanz.finanzinstitut || '-';
            document.getElementById('detailSaldo').textContent = formatCurrency(parseFloat(finanz.aktueller_saldo || 0));
            document.getElementById('detailOriginal').textContent = formatCurrency(parseFloat(finanz.original_betrag || 0));
            
            // Zinskosten
            const zinsenGesamt = parseFloat(finanz.zinsen_gesamt || 0);
            const zinsenMonat = parseFloat(finanz.zinsen_letzte_periode || 0);
            const zinsfreiheit = finanz.zinsfreiheit_tage;
            
            // Zinsstartdatum anzeigen
            const zinsStartdatum = finanz.zins_startdatum;
            document.getElementById('detailZinsStartdatum').textContent = formatDate(zinsStartdatum);
            
            // Zinsstart-Text dynamisch anzeigen (falls vorhanden)
            const zinsstartTextEl = document.getElementById('detailZinsStartdatumInfo');
            if (finanz.zinsstart_text) {
                zinsstartTextEl.textContent = finanz.zinsstart_text;
            } else {
                zinsstartTextEl.textContent = 'Zinsstartdatum';
            }
            
            // Tage seit Zinsstart berechnen
            let tageSeitZinsstart = '-';
            if (zinsStartdatum) {
                try {
                    const zinsStart = new Date(zinsStartdatum);
                    const heute = new Date();
                    const diffTime = Math.abs(heute - zinsStart);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    tageSeitZinsstart = `${diffDays} Tage`;
                } catch (e) {
                    tageSeitZinsstart = '-';
                }
            }
            document.getElementById('detailTageSeitZinsstart').textContent = tageSeitZinsstart;
            
            document.getElementById('detailZinsenGesamt').textContent = zinsenGesamt > 0 ? formatCurrency(zinsenGesamt) : '-';
            document.getElementById('detailZinsenMonat').textContent = zinsenMonat > 0 ? formatCurrency(zinsenMonat) : '-';
            
            if (zinsfreiheit !== null && zinsfreiheit !== undefined) {
                if (zinsfreiheit > 0) {
                    document.getElementById('detailZinsfreiheit').textContent = `${zinsfreiheit} Tage übrig`;
                } else {
                    document.getElementById('detailZinsfreiheit').textContent = 'Zinsen laufen';
                    document.getElementById('detailZinsfreiheit').classList.add('text-danger');
                }
            } else {
                document.getElementById('detailZinsfreiheit').textContent = '-';
            }
            
            finanzSection.classList.remove('d-none');
        } else {
            finanzSection.classList.add('d-none');
        }
        
        // Content anzeigen
        loadingEl.classList.add('d-none');
        contentEl.classList.remove('d-none');
        
    } catch (error) {
        console.error('Fehler beim Laden der Fahrzeugdetails:', error);
        contentEl.innerHTML = `<div class="alert alert-danger">Fehler beim Laden: ${error.message}</div>`;
        loadingEl.classList.add('d-none');
        contentEl.classList.remove('d-none');
    }
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

/**
 * Zinsen-Analyse laden (konsolidiert)
 */
async function loadZinsenAnalyse() {
    try {
        const [dashboard, report, empfehlungen] = await Promise.all([
            fetch('/api/zinsen/dashboard').then(r => r.json()),
            fetch('/api/zinsen/report').then(r => r.json()),
            fetch('/api/zinsen/umbuchung-empfehlung').then(r => r.json())
        ]);
        
        // KPIs aktualisieren
        document.getElementById('zinsenMonatGesamt').textContent = formatCurrency(dashboard.zinskosten_monat || 0);
        document.getElementById('zinsenJahrGesamt').textContent = formatCurrency(dashboard.zinskosten_jahr || 0);
        document.getElementById('anzahlDringend').textContent = dashboard.stellantis_ueber_zinsfreiheit?.anzahl || 0;
        document.getElementById('anzahlWarnung').textContent = dashboard.stellantis_bald_ablaufend?.anzahl || 0;
        
        // Institut-Tabelle
        updateInstitutTabelleZinsen(dashboard);
        
        // Handlungsempfehlungen
        updateEmpfehlungen(empfehlungen);
        
    } catch (error) {
        console.error('Fehler beim Laden der Zinsen-Analyse:', error);
    }
}

/**
 * Institut-Tabelle für Zinsen-Analyse
 */
function updateInstitutTabelleZinsen(dashboard) {
    const tbody = document.getElementById('institutTabelle');
    
    const institute = [
        {
            name: 'Konten Sollzinsen',
            fahrzeuge: '-',
            saldo: '-',
            monat: dashboard.konten_sollzinsen || 0,
            jahr: (dashboard.konten_sollzinsen || 0) * 12,
            status: 'ok'
        },
        {
            name: 'Stellantis',
            fahrzeuge: dashboard.stellantis_gesamt?.anzahl || 0,
            saldo: dashboard.stellantis_gesamt?.saldo || 0,
            monat: dashboard.stellantis_ueber_zinsfreiheit?.zinsen_monat || 0,
            jahr: (dashboard.stellantis_ueber_zinsfreiheit?.zinsen_monat || 0) * 12,
            status: (dashboard.stellantis_ueber_zinsfreiheit?.anzahl || 0) > 0 ? 'danger' : 'ok'
        },
        {
            name: 'Santander',
            fahrzeuge: dashboard.santander?.anzahl || 0,
            saldo: dashboard.santander?.saldo || 0,
            monat: dashboard.santander?.zinsen_monat || 0,
            jahr: (dashboard.santander?.zinsen_monat || 0) * 12,
            status: 'ok'
        },
        {
            name: 'Hyundai Finance',
            fahrzeuge: dashboard.hyundai?.anzahl || 0,
            saldo: dashboard.hyundai?.saldo || 0,
            monat: dashboard.hyundai?.zinsen_monat || 0,
            jahr: (dashboard.hyundai?.zinsen_monat || 0) * 12,
            status: 'ok'
        },
        {
            name: 'Genobank',
            fahrzeuge: dashboard.genobank?.anzahl || 0,
            saldo: dashboard.genobank?.saldo || 0,
            monat: dashboard.genobank?.zinsen_monat || 0,
            jahr: (dashboard.genobank?.zinsen_monat || 0) * 12,
            status: 'ok'
        }
    ];
    
    let html = '';
    let gesamtFz = 0, gesamtSaldo = 0;
    
    institute.forEach(inst => {
        const statusBadge = inst.status === 'danger' 
            ? '<span class="badge bg-danger">Handeln!</span>'
            : '<span class="badge bg-success">OK</span>';
        
        html += `<tr>
            <td><strong>${inst.name}</strong></td>
            <td class="text-end">${inst.fahrzeuge}</td>
            <td class="text-end">${inst.saldo !== '-' ? formatCurrency(inst.saldo) : '-'}</td>
            <td class="text-end ${inst.monat > 500 ? 'text-danger fw-bold' : ''}">${formatCurrency(inst.monat)}</td>
            <td class="text-end">${formatCurrency(inst.jahr)}</td>
            <td class="text-center">${statusBadge}</td>
        </tr>`;
        
        if (typeof inst.fahrzeuge === 'number') gesamtFz += inst.fahrzeuge;
        if (typeof inst.saldo === 'number') gesamtSaldo += inst.saldo;
    });
    
    tbody.innerHTML = html;
    
    // Footer aktualisieren
    document.getElementById('gesamtFahrzeuge').textContent = gesamtFz;
    document.getElementById('gesamtSaldo').textContent = formatCurrency(gesamtSaldo);
    document.getElementById('gesamtMonat').textContent = formatCurrency(dashboard.zinskosten_monat || 0);
    document.getElementById('gesamtJahr').textContent = formatCurrency(dashboard.zinskosten_jahr || 0);
}

/**
 * Handlungsempfehlungen aktualisieren
 */
function updateEmpfehlungen(data) {
    const container = document.getElementById('empfehlungenListe');
    const empfehlungen = data.empfehlungen || [];
    
    if (empfehlungen.length === 0) {
        document.getElementById('empfehlungenSection').classList.add('d-none');
        return;
    }
    
    document.getElementById('empfehlungenSection').classList.remove('d-none');
    
    let html = '<div class="list-group list-group-flush">';
    
    empfehlungen.forEach((emp, idx) => {
        const priorityClass = emp.prioritaet === 1 ? "border-danger" : "border-warning";
        const priorityBadge = emp.prioritaet === 1 
            ? '<span class="badge bg-danger">SOFORT</span>' 
            : '<span class="badge bg-warning text-dark">BALD</span>';
        
        if (emp.typ === "normale_umbuchung") {
            html += `<div class="list-group-item ${priorityClass} border-start border-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${priorityBadge} <i class="bi bi-arrow-left-right me-1"></i>Konten-Umbuchung</h6>
                        <p class="mb-1"><strong>${emp.von_konto}</strong> → <strong>${emp.nach_konto}</strong></p>
                        <small class="text-muted">${emp.beschreibung} (${emp.firma})</small>
                    </div>
                    <div class="text-end">
                        <div class="fs-5 fw-bold">${formatCurrency(emp.betrag)}</div>
                        <div class="text-success"><i class="bi bi-piggy-bank me-1"></i>${formatCurrency(emp.ersparnis_monat)}/Monat</div>
                        <small class="text-muted">${formatCurrency(emp.ersparnis_jahr)}/Jahr</small>
                    </div>
                </div>
            </div>`;
        } else if (emp.typ === "fahrzeug_umfinanzierung") {
            html += `<div class="list-group-item ${priorityClass} border-start border-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${priorityBadge} <i class="bi bi-truck me-1"></i>Fahrzeug-Umfinanzierung</h6>
                        <p class="mb-1"><strong>${emp.anzahl_fahrzeuge} Fahrzeuge</strong> von ${emp.von} → ${emp.nach}</p>
                        <small class="text-muted">${emp.beschreibung}</small>
                    </div>
                    <div class="text-end">
                        <div class="fs-5 fw-bold">${formatCurrency(emp.betrag)}</div>
                        <div class="text-success"><i class="bi bi-piggy-bank me-1"></i>${formatCurrency(emp.ersparnis_monat)}/Monat</div>
                        <small class="text-muted">${formatCurrency(emp.ersparnis_jahr)}/Jahr</small>
                    </div>
                </div>
            </div>`;
        }
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    document.getElementById('badgeEmpfehlungen').textContent = empfehlungen.length;
    document.getElementById('gesamtErsparnis').textContent = 
        `Potenzielle Ersparnis: ${formatCurrency(data.gesamt_ersparnis_monat || 0)}/Monat (${formatCurrency(data.gesamt_ersparnis_jahr || 0)}/Jahr)`;
}
