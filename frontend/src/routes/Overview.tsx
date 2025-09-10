import { useMemo, useState } from "react";
import { fmtCurrency, fmtPct, fmtNumber } from "../lib/fmt";
import { useGwp, useLossRatio, useClaimsFrequency, useAvgSettlementDays } from "../features/overview/api";
import { KpiCard } from "../features/overview/KpiCard";
import TrendBars from "../features/overview/TrendBars";

type Range = { start_date?: string; end_date?: string };

function startOfLastNMonths(n:number){
  const d = new Date(); d.setDate(1); d.setMonth(d.getMonth()-(n-1));
  return d.toISOString().slice(0,10);
}

export default function Overview(){
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  const params:Range = useMemo(()=>({ start_date:start||undefined, end_date:end||undefined }),[start,end]);

  const gwp = useGwp(params);
  const lr  = useLossRatio(params);
  const cf  = useClaimsFrequency(params);
  const asd = useAvgSettlementDays(params);

  const totalGwp = useMemo(()=> (gwp.data??[]).reduce((a,p)=>a+(p.value||0),0), [gwp.data]);
  const weighted = (pts?:{numerator:number; denominator:number}[])=>{
    const num = (pts??[]).reduce((a,p)=>a+(p.numerator||0),0);
    const den = (pts??[]).reduce((a,p)=>a+(p.denominator||0),0);
    return den>0? num/den : 0;
  };

  const lossRatioVal = useMemo(()=>weighted(lr.data),[lr.data]);
  const claimsFreqVal = useMemo(()=>weighted(cf.data),[cf.data]);
  const avgDays = useMemo(()=>{
    const arr = asd.data ?? [];
    return arr.length ? arr.reduce((a,p)=>a+(p.value||0),0)/arr.length : 0;
  },[asd.data]);

  const gwpSeries = (gwp.data ?? []).map(p=>({ date:p.period, value:p.value }));
  const lrSeries  = (lr.data  ?? []).map(p=>({ date:p.period, value:p.ratio }));
  const cfSeries  = (cf.data  ?? []).map(p=>({ date:p.period, value:p.ratio }));
  const asdSeries = (asd.data ?? []).map(p=>({ date:p.period, value:p.value }));

  return (
    <div>
      <h1 className="h1">Overview</h1>

      {/* Filters */}
      <div style={{ marginBottom:16, display:"flex", gap:12, alignItems:"center", flexWrap:"wrap" }}>
        <label className="subtle">
          Start
          <input className="input" type="date" value={start} onChange={e=>setStart(e.target.value)} style={{ marginLeft:8 }}/>
        </label>
        <label className="subtle">
          End
          <input className="input" type="date" value={end} onChange={e=>setEnd(e.target.value)} style={{ marginLeft:8 }}/>
        </label>
        <button className="btn" onClick={()=>{ setStart(startOfLastNMonths(12)); setEnd(""); }}>Last 12 months</button>
        <button className="btn" onClick={()=>{ setStart(""); setEnd(""); }}>Clear</button>
        <span className="subtle" style={{ marginLeft:"auto" }}>{gwp.data?.length ?? 0} months • live</span>
      </div>

      {/* KPI row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4, minmax(0, 1fr))", gap:16 }}>
        <KpiCard title="GWP (sum of months)"           valueDisplay={fmtCurrency(totalGwp)} series={gwpSeries} subtitle={`Points: ${gwp.data?.length ?? 0}`} />
        <KpiCard title="Loss Ratio (weighted)"         valueDisplay={fmtPct(lossRatioVal)} series={lrSeries}    subtitle={`Points: ${lr.data?.length ?? 0}`} />
        <KpiCard title="Claims Frequency (weighted)"   valueDisplay={fmtPct(claimsFreqVal)} series={cfSeries}    subtitle={`Points: ${cf.data?.length ?? 0}`} />
        <KpiCard title="Average Settlement Days"       valueDisplay={fmtNumber(avgDays)}   series={asdSeries}   subtitle={`Points: ${asd.data?.length ?? 0}`} />
      </div>

      {/* Second row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(2, minmax(0, 1fr))", gap:16, marginTop:16 }}>
        <TrendBars title="Claims Frequency — monthly" data={cfSeries} isPercent />
        <TrendBars title="Loss Ratio — monthly"       data={lrSeries} isPercent />
      </div>
    </div>
  );
}
