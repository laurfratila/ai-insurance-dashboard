export type TimeSeriesPoint = { period: string; value: number | null };
export type BreakdownItem  = { key: string; value: number };
export type SLAItem = {
  period: string;
  breaches_gt_30d: number;
  breaches_gt_60d: number;
  still_open: number;
  total_reported: number;
};
