# Generated migration – rename Luwu → Simtaru in existing SiteIdentity rows.
from django.db import migrations


def rename_luwu_to_simtaru(apps, schema_editor):
    SiteIdentity = apps.get_model("geonode_project", "SiteIdentity")
    SiteIdentity.objects.filter(theme="luwu").update(theme="simtaru")


def reverse_simtaru_to_luwu(apps, schema_editor):
    SiteIdentity = apps.get_model("geonode_project", "SiteIdentity")
    SiteIdentity.objects.filter(theme="simtaru").update(theme="luwu")


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0062_siteidentity_font_option"),
    ]

    operations = [
        migrations.RunPython(rename_luwu_to_simtaru, reverse_simtaru_to_luwu),
    ]
