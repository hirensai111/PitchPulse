import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type {
  PredictResponse,
  Venue,
  TrackRecordResponse,
  EventImportanceResponse,
  ModelCardResponse,
} from "@/types/api";

export function useTeams() {
  return useQuery<string[]>({
    queryKey: ["teams"],
    queryFn: async () => {
      const res = await apiClient.get<string[]>("/api/teams");
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useVenues() {
  return useQuery<Venue[]>({
    queryKey: ["venues"],
    queryFn: async () => {
      const res = await apiClient.get<Venue[]>("/api/venues");
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function usePredict(
  team1: string,
  team2: string,
  venue: string,
  matchDate: string
) {
  return useQuery<PredictResponse>({
    queryKey: ["predict", team1, team2, venue, matchDate],
    queryFn: async () => {
      const res = await apiClient.post<PredictResponse>("/api/predict", {
        team1,
        team2,
        venue,
        match_date: matchDate,
      });
      return res.data;
    },
    enabled: !!team1 && !!team2 && !!venue && !!matchDate && team1 !== team2,
  });
}

export function useTrackRecord() {
  return useQuery<TrackRecordResponse>({
    queryKey: ["track-record"],
    queryFn: async () => {
      const res = await apiClient.get<TrackRecordResponse>("/api/track-record");
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useEventImportance(eventId: string) {
  return useQuery<EventImportanceResponse>({
    queryKey: ["event-importance", eventId],
    queryFn: async () => {
      const res = await apiClient.get<EventImportanceResponse>(
        `/api/event-importance/${eventId}`
      );
      return res.data;
    },
    enabled: !!eventId,
    staleTime: 60 * 60 * 1000,
  });
}

export function useModelCard() {
  return useQuery<ModelCardResponse>({
    queryKey: ["model-card"],
    queryFn: async () => {
      const res = await apiClient.get<ModelCardResponse>("/api/model-card");
      return res.data;
    },
    staleTime: 60 * 60 * 1000,
  });
}
