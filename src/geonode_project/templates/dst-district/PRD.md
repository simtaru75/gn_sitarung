**PRODUCT REQUIREMENTS DOCUMENT (PRD)**

**DECISION SUPPORT TOOL (DST)**

**TINGKAT KABUPATEN — KABUPATEN LUWU**

_Program Food Systems, Land Use and Restoration (FOLUR)_

_Provinsi Sulawesi Selatan_

**Versi Dokumen**

1.0

**Tanggal Terbit**

Mei 2026

**Status**

Draft untuk Diskusi

**Klasifikasi**

Internal — FOLUR Project

**Referensi TOR**

Development of DST Web Application — District Level (5 Districts)

1\. Ringkasan Eksekutif
=======================

Decision Support Tool (DST) Kabupaten Luwu adalah aplikasi web berbasis platform GeoNode yang berfungsi sebagai pusat pengelolaan data kabupaten untuk mendukung implementasi Integrated Landscape Management (ILM) di bawah Program FOLUR (Food Systems, Land Use and Restoration). Kabupaten Luwu merupakan satu dari lima kabupaten target FOLUR dengan fokus komoditas kakao dan padi.

Dalam arsitektur DST FOLUR secara nasional, DST Kabupaten Luwu diposisikan sebagai node penyedia data (data provider). Aplikasi ini mengelola dua kelompok data utama: (1) dokumen kebijakan terkait penataan ruang, tata guna lahan, kehutanan/lingkungan, perencanaan pembangunan, serta regulasi sektor kakao dan padi; dan (2) data spasial yang mencakup penggunaan lahan, area HCV/HCS, zona produksi komoditas, area restorasi, dan layer tata ruang.

Seluruh fungsi penilaian dan analitik lanjutan — meliputi policy screening, scorecard system, annual monitoring report, dan formulasi rekomendasi tindak lanjut — TIDAK dibangun pada level kabupaten. Fungsi-fungsi tersebut merupakan kewenangan DST Nasional, yang akan melakukan harvesting (pemanenan otomatis) data dari DST Kabupaten Luwu melalui mekanisme API dan protokol interoperabilitas standar (OGC, CSW, REST). Pemisahan ini menjamin konsistensi metodologi penilaian lintas lima kabupaten target dan menempatkan kabupaten sebagai pemilik (custodian) data otoritatif.

Secara teknis, sistem dibangun di atas instance GeoNode yang telah tersedia, dengan tiga komponen frontend yang dikustomisasi: (i) halaman GeoNode native untuk eksplorasi katalog data dan peta; (ii) halaman landing page publik yang menyajikan profil program, showcase data unggulan, dan akses informasi bagi masyarakat umum; dan (iii) panel admin khusus (custom admin) yang dirancang untuk operasional CRUD oleh pengelola data kabupaten dengan workflow yang disederhanakan, sehingga tidak bergantung pada antarmuka admin Django/GeoNode bawaan yang kompleks.

2\. Latar Belakang
==================

2.1 Konteks Program FOLUR
-------------------------

Program FOLUR Indonesia bertujuan mencapai transformasi rantai pasok komoditas berkelanjutan dan tata kelola lahan, sehingga menurunkan kehilangan kawasan hutan bernilai konservasi tinggi (High Conservation Value/HCV) dan kawasan stok karbon tinggi (High Carbon Stock/HCS) pada lima kabupaten target. Di bawah Outcome 2, program ini mengembangkan rencana ILM jurisdiksional di tiap kabupaten target, dan rencana ILM tersebut memerlukan instrumen pendukung berupa Decision Support Tool.

2.2 Posisi Kabupaten Luwu dalam FOLUR
-------------------------------------

Kabupaten Luwu di Provinsi Sulawesi Selatan ditetapkan sebagai kabupaten target dengan fokus komoditas kakao dan padi. Karakteristik bentang lahan Luwu yang memadukan area perkebunan kakao smallholder, lahan sawah, kawasan hutan, dan ekosistem esensial menempatkan kabupaten ini pada konteks ILM yang khas, sehingga DST yang dikembangkan harus mampu mengakomodasi kebutuhan pengelolaan data lintas sektor tersebut.

2.3 Hubungan dengan DST Nasional
--------------------------------

Dalam dokumen Output 1.4 program FOLUR, dikembangkan policy assessment tool tingkat nasional yang terdiri dari tiga fungsi utama: (1) policy screening; (2) scorecard system dengan matriks penilaian SDG interaction; dan (3) reporting mechanism berupa laporan tahunan. Tool nasional ini akan dioperasikan dengan koordinasi Kementerian Koordinator Bidang Perekonomian (CMEA) dan akses penuh dari BAPPENAS, Kemenko Marves, KLHK, Kementan, dan ATR/BPN.

Mengingat bahwa metodologi penilaian harus konsisten lintas yurisdiksi (nasional dan lima kabupaten target), arsitektur DST Kabupaten Luwu ini secara sengaja diposisikan SEBAGAI PENYEDIA DATA, bukan sebagai pelaksana penilaian. Pembagian peran ini juga sejalan dengan prinsip One Data Indonesia dan One Map Policy yang mengamanatkan agar instansi pemilik data bertindak sebagai walidata, sedangkan analisis dan rekomendasi kebijakan dilakukan oleh instansi yang berwenang di tingkat pusat.

2.4 Kebutuhan Pengembangan
--------------------------

Saat ini, di Kabupaten Luwu telah tersedia berbagai sistem informasi parsial dan data spasial yang dikelola oleh BAPPEDA dan dinas-dinas teknis, namun belum terintegrasi dalam satu platform yang dapat di-harvest oleh sistem nasional. Selain itu, sebagian besar antarmuka pengelolaan data yang tersedia (termasuk admin bawaan GeoNode) memiliki kurva pembelajaran yang tinggi bagi staf pengelola data kabupaten, sehingga diperlukan panel admin khusus yang lebih ergonomis untuk operasional CRUD harian.

3\. Tujuan dan Sasaran Produk
=============================

3.1 Tujuan Umum
---------------

Membangun aplikasi web DST Kabupaten Luwu di atas platform GeoNode yang menyediakan repositori terstruktur untuk dokumen kebijakan dan data spasial terkait ILM, serta dapat dipanen secara otomatis oleh DST Nasional FOLUR.

