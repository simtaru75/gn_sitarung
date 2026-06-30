from django.db import migrations

# Terjemahkan 20 Topic Category standar GeoNode (ISO 19115) ke bahasa Indonesia.
# Hanya menimpa `gn_description` (GeoNode description) dan `description`.
# identifier / is_choice / fa_class TIDAK diubah. Record yang tidak ditemukan
# dilewati (tidak membuat baru) — jadi aman bila instalasi punya subset berbeda.
#
# (identifier, gn_description, description)
TRANSLATIONS = [
    (
        "farming", "Pertanian",
        "Pemeliharaan hewan dan/atau budidaya tanaman. Contoh: pertanian, "
        "irigasi, akuakultur, perkebunan, peternakan, serta hama dan penyakit "
        "yang memengaruhi tanaman dan ternak.",
    ),
    (
        "biota", "Biota",
        "Flora dan/atau fauna di lingkungan alami. Contoh: satwa liar, vegetasi, "
        "ilmu hayati, ekologi, kawasan liar, biota laut, lahan basah, dan habitat.",
    ),
    (
        "boundaries", "Batas Wilayah",
        "Deskripsi legal atas lahan. Contoh: batas politik dan administratif.",
    ),
    (
        "climatologyMeteorologyAtmosphere", "Klimatologi, Meteorologi, dan Atmosfer",
        "Proses dan fenomena atmosfer. Contoh: tutupan awan, cuaca, iklim, kondisi "
        "atmosfer, perubahan iklim, dan curah hujan.",
    ),
    (
        "economy", "Ekonomi",
        "Aktivitas, kondisi, dan ketenagakerjaan ekonomi. Contoh: produksi, tenaga "
        "kerja, pendapatan, perdagangan, industri, pariwisata dan ekowisata, "
        "kehutanan, perikanan, perburuan, serta eksplorasi dan eksploitasi sumber "
        "daya seperti mineral, minyak, dan gas.",
    ),
    (
        "elevation", "Ketinggian",
        "Ketinggian di atas atau di bawah permukaan laut. Contoh: altitude, "
        "batimetri, model elevasi digital, kemiringan lereng, dan produk turunannya.",
    ),
    (
        "environment", "Lingkungan",
        "Sumber daya lingkungan, perlindungan, dan konservasi. Contoh: pencemaran "
        "lingkungan, penyimpanan dan pengolahan limbah, analisis dampak lingkungan, "
        "pemantauan risiko lingkungan, cagar alam, dan bentang alam.",
    ),
    (
        "geoscientificInformation", "Informasi Geosaintifik",
        "Informasi yang berkaitan dengan ilmu kebumian. Contoh: fitur dan proses "
        "geofisika, geologi, mineral, komposisi dan struktur batuan, risiko gempa "
        "bumi, aktivitas vulkanik, tanah longsor, gravitasi, tanah, hidrogeologi, "
        "dan erosi.",
    ),
    (
        "health", "Kesehatan",
        "Kesehatan, layanan kesehatan, ekologi manusia, dan keselamatan. Contoh: "
        "penyakit, faktor yang memengaruhi kesehatan, higiene, penyalahgunaan zat, "
        "kesehatan mental dan fisik, serta layanan kesehatan.",
    ),
    (
        "imageryBaseMapsEarthCover", "Citra, Peta Dasar, dan Tutupan Lahan",
        "Peta dasar. Contoh: tutupan lahan, peta topografi, citra, gambar tak "
        "terklasifikasi, dan anotasi.",
    ),
    (
        "intelligenceMilitary", "Intelijen dan Militer",
        "Pangkalan, struktur, dan aktivitas militer. Contoh: barak, lapangan "
        "latihan, transportasi militer, dan pengumpulan informasi.",
    ),
    (
        "inlandWaters", "Perairan Darat",
        "Fitur perairan darat, sistem drainase, dan karakteristiknya. Contoh: "
        "sungai dan gletser, danau asin, rencana pemanfaatan air, bendungan, arus, "
        "banjir, kualitas air, dan peta hidrografi.",
    ),
    (
        "location", "Lokasi",
        "Informasi dan layanan posisi. Contoh: alamat, jaringan geodetik, titik "
        "kontrol, zona dan layanan pos, serta nama tempat (toponimi).",
    ),
    (
        "oceans", "Lautan",
        "Fitur dan karakteristik perairan asin (selain perairan darat). Contoh: "
        "pasang surut, gelombang pasang, informasi pesisir, dan terumbu karang.",
    ),
    (
        "planningCadastre", "Perencanaan dan Kadaster",
        "Informasi untuk tindakan terkait pemanfaatan lahan di masa depan. Contoh: "
        "peta penggunaan lahan, peta zonasi, survei kadaster, dan kepemilikan lahan.",
    ),
    (
        "society", "Sosial dan Budaya",
        "Karakteristik masyarakat dan budaya. Contoh: permukiman, antropologi, "
        "arkeologi, pendidikan, kepercayaan tradisional, adat istiadat, data "
        "demografi, area rekreasi, analisis dampak sosial, kriminalitas dan "
        "keadilan, serta informasi sensus.",
    ),
    (
        "structure", "Struktur dan Bangunan",
        "Konstruksi buatan manusia. Contoh: bangunan, museum, tempat ibadah, "
        "pabrik, perumahan, monumen, pertokoan, dan menara.",
    ),
    (
        "transportation", "Transportasi",
        "Sarana dan prasarana untuk mengangkut orang dan/atau barang. Contoh: "
        "jalan, bandara/landasan, rute pelayaran, terowongan, peta nautika, lokasi "
        "kendaraan atau kapal, peta aeronautika, dan jalur kereta api.",
    ),
    (
        "utilitiesCommunication", "Utilitas dan Komunikasi",
        "Sistem energi, air, dan limbah serta infrastruktur dan layanan "
        "komunikasi. Contoh: pembangkit listrik tenaga air, panas bumi, surya, dan "
        "nuklir; pemurnian dan distribusi air; pengelolaan limbah; distribusi "
        "listrik dan gas; komunikasi data, telekomunikasi, radio, dan jaringan "
        "komunikasi.",
    ),
    (
        "disaster", "Bencana",
        "Informasi terkait kebencanaan. Contoh: lokasi bencana, zona evakuasi, "
        "fasilitas pencegahan bencana, dan kegiatan tanggap darurat bencana.",
    ),
]


def translate_forward(apps, schema_editor):
    from geonode.base.models import TopicCategory

    for identifier, gn_desc, desc in TRANSLATIONS:
        obj = TopicCategory.objects.filter(identifier=identifier).first()
        if obj is None:
            continue  # hanya update yang sudah ada; jangan buat record baru
        obj.gn_description = gn_desc
        obj.description = desc
        obj.save(update_fields=["gn_description", "description"])


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0022_seed_topik_kategori"),
    ]

    operations = [
        # Reverse no-op: terjemahan dibiarkan (tidak mengembalikan teks English).
        migrations.RunPython(translate_forward, migrations.RunPython.noop),
    ]
