# -*- coding: utf-8 -*-
"""Sinkronisasi batas wilayah administrasi (provinsi -> desa) dari BIG.

Menarik poligon batas administrasi resmi Badan Informasi Geospasial (BIG)
melalui layanan ArcGIS REST publik, lalu meng-*upsert* ke tabel referensi
PostGIS (``RefWilayah*``). Idempoten: menjalankan ulang akan memperbarui baris
yang berubah dan menambah yang baru, dikunci pada kode PUM/Kemendagri.

Strategi: server BIG menolak (500/timeout) query geometri ber-skala nasional
(``where=1=1``), tetapi andal untuk query per-provinsi. Maka penarikan
dilakukan **per provinsi** (``KDPPUM='<kode>'``), tetap dengan paginasi
``resultOffset`` di dalam tiap provinsi.

Contoh::

    python manage.py sync_wilayah_big --level kab
    python manage.py sync_wilayah_big --level desa --provinsi 11
    python manage.py sync_wilayah_big --level all

Untuk melihat animasi progress realtime, jalankan di terminal interaktif
(``docker compose exec django ...`` tanpa flag ``-T``).

Catatan:
- Level ``prov`` dibangun via *dissolve* (ST_Union) dari Kabupaten/Kota, jadi
  level ``kab`` harus sudah tersinkron lebih dulu.
- Sumber data (c) Badan Informasi Geospasial (BIG) -- geoservices.big.go.id
"""
import itertools
import json
import re
import sys
import threading
import time

import requests
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from geonode_project.models import (
    RefKodeBps,
    RefWilayahDesa,
    RefWilayahKabkota,
    RefWilayahKecamatan,
    RefWilayahProvinsi,
)

# Layanan all-in-one publik BIG (skema RBI batas wilayah, ArcGIS 10.81).
# Layer 0 = Kab/Kota, 1 = Kecamatan, 2 = Kelurahan/Desa.
BASE_URL = (
    "https://geoservices.big.go.id/gis/rest/services/"
    "BAPANAS/Batas_Administrasi/MapServer"
)

# Pemetaan kolom model <- field atribut BIG, per jenjang yang ditarik via REST.
LEVELS = {
    "kab": {
        "model": RefWilayahKabkota,
        "layer": 0,
        "order_by": "KDPKAB",
        "fields": {
            "kode_pum": "KDPKAB",
            "kode_bps": "KDBBPS",
            "nama": "WADMKK",
            "kode_prov_pum": "KDPPUM",
            "nama_prov": "WADMPR",
            "luas_ha": "LUASWH",
        },
    },
    "kec": {
        "model": RefWilayahKecamatan,
        "layer": 1,
        "order_by": "KDCPUM",
        "fields": {
            "kode_pum": "KDCPUM",
            "kode_bps": "KDCBPS",
            "nama": "WADMKC",
            "kode_kab_pum": "KDPKAB",
            "nama_kab": "WADMKK",
            "kode_prov_pum": "KDPPUM",
            "nama_prov": "WADMPR",
            "luas_ha": "LUASWH",
        },
    },
    "desa": {
        "model": RefWilayahDesa,
        "layer": 2,
        "order_by": "KDEPUM",
        "fields": {
            "kode_pum": "KDEPUM",
            "kode_bps": "KDEBPS",
            "nama": "WADMKD",
            "kode_kec_pum": "KDCPUM",
            "nama_kec": "WADMKC",
            "kode_kab_pum": "KDPKAB",
            "nama_kab": "WADMKK",
            "kode_prov_pum": "KDPPUM",
            "nama_prov": "WADMPR",
            "luas_ha": "LUASWH",
        },
    },
}


def _coords_2d(coords):
    """Potong tiap posisi koordinat ke [x, y] (buang Z/M), rekursif."""
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)):
        return coords[:2]
    return [_coords_2d(c) for c in coords]


