# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2023 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
"""GeoServer init tasks (robust password sync).

Versi tahan-banting menggantikan default geonode/geoserver:
- Memverifikasi password BENAR-BENAR berubah (cek 200) sebelum dianggap sukses.
- Idempoten: kalau password sudah = GEOSERVER_ADMIN_PASSWORD, langsung sukses.
- Hanya menulis ``geoserver_init.lock`` BILA sukses, sehingga boot berikutnya
  otomatis mencoba lagi bila gagal (tidak terkunci selamanya).
"""
import os
import time
import logging

import requests

logger = logging.getLogger(__name__)

from invoke import task

MAX_ATTEMPTS = 60
SLEEP_SECONDS = 3


def _rest_baseurl():
    port = os.getenv("GEOSERVER_LB_PORT", "8080")
    return f"http://localhost:{port}/geoserver/rest"


def _auth_ok(user, password):
    """True bila kredensial diterima GeoServer REST (HTTP 200)."""
    try:
        r = requests.get(
            f"{_rest_baseurl()}/about/version.xml",
            auth=(user, password),
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def _configure_geoserver_password():
    print(
        "************************configuring Geoserver credentials*****************************"
    )
    user = os.getenv("GEOSERVER_ADMIN_USER", "admin")
    target_pw = os.getenv("GEOSERVER_ADMIN_PASSWORD", "geoserver")
    factory_pw = os.getenv("GEOSERVER_FACTORY_PASSWORD", "geoserver")

    data = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<userPassword>\n"
        f"    <newPassword>{target_pw}</newPassword>\n"
        "</userPassword>"
    )
    headers = {"Content-type": "application/xml", "Accept": "application/xml"}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        # 1) Sudah sesuai target? -> selesai (idempoten).
        if _auth_ok(user, target_pw):
            print("GeoServer admin password already matches target. [Ok]")
            return True

        # 2) Masih factory? -> ubah ke target lalu verifikasi.
        if _auth_ok(user, factory_pw):
            try:
                resp = requests.put(
                    f"{_rest_baseurl()}/security/self/password",
                    data=data,
                    headers=headers,
                    auth=(user, factory_pw),
                    timeout=10,
                )
                print(f"Password change response code: {resp.status_code}")
                if resp.status_code == 200 and _auth_ok(user, target_pw):
                    print("GeoServer admin password updated SUCCESSFULLY! [Ok]")
                    return True
            except Exception as exc:  # noqa: BLE001
                print(f"...password change attempt failed: {exc}")

        print(f"...waiting for Geoserver to be ready... attempt {attempt}/{MAX_ATTEMPTS}")
        time.sleep(SLEEP_SECONDS)

    logger.warning(
        "WARNING: GeoServer admin password could NOT be set after "
        f"{MAX_ATTEMPTS} attempts. Init lock will NOT be written so the next "
        "boot retries."
    )
    return False


def _write_init_lock(ctx):
    print("**************************init file********************************")
    data_dir = os.getenv("GEOSERVER_DATA_DIR", "/geoserver_data/data/")
    lock = os.path.join(data_dir, "geoserver_init.lock")
    ctx.run(f"date > {lock}")


@task
def configure_geoserver(ctx):
    if _configure_geoserver_password():
        _write_init_lock(ctx)
    else:
        print("Skipping init lock (password not confirmed) — will retry next boot.")
