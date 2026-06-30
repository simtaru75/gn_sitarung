# -*- coding: utf-8 -*-
"""(Re)seed tabel crosswalk permanen ``RefKodeBps`` (kode BPS <-> Kemendagri/PUM)
dari berkas di ``seed_data/``:

* provinsi   -> konstanta ``PROVINSI`` di modul ini (38 baris)
* kabkota    -> ``kode_bps_kabkota.csv``   (514, + kolom file_logo)
* kecamatan  -> ``kode_bps_kecamatan.csv`` (~7.285)
* desa       -> ``kode_bps_desa.csv``       (~83.723)

Sumber data nasional kec/desa: dataset bridging BPS Wilkerstat + Kemendagri
(https://github.com/SalzBytes/wilayah_indonesia, basis BPS H1-2025 & Kemendagri
2025), turunan dari https://sig.bps.go.id/bridging-kode/. Provinsi & kabkota
sudah diverifikasi 100% cocok dengan dataset itu.

Provinsi/kabkota di-upsert (idempotent, menjaga file_logo). Kecamatan & desa
berjumlah besar -> dimuat hapus-lalu-``bulk_create`` per jenjang. Jalankan ulang
tiap CSV diperbarui::

    manage.py load_kode_bps
    manage.py load_kode_bps --prune   # hapus baris kabkota yang tak ada lagi di CSV
"""
import csv
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# .../management/commands/load_kode_bps.py -> .../geonode_project
_PKG = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CSV_PATH = os.path.join(_PKG, "seed_data", "kode_bps_kabkota.csv")
KEC_CSV_PATH = os.path.join(_PKG, "seed_data", "kode_bps_kecamatan.csv")
DESA_CSV_PATH = os.path.join(_PKG, "seed_data", "kode_bps_desa.csv")

# Provinsi (kode_pum Kemendagri, kode_bps BPS Wilkerstat, nama). Untuk 32 provinsi
# non-Papua keduanya identik; provinsi Papua hasil pemekaran 2022 BERBEDA
# (Kemendagri 91-96 vs BPS 91/92/94/95/96/97).
PROVINSI = [
    ("11", "11", "Aceh"), ("12", "12", "Sumatera Utara"),
    ("13", "13", "Sumatera Barat"), ("14", "14", "Riau"), ("15", "15", "Jambi"),
    ("16", "16", "Sumatera Selatan"), ("17", "17", "Bengkulu"),
    ("18", "18", "Lampung"), ("19", "19", "Kepulauan Bangka Belitung"),
    ("21", "21", "Kepulauan Riau"), ("31", "31", "DKI Jakarta"),
    ("32", "32", "Jawa Barat"), ("33", "33", "Jawa Tengah"),
    ("34", "34", "Daerah Istimewa Yogyakarta"), ("35", "35", "Jawa Timur"),
    ("36", "36", "Banten"), ("51", "51", "Bali"),
    ("52", "52", "Nusa Tenggara Barat"), ("53", "53", "Nusa Tenggara Timur"),
    ("61", "61", "Kalimantan Barat"), ("62", "62", "Kalimantan Tengah"),
    ("63", "63", "Kalimantan Selatan"), ("64", "64", "Kalimantan Timur"),
    ("65", "65", "Kalimantan Utara"), ("71", "71", "Sulawesi Utara"),
    ("72", "72", "Sulawesi Tengah"), ("73", "73", "Sulawesi Selatan"),
    ("74", "74", "Sulawesi Tenggara"), ("75", "75", "Gorontalo"),
    ("76", "76", "Sulawesi Barat"), ("81", "81", "Maluku"),
    ("82", "82", "Maluku Utara"),
    ("91", "94", "Papua"), ("92", "91", "Papua Barat"),
    ("93", "95", "Papua Selatan"), ("94", "96", "Papua Tengah"),
    ("95", "97", "Papua Pegunungan"), ("96", "92", "Papua Barat Daya"),
]


