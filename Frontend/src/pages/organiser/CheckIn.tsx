import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";
import { getMyEvent, type OrganiserEvent } from "../../api/organiserEvents";
import { checkInTicket, type Ticket } from "../../api/tickets";

export default function CheckIn() {
  const { id } = useParams<{ id: string }>();
  const inputRef = useRef<HTMLInputElement>(null);

  const [event, setEvent] = useState<OrganiserEvent | null>(null);
  const [token, setToken] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTicket, setLastTicket] = useState<Ticket | null>(null);
  const [alreadyUsed, setAlreadyUsed] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getMyEvent(id)
      .then((data) => {
        if (!cancelled) setEvent(data);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load this event.");
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const value = token.trim();
    if (!value) return;

    setError(null);
    setLastTicket(null);
    setAlreadyUsed(false);
    setSubmitting(true);

    try {
      const ticket = await checkInTicket(value);
      setLastTicket(ticket);
      setAlreadyUsed(ticket.status === "USED" && !!ticket.checked_in_at);
      // Heuristic: if checked_in_at is old vs just now — API is idempotent.
      // Simpler message: always say checked in; if already USED, say already scanned.
      setToken("");
      inputRef.current?.focus();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setError(
          typeof data === "object"
            ? JSON.stringify(data)
            : "Check-in failed.",
        );
      } else {
        setError("Check-in failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="checkin-page">
      <p className="page-sub">
        <Link to="/org/events">← My events</Link>
      </p>
      <h1 className="page-title">Check-in</h1>
      <p className="page-sub">
        {event ? event.title : "Loading event…"}
        {event ? ` · ${event.venue}` : null}
      </p>

      <form className="auth-form" onSubmit={onSubmit}>
        <label>
          Ticket token
          <input
            ref={inputRef}
            className="checkin-input"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste token from guest ticket"
            autoComplete="off"
            spellCheck={false}
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Checking…" : "Check in"}
        </button>
      </form>

      {lastTicket && (
        <div className="checkin-result checkin-result--ok">
          <strong>Gate OK — {lastTicket.status}</strong>
          <p className="page-sub" style={{ marginBottom: 0 }}>
            {lastTicket.checked_in_at
              ? `Checked in at ${new Date(lastTicket.checked_in_at).toLocaleString()}`
              : "Ticket accepted"}
            . Scan again is safe (idempotent).
          </p>
        </div>
      )}

      {error && (
        <div className="checkin-result checkin-result--err">
          <p className="state-msg state-msg--error" style={{ padding: 0, margin: 0 }}>
            {error}
          </p>
        </div>
      )}
    </div>
  );
}