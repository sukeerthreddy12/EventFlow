import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createEvent,
  getMyEvent,
  updateEvent,
  type EventWritePayload,
} from "../../api/organiserEvents";
import { apiErrorMessage } from "../../api/errors";

function toLocalInput(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInput(local: string) {
  return new Date(local).toISOString();
}

const empty = {
  title: "",
  description: "",
  venue: "",
  starts_at: "",
  ends_at: "",
  max_capacity: "50",
  price: "0",
};

export default function EventForm() {
  const { id } = useParams<{ id: string }>();
  const isNew = !id;
  const navigate = useNavigate();

  const [form, setForm] = useState(empty);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew || !id) return;
    let cancelled = false;

    getMyEvent(id)
      .then((event) => {
        if (cancelled) return;
        setForm({
          title: event.title,
          description: event.description ?? "",
          venue: event.venue,
          starts_at: toLocalInput(event.starts_at),
          ends_at: toLocalInput(event.ends_at),
          max_capacity: String(event.max_capacity),
          price: String(event.price),
        });
      })
      .catch(() => {
        if (!cancelled) setError("Could not load event.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id, isNew]);

  function setField(key: keyof typeof empty, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);

    const payload: EventWritePayload = {
      title: form.title.trim(),
      description: form.description.trim(),
      venue: form.venue.trim(),
      starts_at: fromLocalInput(form.starts_at),
      ends_at: fromLocalInput(form.ends_at),
      max_capacity: Number(form.max_capacity),
      price: form.price,
    };

    try {
      if (isNew) {
        await createEvent(payload);
        navigate("/org/events");
      } else if (id) {
        await updateEvent(id, payload);
        navigate("/org/events");
      }
      
    } catch (err) {
      setError(apiErrorMessage(err, "Save failed."));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="state-msg">Loading…</p>;

  return (
    <div style={{ maxWidth: 560 }}>
      <p className="page-sub">
        <Link to="/org/events">← My events</Link>
      </p>
      <h1 className="page-title">{isNew ? "New event" : "Edit event"}</h1>
      <p className="page-sub">
        {isNew
          ? "Creates as DRAFT. Publish from the list when ready."
          : "Update details, then manage publish from the list."}
      </p>

      <form className="auth-form" onSubmit={onSubmit}>
        <label>
          Title
          <input
            value={form.title}
            onChange={(e) => setField("title", e.target.value)}
            required
          />
        </label>
        <label>
          Venue
          <input
            value={form.venue}
            onChange={(e) => setField("venue", e.target.value)}
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={form.description}
            onChange={(e) => setField("description", e.target.value)}
            rows={4}
          />
        </label>

        <div className="datetime-row">
          <label>
            Starts
            <input
              type="datetime-local"
              value={form.starts_at}
              onChange={(e) => setField("starts_at", e.target.value)}
              required
            />
          </label>
          <label>
            Ends
            <input
              type="datetime-local"
              value={form.ends_at}
              onChange={(e) => setField("ends_at", e.target.value)}
              required
            />
          </label>
        </div>

        <div className="datetime-row">
          <label>
            Capacity
            <input
              type="number"
              min={1}
              value={form.max_capacity}
              onChange={(e) => setField("max_capacity", e.target.value)}
              required
            />
          </label>
          <label>
            Price
            <input
              type="number"
              min={0}
              step="0.01"
              value={form.price}
              onChange={(e) => setField("price", e.target.value)}
              required
            />
          </label>
        </div>

        {error && <p className="state-msg state-msg--error">{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={saving}>
          {saving ? "Saving…" : isNew ? "Create draft" : "Save changes"}
        </button>
      </form>
    </div>
  );
}