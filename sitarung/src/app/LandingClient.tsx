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

const RTRW_CONTENT = [
  {
    id: "01",
    href: "/rtrw/tujuan",
    image: `${HERO_MEDIA}/fpr.png`,
    title: "Tujuan, Kebijakan & Strategi",
    description: "Susunan pusat permukiman dan sistem jaringan prasarana wilayah pendukung kegiatan sosial ekonomi masyarakat.",
  },
  {
    id: "02",
    href: "/rtrw/struktur",
    image: `${HERO_MEDIA}/Flatdesignlineartaf.png`,
    title: "Rencana Struktur Ruang",
    description: "Hierarki perkotaan serta konektivitas infrastruktur transportasi, energi, telekomunikasi, dan utilitas.",
  },
  {
    id: "03",
    href: "/rtrw/pola",
    image: `${HERO_MEDIA}/Flatdesignlineart3af.png`,
    title: "Rencana Pola Ruang",
    description: "Distribusi peruntukan ruang mencakup penetapan kawasan lindung dan kawasan budidaya.",
  },
  {
    id: "04",
    href: "/rtrw/strategis",
    image: `${HERO_MEDIA}/Flatdesignlineart4af.png`,
    title: "Rencana Kawasan Strategis",
    description: "Wilayah prioritas dengan pengaruh penting terhadap ekonomi, sosial budaya, atau lingkungan hidup.",
  },
  {
    id: "05",
    href: "/rtrw/pemanfaatan",
    image: `${HERO_MEDIA}/teodolit.png`,
    title: "Arahan Pemanfaatan Ruang",
    description: "Ketentuan Kesesuaian Kegiatan Pemanfaatan Ruang (KKPR) dan indikasi program utama pembangunan.",
  },
  {
    id: "06",
    href: "/rtrw/pengendalian",
    image: `${HERO_MEDIA}/kendali.png`,
    title: "Arahan Pengendalian",
    description: "Memastikan pemanfaatan ruang berlangsung tertib dan sesuai dengan rencana tata ruang yang ditetapkan.",
  },
];

const PENATAAN_RUANG_ITEMS = [
  {
    image: `${HERO_MEDIA}/z1.PERENCANAANTATARUANG.png`,
    title: "Perencanaan Tata Ruang",
    description: "Menghasilkan Rencana Umum Tata Ruang dan Rencana Rinci Tata Ruang.",
  },
  {
    image: `${HERO_MEDIA}/z2.PEMANFAATANRUANG.png`,
    title: "Pemanfaatan Ruang",
    description: "Pelaksanaan KKPR dan sinkronisasi program pemanfaatan ruang.",
  },
  {
    image: `${HERO_MEDIA}/z3.PENGENDALIANPEMANFAATANRUANG.png`,
    title: "Pengendalian Pemanfaatan Ruang",
    description: "Mendorong terwujudnya tata ruang sesuai dengan RTR.",
  },
  {
    image: `${HERO_MEDIA}/z4.PENGAWASANPENATAANRUANG.png`,
    title: "Pengawasan Penataan Ruang",
    description: "Kegiatan monev untuk menjamin tercapainya tujuan penyelenggaraan penataan ruang.",
  },
  {
    image: `${HERO_MEDIA}/z5.PEMBINAANPENATAANRUANG.png`,
    title: "Pembinaan Penataan Ruang",
    description: "Meningkatkan kualitas, efektifitas, dan peran masyarakat dalam penyelenggaraan penataan ruang.",
  },
  {
    image: `${HERO_MEDIA}/z6.KELEMBAGAANPENATAANRUANG.png`,
    title: "Kelembagaan Penataan Ruang",
    description: "Penyelenggaraan penataan ruang partisipatif dengan membentuk Forum Penataan Ruang.",
  },
];

const PORTAL_MODULES = [
  {
    badge: "Spasial",
    number: "01",
    type: "spatial",
    title: "Peta Spasial",
    description: "Basis data spasial: informasi geografi, batas wilayah, penggunaan lahan, dan elemen tata ruang digital.",
    image: `${HERO_MEDIA}/editilustrasiparti3.png`,
    href: "/jelajah-dataset",
  },
  {
    badge: "Dokumen",
    number: "02",
    type: "document",
    title: "Dokumen Teknis",
    description: "Dokumen resmi, kebijakan, pedoman perencanaan, serta laporan kegiatan yang relevan dengan tata ruang.",
    image: `${HERO_MEDIA}/editilustrasiparti4.png`,
    href: "/jelajah-dokumen",
  },
  {
    badge: "Dataset",
    number: "03",
    type: "dataset",
    title: "Dataset RTR",
    description: "Data kajian, hasil analisis, dan indikator kunci pendukung penyusunan dan pemantauan Rencana Tata Ruang.",
    image: `${HERO_MEDIA}/editilustrasiparti2.png`,
    href: "/jelajah-endpoint",
  },
];

