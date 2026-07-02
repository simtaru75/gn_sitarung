export default function GeoportalLayersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Layer & Servis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Kelola layer peta, service WMS/WFS, dan konfigurasi GeoServer.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-sm text-gray-500">
          Manajemen layer tersedia di GeoNode Admin.
        </p>
      </div>
    </div>
  );
}
