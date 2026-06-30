# -*- coding: utf-8 -*-
"""Model identitas situs tambahan yang dikelola dari halaman Pengaturan Sistem.

Menyimpan data branding yang tidak ditampung oleh Django ``Site`` (nama & domain)
maupun ``GeoNodeThemeCustomization`` (logo). Saat ini: Nama Kabupaten.
"""
from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gis_models


class SiteIdentity(models.Model):
    """Singleton (selalu pk=1) — satu baris identitas untuk seluruh situs."""

    TIMEZONE_CHOICES = [
        ("WIB", "WIB — Waktu Indonesia Barat (UTC+7)"),
        ("WITA", "WITA — Waktu Indonesia Tengah (UTC+8)"),
        ("WIT", "WIT — Waktu Indonesia Timur (UTC+9)"),
    ]
    TZ_IANA = {
        "WIB": "Asia/Jakarta",
        "WITA": "Asia/Makassar",
        "WIT": "Asia/Jayapura",
    }

    THEME_CHOICES = [
        ("luwu", "Luwu — Editorial Geospatial"),
        ("pesisir", "Pesisir — Tropical Coastal"),
        ("pegunungan", "Pegunungan — Highland Stoic"),
        ("vulkanik", "Vulkanik — Ash & Ember"),
        ("rawa", "Rawa — Wetland Marigold"),
        ("modern", "Modern — Teal Pemerintahan"),
        ("pastel", "Pastel — Cerah Lembut"),
        ("kontras", "Kontras — Bold Cerah"),
    ]

    # Kombinasi font per tema: 3 opsi {label, serif, sans, mono}. Nama = keluarga
    # Google Fonts (dipakai next/font/google di frontend). Indeks opsi disimpan di
    # ``font_option`` (1..3) & berlaku untuk tema aktif.
    FONT_COMBOS = {
        "luwu": [
            {"label": "Modern Editorial", "serif": "Fraunces", "sans": "Geist", "mono": "Geist Mono"},
            {"label": "Klasik Jurnalistik", "serif": "Merriweather", "sans": "Source Sans 3", "mono": "Source Code Pro"},
            {"label": "Humanis & Agraris", "serif": "Lora", "sans": "Fira Sans", "mono": "Fira Mono"},
        ],
        "pesisir": [
            {"label": "Elegan & Mengalir", "serif": "Playfair Display", "sans": "Lato", "mono": "Space Mono"},
            {"label": "Bersih & Berangin", "serif": "Lora", "sans": "Nunito", "mono": "JetBrains Mono"},
            {"label": "Klasik Maritim", "serif": "Merriweather", "sans": "Open Sans", "mono": "Fira Code"},
        ],
        "pegunungan": [
            {"label": "Tradisional & Tangguh", "serif": "Bitter", "sans": "Inter", "mono": "Roboto Mono"},
            {"label": "Megah & Geometris", "serif": "Cormorant Garamond", "sans": "Montserrat", "mono": "Inconsolata"},
            {"label": "Solid & Membumi", "serif": "Zilla Slab", "sans": "Work Sans", "mono": "IBM Plex Mono"},
        ],
        "vulkanik": [
            {"label": "Siaga & Terstruktur", "serif": "Roboto Slab", "sans": "Roboto", "mono": "PT Mono"},
            {"label": "Tegas & Vertikal", "serif": "Alegreya", "sans": "Oswald", "mono": "JetBrains Mono"},
            {"label": "Kuat & Menonjol", "serif": "Bree Serif", "sans": "Rubik", "mono": "Source Code Pro"},
        ],
        "rawa": [
            {"label": "Organik & Estetik", "serif": "Crimson Pro", "sans": "Source Sans 3", "mono": "Courier Prime"},
            {"label": "Hangat & Mudah Dibaca", "serif": "Vollkorn", "sans": "PT Sans", "mono": "Ubuntu Mono"},
            {"label": "Lebar & Berkarakter", "serif": "BioRhyme", "sans": "Cabin", "mono": "Cutive Mono"},
        ],
        "modern": [
            {"label": "Standar Pemerintahan", "serif": "Noto Serif", "sans": "Noto Sans", "mono": "Noto Sans Mono"},
            {"label": "Birokrasi Bersih", "serif": "PT Serif", "sans": "Public Sans", "mono": "Fira Code"},
            {"label": "Berwibawa & Presisi", "serif": "Libre Baskerville", "sans": "IBM Plex Sans", "mono": "IBM Plex Mono"},
        ],
        "pastel": [
            {"label": "Bulat & Bersahabat", "serif": "Gelasio", "sans": "Quicksand", "mono": "Space Mono"},
            {"label": "Elegan & Menyenangkan", "serif": "Alice", "sans": "Poppins", "mono": "Overpass Mono"},
            {"label": "Cerah & Modern", "serif": "Lora", "sans": "DM Sans", "mono": "Anonymous Pro"},
        ],
        "kontras": [
            {"label": "Geometris & Padat", "serif": "Arvo", "sans": "Barlow", "mono": "JetBrains Mono"},
            {"label": "Modern & Berani", "serif": "Rokkitt", "sans": "Space Grotesk", "mono": "Space Mono"},
            {"label": "Industrial & Berat", "serif": "Josefin Slab", "sans": "Archivo", "mono": "Chivo Mono"},
        ],
    }
    FONT_OPTION_CHOICES = [(1, "Opsi 1"), (2, "Opsi 2"), (3, "Opsi 3")]

    nama_kabupaten = models.CharField(
        "Nama Kabupaten", max_length=100, blank=True, default=""
    )
    timezone = models.CharField(
        "Zona waktu", max_length=8, choices=TIMEZONE_CHOICES, default="WIB"
    )
    theme = models.CharField(
        "Tema CMS", max_length=20, choices=THEME_CHOICES, default="luwu"
    )
    font_option = models.PositiveSmallIntegerField(
        "Kombinasi font", choices=FONT_OPTION_CHOICES, default=1,
        help_text="1 dari 3 kombinasi font (serif/sans/mono) untuk tema aktif.",
    )
    webgis_reference_map_id = models.IntegerField(
        "Map referensi WebGIS",
        null=True,
        blank=True,
        help_text="ID Map GeoNode yang dipakai sebagai daftar layer default di WebGIS. "
                  "Kosongkan untuk menggunakan nilai WEBGIS_REFERENCE_MAP_ID dari settings.py.",
    )

    # ── Cakupan wilayah DST (mendorong "Restore Data Wilayah" & auto-muat) ──
    CAKUPAN_LEVEL_CHOICES = [
        ("provinsi", "Provinsi"),
        ("kabupaten", "Kabupaten/Kota"),
    ]
    cakupan_level = models.CharField(
        "Level cakupan DST",
        max_length=12,
        choices=CAKUPAN_LEVEL_CHOICES,
        blank=True,
        default="",
        help_text="provinsi = muat 1 provinsi penuh; kabupaten = muat 1 kabupaten/kota.",
    )
    cakupan_kode_prov = models.CharField(
        "Kode PUM Provinsi cakupan", max_length=32, blank=True, default=""
    )
    cakupan_nama_prov = models.CharField(
        "Nama Provinsi cakupan", max_length=100, blank=True, default=""
    )
    cakupan_kode_kab = models.CharField(
        "Kode PUM Kabupaten/Kota cakupan", max_length=32, blank=True, default=""
    )
    cakupan_nama_kab = models.CharField(
        "Nama Kabupaten/Kota cakupan", max_length=100, blank=True, default=""
    )

    updated = models.DateTimeField(auto_now=True)

    @property
    def iana_timezone(self):
        """Nama zona waktu IANA (mis. 'Asia/Jakarta') untuk kode WIB/WITA/WIT."""
        return self.TZ_IANA.get(self.timezone, "Asia/Jakarta")

    def font_combo(self):
        """Kombinasi font {label, serif, sans, mono} untuk (theme, font_option) aktif."""
        opts = self.FONT_COMBOS.get(self.theme or "luwu") or self.FONT_COMBOS["luwu"]
        idx = (self.font_option or 1) - 1
        if idx < 0 or idx >= len(opts):
            idx = 0
        return opts[idx]

    class Meta:
        verbose_name = "Identitas Situs"
        verbose_name_plural = "Identitas Situs"

    def __str__(self):
        return self.nama_kabupaten or "Identitas Situs"

    def save(self, *args, **kwargs):
        self.pk = 1  # paksa singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ScreeningLog(models.Model):
    """Catatan setiap kali laporan 'Screening Tools analisis' di-generate dari
    Pratinjau Cetak WebGIS.

    Tidak memakai actstream karena actor di sana wajib ada, sedangkan WebGIS
    bisa diakses publik (tanpa login) → ``user`` boleh null dan ``user_label``
    menyimpan nama tampilan ("Publik" bila anonim).
    """

    nomor_reg = models.CharField("Nomor Reg", max_length=64, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="screening_logs",
    )
    user_label = models.CharField(max_length=150, default="Publik")
    ip = models.GenericIPAddressField(null=True, blank=True)
    area_ha = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Screening Log"
        verbose_name_plural = "Screening Logs"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.nomor_reg} · {self.user_label}"


