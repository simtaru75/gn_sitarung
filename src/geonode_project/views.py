from datetime import timedelta
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from actstream.models import Action
from django.contrib.auth import get_user_model
from geonode.documents.models import Document
from geonode.layers.models import Dataset

User = get_user_model()


def resolve_contact_user(value):
    """GeoNode poc/metadata_author bisa berupa User, queryset, atau list."""
    if value is None:
        return None
    if hasattr(value, "get_full_name"):
        return value
    if hasattr(value, "first"):  # queryset/manager
        try:
            return value.first()
        except Exception:
            return None
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return None


def user_org_label(user):
    """Label organisasi (OPD) → fallback nama lengkap → username."""
    if user is None:
        return ""
    org = (getattr(user, "organization", "") or "").strip()
    return org or (user.get_full_name() or "").strip() or getattr(user, "username", "") or ""


def document_walidata_label(doc):
    """Label Walidata sebuah Dokumen.

    Urutan sumber: (1) tautan ``DocumentWalidata`` ke tabel master; (2) ORGANISASI
    user POC (field organisasi saja, bukan nama orang — agar nama dummy/pemilik
    seperti "administrator" atau "Walidata BAPPEDA Luwu" tidak salah tampil
    sebagai Walidata). Kosong bila tak ada keduanya.
    """
    from .models import DocumentWalidata

    link = (
        DocumentWalidata.objects.filter(document_id=doc.pk)
        .select_related("walidata")
        .first()
    )
    if link and link.walidata:
        return link.walidata.nama
    for attr_name in ("poc", "metadata_author"):
        user = resolve_contact_user(getattr(doc, attr_name, None))
        if user is not None:
            org = (getattr(user, "organization", "") or "").strip()
            if org:
                return org
    return ""


def dataset_walidata_label(ds):
    """Label Walidata sebuah Dataset (layer) — paralel ``document_walidata_label``.

    Urutan: (1) tautan ``DatasetWalidata`` ke tabel master; (2) ORGANISASI user
    POC (bukan nama orang). Kosong bila tak ada keduanya.
    """
    from .models import DatasetWalidata

    link = (
        DatasetWalidata.objects.filter(dataset_id=ds.pk)
        .select_related("walidata")
        .first()
    )
    if link and link.walidata:
        return link.walidata.nama
    for attr_name in ("poc", "metadata_author"):
        user = resolve_contact_user(getattr(ds, attr_name, None))
        if user is not None:
            org = (getattr(user, "organization", "") or "").strip()
            if org:
                return org
    return ""


def region_autocomplete_context(resource):
    """Data untuk widget autocomplete 'Region / Cakupan'.

    Return dict berisi:
      - ``regions_all`` : list [{id, name}] seluruh wilayah Indonesia (Indonesia
        + provinsi + kabupaten/kota; code 'IDN' / 'IDN-*') untuk ``json_script``.
      - ``selected_regions`` : list {id, name} region yang sudah terpilih pada
        ``resource`` (untuk chip awal).
    """
    from django.db.models import Q
    from geonode.base.models import Region

    pool = list(
        Region.objects.filter(Q(code="IDN") | Q(code__startswith="IDN-"))
        .order_by("name")
        .values("id", "name")
    )
    selected = list(
        resource.regions.order_by("name").values("id", "name")
    )
    return {
        "regions_all": pool,
        "selected_regions": selected,
    }


def dataset_feature_label(ds):
    """Tipe fitur dataset untuk badge/filter: Point/Line/Polygon atau Raster."""
    if ds.is_raster:
        return "Raster"
    try:
        for attr in ds.attribute_set.all():
            at = (attr.attribute_type or "").lower()
            if "gml:" in at or "geometry" in at or "geom" in (attr.attribute or "").lower():
                if "polygon" in at:
                    return "Polygon"
                if "line" in at:
                    return "Line"
                if "point" in at:
                    return "Point"
    except Exception:
        pass
    try:
        if ds.is_vector():
            return "Vektor"
    except Exception:
        pass
    return ""


def api_dataset_meta(request):
    """JSON metadata dataset yang TIDAK diekspos GeoNode API v2 — dipakai frontend
    Next.js untuk melengkapi kartu & filter Eksplorasi Dataset.

    Per ``pk`` dataset:
      - ``walidata`` : label walidata (tautan ``DatasetWalidata`` ke master, atau
        organisasi user POC) — sumber yang sama dengan halaman edit layer.
      - ``fitur``    : tipe fitur asli (Polygon/Line/Point/Raster/Vektor).

    Read-only & publik (selaras dengan halaman Eksplorasi Dataset publik).
    """
    from django.http import JsonResponse
    from geonode.layers.models import Dataset

    items = {}
    for ds in Dataset.objects.all().prefetch_related("attribute_set"):
        items[str(ds.pk)] = {
            "walidata": dataset_walidata_label(ds),
            "fitur": dataset_feature_label(ds),
        }
    return JsonResponse({"items": items})


def api_komoditas_fokus(request):
    """JSON daftar Komoditas Fokus AKTIF (model ``KomoditasFokus``, dikelola di
    Pengaturan → Daftar Komoditas) untuk seksi Komoditas di frontend Next.js.

    Read-only & publik. Hanya ``aktif=True``, terurut ``urutan``. ``gambar``
    berupa path MEDIA relatif (mis. ``/uploaded/komoditas/...``) yang dilengkapi
    base publik oleh frontend.
    """
    from django.http import JsonResponse
    from .models import KomoditasFokus

    items = []
    for k in KomoditasFokus.objects.filter(aktif=True).order_by("urutan", "id"):
        items.append(
            {
                "id": k.id,
                "nama": k.nama,
                "deskripsi": (k.deskripsi or "").strip(),
                "gambar": k.gambar.url if k.gambar else "",
            }
        )
    return JsonResponse({"items": items})


def api_implementing_partners(request):
    """JSON Implementing Partners AKTIF (model ``ImplementingPartner``, dikelola
    di Pengaturan → Implementing Partners) untuk seksi Mitra di frontend.

    Read-only & publik. Hanya ``aktif=True``, terurut ``urutan``. ``logo`` berupa
    path MEDIA relatif yang dilengkapi base publik oleh frontend.
    """
    from django.http import JsonResponse
    from .models import ImplementingPartner

    items = []
    for p in ImplementingPartner.objects.filter(aktif=True).order_by("urutan", "id"):
        items.append(
            {
                "id": p.id,
                "nama": p.nama,
                "tautan": (p.tautan or "").strip(),
                "logo": p.logo.url if p.logo else "",
            }
        )
    return JsonResponse({"items": items})


def api_indikator_strategis(request):
    """JSON Indikator Strategis AKTIF (model ``IndikatorStrategis``, dikelola di
    Pengaturan → Indikator Strategis) untuk seksi Indikator di frontend.

    Read-only & publik. Hanya ``aktif=True``, terurut ``urutan``. ``ikon`` berupa
    URL statik relatif (``/static/dst-district/img/indikator/<berkas>``) yang
    dilengkapi base publik oleh frontend.
    """
    from django.conf import settings
    from django.http import JsonResponse
    from .models import IndikatorStrategis

    static_url = settings.STATIC_URL or "/static/"
    items = []
    for x in IndikatorStrategis.objects.filter(aktif=True).order_by("urutan", "id"):
        ikon = (x.ikon or "").strip()
        items.append(
            {
                "id": x.id,
                "judul": x.judul,
                "nilai": x.nilai,
                "deskripsi": (x.deskripsi or "").strip(),
                "ikon": f"{static_url}dst-district/img/indikator/{ikon}" if ikon else "",
            }
        )
    return JsonResponse({"items": items})


def _jelajah_dokumen_data(get, page_size=12):
    """Logika Jelajah Dokumen (query + facet + paginasi) dalam bentuk dict JSON —
    dipakai endpoint API untuk frontend Next.js. Paralel ``DocumentExploreView``.
    """
    from django.core.paginator import Paginator
    from django.db.models import Count, Q
    from django.db.models.functions import ExtractYear

    base = Document.objects.filter(is_published=True, is_approved=True)
    sel = {
        "walidata": get.getlist("walidata"),
        "kategori": get.getlist("kategori"),
        "tahun": get.getlist("tahun"),
        "format": get.getlist("format"),
        "wilayah": get.getlist("wilayah"),
    }
    q = (get.get("q") or "").strip()
    sort_map = {"recent": "-last_updated", "az": "title", "year": "-date", "views": "-popular_count"}
    sort = get.get("sort", "recent")
    if sort not in sort_map:
        sort = "recent"

    qs = base.select_related("owner", "category").prefetch_related("regions")
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(abstract__icontains=q) | Q(keywords__name__icontains=q)
        )
    if sel["walidata"]:
        from .models import DocumentWalidata

        wanted = sel["walidata"]
        bridge_ids = set(
            DocumentWalidata.objects.filter(walidata__nama__in=wanted).values_list("document_id", flat=True)
        )
        linked_ids = set(DocumentWalidata.objects.values_list("document_id", flat=True))
        legacy_ids = set(
            base.filter(
                contactrole__role="pointOfContact",
                contactrole__contact__organization__in=wanted,
            )
            .exclude(pk__in=linked_ids)
            .values_list("pk", flat=True)
        )
        qs = qs.filter(pk__in=bridge_ids | legacy_ids)
    if sel["kategori"]:
        qs = qs.filter(category__identifier__in=sel["kategori"])
    if sel["wilayah"]:
        qs = qs.filter(regions__name__in=sel["wilayah"])
    if sel["format"]:
        qs = qs.filter(extension__in=[f.lower() for f in sel["format"]])
    if sel["tahun"]:
        years = [int(y) for y in sel["tahun"] if y.isdigit()]
        if years:
            qs = qs.filter(date__year__in=years)

    qs = qs.distinct().order_by(sort_map[sort])
    total = qs.count()
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(get.get("page") or 1)

    def row(d):
        kategori = ""
        if d.category and (d.category.gn_description or d.category.identifier):
            kategori = d.category.gn_description or d.category.identifier
        year = d.date.year if d.date else (d.last_updated.year if d.last_updated else "")
        updated = d.last_updated or d.date
        return {
            "id": d.pk,
            "title": d.title or "",
            "pengelola": user_org_label(d.owner),
            "walidata": document_walidata_label(d),
            "kategori": kategori,
            "year": year,
            "extension": (d.extension or "").upper(),
            "updated": updated.isoformat() if updated else "",
            "regions": ", ".join(r.name for r in d.regions.all()),
        }

    ext_rows = (
        base.exclude(extension__isnull=True).exclude(extension="")
        .values("extension").annotate(c=Count("id", distinct=True)).order_by("-c")
    )
    year_rows = (
        base.exclude(date__isnull=True)
        .annotate(yr=ExtractYear("date")).values("yr")
        .annotate(c=Count("id", distinct=True)).order_by("-yr")
    )
    return {
        "documents": [row(d) for d in page_obj.object_list],
        "total": total,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "shown_from": page_obj.start_index(),
        "shown_to": page_obj.end_index(),
        "q": q,
        "selected": sel,
        "facets": {
            "walidata": DocumentExploreView._facet_walidata(base),
            "kategori": DatasetExploreView._facet_category(base),
            "wilayah": DatasetExploreView._facet(base, "regions__name"),
            "format": [
                {"value": r["extension"], "label": (r["extension"] or "").upper(), "count": r["c"]}
                for r in ext_rows
            ],
            "tahun": [
                {"value": str(r["yr"]), "label": str(r["yr"]), "count": r["c"]}
                for r in year_rows if r["yr"]
            ],
        },
    }


def api_jelajah_dokumen(request):
    """JSON Jelajah Dokumen Kebijakan untuk frontend Next.js — dokumen + facet +
    paginasi, menerima query string yang sama dengan ``DocumentExploreView``
    (q, walidata, kategori, tahun, format, wilayah, sort, page). Read-only, publik.
    """
    from django.http import JsonResponse

    return JsonResponse(_jelajah_dokumen_data(request.GET))


