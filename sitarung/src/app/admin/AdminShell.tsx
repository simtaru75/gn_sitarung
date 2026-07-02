"use client";

import { useState, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Ikon inline kecil — hindari dependensi library ikon
// ---------------------------------------------------------------------------
const Icon = {
  Dashboard: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  Design: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
    </svg>
  ),
  Features: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <rect x="2" y="2" width="20" height="8" rx="2" /><rect x="2" y="14" width="20" height="8" rx="2" />
      <circle cx="6" cy="6" r="1" fill="currentColor" /><circle cx="6" cy="18" r="1" fill="currentColor" />
    </svg>
  ),
  Geoportal: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" /><ellipse cx="12" cy="12" rx="4" ry="10" />
      <path d="M2 12h20" />
    </svg>
  ),
  Database: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v6c0 1.7 6.4 3 9 3s9-1.3 9-3V5" />
      <path d="M3 11v6c0 1.7 6.4 3 9 3s9-1.3 9-3v-6" />
    </svg>
  ),
  Admin: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  Home: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  ChevronDown: () => (
    <svg className="w-4 h-4 transition-transform" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
  Menu: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  X: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  Logout: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  PanelLeftClose: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 3v18" /><path d="M16 11l-3 3 3 3" />
    </svg>
  ),
  PanelLeftOpen: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 3v18" /><path d="M13 11l3 3-3 3" />
    </svg>
  ),
};

// ---------------------------------------------------------------------------
// Data navigasi sidebar
// ---------------------------------------------------------------------------
interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  children?: { href: string; label: string }[];
}

const NAV_ITEMS: NavItem[] = [
  { href: "/admin", label: "Dashboard", icon: <Icon.Dashboard /> },
  {
    href: "/admin/design",
    label: "Desain & Tema",
    icon: <Icon.Design />,
    children: [
      { href: "/admin/design", label: "Tema CMS" },
      { href: "/admin/design/fonts", label: "Font & Tipografi" },
    ],
  },
  {
    href: "/admin/features",
    label: "Fitur",
    icon: <Icon.Features />,
    children: [
      { href: "/admin/features", label: "Semua Fitur" },
      { href: "/admin/features/frontend", label: "Halaman Depan" },
    ],
  },
  {
    href: "/admin/geoportal",
    label: "Geoportal",
    icon: <Icon.Geoportal />,
    children: [
      { href: "/admin/geoportal", label: "Pengaturan Peta" },
      { href: "/admin/geoportal/layers", label: "Layer & Servis" },
    ],
  },
  {
    href: "/admin/database",
    label: "Database",
    icon: <Icon.Database />,
  },
  {
    href: "/admin/users",
    label: "Pengguna & Roles",
    icon: <Icon.Admin />,
  },
];

// ---------------------------------------------------------------------------
// Komponen
// ---------------------------------------------------------------------------
export default function AdminShell({
  children,
  brandName,
  brandSubtitle,
  logo,
}: {
  children: React.ReactNode;
  brandName: string;
  brandSubtitle: string;
  logo?: string | null;
}) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = useCallback((href: string) => {
    setExpanded((prev) => ({ ...prev, [href]: !prev[href] }));
  }, []);

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* ===== OVERLAY MOBILE ===== */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ===== SIDEBAR ===== */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 bg-folur-900 text-white flex flex-col transition-all duration-300 ease-out lg:static lg:translate-x-0 ${
          collapsed ? "w-16" : "w-64"
        } ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className={`flex items-center h-16 px-3 border-b border-white/10 shrink-0 ${collapsed ? "justify-center" : "gap-3 px-5"}`}>
          {logo && (
            <img src={logo} alt="" className="h-9 w-9 object-contain rounded bg-white p-0.5 shrink-0" />
          )}
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-sm font-bold leading-tight truncate">{brandName}</p>
              <p className="text-[10px] text-folur-300 truncate">{brandSubtitle}</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
          {NAV_ITEMS.map((item) => (
            <div key={item.href}>
              {item.children && !collapsed ? (
                <>
                  <button
                    onClick={() => toggleExpand(item.href)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? "bg-white/15 text-white"
                        : "text-folur-200 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {item.icon}
                    <span className="flex-1 text-left">{item.label}</span>
                    <span className={`transition-transform ${expanded[item.href] ? "rotate-180" : ""}`}>
                      <Icon.ChevronDown />
                    </span>
                  </button>
                  <div
                    className={`overflow-hidden transition-all duration-300 ${
                      expanded[item.href] || isActive(item.href) ? "max-h-80 opacity-100" : "max-h-0 opacity-0"
                    }`}
                  >
                    <div className="ml-9 mt-1 mb-1 space-y-0.5 border-l border-white/10 pl-3">
                      {item.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`block px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                            pathname === child.href
                              ? "bg-white/10 text-white"
                              : "text-folur-300 hover:text-white hover:bg-white/5"
                          }`}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                </>
              ) : item.children && collapsed ? (
                /* collapsed with children: icon-only button, no dropdown */
                <Link
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  title={item.label}
                  className={`flex items-center justify-center px-2 py-2.5 rounded-lg transition-colors ${
                    isActive(item.href)
                      ? "bg-white/15 text-white"
                      : "text-folur-200 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {item.icon}
                </Link>
              ) : (
                <Link
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  title={collapsed ? item.label : undefined}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    collapsed ? "justify-center px-2" : ""
                  } ${
                    isActive(item.href)
                      ? "bg-white/15 text-white"
                      : "text-folur-200 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {item.icon}
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              )}
            </div>
          ))}
        </nav>

        {/* Footer sidebar */}
        <div className={`border-t border-white/10 p-2 space-y-1 shrink-0 ${collapsed ? "" : "p-4 space-y-2"}`}>
          <Link
            href="/"
            title="Lihat Situs"
            className={`flex items-center rounded-lg text-xs text-folur-300 hover:text-white hover:bg-white/10 transition-colors ${
              collapsed ? "justify-center px-2 py-2.5" : "gap-2 px-3 py-2"
            }`}
          >
            <Icon.Home /> {!collapsed && "Lihat Situs"}
          </Link>
          <a
            href="/account/logout"
            title="Keluar"
            className={`flex items-center rounded-lg text-xs text-folur-300 hover:text-red-300 hover:bg-white/10 transition-colors ${
              collapsed ? "justify-center px-2 py-2.5" : "gap-2 px-3 py-2"
            }`}
          >
            <Icon.Logout /> {!collapsed && "Keluar"}
          </a>
        </div>
      </aside>

      {/* ===== MAIN CONTENT ===== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-30 h-16 bg-white border-b border-gray-200 flex items-center px-4 gap-3 shadow-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 lg:hidden"
            aria-label="Buka menu"
          >
            <Icon.Menu />
          </button>
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="hidden lg:flex p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
            aria-label={collapsed ? "Bentangkan sidebar" : "Ciutkan sidebar"}
            title={collapsed ? "Bentangkan sidebar" : "Ciutkan sidebar"}
          >
            {collapsed ? <Icon.PanelLeftOpen /> : <Icon.PanelLeftClose />}
          </button>
          <div className="flex-1" />
          <div className="text-sm text-gray-500">
            Administrator
          </div>
          <div className="h-8 w-px bg-gray-200" />
          <a
            href="/account/logout"
            className="text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Logout
          </a>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
