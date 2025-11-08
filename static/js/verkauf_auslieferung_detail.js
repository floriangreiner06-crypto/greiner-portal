// Auslieferungen Detail - JavaScript (KORRIGIERT TAG 19)
// Kategorisierung nach dealer_vehicle_type, NICHT nach Marke!
let currentMonth = 11;
let currentYear = 2025;
let currentLocation = '';

document.addEventListener('DOMContentLoaded', function() {
    // Event Listeners
    document.getElementById('loadBtn').addEventListener('click', loadData);

    // Initial Load
    loadData();
});

async function loadData() {
    currentMonth = document.getElementById('monthSelect').value;
    currentYear = document.getElementById('yearSelect').value;
    currentLocation = document.getElementById('locationSelect').value;

    await loadSummary();
    await loadDetails();
}

async function loadSummary() {
    const container = document.getElementById('summaryContainer');
    container.innerHTML = '<div class="col-12 text-center"><div class="spinner-border"></div></div>';

    try {
        const response = await fetch(`/api/verkauf/auslieferung/summary?month=${currentMonth}&year=${currentYear}`);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="col-12"><div class="alert alert-danger">${data.error}</div></div>`;
            return;
        }

        // KORRIGIERT: Kategorisierung nach dealer_vehicle_type!
        let neuwagen = { gesamt: 0, neu: 0, test_vorfuehr: 0, gebraucht: 0, umsatz: 0 };
        let testvorfuehr = { gesamt: 0, neu: 0, test_vorfuehr: 0, gebraucht: 0, umsatz: 0 };
        let gebrauchtwagen = { gesamt: 0, neu: 0, test_vorfuehr: 0, gebraucht: 0, umsatz: 0 };
        let opel = { gesamt: 0, neu: 0, test_vorfuehr: 0, gebraucht: 0, umsatz: 0 };
        let hyundai = { gesamt: 0, neu: 0, test_vorfuehr: 0, gebraucht: 0, umsatz: 0 };

        data.summary.forEach(marke => {
            // Neuwagen (alle N)
            neuwagen.gesamt += marke.neu;
            neuwagen.neu += marke.neu;
            neuwagen.umsatz += (marke.umsatz_gesamt / marke.gesamt) * marke.neu;

            // Test/Vorführ (alle T/V)
            testvorfuehr.gesamt += marke.test_vorfuehr;
            testvorfuehr.test_vorfuehr += marke.test_vorfuehr;
            testvorfuehr.umsatz += (marke.umsatz_gesamt / marke.gesamt) * marke.test_vorfuehr;

            // Gebrauchtwagen (alle G/D)
            gebrauchtwagen.gesamt += marke.gebraucht;
            gebrauchtwagen.gebraucht += marke.gebraucht;
            gebrauchtwagen.umsatz += (marke.umsatz_gesamt / marke.gesamt) * marke.gebraucht;

            // Opel (Info-Karte)
            if (marke.make_number === 40) {
                opel.gesamt += marke.gesamt;
                opel.neu += marke.neu;
                opel.test_vorfuehr += marke.test_vorfuehr;
                opel.gebraucht += marke.gebraucht;
                opel.umsatz += marke.umsatz_gesamt;
            }

            // Hyundai (Info-Karte)
            if (marke.make_number === 27) {
                hyundai.gesamt += marke.gesamt;
                hyundai.neu += marke.neu;
                hyundai.test_vorfuehr += marke.test_vorfuehr;
                hyundai.gebraucht += marke.gebraucht;
                hyundai.umsatz += marke.umsatz_gesamt;
            }
        });

        let html = '<div class="row">';

        // 1. Neuwagen (alle N)
        html += `
            <div class="col-md-2">
                <div class="card text-center border-success">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1"><strong>Neuwagen</strong></h6>
                        <small class="text-muted d-block mb-1">(Status: N)</small>
                        <h3 class="text-success mb-2"><strong>${neuwagen.gesamt}</strong></h3>
                        <div class="d-flex flex-column gap-1">
                            <span class="badge bg-success">Neu: ${neuwagen.neu}</span>
                        </div>
                        <p class="mt-2 mb-0 text-muted small">${formatCurrency(neuwagen.umsatz)}</p>
                    </div>
                </div>
            </div>
        `;

        // 2. Test/Vorführ (alle T/V)
        html += `
            <div class="col-md-2">
                <div class="card text-center border-warning">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1"><strong>Test/Vorführ</strong></h6>
                        <small class="text-muted d-block mb-1">(Status: T/V)</small>
                        <h3 class="text-warning mb-2"><strong>${testvorfuehr.gesamt}</strong></h3>
                        <div class="d-flex flex-column gap-1">
                            <span class="badge bg-warning text-dark">T/V: ${testvorfuehr.test_vorfuehr}</span>
                        </div>
                        <p class="mt-2 mb-0 text-muted small">${formatCurrency(testvorfuehr.umsatz)}</p>
                    </div>
                </div>
            </div>
        `;

        // 3. Gebrauchtwagen (alle G/D)
        html += `
            <div class="col-md-2">
                <div class="card text-center border-secondary">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1"><strong>Gebrauchtwagen</strong></h6>
                        <small class="text-muted d-block mb-1">(Status: G/D)</small>
                        <h3 class="text-secondary mb-2"><strong>${gebrauchtwagen.gesamt}</strong></h3>
                        <div class="d-flex flex-column gap-1">
                            <span class="badge bg-secondary">Gebr.: ${gebrauchtwagen.gebraucht}</span>
                        </div>
                        <p class="mt-2 mb-0 text-muted small">${formatCurrency(gebrauchtwagen.umsatz)}</p>
                    </div>
                </div>
            </div>
        `;

        // 4. Opel (Info-Karte)
        if (opel.gesamt > 0) {
            html += `
                <div class="col-md-2">
                    <div class="card text-center border-primary">
                        <div class="card-body p-2">
                            <h6 class="card-title mb-1">Opel</h6>
                            <small class="text-muted d-block mb-1">(alle Status)</small>
                            <h3 class="text-primary mb-2">${opel.gesamt}</h3>
                            <div class="d-flex flex-column gap-1">
                                <span class="badge bg-success">Neu: ${opel.neu}</span>
                                <span class="badge bg-warning text-dark">T/V: ${opel.test_vorfuehr}</span>
                                <span class="badge bg-secondary">Gebr.: ${opel.gebraucht}</span>
                            </div>
                            <p class="mt-2 mb-0 text-muted small">${formatCurrency(opel.umsatz)}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // 5. Hyundai (Info-Karte)
        if (hyundai.gesamt > 0) {
            html += `
                <div class="col-md-2">
                    <div class="card text-center border-info">
                        <div class="card-body p-2">
                            <h6 class="card-title mb-1">Hyundai</h6>
                            <small class="text-muted d-block mb-1">(alle Status)</small>
                            <h3 class="text-info mb-2">${hyundai.gesamt}</h3>
                            <div class="d-flex flex-column gap-1">
                                <span class="badge bg-success">Neu: ${hyundai.neu}</span>
                                <span class="badge bg-warning text-dark">T/V: ${hyundai.test_vorfuehr}</span>
                                <span class="badge bg-secondary">Gebr.: ${hyundai.gebraucht}</span>
                            </div>
                            <p class="mt-2 mb-0 text-muted small">${formatCurrency(hyundai.umsatz)}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // 6. Gesamt
        const gesamt_anzahl = neuwagen.gesamt + testvorfuehr.gesamt + gebrauchtwagen.gesamt;
        const gesamt_umsatz = neuwagen.umsatz + testvorfuehr.umsatz + gebrauchtwagen.umsatz;

        html += `
            <div class="col-md-2">
                <div class="card text-center border-dark">
                    <div class="card-body p-2">
                        <h6 class="card-title mb-1"><strong>GESAMT</strong></h6>
                        <small class="text-muted d-block mb-1">&nbsp;</small>
                        <h3 class="text-dark mb-2"><strong>${gesamt_anzahl}</strong></h3>
                        <div class="d-flex flex-column gap-1">
                            <span class="badge bg-success">Neu: ${neuwagen.gesamt}</span>
                            <span class="badge bg-warning text-dark">T/V: ${testvorfuehr.gesamt}</span>
                            <span class="badge bg-secondary">Gebr.: ${gebrauchtwagen.gesamt}</span>
                        </div>
                        <p class="mt-2 mb-0 text-muted small"><strong>${formatCurrency(gesamt_umsatz)}</strong></p>
                    </div>
                </div>
            </div>
        `;

        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="col-12"><div class="alert alert-danger">Fehler: ${error.message}</div></div>`;
    }
}

async function loadDetails() {
    const container = document.getElementById('verkauferContainer');
    container.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';

    try {
        let url = `/api/verkauf/auslieferung/detail?month=${currentMonth}&year=${currentYear}`;
        if (currentLocation) {
            url += `&location=${encodeURIComponent(currentLocation)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }

        if (!data.verkaufer || data.verkaufer.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Keine Auslieferungen für diesen Zeitraum</div>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table table-striped table-hover">';
        html += `
            <thead class="table-dark">
                <tr>
                    <th>Verkäufer</th>
                    <th class="text-center">Neu</th>
                    <th class="text-center">Test/Vorführ</th>
                    <th class="text-center">Gebraucht</th>
                    <th class="text-center">Gesamt</th>
                    <th>Modelle</th>
                </tr>
            </thead>
            <tbody>
        `;

        data.verkaufer.forEach(vk => {
            html += `
                <tr>
                    <td><strong>${vk.verkaufer_name || 'Unbekannt'}</strong></td>
                    <td class="text-center">
                        <span class="badge bg-success">${vk.summe_neu}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-warning text-dark">${vk.summe_test_vorfuehr}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-secondary">${vk.summe_gebraucht}</span>
                    </td>
                    <td class="text-center">
                        <strong>${vk.summe_gesamt}</strong>
                    </td>
                    <td>
                        ${formatModelle(vk)}
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;

    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">Fehler: ${error.message}</div>`;
    }
}

function formatModelle(vk) {
    let html = '';

    // Neuwagen
    if (vk.neu.length > 0) {
        html += '<div class="mb-2"><strong class="text-success">Neuwagen:</strong><ul class="mb-0">';
        vk.neu.forEach(m => {
            html += `<li>${m.modell} (${m.anzahl}x)</li>`;
        });
        html += '</ul></div>';
    }

    // Test/Vorführ
    if (vk.test_vorfuehr.length > 0) {
        html += '<div class="mb-2"><strong class="text-warning">Test/Vorführ:</strong><ul class="mb-0">';
        vk.test_vorfuehr.forEach(m => {
            html += `<li>${m.modell} (${m.anzahl}x)</li>`;
        });
        html += '</ul></div>';
    }

    // Gebraucht
    if (vk.gebraucht.length > 0) {
        html += '<div class="mb-2"><strong class="text-secondary">Gebraucht:</strong><ul class="mb-0">';
        vk.gebraucht.forEach(m => {
            html += `<li>${m.modell} (${m.anzahl}x)</li>`;
        });
        html += '</ul></div>';
    }

    return html || '<em class="text-muted">Keine Daten</em>';
}

function formatCurrency(value) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}
