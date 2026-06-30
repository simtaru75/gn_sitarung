from django.db import migrations

# Perbaikan: data awal sempat di-seed dengan nama berkas ikon yang belum ada.
# Berkas PNG permanen sebenarnya bernama indikator-strategis-1..7.png di
# static/dst-district/img/indikator/. Migrasi ini menyelaraskan field `ikon`
# pada record yang masih memakai nama lama (idempotent — aman bila sudah benar
# atau bila tabel baru saja di-seed dengan nama yang benar).
REMAP = {
    "ipm.png":                 "indikator-strategis-1.png",
    "pertumbuhan-ekonomi.png": "indikator-strategis-2.png",
    "pdrb-per-kapita.png":     "indikator-strategis-3.png",
    "kemiskinan.png":          "indikator-strategis-4.png",
    "pengangguran.png":        "indikator-strategis-5.png",
    "gini-ratio.png":          "indikator-strategis-6.png",
    "inflasi.png":             "indikator-strategis-7.png",
}


def fix_forward(apps, schema_editor):
    Indikator = apps.get_model("geonode_project", "IndikatorStrategis")
    for old, new in REMAP.items():
        Indikator.objects.filter(ikon=old).update(ikon=new)


def fix_backward(apps, schema_editor):
    Indikator = apps.get_model("geonode_project", "IndikatorStrategis")
    for old, new in REMAP.items():
        Indikator.objects.filter(ikon=new).update(ikon=old)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0019_indikator_strategis"),
    ]

    operations = [
        migrations.RunPython(fix_forward, fix_backward),
    ]
