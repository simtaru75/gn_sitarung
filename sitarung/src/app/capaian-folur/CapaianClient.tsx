"use client";

import type { CapaianData, SiteIdentity } from "@/lib/geonode";

function fmtInt(n: number): string {
  return n.toLocaleString("id-ID").replace(/,/g, ".");
}

export default function CapaianClient({
  data,
  site,
  publicBase,
}: {
  data: CapaianData | null;
  site: SiteIdentity | null;
  publicBase: string;
}) {
  const auto = data?.sitroom?.auto;
  const kpis = data?.indikator ?? [];
  const komoditas = data?.komoditas ?? [];
  // Nama wilayah cakupan dari data capaian (selalu segar) — bukan SiteIdentity
  // yang bisa basi/ter-cache. Deskripsi merujuk cakupan terpilih (Pengaturan).
  // Tanpa prefiks (label "Kabupaten"/"KABUPATEN" sudah ditambah di markup) agar
  // tak dobel saat sumbernya sudah ber-prefiks.
  const kabRaw = data?.kabupaten?.namaKab || site?.namaKabupaten || "Luwu";
  const isKota = /^Kota\s+/i.test(kabRaw);
  const kabName = kabRaw.replace(/^(Kabupaten|Kota)\s+/i, "");
  const kabPrefix = isKota ? "Kota" : "Kabupaten";
  const kabPrefixUpper = isKota ? "KOTA" : "KABUPATEN";

  // Fallback KPI data jika API kosong
  const displayKpis = kpis.length >= 4 ? kpis.slice(0, 4) : [
    { kode: "CI1", nama: "Kawasan lindung terkelola efektif", pilarNama: "Kawasan Lindung", satuan: "ha", nilai: 8420, target: 12500, persen: 51, agregasi: "tahunan", pilar: "", deskripsi: "", extra: "" },
    { kode: "CI3", nama: "Lahan terestorasi", pilarNama: "Restorasi Lahan", satuan: "ha", nilai: 540, target: 1200, persen: 45, agregasi: "tahunan", pilar: "", deskripsi: "", extra: "" },
    { kode: "CI4", nama: "Bentang lahan praktik produksi lestari", pilarNama: "Praktik Lestari", satuan: "ha", nilai: 3150, target: 9000, persen: 30, agregasi: "tahunan", pilar: "", deskripsi: "", extra: "" },
    { kode: "CI11", nama: "Penerima manfaat (petani)", pilarNama: "Penerima Manfaat", satuan: "orang", nilai: 2840, target: 6500, persen: 44, agregasi: "tahunan", pilar: "", deskripsi: "", extra: "" },
  ];

  // Nilai dari database (cakupan wilayah di Pengaturan). Cakupan bisa berbasis
  // desa atau kelurahan — tampilkan jenjang yang relevan.
  const luasHa = auto?.luasBentangHa ?? 0;
  const jmlKec = auto?.jmlKecamatan ?? 0;
  const jmlDesa = auto?.jmlDesa ?? 0;
  const jmlKel = auto?.jmlKelurahan ?? 0;
  const persenMaju = auto?.persenDesaMaju ?? 0;
  const komoditasCount = auto?.komoditasFokus || komoditas.length;
  const wilayahN = jmlDesa || jmlKel;
  const wilayahLabel = jmlDesa ? "desa" : "kelurahan";
  // Nama komoditas mengikuti Daftar Komoditas (Pengaturan), bukan teks statis.
  const komoditasNama = komoditas.length ? komoditas.join(", ") : "komoditas unggulan";

  return (
    <div className="min-h-screen bg-white text-gray-800">
      {/* ===== NAVBAR (gaya jelajah-endpoint: bar forest) ===== */}
      <nav className="bg-ds-forest text-ds-cream">
        <div className="max-w-[1320px] mx-auto px-6 md:px-10 py-3.5 flex items-center justify-between gap-4">
          <a href="/" className="flex items-center gap-3 no-underline text-ds-cream">
            <span className="w-10 h-10 bg-ds-cream flex items-center justify-center overflow-hidden shrink-0">
              <img src={site?.logo || `${publicBase}/icon.png`} alt="Logo" className="w-full h-full object-contain p-0.5 box-border" />
            </span>
            <span className="leading-tight">
              <span className="block font-bold text-[15px]">{site?.siteName || "DST Luwu"}</span>
              <span className="block mt-0.5 font-mono text-[11px] leading-none opacity-80 tracking-[0.04em]">{kabPrefix} {kabName}</span>
            </span>
          </a>
          <ul className="hidden md:flex items-center gap-[26px] list-none m-0 p-0 text-sm">
            <li><a href="/" className="text-ds-cream/80 no-underline hover:text-ds-cream transition-colors">Beranda</a></li>
            <li><a href="/jelajah-dokumen" className="text-ds-cream/80 no-underline hover:text-ds-cream transition-colors">Dokumen Kebijakan</a></li>
            <li><a href="/jelajah-dataset" className="text-ds-cream/80 no-underline hover:text-ds-cream transition-colors">Eksplorasi Dataset</a></li>
            <li><a href="/jelajah-endpoint" className="text-ds-cream/80 no-underline hover:text-ds-cream transition-colors">Endpoint API</a></li>
            <li><a href="/capaian-folur" className="text-ds-cream font-semibold no-underline">Capaian</a></li>
          </ul>
        </div>
      </nav>

      {/* ===== CONTENT ===== */}
      <main className="bg-cap-bg text-cap-ink">
        <section className="py-24">
          <div className="max-w-[1120px] mx-auto px-6 lg:px-14">
            {/* Eyebrow */}
            <span className="inline-block text-xs font-semibold tracking-[0.14em] uppercase mb-6 font-mono text-cap-green-700">
              CAPAIAN PROGRAM FOLUR · {kabPrefixUpper} {kabName.toUpperCase()}
            </span>

            {/* Headline */}
            <h1 className="font-serif text-4xl md:text-5xl lg:text-[56px] font-extrabold leading-[1.04] -tracking-[0.03em] mb-7 max-w-[16ch]">
              Mengelola bentang lahan{" "}
              <span className="text-folur-800">{fmtInt(luasHa)} hektar</span>
              {" "}untuk {komoditasNama}, dan hutan yang lestari
            </h1>

            {/* Lead */}
            <p className="text-lg leading-relaxed max-w-[56ch] mb-0 text-cap-lead">
              Program FOLUR di {kabPrefix} {kabName} memadukan produktivitas komoditas,
              mata pencaharian {fmtInt(wilayahN)} {wilayahLabel}, dan kelestarian lingkungan melalui pendekatan
              pengelolaan bentang lahan terpadu. Berikut perkembangan capaiannya.
            </p>

            {/* Stats Row */}
            <div className="flex flex-wrap gap-14 py-8 my-10 border-y border-cap-line">
              <div className="flex flex-col gap-1.5">
                <span className="text-4xl font-bold leading-none font-mono tabular-nums">
                  {fmtInt(jmlKec)}
                </span>
                <span className="text-sm text-cap-muted">kecamatan</span>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-4xl font-bold leading-none font-mono tabular-nums">
                  {fmtInt(wilayahN)}
                </span>
                <span className="text-sm text-cap-muted">{wilayahLabel}</span>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-4xl font-bold leading-none font-mono tabular-nums">
                  {persenMaju > 0 ? `${persenMaju}%` : "—"}
                </span>
                <span className="text-sm text-cap-muted">desa Mandiri + Maju</span>
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-4xl font-bold leading-none font-mono tabular-nums">
                  {komoditasCount}
                </span>
                <span className="text-sm text-cap-muted">komoditas fokus</span>
              </div>
            </div>

            {/* Commodity Chips */}
            {komoditas.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 mt-1 mb-0">
                <span className="text-[11px] uppercase tracking-[0.1em] font-mono text-gray-400">Komoditas fokus</span>
                {komoditas.map((k) => (
                  <span key={k} className="inline-block px-3.5 py-1 text-[12.5px] rounded-full border bg-cap-ochre/10 text-cap-cocoa border-cap-ochre/20">
                    {k}
                  </span>
                ))}
              </div>
            )}

            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-[18px] mt-12">
              {displayKpis.map((kpi) => (
                <article key={kpi.kode} className="bg-white border border-cap-line rounded-2xl p-5 lg:p-[22px]">
                  <div className="flex items-center gap-2.5 mb-5 lg:mb-[22px]">
                    <span className="inline-block text-[11px] font-bold tracking-[0.04em] text-white bg-folur-800 px-2 py-1 rounded-md font-mono">
                      {kpi.kode}
                    </span>
                    <span className="text-[12.5px] text-cap-muted">{kpi.pilarNama}</span>
                  </div>
                  <h3 className="font-serif text-[15px] font-semibold leading-[1.3] mb-4 min-h-[2.6em]">{kpi.nama}</h3>
                  <div className="text-[38px] font-bold leading-none flex items-baseline gap-1.5 font-mono tabular-nums">
                    {kpi.nilai != null ? fmtInt(kpi.nilai) : "—"}
                    <small className="text-[13px] font-medium text-cap-muted">{kpi.satuan}</small>
                  </div>
                  <div className="h-[6px] rounded mt-[18px] overflow-hidden bg-cap-green-100">
                    <div className="h-full rounded transition-all duration-700 bg-cap-green-600" style={{ width: `${Math.min(kpi.persen, 100)}%` }} />
                  </div>
                  <p className="text-[12.5px] mt-3 font-mono text-cap-muted">
                    {kpi.persen}% dari target {kpi.target != null ? fmtInt(kpi.target) : "—"}{kpi.agregasi === "kumulatif" ? " · kumulatif" : ""}
                  </p>
                </article>
              ))}
            </div>

            {/* Footer CTAs */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mt-11 pt-7 border-t border-cap-line">
              <p className="text-[15px] leading-relaxed max-w-[46ch] m-0 text-cap-muted">
                Pantau capaian <strong>per desa & per tahun</strong> di peta monitoring spasial, atau jelajahi data terbuka di Pusat Data.
              </p>
              <div className="flex items-center gap-6 whitespace-nowrap shrink-0">
                <a href="/webgis-capaian" className="text-[15px] font-semibold no-underline hover:underline text-cap-green-700">Peta Capaian per Wilayah →</a>
                <a href="/jelajah-dataset" className="text-[15px] font-semibold no-underline hover:underline text-cap-green-700">Jelajahi Pusat Data →</a>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ===== FOOTER (gaya jelajah-endpoint: bar forest) ===== */}
      <footer className="bg-ds-forest text-ds-cream/80">
        <div className="max-w-[1320px] mx-auto px-6 md:px-10 py-7 flex flex-wrap items-center gap-3 text-[13px]">
          <div>© 2026 {site?.siteName || "DST Luwu"} · {kabName}</div>
        </div>
      </footer>
    </div>
  );
}
