import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { apiErrorMessage } from "../../api/errors";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      navigate(user.role === "ORGANISER" ? "/org/events" : "/app/events");
    } catch (err) {
      setError(apiErrorMessage(err, "Login failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout-main--padded" style={{ maxWidth: 420 }}>
      <h1 className="page-title">Sign in</h1>
      <p className="page-sub">Use your verified EventFlow account.</p>

      <form onSubmit={onSubmit} className="auth-form">
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
          />
        </label>

        {error && <p className="state-msg state-msg--error">{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="page-sub">
        No account? <Link to="/register">Register</Link>
        {" · "}
        <Link to="/verify-email">Verify email</Link>
        {" · "}
        <Link to="/forgot-password">Forgot password</Link>
      </p>
    </div>
  );
}
