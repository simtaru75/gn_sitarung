import type { NextConfig } from "next";

// Base internal (jaringan docker) untuk proxy same-origin halaman WebGIS:
// peta memakai path relatif (/geoserver, /api/v2, /webgis/...) persis seperti
// di GeoNode, sehingga bebas CORS — Next yang meneruskan ke backend.
const GEONODE_INTERNAL = (process.env.GEONODE_INTERNAL_URL ?? "http://django:8000").replace(/\/+$/, "");
const GEOSERVER_INTERNAL = (process.env.GEOSERVER_INTERNAL_URL ?? "http://geoserver:8080").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  // Gambar GeoNode disajikan di http://localhost (host browser), TIDAK terjangkau
  // optimizer next/image yang jalan DI DALAM container (localhost = container itu
  // sendiri → fetch 500). unoptimized: render <img> apa adanya → browser yang
  // mengambil langsung. remotePatterns tetap untuk jaring pengaman.
  images: {
    unoptimized: true,
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "https", hostname: "unpkg.com" },
    ],
  },
  // API GeoNode memakai trailing slash (/api/v2/datasets/) — jangan 308 dulu
  // sebelum rewrites, supaya proxy same-origin WebGIS tidak redirect-loop.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      { source: "/geoserver/:path*", destination: `${GEOSERVER_INTERNAL}/geoserver/:path*` },
      { source: "/api/v2/:path*", destination: `${GEONODE_INTERNAL}/api/v2/:path*` },
      { source: "/webgis/screening-log/", destination: `${GEONODE_INTERNAL}/webgis/screening-log/` },
      // Data WebGIS Capaian (/webgis-capaian) — choropleth GeoJSON & riwayat desa.
      { source: "/webgis2/geojson/", destination: `${GEONODE_INTERNAL}/webgis2/geojson/` },
      { source: "/webgis2/desa-history/", destination: `${GEONODE_INTERNAL}/webgis2/desa-history/` },
      // Streaming berkas dokumen (PDF.js/gambar/unduh) — same-origin agar bebas
      // CORS. GeoNode menegakkan permission download_resourcebase. Trailing slash
      // di-hardcode (.../file/) supaya tidak kena APPEND_SLASH 301-loop Django.
      { source: "/dokumen/:pk/file/", destination: `${GEONODE_INTERNAL}/dokumen/:pk/file/` },
    ];
  },
};

export default nextConfig;
