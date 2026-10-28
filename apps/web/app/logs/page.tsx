"use client";

export default function Logs() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Log explorer</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-sentinel-500">JSON Lines ingestion</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">Ingest log event</h3>
          <p className="text-xs text-sentinel-500 mb-4">
            POST a JSON Lines event to a registered monitored source.
          </p>
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs text-sentinel-400">Source ID</label>
              <input className="input" placeholder="src-1" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-sentinel-400">Message</label>
              <textarea
                className="input h-32 font-mono text-xs"
                placeholder='JSON log event'
              />
            </div>
            <button className="btn-primary w-full">Ingest</button>
          </div>
        </div>

        <div className="panel">
          <h3 className="text-sm font-semibold mb-3">About log monitoring</h3>
          <ul className="space-y-2 text-sm text-sentinel-400 list-disc pl-5">
            <li>
              Register explicit monitoring roots only (no recursive full-disk
              scans).
            </li>
            <li>Secrets (tokens, keys, passwords) are redacted before storage.</li>
            <li>Duplicate events are grouped into incidents.</li>
            <li>Credential directories are excluded by default.</li>
          </ul>
          <div className="mt-4 p-3 rounded-lg bg-sentinel-800/50 border border-sentinel-700 text-xs text-sentinel-400">
            Real log ingestion requires a registered monitored source and the
            backend running on :8000.
          </div>
        </div>
      </div>
    </div>
  );
}
