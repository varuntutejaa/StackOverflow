"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, qs } from "./api";
import type {
  AppConfig,
  Application,
  Beneficiary,
  Interview,
  MapResponse,
  Notification,
  NsqfRole,
  Outcome,
  OutcomeDashboard,
  Overview,
  Paginated,
  Recommendation,
  Skill,
  TrainingProgram,
  UserPublic,
} from "./types";

export interface ListParams {
  page?: number;
  page_size?: number;
  sort?: string;
  q?: string;
  [k: string]: unknown;
}

/* ---------- meta ---------- */
export const useConfig = () =>
  useQuery({ queryKey: ["config"], queryFn: () => apiFetch<AppConfig>("/meta/config", { auth: false }), staleTime: 300_000 });

export const useHealth = () =>
  useQuery({ queryKey: ["health"], queryFn: () => apiFetch<any>("/health", { auth: false }), refetchInterval: 30_000 });

export const useDemoPointer = () =>
  useQuery({ queryKey: ["demo"], queryFn: () => apiFetch<{ has_demo: boolean; beneficiary_id: string | null; name: string | null }>("/meta/demo", { auth: false }) });

/* ---------- analytics ---------- */
export const useOverview = () =>
  useQuery({ queryKey: ["overview"], queryFn: () => apiFetch<Overview>("/analytics/overview"), refetchInterval: 60_000 });

export const useOutcomeDashboard = () =>
  useQuery({ queryKey: ["outcome-dashboard"], queryFn: () => apiFetch<OutcomeDashboard>("/analytics/outcomes") });

export const useLivelihoodMap = () =>
  useQuery({ queryKey: ["map"], queryFn: () => apiFetch<MapResponse>("/map/livelihood") });

/* ---------- beneficiaries ---------- */
export const useBeneficiaries = (params: ListParams) =>
  useQuery({
    queryKey: ["beneficiaries", params],
    queryFn: () => apiFetch<Paginated<Beneficiary>>(`/beneficiaries${qs(params)}`),
  });

export const useBeneficiary = (id?: string) =>
  useQuery({ queryKey: ["beneficiary", id], queryFn: () => apiFetch<Beneficiary>(`/beneficiaries/${id}`), enabled: !!id });

export const useCreateBeneficiary = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Beneficiary>) => apiFetch<Beneficiary>("/beneficiaries", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["beneficiaries"] }),
  });
};

export const useUpdateBeneficiary = (id: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Beneficiary>) => apiFetch<Beneficiary>(`/beneficiaries/${id}`, { method: "PATCH", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["beneficiary", id] });
      qc.invalidateQueries({ queryKey: ["beneficiaries"] });
    },
  });
};

