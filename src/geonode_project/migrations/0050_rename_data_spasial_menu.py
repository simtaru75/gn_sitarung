# -*- coding: utf-8 -*-
"""Ubah istilah menu navigasi 'Data Spasial' → 'Dataset Spasial'."""
from django.db import migrations


def rename_forward(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="data_spasial").update(title="Dataset Spasial")


def rename_backward(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="data_spasial").update(title="Data Spasial")


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0049_datasetwalidata"),
    ]

    operations = [
        migrations.RunPython(rename_forward, rename_backward),
    ]
