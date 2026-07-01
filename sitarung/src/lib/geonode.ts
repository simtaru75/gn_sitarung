/**
 * Lapisan data GeoNode (server-only) — fetch API v2 lalu normalisasi ke tipe
 * ringkas yang dipakai UI. URL publik sudah dibangun di sini sehingga komponen
 * client cukup merender string.
 *
 * Semua fetch tahan-gagal: bila GeoNode tak terjangkau / non-200, fungsi
 * mengembalikan nilai kosong agar halaman tetap render (tidak crash).
 */
import {
  INTERNAL_BASE,
  datasetUrl,
  documentUrl,
  publicUrl,
  rewriteHostToPublic,
} from "./config";

export const DEFAULT_SITE_LOGO = "http://localhost/uploaded/img/2026/06/prov-250-16.png";

export interface DocumentItem {
  pk: string;
  title: string;
  year: number | null;
  typeLabel: string;
  url: string;
  thumbnail: string;
}

export interface DatasetItem {
  pk: string;
  title: string;
  abstract: string;
  subtype: string;
  featureLabel: string; // "Vektor" | "Raster"
  categoryId: string | null;
  categoryLabel: string | null;
  regionCodes: string[];
  regionNames: string[];
  walidata: string | null;
  epsg: string | null;
  url: string;
  thumbnail: string;
}

export interface CategoryItem {
  identifier: string;
  label: string;
  faClass: string;
  count: number;
}

export interface KomoditasItem {
  id: number;
  nama: string;
  deskripsi: string;
  gambar: string; // URL publik penuh
}

export interface PartnerItem {
  id: number;
  nama: string;
  tautan: string;
  logo: string; // URL publik penuh
}

export interface IndikatorItem {
  id: number;
  judul: string;
  nilai: string;
  deskripsi: string;
  ikon: string; // URL publik penuh
}

export interface LandingData {
  documents: DocumentItem[];
  documentsTotal: number;
  datasets: DatasetItem[];
  datasetsTotal: number;
  categories: CategoryItem[];
  komoditas: KomoditasItem[];
  partners: PartnerItem[];
  indikator: IndikatorItem[];
  screeningTotal: number;
  // Visibilitas seksi (dikelola admin di /dst-auth/frontend/). Key tak ada → tampil.
  sections: Record<string, boolean>;
  // true bila backend GeoNode tak terjangkau saat SSR (semua data inti kosong).
  isOffline: boolean;
}

