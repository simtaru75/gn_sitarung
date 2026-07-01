import type { Metadata } from "next";
import { notFound } from "next/navigation";
import StaticHtmlPage from "@/app/StaticHtmlPage";
import { getSiteIdentity } from "@/lib/geonode";
import { getStaticPage } from "@/lib/static-pages";

export const revalidate = 300;

export async function generateMetadata(): Promise<Metadata> {
  const [page, ident] = await Promise.all([getStaticPage("lainnya", "pengaduan"), getSiteIdentity()]);
  if (!page) return { title: "Pengaduan" };
  const siteLabel = ident.siteName && ident.siteName !== "DST" ? ident.siteName : "SITARUNG";
  return {
    title: `${page.heading} — ${siteLabel}`,
    description: page.summary || page.subheading,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function PengaduanPage() {
  const [page, site] = await Promise.all([getStaticPage("lainnya", "pengaduan"), getSiteIdentity()]);
  if (!page) notFound();

  return <StaticHtmlPage page={page} site={site} sectionLabelOverride="Pengaduan" hideSidebar />;
}