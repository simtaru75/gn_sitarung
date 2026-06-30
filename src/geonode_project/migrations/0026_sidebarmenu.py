from django.db import migrations, models

# (key, title, grup, order) — daftar menu sidebar Panel Admin.
MENUS = [
    ("dashboard",       "Dashboard",          "Ringkasan",          1),
    ("dokumen",         "Dokumen Kebijakan",  "Pengelolaan Data",   2),
    ("data_spasial",    "Data Spasial",       "Pengelolaan Data",   3),
    ("metadata_schema", "Metadata Schema",    "Pengelolaan Data",   4),
    ("akses_nasional",  "Akses Nasional",     "Distribusi & Akses", 5),
    ("endpoint_api",    "Endpoint API",       "Distribusi & Akses", 6),
    ("pengguna",        "Pengguna & Role",    "Administrasi",       7),
    ("audit_log",       "Audit Log",          "Administrasi",       8),
    ("frontend",        "Frontend",           "Administrasi",       9),
    ("backend",         "Backend",            "Administrasi",       10),
    ("pengaturan",      "Pengaturan Sistem",  "Administrasi",       11),
    ("topik_kategori",  "Topik Kategori",     "Administrasi",       12),
    ("tema",            "Tema CMS",           "Administrasi",       13),
    ("geonode",         "GeoNode",            "Tautan",            14),
    ("geonode_admin",   "GeoNode Admin",      "Tautan",            15),
    ("geoserver",       "Geoserver",          "Tautan",            16),
]


def seed_menus(apps, schema_editor):
    SidebarMenu = apps.get_model("geonode_project", "SidebarMenu")
    for key, title, grup, order in MENUS:
        SidebarMenu.objects.get_or_create(
            key=key,
            defaults={"title": title, "grup": grup, "order": order, "is_visible": True},
        )


def unseed_menus(apps, schema_editor):
    apps.get_model("geonode_project", "SidebarMenu").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0025_layanan_detail_kategori"),
    ]

    operations = [
        migrations.CreateModel(
            name="SidebarMenu",
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
                ("key", models.SlugField(max_length=50, unique=True, verbose_name="Kunci")),
                ("title", models.CharField(max_length=100, verbose_name="Nama menu")),
                ("grup", models.CharField(blank=True, max_length=50, verbose_name="Grup")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Urutan")),
                ("is_visible", models.BooleanField(default=True, verbose_name="Tampil")),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Menu Sidebar",
                "verbose_name_plural": "Menu Sidebar",
                "ordering": ["order", "id"],
            },
        ),
        migrations.RunPython(seed_menus, unseed_menus),
    ]
