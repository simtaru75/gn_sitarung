# -*- coding: utf-8 -*-
"""Unduh berkas resource Satu Data lalu daftarkan sebagai Dokumen GeoNode.

Dipakai oleh tombol "Daftarkan ke Dokumen" pada halaman Integrasi Satu Data dan
oleh management command ``register_satudata_documents``. Berkas diunduh dari
``SatuDataResource.url`` ke berkas sementara, lalu dibuat entri ``Document``
GeoNode **draft** (``is_published=False``) memakai pola yang sama dengan unggah
dokumen biasa (``create_asset_and_link`` + thumbnail PDF). Idempoten: resource
yang sudah punya ``document`` dilewati.
"""
import os
import tempfile
from urllib.parse import unquote, urlsplit

import requests
from geonode.documents.models import Document

# Format yang boleh dijadikan Dokumen — selaras dengan DokumenBaruView.ALLOWED_EXT.
ALLOWED_EXT = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "zip", "jpg", "jpeg", "png",
}
MAX_BYTES = 200 * 1024 * 1024  # batas 200 MB per berkas.
USER_AGENT = "DST-FOLUR/satudata_docs"


def set_pdf_thumbnail(document, pdf_path):
    """Render halaman pertama PDF menjadi thumbnail (PyMuPDF). Opsional."""
    try:
        import fitz  # PyMuPDF

        with fitz.open(pdf_path) as pdf:
            if pdf.page_count == 0:
                return
            page = pdf.load_page(0)
            width = page.rect.width or 1
            zoom = max(0.5, min(600.0 / width, 3.0))
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            png_bytes = pix.tobytes("png")
        document.save_thumbnail(f"document-{document.uuid}-thumb.png", png_bytes)
    except Exception:  # noqa: BLE001 — thumbnail opsional, jangan gagalkan proses.
        pass


def _ext_from(format_, url):
    """Tentukan ekstensi berkas dari ``format`` CKAN lalu fallback ke path URL."""
    ext = (format_ or "").strip().lower().lstrip(".")
    if ext in ALLOWED_EXT:
        return ext
    path = unquote(urlsplit(url or "").path)
    url_ext = os.path.splitext(path)[1].lstrip(".").lower()
    if url_ext in ALLOWED_EXT:
        return url_ext
    return ext or url_ext  # mungkin tak didukung; pemanggil yang memutuskan.


def _filename_for(resource, ext):
    base = (resource.nama or "").strip()
    if not base:
        path = unquote(urlsplit(resource.url or "").path)
        base = os.path.splitext(os.path.basename(path))[0]
    base = (base or f"resource-{resource.pk}")[:120]
    if not base.lower().endswith("." + ext):
        base = f"{base}.{ext}"
    # Bersihkan karakter path yang berbahaya untuk nama berkas.
    return base.replace("/", "_").replace("\\", "_")


def _download_to_temp(url, *, verify=True, timeout=180, max_bytes=MAX_BYTES, filename="download.bin"):
    """Unduh streaming ke berkas sementara. Return (path, tmpdir). Raise bila gagal."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.verify = verify
    if not verify:
        try:
            import urllib3
            from urllib3.exceptions import InsecureRequestWarning

            urllib3.disable_warnings(InsecureRequestWarning)
        except Exception:  # noqa: BLE001
            pass

    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, filename)
    size = 0
    with session.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(path, "wb") as out:
            for chunk in r.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(f"Berkas melebihi batas {max_bytes} byte.")
                out.write(chunk)
    return path, tmpdir


def create_geonode_document(path, *, owner, title, abstract, ext):
    """Buat ``Document`` GeoNode (draft) dari berkas lokal + lampirkan asset.

    Helper bersama: dipakai unggah dokumen biasa (``DokumenBaruView``) maupun
    pendaftaran berkas Satu Data. Membuat dokumen **draft** (belum publish).
    """
    from geonode.assets.utils import create_asset_and_link
    from geonode.base.models import Region

    indonesia = Region.objects.filter(name__iexact="Indonesia").first()
    document = Document.objects.create(
        owner=owner,
        title=(title or "Dokumen")[:255],
        language="ind",
        abstract=abstract or "Abstrak / Ringkasan belum tersedia",
        extension=ext,
        subtype="document",
        is_published=False,
        is_approved=False,
    )
    if indonesia:
        document.regions.set([indonesia])
    try:
        document.poc = owner
    except Exception:  # noqa: BLE001
        pass
    create_asset_and_link(document, owner, [path], clone_files=True)
    if ext == "pdf":
        set_pdf_thumbnail(document, path)
    return document


def register_resource_as_document(resource, user, *, verify=True):
    """Unduh ``resource`` lalu daftarkan jadi ``Document``.

    Return ``Document`` bila dibuat, atau ``None`` bila dilewati (sudah terdaftar
    / format tak didukung / tak ada URL). Raise bila unduhan/pembuatan gagal.
    """
    if resource.document_id and Document.objects.filter(pk=resource.document_id).exists():
        return None
    ext = _ext_from(resource.format, resource.url)
    if ext not in ALLOWED_EXT or not resource.url:
        return None

    filename = _filename_for(resource, ext)
    path, tmpdir = _download_to_temp(resource.url, verify=verify, filename=filename)
    try:
        ds = resource.dataset
        # Judul dokumen mengikuti judul dataset agar konsisten dengan tabel
        # "Daftar Dataset" di Integrasi Satu Data. Untuk dataset dengan banyak
        # berkas, nama berkas ditambahkan agar tiap dokumen tetap dapat dibedakan.
        title = ds.title or resource.nama or filename
        if (ds.jumlah_resource or 0) > 1:
            label = (resource.nama or "").rsplit(".", 1)[0].strip()
            if label and label.lower() not in title.lower():
                title = f"{title} — {label}"
        sumber = f"Sumber: {ds.title}"
        if ds.portal_url:
            sumber += f" — {ds.portal_url}"
        abstract = f"{ds.notes}\n\n{sumber}".strip() if ds.notes else sumber
        document = create_geonode_document(
            path, owner=user, title=title, abstract=abstract, ext=ext
        )
        resource.document = document
        resource.save(update_fields=["document"])
        # Wariskan instansi Walidata dataset (bila sudah terpetakan) ke dokumen,
        # agar tampilan/filter Walidata di katalog konsisten dgn Daftar Dataset.
        if ds.walidata_id:
            from .models import DocumentWalidata

            DocumentWalidata.objects.update_or_create(
                document=document, defaults={"walidata_id": ds.walidata_id}
            )
        return document
    finally:
        try:
            os.remove(path)
            os.rmdir(tmpdir)
        except OSError:
            pass


def register_dataset_documents(dataset, user, *, verify=True):
    """Daftarkan semua resource sebuah ``dataset``. Return ringkasan dict."""
    dibuat = dilewati = gagal = 0
    errors = []
    for r in dataset.resources.all():
        try:
            doc = register_resource_as_document(r, user, verify=verify)
            if doc is None:
                dilewati += 1
            else:
                dibuat += 1
        except Exception as exc:  # noqa: BLE001
            gagal += 1
            errors.append(f"{r.nama or r.url}: {exc}")
    return {"dibuat": dibuat, "dilewati": dilewati, "gagal": gagal, "errors": errors}
