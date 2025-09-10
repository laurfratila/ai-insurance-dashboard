import React, { useMemo, useId } from "react";
import { ResponsiveContainer, AreaChart, Area, Tooltip, YAxis } from "recharts";

type Point = { date:string; value:number };

export function KpiCard({
  title, valueDisplay, series, subtitle
}: {
  title:string;
  valueDisplay:string;
  series: Point[];
  subtitle?: string;
}) {
  const last = series.at(-1)?.value ?? 0;
  const prev = series.at(-2)?.value ?? 0;
  const delta = prev !== 0 ? (last - prev) / Math.abs(prev) : 0;
  const deltaPct = new Intl.NumberFormat("en-US", { style:"percent", maximumFractionDigits:1 }).format(delta);
  const up = delta >= 0;

  const gradId = useId();
  const tidy = useMemo(()=>series.map(p => ({...p, M:p.date.slice(0,7)})), [series]);

  // Soft min/max so the line isn't glued to edges
  const [min,max] = useMemo(()=>{
    const vals = tidy.map(t=>t.value);
    if(!vals.length) return [0,1];
    const vmin = Math.min(...vals), vmax = Math.max(...vals);
    const pad = (vmax-vmin||1)*0.15;
    return [vmin-pad, vmax+pad];
  },[tidy]);

  return (
    <div className="app-card" style={{ padding:16 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
        <div className="subtle">{title}</div>
        {series.length>1 && (
          <div style={{
            fontSize:12, fontWeight:700,
            color: up ? "#166534" : "#991b1b",
            background: up ? "rgba(22,163,74,.10)" : "rgba(153,27,27,.10)",
            border:"1px solid var(--ring)", padding:"2px 8px", borderRadius:999
          }}>
            {up ? "▲" : "▼"} {deltaPct}
          </div>
        )}
      </div>

      <div style={{ display:"flex", alignItems:"baseline", gap:12 }}>
        <div style={{ fontSize:32, fontWeight:800 }}>{valueDisplay}</div>
      </div>
      {subtitle && <div className="subtle" style={{ marginTop:6 }}>{subtitle}</div>}

      <div style={{ height:56, marginTop:12 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={tidy}>
            <defs>
              <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#0f172a" stopOpacity={0.3}/>
                <stop offset="100%" stopColor="#0f172a" stopOpacity={0.03}/>
              </linearGradient>
            </defs>
            <YAxis hide domain={[min,max]} />
            <Tooltip formatter={(v:number)=>[v,"value"]} labelFormatter={(l)=>l}/>
            <Area type="monotone" dataKey="value" stroke="#0f172a" strokeWidth={2} fill={`url(#${gradId})`} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
