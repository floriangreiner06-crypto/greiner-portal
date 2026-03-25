/**
 * VKL-Verkaufsdashboard – ruhige, sachliche KPI-Ansicht
 */
(function () {
  'use strict';

  function ampelClass(a) {
    if (a === 'green') return 'bg-success';
    if (a === 'yellow') return 'bg-warning text-dark';
    if (a === 'red') return 'bg-danger';
    return 'bg-secondary';
  }

  function fmtEuro(n) {
    if (n == null || Number.isNaN(n)) return '–';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function setProgress(id, pct) {
    var el = document.getElementById(id);
    if (!el) return;
    var p = Math.max(0, Math.min(140, Number(pct) || 0));
    el.style.width = Math.min(100, p) + '%';
  }

  function sumDb(section) {
    if (!section) return 0;
    return (section.db_nw || 0) + (section.db_gw || 0) + (section.db_tv || 0);
  }

  function renderDbMarkenTable(rows) {
    var tbody = document.querySelector('#tbl-db-marken tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center">keine Daten</td></tr>';
      return;
    }
    var order = ['Opel', 'Hyundai', 'Leapmotor'];
    var filtered = rows.filter(function (r) { return order.indexOf(r.marke) !== -1; });
    rows = filtered.length ? filtered : rows.slice();
    rows.sort(function (a, b) {
      var ai = order.indexOf(a.marke);
      var bi = order.indexOf(b.marke);
      if (ai === -1 && bi === -1) return String(a.marke || '').localeCompare(String(b.marke || ''));
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
    var sumNw = 0, sumTv = 0, sumGw = 0, sumAll = 0, sumStk = 0;
    var sumStkNw = 0, sumStkTv = 0, sumStkGw = 0;
    rows.forEach(function (r) {
      var dbNw = Number(r.db_nw || 0);
      var dbTv = Number(r.db_tv || 0);
      var dbGw = Number(r.db_gw || 0);
      var dbSum = Number(r.db_summe || (dbNw + dbTv + dbGw));
      var stkNw = Number(r.stueck_nw || 0);
      var stkTv = Number(r.stueck_tv || 0);
      var stkGw = Number(r.stueck_gw || 0);
      var stk = Number(r.stueck_summe || (stkNw + stkTv + stkGw));
      var dbPro = Number(r.db_pro_stueck || (stk > 0 ? dbSum / stk : 0));
      var dbProNw = Number(r.db_pro_stueck_nw || (stkNw > 0 ? dbNw / stkNw : 0));
      var dbProTv = Number(r.db_pro_stueck_tv || (stkTv > 0 ? dbTv / stkTv : 0));
      var dbProGw = Number(r.db_pro_stueck_gw || (stkGw > 0 ? dbGw / stkGw : 0));
      sumNw += dbNw;
      sumTv += dbTv;
      sumGw += dbGw;
      sumAll += dbSum;
      sumStk += stk;
      sumStkNw += stkNw;
      sumStkTv += stkTv;
      sumStkGw += stkGw;
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (r.marke || '') + '</td>' +
        '<td class="text-end">' + fmtEuro(dbNw) + '<span class="vkl-subcell">' + fmtEuro(dbProNw) + '/Stk</span></td>' +
        '<td class="text-end">' + fmtEuro(dbTv) + '<span class="vkl-subcell">' + fmtEuro(dbProTv) + '/Stk</span></td>' +
        '<td class="text-end">' + fmtEuro(dbGw) + '<span class="vkl-subcell">' + fmtEuro(dbProGw) + '/Stk</span></td>' +
        '<td class="text-end">' + fmtEuro(dbSum) + '</td>' +
        '<td class="text-end">' + fmtEuro(dbPro) + '<span class="vkl-subcell">gesamt</span></td>';
      tbody.appendChild(tr);
    });
    var totalDbPerStk = sumStk > 0 ? sumAll / sumStk : 0;
    var totalNwPerStk = sumStkNw > 0 ? sumNw / sumStkNw : 0;
    var totalTvPerStk = sumStkTv > 0 ? sumTv / sumStkTv : 0;
    var totalGwPerStk = sumStkGw > 0 ? sumGw / sumStkGw : 0;
    var total = document.createElement('tr');
    total.style.fontWeight = '700';
    total.innerHTML =
      '<td>Gesamt</td>' +
      '<td class="text-end">' + fmtEuro(sumNw) + '<span class="vkl-subcell">' + fmtEuro(totalNwPerStk) + '/Stk</span></td>' +
      '<td class="text-end">' + fmtEuro(sumTv) + '<span class="vkl-subcell">' + fmtEuro(totalTvPerStk) + '/Stk</span></td>' +
      '<td class="text-end">' + fmtEuro(sumGw) + '<span class="vkl-subcell">' + fmtEuro(totalGwPerStk) + '/Stk</span></td>' +
      '<td class="text-end">' + fmtEuro(sumAll) + '</td>' +
      '<td class="text-end">' + fmtEuro(totalDbPerStk) + '</td>';
    tbody.appendChild(total);
  }

  function renderForecast(f) {
    var totalOffen = (f && f.anzahl) || 0;
    var operativ = (f && f.anzahl_operativ_bis_180_tage) || 0;
    var altlasten = (f && f.anzahl_altlasten_ueber_180_tage) || 0;
    setText('kpi-forecast-offen', String(totalOffen));
    setText('kpi-forecast-breakdown',
      'Operativ ' + operativ +
      ' · Altlasten ' + altlasten +
      ' | NW ' + ((f && f.nw) || 0) +
      ' · GW ' + ((f && f.gw) || 0) +
      ' · V/T ' + ((f && f.tv) || 0)
    );
    setText('kpi-forecast-umsatz', fmtEuro(f && f.umsatz_brutto));
    var note = document.getElementById('forecast-note');
    if (note) {
      var basis = (f && f.datengrundlage) ? f.datengrundlage : 'Datengrundlage nicht verfügbar';
      var old = (f && typeof f.anzahl_offen_ueber_180_tage === 'number') ? f.anzahl_offen_ueber_180_tage : 0;
      var oldest = (f && f.aeltester_offener_vertrag) ? f.aeltester_offener_vertrag : 'n/a';
      note.textContent = basis + ' | >180 Tage offen: ' + old + ' | ältester Vertrag: ' + oldest;
    }

    var tbody = document.querySelector('#tbl-forecast-marken tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    var rows = (f && f.marken) ? f.marken.slice(0, 3) : [];
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="2" class="text-muted text-center">keine offenen Aufträge</td></tr>';
      return;
    }
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td>' + (r.marke || '') + '</td><td class="text-end">' + (r.anzahl || 0) + '</td>';
      tbody.appendChild(tr);
    });
  }

  var ytdMode = localStorage.getItem('vklYtdMode') || 'calendar';

  function updateYtdButtons(mode) {
    var c = document.getElementById('btn-ytd-calendar');
    var f = document.getElementById('btn-ytd-fiscal');
    if (c) c.className = 'btn ' + (mode === 'calendar' ? 'btn-secondary' : 'btn-outline-secondary');
    if (f) f.className = 'btn ' + (mode === 'fiscal' ? 'btn-secondary' : 'btn-outline-secondary');
  }

  function render(data) {
    if (!data || !data.success) {
      setText('dash-error', (data && data.error) || 'Unbekannter Fehler');
      var err = document.getElementById('dash-error');
      if (err) err.classList.remove('d-none');
      return;
    }

    var st = data.stand || {};
    var ytd = data.ytd || {};
    setText('dash-stand', (st.monat || '') + '/' + (st.jahr || ''));
    setText('ytd-mode-label', 'YTD: ' + (ytd.label || 'Kalenderjahr') + ' (' + (ytd.start || '-') + ' bis ' + (ytd.ende || '-') + ')');
    updateYtdButtons(ytd.mode || ytdMode);

    var aeM = data.auftragseingang_monat || {};
    var aeY = data.auftragseingang_ytd || {};
    var alM = data.auslieferung_monat || {};
    var alY = data.auslieferung_ytd || {};

    var aeTotal = (aeM.stueck_nw || 0) + (aeM.stueck_gw || 0) + (aeM.stueck_tv || 0);
    var alTotal = (alM.stueck_nw || 0) + (alM.stueck_gw || 0) + (alM.stueck_tv || 0);

    setText('kpi-ae-gesamt', String(aeTotal));
    setText('kpi-ae-breakdown', 'NW ' + (aeM.stueck_nw || 0) + ' · GW ' + (aeM.stueck_gw || 0) + ' · V/T ' + (aeM.stueck_tv || 0));
    setText('kpi-ae-ytd', String((aeY.stueck_nw || 0) + (aeY.stueck_gw || 0) + (aeY.stueck_tv || 0)) + ' Stk');

    setText('kpi-al-gesamt', String(alTotal));
    setText('kpi-al-breakdown', 'NW ' + (alM.stueck_nw || 0) + ' · GW ' + (alM.stueck_gw || 0) + ' · V/T ' + (alM.stueck_tv || 0));
    setText('kpi-al-db', fmtEuro(sumDb(alM)));
    setText('kpi-al-ytd', String((alY.stueck_nw || 0) + (alY.stueck_gw || 0) + (alY.stueck_tv || 0)) + ' Stk');

    renderDbMarkenTable((data.db_marken_monat || {}).marken || []);
    renderForecast(data.forecast_offen || {});

    var zm = data.ziele_monat || {};
    var y = data.ziele_jahr_klein || {};

    var badgeNw = document.getElementById('badge-nw-trend');
    var badgeGw = document.getElementById('badge-gw-trend');
    if (badgeNw) {
      badgeNw.className = 'badge ' + ampelClass(zm.ampel_nw);
      badgeNw.textContent = 'NW ' + (zm.pct_nw_trend_werktag != null ? zm.pct_nw_trend_werktag + '%' : '–');
    }
    if (badgeGw) {
      badgeGw.className = 'badge ' + ampelClass(zm.ampel_gw);
      badgeGw.textContent = 'GW ' + (zm.pct_gw_trend_werktag != null ? zm.pct_gw_trend_werktag + '%' : '–');
    }

    setProgress('goal-nw-bar', zm.pct_nw_trend_werktag);
    setProgress('goal-gw-bar', zm.pct_gw_trend_werktag);
    setText('goal-nw-text', (zm.ist_nw != null ? zm.ist_nw : '–') + '/' + (zm.ziel_nw_bis_heute_werktag != null ? Number(zm.ziel_nw_bis_heute_werktag).toFixed(1) : '–'));
    setText('goal-gw-text', (zm.ist_gw != null ? zm.ist_gw : '–') + '/' + (zm.ziel_gw_bis_heute_werktag != null ? Number(zm.ziel_gw_bis_heute_werktag).toFixed(1) : '–'));

    setText('kpi-jahr-klein',
      'YTD Trend NW ' + (y.pct_nw_trend != null ? y.pct_nw_trend + '%' : '–') +
      ' · GW ' + (y.pct_gw_trend != null ? y.pct_gw_trend + '%' : '–') +
      ' | Soll YTD (WT): ' +
      (y.soll_nw_ytd_werktag != null ? Number(y.soll_nw_ytd_werktag).toFixed(1) : '–') +
      ' / ' +
      (y.soll_gw_ytd_werktag != null ? Number(y.soll_gw_ytd_werktag).toFixed(1) : '–'));

    var rowAfa = document.getElementById('row-afa');
    if (rowAfa && Object.prototype.hasOwnProperty.call(data, 'afa')) {
      rowAfa.classList.remove('d-none');
      var afa = data.afa;
      setText('kpi-afa', afa && !afa.error ? String(afa.anzahl_standzeit_darueber || 0) : '–');
    }

    var rowEkf = document.getElementById('row-ekf');
    var tbody = document.querySelector('#tbl-top-zins tbody');
    if (rowEkf && Object.prototype.hasOwnProperty.call(data, 'einkaufsfinanzierung')) {
      rowEkf.classList.remove('d-none');
      var ekf = data.einkaufsfinanzierung;
      if (ekf && !ekf.error && tbody) {
        setText('kpi-ekf-warn', (ekf.warnungen_kritisch_anzahl || 0) + '/' + (ekf.warnungen_anzahl || 0));
        tbody.innerHTML = '';
        var topRows = (ekf.top_zinsverursacher || []);
        if (!topRows.length) {
          var empty = document.createElement('tr');
          empty.innerHTML = '<td colspan="4" class="text-muted text-center">keine Daten</td>';
          tbody.appendChild(empty);
          return;
        }
        topRows.forEach(function (r) {
          var tr = document.createElement('tr');
          tr.innerHTML =
            '<td>' + (r.vin || '') + '</td>' +
            '<td>' + (r.modell || '') + '</td>' +
            '<td class="text-end">' + fmtEuro(r.saldo) + '</td>' +
            '<td>' + (r.zinsfreiheit != null ? r.zinsfreiheit + ' T' : '–') + '</td>';
          tbody.appendChild(tr);
        });
      }
    }
  }

  function load(mode) {
    ytdMode = mode || ytdMode || 'calendar';
    localStorage.setItem('vklYtdMode', ytdMode);
    updateYtdButtons(ytdMode);
    fetch('/api/verkauf/dashboard-vkl?ytd_mode=' + encodeURIComponent(ytdMode), { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (res) {
        var ct = res.headers.get('Content-Type') || '';
        if (!ct.includes('application/json')) {
          return res.text().then(function () {
            throw new Error('Antwort ist kein JSON (Anmeldung abgelaufen oder Route fehlt).');
          });
        }
        return res.json();
      })
      .then(render)
      .catch(function (e) {
        setText('dash-error', e.message || String(e));
        var err = document.getElementById('dash-error');
        if (err) err.classList.remove('d-none');
      });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var btnCal = document.getElementById('btn-ytd-calendar');
    var btnFis = document.getElementById('btn-ytd-fiscal');
    if (btnCal) btnCal.addEventListener('click', function () { load('calendar'); });
    if (btnFis) btnFis.addEventListener('click', function () { load('fiscal'); });
    load(ytdMode);
  });
})();
