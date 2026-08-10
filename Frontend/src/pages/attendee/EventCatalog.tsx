import { useEffect, useState } from "react";
import EventShowcase from "../../components/events/EventShowcase";
import { listPublicEvents, type PublicEvent } from "../../api/events";

export default function EventCatalog() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    listPublicEvents()
      .then((data) => {
        if (cancelled) return;
        const featured = data.filter((e) => e.is_featured);
        const rest = data.filter((e) => !e.is_featured);
        setEvents([...featured, ...rest]);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Could not load events. Is the API running and CORS enabled?");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="catalog-page">
      <header className="catalog-head">
        <h1 className="page-title">Events</h1>
        <p className="page-sub">
          Published nights worth showing up for — capacity, waitlists, and tickets
          included.
        </p>
      </header>

      {loading && <p className="state-msg">Loading…</p>}
      {error && <p className="state-msg state-msg--error">{error}</p>}
      {!loading && !error && (
        <EventShowcase
          events={events}
          emptyMessage="No published events yet."
        />
      )}
    </div>
  );
}
