# -*- coding: utf-8 -*-
"""Auto-muat schema ``wilayah`` untuk region cakupan terkonfigurasi (saat deploy).

Dipanggil dari entrypoint (``invoke restorewilayah``). Idempoten & tahan-gagal:

- Bila schema ``wilayah`` sudah berisi data -> dilewati.
- Region cakupan diambil dari env (``DST_WILAYAH_LEVEL`` / ``DST_WILAYAH_PROV`` /
  ``DST_WILAYAH_KAB``) untuk server baru yang DB-nya kosong, lalu fallback ke
  ``SiteIdentity`` (yang diisi lewat menu Pengaturan > Restore Data Wilayah).
- Bila cakupan terkonfigurasi -> jalankan ``sync_wilayah_big`` untuk region itu
  (``--replace`` → schema ramping, hanya region cakupan).
- Bila belum dikonfigurasi -> dilewati (admin mengaturnya manual via menu).

Mengganti pendekatan lama (restore dari dump nasional): sumber kini langsung BIG.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from geonode_project.models import (
    RefWilayahDesa,
    RefWilayahKabkota,
    SiteIdentity,
)


class Command(BaseCommand):
    help = "Auto-muat region cakupan ke schema 'wilayah' bila masih kosong."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Muat walau schema sudah berisi."
        )

    def handle(self, *args, **opts):
        if not opts["force"] and (
            RefWilayahDesa.objects.exists() or RefWilayahKabkota.objects.exists()
        ):
            self.stdout.write("Schema 'wilayah' sudah berisi data — auto-muat dilewati.")
            return

        # Prioritas env (server baru, DB kosong) lalu SiteIdentity.
        level = (os.environ.get("DST_WILAYAH_LEVEL") or "").strip()
        prov = (os.environ.get("DST_WILAYAH_PROV") or "").strip()
        kab = (os.environ.get("DST_WILAYAH_KAB") or "").strip()
        if not (level and prov):
            try:
                idn = SiteIdentity.load()
                level = idn.cakupan_level
                prov = idn.cakupan_kode_prov
                kab = idn.cakupan_kode_kab
            except Exception:
                pass

        if not (level in ("provinsi", "kabupaten") and prov):
            self.stdout.write(
                "Cakupan wilayah belum dikonfigurasi — auto-muat dilewati. "
                "Atur via Pengaturan Sistem > Restore Data Wilayah."
            )
            return

        kwargs = {"level": "all", "provinsi": prov, "replace": True}
        if level == "kabupaten" and kab:
            kwargs["kabupaten"] = kab
        self.stdout.write(
            f"Auto-muat wilayah region '{kab or prov}' (level={level}) dari BIG ..."
        )
        call_command("sync_wilayah_big", **kwargs)
