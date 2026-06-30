# Konversi dst-district HTML ke Django Templates + Static

## Context

Direktori `src/geonode_project/templates/dst-district/` saat ini berisi 12 file HTML "skrip" prototipe (total ~13.500 baris) untuk DST Kabupaten Luwu FOLUR. Tiap file adalah HTML standalone dengan `<style>` dan `<script>` inline + Google Fonts dari CDN. Tujuan konversi:

1. **Pertahankan dua tipe halaman**: landing page publik (1 file) dan panel admin (11 file).
2. **Konversi ke Django template** dengan inheritance (`{% extends %}`) dan partial (`{% include %}`) untuk hilangkan duplikasi sidebar/topbar/page-header (~40% redundansi antar file admin).
3. **Pisahkan CSS & JS** ke `src/geonode_project/static/dst-district/` sehingga template HTML jadi ramping.
4. **Wiring URL + views** supaya halaman langsung bisa dibuka via browser (auth belum dipasang).

Klasifikasi hasil eksplorasi:
- **Landing (publik):** `index.html`
- **Admin:** `dashboard.html`, `dokumen.html`, `dokumen-baru.html`, `dokumen-detail.html`, `data-spasial.html`, `layer-baru.html`, `layer-detail.html`, `layer-edit.html`, `akses-nasional.html`, `endpoint-api.html`, `metadata-schema.html`

CSS landing & admin berbagi token (`--forest`, `--cream`, `--ochre`) + font (`Fraunces`, `Geist`, `Geist Mono`); admin menambah `--paper`, `--success`, `--warning`, `--danger`, `--info`.

## Keputusan Desain

- **CSS:** 3 file gabungan — `base.css` (token, reset, typography, font import), `landing.css`, `admin.css`. Disesuaikan via prefix/scope selector di tiap file gabungan agar tidak bentrok.
- **JS:** 2 file gabungan — `landing.js`, `admin.js`. Tiap halaman admin gating per-section pakai `data-page="<slug>"` di `<body>` sehingga handler tahu konteks halamannya.
- **Routing:** Tambahkan `views.py` (TemplateView) + URL patterns ke `urls.py` lokal. Belum ada `@login_required`.
- **Partial template:** Ekstrak `partials/_sidebar.html`, `_topbar.html`, `_page_header.html` untuk dipakai semua halaman admin.

## Struktur Target

```
src/geonode_project/
├── views.py                                          # BARU
├── urls.py                                           # MODIF (tambah custom patterns)
├── templates/dst-district/
│   ├── base.html                                     # BARU — <html>, <head>, fonts, base.css, {% block %}
│   ├── landing/
│   │   ├── base.html                                 # BARU — extends ../base.html, load landing.css/js
│   │   └── index.html                                # KONVERSI dari index.html lama
│   └── admin/
│       ├── base.html                                 # BARU — extends ../base.html, include sidebar+topbar, load admin.css/js
│       ├── partials/
│       │   ├── _sidebar.html                         # BARU
│       │   ├── _topbar.html                          # BARU
│       │   └── _page_header.html                     # BARU
│       ├── dashboard.html
│       ├── dokumen.html
│       ├── dokumen_baru.html
│       ├── dokumen_detail.html
│       ├── data_spasial.html
│       ├── layer_baru.html
│       ├── layer_detail.html
│       ├── layer_edit.html
│       ├── akses_nasional.html
│       ├── endpoint_api.html
│       └── metadata_schema.html
└── static/dst-district/
    ├── css/
    │   ├── base.css       # :root tokens, reset, typography, topo background
    │   ├── landing.css    # semua style dari index.html (832 baris)
    │   └── admin.css      # gabungan style dari 11 file admin (~5500 baris)
    └── js/
        ├── landing.js     # interaksi index.html (~5 baris)
        └── admin.js       # gabungan handler 11 file admin (~110 baris, dispatch via data-page)
```

