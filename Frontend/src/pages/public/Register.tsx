import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../../api/accounts";
import { apiErrorMessage } from "../../api/errors";

export default function Register() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"ATTENDEE" | "ORGANISER">("ATTENDEE");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({ username, email, password, role });
      navigate("/verify-email", { state: { email } });
    } catch (err) {
      setError(apiErrorMessage(err, "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout-main--padded" style={{ maxWidth: 420 }}>
      <h1 className="page-title">Create account</h1>
      <p className="page-sub">
        After signup, grab the verify token from the Django terminal.
      </p>

      <form onSubmit={onSubmit} className="auth-form">
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>
        <label>
          Role
          <select
            value={role}
            onChange={(e) =>
              setRole(e.target.value as "ATTENDEE" | "ORGANISER")
            }
          >
            <option value="ATTENDEE">Attendee</option>
            <option value="ORGANISER">Organiser</option>
          </select>
        </label>

        {error && <p className="state-msg state-msg--error">{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating…" : "Register"}
        </button>
      </form>

      <p className="page-sub">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
