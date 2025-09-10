import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { fmtCurrency, fmtPct, fmtNumber } from "../lib/fmt";
import {
  useGwp,
  useLossRatio,
  useClaimsFrequency,
  useAvgSettlementDays,
} from "../features/overview/api";
import { KpiCard } from "../features/overview/KpiCard";
import TrendBars from "../features/overview/TrendBars";

// ----- Types & helpers -----
type Range = { start_date?: string; end_date?: string };

function startOfLastNMonths(n: number): string {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - (n - 1));
  return d.toISOString().slice(0, 10);
}
function startOfYear(): string {
  const d = new Date();
  d.setMonth(0, 1);
  return d.toISOString().slice(0, 10);
}

// ----- Route component -----
export default function Overview() {
  // Date range
  const [start, setStart] = useState<string>("");
  const [end, setEnd] = useState<string>("");

  const params: Range = useMemo(
    () => ({ start_date: start || undefined, end_date: end || undefined }),
    [start, end]
  );

  // Queries
  const gwp = useGwp(params);
  const lr = useLossRatio(params);
  const cf = useClaimsFrequency(params);
  const asd = useAvgSettlementDays(params);

  // Aggregations
  const totalGwp = useMemo(
    () => (gwp.data ?? []).reduce((a, p) => a + (p.value || 0), 0),
    [gwp.data]
  );

  const weighted = (pts?: { numerator: number; denominator: number }[]) => {
    const num = (pts ?? []).reduce((a, p) => a + (p.numerator || 0), 0);
    const den = (pts ?? []).reduce((a, p) => a + (p.denominator || 0), 0);
    return den > 0 ? num / den : 0;
  };

  const lossRatioVal = useMemo(() => weighted(lr.data), [lr.data]);
  const claimsFreqVal = useMemo(() => weighted(cf.data), [cf.data]);
  const avgDays = useMemo(() => {
    const arr = asd.data ?? [];
    return arr.length ? arr.reduce((a, p) => a + (p.value || 0), 0) / arr.length : 0;
  }, [asd.data]);

  // Series for charts
  const gwpSeries = (gwp.data ?? []).map((p) => ({ date: p.period, value: p.value }));
  const lrSeries = (lr.data ?? []).map((p) => ({ date: p.period, value: p.ratio }));
  const cfSeries = (cf.data ?? []).map((p) => ({ date: p.period, value: p.ratio }));
  const asdSeries = (asd.data ?? []).map((p) => ({ date: p.period, value: p.value }));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-[32px] font-black tracking-tight">Overview</h1>
        <span className="text-sm text-slate-500">{gwp.data?.length ?? 0} months • live</span>
      </div>

      {/* Filters / Quick ranges */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <Label htmlFor="start" className="text-xs text-slate-500">
              Start
            </Label>
            <Input
              id="start"
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="w-44"
            />
          </div>
          <div className="flex flex-col">
            <Label htmlFor="end" className="text-xs text-slate-500">
              End
            </Label>
            <Input
              id="end"
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="w-44"
            />
          </div>

          <div className="flex gap-2 ml-auto">
            <Button
              variant={start === startOfLastNMonths(3) && !end ? "secondary" : "outline"}
              onClick={() => {
                setStart(startOfLastNMonths(3));
                setEnd("");
              }}
              size="sm"
            >
              3m
            </Button>
            <Button
              variant={start === startOfLastNMonths(6) && !end ? "secondary" : "outline"}
              onClick={() => {
                setStart(startOfLastNMonths(6));
                setEnd("");
              }}
              size="sm"
            >
              6m
            </Button>
            <Button
              variant={start === startOfLastNMonths(12) && !end ? "secondary" : "outline"}
              onClick={() => {
                setStart(startOfLastNMonths(12));
                setEnd("");
              }}
              size="sm"
            >
              12m
            </Button>
            <Button
              variant={start === startOfYear() && !end ? "secondary" : "outline"}
              onClick={() => {
                setStart(startOfYear());
                setEnd("");
              }}
              size="sm"
            >
              YTD
            </Button>
            <Button variant="ghost" onClick={() => { setStart(""); setEnd(""); }} size="sm">
              Clear
            </Button>
          </div>
        </div>
      </Card>

      {/* KPI row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="GWP (sum of months)"
          valueDisplay={fmtCurrency(totalGwp)}
          series={gwpSeries}
          subtitle={`Points: ${gwp.data?.length ?? 0}`}
        />
        <KpiCard
          title="Loss Ratio (weighted)"
          valueDisplay={fmtPct(lossRatioVal)}
          series={lrSeries}
          subtitle={`Points: ${lr.data?.length ?? 0}`}
        />
        <KpiCard
          title="Claims Frequency (weighted)"
          valueDisplay={fmtPct(claimsFreqVal)}
          series={cfSeries}
          subtitle={`Points: ${cf.data?.length ?? 0}`}
        />
        <KpiCard
          title="Average Settlement Days"
          valueDisplay={fmtNumber(avgDays)}
          series={asdSeries}
          subtitle={`Points: ${asd.data?.length ?? 0}`}
        />
      </div>

      {/* Second row charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <TrendBars title="Claims Frequency — monthly" data={cfSeries} isPercent />
        <TrendBars title="Loss Ratio — monthly" data={lrSeries} isPercent />
      </div>
    </div>
  );
}