def _to_multipolygon(geojson_geom):
    """GeoJSON -> GEOS MultiPolygon(4326) 2D, perbaiki geometri tak valid."""
    geom = dict(geojson_geom)
    geom["coordinates"] = _coords_2d(geom.get("coordinates"))
    g = GEOSGeometry(json.dumps(geom), srid=4326)
    if not g.valid:
        g = g.buffer(0)
    if g.geom_type == "Polygon":
        g = MultiPolygon(g, srid=4326)
    if g.geom_type != "MultiPolygon":
        raise ValueError(f"geometri bukan poligon: {g.geom_type}")
    if g.srid is None:
        g.srid = 4326
    return g


def _distinct_options(where, code_attr, name_attr, order_attr):
    """[{kode, nama}] hasil query distinct atribut BIG (tanpa geometri).

    Dipakai untuk mengisi dropdown UI 'Restore Data Wilayah' dengan kode PUM
    (agar cocok dengan filter pull). Memakai layer 0 (Kab/Kota) yang memuat
    semua kolom kode/nama jenjang.
    """
    url = f"{BASE_URL}/{LEVELS['kab']['layer']}/query"
    resp = requests.get(
        url,
        params={
            "where": where,
            "outFields": f"{code_attr},{name_attr}",
            "returnGeometry": "false",
            "returnDistinctValues": "true",
            "orderByFields": order_attr,
            "f": "json",
        },
        headers={"User-Agent": "DST-FOLUR/sync_wilayah_big"},
        timeout=60,
    )
    resp.raise_for_status()
    out, seen = [], set()
    for ft in (resp.json().get("features") or []):
        attrs = ft.get("attributes") or {}
        kode = (attrs.get(code_attr) or "").strip()
        nama = (attrs.get(name_attr) or "").strip()
        if kode and "/" not in kode and kode not in seen:
            seen.add(kode)
            out.append({"kode": kode, "nama": nama})
    return out


def fetch_provinsi_options():
    """Daftar provinsi [{kode, nama}] (kode PUM) untuk dropdown."""
    return _distinct_options("1=1", "KDPPUM", "WADMPR", "WADMPR")


def fetch_kabupaten_options(kode_prov):
    """Daftar kabupaten/kota [{kode, nama}] pada satu provinsi (kode PUM)."""
    return _distinct_options(f"KDPPUM='{kode_prov}'", "KDPKAB", "WADMKK", "WADMKK")


