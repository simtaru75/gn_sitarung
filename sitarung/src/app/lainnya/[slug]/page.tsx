import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { notFound } from "next/navigation";
import { getSiteIdentity } from "@/lib/geonode";
import { getStaticPage, getStaticPageEntries } from "@/lib/static-pages";
import StaticHtmlPage from "@/app/StaticHtmlPage";

export const revalidate = 300;

interface Props {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return getStaticPageEntries("lainnya")
    .filter((item) => item.slug !== "index")
    .map((item) => ({ slug: item.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  if (slug === "pengaduan") {
    return { title: "Pengaduan" };
  }
  const [page, ident] = await Promise.all([getStaticPage("lainnya", slug), getSiteIdentity()]);
  if (!page) return { title: "Informasi Publik" };
  const siteLabel = ident.siteName && ident.siteName !== "DST" ? ident.siteName : "SITARUNG";
  return {
    title: `${page.heading} — ${siteLabel}`,
    description: page.summary || page.subheading,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function LainnyaDetailPage({ params }: Props) {
  const { slug } = await params;
  if (slug === "pengaduan") {
    redirect("/pengaduan");
  }
  const [page, site] = await Promise.all([getStaticPage("lainnya", slug), getSiteIdentity()]);
  if (!page) notFound();
  return <StaticHtmlPage page={page} site={site} />;
}