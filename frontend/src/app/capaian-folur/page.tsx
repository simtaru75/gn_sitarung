import { getCapaianFolur, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE } from "@/lib/config";
import type { Metadata } from "next";
import CapaianClient from "./CapaianClient";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Capaian Program — ${ident.siteName}`,
    description: `Capaian Program FOLUR ${ident.namaKabupaten} — Indikator dan KPI`,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function CapaianFolurPage() {
  const [data, site] = await Promise.all([
    getCapaianFolur(),
    getSiteIdentity(),
  ]);

  return <CapaianClient data={data} site={site} publicBase={PUBLIC_BASE} />;
}
