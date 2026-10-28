"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileDiff, ShieldCheck, AlertTriangle } from "@/components/icons";

export default function RepairAttemptPage() {
  const params = useParams();
  const router = useRouter();
  const id = (params.id as string) || "";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/dashboard")} className="text-sentinel-400 hover:text-white">
            <ArrowLeft className="h-5 w-5" /> Back
          </button>
          <h1 className="text-2xl font-bold">Repair attempt</h1>
        </div>
        <span className="badge bg-primary/10 text-primary border-primary/20">Pending verification</span>
      </div>

      <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Patch diff</h3>
        <p className="text-sm text-sentinel-500 mb-3">The proposed patch has not yet been cryptographically verified. No external mutation occurs until you approve.</p>
        <div className="rounded-lg border border-sentinel-700 bg-sentinel-950 p-4 font-mono text-xs overflow-x-auto">
          {`diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -10,7 +10,7 @@
 def process(data):
-    return data[0]
+    return data[0] if data else None`}
        </div>
        <div className="mt-4 flex gap-2 text-xs text-sentinel-500">
          <AlertTriangle className="h-4 w-4 inline shrink-0" />
          <span>Patch SHA-256: {id.slice(0, 16)}…</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Verification</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span>Syntax check</span><span className="text-green-400">passed</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Regression tests</span><span className="text-green-400">passed</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Secret scan</span><span className="text-green-400">clean</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>Policy check</span><span className="text-green-400">passed</span>
            </div>
          </div>
        </div>
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Next step</h3>
          <p className="text-sentinel-400 text-sm mb-4">The patch is ready for approval. Review the exact diff above before approving.</p>
          <div className="flex gap-2">
            <button className="flex-1 btn-primary">View approval</button>
            <button className="flex-1 btn-outline">Request changes</button>
          </div>
        </div>
      </div>
    </div>
  );
}
