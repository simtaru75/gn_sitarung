# -*- coding: utf-8 -*-
"""Relabel berkas logo seed kabupaten: kode BPS -> kode KEMENDAGRI.

Berkas di ``seed_data/logo_kab/`` dinamai ``kab-h250px-<kode>.<ext>`` memakai
**kode BPS**, sedangkan runtime mencari logo default berdasarkan **kode
KEMENDAGRI** (``KDPKAB`` BIG = ``cakupan_kode_kab``). Untuk banyak kabupaten kode
BPS != Kemendagri (lihat tabel jembatan resmi BPS:
https://sig.bps.go.id/bridging-kode/index), bahkan saat himpunan kodenya sama
(permutasi) — sehingga logo bisa tampil untuk kabupaten yang salah.

Command ini memakai crosswalk ``seed_data/logo_code_map.csv`` (kolom
``bps,pum,nama``; ``pum`` boleh ditulis bertitik ``xx.xx``) sebagai sumber
otoritatif lalu merename berkas agar memakai kode Kemendagri. Tiap target
divalidasi ke daftar Kemendagri BIG (kode + nama) supaya salah-peta ketahuan.

Idempotensi via **marker** ``seed_data/logo_code_map.applied.csv`` (mencatat
pasangan bps->pum yang sudah diterapkan). Ini wajib karena remap resmi sering
membentuk **siklus murni** (nama berkas tak berubah, hanya isinya) yang tak bisa
dideteksi dari nama berkas saja. Rename dilakukan **dua fase** (lewat nama
temporer) supaya aman terhadap siklus/tukar-kode.

Pemakaian::

    manage.py relabel_seed_logos             # dry-run + validasi BIG
    manage.py relabel_seed_logos --apply     # eksekusi rename + catat ke marker
    manage.py relabel_seed_logos --no-validate
"""
import csv
import os
import re

from django.core.management.base import BaseCommand, CommandError

# .../geonode_project/management/commands/relabel_seed_logos.py -> .../geonode_project
_PKG = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SEED_KAB = os.path.join(_PKG, "seed_data", "logo_kab")
SEED_PROV = os.path.join(_PKG, "seed_data", "logo_prov")
CSV_PATH = os.path.join(_PKG, "seed_data", "logo_code_map.csv")
APPLIED_PATH = os.path.join(_PKG, "seed_data", "logo_code_map.applied.csv")

KAB_RE = re.compile(r"^(kab-h250px-)(\d+)(\.[A-Za-z0-9]+)$")
PROV_RE = re.compile(r"^(prov-250-)(\d+)(\.[A-Za-z0-9]+)$")
TMP_SUFFIX = ".tmp-relabel"


def _digits(s):
    """Buang non-digit. Kode di CSV boleh bertitik (``14.72``); nama berkas
    tetap digit saja (``1472``) sesuai lookup runtime."""
    return re.sub(r"\D", "", s or "")


def _norm_name(s):
    s = (s or "").lower().strip()
    for pre in ("kabupaten ", "kab. ", "kab ", "kota ", "kepulauan "):
        if s.startswith(pre):
            s = s[len(pre):]
    return re.sub(r"[^a-z0-9]+", "", s)


