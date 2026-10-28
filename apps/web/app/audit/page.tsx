"use client";

import { useEffect, useState } from "react";
import { FileText } from "@/components/icons";
import { listAuditEvents, type AuditEvent } from "@/lib/api";

export default function Audit() {
  const [items, setItems] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAuditEvents()
      .then((d) => setItems(d || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const decisionColor = (d: string) =>
    d === "success" ? "text-green-400" : d === "failure" ? "text-red-400" : "text-sentinel-400";

  if (loading) return <div className="panel p-8">Loading audit events…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Audit history</h2>
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 mr-1" />
          <span className="text-sm text-sentinel-500">Append-only, tamper-evident log</span>
        </div>
      </div>

      <div className="table-container overflow-x-auto">
        <table className="table">
          <thead>
            <tr><th>Time</th><th>Actor</th><th>Action</th><th>Resource</th><th>Decision</th><th>Result</th></tr>
          </thead>
          <tbody>
            {items.slice(0, 100).map((e) => (
              <tr key={e.event_id} className="text-xs">
                <td className="text-sentinel-500">{new Date(e.created_at).toLocaleString()}</td>
                <td className="text-sentinel-400">{e.actor_role || "system"}</td>
                <td className="font-mono text-sentinel-300 truncate max-w-xs">{e.action}</td>
                <td className="text-sentinel-500 truncate max-w-xs">{e.resource}</td>
                <td><span className={decisionColor(e.decision)}>{e.decision}</span></td>
                <td className="text-sentinel-500">{e.result}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={6} className="text-center text-sentinel-500 py-4">No audit events.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <p className="text-sm text-sentinel-400">
          Audit events are append-only. Raw secrets, tokens, and prompts are never recorded. For stronger
          tamper evidence, enable hash chaining and signed checkpoints (see docs/operations.md).
        </p>
      </div>
    </div>
  );
}
