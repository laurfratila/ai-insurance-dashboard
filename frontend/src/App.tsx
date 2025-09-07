import { useEffect, useMemo, useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import {
  Activity,
  Shield,
  FileText,
  Cpu,
  Menu,
  Moon,
  Sun,
} from "lucide-react";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

// ──────────────────────────────────────────────────────────────
// Query Client (React Query)
// ──────────────────────────────────────────────────────────────
const queryClient = new QueryClient();

function useHealth() {
  return useQuery<{ status: string }>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/health");
      if (!res.ok) throw new Error("Health check failed");
      return res.json();
    },
    // don't spam requests
    refetchInterval: 10000,
  });
}

// ──────────────────────────────────────────────────────────────
// Dark mode
// ──────────────────────────────────────────────────────────────
function useDarkMode() {
  const [dark, setDark] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const stored = localStorage.getItem("theme");
    if (stored) return stored === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  return { dark, setDark };
}

// ──────────────────────────────────────────────────────────────
// Layout components
// ──────────────────────────────────────────────────────────────
function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <aside
      className={`fixed z-20 h-full w-64 transform border-r bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/80 transition-transform duration-200 ${
        open ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}
    >
      <div className="flex items-center gap-2 p-4 border-b dark:border-zinc-800">
        <Shield className="h-5 w-5" />
        <span className="font-semibold">AI Insurance</span>
      </div>
      <nav className="p-3 space-y-1">
        <NavItem icon={<Activity className="h-4 w-4" />} label="Dashboard" active />
        <NavItem icon={<FileText className="h-4 w-4" />} label="Claims" />
        <NavItem icon={<Shield className="h-4 w-4" />} label="Policies" />
        <NavItem icon={<Cpu className="h-4 w-4" />} label="AI Insights" />
      </nav>
      <button
        onClick={onClose}
        className="md:hidden m-3 w-full rounded-xl border px-3 py-2 text-sm hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800"
      >
        Close
      </button>
    </aside>
  );
}

function NavItem({ icon, label, active = false }: { icon: React.ReactNode; label: string; active?: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm cursor-pointer select-none border transition-all ${
        active
          ? "border-transparent bg-zinc-100 dark:bg-zinc-800"
          : "border-transparent hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
      }`}
    >
      {icon}
      <span>{label}</span>
    </div>
  );
}

function Header({ onMenu }: { onMenu: () => void }) {
  const { dark, setDark } = useDarkMode();
  const { data, isLoading, isError } = useHealth();

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b bg-white/70 px-4 py-3 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/70">
      <div className="flex items-center gap-2">
        <button onClick={onMenu} className="md:hidden rounded-xl border px-2 py-2 dark:border-zinc-800">
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-lg font-semibold tracking-tight">Dashboard</h1>
      </div>

      <div className="flex items-center gap-3 text-sm">
        <span className={`hidden sm:inline ${isError ? "text-red-600" : isLoading ? "text-zinc-500" : "text-emerald-600"}`}>
          API: {isLoading ? "checking…" : isError ? "error" : data?.status || "unknown"}
        </span>
        <button
          onClick={() => setDark(!dark)}
          className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800"
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          <span className="hidden sm:inline">{dark ? "Light" : "Dark"} mode</span>
        </button>
      </div>
    </header>
  );
}

function KPI({ title, value, delta, icon }: { title: string; value: string; delta?: string; icon?: React.ReactNode }) {
  return (
    <div className="rounded-2xl border p-4 shadow-sm dark:border-zinc-800">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{title}</p>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {delta && <div className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{delta}</div>}
    </div>
  );
}

function useMockSeries() {
  // deterministic sample data
  return useMemo(
    () =>
      Array.from({ length: 12 }).map((_, i) => ({
        month: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i],
        claims: Math.round(30 + 20 * Math.sin((i / 12) * Math.PI * 2) + (i % 3) * 4),
        premium: Math.round(100 + 40 * Math.cos((i / 12) * Math.PI * 2)),
      })),
    []
  );
}

function ClaimsChart() {
  const data = useMockSeries();
  return (
    <div className="rounded-2xl border p-4 shadow-sm dark:border-zinc-800">
      <div className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">Claims vs Premium (sample)</div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
            <XAxis dataKey="month" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip />
            <Line type="monotone" dataKey="claims" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="premium" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function Content() {
  return (
    <main className="p-4 md:p-6 space-y-6">
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <KPI title="Total Policies" value="12,480" delta="▲ 2.1% from last month" icon={<Shield className="h-4 w-4" />} />
        <KPI title="Open Claims" value="384" delta="▼ 0.6% this week" icon={<FileText className="h-4 w-4" />} />
        <KPI title="Loss Ratio" value="58.2%" delta="▲ 1.3% vs target" icon={<Activity className="h-4 w-4" />} />
      </section>

      <section className="grid grid-cols-1 gap-4">
        <ClaimsChart />
      </section>
    </main>
  );
}

function Shell() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-dvh bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="md:pl-64">
        <Header onMenu={() => setOpen(true)} />
        <Content />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Shell />
    </QueryClientProvider>
  );
}
