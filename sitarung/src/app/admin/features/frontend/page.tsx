export default function FeaturesFrontendPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Halaman Depan</h1>
        <p className="text-sm text-gray-500 mt-1">
          Konfigurasi visibilitas seksi di landing page SITARUNG.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-sm text-gray-500">
          Panel konfigurasi landing page tersedia di{" "}
          <a href="/dst-auth/frontend/" className="text-folur-600 underline">Panel Fitur →</a>
        </p>
      </div>
    </div>
  );
}
