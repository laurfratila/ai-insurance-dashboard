import { api } from "../../lib/api";
import { useQuery } from "@tanstack/react-query";
import type { TimeSeriesPoint, RatioSeriesPoint } from "./types";

export async function fetchGwp(params?: { start_date?: string; end_date?: string }) {
  const res = await api.get<TimeSeriesPoint[]>("/api/overview/gwp", { params });
  return res.data;
}
export async function fetchLossRatio(params?: { start_date?: string; end_date?: string }) {
  const res = await api.get<RatioSeriesPoint[]>("/api/overview/loss_ratio", { params });
  return res.data;
}
export async function fetchClaimsFrequency(params?: { start_date?: string; end_date?: string }) {
  const res = await api.get<RatioSeriesPoint[]>("/api/overview/claims_frequency", { params });
  return res.data;
}
export async function fetchAvgSettlementDays(params?: { start_date?: string; end_date?: string }) {
  const res = await api.get<TimeSeriesPoint[]>("/api/overview/avg_settlement_days", { params });
  return res.data;
}

export const useGwp = (params?: { start_date?: string; end_date?: string }) =>
  useQuery({ queryKey: ["gwp", params], queryFn: () => fetchGwp(params) });

export const useLossRatio = (params?: { start_date?: string; end_date?: string }) =>
  useQuery({ queryKey: ["loss_ratio", params], queryFn: () => fetchLossRatio(params) });

export const useClaimsFrequency = (params?: { start_date?: string; end_date?: string }) =>
  useQuery({ queryKey: ["claims_frequency", params], queryFn: () => fetchClaimsFrequency(params) });

export const useAvgSettlementDays = (params?: { start_date?: string; end_date?: string }) =>
  useQuery({ queryKey: ["avg_settlement_days", params], queryFn: () => fetchAvgSettlementDays(params) });