File lama 12 HTML dipindah keluar `templates/` (dihapus setelah verifikasi, atau dipindah ke `_legacy/` untuk referensi diff).

## Langkah Eksekusi

### 1. Inventaris (read-only)
- Baca seluruh `index.html`, `dashboard.html` lengkap untuk validasi awal struktur sidebar/topbar.
- Diff sidebar/topbar antar 3 file admin (mis. `dashboard.html`, `dokumen.html`, `data-spasial.html`) untuk konfirmasi benar-benar identik. Kalau ada perbedaan kecil (e.g. item aktif), tangani via `active_page` context variable.

### 2. Buat skeleton CSS (kosong dulu)
- `static/dst-district/css/base.css` — token `:root`, `*` reset, `body`, `html`, font import via `@import` dari Google Fonts.
- `static/dst-district/css/landing.css` — kosong.
- `static/dst-district/css/admin.css` — kosong.
- `static/dst-district/js/landing.js`, `js/admin.js` — kosong.

### 3. Konversi landing (index.html)
1. Ekstrak `<style>` index.html → split: token shared ke `base.css`, sisanya ke `landing.css`.
2. Ekstrak `<script>` → `landing.js`.
3. Buat `templates/dst-district/base.html`:
   - `{% load static %}` di atas
   - `<head>` dengan `<title>{% block title %}{% endblock %}</title>`, font preconnect, `<link rel="stylesheet" href="{% static 'dst-district/css/base.css' %}">`
   - `{% block extra_css %}{% endblock %}`
   - `<body data-page="{% block page_slug %}{% endblock %}">`
   - `{% block content %}{% endblock %}`
   - `<script src="{% static 'dst-district/js/base.js' %}" defer></script>` (opsional)
   - `{% block extra_js %}{% endblock %}`
4. Buat `templates/dst-district/landing/base.html`:
   - `{% extends 'dst-district/base.html' %}`
   - `{% block extra_css %}<link rel="stylesheet" href="{% static 'dst-district/css/landing.css' %}">{% endblock %}`
   - `{% block extra_js %}<script src="{% static 'dst-district/js/landing.js' %}" defer></script>{% endblock %}`
5. Buat `templates/dst-district/landing/index.html`:
   - `{% extends 'dst-district/landing/base.html' %}`
   - Pindahkan markup `<body>...</body>` dari index.html lama ke `{% block content %}`.
   - Ganti link antar halaman jadi `{% url 'dst:dashboard' %}` dst.

### 4. Konversi admin shell + partials
1. Identifikasi sidebar, topbar, page-header dari `dashboard.html` (paling representatif) sebagai template kanonik.
2. Buat `templates/dst-district/admin/partials/_sidebar.html` — gunakan variabel `{{ active_page }}` untuk menandai item aktif: `<a href="..." class="sb-nav-item {% if active_page == 'dokumen' %}is-active{% endif %}">`.
3. Buat `_topbar.html` — gunakan `{{ breadcrumb }}` (list of dict `{label, url}`) dan `{{ page_title }}`.
4. Buat `_page_header.html` — pakai blok `{% block page_header %}` opsional di tiap halaman.
5. Buat `templates/dst-district/admin/base.html`:
   - `{% extends 'dst-district/base.html' %}`
   - Load `admin.css` + `admin.js`.
   - Layout: `<div class="admin-shell">{% include 'dst-district/admin/partials/_sidebar.html' %}<main>{% include 'dst-district/admin/partials/_topbar.html' %}{% block admin_content %}{% endblock %}</main></div>`