const NEWS_FEATURED = {
  image: `${HERO_MEDIA}/IMG20250819WA00561536x1152.jpg`,
  date: "19 Agustus 2025 · Dinas PUBMTR Sumsel",
  title: "Sosialisasi Perda No. 6 Tahun 2024 tentang RTRW 2024-2044",
  description:
    "Pemerintah Provinsi Sumatera Selatan menyelenggarakan Rapat Koordinasi Forum Penataan Ruang (FPR) dalam rangka sosialisasi Perda RTRW Provinsi Sumatera Selatan Tahun 2024-2044 di Ballroom Hotel The Zuri Palembang.",
};

const NEWS_LIST = [
  {
    image: `${HERO_MEDIA}/Gemini_Generated_Image_qavq05qavq05qavq.png`,
    date: "19 Agustus 2025",
    title: "Tiga Program Strategis dalam RTRW Sumsel 2024-2044 Dorong Pembangunan Berkelanjutan",
    description: "Meningkatkan konektivitas, mendorong pertumbuhan ekonomi, sekaligus menjaga kelestarian lingkungan.",
  },
  {
    image: `${HERO_MEDIA}/kabh250px1607.jpg`,
    date: "Perkembangan RTR Kab/Kota",
    title: "RTR Kabupaten Banyuasin pada Tahap Proses Pengesahan Perda",
    description: "Perkembangan penyusunan rencana tata ruang kabupaten/kota di wilayah Sumatera Selatan.",
  },
];

const VIDEO_GALLERY = [
  {
    href: "https://www.youtube.com/watch?v=Xraf9kZlY3M",
    image: `${HERO_MEDIA}/video.png`,
    title: "Podcast One Day One Innovation tentang SITARUNG dengan narasumber Faustino Do Carmo, ST., M.Si.",
  },
  {
    href: "https://www.youtube.com/watch?v=vu32XVPob-Q",
    image: `${HERO_MEDIA}/part2.png`,
    title: "Penguatan Peran Kelembagaan Penataan Ruang Daerah dalam Pembangunan Daerah - Kemendagri Ditjen Bina Bangda.",
  },
  {
    href: "https://www.youtube.com/watch?v=YM7XXF_vm6Q",
    image: `${HERO_MEDIA}/part3.png`,
    title: "Peran Pemerintah Daerah dalam Pengendalian Pemanfaatan Ruang - Kementerian ATR/BPN.",
  },
  {
    href: "https://www.youtube.com/watch?v=7gj1dM8sSP8",
    image: `${HERO_MEDIA}/part4.png`,
    title: "Peran Pemda dalam Pengendalian Penataan Ruang melalui Instrumen Penataan Ruang - ATR/BPN.",
  },
];

const DOWNLOAD_ITEMS = [
  {
    image: `${HERO_MEDIA}/DOK1.png`,
    label: "PERDA",
    description: "Peraturan Daerah tentang RTRW Provinsi Sumsel",
  },
  {
    image: `${HERO_MEDIA}/DOK2.png`,
    label: "BUKU",
    description: "Dokumen Teknis RTRW Provinsi Sumatera Selatan",
  },
  {
    image: `${HERO_MEDIA}/DOK3.png`,
    label: "PETA",
    description: "Album Peta RTRW Provinsi Sumatera Selatan",
  },
  {
    image: `${HERO_MEDIA}/DOK4.png`,
    label: "KLHS",
    description: "Kajian Lingkungan Hidup Strategis Prov. Sumsel",
  },
];

const KKPR_APPS = [
  { image: `${HERO_MEDIA}/logosumsel.png`, label: "KKPR Sumatera Selatan" },
  { image: `${HERO_MEDIA}/logosumsel.png`, label: "KKPR Provinsi" },
  { image: `${HERO_MEDIA}/Logo_PALI.png`, label: "KKPR PALI" },
  { image: `${HERO_MEDIA}/Lambang_Kabupaten_OKU_Timur.png`, label: "KKPR OKU Timur" },
  { image: `${HERO_MEDIA}/Lambang_Kabupaten_Musi_Banyuasin.png`, label: "KKPR MUBA" },
  { image: `${HERO_MEDIA}/Lambang_Kabupaten_Muara_Enim.gif`, label: "KKPR Muara Enim" },
  { image: `${HERO_MEDIA}/Lambang_Kabupaten_Banyuasin.gif`, label: "KKPR Banyuasin" },
  { image: `${HERO_MEDIA}/Lambang_Kabupaten_Ogan_Komering_Ulu.png`, label: "KKPR OKU" },
  { image: `${HERO_MEDIA}/LambangOganKomeringUluSelatan.png`, label: "KKPR OKU Selatan", wide: true },
];

