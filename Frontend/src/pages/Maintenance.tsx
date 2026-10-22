import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { Panel, StatusPill } from "../components/UI";
import api from "../api/client";
import type { Machine, MaintenanceEvent, MaintenancePrediction } from "../types";

export default function Maintenance() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [predictions, setPredictions] = useState<Record<string, MaintenancePrediction>>({});
  const [events, setEvents] = useState<MaintenanceEvent[]>([]);

  useEffect(() => {
    async function load() {
      const mRes = await api.get("/api/machines");
      const esp32Machines = mRes.data.filter((machine: Machine) => machine.machine_id === "MACHINE_01");
      setMachines(esp32Machines);
      const preds: Record<string, MaintenancePrediction> = {};
      for (const m of esp32Machines) {
        try {
          const pRes = await api.get(`/api/maintenance/${m.machine_id}/latest`);
          preds[m.machine_id] = pRes.data;
        } catch {
          // no prediction yet for this machine
        }
      }
      setPredictions(preds);
      const eventsRes = await api.get("/api/maintenance/events", { params: { limit: 200 } });
      setEvents(eventsRes.data);
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout title="Predictive Maintenance">
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {machines.map((m) => {
          const p = predictions[m.machine_id];
          return (
            <Panel key={m.id} title="ESP32 Monitored Machine">
              {!p ? (
                <p className="text-textmuted text-sm">No prediction yet — waiting for sensor data.</p>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-textmuted font-mono uppercase">Predicted Status</span>
                    <StatusPill status={p.predicted_status} />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs text-textmuted mb-1">
                      <span>Health Score</span><span>{p.health_score}%</span>
                    </div>
                    <div className="w-full bg-panel2 rounded-full h-2 border border-border">
                      <div
                        className={`h-2 rounded-full ${p.health_score > 70 ? "bg-safe" : p.health_score > 40 ? "bg-amber" : "bg-danger"}`}
                        style={{ width: `${p.health_score}%` }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-textmuted font-mono">Failure Probability</p>
                      <p className="text-textprimary font-display font-600">{Math.round(p.failure_probability * 100)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-textmuted font-mono">Remaining Useful Life</p>
                      <p className="text-textprimary font-display font-600">{p.remaining_useful_life_days} days</p>
                    </div>
                  </div>
                  <p className="text-xs text-textmuted font-mono border-t border-border pt-2">
                    Next maintenance: {new Date(p.next_maintenance_date).toLocaleDateString()}
                  </p>
                </div>
              )}
            </Panel>
          );
        })}
      </div>

      {machines.length === 0 && (
        <p className="text-textmuted text-sm mt-6">
          MACHINE_01 is not registered yet. Register the ESP32 monitored machine and send sensor readings to view its prediction here.
        </p>
      )}

      <Panel title="Fault & Worker Safety History">
        {events.length === 0 ? (
          <p className="text-textmuted text-sm">No sensor faults or Worker Safety violations recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-textmuted font-mono text-xs uppercase border-b border-border">
                  <th className="py-2 pr-4">Time</th><th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Machine / Camera</th><th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Cause</th><th className="py-2 pr-4">Sensor readings</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={`${event.source}-${event.id}`} className="border-b border-border/50 align-top">
                    <td className="py-2 pr-4 whitespace-nowrap font-mono text-xs text-textmuted">{new Date(event.timestamp).toLocaleString()}</td>
                    <td className="py-2 pr-4">{event.source === "sensor" ? "Sensor" : "Worker Safety"}</td>
                    <td className="py-2 pr-4">{event.machine_id || event.camera_id || "—"}</td>
                    <td className="py-2 pr-4"><StatusPill status={event.status} /></td>
                    <td className="py-2 pr-4">{event.causes.join(", ")}</td>
                    <td className="py-2 pr-4 text-xs text-textmuted whitespace-nowrap">
                      {event.source === "sensor"
                        ? `Temp ${event.temperature ?? "—"}°C · Humidity ${event.humidity ?? "—"}% · Vibration ${event.vibration ?? "—"} · Current ${event.current_amps ?? "—"}A · Gas ${event.gas_raw ?? "—"} · Distance ${event.distance_cm ?? "—"}cm`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </Layout>
  );
}
