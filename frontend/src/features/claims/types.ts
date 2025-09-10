export type TwoSeriesPoint = { period: string; a: number; b: number };
export type BreakdownItem = { key: string; value: number };
export type RatioSeriesPoint = {
  period: string;
  numerator: number;
  denominator: number;
  ratio: number | null;
};
