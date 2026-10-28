"use client";

import { useState, useEffect } from "react";
import { listRepositories } from "@/lib/api";
import type { Repository } from "@/lib/api";

export default function Workflows() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listRepositories()
      .then((d) => setRepos(d || []))
      .catch(() => setRepos([]));
  }, []);

  const load = () => {
    if (!selected) return;
    setLoading(true);
    fetch(`/api/workflows/${selected}`) // placeholder; wire to backend when available
      .then(() => setRuns([]))
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">CI/CD workflow history</h2>
      <div className="panel">
        <div className="space-y-4">
          <label className="text-xs text-sentinel-400">Repository</label>
          <select
            className="input"
            value={selected || ""}
            onChange={(e) => setSelected(e.target.value || null)}
          >
            <option value="">Select a repository</option>
            {repos.map((r) => <option key={r.id} value={r.id}>{r.full_name}</option>)}
          </select>
          {selected && (
            <button className="btn-primary" onClick={load} disabled={loading}>
              {loading ? "Loading…" : "Load runs"}
            </button>
          )}
        </div>
      </div>
      {runs.length > 0 && (
        <div className="panel">
          <table className="table">
            <thead>
              <tr><th>Run</th><th>Workflow</th><th>Branch</th><th>Status</th><th>Conclusion</th><th>Started</th></tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}><td>{r.run_id}</td><td>{r.name}</td><td>{r.branch}</td><td>{r.status}</td><td>{r.conclusion || "—"}</td><td>{r.started_at || "—"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
