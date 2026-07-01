  // ============================================================
  // KONFIGURASI GeoNode/GeoServer — disuntik dari backend (WebGisView)
  // lewat tag json_script ber-id "webgis-config" di bagian head.
  // baseURL relatif ("") karena halaman, /api, dan /geoserver
  // berada di origin yang sama via nginx.
  // ============================================================
  const GEONODE_CONFIG = JSON.parse(document.getElementById('webgis-config').textContent);
  const CSRF_TOKEN = "";

  // Pusat & bbox Kabupaten Luwu (Belopa)
  const LUWU_CENTER = GEONODE_CONFIG.center;
  const LUWU_BBOX = GEONODE_CONFIG.bbox;

  // ============================================================
  // Inisialisasi Map
  // ============================================================
  const map = L.map('map', {
    center: LUWU_CENTER,
    zoom: 10,
    zoomControl: false,
    attributionControl: true
  });

  // Background layers (selaras dgn .bg-item data-basemap)
  const basemaps = {
    osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    }),
    topo: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      attribution: 'map data © OpenStreetMap · SRTM | style © OpenTopoMap (CC-BY-SA)'
    }),
    s2: L.tileLayer('https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg', {
      maxZoom: 16,
      attribution: 'Sentinel-2 cloudless 2020 by EOX IT Services GmbH — <a href="https://s2maps.eu">s2maps.eu</a>'
    })
  };
  let currentBasemap = basemaps.osm;
  currentBasemap.addTo(map);

  // ============================================================
  // Peta ikhtisar (overview/minimap) + skala — pojok kanan-bawah
  // ============================================================
  if (map.attributionControl) map.attributionControl.setPosition('bottomleft');

  // Skala Garis / Bar Scale — batang kotak-kotak selang-seling (putih/abu tua)
  const BarScale = L.Control.extend({
    options: { position: 'bottomright', maxWidth: 140, segments: 4 },
    onAdd: function (map) {
      this._map = map;
      this._container = L.DomUtil.create('div', 'bar-scale');
      L.DomEvent.disableClickPropagation(this._container);
      map.on('move zoom zoomend moveend resize', this._update, this);
      this._update();
      return this._container;
    },
    onRemove: function (map) {
      map.off('move zoom zoomend moveend resize', this._update, this);
    },
    _update: function () {
      const map = this._map;
      const y = Math.round(map.getSize().y / 2);
      const maxMeters = map.distance(
        map.containerPointToLatLng([0, y]),
        map.containerPointToLatLng([this.options.maxWidth, y])
      );
      if (!isFinite(maxMeters) || maxMeters <= 0) return;
      const dist = this._roundNumber(maxMeters);            // jarak "bulat" <= maxMeters
      const width = Math.round(this.options.maxWidth * (dist / maxMeters));
      this._render(width, dist);
    },
    _roundNumber: function (m) {
      const pow10 = Math.pow(10, Math.floor(Math.log10(m)));
      const d = m / pow10;                                  // 1..10
      const nice = d >= 5 ? 5 : d >= 2 ? 2 : 1;             // 1, 2, atau 5
      return nice * pow10;
    },
    _label: function (m) {
      return m >= 1000 ? (Math.round((m / 1000) * 100) / 100) + ' km'
                       : Math.round(m) + ' m';
    },
    _render: function (width, dist) {
      const seg = this.options.segments;
      const segW = width / seg;
      let bars = '';
      for (let i = 0; i < seg; i++) {
        bars += '<span class="bar-scale-seg ' + (i % 2 ? 'dark' : 'light') +
                '" style="width:' + segW + 'px"></span>';
      }
      this._container.innerHTML =
        '<div class="bar-scale-bar" style="width:' + width + 'px">' + bars + '</div>' +
        '<div class="bar-scale-labels" style="width:' + width + 'px">' +
          '<span>0</span>' +
          '<span style="left:50%">' + this._label(dist / 2) + '</span>' +
          '<span>' + this._label(dist) + '</span>' +
        '</div>';
    }
  });
  new BarScale({ position: 'bottomright', maxWidth: 140, segments: 4 }).addTo(map);
  try {
    const miniLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { minZoom: 0, maxZoom: 13 });
    new L.Control.MiniMap(miniLayer, {
      position: 'bottomright',
      toggleDisplay: true,
      minimized: false,
      width: 170, height: 120,
      zoomLevelOffset: -5,
      aimingRectOptions: { color: '#0000ff', weight: 2, fillColor: '#0000ff', fillOpacity: 0.12 }
    }).addTo(map);
  } catch (e) { console.error('MiniMap gagal dimuat:', e); }

  // ============================================================
  // INTERAKSI: Pencarian lokasi via OpenStreetMap (Nominatim)
  // ============================================================
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');
  let searchMarker = null;
  let searchTimer = null;
  let searchSeq = 0;

  function closeSearch() {
    if (searchResults) { searchResults.classList.remove('open'); searchResults.innerHTML = ''; }
  }

  function gotoResult(r) {
    const lat = parseFloat(r.lat), lon = parseFloat(r.lon);
    if (isNaN(lat) || isNaN(lon)) return;
    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon]).addTo(map);
    searchMarker.bindPopup(r.display_name, { maxWidth: 280 }).openPopup();
    if (r.boundingbox && r.boundingbox.length === 4) {
      const bb = r.boundingbox.map(parseFloat);   // [south, north, west, east]
      map.fitBounds([[bb[0], bb[2]], [bb[1], bb[3]]], { maxZoom: 16, padding: [20, 20] });
    } else {
      map.setView([lat, lon], 14);
    }
    if (searchInput) searchInput.value = r.display_name.split(',')[0];
    closeSearch();
  }

  // Deteksi input koordinat: desimal polos, desimal+arah (N/S/E/W), atau DMS
  // (derajat-menit-detik, mis. 107°22'44.4" E). Mengembalikan {lat, lon} bila valid
  // atau null. Disambiguasi lintang/bujur via besaran (|lintang| ≤ 90; di Luwu bujur
  // ~120 selalu > 90); bila ambigu, ikuti urutan readout peta di bawah: bujur, lintang.
  function parseCoord(q) {
    let s = (q || '').trim();
    if (!s) return null;
    // Normalisasi simbol: prime/quote tipografis → ASCII ('/"), ordinal º → °,
    // rapikan spasi. (° dipertahankan dulu karena jadi pemisah pada format DMS.)
    s = s.replace(/[′´‘’]/g, "'")   // ′ ´ ‘ ’ → '
         .replace(/[″“”]/g, '"')          // ″ “ ” → "
         .replace(/º/g, '°')                   // º → °
         .replace(/\s+/g, ' ')
         .trim();

    // Format DMS: 107°22'44.4" E, 7°21'3.6" S  (menit & detik opsional; detik boleh " atau '')
    const dmsRe = /^(\d+(?:\.\d+)?)\s*°\s*(?:(\d+(?:\.\d+)?)\s*'\s*)?(?:(\d+(?:\.\d+)?)\s*(?:"|'')\s*)?([NSEW])[,;\s]+(\d+(?:\.\d+)?)\s*°\s*(?:(\d+(?:\.\d+)?)\s*'\s*)?(?:(\d+(?:\.\d+)?)\s*(?:"|'')\s*)?([NSEW])$/i;
    const dms = s.match(dmsRe);
    if (dms) {
      const toDec = (d, mn, sc) =>
        parseFloat(d) + (mn ? parseFloat(mn) / 60 : 0) + (sc ? parseFloat(sc) / 3600 : 0);
      let lat = null, lon = null;
      const assign = (val, hemi) => {
        hemi = hemi.toUpperCase();
        if (hemi === 'N') lat = val; else if (hemi === 'S') lat = -val;
        else if (hemi === 'E') lon = val; else if (hemi === 'W') lon = -val;
      };
      assign(toDec(dms[1], dms[2], dms[3]), dms[4]);
      assign(toDec(dms[5], dms[6], dms[7]), dms[8]);
      if (lat === null || lon === null) return null;
      if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
      return { lat, lon };
    }

    // Sesudah DMS, ° tak lagi pemisah struktural → boleh dibuang.
    s = s.replace(/°/g, ' ').replace(/\s+/g, ' ').trim();
    // Format desimal + arah mata angin, mis. "3.638S 120.208E" atau "120.208E, 3.638S"
    const dir = s.match(/^(\d+(?:\.\d+)?)\s*°?\s*([NSEWnsew])[,;\s]+(\d+(?:\.\d+)?)\s*°?\s*([NSEWnsew])$/);
    if (dir) {
      let lat = null, lon = null;
      const apply = (v, d) => {
        d = d.toUpperCase();
        if (d === 'N') lat = v; else if (d === 'S') lat = -v;
        else if (d === 'E') lon = v; else if (d === 'W') lon = -v;
      };
      apply(parseFloat(dir[1]), dir[2]); apply(parseFloat(dir[3]), dir[4]);
      if (lat === null || lon === null) return null;
      if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
      return { lat, lon };
    }
    // Format desimal polos: dua angka dipisah koma / titik-koma / spasi
    const m = s.match(/^([+-]?\d+(?:\.\d+)?)[ ,;]+([+-]?\d+(?:\.\d+)?)$/);
    if (!m) return null;
    const a = parseFloat(m[1]), b = parseFloat(m[2]);
    if (isNaN(a) || isNaN(b)) return null;
    let lat, lon;
    if (Math.abs(a) > 90 && Math.abs(b) <= 90) { lon = a; lat = b; }
    else if (Math.abs(b) > 90 && Math.abs(a) <= 90) { lon = b; lat = a; }
    else { lon = a; lat = b; }   // ambigu → ikut urutan readout peta (bujur, lintang)
    if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    return { lat, lon };
  }

  function gotoCoord(lat, lon) {
    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon]).addTo(map);
    searchMarker.bindPopup(
      'Koordinat<br>Lintang: ' + lat.toFixed(5) + '<br>Bujur: ' + lon.toFixed(5),
      { maxWidth: 220 }
    ).openPopup();
    map.setView([lat, lon], 15);
    closeSearch();
  }

  function showCoordResult(c) {
    searchResults.innerHTML =
      '<div class="search-result" data-coord="1">'
      + '<span class="search-result-name">Menuju koordinat</span>'
      + '<span class="search-result-meta">Lintang ' + c.lat.toFixed(5)
      + ', Bujur ' + c.lon.toFixed(5) + '</span>'
      + '</div>';
    searchResults.classList.add('open');
    const el = searchResults.querySelector('.search-result');
    if (el) el.addEventListener('click', () => gotoCoord(c.lat, c.lon));
  }

  async function runSearch(q) {
    const seq = ++searchSeq;
    const url = 'https://nominatim.openstreetmap.org/search'
      + '?format=jsonv2&limit=6&countrycodes=id&accept-language=id&q=' + encodeURIComponent(q);
    try {
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const data = await r.json();
      if (seq !== searchSeq) return;              // abaikan respons usang
      if (!Array.isArray(data) || !data.length) {
        searchResults.innerHTML = '<div class="search-empty">Tidak ada hasil untuk "' + q + '".</div>';
        searchResults.classList.add('open');
        return;
      }
      searchResults.innerHTML = data.map((d, i) => {
        const parts = String(d.display_name || '').split(',');
        const name = (parts[0] || '').trim();
        const meta = parts.slice(1, 3).join(',').trim();
        return `<div class="search-result" data-i="${i}">
          <span class="search-result-name">${name}</span>
          <span class="search-result-meta">${meta || (d.type || '')}</span>
        </div>`;
      }).join('');
      searchResults.classList.add('open');
      searchResults.querySelectorAll('.search-result').forEach(el => {
        el.addEventListener('click', () => gotoResult(data[parseInt(el.dataset.i, 10)]));
      });
    } catch (e) {
      if (seq !== searchSeq) return;
      searchResults.innerHTML = '<div class="search-empty">Gagal mencari lokasi (jaringan/limit).</div>';
      searchResults.classList.add('open');
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim();
      clearTimeout(searchTimer);
      const coord = parseCoord(q);                         // koordinat → instan, tanpa jaringan
      if (coord) { showCoordResult(coord); return; }
      if (q.length < 3) { closeSearch(); return; }
      searchTimer = setTimeout(() => runSearch(q), 450);   // debounce, hormati rate-limit Nominatim
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const first = searchResults.querySelector('.search-result');
        if (first) first.click();
      } else if (e.key === 'Escape') {
        closeSearch();
      }
    });
  }
  // klik di luar panel pencarian → tutup hasil
  document.addEventListener('click', (e) => {
    const panel = document.querySelector('.panel-search');
    if (panel && !panel.contains(e.target)) closeSearch();
  });

  // Tombol pencarian di topbar → toggle visibilitas panel pencarian
  const searchToggleBtn = document.getElementById('searchToggleBtn');
  const searchPanelEl = document.querySelector('.panel-search');
  if (searchToggleBtn && searchPanelEl) {
    searchToggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const shown = !searchPanelEl.classList.toggle('search-hidden');
      searchToggleBtn.classList.toggle('active', shown);
      searchToggleBtn.setAttribute('aria-pressed', shown ? 'true' : 'false');
      if (shown) { if (searchInput) searchInput.focus(); }   // dibuka → fokus ke input
      else { closeSearch(); }                                // ditutup → tutup dropdown hasil
    });
  }

  // ============================================================
  // INTERAKSI: Upload KML/KMZ → tampil di peta + jadi area analisis
  // ============================================================
  const fileDrop = document.getElementById('fileDrop');
  const uploadInput = document.getElementById('uploadInput');

  function setUploadStatus(msg, kind) {
    const el = document.getElementById('uploadStatus');
    if (!el) return;
    el.textContent = msg || '';
    el.className = 'upload-status' + (kind ? ' ' + kind : '');
  }

  // Pilih geometri untuk dianalisis: utamakan poligon, lalu garis, lalu titik;
  // gabungkan beberapa fitur sejenis menjadi satu (Multi*) via turf.combine.
  // shpjs bisa mengembalikan satu FeatureCollection atau array (banyak shapefile) → satukan
  function normalizeFC(result) {
    if (Array.isArray(result)) {
      const feats = [];
      result.forEach(fc => { if (fc && fc.features) feats.push.apply(feats, fc.features); });
      return { type: 'FeatureCollection', features: feats };
    }
    return result;
  }

  function pickAnalysisGeom(gj) {
    const feats = (gj.type === 'FeatureCollection' ? (gj.features || []) : [gj]).filter(f => f && f.geometry);
    if (!feats.length) return null;
    const polys = feats.filter(f => String(f.geometry.type).includes('Polygon'));
    const lines = feats.filter(f => String(f.geometry.type).includes('Line'));
    const pts   = feats.filter(f => String(f.geometry.type).includes('Point'));
    const subset = polys.length ? polys : (lines.length ? lines : pts);
    if (!subset.length) return null;
    if (subset.length === 1) return subset[0];
    try { return turf.combine(turf.featureCollection(subset)).features[0]; }
    catch (e) { return subset[0]; }
  }

  function onUploaded(gj, name) {
    if (uploadedLayer) { map.removeLayer(uploadedLayer); uploadedLayer = null; }
    uploadedLayer = L.geoJSON(gj, {
      style: { color: '#5D3A1F', weight: 2, fillColor: '#C77D3E', fillOpacity: 0.18 },
      pointToLayer: (f, latlng) => L.circleMarker(latlng, {
        radius: 5, color: '#5D3A1F', fillColor: '#C77D3E', fillOpacity: 0.85, weight: 1.5
      }),
      onEachFeature: (f, layer) => {
        const p = f.properties || {};
        const nm = p.name || p.Name || '';
        const rows = Object.entries(p)
          .filter(([k]) => !/^(styleurl|stylehash|styleurl)$/i.test(k) && p[k] != null && p[k] !== '')
          .map(([k, v]) => `<div><strong>${k}</strong>: ${v}</div>`).join('');
        layer.bindPopup(`<div style="font-size:12px;max-width:240px">${nm ? '<strong>' + nm + '</strong><br>' : ''}${rows}</div>`);
      }
    }).addTo(map);
    try { map.fitBounds(uploadedLayer.getBounds(), { padding: [24, 24], maxZoom: 16 }); } catch (e) {}
    // Jadikan area analisis (overlay/luas) seperti poligon gambar
    if (typeof turf !== 'undefined') {
      const g = pickAnalysisGeom(gj);
      if (g) { analysisBaseGeom = g; clearBufferPreview(); }
    }
  }

  async function handleUploadFile(file) {
    if (!file) return;
    const name = file.name || 'berkas';
    const lower = name.toLowerCase();
    const isKml = lower.endsWith('.kml');
    const isKmz = lower.endsWith('.kmz');
    const isZip = lower.endsWith('.zip');
    if (!isKml && !isKmz && !isZip) { setUploadStatus('Format harus .kml, .kmz, atau .zip (SHP).', 'err'); return; }
    if (file.size > 10 * 1024 * 1024) { setUploadStatus('Ukuran melebihi 10 MB.', 'err'); return; }
    setUploadStatus('Memuat ' + name + '…', '');
    try {
      let gj;
      if (isZip) {
        if (typeof shp === 'undefined') throw new Error('Pustaka Shapefile gagal dimuat');
        gj = normalizeFC(await shp(await file.arrayBuffer()));
      } else {
        if (typeof toGeoJSON === 'undefined') throw new Error('Pustaka KML gagal dimuat');
        let kmlText;
        if (isKmz) {
          if (typeof JSZip === 'undefined') throw new Error('JSZip tidak dimuat');
          const zip = await JSZip.loadAsync(await file.arrayBuffer());
          const entry = Object.keys(zip.files).find(n => n.toLowerCase().endsWith('.kml'));
          if (!entry) throw new Error('Tidak ada .kml di dalam KMZ');
          kmlText = await zip.files[entry].async('string');
        } else {
          kmlText = await file.text();
        }
        const dom = new DOMParser().parseFromString(kmlText, 'text/xml');
        if (dom.getElementsByTagName('parsererror').length) throw new Error('Berkas KML tidak valid');
        gj = toGeoJSON.kml(dom);
      }
      const n = ((gj && gj.features) || []).length;
      if (!n) throw new Error('Tidak ada fitur dalam berkas');
      onUploaded(gj, name);
      setUploadStatus('Berhasil: ' + n + ' fitur. Klik "Analisis" untuk overlay/luas.', 'ok');
    } catch (e) {
      console.error('Upload gagal:', e);
      setUploadStatus('Gagal: ' + e.message, 'err');
    }
  }

  if (fileDrop && uploadInput) {
    fileDrop.addEventListener('click', () => uploadInput.click());
    uploadInput.addEventListener('change', () => {
      if (uploadInput.files && uploadInput.files[0]) handleUploadFile(uploadInput.files[0]);
      uploadInput.value = '';
    });
    ['dragenter', 'dragover'].forEach(ev => fileDrop.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation(); fileDrop.classList.add('dragover');
    }));
    ['dragleave', 'drop'].forEach(ev => fileDrop.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation(); fileDrop.classList.remove('dragover');
    }));
    fileDrop.addEventListener('drop', (e) => {
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (f) handleUploadFile(f);
    });
  }

  // ============================================================
  // GeoServer WMS Layers — diisi dinamis dari /api/v2/maps/<id>/
  // ============================================================
  const layers = {};            // alternate -> L.tileLayer.wms
  const layerBaseOpacity = {};  // alternate -> opacity awal dari API
  const layerBounds = {};       // alternate -> L.LatLngBounds (untuk zoom-to-layer)
  const layerInfo = {};         // alternate -> { title, subtype }
  const catalog = [];           // semua dataset publik dari /api/v2/datasets
  let opacityFactor = 1;        // multiplier global dari slider

  function buildWMSLayer(alternate, options = {}) {
    return L.tileLayer.wms(GEONODE_CONFIG.baseURL + GEONODE_CONFIG.wmsPath, {
      layers: alternate,
      format: 'image/png',
      transparent: true,
      version: '1.1.1',
      attribution: 'DST Luwu',
      ...options
    });
  }

  // EPSG:3857 -> EPSG:4326 (bbox map disimpan dalam Web Mercator)
  function mercToLatLng(x, y) {
    const lng = (x / 20037508.34) * 180;
    let lat = (y / 20037508.34) * 180;
    lat = 180 / Math.PI * (2 * Math.atan(Math.exp(lat * Math.PI / 180)) - Math.PI / 2);
    return [lat, lng];
  }

  // ll_bbox_polygon (GeoJSON lat/lng) -> L.LatLngBounds
  function llBboxToBounds(poly) {
    if (!poly || !poly.coordinates) return null;
    const ring = poly.coordinates[0];
    const lats = ring.map(p => p[1]);
    const lngs = ring.map(p => p[0]);
    return L.latLngBounds(
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)]
    );
  }

  function applyGlobalOpacity() {
    Object.entries(layers).forEach(([alt, l]) => {
      l.setOpacity((layerBaseOpacity[alt] ?? 1) * opacityFactor);
    });
  }

  // Aktifkan layer (buat jika belum ada) & tampilkan di peta
  function activateLayer(alt, opacity = 1.0) {
    if (!layers[alt]) {
      layers[alt] = buildWMSLayer(alt, { opacity });
      layerBaseOpacity[alt] = opacity;
    }
    if (!map.hasLayer(layers[alt])) layers[alt].addTo(map);
    applyGlobalOpacity();
    updateLegend();
  }

  function deactivateLayer(alt) {
    if (layers[alt] && map.hasLayer(layers[alt])) map.removeLayer(layers[alt]);
    updateLegend();
  }

  function zoomToLayer(alt) {
    const b = layerBounds[alt];
    if (b && b.isValid()) map.fitBounds(b, { padding: [40, 40] });
  }

  // ============================================================
  // Legenda dinamis — GetLegendGraphic per layer aktif (Fase F)
  // ============================================================
  function updateLegend() {
    const body = document.getElementById('legend-body');
    if (!body) return;
    // Urutan legenda HARUS sama dengan panel "Layer spasial": ambil urutan dari DOM
    // #layersList (item teratas = layer paling atas di peta). Layer aktif yang belum
    // tampil di daftar (mis. baru diaktifkan) disertakan di akhir sebagai fallback.
    const domOrder = [...document.querySelectorAll('#layersList .layer-item')].map(el => el.dataset.layer);
    const activeSet = Object.keys(layers).filter(alt => map.hasLayer(layers[alt]));
    const active = domOrder.filter(alt => activeSet.includes(alt))
      .concat(activeSet.filter(alt => !domOrder.includes(alt)));
    setTabSub('legend', active.length ? `${active.length} layer aktif` : 'Tidak ada layer aktif');
    if (!active.length) {
      body.innerHTML = '<div class="legend-empty">Aktifkan layer untuk menampilkan legenda.</div>';
      return;
    }
    const base = GEONODE_CONFIG.baseURL + GEONODE_CONFIG.wmsPath;
    const legendOpts = 'fontName:Geist;fontAntiAliasing:true;fontColor:0x4A4A4A;bgColor:0xFAF7F0;dpi:96';
    body.innerHTML = active.map(alt => {
      const title = (layerInfo[alt] && layerInfo[alt].title) || alt;
      const url = `${base}?service=WMS&request=GetLegendGraphic&version=1.0.0&format=image/png`
        + `&layer=${encodeURIComponent(alt)}&legend_options=${encodeURIComponent(legendOpts)}`;
      return `<div class="legend-group-title">${title}</div>`
        + `<img class="legend-img" src="${url}" alt="Legenda ${title}" loading="lazy"`
        + ` onerror="this.style.display='none'">`;
    }).join('');
  }

  function renderLayerItem(key, label, checked) {
    const item = document.createElement('div');
    item.className = 'layer-item';
    item.dataset.layer = key;
    item.innerHTML = `
      <div class="layer-checkbox ${checked ? 'checked' : ''}"></div>
      <div class="layer-name">${label} <span class="layer-type">wms</span></div>
      <button class="layer-zoom-btn" title="Zoom ke layer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
      </button>
    `;
    const cb = item.querySelector('.layer-checkbox');
    cb.addEventListener('click', (e) => {
      e.stopPropagation();
      cb.classList.toggle('checked');
      if (cb.classList.contains('checked')) {
        activateLayer(key, layerBaseOpacity[key] ?? 1);
      } else {
        deactivateLayer(key);
      }
    });
    item.querySelector('.layer-name').addEventListener('click', () => cb.click());

    // Tombol zoom-to-layer (sebelumnya mati) — Fase C
    const zoomBtn = item.querySelector('.layer-zoom-btn');
    if (layerBounds[key] && layerBounds[key].isValid()) {
      zoomBtn.addEventListener('click', (e) => { e.stopPropagation(); zoomToLayer(key); });
    } else {
      zoomBtn.disabled = true;
      zoomBtn.title = 'Bounding box layer tidak tersedia';
      zoomBtn.style.opacity = '0.35';
      zoomBtn.style.cursor = 'not-allowed';
    }
    return item;
  }

  async function loadMapFromGeoNode(mapId) {
    const url = `${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.mapsApiPath}/${mapId}/`;
    const list = document.getElementById('layersList');
    list.innerHTML = '<div style="padding:10px 0;font-family:var(--mono);font-size:10px;color:var(--ink-400);text-transform:uppercase;letter-spacing:0.1em;">Memuat layer…</div>';

    try {
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const m = data.map;
      const mls = [...(m.maplayers || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
      setTabSub('layers', `${mls.length} layer · map "${m.title}"`);

      // Tambah ke Leaflet ascending: order 0 di bawah, order tertinggi di atas
      mls.forEach(ml => {
        const ds = ml.dataset || {};
        const alt = ml.name || ds.alternate;
        if (!alt) return;
        const opacity = (typeof ml.opacity === 'number') ? ml.opacity : 1.0;
        registerLayerMeta(alt, ds.title || alt, ds);
        layerBaseOpacity[alt] = opacity;
        if (!layers[alt]) layers[alt] = buildWMSLayer(alt, { opacity });
        if (ml.visibility !== false && !map.hasLayer(layers[alt])) layers[alt].addTo(map);
      });
      applyGlobalOpacity();

      // Panel: order tertinggi di atas list (sesuai stacking peta)
      list.innerHTML = '';
      [...mls].reverse().forEach(ml => {
        const ds = ml.dataset || {};
        const alt = ml.name || ds.alternate;
        if (!alt) return;
        list.appendChild(renderLayerItem(alt, ds.title || alt, ml.visibility !== false));
      });
      updateLegend();

      // Fit ke bbox map (EPSG:3857)
      if (m.bbox_polygon && m.bbox_polygon.coordinates) {
        const coords = m.bbox_polygon.coordinates[0];
        const xs = coords.map(c => c[0]);
        const ys = coords.map(c => c[1]);
        const sw = mercToLatLng(Math.min(...xs), Math.min(...ys));
        const ne = mercToLatLng(Math.max(...xs), Math.max(...ys));
        map.fitBounds([sw, ne]);
      }
    } catch (err) {
      console.error('Gagal load map dari GeoNode:', err);
      list.innerHTML = `<div style="padding:10px 0;font-family:var(--mono);font-size:10px;color:var(--danger);text-transform:uppercase;letter-spacing:0.1em;">Gagal memuat map id=${mapId}: ${err.message}</div>`;
    }
  }

  // ============================================================
  // Registrasi metadata layer (judul, subtype, bbox dari katalog)
  // ============================================================
  function registerLayerMeta(alt, title, ds) {
    const cat = catalog.find(c => c.alternate === alt);
    layerInfo[alt] = {
      title: title || (cat && cat.title) || alt,
      subtype: (cat && cat.subtype) || (ds && ds.subtype) || 'vector'
    };
    const poly = (ds && ds.ll_bbox_polygon) || (cat && cat.ll_bbox_polygon);
    const b = llBboxToBounds(poly);
    if (b) layerBounds[alt] = b;
  }

  // ============================================================
  // Katalog dataset publik (Fase E) — /api/v2/datasets
  // ============================================================
  const addedLayers = new Set();  // alternate yang punya baris di panel layer

  async function loadCatalog() {
    const url = `${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.datasetsApiPath}/`
      + `?page_size=200&filter{is_published}=true`;
    try {
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      (data.datasets || []).forEach(d => {
        if (!d.alternate) return;
        catalog.push({
          alternate: d.alternate,
          title: d.title || d.alternate,
          subtype: d.subtype || 'vector',
          category: (d.category && (d.category.gn_description || d.category.identifier)) || 'Lainnya',
          ll_bbox_polygon: d.ll_bbox_polygon || null
        });
      });
    } catch (err) {
      console.error('Gagal load katalog dataset:', err);
    }
  }

  function addLayerFromCatalog(alt) {
    const cat = catalog.find(c => c.alternate === alt);
    registerLayerMeta(alt, cat ? cat.title : alt, cat);
    layerBaseOpacity[alt] = layerBaseOpacity[alt] ?? 1;
    activateLayer(alt, layerBaseOpacity[alt]);
    if (!addedLayers.has(alt)) {
      addedLayers.add(alt);
      const list = document.getElementById('layersList');
      list.insertBefore(renderLayerItem(alt, layerInfo[alt].title, true), list.firstChild);
    }
  }

  function removeLayerCompletely(alt) {
    deactivateLayer(alt);
    addedLayers.delete(alt);
    const list = document.getElementById('layersList');
    const row = list.querySelector(`.layer-item[data-layer="${CSS.escape(alt)}"]`);
    if (row) row.remove();
  }

  function renderCatalogPanel() {
    const body = document.getElementById('layers-body');
    if (!body) return;
    const wrap = document.createElement('div');
    wrap.className = 'catalog-wrap';
    wrap.innerHTML = `
      <div class="catalog-head">
        <span>Katalog · ${catalog.length} dataset</span>
        <button class="catalog-toggle" id="catalogToggle">+ Tambah layer</button>
      </div>
      <div id="catalogSearchWrap" style="display:none;">
        <input type="text" id="catalogSearch" class="catalog-search-input" placeholder="Filter dataset…">
        <div id="catalogList" class="catalog-list"></div>
      </div>`;
    const opacityRow = body.querySelector('.opacity-row');
    body.insertBefore(wrap, opacityRow);

    const listEl = wrap.querySelector('#catalogList');
    const groups = {};
    catalog.slice().sort((a, b) => a.title.localeCompare(b.title)).forEach(c => {
      (groups[c.category] = groups[c.category] || []).push(c);
    });
    listEl.innerHTML = Object.keys(groups).sort().map(cat => {
      const rows = groups[cat].map(c => `
        <label class="catalog-item" data-alt="${c.alternate}" data-name="${c.title.toLowerCase()}">
          <input type="checkbox" ${addedLayers.has(c.alternate) ? 'checked' : ''}>
          <span class="catalog-item-name">${c.title}</span>
          <span class="catalog-item-type">${c.subtype}</span>
        </label>`).join('');
      return `<div class="catalog-cat">${cat}</div>${rows}`;
    }).join('');

    wrap.querySelector('#catalogToggle').addEventListener('click', () => {
      const sw = wrap.querySelector('#catalogSearchWrap');
      const open = sw.style.display !== 'none';
      sw.style.display = open ? 'none' : 'block';
      wrap.querySelector('#catalogToggle').textContent = open ? '+ Tambah layer' : '− Tutup katalog';
    });
    wrap.querySelector('#catalogSearch').addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      listEl.querySelectorAll('.catalog-item').forEach(it => {
        it.style.display = it.dataset.name.includes(q) ? '' : 'none';
      });
    });
    listEl.querySelectorAll('.catalog-item input').forEach(inp => {
      inp.addEventListener('change', (e) => {
        const alt = e.target.closest('.catalog-item').dataset.alt;
        if (e.target.checked) addLayerFromCatalog(alt);
        else removeLayerCompletely(alt);
      });
    });
  }

  // ============================================================
  // Bootstrap: katalog dulu (untuk bbox/meta), lalu map kurasi
  // ============================================================
  (async () => {
    await loadCatalog();
    await loadMapFromGeoNode(GEONODE_CONFIG.referenceMapId);
    Object.keys(layers).forEach(alt => addedLayers.add(alt));
    renderCatalogPanel();
  })();

  // ============================================================
  // INTERAKSI: Opacity slider — multiplier terhadap opacity per-layer dari API
  // ============================================================
  const opacitySlider = document.getElementById('opacitySlider');
  const opacityValue = document.getElementById('opacityValue');
  opacitySlider.addEventListener('input', (e) => {
    opacityFactor = parseInt(e.target.value) / 100;
    opacityValue.textContent = e.target.value + '%';
    applyGlobalOpacity();
  });

  // ============================================================
  // INTERAKSI: Background selector — tombol induk (toggle) + daftar
  // ============================================================
  const bgControl = document.getElementById('bgControl');
  const bgToggle = document.getElementById('bgToggle');
  const bgToggleThumb = document.getElementById('bgToggleThumb');
  const bgToggleLabel = document.getElementById('bgToggleLabel');

  function syncBgToggle(item) {
    if (!item) return;
    const lbl = item.querySelector('.bg-label');
    if (bgToggleLabel && lbl) bgToggleLabel.textContent = lbl.textContent;
    if (!bgToggleThumb) return;
    const img = item.querySelector('img.bg-thumb');
    if (item.classList.contains('empty') || !img) {
      bgToggleThumb.classList.add('empty');
      bgToggleThumb.style.backgroundImage = '';
    } else {
      bgToggleThumb.classList.remove('empty');
      bgToggleThumb.style.backgroundImage = `url("${img.src}")`;
    }
  }
  function closeBg() {
    if (bgControl) bgControl.classList.remove('open');
    if (bgToggle) bgToggle.setAttribute('aria-expanded', 'false');
  }
  if (bgToggle) bgToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = bgControl.classList.toggle('open');
    bgToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  // klik di luar panel → tutup
  document.addEventListener('click', (e) => {
    if (bgControl && bgControl.classList.contains('open') && !bgControl.contains(e.target)) closeBg();
  });

  document.querySelectorAll('.bg-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.bg-item').forEach(b => b.classList.remove('active'));
      item.classList.add('active');
      if (currentBasemap) { map.removeLayer(currentBasemap); currentBasemap = null; }
      const key = item.dataset.basemap;
      if (key !== 'none') {                   // 'none' = Empty Background
        currentBasemap = basemaps[key];
        if (currentBasemap) { currentBasemap.addTo(map); currentBasemap.bringToBack(); }
      }
      syncBgToggle(item);
      closeBg();
    });
  });

  // Inisialisasi tombol induk dari item aktif
  syncBgToggle(document.querySelector('.bg-item.active'));

  // ============================================================
  // INTERAKSI: Zoom buttons
  // ============================================================
  document.getElementById('zoomInBtn').addEventListener('click', () => map.zoomIn());
  document.getElementById('zoomOutBtn').addEventListener('click', () => map.zoomOut());

  // Toolrail: tombol yang sebelumnya tidak punya handler
  const railFs = document.querySelector('.toolrail-btn[title="Fullscreen"]');
  if (railFs) railFs.addEventListener('click', () => {
    const el = document.documentElement;
    if (!document.fullscreenElement) { if (el.requestFullscreen) el.requestFullscreen(); }
    else if (document.exitFullscreen) document.exitFullscreen();
  });
  const railHome = document.querySelector('.toolrail-btn[title="Zoom ke Default"]');
  if (railHome) railHome.addEventListener('click', () => map.fitBounds(LUWU_BBOX));
  const railMeasure = document.querySelector('.toolrail-btn[title="Ukur jarak/luas"]');
  if (railMeasure) railMeasure.addEventListener('click', () => startDraw('line'));
  // Clear hasil lokasi: hapus marker pencarian OSM + bersihkan input & dropdown hasil
  const railClear = document.getElementById('clearSearchBtn');
  if (railClear) railClear.addEventListener('click', () => {
    if (searchMarker) { map.removeLayer(searchMarker); searchMarker = null; }
    if (searchInput) searchInput.value = '';
    closeSearch();
  });

  // ============================================================
  // INTERAKSI: Panel collapse
  // ============================================================
  document.querySelectorAll('.panel-collapse').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.panel-card').classList.toggle('collapsed');
    });
  });

  // ============================================================
  // INTERAKSI: Panel tab (Layer spasial / Legenda peta / Screening Tools)
  // ============================================================
  const panelStackEl = document.querySelector('.panel-stack');
  const panelStackSubEl = document.getElementById('panelStackSub');
  const tabSubText = {
    layers: panelStackSubEl ? panelStackSubEl.textContent : '',
    legend: 'Pola Ruang · Klasifikasi FOLUR',
    tools:  'Draw · Buffer · Overlay',
  };
  let activePanelTab = 'layers';

  // Dipanggil oleh loadMapFromGeoNode & updateLegend untuk memperbarui sub-judul
  // panel; hanya menulis ke header bila tab terkait sedang aktif.
  function setTabSub(tab, text) {
    tabSubText[tab] = text;
    if (tab === activePanelTab && panelStackSubEl) panelStackSubEl.textContent = text;
  }
  function switchPanelTab(tab) {
    if (!(tab in tabSubText)) return;
    activePanelTab = tab;
    document.querySelectorAll('.panel-tab').forEach(b =>
      b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('#stack-body .tab-pane').forEach(p =>
      p.classList.toggle('active', p.dataset.pane === tab));
    if (panelStackSubEl) panelStackSubEl.textContent = tabSubText[tab] || '';
    if (panelStackEl) panelStackEl.classList.remove('collapsed');   // klik tab → pastikan terbuka
  }
  document.querySelectorAll('.panel-tab').forEach(btn => {
    btn.addEventListener('click', () => switchPanelTab(btn.dataset.tab));
  });

  // ============================================================
  // INTERAKSI: Draw & ukur (Fase D — leaflet-draw)
  // ============================================================
  const drawnItems = new L.FeatureGroup().addTo(map);
  let activeDrawHandler = null;
  let drawing = false;

  function metricLabel(layer) {
    if (layer instanceof L.Polygon) {
      const latlngs = layer.getLatLngs()[0];
      const area = L.GeometryUtil.geodesicArea(latlngs);
      const ha = area / 10000;
      return area > 1e6 ? `Luas: ${(area / 1e6).toFixed(2)} km² (${ha.toFixed(1)} ha)`
                        : `Luas: ${area.toFixed(0)} m² (${ha.toFixed(2)} ha)`;
    }
    if (layer instanceof L.Polyline) {
      const pts = layer.getLatLngs();
      let d = 0;
      for (let i = 1; i < pts.length; i++) d += pts[i - 1].distanceTo(pts[i]);
      return d > 1000 ? `Panjang: ${(d / 1000).toFixed(2)} km` : `Panjang: ${d.toFixed(0)} m`;
    }
    if (layer instanceof L.Circle) {
      const r = layer.getRadius();
      return `Radius: ${r > 1000 ? (r / 1000).toFixed(2) + ' km' : r.toFixed(0) + ' m'}`;
    }
    return null;
  }

  function startDraw(tool) {
    if (activeDrawHandler) { activeDrawHandler.disable(); activeDrawHandler = null; }
    const opts = { shapeOptions: { color: '#0000ff', fillColor: '#00ff00', weight: 2, fillOpacity: 0.4 } };
    let h = null;
    if (tool === 'line') h = new L.Draw.Polyline(map, opts);
    else if (tool === 'polygon') h = new L.Draw.Polygon(map, opts);
    else if (tool === 'circle') h = new L.Draw.Circle(map, opts);
    else if (tool === 'point') h = new L.Draw.Marker(map);
    if (!h) return;
    activeDrawHandler = h;
    drawing = true;
    h.enable();
  }

  map.on(L.Draw.Event.CREATED, (e) => {
    const layer = e.layer;
    drawnItems.addLayer(layer);
    // Simpan geometri terakhir sebagai dasar area analisis (semua tipe).
    // Titik/garis nanti di-buffer; lingkaran langsung jadi poligon.
    try {
      if (layer instanceof L.Circle && typeof turf !== 'undefined') {
        const c = layer.getLatLng();
        analysisBaseGeom = turf.circle([c.lng, c.lat], layer.getRadius(), { steps: 64, units: 'meters' });
      } else if (typeof layer.toGeoJSON === 'function') {
        analysisBaseGeom = layer.toGeoJSON();
      }
    } catch (err) { analysisBaseGeom = null; }
    clearBufferPreview();
    const label = metricLabel(layer);
    if (label) layer.bindTooltip(label, { permanent: true, direction: 'center', className: 'measure-tip' }).openTooltip();
    drawing = false;
    activeDrawHandler = null;
    document.querySelectorAll('.draw-tool-btn').forEach(b => b.classList.remove('active'));
  });
  map.on(L.Draw.Event.DRAWSTOP, () => { drawing = false; });

  document.querySelectorAll('.draw-tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const wasActive = btn.classList.contains('active');
      document.querySelectorAll('.draw-tool-btn').forEach(b => b.classList.remove('active'));
      if (wasActive) {
        if (activeDrawHandler) activeDrawHandler.disable();
        activeDrawHandler = null; drawing = false;
        return;
      }
      btn.classList.add('active');
      startDraw(btn.dataset.tool);
    });
  });

  // Tombol "Bersihkan" menghapus semua gambar
  const clearDrawBtn = document.querySelector('.btn-tool.clear');
  if (clearDrawBtn) clearDrawBtn.addEventListener('click', () => {
    drawnItems.clearLayers();
    analysisBaseGeom = null;
    coordPoints.length = 0;
    setCoordHint('', null);
    clearBufferPreview();
    if (uploadedLayer) { map.removeLayer(uploadedLayer); uploadedLayer = null; }
    const us = document.getElementById('uploadStatus'); if (us) { us.textContent = ''; us.className = 'upload-status'; }
  });

  // ============================================================
  // ANALISIS AREA NYATA: poligon/lingkaran langsung, atau titik/garis + buffer
  // via WFS GetFeature (BBOX) + Turf.js (buffer/intersect/area)
  // ============================================================
  let analysisBaseGeom = null;    // GeoJSON Feature terakhir digambar/diunggah (titik/garis/poligon)
  let bufferPreviewLayer = null;  // pratinjau area efektif di peta
  let lastAnalysis = null;        // hasil analisis terakhir (untuk panel & laporan cetak)
  let uploadedLayer = null;       // layer hasil unggah KML/KMZ

  function getBufferMeters() {
    const el = document.getElementById('bufferMeters');
    const v = el ? parseFloat(el.value) : 0;
    return (isNaN(v) || v < 0) ? 0 : v;
  }

  function clearBufferPreview() {
    if (bufferPreviewLayer && map.hasLayer(bufferPreviewLayer)) map.removeLayer(bufferPreviewLayer);
    bufferPreviewLayer = null;
  }

  // ---- Titik AoI/PoI via input koordinat — dukung BANYAK titik (pisahkan dengan ";") ----
  // Titik diakumulasi & disimpan sebagai analysisBaseGeom: Point bila 1, MultiPoint bila >1,
  // sehingga "Analisis" mem-buffer SETIAP titik (identik dengan menggambar beberapa titik).
  const coordPoints = [];   // {lat, lon} terkumpul dari input

  function rebuildCoordGeom() {
    if (!coordPoints.length) { analysisBaseGeom = null; return; }
    const coords = coordPoints.map(p => [p.lon, p.lat]);
    analysisBaseGeom = coordPoints.length === 1
      ? { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: coords[0] } }
      : { type: 'Feature', properties: {}, geometry: { type: 'MultiPoint', coordinates: coords } };
    clearBufferPreview();
  }
  function addCoordMarker(lat, lon) {
    const m = L.marker([lat, lon]);
    drawnItems.addLayer(m);
    m.bindTooltip(`${lat.toFixed(5)}, ${lon.toFixed(5)}`,
      { permanent: true, direction: 'top', className: 'measure-tip' }).openTooltip();
  }
  const coordInput = document.getElementById('coordInput');
  const coordAddBtn = document.getElementById('coordAddBtn');
  const coordHint = document.getElementById('coordHint');
  function setCoordHint(msg, kind) {
    if (!coordHint) return;
    coordHint.textContent = msg || '';
    coordHint.className = 'coord-input-hint' + (kind ? ' ' + kind : '');
  }
  function submitCoordPoint() {
    if (!coordInput) return;
    // Banyak titik dipisah ";" atau baris baru; tiap titik pakai spasi/koma (desimal/DMS).
    const segments = coordInput.value.split(/[;\n]+/).map(s => s.trim()).filter(Boolean);
    const added = [], invalid = [];
    segments.forEach(seg => {
      const c = parseCoord(seg);
      if (c) { coordPoints.push(c); addCoordMarker(c.lat, c.lon); added.push(c); }
      else invalid.push(seg);
    });
    if (!added.length) {
      setCoordHint('Format koordinat tak dikenali. Mis. "120.208 -3.638"; pisahkan banyak titik dengan ";".', 'err');
      return;
    }
    rebuildCoordGeom();
    if (added.length === 1) map.setView([added[0].lat, added[0].lon], Math.max(map.getZoom(), 14));
    else map.fitBounds(L.latLngBounds(added.map(p => [p.lat, p.lon])).pad(0.3));
    coordInput.value = '';
    let msg = `${added.length} titik ditambahkan (total ${coordPoints.length}). Atur Buffer lalu klik "Analisis".`;
    if (invalid.length) msg += ` ${invalid.length} entri dilewati (format salah).`;
    setCoordHint(msg, 'ok');
  }
  if (coordAddBtn) coordAddBtn.addEventListener('click', submitCoordPoint);
  if (coordInput) coordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); submitCoordPoint(); }
  });

  function showBufferPreview(poly) {
    clearBufferPreview();
    try {
      bufferPreviewLayer = L.geoJSON(poly, {
        style: { color: '#C77D3E', weight: 1.5, dashArray: '5 4', fillColor: '#C77D3E', fillOpacity: 0.08 }
      }).addTo(map);
    } catch (e) { bufferPreviewLayer = null; }
  }

  // Bangun poligon area-analisis efektif dari geometri gambar + buffer (meter).
  // Titik/garis wajib buffer > 0; poligon/lingkaran dipakai langsung (opsional di-buffer).
  function computeAnalysisPolygon() {
    if (!analysisBaseGeom) return { error: 'empty' };
    const t = String((analysisBaseGeom.geometry || {}).type || '');
    const isArea = t.includes('Polygon');
    const buf = getBufferMeters();
    if (!isArea && buf <= 0) return { error: 'need-buffer' };
    let poly = analysisBaseGeom;
    if (buf > 0) {
      try { poly = turf.buffer(analysisBaseGeom, buf, { units: 'meters' }); }
      catch (e) { return { error: 'buffer-fail' }; }
    }
    if (!poly || !poly.geometry) return { error: 'buffer-fail' };
    return { poly: poly, buffered: buf > 0, base: t };
  }

  // Menentukan field “nama/label” terbaik dari atribut fitur untuk ditampilkan di popup atau legend.
  // Prioritas pertama: field 'name' (case-insensitive); jika tidak ada, gunakan urutan kandidat berikut.
  function pickLabelKey(props) {
    const keys = Object.keys(props || {});
    const nameHit = keys.find(k => k.toLowerCase() === 'name');
    if (nameHit) return nameHit;
    const cands = ['nama_unsur', 'namobj', 'nama', 'keterangan', 'kelas',
                   'kelas_jalan', 'jnsprn', 'fungsi', 'label', 'tipe', 'jenis', 'wadmkk'];
    for (const c of cands) if (keys.includes(c)) return c;
    for (const k of keys) {
      const v = props[k];
      if (typeof v === 'string' && v && !/^(fid|id|objectid|gid)$/i.test(k)) return k;
    }
    return null;
  }

  function fmtArea(m2) {
    const ha = m2 / 10000;
    return ha >= 100 ? (m2 / 1e6).toFixed(2) + ' km²' : ha.toFixed(2) + ' ha';
  }

  function resultRow(name, valueText, pct, pctLabel = 'dari area gambar') {
    const p = Math.max(0, Math.min(100, pct));
    return `<div class="result-row">
      <div class="result-row-top"><span class="result-name">${name}</span><span class="result-value">${valueText}</span></div>
      <div class="result-pct"><strong>${pct.toFixed(1)}%</strong> ${pctLabel}</div>
      <div class="result-bar"><div class="result-bar-fill" style="width:${p}%"></div></div>
    </div>`;
  }

  // Mengembalikan data terstruktur (dipakai panel & laporan cetak):
  //  { alt, title, error:'wfs' } | null |
  //  { kind:'area', interM2, count, pctTotal, rows:[{name,areaM2,pct}] } |
  //  { kind:'feature', geomLabel, count, rows:[{name,count,pct}] }
  async function analyzeLayer(alt, drawn, bboxParam, totalM2) {
    const title = (layerInfo[alt] && layerInfo[alt].title) || alt;
    const url = `${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.wfsPath}?service=WFS&version=2.0.0&request=GetFeature`
      + `&typeNames=${encodeURIComponent(alt)}&outputFormat=application/json&srsName=EPSG:4326`
      + `&count=2000&bbox=${encodeURIComponent(bboxParam)}`;
    let data;
    try {
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      data = await r.json();
      if (!data || !Array.isArray(data.features)) throw new Error('non-WFS');
    } catch (e) {
      return { alt, title, error: 'wfs' };
    }
    const feats = data.features.filter(f => f && f.geometry);
    if (!feats.length) return null;  // tak ada kandidat di bbox

    const isPoly = String(feats[0].geometry.type).includes('Polygon');
    const labelKey = pickLabelKey(feats[0].properties);

    if (isPoly) {
      const byCat = {};
      let interM2 = 0, count = 0;
      for (const f of feats) {
        let clipped = null;
        try { clipped = turf.intersect(drawn, f); } catch (e) { clipped = null; }
        if (!clipped) continue;
        let a = 0;
        try { a = turf.area(clipped); } catch (e) { a = 0; }
        if (a <= 0) continue;
        count++; interM2 += a;
        const cat = labelKey ? (f.properties[labelKey] ?? '(tanpa nama)') : 'Area';
        byCat[cat] = (byCat[cat] || 0) + a;
      }
      if (interM2 <= 0) return null;
      const rows = Object.entries(byCat).sort((a, b) => b[1] - a[1]).map(([cat, a]) => ({
        name: cat, areaM2: a, pct: totalM2 ? (a / totalM2 * 100) : 0
      }));
      return { alt, title, kind: 'area', interM2, count, pctTotal: totalM2 ? (interM2 / totalM2 * 100) : 0, rows };
    } else {
      const isLine = feats[0].geometry.type.includes('Line');
      const byCat = {};
      let total = 0;
      for (const f of feats) {
        let hit = false;
        try { hit = turf.booleanIntersects(drawn, f); } catch (e) {}
        if (!hit) continue;
        total++;
        const cat = labelKey ? (f.properties[labelKey] ?? '(tanpa nilai)') : (isLine ? 'Garis' : 'Titik');
        byCat[cat] = (byCat[cat] || 0) + 1;
      }
      if (!total) return null;
      const rows = Object.entries(byCat).sort((a, b) => b[1] - a[1]).map(([cat, n]) => ({
        name: cat, count: n, pct: total ? (n / total * 100) : 0
      }));
      return { alt, title, kind: 'feature', geomLabel: isLine ? 'garis' : 'titik', count: total, rows };
    }
  }

  // Render satu blok hasil ke panel Analisis
  function panelBlockHTML(b) {
    const head = (sub) => `<div class="analysis-group"><div class="analysis-group-title">${b.title} · ${sub}</div>`;
    if (b.error === 'wfs') {
      return head('tidak mendukung WFS') +
        '<div class="analysis-empty-hint" style="padding:6px 0;">Layer ini tidak bisa di-query (WFS nonaktif).</div></div>';
    }
    if (b.kind === 'area') {
      const rows = b.rows.map(r => resultRow(r.name, fmtArea(r.areaM2), r.pct)).join('');
      return head(`${b.pctTotal.toFixed(1)}% area · ${b.count} fitur`) + rows + '</div>';
    }
    const rows = b.rows.map(r => resultRow(r.name, r.count + ' fitur', r.pct, 'dari fitur di area')).join('');
    return head(`${b.count} ${b.geomLabel} di dalam area`) + rows + '</div>';
  }

  async function runAreaAnalysis() {
    const results = document.getElementById('analysisResults');
    const totalEl = document.getElementById('analysisTotalArea');
    const metaEl = document.getElementById('analysisMeta');
    const noteEl = document.getElementById('analysisAreaNote');
    if (!results) return;

    if (typeof turf === 'undefined') {
      results.innerHTML = '<div class="analysis-empty-hint">Pustaka analisis (Turf.js) gagal dimuat. Periksa koneksi ke CDN.</div>';
      return;
    }

    const built = computeAnalysisPolygon();
    if (built.error === 'empty') {
      if (totalEl) totalEl.innerHTML = '—<span class="unit">ha</span>';
      if (metaEl) metaEl.textContent = 'Belum ada gambar';
      if (noteEl) noteEl.textContent = '';
      clearBufferPreview();
      results.innerHTML = '<div class="analysis-empty-hint">Gambar <strong>poligon</strong>, <strong>lingkaran</strong>, atau <strong>titik/garis</strong> (lalu isi Buffer meter) di peta, kemudian buka panel ini.</div>';
      return;
    }
    if (built.error === 'need-buffer') {
      if (totalEl) totalEl.innerHTML = '—<span class="unit">ha</span>';
      if (metaEl) metaEl.textContent = 'Butuh buffer';
      if (noteEl) noteEl.textContent = '';
      clearBufferPreview();
      results.innerHTML = '<div class="analysis-empty-hint">Titik/garis tidak punya luas. Isi nilai <strong>Buffer (meter)</strong> &gt; 0 di panel Alat, lalu klik <strong>Analisis</strong> lagi.</div>';
      return;
    }
    if (built.error) {
      results.innerHTML = '<div class="analysis-empty-hint">Gagal membuat area buffer dari geometri yang digambar.</div>';
      return;
    }

    const drawn = built.poly;
    showBufferPreview(drawn);

    let totalM2 = 0;
    try { totalM2 = turf.area(drawn); } catch (e) { totalM2 = 0; }
    const totalHa = totalM2 / 10000;
    if (totalEl) totalEl.innerHTML = totalHa.toFixed(2) + `<span class="unit">ha</span>`;

    const activeAlts = Object.keys(layers).filter(a => map.hasLayer(layers[a]));
    if (metaEl) metaEl.innerHTML = `<strong>${activeAlts.length}</strong> layer aktif dianalisis`;
    if (noteEl) {
      const buf = getBufferMeters();
      noteEl.textContent = built.buffered ? `Buffer ${buf} m diterapkan` : '';
    }
    if (!activeAlts.length) {
      results.innerHTML = '<div class="analysis-empty-hint">Tidak ada layer aktif. Aktifkan layer lalu coba lagi.</div>';
      return;
    }

    results.innerHTML = '<div class="analysis-empty-hint">Menganalisis overlay AoI…</div>';
    const bb = turf.bbox(drawn);  // [minLon, minLat, maxLon, maxLat]
    const bboxParam = `${bb[0]},${bb[1]},${bb[2]},${bb[3]},EPSG:4326`;

    const blocks = [];
    for (const alt of activeAlts) {
      const block = await analyzeLayer(alt, drawn, bboxParam, totalM2);
      if (block) blocks.push(block);
    }
    // Simpan hasil terstruktur agar laporan cetak bisa memakainya
    lastAnalysis = {
      totalM2, bufferMeters: getBufferMeters(), buffered: built.buffered, baseType: built.base,
      activeCount: activeAlts.length, activeAlts: activeAlts.slice(), bbox: bb, geom: drawn, blocks, when: Date.now()
    };
    const real = blocks.filter(b => !b.error);
    results.innerHTML = real.length ? blocks.map(panelBlockHTML).join('')
      : '<div class="analysis-empty-hint">Tidak ada fitur layer aktif yang beririsan dengan area gambar.</div>';
  }

  // ============================================================
  // INTERAKSI: Klik peta → GetFeatureInfo nyata ke GeoServer (Fase B)
  // ============================================================
  const popup = document.getElementById('featurePopup');
  const popupTitle = document.getElementById('popupTitle');
  const popupBody = document.getElementById('popupBody');

  function showPopup(title, html) {
    popupTitle.textContent = title;
    popupBody.innerHTML = html;
    popup.classList.add('visible');
  }
  function popupNote(key, val) {
    return `<div class="map-popup-row"><span class="map-popup-key">${key}</span><span class="map-popup-val">${val}</span></div>`;
  }
  function rowsHTML(props) {
    const entries = Object.entries(props || {}).filter(([k]) => k.toLowerCase() !== 'bbox');
    if (!entries.length) return popupNote('—', 'tidak ada atribut');
    return entries.map(([k, v]) => `
      <div class="map-popup-row">
        <span class="map-popup-key">${k}</span>
        <span class="map-popup-val ${(typeof v === 'number' || /^-?\d/.test(String(v))) ? 'mono' : ''}">${v === null ? '—' : v}</span>
      </div>`).join('');
  }

  // Tombol "Info fitur (klik peta)": klik biasa untuk MENYEMBUNYIKAN popup fitur.
  // Info fitur tetap aktif — klik peta lagi akan memunculkan popup tanpa perlu klik tombol ini.
  const infoToggleBtn = document.getElementById('infoToggleBtn');
  if (infoToggleBtn) {
    infoToggleBtn.addEventListener('click', () => {
      if (popup) popup.classList.remove('visible');   // klik → sembunyikan popup
    });
  }

  map.on('click', async (e) => {
    if (drawing) return;       // jangan query fitur saat sedang menggambar
    const queryAlts = Object.keys(layers).filter(alt => map.hasLayer(layers[alt]));
    if (!queryAlts.length) {
      showPopup('TIDAK ADA LAYER', popupNote('info', 'Aktifkan minimal satu layer untuk query fitur.'));
      return;
    }
    const size = map.getSize();
    const b = map.getBounds();
    const params = new URLSearchParams({
      service: 'WMS', version: '1.1.1', request: 'GetFeatureInfo',
      layers: queryAlts.join(','), query_layers: queryAlts.join(','),
      bbox: `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`,
      width: size.x, height: size.y, srs: 'EPSG:4326',
      x: Math.round(e.containerPoint.x), y: Math.round(e.containerPoint.y),
      info_format: 'application/json', feature_count: 5, buffer: 5
    });
    const url = `${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.wmsPath}?${params.toString()}`;
    showPopup('MEMUAT…', popupNote('status', 'query fitur…'));
    try {
      const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const feats = data.features || [];
      if (!feats.length) {
        showPopup('TIDAK ADA FITUR', popupNote('info', 'Tidak ada data pada titik ini.'));
        return;
      }
      const f = feats[0];
      const layerName = String(f.id || '').split('.')[0];
      const alt = queryAlts.find(a => a.split(':').pop() === layerName) || layerName;
      const title = (layerInfo[alt] && layerInfo[alt].title) || alt || 'FITUR';
      let html = rowsHTML(f.properties);
      if (feats.length > 1) html += popupNote('+', `${feats.length - 1} fitur lain di titik ini`);
      showPopup(String(title).toUpperCase(), html);
    } catch (err) {
      console.error('GetFeatureInfo gagal:', err);
      showPopup('GAGAL', popupNote('error', err.message));
    }
  });

  // ============================================================
  // Update koordinat & zoom display
  // ============================================================
  const coordsDisplay = document.getElementById('coordsDisplay');
  const zoomLevel = document.getElementById('zoomLevel');
  map.on('mousemove', (e) => {
    coordsDisplay.innerHTML = `Koord: <strong>${e.latlng.lng.toFixed(3)}°, ${e.latlng.lat.toFixed(3)}°</strong> · Zoom: <strong id="zoomLevel">${map.getZoom()}</strong>`;
  });
  map.on('zoomend', () => {
    zoomLevel.textContent = map.getZoom();
  });

  // ===== PORT dari webgis3: panel Analisis & Print =====
  // AREA ANALYSIS PANEL — open/close & tab switching
  // ============================================================
  const analysisPanel = document.getElementById('analysisPanel');
  const analysisOverlay = document.getElementById('analysisOverlay');
  const analysisCloseBtn = document.getElementById('analysisClose');
  const analysisCloseBtn2 = document.getElementById('analysisClose2');

  function openAnalysis() {
    analysisPanel.classList.add('open');
    analysisOverlay.classList.add('open');
    analysisPanel.setAttribute('aria-hidden', 'false');
    runAreaAnalysis();  // isi panel dengan data nyata saat dibuka
  }
  function closeAnalysis() {
    analysisPanel.classList.remove('open');
    analysisOverlay.classList.remove('open');
    analysisPanel.setAttribute('aria-hidden', 'true');
  }

  // Buka panel saat tombol "Analisis" di tool panel diklik
  document.querySelectorAll('.btn-tool.analyze').forEach(btn =>
    btn.addEventListener('click', openAnalysis)
  );
  // Tutup panel
  analysisCloseBtn.addEventListener('click', closeAnalysis);
  if (analysisCloseBtn2) analysisCloseBtn2.addEventListener('click', closeAnalysis);
  analysisOverlay.addEventListener('click', closeAnalysis);
  // ESC untuk tutup
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && analysisPanel.classList.contains('open')) closeAnalysis();
  });

  // Tab switching
  document.querySelectorAll('.analysis-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      document.querySelectorAll('.analysis-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.dataset.pane === target);
      });
    });
  });
  // ============================================================
  // PRINT PREVIEW MODAL — open/close & print
  // ============================================================
  const printOverlay = document.getElementById('printPreviewOverlay');
  const printCloseBtn = document.getElementById('printCloseBtn');
  const printDocBtn = document.getElementById('printDocBtn');

  async function openPrintPreview() {
    printOverlay.classList.add('open');
    printOverlay.setAttribute('aria-hidden', 'false');
    // Scroll doc to top setiap kali dibuka
    const docWrap = printOverlay.querySelector('.print-doc-wrap');
    if (docWrap) docWrap.scrollTop = 0;
    // Jalankan analisis bila ada gambar tapi belum dianalisis, lalu bangun laporan
    if (!lastAnalysis && analysisBaseGeom) { try { await runAreaAnalysis(); } catch (e) {} }
    buildPrintReport();
  }
  function closePrintPreview() {
    printOverlay.classList.remove('open');
    printOverlay.setAttribute('aria-hidden', 'true');
  }

  // ============================================================
  // Bangun isi Laporan Cetak dari hasil analisis nyata (lastAnalysis)
  // ============================================================
  // Kumpulkan ring [lng,lat] dari Polygon/MultiPolygon (untuk overlay bentuk gambar)
  function collectRings(geom) {
    const g = (geom && geom.geometry) || geom || {};
    const rings = [];
    if (g.type === 'Polygon') (g.coordinates || []).forEach(r => rings.push(r));
    else if (g.type === 'MultiPolygon') (g.coordinates || []).forEach(p => (p || []).forEach(r => rings.push(r)));
    return rings;
  }

  function printMapSnapshot(a) {
    if (!a.bbox) return '';
    let [w, s, e, n] = a.bbox;
    let dx = (e - w) || 0.01, dy = (n - s) || 0.01;
    // padding 30% agar bentuk gambar tidak mepet tepi
    w -= dx * 0.30; e += dx * 0.30; s -= dy * 0.30; n += dy * 0.30;
    dx = e - w; dy = n - s;
    // Samakan rasio bbox dengan rasio gambar (W:H) → tidak distorsi; hanya memperbesar (shape tetap tercover)
    const W = 760, H = 460, target = W / H;
    if (dx / dy < target) { const need = dy * target, add = (need - dx) / 2; w -= add; e += add; dx = need; }
    else { const need = dx / target, add = (need - dy) / 2; s -= add; n += add; dy = need; }

    const layers = (a.activeAlts || []).join(',');
    const img = layers
      ? `<img src="${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.wmsPath}?service=WMS&version=1.1.1&request=GetMap`
        + `&layers=${encodeURIComponent(layers)}&srs=EPSG:4326&bbox=${w},${s},${e},${n}`
        + `&width=${W}&height=${H}&format=image/png&transparent=false" alt="Peta area analisis" onerror="this.style.display='none'">`
      : '';

    // Overlay bentuk yang digambar/diunggah (lon/lat → piksel)
    let svg = '';
    const rings = a.geom ? collectRings(a.geom) : [];
    if (rings.length) {
      const toPx = ([lng, lat]) => [((lng - w) / dx * W).toFixed(1), ((n - lat) / dy * H).toFixed(1)];
      const d = rings.map(r => 'M' + r.map(toPx).map(p => p.join(',')).join(' L') + ' Z').join(' ');
      svg = `<svg class="doc-map-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><path d="${d}" fill="#00ff00" fill-opacity="0.4" stroke="#0000ff" stroke-width="2.5"/></svg>`;
    }

    // Inset locator (peta ikhtisar) — area analisis sebagai kotak pada konteks lebih luas
    let inset = '';
    if (a.bbox && layers) {
      const [ow, os, oe, on] = a.bbox;
      const cx = (ow + oe) / 2, cy = (os + on) / 2;
      const half = Math.max(Math.max(oe - ow, on - os) * 6, 0.45) / 2;
      const lw = cx - half, le = cx + half, ls = cy - half, ln = cy + half;
      const LS = 150;
      const lurl = `${GEONODE_CONFIG.baseURL}${GEONODE_CONFIG.wmsPath}?service=WMS&version=1.1.1&request=GetMap`
        + `&layers=${encodeURIComponent(layers)}&srs=EPSG:4326&bbox=${lw},${ls},${le},${ln}`
        + `&width=${LS}&height=${LS}&format=image/png&transparent=false`;
      const rx = (ow - lw) / (le - lw) * LS, ry = (ln - on) / (ln - ls) * LS;
      const rw = Math.max((oe - ow) / (le - lw) * LS, 3), rh = Math.max((on - os) / (ln - ls) * LS, 3);
      inset = `<div class="doc-map-inset" style="bottom:48px">
        <img src="${lurl}" alt="Lokasi" onerror="this.style.display='none'">
        <svg viewBox="0 0 ${LS} ${LS}" preserveAspectRatio="none"><rect x="${rx.toFixed(1)}" y="${ry.toFixed(1)}" width="${rw.toFixed(1)}" height="${rh.toFixed(1)}" fill="rgba(0,255,0,0.4)" stroke="#0000ff" stroke-width="2"/></svg>
      </div>`;
    }

    // Skala Garis untuk snapshot — lebar batang proporsional thd extent geografis (akurat saat dicetak/PDF)
    let scale = '';
    const midLat = (s + n) / 2;
    const mPerDegLng = 111320 * Math.cos(midLat * Math.PI / 180);
    const totalM = (e - w) * mPerDegLng;          // jarak nyata selebar frame
    if (isFinite(totalM) && totalM > 0) {
      const targetM = totalM * 0.28;              // batang menyasar ~28% lebar peta
      const p10 = Math.pow(10, Math.floor(Math.log10(targetM)));
      const dn = targetM / p10, nice = dn >= 5 ? 5 : dn >= 2 ? 2 : 1;
      const dist = nice * p10;                     // jarak "bulat": 1/2/5 × 10ⁿ
      const pct = (dist / totalM * 100).toFixed(2);
      const fmt = (m) => m >= 1000 ? (Math.round(m / 1000 * 100) / 100) + ' km' : Math.round(m) + ' m';
      let segs = '';
      for (let i = 0; i < 4; i++) segs += `<span class="doc-map-scale-seg ${i % 2 ? 'dark' : 'light'}" style="width:25%"></span>`;
      scale = `<div class="doc-map-scale" style="width:${pct}%">
        <div class="doc-map-scale-bar">${segs}</div>
        <div class="doc-map-scale-labels"><span>0</span><span style="left:50%">${fmt(dist / 2)}</span><span>${fmt(dist)}</span></div>
      </div>`;
    }

    // Graticule (grid lat-long) + label di luar bingkai.
    // Snapshot diminta EPSG:4326 → pemetaan derajat→piksel bersifat linear (garis lurus, jarak sama).
    const niceStep = (span, div) => {
      const raw = span / div;
      const p10 = Math.pow(10, Math.floor(Math.log10(raw)));
      const dn = raw / p10, nv = dn >= 5 ? 5 : dn >= 2 ? 2 : 1;
      return nv * p10;
    };
    const dms = (v) => {
      const dd = Math.floor(v + 1e-9);
      const mm = Math.round((v - dd) * 60);
      if (mm === 60) return (dd + 1) + '°';
      return mm === 0 ? dd + '°' : dd + '°' + (mm < 10 ? '0' : '') + mm + '′';
    };
    const fmtLon = (v) => dms(Math.abs(v)) + (v >= 0 ? ' BT' : ' BB');
    const fmtLat = (v) => dms(Math.abs(v)) + (v >= 0 ? ' LU' : ' LS');

    const step = niceStep(Math.max(e - w, n - s), 4);   // interval identik utk bujur & lintang
    const lons = [], lats = [];
    for (let x = Math.ceil(w / step) * step; x <= e + 1e-9; x += step) lons.push(x);
    for (let y = Math.ceil(s / step) * step; y <= n + 1e-9; y += step) lats.push(y);

    let lines = '';
    lons.forEach(lon => { const px = ((lon - w) / (e - w) * W).toFixed(1); lines += `<line x1="${px}" y1="0" x2="${px}" y2="${H}"/>`; });
    lats.forEach(lat => { const py = ((n - lat) / (n - s) * H).toFixed(1); lines += `<line x1="0" y1="${py}" x2="${W}" y2="${py}"/>`; });
    const graticule = `<svg class="doc-map-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">`
      + `<g stroke="rgba(26,26,26,0.32)" stroke-width="0.75" stroke-dasharray="4 3" vector-effect="non-scaling-stroke">${lines}</g>`
      + `<rect x="0" y="0" width="${W}" height="${H}" fill="none" stroke="#1A1A1A" stroke-width="1.25" vector-effect="non-scaling-stroke"/>`
      + `</svg>`;

    const labX = lons.map(lon => `<span style="left:${((lon - w) / (e - w) * 100).toFixed(2)}%">${fmtLon(lon)}</span>`).join('');
    const labY = lats.map(lat => `<span style="top:${((n - lat) / (n - s) * 100).toFixed(2)}%">${fmtLat(lat)}</span>`).join('');
    const collar = `<div class="doc-grat doc-grat-x top">${labX}</div>`
      + `<div class="doc-grat doc-grat-x bottom">${labX}</div>`
      + `<div class="doc-grat doc-grat-y left">${labY}</div>`
      + `<div class="doc-grat doc-grat-y right">${labY}</div>`;

    return `<div class="doc-map-real">
      <div class="doc-map-plate">
        <div class="doc-map-frame" style="padding-bottom:${(H / W * 100).toFixed(2)}%">${img}${svg}${graticule}${inset}${scale}</div>
        ${collar}
      </div>
      <div class="cap">Snapshot AoI · ${(a.activeAlts || []).length} layer aktif</div>
    </div>`;
  }

  function printSection(b, totalM2) {
    if (b.error === 'wfs') return '';
    const note = (b.alt && layerInfo[b.alt] && layerInfo[b.alt].subtype) ? layerInfo[b.alt].subtype : '';
    let head = `<div class="doc-section"><div class="doc-section-header">`
      + `<div class="doc-section-title">${b.title}</div>`
      + `<div class="doc-section-note">${note}</div></div>`;
    if (b.kind === 'area') {
      const rows = b.rows.map(r => `<tr>
          <td>${r.name}</td>
          <td class="num">${(r.areaM2 / 10000).toFixed(2)}</td>
          <td class="num">${r.pct.toFixed(2)}%</td>
        </tr>`).join('');
      return head + `<table class="doc-table"><thead><tr>
          <th>Kategori</th><th class="num">Luas (ha)</th><th class="num">% Area</th>
        </tr></thead><tbody>${rows}</tbody></table></div>`;
    }
    const rows = b.rows.map(r => `<tr>
        <td>${r.name}</td>
        <td class="num">${r.count}</td>
        <td class="num">${r.pct.toFixed(2)}%</td>
      </tr>`).join('');
    return head + `<table class="doc-table"><thead><tr>
        <th>Kategori</th><th class="num">Jumlah</th><th class="num">% Fitur</th>
      </tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  function buildPrintReport() {
    const el = document.getElementById('printDocContent');
    if (!el) return;
    const a = lastAnalysis;
    if (!a) {
      el.innerHTML = '<div class="doc-empty">Belum ada hasil analisis. Buka panel <strong>Analisis</strong>, gambar poligon/lingkaran (atau titik/garis + buffer), lalu cetak.</div>';
      return;
    }
    const now = new Date(a.when || Date.now());
    let dateStr;
    try { dateStr = now.toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }); }
    catch (e) { dateStr = now.toISOString(); }
    const totalHa = a.totalM2 / 10000;
    const areaUnit = 'ha';
    const areaVal = totalHa.toFixed(2);
    const baseLabel = String(a.baseType || '').includes('Polygon') ? 'poligon'
      : String(a.baseType || '').includes('Line') ? 'garis' : 'titik';
    const hitCount = a.blocks.filter(b => !b.error).length;

    // Nomor registrasi laporan — kombinasi tanggal-waktu + komponen acak (unik tiap cetak)
    const pad = (x) => String(x).padStart(2, '0');
    const regNo = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`
      + `-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
      + `-${Math.floor(1000 + Math.random() * 9000)}`;

    // Catat ke Audit Log (kategori "Screening Tools analisis") — user login atau Publik.
    try {
      fetch('/webgis/screening-log/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body: JSON.stringify({ nomor_reg: regNo, area_ha: (a && a.totalM2) ? a.totalM2 / 10000 : null }),
      }).catch(function () {});
    } catch (e) { /* logging tidak boleh mengganggu cetak */ }

    let html = `<div class="doc-header">
        <div class="doc-header-left">
          <div class="doc-eyebrow">Laporan Analisis ${GEONODE_CONFIG.siteName}</div>
          <h1 class="doc-h1">Analisis <span class="italic">Area of Interest (AoI)</span></h1>
          <div class="doc-h-sub">Area ${a.buffered ? 'buffer <strong>' + a.bufferMeters + ' m</strong> dari ' + baseLabel : baseLabel} seluas <strong>${areaVal} ${areaUnit}</strong>, di-overlay dengan <strong>${a.activeCount}</strong> layer aktif.</div>
        </div>
        <div class="doc-header-right">
          <div class="doc-meta-row"><span class="label">Dibuat</span>${dateStr}</div>
          <div class="doc-meta-row"><span class="label">Nomor Reg</span>${regNo}</div>
        </div>
      </div>`;

    html += `<div class="doc-metrics">
        <div class="doc-metric"><div class="doc-metric-label">Luas Area</div><div class="doc-metric-value">${areaVal}<span class="unit">${areaUnit}</span></div></div>
        <div class="doc-metric"><div class="doc-metric-label">Buffer</div><div class="doc-metric-value">${a.bufferMeters}<span class="unit">m</span></div></div>
        <div class="doc-metric highlight"><div class="doc-metric-label">Layer Beririsan</div><div class="doc-metric-value">${hitCount}</div></div>
      </div>`;

    html += printMapSnapshot(a);

    if (!a.blocks.filter(b => !b.error).length) {
      html += '<div class="doc-empty">Tidak ada fitur layer aktif yang beririsan dengan area.</div>';
    } else {
      a.blocks.forEach(b => { html += printSection(b, a.totalM2); });
    }

    html += `<div class="doc-footer"><div>${GEONODE_CONFIG.siteName}</div></div>`;
    el.innerHTML = html;
  }

  // Wire tombol "Cetak laporan" di footer Area Analisis → buka Print Preview
  document.querySelectorAll('.btn-footer.btn-footer-primary').forEach(btn =>
    btn.addEventListener('click', openPrintPreview)
  );
  // Tutup
  printCloseBtn.addEventListener('click', closePrintPreview);
  // Cetak — panggil browser print dialog (CSS @media print sudah handle layout)
  printDocBtn.addEventListener('click', () => {
    window.print();
  });
  // ESC untuk tutup
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && printOverlay.classList.contains('open')) closePrintPreview();
  });



