# -*- coding: utf-8 -*-
"""Seed menu sidebar 'Integrasi Satu Data' (grup Distribusi & Akses) + resync order.

'Integrasi Satu Data' = harvest katalog dataset dari portal Satu Data Kabupaten
(CKAN). Disisipkan setelah 'Endpoint API'; seluruh order menu diselaraskan ulang
ke daftar kanonik ``SidebarMenu.MENUS`` terbaru agar penyisipan tidak menggeser
tampilan Backend.
"""
from django.db import migrations

# (key, order) — sinkron dengan SidebarMenu.MENUS terbaru.
ORDERS = [
    ("dashboard", 1),
    ("capaian", 2),
    ("dokumen", 3),
    ("data_spasial", 4),
    ("metadata_schema", 5),
    ("akses_nasional", 6),
    ("endpoint_api", 7),
    ("integrasi_satudata", 8),
    ("pengguna", 9),
    ("audit_log", 10),
    ("frontend", 11),
    ("backend", 12),
    ("pengaturan", 13),
    ("data_capaian", 14),
    ("topik_kategori", 15),
    ("walidata", 16),
    ("tema", 17),
    ("geonode", 18),
    ("geonode_admin", 19),
    ("geoserver", 20),
]


def seed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.get_or_create(
        key="integrasi_satudata",
        defaults={
            "title": "Integrasi Satu Data",
            "grup": "Distribusi & Akses",
            "order": 8,
            "is_visible": True,
            "visible_walidata": True,
        },
    )
    for key, order in ORDERS:
        SidebarMenu.objects.filter(key=key).update(order=order)


def unseed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="integrasi_satudata").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0042_satudataset_satudatasource_satudataresource_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
