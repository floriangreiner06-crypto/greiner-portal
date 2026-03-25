function formatBetrag(value) {
    const amount = Number(value || 0);
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amount);
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

function showAlert(message, level) {
    const host = document.getElementById('alert-placeholder');
    if (!host) return;
    const type = level || 'info';
    host.innerHTML =
        '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        escapeHtml(message) +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';
}

let kontenRows = [];

function renderRows() {
    const tbody = document.getElementById('tbody-konten');
    if (!tbody) return;
    if (!kontenRows.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">Keine Konten gefunden.</td></tr>';
        return;
    }

    tbody.innerHTML = kontenRows.map(function (k) {
        const aktiv = !!k.aktiv;
        const saldo = Number(k.saldo || 0);
        const kreditlinie = Number(k.kreditlinie || 0);
        const verfuegbar = saldo + kreditlinie;
        return '<tr>' +
            '<td><span class="badge ' + (aktiv ? 'badge-aktiv' : 'badge-inaktiv') + '">' + (aktiv ? 'Aktiv' : 'Inaktiv') + '</span></td>' +
            '<td>' + escapeHtml(k.bank_name || '-') + '</td>' +
            '<td>' + escapeHtml(k.kontoname || '-') + '</td>' +
            '<td><code>' + escapeHtml(k.iban || '-') + '</code></td>' +
            '<td class="num ' + (saldo >= 0 ? 'text-success' : 'text-danger') + '">' + formatBetrag(saldo) + '</td>' +
            '<td class="num">' + formatBetrag(kreditlinie) + '</td>' +
            '<td class="num ' + (verfuegbar >= 0 ? 'text-success' : 'text-danger') + '">' + formatBetrag(verfuegbar) + '</td>' +
            '<td class="text-end"><button type="button" class="btn btn-sm btn-outline-primary btn-edit" data-id="' + k.id + '"><i class="bi bi-pencil me-1"></i>Bearbeiten</button></td>' +
            '</tr>';
    }).join('');

    tbody.querySelectorAll('.btn-edit').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const kontoId = Number(this.dataset.id);
            openEditModal(kontoId);
        });
    });
}

async function loadKonten() {
    try {
        const response = await fetch('/api/bankenspiegel/konten', { credentials: 'same-origin' });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Konten konnten nicht geladen werden.');
        }
        kontenRows = data.konten || [];
        renderRows();
    } catch (error) {
        showAlert(error.message || 'Fehler beim Laden der Konten.', 'danger');
    }
}

function openEditModal(kontoId) {
    const row = kontenRows.find(function (k) { return Number(k.id) === Number(kontoId); });
    if (!row) return;
    document.getElementById('edit-konto-id').value = String(row.id || '');
    document.getElementById('edit-kontoname').value = row.kontoname || '';
    document.getElementById('edit-bank-id').value = row.bank_id || '';
    document.getElementById('edit-iban').value = row.iban || '';
    document.getElementById('edit-kreditlinie').value = row.kreditlinie || 0;
    document.getElementById('edit-kontoinhaber').value = row.kontoinhaber || '';
    document.getElementById('edit-sort-order').value = row.sort_order || 999;
    document.getElementById('edit-aktiv').checked = !!row.aktiv;
    const modal = new bootstrap.Modal(document.getElementById('modalEdit'));
    modal.show();
}

function initEvents() {
    const reloadBtn = document.getElementById('btn-reload');
    if (reloadBtn) reloadBtn.addEventListener('click', loadKonten);

    const saveBtn = document.getElementById('btn-save');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            showAlert('Speichern ist in dieser Iteration noch nicht aktiviert. Bitte API-Update für Bearbeiten ergänzen.', 'warning');
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    initEvents();
    loadKonten();
});
