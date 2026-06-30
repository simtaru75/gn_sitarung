# Plan: Hubungkan Frontend Next.js ke GeoNode Lokal (env-based, SSR, filter berfungsi)

## Context

Container `frontend` (Next.js 15, port 3000) saat ini adalah landing page **statis** untuk DST FOLUR Kabupaten Luwu. Tiga masalah yang menjadikannya sekadar "mockup":

1. **URL ter-hardcode ke produksi** — hampir semua link & gambar di `frontend/src/app/page.tsx` menunjuk `https://luwu.folur-dst.net/...`, bukan stack GeoNode lokal.
2. **Data mock, bukan dari API** — jumlah dokumen/dataset, daftar dokumen, kartu dataset, dan kategori semuanya array hardcoded; tidak ada koneksi ke GeoNode.
3. **Filter tidak berfungsi** — checkbox di "Eksplorasi Dataset" meng-update React state tapi tidak memfilter apa pun (grid-nya statis).

**Tujuan:** jadikan frontend ini landing page lokal yang hidup — menarik dokumen/dataset/kategori nyata dari GeoNode, dengan URL yang dapat dikonfigurasi (lokal ⇄ prod lewat env), dan filter yang benar-benar bekerja.

**Keputusan (dikonfirmasi user):**
- **Sumber data: lokal via env.** SSR fetch internal ke `http://django:8000` (tanpa CORS); link/gambar browser ke `http://localhost`; bisa di-switch ke domain lain lewat env tanpa ubah kode.
- **Arsitektur: SSR Server Component.** `page.tsx` jadi Server Component yang fetch data; UI interaktif dipindah ke `LandingClient.tsx`.
- **Domain = `localhost` (dikonfirmasi user).** Konsisten dengan konfigurasi stack yang sudah ada di `.env`: `SITEURL=http://localhost/`. Maka `NEXT_PUBLIC_GEONODE_URL` **default `http://localhost`** — dan `thumbnail_url`/`detail_url` dari API (yang sudah absolut ke `SITEURL` = `http://localhost`) langsung konsisten tanpa rewrite host. Mekanisme env tetap dipertahankan (tetap bisa di-switch), hanya saja nilainya kini pasti `localhost`.

## Temuan kunci (hasil eksplorasi)

- **GeoNode REST API v2 sudah aktif** (di-mount via `geonode.urls`): `/api/v2/datasets/`, `/api/v2/documents/`, `/api/v2/categories/`, `/api/v2/regions/`. Mengembalikan JSON kaya, mendukung `page_size`, pagination, dan filter `filter{category.identifier}=...`.
  - **datasets** (total 4): `pk`, `title`, `detail_url` (`http://localhost/catalogue/#/dataset/<pk>`), `thumbnail_url` (`http://localhost/uploaded/thumbs/...`), `subtype` (`vector`/`raster`), `category` (obj/null), `regions` (array), `alternate`, `abstract`.
  - **documents** (total 6): `pk`, `title`, `detail_url`, `thumbnail_url`, `mime_type`, `extension`, `href` (download).
  - **categories** (total 27): kategori Indonesia hasil seed — `identifier`, `gn_description`, `is_choice`, `fa_class`, `count`.
  - **regions** (total 811): termasuk `IDN-*` hasil seed.
- **Tanpa CORS config** di project settings → fetch lintas-origin dari browser berisiko. **Dihindari** dengan SSR: container `frontend` & GeoNode satu network (`gn_frontend_default`), dan `http://django:8000/api/v2/...` **terbukti reachable** dari container frontend.
- Route detail kustom project tersedia: `dataset/<pk>/` dan `dokumen/<pk>/` (lihat `src/geonode_project/urls.py`) — dipakai untuk link publik agar konsisten dengan UX lama.
- Semua URL hardcoded hanya ada di `page.tsx` (layout/globals bersih).

## Arsitektur

```
Browser ──HTML(SSR)──▶ Next server (frontend container)
                          │  fetch ${GEONODE_INTERNAL_URL}/api/v2/...  (http://django:8000, server-only, no CORS)
                          ▼
                        GeoNode API v2
HTML berisi link/gambar absolut ke ${NEXT_PUBLIC_GEONODE_URL} (http://localhost) → browser memuat langsung
```

Dua base URL:
- `GEONODE_INTERNAL_URL` (server-only, default `http://django:8000`) — untuk SSR fetch data.
- `NEXT_PUBLIC_GEONODE_URL` (default `http://localhost`) — untuk link & `<img>` yang dimuat browser. Karena render server-side, dibaca `process.env` saat request (runtime-configurable, tidak perlu rebuild).

