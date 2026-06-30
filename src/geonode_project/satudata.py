# -*- coding: utf-8 -*-
"""Harvest katalog dataset dari portal Satu Data Kabupaten berbasis CKAN.

Menarik seluruh *package* (dataset) dari endpoint CKAN Action API
``/api/3/action/package_search`` (paginasi via ``start``/``rows``) lalu
meng-upsert ke tabel lokal ``SatuDataset`` + ``SatuDataResource``. Idempoten:
dijalankan ulang memperbarui baris yang ada (dikunci pada ``(source, ckan_id)``)
dan menyegarkan daftar resource tiap dataset.

Dipakai oleh tombol "Harvest" di Panel Admin (``IntegrasiSatuDataView``) maupun
management command ``sync_satudata``. Pola koneksi/retry mengikuti
``management/commands/sync_idm.py``.
"""
import time

import re

import requests
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import SatuDataSource, SatuDataset, SatuDataResource, Walidata

PAGE_SIZE = 1000  # batas baris per panggilan package_search di sebagian besar CKAN.
USER_AGENT = "DST-FOLUR/sync_satudata"


def _norm_base(base_url):
    return (base_url or "").strip().rstrip("/")


def _norm_org(s):
    """Normalisasi nama organisasi/Walidata untuk pencocokan.

    Huruf kecil, rapikan spasi, dan buang akhiran wilayah ("Kabupaten Luwu",
    "Kota Belopa", "Kab. Luwu") agar judul organisasi CKAN dapat dicocokkan
    dengan ``kepanjangan``/singkatan Walidata yang tanpa akhiran wilayah.
    """
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\b(kabupaten|kota|kab\.?)\s+\w+\s*$", "", s)
    return s.strip(" -,.")


def build_walidata_index():
    """Peta {nama ternormalisasi: Walidata} dari ``kepanjangan`` & singkatan."""
    idx = {}
    for w in Walidata.objects.all():
        for key in (w.kepanjangan, w.nama):
            k = _norm_org(key)
            if k and k not in idx:
                idx[k] = w
    return idx


def match_walidata(org_title, index=None):
    """Cocokkan judul organisasi CKAN ke satu ``Walidata`` (atau None)."""
    if not org_title:
        return None
    idx = build_walidata_index() if index is None else index
    return idx.get(_norm_org(org_title))


def build_org_map(source):
    """Peta override pemetaan manual {org_title: Walidata|None} untuk ``source``.

    Adanya kunci = keputusan eksplisit admin (``None`` = sengaja tak dipetakan).
    Tak ada kunci = belum diputuskan → pakai pencocokan otomatis.
    """
    from .models import SatuDataOrgWalidata

    out = {}
    if source is None:
        return out
    for m in SatuDataOrgWalidata.objects.filter(source=source).select_related("walidata"):
        out[m.org_title] = m.walidata
    return out


def resolve_walidata(org_title, wali_index=None, org_map=None):
    """Tentukan Walidata sebuah organisasi: override manual dulu, lalu fuzzy."""
    if org_map is not None and org_title in org_map:
        return org_map[org_title]  # eksplisit (boleh None = sengaja tak dipetakan)
    return match_walidata(org_title, wali_index)


def _parse_dt(val):
    """ISO string CKAN -> datetime aware (atau None)."""
    if not val:
        return None
    dt = parse_datetime(str(val))
    if dt is None:
        return None
    if timezone.is_naive(dt):
        try:
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        except Exception:  # noqa: BLE001 — di luar rentang / ambiguous
            return dt
    return dt


def _to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _fetch(session, url, params, retries=4):
    """GET CKAN dengan retry + backoff; kembalikan dict JSON terverifikasi."""
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=120)
            r.raise_for_status()
            data = r.json()
            if not data.get("success", True):
                raise RuntimeError(data.get("error") or "CKAN success=false")
            return data
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Gagal mengambil data CKAN (start={params.get('start')}): {last}")


