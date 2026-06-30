/**
 * Konfigurasi URL GeoNode (server-side).
 *
 * Dua base URL:
 * - INTERNAL_BASE: dipakai server Next untuk fetch API v2 (dalam jaringan
 *   docker, tanpa CORS). Default `http://django:8000`.
 * - PUBLIC_BASE: dipakai untuk link & gambar yang dimuat browser. Default
 *   `http://localhost` (konsisten dengan SITEURL stack). Karena dibaca di
 *   Server Component saat request, nilainya runtime-configurable.
 *
 * Semua helper di sini dipakai server-side (di `geonode.ts` & `page.tsx`).
 * Komponen client menerima string URL yang sudah jadi sebagai props.
 */

export const INTERNAL_BASE = (
  process.env.GEONODE_INTERNAL_URL ?? "http://django:8000"
).replace(/\/+$/, "");

export const PUBLIC_BASE = (
  process.env.NEXT_PUBLIC_GEONODE_URL ?? "http://localhost"
).replace(/\/+$/, "");

/** Bangun URL absolut ke aset/route publik GeoNode (mis. "/static/...", "/uploaded/..."). */
export function publicUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${PUBLIC_BASE}${p}`;
}

/** Halaman detail dataset (route kustom project: /dataset/<pk>/). */
export function datasetUrl(pk: number | string): string {
  return `${PUBLIC_BASE}/dataset/${pk}/`;
}

/** Halaman detail dokumen (route kustom project: /dokumen/<pk>/). */
export function documentUrl(pk: number | string): string {
  return `${PUBLIC_BASE}/dokumen/${pk}/`;
}

/**
 * Ganti host sebuah URL absolut (mis. thumbnail_url dari API yang dibangun
 * terhadap SITEURL) menjadi PUBLIC_BASE. No-op bila host sudah sama
 * (kasus localhost). Jaring pengaman bila PUBLIC_BASE diubah ke domain lain.
 */
export function rewriteHostToPublic(absoluteUrl: string | null | undefined): string {
  if (!absoluteUrl) return "";
  try {
    const u = new URL(absoluteUrl);
    const pub = new URL(`${PUBLIC_BASE}/`);
    u.protocol = pub.protocol;
    u.host = pub.host;
    return u.toString();
  } catch {
    return absoluteUrl ?? "";
  }
}

/** Path logo fallback bila SiteIdentity.logo dari GeoNode kosong. */
export const BRAND_LOGO = "/uploaded/img/2026/06/kab-h250px-7317.png";
