# -*- coding: utf-8 -*-
"""Unduh & daftarkan berkas resource Satu Data sebagai Dokumen GeoNode (bulk).

Memproses seluruh ``SatuDataResource`` yang belum punya ``document`` (dan
formatnya didukung), mengunduh berkasnya, lalu membuat entri ``Document`` GeoNode
**draft**. Idempoten: resource yang sudah terdaftar otomatis dilewati.

Contoh::

    python manage.py register_satudata_documents               # semua, semua dataset
    python manage.py register_satudata_documents --limit 10    # maks 10 dokumen baru
    python manage.py register_satudata_documents --dataset 5   # hanya dataset id 5
"""
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from geonode_project.models import SatuDataResource
from geonode_project.satudata_docs import register_resource_as_document


class Command(BaseCommand):
    help = "Unduh & daftarkan berkas Satu Data sebagai Dokumen GeoNode (draft)."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", type=int, default=None, help="Batasi ke 1 dataset (id).")
        parser.add_argument("--limit", type=int, default=0, help="Maks dokumen baru (0=tak terbatas).")
        parser.add_argument("--owner", default="", help="Username pemilik dokumen (default: superuser pertama).")

    def handle(self, *args, **opts):
        User = get_user_model()
        if opts["owner"]:
            owner = User.objects.filter(username=opts["owner"]).first()
            if not owner:
                raise CommandError(f"User '{opts['owner']}' tidak ditemukan.")
        else:
            owner = User.objects.filter(is_superuser=True).order_by("id").first()
            if not owner:
                raise CommandError("Tidak ada superuser untuk dijadikan pemilik dokumen.")

        qs = SatuDataResource.objects.filter(document__isnull=True).select_related(
            "dataset", "dataset__source"
        )
        if opts["dataset"]:
            qs = qs.filter(dataset_id=opts["dataset"])

        limit = opts["limit"] or 0
        dibuat = dilewati = gagal = 0
        started = time.time()
        for r in qs.iterator():
            if limit and dibuat >= limit:
                break
            src = r.dataset.source if r.dataset_id else None
            verify = src.verifikasi_ssl if src else True
            try:
                doc = register_resource_as_document(r, owner, verify=verify)
                if doc is None:
                    dilewati += 1
                else:
                    dibuat += 1
                    self.stdout.write(f"  + [{doc.pk}] {doc.title[:70]}")
            except Exception as exc:  # noqa: BLE001
                gagal += 1
                self.stderr.write(f"  ! {r.nama or r.url}: {exc}")

        dur = time.time() - started
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSelesai dalam {dur:.1f}s — {dibuat} dokumen dibuat, "
                f"{dilewati} dilewati, {gagal} gagal (pemilik: {owner.username})."
            )
        )
        if dibuat:
            self.stdout.write(
                self.style.WARNING(
                    "Dokumen dibuat sebagai DRAFT — tinjau & publish dari Panel Admin "
                    "→ Dokumen Kebijakan agar tampil di Jelajah Dokumen."
                )
            )
