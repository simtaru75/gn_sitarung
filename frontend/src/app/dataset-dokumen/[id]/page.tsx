import { getDocument, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE } from "@/lib/config";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Script from "next/script";
import DocumentClient from "./DocumentClient";

export const revalidate = 300; // revalidate every 5 minutes (ISR)

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const pk = Number(id);
  if (!Number.isFinite(pk)) return {};
  try {
    const [doc, ident] = await Promise.all([getDocument(pk), getSiteIdentity()]);
    return {
      title: doc?.title ? `${doc.title} — ${ident.siteName}` : `${ident.siteName} — ${ident.namaKabupaten}`,
      description: `Detail Dokumen ${ident?.namaKabupaten ?? ""}`,
      icons: ident?.logo ? { icon: ident.logo } : undefined,
    };
  } catch {
    return {
      title: "Detail Dokumen",
    };
  }
}

export default async function DatasetDokumenPage({ params }: Props) {
  const { id } = await params;
  const pk = Number(id);
  if (!Number.isFinite(pk)) notFound();

  let doc = null;
  let site = null;

  try {
    [doc, site] = await Promise.all([
      getDocument(pk),
      getSiteIdentity(),
    ]);
  } catch {
    notFound();
  }

  if (!doc) notFound();

  return (
    <>
      {doc.isPdf && (
        // PDF.js dilayani same-origin (frontend/public/pdfjs) — tanpa CDN
        // eksternal, sekaligus menghindari blokir Web Worker lintas-origin.
        <Script src="/pdfjs/pdf.min.js" strategy="afterInteractive" />
      )}
      <DocumentClient doc={doc} site={site} publicBase={PUBLIC_BASE} />
    </>
  );
}
