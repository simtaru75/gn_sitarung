# -*- coding: utf-8 -*-
"""Seed crosswalk nasional kecamatan & desa ke ``RefKodeBps`` (fresh install).

Sumber: ``seed_data/kode_bps_kecamatan.csv`` (±7.285) & ``kode_bps_desa.csv``
(±83.723), turunan dataset bridging BPS Wilkerstat + Kemendagri
(SalzBytes/wilayah_indonesia). Karena jumlahnya besar & statis, dimuat dengan
hapus-lalu-``bulk_create`` per jenjang (idempotent). Mirror perilaku management
command ``load_kode_bps`` agar deploy baru otomatis lengkap tanpa langkah manual.
"""
import csv
import os

from django.db import migrations

SEED = os.path.join(os.path.dirname(__file__), "..", "seed_data")
FILES = {
    "kecamatan": os.path.join(SEED, "kode_bps_kecamatan.csv"),
    "desa": os.path.join(SEED, "kode_bps_desa.csv"),
}


def _seed_level(RefKodeBps, level, path):
    if not os.path.exists(path):
        return
    seen, objs = set(), []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pum = (r.get("kode_pum") or "").strip()
            bps = (r.get("kode_bps") or "").strip()
            if not pum or not bps or pum in seen:  # dedupe keep-first
                continue
            seen.add(pum)
            objs.append(RefKodeBps(level=level, kode_pum=pum, kode_bps=bps,
                                   nama=(r.get("nama") or "").strip(), file_logo=""))
    RefKodeBps.objects.filter(level=level).delete()
    RefKodeBps.objects.bulk_create(objs, batch_size=2000)


def seed(apps, schema_editor):
    RefKodeBps = apps.get_model("geonode_project", "RefKodeBps")
    for level, path in FILES.items():
        _seed_level(RefKodeBps, level, path)


def unseed(apps, schema_editor):
    RefKodeBps = apps.get_model("geonode_project", "RefKodeBps")
    RefKodeBps.objects.filter(level__in=("kecamatan", "desa")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0052_kode_wilayah_menu_and_provinsi"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
