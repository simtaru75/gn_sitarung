# -*- coding: utf-8 -*-
"""Pindahkan menu 'Data Capaian' ke grup Administrasi + resync order kanonik."""
from django.db import migrations

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
    ("data_capaian", 13),
    ("topik_kategori", 14),
    ("walidata", 15),
    ("tema", 16),
    ("geonode", 17),
    ("geonode_admin", 18),
    ("geoserver", 19),
]


def fwd(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="data_capaian").update(grup="Administrasi")
    for key, order in ORDERS:
        SidebarMenu.objects.filter(key=key).update(order=order)


def rev(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="data_capaian").update(grup="Pengelolaan Data", order=6)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0040_seed_data_capaian_menu"),
    ]

    operations = [
        migrations.RunPython(fwd, rev),
    ]