export const useArchiveBeneficiary = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/beneficiaries/${id}/archive`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["beneficiaries"] }),
  });
};

/* ---------- locations ---------- */
export const useDistricts = (state?: string) =>
  useQuery({ queryKey: ["districts", state], queryFn: () => apiFetch<string[]>(`/locations/districts${qs({ state })}`) });
export const useLocations = () =>
  useQuery({ queryKey: ["locations"], queryFn: () => apiFetch<Paginated<any>>("/locations?page_size=200") });

/* ---------- skills / nsqf ---------- */
export const useSkills = (params: ListParams = {}) =>
  useQuery({ queryKey: ["skills", params], queryFn: () => apiFetch<Paginated<Skill>>(`/skills${qs({ page_size: 200, ...params })}`) });
export const useSectors = () =>
  useQuery({ queryKey: ["sectors"], queryFn: () => apiFetch<string[]>("/skills/sectors") });
export const useRoles = (params: ListParams = {}) =>
  useQuery({ queryKey: ["nsqf-roles", params], queryFn: () => apiFetch<Paginated<NsqfRole>>(`/nsqf-roles${qs({ page_size: 100, ...params })}`) });

/* ---------- training ---------- */
export const usePrograms = (params: ListParams = {}) =>
  useQuery({ queryKey: ["programs", params], queryFn: () => apiFetch<Paginated<TrainingProgram>>(`/training-programs${qs({ page_size: 100, ...params })}`) });
export const useProviders = (params: ListParams = {}) =>
  useQuery({ queryKey: ["providers", params], queryFn: () => apiFetch<Paginated<any>>(`/training-providers${qs({ page_size: 100, ...params })}`) });

/* ---------- interviews ---------- */
export const useInterviews = (params: ListParams = {}) =>
  useQuery({ queryKey: ["interviews", params], queryFn: () => apiFetch<Paginated<Interview>>(`/interviews${qs(params)}`) });
export const useInterview = (id?: string) =>
  useQuery({ queryKey: ["interview", id], queryFn: () => apiFetch<Interview>(`/interviews/${id}`), enabled: !!id });

export const useCreateInterview = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { beneficiary_id: string; language: string; channel?: string }) =>
      apiFetch<Interview>("/interviews", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interviews"] }),
  });
};

export const useSubmitTurn = (interviewId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { text?: string; text_english?: string; audio_base64?: string; language?: string }) =>
      apiFetch<any>(`/interviews/${interviewId}/turn`, { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interview", interviewId] }),
  });
};

/* ---------- recommendations ---------- */
export const useRecommendations = (beneficiaryId?: string) =>
  useQuery({
    queryKey: ["recommendations", beneficiaryId],
    queryFn: () => apiFetch<Paginated<Recommendation>>(`/recommendations${qs({ beneficiary_id: beneficiaryId, sort: "rank", page_size: 20 })}`),
    enabled: !!beneficiaryId,
  });

export const useRecommendationWeights = () =>
  useQuery({ queryKey: ["reco-weights"], queryFn: () => apiFetch<{ weights: Record<string, number>; description: Record<string, string> }>("/recommendations/weights") });

export const useGenerateRecommendations = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { beneficiary_id: string; top_n?: number; persist?: boolean; weights_override?: Record<string, number> }) =>
      apiFetch<any>("/recommendations/generate", { method: "POST", body }),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ["recommendations", v.beneficiary_id] });
      qc.invalidateQueries({ queryKey: ["beneficiary", v.beneficiary_id] });
    },
  });
};

/* ---------- applications ---------- */
export const useApplications = (params: ListParams = {}) =>
  useQuery({ queryKey: ["applications", params], queryFn: () => apiFetch<Paginated<Application>>(`/applications${qs(params)}`) });

export const useCreateApplication = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { beneficiary_id: string; program_id: string; recommendation_id?: string }) =>
      apiFetch<Application>("/applications", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });
};

export const useUpdateApplication = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      apiFetch<Application>(`/applications/${id}`, { method: "PATCH", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });
};

export const useApplicationAction = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action, body }: { id: string; action: "enroll" | "certificate"; body?: Record<string, unknown> }) =>
      apiFetch<Application>(`/applications/${id}/${action}`, { method: "POST", body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["overview"] });
    },
  });
};

/* ---------- outcomes ---------- */
export const useOutcomes = (params: ListParams = {}) =>
  useQuery({ queryKey: ["outcomes", params], queryFn: () => apiFetch<Paginated<Outcome>>(`/outcomes${qs(params)}`) });

/* ---------- opportunities ---------- */
export const useOpportunities = (params: ListParams = {}) =>
  useQuery({ queryKey: ["opportunities", params], queryFn: () => apiFetch<Paginated<any>>(`/opportunities${qs({ page_size: 100, ...params })}`) });

/* ---------- notifications ---------- */
export const useNotifications = (params: ListParams = {}) =>
  useQuery({ queryKey: ["notifications", params], queryFn: () => apiFetch<Paginated<Notification>>(`/notifications${qs(params)}`), refetchInterval: 45_000 });

export const useUnreadCount = () =>
  useQuery({ queryKey: ["unread"], queryFn: () => apiFetch<{ unread: number }>("/notifications/unread-count"), refetchInterval: 45_000 });

export const useMarkNotificationRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/notifications/${id}/read`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["unread"] });
    },
  });
};

export const useMarkAllRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch("/notifications/read-all", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["unread"] });
    },
  });
};

/* ---------- users / audit ---------- */
export const useUsers = (params: ListParams = {}) =>
  useQuery({ queryKey: ["users", params], queryFn: () => apiFetch<Paginated<UserPublic & { created_at: string }>>(`/users${qs(params)}`) });

export const useCreateUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => apiFetch("/users", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
};

export const useUpdateUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      apiFetch(`/users/${id}`, { method: "PATCH", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
};

export const useAuditLogs = (params: ListParams = {}) =>
  useQuery({ queryKey: ["audit", params], queryFn: () => apiFetch<Paginated<any>>(`/audit-logs${qs(params)}`) });
