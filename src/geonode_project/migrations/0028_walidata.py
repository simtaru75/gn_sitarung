from django.db import migrations, models


def seed_menu(apps, schema_editor):
    """Tambahkan menu sidebar 'Walidata' (di bawah 'Topik Kategori') dan
    geser urutan menu setelahnya agar konsisten dengan SidebarMenu.MENUS."""
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")

    # Geser urutan menu yang sekarang berada setelah Topik Kategori (>= 13).
    new_orders = {
        "tema": 14,
        "geonode": 15,
        "geonode_admin": 16,
        "geoserver": 17,
    }
    for key, order in new_orders.items():
        SidebarMenu.objects.filter(key=key).update(order=order)

    SidebarMenu.objects.get_or_create(
        key="walidata",
        defaults={
            "title": "Walidata",
            "grup": "Administrasi",
            "order": 13,
            "is_visible": True,
            "visible_walidata": True,
        },
    )


def unseed_menu(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    SidebarMenu.objects.filter(key="walidata").delete()
    # Kembalikan urutan menu setelahnya ke nilai semula.
    old_orders = {"tema": 13, "geonode": 14, "geonode_admin": 15, "geoserver": 16}
    for key, order in old_orders.items():
        SidebarMenu.objects.filter(key=key).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0027_sidebarmenu_visible_walidata"),
    ]

    operations = [
        migrations.CreateModel(
            name="Walidata",
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
                ("nama", models.CharField(max_length=120, verbose_name="Singkatan")),
                (
                    "kepanjangan",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Kepanjangan",
                    ),
                ),
                (
                    "alamat",
                    models.TextField(blank=True, default="", verbose_name="Alamat"),
                ),
                (
                    "urutan",
                    models.PositiveIntegerField(default=0, verbose_name="Urutan"),
                ),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Walidata",
                "verbose_name_plural": "Walidata",
                "ordering": ["urutan", "nama", "id"],
            },
        ),
        migrations.RunPython(seed_menu, unseed_menu),
    ]
