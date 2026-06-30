from django.db import migrations, models


# Urutan baru setelah menyisipkan "Layanan Data" pada posisi ke-7
# (tepat di atas "Indikator Strategis").
NEW_ORDER = {
    "hero":              1,
    "hero_carousel":     2,
    "statistik":         3,
    "pencarian":         4,
    "screening_tools":   5,
    "komoditas":         6,
    "layanan_data":      7,
    "indikator_strategis": 8,
    "dokumen":           9,
    "katalog_data":      10,
    "eksplorasi_dataset":11,
    "tentang_program":   12,
    "mitra":             13,
}

_DETAIL = "/jelajah-dokumen/?kategori="

# (judul, ikon, tautan, urutan) — Detail menuju Jelajah Dokumen ter-filter
# berdasarkan identifier Topic Category yang sesuai.
SEED = [
    ("Data Tata Kelola Pemerintahan", "layanan-1.png",  _DETAIL + "tata_kelola_pemerintahan", 1),
    ("Data Lingkungan Hidup",         "layanan-2.png",  _DETAIL + "environment",              2),
    ("Data Ekonomi",                  "layanan-3.png",  _DETAIL + "economy",                  3),
    ("Data Kesehatan",                "layanan-4.png",  _DETAIL + "health",                   4),
    ("Data Infrastruktur",            "layanan-5.png",  _DETAIL + "infrastruktur",            5),
    ("Data Pendidikan dan Kebudayaan","layanan-6.png",  _DETAIL + "educationCulture",         6),
    ("Data Pangan",                   "layanan-7.png",  _DETAIL + "pangan",                   7),
    ("Data Sosial",                   "layanan-8.png",  _DETAIL + "society",                  8),
    ("Data Kecamatan Kab Luwu",       "layanan-9.png",  _DETAIL + "kecamatan",                9),
    ("Data Pariwisata",               "layanan-10.png", _DETAIL + "pariwisata",               10),
]


def seed_forward(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.get_or_create(
        key="layanan_data",
        defaults={
            "title": "Layanan Data",
            "anchor": "layanan-data",
            "order": 7,
            "is_visible": True,
        },
    )
    for key, order in NEW_ORDER.items():
        LandingSection.objects.filter(key=key).update(order=order)

    Layanan = apps.get_model("geonode_project", "LayananData")
    if not Layanan.objects.exists():
        for judul, ikon, tautan, urutan in SEED:
            Layanan.objects.create(
                judul=judul, ikon=ikon, tautan=tautan, urutan=urutan, aktif=True,
            )


def seed_backward(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.filter(key="layanan_data").delete()
    old_order = {
        "hero":              1,
        "hero_carousel":     2,
        "statistik":         3,
        "pencarian":         4,
        "screening_tools":   5,
        "komoditas":         6,
        "indikator_strategis": 7,
        "dokumen":           8,
        "katalog_data":      9,
        "eksplorasi_dataset":10,
        "tentang_program":   11,
        "mitra":             12,
    }
    for key, order in old_order.items():
        LandingSection.objects.filter(key=key).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0020_fix_indikator_ikon"),
    ]

    operations = [
        migrations.CreateModel(
            name="LayananData",
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
                ("judul", models.CharField(max_length=150, verbose_name="Judul layanan")),
                (
                    "ikon",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Nama berkas di static/dst-district/img/layanan/ (mis. layanan-1.png) atau URL lengkap.",
                        max_length=255,
                        verbose_name="Gambar (nama berkas / URL)",
                    ),
                ),
                (
                    "tautan",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="URL halaman detail (boleh internal atau eksternal).",
                        max_length=255,
                        verbose_name="Tautan Detail",
                    ),
                ),
                ("urutan", models.PositiveIntegerField(default=0, verbose_name="Urutan")),
                ("aktif", models.BooleanField(default=True, verbose_name="Aktif")),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Layanan Data",
                "verbose_name_plural": "Layanan Data",
                "ordering": ["urutan", "id"],
            },
        ),
        migrations.RunPython(seed_forward, seed_backward),
    ]
