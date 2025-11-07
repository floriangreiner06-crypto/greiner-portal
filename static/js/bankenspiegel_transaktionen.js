// Bankenspiegel Transaktionen JavaScript
// Filter, Suche und Pagination

let alleTransaktionen = [];
let alleKonten = [];
let currentPage = 1;
let itemsPerPage = 50;
let filteredTransaktionen = [];

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

// Transaktionen laden
async function loadTransaktionen() {
    try {
        // Große Anzahl laden für client-side Filterung
        const response = await fetch('/api/bankenspiegel/transaktionen?limit=10000&offset=0');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        alleTransaktionen = data.transaktionen || [];
        
        // Konten für Filter laden
        await loadKontenFilter();
        
        // Standard-Datum setzen (letzte 90 Tage)
        setDefaultDates();
        
        // URL-Parameter prüfen (z.B. konto_id)
        checkUrlParams();
        
        // Filter anwenden
        applyFilters();
        
    } catch (error) {
        console.error('Fehler beim Laden der Transaktionen:', error);
        showError('Transaktionen konnten nicht geladen werden');
    }
}

// Konten für Filter laden
async function loadKontenFilter() {
    try {
        const response = await fetch('/api/bankenspiegel/konten');
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        alleKonten = data.konten || [];
        
        // Konten-Filter befüllen
        const kontoFilter = document.getElementById('kontoFilter');
        kontoFilter.innerHTML = '<option value="">Alle Konten</option>' +
            alleKonten
                .filter(k => k.aktiv)
                .map(k => `<option value="${k.id}">${k.bank_name} - ${k.kontoname || k.iban}</option>`)
                .join('');
        
    } catch (error) {
        console.error('Fehler beim Laden der Konten:', error);
    }
}

// Standard-Datum setzen (letzte 90 Tage)
function setDefaultDates() {
    const heute = new Date();
    const vor90Tagen = new Date();
    vor90Tagen.setDate(heute.getDate() - 90);
    
    document.getElementById('bisDatum').valueAsDate = heute;
    document.getElementById('vonDatum').valueAsDate = vor90Tagen;
}

// URL-Parameter prüfen
function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const kontoId = urlParams.get('konto_id');
    
    if (kontoId) {
        document.getElementById('kontoFilter').value = kontoId;
    }
}

// Filter anwenden
function applyFilters() {
    const vonDatum = document.getElementById('vonDatum').value;
    const bisDatum = document.getElementById('bisDatum').value;
    const kontoId = document.getElementById('kontoFilter').value;
    const typ = document.getElementById('typFilter').value;
    const searchTerm = document.getElementById('searchTransaktionen').value.toLowerCase();
    
    // Transaktionen filtern
    filteredTransaktionen = alleTransaktionen.filter(t => {
        // Datum-Filter
        if (vonDatum && t.buchungsdatum < vonDatum) return false;
        if (bisDatum && t.buchungsdatum > bisDatum) return false;
        
        // Konto-Filter
        if (kontoId && t.konto_id !== parseInt(kontoId)) return false;
        
        // Typ-Filter
        if (typ === 'einnahmen' && t.betrag < 0) return false;
        if (typ === 'ausgaben' && t.betrag >= 0) return false;
        
        // Suche in Verwendungszweck
        if (searchTerm && !t.verwendungszweck?.toLowerCase().includes(searchTerm)) return false;
        
        return true;
    });
    
    // Statistik aktualisieren
    updateStatistik();
    
    // Zurück zur ersten Seite
    currentPage = 1;
    
    // Tabelle aktualisieren
    updateTransaktionenTable();
    
    // Pagination aktualisieren
    updatePagination();
}

// Statistik aktualisieren
function updateStatistik() {
    const einnahmen = filteredTransaktionen
        .filter(t => t.betrag >= 0)
        .reduce((sum, t) => sum + t.betrag, 0);
    
    const ausgaben = filteredTransaktionen
        .filter(t => t.betrag < 0)
        .reduce((sum, t) => sum + Math.abs(t.betrag), 0);
    
    const saldo = einnahmen - ausgaben;
    
    document.getElementById('einnahmenGefiltert').innerHTML = formatBetrag(einnahmen);
    document.getElementById('ausgabenGefiltert').innerHTML = formatBetrag(ausgaben);
    
    const saldoElement = document.getElementById('saldoGefiltert');
    saldoElement.innerHTML = formatBetrag(saldo);
    saldoElement.className = saldo >= 0 ? 'mb-0 text-success' : 'mb-0 text-danger';
    
    document.getElementById('anzahlGefiltert').innerHTML = formatZahl(filteredTransaktionen.length);
}

// Transaktionen-Tabelle aktualisieren
function updateTransaktionenTable() {
    const tbody = document.querySelector('#transaktionenTable tbody');
    
    if (filteredTransaktionen.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-5 text-muted">
                    <i class="bi bi-inbox me-2"></i>Keine Transaktionen gefunden
                </td>
            </tr>
        `;
        document.getElementById('transaktionenInfo').textContent = 'Keine Transaktionen gefunden';
        return;
    }
    
    // Pagination berechnen
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageTransaktionen = filteredTransaktionen.slice(startIndex, endIndex);
    
    // Tabelle befüllen
    tbody.innerHTML = pageTransaktionen.map(t => {
        const betrag = t.betrag || 0;
        const betragClass = betrag >= 0 ? 'text-success' : 'text-danger';
        const icon = betrag >= 0 ? '↑' : '↓';
        
        // Konto-Info finden
        const konto = alleKonten.find(k => k.id === t.konto_id);
        const kontoInfo = konto 
            ? `${konto.bank_name || ''}<br><small class="text-muted">${konto.kontoname || konto.iban}</small>`
            : '-';
        
        return `
            <tr>
                <td class="text-muted small">${formatDatum(t.buchungsdatum)}</td>
                <td class="small">${kontoInfo}</td>
                <td>
                    <div style="max-width: 500px; overflow: hidden; text-overflow: ellipsis;">
                        ${t.verwendungszweck || '-'}
                    </div>
                </td>
                <td class="text-end ${betragClass} fw-bold">
                    ${icon} ${formatBetrag(Math.abs(betrag))}
                </td>
            </tr>
        `;
    }).join('');
    
    // Info-Text aktualisieren
    const von = startIndex + 1;
    const bis = Math.min(endIndex, filteredTransaktionen.length);
    const gesamt = filteredTransaktionen.length;
    
    document.getElementById('transaktionenInfo').textContent = 
        `${formatZahl(von)}-${formatZahl(bis)} von ${formatZahl(gesamt)} Transaktionen`;
}

// Pagination aktualisieren
function updatePagination() {
    const totalPages = Math.ceil(filteredTransaktionen.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Vorherige Seite
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Seiten-Nummern (max 5 anzeigen)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Nächste Seite
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

// Seite wechseln
function changePage(page) {
    const totalPages = Math.ceil(filteredTransaktionen.length / itemsPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    updateTransaktionenTable();
    updatePagination();
    
    // Zum Anfang scrollen
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Fehlermeldung anzeigen
function showError(message) {
    alert('Fehler: ' + message);
}

// Event Listener beim Laden
document.addEventListener('DOMContentLoaded', function() {
    // Transaktionen laden
    loadTransaktionen();
});
