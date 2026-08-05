import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { getPublicEvent, type PublicEvent } from "../../api/events";
import {
  createRegistration,
  createTeamRegistration,
  type Registration,
  type TeamRegistrationResult,
} from "../../api/registrations";
import { useAuth } from "../../auth/AuthContext";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function EventDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [registering, setRegistering] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);
  const [registration, setRegistration] = useState<Registration | null>(null);
  const [mode, setMode] = useState<"solo" | "team">("solo");
  const [memberEmailsText, setMemberEmailsText] = useState("");
  const [teamResult, setTeamResult] = useState<TeamRegistrationResult | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    getPublicEvent(id)
      .then((data) => {
        if (!cancelled) setEvent(data);
      })
      .catch(() => {
        if (!cancelled) setError("Event not found or unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  async function onRegister() {
    if (!event) return;
    if (!user) {
      navigate("/login", { state: { from: `/app/events/${event.id}` } });
      return;
    }

    setRegError(null);
    setRegistering(true);
    try {
      const reg = await createRegistration(event.id);
      setRegistration(reg);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setRegError(
          typeof data === "object" ? JSON.stringify(data) : "Registration failed.",
        );
      } else {
        setRegError("Registration failed.");
      }
    } finally {
      setRegistering(false);
    }
  }

  async function onTeamRegister(e: React.SubmitEvent<HTMLFormElement>){
    e.preventDefault();
    if (!event) return;
    if (!user) {
      navigate("/login", { state: { from: `/app/events/${event.id}` } });
      return;
    }
  
    const emails = memberEmailsText
      .split(/[\n,]+/)
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean);
  
    if (emails.length === 0) {
      setRegError("Add at least one teammate email.");
      return;
    }
  
    setRegError(null);
    setRegistering(true);
    try {
      const result = await createTeamRegistration(event.id, emails);
      setTeamResult(result);
      // lead's own registration is in the list
      const mine = result.registrations.find((r) => r.user === user.id);
      if (mine) setRegistration(mine);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setRegError(
          typeof data === "object" ? JSON.stringify(data) : "Team registration failed.",
        );
      } else {
        setRegError("Team registration failed.");
      }
    } finally {
      setRegistering(false);
    }
  }

  if (loading) return <p className="state-msg">Loading…</p>;
  if (error) return <p className="state-msg state-msg--error">{error}</p>;
  if (!event) return null;

  const priceLabel = Number(event.price) === 0 ? "Free" : `$${event.price}`;

  return (
    <div className="event-detail">
      <p className="page-sub">
        <Link to="/app/events">← All events</Link>
      </p>

      <header className="event-detail-hero">
        {event.is_featured && <p className="event-kicker">Featured</p>}
        <h1 className="event-detail-title">{event.title}</h1>
        <p className="event-detail-meta">
          <span>{formatWhen(event.starts_at)}</span>
          <span>{event.venue}</span>
        </p>
      </header>

      {event.description && (
        <p className="event-detail-body">{event.description}</p>
      )}

      {!registration && !teamResult && (
        <div className="reg-mode">
          <button
            type="button"
            className={mode === "solo" ? "is-active" : ""}
            onClick={() => setMode("solo")}
          >
            Just me
          </button>
          <button
            type="button"
            className={mode === "team" ? "is-active" : ""}
            onClick={() => setMode("team")}
          >
            Team
          </button>
        </div>
      )}

      <div className="event-detail-panel">
        <div className="event-detail-stats">
          <strong>{priceLabel}</strong>
          <span>
            {event.max_capacity} capacity · ends {formatWhen(event.ends_at)}
          </span>
        </div>

        {!registration && !teamResult ? (
          mode === "solo" ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={onRegister}
              disabled={registering}
            >
              {!user
                ? "Sign in to register"
                : registering
                  ? "Registering…"
                  : "Register"}
            </button>
          ) : (
            <span className="page-sub" style={{ margin: 0 }}>
              Add teammates below
            </span>
          )
        ) : (
          <span
            className={
              (teamResult?.status ?? registration?.status) === "CONFIRMED"
                ? "status-chip status-chip--ok"
                : "status-chip status-chip--wait"
            }
          >
            {(teamResult?.status ?? registration?.status) === "CONFIRMED"
              ? teamResult
                ? `Team confirmed (${teamResult.member_count})`
                : "You’re confirmed"
              : teamResult
                ? `Team waitlisted (${teamResult.member_count})`
                : "You’re on the waitlist"}
          </span>
        )}
      </div>

      {mode === "team" && !registration && !teamResult && (
        <form className="team-form" onSubmit={onTeamRegister}>
          <label>
            Teammate emails
            <textarea
              value={memberEmailsText}
              onChange={(e) => setMemberEmailsText(e.target.value)}
              placeholder={"friend1@example.com\nfriend2@example.com"}
              required
            />
          </label>
          <p className="team-hint">
            One email per line (or comma-separated). They must already have
            EventFlow accounts. Don’t include your own email.
          </p>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={registering || !user}
          >
            {!user
              ? "Sign in to register team"
              : registering
                ? "Registering team…"
                : "Register team"}
          </button>
        </form>
      )}

      {regError && <p className="state-msg state-msg--error">{regError}</p>}
    </div>
  );
}