const KKPR_KABKOTA = [
  { image: `${HERO_MEDIA}/OKU.png`, label: "Ogan Komering Ulu" },
  { image: `${HERO_MEDIA}/OKUSELATAN.png`, label: "OKU Selatan" },
  { image: `${HERO_MEDIA}/OKUTIMUR.png`, label: "OKU Timur" },
  { image: `${HERO_MEDIA}/OGANILIR.png`, label: "Ogan Ilir" },
  { image: `${HERO_MEDIA}/EMPATLAWANG.png`, label: "Empat Lawang" },
  { image: `${HERO_MEDIA}/PENUKALABABPEMATANGILIR.png`, label: "Penukal Abab Pematang Ilir" },
  { image: `${HERO_MEDIA}/MUSIRAWASUTARA.png`, label: "Musi Rawas Utara" },
  { image: `${HERO_MEDIA}/PALEMBANG.png`, label: "Kota Palembang" },
  { image: `${HERO_MEDIA}/PRABUMULIH.png`, label: "Kota Prabumulih" },
  { image: `${HERO_MEDIA}/PAGARALAM.png`, label: "Kota Pagar Alam" },
];

// Menu landing: Materi · Berita · Akurat · Dokumen · Katalog · Dataset · FAQ.
const NAV_LINKS = [
  { href: "#materi-rtrw", label: "Materi" },
  { href: "#berita", label: "Berita" },
  { href: "#screening", label: "Akurat" },
  { href: "#dokumen", label: "Dokumen" },
  { href: "#katalog", label: "Katalog" },
  { href: "#dataset", label: "Dataset" },
  { href: "#tentang-program", label: "FAQ" },
];




