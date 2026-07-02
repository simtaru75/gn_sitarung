export default function DesignFontsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Font & Tipografi</h1>
        <p className="text-sm text-gray-500 mt-1">
          Atur kombinasi font serif, sans-serif, dan monospace untuk seluruh situs.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-sm text-gray-500">
          Panel font tersedia di halaman{" "}
          <a href="/dst-auth/tema/" className="text-folur-600 underline">Tema CMS →</a>
        </p>
      </div>
    </div>
  );
}