def _upsert_package(source, pkg, wali_index=None, org_map=None):
    """Upsert satu package CKAN -> SatuDataset (+ resources). Return True bila baru."""
    ckan_id = str(pkg.get("id") or pkg.get("name") or "").strip()
    if not ckan_id:
        return None
    org = pkg.get("organization") or {}
    org_title = org.get("title") or org.get("name") or ""
    tags = ", ".join(
        t.get("display_name") or t.get("name") or ""
        for t in (pkg.get("tags") or [])
    ).strip(", ")
    name = (pkg.get("name") or "").strip()
    base = _norm_base(source.base_url)
    resources = pkg.get("resources") or []

    defaults = {
        "name": name[:200],
        "title": (pkg.get("title") or name or ckan_id)[:400],
        "notes": pkg.get("notes") or "",
        "organisasi": org_title[:200],
        "walidata": resolve_walidata(org_title, wali_index, org_map),
        "lisensi": (pkg.get("license_title") or "")[:200],
        "tags": tags[:500],
        "jumlah_resource": pkg.get("num_resources") or len(resources),
        "metadata_modified": _parse_dt(pkg.get("metadata_modified")),
        "portal_url": (f"{base}/dataset/{name}" if name else base)[:400],
        "raw": pkg,
    }
    obj, created = SatuDataset.objects.update_or_create(
        source=source, ckan_id=ckan_id, defaults=defaults
    )

    # Upsert resource per ckan_id (JANGAN delete+recreate) agar tautan
    # ``document`` yang sudah didaftarkan tidak hilang saat re-harvest.
    seen_ids = []
    for idx, res in enumerate(resources):
        rid = str(res.get("id") or "").strip()
        rdefaults = {
            "nama": (res.get("name") or res.get("description") or "")[:400],
            "deskripsi": res.get("description") or "",
            "format": (res.get("format") or "")[:50],
            "url": (res.get("url") or "")[:600],
            "ukuran": _to_int(res.get("size")),
            "last_modified": _parse_dt(res.get("last_modified") or res.get("created")),
            "raw": res,
        }
        if rid:
            SatuDataResource.objects.update_or_create(
                dataset=obj, ckan_id=rid, defaults=rdefaults
            )
            seen_ids.append(rid)
        else:
            # Resource tanpa id CKAN — fallback by (dataset, url).
            SatuDataResource.objects.update_or_create(
                dataset=obj, ckan_id="", url=rdefaults["url"], defaults=rdefaults
            )

    # Prune resource yang sudah hilang dari portal (punya ckan_id, tak lagi ada).
    obj.resources.exclude(ckan_id="").exclude(ckan_id__in=seen_ids).delete()
    return created


def harvest_satudata(base_url, *, organisasi=None, source=None, verify=True, logger=None):
    """Harvest seluruh dataset dari portal CKAN ``base_url``.

    ``source`` (SatuDataSource) opsional — bila None, di-get_or_create dari
    ``base_url``. ``organisasi`` opsional menyaring berdasarkan organisasi (fq).
    ``verify`` — verifikasi sertifikat SSL (False untuk portal dengan rantai
    sertifikat tak terverifikasi). ``logger`` opsional: callable(str) untuk progres.
    Mengembalikan dict ringkasan ``{jumlah, baru, update, halaman, count}``.
    """
    base = _norm_base(base_url)
    if not base:
        raise ValueError("Basis URL CKAN kosong.")

    if source is None:
        source, _ = SatuDataSource.objects.get_or_create(
            base_url=base, defaults={"organisasi_filter": organisasi or ""}
        )
    org = organisasi if organisasi is not None else (source.organisasi_filter or "")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.verify = verify
    if not verify:
        # Portal memakai sertifikat tak terverifikasi — sembunyikan peringatan urllib3.
        try:
            from urllib3.exceptions import InsecureRequestWarning
            import urllib3

            urllib3.disable_warnings(InsecureRequestWarning)
        except Exception:  # noqa: BLE001
            pass
    url = f"{base}/api/3/action/package_search"

    start = 0
    baru = update = 0
    count = None
    wali_index = build_walidata_index()  # cocokkan organisasi -> Walidata, sekali saja.
    org_map = build_org_map(source)  # override pemetaan manual admin (prioritas).
    while True:
        params = {"rows": PAGE_SIZE, "start": start}
        if org:
            params["fq"] = f'organization:"{org}"'
        data = _fetch(session, url, params)
        result = data.get("result") or {}
        if count is None:
            count = result.get("count")
        results = result.get("results") or []
        if not results:
            break

        with transaction.atomic():
            for pkg in results:
                created = _upsert_package(source, pkg, wali_index, org_map)
                if created is None:
                    continue
                baru += int(created)
                update += int(not created)

        start += len(results)
        if logger:
            logger(f"  satudata: {start}/{count or '?'} (+{baru} baru, ~{update} update)")
        if len(results) < PAGE_SIZE or (count is not None and start >= count):
            break

    jumlah = baru + update
    source.last_harvested = timezone.now()
    source.last_status = "ok"
    source.last_pesan = f"{jumlah} dataset ({baru} baru, {update} update)"
    source.last_jumlah = jumlah
    source.save(update_fields=[
        "last_harvested", "last_status", "last_pesan", "last_jumlah", "updated"
    ])
    return {
        "jumlah": jumlah,
        "baru": baru,
        "update": update,
        "halaman": (start + PAGE_SIZE - 1) // PAGE_SIZE if start else 0,
        "count": count,
        "source": source,
    }
