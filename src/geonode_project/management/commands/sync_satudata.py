# -*- coding: utf-8 -*-
"""Harvest katalog dataset dari portal Satu Data Kabupaten (CKAN) via CLI.

Pembungkus tipis atas ``geonode_project.satudata.harvest_satudata``. Basis URL
diambil dari argumen ``--base-url`` atau, bila kosong, dari baris ``SatuDataSource``
yang tersimpan (di-set lewat halaman Panel Admin → Integrasi Satu Data).

Contoh::

    python manage.py sync_satudata --base-url https://satudata.luwukab.go.id
    python manage.py sync_satudata        # pakai URL tersimpan di SatuDataSource
"""
import time

from django.core.management.base import BaseCommand, CommandError

from geonode_project.models import SatuDataSource
from geonode_project.satudata import harvest_satudata


class Command(BaseCommand):
    help = "Harvest seluruh dataset dari portal Satu Data Kabupaten (CKAN)."

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default="", help="Basis URL portal CKAN.")
        parser.add_argument(
            "--organisasi", default=None, help="Saring berdasarkan organisasi (opsional)."
        )
        parser.add_argument(
            "--insecure",
            action="store_true",
            help="Abaikan verifikasi sertifikat SSL (portal cert tak terverifikasi).",
        )

    def handle(self, *args, **opts):
        base_url = (opts.get("base_url") or "").strip()
        source = None
        if not base_url:
            source = SatuDataSource.objects.first()
            if not source:
                raise CommandError(
                    "Tidak ada SatuDataSource tersimpan — beri --base-url."
                )
            base_url = source.base_url

        verify = not opts.get("insecure")
        if source is not None and not opts.get("insecure"):
            verify = source.verifikasi_ssl

        started = time.time()
        try:
            stats = harvest_satudata(
                base_url,
                organisasi=opts.get("organisasi"),
                source=source,
                verify=verify,
                logger=self.stdout.write,
            )
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Harvest gagal: {exc}")

        dur = time.time() - started
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSelesai dalam {dur:.1f}s — {stats['jumlah']} dataset "
                f"({stats['baru']} baru, {stats['update']} update) "
                f"dari total {stats.get('count') or '?'} di portal."
            )
        )