### 5. Konversi 11 file admin (loop)
Untuk tiap file admin lama:
1. Ekstrak `<style>` → append ke `admin.css`, prefix dengan komentar `/* === <nama-file> === */`. Karena CSS gabungan, scope kelas yang konflik (mis. `.card` muncul beda di 2 file) via wrapper class `body[data-page="<slug>"] .card { ... }`.
2. Ekstrak `<script>` → bungkus dalam blok `if (document.body.dataset.page === '<slug>') { ... }` di `admin.js`.
3. Hapus sidebar+topbar dari markup (sudah ada di base).
4. Sisa markup (page-header + content) ditaruh di `{% block admin_content %}`.
5. Set `{% block page_slug %}<slug>{% endblock %}` dan tambahkan context `active_page`, `breadcrumb`, `page_title` lewat view.

### 6. URL + Views
- Buat `src/geonode_project/views.py`:
  ```python
  from django.views.generic import TemplateView

  class DstLandingView(TemplateView):
      template_name = "dst-district/landing/index.html"

  class DstAdminPageView(TemplateView):
      page_slug = ""
      page_title = ""
      breadcrumb = []
      def get_context_data(self, **kw):
          ctx = super().get_context_data(**kw)
          ctx.update(active_page=self.page_slug, page_title=self.page_title, breadcrumb=self.breadcrumb)
          return ctx

  class DashboardView(DstAdminPageView):
      template_name = "dst-district/admin/dashboard.html"
      page_slug = "dashboard"; page_title = "Dashboard"
  # ... satu kelas per halaman admin (11 total)
  ```
- Update `src/geonode_project/urls.py`:
  ```python
  from django.urls import path, include
  from geonode.urls import urlpatterns as geonode_urls, handler500  # noqa
  from . import views

  dst_patterns = ([
      path("", views.DstLandingView.as_view(), name="landing"),
      path("admin/dashboard/", views.DashboardView.as_view(), name="dashboard"),
      path("admin/dokumen/", views.DokumenView.as_view(), name="dokumen"),
      # ... 11 admin patterns
  ], "dst")

  urlpatterns = [path("dst/", include(dst_patterns))] + geonode_urls
  ```
- Tabel URL lengkap:
  | Path | View | Nama |
  |---|---|---|
  | `/dst/` | DstLandingView | dst:landing |
  | `/dst/admin/dashboard/` | DashboardView | dst:dashboard |
  | `/dst/admin/dokumen/` | DokumenView | dst:dokumen |
  | `/dst/admin/dokumen/baru/` | DokumenBaruView | dst:dokumen_baru |
  | `/dst/admin/dokumen/<id>/` | DokumenDetailView | dst:dokumen_detail (sementara `<id>` opsional di template; placeholder data) |
  | `/dst/admin/data-spasial/` | DataSpasialView | dst:data_spasial |
  | `/dst/admin/layer/baru/` | LayerBaruView | dst:layer_baru |
  | `/dst/admin/layer/<id>/` | LayerDetailView | dst:layer_detail |
  | `/dst/admin/layer/<id>/edit/` | LayerEditView | dst:layer_edit |
  | `/dst/admin/akses-nasional/` | AksesNasionalView | dst:akses_nasional |
  | `/dst/admin/endpoint-api/` | EndpointApiView | dst:endpoint_api |
  | `/dst/admin/metadata-schema/` | MetadataSchemaView | dst:metadata_schema |

  Karena auth belum dipasang, halaman detail/edit pakai placeholder data untuk demo; nanti tambahkan param `<int:pk>`.

### 7. Cleanup
- Setelah verifikasi visual semua halaman OK, hapus 12 file HTML lama di `templates/dst-district/` (root). PRD.md tetap dipertahankan sebagai referensi.

## File Kritis yang Akan Dimodifikasi / Dibuat

