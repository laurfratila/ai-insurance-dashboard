import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { TimeSeriesPoint, BreakdownItem, DemographicItem } from "./types";

type Range = { start_date?: string; end_date?: string };

export const useRetention = (p: Range) =>
  useQuery({
    queryKey: ["c360", "retention", p],
    queryFn: async () =>
      (await api.get<TimeSeriesPoint[]>("/api/c360/retention", { params: p })).data,
  });

export const useCrossSell = () =>
  useQuery({
    queryKey: ["c360", "cross_sell_distribution"],
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/c360/cross_sell_distribution")).data,
  });

export const useChannelMix = (p: Range) =>
  useQuery({
    queryKey: ["c360", "channel_mix", p],
    queryFn: async () =>
      (await api.get<BreakdownItem[]>("/api/c360/channel_mix", { params: p })).data,
  });

export const useDemographics = () =>
  useQuery({
    queryKey: ["c360", "demographics"],
    queryFn: async () =>
      (await api.get<DemographicItem[]>("/api/c360/demographics")).data,
  });