function accordionItems(namaKab: string, kabShort: string) {
  return [
  {
    id: "01",
    label: "FAQ SITARUNG",
    title: <>Informasi <span className="italic font-normal text-gray-600">Umum</span></>,
    content: (
      <>
        <p><strong className="text-gray-900">SITARUNG</strong> adalah kependekan dari <em>Sistem Informasi Tata Ruang</em> Provinsi Sumatera Selatan. Sistem ini berfungsi sebagai basis data digital yang menyediakan informasi spasial untuk mendukung proses perencanaan, pemantauan, dan pengambilan keputusan terkait tata ruang wilayah.</p>
        <p>Tujuan utama SITARUNG adalah mewujudkan visi dan misi pembangunan daerah ke dalam kondisi tata ruang ideal di Sumatera Selatan. Portal ini menjadi alat bantu dalam proses penataan ruang, mulai dari <strong className="text-gray-900">perencanaan</strong>, <strong className="text-gray-900">pemanfaatan</strong>, hingga <strong className="text-gray-900">pengendalian pemanfaatan ruang</strong>.</p>
        <p>SITARUNG dikelola oleh <strong className="text-gray-900">Dinas Pekerjaan Umum Bina Marga dan Tata Ruang Pemerintah Provinsi Sumatera Selatan</strong>.</p>
      </>
    ),
  },
  {
    id: "02",
    label: "Portal Data",
    title: <>Fitur dan <span className="italic font-normal text-gray-600">Data</span></>,
    content: (
      <>
        <p>SITARUNG menyediakan beberapa modul utama, di antaranya <strong className="text-gray-900">Portal Data SITARUNG</strong> untuk peta dan dokumen, serta <strong className="text-gray-900">Modul Pemetaan KKPR</strong> untuk pengawasan pemanfaatan ruang.</p>
        <p>Melalui Portal Data, pengguna dapat mengakses tiga kategori informasi utama:</p>
        <ul className="list-disc space-y-2 pl-5">
          <li><strong className="text-gray-900">Peta Spasial</strong> untuk informasi geografi, batas wilayah, peruntukan lahan, dan elemen spasial lainnya.</li>
          <li><strong className="text-gray-900">Dokumen Teknis</strong> berupa dokumen resmi, kebijakan, pedoman perencanaan, dan laporan kegiatan.</li>
          <li><strong className="text-gray-900">Dataset RTR</strong> yang berisi data tematik, hasil analisis, temuan penelitian, dan indikator kunci untuk evaluasi RTR.</li>
        </ul>
        <p>SITARUNG juga menyediakan informasi tentang <strong className="text-gray-900">Rencana Struktur Ruang</strong> dan <strong className="text-gray-900">Rencana Pola Ruang</strong> sebagai materi utama penataan ruang wilayah.</p>
      </>
    ),
  },
  {
    id: "03",
    label: "Regulasi",
    title: <>Peraturan dan <span className="italic font-normal text-gray-600">Dokumen</span></>,
    content: (
      <>
        <p>Dasar hukum terkini yang tersedia di SITARUNG adalah <strong className="text-gray-900">Peraturan Daerah Nomor 6 Tahun 2024</strong> tentang Rencana Tata Ruang Wilayah Provinsi Sumatera Selatan Tahun 2024–2044. Dokumen ini menggantikan Perda Nomor 11 Tahun 2016.</p>
        <p>Portal ini juga memuat dokumen yang dapat diunduh, termasuk materi sosialisasi RTRW terbaru serta regulasi terkait <strong className="text-gray-900">RTR Kawasan Strategis Nasional</strong> untuk kawasan perkotaan Palembang, Betung, Indralaya, dan Kayu Agung.</p>
        <p><strong className="text-gray-900">Forum Penataan Ruang</strong> yang tercantum di dalam dokumen berfungsi memfasilitasi perencanaan tata ruang partisipatif dan memberikan pertimbangan kepada pemerintah dalam pelaksanaan penataan ruang.</p>
      </>
    ),
  },
  {
    id: "04",
    label: "Pemanfaatan Ruang",
    title: <>KKPR dan <span className="italic font-normal text-gray-600">Pengendalian</span></>,
    content: (
      <>
        <p><strong className="text-gray-900">KKPR</strong> adalah singkatan dari <em>Kesesuaian Kegiatan Pemanfaatan Ruang</em>. Ini merupakan persyaratan dasar dalam proses perizinan usaha maupun non-usaha, baik di darat maupun perairan.</p>
        <p>Dalam SITARUNG, Modul Pemetaan KKPR membantu pengawasan dan penegakan pelaksanaan rencana tata ruang agar pemanfaatan ruang tetap selaras dengan RTRW Provinsi Sumatera Selatan.</p>
        <p>Arahan pengendalian pemanfaatan ruang menjadi acuan pemerintah dalam <strong className="text-gray-900">pengawasan</strong>, <strong className="text-gray-900">pemberian izin</strong>, <strong className="text-gray-900">insentif atau disinsentif</strong>, dan <strong className="text-gray-900">penerapan sanksi</strong>.</p>
      </>
    ),
  },
  {
    id: "05",
    label: "Kontak",
    title: <>Informasi <span className="italic font-normal text-gray-600">Kontak</span></>,
    content: (
      <>
        <p>Untuk menghubungi admin SITARUNG atau instansi terkait, pengguna dapat menghubungi <strong className="text-gray-900">Dinas Pekerjaan Umum Bina Marga dan Tata Ruang</strong> Provinsi Sumatera Selatan.</p>
        <ul className="list-disc space-y-2 pl-5">
          <li><strong className="text-gray-900">Alamat:</strong> Jl. Ade Irma Nasution No. 10, Palembang, Sumatera Selatan</li>
          <li><strong className="text-gray-900">Telepon:</strong> 071-313431</li>
          <li><strong className="text-gray-900">Email:</strong> <a className="text-folur-700 underline decoration-folur-200 underline-offset-2 hover:text-folur-900" href="mailto:tataruang.sumsel@gmail.com">tataruang.sumsel@gmail.com</a></li>
        </ul>
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
  const nextSlide = useCallback(() => setActiveSlide((s) => (s + 1) % HERO_BANNERS.length), []);
  const prevSlide = useCallback(() => setActiveSlide((s) => (s - 1 + HERO_BANNERS.length) % HERO_BANNERS.length), []);

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

  const currentSlide = HERO_BANNERS[activeSlide] ?? HERO_BANNERS[0];

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
    <div className="bg-cap-bg text-gray-800">
      {hideCss && <style dangerouslySetInnerHTML={{ __html: hideCss }} />}
      {/* ============ HEADER SITARUNG + HERO CAROUSEL ============ */}
      <div className="relative">
        <header className="absolute inset-x-0 top-0 z-50 h-[50px] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.12)]">
          <div className="relative mx-auto h-full max-w-7xl">
            <a href="/" className="absolute left-[5px] top-[3px] z-50 block w-[110px]" aria-label={brandName}>
              <img src={site.logo || `${HERO_MEDIA}/favicon.png`} alt={brandName} className="h-[110px] w-[110px] object-contain drop-shadow" />
            </a>
            <div className="absolute right-4 top-0 hidden w-[110px] sm:block lg:right-[30px]">
              <img src={`${HERO_MEDIA}/lohorights.png`} alt="" className="w-[110px] object-contain drop-shadow" />
            </div>
            <div className="absolute left-[130px] right-[155px] top-0 hidden h-[50px] overflow-hidden lg:block">
              <div className="marquee-track flex h-[50px] items-center whitespace-nowrap">
                <span className="site-title shrink-0 pr-24">{MARQUEE_TITLE}</span>
                <span className="site-title shrink-0 pr-24" aria-hidden="true">{MARQUEE_TITLE}</span>
              </div>
            </div>
          </div>
        </header>

        {/* ============ HERO CAROUSEL SITARUNG (latar banner Jembatan Ampera) ============ */}
        <section
          id="beranda-carousel"
          className="relative overflow-hidden bg-brand-900 text-white select-none"
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          onTouchStart={onTouchStart}
          onTouchEnd={onTouchEnd}
        >
          {HERO_BANNERS.map((banner, i) => (
            <div
              key={banner.bg}
              aria-hidden={activeSlide !== i}
              className={`absolute inset-0 transition-opacity duration-700 ease-in-out ${activeSlide === i ? "opacity-100" : "pointer-events-none opacity-0"}`}
              style={{ background: `${HERO_OVERLAY}, url('${banner.bg}') center/cover` }}
            />
          ))}
          <div className="relative mx-auto max-w-7xl px-6 pt-[50px]">
            <div key={currentSlide.bg} className="relative z-10 grid min-h-[362px] items-center gap-8 py-6 transition-opacity duration-700 ease-in-out lg:grid-cols-2">
              <div>
                <span className="mb-5 inline-block rounded-full bg-white/15 px-3 py-1 text-xs font-medium tracking-wide ring-1 ring-white/20 backdrop-blur">{brandSubtitle}</span>
                <h1 className="text-5xl font-bold leading-none tracking-tight drop-shadow-lg md:text-7xl">{brandName}</h1>
                <p className="mt-4 text-xl font-light text-white/95 drop-shadow md:text-2xl">Sistem Informasi Tata Ruang<br />{brandSubtitle}</p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <a href="/jelajah-dataset" className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-brand-700 shadow-lg transition hover:bg-brand-50">Jelajahi Portal</a>
                  <a href="/jelajah-dokumen" className="rounded-lg px-6 py-3 text-sm font-semibold text-white ring-1 ring-white/50 backdrop-blur transition hover:bg-white/10">Dokumen RTRW</a>
                </div>
              </div>
              <div className="hidden justify-center lg:flex">
                <img src={currentSlide.figure} alt="" className="max-h-[400px] object-contain drop-shadow-2xl" />
              </div>
            </div>

            <div className="absolute bottom-5 left-1/2 z-20 flex -translate-x-1/2 gap-2">
              {HERO_BANNERS.map((_, i) => (
                <button type="button" key={i} onClick={() => setActiveSlide(i)} aria-label={`Slide ${i + 1}`} className={`h-2.5 rounded-full transition-all ${activeSlide === i ? "w-6 bg-white" : "w-2.5 bg-white/40 hover:bg-white/80"}`} />
              ))}
            </div>
          </div>

          <button type="button" onClick={prevSlide} aria-label="Slide sebelumnya" className="absolute left-3 top-1/2 z-20 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-full bg-white/15 text-white ring-1 ring-white/30 backdrop-blur transition-all duration-200 hover:scale-110 hover:bg-white/30 active:scale-95 sm:left-5 lg:left-8">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </button>
          <button type="button" onClick={nextSlide} aria-label="Slide berikutnya" className="absolute right-3 top-1/2 z-20 grid h-11 w-11 -translate-y-1/2 place-items-center rounded-full bg-white/15 text-white ring-1 ring-white/30 backdrop-blur transition-all duration-200 hover:scale-110 hover:bg-white/30 active:scale-95 sm:right-5 lg:right-8">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
          </button>
        </section>
      </div>

      {/* ============ BAR MENU TEAL STICKY ============ */}
      <nav className="sticky top-0 z-40 border-b border-brand-500/20 backdrop-blur" style={{ background: "rgba(154,239,235,0.75)" }}>
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex h-[60px] items-center justify-between">
            <a href="/" className="flex items-center gap-2 lg:hidden">
              <img src={site.logo || `${HERO_MEDIA}/favicon.png`} alt="" className="h-8 w-8 object-contain" />
              <span className="font-bold text-brand-800">{brandName}</span>
            </a>
            <ul className="mx-auto hidden items-center gap-2 lg:flex">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="menu-pill">{link.label}</a>
                </li>
              ))}
            </ul>
            <button onClick={() => setMobileOpen(true)} className="ml-auto rounded-lg p-2 hover:bg-white/50 lg:hidden" aria-label="Buka menu">
              <svg className="h-6 w-6 text-brand-800" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
          </div>
        </div>
      </nav>

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
        </nav>
      </aside>

      {/* ============ STAT STRIP ============ */}
      <section id="statistik" className="relative z-20 bg-white py-8 sm:py-10">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { value: String(data.documentsTotal), label: "Dokumen Kebijakan", sub: "Perda, Perbup, RPJMD, Renstra", color: "text-folur-700" },
              { value: String(data.datasetsTotal), label: "Layer Spasial", sub: "Vektor & raster · ter-publish", color: "text-sky-600" },
              { value: String(data.screeningTotal), label: "Modul Akurat", sub: "Realtime AoI · Audit Log", color: "text-earth-600" },
              { value: String(data.komoditas.length), label: "Berita Terkini", sub: "Fokus Permasalahan Taru", color: "text-folur-600" },
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

      {/* ============ MATERI MUATAN RTRW ============ */}
      <section id="materi-rtrw" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Materi Muatan RTRW</span>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Pola &amp; Struktur Ruang</h2>
          <p className="mt-3 text-gray-500">Tujuan, kebijakan, dan strategi penataan ruang wilayah {brandSubtitle}.</p>
        </div>
        <div className="mt-12 grid gap-7 sm:grid-cols-2 lg:grid-cols-3">
          {RTRW_CONTENT.map((item) => (
            <a key={item.id} href={item.href} className="group relative flex flex-col overflow-hidden rounded-3xl bg-white shadow-[0_10px_30px_-12px_rgba(13,179,144,0.25)] ring-1 ring-brand-500/10 transition duration-300 hover:-translate-y-2 hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)] focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-4 focus-visible:ring-offset-white">
              <div className="relative flex h-56 items-center justify-center overflow-hidden bg-gradient-to-br from-brand-50 via-white to-brand-100/50">
                <span className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-brand-400/20 blur-2xl" />
                <span className="absolute -bottom-8 -left-8 h-24 w-24 rounded-full bg-brand-300/20 blur-2xl" />
                <span className="absolute left-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/85 text-sm font-extrabold text-brand-600 ring-1 ring-brand-500/10 backdrop-blur">{item.id}</span>
                <img src={item.image} alt={item.title} className="relative max-h-[86%] max-w-[84%] object-contain drop-shadow-xl transition duration-500 group-hover:scale-110" />
              </div>
              <div className="flex flex-1 flex-col p-6">
                <h3 className="text-lg font-bold leading-snug text-brand-700">{item.title}</h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-500">{item.description}</p>
                <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-accent">Pelajari <svg className="h-4 w-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
              </div>
              <span className="absolute inset-x-0 bottom-0 h-1 origin-left scale-x-0 bg-gradient-to-r from-brand-400 to-brand-600 transition-transform duration-500 group-hover:scale-x-100" />
            </a>
          ))}
        </div>
      </section>

      {/* ============ PENYELENGGARAAN ============ */}
      <section id="penyelenggaraan" className="border-y border-brand-500/10 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Penyelenggaraan</span>
            <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Penataan Ruang</h2>
          </div>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {PENATAAN_RUANG_ITEMS.map((item) => (
              <div key={item.title} className="group text-center">
                <div className="mx-auto flex h-40 w-40 items-center justify-center sm:h-48 sm:w-48">
                  <img src={item.image} alt={item.title} className="max-h-full max-w-full object-contain drop-shadow-xl transition duration-500 group-hover:scale-110" />
                </div>
                <h4 className="mt-4 font-bold text-brand-700">{item.title}</h4>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ SATU PINTU DATA ============ */}
      <section id="modul" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Satu Pintu Data</span>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Modul Portal Data SITARUNG</h2>
          <p className="mt-3 text-gray-500">Tiga modul utama yang menyatukan data spasial, dokumen, dan dataset tata ruang dalam satu portal terpadu.</p>
        </div>
        <div className="mt-14 grid gap-7 md:grid-cols-3">
          {PORTAL_MODULES.map((module) => (
            <a key={module.title} href={module.href} className="group relative flex flex-col rounded-3xl bg-white shadow-[0_10px_30px_-12px_rgba(13,179,144,0.25)] ring-1 ring-brand-500/10 transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)]">
              <span className="absolute inset-x-6 top-0 h-1 origin-left scale-x-0 rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-transform duration-500 group-hover:scale-x-100" />
              <div className="p-5 pb-0">
                <div className="relative aspect-[5/4] overflow-hidden rounded-2xl bg-gradient-to-br from-brand-50 to-white ring-1 ring-brand-500/10">
                  <span className="absolute left-3 top-3 rounded-full bg-white/85 px-2.5 py-1 text-[11px] font-semibold text-brand-700 ring-1 ring-brand-500/10 backdrop-blur">{module.badge}</span>
                  <span className="absolute right-4 top-3 text-2xl font-extrabold text-brand-200 transition group-hover:text-brand-300">{module.number}</span>
                  <img src={module.image} alt={module.title} className="h-full w-full object-contain p-6 drop-shadow transition duration-500 group-hover:scale-105" />
                </div>
              </div>
              <div className="flex flex-1 flex-col p-6">
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600">
                    {module.type === "spatial" && <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 3 3 6v15l6-3 6 3 6-3V3l-6 3-6-3Z" /><path d="M9 3v15M15 6v15" /></svg>}
                    {module.type === "document" && <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg>}
                    {module.type === "dataset" && <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" /></svg>}
                  </span>
                  <h3 className="text-lg font-bold text-brand-700">{module.title}</h3>
                </div>
                <p className="mt-3 flex-1 text-sm leading-relaxed text-gray-500">{module.description}</p>
                <span className="mt-5 inline-flex items-center gap-2 self-start rounded-full bg-brand-500/10 px-4 py-2 text-sm font-semibold text-brand-700 transition group-hover:bg-brand-600 group-hover:text-white">Buka Modul <svg className="h-4 w-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* ============ TERKINI ============ */}
      <section id="berita" className="border-y border-brand-500/10 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="flex items-end justify-between gap-6">
            <div>
              <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Terkini</span>
              <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Info &amp; Berita</h2>
            </div>
            <a href="#" className="hidden text-sm font-semibold text-accent hover:underline sm:inline">Semua berita →</a>
          </div>
          <div className="mt-10 grid gap-8 lg:grid-cols-2">
            <article className="group overflow-hidden rounded-2xl bg-gray-50 shadow-[0_10px_30px_-12px_rgba(13,179,144,0.25)] ring-1 ring-brand-500/10 transition hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)]">
              <div className="aspect-[16/9] overflow-hidden"><img src={NEWS_FEATURED.image} alt={NEWS_FEATURED.title} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" /></div>
              <div className="p-6">
                <p className="text-xs text-gray-400">{NEWS_FEATURED.date}</p>
                <h3 className="mt-2 text-lg font-bold leading-snug text-gray-900 transition group-hover:text-brand-700">{NEWS_FEATURED.title}</h3>
                <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-gray-500">{NEWS_FEATURED.description}</p>
              </div>
            </article>
            <div className="space-y-6">
              {NEWS_LIST.map((item) => (
                <article key={item.title} className="group flex gap-4 rounded-2xl bg-gray-50 p-4 ring-1 ring-brand-500/10 transition hover:shadow-[0_10px_30px_-12px_rgba(13,179,144,0.25)]">
                  <div className="h-24 w-32 shrink-0 overflow-hidden rounded-xl bg-brand-50"><img src={item.image} alt={item.title} className="h-full w-full object-cover" /></div>
                  <div>
                    <p className="text-xs text-gray-400">{item.date}</p>
                    <h4 className="font-semibold leading-snug text-gray-900 transition group-hover:text-brand-700">{item.title}</h4>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">{item.description}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ GALERI VIDEO ============ */}
      <section id="galeri-video" className="mx-auto max-w-7xl px-6 py-20">
        <div>
          <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Galeri Video</span>
          <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Video</h2>
        </div>
        <div className="mt-10 grid items-stretch gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {VIDEO_GALLERY.map((item) => (
            <a key={item.href} href={item.href} target="_blank" rel="noopener noreferrer" className="group flex flex-col overflow-hidden rounded-2xl bg-white shadow-[0_10px_30px_-12px_rgba(13,179,144,0.25)] ring-1 ring-brand-500/10 transition duration-300 hover:-translate-y-1 hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)]">
              <div className="relative aspect-video overflow-hidden bg-brand-900">
                <img src={item.image} alt={item.title} className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
                <span className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-md bg-black/70 px-2 py-0.5 text-[10px] font-bold tracking-wide text-white"><svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M23 12s0-3.9-.5-5.8a3 3 0 0 0-2.1-2.1C18.5 3.6 12 3.6 12 3.6s-6.5 0-8.4.5A3 3 0 0 0 1.5 6.2 30 30 0 0 0 1 12a30 30 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 8.4.5 8.4.5s6.5 0 8.4-.5a3 3 0 0 0 2.1-2.1C23 15.9 23 12 23 12ZM10 15.5v-7l6 3.5-6 3.5Z" /></svg>YOUTUBE</span>
                <span className="absolute inset-0 flex items-center justify-center"><span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)] transition duration-300 group-hover:scale-110"><svg className="ml-0.5 h-6 w-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg></span></span>
              </div>
              <div className="flex flex-1 flex-col p-4">
                <p className="line-clamp-3 text-sm font-medium leading-snug text-gray-900 transition group-hover:text-brand-700">{item.title}</p>
                <span className="mt-auto inline-flex items-center gap-1.5 pt-3 text-xs font-semibold text-accent">Tonton video <svg className="h-3.5 w-3.5 transition group-hover:translate-x-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* ============ UNDUHAN ============ */}
      <section id="unduhan" className="border-y border-brand-500/10 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div>
            <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Unduhan</span>
            <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Dokumen RTRW</h2>
          </div>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {DOWNLOAD_ITEMS.map((item) => (
              <a key={item.label} href="/jelajah-dokumen" className="group rounded-2xl bg-gray-50 p-6 text-center ring-1 ring-brand-500/10 transition hover:-translate-y-1 hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)]">
                <img src={item.image} alt={item.label} className="mx-auto h-28 object-contain transition group-hover:scale-105" />
                <p className="mt-4 font-bold text-brand-700">{item.label}</p>
                <p className="mt-1 text-sm text-gray-500">{item.description}</p>
              </a>
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
              <p className="text-sm font-semibold text-sky-600 tracking-widest uppercase mb-2">Peta Interaktif</p>
              <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Modul Akurat</h2>
              <p className="text-gray-500 mb-8">SITARUNG AKURAT (Modul Analisis Kesesuaian Kegiatan Pemanfaatan Ruang) sebagai panel manajerial untuk membantu dalam menganalisis, memvisualisasikan, dan mengelola data spasial terkait kesesuaian dan pemanfaatan ruang. Modul ini mampu mengidentifikasi secara cepat area (misalnya potensi pelanggaran atau tumpang tindih pemanfaatan ruang).</p>
              <div className="flex flex-wrap gap-3">
                <a href="/webgis-screening" className="inline-flex items-center px-6 py-3 bg-folur-700 text-white font-semibold rounded-lg hover:bg-folur-800 transition">Modul AKURAT</a>
              </div>
            </div>
            <div className="overflow-hidden shadow-xl border border-gray-200 bg-gray-50">
              <img src="/images/akurat.jpg" alt="SITARUNG AKURAT" className="w-full h-auto" />
            </div>
          </div>
        </div>
      </section>

      {/* ============ SITARUNG KABUPATEN/KOTA ============ */}
      <section id="sitarung-kabupaten" className="border-y border-brand-500/10 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-sm font-semibold uppercase tracking-wider text-brand-600">Tautan Sitarung</span>
            <h2 className="mt-2 text-3xl font-bold text-gray-900 md:text-4xl">Sitarung Kabupaten/Kota</h2>
          </div>
          <div className="mt-10 grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5">
            {KKPR_KABKOTA.map((item) => (
              <a key={item.label} href="/webgis-screening" className="group rounded-2xl bg-gray-50 p-5 text-center ring-1 ring-brand-500/10 transition hover:-translate-y-1 hover:shadow-[0_20px_45px_-18px_rgba(11,75,63,0.45)]">
                <img src={item.image} alt={item.label} className="mx-auto h-28 object-contain transition group-hover:scale-110" onError={(e) => { e.currentTarget.style.display = "none"; }} />
                <p className="mt-3 text-sm font-semibold text-gray-800">{item.label}</p>
              </a>
            ))}
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
          <p className="text-sm font-semibold text-folur-600 tracking-widest uppercase mb-2">SITARUNG · FAQ</p>
          <h2 className="font-serif text-3xl md:text-4xl font-extrabold text-gray-900 mb-4">Pertanyaan yang <span className="italic font-light text-folur-600">Sering Diajukan</span></h2>
          <p className="text-gray-500 max-w-3xl mb-16">Ringkasan informasi dari halaman FAQ SITARUNG Sumatera Selatan, mencakup gambaran umum sistem, fitur data, dokumen RTRW, KKPR, dan kontak instansi pengelola.</p>
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
              <div className="max-w-xs text-sm text-folur-200/70 space-y-1">
                <p>Address: Jl. Ade Irma Nasution No. 10, Palembang, Sumatera Selatan, Indonesia</p>
                <p>Phone: 071-313431, Email: tataruang.sumsel@gmail.com</p>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold mb-4">Navigasi</h4>
              <ul className="space-y-2 text-sm text-folur-200/70">
                <li><a href={"/jelajah-dokumen"} className="hover:text-white">Jelajahi Dokumen</a></li>
                <li><a href={"/jelajah-dataset"} className="hover:text-white">Eksplorasi Dataset</a></li>
                <li><a href={"/webgis-screening/"} className="hover:text-white">Screening Tools</a></li>
                <li><a href={"/jelajah-endpoint"} className="hover:text-white">API & Endpoint</a></li>
                <li><a href={"/pengaduan"} className="hover:text-white">Pengaduan</a></li>
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
          </div>
        </div>
      </footer>
    </div>
  );
}