def fetch_kab_pum_map():
    """{kode_pum_4digit: nama} semua kab/kota dari BIG (``KDPKAB`` -> ``WADMKK``).

    Catatan: BIG TIDAK mengisi kode BPS (``KDBBPS``/``KDCBPS``/``KDEBPS`` kosong),
    jadi peta BPS->PUM tidak bisa ditarik dari BIG. Fungsi ini hanya menyediakan
    daftar kode PUM/Kemendagri (dinormalisasi ke 4 digit) + nama untuk
    memvalidasi crosswalk relabel logo. Paginasi via ``resultOffset`` karena
    distinct bisa terpotong.
    """
    import re as _re

    url = f"{BASE_URL}/{LEVELS['kab']['layer']}/query"
    out, off = {}, 0
    while True:
        resp = requests.get(
            url,
            params={
                "where": "1=1",
                "outFields": "KDPKAB,WADMKK",
                "returnGeometry": "false",
                "returnDistinctValues": "true",
                "orderByFields": "KDPKAB",
                "resultOffset": off,
                "resultRecordCount": 1000,
                "f": "json",
            },
            headers={"User-Agent": "DST-FOLUR/sync_wilayah_big"},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        feats = data.get("features") or []
        for ft in feats:
            attrs = ft.get("attributes") or {}
            kp = _re.sub(r"\D", "", str(attrs.get("KDPKAB") or ""))
            if len(kp) == 4:
                out[kp] = str(attrs.get("WADMKK") or "").strip()
        if not data.get("exceededTransferLimit") or not feats:
            break
        off += len(feats)
    return out


class _Progress:
    """Bar progress + spinner realtime; hanya animasi saat output ke TTY.

    Dipakai sebagai context manager. Spinner & jam dirender thread latar tiap
    0.1s sehingga tetap "hidup" selama menunggu request HTTP yang lambat,
    sedangkan bar terisi setiap kali ``update()`` dipanggil (per halaman).
    Bila stream bukan TTY (mis. dialihkan ke file/log), animasi dimatikan dan
    pemanggil mencetak baris status biasa.
    """

    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    BAR_W = 24

    def __init__(self, stream, label, total):
        self.stream = stream
        self.label = label
        self.total = int(total or 0)
        self.done = 0
        self.extra = ""
        self.start = time.time()
        self.enabled = bool(getattr(stream, "isatty", lambda: False)())
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thr = None
        self._lastlen = 0

    def __enter__(self):
        if self.enabled:
            self.stream.write("\033[?25l")  # sembunyikan kursor
            self.stream.flush()
            self._thr = threading.Thread(target=self._loop, daemon=True)
            self._thr.start()
        return self

    def update(self, done=None, extra=None):
        with self._lock:
            if done is not None:
                self.done = done
            if extra is not None:
                self.extra = extra

    def _compose(self, frame):
        with self._lock:
            done, total, extra = self.done, self.total, self.extra
        if total > 0:
            ratio = min(1.0, done / total)
            filled = int(ratio * self.BAR_W)
            bar = "█" * filled + "░" * (self.BAR_W - filled)
            meta = f"{done}/{total} ({ratio * 100:3.0f}%)"
        else:
            bar = "░" * self.BAR_W
            meta = f"{done}"
        el = int(time.time() - self.start)
        clock = f"{el // 60}:{el % 60:02d}"
        return f"{frame} {self.label:<5} [{bar}] {meta}  {extra}  {clock}"

    def _write(self, text):
        pad = " " * max(0, self._lastlen - len(text))
        self.stream.write("\r" + text + pad)
        self.stream.flush()
        self._lastlen = len(text)

    def _loop(self):
        frames = itertools.cycle(self.FRAMES)
        while not self._stop.is_set():
            self._write(self._compose(next(frames)))
            self._stop.wait(0.1)

    def __exit__(self, *exc):
        self._stop.set()
        if self._thr:
            self._thr.join(timeout=1)
        if self.enabled:
            self._write(self._compose("✓"))
            self.stream.write("\n\033[?25h")  # baris baru + tampilkan kursor
            self.stream.flush()


class Command(BaseCommand):
    help = "Sinkronkan batas wilayah administrasi (prov->desa) dari BIG ke PostGIS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--level",
            choices=["prov", "kab", "kec", "desa", "all"],
            default="all",
            help="Jenjang yang disinkron (default: all).",
        )
        parser.add_argument(
            "--provinsi",
            default=None,
            help="Batasi ke satu kode provinsi (mis. 11 = Aceh) untuk uji/chunking.",
        )
        parser.add_argument(
            "--kabupaten",
            default=None,
            help="Batasi ke satu kode PUM kabupaten/kota (mis. 52.04). Hanya kab/kec/desa.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="TRUNCATE tabel wilayah dulu agar schema hanya berisi region ini.",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=200,
            help=(
                "Fitur per halaman (default 200). Geometri penuh berat; halaman "
                "besar (mis. 1000) bisa timeout di server BIG. Maks efektif 1000."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hanya ambil 1 halaman & tampilkan ringkasan, tanpa menulis DB.",
        )

    # ------------------------------------------------------------------ #
    def handle(self, *args, **opts):
        level = opts["level"]
        self.prov = opts["provinsi"]
        self.kab = opts["kabupaten"]
        self.page_size = opts["page_size"]
        self.dry_run = opts["dry_run"]

        self.session = requests.Session()
        self.session.headers["User-Agent"] = "DST-FOLUR/sync_wilayah_big"

        # Crosswalk PUM->BPS: BIG tak mengisi kode BPS, jadi diisi dari tabel
        # referensi permanen RefKodeBps via join kode_pum (dinormalisasi ke digit).
        # Satu peta gabungan semua jenjang; panjang digit beda per jenjang
        # (kab=4, kec=6, desa=10) sehingga tak bertabrakan. Lihat models.RefKodeBps
        # & manage.py load_kode_bps.
        self._bps_map = {
            re.sub(r"\D", "", p): b
            for p, b in RefKodeBps.objects.values_list("kode_pum", "kode_bps")
        }

        if opts["replace"] and not self.dry_run:
            self._truncate_all()

        started = time.time()
        if level == "all":
            rest_levels = ["kab", "kec", "desa"]
            build_prov = True
        elif level == "prov":
            rest_levels = []
            build_prov = True
        else:
            rest_levels = [level]
            build_prov = False

        totals = {}
        for key in rest_levels:
            totals[key] = self._sync_rest_level(key)

        if build_prov and not self.dry_run:
            totals["prov"] = self._build_provinsi(self.prov)

        dur = time.time() - started
        self.stdout.write(self.style.SUCCESS(f"\nSelesai dalam {dur:.1f}s."))
        for k, v in totals.items():
            self.stdout.write(f"  {k:5} -> {v}")
        self.stdout.write(
            self.style.WARNING(
                "Sumber data (c) Badan Informasi Geospasial (BIG) - geoservices.big.go.id"
            )
        )

    # ------------------------------------------------------------------ #
    def _sync_rest_level(self, key):
        cfg = LEVELS[key]
        url = f"{BASE_URL}/{cfg['layer']}/query"
        out_fields = ",".join(cfg["fields"].values())
        code_field = cfg["fields"]["kode_pum"]
        name_field = cfg["fields"]["nama"]
        model = cfg["model"]

        base_params = {
            "outFields": out_fields,
            "returnGeometry": "true",
            "returnZ": "false",
            "returnM": "false",
            "outSR": 4326,
            "f": "geojson",
            "orderByFields": cfg["order_by"],
        }

        if self.dry_run:
            where = (
                f"KDPKAB='{self.kab}'" if self.kab
                else (f"KDPPUM='{self.prov}'" if self.prov else "1=1")
            )
            data = self._fetch(
                url,
                {**base_params, "where": where, "resultOffset": 0, "resultRecordCount": self.page_size},
            )
            feats = data.get("features") or []
            sample = (feats[0].get("properties") or {}) if feats else {}
            self.stdout.write(
                f"[dry-run] {key}: {len(feats)} fitur halaman pertama "
                f"(contoh: {sample.get(code_field)} / {sample.get(name_field)})"
            )
            return f"dry-run, {len(feats)} fitur halaman pertama"

        wheres, where_total = self._where_clauses(url)
        total = self._count(url, where_total)

        processed = inserted = updated = merged = skipped = 0
        # Kode yang sudah tampil pada run ini -> dipakai untuk menggabung
        # (union) fitur multipart, bukan menimpa.
        self._seen = set()
        with _Progress(sys.stdout, key, total) as bar:
            for where in wheres:
                offset = 0
                while True:
                    params = {
                        **base_params,
                        "where": where,
                        "resultOffset": offset,
                        "resultRecordCount": self.page_size,
                    }
                    data = self._fetch(url, params)
                    feats = data.get("features") or []
                    if not feats:
                        break

                    with transaction.atomic():
                        for ft in feats:
                            res = self._upsert_feature(model, cfg, ft, code_field)
                            if res == "created":
                                inserted += 1
                            elif res == "updated":
                                updated += 1
                            elif res == "merged":
                                merged += 1
                            else:
                                skipped += 1

                    n = len(feats)
                    offset += n
                    processed += n
                    bar.update(done=processed, extra=f"+{inserted} baru")
                    if not bar.enabled:
                        self.stdout.write(
                            f"  {key}: {processed}/{total or '?'} fitur "
                            f"(+{inserted} baru, ~{updated} update, {merged} merge, {skipped} skip)"
                        )
                    if n < self.page_size and not data.get("exceededTransferLimit"):
                        break

        return (
            f"{inserted} baru, {updated} update, {merged} merge multipart, "
            f"{skipped} skip (total {total})"
        )

    # ------------------------------------------------------------------ #
    def _upsert_feature(self, model, cfg, ft, code_field):
        """Upsert satu fitur GeoJSON -> baris model. Return created/updated/skip."""
        props = ft.get("properties") or {}
        geom_json = ft.get("geometry")
        # Lewati fitur non-unit-administrasi:
        #  - kode kosong/spasi  -> poligon badan air/danau/no-data
        #  - kode mengandung '/' -> segmen batas sengketa milik 2 unit
        #    (mis. KDEPUM '52.04.17.2003/52.07.06.2001'), bukan unit tunggal.
        code = (props.get(code_field) or "").strip()
        if not geom_json or not code or "/" in code:
            return "skip"
        try:
            geom = _to_multipolygon(geom_json)
        except Exception:
            return "skip"

        defaults = {"geom": geom}
        for dest, src in cfg["fields"].items():
            if dest == "kode_pum":
                continue
            val = props.get(src)
            if dest == "luas_ha":
                try:
                    val = float(val) if val not in (None, "") else None
                except (TypeError, ValueError):
                    val = None
            else:
                val = val.strip() if isinstance(val, str) else (val or "")
            defaults[dest] = val

        # kode_bps: NILAI DARI BIG SELALU MENANG. Saat ini BIG mengirim KDBBPS/
        # KDCBPS/KDEBPS kosong, sehingga kita isi dari crosswalk permanen
        # (RefKodeBps) untuk jenjang kab/kota, kecamatan, & desa (sejauh datanya
        # tersedia). Bila kelak BIG sudah mengisi kode BPS sendiri lewat API,
        # guard di bawah memastikan kita TIDAK menimpanya — crosswalk hanya
        # menambal yang kosong. Join kode_pum -> digit.
        if ("kode_bps" in defaults and not (defaults.get("kode_bps") or "").strip()):
            bps = getattr(self, "_bps_map", {}).get(re.sub(r"\D", "", code))
            if bps:
                defaults["kode_bps"] = bps

        # Multipart: fitur ke-2+ dengan kode sama pada run ini -> gabung (union)
        # geometrinya ke baris yang sudah ada, jangan ditimpa (agar pulau/bagian
        # terpisah tidak hilang).
        if code in self._seen:
            obj = model.objects.get(kode_pum=code)
            merged_geom = obj.geom.union(geom)
            if merged_geom.geom_type == "Polygon":
                merged_geom = MultiPolygon(merged_geom, srid=4326)
            if merged_geom.srid is None:
                merged_geom.srid = 4326
            obj.geom = merged_geom
            obj.save(update_fields=["geom"])
            return "merged"

        self._seen.add(code)
        _, created = model.objects.update_or_create(
            kode_pum=code, defaults=defaults
        )
        return "created" if created else "updated"

    # ------------------------------------------------------------------ #
    def _province_codes(self, url):
        """Ambil daftar kode provinsi (KDPPUM) tanpa geometri -- ringan & andal."""
        data = self._fetch(
            url,
            {
                "where": "1=1",
                "outFields": "KDPPUM",
                "returnGeometry": "false",
                "returnDistinctValues": "true",
                "orderByFields": "KDPPUM",
                "f": "json",
            },
        )
        codes = []
        for ft in data.get("features") or []:
            code = (ft.get("attributes") or {}).get("KDPPUM")
            if code:
                codes.append(str(code).strip())
        return codes

    # ------------------------------------------------------------------ #
    def _where_clauses(self, url):
        """Daftar klausa WHERE untuk diiterasi + WHERE total (untuk hitung).

        - ``--kabupaten`` -> satu klausa KDPKAB (kab/kec/desa kabupaten itu).
        - ``--provinsi``  -> satu klausa KDPPUM (satu provinsi).
        - tanpa filter    -> per-provinsi (chunking, hindari 500 nasional).
        """
        if self.kab:
            w = f"KDPKAB='{self.kab}'"
            return [w], w
        if self.prov:
            w = f"KDPPUM='{self.prov}'"
            return [w], w
        codes = self._province_codes(url)
        if not codes:
            raise CommandError(
                "Gagal menentukan daftar provinsi (KDPPUM). Coba --provinsi / --kabupaten."
            )
        return [f"KDPPUM='{c}'" for c in codes], "1=1"

    # ------------------------------------------------------------------ #
    def _truncate_all(self):
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                "TRUNCATE wilayah.provinsi, wilayah.kabkota, "
                "wilayah.kecamatan, wilayah.desa RESTART IDENTITY;"
            )
        self.stdout.write("Tabel schema 'wilayah' dikosongkan (--replace).")

    # ------------------------------------------------------------------ #
    def _build_provinsi(self, prov):
        """Bangun poligon provinsi via dissolve (ST_Union) dari Kab/Kota."""
        from django.contrib.gis.db.models import Union

        qs = RefWilayahKabkota.objects.all()
        if prov:
            qs = qs.filter(kode_prov_pum=prov)
        if not qs.exists():
            raise CommandError(
                "Tabel Kabupaten/Kota kosong. Jalankan '--level kab' lebih dulu."
            )

        groups = list(
            qs.values("kode_prov_pum")
            .annotate(geom=Union("geom"))
            .order_by("kode_prov_pum")
        )
        inserted = updated = 0
        with _Progress(sys.stdout, "prov", len(groups)) as bar:
            for i, g in enumerate(groups, 1):
                kode = g["kode_prov_pum"]
                geom = g["geom"]
                if not kode or geom is None:
                    continue
                if geom.geom_type == "Polygon":
                    geom = MultiPolygon(geom, srid=4326)
                if geom.srid is None:
                    geom.srid = 4326
                nama = (
                    RefWilayahKabkota.objects.filter(kode_prov_pum=kode)
                    .values_list("nama_prov", flat=True)
                    .first()
                ) or ""
                _, created = RefWilayahProvinsi.objects.update_or_create(
                    kode_pum=str(kode).strip(),
                    # Kode provinsi PUM == kode BPS pada level 2 digit.
                    defaults={"kode_bps": str(kode).strip(), "nama": nama, "geom": geom},
                )
                inserted += int(created)
                updated += int(not created)
                bar.update(done=i, extra=f"+{inserted} baru")
                if not bar.enabled:
                    self.stdout.write(f"  prov: {i}/{len(groups)} (+{inserted} baru)")
        return f"{inserted} baru, {updated} update (dissolve dari kab)"

    # ------------------------------------------------------------------ #
    def _count(self, url, where):
        """Jumlah fitur total (untuk persen progress). 0 = indeterminate."""
        try:
            data = self._fetch(url, {"where": where, "returnCountOnly": "true", "f": "json"})
            return int(data.get("count") or 0)
        except Exception:
            return 0

    # ------------------------------------------------------------------ #
    def _fetch(self, url, params, retries=4):
        last = None
        for attempt in range(retries):
            try:
                r = self.session.get(url, params=params, timeout=180)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and data.get("error"):
                    raise RuntimeError(data["error"])
                return data
            except Exception as exc:  # noqa: BLE001 - retry semua error transien
                last = exc
                time.sleep(2 ** attempt)
        raise CommandError(
            f"Gagal mengambil {url} (offset={params.get('resultOffset')}): {last}"
        )
