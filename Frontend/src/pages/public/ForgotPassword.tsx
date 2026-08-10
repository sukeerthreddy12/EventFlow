import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../../api/accounts";
import { apiErrorMessage } from "../../api/errors";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const res = await requestPasswordReset(email);
      setMessage(res.message);
    } catch (err) {
      setError(apiErrorMessage(err, "Request failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout-main--padded" style={{ maxWidth: 420 }}>
      <h1 className="page-title">Forgot password</h1>
      <p className="page-sub">
        We’ll email a reset link if an account exists for that address.
        With Resend testing, use your Resend account email.
      </p>

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

        {error && <p className="state-msg state-msg--error">{error}</p>}
        {message && <p className="state-msg">{message}</p>}

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Sending…" : "Send reset link"}
        </button>
      </form>

      <p className="page-sub">
        <Link to="/login">Back to sign in</Link>
        {" · "}
        <Link to="/reset-password">I already have a token</Link>
      </p>
    </div>
  );
}
