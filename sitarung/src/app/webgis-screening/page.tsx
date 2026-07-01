import "./webgis-screening.css";
import fs from "node:fs/promises";
import path from "node:path";
import type { Metadata } from "next";
import { getSiteIdentity } from "@/lib/geonode";
import WebGisClient from "./WebGisClient";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const ident = await getSiteIdentity();
  return {
    title: `WebGIS — ${ident.siteName}`,
    description: `WebGIS ${ident.siteName} — Modul Akurat`,
    icons: ident.logo ? { icon: ident.logo } : undefined,
  };
}

export default async function Page() {
  const ident = await getSiteIdentity();

  // Markup asli halaman GeoNode (diekstrak verbatim dari webgis.html).
  const raw = await fs.readFile(
    path.join(process.cwd(), "src/app/webgis-screening/webgis-body.html"),
    "utf8",
  );
  const html = raw
    .replaceAll("__THEME_LOGO__", ident.logo || "/icon.png")
    .replaceAll("__SITE_NAME__", ident.siteName);

  // Konfigurasi identik dengan WebGisView GeoNode. baseURL "" (relatif) —
  // /geoserver, /api/v2, /webgis/screening-log diproksikan Next (rewrites)
  // sehingga tetap same-origin tanpa CORS.
  const config = {
    baseURL: "",
    wmsPath: "/geoserver/wms",
    wfsPath: "/geoserver/wfs",
    mapsApiPath: "/api/v2/maps",
    datasetsApiPath: "/api/v2/datasets",
    workspace: "geonode",
    referenceMapId: ident.webgisReferenceMapId,
    center: [-3.23, 120.39],
    bbox: [
      [-3.7, 119.9],
      [-2.7, 120.8],
    ],
    siteName: ident.siteName,
    logoURL: ident.logo || "/icon.png",
  };

  return (
    <>
      {/* Aset self-hosted (/vendor) — React 19 menaikkan <link> ke <head>. */}
      <link rel="stylesheet" href="/vendor/fonts/webgis-fonts.css" />
      <link rel="stylesheet" href="/vendor/leaflet/leaflet.css" />
      <link rel="stylesheet" href="/vendor/leaflet-draw/leaflet.draw.css" />
      <link rel="stylesheet" href="/vendor/leaflet-minimap/Control.MiniMap.min.css" />

      {/* Config GeoNode — id & format sama dengan json_script Django. */}
      <script id="webgis-config" type="application/json" dangerouslySetInnerHTML={{ __html: JSON.stringify(config) }} />

      {/* Markup asli dirender server-side (tanpa salinan flight/hydration). */}
      <div data-theme={ident.theme} dangerouslySetInnerHTML={{ __html: html }} />

      <WebGisClient />
    </>
  );
}
