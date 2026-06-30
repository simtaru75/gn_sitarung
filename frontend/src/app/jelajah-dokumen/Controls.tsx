"use client";

import { useRouter } from "next/navigation";
import { type ReactNode } from "react";
import type { DocFilterKey, FacetOpt } from "@/lib/geonode";
import { useNav } from "@/lib/use-nav";

const GROUPS: { key: DocFilterKey; title: string; empty: string; icon: ReactNode }[] = [
  { key: "walidata", title: "Produsen / Walidata", empty: "Belum ada produsen.", icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /> },
  { key: "kategori", title: "Kategori", empty: "Belum ada kategori.", icon: <path d="M3 7h18M3 12h18M3 17h18" /> },
  { key: "tahun", title: "Tahun", empty: "Belum ada tahun.", icon: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></> },
  { key: "format", title: "Format", empty: "Belum ada format.", icon: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /></> },
  { key: "wilayah", title: "Wilayah", empty: "Belum ada wilayah.", icon: <><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></> },
];

export function FilterSidebar({
  facets,
  selected,
  hasActiveFilter,
}: {
  facets: Record<DocFilterKey, FacetOpt[]>;
  selected: Record<DocFilterKey, string[]>;
  hasActiveFilter: boolean;
}) {
  const nav = useNav("/jelajah-dokumen");
  const router = useRouter();

  const toggle = (key: DocFilterKey, value: string, checked: boolean) => {
    nav((p) => {
      const vals = p.getAll(key).filter((v) => v !== value);
      p.delete(key);
      vals.forEach((v) => p.append(key, v));
      if (checked) p.append(key, value);
    });
  };

  return (
    <aside className="pd-aside" aria-label="Filter dokumen">
      {GROUPS.map((g) => (
        <div className="filter-card rounded-xl overflow-hidden" key={g.key}>
          <div className="filter-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">{g.icon}</svg>
            <div className="filter-card-title">{g.title}</div>
          </div>
          <div className="filter-card-body">
            {facets[g.key].length === 0 ? (
              <div className="filter-empty">{g.empty}</div>
            ) : (
              facets[g.key].map((o) => (
                <label className="filter-option" key={o.value}>
                  <input
                    type="checkbox"
                    checked={selected[g.key].includes(o.value)}
                    onChange={(e) => toggle(g.key, o.value, e.target.checked)}
                  />
                  <span className="filter-checkbox" />
                  {o.label}
                  <span className="filter-count">{o.count}</span>
                </label>
              ))
            )}
          </div>
        </div>
      ))}
      {hasActiveFilter && (
        <button type="button" className="filter-reset rounded-xl" onClick={() => router.push("/jelajah-dokumen")}>
          Reset Filter
        </button>
      )}
    </aside>
  );
}

export function SearchBox({ q }: { q: string }) {
  const nav = useNav("/jelajah-dokumen");
  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const val = String(new FormData(e.currentTarget).get("q") ?? "").trim();
    nav((p) => {
      p.delete("q");
      if (val) p.set("q", val);
    });
  };
  return (
    <form className="pd-search rounded-xl" onSubmit={onSubmit}>
      <input key={q} type="search" name="q" defaultValue={q} placeholder="Dokumen apa yang ingin Anda cari?" aria-label="Cari dokumen" />
      <button type="submit" aria-label="Cari">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.2-3.2" /></svg>
      </button>
    </form>
  );
}
