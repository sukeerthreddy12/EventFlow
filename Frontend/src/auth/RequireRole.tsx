import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { User } from "../api/accounts";

export default function RequireRole({ roles }: { roles: User["role"][] }) {
  const { user, loading } = useAuth();

  if (loading) return <p className="state-msg">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) {
    const fallback = user.role === "ORGANISER" ? "/org/events" : "/app/events";
    return <Navigate to={fallback} replace />;
  }
  return <Outlet />;
}
