import { useEffect, useState, type FormEvent } from "react";
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

function apiErrorMessage(err: unknown, fallback: string) {
  if (!axios.isAxiosError(err)) return fallback;
  const data = err.response?.data;
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    if ("detail" in data && typeof data.detail === "string") return data.detail;
    return fallback;
  }
  return fallback;
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
  const [teamResult, setTeamResult] = useState<TeamRegistrationResult | null>(
    null,
  );

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
      setRegError(apiErrorMessage(err, "Registration failed."));
    } finally {
      setRegistering(false);
    }
  }

  async function onTeamRegister(e: FormEvent<HTMLFormElement>) {
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
      const mine = result.registrations.find((r) => r.user === user.id);
      if (mine) setRegistration(mine);
    } catch (err) {
      setRegError(apiErrorMessage(err, "Team registration failed."));
    } finally {
      setRegistering(false);
    }
  }

  if (loading) return <p className="state-msg">Loading night…</p>;
  if (error) return <p className="state-msg state-msg--error">{error}</p>;
  if (!event) return null;

  const priceLabel = Number(event.price) === 0 ? "Free" : `$${event.price}`;
  const outcomeStatus = teamResult?.status ?? registration?.status;
  const isConfirmed = outcomeStatus === "CONFIRMED";
  const done = Boolean(registration || teamResult);

  return (
    <div className="event-detail">
      <p className="event-detail__back">
        <Link to="/app/events">← All events</Link>
      </p>

      <header className="event-detail__stage">
        <div className="event-detail__stage-inner">
          {event.is_featured ? (
            <p className="event-kicker">Featured night</p>
          ) : (
            <p className="event-kicker">Live registration</p>
          )}
          <h1 className="event-detail-title">{event.title}</h1>
          <p className="event-detail-meta">
            <span>{formatWhen(event.starts_at)}</span>
            <span>{event.venue}</span>
            <span>{priceLabel}</span>
          </p>
        </div>
      </header>

      <div className="event-detail__grid">
        <section className="event-detail__story">
          <h2 className="event-detail__section-title">About this night</h2>
          {event.description ? (
            <p className="event-detail-body">{event.description}</p>
          ) : (
            <p className="event-detail-body event-detail-body--muted">
              No description yet — the venue and time are confirmed. Register to
              lock your place.
            </p>
          )}

          <dl className="event-detail__facts">
            <div>
              <dt>Starts</dt>
              <dd>{formatWhen(event.starts_at)}</dd>
            </div>
            <div>
              <dt>Ends</dt>
              <dd>{formatWhen(event.ends_at)}</dd>
            </div>
            <div>
              <dt>Venue</dt>
              <dd>{event.venue}</dd>
            </div>
            <div>
              <dt>Capacity</dt>
              <dd>{event.max_capacity} seats</dd>
            </div>
          </dl>
        </section>

        <aside className="event-detail__register">
          <div className="event-register">
            <header className="event-register__head">
              <h2>Get in</h2>
              <p>
                {done
                  ? "Your place is recorded."
                  : "Solo or team — seats are locked fairly when capacity fills."}
              </p>
            </header>

            <div className="event-register__price">
              <strong>{priceLabel}</strong>
              <span>{event.max_capacity} capacity</span>
            </div>

            {!done && (
              <div className="reg-mode" role="tablist" aria-label="Registration mode">
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

            {!done && mode === "solo" && (
              <button
                type="button"
                className="btn btn-primary event-register__cta"
                onClick={onRegister}
                disabled={registering}
              >
                {!user
                  ? "Sign in to register"
                  : registering
                    ? "Registering…"
                    : "Register for this night"}
              </button>
            )}

            {!done && mode === "team" && (
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
                  className="btn btn-primary event-register__cta"
                  disabled={registering}
                >
                  {!user
                    ? "Sign in to register team"
                    : registering
                      ? "Registering team…"
                      : "Register team"}
                </button>
              </form>
            )}

            {done && (
              <div
                className={
                  isConfirmed
                    ? "event-register__result event-register__result--ok"
                    : "event-register__result event-register__result--wait"
                }
              >
                <strong>
                  {isConfirmed
                    ? teamResult
                      ? `Team confirmed · ${teamResult.member_count} people`
                      : "You’re confirmed"
                    : teamResult
                      ? `Team waitlisted · ${teamResult.member_count} people`
                      : "You’re on the waitlist"}
                </strong>
                <p>
                  {isConfirmed
                    ? "Your ticket is ready when you are."
                    : "We’ll promote you if a seat opens — keep an eye on email."}
                </p>
                {isConfirmed && registration && (
                  <Link
                    to={`/app/tickets/${registration.id}`}
                    className="btn btn-primary"
                  >
                    View ticket
                  </Link>
                )}
                {!isConfirmed && (
                  <Link to="/app/my-registrations" className="btn btn-ghost">
                    My registrations
                  </Link>
                )}
              </div>
            )}

            {regError && (
              <p className="event-register__error">{regError}</p>
            )}

            {!user && !done && (
              <p className="event-register__note">
                New here?{" "}
                <Link to="/register">Create an attendee account</Link> first.
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
