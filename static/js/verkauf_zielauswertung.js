(function(){
  'use strict';

  function setText(id, text){
    var el = document.getElementById(id);
    if(el) el.textContent = text;
  }

  function setBar(id, pct){
    var el = document.getElementById(id);
    if(!el) return;
    var p = Math.max(0, Math.min(140, Number(pct) || 0));
    el.style.width = Math.min(100, p) + '%';
  }

  function pctColor(p){
    if (p == null) return '#64748b';
    if (p >= 100) return '#15803d';
    if (p >= 90) return '#b45309';
    return '#b91c1c';
  }

  fetch('/api/verkauf/dashboard-vkl', { credentials: 'same-origin', headers: { Accept: 'application/json' } })
    .then(function(res){
      var ct = res.headers.get('Content-Type') || '';
      if(!ct.includes('application/json')) throw new Error('Keine JSON-Antwort erhalten.');
      return res.json();
    })
    .then(function(data){
      if(!data || !data.success) throw new Error((data && data.error) || 'Fehler beim Laden');
      var z = data.ziele_monat || {};
      var y = data.ziele_jahr_klein || {};

      setText('zw-monat-nw', (z.ist_nw || 0) + ' / ' + (z.ziel_nw_konzern || 0));
      setText('zw-monat-gw', (z.ist_gw || 0) + ' / ' + (z.ziel_gw_konzern || 0));

      setBar('zw-bar-nw', z.pct_nw_trend_werktag);
      setBar('zw-bar-gw', z.pct_gw_trend_werktag);

      setText('zw-bar-nw-text', 'NW Trend ' + (z.pct_nw_trend_werktag != null ? z.pct_nw_trend_werktag + '%' : '–') +
        ' (Soll bis heute: ' + (z.ziel_nw_bis_heute_werktag != null ? Number(z.ziel_nw_bis_heute_werktag).toFixed(1) : '–') + ')');
      setText('zw-bar-gw-text', 'GW Trend ' + (z.pct_gw_trend_werktag != null ? z.pct_gw_trend_werktag + '%' : '–') +
        ' (Soll bis heute: ' + (z.ziel_gw_bis_heute_werktag != null ? Number(z.ziel_gw_bis_heute_werktag).toFixed(1) : '–') + ')');

      setText('zw-ytd-nw', (y.ist_nw_ytd != null ? y.ist_nw_ytd : '–') + ' / ' + (y.soll_nw_ytd_werktag != null ? Number(y.soll_nw_ytd_werktag).toFixed(1) : '–'));
      setText('zw-ytd-gw', (y.ist_gw_ytd != null ? y.ist_gw_ytd : '–') + ' / ' + (y.soll_gw_ytd_werktag != null ? Number(y.soll_gw_ytd_werktag).toFixed(1) : '–'));
      setText('zw-ytd-nw-pct', y.pct_nw_trend != null ? y.pct_nw_trend + '%' : '–');
      setText('zw-ytd-gw-pct', y.pct_gw_trend != null ? y.pct_gw_trend + '%' : '–');

      var nwPct = document.getElementById('zw-ytd-nw-pct');
      var gwPct = document.getElementById('zw-ytd-gw-pct');
      if(nwPct) nwPct.style.color = pctColor(y.pct_nw_trend);
      if(gwPct) gwPct.style.color = pctColor(y.pct_gw_trend);
    })
    .catch(function(err){
      setText('ziel-error', err.message || String(err));
      var e = document.getElementById('ziel-error');
      if(e) e.classList.remove('d-none');
    });
})();
