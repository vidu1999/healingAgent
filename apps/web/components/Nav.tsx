"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Menu,
  X,
  ShieldAlert,
  LayoutDashboard,
  FileText,
  GitPullRequest,
  AlertCircle,
  Settings,
  LogOut,
  Server,
  ShieldCheck,
} from "@/components/icons";
import { authMe, authLogout } from "@/lib/api";

const NAV: Array<{ label: string; href: string; icon: React.ElementType }> = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Incidents", href: "/incidents", icon: FileText },
  { label: "Repositories", href: "/repositories", icon: GitPullRequest },
  { label: "Workflows", href: "/workflows", icon: Server },
  { label: "Logs", href: "/logs", icon: FileText },
  { label: "Approvals", href: "/approvals", icon: ShieldAlert },
  { label: "Audit", href: "/audit", icon: AlertCircle },
  { label: "System", href: "/system", icon: Settings },
  { label: "Settings", href: "/settings", icon: ShieldCheck },
];

export function Nav() {
  const [user, setUser] = useState<{ email: string; username: string; roles: string[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const load = useCallback(async () => {
    try {
      const me = await authMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleLogout = async () => {
    try {
      await authLogout();
    } catch {
      // ignore
    }
    setUser(null);
    router.push("/login");
  };

  if (loading) {
    return (
      <nav className="border-b border-sentinel-700 bg-sentinel-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sentinel-400">SentinelOps AI</span>
          </div>
          <div className="flex gap-2 animate-pulse">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-4 w-12 rounded bg-sentinel-700" />
            ))}
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="border-b border-sentinel-700 bg-sentinel-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => router.push("/dashboard")}>
          <ShieldCheck className="h-5 w-5 text-sentinel-400" />
          <span className="font-bold text-sentinel-300 tracking-tight">SentinelOps AI</span>
        </div>

        <div className="hidden md:flex items-center gap-1">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={(e) => {
                e.preventDefault();
                router.push(item.href);
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition hover:bg-sentinel-800 hover:text-sentinel-300"
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </a>
          ))}
          {user && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-sentinel-400 hover:bg-sentinel-800">
              <Server className="h-4 w-4" />
              <span title="Local AI status">Ollama</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-2">
              <div className="hidden md:block">
                <span className="text-xs text-sentinel-400">{user.email}</span>{" "}
                <button
                  onClick={handleLogout}
                  className="text-xs text-sentinel-400 underline underline-offset-4 hover:text-white"
                >
                  Log out
                </button>
              </div>
              <button
                onClick={handleLogout}
                className="md:hidden p-2 text-sentinel-400 hover:bg-sentinel-800 rounded-lg"
                aria-label="Log out"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <>
              <a
                href="/login"
                onClick={(e) => { e.preventDefault(); router.push("/login"); }}
                className="text-sm text-sentinel-400 hover:text-white"
              >
                Log in
              </a>
              <a
                href="/dashboard"
                onClick={(e) => { e.preventDefault(); router.push("/dashboard"); }}
                className="btn-primary"
              >
                Dashboard
              </a>
            </>
          )}
        </div>

        <button
          className="md:hidden p-2 text-sentinel-400 hover:bg-sentinel-800 rounded-lg"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {open && user ? (
        <div className="fixed inset-0 z-50 flex" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-sentinel-900/60 backdrop-blur" onClick={(e) => e.stopPropagation()} />
          <div className="relative w-full max-w-md ml-auto bg-sentinel-900 border-l border-sentinel-700 flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 flex justify-between items-center border-b border-sentinel-700">
              <span className="font-semibold">Menu</span>
              <button onClick={() => setOpen(false)} className="text-sentinel-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 space-y-1">
              {NAV.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={(e) => { e.preventDefault(); setOpen(false); router.push(item.href); }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-sentinel-800"
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </a>
              ))}
              <div className="pt-4 border-t border-sentinel-700">
                <button
                  onClick={() => { setOpen(false); handleLogout(); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 rounded-lg"
                >
                  <LogOut className="h-4 w-4" /> Log out
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </nav>
  );
}
