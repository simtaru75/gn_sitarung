# -*- coding: utf-8 -*-
"""Seed kerangka KPI Capaian Program FOLUR (GEF Core Indicators).

8 indikator default sesuai mockup Sitroom. Indikator manual tanpa realisasi →
tampil badge "perlu data" sampai admin mengisi realisasi (FolurCapaian).
Indikator ``TK-MITRA`` bersumber ``auto`` (dihitung dari ImplementingPartner).
Idempoten (get_or_create per ``kode``).
"""
from django.db import migrations

# kode, nama, pilar, satuan, target, arah, sumber, auto_key, extra, deskripsi, urutan
KPIS = [
    ("CI1", "Kawasan lindung terkelola efektif", "kawasan_lindung", "ha", 12500,
     "naik", "manual", "", "",
     "Luas kawasan lindung/konservasi dalam bentang lahan yang dikelola lebih "
     "efektif. Memerlukan data kawasan hutan/lindung (KLHK).", 1),
    ("CI3", "Lahan terestorasi", "restorasi", "ha", 1200,
     "naik", "manual", "", "",
     "Luas lahan terdegradasi yang direstorasi (reforestasi/agroforestri). "
     "Memerlukan data plot restorasi proyek FOLUR.", 2),
    ("CI4", "Bentang lahan praktik produksi lestari", "praktik_lestari", "ha", 9000,
     "naik", "manual", "", "",
     "Luas lanskap produksi di bawah praktik pengelolaan lestari (kakao/padi "
     "berkelanjutan). Memerlukan data intervensi proyek.", 3),
    ("CI6", "Mitigasi emisi gas rumah kaca", "grk", "tCO₂e", 85000,
     "naik", "manual", "", "",
     "Estimasi emisi GRK yang dimitigasi/dihindari dari restorasi dan praktik "
     "lestari. Memerlukan integrasi data karbon (KLHK/BMKG).", 4),
    ("CI11", "Penerima manfaat (petani)", "penerima_manfaat", "orang", 6500,
     "naik", "manual", "", "40% perempuan",
     "Jumlah penerima manfaat langsung (petani), disagregasi gender. Memerlukan "
     "data kelompok tani / proyek FOLUR.", 5),
    ("VC-KEL", "Kelompok tani & koperasi tersertifikasi", "value_chain", "kelompok", 120,
     "naik", "manual", "", "",
     "Kelompok tani / koperasi dengan sertifikasi keberlanjutan (UTZ/RA). "
     "Memerlukan data proyek FOLUR / Pemda.", 6),
    ("VC-PRD", "Produksi kakao", "value_chain", "ton", None,
     "naik", "manual", "", "",
     "Produksi & produktivitas kakao per kecamatan. Memerlukan data "
     "Disbun/Distan & BPS (e-stat).", 7),
    ("TK-MITRA", "Mitra pelaksana aktif", "tata_kelola", "mitra", None,
     "naik", "auto", "mitra_aktif", "",
     "Jumlah mitra pelaksana (Implementing Partners) aktif. Dihitung otomatis "
     "dari data sistem.", 8),
]


def seed(apps, schema_editor):
    Ind = apps.get_model("geonode_project", "FolurIndikator")
    for (kode, nama, pilar, satuan, target, arah, sumber, auto_key, extra,
         deskripsi, urutan) in KPIS:
        Ind.objects.get_or_create(
            kode=kode,
            defaults={
                "nama": nama,
                "pilar": pilar,
                "satuan": satuan,
                "target": target,
                "arah": arah,
                "sumber": sumber,
                "auto_key": auto_key,
                "extra": extra,
                "deskripsi": deskripsi,
                "urutan": urutan,
                "aktif": True,
            },
        )


def unseed(apps, schema_editor):
    Ind = apps.get_model("geonode_project", "FolurIndikator")
    Ind.objects.filter(kode__in=[k[0] for k in KPIS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0035_folurindikator_folurcapaian"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
