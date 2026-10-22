import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, HardHat, Activity, Boxes, Wrench,
  BellRing, FileBarChart, Users as UsersIcon, LineChart, Settings as SettingsIcon,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/worker-safety", label: "Worker Safety", icon: HardHat },
  { to: "/machine-health", label: "Machine Health", icon: Activity },
  { to: "/inventory", label: "Inventory", icon: Boxes },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/alerts", label: "Alerts", icon: BellRing },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/users", label: "Users", icon: UsersIcon, adminOnly: true },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export default function Sidebar() {
  const { user } = useAuth();

  return (
    <aside className="w-60 bg-panel border-r border-border flex flex-col h-screen sticky top-0">
      <div className="px-5 py-6 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-amber pulse-safe" />
          <h1 className="font-display font-700 text-xl tracking-wide text-textprimary">
            INDUS<span className="text-amber">VISION</span>
          </h1>
        </div>
        <p className="text-xs text-textmuted mt-1 font-mono">Industry 4.0 Monitor</p>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {navItems
          .filter((item) => !item.adminOnly || user?.role === "admin")
          .map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-colors border-l-2 ${
                  isActive
                    ? "bg-panel2 border-amber text-textprimary"
                    : "border-transparent text-textmuted hover:text-textprimary hover:bg-panel2/50"
                }`
              }
            >
              <Icon size={17} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
      </nav>

      <div className="px-5 py-4 border-t border-border text-xs text-textmuted font-mono">
        v1.0.0 · {user?.role?.toUpperCase()}
      </div>
    </aside>
  );
}
