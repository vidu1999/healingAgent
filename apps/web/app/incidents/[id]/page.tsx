"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Clock } from "@/components/icons";
import { listIncidents } from "@/lib/api";
import type { Incident } from "@/lib/api";

export default function IncidentDetail() {
  const params = useParams();
  const router = useRouter();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listIncidents()
      .then((list) => {
        const found = list.find((i) => i.id === (params.id as string));
        setIncident(found || null);
      })
      .catch(() => setIncident(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="panel p-8">Loading incident…</div>;
  if (!incident) {
    return (
      <div className="panel p-6 text-center">
        <ArrowLeft className="h-5 w-5 mb-3 inline" onClick={() => router.back()} />
        <h3 className="font-semibold">Incident not found</h3>
      </div>
    );
  }

  const sev = incident.severity;
  const sevColor = sev === "critical" || sev === "error" ? "text-red-400" : sev === "warning" ? "text-amber-400" : "text-sentinel-400";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/incidents")} className="text-sentinel-400 hover:text-white">
            <ArrowLeft className="h-5 w-5" /> Back
          </button>
          <h1 className="text-2xl font-bold">Incident {incident.id.slice(0, 8)}</h1>
        </div>
        <span className={`badge ${sevColor === "text-red-400" ? "bg-red/10 border-red/20" : sevColor === "text-amber-400" ? "bg-amber/10 border-amber/20" : "bg-sentinel-700 border-sentinel-700"} ${sevColor}`}>{sev}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="panel">
          <p className="text-xs text-sentinel-500 uppercase tracking-wider">Status</p>
          <p className="font-medium">{incident.status}</p>
        </div>
        <div className="panel">
          <p className="text-xs text-sentinel-500 uppercase tracking-wider">Source</p>
          <p className="font-medium">{incident.source_type}</p>
        </div>
        <div className="panel">
          <p className="text-xs text-sentinel-500 uppercase tracking-wider">Trace ID</p>
          <p className="font-medium text-sentinel-500 truncate">{incident.trace_id || "—"}</p>
        </div>
      </div>

      <div className="panel">
        <p className="text-xs text-sentinel-500 uppercase tracking-wider mb-3">Description</p>
        <p className="text-sentinel-300 whitespace-pre-wrap">{incident.description || "No description provided."}</p>
      </div>

      <div className="panel">
        <p className="text-xs text-sentinel-500 uppercase tracking-wider mb-3">Related entities</p>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Repository</span><span className="text-sentinel-500">{incident.repository_id || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span>Workflow run</span><span className="text-sentinel-500">{incident.workflow_run_id || "—"}</span>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-sentinel-500" />
          <p className="text-sm text-sentinel-500">Recorded {new Date(incident.created_at).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
