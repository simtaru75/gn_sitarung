from django.db import migrations

# Seed/lengkapi Topic Category khas daerah (Badik Luwu) beserta deskripsinya.
# (identifier, gn_description, description, fa_class)
#
# Strategi pencocokan aman (hindari duplikat di tabel inti base_topiccategory):
#   1. cari record yang sudah ada lewat gn_description (nama tampil), lalu
#   2. lewat identifier; bila tak ada baru dibuat.
# Field yang sudah berisi tidak ditimpa (hanya yang kosong diisi) — sehingga
# idempotent dan menghormati konten yang sudah diedit admin.
CATEGORIES = [
    (
        "tata_kelola_pemerintahan",
        "Tata Kelola Pemerintahan",
        "Data tata kelola dan administrasi pemerintahan daerah — kelembagaan, "
        "perencanaan pembangunan, regulasi, keuangan, dan layanan publik "
        "Pemerintah Kabupaten Luwu.",
        "fa-university",
    ),
    (
        "educationCulture",
        "Pendidikan dan Kebudayaan",
        "Data sektor pendidikan dan kebudayaan — sebaran satuan pendidikan, "
        "tenaga pendidik, angka partisipasi sekolah, serta cagar dan warisan "
        "budaya daerah.",
        "fa-graduation-cap",
    ),
    (
        "pangan",
        "Pangan",
        "Data ketahanan dan produksi pangan — komoditas pertanian, lahan pangan "
        "pertanian berkelanjutan (LP2B), produktivitas, cadangan, dan distribusi "
        "pangan.",
        "fa-leaf",
    ),
    (
        "infrastruktur",
        "Infrastruktur",
        "Data infrastruktur dan utilitas wilayah — jaringan jalan dan jembatan, "
        "irigasi, energi, telekomunikasi, air bersih, serta sarana dan prasarana "
        "publik.",
        "fa-road",
    ),
    (
        "kabupaten",
        "Kabupaten",
        "Data agregat tingkat kabupaten — profil daerah, batas administrasi, dan "
        "indikator pembangunan Kabupaten Luwu secara menyeluruh.",
        "fa-map",
    ),
    (
        "kecamatan",
        "Kecamatan",
        "Data pada cakupan kewilayahan kecamatan — batas administrasi, profil "
        "wilayah, demografi, dan statistik per kecamatan di Kabupaten Luwu.",
        "fa-map-marker",
    ),
    (
        "pariwisata",
        "Pariwisata",
        "Data sektor pariwisata — destinasi dan daya tarik wisata, akomodasi, "
        "ekonomi kreatif, serta kunjungan wisatawan di Kabupaten Luwu.",
        "fa-suitcase",
    ),
]


def seed_categories(apps, schema_editor):
    # Pakai model nyata: base sudah ter-migrasi penuh sebelum migrasi ini
    # (rantai dependency geonode_project → documents/layers → base).
    from geonode.base.models import TopicCategory

    for identifier, gn_desc, desc, fa in CATEGORIES:
        obj = (
            TopicCategory.objects.filter(identifier=identifier).first()
            or TopicCategory.objects.filter(gn_description__iexact=gn_desc).first()
        )
        if obj is None:
            obj = TopicCategory(is_choice=True)
        # identifier + nama + DESKRIPSI di-set otoritatif untuk 7 kategori khas
        # ini — memastikan field Description terisi & selaras tiap identifier.
        # Aman: relasi resource memakai id, bukan string identifier.
        obj.identifier = identifier
        obj.gn_description = gn_desc
        obj.description = desc
        if not (obj.fa_class or "").strip() or obj.fa_class == "fa-times":
            obj.fa_class = fa
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0021_layanan_data"),
    ]

    operations = [
        # Reverse no-op: kategori mungkin sudah dipakai resource — tidak dihapus.
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
