import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TimeSeriesPoint, BreakdownItem, SLAItem } from "@/features/common/types";

type DateRange = { start_date?: string; end_date?: string };

export function useFnol(p: DateRange) {
  return useQuery({
    queryKey: ["ops", "fnol", p],
    // NOTE: /api/ops/...
    queryFn: async () =>
      (await api.get<TimeSeriesPoint[]>("/api/ops/fnol", { params: p })).data,
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
  });
}

export function useSlaBreaches(p: DateRange) {
  return useQuery({
    queryKey: ["ops", "sla_breaches", p],
    // NOTE: /api/ops/...
    queryFn: async () =>
      (await api.get<SLAItem[]>("/api/ops/sla_breaches", { params: p })).data,
  });
}

export function useBacklogByAgeBucket(as_of?: string) {
  const params = { as_of: as_of || undefined };
  return useQuery({
    queryKey: ["ops", "backlog_by_age_bucket", params],
    // NOTE: /api/ops/...
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/ops/backlog_by_age_bucket", { params })).data,
  });
}
