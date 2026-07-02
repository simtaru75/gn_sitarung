export default function DatabasePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Database</h1>
        <p className="text-sm text-gray-500 mt-1">
          Lihat dan kelola dokumen, dataset, dan metadata.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-folur-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-folur-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v6c0 1.7 6.4 3 9 3s9-1.3 9-3V5" />
            <path d="M3 11v6c0 1.7 6.4 3 9 3s9-1.3 9-3v-6" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-gray-900 mb-2">Manajemen Database</h2>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Akses langsung ke Django Admin untuk mengelola dokumen, layer spasial,
          metadata, dan data referensi.
        </p>
        <a
          href="/admin/"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-folur-700 text-white text-sm font-semibold rounded-lg hover:bg-folur-800 transition"
        >
          Buka Django Admin →
        </a>
      </div>
    </div>
  );
}
