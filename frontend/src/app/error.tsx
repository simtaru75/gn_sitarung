"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6 text-center text-gray-850">
      <div className="max-w-md bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-2xl flex items-center justify-center mb-6">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h1 className="font-serif text-2xl font-bold text-gray-900 mb-3">Gangguan Koneksi</h1>
        <p className="text-gray-500 text-sm mb-6 leading-relaxed">
          Koneksi ke Server Data Spasial sedang mengalami gangguan atau offline. Silakan coba muat ulang halaman ini dalam beberapa saat.
        </p>
        <div className="flex gap-3 w-full">
          <button
            onClick={() => reset()}
            className="flex-1 py-3 px-4 bg-folur-700 hover:bg-folur-800 text-white font-semibold rounded-xl text-sm transition"
          >
            Coba Lagi
          </button>
          <a
            href="/"
            className="flex-1 py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl text-sm text-center transition"
          >
            Beranda
          </a>
        </div>
      </div>
    </div>
  );
}
