# -*- coding: utf-8 -*-
"""Task Celery proyek DST.

Pemuatan data wilayah dijalankan di latar (Celery) karena menarik geometri dari
BIG bisa makan beberapa menit — tidak boleh memblokir request web.
"""
from celery import shared_task
from django.core.management import call_command


@shared_task(name="geonode_project.load_wilayah_region", queue="default")
def load_wilayah_region(level, kode_prov, kode_kab=None):
    """Muat ulang schema ``wilayah`` HANYA untuk region cakupan terpilih.

    - ``level='provinsi'``  -> seluruh provinsi ``kode_prov``.
    - ``level='kabupaten'`` -> hanya kabupaten ``kode_kab`` (di ``kode_prov``).

    Selalu ``--replace`` agar schema ramping (hanya berisi region ini).
    """
    kwargs = {"level": "all", "provinsi": kode_prov, "replace": True}
    if level == "kabupaten" and kode_kab:
        kwargs["kabupaten"] = kode_kab
    call_command("sync_wilayah_big", **kwargs)
