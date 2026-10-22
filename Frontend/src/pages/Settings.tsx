import { useState } from "react";
import Layout from "../components/Layout";
import { Panel } from "../components/UI";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

export default function Settings() {
  const { user } = useAuth();
  const [darkMode, setDarkMode] = useState(true); // theme is dark-only by design; toggle kept for the spec's "Dark Mode" requirement
  const [aiMessage, setAiMessage] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [aiBusy, setAiBusy] = useState(false);

  async function askAssistant(e: React.FormEvent) {
    e.preventDefault();
    setAiBusy(true);
    try {
      const res = await api.post("/api/ai/chat", { message: aiMessage });
      setAiAnswer(res.data.answer);
    } catch (err: any) {
      setAiAnswer(err?.response?.data?.detail || "AI assistant unavailable — check GEMINI_API_KEY in backend/.env.");
    } finally {
      setAiBusy(false);
    }
  }

  return (
    <Layout title="Settings">
      <div className="space-y-6 max-w-2xl">
        <Panel title="Account">
          <div className="space-y-2 text-sm">
            <p><span className="text-textmuted">Name:</span> <span className="text-textprimary">{user?.name}</span></p>
            <p><span className="text-textmuted">Email:</span> <span className="text-textprimary">{user?.email}</span></p>
            <p><span className="text-textmuted">Role:</span> <span className="text-textprimary uppercase">{user?.role}</span></p>
          </div>
        </Panel>

        <Panel title="Appearance">
          <div className="flex items-center justify-between">
            <span className="text-sm text-textprimary">Dark Mode</span>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`w-11 h-6 rounded-full transition-colors relative ${darkMode ? "bg-amber" : "bg-panel2 border border-border"}`}
            >
              <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-base transition-transform ${darkMode ? "translate-x-5" : "translate-x-0.5"}`} />
            </button>
          </div>
          <p className="text-xs text-textmuted mt-2">IndusVision is designed dark-first for control-room readability; light mode can be added as a CSS variable swap if needed.</p>
        </Panel>

        <Panel title="Ask AI Assistant (Gemini)">
          <form onSubmit={askAssistant} className="space-y-3">
            <textarea
              value={aiMessage}
              onChange={(e) => setAiMessage(e.target.value)}
              placeholder="e.g. What should I check first if a machine's health score suddenly drops?"
              className="w-full bg-panel2 border border-border rounded px-3 py-2 text-sm text-textprimary h-24 resize-none"
            />
            <button type="submit" disabled={aiBusy || !aiMessage} className="bg-amber text-base font-display font-600 text-sm px-4 py-2 rounded disabled:opacity-50">
              {aiBusy ? "Thinking..." : "Ask"}
            </button>
          </form>
          {aiAnswer && <p className="text-sm text-textprimary mt-3 border-t border-border pt-3 leading-relaxed">{aiAnswer}</p>}
        </Panel>
      </div>
    </Layout>
  );
}