## Perubahan file

### Baru
- **`frontend/src/lib/config.ts`** — accessor env + pembangun URL:
  - `INTERNAL_BASE` = `process.env.GEONODE_INTERNAL_URL ?? "http://django:8000"`
  - `PUBLIC_BASE` = `process.env.NEXT_PUBLIC_GEONODE_URL ?? "http://localhost"`
  - helper: `datasetUrl(pk)`, `documentUrl(pk)`, `publicAsset(path)` (mis. `/static/dst-district/img/...`, `/uploaded/...`), `rewriteHostToPublic(absoluteUrl)` (ganti host `thumbnail_url`/`detail_url` dari SITEURL internal → `PUBLIC_BASE` bila berbeda).
- **`frontend/src/lib/geonode.ts`** — lapisan data ber-tipe (server-only), tiap fungsi `fetch(`${INTERNAL_BASE}/api/v2/...`, { next: { revalidate: 60 }, headers: { Accept: "application/json" } })` dengan try/catch → fallback array kosong (halaman tak pernah crash bila GeoNode down):
  - `getDatasets()`, `getDocuments()`, `getCategories()` (hanya `is_choice` utk Layanan/filter), `getRegions()`/`getRegionFacet()`.
  - Tipe ringkas: `DatasetItem`, `DocumentItem`, `CategoryItem`, `RegionItem`, ter-normalisasi ke field yang dipakai UI + URL publik sudah dibangun.
- **`frontend/src/app/LandingClient.tsx`** — `"use client"`. Berisi **seluruh JSX & hooks interaktif** yang sekarang ada di `page.tsx` (navbar, hero carousel, accordion, state `filters`, handler). Menerima props `initialData` (datasets, documents, categories, regionFacet, stats).

### Diubah
- **`frontend/src/app/page.tsx`** — jadi `async` **Server Component**: panggil fungsi di `geonode.ts` secara paralel (`Promise.all`), susun `initialData`, render `<LandingClient initialData={...} />`. Hapus `"use client"` dan semua array hardcoded yang kini datang dari API.
- **`docker-compose.yml`** (root) — pada service `frontend` tambah:
  ```yaml
  environment:
    - HOSTNAME=0.0.0.0
    - GEONODE_INTERNAL_URL=http://django:8000
    - NEXT_PUBLIC_GEONODE_URL=http://localhost
  depends_on:
    django:
      condition: service_healthy
  ```
- **`frontend/Dockerfile`** — (opsional) terima `ARG NEXT_PUBLIC_GEONODE_URL` + `ENV` agar nilai build-time tersedia bila ada referensi `NEXT_PUBLIC_*` di komponen client. Karena base dipakai server-side, ini hanya jaring pengaman.
- **`frontend/.gitignore`** sudah mengabaikan `.env*.local`; tambah **`frontend/.env.example`** mendokumentasikan kedua variabel.

## Detail per implikasi

### (a) URL berbasis env — ganti hardcode `luwu.folur-dst.net`
- Semua link aksi (`Jelajahi Dokumen`, `Eksplorasi Dataset`, `Detail →`, footer) → `documentUrl(pk)` / `datasetUrl(pk)` / `publicAsset(...)` dari `config.ts`.
- Aset statis GeoNode (ikon folur-*.svg, layanan, indikator) & `uploaded/partners`, `uploaded/komoditas`, `uploaded/thumbs` → `publicAsset("/static/dst-district/img/...")` / `publicAsset("/uploaded/...")`. Di lokal mengarah ke nginx `http://localhost` (project sama → file tersedia).
- `thumbnail_url`/`detail_url` dari API sudah absolut ke SITEURL (`http://localhost`) → pakai apa adanya, atau `rewriteHostToPublic` bila `PUBLIC_BASE` ≠ localhost.

### (b) Data nyata dari API v2
- **Stat strip**: "Dokumen Kebijakan" = `documents.total`; "Layer Spasial" = `datasets.total`; "Screening Tools" tetap statis (1, tak ada di API); "Komoditi Unggulan" tetap statis untuk fase ini (lihat Out-of-scope).
- **Repositori → Dokumen kebijakan**: tabel `DOKUMEN_ROWS` diganti map `initialData.documents` (tahun dari `date`, tipe dari `subtype`/`mime`, judul `title`, link `documentUrl(pk)`).
- **Repositori → Katalog & Eksplorasi Dataset**: kartu di-generate dari `initialData.datasets` (judul, `thumbnail_url`, `subtype`→fitur, `detail_url`, EPSG/`alternate`).
- **Layanan Data**: di-generate dari `categories` ber-`is_choice=true` (label `gn_description`, ikon `fa_class`, link `${PUBLIC}/jelajah-dokumen/?kategori=${identifier}`, badge `count`).
- Caching: `revalidate: 60` → landing mencerminkan dokumen/dataset baru dalam ≤60 detik tanpa rebuild.

