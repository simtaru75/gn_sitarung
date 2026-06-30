from django.db import migrations


def add_hero_carousel(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.get_or_create(
        key="hero_carousel",
        defaults={
            "title": "Hero Carousel (Beranda Alt. 2)",
            "anchor": "beranda-carousel",
            "order": 10,
            "is_visible": False,
        },
    )


def remove_hero_carousel(apps, schema_editor):
    apps.get_model("geonode_project", "LandingSection").objects.filter(
        key="hero_carousel"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0014_alter_siteidentity_theme"),
    ]

    operations = [
        migrations.RunPython(add_hero_carousel, remove_hero_carousel),
    ]
