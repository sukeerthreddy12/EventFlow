import { api } from "./client";

export type EventAnalytics = {
  event_id: string;
  title: string;
  status: string;
  starts_at: string;
  max_capacity: number;
  confirmed_count: number;
  waitlisted_count: number;
  checked_in_count: number;
  check_in_rate: number;
  revenue: string;
};

export type OrganiserAnalyticsSummary = {
  event_count: number;
  total_confirmed: number;
  total_waitlisted: number;
  total_checked_in: number;
  overall_check_in_rate: number;
  total_revenue: string;
  events: EventAnalytics[];
};

export async function getOrganiserAnalyticsSummary() {
  const { data } = await api.get<OrganiserAnalyticsSummary>(
    "/analytics/organiser/summary/",
  );
  return data;
}