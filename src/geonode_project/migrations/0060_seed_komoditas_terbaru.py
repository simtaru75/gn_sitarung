# -*- coding: utf-8 -*-
"""Seed Daftar Komoditas FOLUR — versi terbaru (permanen).

Menangkap kondisi terkini Pengaturan → Daftar Komoditas: 5 komoditas
(Kakao, Padi, Kopi, Kelapa Sawit, Sagu) beserta gambar ``komoditi-*.png``
(dibundel di ``seed_data/komoditas/``). Idempotent & NON-DESTRUKTIF:
``get_or_create`` per nama, dan gambar hanya diisi bila masih kosong —
TIDAK menimpa data/unggahan yang sudah diubah admin. Melengkapi 0009/0012
(yang hanya 4 komoditas + gambar lama).
"""
import os
import shutil

from django.conf import settings
from django.db import migrations
from django.db.models import Q

# (nama, deskripsi, urutan, aktif, berkas_gambar)
KOMODITAS = [
    ("Kakao rakyat",
     "Sektor kakao didominasi petani kecil. Data zona produksi, traceability, "
     "dan kelembagaan petani menjadi tulang punggung penilaian keberlanjutan "
     "rantai pasok di tingkat nasional.",
     1, True, "komoditi-Cocoa.png"),
    ("Padi sawah",
     "Lahan padi berinteraksi erat dengan irigasi teknis dan area sempadan "
     "sungai. Layer spasial sawah, jaringan irigasi, dan dokumen kebijakan "
     "pengairan tersaji bersama untuk perencanaan terpadu.",
     2, True, "komoditi-Rice.png"),
    ("Kopi",
     "Komoditas kopi rakyat pada lahan dataran tinggi; relevan dengan kebijakan "
     "tata guna lahan dan keberlanjutan agroforestri.",
     3, False, "komoditi-Coffee.png"),
    ("Kelapa Sawit",
     "Komoditas kelapa sawit dengan kebutuhan pemantauan kesesuaian lahan dan "
     "kepatuhan terhadap kebijakan lingkungan/bentang lahan.",
     4, False, "komoditi-Palm-Oil.png"),
    ("Sagu",
     "Komoditas sagu dengan kebutuhan pemetaan lahan rawa dan kepatuhan "
     "terhadap kebijakan ekosistem rawa.",
     5, False, "komoditi-Sagu.png"),
]

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "seed_data", "komoditas")


def seed(apps, schema_editor):
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    media_dir = os.path.join(settings.MEDIA_ROOT, "komoditas")
    try:
        os.makedirs(media_dir, exist_ok=True)
    except OSError:
        pass

    for nama, deskripsi, urutan, aktif, fname in KOMODITAS:
        src = os.path.join(SEED_DIR, fname)
        dest_rel = f"komoditas/{fname}"
        dest_abs = os.path.join(settings.MEDIA_ROOT, dest_rel)
        if os.path.exists(src) and not os.path.exists(dest_abs):
            try:
                shutil.copyfile(src, dest_abs)
            except OSError:
                pass
        # Buat record bila belum ada (mis. "Sagu" pada DB lama) — lengkap + gambar.
        Komoditas.objects.get_or_create(
            nama=nama,
            defaults={
                "deskripsi": deskripsi,
                "urutan": urutan,
                "aktif": aktif,
                "gambar": dest_rel,
            },
        )
        # Untuk record yang sudah ada: isi gambar HANYA bila masih kosong
        # (jangan timpa unggahan/edit admin).
        Komoditas.objects.filter(nama=nama).filter(
            Q(gambar="") | Q(gambar__isnull=True)
        ).update(gambar=dest_rel)


def unseed(apps, schema_editor):
    # Non-destruktif: jangan hapus record/berkas. Hanya kosongkan gambar yang
    # menunjuk berkas seed ini.
    Komoditas = apps.get_model("geonode_project", "KomoditasFokus")
    for nama, _d, _u, _a, fname in KOMODITAS:
        Komoditas.objects.filter(nama=nama, gambar=f"komoditas/{fname}").update(gambar="")


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0059_folurcapaianwilayah_komoditas"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
