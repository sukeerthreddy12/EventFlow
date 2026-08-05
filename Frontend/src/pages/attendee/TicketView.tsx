import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPublicEvent, type PublicEvent } from "../../api/events";
import { listMyRegistrations, type Registration } from "../../api/registrations";
import { getTicketByRegistration, type Ticket } from "../../api/tickets";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function TicketView() {
  const { registrationId } = useParams<{ registrationId: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [reg, setReg] = useState<Registration | null>(null);
  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!registrationId) return;
    let cancelled = false;

    async function load() {
      try {
        const regs = await listMyRegistrations();
        const mine = regs.find((r) => r.id === registrationId) ?? null;
        if (!mine) {
          if (!cancelled) setError("Registration not found.");
          return;
        }
        if (mine.status !== "CONFIRMED") {
          if (!cancelled) {
            setError("Tickets are only available for confirmed registrations.");
          }
          return;
        }

        const [t, ev] = await Promise.all([
          getTicketByRegistration(registrationId ?? ""),
          getPublicEvent(mine.event).catch(() => null),
        ]);

        if (!cancelled) {
          setReg(mine);
          setTicket(t);
          setEvent(ev);
        }
      } catch {
        if (!cancelled) {
          setError("Could not load ticket. Is it issued and yours?");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [registrationId]);

  if (loading) return <p className="state-msg">Loading…</p>;
  if (error) return <p className="state-msg state-msg--error">{error}</p>;
  if (!ticket || !reg) return null;

  return (
    <div>
      <p className="page-sub">
        <Link to="/app/my-registrations">← My registrations</Link>
      </p>
      <h1 className="page-title">Your ticket</h1>
      <p className="page-sub">Show this token at the door for check-in.</p>

      <div className="ticket-card">
        <h2>{event?.title ?? "Event"}</h2>
        <div className="ticket-meta">
          {event && <span>{formatWhen(event.starts_at)}</span>}
          {event && <span>{event.venue}</span>}
          <span className="status-chip status-chip--ok">{ticket.status}</span>
        </div>

        <p className="page-sub" style={{ marginTop: "1.25rem", marginBottom: 0 }}>
          Check-in token
        </p>
        <div className="ticket-token">{ticket.token}</div>

        <p className="team-hint">
          QR codes can come later — organisers can paste this token into check-in.
        </p>
      </div>
    </div>
  );
}