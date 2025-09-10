import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRetention, useCrossSell, useChannelMix, useDemographics } from "@/features/c360/api";
import { fmtNumber, fmtPct } from "@/lib/fmt";

function Sparkline({ values }: { values: number[] }) {
  if (!values?.length) return null;
  const min = Math.min(...values), max = Math.max(...values);
  const w = 220, h = 48, step = w / (values.length - 1 || 1);
  const toY = (v: number) => h - ((v - min) / (max - min || 1)) * h;
  const d = values.map((v, i) => `${i ? "L" : "M"} ${i * step},${toY(v)}`).join(" ");
  return <svg width={w} height={h} className="text-slate-800"><path d={d} fill="none" stroke="currentColor" strokeWidth={2}/></svg>;
}

export default function Customer360() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const p = useMemo(() => ({ start_date: start || undefined, end_date: end || undefined }), [start, end]);

  const retention = useRetention(p);
  const crossSell = useCrossSell();
  const channelMix = useChannelMix(p);
  const demo = useDemographics();

  const retentionVals = (retention.data ?? []).map(d => (d.value ?? 0) as number);
  const retentionLatest = retentionVals.length ? retentionVals[retentionVals.length - 1] : 0;

  const cross = crossSell.data ?? [];
  const maxCross = Math.max(1, ...cross.map(i => Number(i.value) || 0)); // scale to max

  const channels = channelMix.data ?? [];
  const channelTotal = Math.max(1, channels.reduce((a, x) => a + (Number(x.value) || 0), 0)); // scale to total

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-[32px] font-black tracking-tight">Customer 360</h1>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">Start</Label>
            <Input type="date" value={start} onChange={(e)=>setStart(e.target.value)} className="w-44"/>
          </div>
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">End</Label>
            <Input type="date" value={end} onChange={(e)=>setEnd(e.target.value)} className="w-44"/>
          </div>
          <div className="ml-auto flex gap-2">
            <Button variant="ghost" onClick={()=>{ setStart(""); setEnd(""); }}>Clear</Button>
          </div>
        </div>
      </Card>

      {/* KPIs / Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Retention */}
        <Card className="p-4">
          <div className="text-sm text-slate-500">Retention (latest)</div>
          <div className="text-3xl font-black">{fmtPct(retentionLatest)}</div>
          <div className="mt-2"><Sparkline values={retentionVals} /></div>
        </Card>

        {/* Cross-sell — normalized to the max value */}
        <Card className="p-4">
          <div className="text-sm text-slate-500">Cross-sell — customers by #products</div>
          <div className="space-y-2 mt-2">
            {cross.map(i => {
              const count = Number(i.value) || 0;
              const pct = Math.min(100, Math.max(0, (count / maxCross) * 100));
              return (
                <div key={i.key} className="flex items-center gap-3">
                  <div className="w-6 text-sm text-slate-600">{i.key}</div>
                  <div className="h-2 bg-slate-200/70 rounded w-full overflow-hidden">
                    <div className="h-2 bg-slate-900 rounded" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="w-16 text-right text-sm">{fmtNumber(count)}</div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Channel mix — normalized to total */}
        <Card className="p-4">
          <div className="text-sm text-slate-500">Channel mix</div>
          <div className="space-y-2 mt-2">
            {channels.map(i => {
              const count = Number(i.value) || 0;
              const frac = count / channelTotal;
              const pct = Math.min(100, Math.max(0, frac * 100));
              return (
                <div key={i.key} className="flex items-center gap-3">
                  <div className="w-24 text-sm font-medium">{i.key}</div>
                  <div className="h-2 bg-slate-200/70 rounded w-full overflow-hidden">
                    <div className="h-2 bg-slate-900 rounded" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="w-28 text-right text-sm">
                    {fmtNumber(count)} <span className="text-slate-500">({fmtPct(frac)})</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Demographics table */}
      <Card className="p-4">
        <div className="font-semibold mb-3">Demographics (age × county)</div>
        <div className="max-h-[360px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr><th className="py-2">Age band</th><th>County</th><th className="text-right">Customers</th></tr>
            </thead>
            <tbody>
              {(demo.data ?? []).map((d, i) => (
                <tr key={`${d.age_band}-${d.county_name}-${i}`} className="border-t">
                  <td className="py-1">{d.age_band}</td>
                  <td className="py-1">{d.county_name}</td>
                  <td className="py-1 text-right">{fmtNumber(d.customers)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
