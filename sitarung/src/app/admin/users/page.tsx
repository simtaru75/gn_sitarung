export default function UsersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Pengguna & Roles</h1>
        <p className="text-sm text-gray-500 mt-1">
          Kelola akun pengguna, hak akses, dan roles admin.
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-folur-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-folur-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-gray-900 mb-2">Manajemen Pengguna</h2>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Akses Django Admin untuk mengelola users, groups, roles, dan permissions.
        </p>
        <a
          href="/admin/people/profile/"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-folur-700 text-white text-sm font-semibold rounded-lg hover:bg-folur-800 transition"
        >
          Buka Admin Users →
        </a>
      </div>
    </div>
  );
}
