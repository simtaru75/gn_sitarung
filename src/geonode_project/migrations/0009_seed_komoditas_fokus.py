# -*- coding: utf-8 -*-
"""Seed 4 fokus komoditas default saat instalasi pertama.

Default tampil: hanya Kakao & Padi (aktif=True); Kopi & Sawit disembunyikan
(aktif=False). Idempotent (get_or_create by nama) — tidak menimpa data yang
sudah ada / diubah admin.
"""
from django.db import migrations

# (nama, deskripsi, urutan, aktif)
DEFAULTS = [
    ("Kakao rakyat",
     "Sektor kakao didominasi petani kecil. Data zona produksi, traceability, "
     "dan kelembagaan petani menjadi tulang punggung penilaian keberlanjutan "
     "rantai pasok di tingkat nasional.",
     1, True),
    ("Padi sawah",
     "Lahan padi berinteraksi erat dengan irigasi teknis dan area sempadan "
     "sungai. Layer spasial sawah, jaringan irigasi, dan dokumen kebijakan "
     "pengairan tersaji bersama untuk perencanaan terpadu.",
     2, True),
    ("Kopi",
     "Komoditas kopi rakyat pada lahan dataran tinggi; relevan dengan kebijakan "
     "tata guna lahan dan keberlanjutan agroforestri.",
     3, False),
    ("Kelapa Sawit",
     "Komoditas kelapa sawit dengan kebutuhan pemantauan kesesuaian lahan dan "
     "kepatuhan terhadap kebijakan lingkungan/bentang lahan.",
     4, False),
    ("Sagu",
     "Komoditas sagu dengan kebutuhan pemetaan lahan rawa dan kepatuhan "
     "terhadap kebijakan ekosistem rawa.",
     5, False),
]


def seed(apps, schema_editor):
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    for nama, deskripsi, urutan, aktif in DEFAULTS:
        Komoditas.objects.get_or_create(
            nama=nama,
            defaults={"deskripsi": deskripsi, "urutan": urutan, "aktif": aktif},
        )


def unseed(apps, schema_editor):
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    Komoditas.objects.filter(nama__in=[d[0] for d in DEFAULTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0008_komoditasfokus"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
