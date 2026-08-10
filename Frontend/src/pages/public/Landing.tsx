import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import LandingHeroScene from "../../components/landing/LandingHeroScene";
import EventShowcase from "../../components/events/EventShowcase";
import { listPublicEvents, type PublicEvent } from "../../api/events";

export default function Landing() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listPublicEvents()
      .then((data) => {
        if (cancelled) return;
        const featured = data.filter((e) => e.is_featured);
        const rest = data.filter((e) => !e.is_featured);
        setEvents([...featured, ...rest].slice(0, 6));
      })
      .catch(() => {
        if (!cancelled) setEvents([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="landing-page">
      <section className="landing">
        <LandingHeroScene />
        <div className="landing-veil" />

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

        <a href="#tonight" className="landing-scroll">
          Upcoming nights
        </a>
      </section>

      <section id="tonight" className="landing-events">
        <div className="landing-events__inner">
          <header className="landing-events__head">
            <h2>Tonight and beyond</h2>
            <p>Published events ready for registration — pick a door and claim a seat.</p>
          </header>

          {loading ? (
            <p className="state-msg">Loading nights…</p>
          ) : (
            <EventShowcase
              events={events}
              emptyMessage="No published events yet — organisers can publish from their dashboard."
            />
          )}

          <div className="landing-events__footer">
            <Link to="/app/events" className="btn btn-ghost">
              View full catalog
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
