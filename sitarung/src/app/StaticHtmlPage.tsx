import { DEFAULT_SITE_LOGO, type SiteIdentity } from "@/lib/geonode";
import type { StaticPageData } from "@/lib/static-pages";

const SECTION_LABELS = {
  rtrw: "Materi RTRW",
  lainnya: "Informasi Publik",
} as const;

export default function StaticHtmlPage({
  page,
  site,
  sectionLabelOverride,
  siblingsOverride,
  hideSidebar = false,
}: {
  page: StaticPageData;
  site: SiteIdentity | null;
  sectionLabelOverride?: string;
  siblingsOverride?: Array<{ slug: string; label: string; href: string }>;
  hideSidebar?: boolean;
}) {
  const sectionLabel = sectionLabelOverride || SECTION_LABELS[page.section];
  const pageLead = page.subheading && page.subheading !== page.heading ? page.subheading : page.summary;
  const siteLabel = site?.siteName && site.siteName !== "DST" ? site.siteName : "SITARUNG";
  const regionLabel = site?.namaKabupaten && site.namaKabupaten !== "Kabupaten" ? site.namaKabupaten : "Provinsi Sumatera Selatan";
  const currentYear = new Date().getFullYear();
  const siteLogo = site?.logo || DEFAULT_SITE_LOGO;
  const siblings = siblingsOverride || page.siblings;

  return (
    <div className="min-h-screen bg-(--paper) text-(--ink)">
      <header className="border-b border-white/10 bg-(--color-cap-green-700) text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-6 py-4">
          <img src={siteLogo} alt={siteLabel} className="h-10 w-10 rounded-full bg-white/92 object-contain p-1 shadow-[0_6px_18px_rgba(0,0,0,0.18)]" />
          <a href="/" className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/6 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/12">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6" /></svg>
            Beranda
          </a>
          <span className="text-xs font-bold uppercase tracking-[0.24em] text-white">{siteLabel}</span>
          <span className="text-xs uppercase tracking-[0.18em] text-white/72">/ {sectionLabel}</span>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-10 md:py-14">
        <div className="mb-10 max-w-4xl">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-(--ochre-600)">{sectionLabel}</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-(--forest) md:text-5xl">{page.heading}</h1>
          {pageLead && <p className="mt-4 text-base leading-relaxed text-(--ink-600) md:text-lg">{pageLead}</p>}
        </div>

        <div className={hideSidebar ? "grid gap-8" : "grid gap-8 lg:grid-cols-[260px_minmax(0,1fr)]"}>
          {!hideSidebar && (
            <aside className="self-start rounded-3xl border border-(--line) bg-white p-5 shadow-[0_10px_30px_-20px_rgba(31,58,46,0.35)] lg:sticky lg:top-24">
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-(--ink-400)">Jelajah Halaman</p>
              <nav className="mt-4 flex flex-col gap-2">
                {siblings.map((item) => {
                  const isActive = page.slug === item.slug || (page.slug === "index" && item.slug === "tujuan" && page.section === "rtrw") || (page.slug === "index" && item.slug === "aboutus" && page.section === "lainnya");
                  return (
                    <a
                      key={item.slug}
                      href={item.href}
                      className={`rounded-2xl px-4 py-3 text-sm transition ${
                        isActive
                          ? "bg-(--forest) font-semibold text-(--cream)"
                          : "bg-(--paper) text-(--ink-600) hover:bg-(--cream) hover:text-(--forest)"
                      }`}
                    >
                      {item.label}
                    </a>
                  );
                })}
              </nav>
            </aside>
          )}

          <article className="overflow-hidden rounded-[28px] border border-(--line) bg-white px-5 py-6 shadow-[0_18px_50px_-28px_rgba(31,58,46,0.35)] md:px-8 md:py-10">
            <div className="static-page-html" dangerouslySetInnerHTML={{ __html: page.html }} />
          </article>
        </div>
      </main>

      <footer className="bg-(--color-cap-green-700) text-white/82">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-7 text-sm">
          <div>© {currentYear} {siteLabel} · {regionLabel}</div>
          <a href="/" className="text-white no-underline transition hover:underline">Kembali ke Beranda →</a>
        </div>
      </footer>

      <style>{STATIC_PAGE_CSS}</style>
    </div>
  );
}

const STATIC_PAGE_CSS = `
  .static-page-html {
    color: var(--ink-600);
    font-family: var(--sans);
    font-size: 0.97rem;
    line-height: 1.85;
  }
  .static-page-html > *:first-child { margin-top: 0; }
  .static-page-html h1,
  .static-page-html h2,
  .static-page-html h3,
  .static-page-html h4,
  .static-page-html h5 {
    color: var(--forest);
    font-family: var(--serif);
    line-height: 1.2;
    margin: 1.75rem 0 0.75rem;
  }
  .static-page-html h2 { font-size: 1.7rem; }
  .static-page-html h3 { font-size: 1.3rem; }
  .static-page-html h4,
  .static-page-html h5 { font-size: 1.05rem; font-family: var(--sans); font-weight: 700; }
  .static-page-html p,
  .static-page-html ol,
  .static-page-html ul,
  .static-page-html blockquote {
    margin: 0 0 1rem;
  }
  .static-page-html ul {
    list-style-type: disc;
    padding-left: 1.35rem;
  }
  .static-page-html ol {
    list-style-type: decimal;
    padding-left: 1.35rem;
  }
  .static-page-html ol[type="a"],
  .static-page-html ol[type="A"] {
    list-style-type: lower-alpha;
  }
  .static-page-html ol[type="i"],
  .static-page-html ol[type="I"] {
    list-style-type: lower-roman;
  }
  .static-page-html ul ul,
  .static-page-html ol ul {
    list-style-type: circle;
  }
  .static-page-html ul ul ul,
  .static-page-html ol ul ul {
    list-style-type: square;
  }
  .static-page-html li + li {
    margin-top: 0.35rem;
  }
  .static-page-html a {
    color: var(--ochre-600);
    text-decoration: none;
  }
  .static-page-html a:hover {
    text-decoration: underline;
  }
  .static-page-html img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 1.5rem auto;
    border-radius: 18px;
    border: 1px solid var(--line);
  }
  .static-page-html table {
    display: block;
    width: 100%;
    overflow-x: auto;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.92rem;
  }
  .static-page-html th,
  .static-page-html td {
    border: 1px solid var(--line-strong);
    padding: 0.75rem;
    vertical-align: top;
    background: white;
  }
  .static-page-html th {
    background: var(--cream);
    color: var(--forest);
    font-weight: 700;
  }
  .static-page-html strong,
  .static-page-html b {
    color: var(--ink);
  }
  .static-page-html hr {
    border: 0;
    border-top: 1px solid var(--line);
    margin: 1.5rem 0;
  }
`;