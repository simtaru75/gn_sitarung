from django.db import migrations

NEW_ORDER = {
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


def reorder_forward(apps, schema_editor):
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    for key, order in NEW_ORDER.items():
        LandingSection.objects.filter(key=key).update(order=order)


def reorder_backward(apps, schema_editor):
    OLD_ORDER = {
        "hero":              1,
        "statistik":         2,
        "screening_tools":   3,
        "komoditas":         4,
        "dokumen":           5,
        "katalog_data":      6,
        "eksplorasi_dataset":7,
        "tentang_program":   8,
        "mitra":             9,
        "hero_carousel":     10,
    }
    LandingSection = apps.get_model("geonode_project", "LandingSection")
    for key, order in OLD_ORDER.items():
        LandingSection.objects.filter(key=key).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0015_add_hero_carousel_section"),
    ]

    operations = [
        migrations.RunPython(reorder_forward, reorder_backward),
    ]
