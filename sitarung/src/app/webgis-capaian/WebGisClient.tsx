"use client";

import { useEffect } from "react";

// Leaflet dulu, lalu aplikasi WebGIS Capaian (porting verbatim dari inline
// <script> webgis2.html). Markup & config dirender server-side; komponen ini
// murni loader script.
const SCRIPTS = [
  "/vendor/leaflet/leaflet.js",
  "/webgis-capaian.js",
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
    __WEBGIS_CAPAIAN_BOOTED__?: boolean;
  }
}

export default function WebGisClient() {
  useEffect(() => {
    // Toggle collapse kartu peta (di GeoNode dipasang via inline onclick;
    // di server component React tak boleh, jadi diikat di sini).
    document.querySelectorAll<HTMLElement>(".map-card-head").forEach((head) => {
      head.addEventListener("click", () => head.parentElement?.classList.toggle("collapsed"));
    });

    if (window.__WEBGIS_CAPAIAN_BOOTED__) return;
    window.__WEBGIS_CAPAIAN_BOOTED__ = true;
    (async () => {
      try {
        for (const src of SCRIPTS) await loadScript(src);
      } catch (e) {
        if (process.env.NODE_ENV !== "production") console.error("WebGIS Capaian gagal memuat pustaka:", e);
        window.__WEBGIS_CAPAIAN_BOOTED__ = false;
      }
    })();
  }, []);

  return null;
}
