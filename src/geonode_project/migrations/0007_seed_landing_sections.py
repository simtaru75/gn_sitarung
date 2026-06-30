# -*- coding: utf-8 -*-
"""Seed daftar section Landing default saat instalasi pertama.

Idempotent (get_or_create) sehingga aman dijalankan ulang. Bila admin
menamb/menghapus section di masa depan, data tidak ditimpa.
"""
from django.db import migrations

# (key, title, anchor, order) — harus selaras dengan LandingSection.SECTIONS
DEFAULTS = [
    ("hero", "Hero / Beranda", "beranda", 1),
    ("statistik", "Statistik Ringkas", "statistik", 2),
    ("screening_tools", "Modul Screening Tools", "screening-tools", 3),
    ("komoditas", "Komoditas Fokus", "komoditas", 4),
    ("dokumen", "Dokumen Kebijakan", "dokumen", 5),
    ("katalog_data", "Katalog Data Spasial", "katalog-data", 6),
    ("eksplorasi_dataset", "Eksplorasi Dataset", "eksplorasi-dataset", 7),
    ("tentang_program", "Tentang Program", "tentang-program", 8),
]


def seed(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    for key, title, anchor, order in DEFAULTS:
        LandingSection.objects.get_or_create(
            key=key,
            defaults={
                "title": title,
                "anchor": anchor,
                "order": order,
                "is_visible": True,
            },
        )


def unseed(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.filter(key__in=[d[0] for d in DEFAULTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0006_landingsection"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
