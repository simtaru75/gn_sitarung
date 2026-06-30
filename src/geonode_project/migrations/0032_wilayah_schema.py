# -*- coding: utf-8 -*-
"""Pindahkan tabel referensi batas wilayah BIG ke schema khusus ``wilayah``.

Tabel ``RefWilayah*`` semula dibuat di schema ``public``. Migrasi ini
memindahkannya ke schema tersendiri ``wilayah`` dan memberi nama bersih
(``provinsi``/``kabkota``/``kecamatan``/``desa``), tanpa kehilangan data.

Dipakai SeparateDatabaseAndState: sisi DATABASE memakai SQL mentah
(``CREATE SCHEMA`` + ``ALTER TABLE ... SET SCHEMA`` + ``RENAME``) karena Django
tidak bisa memindahkan tabel lintas-schema lewat ``AlterModelTable`` biasa;
sisi STATE hanya menyetel ``db_table`` (schema-qualified) agar model & migrasi
selaras.
"""
from django.db import migrations

SCHEMA = "wilayah"

# (model_name_state, nama_tabel_lama_di_public, nama_tabel_baru_di_schema)
TABLES = [
    ("refwilayahprovinsi", "geonode_project_refwilayahprovinsi", "provinsi"),
    ("refwilayahkabkota", "geonode_project_refwilayahkabkota", "kabkota"),
    ("refwilayahkecamatan", "geonode_project_refwilayahkecamatan", "kecamatan"),
    ("refwilayahdesa", "geonode_project_refwilayahdesa", "desa"),
]


def _forward_sql():
    stmts = [f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"]
    for _, old, new in TABLES:
        stmts.append(f"ALTER TABLE public.{old} SET SCHEMA {SCHEMA};")
        stmts.append(f"ALTER TABLE {SCHEMA}.{old} RENAME TO {new};")
    return "\n".join(stmts)


def _reverse_sql():
    stmts = []
    for _, old, new in TABLES:
        stmts.append(f"ALTER TABLE {SCHEMA}.{new} RENAME TO {old};")
        stmts.append(f"ALTER TABLE {SCHEMA}.{old} SET SCHEMA public;")
    stmts.append(f"DROP SCHEMA IF EXISTS {SCHEMA} RESTRICT;")
    return "\n".join(stmts)


class Migration(migrations.Migration):

    dependencies = [
        (
            "geonode_project",
            "0031_refwilayahdesa_refwilayahkabkota_refwilayahkecamatan_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(_forward_sql(), reverse_sql=_reverse_sql()),
            ],
            state_operations=[
                migrations.AlterModelTable(
                    name=state_name, table=f'{SCHEMA}"."{new}'
                )
                for state_name, _old, new in TABLES
            ],
        ),
    ]
