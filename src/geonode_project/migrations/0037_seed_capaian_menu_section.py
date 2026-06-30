# -*- coding: utf-8 -*-
"""Seed menu sidebar 'Capaian Program' & section landing 'Capaian Program FOLUR'.

Idempoten (get_or_create). Selaras dengan SidebarMenu.MENUS / LandingSection.SECTIONS.
"""
from django.db import migrations


def seed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    LandingSection = apps.get_model("geonode_project", "LandingSection")

    SidebarMenu.objects.get_or_create(
        key="capaian",
        defaults={
            "title": "Capaian Program",
            "grup": "Ringkasan",
            "order": 2,
            "is_visible": True,
            "visible_walidata": True,
        },
    )
    LandingSection.objects.get_or_create(
        key="capaian_folur",
        defaults={
            "title": "Capaian Program FOLUR",
            "anchor": "capaian-folur",
            "order": 14,
            "is_visible": True,
        },
    )


def unseed(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    SidebarMenu.objects.filter(key="capaian").delete()
    LandingSection.objects.filter(key="capaian_folur").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0036_seed_folur_kpi"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
