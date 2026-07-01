import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getSiteIdentity } from "@/lib/geonode";
import { getStaticPage } from "@/lib/static-pages";
import StaticHtmlPage from "@/app/StaticHtmlPage";

export const revalidate = 300;

export async function generateMetadata(): Promise<Metadata> {
  const [page, ident] = await Promise.all([getStaticPage("rtrw", "index"), getSiteIdentity()]);
  if (!page) return { title: "Materi RTRW" };
  const siteLabel = ident.siteName && ident.siteName !== "DST" ? ident.siteName : "SITARUNG";
  return {
    title: `${page.heading} — ${siteLabel}`,
    description: page.summary || page.subheading,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function RtrwIndexPage() {
  const [page, site] = await Promise.all([getStaticPage("rtrw", "index"), getSiteIdentity()]);
  if (!page) notFound();
  return <StaticHtmlPage page={page} site={site} />;
}