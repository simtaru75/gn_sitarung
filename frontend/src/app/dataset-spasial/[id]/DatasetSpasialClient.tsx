"use client";

import "./dataset-spasial.css";
import { useMemo, useState } from "react";
import type { DatasetDetail, SiteIdentity } from "@/lib/geonode";
import dynamic from "next/dynamic";

const MapComponent = dynamic(
  () => import("./MapComponent"),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 flex flex-col gap-2.5 items-center justify-center text-center p-10 z-[400] bg-gray-100 animate-pulse">
        <svg className="w-10 h-10 opacity-40 text-gray-500 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
          <path fill="currentColor" d="M12 2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8V2z" />
        </svg>
        <span>Memuat peta spasial...</span>
      </div>
    ),
  }
);

export default function DatasetSpasialClient({
  ds,
  site,
  publicBase,
}: {
  ds: DatasetDetail;
  site: SiteIdentity | null;
  publicBase: string;
}) {
  const [mapReady, setMapReady] = useState(false);
  const [basemap, setBasemap] = useState("osm");
  const [opacity, setOpacity] = useState(100);

  const kabName = site?.namaKabupaten ?? "Luwu";
  const hasLayer = Boolean(ds.typename);

  const bbox = useMemo(() => ds.bbox || ds.extent?.coords || null, [ds]);

  const bboxText = bbox
    ? `${bbox[0].toFixed(4)}, ${bbox[1].toFixed(4)} → ${bbox[2].toFixed(4)}, ${bbox[3].toFixed(4)}`
    : "";

  return (
    <div className="flex flex-col h-screen overflow-hidden text-sm" style={{ fontFamily: "var(--sans)", background: "var(--cream)", color: "var(--ink)" }}>
      {/* ===== HEADER ===== */}
      <header className="flex-shrink-0 flex items-center gap-4 px-6 py-3 border-b z-50" style={{ background: "var(--forest)", color: "var(--cream)", borderColor: "var(--header-line)" }}>
        <a href="/jelajah-dataset" className="inline-flex items-center gap-2 text-sm px-4 py-1.5 border rounded transition" style={{ color: "var(--cream-300)", borderColor: "var(--cream-a25)" }}>
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Katalog
        </a>
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="h-10 w-10 flex-shrink-0 flex items-center justify-center overflow-hidden" style={{ background: "var(--cream)", color: "var(--forest)" }}>
            {site?.logo ? <img src={site.logo} alt="" className="w-full h-full object-contain p-0.5 box-border" /> : <span style={{ fontFamily: "var(--serif)", fontWeight: 600 }}>L</span>}
          </div>
          <div className="min-w-0">
            <div className="text-[9px] tracking-[0.16em] uppercase" style={{ fontFamily: "var(--font-sans)", color: "var(--ochre)" }}>
              Detail Dataset · {kabName}
            </div>
            <div className="text-[17px] font-medium leading-tight whitespace-nowrap overflow-hidden text-ellipsis" style={{ fontFamily: "var(--font-sans)", maxWidth: "48vw" }} title={ds.title}>
              {ds.title}
            </div>
          </div>
        </div>
        <div className="flex-1" />
      </header>

      {/* ===== BODY ===== */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_380px] min-h-0">
        {/* ===== MAP ===== */}
        <div className="relative overflow-hidden" style={{ minHeight: "360px" }}>
          {hasLayer && (
            <MapComponent
              ds={ds}
              site={site}
              publicBase={publicBase}
              opacity={opacity}
              basemap={basemap}
              setMapReady={setMapReady}
              setOpacity={setOpacity}
              setBasemap={setBasemap}
            />
          )}
          {!hasLayer && (
            <div className="absolute inset-0 flex flex-col gap-2.5 items-center justify-center text-center p-10 z-[400]" style={{ color: "var(--ink-400)", fontFamily: "var(--mono)", fontSize: 12 }}>
              <svg className="w-10 h-10 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M9 20l-5.5 3V6L9 3l6 3 5.5-3v17L15 23l-6-3z" /><path d="M9 3v17M15 6v17" /></svg>
              Dataset ini belum memiliki layer spasial ter-publish di GeoServer. Hanya metadata yang tersedia.
            </div>
          )}

          {hasLayer && (
            <>
              {/* Legend */}
              <div className="map-card legend" id="legendCard" style={{ top: 14, left: 14, width: 230, maxHeight: "46%" }}>
                <div className="map-card-head" onClick={(e) => (e.currentTarget.parentElement as HTMLElement).classList.toggle("collapsed")}>
                  <svg className="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
                  <span className="map-card-title">Legenda</span>
                  <span className="map-card-caret">▾</span>
                </div>
                <div className="map-card-body">
                  <LegendContent typename={ds.typename} publicBase={publicBase} />
                  <div className="opacity-row">
                    <label>Opasitas</label>
                    <input type="range" min="0" max="100" value={opacity} onChange={(e) => setOpacity(Number(e.target.value))} />
                  </div>
                </div>
              </div>

              {/* Zoom tools */}
              <div className="map-tools" style={{ top: 14, right: 14 }}>
                <button className="map-btn" title="Perbesar" onClick={() => {}}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                </button>
                <button className="map-btn" title="Perkecil" onClick={() => {}}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" /></svg>
                </button>
              </div>

              {/* Basemap switcher */}
              <div className="map-card bg-control" id="bgCard" style={{ bottom: 26, left: 14, width: 200 }}>
                <div className="map-card-head" onClick={(e) => (e.currentTarget.parentElement as HTMLElement).classList.toggle("collapsed")}>
                  <svg className="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="3" y="3" width="18" height="18" rx="1" /><path d="M3 9h18M9 3v18" /></svg>
                  <span className="map-card-title">Peta Dasar</span>
                  <span className="map-card-caret">▾</span>
                </div>
                <div className="map-card-body">
                  <div className="bg-list">
                    {["osm", "topo", "s2", "none"].map((k) => (
                      <div key={k} className={`bg-item${basemap === k ? " active" : ""}`} data-basemap={k} onClick={() => setBasemap(k)}>
                        <span className="bg-swatch" style={{ background: k === "osm" ? "var(--swatch-osm)" : k === "topo" ? "var(--swatch-topo)" : k === "s2" ? "var(--swatch-s2)" : "var(--cream)" }} />
                        {k === "osm" ? "OpenStreetMap" : k === "topo" ? "OpenTopoMap" : k === "s2" ? "Citra Sentinel-2" : "Tanpa Peta Dasar"}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* ===== SIDEBAR ===== */}
        <aside className="overflow-y-auto px-5 py-6 lg:pb-10 border-l" style={{ background: "var(--paper)", borderColor: "var(--line-strong)", fontFamily: "var(--font-sans)" }}>
          <div className="text-[10px] tracking-[0.16em] uppercase mb-2" style={{ fontFamily: "var(--font-sans)", color: "var(--ochre-600)" }}>Metadata Dataset</div>
          <h1 className="text-[26px] font-medium leading-tight mb-3.5 break-words" style={{ fontFamily: "var(--font-serif)", color: "var(--forest)", letterSpacing: "-0.01em" }}>{ds.title}</h1>

          {/* Badges */}
          <div className="flex flex-wrap gap-1.5 mb-5">
            {ds.feature && <Badge color={ds.isRaster ? "cocoa" : ds.feature === "Polygon" ? "ochre" : "sage"}>{ds.feature}</Badge>}
            {ds.kategori && <Badge color="outline">{ds.kategori}</Badge>}
            <Badge color="outline">{ds.srid}</Badge>
          </div>

          {/* Ringkasan */}
          <div className="mb-6 flex flex-col gap-2.5">
            <div className="flex items-start gap-4">
              <span className="flex-shrink-0 w-[84px] text-xs uppercase" style={{ color: "var(--ink-400)" }}>PRODUSEN</span>
              <span className="font-medium leading-normal" style={{ color: "var(--ink-900)" }}>{ds.walidata || "—"}</span>
            </div>
            <div className="flex items-start gap-4">
              <span className="flex-shrink-0 w-[84px] text-xs uppercase" style={{ color: "var(--ink-400)" }}>ZONA</span>
              <span className="font-medium leading-normal animate-blur-load" style={{ color: "var(--ink-900)" }}>{ds.regions.join(", ") || "Seluruh Kabupaten"}</span>
            </div>
            <div className="flex items-start gap-4">
              <span className="flex-shrink-0 w-[84px] text-xs uppercase" style={{ color: "var(--ink-400)" }}>TAHUN</span>
              <span className="font-medium leading-normal" style={{ color: "var(--ink-900)" }}>{ds.year || "—"}</span>
            </div>
          </div>

          {/* Abstrak */}
          <div className="pt-5 border-t border-dashed mb-6" style={{ borderColor: "var(--line)" }}>
            <h3 className="text-xs uppercase font-semibold mb-2.5" style={{ color: "var(--ink-500)", letterSpacing: "0.06em" }}>Deskripsi</h3>
            <div className={`prose max-w-none text-xs leading-relaxed ${ds.hasRealAbstract ? "italic font-medium" : ""}`} style={{ color: "var(--ink-850)" }}>
              {ds.abstract || "Produsen data belum melengkapi deskripsi abstrak untuk dataset spasial ini."}
            </div>
          </div>

          {/* Download & Links */}
          <div className="pt-5 border-t border-dashed mb-6" style={{ borderColor: "var(--line)" }}>
            <h3 className="text-xs uppercase font-semibold mb-2.5" style={{ color: "var(--ink-500)", letterSpacing: "0.06em" }}>Unduh & Tautan</h3>
            <div className="flex flex-col gap-2">
              {ds.downloads.map((dl) => (
                <a key={dl.url} href={dl.url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between p-2.5 rounded border hover:bg-gray-50 transition" style={{ borderColor: "var(--line)" }}>
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1M4 12V9a3 3 0 013-3h10a3 3 0 013 3v3" /><path d="M12 5v13M12 18l-4-4m4 4l4-4" /></svg>
                    <span className="font-semibold text-xs text-gray-800">{dl.kind}</span>
                  </div>
                  <span className="text-[10px] text-gray-400 font-mono">{dl.meta}</span>
                </a>
              ))}
            </div>
          </div>
        </aside>
      </div>
      <style>{MAP_CSS}</style>
    </div>
  );
}

function LegendContent({ typename, publicBase }: { typename: string; publicBase: string }) {
  const url = `${publicBase}/geoserver/wms?request=GetLegendGraphic&format=image/png&layer=${encodeURIComponent(typename)}&legend_options=forceRuleAdherence:true;fontSize:11;fontName:system-ui;fontColor:0x333333;fontAntiAliasing:true;dpi:96`;
  return (
    <div className="legend-img-wrap">
      <img src={url} alt="Legenda layer" onError={(e) => { e.currentTarget.style.display = "none"; }} />
    </div>
  );
}

function Badge({ children, color }: { children: React.ReactNode; color: "ochre" | "sage" | "cocoa" | "outline" }) {
  let style: React.CSSProperties = {};
  if (color === "ochre") style = { background: "var(--ochre-100)", color: "var(--ochre-800)" };
  else if (color === "sage") style = { background: "var(--sage-100)", color: "var(--sage-800)" };
  else if (color === "cocoa") style = { background: "var(--cocoa-100)", color: "var(--cocoa-800)" };
  else if (color === "outline") style = { border: "1px solid var(--line-strong)", background: "transparent", color: "var(--ink-500)" };
  return (
    <span className="inline-flex px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded" style={style}>
      {children}
    </span>
  );
}

// CSS untuk panel peta yang mengambang (legend, basemap, zoom tools)
const MAP_CSS = `
  .map-card { position:absolute; z-index:500; background:rgba(250,247,240,0.95); backdrop-filter:blur(6px); border:1px solid var(--line-strong, rgba(31,58,46,0.2)); box-shadow:0 4px 16px rgba(31,58,46,0.12); display:flex; flex-direction:column; border-radius:12px; overflow:hidden; }
  .map-card-head { display:flex; align-items:center; gap:8px; padding:9px 12px; border-bottom:1px solid var(--line, rgba(31,58,46,0.1)); cursor:pointer; user-select:none; }
  .map-card-head svg.ic { width:13px; height:13px; color:var(--forest, #1F3A2E); }
  .map-card-title { font-family:monospace; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; color:var(--forest, #1F3A2E); }
  .map-card-caret { margin-left:auto; transition:transform 0.2s; color:var(--ink-400, #7A7A7A); }
  .map-card.collapsed .map-card-caret { transform:rotate(-90deg); }
  .map-card.collapsed .map-card-body { display:none; }
  .map-card-body { padding:10px 12px; overflow-y:auto; }
  .legend-img-wrap img { max-width:100%; display:block; margin-top:2px; }
  .opacity-row { display:flex; align-items:center; gap:8px; padding:8px 12px; border-top:1px solid var(--line, rgba(31,58,46,0.1)); }
  .opacity-row label { font-family:monospace; font-size:9px; text-transform:uppercase; letter-spacing:0.08em; color:var(--ink-400, #7A7A7A); }
  .opacity-row input { flex:1; accent-color:var(--forest, #1F3A2E); }
  .map-tools { position:absolute; top:14px; right:14px; z-index:500; display:flex; flex-direction:column; gap:6px; }
  .map-btn { width:36px; height:36px; display:grid; place-items:center; cursor:pointer; background:rgba(250,247,240,0.95); border:1px solid var(--line-strong, rgba(31,58,46,0.2)); color:var(--forest, #1F3A2E); transition:all 0.15s; box-shadow:0 2px 8px rgba(31,58,46,0.1); border-radius:8px; }
  .map-btn:hover { background:var(--forest, #1F3A2E); color:var(--cream, #F4EFE6); border-color:var(--forest, #1F3A2E); }
  .map-btn svg { width:16px; height:16px; }
  .bg-control { bottom:26px; left:14px; width:200px; }
  .bg-list { padding:6px; }
  .bg-item { display:flex; align-items:center; gap:9px; padding:7px 8px; cursor:pointer; font-size:12px; color:var(--ink-600, #4A4A4A); transition:background 0.15s; border-radius:6px; }
  .bg-item:hover { background:var(--cream-200, #E8DFCE); }
  .bg-item.active { background:var(--forest, #1F3A2E); color:var(--cream, #F4EFE6); }
  .bg-swatch { width:26px; height:20px; flex-shrink:0; border:1px solid var(--line-strong, rgba(31,58,46,0.2)); background-size:cover; background-position:center; border-radius:3px; }
  .leaflet-container { font-family:var(--sans, 'Geist', system-ui, sans-serif) !important; }
  .leaflet-control-zoom { display:none !important; }
  .leaflet-control-attribution { background:rgba(250,247,240,0.92) !important; font-family:monospace !important; font-size:9px !important; color:var(--ink-400, #7A7A7A) !important; padding:2px 8px !important; border:1px solid var(--line, rgba(31,58,46,0.1)) !important; }
  .leaflet-control-attribution a { color:var(--ochre-600, #A66830) !important; }
`;