async function apiGet<T = Record<string, unknown>>(
  path: string,
  revalidate?: number,
): Promise<T | null> {
  try {
    const res = await fetch(`${INTERNAL_BASE}${path}`, {
      headers: { Accept: "application/json" },
      // Default force-dynamic → no-store (data selalu segar). Beri `revalidate`
      // untuk data yang jarang berubah (mis. identitas situs) agar di-cache
      // antar-request & memangkas round-trip backend per halaman.
      ...(revalidate != null
        ? { next: { revalidate } }
        : { cache: "no-store" as const }),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

function yearOf(date: unknown): number | null {
  if (typeof date !== "string") return null;
  const y = new Date(date).getFullYear();
  return Number.isFinite(y) ? y : null;
}

function cap(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

export async function getDocuments(): Promise<{ items: DocumentItem[]; total: number }> {
  // Hanya dokumen ter-approve & ter-publish (publik). Tanpa filter ini API v2
  // ikut mengembalikan dokumen is_approved=false (belum dimoderasi) ke anonim.
  const data = await apiGet<{ documents?: unknown[]; total?: number }>(
    "/api/v2/documents/?page_size=100&sort[]=-date&filter{is_approved}=true&filter{is_published}=true",
  );
  const rows = (data?.documents ?? []) as Record<string, unknown>[];
  const items: DocumentItem[] = rows.map((d) => ({
    pk: String(d.pk),
    title: String(d.title ?? "Tanpa judul"),
    year: yearOf(d.date),
    typeLabel: cap(String(d.subtype ?? d.extension ?? "Document")),
    url: documentUrl(String(d.pk)),
    thumbnail: rewriteHostToPublic(d.thumbnail_url as string),
  }));
  return { items, total: data?.total ?? items.length };
}

export async function getDatasets(): Promise<{ items: DatasetItem[]; total: number }> {
  // Ambil paralel: dataset API v2 + metadata project (walidata & tipe fitur asli
  // yang TIDAK diekspos API v2).
  const [data, meta] = await Promise.all([
    apiGet<{ datasets?: unknown[]; total?: number }>(
      "/api/v2/datasets/?page_size=100&sort[]=-date",
    ),
    apiGet<{ items?: Record<string, { walidata?: string; fitur?: string }> }>(
      "/api/folur/dataset-meta/",
    ),
  ]);
  const metaMap = meta?.items ?? {};
  const rows = (data?.datasets ?? []) as Record<string, unknown>[];
  const items: DatasetItem[] = rows.map((d) => {
    const subtype = String(d.subtype ?? "vector").toLowerCase();
    const cat = (d.category ?? null) as Record<string, unknown> | null;
    const regions = (d.regions ?? []) as Record<string, unknown>[];
    const attribution = String(d.attribution ?? "").trim();
    const m = metaMap[String(d.pk)] ?? {};
    const metaWalidata = String(m.walidata ?? "").trim();
    const metaFitur = String(m.fitur ?? "").trim();
    return {
      pk: String(d.pk),
      title: String(d.title ?? "Tanpa judul"),
      abstract: String(d.abstract ?? "").trim(),
      subtype,
      // Tipe fitur asli (Polygon/Line/Point/Raster) dari project; fallback subtype.
      featureLabel: metaFitur || (subtype === "raster" ? "Raster" : "Vektor"),
      categoryId: cat ? String(cat.identifier) : null,
      categoryLabel: cat ? String(cat.gn_description ?? cat.identifier) : null,
      regionCodes: regions.map((r) => String(r.code)),
      regionNames: regions.map((r) => String(r.name)),
      // Walidata dari sumber project (DatasetWalidata/POC); fallback attribution.
      walidata: metaWalidata || attribution || null,
      epsg: d.srid ? String(d.srid) : null,
      url: datasetUrl(String(d.pk)),
      thumbnail: rewriteHostToPublic(d.thumbnail_url as string),
    };
  });
  return { items, total: data?.total ?? items.length };
}

export async function getChoiceCategories(): Promise<CategoryItem[]> {
  const data = await apiGet<{ categories?: unknown[] }>(
    "/api/v2/categories/?page_size=100",
  );
  const rows = (data?.categories ?? []) as Record<string, unknown>[];
  return rows
    .filter((c) => c.is_choice === true)
    .map((c) => ({
      identifier: String(c.identifier),
      label: String(c.gn_description ?? c.identifier),
      faClass: String(c.fa_class ?? "fa-folder"),
      count: Number(c.count ?? 0),
    }));
}

export async function getKomoditas(): Promise<KomoditasItem[]> {
  const data = await apiGet<{ items?: unknown[] }>("/api/folur/komoditas/");
  const rows = (data?.items ?? []) as Record<string, unknown>[];
  return rows.map((k) => ({
    id: Number(k.id),
    nama: String(k.nama ?? ""),
    deskripsi: String(k.deskripsi ?? ""),
    gambar: k.gambar ? publicUrl(String(k.gambar)) : "",
  }));
}

export async function getPartners(): Promise<PartnerItem[]> {
  const data = await apiGet<{ items?: unknown[] }>("/api/folur/partners/");
  const rows = (data?.items ?? []) as Record<string, unknown>[];
  return rows.map((p) => ({
    id: Number(p.id),
    nama: String(p.nama ?? ""),
    tautan: String(p.tautan ?? ""),
    logo: p.logo ? publicUrl(String(p.logo)) : "",
  }));
}

export async function getIndikator(): Promise<IndikatorItem[]> {
  const data = await apiGet<{ items?: unknown[] }>("/api/folur/indikator/");
  const rows = (data?.items ?? []) as Record<string, unknown>[];
  return rows.map((x) => ({
    id: Number(x.id),
    judul: String(x.judul ?? ""),
    nilai: String(x.nilai ?? ""),
    deskripsi: String(x.deskripsi ?? ""),
    ikon: x.ikon ? publicUrl(String(x.ikon)) : "",
  }));
}

export async function getScreeningCount(): Promise<number> {
  const d = await apiGet<{ count?: number }>("/api/folur/screening-count/");
  return d?.count ?? 1;
}

export async function getLandingSections(): Promise<Record<string, boolean>> {
  // Toggle tampil/sembunyi seksi dari /dst-auth/frontend/ (LandingSection).
  const d = await apiGet<{ sections?: Record<string, boolean> }>("/api/folur/landing-sections/");
  return d?.sections ?? {};
}

export async function getLandingData(): Promise<LandingData> {
  const [docs, datasets, categories, komoditas, partners, indikator, screening, sections] = await Promise.all([
    getDocuments(),
    getDatasets(),
    getChoiceCategories(),
    getKomoditas(),
    getPartners(),
    getIndikator(),
    getScreeningCount(),
    getLandingSections(),
  ]);
  // Backend tak terjangkau bila data inti (dokumen, dataset, kategori) kosong
  // semua — GeoNode normal selalu punya TopicCategory ter-seed.
  const isOffline = docs.total === 0 && datasets.total === 0 && categories.length === 0;
  return {
    documents: docs.items,
    documentsTotal: docs.total,
    datasets: datasets.items,
    datasetsTotal: datasets.total,
    categories,
    komoditas,
    partners,
    indikator,
    screeningTotal: screening,
    sections,
    isOffline,
  };
}

// ── Jelajah Dokumen Kebijakan ──────────────────────────────────────────────

export type DocFilterKey = "walidata" | "kategori" | "tahun" | "format" | "wilayah";

export interface FacetOpt {
  value: string;
  label: string;
  count: number;
}

export interface DocRow {
  id: number;
  title: string;
  pengelola: string;
  walidata: string;
  kategori: string;
  year: string;
  extension: string;
  updated: string; // ISO
  regions: string;
  url: string;
}

export interface JelajahDokumen {
  documents: DocRow[];
  total: number;
  page: number;
  numPages: number;
  hasPrevious: boolean;
  hasNext: boolean;
  shownFrom: number;
  shownTo: number;
  q: string;
  selected: Record<DocFilterKey, string[]>;
  facets: Record<DocFilterKey, FacetOpt[]>;
}

const DOC_FILTER_KEYS: DocFilterKey[] = ["walidata", "kategori", "tahun", "format", "wilayah"];

export async function getJelajahDokumen(query: string): Promise<JelajahDokumen> {
  const path = `/api/folur/jelajah-dokumen/${query ? `?${query}` : ""}`;
  const d = (await apiGet<Record<string, unknown>>(path)) ?? {};
  const facetsRaw = (d.facets ?? {}) as Record<string, unknown>;
  const selRaw = (d.selected ?? {}) as Record<string, unknown>;
  const facets = {} as Record<DocFilterKey, FacetOpt[]>;
  const selected = {} as Record<DocFilterKey, string[]>;
  for (const k of DOC_FILTER_KEYS) {
    facets[k] = ((facetsRaw[k] ?? []) as Record<string, unknown>[]).map((o) => ({
      value: String(o.value),
      label: String(o.label),
      count: Number(o.count ?? 0),
    }));
    selected[k] = ((selRaw[k] ?? []) as unknown[]).map((v) => String(v));
  }
  const rows = (d.documents ?? []) as Record<string, unknown>[];
  return {
    documents: rows.map((r) => ({
      id: Number(r.id),
      title: String(r.title ?? ""),
      pengelola: String(r.pengelola ?? ""),
      walidata: String(r.walidata ?? ""),
      kategori: String(r.kategori ?? ""),
      year: String(r.year ?? ""),
      extension: String(r.extension ?? ""),
      updated: String(r.updated ?? ""),
      regions: String(r.regions ?? ""),
      url: documentUrl(Number(r.id)),
    })),
    total: Number(d.total ?? 0),
    page: Number(d.page ?? 1),
    numPages: Number(d.num_pages ?? 1),
    hasPrevious: Boolean(d.has_previous),
    hasNext: Boolean(d.has_next),
    shownFrom: Number(d.shown_from ?? 0),
    shownTo: Number(d.shown_to ?? 0),
    q: String(d.q ?? ""),
    selected,
    facets,
  };
}

// ── Identitas situs (ikut lingkup wilayah terpilih) ────────────────────────

export interface SiteIdentity {
  namaKabupaten: string;
  siteName: string;
  siteDomain: string;
  logo: string;
  theme: string;
  webgisReferenceMapId: number;
  fonts: { serif: string; sans: string; mono: string };
}

export async function getSiteIdentity(): Promise<SiteIdentity> {
  // Identitas situs identik di semua halaman → cache singkat 10 detik
  // agar perubahan tema di /dst-auth/tema/ segera tampil di frontend.
  const d = (await apiGet<Record<string, unknown>>("/api/folur/site-identity/", 10)) ?? {};
  return {
    namaKabupaten: String(d.nama_kabupaten ?? "") || "Kabupaten",
    siteName: String(d.site_name ?? "") || "DST",
    siteDomain: String(d.site_domain ?? ""),
    logo: d.logo ? publicUrl(String(d.logo)) : DEFAULT_SITE_LOGO,
    theme: String(d.theme ?? "") || "simtaru",
    webgisReferenceMapId: Number(d.webgis_reference_map_id ?? 1),
    fonts: {
      serif: String((d.fonts as Record<string, unknown> | undefined)?.serif ?? "Fraunces"),
      sans: String((d.fonts as Record<string, unknown> | undefined)?.sans ?? "Geist"),
      mono: String((d.fonts as Record<string, unknown> | undefined)?.mono ?? "Geist Mono"),
    },
  };
}

// ── Eksplorasi Endpoint API & OGC ───────────────────────────────────────────

export interface EndpointItem {
  method: string;
  path: string;
  desc: string;
  count: number | null;
  link: string;
  linkLabel: string;
}
export interface EndpointGroup {
  title: string;
  items: EndpointItem[];
}
export interface EndpointsData {
  baseUrl: string;
  geoserverUrl: string;
  stats: { totalEndpoints: number; resources: number; datasets: number; documents: number; ogcServices: number };
  groups: EndpointGroup[];
}

export async function getEndpoints(): Promise<EndpointsData> {
  // Endpoint project /api/folur/endpoints/ — payload identik EndpointApiExploreView
  // (daftar REST v2 + OGC, count katalog, tautan publik siap pakai).
  const d = await apiGet<Record<string, unknown>>("/api/folur/endpoints/");
  const stats = (d?.stats ?? {}) as Record<string, unknown>;
  const groups = Array.isArray(d?.groups) ? (d!.groups as Array<Record<string, unknown>>) : [];
  return {
    baseUrl: String(d?.base_url ?? ""),
    geoserverUrl: String(d?.geoserver_url ?? ""),
    stats: {
      totalEndpoints: Number(stats.total_endpoints ?? 0),
      resources: Number(stats.resources ?? 0),
      datasets: Number(stats.datasets ?? 0),
      documents: Number(stats.documents ?? 0),
      ogcServices: Number(stats.ogc_services ?? 0),
    },
    groups: groups.map((g) => ({
      title: String(g.title ?? ""),
      items: (Array.isArray(g.items) ? (g.items as Array<Record<string, unknown>>) : []).map((it) => ({
        method: String(it.method ?? ""),
        path: String(it.path ?? ""),
        desc: String(it.desc ?? ""),
        count: it.count == null ? null : Number(it.count),
        link: String(it.link ?? ""),
        linkLabel: String(it.link_label ?? ""),
      })),
    })),
  };
}

// ── WebGIS Capaian (/webgis-capaian, port /webgis2/) ───────────────────────

export interface WebgisCapaianIndikator {
  kode: string;
  nama: string;
  [k: string]: unknown;
}
export interface WebgisCapaianConfig {
  geojsonUrl: string;
  historyUrl: string;
  center: [number, number];
  bbox: [[number, number], [number, number]] | null;
  tahun: number;
  years: number[];
  level: string;
  levels: string[];
  nKec: number;
  nDesa: number;
  indikator: WebgisCapaianIndikator[];
  namaKabupaten: string;
  cakupanNama: string;
  komoditasFokus: string[];
  komoditasIcons: Record<string, string>;
  siteName: string;
}

export async function getWebgisCapaianConfig(): Promise<WebgisCapaianConfig | null> {
  // Config DB-derived dipakai ulang dari WebGis2View (identik /webgis2/).
  return apiGet<WebgisCapaianConfig>("/api/folur/webgis-capaian-config/");
}

// ── Eksplorasi Dataset ─────────────────────────────────────────────────────

export type DsFilterKey = "walidata" | "kategori" | "feature" | "wilayah";

export interface DatasetExploreRow {
  id: number;
  title: string;
  walidata: string;
  category: string;
  feature: string;
  regions: string;
  thumbnail: string;
  isRaster: boolean;
  year: string;
  url: string;
}

export interface JelajahDataset {
  datasets: DatasetExploreRow[];
  total: number;
  page: number;
  numPages: number;
  pageList: (number | null)[];
  hasPrevious: boolean;
  hasNext: boolean;
  previousPage: number | null;
  nextPage: number | null;
  shownFrom: number;
  shownTo: number;
  sort: string;
  q: string;
  selected: Record<DsFilterKey, string[]>;
  facets: Record<DsFilterKey, FacetOpt[]>;
}

const DS_FILTER_KEYS: DsFilterKey[] = ["walidata", "kategori", "feature", "wilayah"];

export async function getJelajahDataset(query: string): Promise<JelajahDataset> {
  const path = `/api/folur/jelajah-dataset/${query ? `?${query}` : ""}`;
  const d = (await apiGet<Record<string, unknown>>(path)) ?? {};
  const facetsRaw = (d.facets ?? {}) as Record<string, unknown>;
  const selRaw = (d.selected ?? {}) as Record<string, unknown>;
  const facets = {} as Record<DsFilterKey, FacetOpt[]>;
  const selected = {} as Record<DsFilterKey, string[]>;
  for (const k of DS_FILTER_KEYS) {
    facets[k] = ((facetsRaw[k] ?? []) as Record<string, unknown>[]).map((o) => ({
      value: String(o.value),
      label: String(o.label),
      count: Number(o.count ?? 0),
    }));
    selected[k] = ((selRaw[k] ?? []) as unknown[]).map((v) => String(v));
  }
  const rows = (d.datasets ?? []) as Record<string, unknown>[];
  return {
    datasets: rows.map((r) => ({
      id: Number(r.id),
      title: String(r.title ?? ""),
      walidata: String(r.walidata ?? ""),
      category: String(r.category ?? ""),
      feature: String(r.feature ?? ""),
      regions: String(r.regions ?? ""),
      thumbnail: rewriteHostToPublic(r.thumbnail_url as string),
      isRaster: Boolean(r.is_raster),
      year: String(r.year ?? ""),
      url: datasetUrl(Number(r.id)),
    })),
    total: Number(d.total ?? 0),
    page: Number(d.page ?? 1),
    numPages: Number(d.num_pages ?? 1),
    pageList: ((d.page_list ?? []) as unknown[]).map((p) => (p == null ? null : Number(p))),
    hasPrevious: Boolean(d.has_previous),
    hasNext: Boolean(d.has_next),
    previousPage: d.previous_page == null ? null : Number(d.previous_page),
    nextPage: d.next_page == null ? null : Number(d.next_page),
    shownFrom: Number(d.shown_from ?? 0),
    shownTo: Number(d.shown_to ?? 0),
    sort: String(d.sort ?? "recent"),
    q: String(d.q ?? ""),
    selected,
    facets,
  };
}

/* ------------------------------------------------------------------ */
/*  Document Detail                                                    */
/* ------------------------------------------------------------------ */

export interface DocumentDetail {
  pk: number;
  title: string;
  abstract: string;
  hasRealAbstract: boolean;
  supplemental: string;
  docType: string;
  extension: string;
  isPdf: boolean;
  isImage: boolean;
  hasFile: boolean;
  canDownload: boolean;
  fileUrl: string;
  pengelola: string;
  walidata: string;
  kategori: string;
  year: number | null;
  language: string;
  licenseName: string;
  attribution: string;
  viewsCount: number;
  regions: string[];
  keywords: string[];
  date: string;
  uuidShort: string;
  thumbnailUrl: string;
}

export async function getDocument(pk: string | number): Promise<DocumentDetail | null> {
  // Endpoint project /api/folur/dokumen/<pk>/ — payload identik DocumentDetailView
  // (jenis, walidata poc→author, izin unduh sadar-permission, file_url streaming).
  // SSR anonim (django:8000, tanpa cookie) → can_download = izin publik anonim.
  const d = await apiGet<Record<string, unknown>>(`/api/folur/dokumen/${pk}/`);
  if (!d || d.pk == null) return null;

  return {
    pk: Number(d.pk),
    title: String(d.title ?? "Tanpa judul"),
    abstract: String(d.abstract_text ?? ""),
    hasRealAbstract: Boolean(d.has_real_abstract),
    supplemental: String(d.supplemental ?? ""),
    docType: String(d.doc_type ?? "Dokumen"),
    extension: String(d.extension ?? "").toLowerCase(),
    isPdf: Boolean(d.is_pdf),
    isImage: Boolean(d.is_image),
    hasFile: Boolean(d.has_file),
    canDownload: Boolean(d.can_download),
    // Relatif (/dokumen/<pk>/file/) → diproksi same-origin oleh Next (PDF.js bebas CORS).
    fileUrl: String(d.file_url ?? ""),
    pengelola: String(d.pengelola ?? ""),
    walidata: String(d.walidata ?? ""),
    kategori: String(d.kategori ?? ""),
    year: d.year ? Number(d.year) : null,
    language: String(d.language ?? ""),
    licenseName: String(d.license_name ?? ""),
    attribution: String(d.attribution ?? ""),
    viewsCount: Number(d.views_count ?? 0),
    regions: Array.isArray(d.regions) ? (d.regions as string[]) : [],
    keywords: Array.isArray(d.keywords) ? (d.keywords as string[]) : [],
    date: "",
    uuidShort: String(d.uuid_short ?? ""),
    thumbnailUrl: rewriteHostToPublic(String(d.thumbnail_url ?? "")),
  };
}

/* ------------------------------------------------------------------ */
/*  Capaian FOLUR                                                      */
/* ------------------------------------------------------------------ */

export interface KpiItem {
  kode: string;
  nama: string;
  pilar: string;
  pilarNama: string;
  satuan: string;
  nilai: number | null;
  target: number | null;
  persen: number;
  agregasi: string;
  deskripsi: string;
  extra: string;
}

export interface CapaianData {
  kabupaten: {
    nama: string;
    namaKab: string;
  };
  tahunFilter: number | null;
  tahunTersedia: number[];
  jumlahIndikator: number;
  indikator: KpiItem[];
  komoditas: string[];
  sitroom: {
    auto: {
      luasBentangHa: number;
      jmlKecamatan: number;
      jmlDesa: number;
      jmlKelurahan: number;
      persenDesaMaju: number;
      idmRata2: number;
      periodeIdm: number;
      komoditasFokus: number;
    };
    ringkasan: {
      periode: number;
      totalIndikator: number;
      indikatorTerisi: number;
      indikatorBelum: number;
      pilar: Array<{ slug: string; nama: string; terisi: number; total: number }>;
    };
  };
}

export async function getCapaianFolur(): Promise<CapaianData | null> {
  // Endpoint publik (tanpa PIN) — api_capaian_folur dilindungi key utk integrasi
  // DST Nasional; capaian-publik menyajikan payload identik untuk halaman publik.
  const data = await apiGet<Record<string, unknown>>("/api/folur/capaian-publik/");
  if (!data) return null;

  const kab = (data.kabupaten as Record<string, unknown>) ?? {};
  const sitroom = (data.sitroom as Record<string, unknown>) ?? {};
  const auto = (sitroom.auto as Record<string, unknown>) ?? {};
  const ringkasan = (sitroom.ringkasan as Record<string, unknown>) ?? {};

  const indikators = Array.isArray(data.indikator) ? (data.indikator as Record<string, unknown>[]) : [];
  const kpis: KpiItem[] = indikators.map((d) => ({
    kode: String(d.kode ?? ""),
    nama: String(d.nama ?? ""),
    pilar: String(d.pilar ?? ""),
    pilarNama: String(d.pilar_nama ?? ""),
    satuan: String(d.satuan ?? ""),
    nilai: d.realisasi_terbaru ? Number((d.realisasi_terbaru as Record<string, unknown>).nilai ?? 0) : null,
    target: d.target != null ? Number(d.target) : null,
    persen: d.persen_capaian != null ? Math.round(Number(d.persen_capaian)) : 0,
    agregasi: String(d.agregasi ?? "tahunan"),
    deskripsi: String(d.deskripsi ?? ""),
    extra: String(d.extra ?? ""),
  }));

  return {
    kabupaten: {
      nama: String(kab.nama ?? ""),
      namaKab: String(kab.nama_kab ?? ""),
    },
    tahunFilter: data.tahun_filter ? Number(data.tahun_filter) : null,
    tahunTersedia: Array.isArray(data.tahun_tersedia) ? (data.tahun_tersedia as number[]) : [],
    jumlahIndikator: Number(data.jumlah_indikator ?? 0),
    indikator: kpis,
    komoditas: Array.isArray(data.komoditas) ? (data.komoditas as string[]) : [],
    sitroom: {
      auto: {
        luasBentangHa: Number(auto.luas_bentang_ha ?? 0),
        jmlKecamatan: Number(auto.jml_kecamatan ?? 0),
        jmlDesa: Number(auto.jml_desa ?? 0),
        jmlKelurahan: Number(auto.jml_kelurahan ?? 0),
        persenDesaMaju: Number(auto.persen_desa_maju ?? 0),
        idmRata2: Number(auto.idm_rata2 ?? 0),
        periodeIdm: Number(auto.periode_idm ?? 0),
        komoditasFokus: Number(auto.komoditas_fokus ?? 0),
      },
      ringkasan: {
        periode: Number(ringkasan.periode ?? 0),
        totalIndikator: Number(ringkasan.total_indikator ?? 0),
        indikatorTerisi: Number(ringkasan.indikator_terisi ?? 0),
        indikatorBelum: Number(ringkasan.indikator_belum ?? 0),
        pilar: Array.isArray(ringkasan.pilar)
          ? (ringkasan.pilar as Record<string, unknown>[]).map((p) => ({
              slug: String(p.slug ?? ""),
              nama: String(p.nama ?? ""),
              terisi: Number(p.terisi ?? 0),
              total: Number(p.total ?? 0),
            }))
          : [],
      },
    },
  };
}

/* ------------------------------------------------------------------ */
/*  Dataset Detail                                                     */
/* ------------------------------------------------------------------ */

export interface DatasetDetail {
  pk: number;
  title: string;
  name: string;
  abstract: string;
  hasRealAbstract: boolean;
  subtype: string;
  isRaster: boolean;
  alternate: string;
  typename: string;
  srid: string;
  bbox: [number, number, number, number] | null;
  extent: { coords: [number, number, number, number]; srid: string } | null;
  feature: string;
  geometryLabel: string;
  pengelola: string;
  walidata: string;
  kategori: string;
  categoryId: string;
  year: number | null;
  language: string;
  licenseName: string;
  attribution: string;
  viewsCount: number;
  regions: string[];
  keywords: string[];
  date: string;
  thumbnailUrl: string;
  workspace: string;
  owsUrl: string;
  detailUrl: string;
  endpoints: { label: string; desc: string; url: string }[];
  downloads: { kind: string; meta: string; url: string }[];
}

function isRasterType(subtype?: string): boolean {
  return (subtype ?? "").toLowerCase() === "raster";
}

function featureLabel(subtype?: string): string {
  if (!subtype) return "";
  const s = subtype.toLowerCase();
  if (s === "raster") return "Raster";
  if (s === "vector") return "Vektor";
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export async function getDataset(pk: string | number): Promise<DatasetDetail | null> {
  // Endpoint project /api/folur/dataset/<pk>/ — payload identik DatasetMapView
  // (walidata otoritatif, geometry_label, OGC endpoints & downloads dihitung
  // server). Tidak ada lagi penyusunan URL/label di sisi klien.
  const d = await apiGet<Record<string, unknown>>(`/api/folur/dataset/${pk}/`);
  if (!d || d.pk == null) return null;

  // payload.bbox = [[S,W],[N,E]] (Leaflet) → komponen butuh [W,S,E,N].
  let bbox: [number, number, number, number] | null = null;
  const bp = d.bbox as number[][] | null | undefined;
  if (Array.isArray(bp) && bp.length === 2 && Array.isArray(bp[0]) && Array.isArray(bp[1])) {
    bbox = [bp[0][1], bp[0][0], bp[1][1], bp[1][0]];
  }

  const eps = (d.endpoints ?? []) as Array<Record<string, unknown>>;
  const dls = (d.downloads ?? []) as Array<Record<string, unknown>>;

  return {
    pk: Number(d.pk),
    title: String(d.title ?? d.name ?? "Tanpa judul"),
    name: String(d.name ?? ""),
    abstract: String(d.abstract_text ?? ""),
    hasRealAbstract: Boolean(d.has_real_abstract),
    subtype: String(d.subtype ?? ""),
    isRaster: Boolean(d.is_raster),
    alternate: String(d.typename ?? ""),
    typename: String(d.typename ?? ""),
    srid: String(d.srid ?? "EPSG:4326"),
    bbox,
    extent: null,
    feature: String(d.feature ?? ""),
    geometryLabel: String(d.geometry_label ?? ""),
    pengelola: String(d.pengelola ?? ""),
    walidata: String(d.walidata ?? ""),
    kategori: String(d.kategori ?? ""),
    categoryId: String(d.category_id ?? ""),
    year: d.year ? Number(d.year) : null,
    language: "",
    licenseName: String(d.license_name ?? ""),
    attribution: String(d.attribution ?? ""),
    viewsCount: Number(d.views_count ?? 0),
    regions: Array.isArray(d.regions) ? (d.regions as unknown[]).map(String) : [],
    keywords: Array.isArray(d.keywords) ? (d.keywords as unknown[]).map(String) : [],
    date: "",
    thumbnailUrl: rewriteHostToPublic(d.thumbnail_url as string),
    workspace: "",
    owsUrl: "",
    detailUrl: String(d.catalogue_url ?? ""),
    endpoints: eps.map((e) => ({ label: String(e.label ?? ""), desc: String(e.desc ?? ""), url: String(e.url ?? "") })),
    downloads: dls.map((x) => ({ kind: String(x.kind ?? ""), meta: String(x.meta ?? ""), url: String(x.url ?? "") })),
  };
}
