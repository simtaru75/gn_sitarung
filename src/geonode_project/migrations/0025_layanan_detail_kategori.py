from django.db import migrations

# Arahkan tautan "Detail" tiap kartu Layanan Data ke Jelajah Dokumen ter-filter
# berdasarkan identifier Topic Category yang sesuai (mengganti tautan lama yang
# menuju situs Badik Luwu). Dicocokkan via judul.
NEW_TAUTAN = {
    "Data Tata Kelola Pemerintahan":  "/jelajah-dokumen/?kategori=tata_kelola_pemerintahan",
    "Data Lingkungan Hidup":          "/jelajah-dokumen/?kategori=environment",
    "Data Ekonomi":                   "/jelajah-dokumen/?kategori=economy",
    "Data Kesehatan":                 "/jelajah-dokumen/?kategori=health",
    "Data Infrastruktur":             "/jelajah-dokumen/?kategori=infrastruktur",
    "Data Pendidikan dan Kebudayaan": "/jelajah-dokumen/?kategori=educationCulture",
    "Data Pangan":                    "/jelajah-dokumen/?kategori=pangan",
    "Data Sosial":                    "/jelajah-dokumen/?kategori=society",
    "Data Kecamatan Kab Luwu":        "/jelajah-dokumen/?kategori=kecamatan",
    "Data Pariwisata":                "/jelajah-dokumen/?kategori=pariwisata",
}


def update_tautan(apps, schema_editor):
    LayananData = apps.get_model("geonode_project", "LayananData")
    for judul, tautan in NEW_TAUTAN.items():
        LayananData.objects.filter(judul=judul).update(tautan=tautan)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0024_remove_peraturan_daerah_kategori"),
    ]

    operations = [
        migrations.RunPython(update_tautan, migrations.RunPython.noop),
    ]
