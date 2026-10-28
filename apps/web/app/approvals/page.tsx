"use client";

import { useState, useEffect } from "react";
import { List, Clock, ShieldCheck, XCircle } from "@/components/icons";
import { listApprovals, type ApprovalRequest, approveAction, rejectAction, revokeAction } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-amber/10 text-amber-400 border-amber/20",
  approved: "bg-green/10 text-green-400 border-green/20",
  rejected: "bg-red/10 text-red-400 border-red/20",
  revoked: "bg-sentinel-700 text-sentinel-500 border-sentinel-700",
  consumed: "bg-primary/10 text-primary border-primary/20",
  expired: "bg-sentinel-700 text-sentinel-500 border-sentinel-700",
};

export default function Approvals() {
  const [items, setItems] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listApprovals()
      .then((d) => setItems(d || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const handleAction = async (id: string, action: "approve" | "reject" | "revoke") => {
    const reason = window.prompt("Reason (optional):") || undefined;
    try {
      if (action === "approve") await approveAction(id, reason);
      else if (action === "reject") await rejectAction(id, reason);
      else await revokeAction(id, reason);
      setItems((cur) => cur.map((i) => (i.id === id ? { ...i, status: action === "revoke" ? "revoked" : action === "approve" ? "approved" : "rejected" } : i)));
    } catch (err: any) {
      alert(err?.detail || "Action failed");
    }
  };

  if (loading) return <div className="panel p-8">Loading approvals…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Approval queue</h2>
          <p className="text-sentinel-400">Every external mutation requires explicit human approval.</p>
        </div>
        <div className="flex items-center gap-2">
          <List className="h-4 w-4 mr-2" />
          <span className="text-sm">{items.length} pending action(s)</span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="panel p-8 text-center text-sentinel-500">No pending approvals.</div>
      ) : (
        <div className="table-container overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Action</th><th>Resource</th><th>Risk</th><th>Status</th><th>Requested</th><th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {items.filter((i) => i.status === "pending").map((a) => (
                <tr key={a.id} className="hover:bg-sentinel-800/50">
                  <td>
                    <div className="font-medium">{a.action_type}</div>
                    <p className="text-xs text-sentinel-500 truncate max-w-xs">{a.resource}</p>
                  </td>
                  <td><span className={`badge ${STATUS_COLOR[a.risk_classification] || "bg-sentinel-700"}`}>{a.risk_classification}</span></td>
                  <td><span className={`badge ${STATUS_COLOR[a.status]}`}>{a.status}</span></td>
                  <td className="text-sentinel-500 text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleAction(a.id, "approve")}
                        className="px-3 py-1.5 rounded text-xs bg-green/10 text-green-400 hover:bg-green/20 border border-green/20"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleAction(a.id, "reject")}
                        className="px-3 py-1.5 rounded text-xs bg-red/10 text-red-400 hover:bg-red/20 border border-red/20"
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.filter((i) => i.status !== "pending").map((a) => (
                <tr key={a.id} className="text-sentinel-600">
                  <td className="font-medium">{a.action_type}</td>
                  <td className="text-xs text-sentinel-500 truncate max-w-xs">{a.resource}</td>
                  <td><span className={`badge ${STATUS_COLOR[a.risk_classification] || "bg-sentinel-700"}`}>{a.risk_classification}</span></td>
                  <td><span className={`badge ${STATUS_COLOR[a.status]}`}>{a.status}</span></td>
                  <td className="text-xs text-sentinel-500">{new Date(a.created_at).toLocaleString()}</td>
                  <td>-</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="panel">
        <h3 className="text-sm font-semibold mb-3">How approvals work</h3>
        <ul className="space-y-2 text-sm text-sentinel-400 list-disc pl-5">
          <li>Approval binds to the exact patch hash, base commit, and operation parameters.</li>
          <li>Expired or altered approvals are rejected; consumed atomically to prevent replay.</li>
          <li>Merge and deployment require separate approvals.</li>
          <li>No GitHub write occurs before you approve.</li>
        </ul>
      </div>
    </div>
  );
}
