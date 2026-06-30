# Asisten AI DST FOLUR

DST FOLUR dilengkapi dengan **Asisten AI Kebijakan (Policy Intelligence Assistant)** yang dirancang untuk membantu pengguna dalam menganalisis, menilai, membandingkan, dan mengharmonisasikan kebijakan sektor lahan, pangan, lingkungan, kehutanan, perkebunan, tata ruang, dan pembangunan berkelanjutan.

Melalui antarmuka percakapan yang intuitif, pengguna dapat mengajukan pertanyaan, mengunggah dokumen kebijakan, meminta analisis kesesuaian terhadap prinsip Integrated Landscape Management (ILM), serta memperoleh rekomendasi berbasis bukti untuk mendukung pengambilan keputusan.

Asisten AI mampu membaca dan memahami berbagai dokumen regulasi, melakukan screening otomatis, mengidentifikasi potensi sinergi dan benturan kebijakan, serta menghasilkan analisis dan visualisasi yang mendukung perencanaan pembangunan lanskap berkelanjutan.

---

# 1. Konfigurasi AI

DST FOLUR tidak menggunakan model AI bawaan. Sistem terhubung dengan berbagai penyedia model AI melalui API sehingga organisasi dapat memilih model yang paling sesuai dengan kebutuhan, kapasitas, dan kebijakan keamanan data mereka.

Penyedia yang didukung meliputi:

* [OpenAI](https://platform.openai.com?utm_source=chatgpt.com)
* [Google Gemini](https://ai.google.dev?utm_source=chatgpt.com)
* [Anthropic Claude](https://www.anthropic.com?utm_source=chatgpt.com)
* [OpenRouter](https://openrouter.ai?utm_source=chatgpt.com)
* [Ollama](https://ollama.com?utm_source=chatgpt.com) untuk model lokal
* [llama.cpp](https://github.com/ggerganov/llama.cpp?utm_source=chatgpt.com) untuk model lokal

Pengguna dapat mengonfigurasi beberapa model sekaligus dan memilih model yang paling sesuai untuk tugas tertentu seperti:

* Analisis regulasi
* Screening kebijakan
* Ringkasan dokumen
* Harmonisasi kebijakan
* Penyusunan policy brief
* Analisis konflik dan sinergi
* Pembuatan rekomendasi

**Catatan**

Kunci API dan konfigurasi model disimpan secara aman pada lingkungan DST FOLUR dan tidak dibagikan kepada pihak lain.

---

# 2. Kemampuan Asisten AI

## Analisis Dokumen Kebijakan

Pengguna dapat mengunggah:

* Undang-Undang
* Peraturan Pemerintah
* Peraturan Presiden
* Peraturan Menteri
* Peraturan Daerah
* RPJMN
* RPJMD
* RTRW
* KLHS
* Dokumen perencanaan lainnya

AI akan secara otomatis:

* Mengekstrak isi dokumen
* Mengidentifikasi sektor terkait
* Mengelompokkan tema kebijakan
* Menemukan pasal yang relevan
* Menyusun ringkasan eksekutif

---

## Screening Kesesuaian terhadap ILM

AI dapat menilai tingkat kesesuaian kebijakan terhadap indikator ILM yang telah ditetapkan.

Contoh pertanyaan:

> "Seberapa kuat Perda RTRW ini mendukung konservasi hutan dan ketahanan pangan?"

Hasil analisis dapat berupa:

| Indikator ILM    | Skor |
| ---------------- | ---- |
| Konservasi Hutan | 85   |
| Ketahanan Pangan | 78   |
| Biodiversitas    | 91   |
| Tata Kelola      | 74   |

Beserta penjelasan dan dasar penilaiannya.

---

## Analisis Sinergi dan Benturan Kebijakan

AI dapat membandingkan dua atau lebih regulasi dan mengidentifikasi hubungan antar kebijakan menggunakan Skala Interaksi Nilsson.

| Nilai | Interpretasi        |
| ----- | ------------------- |
| -3    | Sangat bertentangan |
| -2    | Bertentangan        |
| -1    | Kurang mendukung    |
| 0     | Netral              |
| 1     | Cukup mendukung     |
| 2     | Mendukung           |
| 3     | Sangat mendukung    |

Asisten akan menjelaskan:

* Pasal yang saling mendukung
* Pasal yang saling bertentangan
* Dampak terhadap implementasi ILM
* Peluang harmonisasi

---

## Identifikasi Simpul Kritis dan Simpul Penggerak

AI secara otomatis dapat mengidentifikasi:

### Simpul Kritis

Kebijakan yang paling banyak menciptakan hambatan atau konflik terhadap tujuan pembangunan berkelanjutan.

### Simpul Penggerak

Kebijakan yang memiliki pengaruh terbesar dalam mendukung integrasi sektor lahan, pangan, dan lingkungan.

---

## Rekomendasi Harmonisasi Kebijakan

AI dapat memberikan rekomendasi seperti:

* Pasal yang perlu direvisi
* Area tumpang tindih regulasi
* Potensi penyelarasan lintas sektor
* Opsi harmonisasi kebijakan

Contoh:

> "Bagaimana mengurangi konflik antara RTRW dan kebijakan perlindungan gambut?"

---

## Penyusunan Policy Brief

AI dapat membantu menghasilkan:

* Ringkasan kebijakan
* Executive summary
* Policy brief
* Analisis kesenjangan kebijakan
* Rekomendasi strategis

---

# 3. Interaksi dengan Asisten

Pengguna cukup berkomunikasi menggunakan bahasa alami.

Contoh perintah:

* "Ringkas dokumen ini dalam 10 poin utama."
* "Bandingkan Perda RTRW dengan KLHS."
* "Identifikasi kebijakan yang mendukung agroforestri."
* "Cari konflik antara kebijakan perkebunan dan konservasi."
* "Buat policy brief tentang ketahanan pangan berkelanjutan."
* "Apa saja simpul kritis dalam lanskap regulasi Kabupaten Luwu?"

---

# 4. Analitik dan Visualisasi

Asisten AI dapat menghasilkan berbagai visualisasi analitis, antara lain:

* Scorecard kepatuhan ILM
* Heatmap konflik kebijakan
* Matriks Interaksi Nilsson
* Peta sinergi kebijakan
* Jaringan keterkaitan regulasi
* Grafik simpul kritis dan penggerak
* Dashboard indikator ILM

---

# 5. Manajemen Konteks dan Basis Pengetahuan

Asisten AI memanfaatkan:

* Basis data regulasi
* Dokumen proyek FOLUR
* Indikator ILM
* Hasil screening terdahulu
* Knowledge Graph kebijakan

Semakin lengkap basis pengetahuan yang tersedia, semakin akurat dan konsisten hasil analisis yang dihasilkan.

---

# 6. Potensi Penggunaan

DST FOLUR dengan Asisten AI dapat dimanfaatkan oleh:

* Kementerian dan lembaga pemerintah
* Pemerintah daerah
* Tim FOLUR
* Peneliti
* Akademisi
* Organisasi pembangunan
* Mitra pembangunan internasional
* Masyarakat umum

untuk mendukung **pengambilan keputusan berbasis bukti, harmonisasi regulasi, dan penguatan tata kelola lanskap berkelanjutan**.

---

Menurut saya, untuk DST FOLUR, istilah **"Asisten AI"** sebaiknya diganti menjadi **"Asisten Intelijen Kebijakan (Policy Intelligence Assistant)"** karena lebih mencerminkan fungsi strategis sistem dalam melakukan analisis, harmonisasi, dan pengambilan keputusan kebijakan lintas sektor.
