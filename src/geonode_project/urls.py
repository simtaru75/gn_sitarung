# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

# Do not remove handler500 import. It is required to re-export
# the custom error page handler for the GeoNode project
# related issue: https://github.com/GeoNode/geonode-project/issues/570
from django.urls import path, include
from geonode.urls import urlpatterns as geonode_urls, handler500  # noqa

from . import views

dst_public_patterns = (
    [
        path("", views.DstLandingView.as_view(), name="landing"),
        path("webgis/", views.WebGisView.as_view(), name="webgis"),
        path("webgis/screening-log/", views.screening_log_create, name="screening_log"),
        path("webgis2/", views.WebGis2View.as_view(), name="webgis2"),
        path("webgis2/geojson/", views.webgis2_geojson, name="webgis2_geojson"),
        path("webgis2/desa-history/", views.webgis2_desa_history, name="webgis2_desa_history"),
        path("jelajah-dataset/", views.DatasetExploreView.as_view(), name="dataset_explore"),
        path("jelajah-dokumen/", views.DocumentExploreView.as_view(), name="document_explore"),
        path("jelajah-endpoint-api/", views.EndpointApiExploreView.as_view(), name="endpoint_explore"),
        path("capaian-folur/", views.CapaianPublikView.as_view(), name="capaian_publik"),
        path("api/folur/capaian/", views.api_capaian_folur, name="api_capaian_folur"),
        path("api/folur/capaian-publik/", views.api_capaian_publik, name="api_capaian_publik"),
        path("api/folur/dataset-meta/", views.api_dataset_meta, name="api_dataset_meta"),
        path("api/folur/komoditas/", views.api_komoditas_fokus, name="api_komoditas_fokus"),
        path("api/folur/partners/", views.api_implementing_partners, name="api_implementing_partners"),
        path("api/folur/indikator/", views.api_indikator_strategis, name="api_indikator_strategis"),
        path("api/folur/jelajah-dokumen/", views.api_jelajah_dokumen, name="api_jelajah_dokumen"),
        path("api/folur/jelajah-dataset/", views.api_jelajah_dataset, name="api_jelajah_dataset"),
        path("api/folur/site-identity/", views.api_site_identity, name="api_site_identity"),
        path("api/folur/dataset/<int:pk>/", views.api_dataset_detail, name="api_dataset_detail"),
        path("api/folur/dokumen/<int:pk>/", views.api_dokumen_detail, name="api_dokumen_detail"),
        path("api/folur/endpoints/", views.api_endpoint_explore, name="api_endpoint_explore"),
        path("api/folur/webgis-capaian-config/", views.api_webgis2_config, name="api_webgis2_config"),
        path("api/folur/landing-sections/", views.api_landing_sections, name="api_landing_sections"),
        path("api/folur/screening-count/", views.api_screening_count, name="api_screening_count"),
        path("dataset/<int:pk>/", views.DatasetMapView.as_view(), name="dataset_detail"),
        path("dokumen/<int:pk>/", views.DocumentDetailView.as_view(), name="document_detail"),
        path("dokumen/<int:pk>/file/", views.document_file, name="document_file"),
    ],
    "dst",
)

dst_auth_patterns = (
    [
        path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
        path("capaian/", views.CapaianView.as_view(), name="capaian"),
        path("dokumen/", views.DokumenView.as_view(), name="dokumen"),
        path("dokumen/baru/", views.DokumenBaruView.as_view(), name="dokumen_baru"),
        path("dokumen/detail/", views.DokumenDetailView.as_view(), name="dokumen_detail"),
        path("data-spasial/", views.DataSpasialView.as_view(), name="data_spasial"),
        path("layer/baru/", views.LayerBaruView.as_view(), name="layer_baru"),
        path("layer/detail/", views.LayerDetailView.as_view(), name="layer_detail"),
        path("layer/edit/", views.LayerEditView.as_view(), name="layer_edit"),
        path("akses-nasional/", views.AksesNasionalView.as_view(), name="akses_nasional"),
        path("endpoint-api/", views.EndpointApiView.as_view(), name="endpoint_api"),
        path(
            "integrasi-satudata/",
            views.IntegrasiSatuDataView.as_view(),
            name="integrasi_satudata",
        ),
        path("metadata-schema/", views.MetadataSchemaView.as_view(), name="metadata_schema"),
        path("data-capaian/", views.DataCapaianView.as_view(), name="data_capaian"),
        path("pengguna/", views.PenggunaView.as_view(), name="pengguna"),
        path("pengguna/baru/", views.PenggunaBaruView.as_view(), name="pengguna_baru"),
        path("pengguna/edit/", views.PenggunaEditView.as_view(), name="pengguna_edit"),
        path("frontend/", views.FrontendView.as_view(), name="frontend"),
        path("backend/", views.BackendView.as_view(), name="backend"),
        path("pengaturan/", views.PengaturanView.as_view(), name="pengaturan"),
        path("topik-kategori/", views.TopikKategoriView.as_view(), name="topik_kategori"),
        path("walidata/", views.WalidataView.as_view(), name="walidata"),
        path("kode-wilayah/", views.KodeWilayahView.as_view(), name="kode_wilayah"),
        path("tema/", views.TemaView.as_view(), name="tema"),
        path("backup/download/", views.backup_download, name="backup_download"),
        path(
            "wilayah/kabupaten-options/",
            views.wilayah_kabupaten_options,
            name="wilayah_kabupaten_options",
        ),
        path(
            "wilayah/kecdesa-options/",
            views.wilayah_kecdesa_options,
            name="wilayah_kecdesa_options",
        ),
        path("profil/", views.ProfilView.as_view(), name="profil"),
        path("audit-log/", views.AuditLogView.as_view(), name="audit_log"),
    ],
    "dst_auth",
)

urlpatterns = [
    path("", include(dst_public_patterns)),
    path("dst-auth/", include(dst_auth_patterns)),
] + geonode_urls
