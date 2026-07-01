import { getDataset, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE } from "@/lib/config";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import DatasetSpasialClient from "./DatasetSpasialClient";

export const revalidate = 300; // revalidate every 5 minutes (ISR)

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const pk = Number(id);
  if (!Number.isFinite(pk)) return {};
  try {
    const [ds, ident] = await Promise.all([getDataset(pk), getSiteIdentity()]);
    return {
      title: ds?.title ? `${ds.title} — ${ident.siteName}` : `${ident.siteName} — ${ident.namaKabupaten}`,
      description: `Detail Dataset Spasial ${ident?.namaKabupaten ?? ""}`,
      icons: ident?.logo ? { icon: ident.logo } : undefined,
    };
  } catch {
    return {
      title: "Detail Dataset Spasial",
    };
  }
}

export default async function DatasetSpasialPage({ params }: Props) {
  const { id } = await params;
  const pk = Number(id);
  if (!Number.isFinite(pk)) notFound();

  let ds = null;
  let site = null;

  try {
    [ds, site] = await Promise.all([
      getDataset(pk),
      getSiteIdentity(),
    ]);
  } catch {
    notFound();
  }

  if (!ds) notFound();

  return (
    <>
      {/* CSS inti Leaflet WAJIB ada — tanpa ini .leaflet-tile/.leaflet-pane
          tidak ter-posisi absolut & peta tampil berantakan. Next menaikkannya
          ke <head> (render-blocking) sehingga siap sebelum peta di-init.
          leaflet.js dimuat di komponen klien (Script onReady → init seketika). */}
      <link rel="stylesheet" href="/vendor/leaflet/leaflet.css" />
      <DatasetSpasialClient ds={ds} site={site} publicBase={PUBLIC_BASE} />
    </>
  );
}