3.2 Tujuan Spesifik
-------------------

*   Menyediakan repositori terpusat untuk dokumen kebijakan di Kabupaten Luwu yang relevan dengan ILM (tata ruang, lingkungan/kehutanan, pembangunan, komoditas kakao dan padi).
*   Menyediakan repositori terpusat untuk data spasial di Kabupaten Luwu (penggunaan lahan, HCV/HCS, komoditas, restorasi, batas administrasi, dan layer tata ruang lainnya) dengan metadata yang patuh standar SNI ISO 19115.
*   Menyediakan halaman landing page publik yang berfungsi sebagai etalase informasi program FOLUR di Kabupaten Luwu dan portal akses publik atas data yang dipublikasikan.
*   Menyediakan panel admin custom yang menyederhanakan workflow pengelolaan data (CRUD) bagi staf pengelola data kabupaten, dengan tetap memanfaatkan GeoNode sebagai backbone penyimpanan dan publikasi data.
*   Menyediakan endpoint API standar untuk harvesting data oleh DST Nasional, mencakup metadata katalog (CSW), layer spasial (OGC WMS/WFS), dan metadata dokumen kebijakan (REST).
*   Memastikan kepatuhan terhadap kebijakan One Data Indonesia dan One Map Policy.

3.3 Sasaran Pengukuran
----------------------

Keberhasilan produk diukur dengan indikator berikut, untuk dievaluasi pada akhir periode implementasi dan masa pemeliharaan:

**No.**

**Indikator Sasaran**

**Target Minimum**

1

Dokumen kebijakan yang ter-katalog dan ter-publish

Minimum 30 dokumen kebijakan kabupaten yang relevan dengan ILM

2

Layer spasial yang ter-katalog dan ter-publish

Minimum 20 layer spasial tematik terkait ILM Kabupaten Luwu

3

Endpoint harvesting yang dapat diakses DST Nasional

100% endpoint (CSW, WMS, WFS, REST dokumen) berfungsi & ter-dokumentasi

4

Staf kabupaten yang mampu mengoperasikan admin panel

Minimum 10 staf BAPPEDA & dinas terkait lulus Training of Trainers

5

Uptime layanan selama periode pemeliharaan

Minimum 95% uptime selama 6 bulan masa maintenance

6

Kepatuhan metadata terhadap SNI ISO 19115

100% layer dan dokumen memiliki metadata wajib lengkap

4\. Pemangku Kepentingan dan Pengguna
=====================================

4.1 Pemangku Kepentingan Utama
------------------------------

*   **Pemilik Produk:** Pemerintah Kabupaten Luwu, dengan BAPPEDA sebagai walidata utama.
*   **Penyandang Dana / Pengarah Program:** UNDP Indonesia, melalui Program FOLUR Indonesia.
*   **Pengguna Sistem Nasional:** DST Nasional FOLUR (dikoordinasikan oleh CMEA bersama BAPPENAS, KLHK, Kementan, ATR/BPN) yang melakukan harvesting data.
*   **Penyedia Data Sektoral:** Dinas Pertanian, Dinas Lingkungan Hidup, Dinas PUPR/Tata Ruang, Dinas Kehutanan, dan dinas terkait di Kabupaten Luwu.
*   **Pengguna Publik:** Masyarakat umum, peneliti, akademisi, dan mitra pembangunan yang membutuhkan akses data terbuka.

4.2 Peran Pengguna dan Hak Akses
--------------------------------

**Role Pengguna**

**Deskripsi**

**Hak Akses**

**Pengunjung (Public)**

Masyarakat umum, peneliti, mitra pembangunan

Read-only pada landing page; download data dan dokumen yang ditandai publik

**Kontributor Data**

Staf dinas teknis yang mengunggah data sektornya

Create & Update terhadap data milik sendiri; tidak dapat publish

**Admin Data Kabupaten**

Staf BAPPEDA selaku walidata

Full CRUD via admin panel custom; berwenang menerbitkan (publish) data

**Super Admin**

Pengelola sistem (administrator teknis)

Full access termasuk konfigurasi GeoNode, manajemen pengguna, dan log sistem

**Sistem DST Nasional**

Aplikasi otomatis di tingkat nasional

Read-only via API key/OAuth pada endpoint harvesting

5\. Ruang Lingkup Produk
========================

5.1 Cakupan (In-Scope)
----------------------

DST Kabupaten Luwu mencakup ruang lingkup berikut, dengan prinsip dasar sebagai data hub dan bukan analytical engine:

*   **Manajemen Dokumen Kebijakan:** pengunggahan, pengelolaan metadata, kategorisasi, versioning, dan publikasi dokumen kebijakan kabupaten.
*   **Manajemen Data Spasial:** pengunggahan layer vektor dan raster, pengelolaan metadata SNI ISO 19115, simbologi, dan publikasi sebagai layanan OGC.
*   **Landing Page Publik:** halaman beranda kustom yang menampilkan profil FOLUR Luwu, statistik data, peta interaktif unggulan, dokumen terbaru, dan tautan ke katalog GeoNode.
*   **Panel Admin Custom:** antarmuka pengelolaan data yang disederhanakan dan terhubung ke GeoNode melalui API, ditujukan untuk staf walidata.
*   **Endpoint Harvesting:** API publik (dengan otentikasi) untuk konsumsi DST Nasional, mencakup CSW, WMS, WFS, dan REST.
*   **Manajemen Pengguna dan Hak Akses:** berbasis pada modul auth bawaan GeoNode/Django.
*   **Pencatatan Aktivitas (Audit Log):** untuk operasi CRUD pada data.
*   **Dokumentasi:** manual instalasi, manual pengguna, dan dokumentasi API.

5.2 Di Luar Cakupan (Out-of-Scope)
----------------------------------

Untuk menjaga konsistensi metodologi penilaian lintas yurisdiksi serta sesuai pembagian peran pada Output 1.4 FOLUR, fitur-fitur berikut SECARA TEGAS TIDAK DIBANGUN pada DST Kabupaten Luwu, melainkan akan tersedia pada DST Nasional:

