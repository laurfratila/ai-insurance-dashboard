import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BreakdownItem } from "@/features/common/types";

type DateRange = { start_date?: string; end_date?: string };

export function useClaimsByPeril(p: DateRange & { top_n?: number }) {
  const params = { ...p, top_n: p.top_n ?? 10 };
  return useQuery({
    queryKey: ["risk", "claims_by_peril", params],
    // NOTE: /api/risk/...
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/risk/claims_by_peril", { params })).data,
  });
}

export function useCatExposure(p: DateRange & { region?: string }) {
  return useQuery({
    queryKey: ["risk", "cat_exposure", p],
    // NOTE: /api/risk/...
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/risk/cat_exposure", { params: p })).data,
  });
}
