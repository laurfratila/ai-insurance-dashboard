import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useClaimsByPeril, useCatExposure } from "@/features/risk/api";
import { fmtNumber } from "@/lib/fmt";

function HBar({ pct }: { pct: number }) {
  return (
    <div className="h-2 bg-slate-200/70 rounded w-full overflow-hidden">
      <div className="h-2 bg-slate-900 rounded" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
    </div>
  );
}

export default function Risk() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [topN, setTopN] = useState(10);
  const [region, setRegion] = useState("");

  const params = useMemo(() => ({ start_date: start || undefined, end_date: end || undefined }), [start, end]);

  const peril = useClaimsByPeril({ ...params, top_n: topN });
  const cat   = useCatExposure({ ...params, region: region || undefined });

  const maxPeril = Math.max(1, ...(peril.data ?? []).map(d => Number(d.value) || 0));
  const catTotal = Math.max(1,  ...(cat.data ?? []).map(d => Number(d.value) || 0));

  return (
    <div className="space-y-4">
      <h1 className="text-[32px] font-black tracking-tight">Risk & Fraud</h1>

      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">Start</Label>
            <Input type="date" value={start} onChange={e=>setStart(e.target.value)} className="w-44" />
          </div>
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">End</Label>
            <Input type="date" value={end} onChange={e=>setEnd(e.target.value)} className="w-44" />
          </div>
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">Top N perils</Label>
            <Input type="number" min={1} max={100} value={topN} onChange={e=>setTopN(Number(e.target.value||10))} className="w-28" />
          </div>
          <div className="flex flex-col">
            <Label className="text-xs text-slate-500">Region (optional)</Label>
            <Input placeholder="e.g. RO_AB" value={region} onChange={e=>setRegion(e.target.value)} className="w-40" />
          </div>
          <div className="ml-auto">
            <Button variant="ghost" onClick={()=>{ setStart(""); setEnd(""); setRegion(""); setTopN(10); }}>Clear</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-4">
          <div className="text-sm text-slate-500 mb-2">Claims by peril (Top {topN})</div>
          <div className="space-y-2">
            {(peril.data ?? []).map(item => {
              const v = Number(item.value) || 0;
              const pct = (v / maxPeril) * 100;
              return (
                <div key={item.key} className="flex items-center gap-3">
                  <div className="w-28 font-medium">{item.key}</div>
                  <HBar pct={pct} />
                  <div className="w-20 text-right text-sm">{fmtNumber(v)}</div>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-slate-500 mb-2">CAT exposure by region</div>
          <div className="space-y-2">
            {(cat.data ?? []).map(item => {
              const v = Number(item.value) || 0;
              const pct = (v / catTotal) * 100;
              return (
                <div key={item.key} className="flex items-center gap-3">
                  <div className="w-28 font-medium">{item.key}</div>
                  <HBar pct={pct} />
                  <div className="w-28 text-right text-sm">{fmtNumber(v)}</div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
