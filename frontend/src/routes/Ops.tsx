import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFnol, useSlaBreaches, useBacklogByAgeBucket } from "@/features/ops/api";
import { fmtNumber, fmtPct } from "@/lib/fmt";

function Spark({ values }: { values: number[] }) {
  if (!values?.length) return null;
  const min = Math.min(...values), max = Math.max(...values);
  const w=220,h=48,step=w/(values.length-1||1);
  const toY=(v:number)=> h-((v-min)/(max-min||1))*h;
  const d=values.map((v,i)=>`${i?"L":"M"} ${i*step},${toY(v)}`).join(" ");
  return <svg width={w} height={h} className="text-slate-800"><path d={d} fill="none" stroke="currentColor" strokeWidth={2}/></svg>;
}

function HBar({ pct }: { pct:number }) {
  return (
    <div className="h-2 bg-slate-200/70 rounded w-full overflow-hidden">
      <div className="h-2 bg-slate-900 rounded" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
    </div>
  );
}

export default function Ops() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [asOf, setAsOf] = useState("");

  const p = useMemo(()=>({ start_date: start || undefined, end_date: end || undefined }), [start,end]);

  const fnol = useFnol(p);
  const sla  = useSlaBreaches(p);
  const backlog = useBacklogByAgeBucket(asOf || undefined);

  const fnolVals = (fnol.data ?? []).map(p => Number(p.value) || 0);

  const latestSla = (sla.data ?? []).at(-1);
  const breach30 = latestSla?.breaches_gt_30d ?? 0;
  const breach60 = latestSla?.breaches_gt_60d ?? 0;
  const stillOpen = latestSla?.still_open ?? 0;
  const totalRep  = latestSla?.total_reported ?? 1;

  const backlogMax = Math.max(1, ...(backlog.data ?? []).map(b => Number(b.value) || 0));

  return (
    <div className="space-y-4">
      <h1 className="text-[32px] font-black tracking-tight">Operations</h1>

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
            <Label className="text-xs text-slate-500">Backlog as of (optional)</Label>
            <Input type="date" value={asOf} onChange={e=>setAsOf(e.target.value)} className="w-44" />
          </div>
          <div className="ml-auto">
            <Button variant="ghost" onClick={()=>{ setStart(""); setEnd(""); setAsOf(""); }}>Clear</Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-sm text-slate-500">FNOL (First Notice of Loss)</div>
          <div className="text-3xl font-black">{fmtNumber(fnolVals.at(-1) ?? 0)}</div>
          <div className="mt-2"><Spark values={fnolVals} /></div>
          <div className="text-xs text-slate-500 mt-1">Points: {fnol.data?.length ?? 0}</div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-slate-500">SLA breaches (latest month)</div>
          <div className="space-y-1 mt-2 text-sm">
            <div className="flex justify-between"><span>≥30 days</span><span>{fmtNumber(breach30)}</span></div>
            <div className="flex justify-between"><span>≥60 days</span><span>{fmtNumber(breach60)}</span></div>
            <div className="flex justify-between"><span>Still open</span><span>{fmtNumber(stillOpen)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Total reported</span><span>{fmtNumber(totalRep)}</span></div>
            <div className="pt-1 text-slate-600">Breach rate: <b>{fmtPct((breach30+breach60+stillOpen)/(totalRep||1))}</b></div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="text-sm text-slate-500">Backlog — open by region (snapshot)</div>
          <div className="space-y-2 mt-2">
            {(backlog.data ?? []).map(b => {
              const v = Number(b.value) || 0;
              const pct = (v / backlogMax) * 100;
              return (
                <div key={b.key} className="flex items-center gap-3">
                  <div className="w-24 font-medium">{b.key}</div>
                  <HBar pct={pct} />
                  <div className="w-24 text-right text-sm">{fmtNumber(v)}</div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