def _jelajah_dataset_data(get, page_size=12):
    """Logika Eksplorasi Dataset (query + facet + paginasi) dalam dict JSON —
    dipakai endpoint API untuk frontend Next.js. Paralel ``DatasetExploreView``.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q

    base = Dataset.objects.filter(is_published=True, is_approved=True)
    sel = {
        "walidata": get.getlist("walidata"),
        "kategori": get.getlist("kategori"),
        "feature": get.getlist("feature"),
        "wilayah": get.getlist("wilayah"),
    }
    sort_map = {"recent": "-last_updated", "az": "title", "year": "-date", "views": "-popular_count"}
    sort = get.get("sort", "recent")
    if sort not in sort_map:
        sort = "recent"
    q = (get.get("q") or "").strip()

    qs = base.select_related("owner", "category").prefetch_related("regions", "attribute_set")
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(abstract__icontains=q) | Q(keywords__name__icontains=q)
        )
    if sel["walidata"]:
        from .models import DatasetWalidata

        wanted = sel["walidata"]
        bridge_ids = set(
            DatasetWalidata.objects.filter(walidata__nama__in=wanted).values_list("dataset_id", flat=True)
        )
        linked_ids = set(DatasetWalidata.objects.values_list("dataset_id", flat=True))
        legacy_ids = set(
            base.filter(
                contactrole__role="pointOfContact",
                contactrole__contact__organization__in=wanted,
            )
            .exclude(pk__in=linked_ids)
            .values_list("pk", flat=True)
        )
        qs = qs.filter(pk__in=bridge_ids | legacy_ids)
    if sel["kategori"]:
        qs = qs.filter(category__identifier__in=sel["kategori"])
    if sel["wilayah"]:
        qs = qs.filter(regions__name__in=sel["wilayah"])
    if sel["feature"]:
        fq = Q()
        for f in sel["feature"]:
            fl = f.lower()
            if fl == "raster":
                fq |= Q(subtype="raster")
            elif fl in ("polygon", "line", "point"):
                fq |= Q(attribute_set__attribute_type__icontains=fl)
        if fq:
            qs = qs.filter(fq)

    qs = qs.distinct().order_by(sort_map[sort])
    total = qs.count()
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(get.get("page") or 1)

    def row(ds):
        category = ""
        if ds.category and (ds.category.gn_description or ds.category.identifier):
            category = ds.category.gn_description or ds.category.identifier
        year = ds.date.year if ds.date else (ds.last_updated.year if ds.last_updated else "")
        return {
            "id": ds.pk,
            "title": ds.title or ds.name or "",
            "walidata": dataset_walidata_label(ds),
            "category": category,
            "feature": dataset_feature_label(ds),
            "regions": ", ".join(r.name for r in ds.regions.all()),
            "thumbnail_url": ds.thumbnail_url or "",
            "is_raster": bool(ds.is_raster),
            "year": year,
        }

    return {
        "datasets": [row(ds) for ds in page_obj.object_list],
        "total": total,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "page_list": DatasetExploreView._page_list(page_obj.number, paginator.num_pages),
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
        "shown_from": page_obj.start_index(),
        "shown_to": page_obj.end_index(),
        "sort": sort,
        "q": q,
        "selected": sel,
        "facets": {
            "walidata": DatasetExploreView._facet_walidata(base),
            "kategori": DatasetExploreView._facet_category(base),
            "feature": DatasetExploreView._facet_feature(base),
            "wilayah": DatasetExploreView._facet(base, "regions__name"),
        },
    }


def api_jelajah_dataset(request):
    """JSON Eksplorasi Dataset untuk frontend Next.js — dataset + facet + paginasi
    (q, walidata, kategori, feature, wilayah, sort, page). Read-only, publik.
    """
    from django.http import JsonResponse

    return JsonResponse(_jelajah_dataset_data(request.GET))


def api_site_identity(request):
    """JSON identitas situs untuk frontend Next.js — MENGIKUTI lingkup wilayah
    terpilih. ``nama_kabupaten`` dari ``SiteIdentity`` (cakupan), nama & domain
    dari Django ``Site``, logo dari tema aktif. Read-only & publik.
    """
    from django.http import JsonResponse

    try:
        site = fresh_site()
    except Exception:
        site = None
    nama_kabupaten = ""
    tema = ""
    fonts = {}
    ref_map_id = 1
    try:
        from django.conf import settings as dj_settings

        from .models import SiteIdentity

        identity = SiteIdentity.load()
        nama_kabupaten = identity.nama_kabupaten or ""
        tema = (identity.theme or "").strip()
        fonts = identity.font_combo()
        ref_map_id = identity.webgis_reference_map_id or getattr(
            dj_settings, "WEBGIS_REFERENCE_MAP_ID", 1
        )
    except Exception:
        pass
    logo = ""
    try:
        from geonode.themes.models import GeoNodeThemeCustomization

        theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
        if theme and theme.logo:
            logo = theme.logo.url
    except Exception:
        pass
    return JsonResponse(
        {
            "nama_kabupaten": nama_kabupaten,
            "site_name": (site.name if site else "") or "",
            "site_domain": (site.domain if site else "") or "",
            "logo": logo,
            "theme": tema,
            "fonts": fonts,
            "webgis_reference_map_id": ref_map_id,
        }
    )


def fresh_site():
    """Django Site langsung dari DB (melewati SITE_CACHE in-process).

    Sites framework meng-cache get_current() pada dict memori per-proses; di
    uwsgi multi-worker, perubahan nama/domain tidak langsung tampak di worker
    lain. Membaca dari DB menjamin konsistensi lintas worker.
    """
    from django.conf import settings as dj_settings
    from django.contrib.sites.models import Site

    try:
        return Site.objects.get(pk=getattr(dj_settings, "SITE_ID", 5))
    except Exception:
        return Site.objects.get_current()


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def screening_log_create(request):
    """Endpoint publik: catat generate laporan 'Screening Tools analisis'.

    Dipanggil dari WebGIS saat Pratinjau Cetak men-generate Nomor Reg.
    Mendukung pengguna anonim (disimpan sebagai "Publik").

    CSRF-exempt: beacon logging publik & non-sensitif (hanya membuat catatan,
    tanpa efek destruktif), agar andal dari halaman publik di balik proxy HTTPS.
    """
    import json
    from django.http import JsonResponse

    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method"}, status=405)

    try:
        payload = json.loads(request.body or b"{}")
    except Exception:
        payload = {}
    nomor_reg = (payload.get("nomor_reg") or request.POST.get("nomor_reg") or "").strip()[:64]
    if not nomor_reg:
        return JsonResponse({"ok": False, "error": "nomor_reg kosong"}, status=400)

    area_ha = payload.get("area_ha")
    try:
        area_ha = float(area_ha) if area_ha not in (None, "") else None
    except (TypeError, ValueError):
        area_ha = None

    user = request.user if request.user.is_authenticated else None
    label = ((user.get_full_name() or user.username) if user else "Publik") or "Publik"

    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = (xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")) or None

    from .models import ScreeningLog

    log = ScreeningLog.objects.create(
        nomor_reg=nomor_reg, user=user, user_label=label[:150], ip=ip, area_ha=area_ha
    )
    return JsonResponse({"ok": True, "id": log.id})


def api_screening_count(request):
    """GET /api/folur/screening-count/ — jumlah total log screening (publik)."""
    from django.http import JsonResponse
    from .models import ScreeningLog

    return JsonResponse({"count": ScreeningLog.objects.count()})


def api_landing_sections(request):
    """GET /api/folur/landing-sections/ — peta visibilitas section Landing.

    Dikelola admin di /dst-auth/frontend/ (FrontendView → LandingSection).
    Frontend Next.js memakai ini untuk menampilkan/menyembunyikan seksi
    halaman utama sesuai toggle admin. Read-only.
    """
    from django.http import JsonResponse
    from .models import LandingSection

    LandingSection.ensure_defaults()
    sections = {s.key: s.is_visible for s in LandingSection.objects.all()}
    return JsonResponse({"sections": sections})


# ===========================================================================
# Capaian Program FOLUR (KPI) — kalkulasi context untuk Sitroom & landing
# ---------------------------------------------------------------------------
# Memasok context sesuai kontrak templates/dst-district/admin/capaian.html &
# landing/partials/_capaian_folur.html (lihat INTEGRASI.md). Semua kalkulasi
# defensif: bila tabel wilayah/IDM kosong, nilai jatuh ke None/0 dan template
# memakai fallback ``|default:``.
# ===========================================================================

# (slug, label, himpunan status mentah IDM) — urutan = urutan tampil di panel.
FOLUR_IDM_LABELS = [
    ("mandiri", "Mandiri", {"MANDIRI"}),
    ("maju", "Maju", {"MAJU"}),
    ("berkembang", "Berkembang", {"BERKEMBANG"}),
    ("tertinggal", "Tertinggal", {"TERTINGGAL"}),
    ("sangat", "Sangat Tertinggal", {"SANGAT TERTINGGAL", "SANGAT_TERTINGGAL"}),
]


def _folur_prov_singkat(nama_prov):
    """'Sulawesi Selatan' → 'SUL-SEL' (heuristik 3 huruf pertama tiap kata)."""
    nama = (nama_prov or "").strip()
    if not nama:
        return ""
    parts = [p for p in nama.replace(".", " ").split() if p]
    return "-".join(p[:3].upper() for p in parts[:3])


def _apply_seed_region_logo(level, kode_prov, kode_kab):
    """Terapkan logo default region ke logo situs (tema aktif GeoNode).

    Berkas bawaan ada di ``geonode_project/seed_data/``:
    - kabupaten → ``logo_kab/kab-h250px-<kode_kab>.<ext>``
    - provinsi  → ``logo_prov/prov-250-<kode_prov>.<ext>``
    (``<kode>`` = kode PUM, hanya digit). Ekstensi fleksibel — folder boleh
    campur png/jpg/jpeg/webp/svg; bila ada beberapa, urutan prioritas di bawah
    dipakai. Selalu menimpa logo yang ada. Return ``True`` bila berhasil
    diterapkan, ``False`` bila berkas seed tak tersedia atau gagal.
    """
    import os
    import re

    from django.core.files import File

    if level == "kabupaten":
        digits = re.sub(r"\D", "", kode_kab or "")
        subdir, stem = "logo_kab", f"kab-h250px-{digits}"
    elif level == "provinsi":
        digits = re.sub(r"\D", "", kode_prov or "")
        subdir, stem = "logo_prov", f"prov-250-{digits}"
    else:
        return False
    if not digits:
        return False

    base = os.path.join(os.path.dirname(__file__), "seed_data", subdir)
    src = next(
        (
            cand
            for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg")
            for cand in (os.path.join(base, stem + ext),)
            if os.path.exists(cand)
        ),
        None,
    )
    if src is None:
        return False
    try:
        from geonode.themes.models import GeoNodeThemeCustomization

        theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
        if theme is None:
            theme = GeoNodeThemeCustomization(name=digits, is_enabled=True)
            theme.save()
        if theme.logo:
            theme.logo.delete(save=False)
        with open(src, "rb") as fh:
            theme.logo.save(os.path.basename(src), File(fh), save=True)
        return True
    except Exception:  # pragma: no cover - defensif
        return False


def _folur_idm_distribution(level, kode_kab, kode_prov):
    """([{slug,nama,jumlah}], rata_skor, tahun) dari join wilayah.desa↔wilayah.idm.

    Join pada kode ternormalisasi (hanya digit); hanya desa yang punya IDM
    (kelurahan tak diindeks IDM). Mengembalikan ([], None, None) bila kosong.
    """
    from django.db import connection

    where = ""
    params = []
    if level == "kabupaten" and kode_kab:
        where = "WHERE d.kode_kab_pum = %s"
        params = [kode_kab]
    elif level == "provinsi" and kode_prov:
        where = "WHERE d.kode_prov_pum = %s"
        params = [kode_prov]

    sql = f"""
        SELECT upper(trim(i.status)) AS status, count(*) AS n, avg(i.skor_idm) AS rata
        FROM wilayah.desa d
        JOIN wilayah.idm i
          ON regexp_replace(d.kode_pum, '\\D', '', 'g') = i.kode_desa
         AND i.tahun = (SELECT max(tahun) FROM wilayah.idm)
        {where}
        GROUP BY upper(trim(i.status))
    """
    counts = {}
    periode = None
    with connection.cursor() as cur:
        cur.execute("SELECT max(tahun) FROM wilayah.idm")
        row = cur.fetchone()
        periode = row[0] if row else None
        if periode is None:
            return [], None, None
        cur.execute(sql, params)
        for status, n, rata in cur.fetchall():
            counts[status] = (n, rata)

    total_n = sum(n for n, _ in counts.values())
    total_score = sum(float(r) * n for n, r in counts.values() if r is not None)
    idm_avg = (total_score / total_n) if total_n else None

    dist = []
    for slug, nama, names in FOLUR_IDM_LABELS:
        jumlah = sum(cnt for status, (cnt, _r) in counts.items() if status in names)
        dist.append({"slug": slug, "nama": nama, "jumlah": jumlah})
    return dist, idm_avg, periode


def compute_folur_auto_kpis(identity=None):
    """Konteks bentang lahan FOLUR dari data sistem (wilayah.* + IDM + komoditas).

    Dipakai Sitroom & section publik via context ``folur_auto``. Kunci:
    ``luas_ha, jml_kec, jml_desa, jml_kel, persen_desa_maju, idm_avg, komoditas,
    komoditas_lower, komoditas_count, kode_kab, provinsi_singkat, periode_idm,
    idm_distribution``.
    """
    import re
    from django.db import connection
    from .models import (
        SiteIdentity,
        RefWilayahKabkota,
        RefWilayahKecamatan,
        RefWilayahDesa,
        KomoditasFokus,
    )

    if identity is None:
        identity = SiteIdentity.load()

    level = (identity.cakupan_level or "").strip()
    kode_kab = (identity.cakupan_kode_kab or "").strip()
    kode_prov = (identity.cakupan_kode_prov or "").strip()

    out = {
        "luas_ha": None,
        "jml_kec": 0,
        "jml_desa": 0,
        "jml_kel": 0,
        "persen_desa_maju": None,
        "idm_avg": None,
        "idm_distribution": [],
        "periode_idm": None,
        "kode_kab": kode_kab or kode_prov,
        "provinsi_singkat": _folur_prov_singkat(identity.cakupan_nama_prov),
    }

    try:
        if level == "kabupaten" and kode_kab:
            kab_qs = RefWilayahKabkota.objects.filter(kode_pum=kode_kab)
            kec_qs = RefWilayahKecamatan.objects.filter(kode_kab_pum=kode_kab)
            desa_qs = RefWilayahDesa.objects.filter(kode_kab_pum=kode_kab)
        elif level == "provinsi" and kode_prov:
            kab_qs = RefWilayahKabkota.objects.filter(kode_prov_pum=kode_prov)
            kec_qs = RefWilayahKecamatan.objects.filter(kode_prov_pum=kode_prov)
            desa_qs = RefWilayahDesa.objects.filter(kode_prov_pum=kode_prov)
        else:
            kab_qs = RefWilayahKabkota.objects.all()
            kec_qs = RefWilayahKecamatan.objects.all()
            desa_qs = RefWilayahDesa.objects.all()

        # Luas dalam HEKTAR dihitung dari geometri — kolom BIG ``luas_ha``
        # sebenarnya bersatuan km² (mis. Luwu 2.902 km² = 290.210 ha).
        luas_sql = (
            "SELECT COALESCE(sum(ST_Area(geom::geography)) / 10000.0, 0) "
            "FROM wilayah.kabkota"
        )
        luas_params = []
        if level == "kabupaten" and kode_kab:
            luas_sql += " WHERE kode_pum = %s"
            luas_params = [kode_kab]
        elif level == "provinsi" and kode_prov:
            luas_sql += " WHERE kode_prov_pum = %s"
            luas_params = [kode_prov]
        with connection.cursor() as cur:
            cur.execute(luas_sql, luas_params)
            luas = cur.fetchone()[0]
        out["luas_ha"] = round(luas) if luas else None
        out["jml_kec"] = kec_qs.count()

        jml_desa = jml_kel = 0
        for kode in desa_qs.values_list("kode_pum", flat=True):
            last4 = re.sub(r"\D", "", kode or "")[-4:]
            if last4[:1] == "1":
                jml_kel += 1
            else:
                jml_desa += 1
        out["jml_desa"] = jml_desa
        out["jml_kel"] = jml_kel
    except Exception:
        pass

    try:
        dist, idm_avg, periode = _folur_idm_distribution(level, kode_kab, kode_prov)
        out["idm_distribution"] = dist
        out["idm_avg"] = round(idm_avg, 3) if idm_avg is not None else None
        out["periode_idm"] = periode
        total = sum(d["jumlah"] for d in dist)
        maju = sum(d["jumlah"] for d in dist if d["slug"] in ("mandiri", "maju"))
        out["persen_desa_maju"] = round(maju / total * 100) if total else None
    except Exception:
        pass

    komq = list(
        KomoditasFokus.objects.filter(aktif=True).order_by("urutan", "id")
        .values_list("nama", flat=True)
    )
    out["komoditas"] = " · ".join(komq)
    out["komoditas_lower"] = " · ".join(k.lower() for k in komq)
    out["komoditas_count"] = len(komq)
    return out


def _folur_auto_value(auto_key):
    """Nilai KPI ``sumber=auto`` dari data sistem (None bila tak dikenal)."""
    from .models import ImplementingPartner

    if auto_key == "mitra_aktif":
        return ImplementingPartner.objects.filter(aktif=True).count()
    return None


def _folur_spark(capaian_iter):
    """Sparkline inline-SVG dari time-series realisasi (≥2 titik), else ''."""
    pts = sorted(
        ((c.tahun, c.nilai) for c in capaian_iter if c.nilai is not None),
        key=lambda x: x[0],
    )
    if len(pts) < 2:
        return ""
    vals = [v for _, v in pts]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    w, h, n = 48, 16, len(pts)
    coords = " ".join(
        f"{round(i / (n - 1) * w, 1)},{round(h - (v - lo) / span * h, 1)}"
        for i, (_, v) in enumerate(pts)
    )
    return (
        f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
        f'stroke-linejoin="round"><polyline points="{coords}"/></svg>'
    )


def folur_rollup_series(indikator, level="desa"):
    """Roll-up lintas yurisdiksi: {tahun: Σ nilai semua wilayah} dari
    ``FolurCapaianWilayah`` untuk satu indikator + jenjang (default desa).
    Dipakai indikator ``sumber_agregat="roll_up"`` agar angka agregat (Kabupaten)
    otomatis = Σ data per-wilayah — konsisten dengan hero webgis2.
    """
    from django.db.models import Sum
    from .models import FolurCapaianWilayah

    out = {}
    for r in (
        FolurCapaianWilayah.objects.filter(indikator=indikator, level=level)
        .values("tahun")
        .annotate(total=Sum("nilai"))
    ):
        if r["total"] is not None:
            out[r["tahun"]] = r["total"]
    return out


def build_folur_kpis(periode=None):
    """Daftar KPI FOLUR + agregat untuk Sitroom & landing (lihat INTEGRASI.md)."""
    import types

    from .models import FolurIndikator

    indikators = list(
        FolurIndikator.objects.filter(aktif=True)
        .prefetch_related("capaian")
        .order_by("urutan", "id")
    )

    if periode is None:
        years = [c.tahun for ind in indikators for c in ind.capaian.all()]
        periode = max(years) if years else timezone.now().year

    kpis = []
    for ind in indikators:
        sumber_auto = ind.sumber == "auto"
        agregasi = getattr(ind, "agregasi", "tahunan") or "tahunan"
        sumber_agregat = getattr(ind, "sumber_agregat", "manual") or "manual"
        kum_nilai, kum_years = None, []
        spark_pts = None
        if sumber_auto:
            nilai = _folur_auto_value(ind.auto_key)
        else:
            # Deret (tahun, nilai): roll_up = Σ data per-wilayah; manual = FolurCapaian.
            if sumber_agregat == "roll_up":
                roll = folur_rollup_series(ind, level="desa")
                series = sorted(roll.items(), key=lambda x: x[0])
                spark_pts = [
                    types.SimpleNamespace(tahun=th, nilai=nl) for th, nl in series
                ]
            else:
                series = sorted(
                    ((c.tahun, c.nilai) for c in ind.capaian.all() if c.nilai is not None),
                    key=lambda x: x[0],
                )
                spark_pts = list(ind.capaian.all())
            # Realisasi kumulatif tahunan: Σ realisasi semua tahun <= periode.
            cum = [(th, nl) for th, nl in series if th <= periode]
            kum_nilai = sum(nl for _, nl in cum) if cum else None
            kum_years = [th for th, _ in cum]
            if agregasi == "kumulatif":
                # Σ realisasi s.d. tahun terpilih (indikator stok, mis. CI3).
                nilai = kum_nilai
            else:
                # snapshot tahun terpilih (carry-forward ke tahun ≤ bila kosong).
                chosen = next((nl for th, nl in series if th == periode), None)
                if chosen is None:
                    le = [nl for th, nl in series if th <= periode]
                    chosen = le[-1] if le else (series[-1][1] if series else None)
                nilai = chosen

        ada_data = nilai is not None
        persen = 0
        if ada_data and ind.target:
            try:
                if ind.arah == "turun":
                    raw = (ind.target / nilai * 100) if nilai else 0
                else:
                    raw = nilai / ind.target * 100
                persen = max(0, min(round(raw), 100))
            except ZeroDivisionError:
                persen = 0

        kpis.append(
            {
                "kode": ind.kode,
                "nama": ind.nama,
                "pilar": ind.pilar,
                "pilar_nama": ind.pilar_nama,
                "satuan": ind.satuan,
                "nilai": nilai,
                "target": ind.target,
                "persen": persen,
                "ada_data": ada_data,
                "sumber_auto": sumber_auto,
                "agregasi": agregasi,
                "sumber_agregat": sumber_agregat,
                "kum_nilai": kum_nilai,
                "kum_years": kum_years,
                "deskripsi": ind.deskripsi,
                "extra": ind.extra,
                "spark": "" if sumber_auto else _folur_spark(spark_pts or []),
            }
        )

    total = len(kpis)
    terisi = sum(1 for k in kpis if k["ada_data"])

    pilar_order, pilar_map = [], {}
    for k in kpis:
        if k["pilar"] not in pilar_map:
            pilar_map[k["pilar"]] = {
                "slug": k["pilar"], "nama": k["pilar_nama"], "terisi": 0, "total": 0
            }
            pilar_order.append(k["pilar"])
        pilar_map[k["pilar"]]["total"] += 1
        if k["ada_data"]:
            pilar_map[k["pilar"]]["terisi"] += 1

    publik = [k for k in kpis if k["ada_data"] and k["target"]][:4]

    all_years = sorted(
        {c.tahun for ind in indikators for c in ind.capaian.all()}, reverse=True
    )
    if periode not in all_years:
        all_years = sorted(set(all_years) | {periode}, reverse=True)

    from .models import KomoditasFokus

    komoditas_fokus = list(
        KomoditasFokus.objects.filter(aktif=True)
        .order_by("urutan", "nama")
        .values_list("nama", flat=True)
    )

    return {
        "folur_capaian": kpis,
        "folur_capaian_publik": publik,
        "folur_periode": periode,
        "folur_years": all_years,
        "folur_total": total,
        "folur_terisi": terisi,
        "folur_gap_count": total - terisi,
        "folur_pilar_filter": [pilar_map[p] for p in pilar_order],
        "folur_komoditas": komoditas_fokus,
    }


def folur_realisasi_series(ind):
    """Deret realisasi tahunan AGREGAT (Kabupaten) satu indikator, menghormati
    ``sumber_agregat``: roll_up → Σ data desa per tahun; manual → ``FolurCapaian``.
    """
    if (getattr(ind, "sumber_agregat", "manual") or "manual") == "roll_up":
        return [
            {"tahun": th, "nilai": nl}
            for th, nl in sorted(folur_rollup_series(ind, "desa").items())
        ]
    return [
        {"tahun": c.tahun, "nilai": c.nilai}
        for c in sorted(ind.capaian.all(), key=lambda c: c.tahun)
        if c.nilai is not None
    ]


def _capaian_api_key_ok(request):
    """True bila PIN/API key benar. Diterima via header ``X-API-Key``,
    query ``?api_key=``/``?pin=``, atau ``Authorization: ApiKey|Bearer <pin>``.
    Default PIN ``123456`` (override: settings/env ``DST_CAPAIAN_API_KEY``).
    """
    from django.conf import settings as dj_settings

    expected = str(getattr(dj_settings, "DST_CAPAIAN_API_KEY", "123456") or "")
    got = (
        request.META.get("HTTP_X_API_KEY")
        or request.GET.get("api_key")
        or request.GET.get("pin")
        or ""
    )
    if not got:
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        parts = auth.split(None, 1)
        if len(parts) == 2 and parts[0].lower() in ("apikey", "api-key", "bearer", "pin"):
            got = parts[1]
    return bool(expected) and str(got).strip() == expected


def api_capaian_folur(request):
    """API (read-only, JSON) — **Capaian Program FOLUR + Sitroom** kabupaten sebagai
    *service ke DST Nasional*. **Butuh API key (PIN)** — header ``X-API-Key`` atau
    query ``?api_key=`` (default ``123456``). Hanya GET (tanpa CRUD).

    Query string (semua opsional):
      - ``tahun=YYYY``         → filter realisasi ke satu tahun.
      - ``indikator=CI4,CI1``  → subset indikator (kode dipisah koma).
      - ``wilayah=desa`` | ``kecamatan`` → sertakan rincian per-wilayah
        (nilai + kegiatan per tahun; ``kode_pum`` bertitik = hierarki yurisdiksi).

    Angka agregat menghormati ``sumber_agregat`` indikator (roll-up dari data desa
    atau entri manual). Menyertakan blok ``sitroom`` (KPI otomatis + ringkasan pilar).
    """
    import datetime as _dt

    from django.http import JsonResponse

    from .models import (
        SiteIdentity,
        FolurIndikator,
        FolurCapaianWilayah,
        KomoditasFokus,
    )

    if not _capaian_api_key_ok(request):
        resp = JsonResponse(
            {
                "error": "API key (PIN) tidak valid atau tidak disertakan.",
                "cara": "Sertakan header 'X-API-Key: <pin>' atau query '?api_key=<pin>'.",
            },
            status=401,
            json_dumps_params={"ensure_ascii": False},
        )
        resp["WWW-Authenticate"] = 'ApiKey realm="DST Capaian"'
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

    try:
        ftahun = int(request.GET.get("tahun") or 0)
    except (TypeError, ValueError):
        ftahun = 0
    kodes = [
        k.strip().upper()
        for k in (request.GET.get("indikator") or "").split(",")
        if k.strip()
    ]
    wilayah = request.GET.get("wilayah")
    wilayah = wilayah if wilayah in ("desa", "kecamatan") else None

    identity = SiteIdentity.load()
    inds = list(
        FolurIndikator.objects.filter(aktif=True)
        .order_by("urutan", "id")
        .prefetch_related("capaian")
    )
    if kodes:
        inds = [i for i in inds if i.kode.upper() in kodes]

    items, all_years = [], set()
    for ind in inds:
        series = folur_realisasi_series(ind)
        for s in series:
            all_years.add(s["tahun"])
        shown = [s for s in series if (not ftahun or s["tahun"] == ftahun)]
        cum_all = sum(s["nilai"] for s in series) if series else None
        latest = series[-1] if series else None
        ref = cum_all if ind.agregasi == "kumulatif" else (
            latest["nilai"] if latest else None
        )
        persen = None
        if ref is not None and ind.target:
            try:
                raw = (
                    (ind.target / ref * 100)
                    if (ind.arah == "turun" and ref)
                    else (ref / ind.target * 100)
                )
                persen = round(max(0.0, raw), 1)
            except ZeroDivisionError:
                persen = None
        items.append(
            {
                "kode": ind.kode,
                "nama": ind.nama,
                "pilar": ind.pilar,
                "pilar_nama": ind.pilar_nama,
                "satuan": ind.satuan,
                "target": ind.target,
                "arah": ind.arah,
                "agregasi": ind.agregasi,
                "sumber_agregat": getattr(ind, "sumber_agregat", "manual"),
                "realisasi_tahunan": shown,
                "realisasi_terbaru": latest,
                "realisasi_kumulatif": cum_all,
                "persen_capaian": persen,
            }
        )

    # Blok Sitroom: KPI otomatis (formulasi data sistem) + ringkasan pilar.
    auto = compute_folur_auto_kpis(identity)
    summary = build_folur_kpis(ftahun or None)
    sitroom = {
        "auto": {
            "luas_bentang_ha": auto.get("luas_ha"),
            "jml_kecamatan": auto.get("jml_kec"),
            "jml_desa": auto.get("jml_desa"),
            "jml_kelurahan": auto.get("jml_kel"),
            "persen_desa_maju": auto.get("persen_desa_maju"),
            "idm_rata2": auto.get("idm_avg"),
            "periode_idm": auto.get("periode_idm"),
            "komoditas_fokus": auto.get("komoditas_count"),
        },
        "ringkasan": {
            "periode": summary.get("folur_periode"),
            "total_indikator": summary.get("folur_total"),
            "indikator_terisi": summary.get("folur_terisi"),
            "indikator_belum": summary.get("folur_gap_count"),
            "pilar": summary.get("folur_pilar_filter"),
        },
    }

    payload = {
        "service": "DST Kabupaten — Capaian Program FOLUR + Sitroom",
        "version": "1.1",
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "lisensi": "Data Pemerintah Kabupaten; mohon atribusi DST FOLUR.",
        "kabupaten": {
            "nama": identity.nama_kabupaten or "",
            "cakupan_level": identity.cakupan_level or "",
            "kode_prov": identity.cakupan_kode_prov or "",
            "nama_prov": identity.cakupan_nama_prov or "",
            "kode_kab": identity.cakupan_kode_kab or "",
            "nama_kab": identity.cakupan_nama_kab or "",
        },
        "tahun_filter": ftahun or None,
        "tahun_tersedia": sorted(all_years, reverse=True),
        "jumlah_indikator": len(items),
        "indikator": items,
        "komoditas": list(
            KomoditasFokus.objects.filter(aktif=True)
            .order_by("urutan", "nama")
            .values_list("nama", flat=True)
        ),
        "sitroom": sitroom,
    }

    if wilayah:
        qs = FolurCapaianWilayah.objects.filter(level=wilayah, indikator__in=inds)
        if ftahun:
            qs = qs.filter(tahun=ftahun)
        rows = {}
        for r in qs.select_related("indikator").order_by(
            "kode_pum", "indikator__kode", "tahun"
        ):
            w = rows.setdefault(
                r.kode_pum, {"kode_pum": r.kode_pum, "nama": r.nama, "capaian": []}
            )
            w["capaian"].append(
                {
                    "indikator": r.indikator.kode,
                    "tahun": r.tahun,
                    "nilai": r.nilai,
                    "kegiatan": r.kegiatan,
                }
            )
        payload["wilayah"] = {
            "level": wilayah,
            "jumlah": len(rows),
            "data": list(rows.values()),
        }

    resp = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    resp["Access-Control-Allow-Origin"] = "*"  # service publik lintas-origin
    resp["Cache-Control"] = "public, max-age=300"
    return resp


def api_capaian_publik(request):
    """Capaian FOLUR untuk frontend Next.js (PUBLIK, read-only).

    Data capaian bersifat publik (identik halaman /capaian-folur/). Endpoint
    ``api_capaian_folur`` dilindungi PIN demi integrasi DST Nasional; di sini
    kita menyuntik PIN server SENDIRI (dari settings) lalu mendelegasikan,
    sehingga frontend tak perlu menyimpan rahasia & payload tetap identik.
    """
    from django.conf import settings as dj_settings

    request.META["HTTP_X_API_KEY"] = str(
        getattr(dj_settings, "DST_CAPAIAN_API_KEY", "123456") or ""
    )
    return api_capaian_folur(request)


class CapaianPublikView(TemplateView):
    """Halaman publik 'Capaian Program FOLUR' (standalone, seperti Jelajah Dokumen).

    Menyajikan scorecard ringkas FOLUR untuk publik. Konten = partial
    ``landing/partials/_capaian_folur.html`` (KPI auto + KPI publik). Ditautkan
    dari tombol di section Screening Tools (Landing), terlihat bila
    ``sections.capaian_folur`` aktif (Frontend toggle).
    """

    template_name = "dst-district/capaian_publik.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""

        from .models import SiteIdentity

        identity = SiteIdentity.load()
        ctx["nama_kabupaten"] = identity.nama_kabupaten or "(Kabupaten Abc)"
        auto = compute_folur_auto_kpis(identity)
        ctx["folur_auto"] = auto
        ctx["folur_komoditas_count"] = auto.get("komoditas_count", 0)
        ctx.update(build_folur_kpis(auto.get("periode_idm") or None))
        return ctx


class DstLandingView(TemplateView):
    template_name = "dst-district/landing/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        docs_qs = (
            Document.objects.filter(is_published=True, is_approved=True)
            .select_related("owner", "category", "group")
            .prefetch_related("keywords")
            .order_by("-date", "-last_updated")
        )

        doc_rows = []
        for d in docs_qs[:5]:
            if d.date:
                year = d.date.year
            elif d.last_updated:
                year = d.last_updated.year
            else:
                year = ""

            doc_type = ""
            if d.category and (d.category.gn_description or d.category.identifier):
                doc_type = d.category.gn_description or d.category.identifier
            elif d.subtype:
                doc_type = d.subtype.title()
            else:
                doc_type = "Dokumen"

            if d.group and (d.group.title or d.group.slug):
                authority = d.group.title or d.group.slug
            elif d.owner:
                org = getattr(d.owner, "organization", "") or ""
                authority = org or (d.owner.get_full_name() or d.owner.username)
            else:
                authority = "—"

            tags = [k.name for k in d.keywords.all()[:2]]

            doc_rows.append(
                {
                    "id": d.pk,
                    "year": year,
                    "doc_type": doc_type,
                    "title": d.title,
                    "authority": authority,
                    "tags": tags,
                }
            )

        ctx["landing_documents"] = doc_rows
        ctx["landing_documents_total"] = docs_qs.count()

        ds_qs = (
            Dataset.objects.filter(is_published=True, is_approved=True)
            .select_related("owner", "category")
            .prefetch_related("keywords")
            .order_by("-last_updated")
        )

        dataset_rows = []
        for ds in ds_qs[:3]:
            if ds.is_vector():
                geom = ds.subtype or "vector"
                geom_label = f"Vektor · {geom.replace('_', ' ').title()}"
                ogc_text = "WMS · WFS"
            elif ds.is_raster:
                geom_label = "Raster · GeoTIFF"
                ogc_text = "WMS · WCS"
            else:
                geom_label = (ds.subtype or "—").title()
                ogc_text = "WMS"

            category = ""
            if ds.category and (ds.category.gn_description or ds.category.identifier):
                category = ds.category.gn_description or ds.category.identifier

            abstract_text = (ds.abstract or "").strip()
            placeholder_markers = {"", "no abstract provided", "no abstract", "n/a", "-"}
            if abstract_text.lower() in placeholder_markers:
                abstract_text = ""

            srid_text = (ds.srid or "EPSG:4326").upper()

            dataset_rows.append(
                {
                    "id": ds.pk,
                    "title": ds.title or ds.name,
                    "geom_label": geom_label,
                    "category": category,
                    "abstract": abstract_text,
                    "srid": srid_text,
                    "ogc": ogc_text,
                    "thumbnail_url": ds.thumbnail_url or "",
                    "is_raster": bool(ds.is_raster),
                }
            )

        ctx["landing_datasets"] = dataset_rows
        ctx["landing_datasets_total"] = ds_qs.count()

        # ── Eksplorasi Dataset (katalog lengkap + filter metadata) ──────
        # Memetakan metadata Dataset GeoNode ke opsi filter Satu Data:
        #   Pengelola → owner.organization (OPD produsen data)
        #   Walidata  → poc (point of contact / pembina data)
        #   Kategori  → category (ISO TopicCategory)
        #   Feature   → tipe geometri (Point/Line/Polygon) atau Raster
        #   Wilayah   → regions (Region M2M)
        from collections import Counter

        def _resolve_user(value):
            """GeoNode poc/metadata_author bisa berupa User, queryset, atau list."""
            if value is None:
                return None
            if hasattr(value, "get_full_name"):
                return value
            if hasattr(value, "first"):  # queryset/manager
                try:
                    return value.first()
                except Exception:
                    return None
            if isinstance(value, (list, tuple)):
                return value[0] if value else None
            return None

        def _user_label(user):
            if user is None:
                return ""
            org = (getattr(user, "organization", "") or "").strip()
            return org or (user.get_full_name() or "").strip() or user.username

        def _pengelola_label(ds):
            return _user_label(ds.owner)

        def _walidata_label(ds):
            # Konsisten dgn katalog: tautan master (DatasetWalidata) → org POC.
            return dataset_walidata_label(ds)

        def _feature_label(ds):
            if ds.is_raster:
                return "Raster"
            for attr in ds.attribute_set.all():
                at = (attr.attribute_type or "").lower()
                if "gml:" in at or "geometry" in at or "geom" in (attr.attribute or "").lower():
                    if "polygon" in at:
                        return "Polygon"
                    if "line" in at:
                        return "Line"
                    if "point" in at:
                        return "Point"
            if ds.is_vector():
                return "Vektor"
            return ""

        catalog_qs = (
            Dataset.objects.filter(is_published=True, is_approved=True)
            .select_related("owner", "category")
            .prefetch_related("keywords", "regions", "attribute_set")
            .order_by("-last_updated")
        )

        catalog_rows = []
        for ds in catalog_qs[:60]:
            category = ""
            if ds.category and (ds.category.gn_description or ds.category.identifier):
                category = ds.category.gn_description or ds.category.identifier

            region_names = [r.name for r in ds.regions.all()]
            year = ds.date.year if ds.date else (ds.last_updated.year if ds.last_updated else "")

            title = ds.title or ds.name or ""
            catalog_rows.append(
                {
                    "id": ds.pk,
                    "title": title,
                    "title_lower": title.lower(),
                    "pengelola": _pengelola_label(ds),
                    "walidata": _walidata_label(ds),
                    "category": category,
                    "feature": _feature_label(ds),
                    "regions": ", ".join(region_names),
                    "region_list": region_names,
                    "thumbnail_url": ds.thumbnail_url or "",
                    "is_raster": bool(ds.is_raster),
                    "year": year,
                    "views": getattr(ds, "popular_count", 0) or 0,
                }
            )

        def _filter_counts(key):
            counter = Counter()
            for row in catalog_rows:
                value = row.get(key)
                if value:
                    counter[value] += 1
            return [
                {"label": label, "count": count}
                for label, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
            ]

        region_counter = Counter()
        for row in catalog_rows:
            for region_name in row["region_list"]:
                region_counter[region_name] += 1

        ctx["catalog_datasets"] = catalog_rows
        ctx["catalog_shown"] = len(catalog_rows)
        ctx["catalog_total"] = catalog_qs.count()
        ctx["filter_pengelola"] = _filter_counts("pengelola")
        ctx["filter_walidata"] = _filter_counts("walidata")
        ctx["filter_kategori"] = _filter_counts("category")
        ctx["filter_feature"] = _filter_counts("feature")
        ctx["filter_wilayah"] = [
            {"label": label, "count": count}
            for label, count in sorted(region_counter.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
        except Exception:
            theme = None
        ctx["theme"] = theme
        ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""

        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None

        from .models import (
            SiteIdentity,
            ScreeningLog,
            LandingSection,
            KomoditasFokus,
            ImplementingPartner,
            IndikatorStrategis,
            LayananData,
        )

        ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or "(Kabupaten Abc)"
        ctx["screening_count"] = ScreeningLog.objects.count()
        ctx["sections"] = LandingSection.visibility_map()
        komoditas_fokus = list(
            KomoditasFokus.objects.filter(aktif=True).select_related("dataset", "dokumen")
        )
        ctx["komoditas_fokus"] = komoditas_fokus
        ctx["komoditas_aktif_count"] = len(komoditas_fokus)
        ctx["mitra_list"] = list(ImplementingPartner.objects.filter(aktif=True))

        # Indikator strategis — ikon dirujuk dari folder statis (URL dihitung di
        # sini via STATIC_URL agar tidak bergantung manifest staticfiles; berkas
        # yang belum ada hanya menghasilkan img rusak, bukan error 500).
        from django.conf import settings as _dj_settings

        _ikon_base = f"{_dj_settings.STATIC_URL}dst-district/img/indikator/"
        indikator_strategis = list(IndikatorStrategis.objects.filter(aktif=True))
        for _ind in indikator_strategis:
            _ind.ikon_url = (_ikon_base + _ind.ikon) if _ind.ikon else ""
        ctx["indikator_strategis"] = indikator_strategis

        # Layanan Data — ikon boleh berupa nama berkas statis ATAU URL penuh.
        _layanan_base = f"{_dj_settings.STATIC_URL}dst-district/img/layanan/"
        layanan_data = list(LayananData.objects.filter(aktif=True))
        for _lay in layanan_data:
            if _lay.ikon.startswith("http"):
                _lay.ikon_url = _lay.ikon
            else:
                _lay.ikon_url = (_layanan_base + _lay.ikon) if _lay.ikon else ""
            _lay.tautan_external = _lay.tautan.startswith("http") if _lay.tautan else False
        ctx["layanan_data"] = layanan_data
        return ctx


class WebGisView(TemplateView):
    template_name = "dst-district/webgis.html"

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings

        ctx = super().get_context_data(**kwargs)

        # Nama situs custom dari panel admin (Sites framework); fallback ke SITENAME.
        try:
            site_name = fresh_site().name
        except Exception:
            site_name = getattr(dj_settings, "SITENAME", "GeoNode")
        ctx["site_name"] = site_name

        # Logo kabupaten (= logo situs / tema aktif) untuk topbar.
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""

        # referenceMapId: utamakan yang disimpan di DB (admin pengaturan WebGIS),
        # fallback ke WEBGIS_REFERENCE_MAP_ID dari settings.py.
        from .models import SiteIdentity

        identity = SiteIdentity.load()
        ref_map_id = identity.webgis_reference_map_id or getattr(
            dj_settings, "WEBGIS_REFERENCE_MAP_ID", 1
        )

        # Same-origin via nginx → base_url relatif menghindari hardcode & CORS.
        ctx["webgis_config"] = {
            "baseURL": "",
            "wmsPath": "/geoserver/wms",
            "wfsPath": "/geoserver/wfs",
            "mapsApiPath": "/api/v2/maps",
            "datasetsApiPath": "/api/v2/datasets",
            "workspace": "geonode",
            "referenceMapId": ref_map_id,
            "center": [-3.23, 120.39],
            "bbox": [[-3.7, 119.9], [-2.7, 120.8]],
            "siteName": site_name,
        }
        return ctx


class WebGis2View(TemplateView):
    """Halaman publik ``/webgis2/`` — monitoring spasial Capaian Program FOLUR
    per desa/kecamatan (choropleth + sidebar kaya info). Desain mengikuti
    ``dataset_detail.html``; READ-ONLY (entri dilakukan di Admin 'Data Capaian').
    """

    template_name = "dst-district/webgis2.html"

    # 4 indikator FOLUR inti yang dimonitor pada peta.
    INDIKATOR_KODE = ["CI1", "CI3", "CI4", "CI11"]

    def get_context_data(self, **kwargs):
        import datetime
        from django.conf import settings as dj_settings
        from .models import (
            SiteIdentity,
            FolurIndikator,
            FolurCapaian,
            FolurCapaianWilayah,
            RefWilayahDesa,
            RefWilayahKecamatan,
            WEBGIS2_PALETTES,
        )

        ctx = super().get_context_data(**kwargs)

        try:
            site_name = fresh_site().name
        except Exception:
            site_name = getattr(dj_settings, "SITENAME", "GeoNode")
        ctx["site_name"] = site_name
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""

        identity = SiteIdentity.load()
        nama_kabupaten = identity.nama_kabupaten or site_name
        ctx["nama_kabupaten"] = nama_kabupaten

        # Center/bbox dari extent geometri desa cakupan aktif (fallback Sulsel).
        center, bbox = [-3.0, 120.4], None
        try:
            from django.contrib.gis.db.models import Extent

            ext = RefWilayahDesa.objects.aggregate(e=Extent("geom"))["e"]
            if ext:
                x0, y0, x1, y1 = ext
                center = [(y0 + y1) / 2.0, (x0 + x1) / 2.0]
                bbox = [[y0, x0], [y1, x1]]
        except Exception:
            pass

        n_desa = 0
        n_kec = 0
        try:
            n_desa = RefWilayahDesa.objects.count()
            n_kec = RefWilayahKecamatan.objects.count()
        except Exception:
            pass

        # Nama wilayah cakupan diambil dari DATABASE CAKUPAN (RefWilayahDesa.nama_kab),
        # bukan SiteIdentity — agar label peta selalu konsisten dgn geometri yang
        # benar-benar dimuat (SiteIdentity bisa drift dari region aktif). Level
        # kabupaten → 1 nama kab; level provinsi → fallback ke nama provinsi.
        cakupan_nama = ""
        try:
            kabs = [
                k for k in RefWilayahDesa.objects.order_by()
                .values_list("nama_kab", flat=True).distinct() if k
            ]
            if len(kabs) == 1:
                nm = kabs[0].strip()
                low = nm.lower()
                if not (low.startswith("kabupaten") or low.startswith("kota")):
                    nm = f"Kabupaten {nm}"
                cakupan_nama = nm
            elif len(kabs) > 1:
                provs = [
                    p for p in RefWilayahDesa.objects.order_by()
                    .values_list("nama_prov", flat=True).distinct() if p
                ]
                if provs:
                    pv = provs[0].strip()
                    cakupan_nama = pv if pv.lower().startswith("provinsi") else f"Provinsi {pv}"
        except Exception:
            cakupan_nama = ""
        if not cakupan_nama:
            cakupan_nama = nama_kabupaten

        # Tahun aktif: data per-wilayah terbaru → agregat → tahun berjalan.
        tahun = (
            FolurCapaianWilayah.objects.order_by("-tahun")
            .values_list("tahun", flat=True)
            .first()
            or FolurCapaian.objects.order_by("-tahun")
            .values_list("tahun", flat=True)
            .first()
            or datetime.date.today().year
        )

        # Metadata 4 indikator + realisasi agregat terbaru (headline fallback).
        inds = list(
            FolurIndikator.objects.filter(kode__in=self.INDIKATOR_KODE, aktif=True)
        )
        order = {k: i for i, k in enumerate(self.INDIKATOR_KODE)}
        inds.sort(key=lambda d: order.get(d.kode, 99))
        default_ramp = WEBGIS2_PALETTES["hijau"][1]

        # Deret agregat per-tahun (Σ nilai semua wilayah) PER JENJANG (desa &
        # kecamatan) untuk tiap indikator → hero "realisasi kumulatif tahunan"
        # mengikuti yurisdiksi aktif.
        from django.db.models import Sum

        agg_series = {"desa": {}, "kecamatan": {}}
        for lvl in ("desa", "kecamatan"):
            for r in (
                FolurCapaianWilayah.objects.filter(level=lvl, indikator__in=inds)
                .values("indikator__kode", "tahun")
                .annotate(total=Sum("nilai"))
            ):
                agg_series[lvl].setdefault(r["indikator__kode"], []).append(
                    {"tahun": r["tahun"], "nilai": r["total"]}
                )
            for k in agg_series[lvl]:
                agg_series[lvl][k].sort(key=lambda x: x["tahun"])

        indikator_meta = []
        for ind in inds:
            cap = ind.capaian.order_by("-tahun").first()
            palet = getattr(ind, "palet", "hijau") or "hijau"
            indikator_meta.append(
                {
                    "kode": ind.kode,
                    "nama": ind.nama,
                    "satuan": ind.satuan,
                    "target": ind.target,
                    "arah": ind.arah,
                    "pilar": ind.pilar,
                    "pilar_nama": ind.pilar_nama,
                    "deskripsi": ind.deskripsi,
                    "agg": cap.nilai if cap else None,
                    "agg_tahun": cap.tahun if cap else None,
                    "palet": palet,
                    "ramp": WEBGIS2_PALETTES.get(palet, (None, default_ramp))[1],
                    "agregasi": getattr(ind, "agregasi", "tahunan") or "tahunan",
                    "aggSeries": {
                        "desa": agg_series["desa"].get(ind.kode, []),
                        "kecamatan": agg_series["kecamatan"].get(ind.kode, []),
                    },
                }
            )

        # Daftar tahun yang punya data per-wilayah (untuk pemilih TAHUN di webgis2).
        years = sorted(
            {
                y
                for y in FolurCapaianWilayah.objects.order_by()
                .values_list("tahun", flat=True)
                .distinct()
                if y
            },
            reverse=True,
        )
        if not years:
            years = [tahun]
        if tahun not in years:
            years = sorted(set(years) | {tahun}, reverse=True)

        import os as _os
        from django.templatetags.static import static as _static

        from .models import KomoditasFokus

        komoditas_fokus = list(
            KomoditasFokus.objects.filter(aktif=True)
            .order_by("urutan", "nama")
            .values_list("nama", flat=True)
        )
        # Peta nama komoditas -> URL ikon (static) untuk marker peta. Ikon dipakai
        # bila berkasnya tersedia di static/dst-district/img/komoditas/.
        komoditas_icons = {}
        _icon_dir = _os.path.join(
            _os.path.dirname(__file__), "static", "dst-district", "img", "komoditas"
        )
        _avail = set(_os.listdir(_icon_dir)) if _os.path.isdir(_icon_dir) else set()
        for k in KomoditasFokus.objects.all():
            if k.gambar:
                _b = _os.path.basename(k.gambar.name)
                if _b in _avail:
                    komoditas_icons[k.nama] = _static(
                        f"dst-district/img/komoditas/{_b}"
                    )

        ctx["indikator_meta"] = indikator_meta
        ctx["tahun"] = tahun
        ctx["config"] = {
            "geojsonUrl": reverse("dst:webgis2_geojson"),
            "historyUrl": reverse("dst:webgis2_desa_history"),
            "center": center,
            "bbox": bbox,
            "tahun": tahun,
            "years": years,
            "level": "desa",
            "levels": ["desa"] + (["kecamatan"] if n_kec else []),
            "nKec": n_kec,
            "nDesa": n_desa,
            "indikator": indikator_meta,
            "namaKabupaten": nama_kabupaten,
            "cakupanNama": cakupan_nama,
            "komoditasFokus": komoditas_fokus,
            "komoditasIcons": komoditas_icons,
            "siteName": site_name,
        }
        return ctx


def api_webgis2_config(request):
    """JSON config WebGIS Capaian (``/webgis2/``) untuk frontend Next.js.

    Memakai ULANG konteks ``WebGis2View`` (config identik, tanpa duplikasi
    logika DB). Frontend menyuntikkannya ke ``#wg2-config`` lalu memuat
    webgis-capaian.js. Read-only.
    """
    from django.http import JsonResponse

    view = WebGis2View()
    view.request = request
    view.args = ()
    view.kwargs = {}
    ctx = view.get_context_data()
    return JsonResponse(ctx.get("config") or {})


def webgis2_geojson(request):
    """GeoJSON poligon desa/kecamatan cakupan aktif + nilai indikator FOLUR
    (publik, read-only) untuk choropleth ``/webgis2/``.

    Geometri disederhanakan & di-cache (statis sampai region di-restore ulang);
    nilai per wilayah disuntik segar tiap permintaan dari ``FolurCapaianWilayah``.
    """
    import json

    from django.core.cache import cache
    from django.http import JsonResponse

    from .models import FolurCapaianWilayah, RefWilayahDesa, RefWilayahKecamatan

    level = "kecamatan" if (request.GET.get("level") == "kecamatan") else "desa"
    try:
        tahun = int(request.GET.get("tahun") or 0)
    except (TypeError, ValueError):
        tahun = 0

    Model = RefWilayahKecamatan if level == "kecamatan" else RefWilayahDesa

    # Versi cache mengikuti isi tabel cakupan aktif: (jumlah baris, MAX updated_at).
    # Cache 'default' = LocMemCache (per-proses) -> invalidasi lintas-proses tak
    # andal; key di-derive dari state DB bersama agar SEMUA proses otomatis
    # beralih ke geometri baru saat region di-restore (atau di-restore ulang),
    # tanpa nunggu TTL 1 jam. Satu query agregat (count+max) -> murah.
    from django.db.models import Count, Max

    try:
        agg = Model.objects.aggregate(n=Count("pk"), m=Max("updated_at"))
        ver = f"{agg['n'] or 0}_{int(agg['m'].timestamp()) if agg['m'] else 0}"
    except Exception:
        ver = "0_0"

    ckey = f"webgis2_geom_{level}_{ver}"
    base = cache.get(ckey)
    if base is None:
        fields = ["kode_pum", "nama", "geom"] + (
            ["nama_kec", "kode_kec_pum"] if level == "desa" else []
        )
        base = []
        for r in Model.objects.all().only(*fields).iterator():
            if r.geom is None:
                continue
            try:
                simple = r.geom.simplify(0.0008, preserve_topology=True) or r.geom
                gj = json.loads(simple.geojson)
            except Exception:
                try:
                    gj = json.loads(r.geom.geojson)
                except Exception:
                    continue
            # Titik representatif (ST_PointOnSurface) untuk marker ikon komoditas;
            # selalu di dalam poligon (beda dgn centroid yg bisa di luar).
            point = None
            try:
                pos = r.geom.point_on_surface
                point = [round(pos.y, 6), round(pos.x, 6)]  # [lat, lng]
            except Exception:
                try:
                    c = r.geom.centroid
                    point = [round(c.y, 6), round(c.x, 6)]
                except Exception:
                    point = None
            base.append(
                {
                    "kode_pum": r.kode_pum,
                    "nama": r.nama,
                    "nama_kec": getattr(r, "nama_kec", "") or "",
                    "kode_kec_pum": getattr(r, "kode_kec_pum", "") or "",
                    "point": point,
                    "geometry": gj,
                }
            )
        cache.set(ckey, base, 60 * 60)

    # Nilai & kegiatan SEMUA indikator per wilayah, MENGHORMATI agregasi indikator:
    #   - tahunan  -> nilai pada tahun terpilih saja
    #   - kumulatif -> Σ nilai semua tahun <= terpilih (kegiatan = tahun terbaru)
    #   values   = {kode_pum: {kode_indikator: nilai}}
    #   kegiatan = {kode_pum: {kode_indikator: teks kegiatan}}
    # Klien memilih indikator dari sini -> ganti indikator tanpa fetch ulang.
    values = {}
    kegiatan = {}
    komoditas = {}
    if tahun:
        from collections import defaultdict

        per = defaultdict(dict)  # (ik, kp) -> {tahun: (nilai, kegiatan, komoditas)}
        aggmap = {}              # ik -> agregasi
        for ik, ag, kp, th, nil, keg, kom in FolurCapaianWilayah.objects.filter(
            level=level, tahun__lte=tahun
        ).values_list(
            "indikator__kode", "indikator__agregasi", "kode_pum", "tahun",
            "nilai", "kegiatan", "komoditas__nama",
        ):
            aggmap[ik] = ag or "tahunan"
            per[(ik, kp)][th] = (nil, keg, kom)

        for (ik, kp), ydict in per.items():
            if aggmap.get(ik) == "kumulatif":
                nil = sum(v for v, _, _ in ydict.values() if v is not None)
                keg = ydict[max(ydict)][1]  # kegiatan tahun terbaru <= terpilih
                kom = ydict[max(ydict)][2]  # komoditas tahun terbaru <= terpilih
            else:  # tahunan: hanya tahun terpilih
                if tahun not in ydict:
                    continue
                nil, keg, kom = ydict[tahun]
            values.setdefault(kp, {})[ik] = nil
            if keg:
                kegiatan.setdefault(kp, {})[ik] = keg
            if kom:
                komoditas.setdefault(kp, {})[ik] = kom

    features = [
        {
            "type": "Feature",
            "geometry": b["geometry"],
            "properties": {
                "kode_pum": b["kode_pum"],
                "nama": b["nama"],
                "nama_kec": b["nama_kec"],
                "kode_kec_pum": b.get("kode_kec_pum", ""),
                "point": b.get("point"),
                "nilai": values.get(b["kode_pum"], {}),
                "kegiatan": kegiatan.get(b["kode_pum"], {}),
                "komoditas": komoditas.get(b["kode_pum"], {}),
            },
        }
        for b in base
    ]
    return JsonResponse({"type": "FeatureCollection", "features": features})


def webgis2_desa_history(request):
    """Riwayat tahunan satu WILAYAH (desa/kecamatan) untuk semua indikator FOLUR
    (publik, read-only). Dipakai panel 'wilayah terpilih' di ``/webgis2/`` untuk
    menampilkan deret tahunan (tahun · nilai · kegiatan) saat poligon diklik —
    menjawab kasus 1 wilayah dengan kegiatan/nilai berbeda di tahun berbeda.
    Hasil: ``series = {kode_indikator: [{tahun, nilai, kegiatan}, ...]}`` urut tahun.
    """
    from django.http import JsonResponse
    from .models import FolurCapaianWilayah

    level = "kecamatan" if request.GET.get("level") == "kecamatan" else "desa"
    kode_pum = (request.GET.get("kode_pum") or "").strip()
    if not kode_pum:
        return JsonResponse({"ok": False, "series": {}})

    series = {}
    for ik, th, nil, keg, kom in (
        FolurCapaianWilayah.objects.filter(level=level, kode_pum=kode_pum)
        .order_by("indikator__kode", "tahun")
        .values_list("indikator__kode", "tahun", "nilai", "kegiatan", "komoditas__nama")
    ):
        series.setdefault(ik, []).append(
            {"tahun": th, "nilai": nil, "kegiatan": keg or "", "komoditas": kom or ""}
        )
    return JsonResponse(
        {"ok": True, "kode_pum": kode_pum, "level": level, "series": series}
    )


def _dataset_detail_payload(dataset):
    """Data detail dataset (geometry, OGC endpoints, downloads, walidata, …).

    SUMBER TUNGGAL dipakai ``DatasetMapView`` (HTML) DAN ``api_dataset_detail``
    (JSON untuk frontend Next.js) agar desain & fungsi keduanya identik.
    URL OGC relatif (same-origin via nginx/proxy).
    """
    typename = dataset.alternate or dataset.typename or (
        f"{dataset.workspace}:{dataset.name}"
        if dataset.workspace and dataset.name
        else (dataset.name or "")
    )

    if dataset.is_vector():
        _geo = dataset_feature_label(dataset)
        geometry_label = f"Vektor · {_geo if _geo and _geo != 'Vektor' else (dataset.subtype or 'vector').replace('_', ' ').title()}"
    elif dataset.is_raster:
        geometry_label = "Raster · GeoTIFF"
    elif dataset.subtype == "tabular":
        geometry_label = "Tabular · metadata-only"
    else:
        geometry_label = (dataset.subtype or "—").title()

    bbox = None
    bbox_text = ""
    if dataset.ll_bbox_polygon:
        try:
            ext = dataset.ll_bbox_polygon.extent  # (W, S, E, N)
            bbox = [[ext[1], ext[0]], [ext[3], ext[2]]]  # Leaflet [[S,W],[N,E]]
            bbox_text = f"{ext[0]:.4f}, {ext[1]:.4f} → {ext[2]:.4f}, {ext[3]:.4f}"
        except Exception:
            bbox = None
    center = (
        [(bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[1][1]) / 2]
        if bbox else [-3.0, 120.2]
    )

    endpoints = []
    downloads = []
    if typename:
        if dataset.is_vector():
            endpoints.append({"label": "WMS", "desc": "Tampilan peta (image)",
                              "url": f"/geoserver/wms?service=WMS&request=GetMap&layers={typename}"})
            endpoints.append({"label": "WFS", "desc": "Akses fitur vektor (GeoJSON)",
                              "url": f"/geoserver/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/json"})
            downloads.append({"kind": "GeoJSON", "meta": "EPSG:4326",
                              "url": f"/geoserver/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/json&srsName=EPSG:4326"})
            downloads.append({"kind": "Shapefile (ZIP)", "meta": f"{dataset.srid or 'EPSG:4326'}",
                              "url": f"/geoserver/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=SHAPE-ZIP"})
            downloads.append({"kind": "GeoPackage", "meta": f"{dataset.srid or 'EPSG:4326'}",
                              "url": f"/geoserver/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/x-gpkg"})
            downloads.append({"kind": "CSV atribut", "meta": "tanpa geometri",
                              "url": f"/geoserver/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=csv"})
        elif dataset.is_raster:
            endpoints.append({"label": "WMS", "desc": "Tampilan raster (image)",
                              "url": f"/geoserver/wms?service=WMS&request=GetMap&layers={typename}"})
            endpoints.append({"label": "WCS", "desc": "Coverage raster (GeoTIFF)",
                              "url": f"/geoserver/wcs?service=WCS&coverageId={typename}&request=GetCoverage"})
    endpoints.append({"label": "REST", "desc": "Metadata JSON",
                      "url": f"/api/v2/datasets/{dataset.pk}"})
    if dataset.uuid:
        downloads.append({"kind": "Metadata ISO 19139", "meta": "untuk katalog",
                          "url": f"/catalogue/csw?service=CSW&version=2.0.2&request=GetRecordById&id={dataset.uuid}&outputSchema=http://www.isotc211.org/2005/gmd"})

    abstract_text = (dataset.abstract or "").strip()
    placeholders = {"", "no abstract provided", "no abstract", "n/a", "-"}
    has_real_abstract = abstract_text.lower() not in placeholders
    year = dataset.date.year if dataset.date else (
        dataset.last_updated.year if dataset.last_updated else ""
    )
    kategori = ""
    if dataset.category and (dataset.category.gn_description or dataset.category.identifier):
        kategori = dataset.category.gn_description or dataset.category.identifier

    return {
        "typename": typename,
        "geometry_label": geometry_label,
        "feature": dataset_feature_label(dataset),
        "srid": (dataset.srid or "EPSG:4326").upper(),
        "bbox": bbox,
        "bbox_text": bbox_text,
        "center": center,
        "is_raster": bool(dataset.is_raster),
        "title": dataset.title or dataset.name or "",
        "name": dataset.name or "",
        "pengelola": user_org_label(dataset.owner),
        "walidata": dataset_walidata_label(dataset),
        "kategori": kategori,
        "category_id": dataset.category.identifier if dataset.category else "",
        "year": year,
        "has_real_abstract": has_real_abstract,
        "abstract_text": abstract_text if has_real_abstract else "",
        "license_name": dataset.license.name if dataset.license else "",
        "attribution": (dataset.attribution or "").strip(),
        "regions": [r.name for r in dataset.regions.all()],
        "keywords": [k.name for k in dataset.keywords.all()],
        "views_count": getattr(dataset, "popular_count", 0) or 0,
        "endpoints": endpoints,
        "downloads": downloads,
        "catalogue_url": f"/catalogue/#/dataset/{dataset.pk}",
    }


def api_dataset_detail(request, pk):
    """JSON detail dataset untuk frontend Next.js — payload identik dengan
    ``DatasetMapView`` (walidata, OGC endpoints, downloads, dll.). Read-only.
    """
    from django.http import JsonResponse, Http404

    try:
        dataset = (
            Dataset.objects.filter(is_published=True)
            .select_related("owner", "category", "license", "group")
            .prefetch_related("keywords", "regions", "attribute_set")
            .get(pk=pk)
        )
    except (Dataset.DoesNotExist, ValueError, TypeError):
        raise Http404("Dataset tidak ditemukan atau belum dipublikasikan.")

    payload = _dataset_detail_payload(dataset)
    payload["pk"] = dataset.pk
    payload["uuid"] = str(dataset.uuid or "")
    payload["thumbnail_url"] = dataset.thumbnail_url or ""
    payload["subtype"] = dataset.subtype or ""
    return JsonResponse(payload)


class DatasetMapView(TemplateView):
    """Halaman detail peta dataset (publik) — view map + metadata.

    Mirip WebGIS namun fokus ke SATU layer dan TANPA fitur screening tools.
    Dipakai sebagai tautan "Detail" dari Katalog Data & Eksplorasi Dataset,
    menggantikan tautan ke halaman katalog GeoNode/MapStore.
    """

    template_name = "dst-district/dataset_detail.html"

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from django.conf import settings as dj_settings

        ctx = super().get_context_data(**kwargs)

        pk = kwargs.get("pk") or self.request.GET.get("id")
        try:
            dataset = (
                Dataset.objects.filter(is_published=True)
                .select_related("owner", "category", "license", "group")
                .prefetch_related("keywords", "regions", "attribute_set")
                .get(pk=pk)
            )
        except (Dataset.DoesNotExist, ValueError, TypeError):
            raise Http404("Dataset tidak ditemukan atau belum dipublikasikan.")

        # Identitas situs / tema (untuk header)
        try:
            site_name = fresh_site().name
        except Exception:
            site_name = getattr(dj_settings, "SITENAME", "GeoNode")
        ctx["site_name"] = site_name
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""
        try:
            from .models import SiteIdentity

            ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or ""
        except Exception:
            ctx["nama_kabupaten"] = ""

        # Payload tunggal (dipakai juga oleh api_dataset_detail untuk frontend)
        p = _dataset_detail_payload(dataset)
        ctx["dataset"] = dataset
        ctx["map_config"] = {
            "baseURL": "",
            "wmsPath": "/geoserver/wms",
            "wfsPath": "/geoserver/wfs",
            "layer": p["typename"],
            "bbox": p["bbox"],
            "center": p["center"],
            "isRaster": p["is_raster"],
            "title": p["title"],
        }
        ctx["geometry_label"] = p["geometry_label"]
        ctx["feature"] = p["feature"]
        ctx["pengelola"] = p["pengelola"]
        ctx["walidata"] = p["walidata"]
        ctx["kategori"] = p["kategori"]
        ctx["regions_list"] = p["regions"]
        ctx["keywords_list"] = p["keywords"]
        ctx["typename"] = p["typename"]
        ctx["srid"] = p["srid"]
        ctx["bbox_text"] = p["bbox_text"]
        ctx["year"] = p["year"]
        ctx["has_real_abstract"] = p["has_real_abstract"]
        ctx["abstract_text"] = p["abstract_text"]
        ctx["license_name"] = p["license_name"]
        ctx["attribution"] = p["attribution"]
        ctx["endpoints"] = p["endpoints"]
        ctx["downloads"] = p["downloads"]
        ctx["catalogue_url"] = p["catalogue_url"]
        ctx["views_count"] = p["views_count"]
        return ctx


def _document_first_file(document):
    """Path file lokal pertama milik Document (atau None)."""
    try:
        files = list(document.files or [])
    except Exception:
        files = []
    return files[0] if files else None


def document_file(request, pk):
    """Stream berkas dokumen (same-origin) untuk viewer canvas / unduhan.

    Akses berkas (baik pratinjau inline maupun unduhan ``?dl=1``) MENGHORMATI
    permission GeoNode: hanya pengguna dengan ``download_resourcebase`` pada
    resource yang boleh. Untuk publik/anonim hal ini bergantung pada setelan
    "Anyone" di tab Share dokumen:
      - "View and Download" → boleh (200).
      - "View Metadata"     → ditolak (403) — publik hanya boleh metadata.
    """
    import os
    import mimetypes
    from django.http import FileResponse, Http404, HttpResponseForbidden

    try:
        document = Document.objects.filter(is_published=True).get(pk=pk)
    except (Document.DoesNotExist, ValueError, TypeError):
        raise Http404("Dokumen tidak ditemukan atau belum dipublikasikan.")

    resource = document.get_self_resource()
    if not request.user.has_perm("base.download_resourcebase", resource):
        return HttpResponseForbidden(
            "Anda tidak memiliki izin mengunduh/mengakses berkas dokumen ini."
        )

    path = _document_first_file(document)
    if not path or not os.path.exists(path):
        raise Http404("Berkas dokumen tidak tersedia di server.")

    want_download = request.GET.get("dl") == "1"
    ctype, _ = mimetypes.guess_type(path)
    response = FileResponse(open(path, "rb"), content_type=ctype or "application/octet-stream")
    filename = os.path.basename(path)
    disposition = "attachment" if want_download else "inline"
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


_DOC_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "tif", "tiff"}


def _document_detail_payload(document, request):
    """Data detail dokumen (jenis, walidata, abstrak, izin unduh, file_url, …).

    SUMBER TUNGGAL dipakai ``DocumentDetailView`` (HTML) & ``api_dokumen_detail``
    (JSON Next.js). ``can_download`` MENGHORMATI permission GeoNode untuk
    ``request.user`` (anonim pada SSR publik). ``file_url`` = endpoint streaming
    ber-permission ``dst:document_file`` (relatif; frontend proksi same-origin).
    """
    from django.urls import reverse

    resource = document.get_self_resource()
    can_download = request.user.has_perm("base.download_resourcebase", resource)

    ext = (document.extension or "").lower()
    is_pdf = ext == "pdf"
    is_image = (ext in _DOC_IMAGE_EXT or bool(getattr(document, "is_image", False))) and not is_pdf

    if document.category and (document.category.gn_description or document.category.identifier):
        doc_type = document.category.gn_description or document.category.identifier
    else:
        doc_type = "Dokumen"

    # Walidata = instansi dari tabel master (tautan DocumentWalidata), bukan
    # pemilik/POC. Fallback ke ORGANISASI user POC (bukan username), lalu kosong —
    # konsisten dgn katalog/eksplorasi & payload dataset (dataset_walidata_label).
    walidata = document_walidata_label(document)

    abstract_text = (document.abstract or "").strip()
    placeholders = {"", "no abstract provided", "no abstract", "n/a", "-"}
    has_real_abstract = abstract_text.lower() not in placeholders

    supplemental = (document.supplemental_information or "").strip()
    if supplemental.lower() in {"", "no information provided", "n/a", "-"}:
        supplemental = ""

    year = document.date.year if document.date else (
        document.last_updated.year if document.last_updated else ""
    )
    kategori = doc_type if (document.category and (document.category.gn_description or document.category.identifier)) else ""

    return {
        "title": document.title or "",
        "doc_type": doc_type,
        "pengelola": user_org_label(document.owner),
        "walidata": walidata,
        "kategori": kategori,
        "regions": [r.name for r in document.regions.all()],
        "keywords": [k.name for k in document.keywords.all()],
        "abstract_text": abstract_text if has_real_abstract else "",
        "has_real_abstract": has_real_abstract,
        "supplemental": supplemental,
        "year": year,
        "language": (document.language or "").strip(),
        "license_name": document.license.name if document.license else "",
        "attribution": (document.attribution or "").strip(),
        "extension": ext,
        "is_pdf": is_pdf,
        "is_image": is_image,
        "has_file": bool(_document_first_file(document)),
        "can_download": can_download,
        "file_url": reverse("dst:document_file", args=[document.pk]),
        "views_count": getattr(document, "popular_count", 0) or 0,
        "uuid_short": str(document.uuid or "")[:8],
    }


def api_dokumen_detail(request, pk):
    """JSON detail dokumen untuk frontend Next.js — payload identik
    ``DocumentDetailView`` (jenis, walidata, izin unduh sadar-permission, dll.).
    Read-only. 404 bila tak boleh lihat metadata.
    """
    from django.http import JsonResponse, Http404

    try:
        document = (
            Document.objects.filter(is_published=True)
            .select_related("owner", "category", "license", "group")
            .prefetch_related("keywords", "regions")
            .get(pk=pk)
        )
    except (Document.DoesNotExist, ValueError, TypeError):
        raise Http404("Dokumen tidak ditemukan atau belum dipublikasikan.")
    resource = document.get_self_resource()
    if not request.user.has_perm("base.view_resourcebase", resource):
        raise Http404("Anda tidak memiliki izin melihat dokumen ini.")
    payload = _document_detail_payload(document, request)
    payload["pk"] = document.pk
    payload["thumbnail_url"] = document.thumbnail_url or ""
    return JsonResponse(payload)


class DocumentDetailView(TemplateView):
    """Halaman detail dokumen — viewer canvas PDF.js + metadata.

    Menggantikan tautan ke katalog GeoNode untuk dokumen. Pratinjau & unduhan
    MENGHORMATI permission GeoNode (tab Share): pengguna butuh
    ``download_resourcebase`` untuk melihat isi berkas / mengunduh. Publik
    anonim dengan "Anyone = View Metadata" hanya melihat metadata.
    """

    template_name = "dst-district/document_detail.html"

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from django.conf import settings as dj_settings
        from django.urls import reverse

        ctx = super().get_context_data(**kwargs)

        pk = kwargs.get("pk") or self.request.GET.get("id")
        try:
            document = (
                Document.objects.filter(is_published=True)
                .select_related("owner", "category", "license", "group")
                .prefetch_related("keywords", "regions")
                .get(pk=pk)
            )
        except (Document.DoesNotExist, ValueError, TypeError):
            raise Http404("Dokumen tidak ditemukan atau belum dipublikasikan.")

        # Permission GeoNode (tab Share). view_resourcebase = boleh lihat
        # metadata; download_resourcebase = boleh akses isi berkas + unduh.
        resource = document.get_self_resource()
        if not self.request.user.has_perm("base.view_resourcebase", resource):
            raise Http404("Anda tidak memiliki izin melihat dokumen ini.")

        # Identitas situs / tema
        try:
            site_name = fresh_site().name
        except Exception:
            site_name = getattr(dj_settings, "SITENAME", "GeoNode")
        ctx["site_name"] = site_name
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""
        try:
            from .models import SiteIdentity

            ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or ""
        except Exception:
            ctx["nama_kabupaten"] = ""

        # Komputasi metadata DRY — sumber tunggal yang sama dipakai endpoint
        # JSON Next.js (api_dokumen_detail), jadi HTML & frontend selalu sinkron.
        p = _document_detail_payload(document, self.request)
        path = _document_first_file(document)

        ctx["document"] = document
        ctx["doc_type"] = p["doc_type"]
        ctx["pengelola"] = p["pengelola"]
        ctx["walidata"] = p["walidata"]
        ctx["kategori"] = p["kategori"]
        ctx["regions_list"] = p["regions"]
        ctx["keywords_list"] = p["keywords"]
        ctx["abstract_text"] = p["abstract_text"]
        ctx["has_real_abstract"] = p["has_real_abstract"]
        ctx["supplemental"] = p["supplemental"]
        ctx["year"] = p["year"]
        ctx["language"] = p["language"]
        ctx["license_name"] = p["license_name"]
        ctx["attribution"] = p["attribution"]
        ctx["extension"] = p["extension"]
        ctx["is_pdf"] = p["is_pdf"]
        ctx["is_image"] = p["is_image"]
        ctx["has_file"] = p["has_file"]
        # Akses isi berkas (pratinjau + unduh) = punya download_resourcebase.
        ctx["can_download"] = p["can_download"]
        ctx["allow_download"] = p["can_download"]
        ctx["is_authenticated"] = self.request.user.is_authenticated
        ctx["file_url"] = p["file_url"]
        ctx["filename"] = document.title or (path and __import__("os").path.basename(path)) or "dokumen"
        ctx["views_count"] = p["views_count"]
        ctx["uuid_short"] = p["uuid_short"]
        return ctx


class DatasetExploreView(TemplateView):
    """Halaman Eksplorasi Dataset lengkap dengan PAGINASI SERVER-SIDE sejati.

    Semua dataset ter-publish terjangkau (tanpa batas 60 seperti section di
    landing). Filter (Pengelola/Walidata/Kategori/Feature/Wilayah) & sort
    dikirim via query string (GET); tiap halaman = satu request server.
    """

    template_name = "dst-district/dataset_explore.html"
    PER_PAGE = 12

    SORT_MAP = {
        "recent": "-last_updated",
        "az": "title",
        "year": "-date",
        "views": "-popular_count",
    }

    def _row(self, ds):
        category = ""
        if ds.category and (ds.category.gn_description or ds.category.identifier):
            category = ds.category.gn_description or ds.category.identifier
        region_names = [r.name for r in ds.regions.all()]
        year = ds.date.year if ds.date else (ds.last_updated.year if ds.last_updated else "")
        title = ds.title or ds.name or ""
        return {
            "id": ds.pk,
            "title": title,
            "pengelola": user_org_label(ds.owner),
            "walidata": self._walidata(ds),
            "category": category,
            "feature": dataset_feature_label(ds),
            "regions": ", ".join(region_names),
            "thumbnail_url": ds.thumbnail_url or "",
            "is_raster": bool(ds.is_raster),
            "year": year,
        }

    @staticmethod
    def _walidata(ds):
        return dataset_walidata_label(ds)

    @staticmethod
    def _facet_walidata(base):
        """Daftar filter Walidata dataset: tautan master + fallback poc.org."""
        from django.db.models import Count
        from .models import DatasetWalidata

        counts = {}
        for r in (
            DatasetWalidata.objects.filter(dataset__in=base)
            .values("walidata__nama")
            .annotate(c=Count("dataset", distinct=True))
        ):
            lbl = r["walidata__nama"]
            if lbl:
                counts[lbl] = counts.get(lbl, 0) + r["c"]
        linked_ids = DatasetWalidata.objects.values_list("dataset_id", flat=True)
        for r in (
            base.exclude(pk__in=linked_ids)
            .filter(contactrole__role="pointOfContact")
            .exclude(contactrole__contact__organization__isnull=True)
            .exclude(contactrole__contact__organization="")
            .values("contactrole__contact__organization")
            .annotate(c=Count("id", distinct=True))
        ):
            lbl = r["contactrole__contact__organization"]
            if lbl:
                counts[lbl] = counts.get(lbl, 0) + r["c"]
        return [
            {"value": k, "label": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        ]

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings
        from django.core.paginator import Paginator
        from django.db.models import Count, Q

        ctx = super().get_context_data(**kwargs)
        req = self.request

        base = Dataset.objects.filter(is_published=True, is_approved=True)

        # ── Filter terpilih (multi-nilai) ──────────────────────────
        sel = {
            "pengelola": req.GET.getlist("pengelola"),
            "walidata": req.GET.getlist("walidata"),
            "kategori": req.GET.getlist("kategori"),
            "feature": req.GET.getlist("feature"),
            "wilayah": req.GET.getlist("wilayah"),
        }
        sort = req.GET.get("sort", "recent")
        if sort not in self.SORT_MAP:
            sort = "recent"

        # Pencarian teks bebas (dari kotak Pencarian Data di Landing / bar explore).
        q = (req.GET.get("q") or "").strip()

        qs = base.select_related("owner", "category").prefetch_related("regions", "attribute_set")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(abstract__icontains=q)
                | Q(keywords__name__icontains=q)
            )
        if sel["pengelola"]:
            qs = qs.filter(owner__organization__in=sel["pengelola"])
        if sel["walidata"]:
            from .models import DatasetWalidata

            wanted = sel["walidata"]
            bridge_ids = set(
                DatasetWalidata.objects.filter(walidata__nama__in=wanted)
                .values_list("dataset_id", flat=True)
            )
            linked_ids = set(
                DatasetWalidata.objects.values_list("dataset_id", flat=True)
            )
            legacy_ids = set(
                base.filter(
                    contactrole__role="pointOfContact",
                    contactrole__contact__organization__in=wanted,
                )
                .exclude(pk__in=linked_ids)
                .values_list("pk", flat=True)
            )
            qs = qs.filter(pk__in=bridge_ids | legacy_ids)
        if sel["kategori"]:
            qs = qs.filter(category__identifier__in=sel["kategori"])
        if sel["wilayah"]:
            qs = qs.filter(regions__name__in=sel["wilayah"])
        if sel["feature"]:
            fq = Q()
            for f in sel["feature"]:
                fl = f.lower()
                if fl == "raster":
                    fq |= Q(subtype="raster")
                elif fl in ("polygon", "line", "point"):
                    fq |= Q(attribute_set__attribute_type__icontains=fl)
            if fq:
                qs = qs.filter(fq)

        qs = qs.distinct().order_by(self.SORT_MAP[sort])

        total = qs.count()
        paginator = Paginator(qs, self.PER_PAGE)
        page_obj = paginator.get_page(req.GET.get("page") or 1)
        ctx["datasets"] = [self._row(ds) for ds in page_obj.object_list]
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["total"] = total
        ctx["shown_from"] = page_obj.start_index()
        ctx["shown_to"] = page_obj.end_index()
        ctx["sort"] = sort
        ctx["q"] = q
        ctx["selected"] = sel
        ctx["page_list"] = self._page_list(page_obj.number, paginator.num_pages)

        # ── Opsi filter + jumlah (facet, dihitung dari base) ───────
        ctx["filter_pengelola"] = self._facet(base, "owner__organization")
        ctx["filter_walidata"] = self._facet_walidata(base)
        ctx["filter_kategori"] = self._facet_category(base)
        ctx["filter_feature"] = self._facet_feature(base)
        ctx["filter_wilayah"] = self._facet(base, "regions__name")

        # ── Querystring (tanpa page) untuk link paginasi ───────────
        params = req.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()

        # ── Identitas situs/tema (header & footer) ─────────────────
        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""
        try:
            from .models import SiteIdentity

            ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or "(Kabupaten Abc)"
        except Exception:
            ctx["nama_kabupaten"] = ""
        ctx["has_active_filter"] = any(sel.values()) or bool(q)
        return ctx

    # ── Helper facet ───────────────────────────────────────────────
    @staticmethod
    def _facet(base, field):
        from django.db.models import Count

        rows = (
            base.exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values(field)
            .annotate(c=Count("id", distinct=True))
            .order_by("-c", field)
        )
        return [{"value": r[field], "label": r[field], "count": r["c"]} for r in rows]

    @staticmethod
    def _facet_poc(base):
        from django.db.models import Count

        rows = (
            base.filter(contactrole__role="pointOfContact")
            .exclude(contactrole__contact__organization__isnull=True)
            .exclude(contactrole__contact__organization="")
            .values("contactrole__contact__organization")
            .annotate(c=Count("id", distinct=True))
            .order_by("-c", "contactrole__contact__organization")
        )
        return [
            {
                "value": r["contactrole__contact__organization"],
                "label": r["contactrole__contact__organization"],
                "count": r["c"],
            }
            for r in rows
        ]

    @staticmethod
    def _facet_category(base):
        from django.db.models import Count

        rows = (
            base.exclude(category__isnull=True)
            .values("category__identifier", "category__gn_description")
            .annotate(c=Count("id", distinct=True))
            .order_by("-c")
        )
        out = []
        for r in rows:
            label = r["category__gn_description"] or r["category__identifier"]
            if label:
                out.append({"value": r["category__identifier"], "label": label, "count": r["c"]})
        return out

    @staticmethod
    def _facet_feature(base):
        feats = []
        for label, key in (("Polygon", "polygon"), ("Line", "line"), ("Point", "point")):
            c = base.filter(attribute_set__attribute_type__icontains=key).distinct().count()
            if c:
                feats.append({"value": label, "label": label, "count": c})
        rc = base.filter(subtype="raster").count()
        if rc:
            feats.append({"value": "Raster", "label": "Raster", "count": rc})
        return feats

    @staticmethod
    def _page_list(current, num_pages):
        """Daftar nomor halaman dengan elipsis (None) untuk window ringkas."""
        if num_pages <= 7:
            return list(range(1, num_pages + 1))
        pages = [1]
        if current - 1 > 2:
            pages.append(None)
        for p in range(max(2, current - 1), min(num_pages - 1, current + 1) + 1):
            pages.append(p)
        if current + 1 < num_pages - 1:
            pages.append(None)
        pages.append(num_pages)
        return pages


def _backup_dir():
    import os as _os

    return _os.environ.get("DST_DB_BACKUP_DIR", "/pg_backups")


def _human_size(num):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024 or unit == "TB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024.0


def list_db_backups():
    """Daftar berkas backup database di DST_DB_BACKUP_DIR (terbaru dulu)."""
    import os as _os
    from datetime import datetime

    backup_dir = _backup_dir()
    exts = (
        ".sql", ".sql.gz", ".gz", ".dump", ".backup", ".bak",
        ".tar", ".tar.gz", ".tgz", ".zip", ".bz2", ".xz", ".pgdump",
    )
    rows = []
    try:
        for name in _os.listdir(backup_dir):
            path = _os.path.join(backup_dir, name)
            if not _os.path.isfile(path):
                continue
            if not name.lower().endswith(exts):
                continue
            st = _os.stat(path)
            rows.append(
                {
                    "name": name,
                    "size": _human_size(st.st_size),
                    "mtime": datetime.fromtimestamp(st.st_mtime),
                }
            )
    except OSError:
        pass
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return rows, backup_dir


def backup_download(request):
    """Unduh satu berkas backup database (Super Admin saja)."""
    import os as _os
    from django.http import FileResponse, Http404, HttpResponseForbidden

    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("Hanya Super Admin yang dapat mengunduh backup.")

    backup_dir = _backup_dir()
    name = _os.path.basename((request.GET.get("name") or "").strip())
    if not name:
        raise Http404("Nama berkas backup wajib disertakan.")

    real_dir = _os.path.realpath(backup_dir)
    real_path = _os.path.realpath(_os.path.join(backup_dir, name))
    # Cegah path traversal: berkas harus benar-benar di dalam direktori backup.
    if not real_path.startswith(real_dir + _os.sep) or not _os.path.isfile(real_path):
        raise Http404("Berkas backup tidak ditemukan.")

    return FileResponse(open(real_path, "rb"), as_attachment=True, filename=name)


def wilayah_kabupaten_options(request):
    """JSON daftar kabupaten/kota (kode PUM + nama) pada satu provinsi (dari BIG).

    Dipakai dropdown dependent di seksi 'Restore Data Wilayah'. Hanya untuk
    staff/superuser; hasil di-cache 24 jam agar tidak memukul BIG berulang.
    """
    from django.http import JsonResponse

    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser
    ):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    kode_prov = (request.GET.get("prov") or "").strip()
    if not kode_prov:
        return JsonResponse({"ok": True, "options": []})
    try:
        from django.core.cache import cache
        from .management.commands.sync_wilayah_big import fetch_kabupaten_options

        ckey = f"wilayah_kab_options_{kode_prov}"
        opts = cache.get(ckey)
        if opts is None:
            opts = fetch_kabupaten_options(kode_prov)
            cache.set(ckey, opts, 60 * 60 * 24)
        return JsonResponse({"ok": True, "options": opts})
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)


def wilayah_kecdesa_options(request):
    """JSON kecamatan + desa/kelurahan untuk satu kabupaten/kota (kode PUM).

    HYBRID: bila kabupaten yang diminta adalah region cakupan AKTIF (datanya ada
    di ``RefWilayah*`` hasil restore BIG) -> kembalikan data nyata itu; selain
    itu -> pratinjau dari crosswalk nasional permanen ``RefKodeBps``. Dipakai
    panel 'Data Kecamatan & Desa/Kelurahan' di seksi Restore Data Wilayah, yang
    terhubung ke dropdown Kabupaten/Kota.
    """
    from django.http import JsonResponse

    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser
    ):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    kab = (request.GET.get("kab") or "").strip()
    if not kab:
        return JsonResponse({"ok": True, "source": "", "kecamatan": [], "desa": []})

    from .models import RefKodeBps, RefWilayahDesa, RefWilayahKecamatan

    if RefWilayahKecamatan.objects.filter(kode_kab_pum=kab).exists():
        source = "aktif"
        kec_rows = (
            RefWilayahKecamatan.objects.filter(kode_kab_pum=kab)
            .order_by("kode_pum").values("kode_pum", "kode_bps", "nama")
        )
        desa = [
            {"pum": d["kode_pum"], "bps": d["kode_bps"], "nama": d["nama"],
             "kec": d["kode_kec_pum"]}
            for d in RefWilayahDesa.objects.filter(kode_kab_pum=kab)
            .order_by("kode_pum")
            .values("kode_pum", "kode_bps", "nama", "kode_kec_pum")
        ]
    else:
        source = "nasional"
        kec_rows = (
            RefKodeBps.objects.filter(level="kecamatan", kode_pum__startswith=kab + ".")
            .order_by("kode_pum").values("kode_pum", "kode_bps", "nama")
        )
        # RefKodeBps desa tak punya kolom kode_kec; induk = pum tanpa ruas akhir.
        desa = [
            {"pum": d["kode_pum"], "bps": d["kode_bps"], "nama": d["nama"],
             "kec": d["kode_pum"].rsplit(".", 1)[0]}
            for d in RefKodeBps.objects.filter(level="desa", kode_pum__startswith=kab + ".")
            .order_by("kode_pum").values("kode_pum", "kode_bps", "nama")
        ]

    kecamatan = [{"pum": k["kode_pum"], "bps": k["kode_bps"], "nama": k["nama"]}
                 for k in kec_rows]
    return JsonResponse({"ok": True, "source": source,
                         "kecamatan": kecamatan, "desa": desa})


class DocumentExploreView(TemplateView):
    """Halaman Jelajah Dokumen Kebijakan — paginasi server-side sejati.

    Prinsip sama dengan DatasetExploreView, tetapi filter disesuaikan dengan
    field yang tersedia di tabel Document: Pengelola (owner.organization),
    Walidata (poc), Kategori (TopicCategory), Tahun (date), Format (extension),
    dan Wilayah (regions).
    """

    template_name = "dst-district/document_explore.html"
    PER_PAGE = 12

    SORT_MAP = {
        "recent": "-last_updated",
        "az": "title",
        "year": "-date",
        "views": "-popular_count",
    }

    @staticmethod
    def _walidata(doc):
        return document_walidata_label(doc)

    @staticmethod
    def _facet_walidata(base):
        """Daftar filter Walidata: gabungan tautan master + fallback poc.org."""
        from django.db.models import Count
        from .models import DocumentWalidata

        counts = {}
        for r in (
            DocumentWalidata.objects.filter(document__in=base)
            .values("walidata__nama")
            .annotate(c=Count("document", distinct=True))
        ):
            lbl = r["walidata__nama"]
            if lbl:
                counts[lbl] = counts.get(lbl, 0) + r["c"]
        linked_ids = DocumentWalidata.objects.values_list("document_id", flat=True)
        for r in (
            base.exclude(pk__in=linked_ids)
            .filter(contactrole__role="pointOfContact")
            .exclude(contactrole__contact__organization__isnull=True)
            .exclude(contactrole__contact__organization="")
            .values("contactrole__contact__organization")
            .annotate(c=Count("id", distinct=True))
        ):
            lbl = r["contactrole__contact__organization"]
            if lbl:
                counts[lbl] = counts.get(lbl, 0) + r["c"]
        return [
            {"value": k, "label": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        ]

    def _row(self, d):
        if d.category and (d.category.gn_description or d.category.identifier):
            doc_type = d.category.gn_description or d.category.identifier
        else:
            doc_type = "Dokumen"
        kategori = ""
        if d.category and (d.category.gn_description or d.category.identifier):
            kategori = d.category.gn_description or d.category.identifier
        year = d.date.year if d.date else (d.last_updated.year if d.last_updated else "")
        return {
            "id": d.pk,
            "title": d.title or "",
            "doc_type": doc_type,
            "pengelola": user_org_label(d.owner),
            "walidata": self._walidata(d),
            "kategori": kategori,
            "year": year,
            "updated": d.last_updated or d.date,
            "extension": (d.extension or "").upper(),
            "regions": ", ".join(r.name for r in d.regions.all()),
            "thumbnail_url": d.thumbnail_url or "",
        }

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        from django.db.models import Count, Q
        from django.db.models.functions import ExtractYear

        ctx = super().get_context_data(**kwargs)
        req = self.request

        base = Document.objects.filter(is_published=True, is_approved=True)

        sel = {
            "pengelola": req.GET.getlist("pengelola"),
            "walidata": req.GET.getlist("walidata"),
            "kategori": req.GET.getlist("kategori"),
            "tahun": req.GET.getlist("tahun"),
            "format": req.GET.getlist("format"),
            "wilayah": req.GET.getlist("wilayah"),
        }
        sort = req.GET.get("sort", "recent")
        if sort not in self.SORT_MAP:
            sort = "recent"

        # Pencarian teks bebas (dari kotak Pencarian Data di Landing / bar explore).
        q = (req.GET.get("q") or "").strip()

        qs = base.select_related("owner", "category").prefetch_related("regions")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(abstract__icontains=q)
                | Q(keywords__name__icontains=q)
            )
        if sel["pengelola"]:
            qs = qs.filter(owner__organization__in=sel["pengelola"])
        if sel["walidata"]:
            from .models import DocumentWalidata

            wanted = sel["walidata"]
            bridge_ids = set(
                DocumentWalidata.objects.filter(walidata__nama__in=wanted)
                .values_list("document_id", flat=True)
            )
            linked_ids = set(
                DocumentWalidata.objects.values_list("document_id", flat=True)
            )
            legacy_ids = set(
                base.filter(
                    contactrole__role="pointOfContact",
                    contactrole__contact__organization__in=wanted,
                )
                .exclude(pk__in=linked_ids)
                .values_list("pk", flat=True)
            )
            qs = qs.filter(pk__in=bridge_ids | legacy_ids)
        if sel["kategori"]:
            qs = qs.filter(category__identifier__in=sel["kategori"])
        if sel["wilayah"]:
            qs = qs.filter(regions__name__in=sel["wilayah"])
        if sel["format"]:
            qs = qs.filter(extension__in=[f.lower() for f in sel["format"]])
        if sel["tahun"]:
            years = [int(y) for y in sel["tahun"] if y.isdigit()]
            if years:
                qs = qs.filter(date__year__in=years)

        qs = qs.distinct().order_by(self.SORT_MAP[sort])

        total = qs.count()
        paginator = Paginator(qs, self.PER_PAGE)
        page_obj = paginator.get_page(req.GET.get("page") or 1)
        ctx["documents"] = [self._row(d) for d in page_obj.object_list]
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["total"] = total
        ctx["shown_from"] = page_obj.start_index()
        ctx["shown_to"] = page_obj.end_index()
        ctx["sort"] = sort
        ctx["q"] = q
        ctx["selected"] = sel
        ctx["page_list"] = DatasetExploreView._page_list(page_obj.number, paginator.num_pages)

        # Facet (dihitung dari base)
        ctx["filter_pengelola"] = DatasetExploreView._facet(base, "owner__organization")
        ctx["filter_walidata"] = self._facet_walidata(base)
        ctx["filter_kategori"] = DatasetExploreView._facet_category(base)
        ctx["filter_wilayah"] = DatasetExploreView._facet(base, "regions__name")
        # Format (ekstensi)
        ext_rows = (
            base.exclude(extension__isnull=True).exclude(extension="")
            .values("extension").annotate(c=Count("id", distinct=True)).order_by("-c")
        )
        ctx["filter_format"] = [
            {"value": r["extension"], "label": (r["extension"] or "").upper(), "count": r["c"]}
            for r in ext_rows
        ]
        # Tahun (dari date)
        year_rows = (
            base.exclude(date__isnull=True)
            .annotate(yr=ExtractYear("date")).values("yr")
            .annotate(c=Count("id", distinct=True)).order_by("-yr")
        )
        ctx["filter_tahun"] = [
            {"value": str(r["yr"]), "label": str(r["yr"]), "count": r["c"]}
            for r in year_rows if r["yr"]
        ]

        params = req.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()

        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""
        try:
            from .models import SiteIdentity

            ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or "(Kabupaten Abc)"
        except Exception:
            ctx["nama_kabupaten"] = ""
        ctx["has_active_filter"] = any(sel.values()) or bool(q)
        return ctx


def _endpoint_explore_data(geoserver_url):
    """Daftar endpoint REST v2 + OGC services & statistik katalog.

    SUMBER TUNGGAL dipakai ``EndpointApiExploreView`` (HTML) dan
    ``api_endpoint_explore`` (JSON Next.js). Tiap item = tuple
    ``(method, path, desc, count|None)``.
    """
    from geonode.base.models import (
        ResourceBase,
        TopicCategory,
        Region,
        HierarchicalKeyword,
    )
    from geonode.maps.models import Map
    from geonode.groups.models import GroupProfile

    gs = geoserver_url if geoserver_url else "/geoserver"

    rest_resources = [
        ("GET", "/api/v2/datasets", "Daftar layer spasial (Dataset).", Dataset.objects.count()),
        ("GET", "/api/v2/datasets/{id}", "Detail layer berdasarkan ID.", None),
        ("GET", "/api/v2/documents", "Daftar dokumen kebijakan.", Document.objects.count()),
        ("GET", "/api/v2/documents/{id}", "Detail dokumen berdasarkan ID.", None),
        ("GET", "/api/v2/maps", "Daftar peta interaktif.", Map.objects.count()),
        ("GET", "/api/v2/resources", "Gabungan dataset + dokumen + map.", ResourceBase.objects.count()),
    ]
    rest_vocab = [
        ("GET", "/api/v2/categories", "Topic Category ISO 19115.", TopicCategory.objects.count()),
        ("GET", "/api/v2/keywords", "HierarchicalKeyword (tag).", HierarchicalKeyword.objects.count()),
        ("GET", "/api/v2/regions", "Region geografis.", Region.objects.count()),
        ("GET", "/api/v2/groups", "Group profile.", GroupProfile.objects.count()),
    ]
    ogc_services = [
        ("WMS", f"{gs}/wms", "Web Map Service — render peta sebagai gambar.", None),
        ("WFS", f"{gs}/wfs", "Web Feature Service — query fitur vektor.", None),
        ("WCS", f"{gs}/wcs", "Web Coverage Service — raster.", None),
        ("WMTS", f"{gs}/gwc/service/wmts", "Web Map Tile Service — tile pre-rendered.", None),
        ("CSW", "/catalogue/csw", "Catalogue Service for the Web — pencarian metadata.", None),
    ]
    groups = [
        {"title": "REST · Resources", "items": rest_resources},
        {"title": "REST · Vocabulary", "items": rest_vocab},
        {"title": "OGC Services", "items": ogc_services},
    ]
    stats = {
        "total_endpoints": sum(len(g["items"]) for g in groups),
        "resources": ResourceBase.objects.count(),
        "datasets": Dataset.objects.count(),
        "documents": Document.objects.count(),
        "ogc_services": len(ogc_services),
    }
    return groups, stats


def api_endpoint_explore(request):
    """JSON daftar endpoint API & OGC untuk frontend Next.js — payload identik
    ``EndpointApiExploreView``. URL publik dibangun dari ``SITEURL`` (bukan host
    request, agar benar saat SSR memanggil lewat django:8000). Read-only.
    """
    from django.http import JsonResponse
    from django.conf import settings as dj_settings

    base_url = (getattr(dj_settings, "SITEURL", "") or "http://localhost/").rstrip("/")
    geoserver_url = f"{base_url}/geoserver"
    groups_raw, stats = _endpoint_explore_data(geoserver_url)

    def to_item(method, path, desc, count):
        # Aksi & tautan publik — selaras logika template endpoint_explore.html.
        if "{" in path:
            link, link_label = "", ""
        elif path.startswith("http"):
            link, link_label = f"{path}?service={method}&request=GetCapabilities", "GetCaps"
        elif path.startswith("/"):
            link, link_label = base_url + path, "Buka"
        else:
            link, link_label = path, "Buka"
        return {
            "method": method,
            "path": path,
            "desc": desc,
            "count": count,
            "link": link,
            "link_label": link_label,
        }

    groups = [
        {"title": g["title"], "items": [to_item(*it) for it in g["items"]]}
        for g in groups_raw
    ]
    return JsonResponse(
        {
            "base_url": base_url,
            "geoserver_url": geoserver_url,
            "groups": groups,
            "stats": stats,
        }
    )


class EndpointApiExploreView(TemplateView):
    """Halaman publik daftar endpoint API & OGC services (Metadata & API).

    Versi publik (tanpa login) dari ``EndpointApiView`` admin — memakai layout
    Landing agar konsisten dengan halaman Eksplorasi Dataset/Dokumen. Ditautkan
    dari panel "Metadata & API" pada section Pencarian Data di Landing.
    """

    template_name = "dst-district/endpoint_explore.html"

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings

        ctx = super().get_context_data(**kwargs)
        request = self.request
        base_url = f"{request.scheme}://{request.get_host()}"

        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}
        geoserver_url = (ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "").rstrip("/")

        # Daftar endpoint & statistik — sumber tunggal (juga dipakai endpoint
        # JSON api_endpoint_explore untuk frontend Next.js).
        groups, stats = _endpoint_explore_data(geoserver_url)

        ctx["base_url"] = base_url
        ctx["geoserver_url"] = geoserver_url or "—"
        ctx["groups"] = groups
        ctx["stats"] = stats

        # ── Identitas situs/tema (header & footer Landing base) ────
        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""
        try:
            from .models import SiteIdentity

            ctx["nama_kabupaten"] = SiteIdentity.load().nama_kabupaten or "(Kabupaten Abc)"
        except Exception:
            ctx["nama_kabupaten"] = ""
        return ctx


class DstAdminPageView(TemplateView):
    page_slug = ""
    page_title = ""
    breadcrumb = []
    # Bila True, pengguna "Umum" (bukan staff/superuser) boleh membuka halaman.
    umum_allowed = False
    # Bila True, halaman hanya untuk Super Admin (Walidata & Umum diblokir).
    superuser_only = False

    @staticmethod
    def _is_umum(user):
        return bool(
            getattr(user, "is_authenticated", False)
            and not user.is_staff
            and not user.is_superuser
        )

    def dispatch(self, request, *args, **kwargs):
        u = request.user
        # Pengguna Umum hanya boleh halaman yang umum_allowed (Dashboard, Profil).
        if self._is_umum(u) and not self.umum_allowed:
            messages.info(
                request, "Akun Umum hanya memiliki akses ke Dashboard dan Profil."
            )
            return redirect(reverse("dst_auth:dashboard"))
        # Halaman Administrasi khusus Super Admin: blokir Walidata & lainnya.
        if self.superuser_only and getattr(u, "is_authenticated", False) and not u.is_superuser:
            messages.error(request, "Halaman ini hanya dapat diakses oleh Super Admin.")
            return redirect(reverse("dst_auth:dashboard"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.page_slug
        ctx["page_title"] = self.page_title
        ctx["breadcrumb"] = [
            {"label": label, "url": url} for label, url in self.breadcrumb
        ]
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
        except Exception:
            theme = None
        ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""

        user = self.request.user
        if user.is_authenticated:
            display_name = (user.get_full_name() or user.username or "").strip()
            parts = display_name.split()
            if len(parts) >= 2:
                initials = (parts[0][:1] + parts[1][:1]).upper()
            elif parts:
                initials = parts[0][:2].upper()
            else:
                initials = "U"
            if user.is_superuser:
                role = "Super Admin"
            elif user.is_staff:
                role = "Admin Walidata"
            else:
                role = "Pengguna"
        else:
            display_name = ""
            initials = "?"
            role = "Tamu"
        ctx["sidebar_user_name"] = display_name
        ctx["sidebar_user_initials"] = initials
        ctx["sidebar_user_role"] = role

        photo_url = ""
        if user.is_authenticated:
            from avatar.utils import get_primary_avatar

            avatar = get_primary_avatar(user, width=80)
            if avatar:
                photo_url = avatar.avatar_url(80, 80)
        ctx["sidebar_user_photo_url"] = photo_url

        try:
            ctx["site"] = fresh_site()
        except Exception:
            ctx["site"] = None

        # Peta tampil/sembunyi menu sidebar (dipakai _sidebar.html di semua
        # halaman admin). Umum: hanya Dashboard. Walidata: tanpa grup Administrasi.
        user = self.request.user
        is_umum = self._is_umum(user)
        is_walidata = bool(
            getattr(user, "is_authenticated", False)
            and user.is_staff
            and not user.is_superuser
        )
        ctx["is_umum"] = is_umum
        try:
            from .models import SidebarMenu

            if is_umum:
                menus = {key: False for key, _, _, _ in SidebarMenu.MENUS}
                menus["dashboard"] = True
            elif is_walidata:
                # Walidata pakai kolom visible_walidata; Administrasi selalu off.
                menus = SidebarMenu.visibility_map(role="walidata")
                for key, _, grup, _ in SidebarMenu.MENUS:
                    if grup == "Administrasi":
                        menus[key] = False
            else:
                # Super Admin pakai kolom is_visible.
                menus = SidebarMenu.visibility_map(role="super")
            ctx["sidebar_menus"] = menus

            # Header section disembunyikan bila semua menunya tersembunyi.
            group_slug = {
                "Ringkasan": "ringkasan",
                "Pengelolaan Data": "pengelolaan",
                "Distribusi & Akses": "distribusi",
                "Administrasi": "administrasi",
                "Tautan": "tautan",
            }
            sections = {}
            for key, _, grup, _ in SidebarMenu.MENUS:
                slug = group_slug.get(grup, grup)
                sections[slug] = sections.get(slug, False) or bool(menus.get(key))
            ctx["sidebar_sections"] = sections
        except Exception:
            ctx["sidebar_menus"] = {"dashboard": True} if is_umum else {}
            ctx["sidebar_sections"] = {"ringkasan": True}
        return ctx


class DashboardView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/dashboard.html"
    page_slug = "dashboard"
    page_title = "Dashboard"
    breadcrumb = [("Dashboard", None)]
    umum_allowed = True  # Dashboard = satu-satunya menu untuk pengguna Umum

    def get_template_names(self):
        if self._is_umum(self.request.user):
            return ["dst-district/admin/dashboard_umum.html"]
        return [self.template_name]

    def _umum_context(self, ctx, user):
        """Dashboard ringkas pengguna Umum: log aktivitas Screening miliknya."""
        logs = list(user.screening_logs.all()[:100])
        ctx["umum_name"] = (user.get_full_name() or user.username).strip()
        ctx["screening_logs"] = logs
        ctx["screening_total"] = user.screening_logs.count()
        ctx["screening_last"] = logs[0].created if logs else None
        return ctx

    VERB_DOT = {
        "uploaded": "upload",
        "created": "upload",
        "published": "publish",
        "approved": "publish",
        "changed": "review",
        "updated": "review",
        "deleted": "archive",
        "archived": "archive",
        "harvested": "harvest",
        "downloaded": "harvest",
    }

    def get_context_data(self, **kwargs):
        from django.apps import apps as dj_apps
        from geonode.maps.models import Map

        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if ctx.get("is_umum"):
            return self._umum_context(ctx, user)
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        first_name = (user.first_name or user.username or "").strip() or "Pengelola"
        from zoneinfo import ZoneInfo
        from .models import SiteIdentity

        _identity = SiteIdentity.load()
        tz_iana = _identity.iana_timezone
        tz_label = _identity.timezone
        hour = now.astimezone(ZoneInfo(tz_iana)).hour
        if 4 <= hour < 11:
            greeting = "Selamat pagi"
        elif 11 <= hour < 15:
            greeting = "Selamat siang"
        elif 15 <= hour < 18:
            greeting = "Selamat sore"
        else:
            greeting = "Selamat malam"

        ds_total = Dataset.objects.count()
        doc_total = Document.objects.count()
        map_total = Map.objects.count()
        total_resources = ds_total + doc_total + map_total

        ds_pub = Dataset.objects.filter(is_published=True, is_approved=True).count()
        doc_pub = Document.objects.filter(is_published=True, is_approved=True).count()
        map_pub = Map.objects.filter(is_published=True, is_approved=True).count()
        total_pub = ds_pub + doc_pub + map_pub

        new_week = (
            Dataset.objects.filter(created__gte=week_ago).count()
            + Document.objects.filter(created__gte=week_ago).count()
        )

        activity_24h = Action.objects.filter(timestamp__gte=day_ago).count()
        activity_7d = Action.objects.filter(timestamp__gte=week_ago).count()
        last_action = Action.objects.order_by("-timestamp").first()

        review_docs_qs = Document.objects.filter(is_published=True, is_approved=False).order_by(
            "-last_updated"
        )
        review_datasets_qs = Dataset.objects.filter(is_published=True, is_approved=False).order_by(
            "-last_updated"
        )
        draft_docs_qs = Document.objects.filter(is_published=False).order_by("-last_updated")
        draft_datasets_qs = Dataset.objects.filter(is_published=False).order_by("-last_updated")
        no_abstract_ds = (
            Dataset.objects.filter(is_published=True)
            .filter(Q(abstract__isnull=True) | Q(abstract=""))
            .order_by("-last_updated")
        )

        attention_items = []
        if review_docs_qs.exists() or review_datasets_qs.exists():
            attention_items.append(
                {
                    "tone": "urgent",
                    "icon": "doc",
                    "title": f"{review_docs_qs.count() + review_datasets_qs.count()} resource menunggu approval",
                    "desc": ", ".join(
                        [d.title for d in list(review_docs_qs[:2]) + list(review_datasets_qs[:1])]
                    )
                    or "Lihat daftar review",
                    "url": "/dst-auth/dokumen/",
                }
            )
        if draft_docs_qs.exists() or draft_datasets_qs.exists():
            attention_items.append(
                {
                    "tone": "warn",
                    "icon": "info",
                    "title": f"{draft_docs_qs.count() + draft_datasets_qs.count()} draft belum dipublish",
                    "desc": ", ".join(
                        [d.title for d in list(draft_datasets_qs[:2]) + list(draft_docs_qs[:1])]
                    )
                    or "Selesaikan draft",
                    "url": "/dst-auth/data-spasial/",
                }
            )
        if no_abstract_ds.exists():
            attention_items.append(
                {
                    "tone": "info",
                    "icon": "warn",
                    "title": f"{no_abstract_ds.count()} layer tanpa abstract",
                    "desc": ", ".join(d.title for d in no_abstract_ds[:2]) or "Lengkapi metadata",
                    "url": "/dst-auth/data-spasial/",
                }
            )
        attention_total = sum(1 for _ in attention_items)

        recent_actions = (
            Action.objects.select_related(
                "actor_content_type", "action_object_content_type"
            )
            .order_by("-timestamp")[:7]
        )
        activity_rows = []
        for a in recent_actions:
            target = a.action_object or a.target
            target_label = (
                getattr(target, "title", None)
                or getattr(target, "name", None)
                or (a.data or {}).get("object_name")
                or ""
            )
            target_type = (
                a.action_object_content_type.model if a.action_object_content_type else ""
            )
            actor_name = (
                a.actor.get_full_name() if hasattr(a.actor, "get_full_name") else ""
            ) or getattr(a.actor, "username", None) or str(a.actor or "Sistem")
            activity_rows.append(
                {
                    "dot": self.VERB_DOT.get((a.verb or "").lower(), "review"),
                    "verb": a.verb,
                    "actor": actor_name,
                    "target": target_label,
                    "target_type": target_type,
                    "timestamp": a.timestamp,
                }
            )

        try:
            Application = dj_apps.get_model("oauth2_provider", "Application")
            consumer_count = Application.objects.count()
        except LookupError:
            consumer_count = 0

        # Endpoint usage proxy: how many resources each service can serve
        endpoint_counts = [
            {"label": "CSW", "code": "csw", "value": total_pub, "max": total_resources},
            {"label": "WMS", "code": "wms", "value": ds_pub, "max": ds_total},
            {"label": "WFS", "code": "wfs", "value": Dataset.objects.filter(is_published=True, is_approved=True, subtype__in=["vector", "vector_time"]).count(), "max": ds_total},
            {"label": "WCS", "code": "wcs", "value": Dataset.objects.filter(is_published=True, is_approved=True, subtype="raster").count(), "max": ds_total},
            {"label": "REST", "code": "rest", "value": total_pub, "max": total_resources},
        ]
        for ep in endpoint_counts:
            ep["pct"] = (
                int(round(ep["value"] * 100 / ep["max"])) if ep["max"] else 0
            )

        ctx["greeting"] = {
            "salutation": greeting,
            "name": first_name,
            "now": now,
            "tz_iana": tz_iana,
            "tz_label": tz_label,
            "attention_count": attention_total,
        }
        ctx["stats"] = {
            "total_resources": total_resources,
            "new_week": new_week,
            "ds_total": ds_total,
            "doc_total": doc_total,
            "map_total": map_total,
            "total_pub": total_pub,
            "pub_pct": int(round(total_pub * 100 / total_resources)) if total_resources else 0,
            "activity_24h": activity_24h,
            "activity_7d": activity_7d,
            "last_action": last_action.timestamp if last_action else None,
            "attention": attention_total,
        }
        ctx["activity_rows"] = activity_rows
        ctx["attention_items"] = attention_items
        ctx["endpoint_counts"] = endpoint_counts
        ctx["consumer_count"] = consumer_count
        return ctx


class DokumenView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/dokumen.html"
    page_slug = "dokumen"
    page_title = "Dokumen Kebijakan"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Dokumen Kebijakan", None)]
    paginate_by = 7

    SORT_MAP = {
        "title": "title",
        "-title": "-title",
        "date": "date",
        "-date": "-date",
        "updated": "last_updated",
        "-updated": "-last_updated",
    }
    PER_PAGE_OPTIONS = [10, 50, 100, 200]

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from geonode.base.models import TopicCategory

        ctx = super().get_context_data(**kwargs)

        base_qs = (
            Document.objects.select_related("owner", "category", "group")
            .prefetch_related("keywords")
        )

        total = base_qs.count()
        published = base_qs.filter(is_published=True, is_approved=True).count()
        review = base_qs.filter(is_published=True, is_approved=False).count()
        draft = base_qs.filter(is_published=False).count()
        with_abstract = base_qs.exclude(abstract__isnull=True).exclude(abstract="").count()

        status = (self.request.GET.get("status") or "all").lower()
        category = (self.request.GET.get("category") or "").strip()
        search = (self.request.GET.get("q") or "").strip()
        sort = (self.request.GET.get("sort") or "-updated").strip()

        qs = base_qs
        if status == "published":
            qs = qs.filter(is_published=True, is_approved=True)
        elif status == "review":
            qs = qs.filter(is_published=True, is_approved=False)
        elif status == "draft":
            qs = qs.filter(is_published=False)

        if category:
            qs = qs.filter(category__identifier=category)

        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(abstract__icontains=search)
                | Q(keywords__name__icontains=search)
            ).distinct()

        qs = qs.order_by(self.SORT_MAP.get(sort, "-last_updated"))

        category_counts = list(
            TopicCategory.objects.annotate(used=Count("resourcebase"))
            .filter(used__gt=0, resourcebase__document__isnull=False)
            .annotate(doc_used=Count("resourcebase__document"))
            .order_by("-doc_used", "identifier")[:8]
        )

        # Jumlah record per halaman: pilihan 10/50/100/200 (default 10).
        try:
            per_page = int(self.request.GET.get("per_page") or self.PER_PAGE_OPTIONS[0])
        except (TypeError, ValueError):
            per_page = self.PER_PAGE_OPTIONS[0]
        if per_page not in self.PER_PAGE_OPTIONS:
            per_page = self.PER_PAGE_OPTIONS[0]

        paginator = Paginator(qs, per_page)
        page_number = self.request.GET.get("page") or 1
        page_obj = paginator.get_page(page_number)

        # Label Walidata per dokumen: tautan master (bridge) → organisasi POC.
        for d in page_obj.object_list:
            d.walidata_label = document_walidata_label(d)

        querystring_no_page = []
        for key, value in [
            ("status", status if status != "all" else ""),
            ("category", category),
            ("q", search),
            ("sort", sort if sort != "-updated" else ""),
            ("per_page", str(per_page) if per_page != self.PER_PAGE_OPTIONS[0] else ""),
        ]:
            if value:
                querystring_no_page.append(f"{key}={value}")
        querystring_prefix = "&".join(querystring_no_page)

        ctx["documents"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["status"] = status
        ctx["category"] = category
        ctx["search"] = search
        ctx["sort"] = sort
        ctx["querystring_prefix"] = querystring_prefix
        ctx["per_page"] = per_page
        ctx["per_page_options"] = self.PER_PAGE_OPTIONS
        ctx["category_list"] = category_counts
        ctx["status_counts"] = {
            "all": total,
            "published": published,
            "review": review,
            "draft": draft,
        }
        ctx["stats"] = {
            "total": total,
            "published": published,
            "review": review,
            "draft": draft,
            "metadata_complete": with_abstract,
            "metadata_pct": int(round(with_abstract * 100 / total)) if total else 0,
        }
        return ctx


class DokumenBaruView(LoginRequiredMixin, DstAdminPageView):
    """Tambah Dokumen — HANYA form upload berkas (seperti Add Document GeoNode).

    Judul diambil dari nama berkas; metadata TIDAK diisi di sini. Default
    otomatis: bahasa Indonesia (ind) dan wilayah Indonesia; kategori dibiarkan
    kosong (— Tidak ditetapkan —) dan abstrak diisi teks placeholder. Setelah
    upload, redirect ke halaman edit untuk melengkapi metadata.
    """

    template_name = "dst-district/admin/dokumen_baru.html"
    page_slug = "dokumen_baru"
    page_title = "Tambah Dokumen"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Dokumen Kebijakan", "/dst-auth/dokumen/"),
        ("Tambah Dokumen", None),
    ]

    ALLOWED_EXT = {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "txt", "csv", "zip", "jpg", "jpeg", "png",
    }

    def post(self, request, *args, **kwargs):
        import os
        import tempfile
        from .satudata_docs import create_geonode_document

        f = request.FILES.get("file")
        if not f:
            messages.error(request, "Berkas dokumen wajib diunggah.")
            return redirect(reverse("dst_auth:dokumen_baru"))

        ext = (os.path.splitext(f.name)[1].lstrip(".")).lower()
        if ext not in self.ALLOWED_EXT:
            messages.error(
                request,
                f"Format .{ext} tidak didukung. Gunakan PDF/DOCX/XLSX/PPTX/dll.",
            )
            return redirect(reverse("dst_auth:dokumen_baru"))

        # Judul diambil dari nama berkas (tanpa ekstensi).
        title = (os.path.splitext(os.path.basename(f.name))[0] or f.name)[:255]

        # Simpan ke berkas sementara lalu buat Document GeoNode (helper bersama).
        tmpdir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmpdir, f.name)
        with open(tmp_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        try:
            document = create_geonode_document(
                tmp_path, owner=request.user, title=title, abstract="", ext=ext
            )
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Gagal mengunggah dokumen: {exc}")
            return redirect(reverse("dst_auth:dokumen_baru"))
        finally:
            try:
                os.remove(tmp_path)
                os.rmdir(tmpdir)
            except OSError:
                pass

        messages.success(
            request,
            f"Dokumen '{document.title}' berhasil diunggah. Silakan lengkapi metadata di bawah ini.",
        )
        return redirect(f"{reverse('dst_auth:dokumen_detail')}?id={document.pk}")


class DokumenDetailView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/dokumen_detail.html"
    page_slug = "dokumen_detail"
    page_title = "Edit Dokumen"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Dokumen Kebijakan", "/dst-auth/dokumen/"),
        ("Edit", None),
    ]

    def _get_document(self, request):
        from django.http import Http404

        doc_id = request.GET.get("id") or request.POST.get("id")
        if not doc_id:
            return None
        try:
            return (
                Document.objects.select_related("owner", "category", "license", "group")
                .prefetch_related("keywords", "regions")
                .get(pk=doc_id)
            )
        except (Document.DoesNotExist, ValueError):
            raise Http404("Dokumen tidak ditemukan.")

    def get_context_data(self, **kwargs):
        from django.contrib.contenttypes.models import ContentType
        from geonode.base.models import TopicCategory, License, Region

        ctx = super().get_context_data(**kwargs)
        document = self._get_document(self.request)
        ctx["document"] = document
        if document is None:
            return ctx

        try:
            files = list(document.files)
        except Exception:
            files = []

        try:
            ct = ContentType.objects.get_for_model(Document)
            recent_actions = list(
                Action.objects.filter(
                    action_object_content_type=ct,
                    action_object_object_id=str(document.pk),
                ).order_by("-timestamp")[:6]
            )
        except Exception:
            recent_actions = []

        activity_rows = []
        for a in recent_actions:
            actor_name = (
                a.actor.get_full_name() if hasattr(a.actor, "get_full_name") else ""
            ) or getattr(a.actor, "username", None) or str(a.actor or "Sistem")
            activity_rows.append({
                "verb": a.verb,
                "actor": actor_name,
                "timestamp": a.timestamp,
            })

        abstract_text = (document.abstract or "").strip()
        abstract_placeholders = {
            "", "no abstract provided", "no abstract", "n/a", "-",
            "abstrak / ringkasan belum tersedia",
        }
        has_real_abstract = abstract_text.lower() not in abstract_placeholders
        # Bila belum ada abstrak nyata, isi field dengan teks default.
        abstract_display = (
            document.abstract if has_real_abstract else "Abstrak / Ringkasan belum tersedia"
        )

        selected_region_ids = list(document.regions.values_list("pk", flat=True))
        keywords_csv = ", ".join(k.name for k in document.keywords.all())

        # Hanya tampilkan kategori dengan is_choice=True; tetap sertakan kategori
        # dokumen saat ini meski is_choice=False agar tidak hilang dari pilihan.
        from django.db.models import Q

        cat_filter = Q(is_choice=True)
        if document.category_id:
            cat_filter |= Q(pk=document.category_id)
        ctx["categories"] = TopicCategory.objects.filter(cat_filter).order_by("identifier")
        ctx["licenses"] = License.objects.all().order_by("name")
        # Region / Cakupan: autocomplete seluruh wilayah Indonesia (prov + kab/kota).
        ctx.update(region_autocomplete_context(document))
        ctx["walidata_users"] = (
            User.objects.exclude(pk=-1)
            .filter(Q(is_staff=True) | Q(is_superuser=True))
            .order_by("username")
        )
        # Walidata = instansi dari tabel master (Daftar Walidata), bukan user POC.
        from .models import Walidata, DocumentWalidata

        ctx["walidata_list"] = Walidata.objects.all().order_by("urutan", "nama", "id")
        wlink = DocumentWalidata.objects.filter(document=document).first()
        ctx["current_walidata_id"] = wlink.walidata_id if wlink else None
        ctx["files"] = files
        ctx["activity_rows"] = activity_rows
        ctx["has_real_abstract"] = has_real_abstract
        ctx["abstract_display"] = abstract_display
        ctx["selected_region_ids"] = selected_region_ids
        ctx["keywords_csv"] = keywords_csv
        poc_user = resolve_contact_user(getattr(document, "poc", None))
        ctx["current_poc_id"] = poc_user.pk if poc_user else None
        return ctx

    def post(self, request, *args, **kwargs):
        from geonode.base.models import TopicCategory, License, Region

        document = self._get_document(request)
        if document is None:
            messages.error(request, "Parameter id wajib disertakan.")
            return redirect(reverse("dst_auth:dokumen"))

        action = request.POST.get("action", "save")
        detail_url = f"{reverse('dst_auth:dokumen_detail')}?id={document.pk}"

        if action == "delete":
            if not request.user.is_superuser and document.owner_id != request.user.pk:
                messages.error(request, "Anda tidak punya izin menghapus dokumen ini.")
                return redirect(detail_url)
            title = document.title or f"Dokumen #{document.pk}"
            try:
                document.delete()
                messages.success(request, f"Dokumen '{title}' berhasil dihapus.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menghapus: {exc}")
                return redirect(detail_url)
            return redirect(reverse("dst_auth:dokumen"))

        if action == "archive":
            document.is_published = False
            document.is_approved = False
            document.save(update_fields=["is_published", "is_approved"])
            messages.success(
                request, f"Dokumen '{document.title}' diarsipkan (un-published)."
            )
            return redirect(detail_url)

        title = (request.POST.get("title") or "").strip()
        abstract = (request.POST.get("abstract") or "").strip()
        if not title or not abstract:
            messages.error(request, "Judul dan abstrak wajib diisi.")
            return redirect(detail_url)

        category_id = request.POST.get("category") or ""
        if category_id:
            try:
                document.category = TopicCategory.objects.get(pk=category_id)
            except (TopicCategory.DoesNotExist, ValueError):
                pass

        license_id = request.POST.get("license") or ""
        if license_id:
            try:
                document.license = License.objects.get(pk=license_id)
            except (License.DoesNotExist, ValueError):
                document.license = None
        else:
            document.license = None

        owner_id = request.POST.get("owner") or ""
        if owner_id:
            try:
                document.owner = User.objects.get(pk=owner_id)
            except (User.DoesNotExist, ValueError):
                pass

        # Walidata = instansi dari tabel master (DocumentWalidata), bukan user POC.
        # Boleh dipilih walau instansi belum punya akun pengguna.
        from .models import Walidata, DocumentWalidata

        walidata_id = request.POST.get("walidata") or ""
        if walidata_id:
            try:
                w = Walidata.objects.get(pk=walidata_id)
                DocumentWalidata.objects.update_or_create(
                    document=document, defaults={"walidata": w}
                )
            except (Walidata.DoesNotExist, ValueError):
                pass
        else:
            DocumentWalidata.objects.filter(document=document).delete()

        date_str = (request.POST.get("date") or "").strip()
        if date_str:
            try:
                from datetime import datetime

                document.date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass

        document.title = title[:255]
        document.abstract = abstract
        document.purpose = (request.POST.get("purpose") or "").strip()
        document.language = (
            request.POST.get("language") or document.language or "ind"
        ).strip()[:5]
        document.attribution = (request.POST.get("attribution") or "").strip()[:255]
        document.supplemental_information = (
            request.POST.get("supplemental_information") or ""
        ).strip()
        # Field "Pernyataan Kualitas Data" dihilangkan dari form DST; hanya
        # diperbarui bila benar-benar dikirim agar nilai lama tidak terhapus.
        if "data_quality_statement" in request.POST:
            document.data_quality_statement = (
                request.POST.get("data_quality_statement") or ""
            ).strip()

        visibility = request.POST.get("visibility", "draft")
        document.is_published = visibility == "public"
        # Approval dilakukan oleh Walidata (is_staff) maupun Super Admin.
        if request.user.is_staff or request.user.is_superuser:
            document.is_approved = request.POST.get("is_approved") == "on"

        try:
            document.save()
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Gagal menyimpan: {exc}")
            return redirect(detail_url)

        region_ids = request.POST.getlist("regions")
        if region_ids:
            valid_regions = Region.objects.filter(pk__in=region_ids)
            document.regions.set(valid_regions)
        else:
            document.regions.clear()

        keywords_csv = (request.POST.get("keywords") or "").strip()
        new_keywords = [k.strip() for k in keywords_csv.split(",") if k.strip()][:20]
        try:
            document.keywords.clear()
            if new_keywords:
                document.keywords.add(*new_keywords)
        except Exception:
            pass

        messages.success(
            request, f"Dokumen '{document.title}' berhasil diperbarui."
        )
        return redirect(reverse("dst_auth:dokumen"))


class DataSpasialView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/data_spasial.html"
    page_slug = "data_spasial"
    page_title = "Dataset Spasial"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Dataset Spasial", None)]
    paginate_by = 6

    VECTOR_SUBTYPES = ("vector", "vector_time", "tabular")
    RASTER_SUBTYPES = ("raster",)

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "xml":
            return self._export_xml(request)
        return super().get(request, *args, **kwargs)

    def _filtered_queryset(self, request):
        qs = (
            Dataset.objects.select_related("owner", "category", "group")
            .prefetch_related("keywords", "regions", "attribute_set")
            .order_by("-last_updated")
        )
        filter_type = (request.GET.get("type") or "all").lower()
        if filter_type == "vector":
            qs = qs.filter(subtype__in=self.VECTOR_SUBTYPES)
        elif filter_type == "raster":
            qs = qs.filter(subtype__in=self.RASTER_SUBTYPES)
        q = (request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(name__icontains=q)
                | Q(abstract__icontains=q)
                | Q(keywords__name__icontains=q)
            ).distinct()
        return qs, filter_type

    def _export_xml(self, request):
        from django.http import HttpResponse
        from django.utils import timezone as dj_timezone
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        qs, filter_type = self._filtered_queryset(request)

        root = Element(
            "datasets",
            attrib={
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:dct": "http://purl.org/dc/terms/",
                "generator": "(Nama Aplikasi Anda)",
                "exported_at": dj_timezone.now().isoformat(),
                "filter_type": filter_type,
                "count": str(qs.count()),
            },
        )
        for ds in qs:
            d = SubElement(root, "dataset", attrib={"id": str(ds.pk)})
            SubElement(d, "dc:identifier").text = str(ds.uuid or ds.pk)
            SubElement(d, "dc:title").text = ds.title or ds.name or ""
            if ds.abstract:
                SubElement(d, "dc:description").text = ds.abstract
            if ds.date:
                SubElement(d, "dct:date").text = ds.date.isoformat()
            if ds.last_updated:
                SubElement(d, "dct:modified").text = ds.last_updated.isoformat()
            if ds.owner:
                creator = (
                    ds.owner.get_full_name() or ds.owner.username
                ) if ds.owner else ""
                if creator:
                    SubElement(d, "dc:creator").text = creator
            if ds.category and (ds.category.gn_description or ds.category.identifier):
                SubElement(d, "dc:subject").text = (
                    ds.category.gn_description or ds.category.identifier
                )
            for kw in ds.keywords.all():
                SubElement(d, "dc:subject").text = kw.name
            for r in ds.regions.all():
                SubElement(d, "dc:coverage").text = r.name
            if ds.srid:
                SubElement(
                    d, "dct:spatial", attrib={"srid": ds.srid}
                ).text = ""
                if ds.ll_bbox_polygon:
                    try:
                        ext = ds.ll_bbox_polygon.extent
                        SubElement(d, "dct:Box").text = (
                            f"{ext[0]:.6f},{ext[1]:.6f} {ext[2]:.6f},{ext[3]:.6f}"
                        )
                    except Exception:
                        pass
            if ds.language:
                SubElement(d, "dc:language").text = ds.language
            if ds.license and ds.license.name:
                SubElement(d, "dc:rights").text = ds.license.name
            if ds.attribution:
                SubElement(d, "dc:publisher").text = ds.attribution
            if ds.subtype:
                SubElement(d, "dc:type").text = ds.subtype
            typename = ds.typename or (
                f"{ds.workspace}:{ds.name}" if ds.workspace and ds.name else ""
            )
            if typename:
                SubElement(d, "dc:source").text = typename
            SubElement(
                d, "dc:format"
            ).text = "Raster" if ds.is_raster else "Vector"
            SubElement(d, "status").text = (
                "published" if (ds.is_published and ds.is_approved)
                else "review" if ds.is_published
                else "draft"
            )

        raw = tostring(root, encoding="utf-8", xml_declaration=True)
        pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")
        stamp = dj_timezone.now().strftime("%Y%m%d-%H%M%S")
        suffix = filter_type if filter_type != "all" else "all"
        response = HttpResponse(pretty, content_type="application/xml; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="dst-luwu-datasets-{suffix}-{stamp}.xml"'
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs, filter_type = self._filtered_queryset(self.request)
        search = (self.request.GET.get("q") or "").strip()

        stats_qs = Dataset.objects.all()
        total = stats_qs.count()
        vector = stats_qs.filter(subtype__in=self.VECTOR_SUBTYPES).count()
        raster = stats_qs.filter(subtype__in=self.RASTER_SUBTYPES).count()
        draft = stats_qs.filter(Q(is_published=False) | Q(is_approved=False)).count()
        published = stats_qs.filter(is_published=True, is_approved=True).count()
        with_abstract = (
            stats_qs.exclude(abstract__isnull=True).exclude(abstract="").count()
        )

        paginator = Paginator(qs, self.paginate_by)
        page_number = self.request.GET.get("page") or 1
        page_obj = paginator.get_page(page_number)

        # Label Walidata + tipe fitur (Point/Line/Polygon/Raster) per kartu.
        for d in page_obj.object_list:
            d.walidata_label = dataset_walidata_label(d)
            d.feature_label = dataset_feature_label(d)

        ctx["datasets"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["filter_type"] = filter_type
        ctx["search"] = search
        ctx["stats"] = {
            "total": total,
            "vector": vector,
            "raster": raster,
            "draft": draft,
            "published": published,
            "metadata_complete": with_abstract,
            "metadata_pct": int(round(with_abstract * 100 / total)) if total else 0,
        }
        return ctx


class LayerBaruView(LoginRequiredMixin, DstAdminPageView):
    """Unggah Layer — cukup pilih berkas (ZIP shapefile / GeoPackage).

    Form mengunggah berkas langsung ke endpoint importer GeoNode
    (``/uploads/upload``) via JS; GeoNode memproses impor (PostGIS +
    GeoServer) secara asinkron dan mengambil nama layer dari nama berkas.
    Mirip alur Tambah Dokumen, tetapi memakai pipeline importer spasial.
    """

    template_name = "dst-district/admin/layer_baru.html"
    page_slug = "layer_baru"
    page_title = "Unggah Layer"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Dataset Spasial", "/dst-auth/data-spasial/"),
        ("Unggah Layer", None),
    ]


class LayerDetailView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/layer_detail.html"
    page_slug = "layer_detail"
    page_title = "Detail Layer"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Dataset Spasial", "/dst-auth/data-spasial/"),
        ("Detail Layer", None),
    ]

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from django.conf import settings as dj_settings

        ctx = super().get_context_data(**kwargs)

        dataset_id = self.request.GET.get("id")
        if not dataset_id:
            ctx["dataset"] = None
            return ctx

        try:
            dataset = (
                Dataset.objects.select_related("owner", "category", "license", "group")
                .prefetch_related("keywords", "regions")
                .get(pk=dataset_id)
            )
        except (Dataset.DoesNotExist, ValueError):
            raise Http404("Layer tidak ditemukan.")

        attributes = list(dataset.attribute_set.all().order_by("display_order", "attribute"))

        ll_bbox_text = ""
        if dataset.ll_bbox_polygon:
            try:
                ext = dataset.ll_bbox_polygon.extent
                ll_bbox_text = (
                    f"{ext[0]:.4f}, {ext[1]:.4f} → {ext[2]:.4f}, {ext[3]:.4f}"
                )
            except Exception:
                ll_bbox_text = ""

        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}
        gs_url = (ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "").rstrip("/")
        typename = dataset.typename or (
            f"{dataset.workspace}:{dataset.name}" if dataset.workspace and dataset.name else ""
        )

        if dataset.is_vector():
            _geo = dataset_feature_label(dataset)
            geometry_label = f"Vektor · {_geo if _geo and _geo != 'Vektor' else (dataset.subtype or 'vector')}"
        elif dataset.is_raster:
            geometry_label = "Raster · GeoTIFF"
        elif dataset.subtype == "tabular":
            geometry_label = "Tabular · metadata-only"
        else:
            geometry_label = dataset.subtype or "—"

        published = dataset.is_published
        approved = dataset.is_approved

        endpoints = []
        if typename:
            if dataset.is_vector():
                endpoints.append(
                    {
                        "label": "WMS",
                        "klass": "",
                        "desc": "Tampilan peta (image)",
                        "url": f"{gs_url}/wms?service=WMS&request=GetMap&layers={typename}" if gs_url else "",
                    }
                )
                endpoints.append(
                    {
                        "label": "WFS",
                        "klass": "",
                        "desc": "Akses fitur vektor (GeoJSON)",
                        "url": f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/json" if gs_url else "",
                    }
                )
            elif dataset.is_raster:
                endpoints.append(
                    {
                        "label": "WMS",
                        "klass": "",
                        "desc": "Tampilan raster (image)",
                        "url": f"{gs_url}/wms?service=WMS&request=GetMap&layers={typename}" if gs_url else "",
                    }
                )
                endpoints.append(
                    {
                        "label": "WCS",
                        "klass": "",
                        "desc": "Coverage raster (GeoTIFF)",
                        "url": f"{gs_url}/wcs?service=WCS&coverageId={typename}&request=GetCoverage" if gs_url else "",
                    }
                )
        endpoints.append(
            {
                "label": "REST",
                "klass": "rest",
                "desc": "Metadata JSON",
                "url": f"/api/v2/datasets/{dataset.pk}",
            }
        )

        downloads = []
        if typename and gs_url and dataset.is_vector():
            downloads.append(
                {
                    "kind": "GPKG",
                    "klass": "",
                    "name": "GeoPackage (WFS)",
                    "meta": f"{dataset.srid}",
                    "url": f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/x-gpkg",
                }
            )
            downloads.append(
                {
                    "kind": "SHP",
                    "klass": "zip",
                    "name": "Shapefile (ZIP)",
                    "meta": f"{dataset.srid}",
                    "url": f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=SHAPE-ZIP",
                }
            )
            downloads.append(
                {
                    "kind": "JSON",
                    "klass": "json",
                    "name": "GeoJSON",
                    "meta": "EPSG:4326",
                    "url": f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=application/json&srsName=EPSG:4326",
                }
            )
            downloads.append(
                {
                    "kind": "CSV",
                    "klass": "csv",
                    "name": "Atribut CSV",
                    "meta": "tanpa geometri",
                    "url": f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature&outputFormat=csv",
                }
            )
        downloads.append(
            {
                "kind": "XML",
                "klass": "xml",
                "name": "Metadata ISO 19139",
                "meta": "untuk katalog",
                "url": f"/catalogue/csw?service=CSW&version=2.0.2&request=GetRecordById&id={dataset.uuid}&outputSchema=http://www.isotc211.org/2005/gmd",
            }
        )

        related = (
            Dataset.objects.exclude(pk=dataset.pk)
            .filter(is_published=True, is_approved=True)
        )
        if dataset.category_id:
            related = related.filter(category=dataset.category)
        related = list(related.order_by("-last_updated")[:4])

        owner_label = (
            dataset.owner.get_full_name() if dataset.owner else ""
        ) or (dataset.owner.username if dataset.owner else "—")
        year = dataset.date.year if dataset.date else dataset.last_updated.year if dataset.last_updated else ""
        citation = (
            f"{owner_label} ({year}). {dataset.title}. "
            f"Nama Aplikasi Anda. /api/v2/datasets/{dataset.pk}"
        ).strip()

        uuid_str = str(dataset.uuid or "")
        uuid_short = (
            f"{uuid_str[:8]}…{uuid_str[-4:]}" if len(uuid_str) > 16 else uuid_str
        )

        abstract_text = (dataset.abstract or "").strip()
        abstract_placeholders = {
            "",
            "no abstract provided",
            "no abstract",
            "n/a",
            "-",
        }
        has_real_abstract = abstract_text.lower() not in abstract_placeholders

        ctx["dataset"] = dataset
        ctx["has_real_abstract"] = has_real_abstract
        ctx["geometry_label"] = geometry_label
        ctx["ll_bbox_text"] = ll_bbox_text
        ctx["typename"] = typename
        ctx["attributes"] = attributes
        ctx["attributes_total"] = len(attributes)
        ctx["endpoints"] = endpoints
        ctx["downloads"] = downloads
        ctx["related"] = related
        ctx["status_published"] = published
        ctx["status_approved"] = approved
        ctx["owner_label"] = owner_label
        ctx["walidata_label"] = dataset_walidata_label(dataset)
        ctx["citation"] = citation
        ctx["uuid_short"] = uuid_short or "—"
        ctx["can_edit_thumbnail"] = (
            self.request.user.is_superuser
            or self.request.user.pk == dataset.owner_id
        )
        return ctx

    def post(self, request, *args, **kwargs):
        """Unggah / ganti / hapus gambar (thumbnail) layer dari halaman detail.

        Tanpa tombol simpan terpisah: berkas otomatis terkirim begitu dipilih
        (auto-submit di template). Validasi: hanya gambar JPG/PNG/GIF/WebP ≤ 1 MB.
        """
        dataset_id = request.GET.get("id") or request.POST.get("id")
        try:
            dataset = Dataset.objects.get(pk=dataset_id)
        except (Dataset.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Layer tidak ditemukan.")
            return redirect(reverse("dst_auth:data_spasial"))

        back = f"{reverse('dst_auth:layer_detail')}?id={dataset.pk}"
        if not (request.user.is_superuser or dataset.owner_id == request.user.pk):
            messages.error(request, "Anda tidak punya izin mengubah gambar layer ini.")
            return redirect(back)

        action = request.POST.get("action") or ""

        if action == "upload_thumbnail":
            f = request.FILES.get("thumbnail")
            if not f:
                messages.error(request, "Tidak ada berkas gambar yang diunggah.")
                return redirect(back)
            if f.size > 1024 * 1024:
                messages.error(request, "Ukuran gambar melebihi batas 1 MB.")
                return redirect(back)
            allowed = {
                "image/jpeg": "jpg", "image/png": "png",
                "image/gif": "gif", "image/webp": "webp",
            }
            ext = allowed.get((f.content_type or "").lower())
            if not ext:
                messages.error(request, "Format gambar harus JPG, PNG, GIF, atau WebP.")
                return redirect(back)
            try:
                dataset.save_thumbnail(f"dataset-{dataset.uuid}-thumb.{ext}", f.read())
                messages.success(request, "Gambar peta berhasil diperbarui.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan gambar: {exc}")
            return redirect(back)

        if action == "delete_thumbnail":
            try:
                dataset.thumbnail_url = ""
                dataset.save(update_fields=["thumbnail_url"])
                messages.success(request, "Gambar peta dihapus.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menghapus gambar: {exc}")
            return redirect(back)

        return redirect(back)


class LayerEditView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/layer_edit.html"
    page_slug = "layer_edit"
    page_title = "Edit Layer"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Dataset Spasial", "/dst-auth/data-spasial/"),
        ("Edit Layer", None),
    ]

    def _get_dataset(self, request):
        from django.http import Http404

        dataset_id = request.GET.get("id") or request.POST.get("id")
        if not dataset_id:
            return None
        try:
            return (
                Dataset.objects.select_related("owner", "category", "license", "group")
                .prefetch_related("keywords", "regions")
                .get(pk=dataset_id)
            )
        except (Dataset.DoesNotExist, ValueError):
            raise Http404("Layer tidak ditemukan.")

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings
        from geonode.base.models import TopicCategory, License, Region

        ctx = super().get_context_data(**kwargs)
        dataset = self._get_dataset(self.request)
        ctx["dataset"] = dataset
        if dataset is None:
            return ctx

        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}
        gs_url = (ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "").rstrip("/")
        typename = dataset.typename or (
            f"{dataset.workspace}:{dataset.name}" if dataset.workspace and dataset.name else ""
        )

        ll_bbox_text = ""
        if dataset.ll_bbox_polygon:
            try:
                ext = dataset.ll_bbox_polygon.extent
                ll_bbox_text = (
                    f"{ext[0]:.4f}, {ext[1]:.4f} → {ext[2]:.4f}, {ext[3]:.4f}"
                )
            except Exception:
                ll_bbox_text = ""

        if dataset.is_vector():
            _geo = dataset_feature_label(dataset)
            geometry_label = f"Vektor · {_geo if _geo and _geo != 'Vektor' else (dataset.subtype or 'vector')}"
        elif dataset.is_raster:
            geometry_label = "Raster · GeoTIFF"
        elif dataset.subtype == "tabular":
            geometry_label = "Tabular · metadata-only"
        else:
            geometry_label = dataset.subtype or "—"

        keywords_csv = ", ".join(k.name for k in dataset.keywords.all())
        selected_region_ids = list(dataset.regions.values_list("pk", flat=True))

        endpoints = []
        if typename and gs_url and dataset.is_vector():
            endpoints.append(("WMS", f"{gs_url}/wms?service=WMS&request=GetMap&layers={typename}", False))
            endpoints.append(("WFS", f"{gs_url}/wfs?service=WFS&typeName={typename}&request=GetFeature", False))
            endpoints.append(("WCS", "Tidak tersedia untuk vektor", True))
        elif typename and gs_url and dataset.is_raster:
            endpoints.append(("WMS", f"{gs_url}/wms?service=WMS&request=GetMap&layers={typename}", False))
            endpoints.append(("WCS", f"{gs_url}/wcs?service=WCS&coverageId={typename}", False))
            endpoints.append(("WFS", "Tidak tersedia untuk raster", True))
        endpoints.append(("REST", f"/api/v2/datasets/{dataset.pk}", False))

        ctx["categories"] = TopicCategory.objects.all().order_by("identifier")
        ctx["licenses"] = License.objects.all().order_by("name")
        # Region / Cakupan: autocomplete seluruh wilayah Indonesia (prov + kab/kota).
        ctx.update(region_autocomplete_context(dataset))
        ctx["walidata_users"] = (
            User.objects.exclude(pk=-1)
            .filter(Q(is_staff=True) | Q(is_superuser=True))
            .order_by("username")
        )
        # Walidata = instansi dari tabel master (DatasetWalidata), terpisah dari owner.
        from .models import Walidata, DatasetWalidata

        ctx["walidata_master"] = list(Walidata.objects.all().order_by("urutan", "nama", "id"))
        wlink = DatasetWalidata.objects.filter(dataset=dataset).first()
        ctx["current_walidata_id"] = wlink.walidata_id if wlink else None
        ctx["geometry_label"] = geometry_label
        ctx["ll_bbox_text"] = ll_bbox_text
        ctx["typename"] = typename
        ctx["keywords_csv"] = keywords_csv
        ctx["selected_region_ids"] = selected_region_ids
        ctx["endpoints"] = endpoints
        ctx["attribute_count"] = dataset.attribute_set.count()
        return ctx

    def post(self, request, *args, **kwargs):
        from geonode.base.models import TopicCategory, License, Region

        dataset = self._get_dataset(request)
        if dataset is None:
            messages.error(request, "Parameter id wajib disertakan.")
            return redirect(reverse("dst_auth:data_spasial"))

        action = request.POST.get("action", "save")
        detail_url = f"{reverse('dst_auth:layer_edit')}?id={dataset.pk}"

        if action == "delete":
            if not request.user.is_superuser and dataset.owner_id != request.user.pk:
                messages.error(request, "Anda tidak punya izin menghapus layer ini.")
                return redirect(detail_url)
            title = dataset.title or dataset.name
            try:
                dataset.delete()
                messages.success(request, f"Layer '{title}' berhasil dihapus.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menghapus: {exc}")
                return redirect(detail_url)
            return redirect(reverse("dst_auth:data_spasial"))

        if action == "archive":
            dataset.is_published = False
            dataset.is_approved = False
            dataset.save(update_fields=["is_published", "is_approved"])
            messages.success(
                request,
                f"Layer '{dataset.title}' diarsipkan (un-published).",
            )
            return redirect(detail_url)

        # action == "save"
        title = (request.POST.get("title") or "").strip()
        abstract = (request.POST.get("abstract") or "").strip()
        if not title or not abstract:
            messages.error(request, "Judul dan abstrak wajib diisi.")
            return redirect(detail_url)

        category_id = request.POST.get("category") or ""
        if category_id:
            try:
                dataset.category = TopicCategory.objects.get(pk=category_id)
            except (TopicCategory.DoesNotExist, ValueError):
                pass

        license_id = request.POST.get("license") or ""
        if license_id:
            try:
                dataset.license = License.objects.get(pk=license_id)
            except (License.DoesNotExist, ValueError):
                dataset.license = None
        else:
            dataset.license = None

        owner_id = request.POST.get("owner") or ""
        if owner_id:
            try:
                dataset.owner = User.objects.get(pk=owner_id)
            except (User.DoesNotExist, ValueError):
                pass

        # Walidata = instansi dari tabel master (DatasetWalidata), terpisah dari owner.
        from .models import Walidata, DatasetWalidata

        walidata_id = request.POST.get("walidata") or ""
        if walidata_id:
            try:
                w = Walidata.objects.get(pk=walidata_id)
                DatasetWalidata.objects.update_or_create(
                    dataset=dataset, defaults={"walidata": w}
                )
            except (Walidata.DoesNotExist, ValueError):
                pass
        else:
            DatasetWalidata.objects.filter(dataset=dataset).delete()

        date_str = (request.POST.get("date") or "").strip()
        if date_str:
            try:
                from datetime import datetime

                dataset.date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass

        dataset.title = title[:255]
        dataset.abstract = abstract
        dataset.language = (request.POST.get("language") or dataset.language or "ind").strip()[:5]
        dataset.attribution = (request.POST.get("attribution") or "").strip()[:255]

        data_source = (request.POST.get("data_source") or "").strip()
        lineage = (request.POST.get("lineage") or "").strip()
        if data_source and lineage:
            dataset.supplemental_information = f"Sumber data: {data_source}\n\n{lineage}"
        elif data_source:
            dataset.supplemental_information = f"Sumber data: {data_source}"
        elif lineage:
            dataset.supplemental_information = lineage
        else:
            dataset.supplemental_information = ""

        # Field "Pernyataan Kualitas Data" dihilangkan dari form DST; hanya
        # diperbarui bila benar-benar dikirim agar nilai lama tidak terhapus.
        if "data_quality_statement" in request.POST:
            dataset.data_quality_statement = (
                request.POST.get("data_quality_statement") or ""
            ).strip()

        visibility = request.POST.get("visibility", "draft")
        dataset.is_published = visibility == "public"
        # Approval dilakukan oleh Walidata (is_staff) maupun Super Admin.
        if request.user.is_staff or request.user.is_superuser:
            dataset.is_approved = request.POST.get("is_approved") == "on"

        try:
            dataset.save()
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Gagal menyimpan: {exc}")
            return redirect(detail_url)

        region_ids = request.POST.getlist("regions")
        if region_ids:
            valid_regions = Region.objects.filter(pk__in=region_ids)
            dataset.regions.set(valid_regions)
        else:
            dataset.regions.clear()

        keywords_csv = (request.POST.get("keywords") or "").strip()
        new_keywords = [k.strip() for k in keywords_csv.split(",") if k.strip()][:20]
        try:
            dataset.keywords.clear()
            if new_keywords:
                dataset.keywords.add(*new_keywords)
        except Exception:
            pass

        messages.success(request, f"Layer '{dataset.title}' berhasil diperbarui.")
        return redirect(reverse("dst_auth:data_spasial"))


class AksesNasionalView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/akses_nasional.html"
    page_slug = "akses_nasional"
    page_title = "Akses DST Nasional"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Akses DST Nasional", None)]

    def get_context_data(self, **kwargs):
        from django.apps import apps as dj_apps
        from django.conf import settings as dj_settings
        from geonode.maps.models import Map

        ctx = super().get_context_data(**kwargs)

        try:
            Application = dj_apps.get_model("oauth2_provider", "Application")
            AccessToken = dj_apps.get_model("oauth2_provider", "AccessToken")
        except LookupError:
            Application = None
            AccessToken = None

        consumers = []
        if Application is not None:
            now = timezone.now()
            for app in Application.objects.select_related("user").order_by("name", "client_id"):
                client_id = app.client_id or ""
                if len(client_id) > 10:
                    masked = f"{client_id[:6]}{'•' * 6}{client_id[-4:]}"
                else:
                    masked = client_id
                active_tokens = AccessToken.objects.filter(
                    application=app, expires__gt=now
                ).count() if AccessToken else 0
                last_token = (
                    AccessToken.objects.filter(application=app)
                    .order_by("-created")
                    .values_list("created", flat=True)
                    .first()
                    if AccessToken
                    else None
                )
                initials = "".join(p[0] for p in (app.name or client_id).split()[:2]).upper() or "?"
                consumers.append(
                    {
                        "id": app.id,
                        "name": app.name or client_id or f"App #{app.id}",
                        "client_id": client_id,
                        "client_id_masked": masked,
                        "client_type": app.client_type,
                        "grant_type": app.authorization_grant_type,
                        "owner": app.user.get_username() if app.user_id else "—",
                        "created": app.created,
                        "last_token": last_token,
                        "active_tokens": active_tokens,
                        "skip_auth": app.skip_authorization,
                        "initials": initials,
                    }
                )

        published_datasets = Dataset.objects.filter(is_published=True, is_approved=True).count()
        published_docs = Document.objects.filter(is_published=True, is_approved=True).count()
        published_maps = Map.objects.filter(is_published=True, is_approved=True).count()
        total_published = published_datasets + published_docs + published_maps

        token_count_30d = (
            AccessToken.objects.filter(
                created__gte=timezone.now() - timedelta(days=30)
            ).count()
            if AccessToken
            else 0
        )
        action_count_30d = Action.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).count()

        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}
        gs_url = (ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "").rstrip("/")

        endpoints = [
            {
                "label": "CSW",
                "code": "csw",
                "name": "Catalog Service",
                "purpose": "Discovery metadata seluruh resource published, ISO 19139.",
                "url": "/catalogue/csw",
                "active": True,
            },
            {
                "label": "WMS",
                "code": "wms",
                "name": "Web Map Service",
                "purpose": "Render peta sebagai gambar (display).",
                "url": f"{gs_url}/wms" if gs_url else "/geoserver/wms",
                "active": True,
            },
            {
                "label": "WFS",
                "code": "wfs",
                "name": "Web Feature Service",
                "purpose": "Query vektor (GeoJSON / GML).",
                "url": f"{gs_url}/wfs" if gs_url else "/geoserver/wfs",
                "active": True,
            },
            {
                "label": "WCS",
                "code": "wcs",
                "name": "Coverage Service",
                "purpose": "Raster download (GeoTIFF).",
                "url": f"{gs_url}/wcs" if gs_url else "/geoserver/wcs",
                "active": True,
            },
            {
                "label": "REST",
                "code": "rest",
                "name": "GeoNode API v2",
                "purpose": "Resources, datasets, documents.",
                "url": "/api/v2/",
                "active": True,
            },
        ]

        recent_actions = (
            Action.objects.select_related(
                "actor_content_type", "action_object_content_type"
            )
            .order_by("-timestamp")[:8]
        )
        activity_rows = []
        for a in recent_actions:
            target = a.action_object or a.target
            target_label = (
                getattr(target, "title", None)
                or getattr(target, "name", None)
                or (a.data or {}).get("object_name")
                or ""
            )
            activity_rows.append(
                {
                    "timestamp": a.timestamp,
                    "verb": a.verb,
                    "actor": str(a.actor or "—"),
                    "target": target_label,
                    "target_type": (
                        a.action_object_content_type.model
                        if a.action_object_content_type
                        else ""
                    ),
                }
            )

        ctx["consumers"] = consumers
        ctx["endpoints"] = endpoints
        ctx["activity_rows"] = activity_rows
        ctx["stats"] = {
            "consumers": len(consumers),
            "active_tokens_30d": token_count_30d,
            "endpoints_active": sum(1 for e in endpoints if e["active"]),
            "endpoints_total": len(endpoints),
            "published_total": total_published,
            "published_datasets": published_datasets,
            "published_docs": published_docs,
            "published_maps": published_maps,
            "actions_30d": action_count_30d,
        }
        return ctx


class EndpointApiView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/endpoint_api.html"
    page_slug = "endpoint_api"
    page_title = "Endpoint API"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Endpoint API", None)]

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings
        from geonode.base.models import (
            ResourceBase,
            TopicCategory,
            License,
            Region,
            HierarchicalKeyword,
        )
        from geonode.maps.models import Map
        from geonode.groups.models import GroupProfile

        ctx = super().get_context_data(**kwargs)

        request = self.request
        base_url = f"{request.scheme}://{request.get_host()}"

        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}
        geoserver_url = (ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "").rstrip("/")

        rest_resources = [
            ("GET", "/api/v2/datasets", "Daftar layer spasial (Dataset).", Dataset.objects.count()),
            ("GET", "/api/v2/datasets/{id}", "Detail layer berdasarkan ID.", None),
            ("GET", "/api/v2/documents", "Daftar dokumen kebijakan.", Document.objects.count()),
            ("GET", "/api/v2/documents/{id}", "Detail dokumen berdasarkan ID.", None),
            ("GET", "/api/v2/maps", "Daftar peta interaktif.", Map.objects.count()),
            ("GET", "/api/v2/resources", "Gabungan dataset + dokumen + map.", ResourceBase.objects.count()),
            ("GET", "/api/v2/resources/{id}/extra_metadata", "Extra metadata sparse field.", None),
            ("GET", "/api/v2/resources/{id}/linked_resources", "Resource yang ter-link.", None),
        ]

        rest_vocab = [
            ("GET", "/api/v2/categories", "Topic Category ISO 19115.", TopicCategory.objects.count()),
            ("GET", "/api/v2/keywords", "HierarchicalKeyword (tag).", HierarchicalKeyword.objects.count()),
            ("GET", "/api/v2/regions", "Region geografis.", Region.objects.count()),
            ("GET", "/api/v2/groups", "Group profile.", GroupProfile.objects.count()),
            ("GET", "/api/v2/users", "Daftar pengguna (Profile).", User.objects.exclude(pk=-1).count()),
            ("GET", "/api/v2/owners", "Pemilik resource.", None),
        ]

        rest_meta = [
            ("GET", "/api/v2/metadata/autocomplete/categories", "Autocomplete kategori.", None),
            ("GET", "/api/v2/metadata/autocomplete/licenses", "Autocomplete license.", None),
            ("GET", "/api/v2/metadata/autocomplete/regions", "Autocomplete region.", None),
            ("GET", "/api/v2/metadata/autocomplete/users", "Autocomplete pengguna.", None),
            ("GET", "/api/v2/facets", "Daftar facet pencarian.", None),
        ]

        rest_account = [
            ("GET", "/api/v2/userinfo/", "Info user yang sedang login.", None),
            ("POST", "/api/v2/api-auth/login/", "Login session-based.", None),
            ("POST", "/api/v2/api-auth/logout/", "Logout session.", None),
        ]

        ogc_services = [
            ("WMS", f"{geoserver_url}/wms" if geoserver_url else "/geoserver/wms", "Web Map Service — render peta sebagai gambar.", None),
            ("WFS", f"{geoserver_url}/wfs" if geoserver_url else "/geoserver/wfs", "Web Feature Service — query fitur vektor.", None),
            ("WCS", f"{geoserver_url}/wcs" if geoserver_url else "/geoserver/wcs", "Web Coverage Service — raster.", None),
            ("WMTS", f"{geoserver_url}/gwc/service/wmts" if geoserver_url else "/geoserver/gwc/service/wmts", "Web Map Tile Service — tile pre-rendered.", None),
            ("CSW", "/catalogue/csw", "Catalogue Service for the Web — pencarian metadata.", None),
        ]

        # Service Data Capaian FOLUR → DST Nasional (read-only JSON, publik).
        from .models import FolurIndikator

        dst_folur = [
            ("GET", "/api/folur/capaian/?api_key=••••", "Capaian FOLUR + Sitroom (indikator, target, realisasi tahunan/kumulatif, KPI otomatis). Read-only, butuh API key (PIN).", FolurIndikator.objects.filter(aktif=True).count()),
            ("GET", "/api/folur/capaian/?api_key=••••&tahun=2026", "Filter realisasi ke satu tahun.", None),
            ("GET", "/api/folur/capaian/?api_key=••••&wilayah=desa", "Rincian per desa (nilai + kegiatan per tahun).", None),
            ("GET", "/api/folur/capaian/?api_key=••••&wilayah=kecamatan", "Rincian per kecamatan.", None),
        ]

        groups = [
            {"title": "DST · Capaian FOLUR (→ DST Nasional)", "items": dst_folur},
            {"title": "REST · Resources", "items": rest_resources},
            {"title": "REST · Vocabulary", "items": rest_vocab},
            {"title": "REST · Metadata Autocomplete", "items": rest_meta},
            {"title": "REST · Account", "items": rest_account},
            {"title": "OGC Services", "items": ogc_services},
        ]

        total_endpoints = sum(len(g["items"]) for g in groups)

        ctx["base_url"] = base_url
        ctx["geoserver_url"] = geoserver_url or "—"
        ctx["groups"] = groups
        ctx["stats"] = {
            "total_endpoints": total_endpoints,
            "resources": ResourceBase.objects.count(),
            "datasets": Dataset.objects.count(),
            "ogc_services": len(ogc_services),
        }
        return ctx


class MetadataSchemaView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/metadata_schema.html"
    page_slug = "metadata_schema"
    page_title = "Metadata Schema"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Metadata Schema", None)]

    CORE_FIELDS = [
        ("title", "Title", "str"),
        ("abstract", "Abstract", "txt"),
        ("purpose", "Purpose", "txt"),
        ("date", "Date Stamp", "date"),
        ("date_type", "Date Type", "enum"),
        ("edition", "Edition", "str"),
        ("language", "Language", "enum"),
        ("category", "Topic Category", "enum"),
        ("license", "License", "enum"),
        ("regions", "Regions", "arr"),
        ("keywords", "Keywords", "arr"),
        ("attribution", "Attribution", "str"),
        ("data_quality_statement", "Data Quality Statement", "txt"),
        ("supplemental_information", "Supplemental Information", "txt"),
        ("temporal_extent_start", "Temporal Start", "date"),
        ("temporal_extent_end", "Temporal End", "date"),
        ("bbox_polygon", "Bounding Box", "geom"),
        ("srid", "SRID", "str"),
        ("featured", "Featured", "bool"),
        ("is_published", "Published", "bool"),
        ("is_approved", "Approved", "bool"),
    ]

    TYPE_MAP = {
        "CharField": "str",
        "TextField": "txt",
        "IntegerField": "int",
        "BooleanField": "bool",
        "DateField": "date",
        "DateTimeField": "date",
        "PolygonField": "geom",
        "URLField": "url",
        "ForeignKey": "enum",
        "ManyToManyField": "arr",
        "JSONField": "json",
    }

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from geonode.base.models import (
            ResourceBase,
            TopicCategory,
            License,
            Region,
            ExtraMetadata,
        )

        ctx = super().get_context_data(**kwargs)

        rb_fields = {f.name: f for f in ResourceBase._meta.get_fields() if hasattr(f, "name")}

        core_rows = []
        required_count = 0
        for key, label, fallback_type in self.CORE_FIELDS:
            f = rb_fields.get(key)
            ftype = (
                self.TYPE_MAP.get(f.get_internal_type(), fallback_type)
                if f is not None and hasattr(f, "get_internal_type")
                else fallback_type
            )
            required = bool(
                f is not None
                and getattr(f, "blank", True) is False
                and getattr(f, "null", True) is False
                and not getattr(f, "auto_created", False)
            )
            if required:
                required_count += 1
            core_rows.append(
                {
                    "key": key,
                    "label": label,
                    "type": ftype,
                    "required": required,
                    "in_model": f is not None,
                }
            )

        categories = list(
            TopicCategory.objects.annotate(used=Count("resourcebase")).order_by(
                "-used", "identifier"
            )[:30]
        )

        licenses = list(License.objects.all().order_by("name")[:30])

        ctx["core_fields"] = core_rows
        ctx["categories"] = categories
        ctx["licenses"] = licenses
        ctx["stats"] = {
            "total_fields": len(core_rows),
            "required_fields": required_count,
            "categories": TopicCategory.objects.count(),
            "licenses": License.objects.count(),
            "regions": Region.objects.count(),
            "extra_metadata": ExtraMetadata.objects.count(),
            "resources": ResourceBase.objects.count(),
        }
        return ctx


class PenggunaView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/pengguna.html"
    page_slug = "pengguna"
    superuser_only = True
    page_title = "Pengguna & Role"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Pengguna & Role", None),
    ]
    paginate_by = 10

    @staticmethod
    def _role_for(user):
        if user.is_superuser:
            return ("super", "Super Admin")
        if user.is_staff:
            return ("walidata", "Walidata")
        return ("kontrib", "Pengguna")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        base_qs = User.objects.exclude(pk=-1).order_by("-is_superuser", "-is_staff", "username")

        role = (self.request.GET.get("role") or "all").lower()
        qs = base_qs
        if role == "super":
            qs = qs.filter(is_superuser=True)
        elif role == "walidata":
            qs = qs.filter(is_staff=True, is_superuser=False)
        elif role == "kontrib":
            qs = qs.filter(is_staff=False, is_superuser=False)

        search = (self.request.GET.get("q") or "").strip()
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(organization__icontains=search)
            )

        total = base_qs.count()
        super_count = base_qs.filter(is_superuser=True).count()
        walidata_count = base_qs.filter(is_staff=True, is_superuser=False).count()
        kontrib_count = base_qs.filter(is_staff=False, is_superuser=False).count()
        suspended = base_qs.filter(is_active=False).count()
        week_active = base_qs.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()

        paginator = Paginator(qs, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page") or 1)

        try:
            from avatar.utils import get_primary_avatar
        except ImportError:
            get_primary_avatar = None

        rows = []
        for u in page_obj.object_list:
            display = (u.get_full_name() or u.username).strip()
            initials = "".join(p[0] for p in display.split()[:2]).upper() or u.username[:2].upper()
            role_class, role_label = self._role_for(u)
            photo_url = ""
            if get_primary_avatar:
                avatar = get_primary_avatar(u, width=80)
                if avatar:
                    photo_url = avatar.avatar_url(80, 80)
            rows.append(
                {
                    "id": u.pk,
                    "name": display,
                    "username": u.username,
                    "email": u.email or "",
                    "organization": getattr(u, "organization", "") or "",
                    "position": getattr(u, "position", "") or "",
                    "initials": initials,
                    "role_class": role_class,
                    "role_label": role_label,
                    "photo_url": photo_url,
                    "is_active": u.is_active,
                    "last_login": u.last_login,
                    "is_self": u.pk == self.request.user.pk,
                }
            )

        ctx["users"] = rows
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["role"] = role
        ctx["search"] = search
        ctx["stats"] = {
            "total": total,
            "super": super_count,
            "walidata": walidata_count,
            "kontrib": kontrib_count,
            "suspended": suspended,
            "week_active": week_active,
            "week_pct": int(round(week_active * 100 / total)) if total else 0,
        }
        return ctx


class PenggunaBaruView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/pengguna_baru.html"
    page_slug = "pengguna_baru"
    page_title = "Tambah Pengguna"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Pengguna & Role", "/dst-auth/pengguna/"),
        ("Tambah Pengguna", None),
    ]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Hanya Super Admin yang dapat menambah pengguna.")
            return redirect(reverse("dst_auth:pengguna"))
        return super().dispatch(request, *args, **kwargs)

    # Peran yang bisa dipilih saat membuat pengguna (Super Admin lewat Edit saja).
    PERAN_CHOICES = [("umum", "Umum"), ("walidata", "Walidata")]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_data"] = self.request.session.pop("pengguna_baru_form_data", {})
        ctx["errors"] = self.request.session.pop("pengguna_baru_errors", {})
        ctx["peran_choices"] = self.PERAN_CHOICES
        return ctx

    def post(self, request, *args, **kwargs):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email

        username = (request.POST.get("username") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        peran = (request.POST.get("peran") or "umum").strip()
        if peran not in dict(self.PERAN_CHOICES):
            peran = "umum"

        errors = {}
        form_data = {"username": username, "full_name": full_name, "email": email, "peran": peran}

        if not username:
            errors["username"] = ["Username wajib diisi."]
        elif len(username) > 150:
            errors["username"] = ["Username maksimal 150 karakter."]
        elif not username.isascii():
            errors["username"] = ["Username mengandung karakter tidak valid."]
        elif User.objects.filter(username__iexact=username).exists():
            errors["username"] = [f"Pengguna dengan username '{username}' sudah ada."]

        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = ["Format email tidak valid."]
            else:
                if User.objects.filter(email__iexact=email).exists():
                    errors["email"] = ["Email tersebut sudah digunakan akun lain."]

        if not password1:
            errors.setdefault("password1", []).append("Password wajib diisi.")
        if not password2:
            errors.setdefault("password2", []).append("Konfirmasi password wajib diisi.")

        if password1 and password2 and password1 != password2:
            errors.setdefault("password2", []).append("Password tidak cocok.")

        if password1 and not errors.get("password1"):
            try:
                validate_password(password1)
            except ValidationError as exc:
                errors["password1"] = list(exc.messages)

        if errors:
            request.session["pengguna_baru_form_data"] = form_data
            request.session["pengguna_baru_errors"] = errors
            return redirect(reverse("dst_auth:pengguna_baru"))

        user = User.objects.create_user(username=username, password=password1)
        if full_name:
            parts = full_name.split(None, 1)
            user.first_name = parts[0][:150]
            user.last_name = (parts[1] if len(parts) > 1 else "")[:150]
        if email:
            user.email = email
        # Walidata = staff; Umum = pengguna biasa (akses terbatas Dashboard).
        user.is_staff = peran == "walidata"
        user.save()

        peran_label = dict(self.PERAN_CHOICES).get(peran, "Umum")
        messages.success(
            request,
            f"Pengguna '{user.username}' (peran {peran_label}) berhasil dibuat. "
            f"Anda dapat mengedit opsi lebih lanjut lewat Edit Pengguna.",
        )
        return redirect(reverse("dst_auth:pengguna"))


class PenggunaEditView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/pengguna_edit.html"
    page_slug = "pengguna_edit"
    page_title = "Edit Pengguna"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Pengguna & Role", "/dst-auth/pengguna/"),
        ("Edit Pengguna", None),
    ]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Hanya Super Admin yang dapat mengedit pengguna.")
            return redirect(reverse("dst_auth:pengguna"))
        return super().dispatch(request, *args, **kwargs)

    def _get_target_user(self, request):
        from django.http import Http404
        user_id = request.GET.get("id") or request.POST.get("user_id")
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            raise Http404("Pengguna tidak ditemukan.")

    def get(self, request, *args, **kwargs):
        target = self._get_target_user(request)
        if target is None:
            messages.error(request, "Parameter id wajib disertakan.")
            return redirect(reverse("dst_auth:pengguna"))
        self._target_user = target
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = getattr(self, "_target_user", None) or self._get_target_user(self.request)

        display = (target.get_full_name() or target.username).strip()
        initials = "".join(p[0] for p in display.split()[:2]).upper() or target.username[:2].upper()
        role_class, role_label = PenggunaView._role_for(target)
        if target.is_superuser:
            peran = "super"
        elif target.is_staff:
            peran = "walidata"
        else:
            peran = "umum"

        ctx["target_user"] = {
            "id": target.pk,
            "name": display,
            "username": target.username,
            # Profil ditampilkan read-only (label) — diubah pemilik akun via Profil.
            "full_name": (target.get_full_name() or "").strip() or "—",
            "email": target.email or "—",
            "organization": getattr(target, "organization", "") or "—",
            "position": getattr(target, "position", "") or "—",
            "initials": initials,
            "role_class": role_class,
            "role_label": role_label,
            "is_active": target.is_active,
            "peran": peran,
        }
        ctx["is_self"] = target.pk == self.request.user.pk
        ctx["peran_choices"] = [
            ("umum", "Umum"),
            ("walidata", "Walidata"),
            ("super", "Super Admin"),
        ]
        return ctx

    def post(self, request, *args, **kwargs):
        target = self._get_target_user(request)
        if target is None:
            messages.error(request, "Parameter id wajib disertakan.")
            return redirect(reverse("dst_auth:pengguna"))

        # Profil (nama/email/instansi) read-only di sini — hanya peran & status
        # yang dapat diubah admin. Profil diubah pemilik akun lewat menu Profil.
        if target.pk == request.user.pk:
            messages.info(
                request, "Anda tidak dapat mengubah peran atau status akun sendiri."
            )
            return redirect(reverse("dst_auth:pengguna"))

        roles = {"umum": (False, False), "walidata": (True, False), "super": (True, True)}
        peran = (request.POST.get("peran") or "").strip()
        if peran not in roles:
            messages.error(request, "Peran tidak valid.")
            return redirect(f"{reverse('dst_auth:pengguna_edit')}?id={target.pk}")

        target.is_staff, target.is_superuser = roles[peran]
        target.is_active = request.POST.get("is_active") == "1"
        target.save()
        messages.success(
            request, f"Peran & status pengguna '{target.username}' berhasil diperbarui."
        )
        return redirect(reverse("dst_auth:pengguna"))


class CapaianView(LoginRequiredMixin, DstAdminPageView):
    """Sitroom — scorecard Capaian Program FOLUR (results framework / GEF CI)."""

    template_name = "dst-district/admin/capaian.html"
    page_slug = "capaian"
    page_title = "Capaian Program FOLUR"
    breadcrumb = [("Capaian Program", None)]

    def get_context_data(self, **kwargs):
        from .models import SiteIdentity

        ctx = super().get_context_data(**kwargs)
        identity = SiteIdentity.load()
        auto = compute_folur_auto_kpis(identity)
        ctx["folur_auto"] = auto
        ctx["folur_idm"] = auto.get("idm_distribution", [])
        ctx["folur_komoditas_count"] = auto.get("komoditas_count", 0)
        try:
            periode = int(self.request.GET.get("tahun") or 0) or (
                auto.get("periode_idm") or None
            )
        except (TypeError, ValueError):
            periode = auto.get("periode_idm") or None
        ctx.update(build_folur_kpis(periode))
        return ctx


class DataCapaianView(LoginRequiredMixin, DstAdminPageView):
    """Pusat Data Capaian FOLUR — navigasi sumber data, entri realisasi, dan
    formulasi yang menyuapi Sitroom (/dst-auth/capaian/) & Capaian publik
    (/capaian-folur/)."""

    template_name = "dst-district/admin/data_capaian.html"
    page_slug = "data_capaian"
    page_title = "Data Capaian"
    breadcrumb = [("Data Capaian", None)]

    def get_context_data(self, **kwargs):
        from django.urls import reverse
        from .models import (
            SiteIdentity,
            FolurIndikator,
            RefWilayahProvinsi,
            RefWilayahKabkota,
            RefWilayahKecamatan,
            RefWilayahDesa,
            IdmDesa,
            KomoditasFokus,
            ImplementingPartner,
        )

        ctx = super().get_context_data(**kwargs)
        identity = SiteIdentity.load()
        ctx["folur_auto"] = compute_folur_auto_kpis(identity)

        def _safe(fn, default=0):
            try:
                return fn()
            except Exception:
                return default

        # ── Sumber data: status/jumlah ──
        ctx["wilayah_counts"] = {
            "provinsi": _safe(lambda: RefWilayahProvinsi.objects.count()),
            "kabkota": _safe(lambda: RefWilayahKabkota.objects.count()),
            "kecamatan": _safe(lambda: RefWilayahKecamatan.objects.count()),
            "desa": _safe(lambda: RefWilayahDesa.objects.count()),
        }
        ctx["idm_count"] = _safe(lambda: IdmDesa.objects.count())
        ctx["idm_tahun"] = _safe(
            lambda: IdmDesa.objects.order_by("-tahun").values_list("tahun", flat=True).first(),
            None,
        )
        ctx["dataset_count"] = _safe(
            lambda: Dataset.objects.filter(is_published=True).count()
        )
        ctx["komoditas_count"] = _safe(
            lambda: KomoditasFokus.objects.filter(aktif=True).count()
        )
        ctx["partner_count"] = _safe(
            lambda: ImplementingPartner.objects.filter(aktif=True).count()
        )

        # ── Entri data: indikator + realisasi terbaru ──
        rows = []
        manual_total = manual_terisi = 0
        for ind in FolurIndikator.objects.prefetch_related("capaian").order_by("urutan", "id"):
            caps = sorted(ind.capaian.all(), key=lambda c: c.tahun)
            latest = caps[-1] if caps else None
            if ind.sumber == "auto":
                nilai = _folur_auto_value(ind.auto_key)
            else:
                nilai = latest.nilai if latest else None
                manual_total += 1
                if nilai is not None:
                    manual_terisi += 1
            rows.append(
                {
                    "obj": ind,
                    "nilai": nilai,
                    "tahun": latest.tahun if latest else None,
                    "n_realisasi": len(caps),
                    "ada": nilai is not None,
                }
            )
        ctx["kpi_rows"] = rows
        ctx["kpi_total"] = len(rows)
        ctx["kpi_manual_total"] = manual_total
        ctx["kpi_manual_terisi"] = manual_terisi

        # Indikator yang sedang dientri realisasinya (panel inline §02).
        edit_id = self.request.GET.get("edit_kpi")
        kpi_edit = FolurIndikator.objects.filter(pk=edit_id).first() if edit_id else None
        ctx["kpi_edit"] = kpi_edit
        ctx["kpi_capaian_list"] = (
            list(kpi_edit.capaian.order_by("-tahun")) if kpi_edit else []
        )
        ctx["kpi_pilar_choices"] = FolurIndikator.PILAR_CHOICES
        ctx["kpi_sumber_choices"] = FolurIndikator.SUMBER_CHOICES
        ctx["kpi_arah_choices"] = FolurIndikator.ARAH_CHOICES
        ctx["kpi_agregasi_choices"] = FolurIndikator.AGREGASI_CHOICES
        ctx["kpi_sumber_agregat_choices"] = FolurIndikator.SUMBER_AGREGAT_CHOICES
        from .models import WEBGIS2_PALETTES
        ctx["palet_choices"] = [
            {"key": k, "label": v[0], "colors": v[1]}
            for k, v in WEBGIS2_PALETTES.items()
        ]

        # ── Entri capaian per WILAYAH (desa/kecamatan) untuk indikator terpilih ──
        # Grid bulk: tiap wilayah cakupan aktif + nilai tersimpan (FolurCapaianWilayah).
        import datetime as _dt
        from .models import FolurCapaianWilayah

        wil_level = (
            "kecamatan" if self.request.GET.get("wil_level") == "kecamatan" else "desa"
        )
        try:
            wil_tahun = int(self.request.GET.get("wil_tahun") or 0)
        except (TypeError, ValueError):
            wil_tahun = 0
        if not wil_tahun:
            wil_tahun = _dt.date.today().year
        ctx["wil_level"] = wil_level
        ctx["wil_tahun"] = wil_tahun

        wil_rows = []
        if kpi_edit:
            existing = {
                r["kode_pum"]: r
                for r in FolurCapaianWilayah.objects.filter(
                    indikator=kpi_edit, level=wil_level, tahun=wil_tahun
                ).values("kode_pum", "nilai", "kegiatan", "komoditas")
            }

            def _row(r, parent):
                e = existing.get(r["kode_pum"]) or {}
                return {
                    "kode_pum": r["kode_pum"], "nama": r["nama"], "parent": parent,
                    "nilai": e.get("nilai"),
                    "kegiatan": e.get("kegiatan", ""),
                    "komoditas": e.get("komoditas"),
                }

            if wil_level == "kecamatan":
                src = RefWilayahKecamatan.objects.order_by("kode_pum").values(
                    "kode_pum", "nama"
                )
                wil_rows = [_row(r, "") for r in src]
            else:
                src = RefWilayahDesa.objects.order_by("kode_pum").values(
                    "kode_pum", "nama", "nama_kec"
                )
                wil_rows = [_row(r, r["nama_kec"]) for r in src]
        ctx["wil_rows"] = wil_rows
        ctx["wil_total"] = len(wil_rows)
        ctx["wil_terisi"] = sum(1 for r in wil_rows if r["nilai"] is not None)
        # Daftar Fokus Komoditas (Pengaturan) untuk dropdown kolom Komoditi.
        from .models import KomoditasFokus

        ctx["wil_komoditas"] = list(
            KomoditasFokus.objects.filter(aktif=True).order_by("urutan", "nama")
        )
        return ctx

    def post(self, request, *args, **kwargs):
        """Kelola indikator (Super Admin) & entri realisasi (staff+) di halaman ini."""
        from .models import FolurIndikator, FolurCapaian

        user = request.user
        form = request.POST.get("form")
        base = reverse("dst_auth:data_capaian")

        # ── Definisi indikator: simpan / hapus / toggle (Super Admin) ──
        if form in ("kpi_save", "kpi_delete", "kpi_toggle"):
            if not user.is_superuser:
                messages.error(
                    request, "Hanya Super Admin yang dapat mengubah definisi indikator."
                )
                return redirect(base + "#kelola")
            kid = request.POST.get("kpi_id") or ""

            if form == "kpi_toggle":
                obj = FolurIndikator.objects.filter(pk=kid).first()
                if obj:
                    obj.aktif = request.POST.get("aktif") == "on"
                    obj.save(update_fields=["aktif", "updated"])
                    messages.success(
                        request,
                        f"Indikator '{obj.kode}' kini {'aktif' if obj.aktif else 'nonaktif'}.",
                    )
                else:
                    messages.error(request, "Indikator tidak ditemukan.")
                return redirect(base + "#kelola")

            if form == "kpi_delete":
                obj = FolurIndikator.objects.filter(pk=kid).first()
                if obj:
                    kode = obj.kode
                    obj.delete()
                    messages.success(request, f"Indikator '{kode}' dihapus.")
                else:
                    messages.error(request, "Indikator tidak ditemukan.")
                return redirect(base + "#kelola")

            # kpi_save (create bila tanpa id, update bila ada id)
            kode = (request.POST.get("kode") or "").strip()
            nama = (request.POST.get("nama") or "").strip()
            if not kode or not nama:
                messages.error(request, "Kode dan nama indikator wajib diisi.")
                return redirect(base + "#kelola")

            def _kpi_float(name):
                v = (request.POST.get(name) or "").strip().replace(",", ".")
                try:
                    return float(v) if v else None
                except ValueError:
                    return None

            obj = FolurIndikator.objects.filter(pk=kid).first() if kid else FolurIndikator()
            obj.kode = kode[:20]
            obj.nama = nama[:200]
            obj.pilar = (request.POST.get("pilar") or "").strip()
            obj.satuan = (request.POST.get("satuan") or "").strip()[:30]
            obj.deskripsi = (request.POST.get("deskripsi") or "").strip()
            obj.extra = (request.POST.get("extra") or "").strip()[:120]
            obj.arah = (request.POST.get("arah") or "naik").strip()
            obj.agregasi = (request.POST.get("agregasi") or "tahunan").strip()[:10]
            obj.sumber_agregat = (request.POST.get("sumber_agregat") or "manual").strip()[:10]
            obj.palet = (request.POST.get("palet") or "hijau").strip()[:20]
            obj.sumber = (request.POST.get("sumber") or "manual").strip()
            obj.auto_key = (request.POST.get("auto_key") or "").strip()
            obj.baseline = _kpi_float("baseline")
            obj.target = _kpi_float("target")
            try:
                obj.urutan = int(request.POST.get("urutan") or 0)
            except (TypeError, ValueError):
                obj.urutan = 0
            obj.aktif = request.POST.get("aktif") == "on"
            try:
                obj.save()
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan indikator: {exc}")
                return redirect(base + "#kelola")
            messages.success(request, f"Indikator '{obj.kode}' berhasil disimpan.")
            return redirect(f"{base}?edit_kpi={obj.pk}#kelola")

        # ── Realisasi tahunan: simpan / hapus (staff + Super Admin) ──
        if form in ("kpi_capaian_save", "kpi_capaian_delete"):
            if not (user.is_staff or user.is_superuser):
                messages.error(request, "Anda tidak berhak mengubah data capaian.")
                return redirect(base)
            ind_id = request.POST.get("indikator_id") or ""
            indikator = FolurIndikator.objects.filter(pk=ind_id).first()
            if not indikator:
                messages.error(request, "Indikator tidak ditemukan.")
                return redirect(base + "#kelola")
            back = f"{base}?edit_kpi={indikator.pk}#entri"

            if form == "kpi_capaian_delete":
                cid = request.POST.get("capaian_id") or ""
                obj = FolurCapaian.objects.filter(pk=cid, indikator=indikator).first()
                if obj:
                    th = obj.tahun
                    obj.delete()
                    messages.success(request, f"Realisasi {th} dihapus.")
                else:
                    messages.error(request, "Realisasi tidak ditemukan.")
                return redirect(back)

            try:
                tahun = int(request.POST.get("tahun") or 0)
            except (TypeError, ValueError):
                tahun = 0
            nilai_raw = (request.POST.get("nilai") or "").strip().replace(",", ".")
            try:
                nilai = float(nilai_raw)
            except ValueError:
                nilai = None
            if not tahun or nilai is None:
                messages.error(request, "Tahun dan nilai realisasi wajib diisi (angka).")
                return redirect(back)
            FolurCapaian.objects.update_or_create(
                indikator=indikator,
                tahun=tahun,
                defaults={
                    "nilai": nilai,
                    "catatan": (request.POST.get("catatan") or "").strip()[:255],
                },
            )
            messages.success(request, f"Realisasi {indikator.kode} tahun {tahun} disimpan.")
            return redirect(back)

        # ── Capaian per WILAYAH (bulk grid desa/kecamatan) — staff + Super Admin ──
        if form == "kpi_wilayah_save":
            if not (user.is_staff or user.is_superuser):
                messages.error(request, "Anda tidak berhak mengubah data capaian.")
                return redirect(base)
            from .models import (
                FolurCapaianWilayah,
                RefWilayahDesa,
                RefWilayahKecamatan,
                KomoditasFokus,
            )

            indikator = FolurIndikator.objects.filter(
                pk=request.POST.get("indikator_id") or ""
            ).first()
            if not indikator:
                messages.error(request, "Indikator tidak ditemukan.")
                return redirect(base + "#kelola")
            level = "kecamatan" if request.POST.get("level") == "kecamatan" else "desa"
            try:
                tahun = int(request.POST.get("tahun") or 0)
            except (TypeError, ValueError):
                tahun = 0
            back = f"{base}?edit_kpi={indikator.pk}&wil_level={level}&wil_tahun={tahun}#wilayah"
            if not tahun:
                messages.error(request, "Tahun wajib diisi.")
                return redirect(back)

            names = dict(
                (RefWilayahKecamatan if level == "kecamatan" else RefWilayahDesa)
                .objects.values_list("kode_pum", "nama")
            )
            existing = set(
                FolurCapaianWilayah.objects.filter(
                    indikator=indikator, level=level, tahun=tahun
                ).values_list("kode_pum", flat=True)
            )
            valid_kom = set(
                KomoditasFokus.objects.values_list("id", flat=True)
            )

            saved = deleted = 0
            for key, raw in request.POST.items():
                if not key.startswith("nilai_"):
                    continue
                kode_pum = key[len("nilai_"):]
                val = (raw or "").strip().replace(",", ".")
                if val == "":
                    if kode_pum in existing:  # hapus hanya yang sebelumnya ada
                        FolurCapaianWilayah.objects.filter(
                            indikator=indikator, level=level,
                            kode_pum=kode_pum, tahun=tahun,
                        ).delete()
                        deleted += 1
                    continue
                try:
                    nilai = float(val)
                except ValueError:
                    continue
                keg = (request.POST.get("kegiatan_" + kode_pum) or "").strip()[:255]
                kid = (request.POST.get("komoditas_" + kode_pum) or "").strip()
                kom_id = int(kid) if (kid.isdigit() and int(kid) in valid_kom) else None
                FolurCapaianWilayah.objects.update_or_create(
                    indikator=indikator, level=level, kode_pum=kode_pum, tahun=tahun,
                    defaults={
                        "nilai": nilai,
                        "nama": names.get(kode_pum, ""),
                        "kegiatan": keg,
                        "komoditas_id": kom_id,
                    },
                )
                saved += 1
            messages.success(
                request,
                f"Capaian per {level} {indikator.kode} {tahun}: {saved} disimpan"
                + (f", {deleted} dikosongkan" if deleted else "")
                + ".",
            )
            return redirect(back)

        return redirect(base)


class FrontendView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Frontend: kelola tampil/sembunyi section halaman Landing."""

    template_name = "dst-district/admin/frontend.html"
    page_slug = "frontend"
    superuser_only = True
    page_title = "Frontend"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Frontend", None),
    ]

    def get_context_data(self, **kwargs):
        from .models import LandingSection

        ctx = super().get_context_data(**kwargs)
        LandingSection.ensure_defaults()
        sections = list(LandingSection.objects.all())
        visible_count = sum(1 for s in sections if s.is_visible)
        ctx["sections"] = sections
        ctx["visible_count"] = visible_count
        ctx["total_count"] = len(sections)
        ctx["hidden_count"] = len(sections) - visible_count
        return ctx

    def post(self, request, *args, **kwargs):
        from .models import LandingSection

        LandingSection.ensure_defaults()
        # Checkbox tidak terkirim saat tidak dicentang → kumpulkan yang dicentang.
        visible_keys = set(request.POST.getlist("visible"))
        updated = 0
        for section in LandingSection.objects.all():
            new_state = section.key in visible_keys
            if section.is_visible != new_state:
                section.is_visible = new_state
                section.save(update_fields=["is_visible", "updated"])
                updated += 1
        if updated:
            messages.success(
                request, f"Pengaturan tampilan section diperbarui ({updated} perubahan)."
            )
        else:
            messages.success(request, "Tidak ada perubahan pada tampilan section.")
        return redirect(reverse("dst_auth:frontend"))


