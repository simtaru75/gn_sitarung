# -*- coding: utf-8 -*-
"""Seed foto komoditas FOLUR (berkas) saat install pertama.

Berkas dibundel di ``geonode_project/seed_data/komoditas/`` dan disalin ke
MEDIA_ROOT/komoditas/. Field ``gambar`` hanya diisi bila masih kosong, sehingga
TIDAK menimpa foto yang sudah diunggah/diatur admin. Idempotent.

Bergantung pada 0009 (yang membuat 4 record komoditas berbasis nama).
"""
import os
import shutil

from django.conf import settings
from django.db import migrations
from django.db.models import Q

# (nama, berkas)
KOMODITAS = [
    ("Kakao rakyat", "kakao.png"),
    ("Padi sawah", "padi.png"),
    ("Kopi", "kopi.png"),
    ("Kelapa Sawit", "sawit.png"),
]

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "seed_data", "komoditas")


def seed(apps, schema_editor):
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    media_dir = os.path.join(settings.MEDIA_ROOT, "komoditas")
    try:
        os.makedirs(media_dir, exist_ok=True)
    except OSError:
        pass

    for nama, fname in KOMODITAS:
        src = os.path.join(SEED_DIR, fname)
        dest_rel = f"komoditas/{fname}"
        dest_abs = os.path.join(settings.MEDIA_ROOT, dest_rel)
        if os.path.exists(src) and not os.path.exists(dest_abs):
            try:
                shutil.copyfile(src, dest_abs)
            except OSError:
                pass
        # Hanya isi gambar bila record ada DAN gambar masih kosong (jangan menimpa).
        Komoditas.objects.filter(nama=nama).filter(
            Q(gambar="") | Q(gambar__isnull=True)
        ).update(gambar=dest_rel)


def unseed(apps, schema_editor):
    # Tidak menghapus berkas/record; cukup kosongkan gambar yang menunjuk seed.
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    for nama, fname in KOMODITAS:
        Komoditas.objects.filter(nama=nama, gambar=f"komoditas/{fname}").update(gambar="")


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0011_seed_implementing_partners"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
