/* Ported verbatim dari inline <script> webgis2.html (WebGis2View). Membaca config dari #wg2-config; fetch geojson/history via path relatif (diproksi Next). */
(function () {
  var CFG = JSON.parse(document.getElementById('wg2-config').textContent);
  var INDS = CFG.indikator || [];
  // Palet bawaan (hijau). RAMP diset ulang per indikator aktif di render()
  // dari meta.ramp (palet pilihan admin di Data Capaian).
  var DEFAULT_RAMP = ['#dfe7d3', '#b9cda0', '#8caa6e', '#5a8048', '#1F3A2E'];
  var RAMP = DEFAULT_RAMP;
  var NODATA = '#e9e3d6';

  var map = L.map('map', { center: CFG.center || [-3, 120.4], zoom: 10, zoomControl: false, attributionControl: true });
  if (map.attributionControl) map.attributionControl.setPosition('bottomleft');

  var basemaps = {
    osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors' }),
    topo: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17, attribution: 'map data © OpenStreetMap · SRTM | © OpenTopoMap (CC-BY-SA)' }),
    s2: L.tileLayer('https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg', { maxZoom: 16, attribution: 'Sentinel-2 cloudless 2020 — <a href="https://s2maps.eu">s2maps.eu</a>' })
  };
  var currentBasemap = basemaps.osm; currentBasemap.addTo(map);

  if (CFG.bbox) {
    var b = L.latLngBounds(CFG.bbox[0], CFG.bbox[1]);
    if (b.isValid()) map.fitBounds(b, { padding: [6, 6] });
  }

  // ---------- helpers ----------
  function fmt(n) { if (n == null || isNaN(n)) return '—'; return Number(n).toLocaleString('id-ID', { maximumFractionDigits: 1 }); }
  function fmtInt(n) { return Number(n || 0).toLocaleString('id-ID'); }
  function meta(kode) { for (var i = 0; i < INDS.length; i++) if (INDS[i].kode === kode) return INDS[i]; return {}; }
  function valOf(props, kode) { var v = (props.nilai || {})[kode]; return (v == null || v === '') ? null : +v; }
  function kegOf(props, kode) { var k = (props.kegiatan || {})[kode]; return k ? String(k) : ''; }
  function komOf(props, kode) { var k = (props.komoditas || {})[kode]; return k ? String(k) : ''; }
  // Teks tooltip hover: "Nama: nilai satuan · kegiatan" (indikator aktif).
  function tipText(props, kode) {
    var v = valOf(props, kode), keg = kegOf(props, kode);
    var m = (INDS.filter(function (i) { return i.kode === kode; })[0] || {});
    var t = esc(props.nama || props.kode_pum);
    if (v != null) t += ': ' + fmt(v) + (m.satuan ? ' ' + esc(m.satuan) : '');
    if (keg) t += ' · ' + esc(keg);
    return t;
  }
  function esc(s) { var d = document.createElement('span'); d.textContent = (s == null ? '' : String(s)); return d.innerHTML; }

  function classify(vals) {
    vals = vals.filter(function (v) { return v != null; }).sort(function (a, b) { return a - b; });
    if (!vals.length) return { th: [], colors: [], min: null, max: null };
    var uniq = []; var seen = {};
    vals.forEach(function (v) { if (!seen[v]) { seen[v] = 1; uniq.push(v); } });
    var n = Math.min(5, uniq.length);
    var th = [];
    for (var i = 1; i < n; i++) th.push(vals[Math.floor(i * vals.length / n)]);
    return { th: th, colors: RAMP.slice(0, n), min: vals[0], max: vals[vals.length - 1] };
  }
  function colorFor(v, cls) {
    if (v == null) return NODATA;
    var i = 0; while (i < cls.th.length && v >= cls.th[i]) i++;
    return cls.colors[Math.min(i, cls.colors.length - 1)] || RAMP[0];
  }

  // ---------- state ----------
  var state = { kode: INDS.length ? INDS[0].kode : null, tahun: CFG.tahun, level: CFG.level || 'desa', scopeKec: null, scopeKecNama: null, loadedLevel: null, geojson: null, layer: null, komLayer: null, showKom: true, cls: { th: [], colors: [] }, selected: null, selKode: null, history: null };

  // ---------- render ----------
  function styleFn(feature) {
    var v = valOf(feature.properties, state.kode);
    return { color: '#E11D2A', weight: 1, fillColor: colorFor(v, state.cls), fillOpacity: v == null ? 0.45 : 0.85 };
  }

  function renderLegend(cls, m) {
    var el = document.getElementById('legendBody');
    // Label "Tanpa data" disambungkan ke nama wilayah cakupan dari DB cakupan
    // (RefWilayah*), fallback ke nama kabupaten situs bila kosong.
    var cakNama = CFG.cakupanNama || CFG.namaKabupaten || '';
    var ndLabel = 'Tanpa data' + (cakNama ? ' · ' + esc(cakNama) : '');
    var ndRow = '<div class="wg-legend-row"><span class="wg-legend-sw nd"></span>' + ndLabel + '</div>';
    if (!cls.colors.length) {
      el.innerHTML = ndRow;
      return;
    }
    var bounds = [cls.min].concat(cls.th).concat([cls.max]);
    var html = '<div class="wg-legend-cap"><strong>' + esc(m.nama) + '</strong>' + (m.satuan ? ' (' + esc(m.satuan) + ')' : '') + '</div>';
    for (var i = 0; i < cls.colors.length; i++) {
      var lo = bounds[i], hi = bounds[i + 1];
      var lbl = (cls.colors.length === 1) ? fmt(lo) : (fmt(lo) + ' – ' + fmt(hi));
      html += '<div class="wg-legend-row"><span class="wg-legend-sw" style="background:' + cls.colors[i] + '"></span>' + lbl + '</div>';
    }
    html += ndRow;
    // Keterangan SIMBOL KOMODITAS — ikon yang sedang tampil utk indikator ini.
    if (state.showKom) {
      var legIcons = CFG.komoditasIcons || {};
      var present = {};
      scopedFeatures().forEach(function (f) {
        var kk = (f.properties.komoditas || {})[m.kode];
        if (kk && legIcons[kk]) present[kk] = legIcons[kk];
      });
      var knames = Object.keys(present).sort();
      if (knames.length) {
        html += '<div class="wg-legend-komh">Simbol komoditas</div>';
        knames.forEach(function (n) {
          html += '<div class="wg-legend-row"><span class="wg-legend-kombadge"><img src="' + present[n] + '" alt=""></span>' + esc(n) + '</div>';
        });
      }
    }
    el.innerHTML = html;
  }

  function renderRanking(feats, kode, m) {
    var rows = feats.map(function (f) { return { p: f.properties, v: valOf(f.properties, kode) }; })
      .filter(function (r) { return r.v != null; })
      .sort(function (a, b) { return b.v - a.v; }).slice(0, 8);
    var el = document.getElementById('rankList');
    document.getElementById('rankUnit').textContent = m.satuan ? '· ' + m.satuan : '';
    if (!rows.length) { el.innerHTML = '<div class="wg-rank-empty">Belum ada data per wilayah.</div>'; return; }
    var max = rows[0].v || 1;
    el.innerHTML = rows.map(function (r, i) {
      var w = Math.max(3, Math.round((r.v / max) * 100));
      // Tooltip kegiatan (indikator aktif) di area nama+bar; kutip di-escape.
      var keg = kegOf(r.p, kode);
      var tip = keg ? ' title="' + esc(keg).replace(/"/g, '&quot;') + '"' : '';
      return '<div class="wg-rank-row"><div class="wg-rank-no">' + (i + 1) + '</div>'
        + '<div class="wg-rank-main"' + tip + '><div class="wg-rank-nama" data-kode="' + esc(r.p.kode_pum) + '">' + esc(r.p.nama) + '</div>'
        + '<div class="wg-rank-bar"><div class="wg-rank-bar-fill" style="width:' + w + '%"></div></div></div>'
        + '<div class="wg-rank-val">' + fmt(r.v) + '</div></div>';
    }).join('');
    el.querySelectorAll('.wg-rank-nama').forEach(function (n) {
      n.addEventListener('click', function () { focusFeature(n.getAttribute('data-kode')); });
    });
  }

  function renderHero(feats, kode, m) {
    var vals = feats.map(function (f) { return valOf(f.properties, kode); });
    var nonnull = vals.filter(function (v) { return v != null; });
    var realisasi = nonnull.reduce(function (a, b) { return a + b; }, 0);
    var total = feats.length, cov = nonnull.length;
    var usedAgg = false;
    if (cov === 0 && m.agg != null) { realisasi = +m.agg; usedAgg = true; }
    document.getElementById('heroVal').innerHTML = fmt(realisasi) + '<span class="unit">' + esc(m.satuan || '') + '</span>';
    var tgt = m.target;
    var pct = (tgt && tgt > 0) ? (realisasi / tgt * 100) : null;
    document.getElementById('heroPct').textContent = pct == null ? '' : (Math.round(pct) + '% target');
    document.getElementById('heroTarget').innerHTML = tgt ? ('Target: <strong>' + fmt(tgt) + ' ' + esc(m.satuan || '') + '</strong>') : 'Target belum ditetapkan';
    // Realisasi kumulatif tahunan: Σ realisasi semua desa, semua tahun <= terpilih.
    var cumEl = document.getElementById('heroCum');
    if (cumEl) {
      var ser = (((m.aggSeries || {})[state.level]) || []).filter(function (s) { return s.tahun <= state.tahun && s.nilai != null; });
      if (ser.length > 1) {
        var cum = ser.reduce(function (a, s) { return a + (+s.nilai || 0); }, 0);
        var yrs = ser.map(function (s) { return s.tahun; });
        var yl = (yrs.length > 5) ? (yrs[0] + '–' + yrs[yrs.length - 1]) : yrs.join(' + ');
        cumEl.innerHTML = 'Σ Realisasi kumulatif s.d. ' + state.tahun + ': <strong>' + fmt(cum) + ' ' + esc(m.satuan || '') + '</strong> <span class="yrs">(' + yl + ')</span>';
        cumEl.style.display = 'block';
      } else { cumEl.style.display = 'none'; }
    }
    var bar = document.getElementById('heroBar');
    bar.style.width = (pct == null ? 0 : Math.min(100, pct)) + '%';
    bar.classList.toggle('over', pct != null && pct >= 100);
    var scl = document.getElementById('statCovLabel');
    if (scl) scl.textContent = (state.level === 'kecamatan' ? 'Kecamatan' : 'Desa') + ' Terisi Data';
    document.getElementById('statCov').innerHTML = fmtInt(cov) + ' <small>/ ' + fmtInt(total) + '</small>';
    document.getElementById('statPct').textContent = total ? (Math.round(cov / total * 100) + '%') : '—';
    var note = document.getElementById('aggNote');
    if (usedAgg) {
      note.style.display = 'block';
      note.innerHTML = 'Angka di atas memakai <strong>agregat ' + (m.agg_tahun || '') + '</strong> karena rincian per desa belum dientri. Peta menampilkan pola "tanpa data".';
    } else if (cov === 0) {
      note.style.display = 'block';
      note.innerHTML = 'Belum ada data capaian untuk indikator ini. Entri di <strong>Panel Admin → Data Capaian</strong>.';
    } else { note.style.display = 'none'; }
  }

  function render() {
    var kode = state.kode, m = meta(kode);
    // Palet warna mengikuti indikator aktif (pilihan admin); fallback hijau.
    RAMP = (m.ramp && m.ramp.length) ? m.ramp : DEFAULT_RAMP;
    var ab = document.getElementById('aggBadge');
    if (ab) ab.textContent = (m.agregasi === 'kumulatif')
      ? ('Kumulatif s.d. ' + state.tahun) : ('Tahun ' + state.tahun);
    document.getElementById('indTitle').textContent = m.nama || '—';
    document.getElementById('indPilar').textContent = 'FOLUR · ' + (m.pilar_nama || 'GEF Core Indicators');
    document.getElementById('indDesc').textContent = m.deskripsi || 'Tidak ada deskripsi.';
    document.querySelectorAll('#indPills .wg-pill').forEach(function (p) {
      p.classList.toggle('active', p.getAttribute('data-kode') === kode);
    });
    if (!state.geojson) return;
    var feats = scopedFeatures();
    state.cls = classify(feats.map(function (f) { return valOf(f.properties, kode); }));
    if (state.layer) state.layer.setStyle(styleFn);
    renderLegend(state.cls, m);
    renderHero(feats, kode, m);
    renderRanking(feats, kode, m);
    renderKomMarkers();
    if (state.selected) renderSelected(state.selected);
  }

  // ---------- selected feature ----------
  function renderSelected(props) {
    document.getElementById('selSection').style.display = 'block';
    document.getElementById('selNama').textContent = props.nama || props.kode_pum;
    document.getElementById('selKec').textContent = props.nama_kec ? ('Kec. ' + props.nama_kec) : props.kode_pum;
    var body = document.getElementById('selBody');
    body.innerHTML = INDS.map(function (ind) {
      var v = valOf(props, ind.kode);
      var keg = kegOf(props, ind.kode);
      var kom = komOf(props, ind.kode);
      var act = ind.kode === state.kode ? ' active' : '';
      var vv = v == null ? '<span class="wg-sel-rv na">— belum ada</span>'
        : '<span class="wg-sel-rv">' + fmt(v) + ' ' + esc(ind.satuan || '') + '</span>';
      var sub = (keg || kom)
        ? '<div class="wg-sel-keg">' + (keg ? esc(keg) : '')
          + (kom ? ' <span class="wg-sel-kom">' + esc(kom) + '</span>' : '') + '</div>'
        : '';
      return '<div class="wg-sel-row' + act + '">'
        + '<div class="wg-sel-rmain"><span class="wg-sel-rn">' + esc(ind.nama) + '</span>' + vv + '</div>'
        + sub + '</div>';
    }).join('');
    // Di jenjang Kecamatan: tombol drill-down ke desa-desa di dalamnya.
    if (state.level === 'kecamatan') {
      body.innerHTML += '<button type="button" class="wg-drill-btn" id="drillBtn">Telusuri desa di ' + esc(props.nama || '') + ' →</button>';
      var db = document.getElementById('drillBtn');
      if (db) db.addEventListener('click', function () { drillTo(props.kode_pum, props.nama); });
    }
    state.selKode = props.kode_pum;
    ensureHistory(props.kode_pum);
  }

  // Riwayat tahunan wilayah terpilih (semua indikator) — di-fetch sekali per klik.
  function ensureHistory(kodePum) {
    if (state.history && state.history.kode_pum === kodePum) { renderHistory(state.kode); return; }
    state.history = null;
    document.getElementById('selHistory').innerHTML = '<div class="wg-hist-empty">Memuat riwayat…</div>';
    fetch(CFG.historyUrl + '?level=' + encodeURIComponent(state.level) + '&kode_pum=' + encodeURIComponent(kodePum), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (state.selKode !== kodePum) return; state.history = d; renderHistory(state.kode); })
      .catch(function () { document.getElementById('selHistory').innerHTML = ''; });
  }
  function renderHistory(kode) {
    var el = document.getElementById('selHistory'); if (!el) return;
    var h = state.history, m = meta(kode);
    if (!h || !h.series) { el.innerHTML = ''; return; }
    var ser = h.series[kode] || [];
    var head = '<div class="wg-hist-h">Riwayat tahunan · ' + esc(m.kode || kode) + (m.agregasi === 'kumulatif' ? ' (kumulatif)' : '') + '</div>';
    if (!ser.length) { el.innerHTML = head + '<div class="wg-hist-empty">Belum ada entri tahunan.</div>'; return; }
    var cum = m.agregasi === 'kumulatif', run = 0;
    var rows = ser.map(function (s) {
      run += (s.nilai || 0);
      var shown = cum ? run : s.nilai;
      var sub = (s.kegiatan || s.komoditas)
        ? '<span class="wg-hist-keg">' + (s.kegiatan ? esc(s.kegiatan) : '')
          + (s.komoditas ? ' <span class="wg-sel-kom">' + esc(s.komoditas) + '</span>' : '') + '</span>'
        : '';
      return '<div class="wg-hist-row"><span class="wg-hist-th">' + s.tahun + '</span>'
        + '<span class="wg-hist-v">' + fmt(shown) + (m.satuan ? ' ' + esc(m.satuan) : '') + '</span>'
        + sub + '</div>';
    }).join('');
    // Total kumulatif per wilayah ini = Σ nilai semua tahun.
    var tot = ser.reduce(function (a, s) { return a + (+s.nilai || 0); }, 0);
    var foot = '<div class="wg-hist-row wg-hist-total"><span class="wg-hist-th">Σ</span>'
      + '<span class="wg-hist-v">' + fmt(tot) + (m.satuan ? ' ' + esc(m.satuan) : '') + '</span>'
      + '<span class="wg-hist-keg">kumulatif ' + ser.length + ' tahun</span></div>';
    el.innerHTML = head + rows + foot;
  }
  document.getElementById('selClose').addEventListener('click', function () {
    state.selected = null; state.selKode = null; state.history = null;
    document.getElementById('selSection').style.display = 'none';
    document.getElementById('selHistory').innerHTML = '';
    if (state.highlight) { state.layer.resetStyle(state.highlight); state.highlight = null; }
  });

  function focusFeature(kodePum) {
    if (!state.layer) return;
    state.layer.eachLayer(function (ly) {
      if (ly.feature && ly.feature.properties.kode_pum === kodePum) {
        if (state.highlight) state.layer.resetStyle(state.highlight);
        ly.setStyle({ color: '#C77D3E', weight: 2.5 }); ly.bringToFront();
        state.highlight = ly; state.selected = ly.feature.properties;
        renderSelected(ly.feature.properties);
        if (ly.getBounds) map.fitBounds(ly.getBounds(), { maxZoom: 13, padding: [40, 40] });
      }
    });
  }

  // ---------- breadcrumb hierarki yurisdiksi ----------
  function renderBreadcrumb() {
    var el = document.getElementById('breadcrumb'); if (!el) return;
    var kab = CFG.cakupanNama || CFG.namaKabupaten || 'Kabupaten';
    var html = '<button type="button" class="wg-bc-seg" id="bcKab">' + esc(kab) + '</button>';
    if (state.scopeKec) {
      html += '<span class="wg-bc-sep">▸</span><span class="wg-bc-cur">Kec. ' + esc(state.scopeKecNama || '') + '</span>'
        + '<span class="wg-bc-sep">▸</span><span class="wg-bc-cur2">Desa</span>';
    } else {
      html += '<span class="wg-bc-sep">▸</span><span class="wg-bc-cur2">' + (state.level === 'kecamatan' ? 'Kecamatan' : 'Desa') + '</span>';
    }
    el.innerHTML = html;
    var b = document.getElementById('bcKab');
    if (b) b.addEventListener('click', function () { if (state.scopeKec) clearScope(); });
  }
  function syncLevelTabs() {
    document.querySelectorAll('#levelTabs .wg-leveltab').forEach(function (x) {
      x.classList.toggle('active', x.getAttribute('data-level') === state.level);
    });
  }

  // ---------- fitur dalam scope aktif (filter desa ke kecamatan saat drill) ----------
  function scopedFeatures() {
    var fs = (state.geojson && state.geojson.features) || [];
    if (state.level === 'desa' && state.scopeKec) {
      return fs.filter(function (f) { return f.properties.kode_kec_pum === state.scopeKec; });
    }
    return fs;
  }

  // ---------- marker ikon komoditas (di centroid/ST_PointOnSurface wilayah) ----------
  function komIcon(url) {
    return L.divIcon({
      className: 'wg-kom-divicon',
      html: '<span class="wg-kom-badge"><img src="' + url + '" alt=""></span>',
      iconSize: [30, 30], iconAnchor: [15, 15]
    });
  }
  function renderKomMarkers() {
    if (!state.komLayer) state.komLayer = L.layerGroup().addTo(map);
    state.komLayer.clearLayers();
    if (!state.showKom || !state.geojson) return;
    var icons = CFG.komoditasIcons || {};
    scopedFeatures().forEach(function (f) {
      var p = f.properties;
      var kom = (p.komoditas || {})[state.kode];
      var url = kom ? icons[kom] : null;
      if (!url || !p.point) return;
      var mk = L.marker(p.point, { icon: komIcon(url), riseOnHover: true });
      mk.bindTooltip(esc(p.nama) + ' · ' + esc(kom), { direction: 'top', className: 'wg-tip' });
      mk.on('click', function () { focusFeature(p.kode_pum); });
      state.komLayer.addLayer(mk);
    });
  }

  // ---------- load geojson (per TAHUN/JENJANG) ----------
  function updateHeaderMeta() {
    var el = document.getElementById('headerMeta');
    if (el) el.textContent = 'Tahun ' + state.tahun + ' · ' + (CFG.nKec || 0) + ' Kecamatan · ' + (CFG.nDesa || 0) + ' Desa';
  }
  function clearSelection() {
    state.selected = null; state.highlight = null; state.selKode = null; state.history = null;
    document.getElementById('selSection').style.display = 'none';
    var sh = document.getElementById('selHistory'); if (sh) sh.innerHTML = '';
  }
  function buildLayer(fit) {
    if (state.layer) { map.removeLayer(state.layer); state.layer = null; }
    var feats = scopedFeatures();
    document.getElementById('noPreview').style.display = feats.length ? 'none' : 'flex';
    if (!feats.length) { render(); return; }
    state.layer = L.geoJSON({ type: 'FeatureCollection', features: feats }, {
      style: styleFn,
      onEachFeature: function (feature, layer) {
        var p = feature.properties;
        layer.on('mouseover', function () { layer.setStyle({ weight: 1.6, color: '#2A4D3D' }); });
        layer.on('mouseout', function () { if (state.highlight !== layer) state.layer.resetStyle(layer); });
        layer.on('click', function () {
          if (state.highlight && state.highlight !== layer) state.layer.resetStyle(state.highlight);
          layer.setStyle({ color: '#C77D3E', weight: 2.5 }); layer.bringToFront();
          state.highlight = layer; state.selected = p; renderSelected(p);
        });
        layer.bindTooltip(tipText(p, state.kode), { className: 'wg-tip', sticky: true });
      }
    }).addTo(map);
    state.bounds = state.layer.getBounds();
    if (fit && state.bounds.isValid()) map.fitBounds(state.bounds, { padding: [6, 6] });
    render();
  }
  function loadData(fit) {
    clearSelection();
    renderBreadcrumb();
    document.getElementById('noPreview').style.display = 'none';
    fetch(CFG.geojsonUrl + '?level=' + encodeURIComponent(state.level) + '&tahun=' + encodeURIComponent(state.tahun), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (gj) {
        state.geojson = gj; state.loadedLevel = state.level;
        if (!gj.features || !gj.features.length) { if (state.layer) { map.removeLayer(state.layer); state.layer = null; } document.getElementById('noPreview').style.display = 'flex'; render(); return; }
        buildLayer(fit);
      })
      .catch(function () { document.getElementById('noPreview').style.display = 'flex'; document.getElementById('noPreview').lastChild.textContent = ' Gagal memuat data spasial.'; });
  }
  // Drill: dari Kecamatan → desa-desa di dalamnya (scope), tanpa fetch ulang bila bisa.
  function drillTo(kecKode, kecNama) {
    state.scopeKec = kecKode; state.scopeKecNama = kecNama; state.level = 'desa';
    syncLevelTabs(); clearSelection(); renderBreadcrumb();
    if (state.loadedLevel === 'desa' && state.geojson) buildLayer(true);
    else loadData(true);
  }
  function clearScope() {
    if (!state.scopeKec) return;
    state.scopeKec = null; state.scopeKecNama = null;
    clearSelection(); renderBreadcrumb(); buildLayer(true);
  }
  loadData(true);

  // ---------- pemilih TAHUN ----------
  var yearSel = document.getElementById('yearSel');
  if (yearSel) yearSel.addEventListener('change', function () {
    state.tahun = parseInt(this.value, 10) || state.tahun;
    updateHeaderMeta();
    loadData(false);
  });

  // ---------- toggle ikon komoditas ----------
  var komToggle = document.getElementById('komToggle');
  if (komToggle) komToggle.addEventListener('change', function () {
    state.showKom = this.checked;
    render();  // perbarui marker peta + keterangan simbol di legenda
  });

  // ---------- pengalih Yurisdiksi (Desa <-> Kecamatan) ----------
  document.querySelectorAll('#levelTabs .wg-leveltab').forEach(function (t) {
    t.addEventListener('click', function () {
      if (t.classList.contains('active')) return;
      state.level = t.getAttribute('data-level');
      state.scopeKec = null; state.scopeKecNama = null;
      document.querySelectorAll('#levelTabs .wg-leveltab').forEach(function (x) {
        x.classList.toggle('active', x === t);
      });
      loadData(true);
    });
  });

  // ---------- indicator pills ----------
  document.querySelectorAll('#indPills .wg-pill').forEach(function (p) {
    p.addEventListener('click', function () {
      state.kode = p.getAttribute('data-kode');
      // refresh tooltips for new indicator
      if (state.layer) state.layer.eachLayer(function (ly) {
        if (ly.getTooltip()) ly.setTooltipContent(tipText(ly.feature.properties, state.kode));
      });
      render();
    });
  });

  // ---------- map tools ----------
  // Kembali ke extent awal (area cakupan semula): batas poligon -> fallback bbox.
  function fitHome() {
    if (state.bounds && state.bounds.isValid()) map.fitBounds(state.bounds, { padding: [6, 6] });
    else if (CFG.bbox) map.fitBounds(L.latLngBounds(CFG.bbox[0], CFG.bbox[1]), { padding: [6, 6] });
  }
  document.getElementById('zoomIn').addEventListener('click', function () { map.zoomIn(); });
  document.getElementById('zoomOut').addEventListener('click', function () { map.zoomOut(); });
  document.getElementById('zoomToLayer').addEventListener('click', fitHome);
  document.getElementById('zoomHome').addEventListener('click', fitHome);

  // ---------- basemap switch (gaya MapStore2: toggle thumbnail + flyout) ----------
  var bgControl = document.getElementById('bgControl');
  var bgToggle = document.getElementById('bgToggle');
  var bgToggleThumb = document.getElementById('bgToggleThumb');
  function syncBgToggle(item) {
    if (!item || !bgToggleThumb) return;
    var img = item.querySelector('img.bg-thumb');
    if (item.classList.contains('empty') || !img) {
      bgToggleThumb.classList.add('empty'); bgToggleThumb.style.backgroundImage = '';
    } else {
      bgToggleThumb.classList.remove('empty'); bgToggleThumb.style.backgroundImage = 'url("' + img.src + '")';
    }
  }
  function closeBg() { if (bgControl) bgControl.classList.remove('open'); if (bgToggle) bgToggle.setAttribute('aria-expanded', 'false'); }
  if (bgToggle) bgToggle.addEventListener('click', function (e) {
    e.stopPropagation();
    var open = bgControl.classList.toggle('open');
    bgToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  document.addEventListener('click', function (e) {
    if (bgControl && bgControl.classList.contains('open') && !bgControl.contains(e.target)) closeBg();
  });
  document.querySelectorAll('#bgControl .bg-item').forEach(function (item) {
    item.addEventListener('click', function () {
      document.querySelectorAll('#bgControl .bg-item').forEach(function (i) { i.classList.remove('active'); });
      item.classList.add('active');
      if (currentBasemap) { map.removeLayer(currentBasemap); currentBasemap = null; }
      var key = item.getAttribute('data-basemap');
      if (key !== 'none') { currentBasemap = basemaps[key] || null; if (currentBasemap) { currentBasemap.addTo(map); currentBasemap.bringToBack(); } }
      syncBgToggle(item);
      closeBg();
    });
  });
  syncBgToggle(document.querySelector('#bgControl .bg-item.active'));

  // ---------- bar scale ----------
  var BarScale = L.Control.extend({
    options: { position: 'bottomright', maxWidth: 130, segments: 4 },
    onAdd: function (m) {
      this._map = m; this._container = L.DomUtil.create('div', 'bar-scale');
      L.DomEvent.disableClickPropagation(this._container);
      m.on('move zoom zoomend moveend resize', this._update, this); this._update(); return this._container;
    },
    _update: function () {
      var m = this._map, y = Math.round(m.getSize().y / 2);
      var maxMeters = m.distance(m.containerPointToLatLng([0, y]), m.containerPointToLatLng([this.options.maxWidth, y]));
      if (!isFinite(maxMeters) || maxMeters <= 0) return;
      var pow10 = Math.pow(10, Math.floor(Math.log10(maxMeters))), d = maxMeters / pow10;
      var dist = (d >= 5 ? 5 : d >= 2 ? 2 : 1) * pow10;
      var width = Math.round(this.options.maxWidth * (dist / maxMeters));
      var seg = this.options.segments, segW = width / seg, bars = '';
      for (var i = 0; i < seg; i++) bars += '<span class="bar-scale-seg ' + (i % 2 ? 'dark' : 'light') + '" style="width:' + segW + 'px"></span>';
      var lab = function (m2) { return m2 >= 1000 ? (Math.round((m2 / 1000) * 100) / 100) + ' km' : Math.round(m2) + ' m'; };
      this._container.innerHTML = '<div class="bar-scale-bar" style="width:' + width + 'px">' + bars + '</div>'
        + '<div class="bar-scale-labels" style="width:' + width + 'px"><span>0</span><span style="left:50%">' + lab(dist / 2) + '</span><span>' + lab(dist) + '</span></div>';
    }
  });
  new BarScale().addTo(map);

  // initial sidebar paint (before geojson arrives)
  render();
})();
