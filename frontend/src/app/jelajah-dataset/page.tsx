import Image from "next/image";
import "./jelajah-dataset.css";
import type { Metadata } from "next";
import Link from "next/link";
import { getJelajahDataset, getSiteIdentity, type DatasetExploreRow } from "@/lib/geonode";
import { PUBLIC_BASE, publicUrl, BRAND_LOGO } from "@/lib/config";
import { FilterSidebar, SearchBar, SortSelect } from "./Controls";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Eksplorasi Dataset — ${ident.siteName}`,
    description: `Telusuri seluruh dataset spasial ${ident.namaKabupaten} yang ter-publish.`,
  };
}

function badgeClass(d: DatasetExploreRow): string {
  if (d.isRaster) return "cocoa";
  if (d.feature === "Polygon") return "ochre";
  if (d.feature === "Line" || d.feature === "Point") return "sage";
  return "";
}

function RasterPlaceholder() {
  return (
    <svg viewBox="0 0 200 138" preserveAspectRatio="xMidYMid slice">
      <rect width="200" height="138" fill="#1F3A2E" />
      <g opacity="0.85">
        {[0, 46, 92].map((y) =>
          [0, 50, 100, 150].map((x, i) => (
            <rect key={`${x}-${y}`} x={x} y={y} width="50" height="46" fill="#3D6657" opacity={0.5 + ((i + y) % 4) * 0.12} />
          )),
        )}
      </g>
    </svg>
  );
}

function VectorPlaceholder() {
  return (
    <svg viewBox="0 0 200 138" preserveAspectRatio="xMidYMid slice">
      <rect width="200" height="138" fill="#8B9D83" />
      <path d="M20,50 L80,30 L120,60 L160,40 L200,70 L200,138 L20,138 Z" fill="#1F3A2E" opacity="0.6" />
      <path d="M0,90 Q60,75 120,90 T200,85 L200,138 L0,138 Z" fill="#5D3A1F" opacity="0.5" />
      <g stroke="#F4EFE6" strokeWidth="0.5" fill="none" opacity="0.35">
        <path d="M0,40 L200,40" /><path d="M0,80 L200,80" /><path d="M0,120 L200,120" />
      </g>
    </svg>
  );
}

function buildQuery(sp: Record<string, string | string[] | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(sp)) {
    if (v == null) continue;
    if (Array.isArray(v)) v.forEach((x) => p.append(k, x));
    else p.append(k, v);
  }
  return p.toString();
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const query = buildQuery(sp);
  const [data, ident] = await Promise.all([getJelajahDataset(query), getSiteIdentity()]);
  const hasActiveFilter = data.q.length > 0 || Object.values(data.selected).some((a) => a.length > 0);
  const showReset = hasActiveFilter || data.sort !== "recent";

  const pageHref = (page: number) => {
    const p = new URLSearchParams(query);
    p.set("page", String(page));
    return `/jelajah-dataset?${p.toString()}`;
  };

  return (
    <div className="ds-page">
      <link rel="stylesheet" href="/vendor/fonts/inter-mono.css" />
      {/* NAV */}
      <nav className="ds-nav">
        <div className="ds-nav__inner">
          <Link href="/" className="ds-brand">
            <span className="ds-brand__mark relative w-10 h-10 block"><Image src={ident.logo || publicUrl(BRAND_LOGO)} alt="Logo" fill className="object-contain" /></span>
            <span>
              <span className="ds-brand__t1">{ident.siteName}</span>
              <span className="ds-brand__t2">{ident.namaKabupaten}</span>
            </span>
          </Link>
          <ul className="ds-menu">
            <li><Link href="/">Beranda</Link></li>
            <li><Link href="/jelajah-dokumen">Dokumen Kebijakan</Link></li>
            <li><Link href="/jelajah-dataset" className="is-active">Eksplorasi Dataset</Link></li>
            <li><Link href="/jelajah-endpoint">Endpoint API</Link></li>
          </ul>
        </div>
      </nav>

      <section className="dataset-section">
        <div className="section-header">
          <div>
            <div className="section-eyebrow">Repositori · 03</div>
            <h1 className="section-title">Eksplorasi <span className="italic">Dataset</span></h1>
          </div>
          <p className="section-desc">
            Telusuri seluruh dataset spasial {ident.namaKabupaten} yang ter-publish. Filter berdasarkan walidata,
            kategori, jenis fitur, dan wilayah untuk menemukan data yang relevan dengan kebutuhan analisis Anda.
          </p>
        </div>

        <div className="dataset-layout">
          <FilterSidebar facets={data.facets} selected={data.selected} showReset={showReset} />

          <div className="dataset-main">
            <SearchBar q={data.q} />

            <div className="dataset-toolbar">
              <div className="dataset-count">
                {data.total > 0 ? (
                  <>Menampilkan <strong>{data.shownFrom}–{data.shownTo}</strong> dari <strong>{data.total}</strong> dataset{data.q ? ` untuk “${data.q}”` : ""}</>
                ) : (
                  <>Tidak ada dataset{data.q ? ` untuk “${data.q}”` : ""}</>
                )}
              </div>
              <SortSelect sort={data.sort} />
            </div>

            <div className="dataset-grid">
              {data.datasets.length === 0 ? (
                <div className="dataset-empty">Tidak ada dataset yang cocok dengan filter yang dipilih.</div>
              ) : (
                data.datasets.map((d) => (
                  <a href={`/dataset-spasial/${d.id}`} className="dataset-card rounded-xl" key={d.id}>
                    <div className="dataset-thumb rounded-t-xl relative h-40 w-full overflow-hidden">
                      {d.thumbnail ? (
                        <Image src={d.thumbnail} alt={d.title} fill className="object-cover" />
                      ) : d.isRaster ? (
                        <RasterPlaceholder />
                      ) : (
                        <VectorPlaceholder />
                      )}
                      <div className={`dataset-thumb-badge ${badgeClass(d)}`}>{d.feature || "Dataset"}</div>
                    </div>
                    <div className="dataset-body">
                      <div className="dataset-title">{d.title}</div>
                      <div className="dataset-meta">
                        <div className="dataset-meta-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg><div><span className="dataset-meta-key">Walidata:</span>{d.walidata || "—"}</div></div>
                        <div className="dataset-meta-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 7h18M3 12h18M3 17h18" /></svg><div><span className="dataset-meta-key">Kategori:</span>{d.category || "—"}</div></div>
                        <div className="dataset-meta-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" /></svg><div><span className="dataset-meta-key">Feature:</span>{d.feature || "—"}</div></div>
                        <div className="dataset-meta-row"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></svg><div><span className="dataset-meta-key">Wilayah:</span>{d.regions || "—"}</div></div>
                      </div>
                    </div>
                    <div className="dataset-card-footer">
                      <span className="dataset-detail-link">Detail <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg></span>
                    </div>
                  </a>
                ))
              )}
            </div>

            {data.numPages > 1 && (
              <div className="dataset-pagination">
                {data.hasPrevious && data.previousPage ? (
                  <Link className="ds-page-btn rounded-lg" href={pageHref(data.previousPage)} title="Sebelumnya"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg></Link>
                ) : (
                  <span className="ds-page-btn disabled rounded-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg></span>
                )}
                {data.pageList.map((p, i) =>
                  p == null ? (
                    <span className="ds-page-gap" key={`gap-${i}`}>…</span>
                  ) : p === data.page ? (
                    <span className="ds-page-btn current rounded-lg" key={p}>{p}</span>
                  ) : (
                    <Link className="ds-page-btn rounded-lg" href={pageHref(p)} key={p}>{p}</Link>
                  ),
                )}
                {data.hasNext && data.nextPage ? (
                  <Link className="ds-page-btn" href={pageHref(data.nextPage)} title="Berikutnya"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg></Link>
                ) : (
                  <span className="ds-page-btn disabled rounded-lg"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg></span>
                )}
              </div>
            )}
          </div>
        </div>
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
