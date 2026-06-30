"use client";

import { useEffect } from "react";

// Pustaka peta (urutan penting: leaflet dulu, plugin setelahnya), lalu
// aplikasi WebGIS (porting verbatim dari webgis.html GeoNode). Markup &
// config dirender server-side; komponen ini murni loader script.
const SCRIPTS = [
  "/vendor/leaflet/leaflet.js",
  "/vendor/leaflet-draw/leaflet.draw.js",
  "/vendor/leaflet-minimap/Control.MiniMap.min.js",
  "/vendor/togeojson/togeojson.umd.js",
  "/vendor/jszip/jszip.min.js",
  "/vendor/shpjs/shp.min.js",
  "/vendor/turf/turf.min.js",
  "/webgis-screening.js",
];

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) return resolve();
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Gagal memuat ${src}`));
    document.body.appendChild(s);
  });
}

declare global {
  interface Window {
    __WEBGIS_BOOTED__?: boolean;
  }
}

/** Pastikan topbar memakai nilai config (anti-placeholder bila hidrasi dev
 *  menimpa markup server dengan salinan flight). */
function applyBranding() {
  try {
    const cfg = JSON.parse(document.getElementById("webgis-config")?.textContent || "{}");
    const name = document.querySelector(".topbar-title-name");
    if (name && cfg.siteName) name.textContent = `WebGIS ${cfg.siteName}`;
    const logo = document.querySelector<HTMLImageElement>(".topbar-title-mark img");
    if (logo && cfg.logoURL) logo.src = cfg.logoURL;
  } catch {
    /* abaikan — branding fallback markup server */
  }
}

export default function WebGisClient() {
  useEffect(() => {
    applyBranding();
    if (window.__WEBGIS_BOOTED__) return;
    window.__WEBGIS_BOOTED__ = true;
    (async () => {
      try {
        for (const src of SCRIPTS) await loadScript(src);
      } catch (e) {
      if (process.env.NODE_ENV !== "production") console.error("WebGIS gagal memuat pustaka:", e);
        window.__WEBGIS_BOOTED__ = false;
      }
    })();
  }, []);

  return null;
}
