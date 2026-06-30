# -*- coding: utf-8 -*-
"""Seed menu sidebar 'Data Capaian' (grup Pengelolaan Data) + resync order.

'Data Capaian' = pusat navigasi sumber data, entri realisasi, dan formulasi
untuk Sitroom & Capaian publik. Order seluruh menu diselaraskan ulang ke daftar
kanonik ``SidebarMenu.MENUS`` agar penyisipan tidak menggeser tampilan Backend.
"""
from django.db import migrations

# (key, order) — sinkron dengan SidebarMenu.MENUS terbaru.
ORDERS = [
    ("dashboard", 1),
    ("capaian", 2),
    ("dokumen", 3),
    ("data_spasial", 4),
    ("metadata_schema", 5),
    ("data_capaian", 6),
    ("akses_nasional", 7),
    ("endpoint_api", 8),
    ("pengguna", 9),
    ("audit_log", 10),
    ("frontend", 11),
    ("backend", 12),
    ("pengaturan", 13),
    ("topik_kategori", 14),
    ("walidata", 15),
    ("tema", 16),
    ("geonode", 17),
    ("geonode_admin", 18),
    ("geoserver", 19),
]


def seed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.get_or_create(
        key="data_capaian",
        defaults={
            "title": "Data Capaian",
            "grup": "Pengelolaan Data",
            "order": 6,
            "is_visible": True,
            "visible_walidata": True,
        },
    )
    for key, order in ORDERS:
        SidebarMenu.objects.filter(key=key).update(order=order)


def unseed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="data_capaian").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0039_resync_sidebar_order"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
