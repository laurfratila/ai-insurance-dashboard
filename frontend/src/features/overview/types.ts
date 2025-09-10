export type TimeSeriesPoint = {
  period: string;
  value: number;
};

export type RatioSeriesPoint = {
  period: string;
  numerator: number;
  denominator: number;
  ratio: number; // 0..1
};
