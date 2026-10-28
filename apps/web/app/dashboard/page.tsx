import { getDashboardSummary, getOllamaStatus } from "@/lib/api";
import { LayoutDashboard, FileText, AlertCircle, GitPullRequest, ShieldAlert, Server, Clock } from "@/components/icons";

type Stat = { title: string; value: string | number; delta?: string; icon: React.ElementType; color: string };

const STAT_COLORS: Record<string, string> = {
  active_incidents: "text-red-400 bg-red/10 border-red/20",
  critical_errors: "text-red-400 bg-red/10 border-red/20",
  failed_workflows: "text-amber-400 bg-amber/10 border-amber/20",
  recent_repair_attempts: "text-primary bg-primary/10 border-primary/20",
  pending_approvals: "text-amber-400 bg-amber/10 border-amber/20",
};

export default async function Dashboard() {
  let summary;
  let ollama;
  try {
    summary = await getDashboardSummary();
  } catch {
    summary = {
      active_incidents: 0,
      critical_errors: 0,
      failed_workflows: 0,
      recent_repair_attempts: 0,
      pending_approvals: 0,
      verification_rate: "0%",
      integrations: [],
    };
  }
  try {
    ollama = await getOllamaStatus();
  } catch {
    ollama = { reachable: false, model_available: false, model: "-", error: "unreachable", mode: "unavailable" };
  }

  const stats: Stat[] = [
    { title: "Active incidents", value: summary.active_incidents, icon: AlertCircle, color: STAT_COLORS.active_incidents },
    { title: "Critical errors", value: summary.critical_errors, icon: FileText, color: STAT_COLORS.critical_errors },
    { title: "Failed workflows", value: summary.failed_workflows, icon: GitPullRequest, color: STAT_COLORS.failed_workflows },
    { title: "Pending approvals", value: summary.pending_approvals, icon: ShieldAlert, color: STAT_COLORS.pending_approvals },
    { title: "Recent repairs", value: summary.recent_repair_attempts, icon: Clock, color: STAT_COLORS.recent_repair_attempts },
    { title: "Verification rate", value: summary.verification_rate, icon: ShieldCheckIcon, color: "text-green-400 bg-green/10 border-green/20" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sentinel-400">Overview of incidents, workflows, repairs and approvals.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            ollama.reachable && ollama.model_available ? "bg-green/10 text-green-400" : "bg-red/10 text-red-400"
          }`}>
            {ollama.reachable && ollama.model_available ? "Ollama live" : "Ollama unavailable"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.title} className="panel">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-sentinel-500 uppercase tracking-wider">{s.title}</p>
                <p className="text-2xl font-bold">{s.value}</p>
                {s.delta && <p className="text-xs text-green-400">{s.delta}</p>}
              </div>
              <div className={`p-2 rounded-lg ${s.color}`}>
                <s.icon className="h-5 w-5" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="panel">
        <h3 className="text-sm font-semibold mb-4">Integration status</h3>
        <div className="space-y-3">
          {summary.integrations.map((int) => (
            <div key={int.name} className="flex items-center justify-between">
              <span className="text-sm">{int.name}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                int.status === "configured" ? "bg-green/10 text-green-400" : int.status === "not configured"
                  ? "bg-sentinel-700 text-sentinel-500"
                  : "bg-amber/10 text-amber-400"
              }`}>
                {int.status === "configured" ? "Configured" : int.status === "not configured" ? "Not configured" : int.status}
              </span>
            </div>
          ))}
          {summary.integrations.length === 0 && <p className="text-sm text-sentinel-500">No integrations configured.</p>}
        </div>
      </div>
    </div>
  );
}

function ShieldCheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-5 h-5">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0" />
    </svg>
  );
}
