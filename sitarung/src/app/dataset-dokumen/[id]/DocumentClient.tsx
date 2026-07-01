"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import LoadingState from "@/components/LoadingState";
import type { DocumentDetail, SiteIdentity } from "@/lib/geonode";

export default function DocumentClient({
  doc,
  site,
  publicBase,
}: {
  doc: DocumentDetail;
  site: SiteIdentity | null;
  publicBase: string;
}) {
  const asset = useCallback((path: string) => `${publicBase}${path}`, [publicBase]);

  return (
    <div className="flex flex-col h-screen overflow-hidden font-sans" style={{ background: "var(--cream)", color: "var(--ink)", fontSize: 14, lineHeight: 1.55, fontFamily: "var(--sans)" }}>
      {/* ===== HEADER ===== */}
      <header className="flex-shrink-0 flex items-center gap-4 px-6 py-3 z-50" style={{ background: "var(--forest)", color: "var(--cream)" }}>
        <a
          href="/jelajah-dokumen"
          className="inline-flex items-center gap-2 text-sm px-4 py-1.5 border rounded transition"
          style={{ color: "var(--cream-300)", borderColor: "var(--cream-a25)" }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "var(--cream-a10)"; e.currentTarget.style.color = "var(--cream)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = ""; }}
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Dokumen
        </a>
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="h-10 w-10 flex-shrink-0 flex items-center justify-center overflow-hidden" style={{ background: "var(--cream)", color: "var(--forest)" }}>
            {site?.logo ? (
              <img src={site.logo} alt="Logo" className="w-full h-full object-contain p-0.5 box-border" />
            ) : (
              <span style={{ fontFamily: "var(--serif)", fontWeight: 600 }}>L</span>
            )}
          </div>
          <div>
            <div className="text-[9px] tracking-[0.16em] uppercase" style={{ fontFamily: "var(--font-sans)", color: "var(--ochre)" }}>
              Dokumen Kebijakan · {site?.namaKabupaten ?? "Sumatera Selatan"}
            </div>
            <div
              className="text-[17px] font-medium leading-tight whitespace-nowrap overflow-hidden text-ellipsis"
              style={{ fontFamily: "var(--font-sans)", maxWidth: "48vw" }}
              title={doc.title}
            >
              {doc.title}
            </div>
          </div>
        </div>
        <div className="flex-1" />
      </header>

      {/* ===== BODY ===== */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_360px] min-h-0" style={{ gridTemplateRows: "minmax(0,1fr)" }}>
        {/* ===== VIEWER ===== */}
        <div className="flex flex-col min-w-0 min-h-0" style={{ background: "var(--viewer-bg)" }}>
          {doc.canDownload && doc.hasFile && doc.isPdf ? (
            <PdfViewer fileUrl={doc.fileUrl} filename={doc.title} />
          ) : doc.canDownload && doc.hasFile && doc.isImage ? (
            <ImageViewer fileUrl={doc.fileUrl} filename={doc.title} />
          ) : doc.canDownload && doc.hasFile ? (
            <DownloadFallback extension={doc.extension} fileUrl={doc.fileUrl} />
          ) : (
            <LockedView canDownload={doc.canDownload} />
          )}
        </div>

        {/* ===== SIDEBAR ===== */}
        <aside
          className="overflow-y-auto px-5 py-6 lg:pb-10 border-l"
          style={{ background: "var(--paper)", borderColor: "var(--line-strong)", fontFamily: "var(--font-sans)" }}
        >
          <div className="text-[10px] tracking-[0.16em] uppercase mb-2" style={{ fontFamily: "var(--font-sans)", color: "var(--ochre-600)" }}>Metadata Dokumen</div>
          <h1
            className="text-2xl font-medium leading-tight mb-3.5 break-words"
            style={{ fontFamily: "var(--font-serif)", color: "var(--forest)", letterSpacing: "-0.01em" }}
          >
            {doc.title}
          </h1>

          {/* Badges */}
          <div className="flex flex-wrap gap-1.5 mb-5">
            {doc.docType && (
              <span className="text-[9px] font-semibold uppercase tracking-[0.08em] px-2 py-1" style={{ background: "var(--ochre)", color: "var(--forest)" }}>
                {doc.docType}
              </span>
            )}
            {doc.extension && (
              <span className="text-[9px] font-semibold uppercase tracking-[0.08em] px-2 py-1 border" style={{ color: "var(--forest)", borderColor: "var(--line-strong)", background: "transparent" }}>
                .{doc.extension}
              </span>
            )}
            <span
              className="text-[9px] font-semibold uppercase tracking-[0.08em] px-2 py-1"
              style={doc.canDownload ? { background: "var(--sage)", color: "var(--forest)" } : { background: "var(--danger)", color: "var(--cream)" }}
            >
              {doc.canDownload ? "Dapat diunduh" : "Hanya metadata"}
            </span>
          </div>

          {/* Ringkasan */}
          <div className="mb-6">
            <div className="text-[10px] tracking-[0.14em] uppercase pb-2 mb-3 border-b" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)", borderColor: "var(--line)" }}>Ringkasan</div>
            {doc.hasRealAbstract ? (
              <p className="text-[15px] leading-relaxed font-light" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-600)" }}>
                {doc.abstract}
              </p>
            ) : (
              <p className="text-[13px] italic" style={{ color: "var(--ink-400)" }}>Belum ada abstrak metadata untuk dokumen ini.</p>
            )}
          </div>

          {/* Informasi */}
          <div className="mb-6">
            <div className="text-[10px] tracking-[0.14em] uppercase pb-2 mb-3 border-b" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)", borderColor: "var(--line)" }}>Informasi</div>
            <MetaRow label="Jenis" value={doc.docType || "Dokumen"} />
            <MetaRow label="Pengelola" value={doc.pengelola} />
            <MetaRow label="Walidata" value={doc.walidata} />
            <MetaRow label="Kategori" value={doc.kategori} />
            <MetaRow label="Tahun" value={doc.year ? String(doc.year) : ""} />
            {doc.language && <MetaRow label="Bahasa" value={doc.language} />}
            {doc.licenseName && <MetaRow label="Lisensi" value={doc.licenseName} />}
            {doc.attribution && <MetaRow label="Atribusi" value={doc.attribution} />}
            <MetaRow label="Diakses" value={doc.viewsCount ? `${doc.viewsCount}×` : "0×"} />
          </div>

          {/* Informasi Tambahan */}
          {doc.supplemental && (
            <div className="mb-6">
              <div className="text-[10px] tracking-[0.14em] uppercase pb-2 mb-3 border-b" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)", borderColor: "var(--line)" }}>Informasi Tambahan</div>
              <p className="text-[13px] leading-relaxed font-light" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-600)" }}>
                {doc.supplemental.split("\n").map((line, i) => <span key={i}>{line}<br /></span>)}
              </p>
            </div>
          )}

          {/* Wilayah */}
          {doc.regions.length > 0 && (
            <div className="mb-6">
              <div className="text-[10px] tracking-[0.14em] uppercase pb-2 mb-3 border-b" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)", borderColor: "var(--line)" }}>Wilayah</div>
              <div className="flex flex-wrap gap-1.5">
                {doc.regions.map((r) => (
                  <span key={r} className="text-[11px] px-2 py-1 border" style={{ color: "var(--forest)", background: "var(--cream-200)", borderColor: "var(--line)" }}>{r}</span>
                ))}
              </div>
            </div>
          )}

          {/* Kata Kunci */}
          {doc.keywords.length > 0 && (
            <div className="mb-6">
              <div className="text-[10px] tracking-[0.14em] uppercase pb-2 mb-3 border-b" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)", borderColor: "var(--line)" }}>Kata Kunci</div>
              <div className="flex flex-wrap gap-1.5">
                {doc.keywords.map((k) => (
                  <span key={k} className="text-[11px] px-2 py-1 border" style={{ color: "var(--forest)", background: "var(--cream-200)", borderColor: "var(--line)" }}>{k}</span>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="grid py-2 text-[13px] border-b"
      style={{ gridTemplateColumns: "110px 1fr", gap: 10, borderColor: "var(--line)" }}
    >
      <div className="text-[10px] tracking-[0.06em] uppercase pt-0.5" style={{ fontFamily: "var(--font-sans)", color: "var(--ink-400)" }}>{label}</div>
      <div style={{ color: "var(--ink)" }}>{value || "—"}</div>
    </div>
  );
}

/* ================================================================== */
/*  PDF Viewer                                                        */
/* ================================================================== */

function PdfViewer({ fileUrl, filename }: { fileUrl: string; filename: string }) {
  const canvasAreaRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1.2);
  const [numPages, setNumPages] = useState(0);
  const [current, setCurrent] = useState(1);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const pageNumRef = useRef<HTMLInputElement>(null);

  const pdfRef = useRef<unknown>(null);
  const baseSizes = useRef<Record<number, { width: number; height: number }>>({});
  const divs = useRef<Record<number, HTMLDivElement>>({});
  const canvases = useRef<Record<number, HTMLCanvasElement>>({});
  const rendered = useRef<Record<number, boolean>>({});
  const tasks = useRef<Record<number, unknown>>({});

  const goTo = useCallback((num: number) => {
    const n = Math.min(Math.max(1, num), numPages);
    setCurrent(n);
    const d = divs.current[n];
    if (d && canvasAreaRef.current) {
      canvasAreaRef.current.scrollTo({ top: d.offsetTop - 12, behavior: "smooth" });
    }
  }, [numPages]);

  const rerenderAll = useCallback(() => {
    const pdf: Record<string, unknown> = pdfRef.current as Record<string, unknown>;
    if (!pdf) return;
    for (let i = 1; i <= numPages; i++) {
      rendered.current[i] = false;
      const d = divs.current[i];
      if (!d) continue;
      const s = baseSizes.current[i];
      if (!s) return;
      d.style.width = Math.floor(s.width * scale) + "px";
      d.style.height = Math.floor(s.height * scale) + "px";
    }
    // trigger visible render
    const area = canvasAreaRef.current;
    if (!area) return;
    const top = area.scrollTop - 500;
    const bottom = area.scrollTop + area.clientHeight + 500;
    for (let i = 1; i <= numPages; i++) {
      const d = divs.current[i];
      if (!d) continue;
      const dbot = d.offsetTop + d.offsetHeight;
      if (dbot >= top && d.offsetTop <= bottom) renderPage(i, scale);
    }
  }, [numPages, scale]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // <Script> PDF.js dimuat async (afterInteractive) — bisa belum siap
        // saat efek ini jalan. Tunggu window.pdfjsLib hingga ~15 dtk.
        const win = window as unknown as Record<string, unknown>;
        let pdfjsLib = win.pdfjsLib as Record<string, unknown> | undefined;
        const deadline = Date.now() + 15000;
        while (!pdfjsLib && Date.now() < deadline) {
          await new Promise((r) => setTimeout(r, 100));
          if (cancelled) return;
          pdfjsLib = win.pdfjsLib as Record<string, unknown> | undefined;
        }
        if (!pdfjsLib) { setError("Gagal memuat pustaka PDF."); return; }
        (pdfjsLib.GlobalWorkerOptions as Record<string, unknown>).workerSrc = "/pdfjs/pdf.worker.min.js";
        const getDoc = pdfjsLib.getDocument as (opts: Record<string, unknown>) => { promise: Promise<Record<string, unknown>> };

        const task = getDoc({
          url: fileUrl,
          disableRange: true,
          disableStream: true,
        });
        // Berkas besar diunduh penuh dulu (xref PDF di akhir file) — tampilkan
        // persentase supaya tidak tampak macet di "Memuat dokumen…".
        (task as unknown as Record<string, unknown>).onProgress = (p: { loaded: number; total?: number }) => {
          if (p.total) setProgress(Math.min(Math.round((p.loaded / p.total) * 100), 100));
        };
        const pdf = await task.promise;
        if (cancelled) return;

        pdfRef.current = pdf;
        const np = Number(pdf.numPages);
        setNumPages(np);

        const jobs: Promise<void>[] = [];
        // bind(pdf): getPage butuh this (this._transport) — unbound = TypeError.
        const getPage = (pdf.getPage as (n: number) => Promise<{ getViewport: (opts: Record<string, number>) => { width: number; height: number } }>).bind(pdf);
        for (let i = 1; i <= np; i++) {
          jobs.push(
            getPage(i).then((page) => {
              const vp = page.getViewport({ scale: 1 });
              baseSizes.current[i] = { width: vp.width, height: vp.height };
            })
          );
        }
        await Promise.all(jobs);
        if (cancelled) return;

        const area = canvasAreaRef.current;
        const s = baseSizes.current[1];
        const avail = (area?.clientWidth ?? 960) - 48;
        const newScale = s && s.width > 0 && avail > 0
          ? (avail / s.width) < 1 ? Math.max(avail / s.width, 0.3) : 1.0
          : 1.0;
        setScale(newScale);

        setLoading(false);
      } catch (e) {
        if (process.env.NODE_ENV !== "production") console.error("PDF.js gagal memuat dokumen:", e);
        const msg = e instanceof Error && e.message ? ` (${e.name}: ${e.message})` : "";
        if (!cancelled) setError(`Gagal memuat dokumen PDF.${msg}`);
        setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [fileUrl]);

  function renderPage(num: number, sc: number) {
    const pdf = pdfRef.current as Record<string, unknown>;
    if (!pdf || rendered.current[num]) return;
    rendered.current[num] = true;
    // bind(pdf): getPage butuh this (this._transport) — unbound = TypeError.
    const getPage = (pdf.getPage as (n: number) => Promise<{ getViewport: (opts: Record<string, number>) => { width: number; height: number }; render: (opts: Record<string, unknown>) => { promise: Promise<void> } }>).bind(pdf);
    getPage(num).then((page) => {
      if (!rendered.current[num]) return;
      const ratio = window.devicePixelRatio || 1;
      const vp = page.getViewport({ scale: sc });
      const c = canvases.current[num];
      if (!c) return;
      c.width = Math.floor(vp.width * ratio);
      c.height = Math.floor(vp.height * ratio);
      c.style.width = Math.floor(vp.width) + "px";
      c.style.height = Math.floor(vp.height) + "px";
      const task = page.render({
        canvasContext: c.getContext("2d"),
        viewport: vp,
        transform: ratio !== 1 ? [ratio, 0, 0, ratio, 0, 0] : null,
      });
      task.promise.catch(() => {});
    });
  }

  return (
    <>
      {/* Toolbar */}
      <div className="flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 border-b" style={{ background: "var(--viewer-toolbar)", borderColor: "var(--viewer-toolbar-border)" }}>
        <div className="flex items-center gap-1">
          <button className="vt-btn" onClick={() => goTo(current - 1)} title="Halaman sebelumnya" disabled={current <= 1}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><polyline points="15 18 9 12 15 6" /></svg>
          </button>
          <input
            ref={pageNumRef}
            type="number"
            value={current}
            min={1}
            max={numPages}
            onChange={(e) => goTo(parseInt(e.target.value, 10) || 1)}
            className="w-[42px] text-center text-xs rounded px-0.5 py-1"
            style={{ background: "var(--viewer-bg)", border: "1px solid var(--viewer-border)", color: "var(--viewer-fg-strong)", fontFamily: "var(--mono)" }}
          />
          <span className="text-xs" style={{ fontFamily: "var(--mono)", color: "var(--viewer-fg)" }}>/ {numPages || "…"}</span>
          <button className="vt-btn" onClick={() => goTo(current + 1)} title="Halaman berikutnya" disabled={current >= numPages}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
        </div>
        <div className="w-px h-5 mx-1.5" style={{ background: "var(--viewer-border)" }} />
        <div className="flex items-center gap-1">
          <button className="vt-btn" onClick={() => { setScale((s) => Math.max(s - 0.2, 0.3)); }} title="Perkecil">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><line x1="5" y1="12" x2="19" y2="12" /></svg>
          </button>
          <span className="text-xs min-w-[46px] text-center" style={{ fontFamily: "var(--mono)", color: "var(--viewer-fg)" }}>{Math.round(scale * 100)}%</span>
          <button className="vt-btn" onClick={() => { setScale((s) => Math.min(s + 0.2, 4)); }} title="Perbesar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          </button>
          <button className="vt-btn" onClick={() => {
            const s = baseSizes.current[1];
            const avail = (canvasAreaRef.current?.clientWidth ?? 960) - 48;
            if (s && avail > 0) setScale(Math.min(Math.max(avail / s.width, 0.3), 3));
          }} title="Sesuaikan lebar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><path d="M21 3H3v18h18z" /><path d="M8 12h8M8 12l3-3M8 12l3 3M16 12l-3-3M16 12l-3 3" /></svg>
          </button>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-1">
          <PrintButton fileUrl={fileUrl} />
          <a className="vt-btn accent" href={`${fileUrl}?dl=1`} download title="Unduh">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
          </a>
        </div>
      </div>

      {/* Canvas area */}
      <div ref={canvasAreaRef} className="flex-1 min-h-0 overflow-auto p-6 flex flex-col items-center" style={{ alignContent: "safe center" }}>
        <style>{vtBtnStyles}</style>
        {loading && (
          <LoadingState
            label={`Memuat dokumen…${progress > 0 ? ` ${progress}%` : ""}`}
            className="m-auto"
            spinnerClassName="h-12 w-12 opacity-80"
            labelClassName="text-xs font-semibold tracking-[0.14em] uppercase"
            labelStyle={{ fontFamily: "var(--mono)", color: "var(--viewer-loading)" }}
          />
        )}
        {error && <div className="text-xs text-center m-auto max-w-xs leading-relaxed" style={{ fontFamily: "var(--mono)", color: "var(--viewer-msg)" }}>{error}</div>}
        <div id="pdfPages" className="flex flex-col items-center gap-4">
          {!loading && !error && Array.from({ length: numPages }, (_, i) => i + 1).map((n) => (
            <PdfPage key={n} num={n} baseSizes={baseSizes} divs={divs} canvases={canvases} scale={scale} onRender={(num) => renderPage(num, scale)} numPages={numPages} current={current} setCurrent={setCurrent} />
          ))}
        </div>
      </div>

      {/* CSS for vt-btn */}
      <style>{vtBtnStyles}</style>

      {/* Scale re-render */}
      <ScaleEffect scale={scale} rerenderAll={rerenderAll} />
    </>
  );
}

const vtBtnStyles = `
  .vt-btn { width:30px; height:30px; display:grid; place-items:center; cursor:pointer; background:transparent; border:1px solid transparent; color:var(--viewer-fg); border-radius:3px; transition:all 0.12s; }
  .vt-btn:hover { background:var(--viewer-btn-hover); color:var(--viewer-fg-strong); }
  .vt-btn:disabled { opacity:0.35; cursor:default; }
  .vt-btn.accent { color:var(--cream); background:var(--forest-500); }
  .vt-btn.accent:hover { background:var(--ochre); color:var(--forest); }
`;

function ScaleEffect({ scale, rerenderAll }: { scale: number; rerenderAll: () => void }) {
  useEffect(() => {
    rerenderAll();
  }, [scale]);
  return null;
}

function PrintButton({ fileUrl }: { fileUrl: string }) {
  return (
    <button
      className="vt-btn accent"
      title="Cetak"
      onClick={() => {
        const ifr = document.createElement("iframe");
        ifr.style.position = "fixed";
        ifr.style.right = "0";
        ifr.style.bottom = "0";
        ifr.style.width = "0";
        ifr.style.height = "0";
        ifr.style.border = "0";
        ifr.src = fileUrl;
        ifr.onload = () => {
          try { ifr.contentWindow?.focus(); ifr.contentWindow?.print(); } catch { window.open(fileUrl, "_blank"); }
        };
        document.body.appendChild(ifr);
      }}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><rect x="6" y="14" width="12" height="8" /></svg>
    </button>
  );
}

function PdfPage({
  num,
  baseSizes,
  divs,
  canvases,
  scale,
  onRender,
  numPages,
  current,
  setCurrent,
}: {
  num: number;
  baseSizes: React.MutableRefObject<Record<number, { width: number; height: number }>>;
  divs: React.MutableRefObject<Record<number, HTMLDivElement>>;
  canvases: React.MutableRefObject<Record<number, HTMLCanvasElement>>;
  scale: number;
  onRender: (num: number) => void;
  numPages: number;
  current: number;
  setCurrent: (n: number) => void;
}) {
  const divRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (divRef.current) divs.current[num] = divRef.current;
    if (canvasRef.current) canvases.current[num] = canvasRef.current;
    const s = baseSizes.current[num];
    if (s && divRef.current) {
      divRef.current.style.width = Math.floor(s.width * scale) + "px";
      divRef.current.style.height = Math.floor(s.height * scale) + "px";
    }
  }, [scale]);

  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            onRender(num);
          }
        });
      },
      { rootMargin: "500px 0px", threshold: 0.01 }
    );
    if (divRef.current) io.observe(divRef.current);
    return () => io.disconnect();
  }, [num, onRender]);

  return (
    <div
      ref={divRef}
      className="pdf-page bg-white flex-shrink-0 leading-[0]"
      style={{ boxShadow: "var(--viewer-page-shadow)" }}
      data-page={num}
    >
      <canvas ref={canvasRef} className="block" />
    </div>
  );
}

