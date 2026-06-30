from django.db import migrations

# Urutan baru setelah menyisipkan section "Pencarian Data" pada posisi ke-4.
NEW_ORDER = {
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


def add_pencarian(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.get_or_create(
        key="pencarian",
        defaults={
            "title": "Pencarian Data",
            "anchor": "cari",
            "order": 4,
            "is_visible": True,
        },
    )
    # Geser urutan section yang berada setelah "pencarian".
    for key, order in NEW_ORDER.items():
        LandingSection.objects.filter(key=key).update(order=order)


def remove_pencarian(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    LandingSection.objects.filter(key="pencarian").delete()
    # Kembalikan urutan seperti migrasi 0016.
    old_order = {
        "hero":              1,
        "hero_carousel":     2,
        "statistik":         3,
        "screening_tools":   4,
        "komoditas":         5,
        "dokumen":           6,
        "katalog_data":      7,
        "eksplorasi_dataset":8,
        "tentang_program":   9,
        "mitra":             10,
    }
    for key, order in old_order.items():
        LandingSection.objects.filter(key=key).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0017_siteidentity_webgis_reference_map_id"),
    ]

    operations = [
        migrations.RunPython(add_pencarian, remove_pencarian),
    ]
