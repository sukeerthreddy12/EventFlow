import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPublicEvent, type PublicEvent } from "../../api/events";
import {
  cancelRegistration,
  listMyRegistrations,
  type Registration,
} from "../../api/registrations";
import { apiErrorMessage } from "../../api/errors";

type Row = Registration & { eventDetail?: PublicEvent | null };

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function statusClass(status: Registration["status"]) {
  if (status === "CONFIRMED") return "status-chip status-chip--ok";
  if (status === "WAITLISTED") return "status-chip status-chip--wait";
  return "status-chip";
}

export default function MyRegistrations() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const regs = await listMyRegistrations();
        const enriched = await Promise.all(
          regs.map(async (reg) => {
            try {
              const eventDetail = await getPublicEvent(reg.event);
              return { ...reg, eventDetail };
            } catch {
              // cancelled/suppressed events may 404 on public API
              return { ...reg, eventDetail: null };
            }
          }),
        );
        if (!cancelled) setRows(enriched);
      } catch {
        if (!cancelled) setError("Could not load registrations.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onCancel(id: string) {
    setError(null);
    setCancellingId(id);
    try {
      const updated = await cancelRegistration(id);
      setRows((prev) =>
        prev.map((r) => (r.id === id ? { ...r, ...updated } : r)),
      );
    } catch (err) {
      setError(apiErrorMessage(err, "Cancel failed."));
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div>
      <h1 className="page-title">My registrations</h1>
      <p className="page-sub">Your seats, waitlist spots, and past cancels.</p>

      {loading && <p className="state-msg">Loading…</p>}
      {error && <p className="state-msg state-msg--error">{error}</p>}
      {!loading && !error && rows.length === 0 && (
        <p className="state-msg">
          No registrations yet. <Link to="/app/events">Browse events</Link>
        </p>
      )}

      {!loading && rows.length > 0 && (
        <ul className="reg-list">
          {rows.map((row) => (
            <li key={row.id} className="reg-item">
              <div className="reg-item-main">
                {row.eventDetail ? (
                  <Link
                    to={`/app/events/${row.event}`}
                    className="reg-item-title"
                  >
                    {row.eventDetail.title}
                  </Link>
                ) : (
                  <span className="reg-item-title">Event unavailable</span>
                )}
                <div className="reg-item-meta">
                  {row.eventDetail && (
                    <>
                      <span>{formatWhen(row.eventDetail.starts_at)}</span>
                      <span>{row.eventDetail.venue}</span>
                    </>
                  )}
                  <span>Registered {formatWhen(row.created_at)}</span>
                </div>
              </div>


              {row.status === "CONFIRMED" && (
                <Link to={`/app/tickets/${row.id}`} className="btn btn-primary">
                  View ticket
                </Link>
              )}

              <div className="reg-item-actions">
                <span className={statusClass(row.status)}>{row.status}</span>
                {row.status !== "CANCELLED" && (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={cancellingId === row.id}
                    onClick={() => onCancel(row.id)}
                  >
                    {cancellingId === row.id ? "Cancelling…" : "Cancel"}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}