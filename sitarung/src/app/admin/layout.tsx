import type { Metadata } from "next";
import { getSiteIdentity } from "@/lib/geonode";
import AdminShell from "./AdminShell";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `Admin — ${ident.siteName || "SITARUNG"}`,
    description: `Panel administrasi ${ident.siteName}`,
  };
}

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const ident = await getSiteIdentity();
  return (
    <AdminShell
      brandName={ident.siteName || "SITARUNG"}
      brandSubtitle={ident.namaKabupaten || "Sumatera Selatan"}
      logo={ident.logo}
    >
      {children}
    </AdminShell>
  );
}
