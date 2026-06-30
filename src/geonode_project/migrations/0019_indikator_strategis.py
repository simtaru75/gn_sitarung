from django.db import migrations, models


# Urutan baru setelah menyisipkan "Indikator Strategis" pada posisi ke-7.
NEW_ORDER = {
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

# Indikator awal (seed) — bersumber dari situs Badik Luwu (konteks Kab. Luwu).
# Ikon = berkas PNG permanen di static/dst-district/img/indikator/.
SEED = [
    ("Indeks Pembangunan Manusia",   "89%",         "Indeks Pembangunan Manusia Kab Luwu",      "indikator-strategis-1.png", 1),
    ("Pertumbuhan Ekonomi",          "78%",         "Data pertumbuhan ekonomi Kab Luwu 2023",   "indikator-strategis-2.png", 2),
    ("PDRB Per Kapita",              "90%",         "PDRB per kapita Kab Luwu 2023",            "indikator-strategis-3.png", 3),
    ("Tingkat Kemiskinan",           "12%",         "Indeks kemiskinan Kab Luwu",               "indikator-strategis-4.png", 4),
    ("Tingkat Pengangguran Terbuka", "11,5 persen", "Tingkat pengangguran terbuka Kab Luwu",    "indikator-strategis-5.png", 5),
    ("Gini Ratio",                   "0,364",       "Gini ratio tahun 2022",                    "indikator-strategis-6.png", 6),
    ("Inflasi",                      "5,13%",        "Data inflasi Kab Luwu tahun 2022",         "indikator-strategis-7.png", 7),
]


def seed_forward(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.get_or_create(
        key="indikator_strategis",
        defaults={
            "title": "Indikator Strategis",
            "anchor": "indikator-strategis",
            "order": 7,
            "is_visible": True,
        },
    )
    for key, order in NEW_ORDER.items():
        LandingSection.objects.filter(key=key).update(order=order)

    Indikator = apps.get_model("geonode_project", "IndikatorStrategis")
    if not Indikator.objects.exists():
        for judul, nilai, deskripsi, ikon, urutan in SEED:
            Indikator.objects.create(
                judul=judul, nilai=nilai, deskripsi=deskripsi,
                ikon=ikon, urutan=urutan, aktif=True,
            )


def seed_backward(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.filter(key="indikator_strategis").delete()
    old_order = {
        "hero":              1,
        "hero_carousel":     2,
        "statistik":         3,
        "pencarian":         4,
        "screening_tools":   5,
        "komoditas":         6,
        "dokumen":           7,
        "katalog_data":      8,
        "eksplorasi_dataset":9,
        "tentang_program":   10,
        "mitra":             11,
    }
    for key, order in old_order.items():
        LandingSection.objects.filter(key=key).update(order=order)
    # Baris IndikatorStrategis ikut terhapus saat tabel di-drop oleh DeleteModel.


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0018_add_pencarian_section"),
    ]

    operations = [
        migrations.CreateModel(
            name="IndikatorStrategis",
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
                ("judul", models.CharField(max_length=120, verbose_name="Judul indikator")),
                ("nilai", models.CharField(max_length=50, verbose_name="Nilai")),
                (
                    "deskripsi",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="Deskripsi"),
                ),
                (
                    "ikon",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Nama berkas di static/dst-district/img/indikator/ — mis. indikator-strategis-1.png",
                        max_length=100,
                        verbose_name="Ikon (nama berkas PNG)",
                    ),
                ),
                ("urutan", models.PositiveIntegerField(default=0, verbose_name="Urutan")),
                ("aktif", models.BooleanField(default=True, verbose_name="Aktif")),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Indikator Strategis",
                "verbose_name_plural": "Indikator Strategis",
                "ordering": ["urutan", "id"],
            },
        ),
        migrations.RunPython(seed_forward, seed_backward),
    ]
