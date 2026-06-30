# -*- coding: utf-8 -*-
"""Selaraskan ulang ``SidebarMenu.order`` ke urutan kanonik di ``MENUS``.

Baris menu lama (di-seed sebelum 'capaian'/Sitroom ada) masih memakai order
asli, sehingga Sitroom (order=2) bertabrakan dengan Dokumen (order=2) dan tampil
setelahnya di Backend. Migrasi ini menulis ulang order sesuai daftar kanonik:
Dashboard, Sitroom, Dokumen Kebijakan, Data Spasial, Metadata Schema, dst.
"""
from django.db import migrations

# (key, order) — harus sinkron dengan SidebarMenu.MENUS.
ORDERS = [
    ("dashboard", 1),
    ("capaian", 2),
    ("dokumen", 3),
    ("data_spasial", 4),
    ("metadata_schema", 5),
    ("akses_nasional", 6),
    ("endpoint_api", 7),
    ("pengguna", 8),
    ("audit_log", 9),
    ("frontend", 10),
    ("backend", 11),
    ("pengaturan", 12),
    ("topik_kategori", 13),
    ("walidata", 14),
    ("tema", 15),
    ("geonode", 16),
    ("geonode_admin", 17),
    ("geoserver", 18),
]


def resync(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    for key, order in ORDERS:
        SidebarMenu.objects.filter(key=key).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0038_rename_capaian_menu_sitroom"),
    ]

    operations = [
        migrations.RunPython(resync, migrations.RunPython.noop),
    ]
