import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listConsultations,
  createConsultation,
  searchConsultations,
  getConsultation,
  getClinicalRepresentation,
  type ConsultationSummary,
  type ClinicalRepresentationResponse,
} from "@/lib/api";

// Query Keys
export const consultationKeys = {
  all: ["consultations"] as const,
  lists: () => [...consultationKeys.all, "list"] as const,
  list: () => [...consultationKeys.lists()] as const,
  searches: () => [...consultationKeys.all, "search"] as const,
  search: (query: string) => [...consultationKeys.searches(), query] as const,
  details: () => [...consultationKeys.all, "detail"] as const,
  detail: (id: string) => [...consultationKeys.details(), id] as const,
  representation: (id: string) => [...consultationKeys.details(), id, "representation"] as const,
};

// Hooks
export function useConsultations() {
  return useQuery({
    queryKey: consultationKeys.list(),
    queryFn: async () => {
      const res = await listConsultations();
      if (!res.ok) throw new Error(res.error.message);
      return res.data.items;
    },
  });
}

export function useSearchConsultations(query: string) {
  return useQuery({
    queryKey: consultationKeys.search(query),
    queryFn: async () => {
      const res = await searchConsultations(query);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    enabled: query.trim().length >= 3,
  });
}

export function useCreateConsultation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const res = await createConsultation();
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consultationKeys.lists() });
    },
  });
}

export function useConsultationDetail(id: string) {
  return useQuery({
    queryKey: consultationKeys.detail(id),
    queryFn: async () => {
      const res = await getConsultation(id);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useClinicalRepresentation(id: string) {
  return useQuery({
    queryKey: consultationKeys.representation(id),
    queryFn: async () => {
      const res = await getClinicalRepresentation(id);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    enabled: !!id,
  });
}

import { getClinicalNote, updateClinicalNote, type ClinicalNoteUpdate } from "@/lib/api";

export const noteKeys = {
  all: ["notes"] as const,
  details: () => [...noteKeys.all, "detail"] as const,
  detail: (id: string) => [...noteKeys.details(), id] as const,
};

export function useClinicalNote(consultationId: string) {
  return useQuery({
    queryKey: noteKeys.detail(consultationId),
    queryFn: async () => {
      const res = await getClinicalNote(consultationId);
      if (!res.ok) throw new Error(res.error.message);
      return res.data;
    },
    enabled: !!consultationId,
  });
}

export function useUpdateClinicalNote(consultationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ClinicalNoteUpdate) => {
      const res = await updateClinicalNote(consultationId, payload);
      if (!res.ok) {
        if (res.error?.code === "OPTIMISTIC_CONCURRENCY_ERROR") {
          throw new Error("Conflict: The note was modified elsewhere. Please refresh.");
        }
        throw new Error(res.error.message || "Failed to save note.");
      }
      return res.data;
    },
    onSuccess: (data) => {
      // Optimistically update the cache with the newly saved note version
      queryClient.setQueryData(noteKeys.detail(consultationId), data);
    },
  });
}