### (c) Filter berfungsi (Eksplorasi Dataset)
- Karena jumlah dataset kecil (4), **filter sisi-klien** atas `initialData.datasets` sudah cukup & responsif.
- Tiap dataset diberi atribut turunan: `kategori` (`category.identifier`), `fitur` (`subtype`/geometry), `wilayah` (`regions[].code` atau nama), `walidata` (dari `poc`/owner organization — *keterbatasan diketahui*: bila tak ada, kelompok Walidata di-derive seadanya atau disembunyikan).
- Daftar checkbox **Kategori/Fitur/Wilayah** + angka count di-derive dari kumpulan dataset (bukan hardcode). State `filters` yang sudah ada dipakai menghitung `visibleDatasets`; teks "Menampilkan X dari Y" jadi dinamis; tombol Reset tetap.
- Bila ke depan data membesar, fungsi `getDatasets(params)` sudah siap dipanggil dengan `filter{...}` server-side (path peningkatan, tidak dikerjakan sekarang).

## Out-of-scope (follow-up opsional)
- **Komoditas, Indikator Strategis, Implementing Partners** masih dari model project (bukan API v2). Untuk membuatnya dinamis perlu endpoint JSON project kecil (mis. tambah `path("api/landing/", ...)` di `geonode_project/urls.py` mengembalikan komoditas/indikator/partner). Disarankan sebagai fase 2; saat ini tetap statis.
- **Pencarian** (search box) — saat ini dekoratif; menyambungkannya ke `/api/v2/search` bisa jadi follow-up.

## Verifikasi (end-to-end)
1. Build & jalankan: `docker compose up -d --build frontend`.
2. `curl -s http://localhost:3000 | Select-String "Layer Spasial|Dokumen Kebijakan"` → angka cocok API (4 dataset, 6 dokumen).
3. Gunakan preview tools: `preview_start` → `preview_snapshot` memastikan dokumen/dataset nyata muncul; `preview_click` pada checkbox filter Kategori/Fitur lalu `preview_snapshot` → grid dataset benar-benar menyusut; cek `preview_console_logs` **tanpa** error CORS (fetch server-side).
4. Konfirmasi link: kartu dataset → `http://localhost/dataset/<pk>/`, dokumen → `http://localhost/dokumen/<pk>/`.
5. Uji ketahanan: hentikan sementara `django`, reload frontend → halaman tetap render (fallback kosong), tidak crash.
6. (Opsional) Uji fleksibilitas env: domain target sudah `localhost`, namun mekanisme tetap bisa di-switch — set `NEXT_PUBLIC_GEONODE_URL` ke nilai lain, recreate, pastikan link/gambar ikut berubah tanpa ubah kode.

## Catatan risiko
- **Domain sudah pasti `localhost`** (= `SITEURL` di `.env`). Konsekuensinya:
  - `rewriteHostToPublic()` praktis **no-op** untuk skenario lokal (host API sudah `http://localhost`). Tetap disertakan sebagai jaring pengaman bila kelak `NEXT_PUBLIC_GEONODE_URL` diubah ke domain lain, tapi **tidak diperlukan** untuk jalan sekarang.
  - Karena render server-side + nilai env tetap `localhost`, isu `NEXT_PUBLIC_*` build-time vs runtime **tidak berdampak** pada kasus ini (HTML SSR memuat URL absolut `http://localhost/...` apa adanya).
- Filter "Walidata" tak punya padanan langsung di API v2 (konsep project) — diberi derivasi terbaik (dari `poc`/owner) atau ditandai sebagai keterbatasan.
- `revalidate: 60` berarti perubahan tidak instan (≤60 dtk); bisa diturunkan bila perlu.
- **Aset `/uploaded/...` (thumbnail, logo mitra, foto komoditas) hanya tampil bila ada di GeoNode lokal.** Beberapa kini menunjuk file di situs prod; di lokal sebagian bisa 404 hingga di-upload. Disediakan fallback (placeholder/`onError`) agar UI tetap rapi.