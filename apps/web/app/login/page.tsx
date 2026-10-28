"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldAlert, Mail, Lock, AlertTriangle } from "@/components/icons";
import { authLogin } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const callbackUrl = "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await authLogin(email, password);
      router.push(callbackUrl);
      router.refresh();
    } catch (err: any) {
      setError(err?.detail || "Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-sentinel-900">
      <div className="w-full max-w-md">
        <div className="panel">
          <div className="flex items-center gap-2 mb-6">
            <ShieldAlert className="h-6 w-6 text-sentinel-400" />
            <h2 className="text-xl font-bold">SentinelOps AI</h2>
          </div>
          <p className="text-sm text-sentinel-500 mb-6">
            Sign in to access the security-first DevOps monitoring and repair platform.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="block text-xs font-medium text-sentinel-400">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-sentinel-600" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="input pl-10"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="block text-xs font-medium text-sentinel-400">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-sentinel-600" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className="input pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>
            {error && (
              <div className="rounded-lg bg-red/10 p-3 text-sm text-red-400 border border-red/20">
                <AlertTriangle className="h-4 w-4 mr-2 inline shrink-0" />
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full"
            >
              {submitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
          <p className="mt-6 text-xs text-sentinel-600 text-center">
            Local-first deployment. No cloud AI credentials required.
          </p>
        </div>
        <div className="mt-6 flex justify-center">
          <Link href="/" className="text-sm text-sentinel-500 hover:text-sentinel-300">
            ← Back
          </Link>
        </div>
      </div>
    </div>
  );
}
