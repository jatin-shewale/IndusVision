import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { Panel, SeverityBadge } from "../components/UI";
import api from "../api/client";
import type { Alert } from "../types";

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<string>("open");

  async function load() {
    const res = await api.get("/api/alerts", { params: filter === "all" ? {} : { status: filter } });
    setAlerts(res.data);
  }

  useEffect(() => { load(); const t = setInterval(load, 8000); return () => clearInterval(t); }, [filter]);

  async function acknowledge(id: string) {
    await api.patch(`/api/alerts/${id}/acknowledge`);
    load();
  }
  async function resolve(id: string) {
    await api.patch(`/api/alerts/${id}/resolve`);
    load();
  }

  return (
    <Layout title="Alerts">
      <div className="space-y-4">
        <div className="flex gap-2">
          {["open", "acknowledged", "resolved", "all"].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded text-sm font-mono border capitalize ${filter === f ? "bg-amber text-base border-amber" : "bg-panel border-border text-textmuted"}`}>
              {f}
            </button>
          ))}
        </div>

        <Panel title={`${alerts.length} Alert(s)`}>
          {alerts.length === 0 ? (
            <p className="text-textmuted text-sm">No alerts in this view.</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((a) => (
                <div key={a.id} className="border border-border rounded p-3 bg-panel2 flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <SeverityBadge severity={a.severity} />
                      <span className="text-xs text-textmuted font-mono uppercase">{a.source}</span>
                      <span className="text-xs text-textmuted font-mono">{new Date(a.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-textprimary font-medium">{a.title}</p>
                    <p className="text-sm text-textmuted mt-0.5">{a.message}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {a.status === "open" && (
                      <button onClick={() => acknowledge(a.id)} className="text-xs font-mono border border-amber/40 text-amber rounded px-2 py-1 hover:bg-amber/10">
                        Acknowledge
                      </button>
                    )}
                    {a.status !== "resolved" && (
                      <button onClick={() => resolve(a.id)} className="text-xs font-mono border border-safe/40 text-safe rounded px-2 py-1 hover:bg-safe/10">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </Layout>
  );
}
