# -*- coding: utf-8 -*-
"""Seed gambar Daftar Komoditas FOLUR — set gambar terbaru hasil kurasi admin.

Menggantikan gambar default lama (``komoditi-*.png`` dari 0060) dengan berkas
baru ``folur-*.svg`` yang dibundel di ``seed_data/komoditas/``, agar fresh
install langsung menampilkan gambar terbaru.

Idempotent & NON-DESTRUKTIF: gambar hanya diganti bila masih KOSONG atau masih
memakai seed default lama (``komoditi-*.png``). Bila admin sudah mengunggah
gambar kustom lain, nilainya TIDAK ditimpa. Sagu tetap ``komoditi-Sagu.png``
(tidak diubah).
"""
import os
import shutil

from django.conf import settings
from django.db import migrations
from django.db.models import Q

# (nama, berkas_seed_lama, berkas_seed_baru)
KOMODITAS = [
    ("Kakao rakyat", "komoditi-Cocoa.png", "folur-kakao.svg"),
    ("Padi sawah", "komoditi-Rice.png", "folur-padi.svg"),
    ("Kopi", "komoditi-Coffee.png", "folur-kopi.svg"),
    ("Kelapa Sawit", "komoditi-Palm-Oil.png", "folur-sawit.svg"),
]

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "seed_data", "komoditas")


def seed(apps, schema_editor):
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    media_dir = os.path.join(settings.MEDIA_ROOT, "komoditas")
    try:
        os.makedirs(media_dir, exist_ok=True)
    except OSError:
        pass

    for nama, old_fname, new_fname in KOMODITAS:
        src = os.path.join(SEED_DIR, new_fname)
        new_rel = f"komoditas/{new_fname}"
        old_rel = f"komoditas/{old_fname}"
        dest_abs = os.path.join(settings.MEDIA_ROOT, new_rel)
        if os.path.exists(src) and not os.path.exists(dest_abs):
            try:
                shutil.copyfile(src, dest_abs)
            except OSError:
                pass
        # Ganti HANYA bila kosong atau masih seed default lama (jangan timpa kustom).
        Komoditas.objects.filter(nama=nama).filter(
            Q(gambar="") | Q(gambar__isnull=True) | Q(gambar=old_rel)
        ).update(gambar=new_rel)


def unseed(apps, schema_editor):
    # Kembalikan ke seed lama hanya untuk record yang menunjuk berkas baru ini.
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    for nama, old_fname, new_fname in KOMODITAS:
        Komoditas.objects.filter(nama=nama, gambar=f"komoditas/{new_fname}").update(
            gambar=f"komoditas/{old_fname}"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0060_seed_komoditas_terbaru"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
