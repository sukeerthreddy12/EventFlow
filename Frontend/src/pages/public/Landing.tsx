import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <section className="landing">
      <div className="landing-inner">
        <h1 className="landing-brand">EventFlow</h1>
        <p className="landing-line">
          Capacity-aware events. Tickets, waitlists, and doors that know you.
        </p>
        <div className="landing-ctas">
          <Link to="/app/events" className="btn btn-primary">
            Browse events
          </Link>
          <Link to="/login" className="btn btn-ghost">
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}
