import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function AttendeeLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="layout layout-attendee">
      <header className="topbar">
        <Link to="/app/events" className="brand">
          EventFlow
        </Link>
        <nav className="topbar-nav">
          <Link to="/app/events">Events</Link>
          <Link to="/app/my-registrations">My registrations</Link>
          {user ? (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Sign out
            </button>
          ) : (
            <Link to="/login">Sign in</Link>
          )}
        </nav>
      </header>
      <main className="layout-main layout-main--padded">
        <Outlet />
      </main>
    </div>
  );
}
