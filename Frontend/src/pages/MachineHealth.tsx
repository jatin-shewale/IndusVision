import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Sparkles } from "lucide-react";
import Layout from "../components/Layout";
import { Panel, StatusPill } from "../components/UI";
import api from "../api/client";
import type { Machine, SensorReading } from "../types";

export default function MachineHealth() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    api.get("/api/machines").then((res) => {
      setMachines(res.data);
      if (res.data.length && !selected) setSelected(res.data[0].machine_id);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    async function load() {
      const res = await api.get(`/api/sensors/${selected}`, { params: { limit: 50 } });
      setReadings(res.data.reverse());
      setAiSummary("");
    }
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, [selected]);

  async function getAiSummary() {
    setAiLoading(true);
    try {
      const res = await api.get(`/api/ai/machine-summary/${selected}`);
      setAiSummary(res.data.summary);
    } catch (e: any) {
      setAiSummary(e?.response?.data?.detail || "Could not generate AI summary. Check GEMINI_API_KEY in backend/.env.");
    } finally {
      setAiLoading(false);
    }
  }

  const chartData = readings.map((r) => ({
    time: new Date(r.timestamp).toLocaleTimeString(),
    temperature: r.temperature >= 0 ? r.temperature : null,
    humidity: r.humidity >= 0 ? r.humidity : null,
    current: r.current_amps,
    vibration: r.vibration,
    gas: r.gas_raw,
    distance: r.distance_cm >= 0 ? r.distance_cm : null,
  }));

  const charts = [
    { key: "temperature", title: "Temperature", unit: "°C", color: "#FF4D4F" },
    { key: "humidity", title: "Humidity", unit: "%", color: "#4DA3FF" },
    { key: "vibration", title: "Vibration", unit: "0 / 1", color: "#B37FEB" },
    { key: "current", title: "Current", unit: "A", color: "#F0A202" },
    { key: "gas", title: "Gas / Smoke", unit: "raw", color: "#36CFC9" },
    { key: "distance", title: "Distance", unit: "cm", color: "#73D13D" },
  ];

  return (
    <Layout title="Machine Health">
      <div className="space-y-6">
        <div className="flex gap-2 flex-wrap">
          {machines.map((m) => (
            <button
              key={m.machine_id}
              onClick={() => setSelected(m.machine_id)}
              className={`px-3 py-1.5 rounded text-sm font-mono border transition-colors ${
                selected === m.machine_id
                  ? "bg-amber text-base border-amber"
                  : "bg-panel border-border text-textmuted hover:text-textprimary"
              }`}
            >
              {m.machine_id}
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 grid md:grid-cols-2 gap-4">
            {charts.map((chart) => <Panel key={chart.key} title={`${chart.title} (${chart.unit})`}>
              {chartData.length === 0 ? (
                <p className="text-textmuted text-sm">No sensor data yet for this machine. Make sure the ESP32 is POSTing to /api/sensors/ingest.</p>
              ) : (
                <ResponsiveContainer width="100%" height={190}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262E38" />
                    <XAxis dataKey="time" stroke="#8B949E" fontSize={11} />
                    <YAxis stroke="#8B949E" fontSize={11} />
                    <Tooltip contentStyle={{ background: "#151B23", border: "1px solid #262E38" }} />
                    <Line type="monotone" dataKey={chart.key} stroke={chart.color} strokeWidth={2} dot={false} name={chart.title} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </Panel>)}
          </div>

          <Panel
            title="AI Health Summary"
            action={
              <button onClick={getAiSummary} disabled={aiLoading || !selected}
                className="flex items-center gap-1 text-xs font-mono text-amber border border-amber/40 rounded px-2 py-1 hover:bg-amber/10 disabled:opacity-50">
                <Sparkles size={13} /> {aiLoading ? "Thinking..." : "Ask Gemini"}
              </button>
            }
          >
            {aiSummary ? (
              <p className="text-sm text-textprimary leading-relaxed">{aiSummary}</p>
            ) : (
              <p className="text-textmuted text-sm">Click "Ask Gemini" to get a plain-English health summary for {selected || "the selected machine"}, generated from its recent sensor history.</p>
            )}
          </Panel>
        </div>

        <Panel title="Latest Readings">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-textmuted font-mono text-xs uppercase border-b border-border">
                  <th className="py-2 pr-4">Time</th>
                  <th className="py-2 pr-4">Temp °C</th>
                  <th className="py-2 pr-4">Humidity %</th>
                  <th className="py-2 pr-4">Vibration</th>
                  <th className="py-2 pr-4">Current A</th>
                  <th className="py-2 pr-4">Gas</th>
                  <th className="py-2 pr-4">Distance cm</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {[...readings].reverse().slice(0, 15).map((r) => (
                  <tr key={r.id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-mono text-xs text-textmuted">{new Date(r.timestamp).toLocaleTimeString()}</td>
                    <td className="py-2 pr-4">{r.temperature}</td>
                    <td className="py-2 pr-4">{r.humidity}</td>
                    <td className="py-2 pr-4">{r.vibration}</td>
                    <td className="py-2 pr-4">{r.current_amps}</td>
                    <td className="py-2 pr-4">{r.gas_raw}</td>
                    <td className="py-2 pr-4">{r.distance_cm}</td>
                    <td className="py-2 pr-4"><StatusPill status={r.fault ? "fault" : "running"} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </Layout>
  );
}
