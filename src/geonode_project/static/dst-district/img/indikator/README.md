# Ikon Indikator Strategis

Letakkan berkas **PNG** ikon indikator di folder ini. Nama berkas harus sama
persis dengan nilai field **Ikon** pada tiap indikator di
**Panel Admin → Pengaturan Sistem → Indikator Strategis**.

Disarankan PNG transparan, kira-kira persegi (mis. 256×256), karena dirender
dalam kotak ±92×92 px dengan `object-fit: contain`.

## Berkas yang dipakai data awal (seed)

| Indikator                      | Nama berkas                  |
|--------------------------------|------------------------------|
| Indeks Pembangunan Manusia     | `indikator-strategis-1.png`  |
| Pertumbuhan Ekonomi            | `indikator-strategis-2.png`  |
| PDRB Per Kapita                | `indikator-strategis-3.png`  |
| Tingkat Kemiskinan             | `indikator-strategis-4.png`  |
| Tingkat Pengangguran Terbuka   | `indikator-strategis-5.png`  |
| Gini Ratio                     | `indikator-strategis-6.png`  |
| Inflasi                        | `indikator-strategis-7.png`  |

Bila sebuah indikator tidak punya berkas ikon yang cocok, kartu tetap tampil
tanpa ikon (judul, nilai, dan deskripsi saja). Untuk menambah indikator baru
dengan ikon lain, taruh PNG-nya di sini lalu isi nama berkasnya pada field Ikon.

> Setelah menambah berkas, jalankan `python manage.py collectstatic` (di
> lingkungan produksi) agar ikon ikut terkumpul ke `STATIC_ROOT`.
