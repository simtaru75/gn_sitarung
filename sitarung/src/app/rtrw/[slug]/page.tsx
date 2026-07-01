import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getSiteIdentity } from "@/lib/geonode";
import { getStaticPage, getStaticPageEntries } from "@/lib/static-pages";
import StaticHtmlPage from "@/app/StaticHtmlPage";

export const revalidate = 300;

interface Props {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return getStaticPageEntries("rtrw")
    .filter((item) => item.slug !== "index")
    .map((item) => ({ slug: item.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const [page, ident] = await Promise.all([getStaticPage("rtrw", slug), getSiteIdentity()]);
  if (!page) return { title: "Materi RTRW" };
  const siteLabel = ident.siteName && ident.siteName !== "DST" ? ident.siteName : "SITARUNG";
  return {
    title: `${page.heading} — ${siteLabel}`,
    description: page.summary || page.subheading,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function RtrwDetailPage({ params }: Props) {
  const { slug } = await params;
  const [page, site] = await Promise.all([getStaticPage("rtrw", slug), getSiteIdentity()]);
  if (!page) notFound();
  return <StaticHtmlPage page={page} site={site} />;
}