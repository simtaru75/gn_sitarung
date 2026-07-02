"use client";

import { useState, useCallback } from "react";

// ============================================================================
// Data tema — disinkronkan dengan _theme_vars.html (Django) dan globals.css
// ============================================================================
interface ThemeDef {
  id: string;
  name: string;
  tagline: string;
  description: string;
  colors: string[];
}

const THEMES: ThemeDef[] = [
  {
    id: "simtaru", name: "Simtaru", tagline: "Sumatera Selatan",
    description: "Hijau Musi, krem tanah rawa, dan emas Sumatera Selatan. Default DST — palet khas provinsi dengan karakter tata ruang wilayah.",
    colors: ["#0b4b3f", "#0db390", "#f8fafb", "#f0fbfa", "#2EC4B6"],
  },
  {
    id: "pesisir", name: "Pesisir", tagline: "Tropical Coastal",
    description: "Teal laut dalam, pasir hangat, dan koral senja. Untuk kabupaten maritim/kepulauan dengan ekonomi berbasis perikanan.",
    colors: ["#0E3F4F", "#D87A3C", "#F0EAD7", "#6E3E1F", "#8AA8A8"],
  },
  {
    id: "pegunungan", name: "Pegunungan", tagline: "Highland Stoic",
    description: "Slate biru-abu hutan pinus, putih alpine, dan tembaga hangat. Untuk kabupaten dataran tinggi berkontur tegas.",
    colors: ["#2A3848", "#B5763C", "#ECECE6", "#5C3F2A", "#93A099"],
  },
  {
    id: "vulkanik", name: "Vulkanik", tagline: "Ash & Ember",
    description: "Charcoal vulkanik, abu putih, dan bara merah. Untuk kabupaten sekitar gunung api — kontras tinggi, konteks mitigasi bencana.",
    colors: ["#2B2826", "#B83F2E", "#EFE9DF", "#4A2A1C", "#8A8377"],
  },
  {
    id: "rawa", name: "Rawa", tagline: "Wetland Marigold",
    description: "Gambut hijau-zaitun, mist krem, dan marigold tua. Untuk kabupaten ekosistem rawa/gambut dengan komoditas sagu/sawit gambut.",
    colors: ["#2F3A26", "#CC9430", "#EEE9D9", "#5A3A1A", "#9AAB87"],
  },
  {
    id: "modern", name: "Modern", tagline: "Teal Pemerintahan",
    description: "Teal birokrasi, abu muda, dan putih bersih. Tampilan formal-modern bergaya portal pemerintahan — netral untuk kabupaten mana pun.",
    colors: ["#256180", "#E08A3C", "#EAEDF1", "#2C3E46", "#8FA6AE"],
  },
  {
    id: "pastel", name: "Pastel", tagline: "Cerah Lembut",
    description: "Lavender lembut, merah muda pastel, dan mint. Nuansa cerah-ramah yang ringan — cocok untuk tampilan publik yang hangat dan mengundang.",
    colors: ["#5E4A82", "#E89BBE", "#FBF4F7", "#8A6D9C", "#A8C3B5"],
  },
  {
    id: "kontras", name: "Kontras", tagline: "Bold Cerah",
    description: "Navy pekat, oranye terang, dan merah berani di atas abu terang. Kontras tinggi yang tegas & mudah dibaca — menonjolkan elemen penting.",
    colors: ["#14213D", "#FCA311", "#F2F3F5", "#C1121F", "#2EC4B6"],
  },
];

interface FontCombo { label: string; serif: string; sans: string; mono: string; }

