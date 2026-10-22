import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Topbar({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <header className="h-16 border-b border-border bg-base/80 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-10">
      <h2 className="font-display text-lg font-600 text-textprimary tracking-wide">{title}</h2>

      <div className="flex items-center gap-5">
        <span className="font-mono text-xs text-textmuted hidden sm:block">
          {now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })} · {now.toLocaleTimeString("en-IN")}
        </span>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-panel2 flex items-center justify-center font-display font-600 text-amber border border-border">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="hidden md:block">
            <p className="text-sm text-textprimary leading-tight">{user?.name}</p>
            <p className="text-xs text-textmuted leading-tight">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="text-textmuted hover:text-danger transition-colors"
          title="Log out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
