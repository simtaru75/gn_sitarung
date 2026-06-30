# -*- coding: utf-8 -*-
"""Sinkronisasi Indeks Desa Membangun (IDM) per-desa, nasional.

Menarik IDM dari CKAN Kemendesa (satudata.kemendesa.go.id) via DataStore API
(JSON, paginasi) lalu meng-upsert ke tabel ``wilayah.idm`` (model ``IdmDesa``).
Idempoten: dijalankan ulang memperbarui/menambah baris, dikunci pada
(``kode_desa``, ``tahun``).

Contoh::

    python manage.py sync_idm                 # 2024 (default), nasional
    python manage.py sync_idm --replace       # kosongkan dulu lalu isi ulang

Sumber: Kementerian Desa PDT (c) — satudata.kemendesa.go.id
"""
import time

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from geonode_project.models import IdmDesa

CKAN_BASE = "https://satudata.kemendesa.go.id"
# Resource "Indeks Desa Membangun Tahun 2024" (hasil pemutakhiran), datastore aktif.
DEFAULT_RESOURCE = "e3f3d53c-69e3-417c-b7fc-b6dafb923b3d"
DEFAULT_TAHUN = 2024


def _to_float(val):
    if val in (None, "", "-"):
        return None
    try:
        return float(str(val).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = "Tarik Indeks Desa Membangun (IDM) per-desa nasional dari CKAN Kemendesa."

    def add_arguments(self, parser):
        parser.add_argument("--tahun", type=int, default=DEFAULT_TAHUN)
        parser.add_argument("--resource-id", default=DEFAULT_RESOURCE)
        parser.add_argument("--page-size", type=int, default=10000)
        parser.add_argument(
            "--replace",
            action="store_true",
            help="TRUNCATE wilayah.idm dulu sebelum mengisi.",
        )

    def handle(self, *args, **opts):
        tahun = opts["tahun"]
        rid = opts["resource_id"]
        limit = opts["page_size"]
        suffix = f"_{tahun}"

        if opts["replace"]:
            from django.db import connection

            with connection.cursor() as cur:
                cur.execute("TRUNCATE wilayah.idm RESTART IDENTITY;")
            self.stdout.write("Tabel wilayah.idm dikosongkan (--replace).")

        session = requests.Session()
        session.headers["User-Agent"] = "DST-FOLUR/sync_idm"
        url = f"{CKAN_BASE}/api/3/action/datastore_search"

        offset = 0
        inserted = updated = skipped = 0
        total = None
        started = time.time()
        while True:
            data = self._fetch(session, url, {"resource_id": rid, "limit": limit, "offset": offset})
            result = data.get("result") or {}
            if total is None:
                total = result.get("total")
            recs = result.get("records") or []
            if not recs:
                break

            with transaction.atomic():
                for rec in recs:
                    kode = str(rec.get("KODE_DESA") or "").strip()
                    if not kode:
                        skipped += 1
                        continue
                    defaults = {
                        "kode_prov": str(rec.get("KODE_PROV") or "").strip(),
                        "kode_kab": str(rec.get("KODE_KAB") or "").strip(),
                        "kode_kec": str(rec.get("KODE_KEC") or "").strip(),
                        "nama_desa": (rec.get("NAMA_DESA") or "").strip(),
                        "nama_kec": (rec.get("NAMA_KECAMATAN") or "").strip(),
                        "nama_kab": (rec.get("NAMA_KABUPATEN") or "").strip(),
                        "nama_prov": (rec.get("NAMA_PROVINSI") or "").strip(),
                        "iks": _to_float(rec.get(f"IKS{suffix}")),
                        "ike": _to_float(rec.get(f"IKE{suffix}")),
                        "ikl": _to_float(rec.get(f"IKL{suffix}")),
                        "skor_idm": _to_float(rec.get(f"NILAI_IDM{suffix}")),
                        "status": (rec.get(f"STATUS_IDM{suffix}") or "").strip(),
                    }
                    _, created = IdmDesa.objects.update_or_create(
                        kode_desa=kode, tahun=tahun, defaults=defaults
                    )
                    inserted += int(created)
                    updated += int(not created)

            offset += len(recs)
            self.stdout.write(
                f"  idm: {offset}/{total or '?'} (+{inserted} baru, ~{updated} update, {skipped} skip)"
            )
            if len(recs) < limit:
                break

        if inserted + updated == 0:
            raise CommandError("Tidak ada data IDM terbaca — cek resource-id / tahun.")

        dur = time.time() - started
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSelesai dalam {dur:.1f}s — {inserted} baru, {updated} update, "
                f"{skipped} skip (tahun {tahun})."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Sumber: Kementerian Desa PDT (c) - satudata.kemendesa.go.id"
            )
        )

    def _fetch(self, session, url, params, retries=4):
        last = None
        for attempt in range(retries):
            try:
                r = session.get(url, params=params, timeout=120)
                r.raise_for_status()
                data = r.json()
                if not data.get("success", True):
                    raise RuntimeError(data.get("error"))
                return data
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(2 ** attempt)
        raise CommandError(f"Gagal mengambil IDM (offset={params.get('offset')}): {last}")
