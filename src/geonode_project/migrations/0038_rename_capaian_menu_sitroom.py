# -*- coding: utf-8 -*-
"""Ganti label menu sidebar 'Capaian Program' → 'Sitroom' (key tetap 'capaian')."""
from django.db import migrations


def rename(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="capaian").update(title="Sitroom")


def revert(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="capaian").update(title="Capaian Program")


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0037_seed_capaian_menu_section"),
    ]

    operations = [
        migrations.RunPython(rename, revert),
    ]
