// Bankenspiegel Konten JavaScript
// Filter und Tabellen-Funktionen

let alleKonten = [];
let alleBanken = [];

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

// IBAN formatieren (nur letzte 4 Zeichen sichtbar)
function formatIBAN(iban) {
    if (!iban) return '-';
    if (iban.length <= 8) return iban;
    return iban;  // Volle IBAN anzeigen
}

// Konten laden
async function loadKonten() {
    try {
        const response = await fetch('/api/bankenspiegel/konten');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        alleKonten = data.konten || [];
        
        // Banken für Filter extrahieren
        extractBanken();
        
        // Tabelle aktualisieren
        updateKontenTable();
        
        // Gesamtsaldo berechnen
        calculateGesamtsaldo();
        
    } catch (error) {
        console.error('Fehler beim Laden der Konten:', error);
        showError('Konten konnten nicht geladen werden');
    }
}

// Banken für Filter extrahieren
function extractBanken() {
    const bankenSet = new Set();
    alleKonten.forEach(konto => {
        if (konto.bank_name) {
            bankenSet.add(konto.bank_name);
        }
    });
    
    alleBanken = Array.from(bankenSet).sort();
    
    // Bank-Filter befüllen
    const bankFilter = document.getElementById('bankFilter');
    bankFilter.innerHTML = '<option value="">Alle Banken</option>' +
        alleBanken.map(bank => `<option value="${bank}">${bank}</option>`).join('');
}

// Konten-Tabelle aktualisieren
function updateKontenTable() {
    const bankFilter = document.getElementById('bankFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const searchTerm = document.getElementById('searchKonten').value.toLowerCase();
    
    // Konten filtern
    let gefiltert = alleKonten.filter(konto => {
        // Bank-Filter
        if (bankFilter && konto.bank_name !== bankFilter) return false;
        
        // Status-Filter
        if (statusFilter === 'aktiv' && !konto.aktiv) return false;
        if (statusFilter === 'inaktiv' && konto.aktiv) return false;
        
        // Suche
        if (searchTerm) {
            const suchtext = [
                konto.iban,
                konto.kontoname,
                konto.bank_name
            ].join(' ').toLowerCase();
            
            if (!suchtext.includes(searchTerm)) return false;
        }
        
        return true;
    });
    
    const tbody = document.querySelector('#kontenTable tbody');
    
    if (gefiltert.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5 text-muted">
                    <i class="bi bi-inbox me-2"></i>Keine Konten gefunden
                </td>
            </tr>
        `;
        document.getElementById('kontenInfo').textContent = 'Keine Konten gefunden';
        return;
    }
    
    // Tabelle befüllen
    tbody.innerHTML = gefiltert.map(konto => {
        const saldo = konto.saldo || 0;
        const saldoClass = saldo >= 0 ? 'text-success' : 'text-danger';
        const statusBadge = konto.aktiv 
            ? '<span class="badge bg-success">Aktiv</span>'
            : '<span class="badge bg-secondary">Inaktiv</span>';
        
        // Kreditlinie und verfügbar
        const kreditlinie = konto.kreditlinie || 0;
        const verfuegbar = konto.verfuegbar;
        const verfuegbarClass = verfuegbar !== null && verfuegbar !== undefined 
            ? (verfuegbar >= 0 ? 'text-success' : 'text-warning')
            : 'text-muted';
        
        // TAG 213: Bank-Name ausblenden wenn NULL (z.B. "Intern / Gesellschafter" ist redundant)
        const bankNameDisplay = konto.bank_name ? `<strong>${konto.bank_name}</strong>` : '';
        
        return `
            <tr>
                <td>${statusBadge}</td>
                <td>
                    ${bankNameDisplay}
                </td>
                <td>
                    ${konto.kontoname || '-'}
                    <br>
                    <small class="text-muted">${formatIBAN(konto.iban)}</small>
                </td>
                <td>
                    <code class="small">${konto.iban || '-'}</code>
                </td>
                <td class="text-end ${saldoClass} fw-bold">
                    ${formatBetrag(saldo)}
                </td>
                <td class="text-end">
                    ${kreditlinie > 0 ? formatBetrag(kreditlinie) : '<span class="text-muted">-</span>'}
                </td>
                <td class="text-end ${verfuegbarClass} fw-bold">
                    ${verfuegbar !== null && verfuegbar !== undefined ? formatBetrag(verfuegbar) : '<span class="text-muted">-</span>'}
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary" onclick="showTransaktionen(${konto.id})">
                        <i class="bi bi-list me-1"></i>Transaktionen
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Info-Text aktualisieren
    document.getElementById('kontenInfo').textContent = 
        `${formatZahl(gefiltert.length)} von ${formatZahl(alleKonten.length)} Konten angezeigt`;
}

// Gesamtsaldo berechnen
function calculateGesamtsaldo() {
    const aktiveKonten = alleKonten.filter(k => k.aktiv);
    // TAG 213: Verwende 'saldo' statt 'aktueller_saldo' (konsistent mit API-Response)
    const gesamtsaldo = aktiveKonten.reduce((sum, k) => sum + (k.saldo || 0), 0);
    
    const element = document.getElementById('gesamtsaldoKonten');
    element.innerHTML = formatBetrag(gesamtsaldo);
    element.className = gesamtsaldo >= 0 ? 'mb-0 text-success' : 'mb-0 text-danger';
}

// Transaktionen eines Kontos anzeigen
function showTransaktionen(kontoId) {
    window.location.href = `/bankenspiegel/transaktionen?konto_id=${kontoId}`;
}

// Fehlermeldung anzeigen
function showError(message) {
    alert('Fehler: ' + message);
}

// Event Listener beim Laden
document.addEventListener('DOMContentLoaded', function() {
    // Konten laden
    loadKonten();
    
    // Datenstand laden
    loadDatenstand();
    
    // Filter Event Listener
    document.getElementById('bankFilter').addEventListener('change', updateKontenTable);
    document.getElementById('statusFilter').addEventListener('change', updateKontenTable);
    document.getElementById('searchKonten').addEventListener('input', updateKontenTable);
});

// Datenstand laden und anzeigen
async function loadDatenstand() {
    try {
        const response = await fetch('/api/bankenspiegel/datenstand');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        
        if (data.success && data.datenstand) {
            const ds = data.datenstand;
            const badge = document.getElementById('datenstandBadge');
            const label = document.getElementById('datenstandLabel');
            const text = document.getElementById('datenstandText');
            
            // Datum formatieren
            let standText = 'Unbekannt';
            if (ds.neuester_kontostand) {
                const datum = new Date(ds.neuester_kontostand);
                standText = datum.toLocaleDateString('de-DE', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
            
            text.textContent = 'Stand: ' + standText;
            
            // Farbe basierend auf Aktualität
            label.classList.remove('bg-secondary', 'bg-success', 'bg-warning', 'bg-danger');
            
            if (ds.status === 'aktuell') {
                label.classList.add('bg-success');
                label.title = 'Daten sind aktuell (heute oder gestern)';
            } else if (ds.status === 'veraltet') {
                label.classList.add('bg-danger');
                label.title = `Daten sind ${ds.tage_alt} Tage alt - bitte Import prüfen!`;
            } else {
                label.classList.add('bg-warning');
                label.title = `Daten sind ${ds.tage_alt || '?'} Tage alt`;
            }
            
            badge.classList.remove('d-none');
        }
        
    } catch (error) {
        console.error('Fehler beim Laden des Datenstands:', error);
        // Badge nicht anzeigen bei Fehler
    }
}
