# -*- coding: utf-8 -*-
"""Seed tabel ``Region`` GeoNode dengan provinsi + kabupaten/kota Indonesia.

Mengisi opsi field "Region / Cakupan" (metadata layer & dokumen) dengan seluruh
wilayah administrasi Indonesia: Indonesia → 38 Provinsi → ±514 Kabupaten/Kota.
Nama mengikuti konvensi BIG apa adanya — kabupaten tanpa kata "Kabupaten"
(mis. "Luwu"), kota dengan kata "Kota" (mis. "Kota Palopo").

Sumber nama/kode: layanan ArcGIS REST publik BIG (atribut saja, tanpa geometri),
lewat ``fetch_provinsi_options`` / ``fetch_kabupaten_options``.

Idempoten: dikunci pada ``code`` ber-prefix ``IDN-<kode PUM>`` sehingga aman
dijalankan ulang. Contoh::

    python manage.py seed_region_indonesia

Sumber data (c) Badan Informasi Geospasial (BIG) — geoservices.big.go.id
"""
from django.core.management.base import BaseCommand

from geonode.base.models import Region

from geonode_project.management.commands.sync_wilayah_big import (
    fetch_kabupaten_options,
    fetch_provinsi_options,
)


class Command(BaseCommand):
    help = "Seed Region GeoNode dengan provinsi + kabupaten/kota Indonesia (dari BIG)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--provinsi",
            default=None,
            help="Batasi ke satu kode provinsi (mis. 73) untuk uji.",
        )

    def _provinsi_kabkota_local(self, only_prov=None):
        """Sumber OFFLINE dari tabel ``RefKodeBps`` (master nasional yang sudah
        di-seed ``restore_wilayah``). Return (provs, kab_by_prov) atau None bila
        tabel kosong.

        - provs: list[{"kode","nama"}] level provinsi (kode PUM, mis. "73").
        - kab_by_prov: dict kode_prov -> list[{"kode","nama"}] level kab/kota
          (kode PUM mis. "73.17"). Parent ditentukan dari prefix sebelum titik.
        """
        from geonode_project.models import RefKodeBps

        prov_qs = RefKodeBps.objects.filter(level="provinsi").order_by("kode_pum")
        if not prov_qs.exists():
            return None
        provs = [{"kode": r.kode_pum, "nama": r.nama} for r in prov_qs]
        if only_prov:
            provs = [p for p in provs if p["kode"] == only_prov]

        kab_by_prov = {}
        for r in RefKodeBps.objects.filter(level="kabkota").order_by("kode_pum"):
            prov_kode = (r.kode_pum or "").split(".")[0]
            kab_by_prov.setdefault(prov_kode, []).append(
                {"kode": r.kode_pum, "nama": r.nama}
            )
        return provs, kab_by_prov

    def handle(self, *args, **opts):
        indonesia, _ = Region.objects.get_or_create(
            code="IDN", defaults={"name": "Indonesia"}
        )

        only_prov = opts.get("provinsi")
        local = self._provinsi_kabkota_local(only_prov)
        use_local = local is not None
        if use_local:
            provs, kab_by_prov = local
            self.stdout.write(
                f"Sumber LOKAL (RefKodeBps): {len(provs)} provinsi akan diproses…"
            )
        else:
            provs = fetch_provinsi_options()
            if only_prov:
                provs = [p for p in provs if p["kode"] == only_prov]
            kab_by_prov = None
            self.stdout.write(
                f"Sumber BIG (online): {len(provs)} provinsi akan diproses…"
            )

        n_prov = n_kab = 0
        # disable_mptt_updates + rebuild() di akhir: pola bulk-insert MPTT yang
        # benar untuk menambah ratusan node baru (delay_mptt_updates gagal pada
        # pembuatan subtree baru). Pohon disusun ulang sekali setelah blok.
        with Region.objects.disable_mptt_updates():
            for p in provs:
                prov_obj, _ = Region.objects.update_or_create(
                    code=f"IDN-{p['kode']}",
                    defaults={"name": p["nama"], "parent": indonesia},
                )
                n_prov += 1
                if use_local:
                    kklist = kab_by_prov.get(p["kode"], [])
                else:
                    try:
                        kklist = fetch_kabupaten_options(p["kode"])
                    except Exception as exc:  # noqa: BLE001
                        self.stderr.write(f"  ! gagal {p['nama']}: {exc}")
                        continue
                for k in kklist:
                    Region.objects.update_or_create(
                        code=f"IDN-{k['kode']}",
                        defaults={"name": k["nama"], "parent": prov_obj},
                    )
                    n_kab += 1
                self.stdout.write(f"  {p['nama']}: {len(kklist)} kab/kota")

        Region.objects.rebuild()
        self.stdout.write(
            self.style.SUCCESS(
                f"Selesai: {n_prov} provinsi, {n_kab} kabupaten/kota di-seed ke Region."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Sumber data (c) Badan Informasi Geospasial (BIG) — geoservices.big.go.id"
            )
        )