class BackendView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Backend: kelola tampil/sembunyi menu pada sidebar admin.

    Menu pada ``SidebarMenu.LOCKED`` (mis. 'backend' sendiri) selalu tampil dan
    tidak memiliki toggle.
    """

    template_name = "dst-district/admin/backend.html"
    page_slug = "backend"
    superuser_only = True
    page_title = "Backend"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Backend", None),
    ]

    def get_context_data(self, **kwargs):
        from .models import SidebarMenu

        ctx = super().get_context_data(**kwargs)
        SidebarMenu.ensure_defaults()
        # Menu grup "Administrasi" tidak ditampilkan — visibilitasnya sepenuhnya
        # dikontrol peran (khusus Super Admin), bukan toggle global ini.
        menus = list(SidebarMenu.objects.exclude(grup="Administrasi"))
        for m in menus:
            m.locked = m.key in SidebarMenu.LOCKED
        toggleable = [m for m in menus if not m.locked]
        ctx["menus"] = menus
        ctx["total_count"] = len(toggleable)
        ctx["super_count"] = sum(1 for m in toggleable if m.is_visible)
        ctx["walidata_count"] = sum(1 for m in toggleable if m.visible_walidata)
        return ctx

    def post(self, request, *args, **kwargs):
        from .models import SidebarMenu

        SidebarMenu.ensure_defaults()
        super_keys = set(request.POST.getlist("visible_super"))
        wali_keys = set(request.POST.getlist("visible_walidata"))
        locked = SidebarMenu.LOCKED
        updated = 0
        # Dua kolom terpisah: Super Admin (is_visible) & Walidata (visible_walidata).
        # Menu Administrasi dikecualikan (dikontrol peran).
        for menu in SidebarMenu.objects.exclude(grup="Administrasi"):
            if menu.key in locked:
                # Selalu tampil untuk kedua peran.
                if not (menu.is_visible and menu.visible_walidata):
                    menu.is_visible = True
                    menu.visible_walidata = True
                    menu.save(update_fields=["is_visible", "visible_walidata", "updated"])
                continue
            new_super = menu.key in super_keys
            new_wali = menu.key in wali_keys
            if menu.is_visible != new_super or menu.visible_walidata != new_wali:
                menu.is_visible = new_super
                menu.visible_walidata = new_wali
                menu.save(update_fields=["is_visible", "visible_walidata", "updated"])
                updated += 1
        if updated:
            messages.success(
                request, f"Tampilan menu sidebar diperbarui ({updated} perubahan)."
            )
        else:
            messages.success(request, "Tidak ada perubahan pada tampilan menu.")
        return redirect(reverse("dst_auth:backend"))


class PengaturanView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/pengaturan.html"
    page_slug = "pengaturan"
    superuser_only = True
    page_title = "Pengaturan Sistem"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Pengaturan Sistem", None),
    ]

    def _site(self):
        return fresh_site()

    def get_context_data(self, **kwargs):
        from django.conf import settings as dj_settings
        from django.db import connection
        import django
        import sys

        ctx = super().get_context_data(**kwargs)

        site = self._site()
        ogc = (dj_settings.OGC_SERVER or {}).get("default", {}) if hasattr(
            dj_settings, "OGC_SERVER"
        ) else {}

        try:
            from geonode import __version__ as gn_v

            geonode_version = ".".join(str(p) for p in gn_v[:3])
        except Exception:
            geonode_version = "—"

        ctx["site"] = site
        ctx["system"] = {
            "language": dj_settings.LANGUAGE_CODE,
            "timezone": str(dj_settings.TIME_ZONE),
            "debug": dj_settings.DEBUG,
            "site_name_setting": getattr(dj_settings, "SITENAME", ""),
            "site_url_setting": getattr(dj_settings, "SITEURL", ""),
            "django_version": django.get_version(),
            "python_version": sys.version.split()[0],
            "geonode_version": geonode_version,
        }
        ctx["services"] = {
            "geoserver_url": ogc.get("PUBLIC_LOCATION") or ogc.get("LOCATION") or "—",
            "geoserver_user": ogc.get("USER") or "—",
            "db_engine": connection.settings_dict.get("ENGINE", "").rsplit(".", 1)[-1]
            or "—",
            "db_name": connection.settings_dict.get("NAME") or "—",
            "db_host": connection.settings_dict.get("HOST") or "localhost",
            "email_host": getattr(dj_settings, "EMAIL_HOST", "") or "—",
            "email_port": getattr(dj_settings, "EMAIL_PORT", "") or "—",
            "email_from": getattr(dj_settings, "DEFAULT_FROM_EMAIL", "") or "—",
        }

        max_upload = getattr(dj_settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 0) or 0
        max_file = getattr(dj_settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 0) or 0
        max_file_upload = getattr(dj_settings, "DEFAULT_MAX_UPLOAD_SIZE", 0) or 0
        ctx["limits"] = {
            # Batas efektif ukuran file unggahan GeoNode (yang benar-benar membatasi).
            "max_upload_mb": round(max_file_upload / 1024 / 1024, 1) if max_file_upload else 0,
            # Ambang teknis Django (bukan batas ukuran unggahan).
            "file_upload_mb": round(max_file / 1024 / 1024, 1) if max_file else 0,
            "data_upload_mb": round(max_upload / 1024 / 1024, 1) if max_upload else 0,
        }

        ctx["counts"] = {
            "datasets": Dataset.objects.count(),
            "documents": Document.objects.count(),
            "users": User.objects.exclude(pk=-1).count(),
        }

        # Identitas tambahan (Nama Kabupaten, zona waktu) + logo situs aktif.
        from .models import SiteIdentity

        identity = SiteIdentity.load()
        ctx["nama_kabupaten"] = identity.nama_kabupaten
        ctx["tz_code"] = identity.timezone
        ctx["tz_choices"] = SiteIdentity.TIMEZONE_CHOICES
        try:
            from geonode.themes.models import GeoNodeThemeCustomization

            theme = GeoNodeThemeCustomization.objects.filter(is_enabled=True).first()
            ctx["theme_logo_url"] = theme.logo.url if theme and theme.logo else ""
        except Exception:
            ctx["theme_logo_url"] = ""

        # ── FOLUR: daftar fokus komoditas (CRUD) ───────────────────
        from .models import KomoditasFokus, ImplementingPartner

        ctx["komoditas_list"] = list(
            KomoditasFokus.objects.select_related("dataset", "dokumen").all()
        )
        edit_id = self.request.GET.get("edit_komoditas")
        ctx["komoditas_edit"] = (
            KomoditasFokus.objects.filter(pk=edit_id).first() if edit_id else None
        )
        ctx["dataset_options"] = list(
            Dataset.objects.filter(is_published=True).only("pk", "title", "name").order_by("title")[:500]
        )
        ctx["dokumen_options"] = list(
            Document.objects.filter(is_published=True).only("pk", "title").order_by("title")[:500]
        )

        # ── Implementing Partners (CRUD upload logo) ───────────────
        ctx["mitra_list"] = list(ImplementingPartner.objects.all())
        mid = self.request.GET.get("edit_mitra")
        ctx["mitra_edit"] = ImplementingPartner.objects.filter(pk=mid).first() if mid else None

        # ── Indikator Strategis (CRUD, ikon dari folder statis) ────
        from .models import IndikatorStrategis
        from django.conf import settings as _ind_settings

        _ikon_base = f"{_ind_settings.STATIC_URL}dst-district/img/indikator/"
        indikator_list = list(IndikatorStrategis.objects.all())
        for _ind in indikator_list:
            _ind.ikon_url = (_ikon_base + _ind.ikon) if _ind.ikon else ""
        ctx["indikator_list"] = indikator_list
        iid = self.request.GET.get("edit_indikator")
        indikator_edit = (
            IndikatorStrategis.objects.filter(pk=iid).first() if iid else None
        )
        if indikator_edit:
            indikator_edit.ikon_url = (
                (_ikon_base + indikator_edit.ikon) if indikator_edit.ikon else ""
            )
        ctx["indikator_edit"] = indikator_edit

        # ── Layanan Data (CRUD, gambar dari folder statis / URL) ───
        from .models import LayananData

        _lay_base = f"{_ind_settings.STATIC_URL}dst-district/img/layanan/"

        def _lay_url(obj):
            if not obj or not obj.ikon:
                return ""
            return obj.ikon if obj.ikon.startswith("http") else (_lay_base + obj.ikon)

        layanan_list = list(LayananData.objects.all())
        for _lay in layanan_list:
            _lay.ikon_url = _lay_url(_lay)
        ctx["layanan_list"] = layanan_list
        lyid = self.request.GET.get("edit_layanan")
        layanan_edit = LayananData.objects.filter(pk=lyid).first() if lyid else None
        if layanan_edit:
            layanan_edit.ikon_url = _lay_url(layanan_edit)
        ctx["layanan_edit"] = layanan_edit

        # ── WebGIS: pilihan map referensi default layer ─────────────
        from geonode.maps.models import Map
        from django.conf import settings as dj_settings

        ctx["webgis_reference_map_id"] = identity.webgis_reference_map_id
        ctx["webgis_reference_map_id_fallback"] = getattr(
            dj_settings, "WEBGIS_REFERENCE_MAP_ID", 1
        )
        ctx["map_options"] = list(
            Map.objects.only("pk", "title").order_by("title")[:500]
        )

        # ── Backup Database (daftar + unduh) ───────────────────────
        ctx["backups"], ctx["backup_dir"] = list_db_backups()

        # ── Restore Data Wilayah (cakupan BIG) ─────────────────────
        ctx["cakupan_level"] = identity.cakupan_level
        ctx["cakupan_kode_prov"] = identity.cakupan_kode_prov
        ctx["cakupan_nama_prov"] = identity.cakupan_nama_prov
        ctx["cakupan_kode_kab"] = identity.cakupan_kode_kab
        ctx["cakupan_nama_kab"] = identity.cakupan_nama_kab
        try:
            from .models import (
                RefWilayahProvinsi,
                RefWilayahKabkota,
                RefWilayahKecamatan,
                RefWilayahDesa,
            )

            ctx["wilayah_counts"] = {
                "provinsi": RefWilayahProvinsi.objects.count(),
                "kabkota": RefWilayahKabkota.objects.count(),
                "kecamatan": RefWilayahKecamatan.objects.count(),
                "desa": RefWilayahDesa.objects.count(),
            }
            # Kab default panel kec/desa: kabupaten yang BENAR-BENAR ter-restore
            # (RefWilayah*), bukan SiteIdentity.cakupan yang bisa basi. Fallback
            # ke cakupan bila belum ada data restore.
            ctx["wil_active_kab"] = (
                RefWilayahKabkota.objects.values_list("kode_pum", flat=True).first()
                or identity.cakupan_kode_kab or ""
            )
        except Exception:
            ctx["wilayah_counts"] = {}
            ctx["wil_active_kab"] = ""
        try:
            from django.core.cache import cache
            from .management.commands.sync_wilayah_big import fetch_provinsi_options

            opts = cache.get("wilayah_provinsi_options")
            if opts is None:
                opts = fetch_provinsi_options()
                cache.set("wilayah_provinsi_options", opts, 60 * 60 * 24)
            ctx["provinsi_options"] = opts
        except Exception:
            ctx["provinsi_options"] = []
        return ctx

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Hanya Super Admin yang dapat mengubah pengaturan.")
            return redirect(reverse("dst_auth:pengaturan"))

        form = request.POST.get("form")

        # ── Backup Database: buat backup sekarang (pg_dump | gzip) ──
        if form == "backup_create":
            import os as _os
            import subprocess
            from datetime import datetime
            from django.conf import settings as dj_settings

            backup_url = reverse("dst_auth:pengaturan") + "#backup"
            db = dj_settings.DATABASES.get("default", {})
            backup_dir = _backup_dir()
            if not _os.path.isdir(backup_dir):
                messages.error(request, f"Direktori backup tidak tersedia: {backup_dir}")
                return redirect(backup_url)

            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            fname = f"db-{db.get('NAME', 'database')}-{ts}.sql.gz"
            out_path = _os.path.join(backup_dir, fname)
            env = {**_os.environ, "PGPASSWORD": str(db.get("PASSWORD") or "")}
            cmd = [
                "pg_dump",
                "-h", str(db.get("HOST") or "localhost"),
                "-p", str(db.get("PORT") or "5432"),
                "-U", str(db.get("USER") or ""),
                "-d", str(db.get("NAME") or ""),
                "--no-owner", "--no-privileges",
                "--clean", "--if-exists",
                # Schema 'wilayah' (data referensi batas administrasi BIG) bersifat
                # statis & berukuran besar — dikecualikan dari backup rutin. Disimpan
                # terpisah sebagai artefak dump sekali (wilayah_data.dump).
                "--exclude-schema=wilayah",
            ]
            try:
                with open(out_path, "wb") as fout:
                    dump = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                    gz = subprocess.Popen(["gzip", "-c"], stdin=dump.stdout, stdout=fout)
                    dump.stdout.close()
                    gz.communicate(timeout=600)
                    err = dump.stderr.read().decode("utf-8", "replace")[:300]
                    dump.wait(timeout=10)
                if dump.returncode != 0:
                    try:
                        _os.remove(out_path)
                    except OSError:
                        pass
                    messages.error(request, f"Backup gagal: {err or 'pg_dump error'}")
                else:
                    size = _human_size(_os.path.getsize(out_path))
                    messages.success(request, f"Backup berhasil dibuat: {fname} ({size}).")
            except Exception as exc:  # noqa: BLE001
                try:
                    _os.remove(out_path)
                except OSError:
                    pass
                messages.error(request, f"Backup gagal: {exc}")
            return redirect(backup_url)

        # ── Restore Database: upload berkas backup lalu psql ───────
        if form == "backup_restore":
            import os as _os
            import tempfile
            import subprocess
            from django.conf import settings as dj_settings

            backup_url = reverse("dst_auth:pengaturan") + "#backup"
            f = request.FILES.get("restore_file")
            if not f:
                messages.error(request, "Berkas restore wajib diunggah.")
                return redirect(backup_url)
            lname = f.name.lower()
            if not (lname.endswith(".sql") or lname.endswith(".sql.gz") or lname.endswith(".gz")):
                messages.error(request, "Format tidak didukung. Gunakan berkas .sql atau .sql.gz.")
                return redirect(backup_url)

            db = dj_settings.DATABASES.get("default", {})
            env = {
                **_os.environ,
                "PGPASSWORD": str(db.get("PASSWORD") or ""),
                # Jangan menggantung worker bila ada lock; gagal cepat.
                "PGOPTIONS": "-c lock_timeout=20000 -c statement_timeout=600000",
            }
            psql = [
                "psql",
                "-h", str(db.get("HOST") or "localhost"),
                "-p", str(db.get("PORT") or "5432"),
                "-U", str(db.get("USER") or ""),
                "-d", str(db.get("NAME") or ""),
                "-v", "ON_ERROR_STOP=0",
            ]

            tmpdir = tempfile.mkdtemp()
            tmp_path = _os.path.join(tmpdir, f.name)
            with open(tmp_path, "wb") as out:
                for chunk in f.chunks():
                    out.write(chunk)

            err_text = ""
            ok = False
            try:
                if lname.endswith(".gz"):
                    gz = subprocess.Popen(["gunzip", "-c", tmp_path], stdout=subprocess.PIPE)
                    proc = subprocess.Popen(psql, stdin=gz.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                    gz.stdout.close()
                    _, err = proc.communicate(timeout=900)
                    gz.wait(timeout=10)
                else:
                    with open(tmp_path, "rb") as fin:
                        proc = subprocess.Popen(psql, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                        _, err = proc.communicate(timeout=900)
                err_text = (err or b"").decode("utf-8", "replace")
                ok = proc.returncode == 0
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Restore gagal: {exc}")
                return redirect(backup_url)
            finally:
                try:
                    _os.remove(tmp_path)
                    _os.rmdir(tmpdir)
                except OSError:
                    pass

            # ON_ERROR_STOP=0 → returncode 0 walau ada error per-statement; laporkan stderr.
            if err_text.strip():
                snippet = err_text.strip().splitlines()
                tail = " · ".join(snippet[-3:])[:400]
                messages.warning(
                    request,
                    f"Restore selesai dengan sebagian peringatan/error: {tail}. "
                    f"Disarankan restart layanan (django/celery) lalu periksa data.",
                )
            elif ok:
                messages.success(
                    request,
                    "Restore database berhasil. Disarankan restart layanan (django/celery) agar bersih.",
                )
            else:
                messages.error(request, "Restore gagal dijalankan (psql error).")
            return redirect(backup_url)

        # ── Restore Data Wilayah: set cakupan + muat region (Celery) ──
        if form == "wilayah_restore":
            from .models import SiteIdentity

            wil_url = reverse("dst_auth:pengaturan") + "#wilayah"
            level = (request.POST.get("cakupan_level") or "").strip()
            kode_prov = (request.POST.get("kode_prov") or "").strip()
            nama_prov = (request.POST.get("nama_prov") or "").strip()
            kode_kab = (request.POST.get("kode_kab") or "").strip()
            nama_kab = (request.POST.get("nama_kab") or "").strip()

            if level not in ("provinsi", "kabupaten") or not kode_prov:
                messages.error(request, "Pilih level cakupan dan provinsi terlebih dahulu.")
                return redirect(wil_url)
            if level == "kabupaten" and not kode_kab:
                messages.error(request, "Level kabupaten: pilih kabupaten/kota dulu.")
                return redirect(wil_url)

            identity = SiteIdentity.load()
            identity.cakupan_level = level
            identity.cakupan_kode_prov = kode_prov
            identity.cakupan_nama_prov = nama_prov
            identity.cakupan_kode_kab = kode_kab if level == "kabupaten" else ""
            identity.cakupan_nama_kab = nama_kab if level == "kabupaten" else ""

            # "Nama Wilayah" (Identitas situs) ikut terupdate dari region terpilih.
            if level == "kabupaten":
                region_nama = nama_kab.strip()
                # WADMKK BIG: kota sudah berawalan "Kota ", kabupaten polos.
                # Tambah "Kabupaten " bila belum berjenis; fallback dari kode
                # (akhiran >= 71 = kota) bila WADMKK tak memberi prefix.
                _low = region_nama.lower()
                if region_nama and not (_low.startswith("kabupaten")
                                        or _low.startswith("kota")):
                    _kd = "".join(c for c in (kode_kab or "") if c.isdigit())
                    _is_kota = len(_kd) >= 2 and int(_kd[-2:]) >= 71
                    region_nama = f"{'Kota' if _is_kota else 'Kabupaten'} {region_nama}"
            else:
                region_nama = nama_prov.strip()
                if region_nama and not region_nama.lower().startswith("provinsi"):
                    region_nama = f"Provinsi {region_nama}"
            if region_nama:
                identity.nama_kabupaten = region_nama[:100]

            identity.save()

            # Logo default region (seed_data/logo_kab|logo_prov) → logo situs; selalu timpa.
            if _apply_seed_region_logo(level, kode_prov, kode_kab):
                _kode = kode_kab if level == "kabupaten" else kode_prov
                _lbl = "kabupaten" if level == "kabupaten" else "provinsi"
                messages.success(
                    request,
                    f"Logo situs diset ke logo default {_lbl} (kode {_kode}).",
                )

            try:
                from .tasks import load_wilayah_region

                load_wilayah_region.delay(level, kode_prov, kode_kab or None)
                target = nama_kab if level == "kabupaten" else nama_prov
                messages.success(
                    request,
                    f"Pemuatan data wilayah '{target or kode_prov}' dimulai di latar. "
                    "Schema 'wilayah' dikosongkan lalu diisi region ini — segarkan "
                    "halaman untuk memantau jumlah baris.",
                )
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal memicu pemuatan data wilayah: {exc}")
            return redirect(wil_url)

        # ── FOLUR: simpan / hapus / toggle tampil fokus komoditas ──
        if form in ("komoditas_save", "komoditas_delete", "komoditas_toggle"):
            from .models import KomoditasFokus

            folur_url = reverse("dst_auth:pengaturan") + "#folur"
            kid = request.POST.get("komoditas_id") or ""

            if form == "komoditas_toggle":
                obj = KomoditasFokus.objects.filter(pk=kid).first()
                if obj:
                    obj.aktif = request.POST.get("aktif") == "on"
                    obj.save(update_fields=["aktif", "updated"])
                    messages.success(
                        request,
                        f"Komoditas '{obj.nama}' kini {'tampil' if obj.aktif else 'disembunyikan'}.",
                    )
                else:
                    messages.error(request, "Komoditas tidak ditemukan.")
                return redirect(folur_url)

            if form == "komoditas_delete":
                obj = KomoditasFokus.objects.filter(pk=kid).first()
                if obj:
                    nama = obj.nama
                    obj.delete()
                    messages.success(request, f"Komoditas '{nama}' dihapus.")
                else:
                    messages.error(request, "Komoditas tidak ditemukan.")
                return redirect(folur_url)

            # komoditas_save (create bila tanpa id, update bila ada id)
            nama = (request.POST.get("nama") or "").strip()
            if not nama:
                messages.error(request, "Nama komoditas wajib diisi.")
                return redirect(folur_url)
            obj = KomoditasFokus.objects.filter(pk=kid).first() if kid else None
            if obj is None:
                obj = KomoditasFokus()
            obj.nama = nama[:120]
            obj.deskripsi = (request.POST.get("deskripsi") or "").strip()
            ds_id = request.POST.get("dataset") or ""
            obj.dataset = Dataset.objects.filter(pk=ds_id).first() if ds_id else None
            dok_id = request.POST.get("dokumen") or ""
            obj.dokumen = Document.objects.filter(pk=dok_id).first() if dok_id else None
            try:
                obj.urutan = int(request.POST.get("urutan") or 0)
            except (TypeError, ValueError):
                obj.urutan = 0
            obj.aktif = request.POST.get("aktif") == "on"
            img = request.FILES.get("gambar")
            if img:
                obj.gambar = img
            try:
                obj.save()
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan komoditas: {exc}")
                return redirect(folur_url)
            messages.success(request, f"Komoditas '{obj.nama}' berhasil disimpan.")
            return redirect(folur_url)

        # ── Implementing Partners: simpan / hapus / toggle ─────────
        if form in ("mitra_save", "mitra_delete", "mitra_toggle"):
            from .models import ImplementingPartner

            mitra_url = reverse("dst_auth:pengaturan") + "#mitra"
            mid = request.POST.get("mitra_id") or ""

            if form == "mitra_toggle":
                obj = ImplementingPartner.objects.filter(pk=mid).first()
                if obj:
                    obj.aktif = request.POST.get("aktif") == "on"
                    obj.save(update_fields=["aktif", "updated"])
                    messages.success(
                        request,
                        f"Mitra '{obj.nama}' kini {'tampil' if obj.aktif else 'disembunyikan'}.",
                    )
                else:
                    messages.error(request, "Mitra tidak ditemukan.")
                return redirect(mitra_url)

            if form == "mitra_delete":
                obj = ImplementingPartner.objects.filter(pk=mid).first()
                if obj:
                    nama = obj.nama
                    obj.delete()
                    messages.success(request, f"Mitra '{nama}' dihapus.")
                else:
                    messages.error(request, "Mitra tidak ditemukan.")
                return redirect(mitra_url)

            # mitra_save (create/update)
            nama = (request.POST.get("nama") or "").strip()
            if not nama:
                messages.error(request, "Nama mitra wajib diisi.")
                return redirect(mitra_url)
            obj = ImplementingPartner.objects.filter(pk=mid).first() if mid else None
            is_new = obj is None
            if obj is None:
                obj = ImplementingPartner()
            logo = request.FILES.get("logo")
            if is_new and not logo:
                messages.error(request, "Logo wajib diunggah untuk mitra baru.")
                return redirect(mitra_url)
            obj.nama = nama[:150]
            obj.tautan = (request.POST.get("tautan") or "").strip()
            try:
                obj.urutan = int(request.POST.get("urutan") or 0)
            except (TypeError, ValueError):
                obj.urutan = 0
            obj.aktif = request.POST.get("aktif") == "on"
            if logo:
                obj.logo = logo
            try:
                obj.save()
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan mitra: {exc}")
                return redirect(mitra_url)
            messages.success(request, f"Mitra '{obj.nama}' berhasil disimpan.")
            return redirect(mitra_url)

        # ── Indikator Strategis: simpan / hapus / toggle ───────────
        if form in ("indikator_save", "indikator_delete", "indikator_toggle"):
            from .models import IndikatorStrategis

            ind_url = reverse("dst_auth:pengaturan") + "#indikator"
            iid = request.POST.get("indikator_id") or ""

            if form == "indikator_toggle":
                obj = IndikatorStrategis.objects.filter(pk=iid).first()
                if obj:
                    obj.aktif = request.POST.get("aktif") == "on"
                    obj.save(update_fields=["aktif", "updated"])
                    messages.success(
                        request,
                        f"Indikator '{obj.judul}' kini {'tampil' if obj.aktif else 'disembunyikan'}.",
                    )
                else:
                    messages.error(request, "Indikator tidak ditemukan.")
                return redirect(ind_url)

            if form == "indikator_delete":
                obj = IndikatorStrategis.objects.filter(pk=iid).first()
                if obj:
                    judul = obj.judul
                    obj.delete()
                    messages.success(request, f"Indikator '{judul}' dihapus.")
                else:
                    messages.error(request, "Indikator tidak ditemukan.")
                return redirect(ind_url)

            # indikator_save (create bila tanpa id, update bila ada id)
            judul = (request.POST.get("judul") or "").strip()
            nilai = (request.POST.get("nilai") or "").strip()
            if not judul or not nilai:
                messages.error(request, "Judul dan nilai indikator wajib diisi.")
                return redirect(ind_url)
            obj = IndikatorStrategis.objects.filter(pk=iid).first() if iid else None
            if obj is None:
                obj = IndikatorStrategis()
            obj.judul = judul[:120]
            obj.nilai = nilai[:50]
            obj.deskripsi = (request.POST.get("deskripsi") or "").strip()[:255]
            obj.ikon = (request.POST.get("ikon") or "").strip()[:100]
            try:
                obj.urutan = int(request.POST.get("urutan") or 0)
            except (TypeError, ValueError):
                obj.urutan = 0
            obj.aktif = request.POST.get("aktif") == "on"
            try:
                obj.save()
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan indikator: {exc}")
                return redirect(ind_url)
            messages.success(request, f"Indikator '{obj.judul}' berhasil disimpan.")
            return redirect(ind_url)

        # ── Layanan Data: simpan / hapus / toggle ──────────────────
        if form in ("layanan_save", "layanan_delete", "layanan_toggle"):
            from .models import LayananData

            lay_url = reverse("dst_auth:pengaturan") + "#layanan-data"
            lyid = request.POST.get("layanan_id") or ""

            if form == "layanan_toggle":
                obj = LayananData.objects.filter(pk=lyid).first()
                if obj:
                    obj.aktif = request.POST.get("aktif") == "on"
                    obj.save(update_fields=["aktif", "updated"])
                    messages.success(
                        request,
                        f"Layanan '{obj.judul}' kini {'tampil' if obj.aktif else 'disembunyikan'}.",
                    )
                else:
                    messages.error(request, "Layanan tidak ditemukan.")
                return redirect(lay_url)

            if form == "layanan_delete":
                obj = LayananData.objects.filter(pk=lyid).first()
                if obj:
                    judul = obj.judul
                    obj.delete()
                    messages.success(request, f"Layanan '{judul}' dihapus.")
                else:
                    messages.error(request, "Layanan tidak ditemukan.")
                return redirect(lay_url)

            # layanan_save (create bila tanpa id, update bila ada id)
            judul = (request.POST.get("judul") or "").strip()
            if not judul:
                messages.error(request, "Judul layanan wajib diisi.")
                return redirect(lay_url)
            obj = LayananData.objects.filter(pk=lyid).first() if lyid else None
            if obj is None:
                obj = LayananData()
            obj.judul = judul[:150]
            obj.ikon = (request.POST.get("ikon") or "").strip()[:255]
            obj.tautan = (request.POST.get("tautan") or "").strip()[:255]
            try:
                obj.urutan = int(request.POST.get("urutan") or 0)
            except (TypeError, ValueError):
                obj.urutan = 0
            obj.aktif = request.POST.get("aktif") == "on"
            try:
                obj.save()
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Gagal menyimpan layanan: {exc}")
                return redirect(lay_url)
            messages.success(request, f"Layanan '{obj.judul}' berhasil disimpan.")
            return redirect(lay_url)

        # ── WebGIS: simpan map referensi default layer ──────────────
        if form == "webgis_save":
            from .models import SiteIdentity

            webgis_url = reverse("dst_auth:pengaturan") + "#webgis"
            raw = (request.POST.get("webgis_reference_map_id") or "").strip()
            identity = SiteIdentity.load()
            if raw == "" or raw == "0":
                identity.webgis_reference_map_id = None
            else:
                try:
                    identity.webgis_reference_map_id = int(raw)
                except (TypeError, ValueError):
                    messages.error(request, "ID Map tidak valid.")
                    return redirect(webgis_url)
            identity.save()
            messages.success(request, "Pengaturan WebGIS berhasil disimpan.")
            return redirect(webgis_url)

        from .models import SiteIdentity

        # Form "Regional & versi" → zona waktu (WIB/WITA/WIT).
        if request.POST.get("form") == "regional":
            tz = (request.POST.get("timezone") or "").strip().upper()
            valid = {code for code, _ in SiteIdentity.TIMEZONE_CHOICES}
            if tz not in valid:
                messages.error(request, "Zona waktu tidak valid.")
                return redirect(reverse("dst_auth:pengaturan"))
            identity = SiteIdentity.load()
            identity.timezone = tz
            identity.save()
            messages.success(request, f"Zona waktu berhasil diubah ke {tz}.")
            return redirect(reverse("dst_auth:pengaturan"))

        # Form "Logo situs" → unggah / hapus logo (GeoNodeThemeCustomization aktif).
        if request.POST.get("form") in {"logo_upload", "logo_remove"}:
            redirect_to = reverse("dst_auth:pengaturan") + "#identitas"
            if not request.user.is_superuser:
                messages.error(request, "Hanya Super Admin yang dapat mengubah logo.")
                return redirect(redirect_to)
            try:
                from geonode.themes.models import GeoNodeThemeCustomization

                theme = GeoNodeThemeCustomization.objects.filter(
                    is_enabled=True
                ).first()
                if request.POST.get("form") == "logo_remove":
                    if theme and theme.logo:
                        theme.logo.delete(save=True)
                        messages.success(request, "Logo situs berhasil dihapus.")
                    else:
                        messages.info(request, "Belum ada logo untuk dihapus.")
                else:
                    logo_file = request.FILES.get("kabupaten_logo")
                    if not logo_file:
                        messages.error(request, "Tidak ada berkas logo yang dipilih.")
                        return redirect(redirect_to)
                    if theme is None:
                        ident = SiteIdentity.load()
                        theme = GeoNodeThemeCustomization(
                            name=ident.nama_kabupaten or self._site().name,
                            is_enabled=True,
                        )
                    theme.logo = logo_file
                    theme.save()
                    messages.success(request, "Logo situs berhasil diperbarui.")
            except Exception as exc:  # pragma: no cover - defensif
                messages.error(request, f"Logo gagal diproses: {exc}")
            return redirect(redirect_to)

        site = self._site()
        name = (request.POST.get("site_name") or "").strip()
        domain = (request.POST.get("site_domain") or "").strip()

        if not name or not domain:
            messages.error(request, "Nama dan domain tidak boleh kosong.")
            return redirect(reverse("dst_auth:pengaturan"))

        site.name = name[:50]
        site.domain = domain[:100]
        site.save(update_fields=["name", "domain"])
        # Bersihkan SITE_CACHE worker ini; konsistensi lintas-worker dijamin fresh_site().
        from django.contrib.sites.models import Site as _Site

        _Site.objects.clear_cache()

        # Nama Kabupaten → model SiteIdentity (singleton).
        from .models import SiteIdentity

        identity = SiteIdentity.load()
        identity.nama_kabupaten = (request.POST.get("nama_kabupaten") or "").strip()[:100]
        identity.save()

        messages.success(request, "Identitas situs berhasil diperbarui.")
        return redirect(reverse("dst_auth:pengaturan"))


class TopikKategoriView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Topik Kategori: CRUD untuk ``geonode.base.TopicCategory``.

    Mengelola vocabulary kategori ISO 19115 (TopicCategory) yang dipakai
    Dataset/Dokumen — bertautan dengan kartu "Layanan Data" di Landing. Hanya
    Super Admin yang dapat menambah/ubah/hapus (perubahan global GeoNode).
    """

    template_name = "dst-district/admin/topik_kategori.html"
    page_slug = "topik_kategori"
    superuser_only = True
    page_title = "Topik Kategori"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Topik Kategori", None),
    ]

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from geonode.base.models import TopicCategory, ResourceBase

        ctx = super().get_context_data(**kwargs)
        # is_choice=True di atas (-is_choice), lalu urut identifier.
        qs = TopicCategory.objects.all().order_by("-is_choice", "identifier")

        # Jumlah resource (dataset/dokumen/map) yang memakai tiap kategori —
        # berguna sebagai peringatan sebelum menghapus.
        counts = {
            row["category"]: row["c"]
            for row in ResourceBase.objects.filter(category__isnull=False)
            .values("category")
            .annotate(c=Count("id"))
        }
        kategori_list = list(qs)
        for cat in kategori_list:
            cat.resource_count = counts.get(cat.pk, 0)

        ctx["kategori_list"] = kategori_list
        ctx["kategori_total"] = len(kategori_list)
        ctx["kategori_choice"] = sum(1 for c in kategori_list if c.is_choice)
        ctx["kategori_non_choice"] = ctx["kategori_total"] - ctx["kategori_choice"]
        kid = self.request.GET.get("edit_kategori")
        ctx["kategori_edit"] = (
            TopicCategory.objects.filter(pk=kid).first() if kid else None
        )
        return ctx

    def post(self, request, *args, **kwargs):
        from geonode.base.models import TopicCategory

        url = reverse("dst_auth:topik_kategori")
        if not request.user.is_superuser:
            messages.error(request, "Hanya Super Admin yang dapat mengubah Topik Kategori.")
            return redirect(url)

        form = request.POST.get("form") or ""
        kid = request.POST.get("kategori_id") or ""

        if form == "kategori_toggle":
            obj = TopicCategory.objects.filter(pk=kid).first()
            if obj:
                obj.is_choice = request.POST.get("is_choice") == "on"
                obj.save(update_fields=["is_choice"])
                messages.success(
                    request,
                    f"Kategori '{obj.identifier}' kini {'jadi pilihan' if obj.is_choice else 'bukan pilihan'}.",
                )
            else:
                messages.error(request, "Kategori tidak ditemukan.")
            return redirect(url)

        if form == "kategori_delete":
            obj = TopicCategory.objects.filter(pk=kid).first()
            if obj:
                ident = obj.identifier
                obj.delete()
                messages.success(request, f"Kategori '{ident}' dihapus.")
            else:
                messages.error(request, "Kategori tidak ditemukan.")
            return redirect(url)

        # kategori_save (create bila tanpa id, update bila ada id)
        identifier = (request.POST.get("identifier") or "").strip()
        if not identifier:
            messages.error(request, "Identifier wajib diisi.")
            return redirect(url)
        obj = TopicCategory.objects.filter(pk=kid).first() if kid else None
        if obj is None:
            obj = TopicCategory()
        obj.identifier = identifier[:255]
        obj.description = (request.POST.get("description") or "").strip()
        obj.gn_description = (request.POST.get("gn_description") or "").strip()
        obj.fa_class = (request.POST.get("fa_class") or "").strip()[:64] or "fa-times"
        obj.is_choice = request.POST.get("is_choice") == "on"
        try:
            obj.save()
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Gagal menyimpan kategori: {exc}")
            return redirect(url)
        messages.success(request, f"Kategori '{obj.identifier}' berhasil disimpan.")
        return redirect(url)


