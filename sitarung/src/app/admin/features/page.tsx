export default function FeaturesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fitur</h1>
        <p className="text-sm text-gray-500 mt-1">
          Aktifkan/nonaktifkan seksi di halaman depan SITARUNG.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-folur-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-folur-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <rect x="2" y="2" width="20" height="8" rx="2" /><rect x="2" y="14" width="20" height="8" rx="2" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-gray-900 mb-2">Manajemen Fitur Landing</h2>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Kelola visibilitas seksi seperti Hero, Statistik, Komoditas, Dokumen, Dataset,
          dan lainnya melalui panel ini.
        </p>
        <a
          href="/dst-auth/frontend/"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-folur-700 text-white text-sm font-semibold rounded-lg hover:bg-folur-800 transition"
        >
          Buka Panel Fitur →
        </a>
      </div>
    </div>
  );
}