*   **Policy Screening Tool:** modul untuk menyaring dan mengklasifikasi kebijakan berdasarkan kategori (general requirements, subject matter, criminal provisions, transitional provisions, closing).
*   **Scorecard System:** matriks penilaian integrasi kebijakan dengan skala +3 hingga −3 (Indivisible, Reinforcing, Enabling, Consistent, Constraining, Counteracting, Cancelling).
*   **Annual Monitoring Report:** laporan tahunan integrasi kebijakan untuk konsumsi publik dan pemerintah.
*   **Sistem Rekomendasi:** perumusan rekomendasi tindak lanjut kebijakan, identifikasi gap regulasi, dan area regulasi yang perlu diperkuat atau direvisi.
*   **Scenario Planning lanjutan:** simulasi skenario tata ruang dan land use yang bersifat lintas sektor strategis.
*   **Analitik Multi-Yurisdiksi:** perbandingan antar kabupaten target FOLUR.

**Catatan arsitektur:** Semua fitur di atas tetap memerlukan data otoritatif yang dipasok oleh kabupaten. DST Kabupaten Luwu memenuhi kebutuhan tersebut melalui mekanisme harvesting, sehingga DST Nasional dapat memanfaatkan data Luwu beserta empat kabupaten target lainnya (Central Aceh, Mandailing Natal, Sanggau, Sorong) untuk analisis terpadu.

5.3 Asumsi
----------

*   Instance GeoNode versi stabil (4.x atau yang setara) telah tersedia atau akan disediakan pada VPS Kabupaten Luwu.
*   VPS memenuhi spesifikasi minimum sebagaimana tercantum pada TOR (CPU 8 core, RAM 24 GB, Storage 100 GB NVMe, IP Publik dedicated).
*   DST Nasional akan menyediakan spesifikasi formal endpoint dan skema metadata yang dapat diterima untuk harvesting.
*   BAPPEDA Luwu menyediakan tim walidata yang akan terlibat sejak fase asesmen hingga ToT.

5.4 Batasan
-----------

*   Anggaran dan timeline mengikuti deliverables yang ditetapkan dalam TOR.
*   Aplikasi di-deploy on-premise pada server kabupaten (data center kabupaten / situation room), bukan cloud-managed service.
*   Sistem harus tetap berfungsi dengan koneksi internet di tingkat kabupaten yang berpotensi terbatas; akses publik tetap bergantung pada kapasitas jaringan.

6\. Arsitektur Sistem
=====================

6.1 Posisi DST Kabupaten Luwu dalam Ekosistem FOLUR
---------------------------------------------------

Berikut adalah skema konseptual aliran data dari kabupaten ke nasional. DST Kabupaten Luwu, bersama empat DST kabupaten target lainnya, bertindak sebagai node penyedia data yang dipanen oleh DST Nasional. DST Nasional kemudian melakukan policy screening, scoring, reporting, dan formulasi rekomendasi atas seluruh data yang dihimpun.

\[DST Kab. Luwu\]  \[DST Kab. C. Aceh\]  \[DST Kab. Madina\]  \[DST Kab. Sanggau\]  \[DST Kab. Sorong\]

│           │              │              │              │

└───────────┴──────────────┼──────────────┴──────────────┘

**▼  (Harvesting: CSW / WMS / WFS / REST)**

**\[ DST NASIONAL — Screening, Scorecard, Annual Report, Recommendation \]**

▼

_Portal One Data Indonesia & One Map Policy_

6.2 Arsitektur Tingkat Sistem (Logical Architecture)
----------------------------------------------------

DST Kabupaten Luwu disusun dalam empat lapisan logis berikut:

### 6.2.1 Lapisan Penyajian (Presentation Layer)

*   **Landing Page Publik:** frontend kustom (HTML/JS atau framework modern) yang menyajikan profil program, statistik agregat, peta interaktif unggulan, dan navigasi ke katalog GeoNode.
*   **Halaman GeoNode Native:** halaman katalog (layer, dokumen, peta, GeoStory) bawaan GeoNode untuk eksplorasi data yang lebih mendalam, dengan tema visual yang diselaraskan dengan landing page.
*   **Panel Admin Custom:** SPA (Single Page Application) terpisah yang dirancang untuk produktivitas tinggi staf walidata, mengakses GeoNode melalui REST API.

### 6.2.2 Lapisan Aplikasi (Application Layer)

*   **GeoNode Core:** kerangka Django yang menyediakan manajemen layer, dokumen, peta, pengguna, dan permission.
*   **Custom Backend Service:** service tambahan (sebagai Django app atau microservice terpisah) yang memuat logika khusus DST Luwu, misal field metadata FOLUR-specific dan endpoint harvesting yang disesuaikan dengan spesifikasi DST Nasional.
*   **Authentication & Authorization:** memanfaatkan sistem auth Django/GeoNode, dengan ekstensi role-based access control sesuai kebutuhan walidata.

### 6.2.3 Lapisan Layanan Geospasial (Geospatial Services Layer)

*   **GeoServer:** publikasi data spasial sebagai layanan OGC standar (WMS, WFS, WCS, WMTS).
*   **CSW (Catalog Service for the Web):** katalog metadata terbuka untuk discovery, mengikuti standar ISO 19139.
*   **pycsw / GeoNetwork:** mesin katalog bawaan GeoNode.

### 6.2.4 Lapisan Data (Data Layer)

*   **PostgreSQL + PostGIS:** penyimpanan data tabular dan geometri.
*   **File Storage:** penyimpanan file dokumen (PDF, DOCX) dan raster (GeoTIFF) pada filesystem VPS.
*   **ElasticSearch (opsional):** indeks pencarian full-text untuk dokumen dan metadata.

6.3 Pemisahan Frontend Kustom dari GeoNode Bawaan
-------------------------------------------------

Strategi kustomisasi dijalankan dengan menghormati struktur upstream GeoNode untuk menjaga maintainability dan kemampuan upgrade di masa depan:

*   Landing page dan panel admin custom dibangun sebagai aplikasi terpisah (decoupled frontend) yang berkomunikasi dengan GeoNode melalui REST API resmi.
*   Tema GeoNode bawaan (template Django) hanya dikustomisasi seperlunya untuk konsistensi warna, logo, dan navigasi top-level.
*   Tidak melakukan fork mendalam terhadap GeoNode core; semua kustomisasi diletakkan pada Django app terpisah (sebagai contributed app).
*   Routing direncanakan sebagai berikut: domain root (/) → landing page; /catalogue/ → GeoNode native; /admin-panel/ → panel admin custom; /api/ → REST endpoints; /geoserver/ → GeoServer; /catalogue/csw → CSW endpoint.

