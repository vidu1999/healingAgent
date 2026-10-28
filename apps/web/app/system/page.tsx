"use client";

import { useEffect, useState } from "react";
import { Server, Database, ShieldCheck } from "@/components/icons";
import { getOllamaStatus } from "@/lib/api";

export default function System() {
  const [ollama, setOllama] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOllamaStatus()
      .then(setOllama)
      .catch(() => setOllama({ reachable: false, model_available: false, model: "-", error: "unreachable", mode: "unavailable" }))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">System health</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Ollama local inference</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span>Reachable</span>
              <span className={`badge ${ollama?.reachable ? "bg-green/10 text-green-400" : "bg-red/10 text-red-400"}`}>
                {ollama?.reachable ? "Yes" : "No"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Model available</span>
              <span className={`badge ${ollama?.model_available ? "bg-green/10 text-green-400" : "bg-red/10 text-red-400"}`}>
                {ollama?.model_available ? "Yes" : "No"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Model</span><span className="text-sentinel-500 text-sm">{ollama?.model || "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Mode</span>
              <span className={`badge bg-sentinel-700 text-sentinel-400`}>{ollama?.mode || "unavailable"}</span>
            </div>
            {ollama?.error && (
              <p className="text-xs text-red-400 bg-red/10 p-2 rounded">{ollama.error}</p>
            )}
            <p className="text-xs text-sentinel-500">
              Configure OLLAMA_BASE_URL and OLLAMA_MODEL in backend/.env. Never enables a cloud AI fallback.
            </p>
          </div>
        </div>
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Database</h3>
          <div className="flex items-center gap-3 mb-3">
            <Database className="h-5 w-5 text-green-400" />
            <span className="font-medium">PostgreSQL (prod) / SQLite (dev fallback)</span>
          </div>
          <p className="text-xs text-sentinel-500">Alembic migrations under backend/migrations.</p>
        </div>
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Security posture</h3>
          <ul className="space-y-2 text-sm text-sentinel-400 list-disc pl-5">
            <li>HttpOnly, SameSite session cookies</li>
            <li>Argon2id password hashing</li>
            <li>Approval-gated external mutations</li>
            <li>Secret redaction in logs and prompts</li>
            <li>Sandboxed verification worker</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
