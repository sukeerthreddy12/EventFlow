import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  cancelEvent,
  listMyEvents,
  publishEvent,
  softDeleteEvent,
  unpublishEvent,
  type OrganiserEvent,
} from "../../api/organiserEvents";
import { apiErrorMessage } from "../../api/errors";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function statusClass(status: OrganiserEvent["status"]) {
  if (status === "PUBLISHED") return "status-chip status-chip--ok";
  if (status === "CANCELLED") return "status-chip status-chip--cancelled";
  if (status === "DRAFT") return "status-chip status-chip--draft";
  return "status-chip";
}

export default function MyEvents() {
  const [events, setEvents] = useState<OrganiserEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function reload() {
    const data = await listMyEvents();
    setEvents(data);
  }

  useEffect(() => {
    let cancelled = false;
    listMyEvents()
      .then((data) => {
        if (!cancelled) setEvents(data);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load your events.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function runAction(
    id: string,
    action: () => Promise<unknown>,
    after?: () => void,
  ) {
    setError(null);
    setBusyId(id);
    try {
      await action();
      await reload();
      after?.();
    } catch (err) {
      setError(apiErrorMessage(err, "Action failed."));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <div className="org-header">
        <div>
          <h1 className="page-title">My events</h1>
          <p className="page-sub">Drafts, live listings, and cancellations.</p>
        </div>
        <Link to="/org/events/new" className="btn btn-primary">
          New event
        </Link>
      </div>

      {loading && <p className="state-msg">Loading…</p>}
      {error && <p className="state-msg state-msg--error">{error}</p>}
      {!loading && events.length === 0 && (
        <p className="state-msg">No events yet. Create your first one.</p>
      )}

      {!loading && events.length > 0 && (
        <ul className="reg-list">
          {events.map((event) => (
            <li key={event.id} className="reg-item">
              <div className="reg-item-main">
                <Link to={`/org/events/${event.id}`} className="reg-item-title">
                  {event.title}
                </Link>
                <div className="reg-item-meta">
                  <span>{formatWhen(event.starts_at)}</span>
                  <span>{event.venue}</span>
                  <span>
                    {Number(event.price) === 0 ? "Free" : `$${event.price}`}
                  </span>
                  <span>{event.max_capacity} cap</span>
                </div>
              </div>

              <div className="reg-item-actions">
                <span className={statusClass(event.status)}>{event.status}</span>
                <div className="org-actions">
                  {event.status === "DRAFT" && (
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={busyId === event.id}
                      onClick={() =>
                        runAction(event.id, () => publishEvent(event.id))
                      }
                    >
                      Publish
                    </button>
                  )}
                  {event.status === "PUBLISHED" && (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      disabled={busyId === event.id}
                      onClick={() =>
                        runAction(event.id, () => unpublishEvent(event.id))
                      }
                    >
                      Unpublish
                    </button>
                  )}
                  {event.status !== "CANCELLED" && (
                    <button
                      type="button"
                      className="btn btn-ghost"
                      disabled={busyId === event.id}
                      onClick={() => {
                        if (
                          confirm(
                            "Cancel this event? Active guests will be notified.",
                          )
                        ) {
                          runAction(event.id, () => cancelEvent(event.id));
                        }
                      }}
                    >
                      Cancel
                    </button>
                  )}
                  <Link
                    to={`/org/events/${event.id}/check-in`}
                    className="btn btn-ghost"
                  >
                    Check-in
                  </Link>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={busyId === event.id}
                    onClick={() => {
                      if (confirm("Soft-delete this event from your list?")) {
                        runAction(event.id, () => softDeleteEvent(event.id));
                      }
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}