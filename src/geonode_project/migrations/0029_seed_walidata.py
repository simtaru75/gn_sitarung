from django.db import migrations

# (singkatan, kepanjangan) — daftar instansi walidata default untuk semua
# kabupaten. Urutan list = urutan tampil (kolom ``urutan`` diisi otomatis
# dari indeks). Alamat sengaja dikosongkan (diisi belakangan via Panel Admin).
WALIDATA = [
    ("BIG", "Badan Informasi Geospasial"),
    ("KEMENHUT", "Kementerian Kehutanan"),
    ("KEMENDAGRI", "Kementerian Dalam Negeri"),
    ("KEMKOMDIGI", "Kementerian Komunikasi dan Digital Republik Indonesia"),
    ("BAPPENAS", "Badan Perencanaan Pembangunan Nasional"),
    ("BPS", "Badan Pusat Statistik"),
    ("KEMENTAN", "Kementerian Pertanian"),
    ("DPUPR", "Dinas Pekerjaan Umum dan Tata Ruang"),
    ("Bapelitbangda", "Badan Perencanaan Penelitian dan Pengembangan Daerah"),
    ("BAPPEDA", "Badan Perencanaan Pembangunan Daerah"),
    ("DLH", "Dinas Lingkungan Hidup"),
    ("BPBD", "Badan Penanggulangan Bencana Daerah"),
    ("Disparbud", "Dinas Kepariwisataan dan Kebudayaan"),
    ("Disnakertrans", "Dinas Ketenagakerjaan dan Transmigrasi"),
    ("Dispertan", "Dinas Pertanian"),
    ("DPMD", "Dinas Pemberdayaan Masyarakat dan Desa"),
    ("Disdik", "Dinas Pendidikan"),
    ("Bapenda", "Badan Pendapatan Daerah"),
    ("Dispora", "Dinas Kepemudaan dan Olahraga"),
    ("Dishub", "Dinas Perhubungan"),
    ("Disketapangan", "Dinas Ketahanan Pangan"),
    ("DPPPA", "Dinas Pemberdayaan Perempuan dan Perlindungan Anak"),
    ("Bakesbangpol", "Badan Kesatuan Bangsa dan Politik"),
    ("DPPKB", "Dinas Pengendalian Penduduk dan Keluarga Berencana"),
    ("BKAD", "Badan Keuangan dan Aset Daerah"),
    ("DPMPTSP", "Dinas Penanaman Modal dan Pelayanan Terpadu Satu Pintu"),
    ("Dispusip", "Dinas Perpustakaan dan Kearsipan"),
    ("Dispertanah", "Dinas Pertanahan"),
    ("Dinsos", "Dinas Sosial"),
    ("Disperkim", "Dinas Perumahan dan Kawasan Permukiman"),
    ("Inspektorat", "Inspektorat Daerah"),
    ("Dinkes", "Dinas Kesehatan"),
    ("Setda", "Sekretariat Daerah"),
    ("Disdukcapil", "Dinas Kependudukan dan Pencatatan Sipil"),
    ("Diskominfo-SP", "Dinas Komunikasi Informatika Statistik dan Persandian"),
    ("BKPSDM", "Badan Kepegawaian dan Pengembangan Sumber Daya Manusia"),
    ("Diskan", "Dinas Perikanan"),
    ("Disdag", "Dinas Perdagangan"),
    ("Diskop UMKM dan Perind.", "Dinas Koperasi, Usaha Kecil dan Menengah dan Perindustrian"),
]


def seed_walidata(apps, schema_editor):
    Walidata = apps.get_model("geonode_project", "Walidata")
    for idx, (singkatan, kepanjangan) in enumerate(WALIDATA, start=1):
        Walidata.objects.get_or_create(
            nama=singkatan,
            defaults={"kepanjangan": kepanjangan, "alamat": "", "urutan": idx},
        )


def unseed_walidata(apps, schema_editor):
    Walidata = apps.get_model("geonode_project", "Walidata")
    Walidata.objects.filter(nama__in=[s for s, _ in WALIDATA]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("geonode_project", "0028_walidata"),
    ]

    operations = [
        migrations.RunPython(seed_walidata, unseed_walidata),
    ]