/* ================================================================== */
/*  Image Viewer                                                      */
/* ================================================================== */

function ImageViewer({ fileUrl, filename }: { fileUrl: string; filename: string }) {
  return (
    <>
      <div className="flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 border-b" style={{ background: "var(--viewer-toolbar)", borderColor: "var(--viewer-toolbar-border)" }}>
        <span className="text-[11px] whitespace-nowrap overflow-hidden text-ellipsis" style={{ fontFamily: "var(--mono)", color: "var(--viewer-fg-dim)" }}>{filename}</span>
        <div className="flex-1" />
        <a className="vt-btn accent" href={`${fileUrl}?dl=1`} download title="Unduh">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[17px] h-[17px]"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
        </a>
      </div>
      <div className="flex-1 min-h-0 overflow-auto p-6 flex items-center justify-center">
        <img src={fileUrl} alt={filename} className="max-w-full h-auto shadow-lg" />
      </div>
      <style>{vtBtnStyles}</style>
    </>
  );
}

/* ================================================================== */
/*  Download Fallback (non-PDF, non-image)                            */
/* ================================================================== */

function DownloadFallback({ extension, fileUrl }: { extension: string; fileUrl: string }) {
  return (
    <div className="flex-1 min-h-0 overflow-auto p-6 flex items-center justify-center">
      <div className="text-center max-w-sm leading-relaxed" style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--viewer-msg)" }}>
        <svg className="w-[46px] h-[46px] opacity-40 mx-auto mb-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /></svg>
        <div>Pratinjau tidak tersedia untuk jenis berkas{extension ? <strong>.{extension}</strong> : ""} ini.</div>
        <a className="inline-block mt-4 px-5 py-2.5 text-xs tracking-[0.06em]" href={`${fileUrl}?dl=1`} download style={{ background: "var(--forest-500)", color: "var(--cream)", fontFamily: "var(--mono)", textDecoration: "none" }} onMouseEnter={(e) => { e.currentTarget.style.background = "var(--ochre)"; e.currentTarget.style.color = "var(--forest)"; }} onMouseLeave={(e) => { e.currentTarget.style.background = ""; e.currentTarget.style.color = ""; }}>
          Unduh berkas
        </a>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Locked / No-Access View                                           */
/* ================================================================== */

function LockedView({ canDownload }: { canDownload: boolean }) {
  return (
    <div className="flex-1 min-h-0 overflow-auto p-6 flex items-center justify-center">
      <div className="text-center max-w-sm leading-relaxed" style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--viewer-msg)" }}>
        <svg className="w-[46px] h-[46px] opacity-40 mx-auto mb-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
        {!canDownload ? (
          <div><strong>Hanya metadata.</strong><br />Pratinjau & unduhan dokumen ini dibatasi sesuai izin akses. Metadata di sebelah kanan tetap dapat dilihat.</div>
        ) : (
          <div>Berkas dokumen tidak tersedia di server.</div>
        )}
      </div>
    </div>
  );
}
