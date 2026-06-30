import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("geonode_project", "0029_seed_walidata"),
    ]

    operations = [
        migrations.CreateModel(
            name="WalidataMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="walidata_membership",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Pengguna",
                    ),
                ),
                (
                    "walidata",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="anggota",
                        to="geonode_project.walidata",
                        verbose_name="Walidata",
                    ),
                ),
            ],
            options={
                "verbose_name": "Keanggotaan Walidata",
                "verbose_name_plural": "Keanggotaan Walidata",
            },
        ),
    ]
