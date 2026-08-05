import { api } from "./client";

export type User = {
  id: string;
  username: string;
  email: string;
  role: "ADMIN" | "ORGANISER" | "ATTENDEE";
  is_verified: boolean;
};

export type AuthTokens = {
  access: string;
  refresh: string;
};

export async function register(payload: {
  username: string;
  email: string;
  password: string;
  role: "ATTENDEE" | "ORGANISER";
}) {
  const { data } = await api.post("/accounts/register/", payload);
  return data;
}

export async function verifyEmail(token: string) {
  const { data } = await api.post<{ message: string }>(
    "/accounts/verify-email/",
    { token },
  );
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post<AuthTokens>("/accounts/login/", {
    email,
    password,
  });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get<User>("/accounts/me/");
  return data;
}

export async function requestPasswordReset(email: string) {
  const { data } = await api.post<{ message: string }>(
    "/accounts/password-reset/",
    { email },
  );
  return data;
}

export async function confirmPasswordReset(payload: {
  token: string;
  new_password: string;
  new_password_confirm: string;
}) {
  const { data } = await api.post<{ message: string }>(
    "/accounts/password-reset-confirm/",
    payload,
  );
  return data;
}
