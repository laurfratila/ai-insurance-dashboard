import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Bell, LayoutDashboard, FileText, ShieldAlert, Workflow, Users, Settings } from "lucide-react";
import React from "react";

function NavItem({ to, label, icon: Icon }: { to: string; label: string; icon: React.ComponentType<any> }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `navlink ${isActive ? "active" : ""}`}
    >
      <Icon size={18} />
      <span>{label}</span>
    </NavLink>
  );
}

export default function Shell({ children }: { children: React.ReactNode }) {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get("/health")).data,
    refetchInterval: 30000,
  });
  const healthy = health.data?.status === "ok";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "248px 1fr", minHeight: "100vh" }}>
      <aside
        className="sidebar"
        style={{
          background: "linear-gradient(180deg, var(--brand), #be123c)",
          color: "white",
          padding: 22,
        }}
        aria-label="Sidebar navigation"
      >
        <div style={{ fontSize: 24, fontWeight: 900, marginBottom: 18, letterSpacing: 0.2 }}>EnsuraX</div>
        <nav style={{ display: "grid", gap: 6 }}>
          <NavItem to="/overview" label="Overview" icon={LayoutDashboard} />
          <NavItem to="/claims" label="Claims" icon={FileText} />
          <NavItem to="/risk" label="Risk & Fraud" icon={ShieldAlert} />
          <NavItem to="/ops" label="Operations" icon={Workflow} />
          <NavItem to="/c360" label="Customer 360" icon={Users} />
          <div style={{ height: 16 }} />
          <NavItem to="/settings" label="Settings" icon={Settings} />
        </nav>
      </aside>

      <div style={{ padding: 24 }}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <div />
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              title={healthy ? "Backend: OK" : "Backend: unavailable"}
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: healthy ? "var(--good)" : "var(--bad)",
              }}
            />
            <button className="btn" title="Notifications" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Bell size={16} /> Notifications
            </button>
          </div>
        </header>
        <div className="container">{children}</div>
      </div>
    </div>
  );
}
