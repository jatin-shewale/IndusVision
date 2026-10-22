import { useEffect, useState } from "react";
import { Activity, HardHat, Boxes, BellRing, Cpu, ShieldAlert } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import Layout from "../components/Layout";
import { StatCard, StatusPill, SeverityBadge, Panel } from "../components/UI";
import api from "../api/client";
import type { Machine, Alert, Detection, InventoryItem } from "../types";

export default function Dashboard() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [violations, setViolations] = useState<Detection[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [mRes, aRes, dRes, iRes] = await Promise.all([
          api.get("/api/machines"),
          api.get("/api/alerts", { params: { status: "open", limit: 5 } }),
          api.get("/api/detections", { params: { violations_only: true, limit: 5 } }),
          api.get("/api/inventory/items", { params: { low_stock_only: true } }),
        ]);
        setMachines(mRes.data);
        setAlerts(aRes.data);
        setViolations(dRes.data);
        setInventory(iRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 10000); // refresh every 10s for a "live" feel
    return () => clearInterval(interval);
  }, []);

  const runningCount = machines.filter((m) => m.status === "running").length;
  const faultCount = machines.filter((m) => m.status === "fault").length;
  const avgHealth = machines.length
    ? Math.round(machines.reduce((sum, m) => sum + (m.health_score ?? 100), 0) / machines.length)
    : 0;

  const healthTrend = machines.slice(0, 1).map(() => ({})); // placeholder single-machine trend if needed

  return (
    <Layout title="Dashboard">
      {loading ? (
        <p className="text-textmuted font-mono text-sm">Loading plant overview...</p>
      ) : (
        <div className="space-y-6">
          {/* Stat row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Machines Running" value={`${runningCount}/${machines.length}`} icon={Cpu} accent="safe" />
            <StatCard label="Avg Health Score" value={`${avgHealth}%`} icon={Activity} accent={avgHealth > 70 ? "safe" : "danger"} />
            <StatCard label="Open Alerts" value={alerts.length} icon={BellRing} accent={alerts.length ? "danger" : "safe"} />
            <StatCard label="Low Stock Items" value={inventory.length} icon={Boxes} accent={inventory.length ? "amber" : "safe"} />
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Machine status */}
            <div className="lg:col-span-2">
              <Panel title="Machine Status">
                {machines.length === 0 ? (
                  <p className="text-textmuted text-sm">No machines registered yet. Add one via POST /api/machines.</p>
                ) : (
                  <div className="space-y-2">
                    {machines.map((m) => (
                      <div key={m.id} className="flex items-center justify-between bg-panel2 border border-border rounded px-3 py-2.5">
                        <div className="flex items-center gap-3">
                          <span className={`w-2 h-2 rounded-full ${m.status === "fault" ? "bg-danger pulse-critical" : m.status === "running" ? "bg-safe" : "bg-textmuted"}`} />
                          <div>
                            <p className="text-sm text-textprimary font-medium">{m.name}</p>
                            <p className="text-xs text-textmuted font-mono">{m.machine_id} · {m.location || "—"}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-mono text-textmuted">{m.health_score != null ? `${m.health_score}%` : "—"}</span>
                          <StatusPill status={m.status} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Panel>
            </div>

            {/* Recent alerts */}
            <Panel title="Recent Alerts">
              {alerts.length === 0 ? (
                <p className="text-textmuted text-sm flex items-center gap-2"><ShieldAlert size={16} className="text-safe" /> All clear.</p>
              ) : (
                <div className="space-y-2">
                  {alerts.map((a) => (
                    <div key={a.id} className="border border-border rounded px-3 py-2 bg-panel2">
                      <div className="flex items-center justify-between mb-1">
                        <SeverityBadge severity={a.severity} />
                        <span className="text-xs text-textmuted font-mono">{new Date(a.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-sm text-textprimary">{a.title}</p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>

          {/* Recent violations */}
          <Panel title="Recent PPE Violations">
            {violations.length === 0 ? (
              <p className="text-textmuted text-sm flex items-center gap-2"><HardHat size={16} className="text-safe" /> No violations recorded recently.</p>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                {violations.map((v) => (
                  <div key={v.id} className="border border-danger/30 bg-danger/5 rounded p-3">
                    <p className="text-xs font-mono text-textmuted mb-1">{v.camera_id} · {new Date(v.timestamp).toLocaleString()}</p>
                    <p className="text-sm text-textprimary">
                      {v.detections.map((d) => d.class_name).join(", ")}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      )}
    </Layout>
  );
}
