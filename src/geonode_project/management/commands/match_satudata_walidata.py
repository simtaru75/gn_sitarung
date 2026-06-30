# -*- coding: utf-8 -*-
"""Cocokkan organisasi CKAN tiap ``SatuDataset`` ke daftar ``Walidata``.

Backfill/re-sync pencocokan untuk data yang sudah ter-harvest (pencocokan juga
berjalan otomatis tiap harvest). Idempoten & aman dijalankan berulang.

    python manage.py match_satudata_walidata
"""
from django.core.management.base import BaseCommand

from geonode_project.models import SatuDataset
from geonode_project.satudata import build_walidata_index, match_walidata


class Command(BaseCommand):
    help = "Cocokkan organisasi CKAN tiap dataset Satu Data ke daftar Walidata."

    def handle(self, *args, **opts):
        idx = build_walidata_index()
        cocok = kosong = diubah = 0
        for d in SatuDataset.objects.all().only("id", "organisasi", "walidata"):
            w = match_walidata(d.organisasi, idx)
            new_id = w.id if w else None
            if d.walidata_id != new_id:
                d.walidata = w
                d.save(update_fields=["walidata"])
                diubah += 1
            if w:
                cocok += 1
            else:
                kosong += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Selesai — {cocok} cocok, {kosong} belum terpetakan "
                f"({diubah} baris diperbarui)."
            )
        )
