import { Link, Outlet } from "react-router-dom";

export default function PublicLayout() {
  return (
    <div className="layout layout-public">
      <header className="topbar">
        <Link to="/" className="brand">
          EventFlow
        </Link>
        <nav className="topbar-nav">
          <Link to="/login">Sign in</Link>
          <Link to="/register">Register</Link>
        </nav>
      </header>
      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  );
}
