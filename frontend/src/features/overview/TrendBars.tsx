import React from "react";
import { ResponsiveContainer, BarChart, Bar, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";

export default function TrendBars({
  title, data, isPercent=false, height=220
}: {
  title:string;
  data: { date:string; value:number }[];
  isPercent?: boolean;
  height?: number;
}) {
  const fmtM = (d:string)=> {
    const dt = new Date(d); return dt.toLocaleString("en-US",{month:"short"});
  };
  const tickFmt = (v:number)=> isPercent ? new Intl.NumberFormat("en-US",{style:"percent",maximumFractionDigits:0}).format(v) : v;

  const mapped = data.map(p=>({ ...p, M: fmtM(p.date) }));

  return (
    <div className="app-card" style={{ padding:16 }}>
      <div className="subtle" style={{ marginBottom:8 }}>{title}</div>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={mapped}>
            <CartesianGrid stroke="#eef2f7" vertical={false}/>
            <Tooltip
              formatter={(v:number)=>[ isPercent ? new Intl.NumberFormat("en-US",{style:"percent",maximumFractionDigits:1}).format(v) : v, "value" ]}
              labelFormatter={(l)=>l}
            />
            <XAxis dataKey="M" tickLine={false} axisLine={{ stroke:"var(--ring)" }} />
            <YAxis width={40} tickLine={false} axisLine={{ stroke:"var(--ring)" }} tickFormatter={tickFmt} />
            <Bar dataKey="value" radius={[6,6,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