7\. Persyaratan Fungsional
==========================

7.1 Landing Page Publik
-----------------------

### 7.1.1 Tujuan

Menyediakan etalase publik yang ringkas, informatif, dan memandu pengunjung pada data dan dokumen yang dipublikasikan.

### 7.1.2 Komponen Halaman

*   **Hero Section:** judul program, deskripsi singkat FOLUR Luwu, foto bentang lahan kabupaten, dan call-to-action menuju katalog data.
*   **Statistik Singkat:** jumlah dokumen kebijakan, jumlah layer spasial, jumlah kategori data — bersumber otomatis dari GeoNode API.
*   **Peta Interaktif Unggulan:** embed peta GeoNode/GeoStory yang menampilkan layer-layer pilihan (mis. zona kakao, area HCV, batas administrasi).
*   **Showcase Dokumen Terbaru:** 5–10 dokumen kebijakan terbaru atau pilihan dengan tautan ke detail.
*   **Bagian Tentang Program:** ringkasan FOLUR Indonesia, ILM, dan posisi Kabupaten Luwu.
*   **Tautan ke Mitra:** UNDP, BAPPEDA Luwu, dan instansi terkait.
*   **Footer:** kontak, kebijakan privasi, kredit, dan tautan login admin.

### 7.1.3 Persyaratan Teknis Landing Page

*   Responsif untuk perangkat desktop, tablet, dan mobile.
*   Memuat konten dinamis (statistik, dokumen terbaru) melalui pemanggilan REST API GeoNode.
*   Mendukung dua bahasa (Bahasa Indonesia & English) — Bahasa Indonesia sebagai default.
*   Memiliki tautan akses (Login) yang mengarahkan ke panel admin custom.

7.2 Panel Admin Custom (Frontend Pengelolaan Data)
--------------------------------------------------

### 7.2.1 Tujuan

Menyediakan antarmuka khusus bagi staf walidata kabupaten untuk mengelola dokumen kebijakan dan data spasial dengan workflow yang lebih sederhana dibandingkan admin Django/GeoNode bawaan.

### 7.2.2 Modul Panel Admin

1.  **Dashboard Pengelolaan**

*   Ringkasan: total dokumen, total layer, status publikasi (draft / published), aktivitas terbaru.
*   Notifikasi: data yang memerlukan tinjauan, metadata yang tidak lengkap, layer yang gagal publish.

1.  **Manajemen Dokumen Kebijakan**

*   Daftar dokumen dengan filter (kategori sektor, tahun, instansi, status publikasi).
*   Form input baru dengan validasi field wajib (judul, jenis regulasi, tahun, instansi penerbit, sektor, ringkasan, file).
*   Upload file dokumen (PDF, DOCX) dengan progress indicator dan pemindaian dasar (ukuran, jenis file).
*   Tagging berdasarkan tema (land use, kehutanan/lingkungan, tata ruang, pembangunan, komoditas kakao, komoditas padi, dll.).
*   Versioning: setiap perubahan dokumen tercatat sebagai versi baru dengan referensi ke versi sebelumnya.
*   Workflow status: Draft → Review → Published → Archived.
*   Bulk action: publish/unpublish massal.

1.  **Manajemen Data Spasial**

*   Daftar layer dengan filter (kategori tema, format, status, projeksi).
*   Upload layer vektor (Shapefile, GeoPackage, GeoJSON) dan raster (GeoTIFF) dengan validasi otomatis.
*   Form metadata SNI ISO 19115 dengan field wajib yang ter-validasi (judul, abstrak, kategori tema, pemilik data, tanggal akuisisi, sistem koordinat, skala, lisensi).
*   Preview thumbnail layer dan extent geografis sebelum publikasi.
*   Pengaturan simbologi dasar (SLD) untuk visualisasi peta.
*   Indikator status publikasi ke GeoServer dan CSW.

1.  **Manajemen Pengguna dan Role**

*   Daftar pengguna, penambahan/pengubahan, penetapan role.
*   Reset password, penonaktifan akun, audit aktivitas pengguna.

1.  **Log Aktivitas (Audit Trail)**

*   Pencatatan setiap operasi CRUD pada data dengan informasi pelaku, waktu, jenis aksi, dan obyek yang terdampak.
*   Penyaringan log berdasarkan pengguna, jenis aksi, dan rentang waktu.

1.  **Pengaturan Sistem**

*   Konfigurasi metadata default (kabupaten, walidata, kontak).
*   Pengaturan endpoint harvesting (API key untuk DST Nasional).

### 7.2.3 Persyaratan Teknis Panel Admin

*   Berkomunikasi dengan GeoNode melalui REST API resmi (GeoNode API v2).
*   Autentikasi terintegrasi dengan akun GeoNode (single sign-on).
*   Validasi sisi klien (real-time) dan sisi server (sebelum commit ke GeoNode).
*   Mendukung operasi offline parsial: penyimpanan draft di sisi klien sebelum dikirim ke server.

7.3 Integrasi dengan GeoNode Backend
------------------------------------

*   Seluruh data persisten disimpan dan dipublikasikan melalui GeoNode (tidak ada duplikasi penyimpanan data utama di panel admin custom).
*   Panel admin custom tidak menyimpan data otoritatif sendiri; ia hanya menyajikan ulang dan memodifikasi data via API.
*   Kustomisasi GeoNode dibatasi pada: branding (logo, warna, judul situs), penambahan field metadata khusus FOLUR, dan integrasi modul harvest yang sesuai dengan spesifikasi DST Nasional.

7.4 Mekanisme Harvesting oleh DST Nasional
------------------------------------------

### 7.4.1 Endpoint yang Disediakan

**Jenis Endpoint**

**Protokol / Standar**

**Konten yang Dipanen**

**Katalog Metadata**

OGC CSW 2.0.2 / ISO 19139

Metadata seluruh layer dan dokumen yang ber-status published

**Layer Vektor**

OGC WFS 2.0 (GeoJSON, GML)

Geometri dan atribut layer vektor (mis. zona komoditas, batas)

**Layer Raster**

OGC WMS 1.3.0 / WCS 2.0

Layer raster (mis. tutupan lahan, HCV/HCS)

**Dokumen Kebijakan**

