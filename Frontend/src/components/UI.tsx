import { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export function StatCard({
  label, value, icon: Icon, accent = "amber", sub,
}: { label: string; value: string | number; icon: LucideIcon; accent?: "amber" | "safe" | "danger"; sub?: string }) {
  const accentColor = { amber: "text-amber", safe: "text-safe", danger: "text-danger" }[accent];
  return (
    <div className="bg-panel border border-border rounded-lg p-4 flex items-start justify-between">
      <div>
        <p className="text-xs text-textmuted uppercase tracking-wide font-mono">{label}</p>
        <p className="text-2xl font-display font-700 text-textprimary mt-1">{value}</p>
        {sub && <p className="text-xs text-textmuted mt-1">{sub}</p>}
      </div>
      <Icon size={22} className={accentColor} strokeWidth={2} />
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    running: "bg-safe/15 text-safe border-safe/30",
    normal: "bg-safe/15 text-safe border-safe/30",
    idle: "bg-textmuted/15 text-textmuted border-textmuted/30",
    maintenance: "bg-amber/15 text-amber border-amber/30",
    warning: "bg-amber/15 text-amber border-amber/30",
    fault: "bg-danger/15 text-danger border-danger/30",
    failure: "bg-danger/15 text-danger border-danger/30",
    offline: "bg-textmuted/15 text-textmuted border-textmuted/30",
  };
  const cls = map[status] || map.offline;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono border uppercase ${cls}`}>
      {status}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: "critical" | "warning" | "info" }) {
  const map = {
    critical: "bg-danger/15 text-danger border-danger/30",
    warning: "bg-amber/15 text-amber border-amber/30",
    info: "bg-textmuted/15 text-textmuted border-textmuted/30",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono border uppercase ${map[severity]}`}>
      {severity}
    </span>
  );
}

export function Panel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <div className="bg-panel border border-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h3 className="font-display font-600 text-sm tracking-wide text-textprimary">{title}</h3>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