const FONT_COMBOS: Record<string, FontCombo[]> = {
  simtaru: [
    { label: "Klasik Sumsel", serif: '"Merriweather", serif', sans: '"Inter", sans-serif', mono: '"JetBrains Mono", monospace' },
    { label: "Modern Editorial", serif: '"Lora", serif', sans: '"Inter", sans-serif', mono: '"IBM Plex Mono", monospace' },
    { label: "Formal", serif: '"Playfair Display", serif', sans: '"Source Sans 3", sans-serif', mono: '"Fira Code", monospace' },
  ],
  pesisir: [
    { label: "Tropis Biru", serif: '"Lora", serif', sans: '"Inter", sans-serif', mono: '"JetBrains Mono", monospace' },
    { label: "Sans Bersih", serif: '"Merriweather", serif', sans: '"Nunito Sans", sans-serif', mono: '"Fira Code", monospace' },
  ],
  pegunungan: [
    { label: "Serif Tebal", serif: '"Playfair Display", serif', sans: '"Inter", sans-serif', mono: '"IBM Plex Mono", monospace' },
    { label: "Modern", serif: '"Merriweather", serif', sans: '"Source Sans 3", sans-serif', mono: '"JetBrains Mono", monospace' },
  ],
  vulkanik: [
    { label: "Kontras Tinggi", serif: '"Playfair Display", serif', sans: '"Inter", sans-serif', mono: '"Fira Code", monospace' },
    { label: "Geometric", serif: '"Merriweather", serif', sans: '"Nunito Sans", sans-serif', mono: '"JetBrains Mono", monospace' },
  ],
  rawa: [
    { label: "Organik", serif: '"Lora", serif', sans: '"Inter", sans-serif', mono: '"IBM Plex Mono", monospace' },
    { label: "Warm Serif", serif: '"Merriweather", serif', sans: '"Source Sans 3", sans-serif', mono: '"Fira Code", monospace' },
  ],
  modern: [
    { label: "Formal Modern", serif: '"Merriweather", serif', sans: '"Inter", sans-serif', mono: '"JetBrains Mono", monospace' },
    { label: "Clean Sans", serif: '"Lora", serif', sans: '"Nunito Sans", sans-serif', mono: '"IBM Plex Mono", monospace' },
    { label: "Pemerintahan", serif: '"Playfair Display", serif', sans: '"Source Sans 3", sans-serif', mono: '"Fira Code", monospace' },
  ],
  pastel: [
    { label: "Lembut", serif: '"Lora", serif', sans: '"Nunito Sans", sans-serif', mono: '"JetBrains Mono", monospace' },
    { label: "Feminin", serif: '"Playfair Display", serif', sans: '"Inter", sans-serif', mono: '"IBM Plex Mono", monospace' },
  ],
  kontras: [
    { label: "Bold", serif: '"Merriweather", serif', sans: '"Inter", sans-serif', mono: '"Fira Code", monospace' },
    { label: "Geometric", serif: '"Playfair Display", serif', sans: '"Nunito Sans", sans-serif', mono: '"JetBrains Mono", monospace' },
  ],
};

