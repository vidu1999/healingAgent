"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, Filter } from "@/components/icons";
import { listIncidents, type Incident } from "@/lib/api";

export default function Incidents() {
  const router = useRouter();
  const [items, setItems] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  useEffect(() => {
    listIncidents()
      .then((data) => setItems(data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = items.filter(
    (i) => !q || i.title.toLowerCase().includes(q.toLowerCase()) || i.severity.includes(q)
  );

  const severityColor = (s: string) => {
    switch (s) {
      case "critical": return "bg-red/10 text-red-400 border-red/20";
      case "error": return "bg-red/10 text-red-400 border-red/20";
      case "warning": return "bg-amber/10 text-amber-400 border-amber/20";
      default: return "bg-sentinel-700 text-sentinel-400 border-sentinel-700";
    }
  };

  if (loading) return <div className="panel p-8">Loading incidents...</div>;

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      <div className="lg:w-1/3 space-y-4">
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Filters</h3>
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-sentinel-600" />
              <input
                className="input pl-10"
                placeholder="Search incidents…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <button className="w-full btn-outline flex items-center justify-center gap-2">
              <Filter className="h-4 w-4" /> Clear filters
            </button>
          </div>
        </div>
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Severity</h3>
          <div className="space-y-2">
            {["critical", "error", "warning", "info"].map((s) => (
              <button key={s} className={`w-full text-left px-3 py-2 rounded-lg text-xs border ${
                severityColor(s).replace("border-", "border-transparent ") + " text-sentinel-300 hover:bg-sentinel-800"
              }`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Incidents</h2>
          <button
            onClick={() => router.push("/incidents/new")}
            className="flex items-center gap-2 btn-primary"
          >
            <Plus className="h-4 w-4" /> Report incident
          </button>
        </div>
        {filtered.length === 0 ? (
          <div className="panel p-8 text-center text-sentinel-500">No incidents found.</div>
        ) : (
          <div className="table-container overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Severity</th><th>Title</th><th>Source</th><th>Status</th><th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i) => (
                  <tr key={i.id} className="hover:bg-sentinel-800/50 cursor-pointer group" onClick={() => router.push(`/incidents/${i.id}`)}>
                    <td>
                      <span className={`badge ${severityColor(i.severity)}`}>{i.severity}</span>
                    </td>
                    <td className="font-medium truncate max-w-xs">{i.title}</td>
                    <td className="text-sentinel-500 truncate max-w-xs">{i.source_type}</td>
                    <td><span className="badge bg-sentinel-700 text-sentinel-400">{i.status}</span></td>
                    <td className="text-sentinel-500 text-xs">{new Date(i.updated_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
