"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoutButton } from "./LogoutButton";

export interface NavigationItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
  children?: NavigationItem[];
}

const navigationItems: NavigationItem[] = [
  {
    label: "Tableau de bord",
    href: "/dashboard",
    icon: "📊",
  },
  {
    label: "Clients",
    href: "/clients",
    icon: "👥",
  },
  {
    label: "Compagnies",
    href: "/companies",
    icon: "🏢",
  },
  {
    label: "Polices",
    href: "/policies",
    icon: "📋",
  },
  {
    label: "Templates",
    href: "/templates",
    icon: "📄",
  },
  {
    label: "Documents",
    href: "/documents",
    icon: "🗂️",
  },
  {
    label: "Rapports",
    href: "/reports",
    icon: "📈",
  },
  {
    label: "Administration",
    href: "/admin",
    icon: "⚙️",
    children: [
      {
        label: "Configuration Stockage",
        href: "/admin/storage-config",
      },
      {
        label: "Logs d'Audit",
        href: "/admin/audit-logs",
      },
    ],
  },
];

export interface NavigationProps {
  children: React.ReactNode;
}

export function Navigation({ children }: NavigationProps) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={[
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        ].join(" ")}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b">
          <h1 className="text-xl font-bold text-gray-900">MonAssurance</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
          >
            ✕
          </button>
        </div>
        
        <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
          {navigationItems.map((item) => (
            <NavigationItem key={item.href} item={item} pathname={pathname} />
          ))}
        </nav>
        
        <div className="p-4 border-t">
          <LogoutButton />
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b h-16 flex items-center justify-between px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
          >
            ☰
          </button>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              Bienvenue dans MonAssurance
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

interface NavigationItemProps {
  item: NavigationItem;
  pathname: string;
  level?: number;
}

function NavigationItem({ item, pathname, level = 0 }: NavigationItemProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const hasChildren = item.children && item.children.length > 0;
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={[
            "w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors",
            isActive
              ? "bg-blue-100 text-blue-700"
              : "text-gray-700 hover:bg-gray-100",
            level > 0 ? "ml-4" : "",
          ].join(" ")}
        >
          <div className="flex items-center space-x-3">
            {item.icon && <span>{item.icon}</span>}
            <span>{item.label}</span>
          </div>
          <span className={`transform transition-transform ${isExpanded ? "rotate-90" : ""}`}>
            ▶
          </span>
        </button>
        {isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children?.map((child) => (
              <NavigationItem
                key={child.href}
                item={child}
                pathname={pathname}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      className={[
        "flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
        isActive
          ? "bg-blue-100 text-blue-700"
          : "text-gray-700 hover:bg-gray-100",
        level > 0 ? "ml-4" : "",
      ].join(" ")}
    >
      {item.icon && <span>{item.icon}</span>}
      <span>{item.label}</span>
    </Link>
  );
}
