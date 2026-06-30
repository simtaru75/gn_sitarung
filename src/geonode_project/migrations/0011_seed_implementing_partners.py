# -*- coding: utf-8 -*-
"""Seed 7 Implementing Partners (record DB + berkas logo) saat install pertama.

Berkas logo dibundel di ``geonode_project/seed_data/partners/`` (logo-1..7.png)
dan disalin ke MEDIA_ROOT/partners/ saat migrasi dijalankan. Idempotent
(get_or_create by nama; berkas hanya disalin bila belum ada).
"""
import os
import shutil

from django.conf import settings
from django.db import migrations

# (nama, tautan, berkas, urutan)
PARTNERS = [
    ("Kemenko Pangan", "https://www.kemenkopangan.go.id/", "logo-1.png", 1),
    ("BAPPENAS", "https://www.bappenas.go.id/", "logo-2.png", 2),
    ("Kementerian Pertanian", "https://www.pertanian.go.id/", "logo-3.png", 3),
    ("Kementerian Kehutanan", "https://www.kehutanan.go.id/", "logo-4.png", 4),
    ("GEF", "https://www.thegef.org/", "logo-5.png", 5),
    ("UNDP", "https://www.undp.org/", "logo-6.png", 6),
    ("FAO", "https://www.fao.org/home/en", "logo-7.png", 7),
]

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "seed_data", "partners")


def seed(apps, schema_editor):
    Partner = apps.get_model("geonode_project", "ImplementingPartner")
    media_partners = os.path.join(settings.MEDIA_ROOT, "partners")
    try:
        os.makedirs(media_partners, exist_ok=True)
    except OSError:
        pass

    for nama, tautan, fname, urutan in PARTNERS:
        src = os.path.join(SEED_DIR, fname)
        dest_rel = f"partners/{fname}"
        dest_abs = os.path.join(settings.MEDIA_ROOT, dest_rel)
        # Salin berkas logo ke media bila tersedia dan belum ada.
        if os.path.exists(src) and not os.path.exists(dest_abs):
            try:
                shutil.copyfile(src, dest_abs)
            except OSError:
                pass
        Partner.objects.get_or_create(
            nama=nama,
            defaults={
                "tautan": tautan,
                "urutan": urutan,
                "aktif": True,
                "logo": dest_rel,
            },
        )


def unseed(apps, schema_editor):
    Partner = apps.get_model("geonode_project", "ImplementingPartner")
    Partner.objects.filter(nama__in=[p[0] for p in PARTNERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0010_implementingpartner"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
