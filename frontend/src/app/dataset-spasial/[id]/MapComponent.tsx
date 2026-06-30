"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import L from "leaflet";
import type { DatasetDetail, SiteIdentity } from "@/lib/geonode";

const BASEMAPS: Record<string, L.TileLayer> = {};

function createBasemaps() {
  if (Object.keys(BASEMAPS).length > 0) return;
  BASEMAPS.osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap contributors" });
  BASEMAPS.topo = L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", { maxZoom: 17, attribution: "map data © OpenStreetMap · SRTM | © OpenTopoMap (CC-BY-SA)" });
  BASEMAPS.s2 = L.tileLayer("https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg", { maxZoom: 16, attribution: 'Sentinel-2 cloudless 2020 — <a href="https://s2maps.eu">s2maps.eu</a>' });
}

interface MapComponentProps {
  ds: DatasetDetail;
  site: SiteIdentity | null;
  publicBase: string;
  opacity: number;
  basemap: string;
  setMapReady: (value: boolean) => void;
  setOpacity: (value: number) => void;
  setBasemap: (value: string) => void;
}

export default function MapComponent({
  ds,
  site,
  publicBase,
  opacity,
  basemap,
  setMapReady,
  setOpacity,
  setBasemap,
}: MapComponentProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInst = useRef<L.Map | null>(null);
  const dataLayer = useRef<L.TileLayer.WMS | null>(null);
  const currentBasemap = useRef<L.TileLayer | null>(null);
  const resizeObs = useRef<ResizeObserver | null>(null);

  const hasLayer = Boolean(ds.typename);
  const bbox = useMemo(() => ds.bbox || ds.extent?.coords || null, [ds]);
  const center = useMemo<[number, number]>(
    () => (bbox ? [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2] : [-3.3, 120.1]),
    [bbox],
  );

  const initMap = useCallback(() => {
    if (!mapRef.current || mapInst.current) return;

    const map = L.map(mapRef.current, {
      center,
      zoom: 10,
      zoomControl: false,
      attributionControl: true,
    });
    if (map.attributionControl) map.attributionControl.setPosition("bottomleft");
    mapInst.current = map;

    // Basemap
    createBasemaps();
    const bm = BASEMAPS[basemap] || BASEMAPS.osm;
    if (bm) { bm.addTo(map); currentBasemap.current = bm; }

    // WMS layer
    if (hasLayer && ds.typename) {
      const baseUrl = publicBase.replace(/\/+$/, "");
      const wmsPath = "/geoserver/wms";
      try {
        const wms = L.tileLayer.wms(baseUrl + wmsPath, {
          layers: ds.typename,
          format: "image/png",
          transparent: true,
          version: "1.1.1",
          attribution: site?.siteName ?? "DST",
        });
        wms.addTo(map);
        dataLayer.current = wms;
      } catch { /* no layer */ }
    }

    // Bbox
    if (bbox) {
      const bounds = L.latLngBounds(
        [bbox[1], bbox[0]] as [number, number],
        [bbox[3], bbox[2]] as [number, number]
      );
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
    }

    // Bar scale
    const BarScale = L.Control.extend({
      options: { position: "bottomright", maxWidth: 130, segments: 4 },
      onAdd: function (m: L.Map) {
        const container = L.DomUtil.create("div", "bar-scale");
        L.DomEvent.disableClickPropagation(container);
        m.on("move zoom zoomend moveend resize", update);
        update();
        function update() {
          const y = Math.round(m.getSize().y / 2);
          const maxMeters = m.distance(
            m.containerPointToLatLng([0, y]),
            m.containerPointToLatLng([130, y])
          );
          if (!isFinite(maxMeters) || maxMeters <= 0) return;
          const pow10 = Math.pow(10, Math.floor(Math.log10(maxMeters)));
          const d = maxMeters / pow10;
          const dist = (d >= 5 ? 5 : d >= 2 ? 2 : 1) * pow10;
          const width = Math.round(130 * (dist / maxMeters));
          const segW = width / 4;
          let bars = "";
          for (let i = 0; i < 4; i++) bars += '<span class="bar-scale-seg ' + (i % 2 ? "dark" : "light") + '" style="width:' + segW + 'px"></span>';
          const lab = (m2: number) => m2 >= 1000 ? Math.round((m2 / 1000) * 100) / 100 + " km" : Math.round(m2) + " m";
          container.innerHTML =
            '<div class="bar-scale-bar" style="width:' + width + 'px">' + bars + "</div>" +
            '<div class="bar-scale-labels" style="width:' + width + 'px"><span>0</span><span style="left:50%">' + lab(dist / 2) + '</span><span>' + lab(dist) + "</span></div>";
        }
        return container;
      },
    });
    (new BarScale() as L.Control).addTo(map);

    const fitToBbox = () => {
      const m = mapInst.current;
      if (!m || !bbox) return;
      const b = L.latLngBounds(
        [bbox[1], bbox[0]] as [number, number],
        [bbox[3], bbox[2]] as [number, number]
      );
      if (b.isValid()) m.fitBounds(b, { padding: [30, 30] });
    };
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        mapInst.current?.invalidateSize();
        fitToBbox();
      })
    );

    if (typeof ResizeObserver !== "undefined" && mapRef.current) {
      const ro = new ResizeObserver(() => mapInst.current?.invalidateSize());
      ro.observe(mapRef.current);
      resizeObs.current = ro;
    }

    setMapReady(true);
  }, [center, bbox, hasLayer, ds.typename, publicBase, site, basemap, setMapReady]);

  useEffect(() => {
    initMap();
  }, [initMap]);

  useEffect(() => {
    return () => {
      resizeObs.current?.disconnect();
      resizeObs.current = null;
      if (mapInst.current) { mapInst.current.remove(); mapInst.current = null; }
    };
  }, []);

  useEffect(() => {
    if (!mapInst.current) return;
    if (currentBasemap.current) mapInst.current.removeLayer(currentBasemap.current);
    const bm = BASEMAPS[basemap];
    if (bm) {
      bm.addTo(mapInst.current);
      currentBasemap.current = bm;
      if (dataLayer.current) dataLayer.current.bringToFront();
    } else {
      currentBasemap.current = null;
    }
  }, [basemap]);

  useEffect(() => {
    if (dataLayer.current) {
      dataLayer.current.setOpacity(opacity / 100);
    }
  }, [opacity]);

  return <div ref={mapRef} style={{ width: "100%", height: "100%" }} />;
}
