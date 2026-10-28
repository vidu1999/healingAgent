"use client";

import { useState, useEffect } from "react";
import { Plus, Trash2 } from "@/components/icons";
import { listRepositories, type Repository } from "@/lib/api";

export default function Repositories() {
  const [items, setItems] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(false);
  const [name, setName] = useState("");
  const [cloneUrl, setCloneUrl] = useState("");

  useEffect(() => {
    listRepositories()
      .then((d) => setItems(d || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Repositories</h2>
        <button onClick={() => setForm(!form)} className="flex items-center gap-2 btn-primary">
          <Plus className="h-4 w-4" /> {form ? "Cancel" : "Register repository"}
        </button>
      </div>

      {form && (
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Register a GitHub repository</h3>
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs text-sentinel-400">Full name (owner/name)</label>
              <input className="input" placeholder="vidu1999/healingAgent" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-sentinel-400">Clone URL (optional)</label>
              <input className="input" placeholder="https://github.com/owner/repo.git" value={cloneUrl} onChange={(e) => setCloneUrl(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <button className="flex-1 btn-primary" disabled={!name}>Register</button>
              <button type="button" onClick={() => setForm(false)} className="flex-1 btn-outline">Cancel</button>
            </div>
            <p className="text-xs text-sentinel-500">Writes require explicit approval through the approval engine.</p>
          </div>
        </div>
      )}

      <div className="table-container overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th><th>Owner</th><th>Default branch</th><th>Write</th><th>Active</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id} className="hover:bg-sentinel-800/50">
                <td className="font-medium truncate max-w-xs">{r.full_name}</td>
                <td className="text-sentinel-500 text-sm">{r.owner}</td>
                <td className="text-sentinel-500 text-sm">{r.default_branch}</td>
                <td><span className={`badge ${r.allow_write ? "bg-red/10 text-red-400" : "bg-sentinel-700 text-sentinel-400"}`}>{r.allow_write ? "enabled" : "read-only"}</span></td>
                <td><span className={`badge ${r.is_active ? "bg-green/10 text-green-400" : "bg-sentinel-700 text-sentinel-500"}`}>{r.is_active ? "active" : "inactive"}</span></td>
                <td>
                  <button className="text-sentinel-400 hover:text-red-400" title="Remove">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
