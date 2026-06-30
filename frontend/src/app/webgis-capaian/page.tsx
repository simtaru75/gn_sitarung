import "./webgis-capaian.css";
import type { Metadata } from "next";
import { getSiteIdentity, getWebgisCapaianConfig } from "@/lib/geonode";
import WebGisClient from "./WebGisClient";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `WebGIS Capaian — ${ident.siteName}`,
    description: `Monitoring spasial Capaian Program FOLUR per wilayah — ${ident.siteName}.`,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function Page() {
  const [ident, config] = await Promise.all([getSiteIdentity(), getWebgisCapaianConfig()]);

  const namaKabupaten = config?.namaKabupaten || ident.namaKabupaten;
  const indikator = config?.indikator ?? [];
  const years = config?.years ?? [];
  const levels = config?.levels ?? [];
  const komoditasFokus = config?.komoditasFokus ?? [];
  const hasKomIcons = config ? Object.keys(config.komoditasIcons ?? {}).length > 0 : false;

  return (
    <div className="app" data-theme={ident.theme}>
      {/* CSS peta — React 19 menaikkan <link> ke <head>. Font memakai DM Sans
          brand (dimuat app-wide via layout), jadi tak perlu Google Fonts. */}
      <link rel="stylesheet" href="/vendor/leaflet/leaflet.css" />

      {/* Config GeoNode — id & format sama dengan json_script Django (#wg2-config). */}
      <script id="wg2-config" type="application/json" dangerouslySetInnerHTML={{ __html: JSON.stringify(config ?? {}) }} />

      {/* HEADER */}
      <header className="ds-header">
        <a href="/" className="ds-back">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Beranda
        </a>
        <div className="ds-header-brand">
          <div className="ds-header-mark">
            {ident.logo ? <img src={ident.logo} alt="Logo" className="w-full h-full object-contain p-0.5" /> : "L"}
          </div>
          <div className="ds-header-titles">
            <div className="ds-header-eyebrow">Monitoring Spasial · {namaKabupaten}</div>
            <div className="ds-header-title">Capaian Program FOLUR per Wilayah</div>
          </div>
        </div>
        <div className="ds-header-spacer" />
        <div className="ds-header-meta" id="headerMeta">
          Tahun {config?.tahun ?? "—"} · {config?.nKec ?? 0} Kecamatan · {config?.nDesa ?? 0} Desa
        </div>
      </header>

      {/* BODY */}
      <div className="ds-body">
        {/* MAP */}
        <div className="ds-map-wrap">
          <div id="map" />

          {/* Legend */}
          <div className="map-card legend" id="legendCard">
            <div className="map-card-head">
              <svg className="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
              <span className="map-card-title">Legenda</span>
              <span className="map-card-caret">▾</span>
            </div>
            <div className="map-card-body">
              <div className="legend-body" id="legendBody">
                <div className="wg-legend-cap">Memuat…</div>
              </div>
            </div>
          </div>

          {/* Tools */}
          <div className="map-tools">
            <div className="map-btn" id="zoomToLayer" title="Zoom ke cakupan">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 7V3h4M17 3h4v4M21 17v4h-4M7 21H3v-4" /></svg>
            </div>
            <div className="map-btn" id="zoomHome" title="Tampilan awal (area semula)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M4 10.5 12 4l8 6.5V20H4z" /></svg>
            </div>
            <div className="map-btn" id="zoomIn" title="Perbesar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
            </div>
            <div className="map-btn" id="zoomOut" title="Perkecil">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" /></svg>
            </div>
          </div>

          {/* Background selector */}
          <div className="bg-control" id="bgControl">
            <div className="bg-selector" id="bgSelector">
              <div className="bg-selector-title">Peta Dasar</div>
              <div className="bg-items">
                <button type="button" className="bg-item active" data-basemap="osm" title="OpenStreetMap">
                  <img className="bg-thumb" src="https://a.tile.openstreetmap.org/8/213/130.png" alt="" loading="lazy" />
                  <span className="bg-label">OpenStreetMap</span>
                </button>
                <button type="button" className="bg-item" data-basemap="topo" title="OpenTopoMap">
                  <img className="bg-thumb" src="https://a.tile.opentopomap.org/8/213/130.png" alt="" loading="lazy" />
                  <span className="bg-label">OpenTopoMap</span>
                </button>
                <button type="button" className="bg-item" data-basemap="s2" title="Citra Sentinel-2 cloudless">
                  <img className="bg-thumb" src="https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/8/130/213.jpg" alt="" loading="lazy" />
                  <span className="bg-label">Citra Sentinel-2</span>
                </button>
                <button type="button" className="bg-item empty" data-basemap="none" title="Tanpa Peta Dasar">
                  <span className="bg-thumb" />
                  <span className="bg-label">Tanpa Peta Dasar</span>
                </button>
              </div>
            </div>
            <button className="bg-toggle" id="bgToggle" title="Pilih peta dasar" aria-expanded="false">
              <span className="bg-toggle-thumb" id="bgToggleThumb" />
            </button>
          </div>

          <div className="no-preview" id="noPreview" style={{ display: "none" }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M9 20l-5.5 3V6L9 3l6 3 5.5-3v17L15 23l-6-3z" /><path d="M9 3v17M15 6v17" /></svg>
            Geometri wilayah belum tersedia. Restore data wilayah cakupan terlebih dahulu.
          </div>
        </div>

        {/* SIDEBAR */}
        <aside className="ds-side">
          <div className="ds-side-eyebrow">Indikator Capaian</div>
          <h1 className="ds-side-title" id="indTitle">—</h1>
          <div className="ds-side-sub" id="indPilar">FOLUR · GEF Core Indicators</div>

          {/* Indicator selector */}
          <div className="wg-pills" id="indPills">
            {indikator.map((m, i) => (
              <button className={`wg-pill${i === 0 ? " active" : ""}`} data-kode={m.kode} key={m.kode}>
                <div className="wg-pill-kode">{m.kode}</div>
                <div className="wg-pill-nama">{m.nama}</div>
              </button>
            ))}
          </div>

          {/* Breadcrumb hierarki yurisdiksi */}
          <div className="wg-breadcrumb" id="breadcrumb" />

          {/* Pengalih Yurisdiksi (jenjang) */}
          {levels.length > 1 && (
            <div className="wg-leveltabs" id="levelTabs">
              <span className="wg-yearbar-l" style={{ alignSelf: "center" }}>Yurisdiksi</span>
              <button type="button" className="wg-leveltab active" data-level="desa">Desa</button>
              <button type="button" className="wg-leveltab" data-level="kecamatan">Kecamatan</button>
            </div>
          )}

          {/* Pemilih TAHUN + badge agregasi */}
          <div className="wg-yearbar">
            <label htmlFor="yearSel" className="wg-yearbar-l">Tahun</label>
            <select id="yearSel" className="wg-yearsel" defaultValue={config?.tahun}>
              {years.map((y) => <option value={y} key={y}>{y}</option>)}
            </select>
            <span className="wg-aggbadge" id="aggBadge" />
          </div>

          {hasKomIcons && (
            <label className="wg-komtoggle"><input type="checkbox" id="komToggle" defaultChecked /> Ikon komoditas di peta</label>
          )}

          {/* Hero metric */}
          <div className="wg-hero">
            <div className="wg-hero-top">
              <div className="wg-hero-val" id="heroVal">—<span className="unit" id="heroUnit" /></div>
              <div className="wg-hero-pct" id="heroPct" />
            </div>
            <div className="wg-hero-target" id="heroTarget" />
            <div className="wg-progress"><div className="wg-progress-fill" id="heroBar" /></div>
            <div className="wg-hero-cum" id="heroCum" style={{ display: "none" }} />
          </div>

          <div className="wg-statgrid">
            <div className="wg-stat"><div className="wg-stat-k" id="statCovLabel">Desa Terisi Data</div><div className="wg-stat-v" id="statCov">—</div></div>
            <div className="wg-stat"><div className="wg-stat-k">Cakupan</div><div className="wg-stat-v" id="statPct">—</div></div>
          </div>
          <div className="wg-note" id="aggNote" style={{ display: "none" }} />

          {/* Selected desa */}
          <div className="ds-section" id="selSection" style={{ display: "none" }}>
            <div className="ds-section-h">Wilayah Terpilih</div>
            <div className="wg-sel">
              <div className="wg-sel-head">
                <div>
                  <div className="wg-sel-nama" id="selNama">—</div>
                  <div className="wg-sel-kec" id="selKec" />
                </div>
                <button className="wg-sel-close" id="selClose" title="Tutup">×</button>
              </div>
              <div className="wg-sel-body" id="selBody" />
              <div className="wg-sel-hist" id="selHistory" />
            </div>
          </div>

          {/* Ranking */}
          <div className="ds-section">
            <div className="ds-section-h">Peringkat Wilayah <span id="rankUnit" style={{ textTransform: "none", letterSpacing: 0, color: "var(--ink-200)" }} /></div>
            <div className="wg-rank" id="rankList"><div className="wg-rank-empty">Memuat…</div></div>
          </div>

          {/* Komoditas Fokus */}
          {komoditasFokus.length > 0 && (
            <div className="ds-section">
              <div className="ds-section-h">Komoditas Fokus</div>
              <div className="wg-komfokus">
                {komoditasFokus.map((k) => <span className="wg-komchip" key={k}>{k}</span>)}
              </div>
            </div>
          )}

          {/* Description */}
          <div className="ds-section">
            <div className="ds-section-h">Tentang Indikator</div>
            <p className="wg-desc" id="indDesc">—</p>
          </div>

          {/* Footnote */}
          <div className="ds-section" style={{ marginBottom: 0 }}>
            <div className="ds-section-h">Sumber &amp; Catatan</div>
            <p className="wg-desc">
              Batas wilayah: <strong>Badan Informasi Geospasial (BIG)</strong>. Nilai capaian per desa/kecamatan
              dientri di <strong>Panel Admin → Data Capaian</strong>; halaman ini bersifat tinjauan publik (read-only).
            </p>
          </div>
        </aside>
      </div>

      <WebGisClient />
    </div>
  );
}
