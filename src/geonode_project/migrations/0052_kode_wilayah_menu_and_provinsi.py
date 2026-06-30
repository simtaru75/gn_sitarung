# -*- coding: utf-8 -*-
"""Seed provinsi ke RefKodeBps + menu sidebar 'Kode Wilayah' (grup Administrasi).

- Provinsi: 32 non-Papua kode BPS==Kemendagri; 6 provinsi Papua BERBEDA.
- Menu sidebar disisipkan setelah 'Walidata'; seluruh order diselaraskan ulang
  ke daftar kanonik SidebarMenu.MENUS terbaru.
"""
from django.db import migrations

# (kode_pum Kemendagri, kode_bps BPS, nama)
PROVINSI = [
    ("11", "11", "Aceh"), ("12", "12", "Sumatera Utara"),
    ("13", "13", "Sumatera Barat"), ("14", "14", "Riau"), ("15", "15", "Jambi"),
    ("16", "16", "Sumatera Selatan"), ("17", "17", "Bengkulu"),
    ("18", "18", "Lampung"), ("19", "19", "Kepulauan Bangka Belitung"),
    ("21", "21", "Kepulauan Riau"), ("31", "31", "DKI Jakarta"),
    ("32", "32", "Jawa Barat"), ("33", "33", "Jawa Tengah"),
    ("34", "34", "Daerah Istimewa Yogyakarta"), ("35", "35", "Jawa Timur"),
    ("36", "36", "Banten"), ("51", "51", "Bali"),
    ("52", "52", "Nusa Tenggara Barat"), ("53", "53", "Nusa Tenggara Timur"),
    ("61", "61", "Kalimantan Barat"), ("62", "62", "Kalimantan Tengah"),
    ("63", "63", "Kalimantan Selatan"), ("64", "64", "Kalimantan Timur"),
    ("65", "65", "Kalimantan Utara"), ("71", "71", "Sulawesi Utara"),
    ("72", "72", "Sulawesi Tengah"), ("73", "73", "Sulawesi Selatan"),
    ("74", "74", "Sulawesi Tenggara"), ("75", "75", "Gorontalo"),
    ("76", "76", "Sulawesi Barat"), ("81", "81", "Maluku"),
    ("82", "82", "Maluku Utara"),
    ("91", "94", "Papua"), ("92", "91", "Papua Barat"),
    ("93", "95", "Papua Selatan"), ("94", "96", "Papua Tengah"),
    ("95", "97", "Papua Pegunungan"), ("96", "92", "Papua Barat Daya"),
]

ORDERS = [
    ("dashboard", 1), ("capaian", 2), ("dokumen", 3), ("data_spasial", 4),
    ("metadata_schema", 5), ("akses_nasional", 6), ("endpoint_api", 7),
    ("integrasi_satudata", 8), ("pengguna", 9), ("audit_log", 10),
    ("frontend", 11), ("backend", 12), ("pengaturan", 13), ("data_capaian", 14),
    ("topik_kategori", 15), ("walidata", 16), ("kode_wilayah", 17), ("tema", 18),
    ("geonode", 19), ("geonode_admin", 20), ("geoserver", 21),
]


def seed(apps, schema_editor):
    RefKodeBps = apps.get_model("geonode_project", "RefKodeBps")
    for pum, bps, nama in PROVINSI:
        RefKodeBps.objects.update_or_create(
            level="provinsi", kode_pum=pum,
            defaults={"kode_bps": bps, "nama": nama, "file_logo": ""},
        )

    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.get_or_create(
        key="kode_wilayah",
        defaults={
            "title": "Kode Wilayah", "grup": "Administrasi", "order": 17,
            "is_visible": True, "visible_walidata": True,
        },
    )
    for key, order in ORDERS:
        SidebarMenu.objects.filter(key=key).update(order=order)


def unseed(apps, schema_editor):
    RefKodeBps = apps.get_model("geonode_project", "RefKodeBps")
    RefKodeBps.objects.filter(level="provinsi").delete()
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="kode_wilayah").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0051_refkodebps"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