class LandingSection(models.Model):
    """Daftar section halaman Landing + status tampil/sembunyi.

    Dikelola admin via Panel Admin → Frontend. Baris default di-seed otomatis
    saat migrasi pertama. ``key`` = identitas internal stabil yang dipakai di
    template ``index.html`` (lewat ``sections.<key>``); ``anchor`` = id HTML
    section untuk navigasi/scroll.
    """

    # (key, title, anchor, order) — sumber kebenaran daftar section default.
    SECTIONS = [
        ("hero",             "Hero / Beranda",               "beranda",          1),
        ("hero_carousel",    "Hero Carousel (Beranda Alt. 2)","beranda-carousel", 2),
        ("statistik",        "Statistik Ringkas",             "statistik",        3),
        ("pencarian",        "Pencarian Data",                "cari",             4),
        ("screening_tools",  "Modul Screening Tools",         "screening-tools",  5),
        ("komoditas",        "Komoditas Fokus",               "komoditas",        6),
        ("layanan_data",     "Layanan Data",                  "layanan-data",     7),
        ("indikator_strategis","Indikator Strategis",         "indikator-strategis",8),
        ("dokumen",          "Dokumen Kebijakan",             "dokumen",          9),
        ("katalog_data",     "Katalog Data Spasial",          "katalog-data",     10),
        ("eksplorasi_dataset","Eksplorasi Dataset",           "eksplorasi-dataset",11),
        ("tentang_program",  "Tentang Program",               "tentang-program",  12),
        ("mitra",            "Implementing Partners",         "mitra",            13),
        ("capaian_folur",    "Capaian Program FOLUR",         "capaian-folur",    14),
    ]

    # Section yang dibuat tersembunyi secara default (kebalikan dari is_visible=True).
    DEFAULT_HIDDEN = {"hero_carousel"}

    key = models.SlugField("Kunci", max_length=50, unique=True)
    title = models.CharField("Nama section", max_length=100)
    anchor = models.CharField("Anchor (id HTML)", max_length=50, blank=True)
    order = models.PositiveIntegerField("Urutan", default=0)
    is_visible = models.BooleanField("Tampil", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section Landing"
        verbose_name_plural = "Section Landing"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({'tampil' if self.is_visible else 'sembunyi'})"

    @classmethod
    def ensure_defaults(cls):
        """Buat baris default yang belum ada (idempotent)."""
        for key, title, anchor, order in cls.SECTIONS:
            cls.objects.get_or_create(
                key=key,
                defaults={
                    "title": title,
                    "anchor": anchor,
                    "order": order,
                    "is_visible": key not in cls.DEFAULT_HIDDEN,
                },
            )

    @classmethod
    def visibility_map(cls):
        """{key: is_visible} untuk seluruh section kanonik.

        Default True bila barisnya belum ada — agar landing tidak pernah
        kosong total kalau tabel belum ter-seed.
        """
        existing = {s.key: s.is_visible for s in cls.objects.all()}
        return {key: existing.get(key, True) for key, _, _, _ in cls.SECTIONS}


class SidebarMenu(models.Model):
    """Menu pada sidebar Panel Admin + status tampil/sembunyi.

    Dikelola admin via Panel Admin → Backend. ``key`` = identitas internal yang
    selaras dengan ``active_page`` tiap menu di ``_sidebar.html``. Menu pada
    ``LOCKED`` (mis. 'backend') selalu tampil dan tidak punya toggle, agar admin
    tidak mengunci diri sendiri dari panel pengelolaan menu.
    """

    # (key, title, grup, order) — sumber kebenaran daftar menu sidebar.
    MENUS = [
        ("dashboard",       "Dashboard",          "Ringkasan",          1),
        ("capaian",         "Sitroom",            "Ringkasan",          2),
        ("dokumen",         "Dokumen Kebijakan",  "Pengelolaan Data",   3),
        ("data_spasial",    "Data Spasial",       "Pengelolaan Data",   4),
        ("metadata_schema", "Metadata Schema",    "Pengelolaan Data",   5),
        ("akses_nasional",  "Akses Nasional",     "Distribusi & Akses", 6),
        ("endpoint_api",    "Endpoint API",       "Distribusi & Akses", 7),
        ("integrasi_satudata", "Integrasi Satu Data", "Distribusi & Akses", 8),
        ("pengguna",        "Pengguna & Role",    "Administrasi",       9),
        ("audit_log",       "Audit Log",          "Administrasi",       10),
        ("frontend",        "Frontend",           "Administrasi",       11),
        ("backend",         "Backend",            "Administrasi",       12),
        ("pengaturan",      "Pengaturan Sistem",  "Administrasi",       13),
        ("data_capaian",    "Data Capaian",       "Administrasi",       14),
        ("topik_kategori",  "Topik Kategori",     "Administrasi",       15),
        ("walidata",        "Walidata",           "Administrasi",       16),
        ("kode_wilayah",    "Kode Wilayah",       "Administrasi",       17),
        ("tema",            "Tema CMS",           "Administrasi",       18),
        ("geonode",         "GeoNode",            "Tautan",            19),
        ("geonode_admin",   "GeoNode Admin",      "Tautan",            20),
        ("geoserver",       "Geoserver",          "Tautan",            21),
    ]

    # Menu yang selalu tampil (tanpa toggle on/off).
    LOCKED = {"dashboard", "backend"}

    key = models.SlugField("Kunci", max_length=50, unique=True)
    title = models.CharField("Nama menu", max_length=100)
    grup = models.CharField("Grup", max_length=50, blank=True)
    order = models.PositiveIntegerField("Urutan", default=0)
    # is_visible = kolom Super Admin; visible_walidata = kolom Walidata.
    is_visible = models.BooleanField("Tampil (Super Admin)", default=True)
    visible_walidata = models.BooleanField("Tampil (Walidata)", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menu Sidebar"
        verbose_name_plural = "Menu Sidebar"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.title} ({'tampil' if self.is_visible else 'sembunyi'})"

    @classmethod
    def ensure_defaults(cls):
        """Buat baris default yang belum ada (idempotent)."""
        for key, title, grup, order in cls.MENUS:
            cls.objects.get_or_create(
                key=key,
                defaults={
                    "title": title,
                    "grup": grup,
                    "order": order,
                    "is_visible": True,
                    "visible_walidata": True,
                },
            )

    @classmethod
    def visibility_map(cls, role="super"):
        """{key: tampil?} untuk peran tertentu ('super' atau 'walidata').

        'super' memakai kolom is_visible, 'walidata' memakai visible_walidata.
        Default True bila barisnya belum ada. Menu LOCKED dipaksa selalu True.
        """
        field = "visible_walidata" if role == "walidata" else "is_visible"
        existing = {m.key: getattr(m, field) for m in cls.objects.all()}
        vis = {key: existing.get(key, True) for key, _, _, _ in cls.MENUS}
        for k in cls.LOCKED:
            vis[k] = True
        return vis


class KomoditasFokus(models.Model):
    """Daftar fokus komoditas unggulan daerah/FOLUR.

    Dikelola admin di Pengaturan Sistem → FOLUR (CRUD). Tiap komoditas dapat
    ditautkan ke satu Dataset (peta kesesuaian lahan) dan satu Dokumen
    (literatur komoditi), serta punya gambar/foto.
    """

    nama = models.CharField("Nama komoditas", max_length=120)
    deskripsi = models.TextField("Deskripsi", blank=True, default="")
    dataset = models.ForeignKey(
        "layers.Dataset",
        verbose_name="Peta kesesuaian lahan (Dataset)",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    dokumen = models.ForeignKey(
        "documents.Document",
        verbose_name="Literatur komoditi (Dokumen)",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    gambar = models.ImageField("Gambar/Foto", upload_to="komoditas/", null=True, blank=True)
    urutan = models.PositiveIntegerField("Urutan", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fokus Komoditas"
        verbose_name_plural = "Fokus Komoditas"
        ordering = ["urutan", "id"]

    def __str__(self):
        return self.nama


class ImplementingPartner(models.Model):
    """Mitra pelaksana (Implementing Partners) — logo ditampilkan di landing.

    Dikelola admin di Pengaturan Sistem → Implementing Partners (CRUD upload
    logo). Logo dirender dengan tinggi 100px dan lebar proporsional.
    """

    nama = models.CharField("Nama mitra", max_length=150)
    logo = models.ImageField("Logo", upload_to="partners/")
    tautan = models.URLField("Tautan situs", blank=True, default="")
    urutan = models.PositiveIntegerField("Urutan", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Implementing Partner"
        verbose_name_plural = "Implementing Partners"
        ordering = ["urutan", "id"]

    def __str__(self):
        return self.nama


class IndikatorStrategis(models.Model):
    """Indikator strategis daerah (mis. IPM, pertumbuhan ekonomi, inflasi).

    Konten khas daerah (CMS) — section di Landing dapat disembunyikan untuk
    kabupaten lain via Panel Admin → Frontend. Dikelola admin di Pengaturan
    Sistem → Indikator Strategis (CRUD). Nilai disimpan sebagai teks bebas agar
    fleksibel ("89%", "11,5 persen", "0,364"). Ikon dirujuk dari folder statis
    ``static/dst-district/img/indikator/`` (nama berkas pada field ``ikon``).
    """

    judul = models.CharField("Judul indikator", max_length=120)
    nilai = models.CharField("Nilai", max_length=50)
    deskripsi = models.CharField("Deskripsi", max_length=255, blank=True, default="")
    ikon = models.CharField(
        "Ikon (nama berkas PNG)",
        max_length=100,
        blank=True,
        default="",
        help_text="Nama berkas di static/dst-district/img/indikator/ — mis. indikator-strategis-1.png",
    )
    urutan = models.PositiveIntegerField("Urutan", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Indikator Strategis"
        verbose_name_plural = "Indikator Strategis"
        ordering = ["urutan", "id"]

    def __str__(self):
        return f"{self.judul} ({self.nilai})"


class LayananData(models.Model):
    """Kartu layanan / kategori data daerah (mis. Data Ekonomi, Data Kesehatan).

    Konten khas daerah (CMS) — section di Landing dapat disembunyikan untuk
    kabupaten lain via Panel Admin → Frontend. Dikelola admin di Pengaturan
    Sistem → Layanan Data (CRUD). Setiap kartu punya gambar, judul, dan tautan
    "Detail". ``ikon`` boleh berupa nama berkas di
    ``static/dst-district/img/layanan/`` ATAU URL lengkap (http...).
    """

    judul = models.CharField("Judul layanan", max_length=150)
    ikon = models.CharField(
        "Gambar (nama berkas / URL)",
        max_length=255,
        blank=True,
        default="",
        help_text="Nama berkas di static/dst-district/img/layanan/ (mis. layanan-1.png) atau URL lengkap.",
    )
    tautan = models.CharField(
        "Tautan Detail",
        max_length=255,
        blank=True,
        default="",
        help_text="URL halaman detail (boleh internal atau eksternal).",
    )
    urutan = models.PositiveIntegerField("Urutan", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Layanan Data"
        verbose_name_plural = "Layanan Data"
        ordering = ["urutan", "id"]

    def __str__(self):
        return self.judul


class Walidata(models.Model):
    """Daftar instansi Walidata (wali data) — pengampu/penyelenggara data.

    Dikelola admin via Panel Admin → Walidata (CRUD). Tiap baris menyimpan
    singkatan (``nama``), kepanjangan, dan alamat instansi walidata di daerah.
    """

    nama = models.CharField("Singkatan", max_length=120)
    kepanjangan = models.CharField(
        "Kepanjangan", max_length=255, blank=True, default=""
    )
    alamat = models.TextField("Alamat", blank=True, default="")
    urutan = models.PositiveIntegerField("Urutan", default=0)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Walidata"
        verbose_name_plural = "Walidata"
        ordering = ["urutan", "nama", "id"]

    def __str__(self):
        return self.nama


class WalidataMembership(models.Model):
    """Tautan pengguna ke instansi Walidata tempatnya bernaung.

    Dipilih pengguna sendiri di Panel Admin → Profil (kolom Nama Walidata).
    OneToOne: tiap pengguna terkait paling banyak satu walidata.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="walidata_membership",
        verbose_name="Pengguna",
    )
    walidata = models.ForeignKey(
        "Walidata",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anggota",
        verbose_name="Walidata",
    )
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Keanggotaan Walidata"
        verbose_name_plural = "Keanggotaan Walidata"

    def __str__(self):
        return f"{self.user} → {self.walidata}"


class DocumentWalidata(models.Model):
    """Tautan Dokumen GeoNode ke instansi Walidata (tabel master).

    Model ``Document`` milik GeoNode tidak punya kolom Walidata, sehingga
    keterkaitan dokumen ke instansi Walidata disimpan di sini (satu dokumen →
    satu Walidata). Diisi dari form Panel Admin → Dokumen (section Klasifikasi)
    maupun otomatis saat berkas dataset CKAN didaftarkan sebagai Dokumen.

    Sumber kebenaran tampilan/filter Walidata untuk dokumen: bila tautan ini
    ada, dipakai; bila tidak, sistem jatuh ke ``poc.organization`` (dokumen lama).
    """

    document = models.OneToOneField(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="walidata_link",
        verbose_name="Dokumen",
    )
    walidata = models.ForeignKey(
        "Walidata",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Walidata",
    )
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Walidata Dokumen"
        verbose_name_plural = "Walidata Dokumen"

    def __str__(self):
        return f"#{self.document_id} → {self.walidata}"


class DatasetWalidata(models.Model):
    """Tautan Dataset (layer) GeoNode ke instansi Walidata (tabel master).

    Paralel dengan ``DocumentWalidata`` untuk dokumen: ``Dataset`` GeoNode tak
    punya kolom Walidata, jadi keterkaitan ke tabel master disimpan di sini
    (satu dataset → satu Walidata). Sumber kebenaran tampilan/filter Walidata
    untuk dataset; bila tak ada, sistem jatuh ke ``poc.organization`` (data lama).
    """

    dataset = models.OneToOneField(
        "layers.Dataset",
        on_delete=models.CASCADE,
        related_name="walidata_link",
        verbose_name="Dataset",
    )
    walidata = models.ForeignKey(
        "Walidata",
        on_delete=models.CASCADE,
        related_name="geo_datasets",
        verbose_name="Walidata",
    )
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Walidata Dataset"
        verbose_name_plural = "Walidata Dataset"

    def __str__(self):
        return f"#{self.dataset_id} → {self.walidata}"


# ===========================================================================
# Referensi batas wilayah administrasi (BIG / RBI)
# ---------------------------------------------------------------------------
# Tabel referensi murni hasil sinkronisasi dari layanan ArcGIS REST publik
# Badan Informasi Geospasial (geoservices.big.go.id). Disinkron lewat
# ``python manage.py sync_wilayah_big``. Menyimpan kode PUM/Kemendagri & kode
# BPS sekaligus (penjembatan), plus geometri poligon penuh (SRID 4326).
# Sumber data © Badan Informasi Geospasial (BIG).
# ===========================================================================


class RefWilayahBase(models.Model):
    """Basis kolom yang sama untuk tiap jenjang batas administrasi BIG."""

    kode_pum = models.CharField(
        "Kode PUM/Kemendagri", max_length=32, unique=True
    )
    kode_bps = models.CharField(
        "Kode BPS", max_length=32, blank=True, db_index=True
    )
    nama = models.CharField("Nama", max_length=255, db_index=True)
    luas_ha = models.FloatField("Luas menurut peraturan (HA)", null=True, blank=True)
    geom = gis_models.MultiPolygonField("Geometri", srid=4326)
    updated_at = models.DateTimeField("Disinkron pada", auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nama} ({self.kode_pum})"


class RefWilayahProvinsi(RefWilayahBase):
    class Meta:
        db_table = 'wilayah"."provinsi'
        verbose_name = "Ref Wilayah — Provinsi"
        verbose_name_plural = "Ref Wilayah — Provinsi"
        ordering = ["kode_pum"]


class RefWilayahKabkota(RefWilayahBase):
    kode_prov_pum = models.CharField(
        "Kode PUM Provinsi", max_length=32, db_index=True
    )
    nama_prov = models.CharField("Nama Provinsi", max_length=255, blank=True)

    class Meta:
        db_table = 'wilayah"."kabkota'
        verbose_name = "Ref Wilayah — Kabupaten/Kota"
        verbose_name_plural = "Ref Wilayah — Kabupaten/Kota"
        ordering = ["kode_pum"]


class RefWilayahKecamatan(RefWilayahBase):
    kode_kab_pum = models.CharField(
        "Kode PUM Kabupaten/Kota", max_length=32, db_index=True
    )
    kode_prov_pum = models.CharField(
        "Kode PUM Provinsi", max_length=32, db_index=True
    )
    nama_kab = models.CharField("Nama Kabupaten/Kota", max_length=255, blank=True)
    nama_prov = models.CharField("Nama Provinsi", max_length=255, blank=True)

    class Meta:
        db_table = 'wilayah"."kecamatan'
        verbose_name = "Ref Wilayah — Kecamatan"
        verbose_name_plural = "Ref Wilayah — Kecamatan"
        ordering = ["kode_pum"]


class RefWilayahDesa(RefWilayahBase):
    kode_kec_pum = models.CharField(
        "Kode PUM Kecamatan", max_length=32, db_index=True
    )
    kode_kab_pum = models.CharField(
        "Kode PUM Kabupaten/Kota", max_length=32, db_index=True
    )
    kode_prov_pum = models.CharField(
        "Kode PUM Provinsi", max_length=32, db_index=True
    )
    nama_kec = models.CharField("Nama Kecamatan", max_length=255, blank=True)
    nama_kab = models.CharField("Nama Kabupaten/Kota", max_length=255, blank=True)
    nama_prov = models.CharField("Nama Provinsi", max_length=255, blank=True)

    class Meta:
        db_table = 'wilayah"."desa'
        verbose_name = "Ref Wilayah — Desa/Kelurahan"
        verbose_name_plural = "Ref Wilayah — Desa/Kelurahan"
        ordering = ["kode_pum"]


class IdmDesa(models.Model):
    """Indeks Desa Membangun (IDM) per desa — sumber satudata.kemendesa.go.id.

    Tabular (tanpa geometri), di schema ``wilayah`` agar ikut dikecualikan dari
    backup. ``kode_desa`` = kode Kemendagri 10 digit tanpa titik (mis.
    ``1101012001``) — sama dengan ``RefWilayahDesa.kode_pum`` yang di-strip
    titiknya, sehingga bisa di-join. Disinkron via ``manage.py sync_idm``.
    """

    kode_desa = models.CharField(
        "Kode Desa (Kemendagri, tanpa titik)", max_length=20, db_index=True
    )
    kode_prov = models.CharField("Kode Provinsi", max_length=10, blank=True)
    kode_kab = models.CharField("Kode Kabupaten/Kota", max_length=10, blank=True)
    kode_kec = models.CharField("Kode Kecamatan", max_length=12, blank=True)
    nama_desa = models.CharField("Nama Desa/Kelurahan", max_length=255, blank=True)
    nama_kec = models.CharField("Nama Kecamatan", max_length=255, blank=True)
    nama_kab = models.CharField("Nama Kabupaten/Kota", max_length=255, blank=True)
    nama_prov = models.CharField("Nama Provinsi", max_length=255, blank=True)
    tahun = models.PositiveSmallIntegerField("Tahun", db_index=True)
    iks = models.FloatField("Indeks Ketahanan Sosial", null=True, blank=True)
    ike = models.FloatField("Indeks Ketahanan Ekonomi", null=True, blank=True)
    ikl = models.FloatField("Indeks Ketahanan Lingkungan", null=True, blank=True)
    skor_idm = models.FloatField("Nilai IDM", null=True, blank=True)
    status = models.CharField("Status IDM", max_length=32, blank=True, db_index=True)
    updated_at = models.DateTimeField("Disinkron pada", auto_now=True)

    class Meta:
        db_table = 'wilayah"."idm'
        verbose_name = "IDM Desa"
        verbose_name_plural = "IDM Desa"
        ordering = ["kode_desa"]
        unique_together = [("kode_desa", "tahun")]


class RefKodeBps(models.Model):
    """Crosswalk PERMANEN kode Kemendagri (PUM) ↔ kode BPS.

    Layanan BIG hanya menyediakan kode PUM/Kemendagri; kolom BPS-nya
    (``KDBBPS``/``KDCBPS``/``KDEBPS``) selalu kosong. Tabel ini menyimpan
    pemetaan resmi BPS↔Kemendagri (sumber: tabel jembatan BPS,
    https://sig.bps.go.id/bridging-kode) supaya ``kode_bps`` pada data hasil
    "Restore Data Wilayah" (``RefWilayahKabkota`` dst) bisa diisi via join
    ``kode_pum``.

    PENTING — tabel ini di schema default ``geonode_project`` (BUKAN ``wilayah``):
    data wilayah BIG di-``TRUNCATE`` tiap restore, sedangkan crosswalk ini harus
    PERMANEN (tetap ada lintas-restore & ikut backup). Hanya atribut kode/nama —
    TANPA geometri (poligon ada di ``RefWilayah*`` schema ``wilayah``).

    Cakupan kini LENGKAP se-Indonesia di keempat jenjang (38 provinsi, 514
    kab/kota, ±7.285 kecamatan, ±83.723 desa). Di-seed via ``manage.py
    load_kode_bps`` (+ migrasi 0051–0053) dari ``seed_data/kode_bps_*.csv``;
    sumber kec/desa: dataset bridging BPS Wilkerstat + Kemendagri
    (SalzBytes/wilayah_indonesia), provinsi & kabkota terverifikasi 100% cocok.
    """

    LEVEL_CHOICES = [
        ("provinsi", "Provinsi"),
        ("kabkota", "Kabupaten/Kota"),
        ("kecamatan", "Kecamatan"),
        ("desa", "Desa/Kelurahan"),
    ]

    level = models.CharField(
        "Jenjang", max_length=16, choices=LEVEL_CHOICES,
        default="kabkota", db_index=True,
    )
    kode_pum = models.CharField(
        "Kode PUM/Kemendagri", max_length=32, db_index=True
    )
    kode_bps = models.CharField("Kode BPS", max_length=32, db_index=True)
    nama = models.CharField("Nama", max_length=255, blank=True)
    file_logo = models.CharField(
        "Nama berkas logo", max_length=255, blank=True,
        help_text="Berkas di seed_data/logo_kab/ (kab-h250px-<digit kode>.<ext>); "
                  "kosong bila belum ada logo.",
    )

    class Meta:
        verbose_name = "Crosswalk Kode BPS"
        verbose_name_plural = "Crosswalk Kode BPS"
        ordering = ["level", "kode_pum"]
        constraints = [
            models.UniqueConstraint(
                fields=["level", "kode_pum"], name="uniq_refkodebps_level_pum"
            )
        ]

    def __str__(self):
        return f"{self.kode_pum} → {self.kode_bps} ({self.nama})"


# ===========================================================================
# Capaian Program FOLUR (results framework / GEF Core Indicators)
# ---------------------------------------------------------------------------
# Kerangka KPI program FOLUR di kabupaten. Dipakai panel Sitroom
# (``/dst-auth/capaian/``) & section publik di Landing. Tabel DINAMIS (sering
# di-update) → tetap di schema default ``geonode_project`` (BUKAN ``wilayah``
# yang statis & dikecualikan backup).
# ===========================================================================


# Registry palet warna choropleth webgis2 (5 kelas, urut nilai rendah→tinggi).
# SATU sumber kebenaran: dipakai model (choices), view webgis2 (ramp peta+legenda),
# dan dropdown swatch di Admin Data Capaian. Tiap entri: key -> (label, [5 hex]).
WEBGIS2_PALETTES = {
    "hijau":   ("Hijau (bawaan)",      ["#dfe7d3", "#b9cda0", "#8caa6e", "#5a8048", "#1F3A2E"]),
    "biru":    ("Biru",                ["#d6e6f4", "#a9cce3", "#6fa8d6", "#3a7bbf", "#1f4e8c"]),
    "teal":    ("Teal / Toska",        ["#d8efe9", "#a6dacb", "#5fc0a6", "#2f9d83", "#11705c"]),
    "oranye":  ("Oranye",              ["#f6e3c5", "#e7c596", "#d99c5b", "#bf7330", "#8a4b16"]),
    "merah":   ("Merah",               ["#fde0df", "#f6b0ad", "#e87a75", "#cf4640", "#9b1c17"]),
    "ungu":    ("Ungu",                ["#e7e1f0", "#c9b8e0", "#a78bcc", "#7e5bb0", "#553787"]),
    "pelangi": ("Pelangi (Spektral)",  ["#2b83ba", "#abdda4", "#ffffbf", "#fdae61", "#d7191c"]),
    "viridis": ("Viridis",             ["#440154", "#414487", "#22a884", "#7ad151", "#fde725"]),
    "magma":   ("Magma",               ["#000004", "#51127c", "#b73779", "#fc8961", "#fcfdbf"]),
}


class FolurIndikator(models.Model):
    """Indikator capaian program FOLUR (results framework).

    Dikelola admin di Pengaturan Sistem → Capaian Program FOLUR (CRUD). Tiap
    indikator punya ``target``; realisasi per tahun disimpan terpisah di
    ``FolurCapaian``. Indikator ``sumber='auto'`` nilainya DIHITUNG dari data
    sistem (lihat ``compute_folur_auto_kpis`` / ``build_folur_kpis`` di views),
    bukan dari entri manual. ``pilar`` memakai slug yang sama dengan template
    Sitroom (``capaian.html``).
    """

    PILAR_CHOICES = [
        ("kawasan_lindung", "Kawasan Lindung"),
        ("restorasi", "Restorasi Lahan"),
        ("praktik_lestari", "Praktik Lestari"),
        ("grk", "Mitigasi GRK"),
        ("penerima_manfaat", "Penerima Manfaat"),
        ("value_chain", "Rantai Nilai Komoditas"),
        ("tata_kelola", "Tata Kelola Bentang Lahan"),
    ]
    SUMBER_CHOICES = [
        ("manual", "Entri manual"),
        ("auto", "Otomatis (dari data sistem)"),
    ]
    ARAH_CHOICES = [
        ("naik", "Naik = lebih baik"),
        ("turun", "Turun = lebih baik"),
    ]
    AGREGASI_CHOICES = [
        ("tahunan", "Tahunan (snapshot per tahun)"),
        ("kumulatif", "Kumulatif (jumlah antar tahun)"),
    ]
    SUMBER_AGREGAT_CHOICES = [
        ("manual", "Manual (entri agregat per tahun)"),
        ("roll_up", "Roll-up (Σ dari data per-wilayah)"),
    ]
    PALET_CHOICES = [(k, v[0]) for k, v in WEBGIS2_PALETTES.items()]

    kode = models.CharField("Kode", max_length=20)
    nama = models.CharField("Nama indikator", max_length=200)
    pilar = models.CharField("Pilar", max_length=20, choices=PILAR_CHOICES)
    satuan = models.CharField("Satuan", max_length=30, blank=True, default="")
    deskripsi = models.TextField("Deskripsi", blank=True, default="")
    baseline = models.FloatField("Baseline", null=True, blank=True)
    target = models.FloatField("Target", null=True, blank=True)
    arah = models.CharField("Arah capaian", max_length=6, choices=ARAH_CHOICES, default="naik")
    agregasi = models.CharField(
        "Agregasi antar-tahun", max_length=10, choices=AGREGASI_CHOICES,
        default="tahunan",
        help_text="tahunan = nilai tahun terpilih; kumulatif = jumlah s.d. tahun "
        "terpilih (mis. CI3 Lahan terestorasi). Dipakai Sitroom, Capaian Publik, webgis2.",
    )
    sumber_agregat = models.CharField(
        "Sumber angka agregat", max_length=10, choices=SUMBER_AGREGAT_CHOICES,
        default="manual",
        help_text="manual = pakai entri Realisasi Tahunan (FolurCapaian); roll_up = "
        "hitung dari Σ Capaian per Wilayah (desa) → sinkron lintas yurisdiksi.",
    )
    palet = models.CharField(
        "Palet warna peta", max_length=20, choices=PALET_CHOICES, default="hijau",
        help_text="Skema warna class interval di legenda & choropleth /webgis2/.",
    )
    sumber = models.CharField(
        "Sumber nilai", max_length=6, choices=SUMBER_CHOICES, default="manual"
    )
    auto_key = models.SlugField(
        "Kunci komputasi auto",
        max_length=50,
        blank=True,
        default="",
        help_text="Diisi hanya bila sumber=auto; pengenal fungsi penghitung di views.",
    )
    extra = models.CharField(
        "Catatan tambahan (badge)", max_length=120, blank=True, default=""
    )
    urutan = models.PositiveIntegerField("Urutan", default=0)
    aktif = models.BooleanField("Aktif", default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Indikator FOLUR"
        verbose_name_plural = "Indikator FOLUR"
        ordering = ["urutan", "id"]

    def __str__(self):
        return f"{self.kode} · {self.nama}"

    @property
    def pilar_nama(self):
        return dict(self.PILAR_CHOICES).get(self.pilar, self.pilar)


class FolurCapaian(models.Model):
    """Realisasi indikator FOLUR per tahun (time-series)."""

    indikator = models.ForeignKey(
        "FolurIndikator",
        on_delete=models.CASCADE,
        related_name="capaian",
        verbose_name="Indikator",
    )
    tahun = models.PositiveSmallIntegerField("Tahun", db_index=True)
    nilai = models.FloatField("Realisasi")
    catatan = models.CharField("Catatan", max_length=255, blank=True, default="")
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Capaian FOLUR"
        verbose_name_plural = "Capaian FOLUR"
        ordering = ["indikator", "-tahun"]
        unique_together = [("indikator", "tahun")]

    def __str__(self):
        return f"{self.indikator.kode} {self.tahun} = {self.nilai}"


class FolurCapaianWilayah(models.Model):
    """Realisasi indikator FOLUR per WILAYAH (desa/kecamatan) per tahun.

    Pelengkap spasial dari ``FolurCapaian`` (yang agregat per-tahun). Dipakai
    halaman publik ``/webgis2/`` untuk choropleth & monitoring per desa/kecamatan.
    ``kode_pum`` mengacu ke ``RefWilayahDesa``/``RefWilayahKecamatan.kode_pum``
    (format bertitik, mis. ``73.17.01.2005``). Entri dilakukan di Admin
    'Data Capaian'; webgis2 hanya membaca (read-only).
    """

    LEVEL_CHOICES = [
        ("desa", "Desa/Kelurahan"),
        ("kecamatan", "Kecamatan"),
    ]

    indikator = models.ForeignKey(
        "FolurIndikator",
        on_delete=models.CASCADE,
        related_name="capaian_wilayah",
        verbose_name="Indikator",
    )
    level = models.CharField(
        "Jenjang", max_length=10, choices=LEVEL_CHOICES, default="desa", db_index=True
    )
    kode_pum = models.CharField(
        "Kode PUM/Kemendagri", max_length=32, db_index=True
    )
    nama = models.CharField("Nama wilayah", max_length=255, blank=True, default="")
    tahun = models.PositiveSmallIntegerField("Tahun", db_index=True)
    kegiatan = models.CharField(
        "Kegiatan", max_length=255, blank=True, default="",
        help_text="Jenis kegiatan di wilayah ini (teks bebas), mis. "
        "'intensifikasi lahan tanaman padi'.",
    )
    komoditas = models.ForeignKey(
        "KomoditasFokus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capaian_wilayah",
        verbose_name="Komoditas fokus",
        help_text="Relasi ke Fokus Komoditas (Pengaturan). Opsional.",
    )
    nilai = models.FloatField("Realisasi")
    catatan = models.CharField("Catatan", max_length=255, blank=True, default="")
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Capaian FOLUR per Wilayah"
        verbose_name_plural = "Capaian FOLUR per Wilayah"
        ordering = ["indikator", "level", "kode_pum", "-tahun"]
        constraints = [
            models.UniqueConstraint(
                fields=["indikator", "level", "kode_pum", "tahun"],
                name="uniq_folurcapaianwilayah",
            )
        ]
        indexes = [
            models.Index(fields=["indikator", "tahun", "level"]),
        ]

    def __str__(self):
        return f"{self.indikator.kode} {self.level}:{self.kode_pum} {self.tahun} = {self.nilai}"


class SatuDataSource(models.Model):
    """Konfigurasi + log harvest portal Satu Data Kabupaten (CKAN).

    Dipakai sebagai satu baris (singleton): menyimpan basis URL portal CKAN yang
    di-harvest dari halaman Panel Admin → Integrasi Satu Data, serta jejak harvest
    terakhir (waktu, status, jumlah). Field URL di halaman di-prefill dari sini.
    """

    base_url = models.URLField("Basis URL CKAN", max_length=300)
    nama_portal = models.CharField("Nama portal", max_length=200, blank=True, default="")
    organisasi_filter = models.CharField(
        "Filter organisasi (opsional)", max_length=200, blank=True, default=""
    )
    verifikasi_ssl = models.BooleanField(
        "Verifikasi sertifikat SSL",
        default=True,
        help_text="Nonaktifkan bila portal memakai sertifikat yang tak terverifikasi.",
    )
    last_harvested = models.DateTimeField("Terakhir di-harvest", null=True, blank=True)
    last_status = models.CharField("Status terakhir", max_length=10, blank=True, default="")
    last_pesan = models.CharField("Pesan terakhir", max_length=255, blank=True, default="")
    last_jumlah = models.PositiveIntegerField("Jumlah dataset terakhir", default=0)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sumber Satu Data"
        verbose_name_plural = "Sumber Satu Data"
        ordering = ["id"]

    def __str__(self):
        return self.nama_portal or self.base_url


class SatuDataset(models.Model):
    """Satu dataset (CKAN *package*) hasil harvest portal Satu Data Kabupaten."""

    source = models.ForeignKey(
        "SatuDataSource",
        on_delete=models.CASCADE,
        related_name="datasets",
        verbose_name="Sumber",
    )
    ckan_id = models.CharField("ID CKAN", max_length=100)
    name = models.SlugField("Slug", max_length=200, blank=True, default="")
    title = models.CharField("Judul", max_length=400)
    notes = models.TextField("Deskripsi", blank=True, default="")
    organisasi = models.CharField("Organisasi", max_length=200, blank=True, default="")
    walidata = models.ForeignKey(
        "Walidata",
        verbose_name="Walidata",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="satu_datasets",
        help_text="Hasil pencocokan otomatis organisasi CKAN ke daftar Walidata.",
    )
    lisensi = models.CharField("Lisensi", max_length=200, blank=True, default="")
    tags = models.CharField("Tag", max_length=500, blank=True, default="")
    jumlah_resource = models.PositiveIntegerField("Jumlah file", default=0)
    metadata_modified = models.DateTimeField("Diperbarui", null=True, blank=True)
    portal_url = models.URLField("Tautan portal", max_length=400, blank=True, default="")
    raw = models.JSONField("Data mentah", blank=True, default=dict)
    harvested_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dataset Satu Data"
        verbose_name_plural = "Dataset Satu Data"
        ordering = ["title", "id"]
        unique_together = [("source", "ckan_id")]

    def __str__(self):
        return self.title


class SatuDataResource(models.Model):
    """Satu file/resource milik sebuah ``SatuDataset`` (hasil harvest CKAN)."""

    dataset = models.ForeignKey(
        "SatuDataset",
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="Dataset",
    )
    ckan_id = models.CharField("ID CKAN", max_length=100, blank=True, default="")
    nama = models.CharField("Nama file", max_length=400, blank=True, default="")
    deskripsi = models.TextField("Deskripsi", blank=True, default="")
    format = models.CharField("Format", max_length=50, blank=True, default="")
    url = models.URLField("Tautan unduh", max_length=600, blank=True, default="")
    ukuran = models.BigIntegerField("Ukuran (byte)", null=True, blank=True)
    last_modified = models.DateTimeField("Diperbarui", null=True, blank=True)
    document = models.ForeignKey(
        "documents.Document",
        verbose_name="Dokumen GeoNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Terisi bila file ini sudah diunduh & didaftarkan sebagai Dokumen.",
    )
    raw = models.JSONField("Data mentah", blank=True, default=dict)

    class Meta:
        verbose_name = "File Satu Data"
        verbose_name_plural = "File Satu Data"
        ordering = ["id"]

    def __str__(self):
        return self.nama or self.url


class SatuDataOrgWalidata(models.Model):
    """Pemetaan manual organisasi CKAN → instansi Walidata (per sumber Satu Data).

    Mengikat nilai field ``organisasi`` (judul organisasi CKAN) ke satu instansi
    ``Walidata``. Disetel admin di panel Integrasi Satu Data, lalu diterapkan ke
    seluruh ``SatuDataset`` organisasi tersebut sekaligus dipakai harvest berikutnya.

    Semantik ``walidata``:
      * berisi Walidata  → organisasi terpetakan; datasetnya boleh didaftarkan ke Dokumen.
      * ``NULL``         → sengaja TIDAK dipetakan; datasetnya tidak didaftarkan ke Dokumen.
      * tanpa baris      → belum diputuskan; harvest memakai pencocokan otomatis (fuzzy).
    """

    source = models.ForeignKey(
        "SatuDataSource",
        on_delete=models.CASCADE,
        related_name="org_maps",
        verbose_name="Sumber",
    )
    org_title = models.CharField("Organisasi CKAN", max_length=200)
    walidata = models.ForeignKey(
        "Walidata",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="org_maps",
        verbose_name="Walidata",
    )
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pemetaan Organisasi Walidata"
        verbose_name_plural = "Pemetaan Organisasi Walidata"
        ordering = ["org_title"]
        unique_together = [("source", "org_title")]

    def __str__(self):
        return f"{self.org_title} → {self.walidata or '—'}"
