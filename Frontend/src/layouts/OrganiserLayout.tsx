import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function OrganiserLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="layout layout-organiser">
      <header className="topbar">
        <Link to="/org/events" className="brand">
          EventFlow
        </Link>
        <nav className="topbar-nav">
          <Link to="/org/events">My events</Link>
          <Link to="/org/analytics">Analytics</Link>
          <Link to="/org/events/new">New event</Link>
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
        </nav>
      </header>
      <main className="layout-main layout-main--padded">
        <Outlet />
      </main>
    </div>
  );
}