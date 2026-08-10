import { api } from "./client";

export type OrganiserEvent = {
  id: string;
  title: string;
  description: string;
  venue: string;
  starts_at: string;
  ends_at: string;
  max_capacity: number;
  price: string;
  status: "DRAFT" | "PUBLISHED" | "ONGOING" | "COMPLETED" | "CANCELLED";
  refund_eligible: boolean;
  is_featured: boolean;
  is_suppressed: boolean;
  organiser: string;
  created_at: string;
  updated_at: string;
};

export type EventWritePayload = {
  title: string;
  description: string;
  venue: string;
  starts_at: string; // ISO
  ends_at: string;
  max_capacity: number;
  price: string;
};

export async function listMyEvents() {
  const { data } = await api.get<OrganiserEvent[] | { results: OrganiserEvent[] }>(
    "/events/",
  );
  return Array.isArray(data) ? data : data.results;
}

export async function getMyEvent(id: string) {
  const { data } = await api.get<OrganiserEvent>(`/events/${id}/`);
  return data;
}

export async function createEvent(payload: EventWritePayload) {
  const { data } = await api.post<OrganiserEvent>("/events/", payload);
  return data;
}

export async function updateEvent(id: string, payload: EventWritePayload) {
  const { data } = await api.patch<OrganiserEvent>(`/events/${id}/`, payload);
  return data;
}

export async function softDeleteEvent(id: string) {
  await api.delete(`/events/${id}/`);
}

export async function publishEvent(id: string) {
  const { data } = await api.post<OrganiserEvent>(`/events/${id}/publish/`);
  return data;
}

export async function unpublishEvent(id: string) {
  const { data } = await api.post<OrganiserEvent>(`/events/${id}/unpublish/`);
  return data;
}

export async function cancelEvent(id: string) {
  const { data } = await api.post<OrganiserEvent>(`/events/${id}/cancel/`);
  return data;
}