from django.db import migrations

# Hapus kategori auto-buatan "Peraturan Daerah" (identifier peraturan_daerah)
# yang dulu di-assign otomatis ke dokumen baru. Resource yang masih memakainya
# dikosongkan kategorinya dulu (jadi "— Tidak ditetapkan —"), baru record-nya
# dihapus — sehingga aman apa pun perilaku on_delete.


def remove_peraturan_daerah(apps, schema_editor):
    from geonode.base.models import TopicCategory, ResourceBase

    cat = (
        TopicCategory.objects.filter(identifier="peraturan_daerah").first()
        or TopicCategory.objects.filter(gn_description__iexact="Peraturan Daerah").first()
        or TopicCategory.objects.filter(description__iexact="Peraturan Daerah").first()
    )
    if cat is None:
        return
    ResourceBase.objects.filter(category=cat).update(category=None)
    cat.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0023_translate_standard_kategori"),
    ]

    operations = [
        # Reverse no-op: tidak membuat ulang kategori Peraturan Daerah.
        migrations.RunPython(remove_peraturan_daerah, migrations.RunPython.noop),
    ]
