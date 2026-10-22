import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import Layout from "../components/Layout";
import { Panel } from "../components/UI";
import api from "../api/client";
import type { Alert, Detection } from "../types";

const COLORS = ["#FF4D4F", "#F0A202", "#3DDC84", "#8B949E"];

export default function Analytics() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [detections, setDetections] = useState<Detection[]>([]);

  useEffect(() => {
    api.get("/api/alerts", { params: { limit: 500 } }).then((r) => setAlerts(r.data));
    api.get("/api/detections", { params: { limit: 500 } }).then((r) => setDetections(r.data));
  }, []);

  const severityCounts = ["critical", "warning", "info"].map((s) => ({
    name: s, value: alerts.filter((a) => a.severity === s).length,
  }));

  const sourceCounts = ["sensor", "detection", "inventory", "manual"].map((s) => ({
    name: s, count: alerts.filter((a) => a.source === s).length,
  }));

  const violationClassCounts: Record<string, number> = {};
  detections.filter((d) => d.is_violation).forEach((d) => {
    d.detections.forEach((item) => {
      violationClassCounts[item.class_name] = (violationClassCounts[item.class_name] || 0) + 1;
    });
  });
  const violationData = Object.entries(violationClassCounts).map(([name, count]) => ({ name, count }));

  return (
    <Layout title="Analytics">
      <div className="grid lg:grid-cols-2 gap-6">
        <Panel title="Alerts by Severity">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={severityCounts} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={3}>
                {severityCounts.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#151B23", border: "1px solid #262E38" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Alerts by Source">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={sourceCounts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262E38" />
              <XAxis dataKey="name" stroke="#8B949E" fontSize={11} />
              <YAxis stroke="#8B949E" fontSize={11} allowDecimals={false} />
              <Tooltip contentStyle={{ background: "#151B23", border: "1px solid #262E38" }} />
              <Bar dataKey="count" fill="#F0A202" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="PPE Violation Types" action={undefined}>
          {violationData.length === 0 ? (
            <p className="text-textmuted text-sm">No violations recorded yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={violationData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#262E38" />
                <XAxis type="number" stroke="#8B949E" fontSize={11} allowDecimals={false} />
                <YAxis type="category" dataKey="name" stroke="#8B949E" fontSize={11} width={110} />
                <Tooltip contentStyle={{ background: "#151B23", border: "1px solid #262E38" }} />
                <Bar dataKey="count" fill="#FF4D4F" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>
      </div>
    </Layout>
  );
}
