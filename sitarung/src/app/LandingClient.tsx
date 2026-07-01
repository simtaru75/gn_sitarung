"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { LandingData, SiteIdentity } from "@/lib/geonode";
import Image from "next/image";
const OfflineBanner = () => (
  <div className="p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm font-medium text-center my-8">
    ⚠️ Koneksi dengan Server Database sedang mengalami gangguan, atau server sedang dalam maintenance.
  </div>
);

const AUTO_ADVANCE_MS = 6000;
const SWIPE_THRESHOLD = 50;
const HERO_SLIDES = 3;

// Judul header bergulir (marquee) — selaras index-tailwind.html.
const MARQUEE_TITLE = "SISTEM INFORMASI TATA RUANG (SITARUNG)";

// Slide hero SITARUNG: latar banner Jembatan Ampera + figur pejabat.
// Aset di-bundle dari situs ADMINSITARUNG di /adm/PUBLIK/assets/images/.
const HERO_MEDIA = "/adm/PUBLIK/assets/images";
const HERO_BANNERS = [
  { bg: `${HERO_MEDIA}/banner1.png`, figure: `${HERO_MEDIA}/pakhdCopy.png` },
  { bg: `${HERO_MEDIA}/banner2.png`, figure: `${HERO_MEDIA}/PSDATEMPLATEARACREATIVE6Copy.png` },
  { bg: `${HERO_MEDIA}/banner3.png`, figure: `${HERO_MEDIA}/kepala.png` },
];
const HERO_OVERLAY =
  "linear-gradient(90deg,rgba(8,55,46,.90),rgba(8,55,46,.50) 48%,rgba(8,55,46,.10))";

// Selaras dengan menu landing GeoNode: Screening · Layanan · Indikator ·
// Dokumen · Katalog · Dataset · Tentang.
const NAV_LINKS = [
  { href: "#screening", label: "Screening" },
  { href: "#layanan", label: "Layanan" },
  { href: "#indikator", label: "Indikator" },
  { href: "#dokumen", label: "Dokumen" },
  { href: "#katalog", label: "Katalog" },
  { href: "#dataset", label: "Dataset" },
  { href: "#tentang-program", label: "Tentang" },
];




function accordionItems(namaKab: string, kabShort: string) {
  return [
  {
    id: "01",
    label: "Latar Belakang",
    title: <>Program <span className="italic font-normal text-gray-600">FOLUR</span></>,
    content: (
      <>
        <p>Program <strong className="text-gray-900">Food Systems, Land Use and Restoration (FOLUR)</strong> adalah inisiatif global yang didukung oleh UNDP dan GEF untuk mendorong perubahan mendasar dalam pengelolaan sistem pangan, penggunaan lahan, dan pemulihan ekosistem. Di Indonesia, program ini berfokus pada pengurangan deforestasi dan degradasi lahan melalui penguatan tata kelola komoditas pertanian utama.</p>
        <p>Empat komoditas strategis yang menjadi fokus utama adalah <strong className="text-gray-900">kakao rakyat</strong>, <strong className="text-gray-900">padi sawah</strong>, <strong className="text-gray-900">kelapa sawit</strong>, dan <strong className="text-gray-900">kopi</strong> — keempatnya memiliki dampak langsung terhadap mata pencaharian petani kecil sekaligus menjadi faktor penentu dalam penggunaan lahan di kabupaten-kabupaten sasaran.</p>
        <p>Program FOLUR diimplementasikan di <strong className="text-gray-900">5 kabupaten prioritas</strong> di Indonesia — Aceh Timur, Mandailing Natal, Sanggau, Luwu, dan Sorong — dalam kerangka Pengelolaan Lanskap Terpadu (ILM).</p>
      </>
    ),
  },
  {
    id: "02",
    label: "Konteks Wilayah",
    title: <>Mengapa Kabupaten <span className="italic font-normal text-gray-600">{kabShort}?</span></>,
    content: (
      <>
        <p>{namaKab} merupakan salah satu wilayah sasaran FOLUR karena peran strategisnya dalam produksi <strong className="text-gray-900">komoditas pertanian rakyat</strong>. Wilayah ini berpotensi menjadi model pengelolaan lanskap yang mempertemukan kepentingan produktivitas pertanian, konservasi kawasan, dan kesejahteraan petani kecil.</p>
        <p>Dengan keragaman ekosistemnya, {namaKab} menghadapi tantangan nyata dalam menyeimbangkan ekspansi pertanian dan perlindungan kawasan bernilai tinggi <strong className="text-gray-900">(HCV/HCS)</strong>. Program FOLUR hadir untuk memperkuat kapasitas daerah menghadapi tantangan tersebut melalui pendekatan berbasis data.</p>
      </>
    ),
  },
  {
    id: "03",
    label: "Platform Data",
    title: <>Peran <span className="italic font-normal text-gray-600">DST ini</span></>,
    content: (
      <>
        <p><strong className="text-gray-900">Decision Support Tool (DST)</strong> {namaKab} adalah platform data resmi yang dikelola oleh BAPPEDA selaku walidata. DST ini berfungsi sebagai jembatan antara data di tingkat kabupaten dengan kebutuhan pemantauan dan evaluasi di tingkat nasional.</p>
        <p>Seluruh dokumen kebijakan, peta tematik, dan dataset spasial yang dipublikasikan melalui portal ini dapat diakses secara terbuka oleh masyarakat, dan secara otomatis dipanen oleh <strong className="text-gray-900">DST Nasional</strong> untuk keperluan pelaporan program kepada UNDP dan pemangku kepentingan nasional.</p>
        <p className="text-sm bg-gray-50 rounded-xl p-4 border border-gray-100">DST Kabupaten berfungsi sebagai <strong className="text-gray-900">penyedia data (data provider)</strong> — bukan alat analisis. Seluruh fungsi pemantauan dan rekomendasi kebijakan berada di DST Nasional.</p>
      </>
    ),
  },
  {
    id: "04",
    label: "Pemangku Kepentingan",
    title: <>Siapa yang <span className="italic font-normal text-gray-600">terlibat?</span></>,
    content: (
      <>
        <p className="text-gray-600 leading-relaxed">Pengelolaan program melibatkan berbagai pihak di tingkat kabupaten maupun nasional, bekerja secara terkoordinasi dalam kerangka implementasi FOLUR.</p>
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <h4 className="text-sm font-bold text-gray-900 mb-3">Tingkat Kabupaten</h4>
            <div className="flex flex-wrap gap-2">
              {["BAPPEDA", "Dinas Pertanian", "Dinas LH", "Dinas PUPR", "Dinas Kehutanan"].map((item) => (
                <span key={item} className="px-3 py-1.5 text-xs rounded-lg bg-folur-100 text-folur-800 font-medium">{item}</span>
              ))}
            </div>
          </div>
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
            <h4 className="text-sm font-bold text-gray-900 mb-3">Tingkat Nasional & Internasional</h4>
            <div className="flex flex-wrap gap-2">
              {["UNDP Indonesia", "Kemenko Pangan", "BAPPENAS", "Kementan", "KLHK", "GEF"].map((item) => (
                <span key={item} className="px-3 py-1.5 text-xs rounded-lg bg-sky-100 text-sky-800 font-medium">{item}</span>
              ))}
            </div>
          </div>
        </div>
      </>
    ),
  },
  ];
}

