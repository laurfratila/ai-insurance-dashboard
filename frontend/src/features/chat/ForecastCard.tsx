import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

// Simple forecast chart using recharts (or fallback to table if recharts not installed)
// You can enhance this as needed for your data shape
export default function ForecastCard({ rows, summary, question }: { rows: any[]; summary?: string; question?: string }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="p-4 border rounded-xl bg-slate-50">
        <div className="font-semibold mb-2">Forecast</div>
        <div className="text-slate-400">No forecast data.</div>
      </div>
    );
  }


  // Get all unique keys from the first row
  const columns = Object.keys(rows[0]);

  // Prepare data for chart: x = month, y = retention_rate
  // Try to find the right column names
  const monthKey = columns.find((k) => k.toLowerCase().includes("month")) || columns[0];
  const retentionKey = columns.find((k) => k.toLowerCase().includes("retention")) || columns[columns.length-1];

  return (
    <div className="p-4 border rounded-xl bg-slate-50">
      <div className="font-semibold mb-2">Forecast</div>
      {question && <div className="text-xs text-slate-500 mb-2">{question}</div>}
      {/* Line chart for retention rate by month */}
      <div style={{ width: "100%", height: 220 }} className="mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={monthKey} tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={60} />
            <YAxis domain={[0, 1]} tickFormatter={(v) => (v * 100).toFixed(0) + "%"} />
            <Tooltip formatter={(v) => (typeof v === "number" ? (v * 100).toFixed(2) + "%" : v)} />
            <Line type="monotone" dataKey={retentionKey} stroke="#2563eb" strokeWidth={2} dot={true} name="Retention Rate" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="w-full text-sm mb-2">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} className="text-left font-medium">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {summary && <div className="text-xs text-slate-600 mt-2">{summary}</div>}
    </div>
  );
}
