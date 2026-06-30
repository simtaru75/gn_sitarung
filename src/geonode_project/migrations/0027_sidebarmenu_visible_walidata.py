from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0026_sidebarmenu"),
    ]

    operations = [
        migrations.AddField(
            model_name="sidebarmenu",
            name="visible_walidata",
            field=models.BooleanField(default=True, verbose_name="Tampil (Walidata)"),
        ),
        migrations.AlterField(
            model_name="sidebarmenu",
            name="is_visible",
            field=models.BooleanField(default=True, verbose_name="Tampil (Super Admin)"),
        ),
    ]
