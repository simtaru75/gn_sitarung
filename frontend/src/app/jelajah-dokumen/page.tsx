import Image from "next/image";
import "./jelajah-dokumen.css";
import type { Metadata } from "next";
import Link from "next/link";
import { getJelajahDokumen, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE, publicUrl, BRAND_LOGO } from "@/lib/config";
import { buildQuery } from "@/lib/query";
import { FilterSidebar, SearchBox } from "./Controls";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Jelajah Dokumen Kebijakan — ${ident.siteName}`,
    description: `Telusuri dokumen kebijakan & perencanaan ${ident.namaKabupaten} yang terbuka untuk publik.`,
  };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

/** Format ISO → "DD Mon YYYY, HH:MM" dalam WIB (UTC+7). */
function fmtDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const wib = new Date(d.getTime() + 7 * 3600 * 1000);
  const dd = String(wib.getUTCDate()).padStart(2, "0");
  const hh = String(wib.getUTCHours()).padStart(2, "0");
  const mm = String(wib.getUTCMinutes()).padStart(2, "0");
  return `${dd} ${MONTHS[wib.getUTCMonth()]} ${wib.getUTCFullYear()}, ${hh}:${mm}`;
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const query = buildQuery(sp);
  const [data, ident] = await Promise.all([getJelajahDokumen(query), getSiteIdentity()]);
  const hasActiveFilter = data.q.length > 0 || Object.values(data.selected).some((a) => a.length > 0);

  const pageHref = (page: number) => {
    const p = new URLSearchParams(query);
    p.set("page", String(page));
    return `/jelajah-dokumen?${p.toString()}`;
  };

  return (
    <div className="pd-page">
      <link rel="stylesheet" href="/vendor/fonts/inter-mono.css" />
      {/* NAV */}
      <nav className="pd-nav">
        <div className="pd-nav__inner">
          <Link href="/" className="pd-brand">
            <span className="pd-brand__mark relative w-10 h-10 block"><Image src={ident.logo || publicUrl(BRAND_LOGO)} alt="Logo" fill className="object-contain" /></span>
            <span>
              <span className="pd-brand__t1">{ident.siteName}</span>
              <span className="pd-brand__t2">{ident.namaKabupaten}</span>
            </span>
          </Link>
          <ul className="pd-menu">
            <li><Link href="/">Beranda</Link></li>
            <li><Link href="/jelajah-dokumen" className="is-active">Dokumen Kebijakan</Link></li>
            <li><Link href="/jelajah-dataset">Eksplorasi Dataset</Link></li>
            <li><Link href="/jelajah-endpoint">Endpoint API</Link></li>
          </ul>
        </div>
      </nav>

      {/* HEADER */}
      <header className="pd-head">
        <div className="pd-head__eyebrow">Satu Data Indonesia · {ident.namaKabupaten}</div>
        <h1 className="pd-head__title">Jelajah Dokumen <span className="italic">Kebijakan</span></h1>
        <p className="pd-head__desc">
          Telusuri dokumen kebijakan &amp; perencanaan yang terbuka untuk publik — disaring berdasarkan{" "}
          <strong>Produsen Data</strong> (Walidata) atau kata kunci.
        </p>
      </header>

      <div className="pd-wrap">
        <FilterSidebar facets={data.facets} selected={data.selected} hasActiveFilter={hasActiveFilter} />

        <main className="pd-main">
          <SearchBox q={data.q} />

          <p className="pd-count">
            <strong>{data.total}</strong> dokumen{hasActiveFilter ? " · hasil filter" : ""}
          </p>

          <div className="pd-thead rounded-xl">
            <span className="pd-thead__col">Judul</span>
            <span className="pd-thead__col">Format &amp; Tahun</span>
            <span className="pd-thead__col">Kategori</span>
          </div>

          <div className="pd-list">
            {data.documents.length === 0 ? (
              <div className="pd-empty">Tidak ada dokumen yang cocok dengan filter / pencarian Anda.</div>
            ) : (
              data.documents.map((d) => (
                <article className="pd-card rounded-xl" key={d.id}>
                  <div>
                    <h3 className="pd-card__title"><a href={`/dataset-dokumen/${d.id}`}>{d.title}</a></h3>
                    {(d.walidata || d.pengelola) && (
                      <p className="pd-card__meta">
                        <svg className="pd-ico" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="4" y="4" width="16" height="16" rx="2" /><path d="M4 9h16M9 4v16" /></svg>
                        {d.walidata || d.pengelola}
                      </p>
                    )}
                    {d.updated && (
                      <p className="pd-card__meta">
                        <svg className="pd-ico" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 9h18M8 3v4M16 3v4" /></svg>
                        Diperbarui pada {fmtDate(d.updated)} WIB
                      </p>
                    )}
                    <a href={`/dataset-dokumen/${d.id}`} className="pd-detail">
                      DETAIL
                      <span className="pd-detail__arr"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="m9 6 6 6-6 6" /></svg></span>
                    </a>
                  </div>

                  <div>
                    <span className="pd-field__label">Format</span>
                    <span className="pd-field__value">{d.extension || "—"}</span>
                    <span className="pd-field__label pd-field__label--mt">Tahun</span>
                    <span className="pd-field__value">{d.year || "—"}</span>
                  </div>

                  <div>
                    <span className="pd-field__value">{d.kategori || "—"}</span>
                  </div>
                </article>
              ))
            )}
          </div>

          <nav className="pd-pager" aria-label="Navigasi halaman">
            {data.hasPrevious ? (
              <Link className="pd-pager__btn rounded-xl" href={pageHref(data.page - 1)}>Sebelumnya</Link>
            ) : (
              <span className="pd-pager__btn pd-pager__btn--disabled rounded-xl">Sebelumnya</span>
            )}
            {data.hasNext ? (
              <Link className="pd-pager__btn rounded-xl" href={pageHref(data.page + 1)}>Berikutnya</Link>
            ) : (
              <span className="pd-pager__btn pd-pager__btn--disabled rounded-xl">Berikutnya</span>
            )}
          </nav>
        </main>
      </div>

      {/* FOOTER */}
      <footer className="pd-footer">
        <div className="pd-footer__inner">
          <div>© 2026 {ident.siteName} · {ident.namaKabupaten}</div>
          <Link href="/jelajah-dataset">Eksplorasi Dataset →</Link>
        </div>
      </footer>
    </div>
  );
}