type FilterGroup = "walidata" | "kategori" | "fitur" | "wilayah";
type FacetOption = { value: string; label: string; count: number };

function MapPlaceholder() {
  return (
    <svg className="w-16 h-16 text-gray-300" fill="none" stroke="currentColor" strokeWidth="1" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>
  );
}

export default function LandingClient({ data, site, publicBase }: { data: LandingData; site: SiteIdentity; publicBase: string }) {
  const asset = useCallback((path: string) => `${publicBase}${path}`, [publicBase]);

  const brandName = site.siteName || "DST Luwu";
  const brandSubtitle = site.namaKabupaten || "Kabupaten Luwu";
  // Nama wilayah dinamis (identitas situs) untuk prose — hindari hardcode.
  const namaKab = brandSubtitle;                                  // mis. "Kabupaten Sanggau"
  const kabShort = brandSubtitle.replace(/^(Kabupaten|Kota)\s+/i, ""); // mis. "Sanggau"
  const ACCORDION_ITEMS = accordionItems(namaKab, kabShort);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [accordionOpen, setAccordionOpen] = useState<string | null>(null);
  const [filters, setFilters] = useState<Record<FilterGroup, string[]>>({
    walidata: [],
    kategori: [],
    fitur: [],
    wilayah: [],
  });

  // Form pencarian "Temukan dataset yang tepat" → buka halaman jelajah sesuai
  // lingkup terpilih, dgn teks dibawa sbg ?q= (prefill pd-search / esb-input).
  const router = useRouter();
  // Buka halaman jelajah dgn teks dibawa sbg ?q= (prefill pd-search / esb-input).
  const goSearch = useCallback(
    (base: string, text: string) => {
      const q = text.trim();
      router.push(q ? `${base}?q=${encodeURIComponent(q)}` : base);
    },
    [router],
  );

  // Pencarian Utama (dgn lingkup "Cari di:").
  const [searchText, setSearchText] = useState("");
  const [searchScope, setSearchScope] =
    useState<"semua" | "dokumen" | "spasial">("semua");
  const runSearch = useCallback(
    () => goSearch(searchScope === "spasial" ? "/jelajah-dataset" : "/jelajah-dokumen", searchText),
    [goSearch, searchScope, searchText],
  );

  // Pencarian di dalam kartu Dokumen Kebijakan & Dataset Spasial.
  const [docQuery, setDocQuery] = useState("");
  const [spasialQuery, setSpasialQuery] = useState("");

  // Hero carousel terkontrol (tombol prev/next + indikator + auto-advance + swipe).
  const [activeSlide, setActiveSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const touchStartX = useRef<number | null>(null);
  const nextSlide = useCallback(() => setActiveSlide((s) => (s + 1) % HERO_SLIDES), []);
  const prevSlide = useCallback(() => setActiveSlide((s) => (s - 1 + HERO_SLIDES) % HERO_SLIDES), []);

  // Auto-advance; berhenti saat di-hover/disentuh; timer di-reset setiap kali
  // slide berubah (termasuk navigasi manual) karena bergantung pada activeSlide.
  useEffect(() => {
    if (isPaused) return;
    const t = setInterval(nextSlide, AUTO_ADVANCE_MS);
    return () => clearInterval(t);
  }, [activeSlide, isPaused, nextSlide]);

  // Swipe mobile: geser horizontal pada area hero untuk pindah slide.
  const onTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    setIsPaused(true);
  }, []);
  const onTouchEnd = useCallback((e: React.TouchEvent) => {
    const start = touchStartX.current;
    setIsPaused(false);
    touchStartX.current = null;
    if (start == null) return;
    const dx = e.changedTouches[0].clientX - start;
    if (Math.abs(dx) > SWIPE_THRESHOLD) (dx < 0 ? nextSlide : prevSlide)();
  }, [nextSlide, prevSlide]);

  const slideClass = (i: number) =>
    `absolute inset-0 flex items-center transition-opacity duration-700 ease-in-out ${
      activeSlide === i ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
    }`;

  const toggleAccordion = useCallback((id: string) => {
    setAccordionOpen((prev) => (prev === id ? null : id));
  }, []);

  const handleFilterChange = useCallback((group: FilterGroup, value: string, checked: boolean) => {
    setFilters((prev) => {
      const current = new Set(prev[group]);
      if (checked) current.add(value);
      else current.delete(value);
      return { ...prev, [group]: Array.from(current) };
    });
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({ walidata: [], kategori: [], fitur: [], wilayah: [] });
  }, []);

  // Facet checkbox + count diturunkan dari dataset NYATA (bukan hardcode).
  const facets = useMemo(() => {
    const mk = () => new Map<string, FacetOption>();
    const inc = (m: Map<string, FacetOption>, value: string, label: string) => {
      const cur = m.get(value);
      if (cur) cur.count += 1;
      else m.set(value, { value, label, count: 1 });
    };
    const kategori = mk(), fitur = mk(), wilayah = mk(), walidata = mk();
    for (const d of data.datasets) {
      if (d.categoryId) inc(kategori, d.categoryId, d.categoryLabel ?? d.categoryId);
      inc(fitur, d.featureLabel.toLowerCase(), d.featureLabel);
      d.regionNames.forEach((n) => inc(wilayah, n.toLowerCase(), n));
      if (d.walidata) inc(walidata, d.walidata.toLowerCase(), d.walidata);
    }
    const toArr = (m: Map<string, FacetOption>) =>
      Array.from(m.values()).sort((a, b) => a.label.localeCompare(b.label));
    return {
      walidata: toArr(walidata),
      kategori: toArr(kategori),
      fitur: toArr(fitur),
      wilayah: toArr(wilayah),
    };
  }, [data.datasets]);

  const visibleDatasets = useMemo(() => {
    return data.datasets.filter((d) => {
      if (filters.kategori.length && !(d.categoryId && filters.kategori.includes(d.categoryId))) return false;
      if (filters.fitur.length && !filters.fitur.includes(d.featureLabel.toLowerCase())) return false;
      if (filters.wilayah.length && !d.regionNames.some((n) => filters.wilayah.includes(n.toLowerCase()))) return false;
      if (filters.walidata.length && !(d.walidata && filters.walidata.includes(d.walidata.toLowerCase()))) return false;
      return true;
    });
  }, [data.datasets, filters]);

  const FILTER_GROUPS: { key: FilterGroup; title: string; options: FacetOption[]; icon: React.ReactNode }[] = [
    {
      key: "walidata", title: "Walidata", options: facets.walidata,
      icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M12 8v4l2 2" /></svg>,
    },
    {
      key: "kategori", title: "Kategori", options: facets.kategori,
      icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>,
    },
    {
      key: "fitur", title: "Fitur", options: facets.fitur,
      icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" /><path d="M12 2v4m0 12v4m-7.07-15.07l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" /></svg>,
    },
    {
      key: "wilayah", title: "Wilayah", options: facets.wilayah,
      icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0l-4.243-4.243a8 8 0 1111.314 0z" /><circle cx="12" cy="11" r="3" /></svg>,
    },
  ];

  // Visibilitas seksi dikelola admin di /dst-auth/frontend/ (LandingSection).
  // Peta: key LandingSection ⇄ id HTML seksi. Seksi yang dimatikan admin
  // (key === false) disembunyikan; key tak ada → tetap tampil.
  const SECTION_ID_BY_KEY: Record<string, string> = {
    hero: "beranda",
    hero_carousel: "beranda-carousel",
    statistik: "statistik",
    pencarian: "pencarian",
    screening_tools: "screening",
    komoditas: "komoditas",
    layanan_data: "layanan",
    indikator_strategis: "indikator",
    dokumen: "dokumen",
    katalog_data: "katalog",
    eksplorasi_dataset: "dataset",
    tentang_program: "tentang-program",
    mitra: "mitra",
  };
  const hiddenSelectors = Object.entries(SECTION_ID_BY_KEY)
    .filter(([key]) => data.sections?.[key] === false)
    .map(([, id]) => `#${id}`);
  // Wadah Repositori ikut sembunyi bila Dokumen & Dataset dua-duanya nonaktif.
  if (data.sections?.dokumen === false && data.sections?.eksplorasi_dataset === false) {
    hiddenSelectors.push("#repositori");
  }
  const hideCss = hiddenSelectors.length ? `${hiddenSelectors.join(",")}{display:none!important}` : "";

  return (
    <div className="bg-white text-gray-800">
      {hideCss && <style dangerouslySetInnerHTML={{ __html: hideCss }} />}
      {/* ============ HEADER SITARUNG: top-strip marquee + menu pill teal ============ */}
      <header className="fixed top-0 inset-x-0 z-50">
        {/* Strip putih: emblem + judul marquee + logo kanan */}
        <div className="relative h-[46px] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.12)]">
          <div className="relative mx-auto h-full max-w-[1280px] px-3">
            <a href="/" className="absolute left-3 top-1 z-[60] block" aria-label={brandName}>
              <img src={site.logo || `${HERO_MEDIA}/favicon.png`} alt={brandName} className="h-[64px] w-[64px] object-contain drop-shadow" />
            </a>
            <div className="hidden lg:block absolute left-[90px] right-[150px] top-0 h-[46px] overflow-hidden">
              <div className="marquee-track flex items-center h-[46px] whitespace-nowrap">
                <span className="site-title shrink-0 pr-24">{MARQUEE_TITLE}</span>
                <span className="site-title shrink-0 pr-24" aria-hidden="true">{MARQUEE_TITLE}</span>
              </div>
            </div>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:block">
              <img src={`${HERO_MEDIA}/lohorights.png`} alt="" className="h-9 object-contain" />
            </div>
          </div>
        </div>
        {/* Bar menu teal translucent */}
        <nav className="backdrop-blur border-b border-brand-500/20" style={{ background: "rgba(154,239,235,0.92)" }}>
          <div className="mx-auto max-w-[1280px] px-4">
            <div className="flex items-center h-[56px]">
              <a href="/" className="lg:hidden flex items-center gap-2 pl-[64px]">
                <span className="font-bold text-brand-800">{brandName}</span>
              </a>
              <ul className="hidden lg:flex items-center gap-2 mx-auto">
                {NAV_LINKS.map((link) => (
                  <li key={link.href}>
                    <a href={link.href} className="menu-pill">{link.label}</a>
                  </li>
                ))}
              </ul>
              <a href="/jelajah-dataset" className="hidden lg:inline-flex items-center rounded-[10px] bg-accent px-3.5 py-[6px] text-[13px] font-semibold text-white shadow-[0_2px_6px_1px_rgba(0,0,0,0.33)] hover:bg-accent-600 transition">Geoportal</a>
              <button onClick={() => setMobileOpen(true)} className="lg:hidden ml-auto p-2 rounded-lg hover:bg-white/50" aria-label="Buka menu">
                <svg className="w-6 h-6 text-brand-800" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
              </button>
            </div>
          </div>
        </nav>
      </header>

      {/* ============ OFFCANVAS (mobile) ============ */}
      <div
        onClick={() => setMobileOpen(false)}
        className={`fixed inset-0 z-[60] bg-black/50 transition-opacity duration-300 ${mobileOpen ? "opacity-100" : "opacity-0 invisible"}`}
      />
      <aside className={`fixed inset-y-0 left-0 z-[70] w-[82%] max-w-xs bg-white shadow-2xl transition-transform duration-300 ease-out ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center justify-between h-[56px] px-5 bg-brand-700 text-white">
          <div className="flex items-center gap-2">
            <img src={site.logo || `${HERO_MEDIA}/favicon.png`} alt="" className="h-8 w-8 object-contain bg-white/90 rounded-full p-0.5" />
            <span className="font-bold">{brandName}</span>
          </div>
          <button onClick={() => setMobileOpen(false)} className="p-2 rounded-lg hover:bg-white/15" aria-label="Tutup menu">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </div>
        <nav className="p-4 space-y-1">
          {NAV_LINKS.map((link) => (
            <a key={link.href} href={link.href} onClick={() => setMobileOpen(false)} className="block px-3 py-2.5 rounded-lg text-gray-600 hover:bg-brand-500/10 hover:text-brand-700">{link.label}</a>
          ))}
          <a href="/jelajah-dataset" onClick={() => setMobileOpen(false)} className="mt-3 block text-center rounded-lg bg-accent px-4 py-2.5 font-semibold text-white">Geoportal</a>
        </nav>
      </aside>

      {/* ============ HERO CAROUSEL SITARUNG (latar banner Jembatan Ampera) ============ */}
      <header
        id="beranda-carousel"
        className="relative h-[92vh] min-h-[600px] overflow-hidden bg-brand-900 text-white select-none"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {HERO_BANNERS.map((b, i) => (
          <div key={i} className={slideClass(i)} style={{ background: `${HERO_OVERLAY}, url('${b.bg}') center/cover` }}>
            <div className="relative z-10 max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-8 items-center w-full">
              <div>
                <span className="inline-block rounded-full bg-white/15 backdrop-blur px-3 py-1 text-xs font-medium tracking-wide mb-5 ring-1 ring-white/20">{brandSubtitle}</span>
                <h1 className="text-6xl md:text-7xl font-bold tracking-tight leading-none drop-shadow-lg">{brandName}</h1>
                <p className="mt-4 text-xl md:text-2xl text-white/95 font-light drop-shadow">Sistem Informasi Tata Ruang<br />{brandSubtitle}</p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <a href="/jelajah-dataset" className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-brand-700 hover:bg-brand-50 transition shadow-lg">Jelajahi Portal</a>
                  <a href="/jelajah-dokumen" className="rounded-lg ring-1 ring-white/50 px-6 py-3 text-sm font-semibold text-white hover:bg-white/10 transition backdrop-blur">Dokumen RTRW</a>
                </div>
              </div>
              <div className="hidden lg:flex justify-center items-end">
                <img src={b.figure} alt="" className="max-h-[420px] object-contain drop-shadow-2xl" />
              </div>
            </div>
          </div>
        ))}

        {/* Kontrol prev/next — di sisi kiri & kanan */}
        <button onClick={prevSlide} aria-label="Slide sebelumnya" className="absolute left-3 md:left-6 top-1/2 -translate-y-1/2 z-20 grid place-items-center w-11 h-11 md:w-12 md:h-12 rounded-full bg-white/15 hover:bg-white/30 text-white backdrop-blur ring-1 ring-white/30 shadow-lg hover:scale-110 active:scale-95 transition-all duration-200">
          <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <button onClick={nextSlide} aria-label="Slide berikutnya" className="absolute right-3 md:right-6 top-1/2 -translate-y-1/2 z-20 grid place-items-center w-11 h-11 md:w-12 md:h-12 rounded-full bg-white/15 hover:bg-white/30 text-white backdrop-blur ring-1 ring-white/30 shadow-lg hover:scale-110 active:scale-95 transition-all duration-200">
          <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
        </button>

        {/* Indikator dot */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex gap-2">
          {HERO_BANNERS.map((_, i) => (
            <button key={i} onClick={() => setActiveSlide(i)} aria-label={`Slide ${i + 1}`} className={`h-2.5 rounded-full transition-all ${activeSlide === i ? "w-6 bg-white" : "w-2.5 bg-white/50 hover:bg-white/80"}`} />
          ))}
        </div>
      </header>




      {/* ============ STAT STRIP ============ */}
      <section id="statistik" className="relative -mt-20 z-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { value: String(data.documentsTotal), label: "Dokumen Kebijakan", sub: "Perda, Perbup, RPJMD, Renstra", color: "text-folur-700" },
              { value: String(data.datasetsTotal), label: "Layer Spasial", sub: "Vektor & raster · ter-publish", color: "text-sky-600" },
              { value: String(data.screeningTotal), label: "Screening Tools", sub: "Realtime AoI · Audit Log", color: "text-earth-600" },
              { value: String(data.komoditas.length), label: "Komoditi Unggulan", sub: "Fokus komoditi daerah/FOLUR", color: "text-folur-600" },
            ].map((stat, i) => (
              <div key={i} className="stat-card bg-white rounded-2xl shadow-lg p-6 text-center">
                <p className={`text-3xl font-extrabold ${stat.color}`}>{stat.value}</p>
                <p className="text-sm font-semibold text-gray-700 mt-1">{stat.label}</p>
                <p className="text-xs text-gray-400 mt-1">{stat.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ PENCARIAN ============ */}
      <section id="pencarian" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-start mb-16">
            <div>
              <p className="text-xs font-bold text-folur-600 tracking-widest uppercase mb-4 flex items-center gap-2">
                <span className="w-8 h-px bg-folur-500" /> Pencarian Data · Repositori Daerah
              </p>
              <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 leading-tight">
                Temukan dataset <br /> yang <span className="italic font-light text-folur-600">tepat</span>
              </h2>
            </div>
            <div className="lg:pt-8">
              <p className="text-gray-500 text-lg leading-relaxed">
                Telusuri seluruh repositori {brandName} — mulai dari <strong className="text-gray-800">dokumen kebijakan</strong>, <strong className="text-gray-800">layer spasial</strong>, hingga <strong className="text-gray-800">metadata</strong> — dalam satu antarmuka pencarian.
              </p>
            </div>
          </div>

          {/* Kotak Pencarian Utama */}
          <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm mb-16">
            <p className="text-[10px] font-bold uppercase tracking-widest text-folur-600 mb-3 flex items-center gap-2">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              Pencarian Utama
            </p>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <input type="text" value={searchText} onChange={(e) => setSearchText(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") runSearch(); }} placeholder="Ketik nama dokumen, layer, atau topik — mis. 'RTRW', 'kakao', 'LP2B', 'HCV'..." className="w-full bg-gray-50 border border-gray-200 rounded-xl px-6 py-4 text-sm text-gray-800 outline-none focus:border-folur-500 focus:ring-1 focus:ring-folur-500 transition-colors placeholder:text-gray-400" />
              </div>
              <button type="button" onClick={runSearch} className="px-8 py-4 bg-folur-700 hover:bg-folur-800 text-white font-bold text-sm rounded-xl transition flex items-center justify-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                Cari Data
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-4 mt-6">
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Cari di:</span>
              <div className="flex flex-wrap gap-2">
                {([
                  ["semua", "Semua"],
                  ["dokumen", "Dokumen"],
                  ["spasial", "Layer Spasial"],
                ] as const).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setSearchScope(key)}
                    className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded transition ${
                      searchScope === key
                        ? "bg-folur-700 text-white hover:bg-folur-800"
                        : "bg-white text-gray-600 border border-gray-300 hover:bg-gray-100"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Dokumen Kebijakan */}
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-8 flex flex-col transition-all hover:shadow-md hover:border-folur-200">
              <div className="w-10 h-10 rounded-lg bg-folur-50 flex items-center justify-center mb-6">
                <svg className="w-5 h-5 text-folur-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              </div>
              <h3 className="font-serif text-xl font-bold text-gray-900 mb-3">Dokumen <span className="italic font-light text-folur-600">Kebijakan</span></h3>
              <p className="text-sm text-gray-500 mb-6 leading-relaxed">Perda, Perbup, RPJMD, Renstra, SK Bupati, dan dokumen regulasi lain yang mengatur tata kelola lahan dan komoditas di {namaKab}.</p>
              <div className="flex flex-wrap gap-2 mb-6">
                {["RTRW", "Perda", "SK Bupati", "RPJMD", "Renstra"].map((t) => (
                  <span key={t} className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider rounded bg-gray-100 text-gray-600">{t}</span>
                ))}
              </div>
              <div className="relative mb-8">
                <input type="text" value={docQuery} onChange={(e) => setDocQuery(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") goSearch("/jelajah-dokumen", docQuery); }} placeholder="JUDUL ATAU NOMOR DOKUMEN..." className="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-xs text-gray-800 uppercase tracking-wider outline-none focus:border-folur-500 focus:ring-1 focus:ring-folur-500 transition-colors placeholder:text-gray-400" />
                <button type="button" onClick={() => goSearch("/jelajah-dokumen", docQuery)} className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-folur-100 hover:bg-folur-200 rounded-md flex items-center justify-center transition-colors">
                  <svg className="w-4 h-4 text-folur-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </button>
              </div>
              <div className="mt-auto flex items-center justify-between pt-6 border-t border-gray-100">
                <span className="text-xs font-bold uppercase tracking-widest text-folur-700">{data.documentsTotal} dokumen aktif</span>
                <a href={"/jelajah-dokumen"} className="text-xs font-bold uppercase tracking-widest text-folur-600 hover:text-folur-800 transition">Lihat Semua →</a>
              </div>
            </div>

            {/* Dataset Spasial */}
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-8 flex flex-col transition-all hover:shadow-md hover:border-folur-200">
              <div className="w-10 h-10 rounded-lg bg-folur-50 flex items-center justify-center mb-6">
                <svg className="w-5 h-5 text-folur-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>
              </div>
              <h3 className="font-serif text-xl font-bold text-gray-900 mb-3">Dataset <span className="italic font-light text-folur-600">Spasial</span></h3>
              <p className="text-sm text-gray-500 mb-6 leading-relaxed">Layer vektor dan raster yang mencakup pola ruang, komoditas, kawasan konservasi, DAS, infrastruktur, dan batas administrasi {namaKab}.</p>
              <div className="flex flex-wrap gap-2 mb-6">
                {["Pola Ruang", "Kakao", "LP2B", "HCV/HCS", "DAS"].map((t) => (
                  <span key={t} className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider rounded bg-gray-100 text-gray-600">{t}</span>
                ))}
              </div>
              <div className="relative mb-8">
                <input type="text" value={spasialQuery} onChange={(e) => setSpasialQuery(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") goSearch("/jelajah-dataset", spasialQuery); }} placeholder="NAMA LAYER ATAU TOPIK..." className="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-xs text-gray-800 uppercase tracking-wider outline-none focus:border-folur-500 focus:ring-1 focus:ring-folur-500 transition-colors placeholder:text-gray-400" />
                <button type="button" onClick={() => goSearch("/jelajah-dataset", spasialQuery)} className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-folur-100 hover:bg-folur-200 rounded-md flex items-center justify-center transition-colors">
                  <svg className="w-4 h-4 text-folur-700" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </button>
              </div>
              <div className="mt-auto flex items-center justify-between pt-6 border-t border-gray-100">
                <span className="text-xs font-bold uppercase tracking-widest text-folur-700">{data.datasetsTotal} layer aktif</span>
                <a href={"/jelajah-dataset"} className="text-xs font-bold uppercase tracking-widest text-folur-600 hover:text-folur-800 transition">Lihat Semua →</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ SCREENING TOOLS ============ */}
      <section id="screening" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-[1fr_1.6fr] gap-12 items-center">
            <div>
              <p className="text-sm font-semibold text-sky-600 tracking-widest uppercase mb-2">Modul Screening Tools</p>
              <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4"><span className="italic font-light text-folur-600">Decision Support Tool</span><br className="hidden md:block" /> untuk Sinkronisasi Intervensi Zonasi Spasial</h2>
              <p className="text-gray-500 mb-8"><strong>Analisis {kabShort}</strong> — Modul screening tools untuk memenuhi kebutuhan publik yang mengoverlay data AoI/PoI dengan layer-layer peta dasar, peta tematik dan peta rencana di dalam modul pemetaan interaktif dengan output laporan PDF.</p>
              <div className="flex flex-wrap gap-3">
                <a href="/webgis-screening" className="inline-flex items-center px-6 py-3 bg-folur-700 text-white font-semibold rounded-lg hover:bg-folur-800 transition">Screening Tools</a>
                <a href="/capaian-folur" className="inline-flex items-center px-6 py-3 border-2 border-folur-700 text-folur-700 font-semibold rounded-lg hover:bg-folur-50 transition">Capaian Program</a>
              </div>
            </div>
            <div className="rounded-2xl overflow-hidden shadow-xl border border-gray-200 bg-gray-50">
              <img src="/images/zonasi-folur.png" alt="Peta Zonasi FOLUR" className="w-full h-auto" />
            </div>
          </div>
        </div>
      </section>

      {/* ============ KOMODITAS ============ */}
      <section id="komoditas" className="py-24 bg-folur-50">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">FOLUR · Komoditas</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Komoditas <span className="italic font-light text-folur-600">Fokus</span></h2>
          <p className="text-gray-500 max-w-3xl mb-12">Komoditas strategis yang menjadi prioritas program FOLUR di {namaKab} — dikelola secara berkelanjutan untuk mendorong produktivitas pertanian sekaligus menjaga kawasan bernilai tinggi (HCV/HCS).</p>
          <div className="grid md:grid-cols-2 gap-6">
            {data.isOffline ? (
              <div className="col-span-full">
                <OfflineBanner />
              </div>
            ) : data.komoditas.length === 0 ? (
              <p className="text-gray-500 italic">Data komoditas belum tersedia.</p>
            ) : (
              data.komoditas.map((k, i) => (
                <div key={k.id} className="bg-white rounded-2xl shadow-sm overflow-hidden hover:shadow-lg transition group">
                  <div className="h-48 bg-folur-100 flex items-center justify-center p-6 overflow-hidden relative">
                    {k.gambar && (
                      <Image src={k.gambar} alt={k.nama} fill className="p-6 object-contain group-hover:scale-105 transition duration-500" onError={(e) => { e.currentTarget.style.visibility = "hidden"; }} />
                    )}
                  </div>
                  <div className="p-6">
                    <p className="text-xs font-semibold text-folur-600 uppercase tracking-wider mb-2">Komoditas Fokus · {String(i + 1).padStart(2, "0")}</p>
                    <h3 className="font-serif text-lg font-bold text-gray-900 mb-2">{k.nama}</h3>
                    <p className="text-sm text-gray-500">{k.deskripsi}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* ============ LAYANAN DATA (dinamis dari kategori) ============ */}
      <section id="layanan" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">Layanan · {namaKab}</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Layanan <span className="italic font-light text-folur-600">Data</span></h2>
          <p className="text-gray-500 max-w-2xl mb-12">Kategori data dan layanan yang tersedia di {kabShort}. Pilih kategori untuk melihat detailnya.</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-5">
            {data.categories.map((cat) => (
              <a key={cat.identifier}                 href={`/jelajah-dokumen?kategori=${cat.identifier}`} className="layanan-card bg-gray-50 rounded-2xl p-5 flex flex-col items-center text-center border border-gray-100 hover:border-folur-200">
                <span className="w-16 h-16 mb-3 rounded-2xl bg-folur-100 text-folur-700 flex items-center justify-center text-2xl">
                  <i className={`fa ${cat.faClass}`} aria-hidden="true" />
                </span>
                <span className="text-sm font-semibold text-gray-800">{cat.label}</span>
                {cat.count > 0 && <span className="mt-1 text-xs text-gray-400">{cat.count} data</span>}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ============ INDIKATOR STRATEGIS ============ */}
      <section id="indikator" className="py-24 bg-gradient-to-b from-folur-900 to-folur-800 text-white">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-sm font-semibold text-folur-200 tracking-widest uppercase mb-2">Data Makro · {namaKab}</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold mb-4">Indikator Strategis</h2>
          <p className="text-folur-200/70 max-w-2xl mb-12">Capaian indikator pembangunan {namaKab} sebagai acuan perencanaan dan kebijakan berbasis data.</p>
          {data.isOffline ? (
            <OfflineBanner />
          ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {data.isOffline ? (
              <div className="col-span-full">
                <OfflineBanner />
              </div>
            ) : data.indikator.length === 0 ? (
              <p className="text-folur-100/70 italic">Indikator belum tersedia.</p>
            ) : (
              data.indikator.map((ind) => (
                <div key={ind.id} className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/10 text-center flex flex-col items-center">
                  {ind.ikon && (
                    <img src={ind.ikon} alt="" className="w-14 h-14 mb-4 object-contain" loading="lazy" onError={(e) => { e.currentTarget.style.visibility = "hidden"; }} />
                  )}
                  <p className="text-3xl font-extrabold">{ind.nilai}</p>
                  <p className="text-sm font-semibold text-folur-100 mt-1">{ind.judul}</p>
                  <p className="text-xs text-folur-200/60 mt-1">{ind.deskripsi}</p>
                </div>
              ))
            )}
          </div>
          )}
        </div>
      </section>

      {/* ============ REPOSITORI DOKUMEN ============ */}
      <section id="repositori" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">

          {/* Dokumen Kebijakan (dinamis) */}
          <div id="dokumen" className="mb-20 scroll-mt-20">
            <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">Repositori · 01</p>
            <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Dokumen <span className="italic font-light text-folur-600">Kebijakan</span></h2>
            <p className="text-gray-500 max-w-3xl mb-10">Regulasi daerah, rencana strategis, dan dokumen perencanaan {namaKab}. Semua dokumen ter-katalog dengan metadata yang diharvest oleh DST Nasional via REST API.</p>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-wider">
                <div className="col-span-1">Tahun</div>
                <div className="col-span-2">Tipe</div>
                <div className="col-span-7">Judul Dokumen</div>
                <div className="col-span-2 text-right">Aksi</div>
              </div>
              {data.isOffline ? (
                <OfflineBanner />
              ) : data.documents.length === 0 ? (
                <div className="px-6 py-8 text-sm text-gray-400 text-center">Belum ada dokumen ter-publish.</div>
              ) : (
                data.documents.slice(0, 8).map((doc, i) => (
                  <a key={doc.pk} href={`/dataset-dokumen/${doc.pk}`} className="dok-row grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4 py-4 border-b border-gray-50 group items-center" style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className="col-span-1"><span className="text-xs font-bold text-folur-700 bg-folur-100 px-2 py-1 rounded">{doc.year ?? "—"}</span></div>
                    <div className="col-span-2"><span className="text-xs text-gray-400">{doc.typeLabel}</span></div>
                    <div className="col-span-7"><p className="text-sm font-semibold text-gray-800 group-hover:text-folur-700 transition">{doc.title}</p></div>
                    <div className="col-span-2 text-right"><span className="text-sm font-semibold text-folur-600 group-hover:text-folur-800 transition">Lihat →</span></div>
                  </a>
                ))
              )}
            </div>
            <div className="mt-6 text-center">
              <a href={"/jelajah-dokumen"} className="underline-hover inline-flex items-center text-sm font-semibold text-folur-700 hover:text-folur-900">Lihat seluruh {data.documentsTotal} dokumen →</a>
            </div>
          </div>

          {/* Katalog Dataset Spasial (dinamis) */}
          <div id="katalog" className="mb-20 scroll-mt-20">
            <p className="text-sm font-semibold text-sky-600 tracking-widest uppercase mb-2">Repositori · 02</p>
            <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Katalog <span className="italic font-light text-folur-600">Dataset Spasial</span></h2>
            <p className="text-gray-500 max-w-3xl mb-10">Layer vektor dan raster yang mencakup penggunaan lahan, area konservasi, zona produksi, restorasi, dan tata ruang. Tersedia sebagai layanan WMS/WFS dan unduhan GeoPackage/GeoTIFF.</p>
            <div className="grid md:grid-cols-3 gap-6">
              {data.isOffline ? (
                <div className="col-span-full">
                  <OfflineBanner />
                </div>
              ) : data.datasets.length === 0 ? (
                <p className="text-gray-500 italic">Belum ada dataset ter-publish.</p>
              ) : (
                data.datasets.slice(0, 3).map((ds) => (
                  <a key={ds.pk} href={`/dataset-spasial/${ds.pk}`} className="block bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-lg transition group">
                    <div className="h-40 bg-gray-200 flex items-center justify-center overflow-hidden relative">
                      {ds.thumbnail ? (
                        <img src={ds.thumbnail} alt={ds.title} className="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />
                      ) : (
                        <MapPlaceholder />
                      )}
                    </div>
                    <div className="p-5">
                      <span className="text-xs font-semibold text-sky-600">{ds.featureLabel}</span>
                      <p className="text-base font-bold text-gray-900 mt-1 group-hover:text-sky-700">{ds.title}</p>
                      <p className="text-xs text-gray-400 mt-2 line-clamp-2">{ds.abstract || "Belum ada abstrak metadata untuk layer ini."}</p>
                      <div className="flex gap-2 mt-3 flex-wrap">
                        {ds.epsg && <span className="px-2 py-0.5 text-xs rounded bg-sky-50 text-sky-700">{ds.epsg}</span>}
                        <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600">WMS · WFS</span>
                      </div>
                    </div>
                  </a>
                ))
              )}
            </div>
            <div className="mt-6 text-center">
              <a href={"/jelajah-dataset"} className="underline-hover inline-flex items-center text-sm font-semibold text-sky-700 hover:text-sky-900">Lihat seluruh {data.datasetsTotal} layer spasial →</a>
            </div>
          </div>

          {/* Eksplorasi Dataset (filter berfungsi) */}
          <div id="dataset" className="scroll-mt-20">
            <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">Repositori · 03</p>
            <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Eksplorasi <span className="italic font-light text-folur-600">Dataset Spasial</span></h2>
            <p className="text-gray-500 max-w-3xl mb-10">Telusuri seluruh dataset spasial {namaKab} yang ter-publish. Filter berdasarkan walidata, kategori, jenis fitur, dan wilayah untuk menemukan data yang relevan.</p>

            <div className="grid lg:grid-cols-12 gap-6">
              {/* Sidebar Filter (dinamis) */}
              <div className="lg:col-span-3 space-y-4">
                {FILTER_GROUPS.map((group) => (
                  <div key={group.key} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                    <div className="bg-folur-700 text-white px-4 py-2.5 flex items-center gap-2">
                      {group.icon}
                      <span className="text-xs font-bold uppercase tracking-wider">{group.title}</span>
                    </div>
                    <div className="p-4 space-y-2.5 text-sm text-gray-700">
                      {group.options.length === 0 ? (
                        <p className="text-xs text-gray-400 italic">Belum ada data</p>
                      ) : (
                        group.options.map((opt) => (
                          <label key={opt.value} className="flex items-center justify-between cursor-pointer hover:text-folur-700">
                            <span className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                className="accent-folur-600 w-3.5 h-3.5"
                                checked={filters[group.key].includes(opt.value)}
                                onChange={(e) => handleFilterChange(group.key, opt.value, e.target.checked)}
                              />
                              {opt.label}
                            </span>
                            <span className="text-xs text-gray-400">{opt.count}</span>
                          </label>
                        ))
                      )}
                    </div>
                  </div>
                ))}
                <button onClick={resetFilters} className="w-full py-2.5 text-xs font-bold uppercase tracking-wider text-folur-500 border border-folur-200 rounded-xl hover:bg-folur-50 hover:text-folur-600 transition">Reset Filter</button>
              </div>

              {/* Dataset Grid (terfilter) */}
              <div className="lg:col-span-9">
                <div className="flex items-center justify-between mb-6">
                  <p className="text-xs font-bold uppercase tracking-wider text-gray-500">Menampilkan <span className="text-folur-600">{visibleDatasets.length}</span> dari <span className="text-folur-600">{data.datasets.length}</span> dataset</p>
                </div>
                {visibleDatasets.length === 0 ? (
                  <div className="bg-white rounded-xl border border-gray-100 p-12 text-center text-sm text-gray-400">Tidak ada dataset yang cocok dengan filter.</div>
                ) : (
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                    {visibleDatasets.map((ds) => (
                      <a key={ds.pk} href={`/dataset-spasial/${ds.pk}`} className="dataset-card block bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-lg transition group">
                        <div className="h-36 bg-gray-200 relative flex items-center justify-center overflow-hidden">
                          {ds.thumbnail ? (
                            <img src={ds.thumbnail} alt={ds.title} className="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />
                          ) : (
                            <MapPlaceholder />
                          )}
                          <span className="absolute top-2 left-2 px-2.5 py-1 text-xs font-bold uppercase tracking-wider rounded bg-folur-700 text-white">{ds.featureLabel}</span>
                        </div>
                        <div className="p-4">
                          <h4 className="font-bold text-gray-900 group-hover:text-folur-700 transition mb-3">{ds.title}</h4>
                          <div className="text-xs text-gray-500 space-y-1.5">
                            <p className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-folur-200" /><strong className="text-gray-600">Walidata:</strong> {ds.walidata ?? "—"}</p>
                            <p className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-folur-200" /><strong className="text-gray-600">Kategori:</strong> {ds.categoryLabel ?? "—"}</p>
                            <p className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-folur-200" /><strong className="text-gray-600">Fitur:</strong> {ds.featureLabel}</p>
                            <p className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-folur-200" /><strong className="text-gray-600">Wilayah:</strong> {ds.regionNames.join(", ") || "—"}</p>
                          </div>
                          <div className="mt-4 text-right"><span className="text-sm font-semibold text-folur-600 group-hover:text-folur-800">Detail →</span></div>
                        </div>
          </a>
                    ))}
                  </div>
                )}
            <div className="mt-6 text-center">
                  <a href={"/jelajah-dataset"} className="underline-hover inline-flex items-center text-sm font-semibold text-folur-700 hover:text-folur-900">Jelajahi semua dataset →</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ TENTANG PROGRAM ============ */}
      <section id="tentang-program" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">DST FOLUR · Tentang</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Tentang <span className="italic font-light text-folur-600">Program</span></h2>
          <p className="text-gray-500 max-w-3xl mb-16">Program FOLUR adalah inisiatif global yang didukung UNDP dan GEF untuk mendorong perubahan mendasar dalam pengelolaan sistem pangan, penggunaan lahan, dan pemulihan ekosistem di Indonesia.</p>
          <div className="border border-gray-200 rounded-xl overflow-hidden">
            {ACCORDION_ITEMS.map((item) => (
              <div key={item.id} className="border-b border-gray-200 last:border-b-0">
                <button onClick={() => toggleAccordion(item.id)} className="accordion-btn w-full flex items-center justify-between p-6 text-left transition-colors hover:bg-gray-50 group">
                  <div className="flex items-center gap-6">
                    <span className="text-2xl font-extrabold text-gray-300 w-8">{item.id}</span>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 leading-none mb-1">{item.label}</p>
                    <h3 className="font-serif text-2xl font-bold text-gray-900">{item.title}</h3>
                    </div>
                  </div>
                  <div className="bg-gray-100 p-1 rounded group-hover:bg-gray-200 transition-colors">
                    <svg className={`w-4 h-4 text-gray-500 transition-transform duration-300 ${accordionOpen === item.id ? "rotate-180" : ""}`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                  </div>
                </button>
                <div className={`overflow-hidden transition-all duration-500 ease-in-out ${accordionOpen === item.id ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"}`}>
                  <div className="p-6 pt-0 space-y-4 text-gray-600 leading-relaxed">{item.content}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ IMPLEMENTING PARTNERS ============ */}
      <section id="mitra" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">FOLUR · Mitra Pelaksana</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Implementing <span className="italic font-light text-folur-600">Partners</span></h2>
          <p className="text-gray-500 max-w-2xl mb-12">Kolaborasi lintas lembaga yang mendukung tata kelola bentang lahan terpadu di {namaKab}.</p>
          {data.isOffline ? (
            <OfflineBanner />
          ) : data.partners.length === 0 ? (
            <p className="text-gray-500 italic text-center">Data mitra belum tersedia.</p>
          ) : (
            <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
              {data.partners.map((p) => (
                <a
                  key={p.id}
                  href={p.tautan || undefined}
                  title={p.nama}
                  target={p.tautan ? "_blank" : undefined}
                  rel={p.tautan ? "noopener noreferrer" : undefined}
                  className="grayscale hover:grayscale-0 opacity-70 hover:opacity-100 transition"
                >
                  <img src={p.logo} alt={p.nama} className="h-16 md:h-20 object-contain" loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />
                </a>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="bg-folur-900 text-white py-16 font-sans">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-12 mb-12">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="bg-white rounded-lg p-1 inline-flex">
                  <img src={site.logo || asset("/icon.png")} alt={brandName} className="h-10 w-10 object-contain" />
                </span>
                <div>
                  <p className="text-lg font-bold">{brandName}</p>
                  <p className="text-xs text-folur-200">{brandSubtitle}</p>
                </div>
              </div>
              <p className="text-sm text-folur-200/70 max-w-xs">Decision Support Tool untuk tata kelola bentang lahan berkelanjutan di {namaKab}.</p>
            </div>
            <div>
              <h4 className="text-sm font-bold mb-4">Navigasi</h4>
              <ul className="space-y-2 text-sm text-folur-200/70">
                <li><a href={"/jelajah-dokumen"} className="hover:text-white">Jelajahi Dokumen</a></li>
                <li><a href={"/jelajah-dataset"} className="hover:text-white">Eksplorasi Dataset</a></li>
                <li><a href={"/webgis-screening/"} className="hover:text-white">Screening Tools</a></li>
                <li><a href={"/jelajah-endpoint"} className="hover:text-white">API & Endpoint</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-bold mb-4">Kerangka Hukum</h4>
              <ul className="space-y-2 text-sm text-folur-200/70">
                <li>Satu Data Indonesia (SDI)</li>
                <li>Kebijakan Satu Peta (KSP)</li>
                <li>SNI ISO 19115</li>
                <li>Lisensi CC BY 4.0</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-folur-200/50">&copy; 2026 {brandName} &middot; {brandSubtitle}</p>
            <p className="text-xs text-folur-200/50">Didukung oleh UNDP · GEF · Program FOLUR Indonesia</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
