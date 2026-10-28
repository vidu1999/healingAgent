"use client";

export default function Settings() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Settings &amp; access control</h2>
      <div className="panel">
        <h3 className="text-sm font-semibold mb-3">Configuration</h3>
        <p className="text-sm text-sentinel-400">Edit backend/.env for Ollama, GitHub, log roots, sandbox, and approval settings. Restart the backend after changes.</p>
        <table className="table mt-4">
          <thead>
            <tr><th>Setting</th><th>Description</th><th>Example</th></tr>
          </thead>
          <tbody>
            <tr><td className="font-mono text-xs">OLLAMA_BASE_URL</td><td className="text-sentinel-500 text-xs">Local Ollama endpoint</td><td className="font-mono text-xs">http://127.0.0.1:11434</td></tr>
            <tr><td className="font-mono text-xs">OLLAMA_MODEL</td><td className="text-sentinel-500 text-xs">Local coding model</td><td className="font-mono text-xs">codellama:7b-instruct</td></tr>
            <tr><td className="font-mono text-xs">GITHUB_READ_ONLY</td><td className="text-sentinel-500 text-xs">Start read-only</td><td className="font-mono text-xs">true</td></tr>
            <tr><td className="font-mono text-xs">AI_CLOUD_FALLBACK</td><td className="text-sentinel-500 text-xs">Disabled (never cloud AI)</td><td className="font-mono text-xs">false</td></tr>
            <tr><td className="font-mono text-xs">APPROVAL_LIFETIME_SECONDS</td><td className="text-sentinel-500 text-xs">Approval expiry TTL</td><td className="font-mono text-xs">3600</td></tr>
          </tbody>
        </table>
      </div>
      <div className="panel">
        <h3 className="text-sm font-semibold mb-3">Access control</h3>
        <p className="text-sm text-sentinel-400">Initial roles: admin, operator, viewer. Admin user created during seed (development only).</p>
      </div>
    </div>
  );
}
