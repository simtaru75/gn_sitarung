export default function GeoportalPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Geoportal</h1>
        <p className="text-sm text-gray-500 mt-1">
          Kelola layer peta, servis WMS/WFS, dan katalog spasial.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-folur-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-folur-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" /><ellipse cx="12" cy="12" rx="4" ry="10" /><path d="M2 12h20" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-gray-900 mb-2">Pengaturan Geoportal</h2>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Konfigurasi tile server, layer WMS, dan pengaturan peta interaktif.
          Panel ini akan dikembangkan lebih lanjut.
        </p>
      </div>
    </div>
  );
}
