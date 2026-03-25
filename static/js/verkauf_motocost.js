(function () {
  'use strict';

  let currentPage = 1;
  let currentPageSize = 50;
  let lastTotal = 0;
  let optionsLoaded = false;

  function fmtNumber(v) {
    if (v === null || v === undefined || v === '') return '–';
    const n = Number(v);
    if (Number.isNaN(n)) return String(v);
    return n.toLocaleString('de-DE');
  }

  function fmtEz(v) {
    if (v === null || v === undefined || v === '') return '–';
    const n = Number(v);
    if (!Number.isNaN(n) && n > 1000000000) {
      const d = new Date(n);
      return String(d.getMonth() + 1).padStart(2, '0') + '/' + d.getFullYear();
    }
    return String(v);
  }

  function selectedValues(id) {
    const el = document.getElementById(id);
    return Array.from(el.selectedOptions || []).map(function (o) { return o.value; }).filter(Boolean);
  }

  function fillMultiSelect(id, values) {
    const el = document.getElementById(id);
    const selected = selectedValues(id);
    el.innerHTML = '';
    (values || []).forEach(function (v) {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      if (selected.includes(v)) opt.selected = true;
      el.appendChild(opt);
    });
  }

  function showAlert(message, type) {
    const el = document.getElementById('motocost-alert');
    el.className = 'alert py-2 alert-' + (type || 'info');
    el.textContent = message;
    el.classList.remove('d-none');
  }

  function hideAlert() {
    const el = document.getElementById('motocost-alert');
    el.classList.add('d-none');
  }

  function render(rows) {
    const tbody = document.querySelector('#motocost-table tbody');
    tbody.innerHTML = '';
    rows.forEach(function (row) {
      const tr = document.createElement('tr');
      tr.innerHTML = [
        '<td>' + (row.bild ? '<img src="' + row.bild + '" alt="" style="width:54px;height:38px;object-fit:cover;border-radius:4px;">' : '–') + '</td>',
        '<td>' + (row.marke || '–') + '</td>',
        '<td>' + (row.modell || '–') + '</td>',
        '<td class="text-end">' + fmtNumber(row.preis) + '</td>',
        '<td class="text-end">' + fmtNumber(row.marge) + '</td>',
        '<td>' + fmtEz(row.ez) + '</td>',
        '<td class="text-end">' + fmtNumber(row.km) + '</td>',
        '<td>' + (row.problem || '–') + '</td>',
        '<td>' + (row.kraftstoff || '–') + '</td>',
        '<td>' + (row.getriebe || '–') + '</td>',
        '<td>' + (row.plattform || '–') + '</td>',
        '<td>' + (row.link ? '<a href="' + row.link + '" target="_blank" rel="noopener">Öffnen</a>' : '–') + '</td>'
      ].join('');
      tbody.appendChild(tr);
    });
  }

  function setMeta(meta) {
    const el = document.getElementById('motocost-meta');
    if (!meta || !meta.available) {
      el.textContent = 'Noch kein Import vorhanden';
      return;
    }
    el.textContent = 'Import: ' + (meta.imported_at || 'unbekannt') + ' · Zeilen: ' + (meta.row_count || '–') + ' · Quelle: ' + (meta.source || 'unbekannt');
  }

  function buildQueryString() {
    const qs = new URLSearchParams();
    qs.set('page', String(currentPage));
    qs.set('page_size', String(currentPageSize));
    var pairs = [
      ['plattform', selectedValues('f-plattform')],
      ['verkaufsart', selectedValues('f-verkaufsart')],
      ['problem', selectedValues('f-problem')],
      ['land', selectedValues('f-land')],
      ['marke', selectedValues('f-marke')],
      ['kraftstoff', selectedValues('f-kraftstoff')],
      ['getriebe', selectedValues('f-getriebe')],
      ['karosserie', selectedValues('f-karosserie')],
      ['mwst', selectedValues('f-mwst')]
    ];
    pairs.forEach(function (p) {
      if (p[1].length) qs.set(p[0], p[1].join(','));
    });
    [
      ['modell_text', 'f-modell-text'],
      ['km_bis', 'f-km-bis'],
      ['ez_ab', 'f-ez-ab'],
      ['marge_ab', 'f-marge-ab'],
      ['preis_ab', 'f-preis-ab'],
      ['preis_bis', 'f-preis-bis']
    ].forEach(function (it) {
      var v = (document.getElementById(it[1]).value || '').trim();
      if (v) qs.set(it[0], v);
    });
    return qs.toString();
  }

  function updatePageInfo() {
    var from = (currentPage - 1) * currentPageSize + 1;
    var to = Math.min(currentPage * currentPageSize, lastTotal);
    if (lastTotal === 0) { from = 0; to = 0; }
    document.getElementById('motocost-page-info').textContent = 'Seite ' + currentPage + ' · ' + from + '-' + to + ' von ' + lastTotal;
    document.getElementById('motocost-prev').disabled = currentPage <= 1;
    document.getElementById('motocost-next').disabled = currentPage * currentPageSize >= lastTotal;
  }

  async function loadSearch() {
    hideAlert();
    var qs = buildQueryString();
    const res = await fetch('/api/verkauf/motocost/search?' + qs, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
    const ct = (res.headers.get('content-type') || '').toLowerCase();
    if (!ct.includes('application/json')) {
      showAlert('Server hat keine JSON-Antwort geliefert (Session prüfen).', 'danger');
      return null;
    }
    const data = await res.json();
    if (!data.success) {
      showAlert(data.error || 'Laden fehlgeschlagen', 'danger');
      return null;
    }
    render(Array.isArray(data.rows) ? data.rows : []);
    setMeta(data.meta || {});
    lastTotal = Number(data.total || 0);
    updatePageInfo();
    document.getElementById('motocost-benchmark-result').textContent =
      'Treffer: ' + lastTotal + ' · Serverzeit: ' + (data.elapsed_ms || 0) + ' ms';

    if (!optionsLoaded && data.filter_options) {
      fillMultiSelect('f-plattform', data.filter_options.plattformen);
      fillMultiSelect('f-verkaufsart', data.filter_options.verkaufsarten);
      fillMultiSelect('f-problem', data.filter_options.probleme);
      fillMultiSelect('f-land', data.filter_options.laender);
      fillMultiSelect('f-marke', data.filter_options.marken);
      fillMultiSelect('f-kraftstoff', data.filter_options.kraftstoff);
      fillMultiSelect('f-getriebe', data.filter_options.getriebe);
      fillMultiSelect('f-karosserie', data.filter_options.karosserie);
      fillMultiSelect('f-mwst', data.filter_options.mwst);
      optionsLoaded = true;
    }
    return data;
  }

  async function uploadFile() {
    hideAlert();
    const input = document.getElementById('motocost-file');
    const file = input.files && input.files[0];
    if (!file) {
      showAlert('Bitte zuerst eine JSON-Datei auswählen.', 'warning');
      return;
    }
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/verkauf/motocost/import', { method: 'POST', body: fd, credentials: 'same-origin' });
    const ct = (res.headers.get('content-type') || '').toLowerCase();
    if (!ct.includes('application/json')) {
      showAlert('Import fehlgeschlagen: Server-Antwort ist kein JSON.', 'danger');
      return;
    }
    const data = await res.json();
    if (!data.success) {
      showAlert(data.error || 'Import fehlgeschlagen', 'danger');
      return;
    }
    showAlert(data.message || 'Import erfolgreich', 'success');
    currentPage = 1;
    optionsLoaded = false;
    await loadSearch();
  }

  async function runBenchmark() {
    hideAlert();
    const runs = 5;
    const times = [];
    for (let i = 0; i < runs; i++) {
      const t0 = performance.now();
      const data = await loadSearch();
      const t1 = performance.now();
      if (!data) return;
      times.push(t1 - t0);
    }
    const avg = times.reduce(function (a, b) { return a + b; }, 0) / times.length;
    document.getElementById('motocost-benchmark-result').textContent =
      'Benchmark 5x · Ø Clientzeit: ' + avg.toFixed(1) + ' ms · min: ' + Math.min.apply(null, times).toFixed(1) + ' ms · max: ' + Math.max.apply(null, times).toFixed(1) + ' ms';
  }

  document.getElementById('motocost-import').addEventListener('click', uploadFile);
  document.getElementById('motocost-reload').addEventListener('click', function () { currentPage = 1; loadSearch(); });
  document.getElementById('motocost-benchmark').addEventListener('click', runBenchmark);
  document.getElementById('motocost-apply').addEventListener('click', function () { currentPage = 1; loadSearch(); });
  document.getElementById('motocost-reset').addEventListener('click', function () {
    ['f-modell-text', 'f-km-bis', 'f-ez-ab', 'f-marge-ab', 'f-preis-ab', 'f-preis-bis'].forEach(function (id) {
      document.getElementById(id).value = '';
    });
    ['f-plattform', 'f-verkaufsart', 'f-problem', 'f-land', 'f-marke', 'f-kraftstoff', 'f-getriebe', 'f-karosserie', 'f-mwst'].forEach(function (id) {
      Array.from(document.getElementById(id).options).forEach(function (o) { o.selected = false; });
    });
    currentPage = 1;
    loadSearch();
  });
  document.getElementById('f-page-size').addEventListener('change', function (e) {
    currentPageSize = Number(e.target.value || 50);
    currentPage = 1;
    loadSearch();
  });
  document.getElementById('motocost-prev').addEventListener('click', function () {
    if (currentPage > 1) {
      currentPage -= 1;
      loadSearch();
    }
  });
  document.getElementById('motocost-next').addEventListener('click', function () {
    if (currentPage * currentPageSize < lastTotal) {
      currentPage += 1;
      loadSearch();
    }
  });

  loadSearch();
})();
