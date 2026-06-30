import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center px-6">
        <h1 className="font-serif text-6xl font-bold text-gray-300 mb-4">404</h1>
        <p className="text-lg text-gray-500 mb-8">Halaman tidak ditemukan.</p>
        <Link href="/" className="inline-flex items-center px-6 py-3 bg-folur-700 text-white font-semibold rounded-lg hover:bg-folur-800 transition">Kembali ke Beranda</Link>
      </div>
    </div>
  );
}