def load_rows(path=CSV_PATH):
    """Baca CSV -> list dict {kode_pum, kode_bps, nama}. Lewati baris tak lengkap."""
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pum = (r.get("kode_pum") or "").strip()
            bps = (r.get("kode_bps") or "").strip()
            if pum and bps:
                rows.append({
                    "kode_pum": pum, "kode_bps": bps,
                    "nama": (r.get("nama") or "").strip(),
                    "file_logo": (r.get("file_logo") or "").strip(),
                })
    return rows


class Command(BaseCommand):
    help = "(Re)seed RefKodeBps (crosswalk Kemendagri<->BPS) dari CSV."

    def add_arguments(self, parser):
        parser.add_argument("--prune", action="store_true",
                            help="Hapus baris kabkota yang tak ada di CSV.")

    @staticmethod
    def _bulk_level(model, level, path):
        """Muat satu jenjang besar (kec/desa) dengan hapus-lalu-bulk_create.

        Dedupe defensif per kode_pum (keep-first): data sumber kadang memetakan
        satu kode Kemendagri ke >1 kode BPS (kesalahan bridging); baris pertama
        yang menang (kode sah mendahului duplikat keliru pada dump sumber).
        """
        if not os.path.exists(path):
            return 0
        seen, objs = set(), []
        for r in load_rows(path):
            pum = r["kode_pum"]
            if pum in seen:
                continue
            seen.add(pum)
            objs.append(model(level=level, kode_pum=pum, kode_bps=r["kode_bps"],
                              nama=r["nama"], file_logo=""))
        with transaction.atomic():
            model.objects.filter(level=level).delete()
            model.objects.bulk_create(objs, batch_size=2000)
        return len(objs)

    def handle(self, *args, **opts):
        from geonode_project.models import RefKodeBps

        if not os.path.exists(CSV_PATH):
            raise CommandError(f"CSV tidak ada: {CSV_PATH}")
        # Provinsi (statis).
        for pum, bps, nama in PROVINSI:
            RefKodeBps.objects.update_or_create(
                level="provinsi", kode_pum=pum,
                defaults={"kode_bps": bps, "nama": nama, "file_logo": ""},
            )

        rows = load_rows()
        created = updated = 0
        seen = set()
        for r in rows:
            seen.add(r["kode_pum"])
            _, was_created = RefKodeBps.objects.update_or_create(
                level="kabkota", kode_pum=r["kode_pum"],
                defaults={"kode_bps": r["kode_bps"], "nama": r["nama"],
                          "file_logo": r["file_logo"]},
            )
            created += int(was_created)
            updated += int(not was_created)

        pruned = 0
        if opts["prune"]:
            qs = RefKodeBps.objects.filter(level="kabkota").exclude(kode_pum__in=seen)
            pruned = qs.count()
            qs.delete()

        # Kecamatan & desa: dataset nasional (~7.285 + ~83.723 baris unik setelah
        # buang NULL & dedupe, sumber SalzBytes/wilayah_indonesia = BPS Wilkerstat
        # + Kemendagri). Karena jumlahnya besar & merupakan data referensi statis,
        # dimuat dengan hapus-lalu-bulk_create per jenjang (atomik) — jauh lebih
        # cepat daripada update_or_create per baris. file_logo selalu "" di sini.
        n_kec = self._bulk_level(RefKodeBps, "kecamatan", KEC_CSV_PATH)
        n_desa = self._bulk_level(RefKodeBps, "desa", DESA_CSV_PATH)

        self.stdout.write(self.style.SUCCESS(
            f"RefKodeBps kabkota: baru={created} diperbarui={updated} "
            f"dihapus={pruned} total={RefKodeBps.objects.filter(level='kabkota').count()}"))
        self.stdout.write(self.style.SUCCESS(
            f"RefKodeBps kecamatan: dimuat={n_kec} "
            f"total={RefKodeBps.objects.filter(level='kecamatan').count()}"))
        self.stdout.write(self.style.SUCCESS(
            f"RefKodeBps desa: dimuat={n_desa} "
            f"total={RefKodeBps.objects.filter(level='desa').count()}"))
        self.stdout.write(
            f"RefKodeBps provinsi: total={RefKodeBps.objects.filter(level='provinsi').count()}")