REST API JSON + tautan unduh

Metadata dokumen kebijakan dan URL unduh file

**Delta (Sinkronisasi)**

REST API dengan parameter timestamp

Daftar data yang berubah sejak harvest sebelumnya

### 7.4.2 Otentikasi dan Otorisasi Harvesting

*   DST Nasional memperoleh kredensial khusus berupa API key atau OAuth 2.0 client credentials.
*   Endpoint harvesting bersifat read-only dan terbatas pada data yang ber-status published.
*   Logging setiap akses harvesting (siapa, kapan, endpoint apa, parameter).

### 7.4.3 Frekuensi Harvesting

*   Direkomendasikan: harvesting terjadwal harian oleh DST Nasional, dengan opsi on-demand.
*   Mendukung pola incremental harvesting melalui parameter timestamp untuk efisiensi bandwidth.

### 7.4.4 Skema Metadata

*   Metadata patuh terhadap SNI ISO 19115:2014 (untuk data spasial).
*   Metadata dokumen mengikuti skema Dublin Core yang diperluas dengan field FOLUR-specific (sektor, komoditas terkait, jenis regulasi).
*   Field wajib pada metadata mengacu pada profil metadata One Data Indonesia.

7.5 Manajemen Pengguna dan Hak Akses
------------------------------------

*   Sistem role: Pengunjung (anonim), Kontributor, Admin Walidata, Super Admin.
*   Permission berlapis: read (semua data published), write (data milik sendiri), publish (admin walidata), administrasi sistem (super admin).
*   Audit trail untuk setiap perubahan permission.

8\. Persyaratan Non-Fungsional
==============================

8.1 Performa
------------

*   Landing page dimuat sempurna (Time-to-Interactive) dalam ≤ 3 detik pada koneksi 10 Mbps.
*   Panel admin: respon CRUD < 2 detik untuk operasi standar (di luar upload file besar).
*   Endpoint harvesting: paging dengan ukuran default 100 record, mendukung sampai 1.000 record per request.
*   Sistem mampu melayani minimal 50 pengguna konkuren pada landing page dan 10 pengguna konkuren di panel admin.

8.2 Keamanan
------------

*   HTTPS wajib pada seluruh endpoint produksi (termasuk subdomain GeoServer).
*   Password disimpan dengan hashing modern (argon2 atau bcrypt).
*   CSRF dan XSS protection bawaan Django/GeoNode dipertahankan; tidak dimatikan.
*   Rate limiting pada endpoint API publik untuk mitigasi abuse.
*   Backup harian database dan file storage, dengan retensi minimum 30 hari.
*   API key untuk DST Nasional di-rotasi secara berkala (rekomendasi: setiap 6 bulan).

8.3 Interoperabilitas
---------------------

