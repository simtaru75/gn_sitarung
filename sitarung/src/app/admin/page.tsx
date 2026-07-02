import { getLandingData } from "@/lib/geonode";

export const dynamic = "force-dynamic";

export default async function AdminDashboardPage() {
  let data;
  try {
    data = await getLandingData();
  } catch {
    data = null;
  }

  const statCards = [
    {
      label: "Dokumen Kebijakan",
      value: data?.documentsTotal ?? "—",
      sub: "Perda, Perbup, RPJMD, Renstra",
      color: "from-folur-600 to-folur-700",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
        </svg>
      ),
    },
    {
      label: "Layer Spasial",
      value: data?.datasetsTotal ?? "—",
      sub: "Vektor & raster terpublish",
      color: "from-sky-600 to-sky-700",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M9 20l-5.447-2.724A1 1 0 0 1 3 16.382V5.618a1 1 0 0 1 1.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0 0 21 18.382V7.618a1 1 0 0 0-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      ),
    },
    {
      label: "Screening AKURAT",
      value: data?.screeningTotal ?? "—",
      sub: "Realtime AoI · Audit Log",
      color: "from-earth-600 to-earth-700",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      ),
    },
    {
      label: "Berita & Komoditas",
      value: data?.komoditas?.length ?? "—",
      sub: "Fokus permasalahan tata ruang",
      color: "from-emerald-600 to-emerald-700",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 13a2 2 0 0 1-2-2V7m2 13a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      ),
    },
  ];

  const quickLinks = [
    { href: "/admin/design", label: "Desain & Tema", desc: "Atur palet warna, font, dan identitas visual situs." },
    { href: "/admin/features", label: "Fitur Halaman Depan", desc: "Aktifkan/nonaktifkan seksi landing page." },
    { href: "/admin/geoportal", label: "Pengaturan Geoportal", desc: "Kelola layer peta, WMS/WFS, dan katalog spasial." },
    { href: "/admin/database", label: "Database", desc: "Lihat & kelola dokumen, dataset, dan metadata." },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Ringkasan data dan akses cepat ke panel administrasi SITARUNG.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 flex items-start gap-4 hover:shadow-md transition-shadow"
          >
            <div className={`shrink-0 w-11 h-11 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center text-white`}>
              {card.icon}
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-extrabold text-gray-900">{card.value}</p>
              <p className="text-sm font-semibold text-gray-700 mt-0.5">{card.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{card.sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-4">Akses Cepat</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {quickLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-folur-200 transition-all group"
            >
              <h3 className="font-semibold text-gray-900 group-hover:text-folur-700 transition-colors">
                {link.label}
              </h3>
              <p className="text-sm text-gray-500 mt-1">{link.desc}</p>
            </a>
          ))}
        </div>
      </div>

      {/* Status koneksi */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-bold text-gray-900 mb-3">Status Sistem</h2>
        <div className="flex flex-wrap gap-4 text-sm">
          <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            GeoNode Terhubung
          </span>
          <span className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            {data ? "Data tersedia" : "Data tidak tersedia"}
          </span>
        </div>
      </div>
    </div>
  );
}