class WalidataView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Walidata: CRUD daftar instansi walidata (wali data).

    Menyimpan singkatan, kepanjangan, dan alamat tiap instansi walidata di
    daerah. Menu grup Administrasi — hanya Super Admin yang dapat mengakses.
    """

    template_name = "dst-district/admin/walidata.html"
    page_slug = "walidata"
    superuser_only = True
    page_title = "Walidata"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Walidata", None),
    ]

    def get_context_data(self, **kwargs):
        from .models import Walidata

        ctx = super().get_context_data(**kwargs)
        walidata_list = list(Walidata.objects.all())
        ctx["walidata_list"] = walidata_list
        ctx["walidata_total"] = len(walidata_list)
        wid = self.request.GET.get("edit")
        ctx["walidata_edit"] = (
            Walidata.objects.filter(pk=wid).first() if wid else None
        )
        return ctx

    def post(self, request, *args, **kwargs):
        from .models import Walidata

        url = reverse("dst_auth:walidata")
        form = request.POST.get("form") or ""
        wid = request.POST.get("walidata_id") or ""

        if form == "walidata_delete":
            obj = Walidata.objects.filter(pk=wid).first()
            if obj:
                nama = obj.nama
                obj.delete()
                messages.success(request, f"Walidata '{nama}' dihapus.")
            else:
                messages.error(request, "Walidata tidak ditemukan.")
            return redirect(url)

        # walidata_save (create bila tanpa id, update bila ada id)
        nama = (request.POST.get("nama") or "").strip()
        if not nama:
            messages.error(request, "Singkatan wajib diisi.")
            return redirect(url)
        obj = Walidata.objects.filter(pk=wid).first() if wid else None
        if obj is None:
            obj = Walidata()
        obj.nama = nama[:120]
        obj.kepanjangan = (request.POST.get("kepanjangan") or "").strip()[:255]
        obj.alamat = (request.POST.get("alamat") or "").strip()
        try:
            obj.urutan = int(request.POST.get("urutan") or 0)
        except (TypeError, ValueError):
            obj.urutan = 0
        try:
            obj.save()
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Gagal menyimpan walidata: {exc}")
            return redirect(url)
        messages.success(request, f"Walidata '{obj.nama}' berhasil disimpan.")
        return redirect(url)


class IntegrasiSatuDataView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Integrasi Satu Data: harvest katalog CKAN kabupaten.

    Admin menempel basis URL portal Satu Data Kabupaten (CKAN) lalu menekan
    tombol Harvest untuk menarik seluruh dataset + file (resource) ke database
    lokal, lalu menelusurinya sebagai daftar + detail. Harvest manual & idempoten
    (lihat ``geonode_project.satudata.harvest_satudata``). Halaman dapat dibuka
    staff + Super Admin; aksi harvest/hapus khusus Super Admin.
    """

    template_name = "dst-district/admin/integrasi_satudata.html"
    page_slug = "integrasi_satudata"
    page_title = "Integrasi Satu Data"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Distribusi & Akses", None),
        ("Integrasi Satu Data", None),
    ]

    def get_context_data(self, **kwargs):
        from django.db.models import Count
        from .models import SatuDataSource, SatuDataset, Walidata

        ctx = super().get_context_data(**kwargs)
        source = SatuDataSource.objects.first()
        ctx["source"] = source

        qs = SatuDataset.objects.all().select_related("walidata").prefetch_related("resources")
        if source:
            qs = qs.filter(source=source)
        q = (self.request.GET.get("q") or "").strip()
        ctx["q"] = q
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(organisasi__icontains=q)
                | Q(tags__icontains=q)
            )
        # Filter Walidata: id tertentu, atau "none" untuk yang belum terpetakan.
        wsel = (self.request.GET.get("walidata") or "").strip()
        ctx["walidata_sel"] = wsel
        if wsel == "none":
            qs = qs.filter(walidata__isnull=True)
        elif wsel.isdigit():
            qs = qs.filter(walidata_id=int(wsel))

        from .satudata_docs import ALLOWED_EXT, _ext_from
        from geonode.documents.models import Document

        datasets = list(qs)
        # Validasi keberadaan Dokumen sekali jalan: bila dokumen GeoNode sudah
        # dihapus, resource dianggap BELUM terdaftar (checkbox aktif lagi) — walau
        # FK document_id-nya kebetulan masih menggantung.
        doc_ids = {r.document_id for d in datasets for r in d.resources.all() if r.document_id}
        existing_docs = (
            set(Document.objects.filter(pk__in=doc_ids).values_list("pk", flat=True))
            if doc_ids
            else set()
        )
        for d in datasets:
            fmts = []
            n_reg = 0  # resource yang Dokumennya MASIH ADA di GeoNode
            n_able = 0  # resource yang *bisa* didaftarkan (format dokumen + ada URL)
            for r in d.resources.all():
                f = (r.format or "").strip().upper()
                if f and f not in fmts:
                    fmts.append(f)
                if r.document_id and r.document_id in existing_docs:
                    n_reg += 1
                if r.url and _ext_from(r.format, r.url) in ALLOWED_EXT:
                    n_able += 1
            d.format_list = fmts
            d.n_registered = n_reg
            d.n_registerable = n_able
        # Urutkan per organisasi (lalu judul) agar {% regroup %} di template
        # membentuk grup organisasi yang rapi & berurutan.
        datasets.sort(key=lambda d: ((d.organisasi or "").lower(), (d.title or "").lower()))
        ctx["datasets"] = datasets
        ctx["total"] = SatuDataset.objects.filter(source=source).count() if source else 0
        ctx["total_tampil"] = len(datasets)
        ctx["total_resource"] = sum(d.jumlah_resource for d in datasets)

        # Daftar Walidata yang terpakai (untuk dropdown filter) + jumlah tak terpetakan.
        if source:
            ctx["walidata_list"] = list(
                Walidata.objects.filter(satu_datasets__source=source)
                .annotate(n=Count("satu_datasets", filter=Q(satu_datasets__source=source)))
                .order_by("nama")
            )
            ctx["unmatched_count"] = SatuDataset.objects.filter(
                source=source, walidata__isnull=True
            ).count()
        else:
            ctx["walidata_list"] = []
            ctx["unmatched_count"] = 0

        # Panel "Pemetaan Organisasi → Walidata": tiap organisasi CKAN unik + jumlah
        # dataset + Walidata terpilih (override eksplisit, lalu nilai dataset saat ini).
        from .models import SatuDataOrgWalidata

        org_maps = []
        if source:
            explicit = {
                m.org_title: m.walidata_id
                for m in SatuDataOrgWalidata.objects.filter(source=source)
            }
            ds_wali = {}
            for d in (
                SatuDataset.objects.filter(source=source)
                .exclude(walidata__isnull=True)
                .values("organisasi", "walidata")
            ):
                ds_wali.setdefault(d["organisasi"], d["walidata"])
            org_rows = (
                SatuDataset.objects.filter(source=source)
                .values("organisasi")
                .annotate(n=Count("id"))
                .order_by("organisasi")
            )
            for row in org_rows:
                org = row["organisasi"] or ""
                wid = explicit[org] if org in explicit else ds_wali.get(org)
                org_maps.append(
                    {"org_title": org, "count": row["n"], "walidata_id": wid}
                )
        ctx["org_maps"] = org_maps
        ctx["org_unmapped_count"] = sum(1 for o in org_maps if not o["walidata_id"])
        ctx["walidata_master"] = list(Walidata.objects.all().order_by("urutan", "nama", "id"))

        dsid = self.request.GET.get("ds")
        detail = None
        if dsid:
            detail = (
                SatuDataset.objects.filter(pk=dsid, source=source).first()
                if source
                else SatuDataset.objects.filter(pk=dsid).first()
            )
        ctx["dataset_detail"] = detail
        ctx["detail_resources"] = (
            list(detail.resources.select_related("document")) if detail else []
        )
        ctx["detail_tags"] = (
            [t.strip() for t in detail.tags.split(",") if t.strip()] if detail else []
        )
        return ctx

    def post(self, request, *args, **kwargs):
        from .models import SatuDataSource, SatuDataset
        from .satudata import harvest_satudata, _norm_base

        url = reverse("dst_auth:integrasi_satudata")
        if not request.user.is_superuser:
            messages.error(request, "Aksi ini hanya dapat dilakukan oleh Super Admin.")
            return redirect(url)

        form = request.POST.get("form") or ""

        if form == "map_walidata":
            from .models import Walidata, SatuDataOrgWalidata

            source = SatuDataSource.objects.first()
            if not source:
                messages.error(request, "Belum ada sumber data — harvest dulu.")
                return redirect(url)
            orgs = request.POST.getlist("org")
            wals = request.POST.getlist("wal")
            if len(orgs) != len(wals):
                messages.error(request, "Data pemetaan tidak konsisten.")
                return redirect(url)
            valid_ids = set(Walidata.objects.values_list("pk", flat=True))
            n_org = n_ds = 0
            for org, wal in zip(orgs, wals):
                org = (org or "").strip()
                if not org:
                    continue
                wid = int(wal) if (wal or "").isdigit() and int(wal) in valid_ids else None
                SatuDataOrgWalidata.objects.update_or_create(
                    source=source, org_title=org, defaults={"walidata_id": wid}
                )
                n_ds += SatuDataset.objects.filter(
                    source=source, organisasi=org
                ).exclude(walidata_id=wid).update(walidata_id=wid)
                n_org += 1
            messages.success(
                request,
                f"Pemetaan {n_org} organisasi disimpan; {n_ds} dataset diperbarui Walidata-nya.",
            )
            return redirect(url)

        if form == "hapus_semua":
            source = SatuDataSource.objects.first()
            n = SatuDataset.objects.filter(source=source).delete()[0] if source else 0
            if source:
                source.last_jumlah = 0
                source.last_status = ""
                source.last_pesan = "Data dikosongkan."
                source.save(update_fields=["last_jumlah", "last_status", "last_pesan", "updated"])
            messages.success(request, f"{n} dataset dihapus dari basis data lokal.")
            return redirect(url)

        if form == "register_batch":
            from .satudata_docs import register_dataset_documents

            source = SatuDataSource.objects.first()
            verify = source.verifikasi_ssl if source else True
            ids = request.POST.getlist("ds")
            ds_all = list(SatuDataset.objects.filter(pk__in=ids)) if ids else []
            # Gerbang: hanya dataset yang sudah dipetakan ke Walidata yang boleh
            # didaftarkan ke Dokumen DST (organisasi tanpa Walidata sengaja dilewati).
            ds_qs = [d for d in ds_all if d.walidata_id]
            n_tanpa_wali = len(ds_all) - len(ds_qs)
            if not ds_qs:
                messages.error(
                    request,
                    "Dataset terpilih belum dipetakan ke Walidata — "
                    "tetapkan Walidata-nya dulu di panel Pemetaan Organisasi."
                    if n_tanpa_wali
                    else "Pilih setidaknya satu dataset.",
                )
                return redirect(url)
            total_dibuat = total_dilewati = total_gagal = 0
            for ds in ds_qs:
                res = register_dataset_documents(ds, request.user, verify=verify)
                total_dibuat += res["dibuat"]
                total_dilewati += res["dilewati"]
                total_gagal += res["gagal"]
            if total_dibuat:
                messages.success(
                    request,
                    f"{total_dibuat} berkas dari {len(ds_qs)} dataset didaftarkan sebagai Dokumen "
                    f"(draf, perlu ditinjau). {total_dilewati} dilewati, {total_gagal} gagal.",
                )
            elif total_gagal:
                messages.error(request, f"Gagal mendaftarkan {total_gagal} berkas.")
            else:
                messages.info(
                    request,
                    "Tidak ada berkas baru untuk didaftarkan "
                    "(semua sudah terdaftar atau format tidak didukung).",
                )
            return redirect(url)

        if form == "register_docs":
            from .satudata_docs import register_dataset_documents

            source = SatuDataSource.objects.first()
            dsid = request.POST.get("ds") or ""
            ds = SatuDataset.objects.filter(pk=dsid).first()
            back = f"{url}?ds={dsid}" if dsid else url
            if not ds:
                messages.error(request, "Dataset tidak ditemukan.")
                return redirect(url)
            if not ds.walidata_id:
                messages.error(
                    request,
                    "Dataset ini belum dipetakan ke Walidata — tetapkan Walidata-nya "
                    "dulu (panel Pemetaan Organisasi) sebelum mendaftarkan ke Dokumen.",
                )
                return redirect(back)
            verify = source.verifikasi_ssl if source else True
            res = register_dataset_documents(ds, request.user, verify=verify)
            if res["dibuat"]:
                messages.success(
                    request,
                    f"{res['dibuat']} berkas didaftarkan sebagai Dokumen (draf, perlu "
                    f"ditinjau). {res['dilewati']} dilewati, {res['gagal']} gagal.",
                )
            elif res["gagal"]:
                messages.error(
                    request,
                    f"Gagal mendaftarkan {res['gagal']} berkas. "
                    + ("; ".join(res["errors"][:2]) if res.get("errors") else ""),
                )
            else:
                messages.info(
                    request,
                    "Tidak ada berkas baru untuk didaftarkan "
                    "(semua sudah terdaftar atau format tidak didukung).",
                )
            return redirect(back)

        # form == "harvest"
        base_url = _norm_base(request.POST.get("base_url") or "")
        if not base_url:
            messages.error(request, "Basis URL CKAN wajib diisi.")
            return redirect(url)

        source, _ = SatuDataSource.objects.get_or_create(base_url=base_url)
        organisasi = (request.POST.get("organisasi") or "").strip()
        verify_ssl = request.POST.get("abaikan_ssl") != "on"
        dirty = []
        if organisasi != source.organisasi_filter:
            source.organisasi_filter = organisasi
            dirty.append("organisasi_filter")
        if verify_ssl != source.verifikasi_ssl:
            source.verifikasi_ssl = verify_ssl
            dirty.append("verifikasi_ssl")
        if dirty:
            source.save(update_fields=dirty + ["updated"])

        try:
            stats = harvest_satudata(
                base_url, organisasi=organisasi or None, source=source, verify=verify_ssl
            )
        except Exception as exc:  # noqa: BLE001
            source.last_status = "error"
            source.last_pesan = str(exc)[:255]
            source.save(update_fields=["last_status", "last_pesan", "updated"])
            messages.error(request, f"Harvest gagal: {exc}")
            return redirect(url)

        messages.success(
            request,
            f"Harvest selesai — {stats['jumlah']} dataset tersimpan "
            f"({stats['baru']} baru, {stats['update']} diperbarui).",
        )
        return redirect(url)


