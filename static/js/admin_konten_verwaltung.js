/**
 * Admin Konten-Verwaltung: Konten laden (alle=1), Bearbeiten-Modal, PATCH speichern.
 */
(function () {
    'use strict';

    let konten = [];
    let banken = [];
    let aktuellesKontoSortOrder = null;

    function fmtEuro(val) {
        if (val === null || val === undefined) return '–';
        return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(val);
    }

    function showAlert(msg, type) {
        type = type || 'danger';
        var el = document.getElementById('alert-placeholder');
        el.innerHTML = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' + msg + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>';
        setTimeout(function () { el.innerHTML = ''; }, 6000);
    }

    function loadBanken() {
        return fetch('/api/bankenspiegel/banken', { credentials: 'same-origin', cache: 'no-store' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success && data.banken) {
                    banken = data.banken;
                }
            });
    }

    function loadKonten() {
        return fetch('/api/bankenspiegel/konten?alle=1', { credentials: 'same-origin', cache: 'no-store' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success && data.konten) {
                    konten = data.konten;
                    renderTable();
                } else {
                    document.getElementById('tbody-konten').innerHTML = '<tr><td colspan="8" class="text-center text-danger">Fehler: ' + (data.error || 'Unbekannt') + '</td></tr>';
                }
            })
            .catch(function (err) {
                document.getElementById('tbody-konten').innerHTML = '<tr><td colspan="8" class="text-center text-danger">Fehler beim Laden</td></tr>';
                showAlert('Konten konnten nicht geladen werden.', 'danger');
            });
    }

    function renderTable() {
        var tbody = document.getElementById('tbody-konten');
        if (konten.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">Keine Konten gefunden.</td></tr>';
            return;
        }
        tbody.innerHTML = konten.map(function (k) {
            var aktiv = k.aktiv !== false;
            var badge = aktiv ? '<span class="badge badge-aktiv">Aktiv</span>' : '<span class="badge badge-inaktiv">Inaktiv</span>';
            var saldo = k.saldo != null ? parseFloat(k.saldo) : 0;
            var saldoClass = saldo >= 0 ? 'text-success' : 'text-danger';
            var verf = k.verfuegbar;
            var verfStr = (verf !== null && verf !== undefined) ? fmtEuro(verf) : '–';
            var verfClass = (verf !== null && verf !== undefined) ? (verf >= 0 ? 'text-success' : 'text-warning') : 'text-muted';
            var kreditStr = (k.kreditlinie && parseFloat(k.kreditlinie) > 0) ? fmtEuro(k.kreditlinie) : '–';
            return '<tr data-id="' + k.id + '">' +
                '<td>' + badge + '</td>' +
                '<td>' + (k.bank_name || '–') + '</td>' +
                '<td>' + (k.kontoname || '–') + '</td>' +
                '<td><code class="small">' + (k.iban || '–') + '</code></td>' +
                '<td class="num ' + saldoClass + '">' + fmtEuro(saldo) + '</td>' +
                '<td class="num">' + kreditStr + '</td>' +
                '<td class="num ' + verfClass + '">' + verfStr + '</td>' +
                '<td><button type="button" class="btn btn-sm btn-outline-primary btn-edit" data-id="' + k.id + '"><i class="bi bi-pencil"></i> Bearbeiten</button></td>' +
                '</tr>';
        }).join('');
    }

    function openEditModal(kontoId) {
        var k = konten.find(function (x) { return x.id === parseInt(kontoId, 10); });
        if (!k) return;
        document.getElementById('edit-konto-id').value = k.id;
        document.getElementById('edit-kontoname').value = k.kontoname || '';
        document.getElementById('edit-iban').value = k.iban || '';
        document.getElementById('edit-kreditlinie').value = (k.kreditlinie != null && k.kreditlinie !== '') ? parseFloat(k.kreditlinie) : '';
        document.getElementById('edit-kontoinhaber').value = k.kontoinhaber || '';
        document.getElementById('edit-sort-order').value = k.sort_order != null ? k.sort_order : 999;
        aktuellesKontoSortOrder = k.sort_order != null ? parseInt(k.sort_order, 10) : 999;
        document.getElementById('edit-aktiv').checked = k.aktiv !== false;

        var sel = document.getElementById('edit-bank-id');
        sel.innerHTML = '<option value="">– Bitte wählen –</option>' + banken.map(function (b) {
            return '<option value="' + b.id + '"' + (b.id === k.bank_id ? ' selected' : '') + '>' + (b.bank_name || 'ID ' + b.id) + '</option>';
        }).join('');

        var modal = new bootstrap.Modal(document.getElementById('modalEdit'));
        modal.show();
    }

    function saveEdit() {
        var id = document.getElementById('edit-konto-id').value;
        if (!id) return;
        var neuesSortOrder = parseInt(document.getElementById('edit-sort-order').value, 10) || 999;
        var payload = {
            kontoname: document.getElementById('edit-kontoname').value.trim(),
            iban: document.getElementById('edit-iban').value.trim() || null,
            bank_id: document.getElementById('edit-bank-id').value ? parseInt(document.getElementById('edit-bank-id').value, 10) : null,
            kreditlinie: document.getElementById('edit-kreditlinie').value !== '' ? parseFloat(document.getElementById('edit-kreditlinie').value) : 0,
            kontoinhaber: document.getElementById('edit-kontoinhaber').value.trim() || null,
            aktiv: document.getElementById('edit-aktiv').checked
        };
        if (aktuellesKontoSortOrder === null || neuesSortOrder !== aktuellesKontoSortOrder) {
            payload.sort_order = neuesSortOrder;
        }
        if (!payload.kontoname) {
            showAlert('Bitte Kontoname angeben.', 'warning');
            return;
        }

        var btn = document.getElementById('btn-save');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Speichern …';

        fetch('/api/bankenspiegel/konten/' + id, {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
            .then(function (res) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Speichern';
                if (res.ok && res.data.success) {
                    bootstrap.Modal.getInstance(document.getElementById('modalEdit')).hide();
                    loadKonten();
                    showAlert('Konto gespeichert.', 'success');
                } else {
                    showAlert(res.data.error || 'Fehler beim Speichern', 'danger');
                }
            })
            .catch(function () {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Speichern';
                showAlert('Netzwerkfehler beim Speichern.', 'danger');
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        loadBanken().then(loadKonten);

        document.getElementById('btn-reload').addEventListener('click', function () {
            loadKonten();
        });

        document.getElementById('tbody-konten').addEventListener('click', function (e) {
            var btn = e.target.closest('.btn-edit');
            if (btn && btn.dataset.id) openEditModal(btn.dataset.id);
        });

        document.getElementById('btn-save').addEventListener('click', saveEdit);
    });
})();
