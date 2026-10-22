import { useState } from "react";
import { Download } from "lucide-react";
import Layout from "../components/Layout";
import { Panel } from "../components/UI";
import api from "../api/client";

async function downloadReport(url: string, filename: string) {
  const res = await api.get(url, { responseType: "blob" });
  const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export default function Reports() {
  const [busy, setBusy] = useState<string | null>(null);

  async function handle(url: string, filename: string, key: string) {
    setBusy(key);
    try {
      await downloadReport(url, filename);
    } catch (e) {
      alert("Could not generate report. Check backend logs / Gemini API key.");
    } finally {
      setBusy(null);
    }
  }

  const reportButtons = [
    { label: "Daily Safety Report (PDF)", key: "daily-pdf", url: "/api/reports/safety/daily?fmt=pdf", file: "safety_daily.pdf" },
    { label: "Weekly Safety Report (PDF)", key: "weekly-pdf", url: "/api/reports/safety/weekly?fmt=pdf", file: "safety_weekly.pdf" },
    { label: "Monthly Safety Report (Excel)", key: "monthly-xlsx", url: "/api/reports/safety/monthly?fmt=excel", file: "safety_monthly.xlsx" },
    { label: "Inventory Report (Excel)", key: "inv-xlsx", url: "/api/reports/inventory?fmt=excel", file: "inventory_report.xlsx" },
    { label: "Inventory Report (PDF)", key: "inv-pdf", url: "/api/reports/inventory?fmt=pdf", file: "inventory_report.pdf" },
  ];

  return (
    <Layout title="Reports">
      <Panel title="Generate Reports">
        <p className="text-textmuted text-sm mb-4">
          Safety reports include an AI-generated narrative (via Gemini) summarizing the period's PPE violations.
        </p>
        <div className="grid md:grid-cols-2 gap-3">
          {reportButtons.map((r) => (
            <button
              key={r.key}
              onClick={() => handle(r.url, r.file, r.key)}
              disabled={busy === r.key}
              className="flex items-center justify-between border border-border bg-panel2 rounded px-4 py-3 hover:border-amber/50 transition-colors disabled:opacity-50"
            >
              <span className="text-sm text-textprimary">{r.label}</span>
              <Download size={16} className="text-amber" />
            </button>
          ))}
        </div>
      </Panel>
    </Layout>
  );
}