class KodeWilayahView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Kode Wilayah: relasi kode BPS (Wilkerstat) ↔ Kemendagri.

    Berjenjang Provinsi → Kab/Kota → Kecamatan → Desa, SELURUHNYA dari tabel
    referensi PERMANEN ``RefKodeBps`` yang kini lengkap se-Indonesia (38 prov,
    514 kab/kota, ±7.285 kec, ±83.723 desa). Tidak lagi bergantung pada wilayah
    cakupan yang sedang aktif — semua wilayah bisa ditelusuri sampai desa.
    """

    template_name = "dst-district/admin/kode_wilayah.html"
    page_slug = "kode_wilayah"
    page_title = "Kode Wilayah"
    breadcrumb = [("Administrasi", ""), ("Kode Wilayah", "")]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import RefKodeBps

        prov = (self.request.GET.get("prov") or "").strip()
        kab = (self.request.GET.get("kab") or "").strip()
        kec = (self.request.GET.get("kec") or "").strip()

        def by_prefix(level, prefix):
            """Baris RefKodeBps satu jenjang yang berada di bawah `prefix`
            (mis. kecamatan di bawah kab '73.17' -> kode_pum '73.17.xx')."""
            return list(
                RefKodeBps.objects.filter(
                    level=level, kode_pum__startswith=prefix + "."
                ).order_by("kode_pum")
            )

        prov_opts = list(
            RefKodeBps.objects.filter(level="provinsi").order_by("kode_pum")
        )
        kab_opts = by_prefix("kabkota", prov) if prov else []
        kec_opts = by_prefix("kecamatan", kab) if kab else []

        if kec:
            level, src = "desa", by_prefix("desa", kec)
        elif kab:
            level, src = "kecamatan", kec_opts
        elif prov:
            level, src = "kabkota", kab_opts
        else:
            level, src = "provinsi", prov_opts

        rows = [{"no": i, "bps": r.kode_bps, "pum": r.kode_pum,
                 "nama": r.nama, "logo": r.file_logo}
                for i, r in enumerate(src, 1)]

        labels = {"provinsi": "Provinsi", "kabkota": "Kabupaten/Kota",
                  "kecamatan": "Kecamatan", "desa": "Desa/Kelurahan"}
        ctx.update({
            "prov_opts": prov_opts, "kab_opts": kab_opts, "kec_opts": kec_opts,
            "sel_prov": prov, "sel_kab": kab, "sel_kec": kec,
            "rows": rows, "level": level, "level_label": labels[level],
            "is_kabkota": level == "kabkota",
            "periode": "2025 Semester 1 (BPS) — 2025 (Kemendagri)",
            "sumber_url": "https://sig.bps.go.id/bridging-kode/",
        })
        return ctx


class TemaView(LoginRequiredMixin, DstAdminPageView):
    """Panel Admin → Tema CMS: pilih & terapkan tema warna untuk seluruh DST."""

    template_name = "dst-district/admin/tema.html"
    page_slug = "tema"
    superuser_only = True
    page_title = "Tema CMS"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Tema CMS", None),
    ]

    def get_context_data(self, **kwargs):
        import json as _json
        from .models import SiteIdentity

        ctx = super().get_context_data(**kwargs)
        identity = SiteIdentity.load()
        raw = identity.theme or "simtaru"
        ctx["active_theme"] = "simtaru" if raw == "luwu" else raw
        ctx["theme_choices"] = SiteIdentity.THEME_CHOICES
        ctx["font_option"] = identity.font_option or 1
        # Peta tema→3 opsi font untuk pratinjau dinamis di form (JS).
        ctx["font_combos_json"] = _json.dumps(SiteIdentity.FONT_COMBOS)
        ctx["active_font_combos"] = SiteIdentity.FONT_COMBOS.get(
            ctx["active_theme"], SiteIdentity.FONT_COMBOS["simtaru"]
        )
        return ctx

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Hanya Super Admin yang dapat mengubah tema.")
            return redirect(reverse("dst_auth:tema"))
        from .models import SiteIdentity

        theme = (request.POST.get("theme") or "").strip()
        # Auto-migrasi: nilai lama "luwu" → "simtaru" (transisi pasca-rename).
        if theme == "luwu":
            theme = "simtaru"
        valid = {code for code, _ in SiteIdentity.THEME_CHOICES}
        if theme not in valid:
            messages.error(request, "Tema tidak valid.")
            return redirect(reverse("dst_auth:tema"))
        try:
            font_option = int(request.POST.get("font_option") or 1)
        except (TypeError, ValueError):
            font_option = 1
        if font_option not in (1, 2, 3):
            font_option = 1
        identity = SiteIdentity.load()
        identity.theme = theme
        identity.font_option = font_option
        identity.save()
        label = dict(SiteIdentity.THEME_CHOICES).get(theme, theme)
        messages.success(request, f"Tema '{label}' (font opsi {font_option}) diterapkan ke seluruh DST.")
        return redirect(reverse("dst_auth:tema"))


class ProfilView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/profil.html"
    page_slug = "profil"
    page_title = "Profil Pengguna"
    breadcrumb = [("Dashboard", "/dst-auth/dashboard/"), ("Profil Pengguna", None)]
    umum_allowed = True  # pengguna Umum boleh mengelola akun sendiri

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        full_name = user.get_full_name() or user.username
        initials = "".join(part[0] for part in full_name.split()[:2]).upper() or "U"
        if user.is_superuser:
            role = "Super Admin"
        elif user.is_staff:
            role = "Admin Walidata"
        else:
            role = "Pengguna"

        from avatar.utils import get_primary_avatar

        avatar = get_primary_avatar(user, width=160)
        photo_url = avatar.avatar_url(160, 160) if avatar else ""

        from allauth.account.models import EmailAddress

        email_verified = bool(user.email) and EmailAddress.objects.filter(
            user=user, email__iexact=user.email, verified=True
        ).exists()

        # Pilihan Nama Walidata (wired ke tabel Walidata) + seleksi saat ini.
        from .models import Walidata, WalidataMembership

        membership = (
            WalidataMembership.objects.filter(user=user)
            .select_related("walidata")
            .first()
        )
        current = membership.walidata if membership else None
        choices = []
        for w in Walidata.objects.all():
            if w.kepanjangan and w.kepanjangan != w.nama:
                label = f"{w.kepanjangan} ({w.nama})"
            else:
                label = w.nama
            choices.append({"id": w.pk, "label": label})
        ctx["walidata_choices"] = choices
        ctx["walidata_current_id"] = current.pk if current else None

        ctx["profile"] = {
            "full_name": full_name,
            "first_name": user.first_name or (full_name.split()[0] if full_name else ""),
            "email": user.email or "",
            "email_verified": email_verified,
            "initials": initials,
            "role": role,
            "department": (current.nama if current else "")
            or getattr(user, "organization", "")
            or "BAPPEDA Kabupaten",
            "is_active": user.is_active,
            "photo_url": photo_url,
        }
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "update_name":
            self._update_name(request)
        elif action == "update_walidata":
            self._update_walidata(request)
        elif action == "update_email":
            self._update_email(request)
        elif action == "update_password":
            self._update_password(request)
        elif action == "update_photo":
            self._update_photo(request)
        elif action == "remove_photo":
            self._remove_photo(request)
        else:
            messages.error(request, "Aksi tidak dikenal.")
        return redirect(reverse("dst_auth:profil"))

    def _update_name(self, request):
        user = request.user
        full_name = " ".join((request.POST.get("full_name") or "").split())

        if not full_name:
            messages.error(request, "Nama lengkap tidak boleh kosong.")
            return

        # Simpan nama lengkap apa adanya: kata pertama -> first_name, sisanya
        # -> last_name, sehingga get_full_name() mereproduksi teks yang sama
        # persis (tidak ada perubahan otomatis).
        parts = full_name.split(None, 1)
        user.first_name = parts[0][:150]
        user.last_name = (parts[1] if len(parts) > 1 else "")[:150]
        user.save(update_fields=["first_name", "last_name"])
        messages.success(request, "Nama berhasil disimpan.")

    def _update_walidata(self, request):
        from .models import Walidata, WalidataMembership

        user = request.user
        wid = (request.POST.get("walidata") or "").strip()
        walidata = None
        if wid:
            walidata = Walidata.objects.filter(pk=wid).first()
            if walidata is None:
                messages.error(request, "Walidata yang dipilih tidak ditemukan.")
                return
        membership, _ = WalidataMembership.objects.get_or_create(user=user)
        membership.walidata = walidata
        membership.save(update_fields=["walidata", "updated"])
        if walidata:
            messages.success(request, f"Nama Walidata diperbarui ke '{walidata.nama}'.")
        else:
            messages.success(request, "Nama Walidata dikosongkan.")

    def _update_email(self, request):
        user = request.user
        new_email = (request.POST.get("new_email") or "").strip().lower()

        if not new_email:
            messages.error(request, "Email baru tidak boleh kosong.")
            return
        try:
            validate_email(new_email)
        except ValidationError:
            messages.error(request, "Format email tidak valid.")
            return
        if new_email == (user.email or "").lower():
            messages.info(request, "Email baru sama dengan email saat ini.")
            return

        from allauth.account.models import EmailAddress

        if EmailAddress.objects.filter(email__iexact=new_email).exclude(user=user).exists():
            messages.error(request, "Email tersebut sudah digunakan akun lain.")
            return

        user.email = new_email
        user.save(update_fields=["email"])

        EmailAddress.objects.filter(user=user, primary=True).update(primary=False)
        EmailAddress.objects.update_or_create(
            user=user,
            email=new_email,
            defaults={"primary": True, "verified": False},
        )
        messages.success(
            request,
            f"Email berhasil diperbarui ke {new_email} dan langsung berlaku untuk login. "
            "Statusnya ditandai 'belum diverifikasi'.",
        )

    def _update_password(self, request):
        from django.contrib.auth import update_session_auth_hash
        from django.contrib.auth.password_validation import (
            validate_password,
            password_validators_help_texts,
        )

        user = request.user
        old = request.POST.get("oldpassword") or ""
        new1 = request.POST.get("password1") or ""
        new2 = request.POST.get("password2") or ""

        if not old or not new1 or not new2:
            messages.error(request, "Semua kolom kata sandi wajib diisi.")
            return
        if not user.check_password(old):
            messages.error(request, "Kata sandi saat ini salah.")
            return
        if new1 != new2:
            messages.error(request, "Konfirmasi kata sandi tidak cocok.")
            return
        if new1 == old:
            messages.error(request, "Kata sandi baru tidak boleh sama dengan yang lama.")
            return

        try:
            validate_password(new1, user=user)
        except ValidationError as exc:
            messages.error(request, " · ".join(exc.messages))
            return

        user.set_password(new1)
        user.save(update_fields=["password"])
        update_session_auth_hash(request, user)
        messages.success(request, "Kata sandi berhasil diganti.")

    def _update_photo(self, request):
        from avatar.forms import UploadAvatarForm
        from avatar.models import Avatar
        from avatar.signals import avatar_updated
        from avatar.utils import invalidate_cache

        user = request.user
        if "avatar" not in request.FILES:
            messages.error(request, "Tidak ada berkas foto yang diunggah.")
            return

        form = UploadAvatarForm(request.POST, request.FILES, user=user)
        if not form.is_valid():
            errors = " · ".join(
                str(err) for field_errors in form.errors.values() for err in field_errors
            )
            messages.error(request, errors or "Foto tidak dapat diunggah.")
            return

        avatar = Avatar(user=user, primary=True)
        image_file = request.FILES["avatar"]
        avatar.avatar.save(image_file.name, image_file)
        avatar.save()
        invalidate_cache(user)
        avatar_updated.send(sender=Avatar, user=user, avatar=avatar)
        messages.success(request, "Foto profil berhasil diperbarui.")

    def _remove_photo(self, request):
        from avatar.models import Avatar
        from avatar.signals import avatar_deleted
        from avatar.utils import invalidate_cache

        user = request.user
        avatars = Avatar.objects.filter(user=user)
        if not avatars.exists():
            messages.info(request, "Belum ada foto profil untuk dihapus.")
            return

        for a in avatars:
            avatar_deleted.send(sender=Avatar, user=user, avatar=a)
        avatars.delete()
        invalidate_cache(user)
        messages.success(request, "Foto profil berhasil dihapus.")


VERB_CATEGORY = {
    "login": "login",
    "logged in": "login",
    "logged out": "login",
    "uploaded": "create",
    "created": "create",
    "added": "create",
    "changed": "update",
    "updated": "update",
    "edited": "update",
    "published": "publish",
    "approved": "publish",
    "deleted": "delete",
    "removed": "delete",
    "archived": "delete",
    "harvested": "harvest",
    "synced": "harvest",
    "downloaded": "harvest",
    "configured": "config",
}

CATEGORY_GROUP = {
    "login": "login",
    "create": "data",
    "update": "data",
    "publish": "data",
    "delete": "data",
    "harvest": "harvest",
    "config": "config",
}


def _verb_meta(verb):
    """Map an actstream verb to a (dot class, status label, status tone)."""
    key = (verb or "").strip().lower()
    dot = VERB_CATEGORY.get(key, "update")
    if dot in ("create",):
        return dot, "201 Created", "ok"
    if dot in ("publish",):
        return dot, "Published", "ok"
    if dot in ("delete",):
        return dot, "Removed", "warn"
    if dot in ("harvest",):
        return dot, "Harvest", "ok"
    if dot in ("login",):
        return dot, "Login", "ok"
    if dot in ("config",):
        return dot, "Config", "info"
    return dot, "200 OK", "ok"


class AuditLogView(LoginRequiredMixin, DstAdminPageView):
    template_name = "dst-district/admin/audit_log.html"
    page_slug = "audit_log"
    superuser_only = True
    page_title = "Audit Log"
    breadcrumb = [
        ("Dashboard", "/dst-auth/dashboard/"),
        ("Administrasi", None),
        ("Audit Log", None),
    ]
    paginate_by = 25

    RANGE_DELTAS = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "all": None,
    }

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self._export_csv(request)
        return super().get(request, *args, **kwargs)

    def _filtered_actions(self, request):
        qs = Action.objects.select_related(
            "actor_content_type", "action_object_content_type", "target_content_type"
        ).order_by("-timestamp")

        range_key = request.GET.get("range", "7d")
        if range_key not in self.RANGE_DELTAS:
            range_key = "7d"
        delta = self.RANGE_DELTAS[range_key]
        if delta is not None:
            qs = qs.filter(timestamp__gte=timezone.now() - delta)

        category = (request.GET.get("category") or "all").lower()
        if category != "all":
            wanted_verbs = [
                v for v, cat in VERB_CATEGORY.items() if CATEGORY_GROUP.get(cat) == category
            ]
            if wanted_verbs:
                qs = qs.filter(verb__in=wanted_verbs)

        search = (request.GET.get("q") or "").strip()
        if search:
            qs = qs.filter(
                Q(verb__icontains=search)
                | Q(description__icontains=search)
                | Q(data__icontains=search)
            )
        return qs, range_key, category, search

    def _export_csv(self, request):
        import csv
        from io import StringIO
        from django.http import HttpResponse

        qs, range_key, category, search = self._filtered_actions(request)
        if category == "screening":
            return self._export_screening_csv(request, range_key, search)

        buf = StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            [
                "id",
                "timestamp",
                "verb",
                "actor",
                "actor_type",
                "target",
                "target_type",
                "ip",
                "description",
            ]
        )
        for a in qs.iterator():
            actor = a.actor
            actor_name = (
                actor.get_full_name() if hasattr(actor, "get_full_name") else ""
            ) or getattr(actor, "username", None) or str(actor or "")
            actor_type = (
                a.actor_content_type.model if a.actor_content_type else ""
            )
            target_obj = a.action_object or a.target
            target_label = (
                getattr(target_obj, "title", None)
                or getattr(target_obj, "name", None)
                or (a.data or {}).get("object_name")
                or ""
            )
            target_type = (
                a.action_object_content_type.model
                if a.action_object_content_type
                else (a.target_content_type.model if a.target_content_type else "")
            )
            ip = ""
            if isinstance(a.data, dict):
                ip = a.data.get("ip") or a.data.get("ip_address") or ""
            writer.writerow(
                [
                    a.id,
                    a.timestamp.isoformat() if a.timestamp else "",
                    a.verb or "",
                    actor_name,
                    actor_type,
                    target_label,
                    target_type,
                    ip,
                    a.description or "",
                ]
            )

        stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        suffix_bits = [range_key]
        if category and category != "all":
            suffix_bits.append(category)
        suffix = "-".join(suffix_bits)
        response = HttpResponse(
            buf.getvalue(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="dst-luwu-audit-{suffix}-{stamp}.csv"'
        )
        return response

    def _export_screening_csv(self, request, range_key, search):
        import csv
        from io import StringIO
        from django.http import HttpResponse
        from .models import ScreeningLog

        sqs = ScreeningLog.objects.select_related("user").order_by("-created")
        delta = self.RANGE_DELTAS.get(range_key)
        if delta is not None:
            sqs = sqs.filter(created__gte=timezone.now() - delta)
        if search:
            sqs = sqs.filter(
                Q(nomor_reg__icontains=search) | Q(user_label__icontains=search)
            )

        buf = StringIO()
        writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["id", "timestamp", "nomor_reg", "user", "is_public", "ip", "area_ha"])
        for log in sqs.iterator():
            writer.writerow(
                [
                    log.id,
                    log.created.isoformat() if log.created else "",
                    log.nomor_reg,
                    log.user_label,
                    "yes" if log.user_id is None else "no",
                    log.ip or "",
                    f"{log.area_ha:.2f}" if log.area_ha is not None else "",
                ]
            )

        stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="dst-luwu-screening-{range_key}-{stamp}.csv"'
        )
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs, range_key, category, search = self._filtered_actions(self.request)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        stats_qs = Action.objects.all()
        today_count = stats_qs.filter(timestamp__gte=today_start).count()
        week_count = stats_qs.filter(timestamp__gte=week_start).count()
        today_actors = (
            stats_qs.filter(timestamp__gte=today_start)
            .values("actor_object_id")
            .distinct()
            .count()
        )
        harvest_verbs = [v for v, c in VERB_CATEGORY.items() if c == "harvest"]
        harvest_week = stats_qs.filter(
            timestamp__gte=week_start, verb__in=harvest_verbs
        ).count()

        category_counts = {
            "all": stats_qs.count(),
            "login": stats_qs.filter(
                verb__in=[v for v, c in VERB_CATEGORY.items() if c == "login"]
            ).count(),
            "data": stats_qs.filter(
                verb__in=[
                    v for v, c in VERB_CATEGORY.items() if CATEGORY_GROUP.get(c) == "data"
                ]
            ).count(),
            "harvest": stats_qs.filter(verb__in=harvest_verbs).count(),
            "config": stats_qs.filter(
                verb__in=[v for v, c in VERB_CATEGORY.items() if c == "config"]
            ).count(),
        }
        from .models import ScreeningLog

        category_counts["screening"] = ScreeningLog.objects.count()

        page_number = self.request.GET.get("page") or 1
        if category == "screening":
            rows, page_obj, paginator = self._screening_rows(range_key, search, page_number)
        else:
            rows, page_obj, paginator = self._action_rows(qs, page_number)

        grouped = []
        for day, items in groupby(rows, key=lambda r: timezone.localtime(r["timestamp"]).date()):
            items = list(items)
            grouped.append({"date": day, "count": len(items), "rows": items})

        ctx["range"] = range_key
        ctx["category"] = category
        ctx["search"] = search
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["grouped_rows"] = grouped
        ctx["stats"] = {
            "today": today_count,
            "today_actors": today_actors,
            "week": week_count,
            "week_avg": int(round(week_count / 7)) if week_count else 0,
            "harvest_week": harvest_week,
            "retention_days": 365,
        }
        ctx["category_counts"] = category_counts
        return ctx

    def _action_rows(self, qs, page_number):
        paginator = Paginator(qs, self.paginate_by)
        page_obj = paginator.get_page(page_number)
        rows = []
        for action in page_obj.object_list:
            actor = action.actor
            actor_name = (
                actor.get_full_name() if hasattr(actor, "get_full_name") else ""
            ) or getattr(actor, "username", None) or str(actor or "Sistem")
            initials = "".join(p[0] for p in actor_name.split()[:2]).upper() or "?"
            if actor and getattr(actor, "is_superuser", False):
                role = "Super Admin"
            elif actor and getattr(actor, "is_staff", False):
                role = "Walidata"
            elif actor:
                role = "Pengguna"
            else:
                role = "Sistem"

            dot, status_label, status_tone = _verb_meta(action.verb)

            target_obj = action.action_object or action.target
            target_label = (
                getattr(target_obj, "title", None)
                or getattr(target_obj, "name", None)
                or (action.data or {}).get("object_name")
                or ""
            )

            ip = ""
            if isinstance(action.data, dict):
                ip = action.data.get("ip") or action.data.get("ip_address") or ""

            rows.append(
                {
                    "id": action.id,
                    "timestamp": action.timestamp,
                    "verb": action.verb,
                    "dot": dot,
                    "actor_name": actor_name,
                    "actor_initials": initials,
                    "actor_role": role,
                    "target_label": target_label,
                    "target_type": (
                        action.action_object_content_type.model
                        if action.action_object_content_type
                        else ""
                    ),
                    "ip": ip,
                    "status_label": status_label,
                    "status_tone": status_tone,
                    "description": action.description or "",
                }
            )
        return rows, page_obj, paginator

    def _screening_rows(self, range_key, search, page_number):
        """Baris log dari ScreeningLog (kategori 'Screening Tools analisis')."""
        from .models import ScreeningLog

        sqs = ScreeningLog.objects.select_related("user").order_by("-created")
        delta = self.RANGE_DELTAS.get(range_key)
        if delta is not None:
            sqs = sqs.filter(created__gte=timezone.now() - delta)
        if search:
            sqs = sqs.filter(
                Q(nomor_reg__icontains=search) | Q(user_label__icontains=search)
            )

        paginator = Paginator(sqs, self.paginate_by)
        page_obj = paginator.get_page(page_number)
        rows = []
        for log in page_obj.object_list:
            name = log.user_label or "Publik"
            initials = "".join(p[0] for p in name.split()[:2]).upper() or "P"
            rows.append(
                {
                    "id": log.id,
                    "timestamp": log.created,
                    "verb": "men-generate laporan",
                    "dot": "screening",
                    "actor_name": name,
                    "actor_initials": initials,
                    "actor_role": "Pengguna" if log.user else "Publik",
                    "target_label": log.nomor_reg,
                    "target_type": "Screening Tools analisis",
                    "ip": log.ip or "",
                    "status_label": "Generated",
                    "status_tone": "ok",
                    "description": "",
                }
            )
        return rows, page_obj, paginator