**Dibuat:**
- `src/geonode_project/views.py`
- `src/geonode_project/templates/dst-district/base.html`
- `src/geonode_project/templates/dst-district/landing/base.html`
- `src/geonode_project/templates/dst-district/landing/index.html`
- `src/geonode_project/templates/dst-district/admin/base.html`
- `src/geonode_project/templates/dst-district/admin/partials/_sidebar.html`
- `src/geonode_project/templates/dst-district/admin/partials/_topbar.html`
- `src/geonode_project/templates/dst-district/admin/partials/_page_header.html`
- `src/geonode_project/templates/dst-district/admin/{dashboard,dokumen,dokumen_baru,dokumen_detail,data_spasial,layer_baru,layer_detail,layer_edit,akses_nasional,endpoint_api,metadata_schema}.html`
- `src/geonode_project/static/dst-district/css/{base,landing,admin}.css`
- `src/geonode_project/static/dst-district/js/{landing,admin}.js`

**Dimodifikasi:**
- `src/geonode_project/urls.py` — tambah custom `dst_patterns` & `include`.

**Dihapus (setelah verifikasi):**
- 12 HTML lama di `templates/dst-district/*.html` (kecuali `PRD.md`).

## Settings yang Sudah Aman (tidak perlu diubah)

- `TEMPLATES[0]["DIRS"]` sudah memprioritaskan `LOCAL_ROOT/templates` ([settings.py:67](src/geonode_project/settings.py#L67)).
- `STATICFILES_DIRS` sudah include `LOCAL_ROOT/static` ([settings.py:60-62](src/geonode_project/settings.py#L60-L62)).
- `ROOT_URLCONF` sudah menunjuk `geonode_project.urls` ([settings.py:57](src/geonode_project/settings.py#L57)).

## Verifikasi End-to-End

1. **Static collect**: jalankan `python manage.py collectstatic --noinput --dry-run` untuk memastikan path `dst-district/css/*.css` & `dst-district/js/*.js` terdeteksi.
2. **Template syntax**: jalankan `python manage.py check` — harus 0 error.
3. **Run dev server** (atau gunakan Docker compose existing): `python manage.py runserver 0.0.0.0:8000`.
4. **Smoke test browser** — buka tiap URL berikut & verifikasi visual sama dengan HTML lama:
   - `http://localhost:8000/dst/` (landing)
   - `http://localhost:8000/dst/admin/dashboard/`
   - `http://localhost:8000/dst/admin/dokumen/`
   - `http://localhost:8000/dst/admin/dokumen/baru/`
   - `http://localhost:8000/dst/admin/data-spasial/`
   - ... (semua 12 URL)
5. **DevTools network tab**: pastikan `base.css`, `landing.css` ATAU `admin.css`, dan `landing.js`/`admin.js` di-load dari `/static/dst-district/...` dengan status 200 (tidak ada 404).
6. **Console JS**: tidak ada error; interaksi (toggle layer di landing, dropdown di admin, dll) tetap berfungsi sesuai HTML lama.
7. **Diff visual**: buka file lama (`dokumen.html` lewat `file://`) dan baru side-by-side; pastikan tidak ada regresi layout.
8. **Sidebar active state**: klik tiap menu sidebar, item aktif harus berpindah sesuai `active_page` context.

## Risiko & Mitigasi

- **CSS kelas konflik antar halaman admin** (mis. `.card` punya style berbeda di `dashboard.html` vs `data-spasial.html`). Mitigasi: scope dengan `body[data-page="<slug>"] .card { ... }` saat menggabung ke `admin.css`. Identifikasi konflik via grep selector duplikat saat ekstraksi.
- **Inline `<script>` mengandalkan DOM spesifik halaman**. Mitigasi: bungkus per-halaman di `admin.js` dengan guard `data-page`.
- **Font Google CDN di tiap file**: konsolidasi ke 1 `<link>` di `base.html`.
- **Link href lama** (mis. `href="dokumen-detail.html"`): cari-ganti dengan `{% url 'dst:...' %}` saat konversi tiap template; lakukan grep akhir untuk pastikan tidak ada `.html` href tersisa.


###############

# Restrukturisasi URL: DST sebagai homepage, GeoNode ke /gn/, admin DST ke /dst-auth/

## Context

Konversi DST HTML→Django Templates dari sesi sebelumnya sudah selesai (lihat git log). Saat ini routing di [src/geonode_project/urls.py](src/geonode_project/urls.py:47):

- `/` → seluruh GeoNode (warisi dari `geonode.urls`)
- `/dst/` → DST landing
- `/dst/admin/dashboard/` ... (11 path admin) → panel pengelola DST

User ingin restrukturisasi supaya DST menjadi entry-point utama:

- `/` → **DST landing page** (sebelumnya di `/dst/`)
- `/dst-auth/dashboard/`, `/dst-auth/dokumen/`, ... (11 path) → **DST admin** (sebelumnya `/dst/admin/...`)
- `/gn/` → **seluruh GeoNode** (sebelumnya di root)

Tujuan: positioning DST FOLUR sebagai produk publik utama, dengan GeoNode mentah disembunyikan di namespace teknis `/gn/` untuk pengelola yang butuh akses katalog/peta native.

## Risiko & Mitigasi

Memindahkan GeoNode dari root ke `/gn/` adalah perubahan besar dengan risiko medium-tinggi:

| Risiko | Dampak | Mitigasi |
|---|---|---|
| GeoNode template/middleware ber-hardcode `/account/`, `/admin/`, `/api/v2/...` sebagai path absolut | Login flow, navigasi, API discovery bisa rusak | Verifikasi setelah deploy; mungkin perlu set `LOGIN_URL=/gn/account/login/`, dll. di env |
| Sub-urlconf GeoNode pakai `re_path(r"^...")` (regex anchor) | Bisa salah-match di bawah prefix | Django umumnya menangani lewat `include()` — periksa via `manage.py show_urls` |
| Konsumer eksternal (DST Nasional yang harvest) hardcode `<SITEURL>/api/v2/...` | Endpoint berubah ke `<SITEURL>/gn/api/v2/...` | Beri tahu konsumer; alternatif: pasang redirect nginx untuk path lama |
| `/geoserver/` proxy nginx | TIDAK terdampak — proxy nginx di luar Django | — |
| `STATIC_URL` / `MEDIA_URL` absolut dari `SITEURL` | TIDAK terdampak | — |
| `SITEURL` di [.env](.env) saat ini `http://geonode-project-dst/` | Tetap utuh; URL absolut dibangun via env, bukan dari URL prefix | — |

Karena lingkungan ini staging/dev (SITEURL non-publik), risiko dapat diterima. Production butuh testing menyeluruh.

## Keputusan Desain

1. **Pisahkan namespace URL menjadi dua:**
   - `dst:` — hanya untuk landing publik (`dst:landing`)
   - `dst_auth:` — untuk 11 halaman admin (`dst_auth:dashboard`, `dst_auth:dokumen`, dll.)

   Alasan: Django `include()` tidak mendukung dua mount point untuk namespace yang sama. Memisahkan secara semantik juga lebih jelas: `dst:` = publik, `dst_auth:` = area authenticated (meskipun login_required belum dipasang).

2. **Path admin disederhanakan** karena tidak lagi nested di bawah `dst/admin/`:
   - `/dst-auth/dashboard/`, `/dst-auth/dokumen/`, `/dst-auth/dokumen/baru/`, `/dst-auth/dokumen/detail/`
   - `/dst-auth/data-spasial/`, `/dst-auth/layer/baru/`, `/dst-auth/layer/detail/`, `/dst-auth/layer/edit/`
   - `/dst-auth/akses-nasional/`, `/dst-auth/endpoint-api/`, `/dst-auth/metadata-schema/`

3. **Update semua `{% url 'dst:<admin_name>' %}` → `{% url 'dst_auth:<name>' %}`** di:
   - `templates/dst-district/admin/partials/_sidebar.html` (10 link admin)
   - `templates/dst-district/admin/dashboard.html` (quick-actions, harvest-action)
   - `templates/dst-district/admin/dokumen.html` (onclick row → dokumen_detail)
   - `templates/dst-district/admin/data_spasial.html` (onclick → layer_detail)
   - `templates/dst-district/landing/index.html` (footer "REST API" → endpoint_api, "Login Pengelola" → dashboard)
   - Sed pass: `{% url 'dst:dashboard' %}` → `{% url 'dst_auth:dashboard' %}` (dan 9 lainnya)

   `{% url 'dst:landing' %}` (dipakai di sidebar "Lihat Landing Page", footer landing brand, base.html nav) tetap tidak diubah.

4. **Update breadcrumb URLs di [views.py](src/geonode_project/views.py)** — semua `"/dst/admin/dashboard/"` → `"/dst-auth/dashboard/"`, `"/dst/admin/dokumen/"` → `"/dst-auth/dokumen/"`, `"/dst/admin/data-spasial/"` → `"/dst-auth/data-spasial/"`. Total 8 string-literal replacement.

## File Kritis yang Dimodifikasi

- [src/geonode_project/urls.py](src/geonode_project/urls.py) — restrukturisasi penuh urlpatterns
- [src/geonode_project/views.py](src/geonode_project/views.py) — breadcrumb URL constants
- [src/geonode_project/templates/dst-district/admin/partials/_sidebar.html](src/geonode_project/templates/dst-district/admin/partials/_sidebar.html) — namespace ref pada 10 link
- [src/geonode_project/templates/dst-district/admin/*.html](src/geonode_project/templates/dst-district/admin/) — 11 file, namespace ref
- [src/geonode_project/templates/dst-district/landing/index.html](src/geonode_project/templates/dst-district/landing/index.html) — namespace ref footer "REST API" & login

## Target State `urls.py`

```python
from django.urls import path, include
from geonode.urls import urlpatterns as geonode_urls, handler500  # noqa
from . import views

# Public DST landing (namespace 'dst')
dst_public_patterns = (
    [path("", views.DstLandingView.as_view(), name="landing")],
    "dst",
)

# DST admin/management area (namespace 'dst_auth')
dst_auth_patterns = (
    [
        path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
        path("dokumen/", views.DokumenView.as_view(), name="dokumen"),
        path("dokumen/baru/", views.DokumenBaruView.as_view(), name="dokumen_baru"),
        path("dokumen/detail/", views.DokumenDetailView.as_view(), name="dokumen_detail"),
        path("data-spasial/", views.DataSpasialView.as_view(), name="data_spasial"),
        path("layer/baru/", views.LayerBaruView.as_view(), name="layer_baru"),
        path("layer/detail/", views.LayerDetailView.as_view(), name="layer_detail"),
        path("layer/edit/", views.LayerEditView.as_view(), name="layer_edit"),
        path("akses-nasional/", views.AksesNasionalView.as_view(), name="akses_nasional"),
        path("endpoint-api/", views.EndpointApiView.as_view(), name="endpoint_api"),
        path("metadata-schema/", views.MetadataSchemaView.as_view(), name="metadata_schema"),
    ],
    "dst_auth",
)

urlpatterns = [
    path("", include(dst_public_patterns)),       # / → DST landing
    path("dst-auth/", include(dst_auth_patterns)), # /dst-auth/... → admin
    path("gn/", include(geonode_urls)),            # /gn/... → seluruh GeoNode
]
```

## Langkah Eksekusi

1. **Tulis ulang `urls.py`** sesuai template di atas.
2. **Update breadcrumb di `views.py`** — find/replace `"/dst/admin/"` → `"/dst-auth/"` (8 lokasi).
3. **Update template refs** — find/replace lewat `sed` di seluruh `templates/dst-district/`:
   - `{% url 'dst:dashboard' %}` → `{% url 'dst_auth:dashboard' %}`
   - `{% url 'dst:dokumen' %}` → `{% url 'dst_auth:dokumen' %}`
   - `{% url 'dst:dokumen_baru' %}` → `{% url 'dst_auth:dokumen_baru' %}`
   - `{% url 'dst:dokumen_detail' %}` → `{% url 'dst_auth:dokumen_detail' %}`
   - `{% url 'dst:data_spasial' %}` → `{% url 'dst_auth:data_spasial' %}`
   - `{% url 'dst:layer_baru' %}` → `{% url 'dst_auth:layer_baru' %}`
   - `{% url 'dst:layer_detail' %}` → `{% url 'dst_auth:layer_detail' %}`
   - `{% url 'dst:layer_edit' %}` → `{% url 'dst_auth:layer_edit' %}`
   - `{% url 'dst:akses_nasional' %}` → `{% url 'dst_auth:akses_nasional' %}`
   - `{% url 'dst:endpoint_api' %}` → `{% url 'dst_auth:endpoint_api' %}`
   - `{% url 'dst:metadata_schema' %}` → `{% url 'dst_auth:metadata_schema' %}`

   `{% url 'dst:landing' %}` tidak boleh ikut diganti — gunakan sed yang spesifik per nama.

4. **Verifikasi statis:**
   - `python3 -c "import ast; ast.parse(open('src/geonode_project/urls.py').read())"`
   - `grep -rn "{% url 'dst:" src/geonode_project/templates/dst-district/` → harus hanya muncul `dst:landing`.
   - `grep -rn "{% url 'dst_auth:" src/geonode_project/templates/dst-district/` → harus muncul untuk semua 11 admin names di template yang relevan.
   - `grep -rn "/dst/admin/" src/geonode_project/views.py` → harus 0 hasil.

## Verifikasi End-to-End (di container Docker)

1. **Restart django container**: `docker compose restart django`
2. **Health check**: `docker compose exec django python manage.py check`
3. **URL resolution**:
   ```bash
   docker compose exec django python -c "
   from django.urls import reverse
   print('landing:', reverse('dst:landing'))
   print('dashboard:', reverse('dst_auth:dashboard'))
   print('endpoint_api:', reverse('dst_auth:endpoint_api'))
   "
   ```
   Expected: `/`, `/dst-auth/dashboard/`, `/dst-auth/endpoint-api/`.

4. **HTTP smoke test** (host atau container):
   - `curl -I http://localhost/` → 200 (DST landing)
   - `curl -I http://localhost/dst-auth/dashboard/` → 200
   - `curl -I http://localhost/dst-auth/dokumen/baru/` → 200
   - `curl -I http://localhost/gn/` → 200 atau 302 (GeoNode homepage)
   - `curl -I http://localhost/gn/account/login/` → 200 (login GeoNode)
   - `curl -I http://localhost/account/login/` → 404 (sudah pindah)

5. **GeoServer proxy** masih jalan: `curl -I http://localhost/geoserver/web/` → 200 atau 302 (tidak dipengaruhi karena di-handle nginx).

6. **Browser smoke**:
   - Buka `http://localhost/` → DST landing
   - Klik "Login Pengelola" → `/dst-auth/dashboard/`
   - Klik tiap menu sidebar admin → URL bermula `/dst-auth/...`
   - Buka `http://localhost/gn/` → GeoNode homepage native; navigasi internal (catalog, maps, login) berfungsi
   - Buka `http://localhost/gn/admin/` → Django admin

## Catatan untuk Operasional

- Konsumer eksternal (DST Nasional API harvest) perlu diberi tahu bahwa endpoint API GeoNode berpindah ke `/gn/api/v2/...`. Jika downtime tidak boleh, tambahkan rewrite nginx: `/api/v2/...` → `/gn/api/v2/...` sebagai bridging.
- Tidak ada perubahan ke `.env`, `settings.py`, atau `STATICFILES_DIRS` — semua tetap.
- Tidak ada perubahan ke `static/dst-district/css/*.css` atau `js/*.js`.
