import { api } from "./client";

export type PublicEvent = {
  id: string;
  title: string;
  description: string;
  venue: string;
  starts_at: string;
  ends_at: string;
  max_capacity: number;
  price: string;
  status: string;
  is_featured: boolean;
};

export async function listPublicEvents(): Promise<PublicEvent[]> {
  const { data } = await api.get<PublicEvent[] | { results: PublicEvent[] }>(
    "/events/public/",
  );
  return Array.isArray(data) ? data : data.results;
}

export async function getPublicEvent(id: string): Promise<PublicEvent> {
  const { data } = await api.get<PublicEvent>(`/events/public/${id}/`);
  return data;
}

