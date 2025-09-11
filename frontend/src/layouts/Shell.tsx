import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Button } from "@/components/ui/button";
import ChatDock from "@/features/chat/ChatDock";

import {
  Bell,
  MessageSquare,
  LayoutDashboard,
  FileText,
  ShieldAlert,
  Workflow,
  Users,
  Settings,
} from "lucide-react";

function NavItem({
  to,
  label,
  icon: Icon,
}: {
  to: string;
  label: string;
  icon: React.ComponentType<any>;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-3 py-2 rounded-lg font-semibold transition
         ${isActive ? "bg-white text-slate-900 shadow-soft" : "text-white/95 hover:bg-white/10"}`
      }
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
    refetchInterval: 30_000,
  });
  const ok = health.data?.status === "ok";

  // Chat dock toggle
  const [chatOpen, setChatOpen] = useState(true);

  return (
    <div
      className="grid min-h-screen"
      style={{ gridTemplateColumns: chatOpen ? "260px 1fr 360px" : "260px 1fr" }}
    >
      {/* Sidebar */}
      <aside className="bg-gradient-to-b from-indigo-950 to-slate-900 text-white p-6">
        <div className="text-2xl font-black tracking-tight mb-4">EnsuraX</div>
        <nav className="grid gap-1">
          <NavItem to="/overview" label="Overview" icon={LayoutDashboard} />
          <NavItem to="/claims" label="Claims" icon={FileText} />
          <NavItem to="/risk" label="Risk & Fraud" icon={ShieldAlert} />
          <NavItem to="/ops" label="Operations" icon={Workflow} />
          <NavItem to="/c360" label="Customer 360" icon={Users} />
          <div className="h-3" />
          <NavItem to="/settings" label="Settings" icon={Settings} />
        </nav>
      </aside>

      {/* Main column */}
      <div className="p-6">
        <header className="flex items-center justify-between mb-4">
          <div />
          <div className="flex items-center gap-2">
            <Button
              variant={chatOpen ? "secondary" : "outline"}
              size="sm"
              className="gap-2"
              onClick={() => setChatOpen((v) => !v)}
            >
              <MessageSquare size={16} />
              {chatOpen ? "Hide Assistant" : "Show Assistant"}
            </Button>

            <span
              className={`size-2 rounded-full ${ok ? "bg-emerald-600" : "bg-rose-500"}`}
              title={ok ? "Backend: OK" : "Backend: down"}
            />
            <Button variant="outline" size="sm" className="gap-2">
              <Bell size={16} /> Notifications
            </Button>
          </div>
        </header>

        <main className="max-w-[1200px] mx-auto">{children}</main>
      </div>

      {/* Right chat dock (persistent across pages) */}
      {chatOpen && <ChatDock visible={chatOpen} onToggle={() => setChatOpen(false)} />}
    </div>
  );
}
