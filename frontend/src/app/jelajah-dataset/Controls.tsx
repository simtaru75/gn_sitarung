"use client";

import { useRouter } from "next/navigation";
import { type ReactNode } from "react";
import type { DsFilterKey, FacetOpt } from "@/lib/geonode";
import { useNav } from "@/lib/use-nav";

const GROUPS: { key: DsFilterKey; title: string; empty: string; icon: ReactNode }[] = [
  { key: "walidata", title: "Walidata", empty: "Belum ada metadata walidata.", icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /> },
  { key: "kategori", title: "Kategori", empty: "Belum ada kategori.", icon: <path d="M3 7h18M3 12h18M3 17h18" /> },
  { key: "feature", title: "Feature", empty: "Belum ada tipe fitur.", icon: <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" /> },
  { key: "wilayah", title: "Wilayah", empty: "Belum ada metadata wilayah.", icon: <><path d="M21 10c0 7-9 12-9 12s-9-5-9-12a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></> },
];

export function FilterSidebar({
  facets,
  selected,
  showReset,
}: {
  facets: Record<DsFilterKey, FacetOpt[]>;
  selected: Record<DsFilterKey, string[]>;
  showReset: boolean;
}) {
  const nav = useNav("/jelajah-dataset");
  const router = useRouter();
  const toggle = (key: DsFilterKey, value: string, checked: boolean) => {
    nav((p) => {
      const vals = p.getAll(key).filter((v) => v !== value);
      p.delete(key);
      vals.forEach((v) => p.append(key, v));
      if (checked) p.append(key, value);
    });
  };
  return (
    <aside className="dataset-sidebar">
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
                  <input type="checkbox" checked={selected[g.key].includes(o.value)} onChange={(e) => toggle(g.key, o.value, e.target.checked)} />
                  <span className="filter-checkbox" />
                  {o.label}
                  <span className="filter-count">{o.count}</span>
                </label>
              ))
            )}
          </div>
        </div>
      ))}
      {showReset && (
        <button type="button" className="filter-reset rounded-xl" onClick={() => router.push("/jelajah-dataset")}>
          Reset Filter
        </button>
      )}
    </aside>
  );
}

export function SearchBar({ q }: { q: string }) {
  const nav = useNav("/jelajah-dataset");
  const submit = (val: string) => nav((p) => { p.delete("q"); if (val.trim()) p.set("q", val.trim()); });
  return (
    <form
      className="explore-searchbar rounded-xl overflow-hidden"
      onSubmit={(e) => {
        e.preventDefault();
        submit(String(new FormData(e.currentTarget).get("q") ?? ""));
      }}
    >
      <svg className="esb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
      <input key={q} className="esb-input" type="text" name="q" defaultValue={q} placeholder="Cari dataset — judul, abstrak, atau kata kunci…" />
        <button className="esb-btn rounded-r-xl" type="submit">Cari</button>
      {q && (
        <button className="esb-clear" type="button" title="Bersihkan pencarian" onClick={() => submit("")}>
          &times;
        </button>
      )}
    </form>
  );
}

export function SortSelect({ sort }: { sort: string }) {
  const nav = useNav("/jelajah-dataset");
  return (
    <select
      className="dataset-sort rounded-lg"
      defaultValue={sort}
      onChange={(e) => {
        const v = e.target.value;
        nav((p) => { p.delete("sort"); if (v && v !== "recent") p.set("sort", v); });
      }}
    >
      <option value="recent">Terbaru</option>
      <option value="views">Paling diakses</option>
      <option value="az">Nama A–Z</option>
      <option value="year">Tahun ↓</option>
    </select>
  );
}
