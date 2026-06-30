# Rencana: Sinkronisasi Data Intervensi Pengelolaan Lahan Lintas Yurisdiksi

> Tujuan besar: satu intervensi yang sama (mis. "tanam kakao", "ujicoba insektisida
> alami") terlihat tersinkron **lintas yurisdiksi** — Desa → Kecamatan → Kabupaten —
> lengkap dimensi waktu (tahunan + kumulatif). Dibagi **3 tahap mandiri & dapat
> diverifikasi sendiri**, supaya pekerjaan bisa berhenti/lanjut rapi antar sesi.

Status: **2026-06-08 — Tahap 1, 2, 3 SELESAI & terverifikasi.** (Tahap 1 mode = A non-destruktif.)
Migration: `0058_folurindikator_sumber_agregat`. Detail implementasi ada di git history.
**Juga sudah dibangun**: layanan API per-kabupaten `/api/folur/capaian/` (API key PIN, blok
Sitroom, daftar komoditas) — lihat bagian "Layanan API per-kabupaten". **Berikutnya
(rancangan)**: Tahap 4 — Endpoint Agregat DST Nasional (di bawah).

---

## 0. Konteks arsitektur (jangkar kode — supaya sesi baru tak perlu eksplor ulang)

**Model** (`src/geonode_project/models.py`)
- `FolurIndikator` — `kode, nama, pilar, satuan, target, arah(naik/turun), agregasi(tahunan/kumulatif), palet, sumber(manual/auto), auto_key, aktif`. Punya `PILAR_CHOICES / ARAH_CHOICES / AGREGASI_CHOICES / PALET_CHOICES`. Registry warna: `WEBGIS2_PALETTES`.
- `FolurCapaian` — agregat **Kabupaten** per tahun. `unique(indikator, tahun)`; field `nilai, catatan`.
- `FolurCapaianWilayah` — per **Desa/Kecamatan**. `unique(indikator, level, kode_pum, tahun)`; field `level(desa|kecamatan), kode_pum, nama, tahun, nilai, kegiatan`.
- `RefWilayahDesa` / `RefWilayahKecamatan` (schema `wilayah`) — `geom, kode_pum, kode_bps, nama` + desa: `kode_kec_pum, kode_kab_pum, nama_kec, nama_kab`; kec: `kode_kab_pum, nama_kab`. (Hanya cakupan aktif; di-truncate tiap restore region.)

**Views** (`src/geonode_project/views.py`)
- `build_folur_kpis(periode)` — dipakai Sitroom & Capaian Publik. Baca `FolurCapaian`. Sudah hormati `agregasi` (kumulatif = Σ≤periode) + ekspos per-kpi: `nilai, persen, agregasi, kum_nilai, kum_years, spark, ...` + `folur_years`.
- `compute_folur_auto_kpis(identity)` — KPI sumber=auto.
- `CapaianView` (Sitroom, `dst_auth:capaian`) — baca `?tahun=`.
- `CapaianPublikView` (`dst:capaian_publik`).
- `WebGis2View` (`dst:webgis2`) — `config`: `geojsonUrl, historyUrl, center, bbox, tahun, years, level("desa"), nKec, nDesa, cakupanNama, indikator[]`. Tiap `indikator[]`: `kode,nama,satuan,target,arah,agregasi,palet,ramp,aggSeries[{tahun,nilai}],agg,agg_tahun`. `aggSeries` = Σ nilai semua desa per tahun (level **desa** saja saat ini).
- `webgis2_geojson(request)` — param `level, tahun`; geometri di-cache (key versi `count+max(updated_at)`); nilai+kegiatan disuntik segar; **kumulatif** (Σ≤tahun) bila `indikator.agregasi=="kumulatif"`. Properti fitur: `kode_pum, nama, nama_kec, nilai{kode:val}, kegiatan{kode:txt}`.
- `webgis2_desa_history(request)` — param `level, kode_pum`; balikan `series{kode_indikator:[{tahun,nilai,kegiatan}]}`.
- `DataCapaianView` (`dst_auth:data_capaian`) — CRUD indikator (`kpi_save` baca `palet,agregasi`), entri realisasi tahunan (`kpi_capaian_save` → FolurCapaian), entri **per wilayah** (`kpi_wilayah_save` → FolurCapaianWilayah; context `wil_rows` punya selector Jenjang desa/kecamatan + kolom Kegiatan).

**Templates** (`src/geonode_project/templates/dst-district/`)
- `webgis2.html` — JS: `state{kode,tahun,geojson,layer,cls,selected,selKode,history}`, `RAMP/DEFAULT_RAMP`, `loadData(fit)`, `render()`, `renderHero/renderLegend/renderRanking/renderSelected/renderHistory(kode)`, `ensureHistory`, pemilih `#yearSel`, pills `#indPills`, hero `#heroCum`.
- `admin/capaian.html` — kartu KPI Sitroom (`cap-card`, baris "Σ Realisasi kumulatif").
- `admin/data_capaian.html` — form indikator (`kpi_save`, dropdown swatch palet + selector Agregasi) + panel "Capaian per Wilayah" (`#wilayah`).
- `landing/partials/_capaian_folur.html` — Capaian Publik (CTA ke webgis2).

**URLs** (`src/geonode_project/urls.py`): `dst:` (publik) & `dst_auth:` (admin).

**Operasional**: container `django4geonode_folurian` (source bind-mount). Template = auto-reload (loader bukan cached). **Edit `.py` → wajib `docker restart django4geonode_folurian`**. Migration: `docker exec ... python manage.py makemigrations geonode_project && migrate`. Cache = **LocMemCache per-proses**. Migration terakhir: `0058_folurindikator_sumber_agregat`.

---

## TAHAP 1 — Roll-up otomatis lintas yurisdiksi (LEVER UTAMA "sinkronisasi")

**Masalah**: angka Kabupaten (`FolurCapaian`) diisi **terpisah** dari data Desa
(`FolurCapaianWilayah`) → tidak sinkron (CI1 pernah 400 di Sitroom vs 55 di webgis2).

**Tujuan**: angka Kabupaten **bisa dihitung** dari Σ data Desa → satu sumber kebenaran;
entri desa otomatis menyegarkan total kecamatan & kabupaten.

**Keputusan desain (rekomendasi: NON-DESTRUKTIF, per-indikator)**
- Tambah `FolurIndikator.sumber_agregat` = `manual` (pakai `FolurCapaian`, default → perilaku lama)
  | `roll_up` (hitung dari Σ `FolurCapaianWilayah` level desa).
- *Alternatif yang HARUS dikonfirmasi ke user sebelum mulai*: (a) roll-up sebagai
  **tampilan** saja (entri manual tetap ada, hanya tak dipakai saat roll_up) — rekomendasi;
  (b) roll-up **menggantikan** entri manual (sembunyikan form realisasi tahunan saat roll_up).

**Langkah**
1. **Helper** `folur_rollup_series(indikator, level="desa")` di `views.py` → `{tahun: Σnilai}`
   dari `FolurCapaianWilayah.filter(indikator,level).values('tahun').annotate(Sum('nilai'))`.
   (Mirip `agg_series` yang sudah ada di `WebGis2View`; pertimbangkan ekstrak jadi util bersama.)
2. **Model**: `sumber_agregat = CharField(choices, default="manual")` + `SUMBER_AGREGAT_CHOICES`.
   Migration `0058_folurindikator_sumber_agregat`.
3. **`build_folur_kpis`**: bila `ind.sumber_agregat=="roll_up"` → `nilai`/`kum_nilai`/`kum_years`
   dihitung dari `folur_rollup_series` (hormati `agregasi`: tahunan=snapshot tahun, kumulatif=Σ≤periode),
   bukan dari `FolurCapaian`. `spark` juga dari series roll-up.
4. **Admin Data Capaian**:
   - Form indikator: tambah selector "Sumber agregat" (manual/roll_up) di `kpi_save` + handler.
   - Panel "Realisasi tahunan" (`FolurCapaian`): bila roll_up → tampilkan **read-only/terhitung**
     dengan catatan "dihitung dari data per-wilayah" (jangan hapus data manual lama).
5. **Konsistensi**: untuk indikator roll_up, Sitroom = hero webgis2 = Σ desa (selisih hilang).
6. **Verifikasi**:
   - Set 1 indikator → roll_up; entri 2–3 desa lintas tahun.
   - `build_folur_kpis(periode)` → nilai = Σ desa; bandingkan dengan `webgis2` hero (harus sama).
   - Indikator lain (manual) tak berubah. Snapshot+restore data uji.

**File**: `models.py` (+field, +migration 0058), `views.py` (+helper, build_folur_kpis,
DataCapaianView.kpi_save + context), `admin/data_capaian.html` (selector + panel read-only).
**Ukuran**: sedang. **Dependensi**: tak ada (fondasi). **Risiko**: pastikan default `manual`
agar indikator lama tak berubah; auto-indikator (`sumber=auto`) tak terpengaruh.

---

## TAHAP 2 — Pengalih Yurisdiksi Desa ↔ Kecamatan di webgis2

**Tujuan**: peta + panel webgis2 bisa di jenjang **Kecamatan** (data & endpoint sudah siap;
UI masih kunci `level="desa"`).

**Langkah**
1. **`WebGis2View`**: 
   - `config.levels` = `["desa"]` + `"kecamatan"` bila `RefWilayahKecamatan` ada isinya.
   - `aggSeries` jadi **per-level**: `aggSeriesByLevel = {desa:{kode:[...]}, kecamatan:{kode:[...]}}`
     (Σ nilai per tahun untuk tiap level). Sisipkan ke tiap `indikator[]` sebagai
     `aggSeries: {desa:[...], kecamatan:[...]}` (UBAH struktur — sesuaikan `renderHero`).
   - `nDesa`/`nKec` sudah ada; pakai sesuai level aktif untuk statgrid.
2. **`webgis2.html`**:
   - Tambah toggle **Desa | Kecamatan** dekat `#yearSel` (mis. `#levelSel`).
   - `state.level` (default `"desa"`); on change → `state.level=...; loadData(true)` (fit ulang).
   - `loadData` & `ensureHistory` kirim `level=state.level` (sudah ada param di endpoint).
   - `renderHero` baca `m.aggSeries[state.level]`. Label statgrid "Desa/Kecamatan Terisi".
   - `tipText/renderSelected/renderHistory` sudah generik (pakai properties) — cek `nama_kec`
     hanya relevan untuk desa (sembunyikan utk kecamatan).
3. **Verifikasi**: toggle ke Kecamatan → choropleth 22 kecamatan, klik → riwayat tahunan
   kecamatan, hero kumulatif benar. Toggle balik ke Desa tetap jalan.

**File**: `views.py` (WebGis2View: levels + aggSeries per-level), `webgis2.html` (toggle + JS level).
**Ukuran**: sedang. **Dependensi**: independen dari Tahap 1 (boleh duluan). **Risiko**:
ubah struktur `aggSeries` → update `renderHero` Tahap-sebelumnya; pastикан geojson kecamatan
ada (RefWilayahKecamatan terisi saat region di-restore).

---

## TAHAP 3 — Breadcrumb hierarki yurisdiksi (Kabupaten ▸ Kecamatan ▸ Desa)

**Tujuan**: navigasi turun/naik jenjang — klik kecamatan → lihat desa-desanya;
breadcrumb menampilkan jalur; statistik (hero/ranking) ikut ter-scope.

**Langkah**
1. **Properti**: tambah `kode_kec_pum` ke properti fitur **desa** di `webgis2_geojson`
   (sudah ada `nama_kec`; tambah kode utk filter andal).
2. **`webgis2.html`**:
   - Bar breadcrumb: `Kabupaten {cakupanNama} ▸ Kec. {nama} ▸ Desa {nama}`.
   - Dari level Kecamatan, klik 1 kecamatan → **drill**: pindah ke level Desa **terfilter**
     ke kecamatan itu (filter `state.geojson.features` by `kode_kec_pum`, atau muat ulang +
     filter klien), zoom ke bounds-nya.
   - Hero/ranking/statgrid dihitung dari subset fitur terfilter (scope kecamatan).
   - Klik segmen breadcrumb → naik (Desa→Kecamatan→Kabupaten/penuh).
3. **Verifikasi**: drill kabupaten→kecamatan→desa; angka hero/ranking sesuai subset;
   breadcrumb naik/turun benar.

**File**: `views.py` (geojson: +`kode_kec_pum`), `webgis2.html` (breadcrumb + filter/scope + zoom).
**Ukuran**: lebih besar (UX & scoping). **Dependensi**: paling baik **setelah Tahap 2**
(butuh level Kecamatan). **Risiko**: konsistensi scoping (hero/ranking/legend pakai subset
yang sama); performa filter klien (227 desa → ringan).

---

## Urutan & catatan eksekusi
- **Disarankan**: Tahap 1 → 2 → 3. (1 = nilai bisnis tertinggi & fondasi konsistensi;
  3 bergantung pada 2.) Tahap 2 boleh didahulukan bila ingin cepat lihat jenjang kecamatan.
- Tiap tahap: **edit → (jika .py) restart container → uji test-Client/curl dengan data uji →
  snapshot+restore (JANGAN tinggalkan data palsu) → laporkan**.
- Selalu `makemigrations --check`/migrate bersih; migration baru masuk repo.
- Sebelum mulai **Tahap 1**, konfirmasi ke user: roll-up *tampilan saja* (rekomendasi) vs
  *menggantikan* entri manual.

## Verifikasi akhir (definisi "selesai")
Satu indikator roll_up: entri data **desa** → otomatis tampil benar & **konsisten** di
webgis2 (desa & kecamatan, dengan breadcrumb), Sitroom, dan Capaian Publik — Σ desa = Σ
kecamatan = angka kabupaten, untuk tahun terpilih maupun kumulatif.

---

## Layanan API per-kabupaten (SUDAH dibangun — fondasi agregasi nasional)

Endpoint **read-only** (GET, tanpa CRUD), butuh **API key (PIN)**:
```
GET /api/folur/capaian/?api_key=<pin>        (default PIN 123456; override env DST_CAPAIAN_API_KEY)
    &tahun=YYYY            filter realisasi 1 tahun
    &indikator=CI4,CI1     subset indikator
    &wilayah=desa|kecamatan  rincian per-wilayah (nilai + kegiatan per tahun)
```
Auth: header `X-API-Key` (disarankan) / query `?api_key=`/`?pin=` / `Authorization: ApiKey <pin>`.

Payload (v1.1) — **siap diagregasi**: `kabupaten{kode_kab,...}` (kunci sumber),
`indikator[]{kode,satuan,target,realisasi_tahunan,realisasi_terbaru,realisasi_kumulatif,
persen_capaian,agregasi,sumber_agregat}`, `komoditas[]` (daftar nama), `sitroom{auto{
luas_bentang_ha,jml_kecamatan,jml_desa,persen_desa_maju,idm_rata2,...}, ringkasan{
total_indikator,terisi,pilar[]}}`. `kode_pum` bertitik = hierarki yurisdiksi.

**Jangkar kode**: `_capaian_api_key_ok(request)`, `folur_realisasi_series(ind)` (hormati
roll-up), `api_capaian_folur(request)` di `views.py`; URL `dst:api_capaian_folur`
(`/api/folur/capaian/`); setting `DST_CAPAIAN_API_KEY`; terdaftar di katalog `EndpointApiView`.

---

## TAHAP 4 (RANCANGAN) — Endpoint Agregat DST Nasional

**Konteks**: akan ada **5 DST kabupaten**, tiap instans mengekspos
`/api/folur/capaian/?api_key=<pin>` (di atas). **DST Nasional perlu SATU endpoint yang
menarik & menjumlahkan ke-5 kabupaten otomatis** (mis. agregat komoditas nasional, total
hutan lindung [CI1] terkelola, luas bentang lahan, dll).

> **Penting**: endpoint agregat ini **hidup di instans DST Nasional** (deployment terpisah),
> **bukan** di instans kabupaten. Kabupaten = *sumber data*; Nasional = *agregator*. Tidak ada
> perubahan kode di kabupaten (cukup pastikan endpoint + API key aktif & dapat dijangkau).

**Rancangan komponen (di instans Nasional)**
1. **Registry node** — model `DstKabupatenNode`: `nama, kode_kab, base_url, api_key (secret),
   aktif, last_sync, last_status`. Dikelola di Admin Nasional ("Node Kabupaten").
2. **Harvest (Celery)** — task `harvest_dst_nodes`: iterasi registry → `GET {base_url}/api/folur/
   capaian/` (header `X-API-Key`), simpan **snapshot** mentah per node (model `DstNodeSnapshot`
   atau cache) + timestamp. Timeout per-node; node gagal → pakai snapshot terakhir + tandai *stale*.
   Jadwal via Celery beat + tombol "Harvest sekarang" di admin.
3. **Endpoint agregat** `GET /api/nasional/agregat/` (read-only, **auth sendiri** — API key/OAuth2
   untuk konsumen kementerian). Menghitung dari snapshot terbaru:
   - **Per indikator (kode)**: Σ `realisasi_terbaru.nilai` + deret per-tahun + kumulatif lintas
     kabupaten; **cek konsistensi `satuan`** (mismatch → *flag*, jangan diam-diam dijumlah);
     `n_kabupaten_melapor`; `breakdown[]` per kabupaten `{kode_kab, nilai}`.
   - **Komoditas nasional**: union + **frekuensi** (komoditas X dipakai di N kabupaten) dari `komoditas[]`.
   - **Luas bentang nasional**: Σ `sitroom.auto.luas_bentang_ha`. **Cakupan**: Σ `jml_desa/jml_kecamatan` + jumlah kabupaten.
   - **Tren nasional**: Σ per tahun lintas kabupaten.
   - **Metadata**: `generated_at`, daftar node (sukses/gagal/stale), umur snapshot.
4. **Penyajian**: dashboard/peta nasional (choropleth per kabupaten, drilldown ke kabupaten →
   reuse pola webgis2) memanggil endpoint agregat ini.

**Prasyarat (SUDAH terpenuhi di sisi kabupaten)**: `kode_kab` kunci unik · kode indikator stabil
(CI1/CI3/CI4/CI11) · nilai numerik + `satuan` · `komoditas[]` bersih · `kode_pum` hierarkis.

**Tata kelola (wajib agar Σ bersih)**: master registry indikator dari **pusat** (kode + satuan
seragam di ke-5 kabupaten) + *unit guard* di agregator. Transport **HTTPS**; key per-node disimpan
sebagai secret.

**Resilience**: agregasi **parsial** bila sebagian node down (laporkan node gagal); cache last-good.

**File (nanti, di instans Nasional)**: model registry/snapshot + migration · Celery task harvest ·
view agregat + URL · admin node. **Ukuran**: sedang–besar. **Risiko**: jaringan antar-instans,
keamanan key, harmonisasi satuan/kode.
