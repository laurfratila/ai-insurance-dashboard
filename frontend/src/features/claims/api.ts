import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TwoSeriesPoint, BreakdownItem, RatioSeriesPoint } from "./types";

type Range = { start_date?: string; end_date?: string };

export const usePaidVsReserve = (p: Range) =>
  useQuery({
    queryKey: ["claims", "paid_vs_reserve", p],
    queryFn: async () =>
      (await api.get<TwoSeriesPoint[]>("/api/claims/paid_vs_reserve", { params: p })).data,
  });

export const useSeverityHistogram = () =>
  useQuery({
    queryKey: ["claims", "severity_histogram"],
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/claims/severity_histogram")).data,
  });

export const useOpenVsClosedRatio = (p: Range) =>
  useQuery({
    queryKey: ["claims", "open_vs_closed_ratio", p],
    queryFn: async () =>
      (await api.get<RatioSeriesPoint[]>("/api/claims/open_vs_closed_ratio", { params: p })).data,
  });
