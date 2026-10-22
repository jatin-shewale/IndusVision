import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, AlertTriangle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-base flex">
      {/* Left: hazard-stripe hero, grounded in the industrial-monitoring subject */}
      <div className="hidden lg:flex lg:w-1/2 hazard-stripe border-r border-border items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-base via-transparent to-transparent" />
        <div className="relative z-10 px-12 max-w-md">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-3 h-3 rounded-full bg-amber pulse-safe" />
            <span className="font-mono text-xs text-textmuted uppercase tracking-widest">System Online</span>
          </div>
          <h1 className="font-display text-5xl font-700 text-textprimary leading-tight">
            INDUS<span className="text-amber">VISION</span>
          </h1>
          <p className="text-textmuted mt-4 leading-relaxed">
            Real-time AI vision, IoT sensing, and predictive maintenance —
            unified into one control room for the whole plant floor.
          </p>
          <div className="mt-8 space-y-3 font-mono text-sm text-textmuted">
            <div className="flex items-center gap-2"><ShieldCheck size={16} className="text-safe" /> PPE compliance monitoring</div>
            <div className="flex items-center gap-2"><AlertTriangle size={16} className="text-amber" /> Live machine health & alerts</div>
          </div>
        </div>
      </div>

      {/* Right: login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8 text-center">
            <h1 className="font-display text-3xl font-700 text-textprimary">
              INDUS<span className="text-amber">VISION</span>
            </h1>
          </div>

          <h2 className="font-display text-2xl font-600 text-textprimary mb-1">Sign in</h2>
          <p className="text-textmuted text-sm mb-6">Access your role-based dashboard.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-mono text-textmuted uppercase">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full mt-1 bg-panel border border-border rounded px-3 py-2.5 text-textprimary focus:outline-none focus:border-amber transition-colors"
                placeholder="you@indusvision.local"
              />
            </div>
            <div>
              <label className="text-xs font-mono text-textmuted uppercase">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full mt-1 bg-panel border border-border rounded px-3 py-2.5 text-textprimary focus:outline-none focus:border-amber transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="bg-danger/10 border border-danger/30 text-danger text-sm rounded px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full bg-amber text-base font-display font-700 rounded py-2.5 hover:brightness-110 transition disabled:opacity-50"
            >
              {busy ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="text-xs text-textmuted mt-6 font-mono">
            First time setup? Run <code className="text-amber">seed_data.py</code> on the backend, then log in with
            <br />admin@indusvision.local / Admin@123
          </p>
        </div>
      </div>
    </div>
  );
}
