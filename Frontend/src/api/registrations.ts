import { api } from "./client";

export type Registration = {
  id: string;
  user: string;
  event: string;
  status: "CONFIRMED" | "WAITLISTED" | "CANCELLED";
  created_at: string;
  updated_at: string;
};

export async function createRegistration(eventId: string) {
  const { data } = await api.post<Registration>("/registrations/", {
    event_id: eventId,
  });
  return data;
}


export type TeamRegistrationResult = {
    id: string;
    group_token: string;
    event: string;
    lead: string;
    member_count: number;
    status: "CONFIRMED" | "WAITLISTED" | "CANCELLED";
    registrations: Registration[];
  };
  
  export async function createTeamRegistration(
    eventId: string,
    memberEmails: string[],
  ) {
    const { data } = await api.post<TeamRegistrationResult>(
      "/registrations/team/",
      {
        event_id: eventId,
        member_emails: memberEmails,
      },
    );
    return data;
  }

  export async function listMyRegistrations() {
    const { data } = await api.get<Registration[]>("/registrations/");
    return data;
  }
  
  export async function cancelRegistration(id: string) {
    const { data } = await api.post<Registration>(
      `/registrations/${id}/cancel/`,
    );
    return data;
  }

