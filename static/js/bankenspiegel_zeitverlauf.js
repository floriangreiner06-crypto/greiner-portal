// Bankenspiegel Zeitverlauf JavaScript
// Zeigt historische Entwicklung der Konten über mehrere Tage

let zeitverlaufData = null;

// Formatierung von Beträgen
function formatBetrag(betrag) {
    if (betrag === null || betrag === undefined) return '-';
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(betrag);
}

// Formatierung von Zahlen (ohne Währung)
function formatZahl(zahl) {
    if (zahl === null || zahl === undefined) return '-';
    return new Intl.NumberFormat('de-DE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(zahl);
}

// Datum formatieren
function formatDatum(datumStr) {
    if (!datumStr) return '';
    const datum = new Date(datumStr + 'T00:00:00');
    const wochentag = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'][datum.getDay()];
    return `${wochentag}. ${datum.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })}`;
}

// Zeitverlauf laden
async function loadZeitverlauf() {
    const tage = document.getElementById('tageFilter').value;
    
    try {
        const response = await fetch(`/api/bankenspiegel/zeitverlauf?tage=${tage}`);
        if (!response.ok) throw new Error('API Fehler');
        
        const data = await response.json();
        if (!data.success) throw new Error(data.error || 'Unbekannter Fehler');
        
        zeitverlaufData = data;
        updateZeitverlaufTable();
        
    } catch (error) {
        console.error('Fehler beim Laden des Zeitverlaufs:', error);
        showError('Zeitverlauf konnte nicht geladen werden');
    }
}

// Tabelle aktualisieren
function updateZeitverlaufTable() {
    if (!zeitverlaufData || !zeitverlaufData.stichtage || zeitverlaufData.stichtage.length === 0) {
        const tbody = document.querySelector('#zeitverlaufTable tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="100" class="text-center py-5 text-muted">
                    <i class="bi bi-inbox me-2"></i>Keine historischen Daten gefunden
                </td>
            </tr>
        `;
        document.getElementById('zeitverlaufInfo').textContent = 'Keine Daten verfügbar';
        return;
    }
    
    const stichtage = zeitverlaufData.stichtage;
    const konten = zeitverlaufData.konten || [];
    
    // Header aktualisieren
    const headerRow = document.getElementById('stichtageHeader');
    const subHeaderRow = document.getElementById('stichtageSubHeader');
    
    headerRow.colSpan = stichtage.length * 3;
    headerRow.textContent = `${stichtage.length} Tage`;
    
    subHeaderRow.innerHTML = stichtage.map(datumStr => {
        const datum = formatDatum(datumStr);
        return `
            <th class="text-center" style="min-width: 100px;">Guthaben</th>
            <th class="text-center" style="min-width: 100px;">Darl.-Stand</th>
            <th class="text-center" style="min-width: 100px;">Freie Linie</th>
        `;
    }).join('');
    
    // Tabelle befüllen
    const tbody = document.querySelector('#zeitverlaufTable tbody');
    
    if (konten.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="${3 + stichtage.length * 3}" class="text-center py-5 text-muted">
                    <i class="bi bi-inbox me-2"></i>Keine Konten gefunden
                </td>
            </tr>
        `;
        document.getElementById('zeitverlaufInfo').textContent = 'Keine Konten gefunden';
        return;
    }
    
    // Summen-Zeile berechnen
    const summen = {
        linie: 0,
        tage: {}
    };
    
    stichtage.forEach(datumStr => {
        summen.tage[datumStr] = {
            guthaben: 0,
            darlehen_stand: 0,
            freie_linie: 0
        };
    });
    
    // Tabelle aufbauen
    tbody.innerHTML = konten.map(konto => {
        const kreditlinie = konto.kreditlinie || 0;
        summen.linie += kreditlinie;
        
        const tageCells = stichtage.map(datumStr => {
            const tagData = konto.tage[datumStr];
            
            if (!tagData) {
                return `
                    <td class="text-end text-muted">-</td>
                    <td class="text-end text-muted">-</td>
                    <td class="text-end text-muted">-</td>
                `;
            }
            
            const guthaben = tagData.guthaben || 0;
            const darlehen = tagData.darlehen_stand || 0;
            const freieLinie = tagData.freie_linie;
            
            // Summen aktualisieren
            summen.tage[datumStr].guthaben += guthaben;
            summen.tage[datumStr].darlehen_stand += darlehen;
            if (freieLinie !== null && freieLinie !== undefined) {
                summen.tage[datumStr].freie_linie += freieLinie;
            }
            
            const guthabenClass = guthaben > 0 ? 'text-success' : 'text-muted';
            const darlehenClass = darlehen > 0 ? 'text-danger' : 'text-muted';
            const freieLinieClass = freieLinie !== null && freieLinie !== undefined
                ? (freieLinie >= 0 ? 'text-success' : 'text-warning')
                : 'text-muted';
            
            return `
                <td class="text-end ${guthabenClass}">${formatBetrag(guthaben)}</td>
                <td class="text-end ${darlehenClass}">${formatBetrag(darlehen)}</td>
                <td class="text-end ${freieLinieClass}">${freieLinie !== null && freieLinie !== undefined ? formatBetrag(freieLinie) : '-'}</td>
            `;
        }).join('');
        
        return `
            <tr>
                <td>
                    <strong>${konto.bank_name || '-'}</strong><br>
                    <small class="text-muted">${konto.kontoname || '-'}</small>
                </td>
                <td class="text-end">${kreditlinie > 0 ? formatBetrag(kreditlinie) : '-'}</td>
                ${tageCells}
            </tr>
        `;
    }).join('') + `
        <tr class="table-info fw-bold">
            <td>Summen</td>
            <td class="text-end">${formatBetrag(summen.linie)}</td>
            ${stichtage.map(datumStr => {
                const summe = summen.tage[datumStr];
                return `
                    <td class="text-end">${formatBetrag(summe.guthaben)}</td>
                    <td class="text-end">${formatBetrag(summe.darlehen_stand)}</td>
                    <td class="text-end">${formatBetrag(summe.freie_linie)}</td>
                `;
            }).join('')}
        </tr>
    `;
    
    // Info-Text aktualisieren
    document.getElementById('zeitverlaufInfo').textContent = 
        `${konten.length} Konten, ${stichtage.length} Tage angezeigt`;
}

// Fehlermeldung anzeigen
function showError(message) {
    alert('Fehler: ' + message);
}

// Event Listener beim Laden
document.addEventListener('DOMContentLoaded', function() {
    // Zeitverlauf laden
    loadZeitverlauf();
    
    // Filter Event Listener
    document.getElementById('tageFilter').addEventListener('change', loadZeitverlauf);
});