function loadGoogleFonts(combo: FontCombo) {
  [combo.serif, combo.sans, combo.mono].forEach((stack) => {
    const fam = stack.split(",")[0].trim().replace(/['"]/g, "");
    if (!fam || document.querySelector(`link[data-font="${fam}"]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.setAttribute("data-font", fam);
    link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(fam)}:ital,wght@0,400;0,600;0,700;1,400&display=swap`;
    document.head.appendChild(link);
  });
}

export default function DesignPage() {
  const [activeTheme, setActiveTheme] = useState<string>(() => {
    if (typeof document !== "undefined") return document.documentElement.getAttribute("data-theme") || "simtaru";
    return "simtaru";
  });
  const [previewTheme, setPreviewTheme] = useState<string | null>(null);
  const [fontIdx, setFontIdx] = useState(1);
  const [saved, setSaved] = useState(false);

  const currentTheme = previewTheme ?? activeTheme;
  const combos = FONT_COMBOS[currentTheme] || FONT_COMBOS.simtaru;
  const safeFontIdx = fontIdx >= 1 && fontIdx <= combos.length ? fontIdx : 1;

  const preview = useCallback((theme: string, fidx?: number) => {
    document.documentElement.setAttribute("data-theme", theme);
    setPreviewTheme(theme);
    const idx = (fidx ?? safeFontIdx) - 1;
    const combo = (FONT_COMBOS[theme] || FONT_COMBOS.simtaru)[idx >= 0 ? idx : 0];
    if (combo) {
      const r = document.documentElement.style;
      r.setProperty("--serif", combo.serif);
      r.setProperty("--sans", combo.sans);
      r.setProperty("--mono", combo.mono);
      loadGoogleFonts(combo);
    }
  }, [safeFontIdx]);

  const resetPreview = useCallback(() => {
    document.documentElement.setAttribute("data-theme", activeTheme);
    setPreviewTheme(null);
    setFontIdx(1);
  }, [activeTheme]);

  const saveTheme = useCallback(() => {
    const theme = previewTheme ?? activeTheme;
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/dst-auth/tema/";
    form.target = "_blank";
    const t = document.createElement("input"); t.type = "hidden"; t.name = "theme"; t.value = theme;
    form.appendChild(t);
    const f = document.createElement("input"); f.type = "hidden"; f.name = "font_option"; f.value = String(safeFontIdx);
    form.appendChild(f);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    setActiveTheme(theme);
    setPreviewTheme(null);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }, [previewTheme, activeTheme, safeFontIdx]);

  return (
    <div className="space-y-8">
      {/* header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Desain & <span className="italic font-light text-folur-600">Tema</span></h1>
          <p className="text-sm text-gray-500 mt-1">Pilih palet warna yang mencerminkan identitas kabupaten — tema berlaku ke seluruh halaman publik dan panel admin.</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-gray-400">
          Tema aktif: <strong className="text-folur-700">{activeTheme}</strong>
        </div>
      </div>

      {saved && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-medium">
          <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
          Tema <strong>{activeTheme}</strong> berhasil diterapkan ke seluruh situs.
        </div>
      )}

      {/* grid tema */}
      <div>
        <div className="flex items-baseline gap-4 mb-4 pb-3 border-b border-gray-200">
          <span className="font-serif text-lg text-gray-300">01</span>
          <h2 className="font-serif text-xl text-gray-900">Pilih <span className="italic font-light text-folur-600">tema</span></h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {THEMES.map((theme) => {
            const isActive = currentTheme === theme.id;
            return (
              <button key={theme.id} type="button" onClick={() => preview(theme.id)}
                className={`group text-left bg-white rounded-xl border-2 transition-all duration-200 overflow-hidden hover:shadow-lg ${
                  isActive ? "border-folur-500 shadow-md shadow-folur-500/10 ring-1 ring-folur-500" : "border-gray-200 hover:border-gray-300"
                }`}>
                <div className="aspect-[5/3] grid grid-cols-[2.2fr_1fr_0.8fr] grid-rows-2">
                  <div className="row-span-2" style={{background:theme.colors[0]}}/>
                  <div className="row-span-2" style={{background:theme.colors[1]}}/>
                  <div style={{background:theme.colors[2]}}/>
                  <div style={{background:theme.colors[3]}}/>
                </div>
                <div className="p-4">
                  <h3 className="font-serif text-lg font-bold text-gray-900 leading-tight">{theme.name}</h3>
                  <p className="font-mono text-[10px] uppercase tracking-wider text-folur-500 mt-0.5">{theme.tagline}</p>
                  <p className="text-xs text-gray-500 mt-2 line-clamp-3 leading-relaxed">{theme.description}</p>
                  <div className="flex gap-1 mt-3">
                    {theme.colors.map((c,i)=><span key={i} className="w-5 h-5 rounded border border-gray-200" style={{background:c}} title={c}/>)}
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <span className={`font-mono text-[10px] uppercase tracking-wider ${isActive?"text-folur-600 font-bold":"text-gray-400"}`}>
                      {isActive?"Aktif":"Tersedia"}
                    </span>
                    <span className="font-mono text-[11px] uppercase tracking-wider text-folur-600 font-semibold flex items-center gap-1 group-hover:gap-2 transition-all">
                      Pratinjau <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* apply bar */}
      <div className="bg-folur-900 text-white rounded-2xl p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-4">
          <svg className="w-5 h-5 text-folur-300" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span className="font-mono text-[10px] uppercase tracking-widest text-folur-300">Terapkan ke seluruh SITARUNG</span>
        </div>
        <h2 className="font-serif text-2xl mb-2">Tema <span className="italic text-folur-300">{currentTheme}</span> siap diterapkan</h2>
        <p className="text-folur-200/70 text-sm max-w-xl mb-6">
          Klik kartu tema di atas untuk <strong className="text-white">pratinjau langsung</strong> — seluruh halaman admin ini berubah seketika. Tekan <strong className="text-white">Terapkan tema</strong> untuk menyimpannya secara permanen ke Django backend.
        </p>
        <div className="mb-6 max-w-xs">
          <label htmlFor="fontSelect" className="block text-xs font-bold uppercase tracking-wider text-folur-300 mb-2">Kombinasi Font</label>
          <select id="fontSelect" value={safeFontIdx}
            onChange={(e) => { const idx = parseInt(e.target.value,10); setFontIdx(idx); preview(currentTheme, idx); }}
            className="w-full px-4 py-2.5 rounded-lg bg-white/10 border border-white/20 text-white text-sm focus:outline-none focus:ring-2 focus:ring-folur-400 focus:border-transparent">
            {combos.map((opt,i) => (
              <option key={i} value={i+1} className="text-gray-900">
                Opsi {i+1} — {opt.label} · {opt.serif.split(",")[0].replace(/['"]/g,"")}/{opt.sans.split(",")[0].replace(/['"]/g,"")}/{opt.mono.split(",")[0].replace(/['"]/g,"")}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={saveTheme}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-folur-300 text-folur-900 font-semibold rounded-lg text-sm hover:bg-white transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Terapkan tema
          </button>
          <button type="button" onClick={resetPreview}
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-white/20 text-white rounded-lg text-sm hover:bg-white/10 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg> Batalkan pratinjau
          </button>
        </div>
      </div>
    </div>
  );
}

