import "./jelajah-endpoint.css";
import type { Metadata } from "next";
import Link from "next/link";
import { getEndpoints, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE, publicUrl, BRAND_LOGO } from "@/lib/config";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Endpoint API & OGC — ${ident.siteName}`,
    description: `Daftar endpoint REST v2 & OGC Services (WMS/WFS/WCS/WMTS/CSW) yang aktif pada ${ident.siteName}.`,
  };
}

export default async function Page() {
  const [data, ident] = await Promise.all([getEndpoints(), getSiteIdentity()]);

  return (
    <div className="ep-page">
      <link rel="stylesheet" href="/vendor/fonts/inter-mono.css" />
      {/* NAV */}
      <nav className="ds-nav">
        <div className="ds-nav__inner">
          <Link href="/" className="ds-brand">
            <span className="ds-brand__mark"><img src={ident.logo || publicUrl(BRAND_LOGO)} alt="Logo" /></span>
            <span>
              <span className="ds-brand__t1">{ident.siteName}</span>
              <span className="ds-brand__t2">{ident.namaKabupaten}</span>
            </span>
          </Link>
          <ul className="ds-menu">
            <li><Link href="/">Beranda</Link></li>
            <li><Link href="/jelajah-dokumen">Dokumen Kebijakan</Link></li>
            <li><Link href="/jelajah-dataset">Eksplorasi Dataset</Link></li>
            <li><Link href="/jelajah-endpoint" className="is-active">Endpoint API</Link></li>
          </ul>
        </div>
      </nav>

      <section className="endpoint-section" id="endpoint-api">
        <div className="section-header">
          <div>
            <div className="section-eyebrow">Distribusi &amp; Akses · API</div>
            <h1 className="section-title">Endpoint <span className="italic">API &amp; OGC</span></h1>
          </div>
          <p className="section-desc">
            Daftar endpoint resmi GeoNode REST v2 dan OGC Services (WMS, WFS, WCS, WMTS, CSW) yang aktif
            pada {ident.siteName}. Gunakan untuk integrasi langsung ke QGIS/ArcGIS, sistem pemerintahan,
            atau aplikasi pihak ketiga. Hitungan resource diambil langsung dari katalog {ident.namaKabupaten}.
          </p>
        </div>

        {/* Base URL */}
        <div className="ep-baseurl">
          <span className="ep-baseurl-label">Base URL</span>
          <span className="ep-baseurl-value">{data.baseUrl || PUBLIC_BASE}</span>
        </div>

        {/* Stats */}
        <div className="ep-stats">
          <div className="ep-stat">
            <div className="ep-stat-label">Total Endpoint</div>
            <div className="ep-stat-value">{data.stats.totalEndpoints}</div>
            <div className="ep-stat-meta">REST &amp; OGC tercatat</div>
          </div>
          <div className="ep-stat">
            <div className="ep-stat-label">Dataset</div>
            <div className="ep-stat-value">{data.stats.datasets}</div>
            <div className="ep-stat-meta">via <code>/api/v2/datasets</code></div>
          </div>
          <div className="ep-stat">
            <div className="ep-stat-label">Dokumen</div>
            <div className="ep-stat-value">{data.stats.documents}</div>
            <div className="ep-stat-meta">via <code>/api/v2/documents</code></div>
          </div>
          <div className="ep-stat">
            <div className="ep-stat-label">OGC Services</div>
            <div className="ep-stat-value">{data.stats.ogcServices}</div>
            <div className="ep-stat-meta">{data.geoserverUrl}</div>
          </div>
        </div>

        {/* Endpoint groups */}
        {data.groups.map((g) => (
          <div className="ep-group" key={g.title}>
            <div className="ep-group-header">
              {g.title}
              <span className="ep-group-count">{g.items.length}</span>
            </div>
            {g.items.map((it) => (
              <div className="ep-row" key={`${it.method}-${it.path}`}>
                <span className={`ep-method ${it.method.toLowerCase()}`}>{it.method}</span>
                <span className="ep-path">{it.path}</span>
                <span className="ep-desc">{it.desc}</span>
                {it.count != null ? (
                  <span className="ep-count">{it.count}<span className="ep-count-label">item</span></span>
                ) : (
                  <span className="ep-count empty">—</span>
                )}
                <span className="ep-action">
                  {it.link ? (
                    <a href={it.link} target="_blank" rel="noopener noreferrer">{it.linkLabel}</a>
                  ) : (
                    <span className="ep-action-id">{"{id}"}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        ))}
      </section>

      <footer className="ds-footer">
        <div className="ds-footer__inner">
          <div>© 2026 {ident.siteName} · {ident.namaKabupaten}</div>
          <a href={`${PUBLIC_BASE}/catalogue/csw`} target="_blank" rel="noopener noreferrer">Katalog CSW</a>
        </div>
      </footer>
    </div>
  );
}
