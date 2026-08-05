import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPublicEvents, type PublicEvent } from "../../api/events.ts";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function EventCatalog() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    listPublicEvents()
      .then((data) => {
        if (!cancelled) setEvents(data);
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
    <div>
      <h1 className="page-title">Events</h1>
      <p className="page-sub">Published nights worth showing up for.</p>

      {loading && <p className="state-msg">Loading…</p>}
      {error && <p className="state-msg state-msg--error">{error}</p>}
      {!loading && !error && events.length === 0 && (
        <p className="state-msg">No published events yet.</p>
      )}

      {!loading && !error && events.length > 0 && (
        <ul className="event-list">
          {events.map((event) => (
            <li key={event.id}>
              <Link to={`/app/events/${event.id}`} className="event-row">
                <div className="event-row-title">
                  <span>{event.title}</span>
                  <span className="event-price">
                    {Number(event.price) === 0 ? "Free" : `$${event.price}`}
                  </span>
                </div>
                <div className="event-row-meta">
                  <span>{formatWhen(event.starts_at)}</span>
                  <span>{event.venue}</span>
                  <span>{event.max_capacity} seats</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
