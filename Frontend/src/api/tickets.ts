import { api } from "./client";

export type Ticket = {
  id: string;
  registration: string;
  token: string;
  status: "CONFIRMED" | "CANCELLED" | "USED";
  checked_in_at: string | null;
  created_at: string;
  updated_at: string;
};

export async function getTicketByRegistration(registrationId: string) {
  const { data } = await api.get<Ticket>(
    `/tickets/by-registration/${registrationId}/`,
  );
  return data;
}


export async function checkInTicket(token: string) {
    const { data } = await api.post<Ticket>("/tickets/check-in/", { token });
    return data;
  }