class Command(BaseCommand):
    help = "Relabel berkas logo seed kabupaten via crosswalk BPS -> KEMENDAGRI."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Eksekusi rename + catat ke marker (default: dry-run).")
        parser.add_argument("--no-validate", action="store_true",
                            help="Lewati validasi ke BIG (offline).")

    def _load_crosswalk(self):
        if not os.path.exists(CSV_PATH):
            raise CommandError(f"Crosswalk tidak ada: {CSV_PATH}")
        rows = []
        with open(CSV_PATH, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                bps, pum = (r.get("bps") or "").strip(), (r.get("pum") or "").strip()
                if bps and pum:
                    rows.append({"bps": bps, "pum": pum, "nama": (r.get("nama") or "").strip()})
        return rows

    def _load_applied(self):
        s = set()
        if os.path.exists(APPLIED_PATH):
            with open(APPLIED_PATH, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    b, p = _digits(r.get("bps", "")), _digits(r.get("pum", ""))
                    if b and p:
                        s.add((b, p))
        return s

    def _append_applied(self, pairs):
        new = not os.path.exists(APPLIED_PATH)
        with open(APPLIED_PATH, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["bps", "pum"])
            for b, p in pairs:
                w.writerow([b, p])

    def handle(self, *args, **opts):
        apply = opts["apply"]
        rows = self._load_crosswalk()
        applied = self._load_applied()

        big = {}
        if not opts["no_validate"]:
            from .sync_wilayah_big import fetch_kab_pum_map
            self.stdout.write("Memvalidasi target ke daftar Kemendagri BIG ...")
            try:
                big = fetch_kab_pum_map()
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(
                    f"Validasi BIG gagal ({exc}). Lanjut tanpa validasi."))

        # Validasi tiap baris crosswalk.
        for r in rows:
            pd = _digits(r["pum"])
            if big and pd not in big:
                self.stdout.write(self.style.ERROR(
                    f"  INVALID: pum {r['pum']} (dari bps {r['bps']}) bukan kode Kemendagri BIG"))
            elif big and r["nama"] and _norm_name(r["nama"]) != _norm_name(big.get(pd, "")):
                self.stdout.write(self.style.WARNING(
                    f"  CEK NAMA: bps {r['bps']} -> {r['pum']} : CSV='{r['nama']}' vs BIG='{big.get(pd)}'"))

        # Baris "pending": non-identitas & belum tercatat di marker.
        pending = {}
        n_identity = n_done = 0
        for r in rows:
            b, p = _digits(r["bps"]), _digits(r["pum"])
            if b == p:
                n_identity += 1
            elif (b, p) in applied:
                n_done += 1
            else:
                pending[b] = p

        if not os.path.isdir(SEED_KAB):
            raise CommandError(f"Folder tidak ada: {SEED_KAB}")
        files = sorted(os.listdir(SEED_KAB))
        existing = set(files)
        big_set = set(big)

        plans = []
        n_untouched = n_noncrosswalk_bps = 0
        for fn in files:
            m = KAB_RE.match(fn)
            if not m:
                continue
            prefix, code, ext = m.group(1), m.group(2), m.group(3)
            if code in pending:
                plans.append((fn, f"{prefix}{pending[code]}{ext}"))
            else:
                n_untouched += 1
                if big and code not in big_set:
                    n_noncrosswalk_bps += 1  # kode bukan Kemendagri & tak ada di crosswalk

        # Tabrakan target (yang bukan bagian dari rotasi).
        srcs = {s for s, _ in plans}
        dst_count = {}
        for _, d in plans:
            dst_count[d] = dst_count.get(d, 0) + 1
        safe, collisions = [], []
        for s, d in plans:
            if dst_count[d] > 1:
                collisions.append((s, d, "target ganda"))
            elif d in existing and d not in srcs:
                collisions.append((s, d, "target sudah ada (bukan bagian rotasi)"))
            else:
                safe.append((s, d))

        if apply and safe:
            staged = []
            for s, d in safe:
                tp = os.path.join(SEED_KAB, s + TMP_SUFFIX)
                os.rename(os.path.join(SEED_KAB, s), tp)
                staged.append((tp, os.path.join(SEED_KAB, d)))
            for tp, dp in staged:
                os.rename(tp, dp)
            self._append_applied(
                (KAB_RE.match(s).group(2), KAB_RE.match(d).group(2)) for s, d in safe)

        # Laporan.
        self.stdout.write("")
        verb = "RENAMED" if apply else "rename"
        for s, d in safe:
            tcode = KAB_RE.match(d).group(2)
            tn = f" ({big[tcode]})" if big.get(tcode) else ""
            self.stdout.write(f"  {verb}: {s} -> {d}{tn}")
        for s, d, why in collisions:
            self.stdout.write(self.style.ERROR(f"  COLLISION ({why}): {s} -> {d} [DILEWATI]"))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Kab: rename={len(safe)} sudah-diterapkan={n_done} identitas={n_identity} "
            f"tak-diubah={n_untouched} (di antaranya kode-non-Kemendagri={n_noncrosswalk_bps}) "
            f"collision={len(collisions)}"))

        self._verify_provinsi()
        if not apply:
            self.stdout.write(self.style.WARNING(
                "\nDRY-RUN — belum ada berkas diubah. Tambah --apply untuk eksekusi."))

    def _verify_provinsi(self):
        if not os.path.isdir(SEED_PROV):
            return
        try:
            from .sync_wilayah_big import fetch_provinsi_options
            prov_set = {p["kode"] for p in fetch_provinsi_options()}
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.WARNING(
                f"Provinsi: verifikasi dilewati (gagal ambil KDPPUM: {exc})."))
            return
        unknown = [fn for fn in sorted(os.listdir(SEED_PROV))
                   if PROV_RE.match(fn) and PROV_RE.match(fn).group(2) not in prov_set]
        if unknown:
            self.stdout.write(self.style.WARNING(
                f"Provinsi: {len(unknown)} berkas kodenya tak ada di KDPPUM: {', '.join(unknown)}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Provinsi: semua kode cocok dengan KDPPUM."))
