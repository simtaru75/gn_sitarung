import LandingClient from "./LandingClient";
import { getLandingData, getSiteIdentity } from "@/lib/geonode";
import { PUBLIC_BASE } from "@/lib/config";
import type { Metadata } from "next";

export const revalidate = 300; // revalidate every 5 minutes (ISR)

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Beranda — ${ident.siteName}`,
    description: `Platform ${ident.siteName} — Data otoritatif untuk tata kelola bentang lahan di ${ident.namaKabupaten}`,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function Page() {
  const [data, site] = await Promise.all([getLandingData(), getSiteIdentity()]);
  return (
    <>
      <link rel="stylesheet" href="/vendor/fontawesome/css/all.min.css" />
      <link rel="stylesheet" href="/vendor/fontawesome/css/v4-shims.min.css" />
      <LandingClient data={data} site={site} publicBase={PUBLIC_BASE} />
    </>
  );
}
