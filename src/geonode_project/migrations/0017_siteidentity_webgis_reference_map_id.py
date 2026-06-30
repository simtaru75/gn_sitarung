from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0016_reorder_landing_sections"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteidentity",
            name="webgis_reference_map_id",
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name="Map referensi WebGIS",
                help_text=(
                    "ID Map GeoNode yang dipakai sebagai daftar layer default di WebGIS. "
                    "Kosongkan untuk menggunakan nilai WEBGIS_REFERENCE_MAP_ID dari settings.py."
                ),
            ),
        ),
    ]
