
import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePaidVsReserve, useSeverityHistogram, useOpenVsClosedRatio } from "@/features/claims/api";
import type { TwoSeriesPoint } from "@/features/claims/types";
import { fmtNumber, fmtCurrency, fmtPct } from "@/lib/fmt";

// tiny inline sparkline (SVG)
function Sparkline({ data, a }: { data: TwoSeriesPoint[]; a: "a" | "b" }) {
  if (!data?.length) return null;
  const vals = data.map(d => d[a] ?? 0);
  const min = Math.min(...vals), max = Math.max(...vals);
  const w = 220, h = 48;
  const toY = (v: number) => h - ((v - min) / (max - min || 1)) * h;
  const step = w / (vals.length - 1 || 1);
  const dPath = vals.map((v, i) => `${i ? "L" : "M"} ${i * step},${toY(v)}`).join(" ");
  return (
    <svg width={w} height={h} className="text-slate-800">
      <path d={dPath} fill="none" stroke="currentColor" strokeWidth={2} />
    </svg>
  );
}

export default function Claims() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const params = useMemo(() => ({ start_date: start || undefined, end_date: end || undefined }), [start, end]);

  const paidReserve = usePaidVsReserve(params);
  const severities = useSeverityHistogram();
  const openClosed = useOpenVsClosedRatio(params);

  const paidTotal = useMemo(
    () => (paidReserve.data ?? []).reduce((a, p) => a + (p.a || 0), 0),
    [paidReserve.data]
  );
  const reserveTotal = useMemo(
    () => (paidReserve.data ?? []).reduce((a, p) => a + (p.b || 0), 0),
    [paidReserve.data]
  );
  const avgCloseRatio = useMemo(() => {
    const arr = openClosed.data ?? [];
    if (!arr.length) return 0;
    const r = arr.reduce((a, x) => a + (x.ratio ?? 0), 0) / arr.length;
    return r;
  }, [openClosed.data]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-[32px] font-black tracking-tight">Claims</h1>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">Start</Label>
            <Input type="date" value={start} onChange={(e)=>setStart(e.target.value)} className="w-44" />
          </div>
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">End</Label>
            <Input type="date" value={end} onChange={(e)=>setEnd(e.target.value)} className="w-44" />
          </div>
          <div className="ml-auto flex gap-2">
            <Button variant="ghost" onClick={()=>{setStart(""); setEnd("");}}>Clear</Button>
          </div>
        </div>
      </Card>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="p-4">
          <div className="text-sm text-slate-500">Paid Total</div>
          <div className="text-3xl font-black">{fmtCurrency(paidTotal)}</div>
          <div className="mt-2"><Sparkline data={paidReserve.data ?? []} a="a" /></div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500">Outstanding Reserve</div>
          <div className="text-3xl font-black">{fmtCurrency(reserveTotal)}</div>
          <div className="mt-2"><Sparkline data={paidReserve.data ?? []} a="b" /></div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500">Closed / Open Ratio</div>
          <div className="text-3xl font-black">{fmtPct(avgCloseRatio)}</div>
          <div className="text-xs text-slate-500 mt-1">Points: {openClosed.data?.length ?? 0}</div>
        </Card>
      </div>

      {/* Charts / Lists */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-4">
          <div className="font-semibold mb-3">Severity distribution</div>
          <div className="space-y-2">
            {(severities.data ?? []).map(s => (
              <div key={s.key} className="flex items-center gap-3">
                <div className="w-28 text-sm text-slate-600">{s.key}</div>
                <div className="h-2 bg-slate-200 rounded w-full">
                  <div className="h-2 bg-slate-900 rounded" style={{ width: `${Math.min(100, s.value)}%` }} />
                </div>
                <div className="w-16 text-right text-sm">{fmtNumber(s.value)}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="font-semibold mb-3">Open vs Closed — monthly ratio</div>
          <div className="space-y-1 text-sm text-slate-600">
            {(openClosed.data ?? []).map(p => (
              <div key={p.period} className="flex items-center justify-between">
                <div>{new Date(p.period).toLocaleDateString(undefined, { month: "short", year: "2-digit" })}</div>
                <div className="w-48 h-2 bg-slate-200 rounded">
                  <div className="h-2 bg-slate-900 rounded" style={{ width: `${Math.max(0, Math.min(1, p.ratio ?? 0)) * 100}%` }} />
                </div>
                <div className="w-16 text-right">{fmtPct(p.ratio ?? 0)}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
