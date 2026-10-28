"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, Play, Terminal, Bug, ShieldCheck, Clock } from "@/components/icons";
import { listIncidents } from "@/lib/api";

export default function InvestigationWorkspace() {
  const params = useParams();
  const router = useRouter();
  const [incident, setIncident] = useState<any>(null);
  const [state, setState] = useState("DETECTED");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listIncidents()
      .then((list) => setIncident(list.find((i) => i.id === (params.id as string)) || null))
      .catch(() => setIncident(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  const TRANSITIONS: Array<{ label: string; to: string; icon: React.ElementType }> = [
    { label: "Triaged", to: "TRIAGED", icon: Clock },
    { label: "Investigating", to: "INVESTIGATING", icon: Terminal },
    { label: "Fix candidate ready", to: "FIX_CANDIDATE_READY", icon: Bug },
    { label: "Patch verified", to: "PATCH_VERIFIED", icon: ShieldCheck },
  ];

  if (loading) return <div className="panel p-8">Loading…</div>;
  if (!incident) {
    return (
      <div className="panel p-6 text-center">
        <ArrowLeft className="h-5 w-5 mb-3 inline" onClick={() => router.back()} />
        <h3 className="font-semibold">Investigation not found</h3>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/incidents")} className="text-sentinel-400 hover:text-white">
            <ArrowLeft className="h-5 w-5" /> Back
          </button>
          <h1 className="text-2xl font-bold">Investigation</h1>
        </div>
        <span className="badge bg-sentinel-700 text-sentinel-400">{state}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="panel">
            <h3 className="text-sm font-semibold mb-4">Incident</h3>
            <p className="font-medium">{incident.title}</p>
            <p className="text-sentinel-400 text-sm mt-2">{incident.description || "No description"}</p>
            <div className="mt-4 flex gap-2 text-sm text-sentinel-500">
              <span>Severity: {incident.severity}</span>
              <span>Source: {incident.source_type}</span>
              <span>Trace: {incident.trace_id || "—"}</span>
            </div>
          </div>

          <div className="panel">
            <h3 className="text-sm font-semibold mb-4">AI investigation output</h3>
            <p className="text-sentinel-500 text-sm">No investigation output yet. Run an investigation to generate a root-cause analysis and proposed fix.</p>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="panel space-y-3">
            <h3 className="text-sm font-semibold mb-3">Transition state</h3>
            <div className="space-y-2">
              {TRANSITIONS.map((t) => (
                <button key={t.to} onClick={() => setState(t.to)} className="w-full text-left btn-outline flex items-center justify-between">
                  <span className="flex items-center gap-2"><t.icon className="h-4 w-4" /> {t.label}</span>
                  <span className="text-xs text-sentinel-500">{t.to}</span>
                </button>
              ))}
            </div>
            <div className="mt-4">
              <button className="w-full btn-primary flex items-center justify-center gap-2">
                <Play className="h-4 w-4" /> Run investigation (local model)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
