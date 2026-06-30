# -*- coding: utf-8 -*-
"""Seed/enforce Topic Category (Topik Kategori) dalam bahasa Indonesia.

Dijalankan dari ``entrypoint.sh`` TEPAT setelah ``invoke fixtures`` (yang memuat
``initial_data.json`` berisi kategori standar GeoNode dalam bahasa Inggris).
Perintah ini menimpa balik ke bahasa Indonesia sesuai kurasi admin
(``kategori.csv``): nama tampil, deskripsi, ikon FontAwesome, dan status
``is_choice`` (apakah dipakai sebagai pilihan).

Karena dipanggil di dalam blok init yang di-gate ``geonode_init.lock``, perintah
ini hanya berjalan saat fresh install / FORCE_REINIT — sehingga TIDAK menimpa
editan admin pada restart biasa.

Idempoten: cocokkan per ``identifier``; buat bila belum ada, perbarui bila ada.
Deskripsi lengkap diambil dari migrasi 0022/0023 (sumber kebenaran sebelumnya).
"""
from django.core.management.base import BaseCommand

# (identifier, gn_description, fa_class, is_choice, description)
KATEGORI = [
    ("economy", "Ekonomi", "fa-shopping-cart", True,
     "Aktivitas, kondisi, dan ketenagakerjaan ekonomi. Contoh: produksi, tenaga "
     "kerja, pendapatan, perdagangan, industri, pariwisata dan ekowisata, "
     "kehutanan, perikanan, perburuan, serta eksplorasi dan eksploitasi sumber "
     "daya seperti mineral, minyak, dan gas."),
    ("educationCulture", "Pendidikan dan Kebudayaan", "fa-user-graduate", True,
     "Data sektor pendidikan dan kebudayaan — sebaran satuan pendidikan, tenaga "
     "pendidik, angka partisipasi sekolah, serta cagar dan warisan budaya daerah."),
    ("environment", "Lingkungan", "fa-tree", True,
     "Sumber daya lingkungan, perlindungan, dan konservasi. Contoh: pencemaran "
     "lingkungan, penyimpanan dan pengolahan limbah, analisis dampak lingkungan, "
     "pemantauan risiko lingkungan, cagar alam, dan bentang alam."),
    ("health", "Kesehatan", "fa-stethoscope", True,
     "Kesehatan, layanan kesehatan, ekologi manusia, dan keselamatan. Contoh: "
     "penyakit, faktor yang memengaruhi kesehatan, higiene, penyalahgunaan zat, "
     "kesehatan mental dan fisik, serta layanan kesehatan."),
    ("infrastruktur", "Infrastruktur", "fa-road-bridge", True,
     "Data infrastruktur dan utilitas wilayah — jaringan jalan dan jembatan, "
     "irigasi, energi, telekomunikasi, air bersih, serta sarana dan prasarana "
     "publik."),
    ("kabupaten", "Kabupaten", "fa-building-columns", True,
     "Data agregat tingkat kabupaten — profil daerah, batas administrasi, dan "
     "indikator pembangunan Kabupaten Luwu secara menyeluruh."),
    ("kecamatan", "Kecamatan", "fa-building-columns", True,
     "Data pada cakupan kewilayahan kecamatan — batas administrasi, profil "
     "wilayah, demografi, dan statistik per kecamatan di Kabupaten Luwu."),
    ("pangan", "Pangan", "fa-bowl-rice", True,
     "Data ketahanan dan produksi pangan — komoditas pertanian, lahan pangan "
     "pertanian berkelanjutan (LP2B), produktivitas, cadangan, dan distribusi "
     "pangan."),
    ("pariwisata", "Pariwisata", "fa-person-walking-luggage", True,
     "Data sektor pariwisata — destinasi dan daya tarik wisata, akomodasi, "
     "ekonomi kreatif, serta kunjungan wisatawan di Kabupaten Luwu."),
    ("society", "Sosial dan Budaya", "fa-comments", True,
     "Karakteristik masyarakat dan budaya. Contoh: permukiman, antropologi, "
     "arkeologi, pendidikan, kepercayaan tradisional, adat istiadat, data "
     "demografi, area rekreasi, analisis dampak sosial, kriminalitas dan "
     "keadilan, serta informasi sensus."),
    ("tata_kelola_pemerintahan", "Tata Kelola Pemerintahan", "fa-building-columns", True,
     "Data tata kelola dan administrasi pemerintahan daerah — kelembagaan, "
     "perencanaan pembangunan, regulasi, keuangan, dan layanan publik Pemerintah "
     "Kabupaten Luwu."),
    ("biota", "Biota", "fa-leaf", False,
     "Flora dan/atau fauna di lingkungan alami. Contoh: satwa liar, vegetasi, "
     "ilmu hayati, ekologi, kawasan liar, biota laut, lahan basah, dan habitat."),
    ("boundaries", "Batas Wilayah", "fa-ellipsis-h", False,
     "Deskripsi legal atas lahan. Contoh: batas politik dan administratif."),
    ("climatologyMeteorologyAtmosphere", "Klimatologi, Meteorologi, dan Atmosfer", "fa-cloud", False,
     "Proses dan fenomena atmosfer. Contoh: tutupan awan, cuaca, iklim, kondisi "
     "atmosfer, perubahan iklim, dan curah hujan."),
    ("elevation", "Ketinggian", "fa-flag", False,
     "Ketinggian di atas atau di bawah permukaan laut. Contoh: altitude, "
     "batimetri, model elevasi digital, kemiringan lereng, dan produk turunannya."),
    ("farming", "Pertanian", "fa-lemon-o", False,
     "Pemeliharaan hewan dan/atau budidaya tanaman. Contoh: pertanian, irigasi, "
     "akuakultur, perkebunan, peternakan, serta hama dan penyakit yang "
     "memengaruhi tanaman dan ternak."),
    ("geoscientificInformation", "Informasi Geosaintifik", "fa-bullseye", False,
     "Informasi yang berkaitan dengan ilmu kebumian. Contoh: fitur dan proses "
     "geofisika, geologi, mineral, komposisi dan struktur batuan, risiko gempa "
     "bumi, aktivitas vulkanik, tanah longsor, gravitasi, tanah, hidrogeologi, "
     "dan erosi."),
    ("imageryBaseMapsEarthCover", "Citra, Peta Dasar, dan Tutupan Lahan", "fa-globe", False,
     "Peta dasar. Contoh: tutupan lahan, peta topografi, citra, gambar tak "
     "terklasifikasi, dan anotasi."),
    ("inlandWaters", "Perairan Darat", "fa-tint", False,
     "Fitur perairan darat, sistem drainase, dan karakteristiknya. Contoh: "
     "sungai dan gletser, danau asin, rencana pemanfaatan air, bendungan, arus, "
     "banjir, kualitas air, dan peta hidrografi."),
    ("intelligenceMilitary", "Intelijen dan Militer", "fa-fighter-jet", False,
     "Pangkalan, struktur, dan aktivitas militer. Contoh: barak, lapangan "
     "latihan, transportasi militer, dan pengumpulan informasi."),
    ("location", "Lokasi", "fa-map-marker", False,
     "Informasi dan layanan posisi. Contoh: alamat, jaringan geodetik, titik "
     "kontrol, zona dan layanan pos, serta nama tempat (toponimi)."),
    ("oceans", "Lautan", "fa-anchor", False,
     "Fitur dan karakteristik perairan asin (selain perairan darat). Contoh: "
     "pasang surut, gelombang pasang, informasi pesisir, dan terumbu karang."),
    ("planningCadastre", "Perencanaan dan Kadaster", "fa-home", False,
     "Informasi untuk tindakan terkait pemanfaatan lahan di masa depan. Contoh: "
     "peta penggunaan lahan, peta zonasi, survei kadaster, dan kepemilikan lahan."),
    ("population", "Kependudukan/Populasi", "fa-male", False,
     "Permukiman, antropologi, arkeologi, pendidikan, kepercayaan tradisional, "
     "adat istiadat, kesehatan dan keselamatan, serta data demografi dan sensus "
     "kependudukan."),
    ("structure", "Struktur dan Bangunan", "fa-building", False,
     "Konstruksi buatan manusia. Contoh: bangunan, museum, tempat ibadah, "
     "pabrik, perumahan, monumen, pertokoan, dan menara."),
    ("transportation", "Transportasi", "fa-truck", False,
     "Sarana dan prasarana untuk mengangkut orang dan/atau barang. Contoh: "
     "jalan, bandara/landasan, rute pelayaran, terowongan, peta nautika, lokasi "
     "kendaraan atau kapal, peta aeronautika, dan jalur kereta api."),
    ("utilitiesCommunication", "Utilitas dan Komunikasi", "fa-phone", False,
     "Sistem energi, air, dan limbah serta infrastruktur dan layanan komunikasi. "
     "Contoh: pembangkit listrik tenaga air, panas bumi, surya, dan nuklir; "
     "pemurnian dan distribusi air; pengelolaan limbah; distribusi listrik dan "
     "gas; komunikasi data, telekomunikasi, radio, dan jaringan komunikasi."),
]


class Command(BaseCommand):
    help = "Seed/enforce Topik Kategori (TopicCategory) dalam bahasa Indonesia."

    def handle(self, *args, **opts):
        from geonode.base.models import TopicCategory

        created = 0
        updated = 0
        for identifier, gn_desc, fa, is_choice, desc in KATEGORI:
            obj = TopicCategory.objects.filter(identifier=identifier).first()
            if obj is None:
                obj = TopicCategory(identifier=identifier)
                created += 1
            else:
                updated += 1
            obj.gn_description = gn_desc
            obj.description = desc
            obj.fa_class = fa
            obj.is_choice = is_choice
            obj.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Topik Kategori: {created} dibuat, {updated} diperbarui "
                f"(total {len(KATEGORI)} kategori bahasa Indonesia)."
            )
        )
