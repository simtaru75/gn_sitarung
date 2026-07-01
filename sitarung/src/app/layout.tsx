import type { Metadata } from "next";
import { getSiteIdentity } from "@/lib/geonode";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `${ident.siteName} — ${ident.namaKabupaten}`,
    description: `Platform ${ident.siteName} — DST FOLUR ${ident.namaKabupaten}`,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

function gfUrl(serif: string, sans: string, mono: string): string {
  const extract = (stack: string) => stack.split(",")[0].trim().replace(/['"]/g, "");
  const names = [extract(serif), extract(sans), extract(mono)];
  const params = names.map((n) => `family=${encodeURIComponent(n)}:ital,wght@0,400;0,600;0,700;1,400`);
  return `https://fonts.googleapis.com/css2?${params.join("&")}&display=swap`;
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const ident = await getSiteIdentity();
  const f = ident.fonts;

  return (
    <html lang="id" data-theme={ident.theme || "simtaru"}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href={gfUrl(f.serif, f.sans, f.mono)} rel="stylesheet" />
      </head>
      <body
        className="antialiased"
        style={{
          "--font-sans": `${f.sans}, system-ui, sans-serif`,
          "--font-serif": `${f.serif}, serif`,
          "--font-mono": `${f.mono}, ui-monospace, monospace`,
          "--serif": `${f.serif}, serif`,
          "--sans": `${f.sans}, system-ui, sans-serif`,
          "--mono": `${f.mono}, ui-monospace, monospace`,
          fontFamily: `${f.sans}, system-ui, sans-serif`,
        } as React.CSSProperties}
      >
        {children}
      </body>
    </html>
  );
}