*   Patuh terhadap kebijakan One Data Indonesia (https://data.go.id) dalam hal skema metadata dan publikasi.
*   Patuh terhadap One Map Policy (Perpres 27/2014 dan turunannya) dalam hal sistem referensi koordinat dan struktur peta dasar.
*   Menyediakan layanan OGC standar (WMS, WFS, CSW) yang dapat dikonsumsi aplikasi pihak ketiga (mis. QGIS, ArcGIS).
*   Format pertukaran data: GeoJSON, GeoPackage, Shapefile, GeoTIFF; metadata ISO 19139 XML dan JSON-LD.

8.4 Skalabilitas
----------------

*   Arsitektur memungkinkan penambahan node aplikasi (horizontal scaling) di belakang reverse proxy.
*   PostgreSQL dapat dipisahkan ke server database tersendiri ketika beban meningkat.
*   Storage layer mendukung migrasi ke object storage (S3-compatible) apabila ke depan diperlukan.

8.5 Ketersediaan
----------------

*   Target uptime ≥ 95% selama masa pemeliharaan.
*   Maintenance window terjadwal pada jam non-produktif (mis. malam hari, akhir pekan).

8.6 Pemeliharaan dan Keterbacaan Kode
-------------------------------------

*   Kode sumber mengikuti konvensi Python/Django (PEP 8) dan style guide frontend yang ditetapkan.
*   Setiap modul kustomisasi terdokumentasi (docstring, README per modul).
*   Repositori kode dipelihara dengan version control (Git) dan branching strategy yang jelas.

8.7 Aksesibilitas
-----------------

*   Landing page memenuhi WCAG 2.1 level AA untuk komponen kunci.
*   Bahasa antarmuka utama: Bahasa Indonesia. Bahasa Inggris disediakan untuk halaman landing publik.

8.8 Lokalisasi Konten
---------------------

*   Sistem referensi koordinat default: WGS 84 / EPSG:4326; UTM Zone 51S untuk konteks lokal Luwu.
*   Format tanggal: DD/MM/YYYY (Indonesia).

9\. Spesifikasi Teknis
======================

9.1 Stack Teknologi
-------------------

**Lapisan**

**Komponen**

**Backend CMS**

GeoNode 4.x (Django), Python 3.10+

**Database**

PostgreSQL 14+ dengan ekstensi PostGIS 3.x

**Map Server**

GeoServer 2.23+ (Java 11+)

**Katalog Metadata**

pycsw (bundled GeoNode)

**Pencarian**

ElasticSearch (opsional, bundled GeoNode)

**Frontend Landing**

HTML5/CSS3/JS modern; opsi framework: React/Vue/Astro

**Frontend Admin Panel**

Single Page Application (React / Vue + komponen UI library)

**Reverse Proxy**

Nginx

**Containerization**

Docker & Docker Compose (opsional sesuai kondisi server kabupaten)

**Sistem Operasi Server**

Ubuntu Server LTS atau distro Linux setara

9.2 Spesifikasi Infrastruktur VPS
---------------------------------

Mengacu pada TOR pengembangan DST, spesifikasi VPS yang menampung DST Kabupaten Luwu adalah:

**Komponen**

**Minimum**

**Direkomendasikan**

**CPU**

8 Core

**12 Core**

**RAM**

24 GB

**48 GB**

**Storage**

100 GB NVMe

**500 GB NVMe**

**Bandwidth**

100 Mbps

**Unlimited**

**IP Publik**

Dedicated

**Dedicated**

**Root Access**

Full

**Full**

**Sistem Operasi**

Linux / Windows

**Linux**

9.3 Domain dan Routing
----------------------

*   Direkomendasikan: dst-luwu.\[domain-pemkab\].go.id atau folur-luwu.\[domain-pemkab\].go.id.
*   Subdomain: geoserver.dst-luwu... untuk layanan OGC; api.dst-luwu... untuk REST endpoint.
*   Sertifikat TLS dari Let's Encrypt atau penyedia institusional.

9.4 Pencadangan dan Pemulihan
-----------------------------

*   Backup database harian (full) dan transaction log per jam.
*   Backup file media mingguan.
*   Retensi minimum 30 hari untuk daily backup, 12 minggu untuk weekly backup.
*   Uji pemulihan (restore drill) dilakukan minimal sekali selama masa pemeliharaan.

10\. Model Data
===============

10.1 Entitas Utama
------------------

Sistem mengelola dua entitas utama, ditambah entitas pendukung untuk metadata, pengguna, dan kategori.

### 10.1.1 Entitas: Dokumen Kebijakan

**Field**

**Tipe**

**Wajib**

**Keterangan**

id

UUID

Ya

Identifier unik

title

String (255)

Ya

Judul resmi dokumen

regulation\_type

Enum

Ya

Perda, Perbup, SK Bupati, Peraturan Desa, dst.

issuing\_year

Integer

Ya

Tahun penerbitan

issuing\_authority

String

Ya

Instansi penerbit (BAPPEDA Luwu, Dinas LH, dst.)

sector

Multi-select

Ya

Land use, kehutanan/lingkungan, tata ruang, pembangunan, kakao, padi, dll.

abstract

Text

Ya

Ringkasan dokumen

file

File (PDF/DOCX)

Ya

File dokumen utama

status

Enum

Ya

Draft / Review / Published / Archived

version

Integer

Ya

Nomor versi, auto-increment

supersedes\_id

UUID (FK)

Tidak

Referensi ke dokumen yang digantikan

tags

Array<String>

Tidak

Kata kunci tambahan

created\_at / updated\_at

Timestamp

Ya

Untuk incremental harvesting

language

ISO 639-1

Ya

Default: id

license

String

Ya

Lisensi dokumen (mis. CC BY 4.0)

### 10.1.2 Entitas: Layer Spasial

**Field**

**Tipe**

**Wajib**

**Keterangan**

id

UUID

Ya

Identifier unik

title

String

Ya

Judul layer

abstract

Text

Ya

Deskripsi layer

data\_format

Enum

Ya

Vector / Raster

theme\_category

Multi-select

Ya

Tutupan lahan, HCV, HCS, komoditas, restorasi, batas administrasi, dll.

crs

String (EPSG)

Ya

Mis. EPSG:4326, EPSG:32751

scale\_denominator

Integer

Ya

Skala terkecil dan terbesar

bbox

Geometry

Ya

Bounding box geografis

acquisition\_date

Date

Ya

Tanggal akuisisi data

data\_source

String

Ya

Sumber data (instansi/citra)

data\_owner

String

Ya

Walidata instansi

lineage

Text

Disarankan

Riwayat & metodologi

status

Enum

Ya

Draft / Review / Published / Archived

style\_sld

File (SLD)

Tidak

Simbologi

license

String

Ya

Lisensi penggunaan data

created\_at / updated\_at

Timestamp

Ya

Untuk incremental harvesting

10.2 Kategori Tematik Layer Spasial (untuk Konteks Luwu)
--------------------------------------------------------

*   Tutupan lahan dan penggunaan lahan (land use / land cover).
*   Kawasan HCV dan HCS.
*   Zona perkebunan kakao (smallholder dan korporasi).
*   Zona sawah / lahan padi.
*   Area restorasi dan rehabilitasi lahan.
*   Tata ruang: pola ruang RTRW Kabupaten Luwu, struktur ruang.
*   Ekosistem esensial dan habitat keanekaragaman hayati.
*   Batas administrasi (kabupaten, kecamatan, desa).
*   Jaringan infrastruktur (jalan, sungai, jaringan irigasi).
*   Data dasar: topografi, hidrologi, geologi.

10.3 Kategori Sektor Dokumen Kebijakan
--------------------------------------

*   Tata ruang dan perencanaan wilayah (RTRW, RDTR, rencana detail tematik).
*   Lingkungan hidup dan kehutanan (perlindungan ekosistem, KLHS, izin lingkungan).
*   Pertanian dan komoditas (kakao, padi, kebijakan pupuk, sertifikasi keberlanjutan).
*   Pembangunan daerah (RPJMD, Renstra OPD, Rencana Aksi Daerah).
*   Penataan agraria dan pertanahan.
*   Restorasi lahan dan rehabilitasi DAS.

11\. Integrasi dengan DST Nasional
==================================

11.1 Pola Integrasi
-------------------

Pola integrasi yang dipilih adalah pull-based harvesting, di mana DST Nasional secara periodik melakukan permintaan ke endpoint DST Kabupaten Luwu untuk mengambil metadata dan data terbaru. Pola ini dipilih karena: (1) kabupaten tetap menjadi pemilik dan kontrol penuh atas datanya; (2) tidak diperlukan pemicu push dari kabupaten ke pusat yang dapat membebani sumber daya kabupaten; (3) sinkron dengan kebiasaan operasional pengumpulan data lintas walidata di Indonesia.

11.2 Tahapan Harvesting
-----------------------

**Tahap 1 — Discovery:** DST Nasional memanggil endpoint CSW (GetCapabilities, GetRecords) untuk memperoleh daftar resource terkini.

**Tahap 2 — Metadata Retrieval:** DST Nasional memanggil GetRecordById untuk metadata lengkap setiap resource.

**Tahap 3 — Data Access:** DST Nasional mengakses layer melalui WMS/WFS/WCS dan dokumen melalui URL unduh, sesuai informasi yang termuat dalam metadata.

**Tahap 4 — Sinkronisasi Inkremental:** Pada siklus berikutnya, DST Nasional hanya memanggil resource dengan updated\_at lebih baru dari harvest sebelumnya.

11.3 Kontrak API Ringkas
------------------------

Spesifikasi API lengkap akan diuraikan dalam dokumen API Specification terpisah dan akan disepakati bersama tim DST Nasional. Berikut adalah gambaran high-level kontrak API:

**Endpoint (Pattern)**

**Metode**

**Deskripsi**

/catalogue/csw

GET/POST

OGC CSW endpoint (GetCapabilities, GetRecords, GetRecordById)

/geoserver/wms

GET

OGC WMS untuk layer raster dan vektor (display)

/geoserver/wfs

GET/POST

OGC WFS untuk akses fitur vektor (GeoJSON/GML)

/api/v1/documents

GET

Daftar dokumen kebijakan dengan filter dan paging

/api/v1/documents/{id}

GET

Detail metadata dokumen + URL unduh file

/api/v1/layers

GET

Daftar layer dengan metadata ringkas

/api/v1/sync/changes

GET

Daftar perubahan sejak parameter timestamp (since)

11.4 Format Pertukaran
----------------------

*   Metadata: ISO 19139 (XML) dan JSON-LD.
*   Data vektor: GeoJSON, GML 3.2, GeoPackage (untuk unduhan).
*   Data raster: GeoTIFF (untuk unduhan) dan tile WMS/WMTS (untuk display).
*   Dokumen: PDF / DOCX dengan metadata terpisah.

11.5 Tata Kelola Perubahan API
------------------------------

*   Setiap perubahan kontrak API yang bersifat breaking dikomunikasikan ke DST Nasional minimum 30 hari sebelum penerapan.
*   Versi API menggunakan prefiks /api/v1 dan seterusnya.
*   Deprecation policy: versi lama tetap berfungsi minimum 6 bulan sejak rilis versi baru.

12\. Alur Pengguna Utama
========================

12.1 Alur: Publikasi Dokumen Kebijakan oleh Walidata
----------------------------------------------------

*   Walidata login ke panel admin custom.
*   Memilih menu Dokumen Kebijakan → Tambah Baru.
*   Mengisi form metadata (judul, jenis, tahun, instansi, sektor, abstrak, dll).
*   Mengunggah file PDF/DOCX.
*   Menyimpan sebagai draft (status: Draft).
*   Admin Walidata meninjau, lalu mengubah status menjadi Published.
*   Sistem menulis metadata ke katalog GeoNode (CSW).
*   Pada siklus harvesting berikutnya, DST Nasional mengambil metadata dan file.

12.2 Alur: Publikasi Layer Spasial oleh Walidata
------------------------------------------------

*   Walidata login ke panel admin custom.
*   Memilih menu Data Spasial → Unggah Baru.
*   Mengunggah file Shapefile/GeoPackage/GeoTIFF; sistem mendeteksi format dan CRS.
*   Mengisi metadata wajib (judul, abstrak, kategori, sumber, walidata, dll).
*   Sistem mempublikasi layer ke GeoServer dan metadata ke CSW.
*   Admin Walidata mengubah status menjadi Published.
*   Pada siklus harvesting berikutnya, DST Nasional dapat mengakses layer melalui WMS/WFS.

12.3 Alur: Akses Publik melalui Landing Page
--------------------------------------------

*   Pengunjung membuka halaman landing.
*   Melihat statistik program dan peta interaktif unggulan.
*   Menelusuri dokumen terbaru atau lanjut ke katalog GeoNode.
*   Mengunduh dokumen / data dengan lisensi yang berlaku.

12.4 Alur: Harvesting oleh DST Nasional
---------------------------------------

*   DST Nasional mengautentikasi dengan API key.
*   Mengambil daftar perubahan via /api/v1/sync/changes?since=...
*   Untuk setiap perubahan, memanggil metadata lengkap dan/atau mengakses data via WMS/WFS/REST.
*   Menyimpan replika atau referensi sesuai kebijakan internal DST Nasional.

13\. Kriteria Penerimaan (Acceptance Criteria)
==============================================

Produk dianggap diterima ketika seluruh kriteria berikut terpenuhi:

13.1 Kriteria Fungsional
------------------------

*   Landing page publik dapat diakses dengan konten dinamis yang ter-update dari GeoNode.
*   Panel admin custom dapat melakukan CRUD penuh untuk dokumen kebijakan dan layer spasial.
*   Sistem mendukung minimum 30 dokumen kebijakan dan 20 layer spasial sebagai konten awal.
*   Endpoint CSW, WMS, WFS, dan REST dapat diakses dan diuji dari klien standar (mis. QGIS untuk OGC, Postman untuk REST).
*   DST Nasional (atau simulator harvesting) berhasil mengambil metadata dan data melalui endpoint yang disediakan.
*   Workflow status (Draft → Review → Published → Archived) berfungsi sesuai spesifikasi.
*   Audit log mencatat seluruh operasi CRUD dengan benar.

13.2 Kriteria Non-Fungsional
----------------------------

*   Landing page mencapai Lighthouse score ≥ 80 (Performance) pada perangkat desktop.
*   Operasi CRUD panel admin standar selesai dalam < 2 detik (di luar upload file besar).
*   HTTPS aktif pada seluruh endpoint produksi.
*   Backup harian terkonfigurasi dan terverifikasi melalui uji restore minimum sekali.

13.3 Kriteria Dokumentasi dan Pelatihan
---------------------------------------

*   Manual instalasi (technical doc) tersedia dan diverifikasi melalui instalasi ulang di lingkungan staging.
*   Manual pengguna (user manual) tersedia dalam Bahasa Indonesia.
*   Dokumentasi API tersedia dan dapat dipakai oleh tim DST Nasional.
*   Minimum 2 sesi training (sesuai TOR: 2 kali, 20 orang/event) terlaksana di Kabupaten Luwu.
*   Minimum 10 staf BAPPEDA & dinas terkait lulus ToT (Training of Trainers).

13.4 Kriteria Pemeliharaan
--------------------------

*   Selama 6 bulan masa pemeliharaan: ketersediaan layanan ≥ 95%, respon perbaikan bug kritis ≤ 24 jam, perbaikan bug non-kritis ≤ 7 hari.

14\. Tahapan dan Jadwal
=======================

Jadwal mengikuti struktur deliverable yang ditetapkan dalam TOR:

**Deliverable**

**Lingkup Aktivitas**

**% Pembayaran**

**Estimasi Periode**

**D1 — Inception**

Metodologi dan rencana kerja

Asesmen sistem dan data existing di Luwu

Stakeholder mapping & ringkasan FGD

Gap analysis kebutuhan ILM vs sistem existing

Arsitektur akhir dan rencana kustomisasi

**20%**

Bulan 1–2

**D2 — Development Progress**

Progress modul inti (GeoNode customization)

Progress landing page

Progress panel admin custom

Dokumentasi konsultasi stakeholder

Demo prototype / beta

Pembaruan timeline dan mitigasi risiko

**30%**

Bulan 3–5

**D3 — Final Deployment**

DST Kab. Luwu ter-deploy & operasional

Hasil testing & validasi

ToT dan knowledge transfer

Source code lengkap

Installation & user manual

Verifikasi interoperabilitas dengan DST Nasional

**40%**

Bulan 6–7

**D4 — Maintenance**

6 bulan masa pemeliharaan

Penanganan bug & permintaan dukungan

Laporan akhir maintenance

**10%**

Bulan 8–13

15\. Risiko dan Mitigasi
========================

**Risiko**

**Tingkat**

**Mitigasi**

Spesifikasi harvesting dari DST Nasional belum final pada saat pengembangan

**Tinggi**

Adopsi protokol standar (CSW/WMS/WFS/REST) sebagai dasar; sediakan adapter layer untuk perubahan minor; koordinasi periodik dengan tim DST Nasional

Kapasitas teknis staf walidata yang variatif

Menengah

Panel admin custom dirancang sederhana (UX-first); ToT intensif; user manual berbahasa Indonesia; helpdesk selama maintenance

Kualitas metadata data lama (legacy) tidak lengkap

Menengah

Workshop metadata bersama walidata di awal proyek; validator metadata pada panel admin; template metadata default

Keterbatasan bandwidth/koneksi VPS kabupaten

Menengah

Optimasi tile caching; harvesting incremental; kompresi response; deployment file besar via CDN bila perlu

Kustomisasi GeoNode mempersulit upgrade upstream

Menengah

Letakkan kustomisasi pada Django app terpisah; minimasi fork core; dokumentasi perubahan; ikuti pola GeoNode contributed apps

Tumpang tindih kewenangan walidata antar OPD

Menengah

FGD penetapan walidata di awal proyek; SK Bupati / Surat Edaran terkait pengelolaan data DST; matriks RACI yang jelas

Resistensi adopsi karena perubahan workflow

Rendah-Menengah

Pelibatan walidata sejak fase asesmen; ToT bertahap; champion users di tiap OPD

Insiden keamanan (kebocoran/serangan)

Rendah

HTTPS, hardening server, rate limiting, audit log, prosedur incident response, backup terjadwal

16\. Apendiks
=============

16.1 Glosarium
--------------

*   **DST:** Decision Support Tool — perangkat lunak pendukung pengambilan keputusan.
*   **FOLUR:** Food Systems, Land Use and Restoration — program global yang didukung GEF dan diimplementasikan UNDP di Indonesia.
*   **ILM:** Integrated Landscape Management — pendekatan pengelolaan bentang lahan terpadu.
*   **HCV:** High Conservation Value — kawasan bernilai konservasi tinggi.
*   **HCS:** High Carbon Stock — kawasan stok karbon tinggi.
*   **GeoNode:** Platform open source CMS geospasial berbasis Django.
*   **CSW:** Catalog Service for the Web — standar OGC untuk katalog metadata.
*   **WMS / WFS / WCS:** Web Map / Feature / Coverage Service — standar layanan geospasial OGC.
*   **Walidata:** Instansi yang berwenang mengelola data tematik tertentu (UU 39/2019, Perpres 39/2019 tentang Satu Data Indonesia).
*   **ToT:** Training of Trainers — pelatihan untuk calon fasilitator/pelatih internal.

16.2 Referensi
--------------

*   Terms of Reference: Development of Decision Support Tools (DST) Web Application for Food Systems, Land Use and Restoration at District Level (5 Districts), UNDP Indonesia.
*   Project Document FOLUR Indonesia — Output 1.4: Decision Support Tool for Informing Policy Formulation and Planning.
*   Perpres 39 Tahun 2019 tentang Satu Data Indonesia.
*   Perpres 27 Tahun 2014 tentang Pelaksanaan Kebijakan Satu Peta (One Map Policy) dan turunannya.
*   SNI ISO 19115:2014 — Informasi Geografis — Metadata.
*   Dokumentasi GeoNode: https://docs.geonode.org/.
*   Portal Satu Data Indonesia: https://data.go.id/.
*   Nilsson M., Griggs D., Visbeck M. (2016) — Scorecard matrix yang diadopsi DST Nasional.

16.3 Catatan Pembagian Tanggung Jawab antara DST Kabupaten dan DST Nasional
---------------------------------------------------------------------------

**Fungsi / Modul**

**DST Kab. Luwu**

**DST Nasional**

Pengelolaan data spasial otoritatif kabupaten

**✔ Penyedia**

—

Pengelolaan dokumen kebijakan kabupaten

**✔ Penyedia**

—

Publikasi katalog (CSW, WMS, WFS)

**✔ Penyedia**

Konsumen

Policy Screening (general req., subject matter, dll.)

—

**✔ Pelaksana**

Scorecard System (+3 s.d. −3)

—

**✔ Pelaksana**

Annual Monitoring Report integrasi kebijakan

—

**✔ Pelaksana**

Formulasi rekomendasi & gap regulasi

—

**✔ Pelaksana**

Analisis lintas yurisdiksi 5 kabupaten target

—

**✔ Pelaksana**

Pelaporan untuk konsumsi publik nasional

—

**✔ Pelaksana**

_— Akhir Dokumen —_


**✔ TAMBAHAN**

Teks literal keterangan muncul di:

webgis.html
baris sekitar 2312: 'pola_ruang': 'keterangan'
baris sekitar 2318: const cands = ['nama_unsur', 'namobj', 'nama', 'name', 'keterangan', 'kelas', ...]


  // Override atribut kategori per-layer (key: alternate atau nama tanpa workspace)
  const LAYER_LABEL_ATTR = {
    'pola_ruang': 'keterangan',   // Pola Ruang dikelompokkan berdasarkan KETERANGAN
    'rawan_bencana': 'krb_03',    // Rawan Bencana dikelompokkan berdasarkan krb_03
    'jalan': 'fungsi_ren',        // Jalan dikelompokkan berdasarkan fungsi_ren (butuh WFS aktif)
  };
